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
    0: ("Step 1: Client Training", "Each client trains the local model on its private data partition."),
    1: ("Step 2: Encryption", "Model weights are encrypted using ECIES (secp256k1 ECDH + AES-GCM)."),
    2: ("Step 3: Ring Signature", "Clients sign updates anonymously using LSAG ring signatures."),
    3: ("Step 4: Send to Server", "Encrypted, signed updates are transmitted to the coordinator."),
    4: ("Step 5: Verify Signatures", "The server verifies each ring signature and checks for replay attacks."),
    5: ("Step 6: Threshold Decryption", "t-of-n threshold parties contribute partial decryptions to reconstruct the shared secret."),
    6: ("Step 7: Aggregation", "Decrypted weight vectors are averaged via federated averaging."),
    7: ("Step 8: Update Global Model", "The global model is updated and evaluated on the test set."),
}

STEP_ICONS = ["&#x1F9E0;", "&#x1F512;", "&#x1F575;", "&#x1F4E1;", "&#x2705;", "&#x1F511;", "&#x1F4CA;", "&#x2B50;"]


def render_stepper(current_step: int) -> None:
    parts = []
    for i, (num, label) in enumerate(STEPS):
        if i > 0:
            if i < current_step:
                cls = "step-connector step-connector-done"
            elif i == current_step:
                cls = "step-connector step-connector-active"
            else:
                cls = "step-connector"
            parts.append(f'<div class="{cls}"></div>')
        if i < current_step:
            circle_cls, label_cls = "step-circle step-done", "step-label step-label-done"
            icon = "&#x2713;"
        elif i == current_step:
            circle_cls, label_cls = "step-circle step-active", "step-label step-label-active"
            icon = num
        else:
            circle_cls, label_cls = "step-circle step-pending", "step-label"
            icon = num
        parts.append(
            f'<div class="step-item">'
            f'<div class="{circle_cls}">{icon}</div>'
            f'<div class="{label_cls}">{label}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="stepper-container">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_step_info(step: int) -> None:
    title, desc = STEP_DESCRIPTIONS.get(step, ("", ""))
    if title:
        st.markdown(
            f'<div class="step-info"><h3>{STEP_ICONS[step]} {title}</h3><p>{desc}</p></div>',
            unsafe_allow_html=True,
        )


def render_clients_training(num_clients: int, progress: dict, statuses: dict, active_client: int = -1) -> str:
    rows = []
    for cid in range(num_clients):
        pct = progress.get(cid, 0)
        status = statuses.get(cid, "")
        if cid == active_client and not status:
            status = "Training..."
        bar_cls = "bar-done" if pct >= 100 else "bar-training"
        if cid == active_client:
            bar_cls += " active-pulse"
            if pct == 0: pct = 100
        status_color = "#3fb950" if pct >= 100 and cid != active_client else ("#d29922" if cid == active_client else "#8b949e")
        rows.append(
            f'<div class="client-row">'
            f'<span class="client-icon">&#x1F4BB;</span>'
            f'<span class="client-name">Client {cid}</span>'
            f'<div class="client-bar-bg"><div class="client-bar-fill {bar_cls}" style="width:{pct}%"></div></div>'
            f'<span class="client-status" style="color:{status_color}">{status}</span>'
            f'</div>'
        )
    return (
        f'<div class="viz-panel">'
        f'<h4>&#x1F4BB; Clients (Train Locally)</h4>'
        f'{"".join(rows)}'
        f'</div>'
    )


def render_encrypted_updates(num_clients: int, enc_previews: list, active_client: int = -1) -> str:
    blocks = []
    for cid, preview in enc_previews:
        blocks.append(
            f'<div class="enc-block">&#x1F512; Client {cid}: {preview}</div>'
        )
    if active_client != -1 and active_client < num_clients:
        blocks.append(f'<div class="enc-block active-pulse" style="border-color:#d29922;color:#d29922;">&#x23F3; Client {active_client}: Encrypting...</div>')
    content = "".join(blocks) if blocks else '<div style="color:#484f58;font-size:0.8rem;">Waiting for encryption...</div>'
    return f'<div class="viz-panel"><h4>&#x1F510; Encrypted Updates</h4>{content}</div>'


def render_ring_signatures(num_clients: int, sig_statuses: dict, active_client: int = -1) -> str:
    nodes = []
    for cid in range(num_clients):
        status = sig_statuses.get(cid, "pending")
        if status == "signed":
            cls = "ring-node ring-unknown"
        elif cid == active_client:
            cls = "ring-node ring-member active-pulse"
            nodes.append(f'<span class="{cls}" style="border-color:#d29922;color:#d29922;">C{cid}</span>')
            continue
        else:
            cls = "ring-node ring-member"
        nodes.append(f'<span class="{cls}">C{cid}</span>')
    valid_count = sum(1 for s in sig_statuses.values() if s == "signed")
    validity = f'<div class="ring-valid">&#x2713; {valid_count} signatures generated</div>' if valid_count else ""
    return (
        f'<div class="viz-panel"><h4>&#x1F575; Ring Signatures</h4>'
        f'<div class="ring-container">{"".join(nodes)}{validity}</div></div>'
    )


def render_threshold_parties(num_parties: int, threshold: int, active_parties: list, status: str = "", active_client: int = -1) -> str:
    rows = []
    for pid in range(num_parties):
        if pid in active_parties:
            dot_cls = "party-dot party-active active-pulse" if active_client != -1 else "party-dot party-active"
        else:
            dot_cls = "party-dot party-inactive"
        rows.append(
            f'<div class="party-row">'
            f'<div class="{dot_cls}">P{pid}</div>'
            f'<span class="party-label">Party {pid}</span>'
            f'</div>'
        )
    if active_client != -1:
        status_html = f'<div style="color:#d29922;font-size:0.8rem;margin-top:0.5rem;" class="active-pulse">&#x23F3; Decrypting Client {active_client}...</div>'
    else:
        status_html = f'<div style="color:#3fb950;font-size:0.8rem;margin-top:0.5rem;">&#x2713; {status}</div>' if status else ""
    return (
        f'<div class="viz-panel">'
        f'<h4>&#x1F511; Threshold Parties (t={threshold} of {num_parties})</h4>'
        f'{"".join(rows)}{status_html}</div>'
    )


def render_aggregation(active: bool = False) -> str:
    if active:
        content = '<div class="agg-symbol">&#x03A3;</div><div style="color:#3fb950;text-align:center;font-size:0.8rem;">Federated averaging complete</div>'
    else:
        content = '<div class="agg-symbol" style="opacity:0.3;">&#x03A3;</div><div style="color:#484f58;text-align:center;font-size:0.8rem;">Waiting...</div>'
    return f'<div class="viz-panel"><h4>&#x1F4CA; Aggregation</h4>{content}</div>'


def render_server_verification(num_clients: int, results: list, active_client: int = -1) -> str:
    rows = []
    for cid, valid in results:
        icon = "&#x2705;" if valid else "&#x274C;"
        color = "#3fb950" if valid else "#f85149"
        rows.append(f'<div style="color:{color};font-size:0.8rem;padding:0.2rem 0;">{icon} Update {cid}: {"Valid" if valid else "Invalid"}</div>')
    if active_client != -1 and active_client < num_clients:
        rows.append(f'<div style="color:#d29922;font-size:0.8rem;padding:0.2rem 0;" class="active-pulse">&#x23F3; Update {active_client}: Verifying...</div>')
    content = "".join(rows) if rows else '<div style="color:#484f58;font-size:0.8rem;">Waiting for updates...</div>'
    return f'<div class="viz-panel"><h4>&#x1F5A5; Server Verification</h4>{content}</div>'


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


def render_metric_card(title: str, value: str, delta: str = "") -> str:
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    return (
        f'<div class="metric-card">'
        f'<h3>{title}</h3>'
        f'<div class="value">{value}</div>'
        f'{delta_html}</div>'
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
