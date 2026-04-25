"""
secp256k1 Elliptic Curve Primitives

Implements low-level point arithmetic, encoding, and hash-to-curve
operations on the secp256k1 curve used by Bitcoin and Ethereum.
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Point:
    """Affine point on secp256k1 (or the point at infinity)."""
    x: Optional[int]
    y: Optional[int]

    def is_infinity(self) -> bool:
        return self.x is None and self.y is None


INFINITY = Point(None, None)


class Secp256k1:
    """secp256k1 domain parameters."""
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    a = 0
    b = 7
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
    G = Point(Gx, Gy)
    n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


# ---------------------------------------------------------------------------
# Modular Arithmetic
# ---------------------------------------------------------------------------

def inv_mod(x: int, p: int) -> int:
    """Modular inverse using Fermat's little theorem (p must be prime)."""
    return pow(x, p - 2, p)


# ---------------------------------------------------------------------------
# Point Arithmetic
# ---------------------------------------------------------------------------

def point_add(P: Point, Q: Point) -> Point:
    """Elliptic curve point addition / doubling on secp256k1."""
    if P.is_infinity():
        return Q
    if Q.is_infinity():
        return P
    p = Secp256k1.p
    if P.x == Q.x and (P.y != Q.y or P.y == 0):
        return INFINITY
    if P.x == Q.x:
        lam = (3 * P.x * P.x + Secp256k1.a) * inv_mod(2 * P.y, p) % p
    else:
        lam = (Q.y - P.y) * inv_mod(Q.x - P.x, p) % p
    rx = (lam * lam - P.x - Q.x) % p
    ry = (lam * (P.x - rx) - P.y) % p
    return Point(rx, ry)


def scalar_mult(k: int, P: Point) -> Point:
    """Double-and-add scalar multiplication: k * P."""
    if k % Secp256k1.n == 0 or P.is_infinity():
        return INFINITY
    if k < 0:
        return scalar_mult(-k, Point(P.x, (-P.y) % Secp256k1.p))
    result = INFINITY
    addend = P
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


# ---------------------------------------------------------------------------
# Modular Square Root (optimized for secp256k1 where p ≡ 3 mod 4)
# ---------------------------------------------------------------------------

def mod_sqrt(a: int, p: int) -> Optional[int]:
    """Compute modular square root for secp256k1 (p ≡ 3 mod 4 fast path)."""
    if a == 0:
        return 0
    x = pow(a, (p + 1) // 4, p)
    if (x * x) % p == a % p:
        return x
    return None


# ---------------------------------------------------------------------------
# Point Encoding / Decoding
# ---------------------------------------------------------------------------

def point_to_bytes(P: Point) -> bytes:
    """Encode point as uncompressed bytes: 0x04 || x(32) || y(32)."""
    if P.is_infinity():
        return b'\x00'
    xb = P.x.to_bytes(32, 'big')
    yb = P.y.to_bytes(32, 'big')
    return b'\x04' + xb + yb


def bytes_to_point(b: bytes) -> Point:
    """Decode uncompressed point from bytes."""
    if len(b) == 1 and b[0] == 0:
        return INFINITY
    if b[0] != 4 or len(b) != 65:
        raise ValueError("Only uncompressed point format (0x04||x||y) is supported")
    x = int.from_bytes(b[1:33], 'big')
    y = int.from_bytes(b[33:], 'big')
    return Point(x, y)


# ---------------------------------------------------------------------------
# Hash Utilities
# ---------------------------------------------------------------------------

def sha256_hash(b: bytes) -> bytes:
    """SHA-256 digest."""
    return hashlib.sha256(b).digest()


def hash_to_scalar(*parts: bytes) -> int:
    """Domain-separated hash to a scalar in [0, n)."""
    h = hashlib.sha256(b'LSAG' + b''.join(parts)).digest()
    return int.from_bytes(h, 'big') % Secp256k1.n


def hash_to_point(data: bytes, tag: bytes = b'Hp') -> Point:
    """Hash arbitrary data to a curve point using try-and-increment."""
    counter = 0
    p = Secp256k1.p
    while True:
        digest = hashlib.sha256(tag + data + counter.to_bytes(4, 'big')).digest()
        x = int.from_bytes(digest, 'big') % p
        rhs = (pow(x, 3, p) + Secp256k1.a * x + Secp256k1.b) % p
        y = mod_sqrt(rhs, p)
        if y is not None:
            if y & 1:
                y = p - y
            return Point(x, y)
        counter += 1


# ---------------------------------------------------------------------------
# Key Generation
# ---------------------------------------------------------------------------

def generate_keypair() -> Tuple[int, Point]:
    """Generate a random secp256k1 keypair (private scalar, public point)."""
    priv = secrets.randbelow(Secp256k1.n - 1) + 1
    pub = scalar_mult(priv, Secp256k1.G)
    return priv, pub
