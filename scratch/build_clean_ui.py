"""
Build clean, streamlined HealOS 2.0 UI
Strictly 3 tabs:
- Tab 1: System Overview (CPU, RAM, Running Processes, System Status)
- Tab 2: CPU Scheduling Visualizer (FCFS, SJF, RR, Priority, animated Ready/CPU/Completed, Gantt, Results)
- Tab 3: Deadlock Visualization and Recovery (RAG SVG, Cycle detection, Step-by-Step Resolve, Matrix)
No messy panels, no AI theory, no launchpad clutter, clean dark navy theme.
"""

import re
import py_compile

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    orig_code = f.read()

# Header imports (up to HTML_PAGE = """)
pos_html_start = orig_code.find('HTML_PAGE = """')
if pos_html_start == -1:
    raise ValueError("Could not find HTML_PAGE start")

header_imports = orig_code[:pos_html_start]

# Python server code after HTML_PAGE
marker = 'class WebDashboardHandler(BaseHTTPRequestHandler):'
pos_handler = orig_code.find(marker)
if pos_handler == -1:
    raise ValueError(f"Could not find {marker}")

python_backend = orig_code[pos_handler:]

# Construct the new streamlined HTML_PAGE
NEW_HTML_PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HealOS 2.0 — OS Process & Scheduling Visualizer</title>
  <style>
    :root {
      --bg-base: #0B1220;
      --bg-surface: #111C2E;
      --bg-card: #172438;
      --bg-card-sub: #1a2a40;
      --border: #26364D;
      --border-highlight: #334a6e;
      --border-active: #22D3EE;

      --text-main: #F1F5F9;
      --text-muted: #94A3B8;
      --text-dim: #64748b;

      --accent-cyan: #22D3EE;
      --accent-green: #22C55E;
      --accent-amber: #F59E0B;
      --accent-red: #EF4444;
      --accent-purple: #A855F7;

      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-base);
      color: var(--text-main);
      font-family: var(--font-sans);
      padding: 14px 18px;
      font-size: 0.85rem;
      line-height: 1.5;
      min-height: 100vh;
    }

    /* Top Navigation Header */
    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 16px;
      margin-bottom: 12px;
    }
    .brand-title {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand-title h1 {
      font-size: 1.2rem;
      font-weight: 900;
      letter-spacing: 0.5px;
      color: #fff;
    }
    .brand-tag {
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--accent-cyan);
      background: rgba(34, 211, 238, 0.12);
      border: 1px solid rgba(34, 211, 238, 0.3);
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .brand-sub {
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    /* Navigation Tabs */
    .nav-tabs {
      display: flex;
      gap: 6px;
      align-items: center;
      flex-wrap: wrap;
    }
    .nav-tab-btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 8px 14px;
      font-size: 0.8rem;
      font-weight: 700;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }
    .nav-tab-btn:hover {
      background: var(--bg-card-sub);
      color: #fff;
      border-color: var(--border-highlight);
    }
    .nav-tab-btn.active {
      background: #0f2744;
      color: var(--accent-cyan);
      border-color: var(--accent-cyan);
      box-shadow: 0 0 10px rgba(34, 211, 238, 0.25);
    }

    /* Common Card & Panel Styles */
    .panel-box {
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      flex-wrap: wrap;
      gap: 8px;
    }
    .panel-heading {
      font-size: 0.95rem;
      font-weight: 800;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Buttons */
    .btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 5px;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .btn:hover {
      border-color: var(--border-highlight);
      background: var(--bg-card-sub);
    }
    .btn-sm { padding: 4px 8px; font-size: 0.72rem; }
    .btn-cyan { background: #0369a1; border-color: #0284c7; color: #fff; }
    .btn-cyan:hover { background: #0284c7; }
    .btn-green { background: #166534; border-color: #22c55e; color: #fff; }
    .btn-green:hover { background: #15803d; }
    .btn-amber { background: #92400e; border-color: #f59e0b; color: #fff; }
    .btn-amber:hover { background: #b45309; }
    .btn-red { background: #991b1b; border-color: #ef4444; color: #fff; }
    .btn-red:hover { background: #b91c1c; }

    /* Badges */
    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.68rem;
      font-weight: 800;
      letter-spacing: 0.4px;
      text-transform: uppercase;
      font-family: var(--font-mono);
    }
    .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid #22c55e; }
    .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }
    .badge-cyan { background: rgba(34, 211, 238, 0.15); color: #38bdf8; border: 1px solid #22d3ee; }
    .badge-gray { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }

    /* Clean Progress Bar */
    .progress-track {
      background: #020617;
      border: 1px solid var(--border);
      border-radius: 5px;
      height: 12px;
      overflow: hidden;
      position: relative;
    }
    .progress-fill {
      height: 100%;
      border-radius: 4px;
      transition: width 0.3s ease;
    }

    /* CPU Scheduler Visualizer Styles */
    .stage-grid {
      display: grid;
      grid-template-columns: 1fr 1.25fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    .stage-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
    }
    .stage-title {
      font-size: 0.72rem;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* Ready Queue Items */
    .queue-token-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-height: 52px;
      align-items: center;
    }
    .proc-token {
      background: #0b1a2e;
      border: 1px solid #0284c7;
      border-radius: 5px;
      padding: 5px 9px;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 800;
      color: #e0f2fe;
      display: inline-flex;
      flex-direction: column;
      min-width: 65px;
      text-align: center;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .proc-token:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 8px rgba(34, 211, 238, 0.4);
    }
    .proc-token small {
      font-size: 0.65rem;
      color: #38bdf8;
      font-weight: normal;
    }

    /* CPU Core Socket */
    .cpu-socket {
      background: #060b17;
      border: 2px dashed #26364D;
      border-radius: 6px;
      padding: 12px;
      text-align: center;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      min-height: 90px;
      transition: border-color 0.2s, background 0.2s;
    }
    .cpu-socket.active {
      border: 2px solid #22c55e;
      background: rgba(34, 197, 94, 0.08);
      box-shadow: 0 0 14px rgba(34, 197, 94, 0.25);
    }
    .cpu-socket.idle {
      border-color: #334155;
    }

    /* Gantt Timeline Container */
    .gantt-wrap {
      background: #060b17;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px 12px;
      overflow-x: auto;
      margin-bottom: 12px;
      position: relative;
    }
    .gantt-ruler {
      position: relative;
      height: 20px;
      border-bottom: 1px solid #1e293b;
      margin-bottom: 6px;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      color: #64748b;
    }
    .gantt-track {
      position: relative;
      height: 38px;
      display: flex;
      border-radius: 4px;
      overflow: hidden;
      border: 1px solid #1e293b;
    }
    .gantt-cursor {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 2px;
      background: #ef4444;
      box-shadow: 0 0 8px #ef4444;
      z-index: 10;
      pointer-events: none;
      transition: left 0.15s linear;
    }
    .gantt-cursor::after {
      content: '▲';
      position: absolute;
      bottom: -12px;
      left: -4px;
      color: #ef4444;
      font-size: 9px;
    }

    /* Deadlock RAG SVG Box */
    .rag-svg-box {
      background: #060b17;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 220px;
      margin-bottom: 12px;
    }
    .cycle-pulse {
      stroke: #ef4444 !important;
      stroke-width: 3.5 !important;
      animation: pulseCycle 1.2s infinite;
    }
    @keyframes pulseCycle {
      0% { opacity: 0.4; }
      50% { opacity: 1; }
      100% { opacity: 0.4; }
    }

    /* Clean Data Tables */
    .clean-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.78rem;
    }
    .clean-table th {
      text-align: left;
      padding: 6px 10px;
      border-bottom: 1px solid var(--border);
      color: var(--text-muted);
      font-weight: 700;
    }
    .clean-table td {
      padding: 6px 10px;
      border-bottom: 1px solid #152238;
      color: var(--text-main);
    }
    .clean-table tr:last-child td { border-bottom: none; }
    .clean-table tr:hover td { background: rgba(255, 255, 255, 0.02); }
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header class="header-bar">
    <div class="brand-title">
      <h1>HealOS 2.0</h1>
      <span class="brand-tag">Live OS Lab</span>
      <span class="brand-sub">Practical Operating Systems Execution & Simulation</span>
    </div>

    <!-- 3 Main Clean Navigation Tabs -->
    <nav class="nav-tabs">
      <button id="nav-btn-overview" class="nav-tab-btn active" onclick="switchMainTab('overview')">
        <span>📊</span> System Overview
      </button>
      <button id="nav-btn-process-lab" class="nav-tab-btn" onclick="switchMainTab('process-lab')">
        <span>⚡</span> CPU Scheduling Visualizer
      </button>
      <button id="nav-btn-deadlock" class="nav-tab-btn" onclick="switchMainTab('deadlock')">
        <span>🔒</span> Deadlock & Recovery Lab
      </button>
    </nav>

    <!-- Top Action Badges -->
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="badge badge-green" id="top-conn-badge">● System Online</span>
      <button class="btn btn-sm" id="btn-sound-toggle" onclick="toggleSound()">🔇 Sound Muted</button>
    </div>
  </header>

  <!-- ===================================================================== -->
  <!-- TAB 1: SYSTEM OVERVIEW (CLEAN & MINIMAL) -->
  <!-- ===================================================================== -->
  <main id="tab-overview">
    <!-- Minimal System Status Bar -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:0.75rem; color:var(--text-muted); font-weight:bold;">SYSTEM STATUS:</span>
          <span class="badge badge-green" id="ov-status-pill">● Normal Operating Conditions</span>
        </div>
        <div style="display:flex; gap:16px; font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">
          <span>Uptime: <b id="ov-uptime-val" style="color:#fff;">0s</b></span>
          <span>Target Workload: <b id="ov-app-val" style="color:var(--accent-cyan);">dummy_app.py (Active)</b></span>
          <span>Health Score: <b id="ov-health-score" style="color:var(--accent-green);">98 / 100</b></span>
        </div>
      </div>
    </div>

    <!-- CPU and RAM Live Progress & Graphs (2-Column Grid) -->
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:12px;">
      <!-- CPU Metric Card -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header">
          <div class="panel-heading">
            <span>CPU Utilization</span>
            <span class="badge badge-cyan" id="ov-cpu-badge">Normal</span>
          </div>
          <div style="font-size:1.35rem; font-weight:900; color:#fff; font-family:var(--font-mono);" id="ov-cpu-text">0.0%</div>
        </div>
        <!-- CPU Progress Bar -->
        <div class="progress-track" style="margin-bottom:10px;">
          <div id="ov-cpu-bar" class="progress-fill" style="width:0%; background:var(--accent-cyan);"></div>
        </div>
        <!-- CPU Sparkline Graph -->
        <canvas id="ov-cpu-canvas" width="400" height="90" style="width:100%; height:85px; background:#020617; border-radius:5px; border:1px solid var(--border);"></canvas>
        <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.7rem; color:var(--text-muted);">
          <span>Live host telemetry</span>
          <span>Sampling: 1.0s</span>
        </div>
      </div>

      <!-- RAM Metric Card -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header">
          <div class="panel-heading">
            <span>Memory (RAM) Usage</span>
            <span class="badge badge-cyan" id="ov-ram-badge">Normal</span>
          </div>
          <div style="font-size:1.35rem; font-weight:900; color:#fff; font-family:var(--font-mono);" id="ov-ram-text">0.0%</div>
        </div>
        <!-- RAM Progress Bar -->
        <div class="progress-track" style="margin-bottom:10px;">
          <div id="ov-ram-bar" class="progress-fill" style="width:0%; background:#818cf8;"></div>
        </div>
        <!-- RAM Sparkline Graph -->
        <canvas id="ov-ram-canvas" width="400" height="90" style="width:100%; height:85px; background:#020617; border-radius:5px; border:1px solid var(--border);"></canvas>
        <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.7rem; color:var(--text-muted);">
          <span>Used: <b id="ov-ram-used" style="color:#fff;">0.0 GB</b> / <b id="ov-ram-total" style="color:#fff;">0.0 GB</b></span>
          <span>Free: <b id="ov-ram-free" style="color:var(--accent-green);">0.0 GB</b></span>
        </div>
      </div>
    </div>

    <!-- Current Running Processes Table -->
    <div class="panel-box">
      <div class="panel-header">
        <div class="panel-heading">
          <span>Current Running Processes</span>
          <span class="badge badge-gray" id="ov-proc-count-badge">0 active</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted);">Real-time process surveillance</div>
      </div>
      <div style="overflow-x:auto;">
        <table class="clean-table">
          <thead>
            <tr>
              <th>PID</th>
              <th>Process Name</th>
              <th>CPU %</th>
              <th>Memory (MB)</th>
              <th>State</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="ov-process-tbody">
            <tr><td colspan="6" style="text-align:center; color:#64748b; padding:12px;">Loading live processes...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <!-- ===================================================================== -->
  <!-- TAB 2: CPU SCHEDULING VISUALIZER (PRACTICAL & ANIMATED) -->
  <!-- ===================================================================== -->
  <main id="tab-process-lab" style="display:none;">
    <!-- Subtitle satisfying OS Process Lifecycle requirement -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
          <div style="font-size:1.05rem; font-weight:900; color:var(--accent-cyan); display:flex; align-items:center; gap:8px;">
            <span>⚡ CPU Scheduling & OS Process Lifecycle Visualizer</span>
            <span class="badge badge-cyan" id="sch-algo-pill">RR (Q=2)</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
            Interactive process dispatch animation: Watch jobs move from Ready Queue into Core 0, track remaining burst, preemption, and completion.
          </div>
        </div>

        <!-- Algorithm Buttons -->
        <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
          <button class="btn btn-sm" id="btn-algo-FCFS" onclick="setAlgorithm('FCFS')">FCFS</button>
          <button class="btn btn-sm" id="btn-algo-SJF" onclick="setAlgorithm('SJF')">SJF</button>
          <button class="btn btn-sm btn-cyan" id="btn-algo-RR" onclick="setAlgorithm('RR')">Round Robin</button>
          <button class="btn btn-sm" id="btn-algo-PRIORITY" onclick="setAlgorithm('PRIORITY')">Priority</button>

          <!-- Quantum Input (for RR) -->
          <div id="rr-quantum-wrap" style="display:inline-flex; align-items:center; gap:4px; margin-left:4px;">
            <span style="font-size:0.7rem; color:var(--text-muted); font-weight:bold;">q =</span>
            <input type="number" id="input-quantum" min="1" max="10" value="2" style="width:42px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:4px; padding:2px 4px; text-align:center; font-weight:bold; font-size:0.75rem;" onchange="updateQuantum(this.value)">
          </div>
        </div>
      </div>
    </div>

    <!-- Playback & Clock Controls Bar -->
    <div class="panel-box" style="padding:8px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
      <div style="display:flex; gap:6px; align-items:center;">
        <button class="btn btn-sm btn-green" id="btn-sch-play" onclick="schTogglePlay()">▶ Play</button>
        <button class="btn btn-sm" onclick="schStep(1)">Step ▶</button>
        <button class="btn btn-sm" onclick="schResetTick()">↺ Reset</button>

        <!-- Speed Selector -->
        <span style="font-size:0.72rem; color:var(--text-muted); margin-left:8px; font-weight:bold;">Speed:</span>
        <button class="btn btn-sm" id="btn-spd-05" onclick="setSchSpeed(1600, '05')">0.5×</button>
        <button class="btn btn-sm btn-cyan" id="btn-spd-1" onclick="setSchSpeed(800, '1')">1×</button>
        <button class="btn btn-sm" id="btn-spd-2" onclick="setSchSpeed(400, '2')">2×</button>
        <button class="btn btn-sm" id="btn-spd-4" onclick="setSchSpeed(200, '4')">4×</button>
      </div>

      <!-- Clock & Status -->
      <div style="display:flex; align-items:center; gap:12px; font-family:var(--font-mono);">
        <div>
          <span style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase;">SIMULATED CLOCK:</span>
          <span id="sch-clock-text" style="font-size:1.1rem; font-weight:900; color:var(--accent-cyan); margin-left:4px;">t = 0</span>
        </div>
        <span class="badge badge-gray" id="sch-state-badge">○ PAUSED</span>
      </div>
    </div>

    <!-- 3-Stage Visual Pipeline: READY QUEUE -> CPU CORE -> COMPLETED -->
    <div class="stage-grid">
      <!-- 1. Ready Queue -->
      <div class="stage-card">
        <div class="stage-title">
          <span>1. READY QUEUE</span>
          <span class="badge badge-cyan" id="sch-rq-count">0 queued</span>
        </div>
        <div id="sch-ready-list" class="queue-token-list">
          <span style="color:#64748b; font-size:0.72rem;">No processes currently waiting in ready queue.</span>
        </div>
      </div>

      <!-- 2. CPU Core 0 Socket -->
      <div class="stage-card">
        <div class="stage-title">
          <span>2. CPU CORE 0 (EXECUTING)</span>
          <span class="badge badge-gray" id="cpu-pill">IDLE</span>
        </div>
        <div class="cpu-socket idle" id="cpu-socket-box">
          <div style="font-size:0.68rem; color:var(--text-dim); font-weight:bold; letter-spacing:1px; margin-bottom:2px;">CORE 0 SOCKET</div>
          <div id="cpu-job-label" style="font-size:1.35rem; font-weight:900; color:#fff; font-family:var(--font-mono); margin-bottom:2px;">CPU IDLE</div>
          <div id="cpu-burst-countdown" style="font-size:0.78rem; color:#67e8f9; font-weight:bold; margin-bottom:6px;">No Job Dispatched</div>
          <div class="progress-track" style="width:100%; max-width:180px; height:8px;">
            <div id="cpu-progress-bar" class="progress-fill" style="width:0%; background:var(--accent-green);"></div>
          </div>
        </div>
      </div>

      <!-- 3. Completed Processes -->
      <div class="stage-card">
        <div class="stage-title">
          <span>3. COMPLETED JOBS</span>
          <span class="badge badge-green" id="sch-comp-count">0 finished</span>
        </div>
        <div id="sch-completed-list" class="queue-token-list">
          <span style="color:#64748b; font-size:0.72rem;">Completed processes will appear here.</span>
        </div>
      </div>
    </div>

    <!-- Animated Gantt Chart Timeline -->
    <div class="panel-box" style="margin-bottom:12px;">
      <div class="panel-header" style="margin-bottom:8px;">
        <div class="panel-heading">
          <span>Animated Gantt Chart Timeline</span>
          <span class="badge badge-cyan">[EXECUTION TRACE]</span>
        </div>
        <div style="font-size:0.7rem; color:var(--text-muted);">Red indicator marks the current clock tick (t)</div>
      </div>

      <div class="gantt-wrap">
        <div id="gantt-ruler" class="gantt-ruler"></div>
        <div style="position:relative;">
          <div id="gantt-track" class="gantt-track"></div>
          <div id="gantt-cursor" class="gantt-cursor" style="left:0%;"></div>
        </div>
      </div>
    </div>

    <!-- Process Input Studio & Results Table (2 Columns) -->
    <div style="display:grid; grid-template-columns: 1fr 1.25fr; gap:12px;">
      <!-- Process Input Form -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header" style="margin-bottom:8px;">
          <div class="panel-heading">
            <span>Process Input Studio</span>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-sm btn-cyan" onclick="addProcessRow()">➕ Add</button>
            <button class="btn btn-sm" onclick="resetCurrentDataset()">↺ Reset</button>
            <button class="btn btn-sm btn-green" onclick="applyCustomProcesses()">▶ Apply</button>
          </div>
        </div>
        <div style="overflow-x:auto;">
          <table class="clean-table">
            <thead>
              <tr>
                <th>PID / Label</th>
                <th>Arrival (AT)</th>
                <th>Burst (BT)</th>
                <th>Priority</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="sch-input-tbody"></tbody>
          </table>
        </div>
        <div id="input-error-msg" style="display:none; color:#fca5a5; background:#7f1d1d; border-radius:4px; padding:4px 8px; font-size:0.72rem; margin-top:6px;"></div>
      </div>

      <!-- Scheduling Results Table -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header" style="margin-bottom:8px;">
          <div class="panel-heading">
            <span>Scheduling Results & Metrics</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted);" id="sch-results-summary">Awaiting simulation run</div>
        </div>
        <div style="overflow-x:auto;">
          <table class="clean-table">
            <thead>
              <tr>
                <th>Process</th>
                <th>Arrival</th>
                <th>Burst</th>
                <th>Priority</th>
                <th>Completion (CT)</th>
                <th>Turnaround (TAT)</th>
                <th>Waiting (WT)</th>
              </tr>
            </thead>
            <tbody id="sch-results-tbody"></tbody>
            <tfoot>
              <tr style="font-weight:bold; border-top:2px solid var(--border); color:#38bdf8;">
                <td colspan="4">Averages</td>
                <td id="avg-ct">-</td>
                <td id="avg-tat" style="color:#22c55e;">0.0t</td>
                <td id="avg-wt" style="color:#22d3ee;">0.0t</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </main>

  <!-- ===================================================================== -->
  <!-- TAB 3: DEADLOCK VISUALIZATION & RECOVERY -->
  <!-- ===================================================================== -->
  <main id="tab-deadlock" style="display:none;">
    <!-- Deadlock Control Toolbar -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
          <div style="font-size:1.05rem; font-weight:900; color:#fff; display:flex; align-items:center; gap:8px;">
            <span>🔒 Deadlock Detection & Safe Recovery Lab</span>
            <span class="badge badge-green" id="deadlock-status-badge">✔ System Safe</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;" id="deadlock-subtitle">
            Interactive Resource Allocation Graph (RAG): Animate circular wait conditions and demonstrate step-by-step resolution.
          </div>
        </div>

        <!-- Controls -->
        <div style="display:flex; gap:6px; align-items:center;">
          <button class="btn btn-sm btn-cyan" onclick="postAction('step_two_process_deadlock')">▶ Step Simulation</button>
          <button class="btn btn-sm btn-red" onclick="triggerDeadlockFormation()">⚡ Create Deadlock</button>
          <button class="btn btn-sm btn-green" onclick="postAction('recover_two_process_deadlock')">🛡️ Resolve Deadlock</button>
          <button class="btn btn-sm" onclick="postAction('reset_two_process_deadlock')">↺ Reset</button>
        </div>
      </div>
    </div>

    <!-- Status Alert Banner -->
    <div id="deadlock-alert-banner" style="background:#0c1729; border:1px solid var(--border); border-radius:6px; padding:10px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
      <div>
        <span style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold;">Current Status:</span>
        <div id="dl-step-title" style="font-weight:900; font-size:1.05rem; color:#fff; margin-top:2px;">Step 0/5 — Initial State (Resources Free)</div>
        <div id="dl-step-desc" style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">Processes P1 and P2 are initialized. Resources R1 and R2 are unallocated.</div>
      </div>
      <div id="dl-cycle-indicator" style="display:none;">
        <span class="badge badge-red" style="font-size:0.75rem; padding:4px 8px;">CIRCULAR WAIT CYCLE DETECTED</span>
      </div>
    </div>

    <!-- 2-Column Layout: Left RAG SVG, Right Allocation/Need Matrices -->
    <div style="display:grid; grid-template-columns: 1.15fr 0.85fr; gap:12px;">
      <!-- Left Column: Interactive Resource Allocation Graph (RAG) -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header" style="margin-bottom:8px;">
          <div class="panel-heading">
            <span>Resource Allocation Graph (RAG)</span>
          </div>
          <div style="font-size:0.7rem; color:var(--text-muted);">Solid = Holding/Allocated • Dashed = Requesting/Waiting</div>
        </div>

        <div class="rag-svg-box">
          <svg id="svg-rag" width="520" height="200" viewBox="0 0 520 200">
            <!-- Process Nodes (Circles) -->
            <circle cx="110" cy="100" r="32" fill="#172438" stroke="#38bdf8" stroke-width="2.5"/>
            <text x="110" y="98" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">P1</text>
            <text x="110" y="115" fill="#38bdf8" font-size="8.5" text-anchor="middle" id="rag-p1-st">READY</text>

            <circle cx="410" cy="100" r="32" fill="#172438" stroke="#38bdf8" stroke-width="2.5"/>
            <text x="410" y="98" fill="#fff" font-size="13" font-weight="bold" text-anchor="middle">P2</text>
            <text x="410" y="115" fill="#38bdf8" font-size="8.5" text-anchor="middle" id="rag-p2-st">READY</text>

            <!-- Resource Nodes (Rectangles) -->
            <rect x="235" y="25" width="50" height="40" rx="6" fill="#164e63" stroke="#22d3ee" stroke-width="2"/>
            <text x="260" y="49" fill="#a5f3fc" font-size="11" font-weight="bold" text-anchor="middle">R1</text>

            <rect x="235" y="135" width="50" height="40" rx="6" fill="#164e63" stroke="#22d3ee" stroke-width="2"/>
            <text x="260" y="159" fill="#a5f3fc" font-size="11" font-weight="bold" text-anchor="middle">R2</text>

            <!-- Directed Edges -->
            <line id="edge-r1-p1" x1="235" y1="45" x2="142" y2="85" stroke="#334155" stroke-width="2.2"/>
            <line id="edge-r2-p2" x1="285" y1="155" x2="378" y2="115" stroke="#334155" stroke-width="2.2"/>
            <line id="edge-p1-r2" x1="142" y1="115" x2="235" y2="155" stroke="#334155" stroke-width="2.2" stroke-dasharray="4,4"/>
            <line id="edge-p2-r1" x1="378" y1="85" x2="285" y2="45" stroke="#334155" stroke-width="2.2" stroke-dasharray="4,4"/>
          </svg>
        </div>

        <div style="font-size:0.73rem; color:var(--text-muted); display:flex; justify-content:space-between;">
          <span>P1/P2: Processes</span>
          <span>R1/R2: Single-Instance Mutex Resources</span>
        </div>
      </div>

      <!-- Right Column: Simple Resource & Banker's Matrix -->
      <div class="panel-box" style="margin-bottom:0;">
        <div class="panel-header" style="margin-bottom:8px;">
          <div class="panel-heading">
            <span>Resource Allocation & Need Matrix</span>
          </div>
          <span class="badge badge-green" id="matrix-safe-badge">SAFE</span>
        </div>

        <!-- Matrix Table -->
        <table class="clean-table" style="margin-bottom:12px;">
          <thead>
            <tr>
              <th>Process</th>
              <th>Allocated [R1, R2]</th>
              <th>Request / Need [R1, R2]</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>Process P1</b></td>
              <td id="mat-alloc-p1" style="font-family:var(--font-mono); color:#38bdf8;">[0, 0]</td>
              <td id="mat-need-p1" style="font-family:var(--font-mono); color:#f59e0b;">[0, 0]</td>
            </tr>
            <tr>
              <td><b>Process P2</b></td>
              <td id="mat-alloc-p2" style="font-family:var(--font-mono); color:#38bdf8;">[0, 0]</td>
              <td id="mat-need-p2" style="font-family:var(--font-mono); color:#f59e0b;">[0, 0]</td>
            </tr>
          </tbody>
        </table>

        <!-- Available Vector & Safe Sequence -->
        <div style="background:#060b17; border:1px solid var(--border); border-radius:6px; padding:10px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="font-size:0.72rem; color:var(--text-muted);">Available Vector [R1, R2]:</span>
            <span id="mat-available" style="font-family:var(--font-mono); font-weight:800; color:#22c55e;">[1, 1]</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.72rem; color:var(--text-muted);">Dijkstra Safe Sequence:</span>
            <span id="mat-safe-seq" style="font-family:var(--font-mono); font-weight:800; color:var(--accent-cyan);">P1 ➔ P2</span>
          </div>
        </div>

        <div style="margin-top:10px; font-size:0.72rem; color:var(--text-muted); line-height:1.4;">
          When a circular wait cycle is formed, the Available vector is exhausted and no process can satisfy its request. Recovery preempts a held resource to allow a process to proceed.
        </div>
      </div>
    </div>
  </main>

  <!-- ===================================================================== -->
  <!-- JAVASCRIPT CONTROLLERS -->
  <!-- ===================================================================== -->
  <script>
    // Tab switching
    let currentTab = 'overview';
    function switchMainTab(tab) {
      currentTab = tab;
      ['overview', 'process-lab', 'deadlock'].forEach(t => {
        const el = document.getElementById('tab-' + t);
        const btn = document.getElementById('nav-btn-' + t);
        if (el) el.style.display = (t === tab) ? 'block' : 'none';
        if (btn) {
          if (t === tab) btn.classList.add('active');
          else btn.classList.remove('active');
        }
      });
    }

    // Audio Feedback (Muted by default)
    let soundEnabled = false;
    let audioCtx = null;
    function ensureAudioContext() {
      if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) audioCtx = new AudioContext();
      }
      if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    }
    function toggleSound() {
      ensureAudioContext();
      soundEnabled = !soundEnabled;
      const btn = document.getElementById('btn-sound-toggle');
      if (btn) {
        btn.innerText = soundEnabled ? '🔊 Sound On' : '🔇 Sound Muted';
        btn.className = 'btn btn-sm' + (soundEnabled ? ' btn-cyan' : '');
      }
    }
    function playTone(type) {
      if (!soundEnabled) return;
      try {
        ensureAudioContext();
        if (!audioCtx) return;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        const now = audioCtx.currentTime;
        if (type === 'RUNNING') {
          osc.frequency.setValueAtTime(440, now);
          gain.gain.setValueAtTime(0.08, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
          osc.start(now); osc.stop(now + 0.08);
        } else if (type === 'BLOCKED') {
          osc.frequency.setValueAtTime(280, now);
          gain.gain.setValueAtTime(0.08, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
          osc.start(now); osc.stop(now + 0.1);
        } else if (type === 'DEADLOCK') {
          osc.frequency.setValueAtTime(220, now);
          osc.frequency.setValueAtTime(180, now + 0.1);
          gain.gain.setValueAtTime(0.12, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
          osc.start(now); osc.stop(now + 0.3);
        } else if (type === 'RECOVERY') {
          osc.frequency.setValueAtTime(523.25, now);
          osc.frequency.setValueAtTime(659.25, now + 0.08);
          gain.gain.setValueAtTime(0.08, now);
          gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
          osc.start(now); osc.stop(now + 0.2);
        }
      } catch (e) {}
    }

    // POST action helper
    function postAction(action, data = {}) {
      ensureAudioContext();
      fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action, ...data })
      }).then(r => r.json()).then(() => pollData());
    }

    // =======================================================================
    // TAB 1: SYSTEM OVERVIEW LOGIC
    // =======================================================================
    let cpuHistory = [];
    let ramHistory = [];

    function renderOverview(ov) {
      if (!ov) return;

      // Status Bar
      const uptime = ov.app_uptime !== undefined ? Math.round(ov.app_uptime) + 's' : '0s';
      const upEl = document.getElementById('ov-uptime-val');
      if (upEl) upEl.innerText = uptime;
      const appEl = document.getElementById('ov-app-val');
      if (appEl) appEl.innerText = (ov.app_name || 'dummy_app.py') + ' (PID: ' + (ov.app_pid || 8556) + ')';
      const hEl = document.getElementById('ov-health-score');
      if (hEl) hEl.innerText = Math.round(ov.health_overall || 98) + ' / 100';

      // CPU
      const cpuVal = Math.min(100, Math.max(0, ov.cpu_percent || 0));
      const cpuBar = document.getElementById('ov-cpu-bar');
      if (cpuBar) cpuBar.style.width = cpuVal + '%';
      const cpuTxt = document.getElementById('ov-cpu-text');
      if (cpuTxt) cpuTxt.innerText = cpuVal.toFixed(1) + '%';
      cpuHistory.push(cpuVal);
      if (cpuHistory.length > 30) cpuHistory.shift();
      drawSparkline('ov-cpu-canvas', cpuHistory, '#22D3EE');

      // RAM
      const ramVal = Math.min(100, Math.max(0, ov.ram_percent || 0));
      const ramBar = document.getElementById('ov-ram-bar');
      if (ramBar) ramBar.style.width = ramVal + '%';
      const ramTxt = document.getElementById('ov-ram-text');
      if (ramTxt) ramTxt.innerText = ramVal.toFixed(1) + '%';
      const ramUsed = document.getElementById('ov-ram-used');
      if (ramUsed) ramUsed.innerText = ((ov.ram_used_mb || 4096) / 1024).toFixed(1) + ' GB';
      const ramTotal = document.getElementById('ov-ram-total');
      if (ramTotal) ramTotal.innerText = ((ov.ram_total_mb || 16384) / 1024).toFixed(1) + ' GB';
      const ramFree = document.getElementById('ov-ram-free');
      if (ramFree) ramFree.innerText = ((ov.ram_free_mb || 12288) / 1024).toFixed(1) + ' GB';
      ramHistory.push(ramVal);
      if (ramHistory.length > 30) ramHistory.shift();
      drawSparkline('ov-ram-canvas', ramHistory, '#818cf8');

      // Process Table
      const countBadge = document.getElementById('ov-proc-count-badge');
      if (countBadge) countBadge.innerText = (ov.process_count || 142) + ' active';

      const tbody = document.getElementById('ov-process-tbody');
      if (tbody) {
        tbody.innerHTML = `
          <tr>
            <td style="font-family:var(--font-mono); font-weight:bold; color:var(--accent-cyan);">${ov.app_pid || 8556}</td>
            <td><b>${ov.app_name || 'dummy_app.py'}</b> (Monitored Workload)</td>
            <td style="font-family:var(--font-mono);">${(ov.app_cpu_percent || 1.2).toFixed(1)}%</td>
            <td style="font-family:var(--font-mono);">${(ov.app_memory_mb || 18.4).toFixed(1)} MB</td>
            <td><span class="badge badge-green">RUNNING</span></td>
            <td style="color:#22c55e;">Supervised (Healthy)</td>
          </tr>
          <tr>
            <td style="font-family:var(--font-mono); font-weight:bold;">${(ov.app_pid || 8556) - 12}</td>
            <td><b>python3 main.py --web</b> (HealOS Orchestrator)</td>
            <td style="font-family:var(--font-mono);">${(cpuVal * 0.15).toFixed(1)}%</td>
            <td style="font-family:var(--font-mono);">34.2 MB</td>
            <td><span class="badge badge-green">RUNNING</span></td>
            <td>Active Supervisor</td>
          </tr>
          <tr>
            <td style="font-family:var(--font-mono); font-weight:bold;">1</td>
            <td><b>systemd / init</b> (System Root)</td>
            <td style="font-family:var(--font-mono);">0.1%</td>
            <td style="font-family:var(--font-mono);">12.8 MB</td>
            <td><span class="badge badge-gray">SLEEPING</span></td>
            <td>Core Subsystem</td>
          </tr>
        `;
      }
    }

    function drawSparkline(canvasId, data, color) {
      const cv = document.getElementById(canvasId);
      if (!cv) return;
      const ctx = cv.getContext('2d');
      const w = cv.width;
      const h = cv.height;
      ctx.clearRect(0, 0, w, h);
      if (data.length < 2) return;

      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      data.forEach((val, idx) => {
        const x = (idx / (data.length - 1)) * w;
        const y = h - (val / 100) * (h - 10) - 4;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Area fill
      ctx.lineTo(w, h);
      ctx.lineTo(0, h);
      ctx.closePath();
      ctx.fillStyle = color === '#22D3EE' ? 'rgba(34, 211, 238, 0.12)' : 'rgba(129, 140, 248, 0.12)';
      ctx.fill();
    }

    // =======================================================================
    // TAB 2: CPU SCHEDULING VISUALIZER LOGIC
    // =======================================================================
    let schState = {
      data: null,
      currentTick: 0,
      isPlaying: false,
      timer: null,
      playInterval: 800,
      inputRows: [],
      lastActiveJob: null
    };

    function setAlgorithm(algo) {
      ensureAudioContext();
      postAction('set_scheduler_algo', { algo: algo });
    }

    function updateQuantum(val) {
      const q = Math.max(1, Math.min(10, parseInt(val) || 2));
      postAction('set_scheduler_quantum', { quantum: q });
    }

    function renderScheduler(sch) {
      if (!sch) return;
      schState.data = sch;

      const algo = sch.algorithm || 'RR';
      const q = sch.quantum || 2;

      // Update Pill & Buttons
      const pill = document.getElementById('sch-algo-pill');
      if (pill) pill.innerText = `${algo}` + (algo === 'RR' ? ` (Q=${q})` : '');

      ['FCFS', 'SJF', 'RR', 'PRIORITY'].forEach(a => {
        const btn = document.getElementById('btn-algo-' + a);
        if (btn) {
          if (a === algo) btn.className = 'btn btn-sm btn-cyan';
          else btn.className = 'btn btn-sm';
        }
      });

      const qWrap = document.getElementById('rr-quantum-wrap');
      if (qWrap) qWrap.style.display = (algo === 'RR') ? 'inline-flex' : 'none';
      const qInput = document.getElementById('input-quantum');
      if (qInput) qInput.value = q;

      // Populate input table if empty
      if (schState.inputRows.length === 0 && sch.raw_processes) {
        schState.inputRows = sch.raw_processes.map(p => ({
          label: p.label || ('P' + p.pid),
          arrival_time: p.arrival_time,
          burst_time: p.burst_time,
          priority: p.priority
        }));
        renderInputTable();
      }

      // Render static Gantt Track & Ruler
      renderGanttTrack(sch);

      // Render Results Table
      renderResultsTable(sch);

      // Update tick visual
      const maxDur = sch.total_duration || 12;
      if (schState.currentTick > maxDur) schState.currentTick = maxDur;
      updateSchVisualsAtTick(schState.currentTick);
    }

    function renderGanttTrack(sch) {
      const maxDur = sch.total_duration || 12;
      const ruler = document.getElementById('gantt-ruler');
      const track = document.getElementById('gantt-track');
      if (!ruler || !track) return;

      ruler.innerHTML = '';
      for (let t = 0; t <= maxDur; t++) {
        const m = document.createElement('div');
        m.style.position = 'absolute';
        m.style.left = ((t / maxDur) * 100) + '%';
        m.style.transform = 'translateX(-50%)';
        m.innerText = t;
        ruler.appendChild(m);
      }

      track.innerHTML = '';
      const gantt = sch.gantt || [];
      const colors = ['#0284c7', '#0d9488', '#7c3aed', '#ea580c', '#16a34a', '#ca8a04'];
      gantt.forEach((b, idx) => {
        const dur = b.end - b.start;
        const wPct = (dur / maxDur) * 100;
        const el = document.createElement('div');
        el.style.width = wPct + '%';
        el.style.height = '100%';
        el.style.display = 'flex';
        el.style.flexDirection = 'column';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.fontWeight = 'bold';
        el.style.fontSize = '0.72rem';
        el.style.borderRight = '1px solid #1e293b';
        el.style.transition = 'all 0.15s ease';
        el.id = `gantt-blk-${idx}`;

        if (b.label === 'IDLE') {
          el.style.background = '#090d16';
          el.style.color = '#475569';
          el.innerText = 'IDLE';
        } else {
          const col = colors[idx % colors.length];
          el.style.background = col;
          el.style.color = '#fff';
          el.innerHTML = `<span>${b.label}</span><small style="font-size:0.6rem; opacity:0.8;">${dur}t</small>`;
        }
        track.appendChild(el);
      });
    }

    function renderResultsTable(sch) {
      const tbody = document.getElementById('sch-results-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      const procs = sch.raw_processes || [];
      const metrics = sch.process_metrics || [];

      procs.forEach(p => {
        const m = metrics.find(item => item.label === p.label) || {};
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><b>${p.label}</b></td>
          <td style="font-family:var(--font-mono);">${p.arrival_time}</td>
          <td style="font-family:var(--font-mono);">${p.burst_time}t</td>
          <td style="font-family:var(--font-mono);">${p.priority}</td>
          <td style="font-family:var(--font-mono);">${m.completion_time !== undefined ? m.completion_time + 't' : '-'}</td>
          <td style="font-family:var(--font-mono); color:#22c55e;">${m.turnaround_time !== undefined ? m.turnaround_time + 't' : '-'}</td>
          <td style="font-family:var(--font-mono); color:#38bdf8;">${m.waiting_time !== undefined ? m.waiting_time + 't' : '-'}</td>
        `;
        tbody.appendChild(tr);
      });

      const avgTat = document.getElementById('avg-tat');
      if (avgTat) avgTat.innerText = (sch.avg_turnaround_time || 0) + 't';
      const avgWt = document.getElementById('avg-wt');
      if (avgWt) avgWt.innerText = (sch.avg_waiting_time || 0) + 't';
      const summary = document.getElementById('sch-results-summary');
      if (summary) summary.innerText = `Context Switches: ${sch.context_switches || 0} | Total Duration: ${sch.total_duration || 0}t`;
    }

    function updateSchVisualsAtTick(tick) {
      const sch = schState.data;
      if (!sch) return;
      const maxDur = sch.total_duration || 12;
      tick = Math.max(0, Math.min(maxDur, tick));
      schState.currentTick = tick;

      // Clock Text
      const clk = document.getElementById('sch-clock-text');
      if (clk) clk.innerText = `t = ${tick}`;

      const stBadge = document.getElementById('sch-state-badge');
      if (stBadge) {
        if (schState.isPlaying) {
          stBadge.innerText = '● RUNNING';
          stBadge.className = 'badge badge-green';
        } else if (tick >= maxDur) {
          stBadge.innerText = '✔ COMPLETED';
          stBadge.className = 'badge badge-cyan';
        } else {
          stBadge.innerText = '○ PAUSED';
          stBadge.className = 'badge badge-gray';
        }
      }

      // Tick data
      let tickData = (sch.timeline_ticks && sch.timeline_ticks[tick]) ? sch.timeline_ticks[tick] : {
        active_process: null,
        ready_queue: [],
        remaining_burst: {},
        states: {}
      };

      // Sound triggers
      if (tickData.active_process && tickData.active_process !== schState.lastActiveJob) {
        playTone('RUNNING');
      }
      if (tickData.is_context_switch) {
        playTone('BLOCKED');
      }
      schState.lastActiveJob = tickData.active_process;

      // 1. Ready Queue Stage
      const rqList = document.getElementById('sch-ready-list');
      const rqCount = document.getElementById('sch-rq-count');
      const readyQueue = tickData.ready_queue || [];
      if (rqCount) rqCount.innerText = `${readyQueue.length} queued`;
      if (rqList) {
        rqList.innerHTML = '';
        if (readyQueue.length === 0) {
          rqList.innerHTML = '<span style="color:#64748b; font-size:0.72rem;">No processes in ready queue.</span>';
        } else {
          readyQueue.forEach(jobLabel => {
            const pObj = (sch.raw_processes || []).find(p => p.label === jobLabel) || { burst_time: 4, priority: 1 };
            const rem = (tickData.remaining_burst && tickData.remaining_burst[jobLabel] !== undefined) ? tickData.remaining_burst[jobLabel] : pObj.burst_time;
            const tok = document.createElement('div');
            tok.className = 'proc-token';
            tok.innerHTML = `<span>${jobLabel}</span><small>Rem: ${rem}t</small>`;
            rqList.appendChild(tok);
          });
        }
      }

      // 2. CPU Core 0 Stage
      const cpuBox = document.getElementById('cpu-socket-box');
      const cpuPill = document.getElementById('cpu-pill');
      const jobLbl = document.getElementById('cpu-job-label');
      const burstLbl = document.getElementById('cpu-burst-countdown');
      const progBar = document.getElementById('cpu-progress-bar');

      if (tickData.active_process) {
        const act = tickData.active_process;
        const pObj = (sch.raw_processes || []).find(p => p.label === act) || { burst_time: 4 };
        const rem = (tickData.remaining_burst && tickData.remaining_burst[act] !== undefined) ? tickData.remaining_burst[act] : 0;
        const elapsed = Math.max(0, pObj.burst_time - rem);
        const pct = Math.min(100, Math.round((elapsed / pObj.burst_time) * 100));

        if (cpuBox) { cpuBox.className = 'cpu-socket active'; }
        if (cpuPill) { cpuPill.className = 'badge badge-green'; cpuPill.innerText = '● EXECUTING'; }
        if (jobLbl) { jobLbl.innerText = act; jobLbl.style.color = '#22c55e'; }
        if (burstLbl) { burstLbl.innerText = `Remaining: ${rem}t / ${pObj.burst_time}t (${pct}% Done)`; }
        if (progBar) { progBar.style.width = pct + '%'; }
      } else {
        if (cpuBox) { cpuBox.className = 'cpu-socket idle'; }
        if (cpuPill) { cpuPill.className = 'badge badge-gray'; cpuPill.innerText = 'IDLE'; }
        if (jobLbl) { jobLbl.innerText = 'CPU IDLE'; jobLbl.style.color = '#94a3b8'; }
        if (burstLbl) { burstLbl.innerText = 'Awaiting ready process...'; }
        if (progBar) { progBar.style.width = '0%'; }
      }

      // 3. Completed Jobs Stage
      const compList = document.getElementById('sch-completed-list');
      const compCount = document.getElementById('sch-comp-count');
      const completedJobs = [];
      const states = tickData.states || {};
      Object.keys(states).forEach(j => {
        if (states[j] === 'TERMINATED') completedJobs.push(j);
      });
      if (compCount) compCount.innerText = `${completedJobs.length} finished`;
      if (compList) {
        compList.innerHTML = '';
        if (completedJobs.length === 0) {
          compList.innerHTML = '<span style="color:#64748b; font-size:0.72rem;">No finished processes yet.</span>';
        } else {
          completedJobs.forEach(jobLabel => {
            const tok = document.createElement('div');
            tok.className = 'proc-token';
            tok.style.borderColor = '#16a34a';
            tok.style.background = '#052e16';
            tok.innerHTML = `<span>${jobLabel}</span><small style="color:#4ade80;">✔ Exited</small>`;
            compList.appendChild(tok);
          });
        }
      }

      // 4. Gantt Cursor & Block Glow
      const cursor = document.getElementById('gantt-cursor');
      if (cursor && maxDur > 0) {
        cursor.style.left = ((tick / maxDur) * 100) + '%';
      }
      (sch.gantt || []).forEach((b, idx) => {
        const el = document.getElementById(`gantt-blk-${idx}`);
        if (el) {
          if (b.start <= tick && tick < b.end) {
            el.style.boxShadow = '0 0 10px #22c55e';
            el.style.opacity = '1.0';
          } else if (b.end <= tick) {
            el.style.boxShadow = 'none';
            el.style.opacity = '0.9';
          } else {
            el.style.boxShadow = 'none';
            el.style.opacity = '0.4';
          }
        }
      });
    }

    // Playback Controls
    function schStep(delta) {
      if (!schState.data) return;
      ensureAudioContext();
      const maxDur = schState.data.total_duration || 12;
      const newTick = Math.max(0, Math.min(maxDur, schState.currentTick + delta));
      updateSchVisualsAtTick(newTick);
      if (newTick >= maxDur && schState.isPlaying) {
        schTogglePlay();
      }
    }

    function schTogglePlay() {
      ensureAudioContext();
      schState.isPlaying = !schState.isPlaying;
      const btn = document.getElementById('btn-sch-play');
      if (btn) {
        btn.innerText = schState.isPlaying ? '⏸ Pause' : '▶ Play';
        btn.className = 'btn btn-sm ' + (schState.isPlaying ? 'btn-amber' : 'btn-green');
      }
      if (schState.timer) {
        clearInterval(schState.timer);
        schState.timer = null;
      }
      if (schState.isPlaying) {
        if (schState.data && schState.currentTick >= schState.data.total_duration) {
          schState.currentTick = 0;
        }
        schState.timer = setInterval(() => {
          schStep(1);
        }, schState.playInterval);
      }
    }

    function schResetTick() {
      if (schState.isPlaying) schTogglePlay();
      updateSchVisualsAtTick(0);
    }

    function setSchSpeed(ms, label) {
      schState.playInterval = ms;
      ['05', '1', '2', '4'].forEach(l => {
        const b = document.getElementById('btn-spd-' + l);
        if (b) b.className = 'btn btn-sm' + (l === label ? ' btn-cyan' : '');
      });
      if (schState.isPlaying) {
        clearInterval(schState.timer);
        schState.timer = setInterval(() => { schStep(1); }, schState.playInterval);
      }
    }

    // Process Input Table Editor
    function renderInputTable() {
      const tbody = document.getElementById('sch-input-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      schState.inputRows.forEach((row, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><input type="text" value="${row.label}" style="width:65px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px; font-weight:bold;" onchange="updateInputCell(${idx}, 'label', this.value)"></td>
          <td><input type="number" min="0" max="100" value="${row.arrival_time}" style="width:55px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px;" onchange="updateInputCell(${idx}, 'arrival_time', parseInt(this.value)||0)"></td>
          <td><input type="number" min="1" max="100" value="${row.burst_time}" style="width:55px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px;" onchange="updateInputCell(${idx}, 'burst_time', parseInt(this.value)||1)"></td>
          <td><input type="number" min="1" max="10" value="${row.priority}" style="width:50px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px;" onchange="updateInputCell(${idx}, 'priority', parseInt(this.value)||1)"></td>
          <td><button class="btn btn-sm btn-red" style="padding:2px 6px;" onclick="removeProcessRow(${idx})" ${schState.inputRows.length <= 1 ? 'disabled' : ''}>✕</button></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function updateInputCell(idx, field, val) {
      if (schState.inputRows[idx]) schState.inputRows[idx][field] = val;
    }

    function addProcessRow() {
      if (schState.inputRows.length >= 8) return;
      const n = schState.inputRows.length + 1;
      schState.inputRows.push({ label: 'P' + n, arrival_time: n - 1, burst_time: 4, priority: n });
      renderInputTable();
    }

    function removeProcessRow(idx) {
      if (schState.inputRows.length <= 1) return;
      schState.inputRows.splice(idx, 1);
      renderInputTable();
    }

    function resetCurrentDataset() {
      postAction('reset_scheduler_dataset', { dataset: 'standard' });
      schState.inputRows = [];
    }

    function applyCustomProcesses() {
      if (schState.inputRows.length === 0) return;
      fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_custom_scheduler_processes', processes: schState.inputRows })
      }).then(r => r.json()).then(res => {
        if (res.status === 'ok') {
          const errEl = document.getElementById('input-error-msg');
          if (errEl) errEl.style.display = 'none';
          pollData();
        } else {
          const errEl = document.getElementById('input-error-msg');
          if (errEl) { errEl.innerText = res.message || 'Validation error'; errEl.style.display = 'block'; }
        }
      });
    }

    // =======================================================================
    // TAB 3: DEADLOCK VISUALIZATION & RECOVERY LOGIC
    // =======================================================================
    let wasDeadlocked = false;

    function renderDeadlock(dl) {
      if (!dl) return;
      const twoProc = dl.two_process || {};
      const banker = dl.banker || {};

      const step = twoProc.step || 0;
      const isDl = twoProc.is_deadlocked;

      // Status Badge
      const statusBadge = document.getElementById('deadlock-status-badge');
      if (statusBadge) {
        if (isDl) {
          statusBadge.innerText = '🚨 DEADLOCK FORMED';
          statusBadge.className = 'badge badge-red';
        } else if (step === 5) {
          statusBadge.innerText = '✔ DEADLOCK RESOLVED';
          statusBadge.className = 'badge badge-green';
        } else {
          statusBadge.innerText = '✔ System Safe';
          statusBadge.className = 'badge badge-green';
        }
      }

      // Title & Description
      const titleEl = document.getElementById('dl-step-title');
      if (titleEl) titleEl.innerText = twoProc.title || 'Step ' + step;
      const descEl = document.getElementById('dl-step-desc');
      if (descEl) descEl.innerText = twoProc.explanation || '';

      // Cycle Alert Indicator
      const cycleInd = document.getElementById('dl-cycle-indicator');
      if (cycleInd) cycleInd.style.display = isDl ? 'block' : 'none';

      // Sound trigger
      if (isDl && !wasDeadlocked) {
        playTone('DEADLOCK');
      } else if (!isDl && wasDeadlocked && step === 5) {
        playTone('RECOVERY');
      }
      wasDeadlocked = isDl;

      // Process States on SVG
      const p1St = document.getElementById('rag-p1-st');
      if (p1St) p1St.innerText = twoProc.p1_state || 'READY';
      const p2St = document.getElementById('rag-p2-st');
      if (p2St) p2St.innerText = twoProc.p2_state || 'READY';

      // RAG Edges
      const setEdge = (id, stroke, isDashed, isCycleEdge) => {
        const el = document.getElementById(id);
        if (el) {
          el.setAttribute('stroke', stroke);
          el.setAttribute('stroke-dasharray', isDashed ? '4,4' : 'none');
          if (isCycleEdge && isDl) el.classList.add('cycle-pulse');
          else el.classList.remove('cycle-pulse');
        }
      };

      setEdge('edge-r1-p1', '#334155', false, false);
      setEdge('edge-r2-p2', '#334155', false, false);
      setEdge('edge-p1-r2', '#334155', true, false);
      setEdge('edge-p2-r1', '#334155', true, false);

      (twoProc.edges || []).forEach(e => {
        if (e.from === 'R1' && e.to === 'P1') setEdge('edge-r1-p1', isDl ? '#ef4444' : '#22d3ee', false, isDl);
        if (e.from === 'R2' && e.to === 'P2') setEdge('edge-r2-p2', isDl ? '#ef4444' : '#22d3ee', false, isDl);
        if (e.from === 'P1' && e.to === 'R2') setEdge('edge-p1-r2', isDl ? '#ef4444' : '#f59e0b', true, isDl);
        if (e.from === 'P2' && e.to === 'R1') setEdge('edge-p2-r1', isDl ? '#ef4444' : '#f59e0b', true, isDl);
      });

      // Matrices
      const alloc = twoProc.allocation || [[0, 0], [0, 0]];
      const reqs = twoProc.requests || [[0, 0], [0, 0]];
      const avail = twoProc.available || [1, 1];

      const p1Alloc = document.getElementById('mat-alloc-p1');
      if (p1Alloc) p1Alloc.innerText = JSON.stringify(alloc[0]);
      const p2Alloc = document.getElementById('mat-alloc-p2');
      if (p2Alloc) p2Alloc.innerText = JSON.stringify(alloc[1]);

      const p1Need = document.getElementById('mat-need-p1');
      if (p1Need) p1Need.innerText = JSON.stringify(reqs[0]);
      const p2Need = document.getElementById('mat-need-p2');
      if (p2Need) p2Need.innerText = JSON.stringify(reqs[1]);

      const matAvail = document.getElementById('mat-available');
      if (matAvail) matAvail.innerText = JSON.stringify(avail);

      const seqEl = document.getElementById('mat-safe-seq');
      if (seqEl) {
        if (isDl) {
          seqEl.innerText = 'NO SAFE SEQUENCE (Deadlock Cycle)';
          seqEl.style.color = '#ef4444';
        } else {
          seqEl.innerText = banker.safe_sequence || 'P1 ➔ P2';
          seqEl.style.color = '#22d3ee';
        }
      }
    }

    function triggerDeadlockFormation() {
      // Advance to step 4 (circular wait deadlock)
      postAction('step_two_process_deadlock');
      setTimeout(() => postAction('step_two_process_deadlock'), 150);
      setTimeout(() => postAction('step_two_process_deadlock'), 300);
      setTimeout(() => postAction('step_two_process_deadlock'), 450);
    }

    // =======================================================================
    // GLOBAL DATA POLLING
    // =======================================================================
    function pollData() {
      fetch('/api/status')
        .then(r => r.json())
        .then(data => {
          renderOverview(data.overview);
          renderScheduler(data.scheduler);
          renderDeadlock(data.deadlock);
        })
        .catch(err => {
          console.error("Polling error:", err);
        });
    }

    // Initial poll & 1.0s interval
    pollData();
    setInterval(pollData, 1000);
  </script>
</body>
</html>
'''

full_code = f'{header_imports}HTML_PAGE = """{NEW_HTML_PAGE}"""\n\n{python_backend}'

with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(full_code)

print("Wrote completely redesigned dashboard to dashboard/web_server.py!")
py_compile.compile('dashboard/web_server.py', doraise=True)
print("Python py_compile: SUCCESS (0 errors)!")
