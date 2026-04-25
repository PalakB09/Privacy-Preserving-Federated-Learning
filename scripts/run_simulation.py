"""
Federated Learning Simulation Runner

Orchestrates the full privacy-preserving federated learning pipeline:
    1. Loads configuration from YAML
    2. Performs dealerless threshold key generation
    3. Loads and partitions the dataset
    4. Runs N federated rounds with local training, ECIES encryption,
       LSAG signing, threshold decryption, and federated averaging
    5. Evaluates the global model each round
    6. Generates accuracy/loss plots
"""

import os
import sys
import warnings

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import yaml
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

# Ensure project root is on sys.path for clean imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from crypto.secp256k1 import generate_keypair
from crypto.threshold import ThresholdDecryption, dealerless_keygen
from crypto.lsag import LSAG
from data.dataset_loader import load_dataset
from federated.client import FederatedClient
from federated.coordinator import FederatedCoordinator
from federated.model import FederatedLogisticRegression
from scripts.visualize import plot_metrics
from utils.logger import get_logger

warnings.filterwarnings("ignore")

log = get_logger("Main")
log_threshold = get_logger("Threshold")


def load_config(path: str = None) -> dict:
    """Load YAML configuration file."""
    if path is None:
        path = os.path.join(PROJECT_ROOT, "config", "config.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run_simulation(config: dict = None) -> dict:
    """
    Execute the full federated learning simulation.

    Returns a results dict with accuracy/loss history and final metrics.
    """
    if config is None:
        config = load_config()

    # ── Reproducibility ──
    seed = config.get("random_seed", 42)
    np.random.seed(seed)

    num_clients = config["num_clients"]
    num_parties = config["num_parties"]
    threshold = config["threshold"]
    num_rounds = config["rounds"]
    lr = config["learning_rate"]
    local_epochs = config["local_epochs"]

    print()
    print("=" * 70)
    print("  PRIVACY-PRESERVING FEDERATED LEARNING WITH THRESHOLD CRYPTOGRAPHY")
    print("=" * 70)
    print()

    # ── Step 1: Threshold Key Generation ──
    log.info("Running dealerless distributed key generation...")
    shares, server_pub = dealerless_keygen(num_parties, threshold)
    log.info("Dealerless key generation complete (no party knows full private key)")
    log.info(f"Parties {list(range(num_parties))} hold shares")
    log.info(f"Any {threshold} parties can collaborate to decrypt")
    print()

    # ── Step 2: Client Keypairs ──
    client_keypairs = [generate_keypair() for _ in range(num_clients)]
    all_pub_keys = [kp[1] for kp in client_keypairs]
    log.info(f"{num_clients} client secp256k1 keypairs generated")
    print()

    # ── Step 3: Load Dataset ──
    log.info("Loading dataset...")
    client_data, X_test, y_test, eval_scaler = load_dataset(config)
    print()

    # ── Step 4: Initialize Clients ──
    clients = []
    for cid in range(num_clients):
        X_c, y_c = client_data[cid]
        client = FederatedClient(
            client_id=cid,
            X_train=X_c,
            y_train=y_c,
            keypair=client_keypairs[cid],
            learning_rate=lr,
            local_epochs=local_epochs,
        )
        clients.append(client)

    threshold_dec = ThresholdDecryption(shares, threshold=threshold)
    lsag = LSAG()

    # ── Step 5: Federated Training Loop ──
    log.info(f"Starting federated training: {num_rounds} rounds, {local_epochs} local epochs, lr={lr}")
    print()

    global_params = None
    accuracy_history = []
    loss_history = []

    # Select which parties participate in threshold decryption
    party_indices = list(range(0, num_parties, num_parties // threshold))[:threshold]

    for round_num in range(1, num_rounds + 1):
        print(f"\n{'-' * 70}")
        print(f"  ROUND {round_num}/{num_rounds}")
        print(f"{'-' * 70}")

        enc_updates = []
        signatures = []
        round_losses = []

        for client in clients:
            log.info(f"[Client {client.client_id}] Local training ({local_epochs} epochs)...")
            client.train(global_params)

            local_acc = client.get_local_accuracy()
            local_loss = client.get_local_loss()
            round_losses.append(local_loss)
            log.info(f"[Client {client.client_id}] Training complete - accuracy: {local_acc:.4f}, loss: {local_loss:.4f}")

            enc = client.encrypt_update(server_pub)
            enc_updates.append(enc)
            log.info(f"[Client {client.client_id}] Update encrypted")

            sig = client.sign_update(enc, all_pub_keys)
            signatures.append(sig)
            log.info(f"[Client {client.client_id}] Signed anonymously (LSAG ring signature)")

        print()
        log.info("Server: Verifying signatures and performing threshold decryption...")
        log_threshold.info(f"Parties {party_indices} contributing to threshold decryption")

        coordinator = FederatedCoordinator(threshold_dec, lsag, num_clients)
        global_params = coordinator.aggregate_round(enc_updates, signatures, party_indices)
        log_threshold.info("Reconstruction successful")

        # ── Evaluate Global Model ──
        global_model = FederatedLogisticRegression(learning_rate=lr, max_iter=local_epochs)
        global_model.set_parameters(global_params)

        y_pred = global_model.predict(X_test)
        y_proba = global_model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)
        avg_loss = float(np.mean(round_losses))

        accuracy_history.append(acc)
        loss_history.append(avg_loss)

        print()
        log.info(f"[Round {round_num}] Global Accuracy: {acc:.4f} | AUC: {auc:.4f} | Avg Loss: {avg_loss:.4f}")

    # ── Final Evaluation ──
    print(f"\n{'=' * 70}")
    print("  FINAL GLOBAL MODEL EVALUATION")
    print(f"{'=' * 70}\n")

    final_pred = global_model.predict(X_test)
    final_proba = global_model.predict_proba(X_test)[:, 1]

    final_acc = accuracy_score(y_test, final_pred)
    final_auc = roc_auc_score(y_test, final_proba)

    print(f"  Final Accuracy:  {final_acc:.4f}")
    print(f"  Final AUC:       {final_auc:.4f}")
    print(f"\n  Classification Report:")
    report = classification_report(y_test, final_pred)
    print(report)
    print(f"  Confusion Matrix:")
    print(f"    {confusion_matrix(y_test, final_pred)}")

    # ── Visualization ──
    output_dir = os.path.join(PROJECT_ROOT, "outputs")
    acc_plot, loss_plot = plot_metrics(accuracy_history, loss_history, output_dir)
    log.info(f"Plots saved to {output_dir}/")

    # ── Summary ──
    print(f"\n{'=' * 70}")
    print("  SECURITY SUMMARY")
    print(f"{'=' * 70}")
    print(f"  [+] ECIES encryption (secp256k1 + AES-GCM + PBKDF2)")
    print(f"  [+] Anonymous authentication via LSAG ring signatures")
    print(f"  [+] Dealerless threshold decryption ({threshold}/{num_parties} parties)")
    print(f"  [+] Replay attack prevention")
    print(f"  [+] Constant-time signature verification")
    print(f"  [+] {num_rounds} rounds x {local_epochs} local epochs completed")
    print(f"  >>> Final Accuracy: {final_acc:.4f}")
    print(f"  >>> Final AUC:      {final_auc:.4f}")
    print()

    return {
        "accuracy_history": accuracy_history,
        "loss_history": loss_history,
        "final_accuracy": final_acc,
        "final_auc": final_auc,
        "global_params": global_params,
    }


if __name__ == "__main__":
    run_simulation()
