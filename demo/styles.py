"""CSS styles for the Streamlit demo UI."""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 1.5rem 2rem; border-radius: 16px; margin-bottom: 1rem;
    color: white; text-align: center;
}
.main-header h1 { font-size: 1.8rem; font-weight: 700; margin: 0; }
.main-header p { font-size: 0.9rem; opacity: 0.7; margin-top: 0.3rem; }

/* Stepper */
.stepper-container {
    display: flex; justify-content: center; align-items: flex-start;
    gap: 0; padding: 0.8rem 0; margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #0d1117, #161b22);
    border-radius: 14px; border: 1px solid rgba(255,255,255,0.06);
}
.step-item {
    display: flex; flex-direction: column; align-items: center;
    min-width: 90px; position: relative;
}
.step-circle {
    width: 36px; height: 36px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem; margin-bottom: 4px;
    transition: all 0.3s ease;
}
.step-done { background: #2ea043; color: white; box-shadow: 0 0 8px rgba(46,160,67,0.4); }
.step-active {
    background: #00b4d8; color: white;
    box-shadow: 0 0 12px rgba(0,180,216,0.6);
    animation: stepPulse 1.5s ease-in-out infinite;
}
.step-pending { background: #21262d; color: #484f58; border: 1px solid #30363d; }
.step-label {
    font-size: 0.65rem; color: #8b949e; text-align: center;
    max-width: 80px; line-height: 1.2;
}
.step-label-active { color: #58a6ff; font-weight: 600; }
.step-label-done { color: #3fb950; }
.step-connector {
    width: 28px; height: 2px; margin-top: 17px;
    background: #21262d; flex-shrink: 0;
}
.step-connector-done { background: #2ea043; }
.step-connector-active { background: linear-gradient(90deg, #2ea043, #00b4d8); }

@keyframes stepPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(0,180,216,0.4); }
    50% { box-shadow: 0 0 20px rgba(0,180,216,0.8); }
}

/* Step info banner */
.step-info {
    background: linear-gradient(135deg, #0d1117, #161b22);
    border: 1px solid rgba(0,180,216,0.2); border-radius: 10px;
    padding: 0.8rem 1.2rem; margin-bottom: 0.8rem;
}
.step-info h3 { color: #58a6ff; margin: 0 0 0.3rem 0; font-size: 1rem; }
.step-info p { color: #8b949e; margin: 0; font-size: 0.85rem; }

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    padding: 1rem 1.2rem; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    text-align: center; color: white;
}
.metric-card h3 {
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 1px; opacity: 0.6; margin: 0 0 0.4rem 0;
}
.metric-card .value {
    font-size: 1.6rem; font-weight: 700;
    background: linear-gradient(90deg, #00b4d8, #48cae4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-card .delta { font-size: 0.7rem; color: #3fb950; margin-top: 0.2rem; }

/* Visualization panels */
.viz-panel {
    background: linear-gradient(135deg, #0d1117, #161b22);
    border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;
    padding: 1rem; margin-bottom: 0.5rem; min-height: 180px;
}
.viz-panel h4 {
    color: #c9d1d9; font-size: 0.85rem;
    margin: 0 0 0.8rem 0; text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Client rows */
.client-row {
    display: flex; align-items: center; gap: 10px;
    padding: 0.4rem 0.6rem; margin-bottom: 0.3rem;
    background: rgba(255,255,255,0.03); border-radius: 8px;
}
.client-icon { font-size: 1.1rem; }
.client-name { color: #c9d1d9; font-size: 0.8rem; min-width: 60px; }
.client-bar-bg {
    flex: 1; height: 8px; background: #21262d;
    border-radius: 4px; overflow: hidden;
}
.client-bar-fill {
    height: 100%; border-radius: 4px;
    transition: width 0.5s ease;
}
.bar-training { background: linear-gradient(90deg, #f0883e, #d29922); }
.bar-done { background: linear-gradient(90deg, #2ea043, #3fb950); }
.client-status { font-size: 0.75rem; min-width: 40px; text-align: right; }

/* Encrypted block */
.enc-block {
    background: #0d1117; border: 1px solid #30363d;
    border-radius: 8px; padding: 0.5rem 0.7rem;
    font-family: 'Courier New', monospace; font-size: 0.7rem;
    color: #f0883e; margin-bottom: 0.3rem;
    word-break: break-all;
}

/* Ring signature visual */
.ring-container { text-align: center; padding: 0.5rem; }
.ring-node {
    display: inline-block; width: 36px; height: 36px;
    border-radius: 50%; margin: 0 4px;
    line-height: 36px; font-size: 0.75rem; font-weight: 600;
}
.ring-unknown { background: #6e40c9; color: white; }
.ring-member { background: #21262d; color: #8b949e; border: 1px solid #30363d; }
.ring-valid { color: #3fb950; font-weight: 600; font-size: 0.8rem; margin-top: 0.5rem; }

/* Threshold party */
.party-row {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 0.3rem;
}
.party-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 600;
}
.party-active { background: #f0883e; color: white; }
.party-inactive { background: #21262d; color: #484f58; border: 1px solid #30363d; }
.party-label { color: #8b949e; font-size: 0.75rem; }

/* Server flow arrows */
.flow-arrow { color: #484f58; font-size: 1.2rem; text-align: center; padding: 0.3rem; }
.flow-arrow-active { color: #00b4d8; }

/* Aggregation */
.agg-symbol {
    font-size: 2.5rem; text-align: center; padding: 0.5rem;
    color: #00b4d8;
}

/* Status bar */
.status-bar {
    display: flex; align-items: center; gap: 1rem;
    background: #0d1117; border-top: 1px solid #21262d;
    padding: 0.5rem 1rem; border-radius: 0 0 12px 12px;
    font-size: 0.75rem; color: #8b949e;
    margin-top: 0.5rem;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-green { background: #3fb950; }
.dot-yellow { background: #d29922; }
.dot-blue { background: #58a6ff; }

/* Round progress */
.round-pill {
    display: inline-block; padding: 0.2rem 0.6rem;
    border-radius: 12px; font-size: 0.75rem; font-weight: 600;
    margin: 0.15rem;
}
.round-done { background: rgba(46,160,67,0.15); color: #3fb950; border: 1px solid rgba(46,160,67,0.3); }
.round-active { background: rgba(0,180,216,0.15); color: #58a6ff; border: 1px solid rgba(0,180,216,0.3); }
.round-pending { background: rgba(255,255,255,0.03); color: #484f58; border: 1px solid #21262d; }

/* Security badge */
.security-badge {
    display: inline-block; background: rgba(0,180,216,0.12);
    border: 1px solid rgba(0,180,216,0.25); color: #48cae4;
    padding: 0.2rem 0.6rem; border-radius: 6px;
    font-size: 0.75rem; font-weight: 600; margin: 0.1rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00b4d8, #0077b6) !important;
    color: white !important; border: none !important;
    padding: 0.6rem 1.5rem !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    width: 100% !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,180,216,0.35) !important;
}
/* Active Pulse Animation */
.active-pulse {
    animation: clientPulse 1.5s infinite;
}
@keyframes clientPulse {
    0% { opacity: 1; box-shadow: 0 0 5px rgba(210, 153, 34, 0.4); }
    50% { opacity: 0.7; box-shadow: 0 0 15px rgba(210, 153, 34, 0.9); }
    100% { opacity: 1; box-shadow: 0 0 5px rgba(210, 153, 34, 0.4); }
}

/* ─── Math Panel ─── */
.math-panel {
    background: linear-gradient(135deg, #0a0d14, #111827);
    border: 1px solid rgba(0, 180, 216, 0.2);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.math-panel-header {
    font-size: 1rem; font-weight: 700;
    color: #58a6ff; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 0.6rem;
}
.math-focus-badge {
    background: rgba(0, 180, 216, 0.12);
    border: 1px solid rgba(0, 180, 216, 0.3);
    color: #48cae4; padding: 0.1rem 0.6rem;
    border-radius: 20px; font-size: 0.75rem;
    font-weight: 600;
}
.math-block {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.8rem;
}
.math-block-title {
    color: #e6edf3; font-size: 0.88rem;
    font-weight: 700; margin-bottom: 0.7rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.2px;
}
.math-row {
    display: flex; align-items: flex-start;
    gap: 1rem; padding: 0.3rem 0;
    font-size: 0.82rem; border-bottom: 1px solid rgba(255,255,255,0.03);
}
.math-label {
    color: #8b949e; min-width: 200px;
    flex-shrink: 0; font-size: 0.8rem;
    font-family: 'Inter', sans-serif; font-weight: 500;
}
.math-value {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem; word-break: break-all;
    line-height: 1.5;
}
.math-value.mono {
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
    font-size: 0.75rem;
}
.math-arrow {
    text-align: center; color: #30363d;
    font-size: 1rem; padding: 0.3rem 0;
}

</style>
"""
