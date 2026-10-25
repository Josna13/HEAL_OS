import sys
sys.path.insert(0, '.')
import py_compile
import subprocess
import shutil

# Step 1: Prepare the HTML for Tab 3
dl_tab_html = """  <!-- ===================================================================== -->
  <!-- TAB 3: DEADLOCK DETECTION & SAFE RECOVERY LAB (LIVE ANIMATION STUDIO) -->
  <!-- ===================================================================== -->
  <main id="tab-deadlock" style="display:none;">
    <!-- 1. Top Control & Scenario Toolbar -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
          <div style="font-size:1.05rem; font-weight:900; color:#fff; display:flex; align-items:center; gap:8px;">
            <span>🔒 Real-Time Deadlock Visualization & Recovery Studio</span>
            <span class="badge badge-green" id="dl-status-badge"><span id="deadlock-status-badge" style="display:none;"></span>● System Safe</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
            Interactive Resource Allocation Graph (RAG): Watch processes compete, request locks, deadlock in circular wait, and recover step-by-step.
          </div>
        </div>

        <!-- Scenario Selector Buttons -->
        <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
          <span style="font-size:0.7rem; color:var(--text-dim); font-weight:bold; text-transform:uppercase;">Scenario:</span>
          <button class="btn btn-sm btn-cyan" id="btn-dl-sc-three" onclick="setDlScenario('three_process')">3-Process Circular Deadlock</button>
          <button class="btn btn-sm" id="btn-dl-sc-two" onclick="setDlScenario('two_process')">2-Process Mutex</button>
          <button class="btn btn-sm" id="btn-dl-sc-banker" onclick="setDlScenario('banker_safe')">Banker's Algorithm</button>
        </div>
      </div>
    </div>

    <!-- 2. Simulation Playback Controls Bar -->
    <div class="panel-box" style="padding:8px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
      <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
        <button class="btn btn-sm btn-green" id="btn-dl-play" onclick="dlTogglePlay()">▶ Start Demo</button>
        <button class="btn btn-sm" onclick="dlStep(1)">Step ❯</button>
        <button class="btn btn-sm" onclick="dlStep(-1)">❮ Back</button>
        <button class="btn btn-sm btn-purple" id="btn-dl-recover" onclick="dlStartRecovery()" style="font-weight:bold;">🛡 Recover Deadlock</button>
        <button class="btn btn-sm" onclick="dlReset()">↺ Reset</button>

        <!-- Speed Selector -->
        <span style="font-size:0.72rem; color:var(--text-muted); margin-left:8px; font-weight:bold;">Speed:</span>
        <button class="btn btn-sm" id="btn-dlspd-05" onclick="setDlSpeed(2400, '05')">0.5×</button>
        <button class="btn btn-sm btn-cyan" id="btn-dlspd-1" onclick="setDlSpeed(1200, '1')">1×</button>
        <button class="btn btn-sm" id="btn-dlspd-2" onclick="setDlSpeed(600, '2')">2×</button>
        <button class="btn btn-sm" id="btn-dlspd-4" onclick="setDlSpeed(300, '4')">4×</button>
      </div>

      <!-- Step Counter & Current Phase Indicator -->
      <div style="display:flex; align-items:center; gap:12px; font-family:var(--font-mono);">
        <div>
          <span style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase;">SIMULATION STEP:</span>
          <span id="dl-step-indicator" style="font-size:1.1rem; font-weight:900; color:var(--accent-cyan); margin-left:4px;">Step 0 / 11</span>
        </div>
        <span class="badge badge-gray" id="dl-phase-badge">○ READY</span>
      </div>
    </div>

    <!-- 3. Main Studio Workspace: (Left: Animated Graph, Right: Live Timeline & Inspector) -->
    <div style="display:grid; grid-template-columns: 1.35fr 1fr; gap:12px; margin-bottom:12px;">
      <!-- Left Column: Animated Resource Allocation Graph (RAG) -->
      <div class="panel-box" style="margin-bottom:0; display:flex; flex-direction:column;">
        <div class="panel-header" style="margin-bottom:8px;">
          <div class="panel-heading">
            <span>Animated Resource Allocation Graph</span>
            <span class="badge badge-cyan" id="dl-rag-type-badge">3 Processes • 3 Resources</span>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span id="dl-cycle-warning-pill" class="badge badge-red" style="display:none; animation:pulse-red 1.2s infinite ease-in-out;">⚠ CIRCULAR WAIT DETECTED</span>
          </div>
        </div>

        <!-- SVG Visual Canvas -->
        <div style="background:#020617; border:1px solid var(--border); border-radius:8px; padding:8px; position:relative; min-height:360px; display:flex; align-items:center; justify-content:center;">
          <svg id="rag-svg" width="560" height="340" viewBox="0 0 560 340" style="max-width:100%; height:auto;">
            <defs>
              <!-- Arrowhead for Allocation: Cyan -->
              <marker id="arrow-alloc" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <polygon points="0 1, 8 4, 0 7" fill="#22d3ee" />
              </marker>
              <!-- Arrowhead for Request: Amber -->
              <marker id="arrow-req" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <polygon points="0 1, 8 4, 0 7" fill="#f59e0b" />
              </marker>
              <!-- Arrowhead for Deadlock Cycle: Red -->
              <marker id="arrow-cycle" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto">
                <polygon points="0 0.5, 9 4, 0 7.5" fill="#ef4444" />
              </marker>
              <!-- Radial gradient for deadlocked process glow -->
              <radialGradient id="grad-deadlock" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ef4444" stop-opacity="0.5"/>
                <stop offset="100%" stop-color="#ef4444" stop-opacity="0"/>
              </radialGradient>
            </defs>

            <!-- Dynamic Edge Layer -->
            <g id="rag-edges-group"></g>

            <!-- Dynamic Node Layer -->
            <g id="rag-nodes-group"></g>
          </svg>
        </div>

        <!-- Legend and Visual Key -->
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-top:8px; padding:6px 10px; background:rgba(255,255,255,0.02); border-radius:4px; font-size:0.68rem; color:var(--text-dim);">
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:16px; height:3px; background:#22d3ee;"></span>
            <span>Solid Cyan: Holding Resource (Allocated)</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:16px; height:3px; border-top:2px dashed #f59e0b;"></span>
            <span>Dashed Amber: Requesting Lock (Waiting)</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-block; width:16px; height:4px; background:#ef4444; box-shadow:0 0 6px #ef4444;"></span>
            <span style="color:#fca5a5; font-weight:bold;">Glowing Red: Circular Wait (Deadlock)</span>
          </div>
        </div>
      </div>

      <!-- Right Column: Recovery Inspector & Execution Event Timeline -->
      <div style="display:flex; flex-direction:column; gap:12px;">
        <!-- Recovery Inspector & Heuristic Strategy Card -->
        <div class="panel-box" style="margin-bottom:0;">
          <div class="panel-header" style="margin-bottom:8px;">
            <div class="panel-heading">
              <span>Deadlock & Recovery Diagnostics</span>
            </div>
            <span class="badge badge-cyan" id="dl-strategy-badge">Process Preemption</span>
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:0.73rem;">
            <div style="background:#0a0f1d; padding:6px 8px; border-radius:4px; border:1px solid var(--border);">
              <div style="color:var(--text-dim); font-size:0.65rem; text-transform:uppercase;">Cycle Involves:</div>
              <div id="diag-cycle-procs" style="font-weight:bold; color:#fff; font-family:var(--font-mono); margin-top:2px;">None (Safe)</div>
            </div>
            <div style="background:#0a0f1d; padding:6px 8px; border-radius:4px; border:1px solid var(--border);">
              <div style="color:var(--text-dim); font-size:0.65rem; text-transform:uppercase;">Victim Candidate:</div>
              <div id="diag-victim-proc" style="font-weight:bold; color:#f59e0b; font-family:var(--font-mono); margin-top:2px;">None</div>
            </div>
          </div>

          <div style="margin-top:8px; font-size:0.72rem; line-height:1.4; color:var(--text-muted); background:#0f172a; border-left:3px solid var(--accent-cyan); padding:6px 8px; border-radius:2px;" id="diag-explanation-box">
            System running normally. No circular resource dependencies detected.
          </div>
        </div>

        <!-- Live Event Timeline (Scrollable ordered actions) -->
        <div class="panel-box" style="margin-bottom:0; flex:1; display:flex; flex-direction:column;">
          <div class="panel-header" style="margin-bottom:6px;">
            <div class="panel-heading">
              <span>Simulation Event Timeline</span>
            </div>
            <span style="font-size:0.68rem; color:var(--text-dim);" id="dl-timeline-count">0 events</span>
          </div>

          <div id="dl-event-feed" style="flex:1; max-height:220px; overflow-y:auto; display:flex; flex-direction:column; gap:6px; padding-right:4px;">
            <!-- Dynamic Event Cards -->
          </div>
        </div>
      </div>
    </div>

    <!-- 4. Resource Matrices and Safe-State Analysis (Allocation, Max, Need, Available) -->
    <div class="panel-box" style="margin-bottom:12px;">
      <div class="panel-header" style="margin-bottom:10px;">
        <div class="panel-heading">
          <span>Resource Allocation Matrices & Banker's Safe-State Analysis</span>
          <span class="badge badge-cyan">[MATHEMATICAL ACCOUNTING]</span>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="font-size:0.72rem; color:var(--text-muted);">
            Dijkstra Safe Sequence: <b id="mat-safe-seq-str" style="color:var(--accent-cyan); font-family:var(--font-mono);">P1 ➔ P2 ➔ P0</b>
          </div>
          <span class="badge badge-green" id="mat-safe-pill">SAFE STATE</span>
        </div>
      </div>

      <!-- 4 Matrices Grid -->
      <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px;">
        <!-- Matrix 1: Allocation -->
        <div style="background:#090d16; border:1px solid var(--border); border-radius:6px; padding:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; font-weight:bold; color:var(--accent-cyan);">Allocation Matrix (Current)</span>
          </div>
          <table class="clean-table" style="font-size:0.72rem;" id="mat-table-alloc">
            <!-- Dynamic -->
          </table>
        </div>

        <!-- Matrix 2: Maximum Claim -->
        <div style="background:#090d16; border:1px solid var(--border); border-radius:6px; padding:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; font-weight:bold; color:#818cf8;">Maximum Claim Matrix (Max)</span>
          </div>
          <table class="clean-table" style="font-size:0.72rem;" id="mat-table-max">
            <!-- Dynamic -->
          </table>
        </div>

        <!-- Matrix 3: Need Matrix (Need = Max - Allocation) -->
        <div style="background:#090d16; border:1px solid var(--border); border-radius:6px; padding:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; font-weight:bold; color:#f59e0b;">Need Matrix (Max − Alloc)</span>
          </div>
          <table class="clean-table" style="font-size:0.72rem;" id="mat-table-need">
            <!-- Dynamic -->
          </table>
        </div>

        <!-- Matrix 4: Available Resources Vector -->
        <div style="background:#090d16; border:1px solid var(--border); border-radius:6px; padding:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; font-weight:bold; color:#22c55e;">Available Vector (Free)</span>
          </div>
          <div id="mat-vector-available" style="display:flex; flex-direction:column; gap:6px; margin-top:8px;">
            <!-- Dynamic Badges -->
          </div>
          <div style="margin-top:10px; font-size:0.68rem; color:var(--text-dim); line-height:1.3;">
            <b style="color:#94a3b8;">OS Principle:</b> An <i>unsafe state</i> is not yet deadlocked, but lacks a guaranteed safe execution path if all processes demand their peak need.
          </div>
        </div>
      </div>
    </div>
  </main>"""

print("HTML template prepared successfully.")
