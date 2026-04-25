"""
Streamlit Demo UI - Privacy-Preserving Federated Learning
Step-by-step animated execution with interactive visualization.
"""

import os, sys, io, contextlib, warnings, json, time
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
warnings.filterwarnings("ignore")

from crypto.secp256k1 import generate_keypair
from crypto.threshold import ThresholdDecryption, dealerless_keygen
from crypto.lsag import LSAG
from data.dataset_loader import load_dataset
from federated.client import FederatedClient
from federated.coordinator import FederatedCoordinator
from federated.model import FederatedLogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score

from demo.styles import MAIN_CSS
from demo.renderers import (
    render_stepper, render_step_info, render_clients_training,
    render_encrypted_updates, render_ring_signatures, render_threshold_parties,
    render_aggregation, render_server_verification, render_round_progress,
    render_metric_card, render_math_panel, STEPS,
)

st.set_page_config(page_title="Threshold-FL Demo", page_icon="", layout="wide", initial_sidebar_state="expanded")
st.markdown(MAIN_CSS, unsafe_allow_html=True)


# ── Session State Defaults ──
DEFAULTS = {
    "mode": "step", "current_step": -1, "current_round": 1, "current_client": 0, "round_precomputed": False,
    "sim_initialized": False, "sim_complete": False, "auto_running": False,
    "logs": [], "accuracy_history": [], "loss_history": [], "auc_history": [],
    "global_params": None, "enc_updates": [], "signatures": [],
    "client_progress": {}, "client_statuses": {}, "enc_previews": [],
    "sig_statuses": {}, "verify_results": [], "threshold_status": "",
    "agg_done": False, "round_losses": [],
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)(v)


def add_log(msg):
    st.session_state.logs.append(msg)


def get_config():
    return {
        "num_clients": st.session_state.get("p_clients", 3),
        "num_parties": st.session_state.get("p_parties", 5),
        "threshold": st.session_state.get("p_threshold", 3),
        "rounds": st.session_state.get("p_rounds", 2),
        "learning_rate": st.session_state.get("p_lr", 0.1),
        "local_epochs": st.session_state.get("p_epochs", 10),
        "random_seed": 42, "test_size": 0.2,
        "dataset_path": "filtered_diabetes_data (2).csv",
    }


