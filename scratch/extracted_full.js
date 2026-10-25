
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
      if (tabId === 'deadlock') { renderDeadlockView(); pollData(); }
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
      // CPU Scheduling & General Simulation Sounds
      if (event === 'PROC_START' || event === 'DISPATCH' || event === 'RUNNING') {
        playTone(587, 'sine', 0.12, 0.035);
      } else if (event === 'PROC_PREEMPT' || event === 'PREEMPT' || event === 'BLOCKED') {
        playTone(330, 'square', 0.08, 0.025);
      } else if (event === 'PROC_COMPLETE' || event === 'COMPLETE') {
        playTone(880, 'sine', 0.2, 0.04);
      } else if (event === 'CRASH_WARN') {
        playTone(220, 'sawtooth', 0.25, 0.05);
      } else if (event === 'RECOVERY_PASS') {
        playTone(523, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(659, 'sine', 0.2, 0.04), 110);
      } else if (event === 'RECOVERY_FAIL') {
        playTone(370, 'sawtooth', 0.14, 0.05);
        setTimeout(() => playTone(185, 'sawtooth', 0.22, 0.05), 120);
      } else if (event === 'LEAK_WARN') {
        playTone(700, 'sine', 0.15, 0.035);
      } 
      // Dedicated Deadlock & Recovery Lab Sound Effects
      else if (event === 'RES_ACQUIRE') {
        // Resource acquired: short, soft confirmation sound
        playTone(587, 'sine', 0.10, 0.035);
      } else if (event === 'RES_REQUEST') {
        // Resource request: subtle click or request sound
        playTone(440, 'triangle', 0.06, 0.025);
      } else if (event === 'PROC_BLOCKED') {
        // Process blocked: distinct warning tone
        playTone(310, 'square', 0.12, 0.035);
      } else if (event === 'DEADLOCK_ALERT' || event === 'DEADLOCK_CYCLE' || event === 'DEADLOCK') {
        // Deadlock detected: clear, brief alert sound
        playTone(260, 'sawtooth', 0.32, 0.055);
      } else if (event === 'RECOVERY_START') {
        // Recovery begins: distinct transition sound
        playTone(415, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(554, 'sine', 0.18, 0.04), 100);
      } else if (event === 'RES_RELEASE') {
        // Resource released: soft release sound
        playTone(520, 'sine', 0.08, 0.03);
        setTimeout(() => playTone(390, 'sine', 0.12, 0.025), 70);
      } else if (event === 'PROC_UNBLOCK') {
        // Process unblocked: short confirmation sound
        playTone(659, 'sine', 0.12, 0.035);
      } else if (event === 'ALL_COMPLETE' || event === 'DEADLOCK_RESOLVED') {
        // All processes completed: distinct success sound
        playTone(523, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(659, 'sine', 0.14, 0.04), 90);
        setTimeout(() => playTone(784, 'sine', 0.22, 0.045), 180);
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

    // ==================== REAL-TIME DEADLOCK VISUALIZATION & RECOVERY STUDIO =====================

    const DL_SCENARIOS = {
      three_process: {
        id: 'three_process',
        name: '3-Process Circular Deadlock (P0, P1, P2)',
        procs: ['P0', 'P1', 'P2'],
        resources: [
          { id: 'R0', name: 'R0 (Mutex A)', total: 1 },
          { id: 'R1', name: 'R1 (Mutex B)', total: 1 },
          { id: 'R2', name: 'R2 (Mutex C)', total: 1 }
        ],
        max_matrix: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
        node_coords: {
          P0: { x: 280, y: 55, type: 'P', label: 'P0' },
          R1: { x: 410, y: 115, type: 'R', label: 'R1' },
          P1: { x: 410, y: 225, type: 'P', label: 'P1' },
          R2: { x: 280, y: 285, type: 'R', label: 'R2' },
          P2: { x: 150, y: 225, type: 'P', label: 'P2' },
          R0: { x: 150, y: 115, type: 'R', label: 'R0' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State (System Nominal)',
            tag: 'INIT',
            action: 'System initialized. P0, P1, P2 are READY. Resources R0, R1, R2 are currently unallocated.',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
            states: { P0: 'READY', P1: 'READY', P2: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P0 ➔ P1 ➔ P2',
            explanation: 'All single-instance resources are free. Safe sequence exists.',
            sound: null
          },
          {
            step: 1,
            title: 'P0 Acquires R0',
            tag: 'ACQUIRE',
            action: 'P0 requests and is granted Resource R0 (Mutex A). Allocation edge: R0 ➔ P0.',
            available: [0, 1, 1],
            allocation: [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 1, 1], [1, 0, 1]],
            states: { P0: 'RUNNING', P1: 'READY', P2: 'READY' },
            edges: [{ from: 'R0', to: 'P0', type: 'alloc' }],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P1 ➔ P2 ➔ P0',
            explanation: 'P0 is executing with R0 held. R1 and R2 remain available.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 2,
            title: 'P1 Acquires R1',
            tag: 'ACQUIRE',
            action: 'P1 requests and is granted Resource R1 (Mutex B). Allocation edge: R1 ➔ P1.',
            available: [0, 0, 1],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 1]],
            states: { P0: 'RUNNING', P1: 'RUNNING', P2: 'READY' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P2 ➔ P0 ➔ P1',
            explanation: 'P1 holds R1 while P0 holds R0. R2 is the only remaining available resource.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 3,
            title: 'P2 Acquires R2',
            tag: 'ACQUIRE',
            action: 'P2 requests and is granted Resource R2 (Mutex C). Allocation edge: R2 ➔ P2. Available pool exhausted.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'RUNNING', P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'Unsafe (Critical)',
            explanation: 'All 3 resources are held: P0 holds R0, P1 holds R1, P2 holds R2. Available=[0,0,0].',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 4,
            title: 'P0 Requests R1 (Blocked)',
            tag: 'BLOCKED',
            action: 'P0 requests R1 to proceed. R1 is currently held by P1 (0 free). P0 enters BLOCKED state. Request edge: P0 ➔ R1.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'BLOCKED', P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P0 is waiting for P1 to release R1. P0 cannot continue execution.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 5,
            title: 'P1 Requests R2 (Blocked)',
            tag: 'BLOCKED',
            action: 'P1 requests R2 to proceed. R2 is currently held by P2 (0 free). P1 enters BLOCKED state. Request edge: P1 ➔ R2.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'BLOCKED', P1: 'BLOCKED', P2: 'RUNNING' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0', 'P1'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P1 is waiting for P2 to release R2, while P0 is waiting for P1.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 6,
            title: 'P2 Requests R0 (CIRCULAR WAIT DEADLOCK)',
            tag: 'DEADLOCK',
            action: 'P2 requests R0, which is held by P0. Circular Wait cycle closed: P0 ➔ R1 ➔ P1 ➔ R2 ➔ P2 ➔ R0 ➔ P0! Complete deadlock.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            states: { P0: 'DEADLOCKED', P1: 'DEADLOCKED', P2: 'DEADLOCKED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc', in_cycle: true },
              { from: 'P0', to: 'R1', type: 'req', in_cycle: true },
              { from: 'R1', to: 'P1', type: 'alloc', in_cycle: true },
              { from: 'P1', to: 'R2', type: 'req', in_cycle: true },
              { from: 'R2', to: 'P2', type: 'alloc', in_cycle: true },
              { from: 'P2', to: 'R0', type: 'req', in_cycle: true }
            ],
            cycle: ['P0', 'R1', 'P1', 'R2', 'P2', 'R0', 'P0'],
            blocked: ['P0', 'P1', 'P2'],
            is_deadlocked: true,
            recovery_active: false,
            victim: null,
            safe_seq: 'NONE (Cycle Detected)',
            explanation: 'Genuine deadlock: All Coffman conditions met (Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait).',
            sound: 'DEADLOCK_ALERT'
          },
          {
            step: 7,
            title: 'Recovery: Victim Selection & Preemption',
            tag: 'RECOVERY',
            action: 'Deadlock recovery initiated. Heuristic evaluates victim cost: P2 selected as victim (lowest rollback penalty). P2 preempted; R2 released back to OS.',
            available: [0, 0, 1],
            allocation: [[1, 0, 0], [0, 1, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 1], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'BLOCKED', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0', 'P1'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2 (Lowest Cost)',
            safe_seq: 'P1 ➔ P0 ➔ P2',
            explanation: 'Circular wait broken! Resource R2 is now available (Available=[0,0,1]). Evaluating pending requests...',
            sound: 'RECOVERY_START'
          },
          {
            step: 8,
            title: 'P1 Unblocked & Allocated R2',
            tag: 'UNBLOCK',
            action: 'Rechecking blocked requests: P1 was waiting for R2. Since R2 is now free, request is granted! R2 allocated to P1. P1 returns to RUNNING.',
            available: [0, 0, 0],
            allocation: [[1, 0, 0], [0, 1, 1], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'RUNNING', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' },
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P1', type: 'alloc' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2 (Preempted)',
            safe_seq: 'P1 ➔ P0',
            explanation: 'P1 holds both R1 and R2, satisfying its maximum claim. P1 resumes active execution.',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 9,
            title: 'P1 Completes & Releases R1, R2',
            tag: 'RELEASE',
            action: 'P1 completes execution and terminates (COMPLETED). Resources R1 and R2 are returned to the available pool (Available=[0,1,1]).',
            available: [0, 1, 1],
            allocation: [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 1, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'BLOCKED', P1: 'COMPLETED', P2: 'TERMINATED' },
            edges: [
              { from: 'R0', to: 'P0', type: 'alloc' },
              { from: 'P0', to: 'R1', type: 'req' }
            ],
            cycle: [],
            blocked: ['P0'],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2',
            safe_seq: 'P0 ➔ P2',
            explanation: "P1 has completed and freed all resources. P0's pending request for R1 can now be satisfied.",
            sound: 'RES_RELEASE'
          },
          {
            step: 10,
            title: 'P0 Acquires R1 & Completes',
            tag: 'UNBLOCK',
            action: 'P0 acquires freed R1, executes to completion (COMPLETED), and releases R0 and R1 back to OS. Available pool: [1,1,1].',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [1, 0, 1]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'READY TO RESTART' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: true,
            victim: 'P2',
            safe_seq: 'P2',
            explanation: 'P0 completed cleanly. All original resources are now free for victim P2 to restart.',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 11,
            title: 'P2 Restarted — All Processes Completed',
            tag: 'SUCCESS',
            action: 'Preempted victim P2 is restarted with full resources available. P2 runs to completion. All processes COMPLETED! System 100% recovered.',
            available: [1, 1, 1],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'System Nominal (All Finished)',
            explanation: 'Deadlock demonstration successfully concluded. 0 active locks, 0 blocked threads, 100% completion.',
            sound: 'ALL_COMPLETE'
          }
        ]
      },

      two_process: {
        id: 'two_process',
        name: '2-Process Mutex Deadlock (P1, P2)',
        procs: ['P1', 'P2'],
        resources: [
          { id: 'R1', name: 'R1 (Mutex 1)', total: 1 },
          { id: 'R2', name: 'R2 (Mutex 2)', total: 1 }
        ],
        max_matrix: [[1, 1], [1, 1]],
        node_coords: {
          P1: { x: 200, y: 75, type: 'P', label: 'P1' },
          P2: { x: 360, y: 75, type: 'P', label: 'P2' },
          R1: { x: 200, y: 245, type: 'R', label: 'R1' },
          R2: { x: 360, y: 245, type: 'R', label: 'R2' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State (Resources Free)',
            tag: 'INIT',
            action: 'P1 and P2 initialized. Single-instance mutexes R1 and R2 are free. Available=[1,1].',
            available: [1, 1],
            allocation: [[0, 0], [0, 0]],
            need: [[1, 1], [1, 1]],
            states: { P1: 'READY', P2: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P1 ➔ P2',
            explanation: 'Both processes ready to request mutexes.',
            sound: null
          },
          {
            step: 1,
            title: 'P1 Acquires R1',
            tag: 'ACQUIRE',
            action: 'P1 requests and is granted Mutex R1. Allocation edge: R1 ➔ P1. Available=[0,1].',
            available: [0, 1],
            allocation: [[1, 0], [0, 0]],
            need: [[0, 1], [1, 1]],
            states: { P1: 'RUNNING', P2: 'READY' },
            edges: [{ from: 'R1', to: 'P1', type: 'alloc' }],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'P2 ➔ P1',
            explanation: 'P1 holds R1; R2 is free.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 2,
            title: 'P2 Acquires R2',
            tag: 'ACQUIRE',
            action: 'P2 requests and is granted Mutex R2. Allocation edge: R2 ➔ P2. Available=[0,0].',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'RUNNING', P2: 'RUNNING' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'Unsafe',
            explanation: 'Both single-instance resources are now allocated.',
            sound: 'RES_ACQUIRE'
          },
          {
            step: 3,
            title: 'P1 Requests R2 (Blocked)',
            tag: 'BLOCKED',
            action: 'P1 requests R2 to proceed. R2 is held by P2. P1 is BLOCKED. Request edge: P1 ➔ R2.',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'BLOCKED', P2: 'RUNNING' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc' },
              { from: 'R2', to: 'P2', type: 'alloc' },
              { from: 'P1', to: 'R2', type: 'req' }
            ],
            cycle: [],
            blocked: ['P1'],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: 'None',
            explanation: 'P1 waiting on R2 held by P2.',
            sound: 'PROC_BLOCKED'
          },
          {
            step: 4,
            title: 'P2 Requests R1 (DEADLOCK FORMED)',
            tag: 'DEADLOCK',
            action: 'P2 requests R1, held by P1. Circular wait formed: P1 ➔ R2 ➔ P2 ➔ R1 ➔ P1. DEADLOCK!',
            available: [0, 0],
            allocation: [[1, 0], [0, 1]],
            need: [[0, 1], [1, 0]],
            states: { P1: 'DEADLOCKED', P2: 'DEADLOCKED' },
            edges: [
              { from: 'R1', to: 'P1', type: 'alloc', in_cycle: true },
              { from: 'P1', to: 'R2', type: 'req', in_cycle: true },
              { from: 'R2', to: 'P2', type: 'alloc', in_cycle: true },
              { from: 'P2', to: 'R1', type: 'req', in_cycle: true }
            ],
            cycle: ['P1', 'R2', 'P2', 'R1', 'P1'],
            blocked: ['P1', 'P2'],
            is_deadlocked: true,
            recovery_active: false,
            victim: null,
            safe_seq: 'NONE (Cycle Detected)',
            explanation: 'Both processes blocked in circular wait. Recovery required.',
            sound: 'DEADLOCK_ALERT'
          },
          {
            step: 5,
            title: 'Recovery: Preempt P2 & Complete P1',
            tag: 'SUCCESS',
            action: 'Recovery preemption terminates P2, freeing R2. P1 acquires R2, runs to completion, and releases all resources. All finished.',
            available: [1, 1],
            allocation: [[0, 0], [0, 0]],
            need: [[0, 0], [0, 0]],
            states: { P1: 'COMPLETED', P2: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: 'P2',
            safe_seq: 'P1 ➔ P2 (Recovered)',
            explanation: 'Cycle broken! P1 finished and released R1, R2. P2 completed.',
            sound: 'ALL_COMPLETE'
          }
        ]
      },

      banker_safe: {
        id: 'banker_safe',
        name: "Banker's Algorithm Safe-State Analysis (5 Processes)",
        procs: ['P0', 'P1', 'P2', 'P3', 'P4'],
        resources: [
          { id: 'A', name: 'A (CPU)', total: 10 },
          { id: 'B', name: 'B (RAM)', total: 5 },
          { id: 'C', name: 'C (Disk)', total: 7 }
        ],
        max_matrix: [
          [7, 5, 3],
          [3, 2, 2],
          [9, 0, 2],
          [2, 2, 2],
          [4, 3, 3]
        ],
        node_coords: {
          P0: { x: 120, y: 55, type: 'P', label: 'P0' },
          P1: { x: 120, y: 110, type: 'P', label: 'P1' },
          P2: { x: 120, y: 165, type: 'P', label: 'P2' },
          P3: { x: 120, y: 220, type: 'P', label: 'P3' },
          P4: { x: 120, y: 275, type: 'P', label: 'P4' },
          A: { x: 420, y: 80, type: 'R', label: 'A' },
          B: { x: 420, y: 165, type: 'R', label: 'B' },
          C: { x: 420, y: 250, type: 'R', label: 'C' }
        },
        steps: [
          {
            step: 0,
            title: 'Initial State — Banker Benchmark',
            tag: 'INIT',
            action: '5 processes and 3 resources. Total instances: [10, 5, 7]. Currently available: [3, 3, 2].',
            available: [3, 3, 2],
            allocation: [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
            need: [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
            states: { P0: 'READY', P1: 'READY', P2: 'READY', P3: 'READY', P4: 'READY' },
            edges: [
              { from: 'B', to: 'P0', type: 'alloc' },
              { from: 'A', to: 'P1', type: 'alloc' },
              { from: 'A', to: 'P2', type: 'alloc' },
              { from: 'C', to: 'P2', type: 'alloc' },
              { from: 'A', to: 'P3', type: 'alloc' },
              { from: 'B', to: 'P3', type: 'alloc' },
              { from: 'C', to: 'P3', type: 'alloc' },
              { from: 'C', to: 'P4', type: 'alloc' }
            ],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'Dijkstra safety algorithm tests which process can finish with Available=[3,3,2].',
            sound: null
          },
          {
            step: 1,
            title: 'P1 Evaluated (Need [1,2,2] <= Available [3,3,2])',
            tag: 'UNBLOCK',
            action: "P1's Need [1,2,2] <= Available [3,3,2]. P1 runs to completion and releases allocation [2,0,0]. New Available = [5,3,2].",
            available: [5, 3, 2],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'READY', P4: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P1 finishes successfully. Available pool expanded to [5, 3, 2].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 2,
            title: 'P3 Evaluated (Need [0,1,1] <= Available [5,3,2])',
            tag: 'UNBLOCK',
            action: "P3's Need [0,1,1] <= Available [5,3,2]. P3 runs to completion and releases allocation [2,1,1]. New Available = [7,4,3].",
            available: [7, 4, 3],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 2]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 0, 0], [4, 3, 1]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'READY' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P3 finishes successfully. Available pool expanded to [7, 4, 3].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 3,
            title: 'P4 Evaluated (Need [4,3,1] <= Available [7,4,3])',
            tag: 'UNBLOCK',
            action: "P4's Need [4,3,1] <= Available [7,4,3]. P4 runs to completion and releases allocation [0,0,2]. New Available = [7,4,5].",
            available: [7, 4, 5],
            allocation: [[0, 1, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 0]],
            need: [[7, 4, 3], [0, 0, 0], [6, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'READY', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P4 finishes successfully. Available pool expanded to [7, 4, 5].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 4,
            title: 'P0 Evaluated (Need [7,4,3] <= Available [7,4,5])',
            tag: 'UNBLOCK',
            action: "P0's Need [7,4,3] <= Available [7,4,5]. P0 runs to completion and releases allocation [0,1,0]. New Available = [7,5,5].",
            available: [7, 5, 5],
            allocation: [[0, 0, 0], [0, 0, 0], [3, 0, 2], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [6, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'READY', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P0 finishes successfully. Available pool expanded to [7, 5, 5].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 5,
            title: 'P2 Evaluated (Need [6,0,0] <= Available [7,5,5])',
            tag: 'UNBLOCK',
            action: "P2's Need [6,0,0] <= Available [7,5,5]. P2 runs to completion and releases allocation [3,0,2]. New Available = [10,5,7].",
            available: [10, 5, 7],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2>',
            explanation: 'P2 finishes. All total resources returned: [10, 5, 7].',
            sound: 'PROC_UNBLOCK'
          },
          {
            step: 6,
            title: 'Banker Verification Complete — Safe State Confirmed',
            tag: 'SUCCESS',
            action: 'All 5 processes have executed to completion without deadlock. Safe sequence <P1, P3, P4, P0, P2> verified!',
            available: [10, 5, 7],
            allocation: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            need: [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
            states: { P0: 'COMPLETED', P1: 'COMPLETED', P2: 'COMPLETED', P3: 'COMPLETED', P4: 'COMPLETED' },
            edges: [],
            cycle: [],
            blocked: [],
            is_deadlocked: false,
            recovery_active: false,
            victim: null,
            safe_seq: '<P1, P3, P4, P0, P2> (VERIFIED)',
            explanation: 'Bankers Algorithm guarantees safe resource allocation.',
            sound: 'ALL_COMPLETE'
          }
        ]
      }
    };

    let dlState = {
      scenarioKey: 'three_process',
      stepIdx: 0,
      isPlaying: false,
      timer: null,
      playInterval: 1200,
      lastSoundStep: -1
    };

    function setDlScenario(key) {
      ensureAudioContext();
      if (!DL_SCENARIOS[key]) return;
      if (dlState.isPlaying) dlTogglePlay();
      dlState.scenarioKey = key;
      dlState.stepIdx = 0;
      dlState.lastSoundStep = -1;

      ['three', 'two', 'banker'].forEach(k => {
        const btn = document.getElementById('btn-dl-sc-' + k);
        if (btn) {
          const match = (k === 'three' && key === 'three_process') ||
                        (k === 'two' && key === 'two_process') ||
                        (k === 'banker' && key === 'banker_safe');
          btn.className = 'btn btn-sm' + (match ? ' btn-cyan' : '');
        }
      });

      renderDeadlockView();
    }

    function dlTogglePlay() {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;
      dlState.isPlaying = !dlState.isPlaying;

      const playBtn = document.getElementById('btn-dl-play');
      if (playBtn) {
        playBtn.innerText = dlState.isPlaying ? '⏸ Pause Demo' : '▶ Resume Demo';
        playBtn.className = 'btn btn-sm ' + (dlState.isPlaying ? 'btn-amber' : 'btn-green');
      }

      if (dlState.timer) {
        clearInterval(dlState.timer);
        dlState.timer = null;
      }

      if (dlState.isPlaying) {
        if (dlState.stepIdx >= sc.steps.length - 1) {
          dlState.stepIdx = 0;
          dlState.lastSoundStep = -1;
          renderDeadlockView();
        }
        dlState.timer = setInterval(() => {
          dlStep(1);
        }, dlState.playInterval);
      }
    }

    function dlStep(delta) {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;

      const newIdx = dlState.stepIdx + delta;
      if (newIdx < 0 || newIdx >= sc.steps.length) {
        if (dlState.isPlaying) dlTogglePlay();
        return;
      }

      dlState.stepIdx = newIdx;
      const stepData = sc.steps[newIdx];

      // Play discrete sound effect on forward transition
      if (delta > 0 && stepData.sound && dlState.lastSoundStep !== newIdx) {
        playSound(stepData.sound);
        dlState.lastSoundStep = newIdx;
      }

      renderDeadlockView();

      if (newIdx >= sc.steps.length - 1 && dlState.isPlaying) {
        dlTogglePlay();
      }
    }

    function dlStartRecovery() {
      ensureAudioContext();
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;

      if (dlState.scenarioKey === 'three_process') {
        // If not deadlocked yet, jump to deadlock step (6) and play
        if (dlState.stepIdx < 6) {
          dlState.stepIdx = 6;
          playSound('DEADLOCK_ALERT');
          renderDeadlockView();
          setTimeout(() => {
            if (!dlState.isPlaying) dlTogglePlay();
          }, 800);
        } else if (dlState.stepIdx === 6) {
          // At deadlock -> proceed with recovery (step 7)
          dlStep(1);
          if (!dlState.isPlaying) dlTogglePlay();
        }
      } else if (dlState.scenarioKey === 'two_process') {
        if (dlState.stepIdx < 4) {
          dlState.stepIdx = 4;
          playSound('DEADLOCK_ALERT');
          renderDeadlockView();
          setTimeout(() => {
            if (!dlState.isPlaying) dlTogglePlay();
          }, 800);
        } else if (dlState.stepIdx === 4) {
          dlStep(1);
        }
      }
    }

    function dlReset() {
      ensureAudioContext();
      if (dlState.isPlaying) dlTogglePlay();
      dlState.stepIdx = 0;
      dlState.lastSoundStep = -1;
      const playBtn = document.getElementById('btn-dl-play');
      if (playBtn) {
        playBtn.innerText = '▶ Start Demo';
        playBtn.className = 'btn btn-sm btn-green';
      }
      renderDeadlockView();
    }

    function setDlSpeed(ms, label) {
      dlState.playInterval = ms;
      ['05', '1', '2', '4'].forEach(l => {
        const b = document.getElementById('btn-dlspd-' + l);
        if (b) b.className = 'btn btn-sm' + (l === label ? ' btn-cyan' : '');
      });
      if (dlState.isPlaying) {
        clearInterval(dlState.timer);
        dlState.timer = setInterval(() => { dlStep(1); }, dlState.playInterval);
      }
    }

    function renderDeadlockView() {
      const sc = DL_SCENARIOS[dlState.scenarioKey];
      if (!sc) return;
      const s = sc.steps[dlState.stepIdx];
      if (!s) return;

      // 1. Status Badges & Phase
      const statusBadge = document.getElementById('dl-status-badge');
      if (statusBadge) {
        if (s.is_deadlocked) {
          statusBadge.innerText = '⚠ DEADLOCK DETECTED';
          statusBadge.className = 'badge badge-red';
        } else if (s.recovery_active) {
          statusBadge.innerText = '🛡 RECOVERING';
          statusBadge.className = 'badge badge-purple';
        } else if (dlState.stepIdx === sc.steps.length - 1) {
          statusBadge.innerText = '✔ COMPLETED & SAFE';
          statusBadge.className = 'badge badge-green';
        } else {
          statusBadge.innerText = '● System Safe';
          statusBadge.className = 'badge badge-cyan';
        }
      }

      const phaseBadge = document.getElementById('dl-phase-badge');
      if (phaseBadge) {
        phaseBadge.innerText = s.tag;
        if (s.tag === 'DEADLOCK') phaseBadge.className = 'badge badge-red';
        else if (s.tag === 'BLOCKED') phaseBadge.className = 'badge badge-amber';
        else if (s.tag === 'SUCCESS' || s.tag === 'UNBLOCK') phaseBadge.className = 'badge badge-green';
        else if (s.tag === 'RECOVERY') phaseBadge.className = 'badge badge-purple';
        else phaseBadge.className = 'badge badge-gray';
      }

      const stepInd = document.getElementById('dl-step-indicator');
      if (stepInd) stepInd.innerText = `Step ${s.step} / ${sc.steps.length - 1}`;

      const ragType = document.getElementById('dl-rag-type-badge');
      if (ragType) ragType.innerText = sc.name;

      const cycleWarn = document.getElementById('dl-cycle-warning-pill');
      if (cycleWarn) cycleWarn.style.display = s.is_deadlocked ? 'inline-block' : 'none';

      // 2. Render SVG Nodes and Edges
      renderRagGraph(sc, s);

      // 3. Render Diagnostics
      const diagCycle = document.getElementById('diag-cycle-procs');
      if (diagCycle) diagCycle.innerText = s.cycle.length > 0 ? s.cycle.join(' ➔ ') : 'None (No Cycle)';
      const diagVictim = document.getElementById('diag-victim-proc');
      if (diagVictim) diagVictim.innerText = s.victim ? s.victim : (s.is_deadlocked ? 'P2 (Candidate)' : 'None Needed');
      const diagExpl = document.getElementById('diag-explanation-box');
      if (diagExpl) diagExpl.innerText = s.explanation || s.action;

      // 4. Render Event Timeline Feed
      renderEventTimeline(sc, dlState.stepIdx);

      // 5. Render Matrices (Allocation, Max, Need, Available)
      renderMatrices(sc, s);
    }

    function renderRagGraph(sc, s) {
      const nodesG = document.getElementById('rag-nodes-group');
      const edgesG = document.getElementById('rag-edges-group');
      if (!nodesG || !edgesG) return;

      const coords = sc.node_coords || {};

      // Render Edges
      let edgesHtml = '';
      (s.edges || []).forEach(e => {
        const fromCoord = coords[e.from];
        const toCoord = coords[e.to];
        if (!fromCoord || !toCoord) return;

        // Calculate offset line endpoints
        const dx = toCoord.x - fromCoord.x;
        const dy = toCoord.y - fromCoord.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const rFrom = fromCoord.type === 'P' ? 24 : 22;
        const rTo = toCoord.type === 'P' ? 26 : 24;

        const x1 = fromCoord.x + (dx / dist) * rFrom;
        const y1 = fromCoord.y + (dy / dist) * rFrom;
        const x2 = toCoord.x - (dx / dist) * rTo;
        const y2 = toCoord.y - (dy / dist) * rTo;

        if (e.in_cycle) {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#ef4444" stroke-width="3.5" marker-end="url(#arrow-cycle)" class="edge-cycle" />`;
        } else if (e.type === 'alloc') {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#22d3ee" stroke-width="2.5" marker-end="url(#arrow-alloc)" />`;
        } else {
          edgesHtml += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#f59e0b" stroke-width="2.2" stroke-dasharray="5,4" marker-end="url(#arrow-req)" />`;
        }
      });
      edgesG.innerHTML = edgesHtml;

      // Render Nodes
      let nodesHtml = '';
      Object.keys(coords).forEach(id => {
        const n = coords[id];
        if (n.type === 'P') {
          // Process Node: Circle
          const state = (s.states && s.states[id]) || 'READY';
          let strokeCol = '#38bdf8';
          let fillCol = '#0f172a';
          let stateCol = '#64748b';

          if (state === 'RUNNING') { strokeCol = '#22c55e'; stateCol = '#22c55e'; fillCol = '#052e16'; }
          else if (state.includes('BLOCKED')) { strokeCol = '#f59e0b'; stateCol = '#f59e0b'; fillCol = '#241405'; }
          else if (state.includes('DEADLOCKED')) { strokeCol = '#ef4444'; stateCol = '#ef4444'; fillCol = '#2b0707'; }
          else if (state.includes('TERMINATED')) { strokeCol = '#64748b'; stateCol = '#ef4444'; fillCol = '#1e293b'; }
          else if (state.includes('COMPLETED')) { strokeCol = '#38bdf8'; stateCol = '#38bdf8'; fillCol = '#042f2e'; }

          const isDeadlockedNode = state.includes('DEADLOCKED');
          const extraClass = isDeadlockedNode ? 'node-deadlocked' : '';

          nodesHtml += `
            <g class="${extraClass}">
              <circle cx="${n.x}" cy="${n.y}" r="24" fill="${fillCol}" stroke="${strokeCol}" stroke-width="${isDeadlockedNode ? 3.5 : 2.5}" />
              <text x="${n.x}" y="${n.y + 4}" text-anchor="middle" fill="#ffffff" font-weight="900" font-size="12" font-family="monospace">${n.label}</text>
              <rect x="${n.x - 32}" y="${n.y + 28}" width="64" height="15" rx="3" fill="#090d16" stroke="${strokeCol}" stroke-width="1" />
              <text x="${n.x}" y="${n.y + 39}" text-anchor="middle" fill="${stateCol}" font-weight="bold" font-size="8">${state.split(' ')[0]}</text>
            </g>
          `;
        } else {
          // Resource Node: Rectangle
          const resObj = (sc.resources || []).find(r => r.id === id) || { total: 1 };
          const resIdx = (sc.resources || []).findIndex(r => r.id === id);
          const availCount = (s.available && resIdx !== -1) ? s.available[resIdx] : 0;
          const isFree = availCount > 0;
          const isCycleRes = s.cycle && s.cycle.includes(id);

          const borderCol = isCycleRes ? '#ef4444' : (isFree ? '#818cf8' : '#e0e7ff');
          const bgCol = isCycleRes ? '#2d0606' : '#1e1b4b';

          nodesHtml += `
            <g>
              <rect x="${n.x - 28}" y="${n.y - 18}" width="56" height="36" rx="6" fill="${bgCol}" stroke="${borderCol}" stroke-width="${isCycleRes ? 3 : 2}" />
              <text x="${n.x}" y="${n.y - 2}" text-anchor="middle" fill="#c7d2fe" font-weight="900" font-size="11" font-family="monospace">${n.label}</text>
              <text x="${n.x}" y="${n.y + 11}" text-anchor="middle" fill="${isFree ? '#4ade80' : '#f87171'}" font-weight="bold" font-size="8.5">${availCount}/${resObj.total} free</text>
            </g>
          `;
        }
      });
      nodesG.innerHTML = nodesHtml;
    }

    function renderEventTimeline(sc, curStepIdx) {
      const feed = document.getElementById('dl-event-feed');
      const countEl = document.getElementById('dl-timeline-count');
      if (!feed) return;

      const stepsSoFar = sc.steps.slice(0, curStepIdx + 1);
      if (countEl) countEl.innerText = `${stepsSoFar.length} / ${sc.steps.length} steps`;

      feed.innerHTML = stepsSoFar.map((st, idx) => {
        const isCurrent = idx === curStepIdx;
        let badgeCol = '#64748b';
        if (st.tag === 'ACQUIRE') badgeCol = '#22d3ee';
        else if (st.tag === 'BLOCKED') badgeCol = '#f59e0b';
        else if (st.tag === 'DEADLOCK') badgeCol = '#ef4444';
        else if (st.tag === 'RECOVERY') badgeCol = '#a855f7';
        else if (st.tag === 'UNBLOCK') badgeCol = '#22c55e';
        else if (st.tag === 'RELEASE') badgeCol = '#38bdf8';
        else if (st.tag === 'SUCCESS') badgeCol = '#4ade80';

        return `
          <div style="background:${isCurrent ? '#17253d' : '#0b1120'}; border:1px solid ${isCurrent ? 'var(--accent-cyan)' : 'var(--border)'}; border-radius:4px; padding:6px 8px; font-size:0.71rem; transition:all 0.15s ease;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
              <span style="font-weight:bold; color:#fff; font-family:var(--font-mono);">${st.title}</span>
              <span class="badge" style="background:${badgeCol}22; color:${badgeCol}; border-color:${badgeCol}; font-size:0.62rem; padding:1px 4px;">${st.tag}</span>
            </div>
            <div style="color:var(--text-muted); font-size:0.68rem; line-height:1.3;">${st.action}</div>
          </div>
        `;
      }).join('');

      // Auto-scroll to bottom
      feed.scrollTop = feed.scrollHeight;
    }

    function renderMatrices(sc, s) {
      // 1. Allocation Matrix
      const tAlloc = document.getElementById('mat-table-alloc');
      if (tAlloc) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (s.allocation && s.allocation[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); font-weight:${val>0?'bold':'normal'}; color:${val>0?'#22d3ee':'#64748b'};">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tAlloc.innerHTML = th + tb;
      }

      // 2. Maximum Claim Matrix
      const tMax = document.getElementById('mat-table-max');
      if (tMax) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (sc.max_matrix && sc.max_matrix[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); color:#c7d2fe;">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tMax.innerHTML = th + tb;
      }

      // 3. Need Matrix
      const tNeed = document.getElementById('mat-table-need');
      if (tNeed) {
        let th = '<thead><tr><th>Proc</th>' + sc.resources.map(r => `<th>${r.id}</th>`).join('') + '</tr></thead>';
        let tb = '<tbody>' + sc.procs.map((p, pIdx) => {
          const row = (s.need && s.need[pIdx]) || sc.resources.map(() => 0);
          return `<tr><td><b>${p}</b></td>` + row.map(val => `<td style="font-family:var(--font-mono); font-weight:${val>0?'bold':'normal'}; color:${val>0?'#f59e0b':'#64748b'};">${val}</td>`).join('') + '</tr>';
        }).join('') + '</tbody>';
        tNeed.innerHTML = th + tb;
      }

      // 4. Available Vector
      const vAvail = document.getElementById('mat-vector-available');
      if (vAvail) {
        vAvail.innerHTML = sc.resources.map((r, rIdx) => {
          const count = (s.available && s.available[rIdx] !== undefined) ? s.available[rIdx] : 0;
          return `
            <div style="display:flex; justify-content:space-between; align-items:center; background:#020617; padding:3px 6px; border-radius:3px; border:1px solid var(--border);">
              <span style="font-family:var(--font-mono); font-weight:bold; color:#fff;">${r.name}:</span>
              <span class="badge ${count > 0 ? 'badge-green' : 'badge-red'}" style="font-family:var(--font-mono); font-weight:900;">${count} Free</span>
            </div>
          `;
        }).join('');
      }

      // Safe state pill & safe sequence
      const seqStr = document.getElementById('mat-safe-seq-str');
      if (seqStr) seqStr.innerText = s.safe_seq || 'None';

      const safePill = document.getElementById('mat-safe-pill');
      if (safePill) {
        if (s.is_deadlocked) {
          safePill.innerText = 'DEADLOCKED (CYCLE)';
          safePill.className = 'badge badge-red';
        } else if (s.safe_seq && s.safe_seq.includes('Unsafe')) {
          safePill.innerText = 'UNSAFE STATE';
          safePill.className = 'badge badge-amber';
        } else {
          safePill.innerText = 'SAFE STATE';
          safePill.className = 'badge badge-green';
        }
      }
    }

    // Backend Polling Hook (Compatible with external telemetry)
    function renderDeadlock(backendData) {
      // If user is not currently running an interactive simulation, keep view fresh
      if (!dlState.isPlaying && dlState.stepIdx === 0) {
        renderDeadlockView();
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
  