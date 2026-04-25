"""
Federated Learning Client

Encapsulates local training, weight encryption, and anonymous signing
for a single participant in the federated learning protocol.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import accuracy_score

from crypto.secp256k1 import Point, generate_keypair
from crypto.encryption import encrypt_weights
from crypto.lsag import LSAG
from .model import FederatedLogisticRegression


class FederatedClient:
    """A single federated learning participant."""

    def __init__(
        self,
        client_id: int,
        X_train: np.ndarray,
        y_train: np.ndarray,
        keypair: Tuple[int, Point],
        learning_rate: float = 0.1,
        local_epochs: int = 10,
        C: float = 1.0,
    ):
        self.client_id = client_id
        self.X_train = X_train
        self.y_train = y_train
        self.private_key, self.public_key = keypair

        self.model = FederatedLogisticRegression(
            learning_rate=learning_rate,
            max_iter=local_epochs,
            C=C,
        )
        self._last_weights: Optional[np.ndarray] = None

    def train(self, global_params: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Run local training for the configured number of epochs.

        If global_params is provided, the model is warm-started from the
        aggregated global state before training.

        Returns the trained parameter vector.
        """
        init_coef = None
        init_intercept = None

        if global_params is not None:
            self.model.set_parameters(global_params)
            init_coef = self.model.coef_
            init_intercept = self.model.intercept_

        self.model.fit(
            self.X_train,
            self.y_train,
            init_coef=init_coef,
            init_intercept=init_intercept,
        )

        self._last_weights = self.model.get_parameters()
        return self._last_weights

    def encrypt_update(self, server_pub: Point) -> Dict[str, str]:
        """Encrypt the latest weight vector under the server's public key."""
        if self._last_weights is None:
            raise RuntimeError("Must call train() before encrypt_update()")
        return encrypt_weights(server_pub, self._last_weights)

    def sign_update(
        self,
        enc_dict: Dict[str, str],
        all_pub_keys: List[Point],
    ) -> Dict[str, Any]:
        """Produce an LSAG ring signature over the encrypted update."""
        lsag = LSAG()
        message = json.dumps(enc_dict, sort_keys=True).encode()
        signer_index = next(
            i for i, pk in enumerate(all_pub_keys)
            if pk.x == self.public_key.x and pk.y == self.public_key.y
        )
        return lsag.sign(message, self.private_key, all_pub_keys, signer_index)

    def get_local_accuracy(self) -> float:
        """Evaluate model accuracy on the client's own training data."""
        preds = self.model.predict(self.X_train)
        return accuracy_score(self.y_train, preds)

    def get_local_loss(self) -> float:
        """Evaluate model loss on the client's own training data."""
        return self.model.compute_loss(self.X_train, self.y_train)
