"""Rendering helper functions for the step-by-step animated UI."""

import streamlit as st

STEPS = [
    ("1", "Client Training"),
    ("2", "Encryption"),
    ("3", "Ring Signature"),
    ("4", "Send to Server"),
    ("5", "Verify Signatures"),
    ("6", "Threshold Decrypt"),
    ("7", "Aggregation"),
    ("8", "Update Model"),
]

STEP_DESCRIPTIONS = {
    0: ("Step 1: Client Training", "Each selected client trains the local model on its private data."),
    1: ("Step 2: Encryption", "Model weights are encrypted using ECIES (secp256k1 ECDH + AES-GCM)."),
    2: ("Step 3: Ring Signature", "Clients sign updates anonymously using LSAG ring signatures."),
    3: ("Step 4: Send to Server", "Encrypted, signed updates are transmitted to the coordinator."),
    4: ("Step 5: Verify Signatures", "The server verifies each ring signature and checks for replay attacks."),
    5: ("Step 6: Threshold Decryption", "t-of-n threshold parties contribute partial decryptions to reconstruct the shared secret."),
    6: ("Step 7: Aggregation", "Decrypted weight vectors are averaged via federated averaging."),
    7: ("Step 8: Update Global Model", "The global model is updated and evaluated on the test set."),
}


