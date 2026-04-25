"""
Federated Learning Coordinator (Server)

Handles signature verification, replay-attack prevention, threshold
decryption orchestration, and federated averaging of client updates.
"""

import hashlib
import json
from typing import Any, Dict, List

import numpy as np

from crypto.lsag import LSAG
from crypto.threshold import ThresholdDecryption
from utils.logger import get_logger

log = get_logger("Server")


class FederatedCoordinator:
    """Central server that aggregates encrypted, signed client updates."""

    def __init__(
        self,
        threshold_decryptor: ThresholdDecryption,
        lsag: LSAG,
        num_clients: int,
    ):
        self.threshold = threshold_decryptor
        self.lsag = lsag
        self.num_clients = num_clients
        self.seen_signatures: set = set()

    def aggregate_round(
        self,
        encrypted_updates: List[Dict],
        signatures: List[Dict],
        party_indices: List[int],
    ) -> np.ndarray:
        """
        Execute one aggregation round:
            1. Verify each client's ring signature
            2. Reject replayed signatures
            3. Threshold-decrypt valid updates
            4. Return federated average of decrypted weights
        """
        if len(party_indices) < self.threshold.threshold:
            raise ValueError(
                f"Need at least {self.threshold.threshold} parties for "
                f"threshold decryption, got {len(party_indices)}"
            )

        valid_updates: List[np.ndarray] = []

        for cid, (enc, sig) in enumerate(zip(encrypted_updates, signatures)):
            sig_hash = hashlib.sha256(
                json.dumps(sig, sort_keys=True).encode()
            ).hexdigest()

            if sig_hash in self.seen_signatures:
                log.warning(f"Client {cid}: Replay attack detected - skipping")
                continue

            message = json.dumps(enc, sort_keys=True).encode()
            if not self.lsag.verify(sig, message):
                log.error(f"Client {cid}: Invalid ring signature")
                continue

            log.info(f"Anonymous update {cid}: signature valid")

            partial_secrets = []
            for party_idx in party_indices:
                partial = self.threshold.get_partial_decryption(enc, party_idx)
                partial_secrets.append(partial)

            try:
                weights = self.threshold.combine_and_decrypt(enc, partial_secrets)
                valid_updates.append(weights)
                self.seen_signatures.add(sig_hash)
            except Exception as e:
                log.error(f"Client {cid}: Threshold decryption failed - {e}")

        if not valid_updates:
            raise ValueError("No valid updates received in this round")

        aggregated = np.mean(valid_updates, axis=0)
        log.info(f"Aggregation complete - {len(valid_updates)} valid updates averaged")
        return aggregated