def init_simulation():
    """Initialize crypto keys, dataset, and clients."""
    cfg = get_config()
    np.random.seed(cfg["random_seed"])
    add_log("[SYSTEM] Simulation initialized")

    shares, server_pub = dealerless_keygen(cfg["num_parties"], cfg["threshold"])
    add_log(f"[THRESHOLD] Dealerless key generation complete")

    keypairs = [generate_keypair() for _ in range(cfg["num_clients"])]
    all_pubs = [kp[1] for kp in keypairs]
    add_log(f"[SETUP] {cfg['num_clients']} client keypairs generated")

    client_data, X_test, y_test, _ = load_dataset(cfg)
    add_log(f"[DATA] Dataset loaded - {len(y_test)} test samples")

    clients = []
    for cid in range(cfg["num_clients"]):
        X_c, y_c = client_data[cid]
        clients.append(FederatedClient(
            client_id=cid, X_train=X_c, y_train=y_c, keypair=keypairs[cid],
            learning_rate=cfg["learning_rate"], local_epochs=cfg["local_epochs"],
        ))

    threshold_dec = ThresholdDecryption(shares, threshold=cfg["threshold"])
    party_indices = list(range(0, cfg["num_parties"], max(1, cfg["num_parties"] // cfg["threshold"])))[:cfg["threshold"]]

    st.session_state.sim_data = {
        "clients": clients, "server_pub": server_pub, "all_pubs": all_pubs,
        "threshold_dec": threshold_dec, "lsag": LSAG(),
        "party_indices": party_indices, "cfg": cfg,
        "X_test": X_test, "y_test": y_test,
    }
    st.session_state.sim_initialized = True
    st.session_state.current_step = 0
    st.session_state.current_round = 1
    st.session_state.current_client = 0
    st.session_state.round_precomputed = False
    add_log(f"[CONFIG] Clients: {cfg['num_clients']} | Parties: {cfg['num_parties']} | Threshold: {cfg['threshold']}")
    add_log(f"[ROUND 1] Starting round 1")


def reset_round_state():
    for k in ["enc_updates", "signatures", "enc_previews", "verify_results", "round_losses"]:
        st.session_state[k] = []
    st.session_state.client_progress = {}
    st.session_state.client_statuses = {}
    st.session_state.sig_statuses = {}
    st.session_state.threshold_status = ""
    st.session_state.agg_done = False


def precompute_round():
    sd = st.session_state.sim_data
    clients = sd["clients"]
    cfg = sd["cfg"]
    nc = cfg["num_clients"]
    lsag = sd["lsag"]
    td = sd["threshold_dec"]
    pi = sd["party_indices"]

    add_log(f"[SYSTEM] Precomputing round {st.session_state.current_round} mathematics...")
    
    losses, progress, statuses = [], {}, {}
    for c in clients:
        c.train(st.session_state.global_params)
        losses.append(c.get_local_loss())
        progress[c.client_id] = 100
        statuses[c.client_id] = f"{c.get_local_accuracy():.2%}"
    
    enc_updates = [c.encrypt_update(sd["server_pub"]) for c in clients]
    enc_previews = [(c.client_id, enc["ciphertext"][:20] + "...") for c, enc in zip(clients, enc_updates)]

    signatures = [c.sign_update(enc_updates[c.client_id], sd["all_pubs"]) for c in clients]
    sig_statuses = {c.client_id: "signed" for c in clients}

    verify_results = [(cid, lsag.verify(signatures[cid], json.dumps(enc_updates[cid], sort_keys=True).encode())) for cid in range(nc)]

    decrypted = [td.combine_and_decrypt(enc_updates[cid], [td.get_partial_decryption(enc_updates[cid], pidx) for pidx in pi]) for cid in range(nc)]

    agg = np.mean(decrypted, axis=0)

    gm = FederatedLogisticRegression(learning_rate=cfg["learning_rate"], max_iter=cfg["local_epochs"])
    gm.set_parameters(agg)
    acc, auc = accuracy_score(sd["y_test"], gm.predict(sd["X_test"])), roc_auc_score(sd["y_test"], gm.predict_proba(sd["X_test"])[:, 1])
    
    st.session_state.sim_data["precomputed"] = {
        "losses": losses, "progress": progress, "statuses": statuses,
        "enc_updates": enc_updates, "enc_previews": enc_previews,
        "signatures": signatures, "sig_statuses": sig_statuses,
        "verify_results": verify_results, "decrypted": decrypted,
        "agg": agg, "acc": acc, "auc": auc, "avg_loss": float(np.mean(losses))
    }
    st.session_state.round_precomputed = True
    add_log(f"[SYSTEM] Precomputation complete.")


def advance_step():
    step = st.session_state.current_step
    cid = st.session_state.current_client
    if step < 0 or st.session_state.sim_complete: return
    
    if not st.session_state.get("round_precomputed", False):
        precompute_round()
        return
    
    sd = st.session_state.sim_data
    pc = sd["precomputed"]
    nc = sd["cfg"]["num_clients"]
    pi = sd["party_indices"]
    
    client_steps = [0, 1, 2, 3, 4, 5]
    is_auto = st.session_state.auto_running
    
    def reveal_client(s, c):
        if s == 0:
            st.session_state.client_progress[c] = pc["progress"][c]
            st.session_state.client_statuses[c] = pc["statuses"][c]
            if c == 0: st.session_state.round_losses = pc["losses"]
            add_log(f"[CLIENT {c}] Training complete - acc: {pc['statuses'][c]}")
        elif s == 1:
            if c == 0: st.session_state.enc_updates, st.session_state.enc_previews = [], []
            st.session_state.enc_updates.append(pc["enc_updates"][c])
            st.session_state.enc_previews.append(pc["enc_previews"][c])
            add_log(f"[CLIENT {c}] Update encrypted")
        elif s == 2:
            if c == 0: st.session_state.signatures = []
            st.session_state.signatures.append(pc["signatures"][c])
            st.session_state.sig_statuses[c] = "signed"
            add_log(f"[CLIENT {c}] Signed anonymously")
        elif s == 3:
            add_log(f"[NETWORK] Client {c} -> Server [OK]")
        elif s == 4:
            if c == 0: st.session_state.verify_results = []
            st.session_state.verify_results.append(pc["verify_results"][c])
            valid = pc["verify_results"][c][1]
            add_log(f"[SERVER] Update {c}: signature {'valid' if valid else 'INVALID'}")
        elif s == 5:
            if c == 0: add_log(f"[THRESHOLD] Parties {pi} contributing partial decryptions")
            add_log(f"[THRESHOLD] Decrypted update from Client {c}")
            if c == nc - 1:
                st.session_state._decrypted_updates = pc["decrypted"]
                st.session_state.threshold_status = "Reconstruction successful"

    def reveal_global(s):
        if s == 6:
            st.session_state.global_params = pc["agg"]
            st.session_state.agg_done = True
            add_log(f"[SERVER] Aggregation complete - {nc} updates averaged")
        elif s == 7:
            acc, auc, avg_loss = pc["acc"], pc["auc"], pc["avg_loss"]
            st.session_state.accuracy_history.append(acc)
            st.session_state.loss_history.append(avg_loss)
            st.session_state.auc_history.append(auc)
            rnd = st.session_state.current_round
            add_log(f"[ROUND {rnd}] Accuracy: {acc:.4f} | AUC: {auc:.4f} | Loss: {avg_loss:.4f}")
            if rnd < sd["cfg"]["rounds"]:
                st.session_state.current_round += 1
                st.session_state.current_step = 0
                st.session_state.current_client = 0
                st.session_state.round_precomputed = False
                reset_round_state()
                add_log(f"[ROUND {rnd + 1}] Starting round {rnd + 1}")
            else:
                st.session_state.sim_complete = True
                add_log(f"[SYSTEM] Simulation complete!")

    if step in client_steps:
        if is_auto:
            reveal_client(step, cid)
            st.session_state.current_client += 1
            if st.session_state.current_client >= nc:
                st.session_state.current_client = 0
                st.session_state.current_step += 1
        else:
            for i in range(nc):
                reveal_client(step, i)
            st.session_state.current_step += 1
    else:
        reveal_global(step)
        if not st.session_state.sim_complete and st.session_state.current_step != 0:
            st.session_state.current_step += 1


def reset_simulation():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)(v)
    if "sim_data" in st.session_state:
        del st.session_state.sim_data
    if "_decrypted_updates" in st.session_state:
        del st.session_state._decrypted_updates


def make_chart(data, color, marker, ylabel, title):
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")
    rounds = list(range(1, len(data) + 1))
    ax.plot(rounds, data, marker=marker, linewidth=2.5, markersize=7,
            color=color, markerfacecolor=color)
    ax.set_xlabel("Round", color="white", fontsize=10)
    ax.set_ylabel(ylabel, color="white", fontsize=10)
    ax.set_title(title, color="white", fontsize=11, fontweight="bold")
    if data:
        max_r = max(len(data), 2)
        ax.set_xticks(range(1, max_r + 1))
    ax.tick_params(colors="white", labelsize=8)
    ax.grid(True, alpha=0.15, color="white")
    for spine in ax.spines.values():
        spine.set_color("#21262d")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════
# MAIN UI
# ═══════════════════════════════════════════════

def main():
    # Header
    st.markdown(
        '<div class="main-header">'
        '<h1>Privacy-Preserving Federated Learning</h1>'
        '<p>Threshold Cryptography &middot; LSAG Ring Signatures &middot; Secure Aggregation</p>'
        '</div>', unsafe_allow_html=True,
    )

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### Simulation Parameters")
        st.session_state.p_clients = st.slider("Number of Clients", 2, 10, 3, key="sl_c")
        st.session_state.p_parties = st.slider("Number of Threshold Parties", 3, 10, 5, key="sl_p")
        max_t = st.session_state.p_parties
        st.session_state.p_threshold = st.slider("Threshold (t)", 2, max_t, min(3, max_t), key="sl_t")
        st.session_state.p_rounds = st.slider("Federated Rounds", 1, 10, 2, key="sl_r")
        st.session_state.p_epochs = st.slider("Local Epochs per Round", 1, 50, 10, key="sl_e")
        st.session_state.p_lr = st.select_slider("Learning Rate", [0.001, 0.01, 0.05, 0.1, 0.5], 0.1, key="sl_lr")

        st.markdown("---")
        st.markdown("### Animation & Execution")
        mode = st.radio("Execution Mode", ["Step-by-Step", "Auto Run"], horizontal=True, key="mode_radio")
        st.session_state.mode = "step" if mode == "Step-by-Step" else "auto"

        if st.session_state.mode == "auto":
            st.selectbox("Animation Speed", ["Slow", "Normal", "Fast"], index=1, key="speed_sel")

        st.markdown("---")

        # Action buttons
        if not st.session_state.sim_initialized:
            if st.button("Start Simulation", width="stretch", key="btn_start"):
                init_simulation()
                if st.session_state.mode == "auto":
                    st.session_state.auto_running = True
                st.rerun()
        else:
            if st.session_state.mode == "step" and not st.session_state.sim_complete:
                if st.button("Next Step", width="stretch", key="btn_next"):
                    advance_step()
                    st.rerun()
            elif st.session_state.mode == "auto" and not st.session_state.sim_complete:
                if st.button("Run All Steps", width="stretch", key="btn_auto"):
                    st.session_state.auto_running = True
                    st.rerun()

        if st.session_state.sim_initialized:
            if st.button("Reset Simulation", width="stretch", key="btn_reset"):
                reset_simulation()
                st.rerun()

        st.markdown("---")
        st.markdown("### Dataset")
        ds_status = "Loaded" if st.session_state.sim_initialized else "Not loaded"
        ds_color = "#3fb950" if st.session_state.sim_initialized else "#484f58"
        st.markdown(f'<span style="color:{ds_color};font-weight:600;">{ds_status}</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Security Features")
        for b in ["ECIES", "AES-GCM", "PBKDF2", "LSAG Ring Sig", "Threshold", "Replay Prevention"]:
            st.markdown(f'<span class="security-badge">{b}</span>', unsafe_allow_html=True)



    # ── Main Content ──
    if not st.session_state.sim_initialized:
        render_welcome()
        return

    cfg = get_config()
    step = st.session_state.current_step
    rnd = st.session_state.current_round
    total_rounds = cfg["rounds"]

    # Stepper
    render_stepper(step)
    if not st.session_state.sim_complete:
        render_step_info(step)

    # ── Visualization Grid ──
    viz_col1, viz_col2, viz_col3, viz_col4 = st.columns([2, 2, 2, 2])

    is_auto = st.session_state.auto_running
    active_c = st.session_state.current_client if is_auto else -1

    with viz_col1:
        st.markdown(
            render_clients_training(
                cfg["num_clients"],
                st.session_state.client_progress,
                st.session_state.client_statuses,
                active_client=active_c if step == 0 else -1
            ), unsafe_allow_html=True,
        )

    with viz_col2:
        st.markdown(
            render_encrypted_updates(
                cfg["num_clients"],
                st.session_state.enc_previews,
                active_client=active_c if step == 1 else -1
            ), unsafe_allow_html=True,
        )

    with viz_col3:
        st.markdown(
            render_ring_signatures(
                cfg["num_clients"], 
                st.session_state.sig_statuses,
                active_client=active_c if step == 2 else -1
            ), unsafe_allow_html=True,
        )

    with viz_col4:
        st.markdown(
            render_threshold_parties(
                cfg["num_parties"], cfg["threshold"],
                st.session_state.sim_data["party_indices"] if "sim_data" in st.session_state else [],
                st.session_state.threshold_status,
                active_client=active_c if step == 5 else -1
            ), unsafe_allow_html=True,
        )

    # ── Server + Aggregation row ──
    srv_col, agg_col = st.columns([1, 1])
    with srv_col:
        st.markdown(
            render_server_verification(
                cfg["num_clients"],
                st.session_state.verify_results,
                active_client=active_c if step == 4 else -1
            ), unsafe_allow_html=True,
        )
    with agg_col:
        st.markdown(render_aggregation(st.session_state.agg_done), unsafe_allow_html=True)

    # ── Progress + Round Info ──
    p_col1, p_col2 = st.columns([3, 1])
    with p_col1:
        st.markdown("**Round Progress**")
        st.markdown(render_round_progress(rnd, total_rounds), unsafe_allow_html=True)
    with p_col2:
        st.markdown(f"**Current Round:** {rnd} / {total_rounds}")

    st.markdown("---")

    # ── Math Panel ──
    if st.session_state.get("round_precomputed", False):
        pc = st.session_state.sim_data.get("precomputed") if "sim_data" in st.session_state else None
        is_auto = st.session_state.auto_running
        focused_c = st.session_state.current_client if is_auto else max(0, min(
            st.session_state.client_progress.__len__() - 1, 0))
        # In step mode show the last completed client
        if not is_auto and st.session_state.client_statuses:
            focused_c = max(st.session_state.client_statuses.keys())
        st.markdown(
            render_math_panel(
                step=step,
                pc=pc,
                focused_client=focused_c,
                num_clients=cfg["num_clients"],
                party_indices=st.session_state.sim_data.get("party_indices", []) if "sim_data" in st.session_state else [],
                cfg=cfg,
            ), unsafe_allow_html=True,
        )
    else:
        st.markdown(
            render_math_panel(step=step, pc=None, focused_client=0,
                              num_clients=cfg["num_clients"], party_indices=[], cfg=cfg),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Bottom: Log + Metrics + Chart ──
    bottom_col1, bottom_col2, bottom_col3 = st.columns([2, 1.5, 2.5])

    with bottom_col1:
        st.markdown("#### Live Simulation Log")
        log_text = "\n".join(reversed(st.session_state.logs))
        st.markdown(f'<div style="max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; background: #0d1117; color: #c9d1d9; padding: 10px; border-radius: 5px; border: 1px solid #30363d;">{log_text if log_text else "Waiting..."}</div>', unsafe_allow_html=True)

    with bottom_col2:
        st.markdown("#### Performance Metrics")
        if st.session_state.accuracy_history:
            latest_acc = st.session_state.accuracy_history[-1]
            latest_auc = st.session_state.auc_history[-1]
            latest_loss = st.session_state.loss_history[-1]
            delta_acc = ""
            if len(st.session_state.accuracy_history) > 1:
                d = latest_acc - st.session_state.accuracy_history[-2]
                delta_acc = f"+{d:.4f}" if d >= 0 else f"{d:.4f}"
            st.markdown(render_metric_card("Accuracy", f"{latest_acc:.4f}", delta_acc), unsafe_allow_html=True)
            st.markdown(render_metric_card("AUC Score", f"{latest_auc:.4f}"), unsafe_allow_html=True)
            st.markdown(render_metric_card("Loss", f"{latest_loss:.4f}"), unsafe_allow_html=True)
        else:
            st.markdown(render_metric_card("Accuracy", "-"), unsafe_allow_html=True)
            st.markdown(render_metric_card("AUC Score", "-"), unsafe_allow_html=True)
            st.markdown(render_metric_card("Loss", "-"), unsafe_allow_html=True)

    with bottom_col3:
        st.markdown("#### Accuracy Over Rounds")
        if st.session_state.accuracy_history:
            img_buf = make_chart(st.session_state.accuracy_history, "#00b4d8", "o", "Accuracy", "")
            st.image(img_buf, use_container_width=True)
        else:
            st.markdown('<div class="viz-panel" style="text-align:center;color:#484f58;padding:2rem;">Chart will appear after first round completes</div>', unsafe_allow_html=True)

    # ── Status Bar ──
    nc = cfg["num_clients"]
    np_ = cfg["num_parties"]
    t = cfg["threshold"]
    enc_ok = len(st.session_state.enc_previews) > 0
    sig_ok = len(st.session_state.sig_statuses) > 0
    thr_ok = bool(st.session_state.threshold_status)
    agg_ok = st.session_state.agg_done

    def dot(ok):
        return '<span class="status-dot dot-green"></span>' if ok else '<span class="status-dot dot-yellow"></span>'

    status_html = (
        f'<div class="status-bar">'
        f'<span>Encryption: {dot(enc_ok)}</span>'
        f'<span>Signatures: {dot(sig_ok)}</span>'
        f'<span>Threshold: {dot(thr_ok)}</span>'
        f'<span>Aggregation: {dot(agg_ok)}</span>'
        f'<span style="margin-left:auto;">Clients: {nc} | Parties: {np_}/{t}</span>'
        f'</div>'
    )
    st.markdown(status_html, unsafe_allow_html=True)

    # ── Completion Summary ──
    if st.session_state.sim_complete:
        st.markdown("---")
        st.success("Simulation Complete!")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(render_metric_card("Final Accuracy", f"{st.session_state.accuracy_history[-1]:.4f}"), unsafe_allow_html=True)
        with sc2:
            st.markdown(render_metric_card("Final AUC", f"{st.session_state.auc_history[-1]:.4f}"), unsafe_allow_html=True)
        with sc3:
            st.markdown(render_metric_card("Rounds", str(total_rounds)), unsafe_allow_html=True)
        with sc4:
            st.markdown(render_metric_card("Clients", str(nc)), unsafe_allow_html=True)

        ch1, ch2 = st.columns(2)
        with ch1:
            img_buf = make_chart(st.session_state.accuracy_history, "#00b4d8", "o", "Accuracy", "Accuracy vs. Round")
            st.image(img_buf, use_container_width=True)
        with ch2:
            img_buf = make_chart(st.session_state.loss_history, "#e63946", "s", "Avg Loss", "Loss vs. Round")
            st.image(img_buf, use_container_width=True)

        st.markdown("#### Participation Summary")
        rounds_list = list(range(1, total_rounds + 1))
        pi = st.session_state.sim_data["party_indices"]
        df = pd.DataFrame({
            "Round": [f"Round {r}" for r in rounds_list],
            "Clients": [nc] * total_rounds,
            "Threshold": [f"{t}/{np_}"] * total_rounds,
            "Parties": [str(pi)] * total_rounds,
            "Accuracy": [f"{a:.4f}" for a in st.session_state.accuracy_history],
            "Loss": [f"{l:.4f}" for l in st.session_state.loss_history],
        })
        st.dataframe(df, width="stretch")
    

    # ── Auto-run loop ──
    if st.session_state.auto_running and not st.session_state.sim_complete:
        speed_map = {"Slow": 1.0, "Normal": 0.3, "Fast": 0.05}
        delay = speed_map.get(st.session_state.get("speed_sel", "Normal"), 0.3)
        time.sleep(delay)
        advance_step()
        st.rerun()


def render_welcome():
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Threshold Cryptography\nDealerless DKG ensures no single party holds the full key. Decryption requires *t* of *n* parties.")
    with c2:
        st.markdown("#### Anonymous Authentication\nLSAG ring signatures prove membership without revealing identity. Key images enable replay detection.")
    with c3:
        st.markdown("#### Federated Learning\nLogistic regression trained across distributed clients. Only encrypted updates leave each device.")
    st.markdown("---")
    st.info("Configure parameters in the sidebar and click **Start Simulation** to begin.")


if __name__ == "__main__":
    main()
