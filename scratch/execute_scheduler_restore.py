import sys
import shutil
import py_compile
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

print("Starting restoration of CPU Scheduler and sound integration in dashboard/web_server.py...")

# 1. Read files
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

# Backup
shutil.copyfile('dashboard/web_server.py', 'dashboard/web_server.py.bak')
print("Backed up dashboard/web_server.py to dashboard/web_server.py.bak")

with open('scratch/clean_tab2_html.txt', 'r', encoding='utf-8') as f:
    clean_tab2_html = f.read().strip()

# 2. Replace Tab 2 HTML
pos_t2_start = ws.find('<!-- ===================================================================== -->\n  <!-- TAB 2: CPU SCHEDULING')
if pos_t2_start == -1:
    pos_t2_start = ws.find('<main id="tab-process-lab"')
pos_t2_end = ws.find('</main>', pos_t2_start) + len('</main>')

print(f"Replacing Tab 2 HTML from {pos_t2_start} to {pos_t2_end}")
ws = ws[:pos_t2_start] + clean_tab2_html + ws[pos_t2_end:]

# 3. Replace Audio block
pos_audio_start = ws.find('// Audio Tone Generator')
if pos_audio_start == -1:
    pos_audio_start = ws.find('let soundEnabled = false;')

pos_audio_end = ws.find('// Generic Action Dispatcher', pos_audio_start)
print(f"Replacing Audio block from {pos_audio_start} to {pos_audio_end}")

new_audio_block = """// Audio Tone Generator (Subtle Web Audio API synthesis - simulations only)
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

    // Unlock browser audio on first user interaction
    window.addEventListener('click', () => { ensureAudioContext(); }, { once: true });

    function toggleSound() {
      ensureAudioContext();
      soundEnabled = !soundEnabled;
      const btn = document.getElementById('btn-sound-toggle');
      if (btn) {
        btn.innerText = soundEnabled ? '🔊 Sound On' : '🔇 Sound Muted';
        btn.className = 'btn btn-sm' + (soundEnabled ? ' btn-cyan' : '');
      }
    }

    function playTone(freq, type, dur, gainVal) {
      if (!soundEnabled) return;
      try {
        ensureAudioContext();
        if (!audioCtx) return;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type || 'sine';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        const g = gainVal !== undefined ? gainVal : 0.04;
        gain.gain.setValueAtTime(g, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + (dur || 0.15));
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + (dur || 0.15));
      } catch (e) {}
    }

    function playSound(event) {
      if (!soundEnabled) return;
      if (event === 'PROC_START' || event === 'DISPATCH' || event === 'RUNNING') {
        // Quiet sound when process starts executing (gentle 587Hz chime)
        playTone(587, 'sine', 0.12, 0.035);
      } else if (event === 'PROC_PREEMPT' || event === 'PREEMPT' || event === 'BLOCKED') {
        // Quiet sound when preempted (soft 330Hz square blip)
        playTone(330, 'square', 0.08, 0.025);
      } else if (event === 'PROC_COMPLETE' || event === 'COMPLETE') {
        // Quiet sound when process completes (positive 880Hz chime)
        playTone(880, 'sine', 0.2, 0.04);
      } else if (event === 'CRASH_WARN') {
        // Brief warning sound when crash is detected (warning 220Hz buzz)
        playTone(220, 'sawtooth', 0.25, 0.05);
      } else if (event === 'RECOVERY_PASS') {
        // Short success sound when recovery is verified (two-tone chime: 523Hz -> 659Hz)
        playTone(523, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(659, 'sine', 0.2, 0.04), 110);
      } else if (event === 'RECOVERY_FAIL') {
        // Error sound if failed (descending: 440Hz -> 220Hz)
        playTone(440, 'sawtooth', 0.15, 0.05);
        setTimeout(() => playTone(220, 'sawtooth', 0.22, 0.05), 120);
      } else if (event === 'LEAK_WARN') {
        // Subtle warning sound when resource threshold reached (gentle 700Hz ping)
        playTone(700, 'sine', 0.15, 0.035);
      } else if (event === 'DEADLOCK_CYCLE' || event === 'DEADLOCK') {
        // Warning sound when deadlock cycle is detected (ominous 260Hz alert)
        playTone(260, 'sawtooth', 0.3, 0.05);
      } else if (event === 'DEADLOCK_RESOLVED') {
        // Success sound when recovery completes (bright chord: 659Hz -> 784Hz)
        playTone(659, 'sine', 0.14, 0.04);
        setTimeout(() => playTone(784, 'sine', 0.22, 0.04), 120);
      }
    }
"""

