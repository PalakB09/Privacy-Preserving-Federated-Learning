with open('demo/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_code = """def precompute_round():
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
"""

# Replace DEFAULTS
for i, line in enumerate(lines):
    if '"current_step": -1, "current_round": 1,' in line:
        lines[i] = line.replace('"current_step": -1, "current_round": 1,', '"current_step": -1, "current_round": 1, "current_client": 0, "round_precomputed": False,')

for i, line in enumerate(lines):
    if 'st.session_state.current_round = 1' in line and 'st.session_state.current_client' not in lines[i+1]:
        lines.insert(i+1, '    st.session_state.current_client = 0\n    st.session_state.round_precomputed = False\n')
        break

# Find run_step and advance_step lines
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith('def run_step(step_idx):'):
        start_idx = i
    if line.startswith('def reset_simulation():'):
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    del lines[start_idx:end_idx]
    lines.insert(start_idx, new_code + "\n\n")
    
with open('demo/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
