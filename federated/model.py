"""
Federated Logistic Regression Model

A from-scratch logistic regression with L2 regularization, designed for
federated learning where parameters are exchanged between clients and
the coordinator each round.
"""

import numpy as np


class FederatedLogisticRegression:
    """Binary logistic regression with gradient descent and L2 regularization."""

    def __init__(self, learning_rate: float = 0.01, max_iter: int = 100, C: float = 1.0):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.C = C
        self.coef_: np.ndarray = None
        self.intercept_: float = None

    def sigmoid(self, z: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid activation."""
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        init_coef: np.ndarray = None,
        init_intercept: float = None,
    ) -> "FederatedLogisticRegression":
        """
        Train via gradient descent with optional warm-start from global parameters.

        Args:
            X: feature matrix (n_samples, n_features)
            y: binary labels
            init_coef: optional initial coefficient vector
            init_intercept: optional initial intercept

        Returns:
            self (for chaining)
        """
        n_samples, n_features = X.shape

        if init_coef is not None and init_intercept is not None:
            self.coef_ = init_coef.copy()
            self.intercept_ = float(init_intercept) if np.isscalar(init_intercept) else float(init_intercept.copy())
        else:
            self.coef_ = np.zeros(n_features)
            self.intercept_ = 0.0

        for _ in range(self.max_iter):
            z = X.dot(self.coef_) + self.intercept_
            h = self.sigmoid(z)
            dw = (1 / n_samples) * X.T.dot(h - y) + (1 / self.C) * self.coef_
            db = (1 / n_samples) * np.sum(h - y)
            self.coef_ -= self.learning_rate * dw
            self.intercept_ -= self.learning_rate * db

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return class probabilities [P(y=0), P(y=1)]."""
        z = X.dot(self.coef_) + self.intercept_
        prob_1 = self.sigmoid(z)
        prob_0 = 1 - prob_1
        return np.column_stack([prob_0, prob_1])

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return binary predictions."""
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

    def get_parameters(self) -> np.ndarray:
        """Flatten model parameters into a single vector [coef | intercept]."""
        return np.concatenate([self.coef_.flatten(), [self.intercept_]])

    def set_parameters(self, parameters: np.ndarray) -> None:
        """Restore model parameters from a flat vector."""
        self.coef_ = parameters[:-1].copy()
        self.intercept_ = float(parameters[-1])

    def compute_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """Binary cross-entropy loss with L2 penalty."""
        z = X.dot(self.coef_) + self.intercept_
        h = self.sigmoid(z)
        eps = 1e-15
        h = np.clip(h, eps, 1 - eps)
        bce = -np.mean(y * np.log(h) + (1 - y) * np.log(1 - h))
        l2 = (1 / (2 * self.C)) * np.sum(self.coef_ ** 2)
        return bce + l2