ws = ws[:pos_audio_start] + new_audio_block + "\n    " + ws[pos_audio_end:]

# 4. Replace Scheduler JS
pos_sch_js_start = ws.find('// ==================== CPU SCHEDULER CONTROLLER =========================')
if pos_sch_js_start == -1:
    pos_sch_js_start = ws.find('let schedulerState = {')
    if pos_sch_js_start == -1:
        pos_sch_js_start = ws.find('let schState = {')

pos_sch_js_end = ws.find('// ==================== DEADLOCK LAB CONTROLLER ===========================', pos_sch_js_start)
print(f"Replacing Scheduler JS from {pos_sch_js_start} to {pos_sch_js_end}")

new_sch_js = """// ==================== CPU SCHEDULER CONTROLLER =========================
    let schState = {
      data: null,
      currentTick: 0,
      isPlaying: false,
      timer: null,
      playInterval: 800,
      inputRows: [],
      lastActiveJob: null,
      lastCompletedCount: 0
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

      // Subtle simulation sound triggers (discrete transitions only)
      if (tickData.active_process && tickData.active_process !== schState.lastActiveJob) {
        playSound('PROC_START');
      }
      if (tickData.is_context_switch) {
        playSound('PROC_PREEMPT');
      }
      const states = tickData.states || {};
      const completedNow = Object.keys(states).filter(j => states[j] === 'TERMINATED').length;
      if (schState.lastCompletedCount !== null && completedNow > schState.lastCompletedCount) {
        playSound('PROC_COMPLETE');
      }
      schState.lastActiveJob = tickData.active_process;
      schState.lastCompletedCount = completedNow;

      // 1. Ready Queue Stage
      const rqList = document.getElementById('sch-ready-list');
      const rqCount = document.getElementById('sch-rq-count');
      const readyQueue = tickData.ready_queue || [];
      if (rqCount) rqCount.innerText = `${readyQueue.length} queued`;
      if (rqList) {
        rqList.innerHTML = '';
        if (readyQueue.length === 0) {
          rqList.innerHTML = '<span style="color:#64748b; font-size:0.72rem;">No processes currently waiting in ready queue.</span>';
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

      // 2. CPU Core 0 Stage (With live countdown & progress)
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
      schState.lastActiveJob = null;
      schState.lastCompletedCount = 0;
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
"""

ws = ws[:pos_sch_js_start] + new_sch_js + "\n    " + ws[pos_sch_js_end:]

# 5. Update pollData() to render scheduler and deadlock, and wire sound tracking variables
# First check if tracking variables are placed before renderOverview
if "let lastMonitoredRunning = null;" not in ws:
    pos_ov_top = ws.find('// ==================== SYSTEM OVERVIEW TAB POLLING =======================')
    var_defs = """// Simulation Sound & State Trackers
    let lastMonitoredRunning = null;
    let lastRecoveryOccurred = false;
    let leakThresholdWarned = false;
    let wasDeadlocked = false;

    """
    ws = ws[:pos_ov_top] + var_defs + ws[pos_ov_top:]

# Update pollData
pos_polldata = ws.find('function pollData() {')
pos_polldata_end = ws.find('// Initial poll & 1.0s interval', pos_polldata)