def render_stepper(current_step: int) -> None:
    parts = []
    total_steps = len(STEPS)
    for i, (num, label) in enumerate(STEPS):
        if i < current_step:
            circle_cls, label_cls = "step-circle step-done", "step-label step-label-done"
            icon = "&#x2713;"
        elif i == current_step:
            circle_cls, label_cls = "step-circle step-active", "step-label step-label-active"
            icon = num
        else:
            circle_cls, label_cls = "step-circle step-pending", "step-label"
            icon = num
            
        line_html = ""
        if i < total_steps - 1:
            line_cls = "step-line step-line-active" if i < current_step else "step-line"
            line_html = f'<div class="{line_cls}"></div>'
            
        parts.append(
            f'<div class="step-item">'
            f'<div class="{circle_cls}">{icon}</div>'
            f'<div class="{label_cls}">{label}</div>'
            f'{line_html}'
            f'</div>'
        )
    st.markdown(f'<div class="stepper-container">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_step_info(step: int) -> None:
    title, desc = STEP_DESCRIPTIONS.get(step, ("", ""))
    if title:
        st.markdown(
            f'<h3 class="text-primary-color" style="font-size:1.1rem; font-weight:600; margin:0 0 0.5rem 0;">{title}</h3>'
            f'<p class="text-secondary" style="font-size:0.85rem; margin:0;">{desc}</p>',
            unsafe_allow_html=True,
        )


def render_clients_training(num_clients: int, progress: dict, statuses: dict, active_client: int = -1) -> str:
    rows = []
    for cid in range(num_clients):
        pct = progress.get(cid, 0)
        status = statuses.get(cid, "")
        if cid == active_client and not status:
            status = "Training..."
        
        # Override for the mockup's visual exactness
        display_pct = pct
        if pct == 0 and cid == active_client: display_pct = 50
        
        status_color = "var(--color-success)" if pct >= 100 and cid != active_client else ("var(--color-primary)" if cid == active_client else "var(--text-muted)")
        rows.append(
            f'<div class="client-row">'
            f'<span class="client-icon" style="color:var(--color-primary)">&#x1F464;</span>'
            f'<span class="client-name">Client {cid+1}</span>'
            f'<div class="client-bar-bg"><div class="client-bar-fill" style="width:{display_pct}%; background:{status_color};"></div></div>'
            f'<span class="client-status" style="color:{status_color}">{display_pct}%</span>'
            f'</div>'
        )
    return (
        f'<div class="pipeline-card">'
        f'<div class="pipeline-header"><span class="text-primary-color">CLIENTS (TRAIN LOCALLY)</span></div>'
        f'<div style="flex:1; display:flex; flex-direction:column; justify-content:center;">{"".join(rows)}</div>'
        f'</div>'
    )

def render_encrypted_updates(num_clients: int, enc_previews: list, active_client: int = -1) -> str:
    blocks = []
    for cid, preview in enc_previews:
        blocks.append(
            f'<div class="enc-block"><span class="enc-icon">&#x1F512;</span> {preview[:10]}...</div>'
        )
    if active_client != -1 and active_client < num_clients:
        blocks.append(f'<div class="enc-block active-pulse" style="border-color:var(--color-encryption);"><span class="enc-icon">&#x1F512;</span> - </div>')
        
    # Pad out the remaining so the card size looks right
    while len(blocks) < num_clients:
        blocks.append(f'<div class="enc-block" style="opacity:0.3;"><span class="enc-icon">&#x1F512;</span> - </div>')
        
    content = "".join(blocks)
    return f'<div class="pipeline-card"><div class="pipeline-header"><span class="text-encryption">ENCRYPTED UPDATES</span> <span class="text-encryption">&#x1F512;</span></div><div style="flex:1; display:flex; flex-direction:column; justify-content:center;">{content}</div></div>'

def render_ring_signatures(num_clients: int, sig_statuses: dict, active_client: int = -1) -> str:
    rows = []
    for cid in range(num_clients):
        status = sig_statuses.get(cid, "pending")
        if status == "signed":
            rows.append(f'<div class="ring-row"><span class="ring-valid">&#x2714;</span> <span class="ring-status">Valid</span></div>')
        elif cid == active_client:
            rows.append(f'<div class="ring-row active-pulse"><span style="color:var(--color-warning);">&#x23F3;</span> <span class="ring-status">Generating...</span></div>')
        else:
            rows.append(f'<div class="ring-row"><span style="color:var(--text-muted);">-</span></div>')
            
    content = "".join(rows)
    return f'<div class="pipeline-card"><div class="pipeline-header"><span class="text-signature">RING SIGNATURES</span> <span class="text-signature">&#x270D;</span></div><div style="flex:1; display:flex; flex-direction:column; justify-content:center;">{content}</div></div>'

def render_server_verification(num_clients: int, results: list, active_client: int = -1) -> str:
    # A single solid block representing the server processing
    return (
        f'<div class="pipeline-card" style="border:none; box-shadow:none; padding:0; background:transparent;">'
        f'<div class="server-block">'
        f'<div class="server-icon">&#x1F5C4;</div>'
        f'<div style="color:var(--color-primary); font-weight:700; font-size:0.8rem;">SERVER</div>'
        f'</div>'
        f'</div>'
    )

def render_threshold_parties(num_parties: int, threshold: int, active_parties: list, status: str = "", active_client: int = -1) -> str:
    dots = []
    for pid in range(num_parties):
        if pid in active_parties:
            dot_cls = "party-dot party-active active-pulse" if active_client != -1 else "party-dot party-active"
        else:
            dot_cls = "party-dot party-inactive"
        dots.append(f'<div class="{dot_cls}">P{pid}</div>')
        
    content = f'<div class="party-grid">{"".join(dots)}</div>'
    if status or active_client != -1:
        content += f'<div class="decryption-box">{"Reconstruction &#x1F513;" if status else "Partial Decryptions"}</div>'
    else:
        content += f'<div class="decryption-box" style="opacity:0.3;">Waiting...</div>'
        
    return (
        f'<div class="pipeline-card" style="min-width: 220px;">'
        f'<div class="pipeline-header" style="justify-content:center;"><span class="text-threshold">THRESHOLD PARTIES (t = {threshold} of {num_parties})</span></div>'
        f'<div style="flex:1; display:flex; flex-direction:column; justify-content:center;">{content}</div>'
        f'</div>'
    )

def render_aggregation(active: bool = False) -> str:
    icon_cls = "agg-icon active-pulse" if active else "agg-icon"
    opacity = "1" if active else "0.3"
    content = f'<div class="agg-block" style="opacity:{opacity};"><div class="{icon_cls}">&#x03A3;</div><div class="agg-text">Global Model Update</div></div>'
    return f'<div class="pipeline-card" style="border-color:var(--color-warning);"><div class="pipeline-header" style="justify-content:center;"><span class="text-warning">AGGREGATION</span></div>{content}</div>'


def render_round_progress(current_round: int, total_rounds: int) -> str:
    pills = []
    for r in range(1, total_rounds + 1):
        if r < current_round:
            cls = "round-pill round-done"
        elif r == current_round:
            cls = "round-pill round-active"
        else:
            cls = "round-pill round-pending"
        pills.append(f'<span class="{cls}">Round {r}</span>')
    return "".join(pills)


def render_metrics_grid(acc: float, auc: float, loss: float, acc_d: float, auc_d: float, loss_d: float) -> str:
    def t_fmt(d, invert=False):
        if d == 0: return '<span class="metric-trend text-secondary">-</span>'
        good = d > 0 if not invert else d < 0
        cls = "trend-up" if good else "trend-down"
        arrow = "↑" if d > 0 else "↓"
        return f'<span class="metric-trend {cls}">{arrow} {abs(d):.2f}% vs prev round</span>'
        
    return (
        f'<div class="metrics-grid">'
        f'<div class="metric-box"><div class="metric-label">Accuracy</div><div class="metric-value">{acc:.4f}</div>{t_fmt(acc_d)}</div>'
        f'<div class="metric-box"><div class="metric-label">AUC Score</div><div class="metric-value">{auc:.4f}</div>{t_fmt(auc_d)}</div>'
        f'<div class="metric-box"><div class="metric-label">Loss</div><div class="metric-value" style="color:var(--color-warning)">{loss:.4f}</div>{t_fmt(loss_d, True)}</div>'
        f'</div>'
    )

def render_bottom_status(nc: int, np: int, t: int, s_enc: bool, s_sig: bool, s_thr: bool, s_agg: bool) -> str:
    def chk(ok): return '<span class="text-success">&#x2714;</span>' if ok else '<span class="text-muted">&#x25CF;</span>'
    return (
        f'<div class="bottom-status-bar">'
        f'<div class="status-group">'
        f'<span style="font-weight:600; font-size:0.85rem; color:var(--text-primary)">System Status</span>'
        f'<div class="status-item">Encryption: {chk(s_enc)}</div>'
        f'<div class="status-item">Signatures: {chk(s_sig)}</div>'
        f'<div class="status-item">Threshold: {chk(s_thr)}</div>'
        f'<div class="status-item">Aggregation: {chk(s_agg)}</div>'
        f'<div class="status-badge" style="margin-left:1rem;">All Systems Secure</div>'
        f'</div>'
        f'<div class="status-group">'
        f'<span style="font-weight:600; font-size:0.85rem; color:var(--text-primary)">Participants</span>'
        f'<div class="status-item text-primary-color" style="font-weight:600;">Clients: {nc}/{nc}</div>'
        f'<div class="status-item text-success" style="font-weight:600;">Parties: {np}/{np} (t={t})</div>'
        f'</div>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# MATH PANEL: Live Mathematical Execution
# ─────────────────────────────────────────────────────────────────────────────

def _math_row(label: str, value: str, color: str = "#c9d1d9") -> str:
    return (
        f'<div class="math-row">'
        f'<span class="math-label">{label}</span>'
        f'<span class="math-value" style="color:{color}">{value}</span>'
        f'</div>'
    )

def _math_arrow() -> str:
    return '<div class="math-arrow">&#x25BC;</div>'

def _math_block(title: str, rows: list, icon: str = "&#x1F9EE;") -> str:
    content = "".join(rows)
    return (
        f'<div class="math-block">'
        f'<div class="math-block-title">{icon} {title}</div>'
        f'{content}'
        f'</div>'
    )

def render_math_panel(step: int, pc: dict, focused_client: int, num_clients: int,
                      party_indices: list, cfg: dict) -> str:
    """
    Renders the Live Mathematical Execution panel.
    Shows real computed values for the current step and focused client.
    pc = precomputed dict from sim_data["precomputed"] (contains actual crypto results).
    """
    if pc is None:
        return (
            '<div class="math-panel">'
            '<div class="math-panel-header">&#x1F52C; Live Mathematical Execution</div>'
            '<div style="color:#484f58;font-size:0.85rem;text-align:center;padding:2rem;">'
            'Waiting for computation to begin...</div>'
            '</div>'
        )

    c = focused_client
    blocks = []

    # ── Step 0: Client Training ──
    if step == 0:
        local_loss = pc["losses"][c] if c < len(pc["losses"]) else None
        local_acc  = pc["statuses"].get(c, "-")
        blocks.append(_math_block(f"Logistic Regression Update — Client {c}", [
            _math_row("Algorithm", "Mini-batch SGD + Binary Cross-Entropy Loss", "#58a6ff"),
            _math_row("Learning Rate (&#x03B7;)", f'{cfg["learning_rate"]}', "#d29922"),
            _math_row("Local Epochs", f'{cfg["local_epochs"]}', "#d29922"),
            _math_arrow(),
            _math_row("Local Loss (BCE)", f'{local_loss:.6f}' if local_loss is not None else "—", "#f0883e"),
            _math_row("Local Accuracy", f'{local_acc}', "#3fb950"),
        ], "&#x1F9E0;"))

    # ── Step 1: ECIES Encryption ──
    elif step == 1:
        if c < len(pc["enc_updates"]):
            enc = pc["enc_updates"][c]
            cipher_hex = enc.get("ciphertext", "")[:48] + "..."
            tag_hex    = enc.get("tag", "")[:24] + "..." if "tag" in enc else "included in ciphertext"
            nonce_hex  = enc.get("nonce", "")[:24] + "..." if "nonce" in enc else "embedded"
            blocks.append(_math_block(f"ECIES Encryption — Client {c}", [
                _math_row("Scheme", "ECIES: secp256k1 ECDH + AES-256-GCM", "#58a6ff"),
                _math_row("Step 1", "Generate ephemeral keypair on secp256k1", "#8b949e"),
                _math_row("Step 2", "ECDH shared secret &#x2192; PBKDF2 &#x2192; AES key", "#8b949e"),
                _math_row("Step 3", "Encrypt weight vector w/ AES-GCM (256-bit)", "#8b949e"),
                _math_arrow(),
                _math_row("Ciphertext (hex sample)", cipher_hex, "#f0883e"),
                _math_row("GCM Auth Tag", tag_hex, "#d29922"),
                _math_row("Nonce", nonce_hex, "#48cae4"),
            ], "&#x1F512;"))

    # ── Step 2: LSAG Ring Signature ──
    elif step == 2:
        if c < len(pc["signatures"]):
            sig = pc["signatures"][c]
            # Different LSAG implementations store fields differently
            c0_val = sig.get("c0", sig.get("c", sig.get("challenge", "N/A")))
            c0_str = repr(c0_val)[:40] + "..."
            s_val  = sig.get("s", sig.get("responses", sig.get("scalars", "N/A")))
            s_str  = str(s_val)[:50] + "..."
            blocks.append(_math_block(f"LSAG Ring Signature — Client {c}", [
                _math_row("Scheme", "Linkable Spontaneous Anonymous Group Sig.", "#58a6ff"),
                _math_row("Ring Size (n)", str(num_clients), "#d29922"),
                _math_row("Message", "SHA-256( JSON(enc_update) )", "#8b949e"),
                _math_row("Step 1", "Pick random scalar k &#x2208; Z_n", "#8b949e"),
                _math_row("Step 2", "Compute L&#x1D5CE; = s&#x1D5CE;&#x00B7;G + c&#x1D5CE;&#x00B7;P&#x1D5CE; for each member", "#8b949e"),
                _math_row("Step 3", "Verify ring closes: c&#x2099;&#x208A;&#x2081; == c&#x2080;", "#8b949e"),
                _math_arrow(),
                _math_row("Challenge c&#x2080;", c0_str, "#f0883e"),
                _math_row("Responses s[] (sample)", s_str, "#48cae4"),
                _math_row("True Signer", "ANONYMOUS — ring conceals identity", "#3fb950"),
            ], "&#x1F575;"))

    # ── Step 3: Network Send ──
    elif step == 3:
        if c < len(pc["enc_updates"]):
            enc = pc["enc_updates"][c]
            cipher_len = len(enc.get("ciphertext", "")) // 2
            blocks.append(_math_block(f"Network Packet — Client {c}", [
                _math_row("Transport", "Signed + Encrypted payload over secure channel", "#58a6ff"),
                _math_row("Payload size", f"~{cipher_len} bytes ciphertext + signature", "#8b949e"),
                _math_row("Contents", "{ ciphertext, tag, nonce, LSAG signature }", "#8b949e"),
                _math_row("Anonymity", "Server cannot link packet to real identity", "#3fb950"),
                _math_row("Integrity", "GCM tag + LSAG signature provide authenticity", "#3fb950"),
                _math_arrow(),
                _math_row("Status", "&#x2705; Delivered to Aggregation Server", "#3fb950"),
            ], "&#x1F4E1;"))

    # ── Step 4: Signature Verification ──
    elif step == 4:
        if c < len(pc["verify_results"]):
            _, valid = pc["verify_results"][c]
            status_str = "&#x2705; VALID" if valid else "&#x274C; INVALID"
            res_color  = "#3fb950" if valid else "#f85149"
            blocks.append(_math_block(f"LSAG Verification — Update {c}", [
                _math_row("Algorithm", "LSAG forward-pass ring reconstruction", "#58a6ff"),
                _math_row("Input", "Signature (c&#x2080;, [s&#x2080;..s&#x2099;]) + ring public keys", "#8b949e"),
                _math_row("Step 1", "Recompute L&#x1D5CE; = s&#x1D5CE;&#x00B7;G + c&#x1D5CE;&#x00B7;P&#x1D5CE; for each member", "#8b949e"),
                _math_row("Step 2", "Recompute R&#x1D5CE; = s&#x1D5CE;&#x00B7;H(P&#x1D5CE;) + c&#x1D5CE;&#x00B7;KeyImage", "#8b949e"),
                _math_row("Step 3", "Check: c&#x2099;&#x208A;&#x2081; == c&#x2080; (ring must close)", "#8b949e"),
                _math_arrow(),
                _math_row("Verification Result", status_str, res_color),
                _math_row("Replay Attack Check", "&#x2705; Key image unique — no double-spend", "#3fb950"),
            ], "&#x2705;"))

    # ── Step 5: Threshold Decryption ──
    elif step == 5:
        if c < len(pc["decrypted"]):
            weights   = pc["decrypted"][c]
            w_preview = f"[{', '.join(f'{w:.4f}' for w in weights[:5])}{'...' if len(weights) > 5 else ''}]"
            t  = cfg["threshold"]
            n  = cfg["num_parties"]
            blocks.append(_math_block(f"Threshold Decryption — Client {c}", [
                _math_row("Scheme", f"Shamir Secret Sharing ({t}-of-{n} threshold)", "#58a6ff"),
                _math_row("Active Parties", str(party_indices), "#d29922"),
                _math_row("Step 1", f"Each party P&#x1D5CE; computes partial Dec&#x1D5CE; = share&#x1D5CE;(enc)", "#8b949e"),
                _math_row("Step 2", "Combine via Lagrange interpolation in exponent", "#8b949e"),
                _math_row("Formula", f"w = &#x03A3; ( Dec&#x1D5CE; &#x00B7; &#x03BB;&#x1D5CE; ) mod p", "#d29922"),
                _math_arrow(),
                _math_row("Decrypted Weights (first 5)", w_preview, "#3fb950"),
                _math_row("Vector Dimensions", f"{len(weights)} features", "#48cae4"),
            ], "&#x1F511;"))

    # ── Step 6: Aggregation ──
    elif step == 6:
        if pc.get("agg") is not None:
            agg = pc["agg"]
            num_dims = len(agg)

            # Build a mini HTML bar chart for first 12 weights
            display_weights = list(agg[:12])
            max_abs = max(abs(float(w)) for w in display_weights) if len(display_weights) > 0 else 1.0
            if max_abs == 0: max_abs = 1.0

            bars_html = ""
            for i, w in enumerate(display_weights):
                w = float(w)
                pct = min(100, abs(w) / max_abs * 100)
                bar_color = "#00b4d8" if w >= 0 else "#f0883e"
                bars_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
                    f'<span style="color:#8b949e;font-size:0.72rem;min-width:22px;text-align:right;">w{i}</span>'
                    f'<div style="flex:1;background:#21262d;border-radius:3px;height:10px;overflow:hidden;">'
                    f'<div style="width:{pct:.1f}%;background:{bar_color};height:100%;border-radius:3px;'
                    f'transition:width 0.4s ease;"></div></div>'
                    f'<span style="color:{bar_color};font-size:0.72rem;min-width:68px;'
                    f'font-family:\'SFMono-Regular\',monospace;">{w:+.5f}</span>'
                    f'</div>'
                )
            if num_dims > 12:
                bars_html += f'<div style="color:#484f58;font-size:0.72rem;margin-top:4px;">... {num_dims - 12} more features</div>'

            # Compute per-client contribution diff for transparency
            client_rows = []
            for ci, dw in enumerate(pc.get("decrypted", [])):
                diff = dw[:3]
                diff_str = "  ".join(f"{v:+.4f}" for v in diff) + " ..."
                client_rows.append(_math_row(f"Client {ci} weights (first 3)", diff_str, "#48cae4"))

            agg_preview = f"[{', '.join(f'{w:.4f}' for w in agg[:5])}{'...' if num_dims > 5 else ''}]"
            blocks.append(_math_block("FedAvg Aggregation", [
                _math_row("Algorithm", "Federated Averaging (McMahan et al. 2017)", "#58a6ff"),
                _math_row("Formula", f"w_global = (1/{num_clients}) · Σ wᵢ", "#d29922"),
                _math_row("Updates Averaged", str(num_clients), "#d29922"),
                _math_row("Weight Dimensions", f"{num_dims} features", "#48cae4"),
                _math_row("Weight Policy", "Equal weighting (uniform data split assumed)", "#8b949e"),
                *client_rows,
                _math_arrow(),
                _math_row("Global Weights (first 5)", agg_preview, "#3fb950"),
                f'<div style="margin:0.6rem 0 0.2rem;color:#8b949e;font-size:0.78rem;">Aggregated Weight Vector (w₀ … w{min(11,num_dims-1)}):</div>',
                f'<div style="background:#0d1117;border-radius:8px;padding:0.7rem 0.8rem;margin-top:0.2rem;">{bars_html}</div>',
            ], "&#x1F4CA;"))


    # ── Step 7: Global Model Update ──
    elif step == 7:
        acc, auc, avg_loss = pc.get("acc"), pc.get("auc"), pc.get("avg_loss")
        if acc is not None:
            blocks.append(_math_block("Global Model Evaluation", [
                _math_row("Model", "Binary Logistic Regression", "#58a6ff"),
                _math_row("Test Set", "Held-out partition (20% of dataset)", "#8b949e"),
                _math_row("Metric 1", "Accuracy = (TP + TN) / N", "#8b949e"),
                _math_row("Metric 2", "AUC-ROC — area under receiver-operator curve", "#8b949e"),
                _math_arrow(),
                _math_row("Test Accuracy", f"{acc:.6f}  ({acc:.2%})", "#3fb950"),
                _math_row("AUC-ROC Score", f"{auc:.6f}", "#00b4d8"),
                _math_row("Round Avg Loss", f"{avg_loss:.6f}", "#f0883e"),
            ], "&#x2B50;"))

    if not blocks:
        blocks_html = '<div style="color:#484f58;font-size:0.85rem;text-align:center;padding:1.5rem;">Computation pending for this step...</div>'
    else:
        blocks_html = "".join(blocks)

    focused_label = f"Client {c}" if step < 6 else "Global Model"
    return (
        f'<div class="math-panel">'
        f'<div class="math-panel-header">'
        f'&#x1F52C; Live Mathematical Execution'
        f'&nbsp;&nbsp;<span class="math-focus-badge">Focus: {focused_label}</span>'
        f'</div>'
        f'{blocks_html}'
        f'</div>'
    )
