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
    render_metrics_grid, render_bottom_status, render_math_panel, STEPS,
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
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    rounds = list(range(1, len(data) + 1))
    ax.plot(rounds, data, marker=marker, linewidth=2.5, markersize=7,
            color=color, markerfacecolor=color)
    ax.set_xlabel("Round", color="#64748b", fontsize=10)
    ax.set_ylabel(ylabel, color="#64748b", fontsize=10)
    if title:
        ax.set_title(title, color="#0f172a", fontsize=11, fontweight="bold")
    if data:
        max_r = max(len(data), 2)
        ax.set_xticks(range(1, max_r + 1))
    ax.tick_params(colors="#64748b", labelsize=8)
    ax.grid(True, alpha=0.15, color="#64748b")
    for spine in ax.spines.values():
        spine.set_color("#e5e7eb")
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
    # ── Top Header ──
    st.markdown(
        '<div class="top-header">'
        '<div class="header-title-container">'
        '<h1><span style="color:var(--color-warning); font-size:1.8rem;">&#x1F512;</span> Privacy-Preserving Federated Learning</h1>'
        '<p>Threshold Cryptography &middot; LSAG Ring Signatures &middot; Secure Aggregation</p>'
        '</div>'
        '</div>', unsafe_allow_html=True
    )

    # ── Sidebar ──
    with st.sidebar:
        st.markdown('<div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem;"><span style="color:var(--color-primary); font-size:1.5rem;">&#x2699;</span> <span style="font-weight:600;">Simulation Parameters</span></div>', unsafe_allow_html=True)
        st.session_state.p_clients = st.slider("Number of Clients", 2, 10, 5, key="sl_c")
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

    # ── Pipeline Visualization (Unified Row) ──
    is_auto = st.session_state.auto_running
    active_c = st.session_state.current_client if is_auto else -1

    pipeline_html = f"""
    <div class="pipeline-container">
        {render_clients_training(cfg["num_clients"], st.session_state.client_progress, st.session_state.client_statuses, active_c if step == 0 else -1)}
        <div class="flow-arrow">&#x279C;</div>
        {render_encrypted_updates(cfg["num_clients"], st.session_state.enc_previews, active_c if step == 1 else -1)}
        <div class="flow-arrow">&#x279C;</div>
        {render_ring_signatures(cfg["num_clients"], st.session_state.sig_statuses, active_c if step == 2 else -1)}
        <div class="flow-arrow">&#x279C;</div>
        {render_server_verification(cfg["num_clients"], st.session_state.verify_results, active_c if step == 4 else -1)}
        <div class="flow-arrow">&#x279C;</div>
        {render_threshold_parties(cfg["num_parties"], cfg["threshold"], st.session_state.sim_data.get("party_indices", []) if "sim_data" in st.session_state else [], st.session_state.threshold_status, active_c if step == 5 else -1)}
        <div class="flow-arrow">&#x279C;</div>
        {render_aggregation(st.session_state.agg_done)}
    </div>
    """
    st.markdown(pipeline_html, unsafe_allow_html=True)

    # ── Progress + Round Info ──
    p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
    with p_col1:
        if not st.session_state.sim_complete:
            render_step_info(step)
    with p_col2:
        completed_clients = sum(1 for p in st.session_state.client_progress.values() if p >= 100)
        pct = (completed_clients / cfg["num_clients"]) * 100 if cfg["num_clients"] > 0 else 0
        st.markdown(f'<div style="font-size:0.85rem; font-weight:600; margin-bottom:0.5rem; color:var(--text-primary);">Progress</div><div style="width:100%; height:4px; background:#e2e8f0; border-radius:2px; margin-bottom:0.5rem;"><div style="width:{pct}%; height:100%; background:var(--color-primary); border-radius:2px;"></div></div><div style="font-size:0.75rem; color:var(--text-secondary);">{completed_clients} / {cfg["num_clients"]} clients trained</div>', unsafe_allow_html=True)
    with p_col3:
        st.markdown(f'<div class="dashboard-card" style="text-align:center; padding:0.5rem;"><div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.5rem;">Current Round</div><div style="font-size:1.5rem; font-weight:700;">{rnd} / {total_rounds}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    
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

    # ── Center Grid ──
    g_col1, g_col2, g_col3 = st.columns([1, 1.5, 1])

    with g_col1:
        st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">Live Simulation Log</div>', unsafe_allow_html=True)
        log_html = []
        for msg in reversed(st.session_state.logs):
            msg = msg.replace("[SYSTEM]", '<span class="log-system">[SYSTEM]</span>')
            msg = msg.replace("[CLIENT", '<span class="log-client">[CLIENT')
            msg = msg.replace("]", ']</span>', 1) if "CLIENT" in msg else msg
            msg = msg.replace("[ROUND", '<span class="log-round">[ROUND')
            msg = msg.replace("]", ']</span>', 1) if "ROUND" in msg else msg
            log_html.append(msg)
        
        log_text = "<br>".join(log_html)
        st.markdown(f'<div class="log-terminal">{log_text if log_text else "Waiting..."}</div></div>', unsafe_allow_html=True)

    with g_col2:
        st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">Performance Metrics</div>', unsafe_allow_html=True)
        if st.session_state.accuracy_history:
            latest_acc = st.session_state.accuracy_history[-1]
            latest_auc = st.session_state.auc_history[-1]
            latest_loss = st.session_state.loss_history[-1]
            acc_d = auc_d = loss_d = 0.0
            if len(st.session_state.accuracy_history) > 1:
                acc_d = (latest_acc - st.session_state.accuracy_history[-2]) * 100
                auc_d = (latest_auc - st.session_state.auc_history[-2]) * 100
                loss_d = (latest_loss - st.session_state.loss_history[-2]) * 100
            st.markdown(render_metrics_grid(latest_acc, latest_auc, latest_loss, acc_d, auc_d, loss_d), unsafe_allow_html=True)
            
            st.markdown('<div style="font-size:0.85rem; font-weight:600; margin:1rem 0 0.5rem 0;">Round Progress</div>', unsafe_allow_html=True)
            st.markdown(render_round_progress(rnd, total_rounds), unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding:2rem; color:var(--text-muted); font-size:0.85rem;">Metrics will appear after first round completes</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g_col3:
        st.markdown('<div class="dashboard-card"><div class="dashboard-card-title">Accuracy Over Rounds</div>', unsafe_allow_html=True)
        if st.session_state.accuracy_history:
            img_buf = make_chart(st.session_state.accuracy_history, "#2563eb", "o", "Accuracy", "")
            st.image(img_buf, use_container_width=True)
        else:
            st.markdown('<div style="text-align:center; padding:2rem; color:var(--text-muted); font-size:0.85rem;">Chart will appear after first round completes</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Bottom Status Bar ──
    nc = cfg["num_clients"]
    np_ = cfg["num_parties"]
    t = cfg["threshold"]
    enc_ok = len(st.session_state.enc_previews) > 0
    sig_ok = len(st.session_state.sig_statuses) > 0
    thr_ok = bool(st.session_state.threshold_status)
    agg_ok = st.session_state.agg_done

    st.markdown(render_bottom_status(nc, np_, t, enc_ok, sig_ok, thr_ok, agg_ok), unsafe_allow_html=True)

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
            img_buf = make_chart(st.session_state.accuracy_history, "#2563eb", "o", "Accuracy", "Accuracy vs. Round")
            st.image(img_buf, use_container_width=True)
        with ch2:
            img_buf = make_chart(st.session_state.loss_history, "#ef4444", "s", "Avg Loss", "Loss vs. Round")
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
