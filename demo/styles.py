"""CSS styles for the Streamlit demo UI."""

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-main: var(--background-color, #f8fafc);
    --bg-card: var(--secondary-background-color, #ffffff);
    --border-color: color-mix(in srgb, var(--text-color) 15%, transparent);
    
    --text-primary: var(--text-color, #0f172a);
    --text-secondary: color-mix(in srgb, var(--text-color) 70%, transparent);
    --text-muted: color-mix(in srgb, var(--text-color) 40%, transparent);
    
    --color-primary: var(--primary-color, #2563eb);
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-danger: #ef4444;
    
    --color-encryption: #8b5cf6;
    --color-signature: #f59e0b;
    --color-threshold: #22c55e;
    --color-aggregation: #f97316;
}

/* Global Reset & Typography */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: var(--bg-main); color: var(--text-primary); }

/* Hide default streamlit header background to allow custom header but keep buttons */
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
header[data-testid="stHeader"] { background-color: transparent !important; }

/* Utilities */
.text-primary-color { color: var(--color-primary) !important; }
.text-success { color: var(--color-success) !important; }
.text-warning { color: var(--color-warning) !important; }
.text-danger { color: var(--color-danger) !important; }
.text-encryption { color: var(--color-encryption) !important; }
.text-signature { color: var(--color-signature) !important; }
.text-threshold { color: var(--color-threshold) !important; }
.text-aggregation { color: var(--color-aggregation) !important; }
.text-secondary { color: var(--text-secondary) !important; }

/* Custom Top Header */
.top-header {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--bg-card); border-bottom: 1px solid var(--border-color);
    padding: 1rem 1.5rem; margin: -1rem -1rem 1.5rem -1rem;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}
.header-title-container h1 { font-size: 1.5rem; font-weight: 700; margin: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem; }
.header-title-container p { font-size: 0.85rem; color: var(--text-secondary); margin: 0.2rem 0 0 2rem; font-weight: 500; }

/* 8-Step Stepper */
.stepper-container {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 2rem; margin-bottom: 1rem;
    background: transparent;
}
.step-item {
    display: flex; flex-direction: column; align-items: center; position: relative; flex: 1;
}
.step-circle {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; font-size: 0.85rem; margin-bottom: 8px; z-index: 2;
    transition: all 0.2s ease;
}
.step-done { background: var(--bg-card); color: var(--color-primary); border: 2px solid var(--color-primary); }
.step-active { background: var(--color-primary); color: white; border: 2px solid var(--color-primary); box-shadow: 0 0 0 4px rgba(37,99,235,0.15); }
.step-pending { background: var(--bg-card); color: var(--text-muted); border: 2px solid var(--border-color); }
.step-label { font-size: 0.75rem; color: var(--text-secondary); text-align: center; font-weight: 500; white-space: nowrap; }
.step-label-active { color: var(--text-primary); font-weight: 700; }
.step-line {
    position: absolute; top: 16px; left: 50%; width: 100%; height: 2px;
    background: var(--border-color); z-index: 1;
}
.step-line-active { background: var(--color-primary); }

/* Unified Pipeline Container */
.pipeline-container {
    display: flex; align-items: center; justify-content: space-between;
    gap: 0.5rem; overflow-x: auto; padding-bottom: 1rem; margin-bottom: 1.5rem;
}
.flow-arrow { color: var(--text-muted); font-size: 1.2rem; display: flex; align-items: center; justify-content: center; }

/* Pipeline Cards */
.pipeline-card {
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 1rem; min-width: 160px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
    display: flex; flex-direction: column; height: 240px;
}
.pipeline-header {
    font-size: 0.7rem; font-weight: 700; color: var(--text-secondary);
    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 1rem;
    display: flex; justify-content: space-between; align-items: center;
}

/* Base Card Style for Grid */
.dashboard-card {
    background: var(--bg-card); border: 1px solid var(--border-color);
    border-radius: 12px; padding: 1.25rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
    height: 100%;
}
.dashboard-card-title {
    font-size: 0.9rem; font-weight: 600; color: var(--text-primary);
    margin-bottom: 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;
}

/* Live Log Terminal */
.log-terminal {
    background: #0f172a; border-radius: 8px; padding: 1rem;
    height: 280px; overflow-y: auto;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 0.75rem; line-height: 1.5; color: #e2e8f0;
}
.log-system { color: #94a3b8; }
.log-client { color: #38bdf8; }
.log-round { color: #c084fc; }

/* Performance Metric Sub-cards */
.metrics-grid {
    display: flex; gap: 1rem; height: 100%; align-items: stretch;
}
.metric-box {
    flex: 1; border: 1px solid var(--border-color); border-radius: 8px;
    padding: 1rem; display: flex; flex-direction: column; justify-content: center; align-items: center;
}
.metric-label { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; margin-bottom: 0.5rem; }
.metric-value { font-size: 1.75rem; font-weight: 700; color: var(--color-primary); margin-bottom: 0.25rem; }
.metric-trend { font-size: 0.65rem; font-weight: 600; }
.trend-up { color: var(--color-success); }
.trend-down { color: var(--color-danger); }

/* Client Rows */
.client-row {
    display: flex; align-items: center; gap: 8px; padding: 0.3rem 0;
}
.client-name { font-size: 0.75rem; color: var(--text-primary); font-weight: 500; min-width: 55px; display: flex; align-items: center; gap: 4px; }
.client-bar-bg { flex: 1; height: 6px; background: var(--border-color); border-radius: 3px; overflow: hidden; }
.client-bar-fill { height: 100%; background: var(--color-success); border-radius: 3px; transition: width 0.3s ease; }
.client-status { font-size: 0.7rem; color: var(--text-secondary); min-width: 35px; text-align: right; }

/* Encrypted Block */
.enc-block {
    background: var(--bg-main); border: 1px solid var(--border-color); border-radius: 6px;
    padding: 0.4rem 0.6rem; font-family: monospace; font-size: 0.7rem; color: var(--text-secondary);
    margin-bottom: 0.4rem; display: flex; align-items: center; gap: 6px;
}
.enc-icon { color: var(--color-encryption); }

/* Ring Signatures */
.ring-row { display: flex; align-items: center; gap: 8px; padding: 0.4rem 0; border-bottom: 1px solid var(--border-color); }
.ring-row:last-child { border-bottom: none; }
.ring-status { font-size: 0.75rem; font-weight: 500; }
.ring-valid { color: var(--color-success); }

/* Server Block */
.server-block {
    background: color-mix(in srgb, var(--color-primary) 10%, transparent); border: 1px solid color-mix(in srgb, var(--color-primary) 30%, transparent); border-radius: 12px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;
}
.server-icon { background: var(--color-primary); color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 700; letter-spacing: 1px; margin-bottom: 0.5rem; }

/* Threshold Parties */
.party-grid { display: flex; justify-content: center; gap: 8px; margin-bottom: 1rem; }
.party-dot {
    width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 600; flex-direction: column;
}
.party-active { background: color-mix(in srgb, var(--color-success) 15%, transparent); color: var(--color-success); border: 1px solid color-mix(in srgb, var(--color-success) 40%, transparent); }
.party-inactive { background: var(--border-color); color: var(--text-muted); border: 1px solid transparent; }
.decryption-box {
    border: 1px solid var(--border-color); border-radius: 6px; padding: 0.5rem;
    text-align: center; font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.5rem;
}

/* Aggregation */
.agg-block { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; }
.agg-icon {
    width: 64px; height: 64px; border-radius: 50%; border: 2px solid var(--color-warning);
    display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: var(--color-warning); margin-bottom: 1rem;
}
.agg-text { font-size: 0.75rem; font-weight: 600; color: var(--color-warning); }

/* Bottom Status Bar */
.bottom-status-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--bg-card); border-top: 1px solid var(--border-color);
    padding: 0.75rem 1.5rem; margin: 1.5rem -1rem -1rem -1rem;
}
.status-group { display: flex; align-items: center; gap: 1.5rem; }
.status-item { font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.3rem; }
.status-badge { background: color-mix(in srgb, var(--color-primary) 10%, transparent); color: var(--color-primary); border: 1px solid color-mix(in srgb, var(--color-primary) 30%, transparent); padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
/* Active Pulse Animation */
.active-pulse {
    animation: clientPulse 1.5s infinite;
}
@keyframes clientPulse {
    0% { opacity: 1; box-shadow: 0 0 5px var(--color-warning); border-color: var(--color-warning) !important; color: var(--color-warning) !important; }
    50% { opacity: 0.7; box-shadow: 0 0 15px var(--color-warning); border-color: var(--color-warning) !important; color: var(--color-warning) !important; }
    100% { opacity: 1; box-shadow: 0 0 5px var(--color-warning); border-color: var(--color-warning) !important; color: var(--color-warning) !important; }
}

/* Math Panel */
.math-panel {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
}
.math-panel-header {
    font-size: 1rem; font-weight: 700;
    color: var(--color-primary); margin-bottom: 1rem;
    display: flex; align-items: center; gap: 0.8rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.6rem;
}
.math-focus-badge {
    background: color-mix(in srgb, var(--color-primary) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--color-primary) 30%, transparent);
    color: var(--color-primary); padding: 0.1rem 0.6rem;
    border-radius: 20px; font-size: 0.75rem;
    font-weight: 600;
}
.math-block {
    background: var(--bg-main);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.8rem;
}
.math-block-title {
    color: var(--text-primary); font-size: 0.88rem;
    font-weight: 700; margin-bottom: 0.7rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.2px;
}
.math-row {
    display: flex; align-items: flex-start;
    gap: 1rem; padding: 0.3rem 0;
    font-size: 0.82rem; border-bottom: 1px solid var(--border-color);
}
.math-row:last-child { border-bottom: none; }
.math-label {
    color: var(--text-secondary); min-width: 200px;
    flex-shrink: 0; font-size: 0.8rem;
    font-family: 'Inter', sans-serif; font-weight: 500;
}
.math-value {
    font-family: 'Inter', sans-serif; color: var(--text-primary);
    font-size: 0.82rem; word-break: break-all;
    line-height: 1.5;
}
.math-value.mono {
    font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
    font-size: 0.75rem;
}
.math-arrow {
    text-align: center; color: var(--text-muted);
    font-size: 1rem; padding: 0.3rem 0;
}

</style>
"""
