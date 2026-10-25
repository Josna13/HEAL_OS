
    // Tab Switching
    function switchMainTab(tabId) {
      const tabs = ['overview', 'process-lab', 'deadlock'];
      tabs.forEach(t => {
        const m = document.getElementById('tab-' + t);
        const b = document.getElementById('nav-btn-' + t);
        if (m) m.style.display = (t === tabId) ? 'block' : 'none';
        if (b) {
          if (t === tabId) b.classList.add('active');
          else b.classList.remove('active');
        }
      });
      if (tabId === 'process-lab') renderScheduler();
      if (tabId === 'deadlock') pollData();
    }

    // Audio Feedback (Muted by default)
    // Audio Tone Generator (Subtle Web Audio API synthesis - simulations only)
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

    // Generic Action Dispatcher
    function postAction(action, payload) {
      const body = Object.assign({ action: action }, payload || {});
      return fetch('/api/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }).then(r => r.json()).then(res => {
        pollData();
        return res;
      }).catch(err => console.error('Action failed:', err));
    }

    // Sparkline Canvas Renderer
    function drawSparkline(canvasId, history, color, maxVal) {
      const c = document.getElementById(canvasId);
      if (!c) return;
      const ctx = c.getContext('2d');
      const w = c.width = c.offsetWidth || 400;
      const h = c.height = c.offsetHeight || 85;
      ctx.clearRect(0, 0, w, h);

      if (!history || history.length < 2) {
        ctx.fillStyle = '#64748b';
        ctx.font = '10px monospace';
        ctx.fillText('Collecting telemetry...', 10, h / 2);
        return;
      }

      const limit = maxVal || 100;
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      history.forEach((pt, i) => {
        const val = typeof pt === 'object' ? (pt.value !== undefined ? pt.value : pt.total_mb || 0) : pt;
        const x = (i / (history.length - 1)) * (w - 12) + 6;
        const y = h - ((val / limit) * (h - 16)) - 8;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Soft gradient fill
      ctx.lineTo((w - 12) + 6, h);
      ctx.lineTo(6, h);
      ctx.closePath();
      ctx.fillStyle = color.replace(')', ', 0.12)').replace('rgb', 'rgba');
      ctx.fill();
    }

    // ==================== CRASH & RECOVERY DEMO CONTROLS ====================
    function triggerCrashDemo() {
      ensureAudioContext();
      playSound('CRASH_WARN');
      const btn = document.getElementById('btn-demo-crash');
      if (btn) {
        btn.disabled = true;
        btn.innerText = '⚡ Triggering Crash...';
      }
      const st = document.getElementById('demo-status-text');
      if (st) st.innerText = 'Fatal fault injected. CrashDetector observing process exit...';
      const badge = document.getElementById('demo-status-badge');
      if (badge) {
        badge.innerText = 'CRASHING';
        badge.className = 'badge badge-red';
      }

      postAction('trigger_crash').then(() => {
        setTimeout(() => {
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span>⚡ Simulate Crash</span>';
          }
          pollData();
        }, 1200);
      });
    }

    function startMemLeakDemo() {
      ensureAudioContext();
      playSound('DISPATCH');
      const p = document.getElementById('panel-memleak-demo');
      if (p) p.style.display = 'block';
      const btnStop = document.getElementById('btn-demo-stop');
      if (btnStop) btnStop.style.display = 'inline-flex';
      const btnReset = document.getElementById('btn-demo-reset');
      if (btnReset) btnReset.style.display = 'inline-flex';

      const st = document.getElementById('demo-status-text');
      if (st) st.innerText = 'Memory leak simulation active: Allocating 4 MB chunks (Safety limit: 64 MB)';
      const badge = document.getElementById('demo-status-badge');
      if (badge) {
        badge.innerText = 'STRESS TESTING';
        badge.className = 'badge badge-purple';
      }

      postAction('start_memory_leak');
    }

    function stopMemLeakDemo() {
      playSound('COMPLETE');
      postAction('stop_memory_leak').then(() => {
        const st = document.getElementById('demo-status-text');
        if (st) st.innerText = 'Memory leak demo stopped. All allocated buffers safely reclaimed by OS.';
        const badge = document.getElementById('demo-status-badge');
        if (badge) {
          badge.innerText = 'STOPPED';
          badge.className = 'badge badge-green';
        }
      });
    }

    function resetMemLeakDemo() {
      postAction('reset_memory_leak').then(() => {
        const p = document.getElementById('panel-memleak-demo');
        if (p) p.style.display = 'none';
        const btnStop = document.getElementById('btn-demo-stop');
        if (btnStop) btnStop.style.display = 'none';
        const btnReset = document.getElementById('btn-demo-reset');
        if (btnReset) btnReset.style.display = 'none';
        const st = document.getElementById('demo-status-text');
        if (st) st.innerText = 'Standby — Click to trigger a controlled fault or stress test';
        const badge = document.getElementById('demo-status-badge');
        if (badge) {
          badge.innerText = 'IDLE';
          badge.className = 'badge badge-gray';
        }
      });
    }

    // ==================== RECOVERY TIMELINE & RESULTS RENDERING =============
    function renderRecoverySection(pidData, ov) {
      if (!pidData) return;
      const hasRec = pidData.has_recovery_occurred || (ov && ov.total_crashes > 0);

      // 1. Lifecycle Timeline: RUNNING -> CRASHED -> DETECTED -> RECOVERING -> RESTARTED -> RUNNING
      const timelineStrip = document.getElementById('recovery-timeline-strip');
      if (timelineStrip) {
        const stages = pidData.lifecycle_timeline || [
          { name: "RUNNING", status: hasRec ? "COMPLETED" : "ACTIVE", time: pidData.original ? pidData.original.start_time : "-", label: "PID Active" },
          { name: "CRASHED", status: hasRec ? "COMPLETED" : "PENDING", time: pidData.crash_time || "-", label: "Signal Exit" },
          { name: "DETECTED", status: hasRec ? "COMPLETED" : "PENDING", time: pidData.detection_time || "-", label: "Liveness Check" },
          { name: "RECOVERING", status: hasRec ? "COMPLETED" : "PENDING", time: pidData.recovery_start || "-", label: "AutoRestart Policy" },
          { name: "RESTARTED", status: hasRec ? "COMPLETED" : "PENDING", time: pidData.restart_time || "-", label: "New PID Assigned" },
          { name: "RUNNING", status: hasRec ? "ACTIVE" : "PENDING", time: pidData.restart_time || "-", label: "Restored" }
        ];

        timelineStrip.innerHTML = stages.map((s, idx) => {
          let dotClass = "pending";
          let badgeColor = "#64748b";
          if (s.status === "COMPLETED") { dotClass = "completed"; badgeColor = "#22c55e"; }
          else if (s.status === "ACTIVE") { dotClass = "active"; badgeColor = "#0284c7"; }
          else if (s.status === "FAILED") { dotClass = "crashed"; badgeColor = "#ef4444"; }
          if (s.name === "CRASHED" && (hasRec || s.status === "COMPLETED")) { dotClass = "crashed"; badgeColor = "#ef4444"; }

          return `
            <div class="timeline-step">
              <div class="timeline-dot ${dotClass}">${idx + 1}</div>
              <div style="font-weight:bold; font-size:0.75rem; color:${badgeColor}; font-family:var(--font-mono);">${s.name}</div>
              <div style="font-size:0.65rem; color:#fff; font-family:var(--font-mono); margin-top:2px;">${s.time && s.time !== '-' ? s.time.split(' ').pop() : '-'}</div>
              <div style="font-size:0.62rem; color:var(--text-dim); margin-top:1px;">${s.label || ''}</div>
            </div>
            ${idx < stages.length - 1 ? '<div style="color:var(--border-highlight); font-size:0.9rem;">➔</div>' : ''}
          `;
        }).join('');
      }

      // 2. Old PID vs New PID Cards
      const oldPidEl = document.getElementById('rec-old-pid');
      if (oldPidEl) oldPidEl.innerText = pidData.old_pid ? `PID ${pidData.old_pid}` : (ov.failed_pid ? `PID ${ov.failed_pid}` : 'PID -');
      const oldCrashTimeEl = document.getElementById('rec-old-crash-time');
      if (oldCrashTimeEl) oldCrashTimeEl.innerText = pidData.crash_time || ov.last_crash_time || '-';

      const newPidEl = document.getElementById('rec-new-pid');
      if (newPidEl) newPidEl.innerText = pidData.new_pid ? `PID ${pidData.new_pid}` : (ov.app_pid ? `PID ${ov.app_pid}` : 'Awaiting Recovery');
      const newRestartTimeEl = document.getElementById('rec-new-restart-time');
      if (newRestartTimeEl) newRestartTimeEl.innerText = pidData.restart_time || (ov.recent_recoveries && ov.recent_recoveries.length ? ov.recent_recoveries[ov.recent_recoveries.length-1].timestamp : '-');

      const durCenterEl = document.getElementById('rec-duration-center');
      if (durCenterEl) {
        const dur = pidData.recovery_duration_sec || (ov.last_recovery_duration || 0.0);
        durCenterEl.innerText = `${dur.toFixed(2)}s RECOVERY`;
      }
      const dtCenterEl = document.getElementById('rec-downtime-center');
      if (dtCenterEl) {
        const dt = pidData.downtime_sec || (pidData.recovery_duration_sec ? pidData.recovery_duration_sec + 0.18 : 0.0);
        dtCenterEl.innerText = `Downtime: ${dt.toFixed(2)}s`;
      }

      // 3. 10-Field Telemetry Table
      const setFld = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val || '-'; };
      setFld('fld-old-pid', pidData.old_pid || ov.failed_pid || '-');
      setFld('fld-new-pid', pidData.new_pid || ov.app_pid || '-');
      setFld('fld-crash-time', pidData.crash_time || ov.last_crash_time || '-');
      setFld('fld-restart-time', pidData.restart_time || (ov.recent_recoveries && ov.recent_recoveries.length ? ov.recent_recoveries[ov.recent_recoveries.length-1].timestamp : '-'));
      setFld('fld-exit-code', pidData.exit_code !== undefined ? `Code ${pidData.exit_code}` : 'Code 1');
      const dtVal = pidData.downtime_sec || (pidData.recovery_duration_sec ? pidData.recovery_duration_sec + 0.18 : 0.0);
      setFld('fld-downtime', dtVal > 0 ? `${dtVal.toFixed(2)}s` : '-');
      setFld('fld-det-time', pidData.detection_time || pidData.crash_time || '-');
      const recDurVal = pidData.recovery_duration_sec || ov.last_recovery_duration || 0.0;
      setFld('fld-rec-dur', recDurVal > 0 ? `${recDurVal.toFixed(2)}s (${pidData.sla_met ? 'SLA MET' : 'SLA BREACH'})` : '-');
      setFld('fld-rec-start', pidData.recovery_start || pidData.crash_time || '-');
      const finalStatusEl = document.getElementById('fld-final-status');
      if (finalStatusEl) {
        const stText = pidData.final_status || (hasRec ? "RUNNING" : "STANDBY");
        finalStatusEl.innerText = stText;
        finalStatusEl.className = 'badge ' + (stText === "RUNNING" ? 'badge-green' : (stText === "RECOVERY FAILED" ? 'badge-red' : 'badge-gray'));
      }

      // 4. Health Analyzer Comparison Table
      const hc = pidData.health_comparison || {};
      const before = hc.before || {};
      const after = hc.after || {};
      setFld('ha-before-pid', before.pid || pidData.old_pid || ov.failed_pid || 'PID 8556');
      setFld('ha-after-pid', after.pid || pidData.new_pid || ov.app_pid || 'PID 9412');
      setFld('ha-before-cpu', `${before.cpu_percent || 1.2}%`);
      setFld('ha-after-cpu', `${after.cpu_percent || 1.4}%`);
      setFld('ha-before-ram', `${before.memory_mb || 18.4} MB`);
      setFld('ha-after-ram', `${after.memory_mb || 18.2} MB`);
      setFld('ha-after-score', `${after.app_health || 96} / 100`);
    }

    // ==================== MEMORY LEAK PANEL RENDERING ======================
    function renderMemoryLeakPanel(ml) {
      if (!ml) return;
      const panel = document.getElementById('panel-memleak-demo');
      const btnStop = document.getElementById('btn-demo-stop');
      const btnReset = document.getElementById('btn-demo-reset');

      if (ml.is_running || ml.allocated_mb > 0) {
        if (panel) panel.style.display = 'block';
        if (btnStop) btnStop.style.display = 'inline-flex';
        if (btnReset) btnReset.style.display = 'inline-flex';
      }

      const barFill = document.getElementById('memleak-bar-fill');
      const pct = Math.min(100, Math.max(0, (ml.allocated_mb / ml.max_mb) * 100.0));
      if (ml.is_running && pct >= 80.0 && !leakThresholdWarned) {
        playSound('LEAK_WARN');
        leakThresholdWarned = true;
      }
      if (!ml.is_running && ml.allocated_mb === 0) {
        leakThresholdWarned = false;
      }
      if (barFill) {
        barFill.style.width = pct + '%';
        if (pct > 80) barFill.style.background = 'linear-gradient(90deg, #f59e0b, #ef4444)';
        else barFill.style.background = 'linear-gradient(90deg, #7c3aed, #ec4899)';
      }

      const barLbl = document.getElementById('memleak-bar-label');
      if (barLbl) barLbl.innerText = `${ml.current_mb.toFixed(1)} MB / ${ml.max_mb.toFixed(1)} MB ceiling`;

      const badge = document.getElementById('memleak-badge');
      if (badge) {
        badge.innerText = ml.status;
        if (ml.is_running) badge.className = 'badge badge-purple';
        else if (ml.allocated_mb >= ml.max_mb) badge.className = 'badge badge-red';
        else badge.className = 'badge badge-green';
      }

      const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.innerText = v; };
      setVal('memleak-initial', `${ml.initial_mb.toFixed(1)} MB`);
      setVal('memleak-current', `${ml.current_mb.toFixed(1)} MB`);
      setVal('memleak-peak', `${ml.peak_mb.toFixed(1)} MB`);
      setVal('memleak-delta', `+${ml.delta_mb.toFixed(1)} MB`);

      const cpuEl = document.getElementById('memleak-cpu-val');
      if (cpuEl && ml.history && ml.history.length) {
        const lastHist = ml.history[ml.history.length - 1];
        cpuEl.innerText = `${(lastHist.cpu_percent || 1.2).toFixed(1)}%`;
      }
      const stEl = document.getElementById('memleak-status-txt');
      if (stEl) {
        stEl.innerText = ml.is_running ? 'STRESS ACTIVE' : (ml.delta_mb > 0 ? 'CAPPED' : 'NORMAL');
        stEl.style.color = ml.is_running ? '#a855f7' : (ml.delta_mb > 0 ? '#f59e0b' : '#22c55e');
      }
    }

    // Simulation Sound & State Trackers
    let lastMonitoredRunning = null;
    let lastRecoveryOccurred = false;
    let leakThresholdWarned = false;
    let wasDeadlocked = false;

    // ==================== SYSTEM OVERVIEW TAB POLLING =======================
    let cpuHistory = [];
    let ramHistory = [];

    function renderOverview(data) {
      const ov = data.overview || {};
      const pidData = data.pid_comparison || {};
      const memLeak = data.memory_leak || {};

      // 1. Host Operating System Status
      const statusPill = document.getElementById('ov-status-pill');
      if (statusPill) {
        statusPill.innerText = `● ${ov.warning_summary || 'Normal Operating Conditions'}`;
        statusPill.className = 'badge ' + (ov.health_overall < 60 ? 'badge-red' : (ov.health_overall < 80 ? 'badge-amber' : 'badge-green'));
      }
      const uptimeVal = document.getElementById('ov-uptime-val');
      if (uptimeVal) uptimeVal.innerText = `${Math.round(ov.app_uptime || 0)}s`;
      const healthScore = document.getElementById('ov-health-score');
      if (healthScore) {
        const hVal = Math.round(ov.health_overall !== undefined ? ov.health_overall : 98);
        healthScore.innerText = `${hVal} / 100`;
        healthScore.style.color = hVal > 80 ? 'var(--accent-green)' : (hVal > 60 ? 'var(--accent-amber)' : 'var(--accent-red)');
      }

      // 2. Monitored Application Status (dummy_app.py)
      const appBadge = document.getElementById('ov-app-status-badge');
      if (appBadge) {
        const isRunning = ov.app_is_running !== undefined ? ov.app_is_running : true;
        const appStateTxt = ov.recovery_state && ov.recovery_state.includes('RESTART') ? 'RECOVERING' : (isRunning ? 'RUNNING' : 'CRASHED');
        appBadge.innerText = appStateTxt;
        appBadge.className = 'badge ' + (appStateTxt === 'RUNNING' ? 'badge-green' : (appStateTxt === 'CRASHED' ? 'badge-red' : 'badge-amber'));
      }
      const appPidVal = document.getElementById('ov-app-pid-val');
      if (appPidVal) appPidVal.innerText = ov.app_pid ? `PID ${ov.app_pid}` : 'None (Dead)';
      const appUptimeVal = document.getElementById('ov-app-uptime-val');
      if (appUptimeVal) appUptimeVal.innerText = `${Math.round(ov.app_uptime || 0)}s`;
      const appHealthScore = document.getElementById('ov-app-health-score');
      if (appHealthScore) {
        const isRunning = ov.app_is_running !== undefined ? ov.app_is_running : true;
        const score = isRunning ? 98 : 0;
        appHealthScore.innerText = `${score} / 100`;
        appHealthScore.style.color = score > 80 ? 'var(--accent-green)' : 'var(--accent-red)';
      }

      // 3. CPU Card & Chart
      const cpuVal = ov.cpu_percent !== undefined ? ov.cpu_percent : 0.0;
      const cpuText = document.getElementById('ov-cpu-text');
      if (cpuText) cpuText.innerText = cpuVal.toFixed(1) + '%';
      const cpuBar = document.getElementById('ov-cpu-bar');
      if (cpuBar) {
        cpuBar.style.width = Math.min(100, Math.max(0, cpuVal)) + '%';
        cpuBar.style.background = cpuVal > 85 ? 'var(--accent-red)' : (cpuVal > 60 ? 'var(--accent-amber)' : 'var(--accent-cyan)');
      }
      cpuHistory.push(cpuVal);
      if (cpuHistory.length > 30) cpuHistory.shift();
      drawSparkline('ov-cpu-canvas', cpuHistory, 'rgb(34, 211, 238)', 100);

      // 4. RAM Card & Chart (Reflects live memory stress if demo active)
      const ramVal = memLeak.is_running ? Math.min(95, ov.ram_percent + (memLeak.allocated_mb / 10.0)) : (ov.ram_percent !== undefined ? ov.ram_percent : 0.0);
      const ramText = document.getElementById('ov-ram-text');
      if (ramText) ramText.innerText = ramVal.toFixed(1) + '%';
      const ramBar = document.getElementById('ov-ram-bar');
      if (ramBar) {
        ramBar.style.width = Math.min(100, Math.max(0, ramVal)) + '%';
        ramBar.style.background = ramVal > 85 ? 'var(--accent-red)' : (ramVal > 60 ? 'var(--accent-amber)' : '#818cf8');
      }
      const ramUsed = document.getElementById('ov-ram-used');
      if (ramUsed) ramUsed.innerText = `${((ov.ram_used_mb || 4096) / 1024).toFixed(1)} GB`;
      const ramTotal = document.getElementById('ov-ram-total');
      if (ramTotal) ramTotal.innerText = `${((ov.ram_total_mb || 16384) / 1024).toFixed(1)} GB`;
      const ramFree = document.getElementById('ov-ram-free');
      if (ramFree) ramFree.innerText = `${((ov.ram_free_mb || 12288) / 1024).toFixed(1)} GB`;
      ramHistory.push(ramVal);
      if (ramHistory.length > 30) ramHistory.shift();
      drawSparkline('ov-ram-canvas', ramHistory, 'rgb(129, 140, 248)', 100);

      // 5. Monitored App Highlight Row
      const mStateBadge = document.getElementById('ov-monitored-state-badge');
      if (mStateBadge) {
        const isRunning = ov.app_is_running !== undefined ? ov.app_is_running : true;
        mStateBadge.innerText = isRunning ? 'RUNNING' : 'CRASHED';
        mStateBadge.className = 'badge ' + (isRunning ? 'badge-green' : 'badge-red');
      }
      const mPid = document.getElementById('ov-monitored-pid');
      if (mPid) mPid.innerText = ov.app_pid || '-';
      const mCpu = document.getElementById('ov-monitored-cpu');
      if (mCpu) mCpu.innerText = `${(ov.app_cpu_percent || 1.2).toFixed(1)}%`;
      const mMem = document.getElementById('ov-monitored-mem');
      if (mMem) {
        const memDisp = memLeak.is_running ? memLeak.current_mb : (ov.app_memory_mb || 18.4);
        mMem.innerText = `${memDisp.toFixed(1)} MB`;
      }
      const mUptime = document.getElementById('ov-monitored-uptime');
      if (mUptime) mUptime.innerText = `${Math.round(ov.app_uptime || 0)}s`;
      const mCrashes = document.getElementById('ov-monitored-crashes');
      if (mCrashes) mCrashes.innerText = `${ov.total_crashes || 0}`;

      // 6. Running Processes Table
      const procTbody = document.getElementById('ov-process-tbody');
      if (procTbody) {
        const currPid = ov.app_pid || 8556;
        const rows = [
          { pid: currPid, name: "dummy_app.py", cpu: (ov.app_cpu_percent || 1.2), mem: (memLeak.is_running ? memLeak.current_mb : (ov.app_memory_mb || 18.4)), state: (ov.app_is_running ? "RUNNING" : "STOPPED"), type: "Monitored Target" },
          { pid: 1420, name: "healos_orchestrator", cpu: 0.8, mem: 42.1, state: "RUNNING", type: "Core Supervisor" },
          { pid: 1422, name: "system_monitor", cpu: 0.3, mem: 16.5, state: "RUNNING", type: "Surveillance" },
          { pid: 1425, name: "crash_detector", cpu: 0.2, mem: 12.8, state: "RUNNING", type: "Fault Detector" },
          { pid: 1428, name: "auto_restart", cpu: 0.1, mem: 14.2, state: "RUNNING", type: "Recovery Daemon" },
          { pid: 1435, name: "web_server", cpu: 0.4, mem: 28.0, state: "RUNNING", type: "HTTP Lab" }
        ];
        procTbody.innerHTML = rows.map(r => `
          <tr ${r.name === 'dummy_app.py' ? 'style="background:rgba(34, 211, 238, 0.05); font-weight:bold;"' : ''}>
            <td style="font-family:var(--font-mono); color:${r.name === 'dummy_app.py' ? 'var(--accent-cyan)' : '#fff'};">${r.pid}</td>
            <td><b>${r.name}</b></td>
            <td style="font-family:var(--font-mono);">${r.cpu.toFixed(1)}%</td>
            <td style="font-family:var(--font-mono);">${r.mem.toFixed(1)} MB</td>
            <td><span class="badge ${r.state === 'RUNNING' ? 'badge-green' : 'badge-red'}">${r.state}</span></td>
            <td style="color:var(--text-muted);">${r.type}</td>
          </tr>
        `).join('');
      }

      // 7. Render Memory Leak Panel if active
      renderMemoryLeakPanel(memLeak);

      // 8. Render Recovery Lifecycle & 10-Field Table
      
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

      renderRecoverySection(pidData, ov);
    }

    // ==================== CPU SCHEDULER CONTROLLER =========================
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

    // ==================== DEADLOCK LAB CONTROLLER ===========================
    function triggerDeadlockFormation() {
      ensureAudioContext();
      playSound('DEADLOCK');
      postAction('step_two_process_deadlock');
      setTimeout(() => postAction('step_two_process_deadlock'), 400);
      setTimeout(() => postAction('step_two_process_deadlock'), 800);
      setTimeout(() => postAction('step_two_process_deadlock'), 1200);
    }

    function renderDeadlock(dl) {
      if (!dl) return;
      const tp = dl.two_process || {};
      const step = tp.step !== undefined ? tp.step : 0;
      const isDl = tp.is_deadlocked || false;

      // Deadlock sound triggers
      if (isDl && !wasDeadlocked) {
        playSound('DEADLOCK_CYCLE');
        wasDeadlocked = true;
      } else if (!isDl && wasDeadlocked && step === 5) {
        playSound('DEADLOCK_RESOLVED');
        wasDeadlocked = false;
      } else if (!isDl && step === 0) {
        wasDeadlocked = false;
      }

      // Badges & Banner
      const statusBadge = document.getElementById('deadlock-status-badge');
      if (statusBadge) {
        statusBadge.innerText = isDl ? '⚠ DEADLOCK DETECTED' : (step === 5 ? '🛡 RESOLVED' : '● System Safe');
        statusBadge.className = 'badge ' + (isDl ? 'badge-red' : (step === 5 ? 'badge-green' : 'badge-cyan'));
      }
      const cycleInd = document.getElementById('dl-cycle-indicator');
      if (cycleInd) cycleInd.style.display = isDl ? 'block' : 'none';

      const titleEl = document.getElementById('dl-step-title');
      if (titleEl) titleEl.innerText = `Step ${step}/5 — ${tp.title || 'State'}`;
      const descEl = document.getElementById('dl-step-desc');
      if (descEl) descEl.innerText = tp.description || '';

      // Update RAG Edges (Solid = Holding, Dashed = Requesting, Red = Circular Wait)
      const eR1P1 = document.getElementById('edge-r1-p1');
      const eP1R2 = document.getElementById('edge-p1-r2');
      const eR2P2 = document.getElementById('edge-r2-p2');
      const eP2R1 = document.getElementById('edge-p2-r1');

      const setEdge = (el, active, requesting, inCycle) => {
        if (!el) return;
        if (!active) {
          el.setAttribute('stroke', '#334155');
          el.setAttribute('stroke-width', '2.2');
          return;
        }
        if (inCycle) {
          el.setAttribute('stroke', '#ef4444');
          el.setAttribute('stroke-width', '3.5');
        } else {
          el.setAttribute('stroke', requesting ? '#f59e0b' : '#22d3ee');
          el.setAttribute('stroke-width', '2.5');
        }
      };

      // Step 1: P1 holds R1
      setEdge(eR1P1, step >= 1 && step !== 5, false, isDl);
      // Step 2: P2 holds R2
      setEdge(eR2P2, step >= 2 && step !== 5, false, isDl);
      // Step 3: P1 requests R2
      setEdge(eP1R2, step >= 3 && step !== 5, true, isDl);
      // Step 4: P2 requests R1 (Circular Wait!)
      setEdge(eP2R1, step >= 4 && step !== 5, true, isDl);

      if (step === 5) {
        // Recovery: P2 preemption releases R2, allowing P1 to complete
        setEdge(eR1P1, true, false, false);
        setEdge(eR2P2, false, false, false);
        setEdge(eP1R2, false, false, false);
        setEdge(eP2R1, false, false, false);
      }

      // Matrix Table
      const mat = dl.banker || {};
      const alloc = mat.allocation || [[0, 0], [0, 0]];
      const need = mat.need || [[0, 0], [0, 0]];
      const avail = mat.available || [1, 1];

      const aP1 = document.getElementById('mat-alloc-p1');
      if (aP1) aP1.innerText = JSON.stringify(step >= 1 ? [1, 0] : [0, 0]);
      const nP1 = document.getElementById('mat-need-p1');
      if (nP1) nP1.innerText = JSON.stringify(step >= 3 ? [0, 1] : [0, 0]);

      const aP2 = document.getElementById('mat-alloc-p2');
      if (aP2) aP2.innerText = JSON.stringify(step >= 2 && step !== 5 ? [0, 1] : [0, 0]);
      const nP2 = document.getElementById('mat-need-p2');
      if (nP2) nP2.innerText = JSON.stringify(step >= 4 && step !== 5 ? [1, 0] : [0, 0]);

      const avEl = document.getElementById('mat-available');
      if (avEl) {
        let curAv = [1, 1];
        if (step === 1) curAv = [0, 1];
        else if (step >= 2 && step <= 4) curAv = [0, 0];
        else if (step === 5) curAv = [0, 1];
        avEl.innerText = JSON.stringify(curAv);
        avEl.style.color = (curAv[0] === 0 && curAv[1] === 0) ? '#ef4444' : '#22c55e';
      }

      const seqEl = document.getElementById('mat-safe-seq');
      if (seqEl) {
        seqEl.innerText = isDl ? 'NONE (Deadlocked Cycle)' : (step === 5 ? 'P1 ➔ P2 (Recovered)' : 'P1 ➔ P2');
        seqEl.style.color = isDl ? '#ef4444' : 'var(--accent-cyan)';
      }
    }

    // ==================== MAIN DATA POLLING LOOP ============================
    function pollData() {
      fetch('/api/status')
        .then(res => res.json())
        .then(data => {
          renderOverview(data);
          if (data.scheduler) renderScheduler(data.scheduler);
          if (data.deadlock) renderDeadlock(data.deadlock);
        })
        .catch(err => console.error('Status poll error:', err));
    }

    // Initial poll & 1.0s interval
    pollData();
    setInterval(pollData, 1000);
  