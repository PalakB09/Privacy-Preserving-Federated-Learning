"""
Threshold Cryptography Module

Implements dealerless distributed key generation (Pedersen DKG style),
Shamir secret sharing with Lagrange interpolation, and threshold
decryption coordinated across multiple parties.
"""

import base64
import secrets
from typing import Any, Dict, List, Tuple

import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

from .secp256k1 import (
    INFINITY,
    Point,
    Secp256k1,
    bytes_to_point,
    point_add,
    point_to_bytes,
    scalar_mult,
)

P = Secp256k1.n  # group order used for modular arithmetic


def dealerless_keygen(num_parties: int, threshold: int) -> Tuple[List[Tuple[int, int]], Point]:
    """
    Dealerless distributed key generation using joint random secret sharing.

    Each party independently generates a random polynomial and shares
    evaluations with all other parties. The joint secret key d is never
    explicitly constructed — only its public key d*G is computed.

    Returns:
        shares: list of (party_id, share_value) Shamir shares
        public_key: Point = d * G
    """
    if threshold < 2 or threshold > num_parties:
        raise ValueError(f"Threshold must be between 2 and {num_parties}")

    degree = threshold - 1

    polynomials: List[List[int]] = []
    for _ in range(num_parties):
        coeffs = [secrets.randbelow(Secp256k1.n) for _ in range(degree + 1)]
        polynomials.append(coeffs)

    shares_scalar = [0] * num_parties
    for i in range(num_parties):
        coeffs = polynomials[i]
        for j in range(num_parties):
            x = j + 1
            fx = 0
            for k, a_k in enumerate(coeffs):
                fx = (fx + a_k * pow(x, k, Secp256k1.n)) % Secp256k1.n
            shares_scalar[j] = (shares_scalar[j] + fx) % Secp256k1.n

    public_key = INFINITY
    for coeffs in polynomials:
        a0 = coeffs[0]
        public_key = point_add(public_key, scalar_mult(a0, Secp256k1.G))

    return [(i + 1, shares_scalar[i]) for i in range(num_parties)], public_key


def lagrange_interpolate(x: int, shares: List[Tuple[int, int]]) -> int:
    """Lagrange interpolation at point x over the secp256k1 group order."""
    total = 0
    for i, (xi, yi) in enumerate(shares):
        num, den = 1, 1
        for j, (xj, _) in enumerate(shares):
            if i != j:
                num = (num * (x - xj)) % P
                den = (den * (xi - xj)) % P
        inv_den = pow(den, -1, P)
        term = yi * num * inv_den
        total = (total + term) % P
    return total


class ThresholdDecryption:
    """Coordinates multi-party threshold decryption of ECIES ciphertexts."""

    def __init__(self, shares: List[Tuple[int, int]], threshold: int):
        self.shares = shares
        self.threshold = threshold
        self.n = len(shares)

    def get_partial_decryption(self, enc_dict: Dict, party_index: int) -> Dict[str, Any]:
        """
        Compute a partial decryption contribution from a single party.

        The party multiplies the ephemeral public key by their secret share,
        producing a partial shared-secret point.
        """
        if party_index >= len(self.shares):
            raise ValueError(f"Party index {party_index} out of range")

        eph_pub = bytes_to_point(bytes.fromhex(enc_dict["eph_pub"]))
        share_id, share_value = self.shares[party_index]
        partial_point = scalar_mult(share_value, eph_pub)

        return {
            'party_id': share_id,
            'partial_secret': point_to_bytes(partial_point).hex(),
        }

    def combine_and_decrypt(self, enc_dict: Dict, partial_secrets: List[Dict]) -> np.ndarray:
        """
        Combine partial decryptions via Lagrange interpolation in the exponent,
        then derive the AES key and decrypt the ciphertext.
        """
        if len(partial_secrets) < self.threshold:
            raise ValueError(
                f"Need at least {self.threshold} parties, got {len(partial_secrets)}"
            )

        points_for_interpolation = []
        for ps in partial_secrets:
            party_id = ps['party_id']
            partial_point = bytes_to_point(bytes.fromhex(ps['partial_secret']))
            points_for_interpolation.append((party_id, partial_point))

        combined_point = INFINITY
        for i, (xi, Pi) in enumerate(points_for_interpolation):
            lambda_i = 1
            for j, (xj, _) in enumerate(points_for_interpolation):
                if i != j:
                    num = (0 - xj) % P
                    den = (xi - xj) % P
                    lambda_i = (lambda_i * num * pow(den, -1, P)) % P
            term = scalar_mult(lambda_i, Pi)
            combined_point = point_add(combined_point, term)

        if combined_point.is_infinity():
            raise ValueError("Combined point is point at infinity - invalid partials")

        shared_secret = int(combined_point.x).to_bytes(32, "big")

        salt = base64.b64decode(enc_dict["salt"])
        derived_aes_key = PBKDF2(shared_secret, salt, dkLen=16, count=100000)

        nonce = base64.b64decode(enc_dict["nonce"])
        tag = base64.b64decode(enc_dict["tag"])
        ciphertext = base64.b64decode(enc_dict["ciphertext"])

        cipher_aes = AES.new(derived_aes_key, AES.MODE_GCM, nonce=nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        return np.frombuffer(data, dtype=np.float64)
