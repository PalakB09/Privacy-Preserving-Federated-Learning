"""
Visualization Utilities

Generates publication-quality plots for federated learning metrics
(accuracy and loss vs. training rounds) and saves them to the outputs directory.
"""

import os
from typing import List

import matplotlib.pyplot as plt


def plot_metrics(
    accuracies: List[float],
    losses: List[float],
    output_dir: str = "outputs",
) -> None:
    """
    Generate and save accuracy-vs-rounds and loss-vs-rounds plots.

    Args:
        accuracies: list of global model accuracy per round
        losses: list of average client loss per round
        output_dir: directory to save PNG plots
    """
    os.makedirs(output_dir, exist_ok=True)
    rounds = list(range(1, len(accuracies) + 1))

    plt.style.use("seaborn-v0_8-darkgrid")

    # --- Accuracy Plot ---
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        rounds, accuracies,
        marker="o", linewidth=2.5, markersize=8,
        color="#00b4d8", markerfacecolor="#0077b6",
    )
    ax.set_xlabel("Federated Round", fontsize=13)
    ax.set_ylabel("Global Accuracy", fontsize=13)
    ax.set_title("Federated Learning — Accuracy vs. Round", fontsize=15, fontweight="bold")
    ax.set_xticks(rounds)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    acc_path = os.path.join(output_dir, "accuracy_vs_rounds.png")
    fig.savefig(acc_path, dpi=150)
    plt.close(fig)

    # --- Loss Plot ---
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        rounds, losses,
        marker="s", linewidth=2.5, markersize=8,
        color="#e63946", markerfacecolor="#a4133c",
    )
    ax.set_xlabel("Federated Round", fontsize=13)
    ax.set_ylabel("Average Client Loss", fontsize=13)
    ax.set_title("Federated Learning — Loss vs. Round", fontsize=15, fontweight="bold")
    ax.set_xticks(rounds)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    loss_path = os.path.join(output_dir, "loss_vs_rounds.png")
    fig.savefig(loss_path, dpi=150)
    plt.close(fig)

    return acc_path, loss_path
