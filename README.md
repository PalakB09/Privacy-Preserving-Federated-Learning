# 🔐 Privacy-Preserving Federated Learning with Threshold Cryptography

A production-grade research prototype implementing **privacy-preserving federated learning** that combines **threshold cryptography**, **ECIES encryption**, and **LSAG ring signatures** to ensure data confidentiality, anonymous authentication, and secure model aggregation.

---

## 📋 Problem Statement

Federated learning enables collaborative model training without sharing raw data. However, standard FL remains vulnerable to:

- **Model update inference attacks** — an honest-but-curious server can extract information from plaintext gradients
- **Identity tracking** — the server can correlate updates to specific clients across rounds
- **Single point of failure** — if the server's decryption key is compromised, all updates are exposed

This project addresses all three threats simultaneously through a layered cryptographic architecture.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FEDERATED LEARNING LAYER                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Client 0 │  │ Client 1 │  │ Client 2 │   Local Training      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │              │              │                            │
│       ▼              ▼              ▼                            │
│  ┌─────────────────────────────────────────┐                    │
│  │          ECIES ENCRYPTION               │                    │
│  │  secp256k1 ECDH + AES-GCM + PBKDF2     │                    │
│  └─────────────────────────────────────────┘                    │
│       │              │              │                            │
│       ▼              ▼              ▼                            │
│  ┌─────────────────────────────────────────┐                    │
│  │      LSAG RING SIGNATURES              │                    │
│  │  Anonymous authentication + linkability  │                    │
│  └─────────────────────────────────────────┘                    │
│       │              │              │                            │
│       ▼              ▼              ▼                            │
│  ┌─────────────────────────────────────────┐                    │
│  │       COORDINATOR (SERVER)              │                    │
│  │  Signature verify → Threshold decrypt   │                    │
│  │  → Federated averaging                  │                    │
│  └─────────────────┬───────────────────────┘                    │
│                    │                                             │
│       ┌────────────┼────────────┐                               │
│       ▼            ▼            ▼                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │
│  │ Party 0 │ │ Party 2 │ │ Party 4 │  Threshold Decryption     │
│  │ (share) │ │ (share) │ │ (share) │  (t-of-n parties)         │
│  └─────────┘ └─────────┘ └─────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
threshold-fl/
│
├── crypto/                    # Cryptographic primitives
│   ├── secp256k1.py           # Elliptic curve point operations
│   ├── threshold.py           # Dealerless DKG + threshold decryption
│   ├── encryption.py          # ECIES encrypt/decrypt (AES-GCM + PBKDF2)
│   └── lsag.py                # LSAG ring signature (sign + verify)
│
├── federated/                 # Federated learning components
│   ├── model.py               # Logistic regression (from scratch)
│   ├── client.py              # FL client: train, encrypt, sign
│   └── coordinator.py         # Server: verify, decrypt, aggregate
│
├── data/
│   └── dataset_loader.py      # Dataset loading + client partitioning
│
├── scripts/
│   ├── run_simulation.py      # Main simulation orchestration
│   └── visualize.py           # Matplotlib plotting utilities
│
├── demo/
│   └── app.py                 # Streamlit interactive dashboard
│
├── config/
│   └── config.yaml            # Simulation parameters
│
├── utils/
│   └── logger.py              # Timestamped color-coded logger
│
├── outputs/                   # Generated plots (auto-created)
├── requirements.txt
└── README.md
```

---

## 🔧 Module Breakdown

### Crypto Layer

| Module | Description |
|--------|-------------|
| `secp256k1.py` | Custom secp256k1 curve implementation: point addition, scalar multiplication, hash-to-point, key generation |
| `threshold.py` | Dealerless distributed key generation (Pedersen-style) with Shamir sharing and Lagrange interpolation in the exponent |
| `encryption.py` | ECIES-style hybrid encryption: ephemeral ECDH → PBKDF2 → AES-256-GCM |
| `lsag.py` | Linkable Spontaneous Anonymous Group signatures with constant-time verification |

### Federated Layer

| Module | Description |
|--------|-------------|
| `model.py` | Binary logistic regression with L2 regularization, gradient descent, and loss tracking |
| `client.py` | Encapsulates local training, weight encryption, and anonymous signing per participant |
| `coordinator.py` | Server-side: signature verification, replay prevention, threshold decryption, federated averaging |

---

## 🚀 How to Run

### 1. Setup Virtual Environment

```bash
cd threshold-fl
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Place Dataset

