import re
import py_compile
import subprocess

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. NEW CSS STYLES
# -----------------------------------------------------------------------------
css_marker = '/* CPU Socket & Queues */'
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
    padding: 7px 12px;
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

if '.studio-toolbar' not in text:
    text = text.replace(css_marker, new_css + "\n  " + css_marker)
    print("Injected studio CSS!")

# -----------------------------------------------------------------------------
# 2. COMPLETE CPU EXECUTION STUDIO HTML FOR TAB 2
# -----------------------------------------------------------------------------
start_marker = '<div id="tab-process-lab" style="display: none;">'
end_marker = '<!-- ========================================================================= -->\n<!-- TAB 3: SELF-HEALING & RECOVERY -->'

new_tab2_html = """<div id="tab-process-lab" style="display: none;">
  <!-- CPU Execution Studio Header & Quick-Access Controls -->
  <div class="panel-card" style="padding:12px 16px; margin-bottom:12px;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
      <div>
        <div style="display:flex; align-items:center; gap:8px;">
          <h2 style="font-size:1.15rem; font-weight:900; color:#38bdf8; letter-spacing:0.5px;">⚡ CPU EXECUTION STUDIO</h2>
          <span class="badge badge-sim">[SIMULATION ENGINE ACTIVE]</span>
          <span class="badge badge-live" id="sch-active-algo-badge" style="background:#1e1b4b; border-color:#818cf8; color:#c7d2fe;">ALGO: RR (Q=2)</span>
        </div>
        <p style="color:var(--text-muted); font-size:0.75rem; margin-top:2px;">
          Interactive OS Process Lifecycle, Short-Term CPU Scheduling, Live Ready Queue & Gantt Execution Timeline
        </p>
      </div>
      <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center;">
        <button class="btn btn-sm btn-purple" id="btn-toggle-comparison" onclick="toggleAlgorithmComparison()">📊 Compare All Algorithms</button>
        <button class="btn btn-sm" onclick="toggleProcessInputDrawer()" id="btn-toggle-inputs">✏️ Process Input Studio</button>
        <button class="btn btn-sm" onclick="toggleSecondaryStateMachine()" id="btn-toggle-secondary-sm">👁️ 5-State Machine View</button>
      </div>
    </div>
  </div>

  <!-- Collapsible Process-Input Studio Table -->
  <div id="process-input-drawer" style="display:none; background:#070d19; border:1px solid #1e293b; border-radius:8px; padding:12px; margin-bottom:12px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:8px;">
      <div>
        <span style="font-weight:800; font-size:0.85rem; color:#93c5fd;">Custom Process Specifications (Max 10 jobs)</span>
        <div style="font-size:0.7rem; color:var(--text-dim); margin-top:1px;">Assigns unique simulated PIDs (<span style="color:#38bdf8;">[SIMULATED PID]</span> namespace: P101–P999) isolated from real host processes.</div>
      </div>
      <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
        <span style="font-size:0.75rem; color:var(--text-muted); font-weight:bold;">Presets:</span>
        <select id="select-dataset" style="background:#1e293b; border:1px solid var(--border-highlight); color:#fff; border-radius:4px; padding:3px 8px; font-size:0.76rem;" onchange="loadPresetDataset(this.value)">
          <option value="standard">Standard Benchmark (P1–P4)</option>
          <option value="convoy">Convoy Effect (Heavy P1)</option>
          <option value="priority_mix">Priority Mix</option>
          <option value="staggered">Staggered Arrivals</option>
        </select>
        <button class="btn btn-sm btn-accent" onclick="addProcessRow()">➕ Add Process</button>
        <button class="btn btn-sm" onclick="resetCurrentDataset()">↺ Reset</button>
        <button class="btn btn-sm btn-success" onclick="applyCustomProcesses()">▶ Apply & Recalculate</button>
      </div>
    </div>
    <div id="input-error-msg" style="display:none; color:#fca5a5; background:#7f1d1d; border:1px solid #ef4444; border-radius:4px; padding:4px 8px; font-size:0.74rem; margin-bottom:6px;"></div>
    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse; font-size:0.76rem;">
        <thead>
          <tr style="border-bottom:1px solid #1e293b; color:var(--text-muted); text-align:left;">
            <th style="padding:6px;">PID / Label</th>
            <th style="padding:6px;">Arrival Time (AT ≥ 0)</th>
            <th style="padding:6px;">Burst Time (BT ≥ 1)</th>
            <th style="padding:6px;">Priority (1 = Highest)</th>
            <th style="padding:6px; text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody id="process-input-tbody">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- Collapsible Side-by-Side Algorithm Comparison Panel -->
  <div id="algorithm-comparison-panel" style="display:none; margin-bottom:12px; background:#0c1222; border:1px solid var(--accent-purple); border-radius:8px; padding:12px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-weight:800; font-size:0.85rem; color:#d8b4fe;">📊 Algorithm Performance Matrix (Side-by-Side Benchmark)</span>
      <button class="btn btn-sm" onclick="toggleAlgorithmComparison()">✕ Close</button>
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse; font-size:0.76rem;">
        <thead>
          <tr style="border-bottom:1px solid #1e293b; color:var(--text-muted); text-align:left;">
            <th style="padding:6px;">Algorithm</th>
            <th style="padding:6px;">Avg Turnaround (TAT)</th>
            <th style="padding:6px;">Avg Waiting Time (WT)</th>
            <th style="padding:6px;">Avg Response Time (RT)</th>
            <th style="padding:6px;">Context Switches</th>
            <th style="padding:6px;">Relative Efficiency</th>
          </tr>
        </thead>
        <tbody id="scheduler-comparison-table-body">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- 1. Algorithm Selector Cards -->
  <div class="algo-selector-grid">
    <div class="algo-card active" id="card-algo-RR" onclick="setAlgorithm('RR')">
      <div class="algo-card-title">
        <span>Round Robin (RR)</span>
        <span class="badge badge-live" style="font-size:0.65rem;">PREEMPTIVE</span>
      </div>
      <div class="algo-card-sub">Time-sliced scheduling ensuring equitable latency and zero starvation.</div>
      <div style="display:flex; align-items:center; gap:6px; margin-top:6px;" onclick="event.stopPropagation();">
        <span style="font-size:0.7rem; color:var(--text-dim); font-weight:bold;">Quantum (q):</span>
        <input type="number" id="input-rr-quantum" min="1" max="10" value="2" style="width:44px; background:#1e293b; border:1px solid var(--border-highlight); color:#fff; border-radius:4px; padding:2px 4px; font-weight:bold; text-align:center; font-size:0.75rem;" onchange="updateQuantum(this.value)">
      </div>
    </div>

    <div class="algo-card" id="card-algo-SJF" onclick="setAlgorithm('SJF')">
      <div class="algo-card-title">
        <span>Shortest Job First</span>
        <span class="badge badge-sim" style="font-size:0.65rem;">NON-PREEMPT</span>
      </div>
      <div class="algo-card-sub">Dispatches the arrived process with minimum CPU burst; minimizes avg waiting time.</div>
    </div>

    <div class="algo-card" id="card-algo-FCFS" onclick="setAlgorithm('FCFS')">
      <div class="algo-card-title">
        <span>First-Come, First-Served</span>
        <span class="badge badge-sim" style="font-size:0.65rem;">FIFO DISPATCH</span>
      </div>
      <div class="algo-card-sub">Executes in strict chronological order of arrival. Prone to convoy effect.</div>
    </div>

    <div class="algo-card" id="card-algo-PRIORITY" onclick="setAlgorithm('PRIORITY')">
      <div class="algo-card-title">
        <span>Priority Scheduling</span>
        <span class="badge badge-sim" style="font-size:0.65rem;">1 = HIGHEST</span>
      </div>
      <div class="algo-card-sub">Dispatches the arrived task with lowest numerical priority value (1 is highest).</div>
    </div>
  </div>

  <!-- Active Algorithm Selection Rule Explanation Banner -->
  <div style="background:#091224; border:1px solid #1e293b; border-radius:6px; padding:8px 12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
    <div style="display:flex; align-items:center; gap:6px;">
      <span style="font-size:0.72rem; color:var(--text-dim); font-weight:bold; text-transform:uppercase;">Active Selection Rule:</span>
      <span id="sch-rule-explanation" style="font-size:0.78rem; color:#38bdf8; font-weight:600;">Round Robin dispatches the head of the READY queue for up to 2 ticks, then preempts unfinished jobs to the tail.</span>
    </div>
    <div style="font-size:0.72rem; color:var(--text-dim); font-family:monospace;" id="sch-context-switches-banner">Context Switches: 0</div>
  </div>

  <!-- 2. Playback & Deterministic Clock Control Bar -->
  <div class="studio-toolbar">
    <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
      <button class="btn btn-sm btn-accent" id="btn-sch-play" onclick="schTogglePlay()">▶ Play</button>
      <button class="btn btn-sm" onclick="schResetTick()" id="btn-sch-reset">↺ Reset</button>
      <button class="btn btn-sm" onclick="schStep(-1)" title="Step back 1 tick">◀ Step Tick</button>
      <button class="btn btn-sm" onclick="schStep(1)" title="Advance 1 tick">Step Tick ▶</button>
      <button class="btn btn-sm btn-purple" onclick="schStepEvent(1)" title="Advance to next scheduler dispatch or completion event">⏭ Step Event</button>
      
      <!-- Speed Selector -->
      <div style="display:inline-flex; border:1px solid var(--border); border-radius:4px; overflow:hidden; margin-left:4px;">
        <button class="btn btn-sm" id="btn-speed-05" onclick="setSchSpeed(1600, '05')">0.5×</button>
        <button class="btn btn-sm btn-accent" id="btn-speed-1" onclick="setSchSpeed(800, '1')">1×</button>
        <button class="btn btn-sm" id="btn-speed-2" onclick="setSchSpeed(400, '2')">2×</button>
        <button class="btn btn-sm" id="btn-speed-4" onclick="setSchSpeed(200, '4')">4×</button>
      </div>
    </div>

    <!-- Clock and Status Display -->
    <div style="display:flex; align-items:center; gap:12px; font-family:var(--font-mono);">
      <div>
        <span style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase;">SIMULATED CLOCK:</span>
        <span id="sch-clock-val" style="font-weight:900; font-size:1.15rem; color:#38bdf8; margin-left:4px;">t = 0</span>
      </div>
      <div id="sch-simulation-status" style="font-size:0.75rem; font-weight:bold; color:#94a3b8;">○ PAUSED</div>
    </div>
  </div>

  <!-- 3. MAIN STAGE: Central CPU Core 0, Live Ready Queue & Process Lanes -->
  <div style="display:grid; grid-template-columns: 1.15fr 0.85fr; gap:12px; margin-bottom:12px;">
    <!-- LEFT COLUMN: CPU Core 0 & Process Execution Lanes -->
    <div style="display:flex; flex-direction:column; gap:12px;">
      <!-- Central CPU Core 0 Socket Visual -->
      <div class="panel-card" style="margin-bottom:0;">
        <div class="panel-top" style="margin-bottom:8px;">
          <div class="panel-title">
            <span>Central CPU Core 0 (Active Execution Stage)</span>
            <span class="badge badge-sim">[CORE 0]</span>
          </div>
          <span id="cpu-status-pill" class="badge badge-live">○ IDLE</span>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; align-items:center;">
          <!-- Left: Glowing CPU Socket -->
          <div class="cpu-socket-box idle" id="cpu-socket-element" style="padding:14px; min-height:120px; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="font-size:0.68rem; color:var(--text-dim); font-weight:bold; letter-spacing:1px; margin-bottom:4px;">CPU CORE 0 [SOCKET]</div>
            <div id="cpu-exec-label" style="font-size:1.45rem; font-weight:900; color:#fff; font-family:var(--font-mono); margin-bottom:4px;">CPU IDLE</div>
            
            <!-- Remaining Burst Time Countdown Badge -->
            <div id="cpu-exec-burst" style="font-size:0.82rem; color:#67e8f9; font-weight:bold; margin-bottom:6px;">No Job Dispatched</div>
            
            <!-- Animated Burst Progress Bar -->
            <div style="background:#020617; border:1px solid #1e293b; border-radius:4px; height:8px; width:100%; max-width:200px; overflow:hidden;">
              <div id="cpu-exec-prog-bar" style="width:0%; height:100%; background:linear-gradient(90deg, #10b981, #06b6d4); transition: width 0.2s linear;"></div>
            </div>
          </div>

          <!-- Right: Execution Interval, Stats & Rationale -->
          <div style="display:flex; flex-direction:column; justify-content:space-between; height:100%; gap:6px;">
            <div style="background:#080f1e; border:1px solid #1e293b; border-radius:6px; padding:8px 10px;">
              <div style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold;">Execution Interval:</div>
              <div id="cpu-exec-interval" style="font-family:var(--font-mono); font-size:0.85rem; font-weight:800; color:#f8fafc; margin-top:1px;">Interval: Awaiting dispatch</div>
            </div>

            <div style="background:#080f1e; border:1px solid #1e293b; border-radius:6px; padding:8px 10px;">
              <div style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold;">Time Slice & Preemption Counter:</div>
              <div id="cpu-exec-stats" style="font-family:var(--font-mono); font-size:0.8rem; color:#38bdf8; margin-top:1px;">Slice: - | Preemptions: 0</div>
            </div>

            <div style="background:#080f1e; border:1px solid #1e293b; border-radius:6px; padding:8px 10px;">
              <div style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold;">Active Decision:</div>
              <div id="sch-decision-banner" style="font-size:0.75rem; color:#94a3b8; line-height:1.3; margin-top:1px;">Awaiting scheduler initialization.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Process Execution Lanes (Per-Process Real-Time Horizontal Progress) -->
      <div class="panel-card" style="margin-bottom:0;">
        <div class="panel-top" style="margin-bottom:8px;">
          <div class="panel-title">
            <span>Process Execution Lanes (Real-Time Consumption)</span>
            <span class="badge badge-sim">[PROGRESS MONITOR]</span>
          </div>
          <span style="font-size:0.7rem; color:var(--text-dim);">Click lane to inspect process</span>
        </div>
        <div id="process-execution-lanes">
          <!-- Dynamically generated process lane rows -->
        </div>
      </div>
    </div>

    <!-- RIGHT COLUMN: Live Ready Queue & Selected Process Inspector -->
    <div style="display:flex; flex-direction:column; gap:12px;">
      <!-- Live Ready Queue (Dispatch Order) -->
      <div class="panel-card" style="margin-bottom:0;">
        <div class="panel-top" style="margin-bottom:8px;">
          <div class="panel-title">
            <span>Live Ready Queue (Dispatch Order)</span>
            <span class="badge badge-sim" id="ready-queue-count-badge">0 queued</span>
          </div>
        </div>
        
        <!-- Queue Tokens Container -->
        <div id="live-ready-queue-strip" class="ready-queue-strip" style="min-height:55px; margin-bottom:6px;">
          <span style="color:#64748b; font-size:0.74rem;">Ready queue empty (No processes awaiting CPU dispatch).</span>
        </div>

        <div style="font-size:0.72rem; color:var(--text-dim);" id="ready-queue-reason">
          Queue ordering determined strictly by active scheduling algorithm.
        </div>
      </div>

      <!-- Selected Process Inspector -->
      <div class="panel-card" style="margin-bottom:0; flex:1;">
        <div class="panel-top" style="margin-bottom:6px;">
          <div class="panel-title">
            <span>Selected Process Inspector</span>
            <span class="badge badge-sim" id="inspector-pid-badge">[SIMULATED PID]</span>
          </div>
          <span id="inspector-state-pill" class="badge badge-live">STATE: -</span>
        </div>

        <div style="font-weight:900; font-size:1.05rem; color:#f8fafc; font-family:var(--font-mono); margin-bottom:2px;" id="inspector-job-name">
          No Process Selected
        </div>
        <div id="inspector-explanation" style="font-size:0.74rem; color:#94a3b8; line-height:1.4; margin-bottom:8px;">
          Click any process row, CPU core, or Gantt block to inspect its complete OS metrics and state lifecycle.
        </div>

        <!-- Metrics Grid -->
        <div class="inspector-metric-grid">
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Arrival (AT)</div>
            <div class="inspector-metric-val" id="insp-at">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Burst (BT)</div>
            <div class="inspector-metric-val" id="insp-bt">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Remaining</div>
            <div class="inspector-metric-val" id="insp-rem">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">First Start</div>
            <div class="inspector-metric-val" id="insp-st">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Completion</div>
            <div class="inspector-metric-val" id="insp-ct">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Waiting (WT)</div>
            <div class="inspector-metric-val" id="insp-wt">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Turnaround</div>
            <div class="inspector-metric-val" id="insp-tat">-</div>
          </div>
          <div class="inspector-metric-box">
            <div class="inspector-metric-lbl">Response (RT)</div>
            <div class="inspector-metric-val" id="insp-rt">-</div>
          </div>
        </div>

        <!-- State-Transition History Timeline -->
        <div style="margin-top:8px;">
          <div style="font-size:0.68rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold; margin-bottom:3px;">State-Transition Sequence:</div>
          <div id="inspector-history-timeline" style="font-family:var(--font-mono); font-size:0.72rem; color:#cbd5e1; background:#080f1e; border:1px solid #1e293b; border-radius:4px; padding:6px 8px; max-height:60px; overflow-y:auto;">
            Select a process to view its transition history.
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 4. Dynamic Gantt Timeline with Moving Playback Cursor -->
  <div class="panel-card" style="margin-bottom:12px;">
    <div class="panel-top" style="margin-bottom:8px;">
      <div class="panel-title">
        <span>Dynamic Gantt Execution Timeline</span>
        <span class="badge badge-sim">[SCHEDULE TRACE]</span>
      </div>
      <div style="font-size:0.7rem; color:var(--text-dim);">Hover for duration • Click block to inspect process</div>
    </div>

    <div class="gantt-chart-container">
      <!-- Time Ruler with Ticks -->
      <div id="gantt-time-ruler" class="gantt-time-ruler">
        <!-- Rendered by JS -->
      </div>

      <!-- Gantt Execution Blocks Strip with Moving Cursor -->
      <div style="position:relative; min-height:42px;">
        <div id="gantt-timeline-blocks" style="display:flex; height:38px; border-radius:4px; overflow:hidden; border:1px solid var(--border);">
          <!-- Rendered by JS -->
        </div>
        <!-- Moving Playback Cursor Indicator -->
        <div id="gantt-playback-cursor" class="gantt-playback-cursor" style="left:0%;"></div>
      </div>
    </div>
  </div>

  <!-- 5. Scheduling Performance Metrics & Compact Event Feed -->
  <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:12px;">
    <!-- Performance Summary Metrics Cards -->
    <div class="panel-card" style="margin-bottom:0;">
      <div class="panel-top" style="margin-bottom:8px;">
        <div class="panel-title">
          <span>Scheduling Performance Metrics</span>
          <span class="badge badge-sim">[COMPUTED RESULTS]</span>
        </div>
      </div>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap:8px;">
        <div class="inspector-metric-box" style="padding:8px;">
          <div class="inspector-metric-lbl">Avg Waiting Time</div>
          <div class="inspector-metric-val" id="metric-avg-wt" style="font-size:1.1rem; color:#10b981;">0.00t</div>
        </div>
        <div class="inspector-metric-box" style="padding:8px;">
          <div class="inspector-metric-lbl">Avg Turnaround</div>
          <div class="inspector-metric-val" id="metric-avg-tat" style="font-size:1.1rem; color:#38bdf8;">0.00t</div>
        </div>
        <div class="inspector-metric-box" style="padding:8px;">
          <div class="inspector-metric-lbl">Avg Response Time</div>
          <div class="inspector-metric-val" id="metric-avg-rt" style="font-size:1.1rem; color:#c084fc;">0.00t</div>
        </div>
        <div class="inspector-metric-box" style="padding:8px;">
          <div class="inspector-metric-lbl">Context Switches</div>
          <div class="inspector-metric-val" id="metric-context-switches" style="font-size:1.1rem; color:#f59e0b;">0</div>
        </div>
      </div>
    </div>

    <!-- Compact Real-Time Scheduler Event Feed -->
    <div class="panel-card" style="margin-bottom:0;">
      <div class="panel-top" style="margin-bottom:6px;">
        <div class="panel-title">
          <span>Scheduler Event Feed</span>
          <span class="badge badge-sim">[AUDIT STREAM]</span>
        </div>
      </div>
      <div id="sch-event-feed" style="max-height:95px; overflow-y:auto; font-family:var(--font-mono); font-size:0.72rem; color:#cbd5e1; background:#080f1e; border:1px solid #1e293b; border-radius:4px; padding:6px 8px;">
        <div>[t=0] CPU Scheduler initialized. Ready for execution.</div>
      </div>
    </div>
  </div>

  <!-- 6. Collapsible Secondary View: Theoretical 5-State Machine Diagram -->
  <div class="panel-card" style="margin-bottom:0;">
    <div class="panel-top" style="cursor:pointer;" onclick="toggleSecondaryStateMachine()">
      <div class="panel-title">
        <span>👁️ Theoretical 5-State Machine & PID Allocation Pipeline (Secondary View)</span>
        <span class="badge badge-sim">[OS THEORY]</span>
      </div>
      <button class="btn btn-sm" id="btn-expand-sm">Expand ▼</button>
    </div>

    <div id="secondary-state-machine-drawer" style="display:none; margin-top:10px;">
      <p style="font-size:0.75rem; color:var(--text-muted); margin-bottom:8px;">
        Classic OS Process State Transitions (Silberschatz/Stallings): Processes transition between NEW, READY, RUNNING, WAITING, and TERMINATED.
      </p>
      
      <!-- SVG 5-State Machine Diagram -->
      <div style="background:#020617; border:1px solid #1e293b; border-radius:6px; padding:10px; text-align:center;">
        <svg id="svg-lifecycle-states" viewBox="0 0 710 270" style="width:100%; max-height:220px; font-family:sans-serif;">
          <defs>
            <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#06b6d4" />
            </marker>
            <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#10b981" />
            </marker>
            <marker id="arrow-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#f59e0b" />
            </marker>
            <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#ef4444" />
            </marker>
          </defs>

          <!-- Transition Paths -->
          <path id="trans-new-ready" d="M 120 65 L 180 65" fill="none" stroke="#06b6d4" stroke-width="2" marker-end="url(#arrow-cyan)"/>
          <path id="trans-ready-running" d="M 315 50 L 395 50" fill="none" stroke="#10b981" stroke-width="2" marker-end="url(#arrow-green)"/>
          <path id="trans-running-ready" d="M 395 80 L 315 80" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="4" marker-end="url(#arrow-amber)"/>
          <path id="trans-running-waiting" d="M 445 90 C 445 150, 390 190, 390 190" fill="none" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrow-amber)"/>
          <path id="trans-waiting-ready" d="M 290 190 C 290 150, 245 90, 245 90" fill="none" stroke="#06b6d4" stroke-width="2" marker-end="url(#arrow-cyan)"/>
          <path id="trans-running-term" d="M 525 65 L 585 65" fill="none" stroke="#ef4444" stroke-width="2" marker-end="url(#arrow-red)"/>

          <!-- State Nodes -->
          <g id="state-node-NEW" transform="translate(10, 40)">
            <rect width="110" height="50" rx="8" fill="#3b0764" stroke="#c084fc" stroke-width="2"/>
            <text x="55" y="22" fill="#e9d5ff" font-size="11" font-weight="bold" text-anchor="middle">NEW</text>
            <text x="55" y="38" fill="#d8b4fe" font-size="9" text-anchor="middle" id="txt-count-new">Allocated</text>
          </g>

          <g id="state-node-READY" transform="translate(180, 40)">
            <rect width="135" height="50" rx="8" fill="#083344" stroke="#06b6d4" stroke-width="2"/>
            <text x="67" y="22" fill="#a5f3fc" font-size="11" font-weight="bold" text-anchor="middle">READY QUEUE</text>
            <text x="67" y="38" fill="#67e8f9" font-size="9" text-anchor="middle" id="txt-count-ready">In Memory</text>
          </g>

          <g id="state-node-RUNNING" transform="translate(395, 40)">
            <rect width="130" height="50" rx="8" fill="#064e3b" stroke="#10b981" stroke-width="2"/>
            <text x="65" y="22" fill="#a7f3d0" font-size="11" font-weight="bold" text-anchor="middle">RUNNING (CPU)</text>
            <text x="65" y="38" fill="#6ee7b7" font-size="9" text-anchor="middle" id="txt-running-label">CPU Core 0</text>
          </g>

          <g id="state-node-WAITING" transform="translate(265, 185)">
            <rect width="150" height="50" rx="8" fill="#451a03" stroke="#f59e0b" stroke-width="2"/>
            <text x="75" y="22" fill="#fde68a" font-size="11" font-weight="bold" text-anchor="middle">WAITING / I/O</text>
            <text x="75" y="38" fill="#fbbf24" font-size="9" text-anchor="middle" id="txt-count-waiting">Blocked</text>
          </g>

          <g id="state-node-TERMINATED" transform="translate(585, 40)">
            <rect width="115" height="50" rx="8" fill="#450a0a" stroke="#ef4444" stroke-width="2"/>
            <text x="57" y="22" fill="#fecaca" font-size="11" font-weight="bold" text-anchor="middle">TERMINATED</text>
            <text x="57" y="38" fill="#f87171" font-size="9" text-anchor="middle" id="txt-count-term">Exited</text>
          </g>
        </svg>
      </div>
    </div>
  </div>
</div>
"""

# Replace tab-process-lab in HTML
pos_start = text.find(start_marker)
pos_end = text.find(end_marker)
text = text[:pos_start] + new_tab2_html + text[pos_end:]
print("Replaced tab-process-lab HTML!")

with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)

py_compile.compile('dashboard/web_server.py', doraise=True)
print("Python py_compile: 0 errors!")
