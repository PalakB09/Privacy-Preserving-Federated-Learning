"""
Linkable Spontaneous Anonymous Group (LSAG) Ring Signatures

Provides anonymous authentication: a signer can prove membership in a ring
of public keys without revealing which key is theirs. The key image enables
linkability (double-spend / replay detection) while preserving anonymity.
"""

import hashlib
import secrets
from typing import Any, Dict, List, Tuple

from .secp256k1 import (
    Point,
    Secp256k1,
    generate_keypair,
    hash_to_point,
    hash_to_scalar,
    point_add,
    point_to_bytes,
    bytes_to_point,
    scalar_mult,
)


class LSAG:
    """LSAG ring signature scheme over secp256k1."""

    def __init__(self):
        self.G = Secp256k1.G
        self.n = Secp256k1.n

    def generate_keypair(self) -> Tuple[int, Point]:
        """Generate a secp256k1 keypair for use in a ring."""
        return generate_keypair()

    def key_image(self, priv: int, pub: Point) -> Point:
        """Compute key image I = x * H(P) for linkability."""
        Hp = hash_to_point(point_to_bytes(pub))
        return scalar_mult(priv, Hp)

    def sign(
        self,
        message: bytes,
        priv: int,
        pub_keys: List[Point],
        signer_index: int,
    ) -> Dict[str, Any]:
        """
        Produce an LSAG ring signature.

        Args:
            message: the data being signed
            priv: signer's private key
            pub_keys: ordered list of all ring members' public keys
            signer_index: index of the actual signer in pub_keys

        Returns:
            Signature dict containing key image, initial challenge, and
            response scalars.
        """
        ring_size = len(pub_keys)
        if not (0 <= signer_index < ring_size):
            raise ValueError("signer_index out of range")

        I = self.key_image(priv, pub_keys[signer_index])

        s = [0] * ring_size
        for i in range(ring_size):
            if i != signer_index:
                s[i] = secrets.randbelow(self.n)
        alpha = secrets.randbelow(self.n)

        Ls = scalar_mult(alpha, self.G)
        Hps = hash_to_point(point_to_bytes(pub_keys[signer_index]))
        Rs = scalar_mult(alpha, Hps)

        pubkeys_bytes = b''.join(point_to_bytes(pk) for pk in pub_keys)
        c = [0] * ring_size
        c[(signer_index + 1) % ring_size] = hash_to_scalar(
            message, point_to_bytes(I), point_to_bytes(Ls), point_to_bytes(Rs), pubkeys_bytes
        )

        i = (signer_index + 1) % ring_size
        while i != signer_index:
            Li = point_add(scalar_mult(s[i], self.G), scalar_mult(c[i], pub_keys[i]))
            Ri = point_add(
                scalar_mult(s[i], hash_to_point(point_to_bytes(pub_keys[i]))),
                scalar_mult(c[i], I),
            )
            c[(i + 1) % ring_size] = hash_to_scalar(
                message, point_to_bytes(I), point_to_bytes(Li), point_to_bytes(Ri), pubkeys_bytes
            )
            i = (i + 1) % ring_size

        s[signer_index] = (alpha - (c[signer_index] * priv)) % self.n

        return {
            'I': point_to_bytes(I).hex(),
            'c0': c[0],
            's': [int(x) for x in s],
            'pubkeys': [point_to_bytes(pk).hex() for pk in pub_keys],
            'ring_size': ring_size,
            'message_hash': hashlib.sha256(message).hexdigest(),
        }

    def verify(self, signature: Dict[str, Any], message: bytes) -> bool:
        """
        Verify an LSAG ring signature.

        Uses constant-time comparison for the final challenge check
        to mitigate timing side-channels.
        """
        try:
            ring_size = signature['ring_size']
            if ring_size <= 0:
                return False

            pubkeys_bytes_list = [bytes.fromhex(x) for x in signature['pubkeys']]
            pub_keys = [bytes_to_point(b) for b in pubkeys_bytes_list]
            s = signature['s']
            if len(s) != ring_size:
                return False

            c = signature['c0']
            I = bytes_to_point(bytes.fromhex(signature['I']))
            pubkeys_bytes = b''.join(point_to_bytes(pk) for pk in pub_keys)

            cur_c = c
            for i in range(ring_size):
                Li = point_add(scalar_mult(s[i], self.G), scalar_mult(cur_c, pub_keys[i]))
                Ri = point_add(
                    scalar_mult(s[i], hash_to_point(point_to_bytes(pub_keys[i]))),
                    scalar_mult(cur_c, I),
                )
                cur_c = hash_to_scalar(
                    message, point_to_bytes(I), point_to_bytes(Li), point_to_bytes(Ri), pubkeys_bytes
                )

            return secrets.compare_digest(
                cur_c.to_bytes(32, 'big'),
                c.to_bytes(32, 'big'),
            )
        except Exception:
            return False