new_polldata = """function pollData() {
      fetch('/api/status')
        .then(res => res.json())
        .then(data => {
          renderOverview(data);
          if (data.scheduler) renderScheduler(data.scheduler);
          if (data.deadlock) renderDeadlock(data.deadlock);
        })
        .catch(err => console.error('Status poll error:', err));
    }

    """
ws = ws[:pos_polldata] + new_polldata + ws[pos_polldata_end:]

# 6. Ensure Crash Demo trigger button calls CRASH_WARN sound
ws = ws.replace("playSound('DEADLOCK');\n      const btn = document.getElementById('btn-demo-crash');", "playSound('CRASH_WARN');\n      const btn = document.getElementById('btn-demo-crash');")

# 7. Ensure renderOverview has recovery verified sound
if "playSound('RECOVERY_PASS')" not in ws:
    # Find renderRecoverySection call in renderOverview
    pos_rec_call = ws.find('renderRecoverySection(pidData, ov);')
    if pos_rec_call != -1:
        rec_sound_code = """
      // Verification Sound Triggers (discrete transitions only)
      const hasRec = pidData.has_recovery_occurred || (ov && ov.total_crashes > 0);
      const isRunning = ov.app_is_running !== undefined ? ov.app_is_running : true;
      if (lastMonitoredRunning !== null) {
        if (lastMonitoredRunning === true && isRunning === false) {
          playSound('CRASH_WARN');
        }
        if (lastMonitoredRunning === false && isRunning === true && hasRec && !lastRecoveryOccurred) {
          playSound('RECOVERY_PASS');
          lastRecoveryOccurred = true;
        }
      }
      lastMonitoredRunning = isRunning;
      if (!hasRec) lastRecoveryOccurred = false;

      renderRecoverySection(pidData, ov);"""
        ws = ws[:pos_rec_call] + rec_sound_code + ws[pos_rec_call + len('renderRecoverySection(pidData, ov);'):]

# 8. Ensure renderMemoryLeakPanel has LEAK_WARN sound at 80% ceiling
if "playSound('LEAK_WARN')" not in ws:
    pos_pct = ws.find("const pct = Math.min(100, Math.max(0, (ml.allocated_mb / ml.max_mb) * 100.0));")
    if pos_pct != -1:
        leak_sound_code = """const pct = Math.min(100, Math.max(0, (ml.allocated_mb / ml.max_mb) * 100.0));
      if (ml.is_running && pct >= 80.0 && !leakThresholdWarned) {
        playSound('LEAK_WARN');
        leakThresholdWarned = true;
      }
      if (!ml.is_running && ml.allocated_mb === 0) {
        leakThresholdWarned = false;
      }"""
        ws = ws[:pos_pct] + leak_sound_code + ws[pos_pct + len("const pct = Math.min(100, Math.max(0, (ml.allocated_mb / ml.max_mb) * 100.0));"):]

# 9. Ensure Deadlock has DEADLOCK_CYCLE and DEADLOCK_RESOLVED sounds
if "playSound('DEADLOCK_CYCLE')" not in ws:
    pos_dl_render = ws.find("const isDl = tp.is_deadlocked || false;")
    if pos_dl_render != -1:
        dl_sound_code = """const isDl = tp.is_deadlocked || false;

      // Deadlock sound triggers
      if (isDl && !wasDeadlocked) {
        playSound('DEADLOCK_CYCLE');
        wasDeadlocked = true;
      } else if (!isDl && wasDeadlocked && step === 5) {
        playSound('DEADLOCK_RESOLVED');
        wasDeadlocked = false;
      } else if (!isDl && step === 0) {
        wasDeadlocked = false;
      }"""
        ws = ws[:pos_dl_render] + dl_sound_code + ws[pos_dl_render + len("const isDl = tp.is_deadlocked || false;"):]

# Save modified web_server.py
with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(ws)

print(f"dashboard/web_server.py updated successfully. Length: {len(ws)} chars, {len(ws.splitlines())} lines.")

# Compile check
py_compile.compile('dashboard/web_server.py', doraise=True)
print("py_compile check passed: dashboard/web_server.py is valid Python!")
