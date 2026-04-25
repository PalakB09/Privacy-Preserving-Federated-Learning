"""
Dataset Loader

Loads the diabetes binary classification dataset, applies train/test
splitting with stratification, per-client partitioning, and StandardScaler
normalization. Supports deterministic reproducibility via random seeds.
"""

import os
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from utils.logger import get_logger

log = get_logger("Data")


def load_dataset(config: Dict) -> Tuple[
    List[Tuple[np.ndarray, np.ndarray]],
    np.ndarray,
    np.ndarray,
    StandardScaler,
]:
    """
    Load and prepare the dataset for federated learning.

    Returns:
        client_data: list of (X_scaled, y) tuples, one per client
        X_test_scaled: scaled test features
        y_test: test labels
        eval_scaler: the scaler fitted on full training data (for evaluation)
    """
    seed = config.get("random_seed", 42)
    num_clients = config.get("num_clients", 3)
    test_size = config.get("test_size", 0.2)
    dataset_path = config.get("dataset_path", "filtered_diabetes_data.csv")

    if not os.path.isabs(dataset_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dataset_path = os.path.join(base_dir, dataset_path)

    log.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)

    target_col = "Diabetes_binary"
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    log.info(f"Total training samples: {len(X_train_full)}")
    log.info(f"Test samples: {len(X_test)}")

    X_splits = np.array_split(X_train_full, num_clients)
    y_splits = np.array_split(y_train_full, num_clients)

    client_data = []
    for cid, (X_c, y_c) in enumerate(zip(X_splits, y_splits)):
        scaler = StandardScaler()
        X_c_scaled = scaler.fit_transform(X_c)
        client_data.append((X_c_scaled, y_c))
        log.info(f"Client {cid}: {len(X_c)} samples")

    eval_scaler = StandardScaler()
    eval_scaler.fit(X_train_full)
    X_test_scaled = eval_scaler.transform(X_test)

    return client_data, X_test_scaled, y_test, eval_scaler
