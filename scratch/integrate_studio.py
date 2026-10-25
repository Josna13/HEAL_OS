"""
Integrate CPU Execution Studio redesign into dashboard/web_server.py
"""
import re
import py_compile
import subprocess

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# -----------------------------------------------------------------------------
# 1. CSS STYLES
# -----------------------------------------------------------------------------
css_marker = '/* CPU Socket & Queues */'
studio_css = """  /* CPU Execution Studio Styles */
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
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }
  .algo-card {
    background: #0c1322;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    position: relative;
  }
  .algo-card:hover {
    border-color: var(--border-highlight);
    background: #111a30;
  }
  .algo-card.active {
    background: #0f2744;
    border-color: var(--accent-cyan);
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.3);
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
    min-width: 105px;
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
    text = text.replace(css_marker, studio_css + "\n  " + css_marker)
    print("Injected studio CSS successfully!")
else:
    print("Studio CSS already present.")

# -----------------------------------------------------------------------------
# 2. HTML FOR TAB 2: CPU EXECUTION STUDIO
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

pos_start = text.find(start_marker)
pos_end = text.find(end_marker)
if pos_start != -1 and pos_end != -1:
    text = text[:pos_start] + new_tab2_html + text[pos_end:]
    print("Replaced tab-process-lab HTML successfully!")
else:
    print(f"Error finding markers: start={pos_start}, end={pos_end}")

# -----------------------------------------------------------------------------
# 3. JAVASCRIPT FUNCTIONS FOR THE CPU EXECUTION STUDIO
# -----------------------------------------------------------------------------
# Replace old renderWorkspace2 through updateQuantum (lines 3275 - 3760)
js_start_marker = 'function renderWorkspace2(sch, comp) {'
js_end_marker = 'let wasDeadlocked = false;'

new_js = """function renderWorkspace2(sch, comp) {
  if (!sch) return;
  schState.data = sch;
  schState.comp = comp;

  // Active Algorithm buttons & Badge
  const algo = sch.algorithm || 'RR';
  const q = sch.quantum || 2;
  const badge = document.getElementById('sch-active-algo-badge');
  if (badge) badge.innerText = `ALGO: ${algo}` + (algo === 'RR' ? ` (Q=${q})` : '');

  ['RR', 'FCFS', 'SJF', 'PRIORITY'].forEach(a => {
    const card = document.getElementById('card-algo-' + a);
    if (card) {
      if (a === algo) card.classList.add('active');
      else card.classList.remove('active');
    }
  });

  const qInput = document.getElementById('input-rr-quantum');
  if (qInput) qInput.value = q;

  // Selection rule explanation
  const ruleEl = document.getElementById('sch-rule-explanation');
  if (ruleEl) {
    if (algo === 'FCFS') {
      ruleEl.innerText = 'First-Come, First-Served: Executes processes strictly in order of arrival time. Non-preemptive.';
    } else if (algo === 'SJF') {
      ruleEl.innerText = 'Shortest Job First: Dispatches the arrived process with the smallest CPU burst. Minimizes avg wait time.';
    } else if (algo === 'RR') {
      ruleEl.innerText = `Round Robin: Allocates fixed quantum (q=${q}t) per task in FIFO order, preempting unfinished jobs to the tail.`;
    } else if (algo === 'PRIORITY') {
      ruleEl.innerText = 'Priority Scheduling: Dispatches the arrived process with lowest numerical priority value (1 = Highest).';
    }
  }

  const csBanner = document.getElementById('sch-context-switches-banner');
  if (csBanner) csBanner.innerText = `Context Switches: ${sch.context_switches}`;

  // Performance Metrics Scorecard
  const mAvgWt = document.getElementById('metric-avg-wt');
  if (mAvgWt) mAvgWt.innerText = sch.avg_waiting_time + 't';
  const mAvgTat = document.getElementById('metric-avg-tat');
  if (mAvgTat) mAvgTat.innerText = sch.avg_turnaround_time + 't';
  const mAvgRt = document.getElementById('metric-avg-rt');
  if (mAvgRt) mAvgRt.innerText = sch.avg_response_time + 't';
  const mCs = document.getElementById('metric-context-switches');
  if (mCs) mCs.innerText = sch.context_switches;

  // Populate process input table if empty
  if (schState.inputRows.length === 0 && sch.raw_processes) {
    schState.inputRows = sch.raw_processes.map(p => ({
      label: p.label || ('P' + p.pid),
      arrival_time: p.arrival_time,
      burst_time: p.burst_time,
      priority: p.priority
    }));
    renderInputRows();
  }

  // Comparison scorecard matrix
  if (comp) {
    const tbody = document.getElementById('scheduler-comparison-table-body');
    if (tbody) {
      tbody.innerHTML = '';
      const algoNames = {
        'RR': 'Round Robin (RR)',
        'FCFS': 'First-Come, First-Served',
        'SJF': 'Shortest Job First',
        'PRIORITY': 'Priority Scheduling'
      };
      Object.keys(comp).forEach(k => {
        const item = comp[k];
        const isCurrent = (item.algorithm === algo || k === algo);
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid #1e293b';
        if (isCurrent) tr.style.background = 'rgba(6, 182, 212, 0.1)';
        tr.innerHTML = `
          <td style="padding:6px 8px; font-weight:bold; color:${isCurrent ? '#38bdf8' : '#e2e8f0'};">
            ${algoNames[k] || item.algorithm} ${isCurrent ? '<span class="badge badge-live" style="font-size:0.6rem; padding:1px 4px;">ACTIVE</span>' : ''}
          </td>
          <td style="padding:6px 8px; font-family:var(--font-mono);">${item.avg_turnaround_time}t</td>
          <td style="padding:6px 8px; font-family:var(--font-mono); color:#10b981;">${item.avg_waiting_time}t</td>
          <td style="padding:6px 8px; font-family:var(--font-mono); color:#c084fc;">${item.avg_response_time}t</td>
          <td style="padding:6px 8px; font-family:var(--font-mono); color:#f59e0b; font-weight:bold;">${item.context_switches}</td>
          <td style="padding:6px 8px; font-size:0.72rem; color:var(--text-muted);">${item.avg_waiting_time <= 4.0 ? '⚡ Low Wait Latency' : 'Standard Queue'}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  }

  // Clamp tick & Render Gantt static structure
  const maxDuration = sch.total_duration || 12;
  if (schState.currentTick > maxDuration) schState.currentTick = maxDuration;

  renderGanttTimelineStructure(sch);
  updateSchVisualsAtTick(schState.currentTick);
}

function renderGanttTimelineStructure(sch) {
  const maxDuration = sch.total_duration || 12;
  const ruler = document.getElementById('gantt-time-ruler');
  const blocksContainer = document.getElementById('gantt-timeline-blocks');
  if (!ruler || !blocksContainer) return;

  // 1. Time ruler
  ruler.innerHTML = '';
  for (let t = 0; t <= maxDuration; t++) {
    const mark = document.createElement('div');
    mark.style.position = 'absolute';
    mark.style.left = ((t / maxDuration) * 100) + '%';
    mark.style.transform = 'translateX(-50%)';
    mark.style.fontSize = '0.66rem';
    mark.style.color = '#64748b';
    mark.innerText = t;
    ruler.appendChild(mark);
  }

  // 2. Gantt execution blocks
  blocksContainer.innerHTML = '';
  const gantt = sch.gantt || [];
  gantt.forEach((b, idx) => {
    const blk = document.createElement('div');
    const dur = b.end - b.start;
    const widthPct = (dur / maxDuration) * 100;
    blk.style.width = widthPct + '%';
    blk.style.height = '100%';
    blk.style.display = 'flex';
    blk.style.flexDirection = 'column';
    blk.style.alignItems = 'center';
    blk.style.justifyContent = 'center';
    blk.style.fontSize = '0.72rem';
    blk.style.fontWeight = '800';
    blk.style.cursor = 'pointer';
    blk.style.transition = 'all 0.15s ease';
    blk.id = `gantt-block-${idx}`;
    blk.dataset.start = b.start;
    blk.dataset.end = b.end;
    blk.dataset.label = b.label;

    if (b.label === 'IDLE') {
      blk.style.background = '#090d16';
      blk.style.color = '#475569';
      blk.style.borderRight = '1px solid #1e293b';
      blk.title = `CPU IDLE [${b.start} → ${b.end}]`;
      blk.innerHTML = `<span style="font-size:0.6rem; color:#475569;">IDLE</span>`;
    } else {
      // Color-coded process slice
      blk.style.background = '#0c4a6e';
      blk.style.borderRight = '1px solid #0369a1';
      blk.style.color = '#bae6fd';
      blk.title = `${b.label}: Executed from t=${b.start} to t=${b.end} (${dur}t)`;
      blk.innerHTML = `<span>${b.label}</span><small style="font-size:0.58rem; color:#7dd3fc;">[${b.start}-${b.end}]</small>`;
      blk.onclick = () => highlightJob(b.label);
    }
    blocksContainer.appendChild(blk);
  });
}

function updateSchVisualsAtTick(tick) {
  const sch = schState.data;
  if (!sch) return;
  const maxDuration = sch.total_duration || 12;
  tick = Math.max(0, Math.min(maxDuration, tick));
  schState.currentTick = tick;

  // 1. Clock & status
  const clockEl = document.getElementById('sch-clock-val');
  if (clockEl) clockEl.innerText = `t = ${tick}`;

  const statusEl = document.getElementById('sch-simulation-status');
  if (statusEl) {
    if (schState.isPlaying) {
      statusEl.innerText = '● RUNNING';
      statusEl.style.color = '#10b981';
    } else if (tick >= maxDuration && maxDuration > 0) {
      statusEl.innerText = '✔ COMPLETED';
      statusEl.style.color = '#38bdf8';
    } else {
      statusEl.innerText = '○ PAUSED';
      statusEl.style.color = '#94a3b8';
    }
  }

  // 2. Get tick data
  let tickData = null;
  if (sch.timeline_ticks && sch.timeline_ticks[tick]) {
    tickData = sch.timeline_ticks[tick];
  } else {
    tickData = {
      active_process: null,
      ready_queue: [],
      remaining_burst: {},
      states: {},
      decision_reason: `t = ${tick}: Scheduler simulation nominal.`,
      is_context_switch: false
    };
  }

  // 3. Sound triggers
  if (tickData.active_process && tickData.active_process !== schState.lastActiveJob) {
    playTone('RUNNING');
  }
  if (tickData.is_context_switch) {
    playTone('BLOCKED');
  }
  schState.lastActiveJob = tickData.active_process;

  // 4. Central CPU Core 0 Socket Visual
  const cpuSocket = document.getElementById('cpu-socket-element');
  const cpuStatusPill = document.getElementById('cpu-status-pill');
  const cpuExecLbl = document.getElementById('cpu-exec-label');
  const cpuExecBurst = document.getElementById('cpu-exec-burst');
  const cpuExecProgBar = document.getElementById('cpu-exec-prog-bar');
  const cpuExecInterval = document.getElementById('cpu-exec-interval');
  const cpuExecStats = document.getElementById('cpu-exec-stats');
  const schDecisionBanner = document.getElementById('sch-decision-banner');

  if (schDecisionBanner) schDecisionBanner.innerText = tickData.decision_reason || `t = ${tick}: Operating systems CPU core executing.`;

  const procs = sch.raw_processes || [];
  const gantt = sch.gantt || [];

  if (tickData.active_process) {
    const act = tickData.active_process;
    const pObj = procs.find(p => p.label === act) || { burst_time: 4, arrival_time: 0, priority: 1, pid: 1 };
    const rem = (tickData.remaining_burst && tickData.remaining_burst[act] !== undefined) ? tickData.remaining_burst[act] : 0;
    const elapsed = Math.max(0, pObj.burst_time - rem);
    const pct = Math.min(100, Math.round((elapsed / pObj.burst_time) * 100));

    if (cpuSocket) cpuSocket.className = 'cpu-socket-box running';
    if (cpuStatusPill) {
      cpuStatusPill.className = 'badge badge-sim';
      cpuStatusPill.innerText = '● ACTIVE';
      cpuStatusPill.style.borderColor = '#10b981';
      cpuStatusPill.style.color = '#34d399';
    }
    if (cpuExecLbl) {
      cpuExecLbl.innerText = `${act} [P10${pObj.pid || 1}]`;
      cpuExecLbl.style.color = '#34d399';
    }
    if (cpuExecBurst) {
      cpuExecBurst.innerText = `Executing • Remaining: ${rem}t / ${pObj.burst_time}t (${pct}% Done)`;
      cpuExecBurst.style.color = '#6ee7b7';
    }
    if (cpuExecProgBar) {
      cpuExecProgBar.style.width = pct + '%';
      cpuExecProgBar.style.background = 'linear-gradient(90deg, #10b981, #06b6d4)';
    }

    // Find current interval block
    const curBlock = gantt.find(b => b.label === act && b.start <= tick && tick < b.end) || gantt.find(b => b.label === act);
    if (cpuExecInterval && curBlock) {
      cpuExecInterval.innerText = `Interval: [t=${curBlock.start} → t=${curBlock.end}] (${curBlock.end - curBlock.start}t slice)`;
    }
    if (cpuExecStats && curBlock) {
      const sliceDone = tick - curBlock.start + 1;
      cpuExecStats.innerText = `Slice Progress: ${sliceDone}t / ${curBlock.end - curBlock.start}t | Priority: ${pObj.priority}`;
    }
  } else {
    // Idle Core
    if (cpuSocket) cpuSocket.className = 'cpu-socket-box idle';
    if (cpuStatusPill) {
      cpuStatusPill.className = 'badge badge-live';
      cpuStatusPill.innerText = '○ IDLE';
      cpuStatusPill.style.borderColor = '#475569';
      cpuStatusPill.style.color = '#94a3b8';
    }
    if (cpuExecLbl) {
      cpuExecLbl.innerText = 'CPU IDLE';
      cpuExecLbl.style.color = '#94a3b8';
    }
    if (cpuExecBurst) {
      cpuExecBurst.innerText = 'No Job Dispatched (Awaiting Ready Process)';
      cpuExecBurst.style.color = '#64748b';
    }
    if (cpuExecProgBar) {
      cpuExecProgBar.style.width = '0%';
    }
    if (cpuExecInterval) cpuExecInterval.innerText = 'Interval: Core in low-power idle sleep';
    if (cpuExecStats) cpuExecStats.innerText = 'Slice: - | Preemptions: 0';
  }

  // 5. Live Ready Queue Strip
  const rqStrip = document.getElementById('live-ready-queue-strip');
  const rqCountBadge = document.getElementById('ready-queue-count-badge');
  const readyList = tickData.ready_queue || [];
  if (rqCountBadge) rqCountBadge.innerText = `${readyList.length} queued`;

  if (rqStrip) {
    rqStrip.innerHTML = '';
    if (readyList.length === 0) {
      rqStrip.innerHTML = '<span style="color:#64748b; font-size:0.74rem;">Ready queue empty (No processes awaiting CPU dispatch).</span>';
    } else {
      readyList.forEach((jobLabel, idx) => {
        const pObj = procs.find(p => p.label === jobLabel) || { burst_time: 4, arrival_time: 0, priority: 1, pid: idx+1 };
        const rem = (tickData.remaining_burst && tickData.remaining_burst[jobLabel] !== undefined) ? tickData.remaining_burst[jobLabel] : pObj.burst_time;
        const isSelected = (schState.selectedJob === jobLabel);

        const card = document.createElement('div');
        card.className = 'ready-token-card' + (isSelected ? ' proc-highlight' : '');
        card.onclick = () => highlightJob(jobLabel);

        // Algorithm-based order badge
        let reasonBadge = `Pos #${idx+1}`;
        if (sch.algorithm === 'SJF') reasonBadge = `BT: ${rem}t`;
        else if (sch.algorithm === 'PRIORITY') reasonBadge = `Pri: ${pObj.priority}`;
        else if (sch.algorithm === 'FCFS') reasonBadge = `AT: ${pObj.arrival_time}`;
        else if (sch.algorithm === 'RR') reasonBadge = `Turn #${idx+1}`;

        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
            <span style="font-weight:900; font-size:0.8rem; color:#f8fafc;">${jobLabel}</span>
            <span class="badge badge-sim" style="font-size:0.6rem; padding:1px 4px;">P10${pObj.pid || idx+1}</span>
          </div>
          <div style="font-size:0.68rem; color:#38bdf8; font-family:var(--font-mono); margin-bottom:2px;">Rem: ${rem}t • AT: ${pObj.arrival_time}</div>
          <div style="font-size:0.62rem; color:#94a3b8; background:#020617; border-radius:3px; padding:1px 4px; text-align:center;">${reasonBadge}</div>
        `;
        rqStrip.appendChild(card);
      });
    }
  }

  // 6. Process Execution Lanes (Horizontal Swimlanes)
  const lanesContainer = document.getElementById('process-execution-lanes');
  if (lanesContainer) {
    lanesContainer.innerHTML = '';
    procs.forEach((p, idx) => {
      const lbl = p.label;
      const isSelected = (schState.selectedJob === lbl);
      const isRunning = (tickData.active_process === lbl);
      const state = (tickData.states && tickData.states[lbl]) ? tickData.states[lbl] : 'READY';
      const rem = (tickData.remaining_burst && tickData.remaining_burst[lbl] !== undefined) ? tickData.remaining_burst[lbl] : p.burst_time;
      const total = p.burst_time;
      const elapsed = Math.max(0, total - rem);
      const pct = Math.min(100, Math.round((elapsed / total) * 100));

      const row = document.createElement('div');
      row.className = 'exec-lane-row' + (isSelected ? ' selected' : '');
      row.onclick = () => highlightJob(lbl);

      let badgeBg = '#0284c7';
      let statePill = `<span class="badge" style="background:#083344; color:#38bdf8;">READY</span>`;
      let progColor = '#0284c7';

      if (state === 'RUNNING') {
        badgeBg = '#059669';
        statePill = `<span class="badge" style="background:#064e3b; color:#34d399; font-weight:800;">● RUNNING</span>`;
        progColor = '#10b981';
      } else if (state === 'TERMINATED') {
        badgeBg = '#334155';
        statePill = `<span class="badge" style="background:#450a0a; color:#fca5a5;">TERMINATED</span>`;
        progColor = '#475569';
      } else if (state === 'NEW') {
        badgeBg = '#581c87';
        statePill = `<span class="badge" style="background:#3b0764; color:#c084fc;">NEW</span>`;
        progColor = '#a855f7';
      }

      // Arrival position percent along ruler
      const arrivalPct = Math.min(100, (p.arrival_time / maxDuration) * 100);

      row.innerHTML = `
        <div class="exec-lane-badge" style="background:${badgeBg};">
          ${lbl}
        </div>
        <div style="min-width:75px;">
          <div style="font-size:0.65rem; color:var(--text-dim);">[SIM: P10${p.pid || idx+1}]</div>
          <div style="font-size:0.7rem; color:#94a3b8; font-family:var(--font-mono);">Pri: ${p.priority} | AT: ${p.arrival_time}</div>
        </div>
        <div class="exec-lane-track">
          <div class="exec-lane-progress" style="width:${pct}%; background:${progColor};"></div>
          <div class="exec-lane-marker" style="left:${arrivalPct}%;" title="Arrives at t=${p.arrival_time}"></div>
        </div>
        <div style="min-width:65px; font-family:var(--font-mono); font-size:0.75rem; text-align:right; color:#67e8f9;">
          ${rem}/${total}t
        </div>
        <div style="min-width:85px; text-align:right;">
          ${statePill}
        </div>
      `;
      lanesContainer.appendChild(row);
    });
  }

  // 7. Update Gantt Playback Cursor position & Block Highlights
  const cursor = document.getElementById('gantt-playback-cursor');
  if (cursor && maxDuration > 0) {
    const leftPct = (tick / maxDuration) * 100;
    cursor.style.left = leftPct + '%';
  }

  gantt.forEach((b, idx) => {
    const blk = document.getElementById(`gantt-block-${idx}`);
    if (blk) {
      if (b.start <= tick && tick < b.end) {
        blk.style.boxShadow = '0 0 10px #34d399';
        blk.style.border = '2px solid #34d399';
      } else if (b.end <= tick) {
        blk.style.boxShadow = 'none';
        blk.style.border = 'none';
        blk.style.opacity = '0.9';
      } else {
        blk.style.boxShadow = 'none';
        blk.style.border = 'none';
        blk.style.opacity = '0.45';
      }
    }
  });

  // 8. Update Selected Process Inspector
  updateSelectedProcessInspector(sch, tickData);

  // 9. Update Event Feed
  updateSchedulerEventFeed(sch, tick);

  // 10. Update Secondary 5-State Machine Diagram
  updateSecondaryStateMachineVisuals(sch, tickData);
}

function updateSelectedProcessInspector(sch, tickData) {
  const procs = sch.raw_processes || [];
  if (procs.length === 0) return;

  // If no job explicitly selected, default to active job or first job
  let targetLabel = schState.selectedJob;
  if (!targetLabel) {
    targetLabel = tickData.active_process || procs[0].label;
  }

  const p = procs.find(item => item.label === targetLabel) || procs[0];
  const lbl = p.label;
  const rem = (tickData.remaining_burst && tickData.remaining_burst[lbl] !== undefined) ? tickData.remaining_burst[lbl] : p.burst_time;
  const state = (tickData.states && tickData.states[lbl]) ? tickData.states[lbl] : 'READY';
  const m = (sch.process_metrics || []).find(pm => (pm.label === lbl || pm.pid === p.pid)) || {};

  const pidBadge = document.getElementById('inspector-pid-badge');
  if (pidBadge) pidBadge.innerText = `[SIMULATED PID: P10${p.pid || 1}]`;

  const statePill = document.getElementById('inspector-state-pill');
  if (statePill) {
    statePill.innerText = `STATE: ${state}`;
    statePill.style.color = (state === 'RUNNING') ? '#34d399' : (state === 'TERMINATED' ? '#fca5a5' : '#38bdf8');
  }

  const jobName = document.getElementById('inspector-job-name');
  if (jobName) jobName.innerText = `${lbl} (Simulated Task)`;

  const explanation = document.getElementById('inspector-explanation');
  if (explanation) {
    if (state === 'NEW') {
      explanation.innerText = `${lbl} is in the NEW state. Allocated in PCB pool; scheduled to enter the Ready Queue at arrival time t=${p.arrival_time}.`;
    } else if (state === 'RUNNING') {
      explanation.innerText = `${lbl} is currently RUNNING on Core 0. First dispatched at t=${m.first_start_time || 0}. Remaining burst: ${rem}t out of ${p.burst_time}t.`;
    } else if (state === 'TERMINATED') {
      explanation.innerText = `${lbl} has successfully TERMINATED at t=${m.completion_time}. Total turnaround time was ${m.turnaround_time}t with ${m.waiting_time}t spent waiting in queue.`;
    } else {
      explanation.innerText = `${lbl} is currently in the READY queue awaiting Core 0 dispatch. Remaining burst: ${rem}t. Priority: ${p.priority}.`;
    }
  }

  // Populate metrics grid
  const setVal = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.innerText = (val !== undefined && val !== null && val !== '') ? val : '-';
  };
  setVal('insp-at', `${p.arrival_time}`);
  setVal('insp-bt', `${p.burst_time}t`);
  setVal('insp-rem', `${rem}t`);
  setVal('insp-st', m.first_start_time !== undefined && m.first_start_time !== '-' ? `${m.first_start_time}t` : '-');
  setVal('insp-ct', m.completion_time !== undefined && m.completion_time !== '-' ? `${m.completion_time}t` : '-');
  setVal('insp-wt', m.waiting_time !== undefined ? `${m.waiting_time}t` : '-');
  setVal('insp-tat', m.turnaround_time !== undefined ? `${m.turnaround_time}t` : '-');
  setVal('insp-rt', m.response_time !== undefined ? `${m.response_time}t` : '-');

  // State Transition Sequence History
  const historyEl = document.getElementById('inspector-history-timeline');
  if (historyEl) {
    let steps = [];
    steps.push(`<span style="color:#c084fc;">NEW (t=0)</span>`);
    steps.push(`<span style="color:#38bdf8;">READY (t=${p.arrival_time})</span>`);
    if (m.first_start_time !== undefined && m.first_start_time !== '-') {
      steps.push(`<span style="color:#34d399;">RUNNING (t=${m.first_start_time})</span>`);
    }
    if (m.completion_time !== undefined && m.completion_time !== '-') {
      steps.push(`<span style="color:#ef4444;">TERMINATED (t=${m.completion_time})</span>`);
    }
    historyEl.innerHTML = steps.join(' <span style="color:#64748b;">➔</span> ');
  }
}

function updateSchedulerEventFeed(sch, currentTick) {
  const feed = document.getElementById('sch-event-feed');
  if (!feed) return;

  const events = [];
  events.push(`[t=0] CPU Execution Studio initialized. Simulation ready.`);
  
  const procs = sch.raw_processes || [];
  const gantt = sch.gantt || [];

  for (let t = 0; t <= currentTick; t++) {
    // Arrival events
    procs.forEach(p => {
      if (p.arrival_time === t) {
        events.push(`[t=${t}] Process ${p.label} [P10${p.pid}] ARRIVED into Ready Queue (BT=${p.burst_time}t, Pri=${p.priority})`);
      }
    });

    // Dispatch and preemption events
    gantt.forEach(b => {
      if (b.start === t && b.label !== 'IDLE') {
        events.push(`[t=${t}] Core 0 DISPATCHED ${b.label} (Interval: [${b.start}→${b.end}])`);
      }
      if (b.end === t && b.label !== 'IDLE') {
        const pm = (sch.process_metrics || []).find(m => m.label === b.label);
        if (pm && pm.completion_time === t) {
          events.push(`[t=${t}] Process ${b.label} completed all bursts ➔ TERMINATED (TAT=${pm.turnaround_time}t)`);
        } else {
          events.push(`[t=${t}] Process ${b.label} time slice expired ➔ Preempted to Ready Queue`);
        }
      }
    });
  }

  feed.innerHTML = events.slice(-8).map(ev => `<div>${ev}</div>`).join('');
  feed.scrollTop = feed.scrollHeight;
}

function updateSecondaryStateMachineVisuals(sch, tickData) {
  const states = tickData.states || {};
  let countNew = 0;
  let countReady = 0;
  let countRunning = 0;
  let countTerm = 0;

  Object.values(states).forEach(st => {
    if (st === 'NEW') countNew++;
    else if (st === 'READY') countReady++;
    else if (st === 'RUNNING') countRunning++;
    else if (st === 'TERMINATED') countTerm++;
  });

  const txtNew = document.getElementById('txt-count-new');
  if (txtNew) txtNew.innerText = `${countNew} Process${countNew === 1 ? '' : 'es'}`;
  const txtReady = document.getElementById('txt-count-ready');
  if (txtReady) txtReady.innerText = `${countReady} Queued`;
  const txtRunning = document.getElementById('txt-running-label');
  if (txtRunning) txtRunning.innerText = tickData.active_process ? `${tickData.active_process} (Active)` : 'Core 0 Idle';
  const txtTerm = document.getElementById('txt-count-term');
  if (txtTerm) txtTerm.innerText = `${countTerm} Exited`;
}

function schStep(delta) {
  if (!schState.data) return;
  ensureAudioContext();
  const maxDuration = schState.data.total_duration || 12;
  const newTick = Math.max(0, Math.min(maxDuration, schState.currentTick + delta));
  updateSchVisualsAtTick(newTick);
  if (newTick >= maxDuration && schState.isPlaying) {
    schTogglePlay();
  }
}

function schStepEvent(dir) {
  if (!schState.data) return;
  ensureAudioContext();
  const sch = schState.data;
  const maxDuration = sch.total_duration || 12;
  const cur = schState.currentTick;
  const gantt = sch.gantt || [];
  const procs = sch.raw_processes || [];

  // Collect boundary ticks
  const boundaries = new Set();
  boundaries.add(0);
  boundaries.add(maxDuration);
  procs.forEach(p => boundaries.add(p.arrival_time));
  gantt.forEach(b => {
    boundaries.add(b.start);
    boundaries.add(b.end);
  });

  const sorted = Array.from(boundaries).sort((a, b) => a - b);
  let nextTick = cur;

  if (dir > 0) {
    for (let t of sorted) {
      if (t > cur) {
        nextTick = t;
        break;
      }
    }
  } else {
    for (let i = sorted.length - 1; i >= 0; i--) {
      if (sorted[i] < cur) {
        nextTick = sorted[i];
        break;
      }
    }
  }

  updateSchVisualsAtTick(nextTick);
}

function schTogglePlay() {
  ensureAudioContext();
  schState.isPlaying = !schState.isPlaying;
  const btn = document.getElementById('btn-sch-play');
  if (btn) {
    btn.innerText = schState.isPlaying ? '⏸ Pause' : '▶ Play';
    btn.className = 'btn btn-sm' + (schState.isPlaying ? ' btn-purple' : ' btn-accent');
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
  const statusEl = document.getElementById('sch-simulation-status');
  if (statusEl) {
    statusEl.innerText = schState.isPlaying ? '● RUNNING' : '○ PAUSED';
    statusEl.style.color = schState.isPlaying ? '#10b981' : '#94a3b8';
  }
}

function schResetTick() {
  if (schState.isPlaying) schTogglePlay();
  updateSchVisualsAtTick(0);
}

function setSchSpeed(ms, label) {
  schState.playInterval = ms;
  ['05', '1', '2', '4'].forEach(l => {
    const b = document.getElementById('btn-speed-' + l);
    if (b) b.className = 'btn btn-sm' + (l === label ? ' btn-accent' : '');
  });
  if (schState.isPlaying) {
    clearInterval(schState.timer);
    schState.timer = setInterval(() => { schStep(1); }, schState.playInterval);
  }
}

function highlightJob(lbl) {
  schState.selectedJob = (schState.selectedJob === lbl) ? null : lbl;
  updateSchVisualsAtTick(schState.currentTick);
}

function toggleSecondaryStateMachine() {
  const drawer = document.getElementById('secondary-state-machine-drawer');
  const btn = document.getElementById('btn-expand-sm');
  if (!drawer) return;
  const isOpen = (drawer.style.display !== 'none');
  drawer.style.display = isOpen ? 'none' : 'block';
  if (btn) btn.innerText = isOpen ? 'Expand ▼' : 'Collapse ▲';
}

function toggleProcessInputDrawer() {
  const el = document.getElementById('process-input-drawer');
  const btn = document.getElementById('btn-toggle-inputs');
  if (!el) return;
  const isOpen = (el.style.display !== 'none');
  el.style.display = isOpen ? 'none' : 'block';
  if (btn) btn.innerText = isOpen ? '✏️ Process Input Studio' : '✕ Close Input Studio';
}

function renderInputRows() {
  const tbody = document.getElementById('process-input-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  schState.inputRows.forEach((row, idx) => {
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid #1e293b';
    tr.innerHTML = `
      <td style="padding:4px;"><input type="text" value="${row.label}" style="width:75px; background:#0f172a; border:1px solid #334155; color:#fff; border-radius:3px; padding:3px 5px; font-weight:bold;" onchange="updateInputCell(${idx}, 'label', this.value)"></td>
      <td style="padding:4px;"><input type="number" min="0" max="100" value="${row.arrival_time}" style="width:65px; background:#0f172a; border:1px solid #334155; color:#fff; border-radius:3px; padding:3px 5px;" onchange="updateInputCell(${idx}, 'arrival_time', parseInt(this.value)||0)"></td>
      <td style="padding:4px;"><input type="number" min="1" max="100" value="${row.burst_time}" style="width:65px; background:#0f172a; border:1px solid #334155; color:#fff; border-radius:3px; padding:3px 5px;" onchange="updateInputCell(${idx}, 'burst_time', parseInt(this.value)||1)"></td>
      <td style="padding:4px;"><input type="number" min="1" max="10" value="${row.priority}" style="width:55px; background:#0f172a; border:1px solid #334155; color:#fff; border-radius:3px; padding:3px 5px;" onchange="updateInputCell(${idx}, 'priority', parseInt(this.value)||1)"></td>
      <td style="padding:4px; text-align:right;"><button class="btn btn-sm btn-danger" style="padding:2px 8px; font-size:0.65rem;" onclick="removeProcessRow(${idx})" ${schState.inputRows.length <= 1 ? 'disabled' : ''}>✕ Remove</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function updateInputCell(idx, field, val) {
  if (schState.inputRows[idx]) {
    schState.inputRows[idx][field] = val;
  }
}

function addProcessRow() {
  if (schState.inputRows.length >= 10) {
    showInputError('Maximum of 10 processes allowed.');
    return;
  }
  const nextIdx = schState.inputRows.length + 1;
  schState.inputRows.push({
    label: 'P' + nextIdx,
    arrival_time: nextIdx - 1,
    burst_time: 4,
    priority: nextIdx
  });
  renderInputRows();
}

function removeProcessRow(idx) {
  if (schState.inputRows.length <= 1) return;
  schState.inputRows.splice(idx, 1);
  renderInputRows();
}

function showInputError(msg) {
  const el = document.getElementById('input-error-msg');
  if (el) {
    el.innerText = msg;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 4000);
  }
}

function applyCustomProcesses() {
  if (schState.inputRows.length === 0) {
    showInputError('Process list cannot be empty.');
    return;
  }
  fetch('/api/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'set_custom_scheduler_processes', processes: schState.inputRows })
  })
    .then(r => r.json())
    .then(res => {
      if (res.status === 'ok') {
        showToast('✅ Scheduler updated with custom process specifications.');
        document.getElementById('input-error-msg').style.display = 'none';
        toggleProcessInputDrawer();
        pollData();
      } else {
        showInputError('Validation error: ' + (res.message || 'Invalid process parameters'));
      }
    })
    .catch(err => {
      showInputError('Network error applying processes: ' + err);
    });
}

function loadPresetDataset(key) {
  fetch('/api/action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'reset_scheduler_dataset', dataset: key })
  })
    .then(r => r.json())
    .then(res => {
      showToast(`✅ Loaded preset dataset: ${key}`);
      schState.inputRows = [];
      pollData();
    });
}

function resetCurrentDataset() {
  const sel = document.getElementById('select-dataset');
  const key = sel ? sel.value : 'standard';
  loadPresetDataset(key);
}

function updateQuantum(val) {
  const q = Math.max(1, Math.min(10, parseInt(val) || 2));
  postAction('set_scheduler_quantum', { quantum: q });
}

"""

pos_js_start = text.find(js_start_marker)
pos_js_end = text.find(js_end_marker)
if pos_js_start != -1 and pos_js_end != -1:
    text = text[:pos_js_start] + new_js + text[pos_js_end:]
    print("Replaced scheduler JavaScript successfully!")
else:
    print(f"Error finding JS markers: start={pos_js_start}, end={pos_js_end}")

# Write to web_server.py
with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(text)

py_compile.compile('dashboard/web_server.py', doraise=True)
print("Python py_compile: SUCCESS (0 errors)!")
