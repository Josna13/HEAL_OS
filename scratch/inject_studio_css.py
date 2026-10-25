import os, sys, re, subprocess, py_compile
sys.path.insert(0, os.path.abspath('.'))

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add new CSS
css_anchor = '/* Gantt Blocks */'
new_css = """  /* CPU Execution Studio Styles */
  .studio-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    background: #0c1322;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 12px;
  }
  .algo-selector-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }
  .algo-card {
    background: #0c1322;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    cursor: pointer;
    transition: 0.2s;
    text-align: left;
  }
  .algo-card:hover {
    border-color: var(--border-highlight);
    background: #111a30;
  }
  .algo-card.active {
    background: #0f2744;
    border-color: var(--accent-cyan);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.25);
  }
  .algo-card-title {
    font-weight: 800;
    font-size: 0.85rem;
    color: #f8fafc;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .algo-card-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
    line-height: 1.3;
  }

  .exec-lane-row {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #080f1e;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
  }
  .exec-lane-row:hover {
    background: #0f1c35;
    border-color: var(--accent-cyan);
  }
  .exec-lane-row.selected {
    border-color: #f59e0b;
    background: #172033;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.25);
  }
  .exec-lane-badge {
    font-family: var(--font-mono);
    font-weight: 800;
    font-size: 0.8rem;
    padding: 3px 8px;
    border-radius: 4px;
    min-width: 55px;
    text-align: center;
    color: #fff;
  }
  .exec-lane-track {
    flex: 1;
    height: 14px;
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 4px;
    position: relative;
    overflow: hidden;
  }
  .exec-lane-progress {
    height: 100%;
    transition: width 0.2s linear;
  }
  .exec-lane-marker {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #94a3b8;
    z-index: 2;
  }

  .gantt-chart-container {
    position: relative;
    background: #060b17;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
    overflow-x: auto;
  }
  .gantt-time-ruler {
    display: flex;
    position: relative;
    height: 22px;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 6px;
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-dim);
  }
  .gantt-playback-cursor {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #f43f5e;
    box-shadow: 0 0 8px #f43f5e;
    z-index: 10;
    pointer-events: none;
    transition: left 0.12s linear;
  }
  .gantt-playback-cursor::after {
    content: '▲';
    position: absolute;
    bottom: -13px;
    left: -4px;
    color: #f43f5e;
    font-size: 10px;
  }

  .ready-token-card {
    display: inline-flex;
    flex-direction: column;
    background: #0b1a2e;
    border: 1px solid #0284c7;
    border-radius: 6px;
    padding: 6px 10px;
    min-width: 95px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .ready-token-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 8px rgba(2, 132, 199, 0.4);
  }

  .inspector-metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(75px, 1fr));
    gap: 6px;
    margin: 8px 0;
  }
  .inspector-metric-box {
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 4px;
    padding: 5px 6px;
    text-align: center;
  }
  .inspector-metric-lbl {
    font-size: 0.63rem;
    color: var(--text-dim);
    text-transform: uppercase;
  }
  .inspector-metric-val {
    font-size: 0.82rem;
    font-weight: 800;
    color: #38bdf8;
    font-family: var(--font-mono);
  }
"""

if '.studio-toolbar' not in code:
    code = code.replace(css_anchor, new_css + "\n  " + css_anchor)
    print("Injected Studio CSS!")

# Verify
assert '.studio-toolbar' in code
print("CSS verification successful!")
