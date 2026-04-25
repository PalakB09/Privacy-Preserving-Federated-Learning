"""
ECIES-style Encryption / Decryption

Combines secp256k1 ECDH with AES-256-GCM and PBKDF2 key derivation
to encrypt and decrypt numpy weight arrays for federated learning.
"""

import base64
from typing import Dict

import numpy as np
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

from .secp256k1 import (
    Point,
    bytes_to_point,
    generate_keypair,
    point_to_bytes,
    scalar_mult,
)


def encrypt_weights(pub_point: Point, weights: np.ndarray) -> Dict[str, str]:
    """
    Encrypt a weight vector under the recipient's public key using ECIES.

    Steps:
        1. Generate ephemeral keypair (r, R = r*G)
        2. ECDH shared secret: S = r * pub_point
        3. Derive AES key via PBKDF2(S.x, salt)
        4. AES-GCM encrypt the raw weight bytes

    Returns a dict with hex/base64-encoded ciphertext components.
    """
    eph_priv, eph_pub = generate_keypair()

    shared_point = scalar_mult(eph_priv, pub_point)
    shared_secret = int(shared_point.x).to_bytes(32, "big")

    salt = get_random_bytes(16)
    aes_key = PBKDF2(shared_secret, salt, dkLen=16, count=100000)

    cipher_aes = AES.new(aes_key, AES.MODE_GCM)
    ciphertext, tag = cipher_aes.encrypt_and_digest(weights.tobytes())

    return {
        "eph_pub": point_to_bytes(eph_pub).hex(),
        "salt": base64.b64encode(salt).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "nonce": base64.b64encode(cipher_aes.nonce).decode(),
        "tag": base64.b64encode(tag).decode(),
    }


def decrypt_weights(priv_int: int, enc_dict: Dict) -> np.ndarray:
    """
    Decrypt an ECIES ciphertext using the recipient's private scalar.

    This is the single-party decryption path. For threshold decryption,
    use ThresholdDecryption.combine_and_decrypt() instead.
    """
    eph_pub = bytes_to_point(bytes.fromhex(enc_dict["eph_pub"]))
    nonce = base64.b64decode(enc_dict["nonce"])
    tag = base64.b64decode(enc_dict["tag"])
    ciphertext = base64.b64decode(enc_dict["ciphertext"])
    salt = base64.b64decode(enc_dict["salt"])

    shared_point = scalar_mult(priv_int, eph_pub)
    shared_secret = int(shared_point.x).to_bytes(32, "big")

    aes_key = PBKDF2(shared_secret, salt, dkLen=16, count=100000)

    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    data = cipher_aes.decrypt_and_verify(ciphertext, tag)
    return np.frombuffer(data, dtype=np.float64)