Ensure `filtered_diabetes_data (2).csv` is in the `threshold-fl/` directory (or update the path in `config/config.yaml`).

### 4. Run Simulation (CLI)

```bash
python scripts/run_simulation.py
```

### 5. Launch Streamlit Demo

```bash
streamlit run demo/app.py
```

---

## ⚙️ Configuration

Edit `config/config.yaml`:

```yaml
num_clients: 3        # Number of federated learning clients
num_parties: 5        # Number of threshold decryption parties
threshold: 3          # Minimum parties needed to decrypt (t-of-n)
rounds: 2             # Number of federated training rounds
learning_rate: 0.1    # Gradient descent learning rate
local_epochs: 10      # Training epochs per client per round
random_seed: 42       # For reproducibility
test_size: 0.2        # Train/test split ratio
dataset_path: "filtered_diabetes_data (2).csv"
```

---

## 📊 Sample Output

```
======================================================================
  PRIVACY-PRESERVING FEDERATED LEARNING WITH THRESHOLD CRYPTOGRAPHY
======================================================================

[11:23:45] [Main] Running dealerless distributed key generation...
[11:23:45] [Main] Dealerless key generation complete (no party knows full private key)
[11:23:45] [Main] Parties [0, 1, 2, 3, 4] hold shares
[11:23:45] [Main] Any 3 parties can collaborate to decrypt

[11:23:46] [Main] 3 client secp256k1 keypairs generated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ROUND 1/2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[11:23:46] [Main] [Client 0] Local training (10 epochs)...
[11:23:46] [Main] [Client 0] Training complete — accuracy: 0.8542, loss: 0.4523
[11:23:47] [Main] [Client 0] Update encrypted
[11:23:48] [Main] [Client 0] Signed anonymously (LSAG ring signature)

[11:23:49] [Server] Anonymous update 0: signature valid ✓
[11:23:49] [Threshold] Parties [0, 2, 4] contributing to threshold decryption
[11:23:50] [Threshold] Reconstruction successful ✓

[11:23:50] [Server] Aggregation complete — 3 valid updates averaged
[11:23:50] [Main] [Round 1] Global Accuracy: 0.8400 | AUC: 0.8912

======================================================================
  SECURITY SUMMARY
======================================================================
  ✅ ECIES encryption (secp256k1 + AES-GCM + PBKDF2)
  ✅ Anonymous authentication via LSAG ring signatures
  ✅ Dealerless threshold decryption (3/5 parties)
  ✅ Replay attack prevention
  ✅ Constant-time signature verification
  🎯 Final Accuracy: 0.8456
  🎯 Final AUC: 0.9023
```

---

## 🛡️ Security Properties

| Property | Mechanism |
|----------|-----------|
| **Data Confidentiality** | ECIES hybrid encryption (secp256k1 ECDH + AES-GCM) |
| **Key Derivation** | PBKDF2 with random salt (100,000 iterations) |
| **Distributed Trust** | Dealerless threshold key generation — no trusted dealer |
| **Anonymous Auth** | LSAG ring signatures hide signer identity |
| **Linkability** | Key images detect double-signing / replay attacks |
| **Timing Safety** | Constant-time signature comparison via `secrets.compare_digest` |

---

## 📚 Academic References

1. Pedersen, T.P. "A Threshold Cryptosystem without a Trusted Party." *EUROCRYPT 1991*.
2. Liu, J.K., Wei, V.K., Wong, D.S. "Linkable Spontaneous Anonymous Group Signature for Ad Hoc Groups." *ACISP 2004*.
3. McMahan, H.B., et al. "Communication-Efficient Learning of Deep Networks from Decentralized Data." *AISTATS 2017*.
4. Bonawitz, K., et al. "Practical Secure Aggregation for Privacy-Preserving Machine Learning." *CCS 2017*.

---

## 📄 License

Research prototype — for academic use.
