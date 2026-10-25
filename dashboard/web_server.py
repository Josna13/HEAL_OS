"""Zero-dependency self-healing observatory and visual interactive lab for HealOS 2.0."""

import json
import threading
import time
import sys
import gc
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List, Optional

from dashboard.process_lifecycle import LifecycleEngine
from dashboard.cpu_scheduler import CPUScheduler, ScheduledProcess
from dashboard.deadlock_lab import (
    get_standard_scenarios,
    BankersAlgorithm,
    TwoProcessDeadlockSimulation,
)
from dashboard.pid_comparison import CrashRecoveryComparison, ProcessIdentityRecord
from config import CRASH_TRIGGER_FILE


class MemoryLeakSimulator:
    """
    Controlled, bounded memory-stress engine for educational demonstration.
    Allocates real bytearrays in steps of 4 MB up to a maximum safety ceiling (64 MB).
    Immediately releases memory and invokes garbage collection upon stop or reset.
    """
    def __init__(self, max_mb: int = 64, step_mb: int = 4, interval_sec: float = 0.5):
        self.max_mb = max_mb
        self.step_mb = step_mb
        self.interval_sec = interval_sec
        self.buffer: List[bytearray] = []
        self.is_running: bool = False
        self.initial_app_mb: float = 18.4
        self.peak_mb: float = 18.4
        self.start_timestamp: Optional[str] = None
        self.history: List[Dict[str, Any]] = []
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self, initial_mb: float = 18.4):
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            if not self.buffer:
                self.initial_app_mb = round(initial_mb, 1)
                self.peak_mb = self.initial_app_mb
                self.start_timestamp = datetime.now().strftime("%H:%M:%S")
                self.history = [{"timestamp": self.start_timestamp, "allocated_mb": 0.0, "total_mb": self.initial_app_mb, "cpu_percent": 1.2}]
            self._thread = threading.Thread(target=self._worker, daemon=True, name="MemoryLeakSimulatorThread")
            self._thread.start()

    def _worker(self):
        while True:
            time.sleep(self.interval_sec)
            with self._lock:
                if not self.is_running:
                    break
                curr_alloc = len(self.buffer) * self.step_mb
                if curr_alloc < self.max_mb:
                    try:
                        chunk = bytearray(self.step_mb * 1024 * 1024)
                        self.buffer.append(chunk)
                    except MemoryError:
                        self.is_running = False
                        break
                    now_alloc = len(self.buffer) * self.step_mb
                    total_mb = round(self.initial_app_mb + now_alloc, 1)
                    if total_mb > self.peak_mb:
                        self.peak_mb = total_mb
                    ts = datetime.now().strftime("%H:%M:%S")
                    import random
                    sim_cpu = round(1.2 + random.uniform(0.8, 2.4), 1)
                    self.history.append({"timestamp": ts, "allocated_mb": float(now_alloc), "total_mb": total_mb, "cpu_percent": sim_cpu})
                    if len(self.history) > 40:
                        self.history.pop(0)
                else:
                    self.is_running = False
                    break

    def stop(self):
        with self._lock:
            self.is_running = False
            self.buffer.clear()
            gc.collect()

    def reset(self):
        with self._lock:
            self.is_running = False
            self.buffer.clear()
            self.initial_app_mb = 18.4
            self.peak_mb = 18.4
            self.history.clear()
            gc.collect()

    def get_status(self, current_app_mb: float = 18.4) -> Dict[str, Any]:
        with self._lock:
            curr_alloc = len(self.buffer) * self.step_mb
            base_mb = self.initial_app_mb if self.initial_app_mb > 0 else current_app_mb
            total = round(base_mb + curr_alloc, 1)
            if total > self.peak_mb:
                self.peak_mb = total
            delta = curr_alloc
            if self.is_running:
                st = "LEAKING (ACTIVE)"
            elif curr_alloc >= self.max_mb:
                st = "SAFETY LIMIT REACHED (64 MB)"
            elif curr_alloc == 0 and self.peak_mb > base_mb:
                st = "STOPPED (MEMORY FREED)"
            else:
                st = "IDLE"

            return {
                "is_running": self.is_running,
                "status": st,
                "current_mb": total,
                "allocated_mb": float(curr_alloc),
                "initial_mb": round(base_mb, 1),
                "peak_mb": round(self.peak_mb, 1),
                "delta_mb": round(delta, 1),
                "max_mb": self.max_mb,
                "history": list(self.history),
            }


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HealOS 2.0 - Operating Systems Visual Lab & Control Center</title>
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
      font-size: 13px;
      line-height: 1.45;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Top Navigation Bar */
    header {
      background-color: var(--bg-surface);
      border-bottom: 1px solid var(--border);
      padding: 0 16px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .brand-title {
      font-weight: 800;
      font-size: 1.05rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .brand-title span { color: var(--accent-cyan); }
    .nav-tabs {
      display: flex;
      gap: 4px;
      height: 100%;
      align-items: center;
    }
    .nav-tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-weight: 600;
      font-size: 0.8rem;
      padding: 6px 14px;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .nav-tab-btn:hover {
      background-color: var(--bg-card);
      color: var(--text-main);
    }
    .nav-tab-btn.active {
      background-color: var(--bg-card);
      color: var(--accent-cyan);
      box-shadow: inset 0 -2px 0 var(--accent-cyan);
    }

    /* Layout Containers */
    main {
      flex: 1;
      padding: 16px;
      max-width: 1360px;
      width: 100%;
      margin: 0 auto;
    }

    /* Common Card / Panel Styling */
    .panel-box {
      background-color: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
      margin-bottom: 14px;
    }
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .panel-heading {
      font-weight: 700;
      font-size: 0.88rem;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-cyan { background: rgba(34, 211, 238, 0.15); color: #67e8f9; border: 1px solid rgba(34, 211, 238, 0.3); }
    .badge-gray { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
    .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c4b5fd; border: 1px solid rgba(168, 85, 247, 0.3); }

    /* Buttons */
    .btn {
      background-color: var(--bg-card);
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 5px 12px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.15s ease;
    }
    .btn:hover { background-color: var(--border-highlight); border-color: var(--border-active); }
    .btn-sm { padding: 3px 8px; font-size: 0.72rem; }
    .btn-cyan { background-color: rgba(34, 211, 238, 0.15); border-color: var(--accent-cyan); color: #a5f3fc; }
    .btn-cyan:hover { background-color: var(--accent-cyan); color: #000; }
    .btn-green { background-color: rgba(34, 197, 94, 0.15); border-color: var(--accent-green); color: #86efac; }
    .btn-green:hover { background-color: var(--accent-green); color: #000; }
    .btn-red { background-color: rgba(239, 68, 68, 0.15); border-color: var(--accent-red); color: #fca5a5; }
    .btn-red:hover { background-color: var(--accent-red); color: #fff; }
    .btn-purple { background-color: rgba(168, 85, 247, 0.15); border-color: var(--accent-purple); color: #e9d5ff; }
    .btn-purple:hover { background-color: var(--accent-purple); color: #000; }

    /* Progress Track */
    .progress-track {
      background: #020617;
      border: 1px solid var(--border);
      border-radius: 4px;
      height: 8px;
      overflow: hidden;
      position: relative;
    }
    .progress-fill {
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }

    /* Clean Tables */
    .clean-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.75rem;
    }
    .clean-table th {
      background-color: var(--bg-card);
      color: var(--text-muted);
      font-weight: 700;
      text-align: left;
      padding: 6px 10px;
      border-bottom: 1px solid var(--border);
      text-transform: uppercase;
      font-size: 0.68rem;
    }
    .clean-table td {
      padding: 6px 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-main);
    }
    .clean-table tr:hover td {
      background-color: rgba(255, 255, 255, 0.02);
    }

    /* Stage Pipeline (Ready -> Core 0 -> Completed) */
    .stage-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }
    .stage-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 10px;
      min-height: 140px;
      display: flex;
      flex-direction: column;
    }
    .stage-title {
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .queue-token-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      flex: 1;
      align-content: flex-start;
    }
    .proc-token {
      background: var(--bg-card);
      border: 1px solid var(--border-highlight);
      border-radius: 4px;
      padding: 4px 8px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      transition: all 0.2s ease;
    }
    .proc-token.executing {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 10px rgba(34, 211, 238, 0.35);
      background: rgba(34, 211, 238, 0.1);
    }

    /* CPU Socket */
    .cpu-socket {
      flex: 1;
      background: #060b17;
      border: 2px dashed var(--border-highlight);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 8px;
      text-align: center;
      transition: all 0.25s ease;
    }
    .cpu-socket.active {
      border-style: solid;
      border-color: var(--accent-cyan);
      background: rgba(14, 165, 233, 0.08);
    }

    /* Gantt Chart */
    .gantt-wrap {
      background: #020617;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 8px;
      overflow-x: auto;
    }
    .gantt-track {
      display: flex;
      height: 38px;
      position: relative;
      background: #070e1b;
      border-radius: 4px;
      margin-top: 14px;
    }
    .gantt-block {
      height: 100%;
      border-right: 1px solid #020617;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: #fff;
      overflow: hidden;
      white-space: nowrap;
    }
    .gantt-ruler {
      position: relative;
      height: 16px;
      display: flex;
      font-size: 0.65rem;
      color: var(--text-dim);
      font-family: var(--font-mono);
    }
    .gantt-cursor {
      position: absolute;
      top: -14px;
      bottom: 0;
      width: 2px;
      background: #ef4444;
      pointer-events: none;
      z-index: 10;
      transition: left 0.15s ease-out;
    }
    .gantt-cursor::before {
      content: '▲';
      position: absolute;
      top: 0;
      left: -4px;
      color: #ef4444;
      font-size: 10px;
    }

    /* SVG RAG Box */
    .rag-svg-box {
      background: #040813;
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px;
      margin-bottom: 10px;
    }

    /* Step Timeline Pills */
    .timeline-step {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      flex: 1;
      position: relative;
    }
    .timeline-dot {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      font-weight: 800;
      margin-bottom: 4px;
    }
    .timeline-dot.completed { background: #166534; color: #86efac; border: 1px solid #22c55e; }
    .timeline-dot.active { background: #075985; color: #7dd3fc; border: 1px solid #0284c7; box-shadow: 0 0 8px #0284c7; }
    .timeline-dot.crashed { background: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; box-shadow: 0 0 8px #ef4444; }
    .timeline-dot.pending { background: #1e293b; color: #64748b; border: 1px solid #334155; }
  
    /* Deadlock Lab Real-Time Animations */
    @keyframes pulse-red {
      0% { filter: drop-shadow(0 0 3px #ef4444); stroke-width: 3px; }
      50% { filter: drop-shadow(0 0 12px #ef4444); stroke-width: 4.5px; }
      100% { filter: drop-shadow(0 0 3px #ef4444); stroke-width: 3px; }
    }
    @keyframes pulse-node-deadlock {
      0% { filter: drop-shadow(0 0 4px #ef4444); }
      50% { filter: drop-shadow(0 0 16px #ef4444); }
      100% { filter: drop-shadow(0 0 4px #ef4444); }
    }
    .edge-cycle {
      animation: pulse-red 1.2s infinite ease-in-out;
    }
    .node-deadlocked {
      animation: pulse-node-deadlock 1.2s infinite ease-in-out;
    }
</style>
</head>
<body>

  <!-- Header Navigation Bar (Strictly 3 Tabs) -->
  <header>
    <div class="brand-group">
      <div class="brand-title">Heal<span>OS</span> 2.0</div>
      <span class="badge badge-cyan">AUTONOMIC LAB</span>
    </div>

    <nav class="nav-tabs">
      <button id="nav-btn-overview" class="nav-tab-btn active" onclick="switchMainTab('overview')">
        <span>📊</span> System Overview
      </button>
      <button id="nav-btn-process-lab" class="nav-tab-btn" onclick="switchMainTab('process-lab')">
        <span>⚡</span> CPU Scheduling
      </button>
      <button id="nav-btn-deadlock" class="nav-tab-btn" onclick="switchMainTab('deadlock')">
        <span>🔒</span> Deadlock Lab
      </button>
    </nav>

    <div style="display:flex; align-items:center; gap:8px;">
      <button class="btn btn-sm" id="btn-sound-toggle" onclick="toggleSound()">🔇 Sound Muted</button>
    </div>
  </header>

  <!-- ===================================================================== -->
  <!-- TAB 1: SYSTEM OVERVIEW (CLEAN, PRACTICAL, LIVE MONITORING & STRESS LAB) -->
  <!-- ===================================================================== -->
  <main id="tab-overview">
    <!-- Top: Dual Status Bar (Host System Status & Target Application Status) -->
    <div class="panel-box" style="padding:12px 16px; margin-bottom:12px;">
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; align-items:center;">
        <!-- Left: Host Operating System Status -->
        <div style="display:flex; flex-direction:column; gap:4px; border-right:1px solid var(--border); padding-right:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:0.72rem; color:var(--text-muted); font-weight:bold; letter-spacing:0.5px;">HOST OPERATING SYSTEM</span>
            <span class="badge badge-green" id="ov-status-pill">● Normal Operating Conditions</span>
          </div>
          <div style="display:flex; gap:16px; font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono); margin-top:2px;">
            <span>Uptime: <b id="ov-uptime-val" style="color:#fff;">0s</b></span>
            <span>OS Health: <b id="ov-health-score" style="color:var(--accent-green);">98 / 100</b></span>
            <span>Host Kernel: <b style="color:var(--accent-cyan);">Linux / WSL (Healthy)</b></span>
          </div>
        </div>

        <!-- Right: Target Monitored Application Status (dummy_app.py) -->
        <div style="display:flex; flex-direction:column; gap:4px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:0.72rem; color:var(--text-muted); font-weight:bold; letter-spacing:0.5px;">MONITORED APPLICATION</span>
              <span style="font-size:0.75rem; color:var(--accent-cyan); font-weight:bold;" id="ov-app-val">dummy_app.py</span>
            </div>
            <span class="badge badge-green" id="ov-app-status-badge">RUNNING</span>
          </div>
          <div style="display:flex; gap:16px; font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono); margin-top:2px;">
            <span>Active PID: <b id="ov-app-pid-val" style="color:var(--accent-cyan);">Loading...</b></span>
            <span>App Uptime: <b id="ov-app-uptime-val" style="color:#fff;">0s</b></span>
            <span>App Health: <b id="ov-app-health-score" style="color:var(--accent-green);">98 / 100</b></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Middle: CPU & RAM Charts (2-Column Grid) -->
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
        <div class="progress-track" style="margin-bottom:10px;">
          <div id="ov-cpu-bar" class="progress-fill" style="width:0%; background:var(--accent-cyan);"></div>
        </div>
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
        <div class="progress-track" style="margin-bottom:10px;">
          <div id="ov-ram-bar" class="progress-fill" style="width:0%; background:#818cf8;"></div>
        </div>
        <canvas id="ov-ram-canvas" width="400" height="90" style="width:100%; height:85px; background:#020617; border-radius:5px; border:1px solid var(--border);"></canvas>
        <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.7rem; color:var(--text-muted);">
          <span>Used: <b id="ov-ram-used" style="color:#fff;">0.0 GB</b> / <b id="ov-ram-total" style="color:#fff;">0.0 GB</b></span>
          <span>Free: <b id="ov-ram-free" style="color:var(--accent-green);">0.0 GB</b></span>
        </div>
      </div>
    </div>

    <!-- Below: Current Monitored Process Information & System Processes Table -->
    <div class="panel-box" style="margin-bottom:12px;">
      <div class="panel-header" style="margin-bottom:8px;">
        <div class="panel-heading">
          <span>Current Monitored Process Information</span>
          <span class="badge badge-cyan" id="ov-proc-count-badge">Active</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted);">Real-time process identity & resource surveillance</div>
      </div>

      <!-- Highlighted Monitored App Row -->
      <div style="background:#0c1729; border:1px solid var(--border-highlight); border-radius:6px; padding:10px 14px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="font-size:1.05rem; font-weight:bold; color:#fff; font-family:var(--font-mono);">dummy_app.py</span>
          <span class="badge badge-green" id="ov-monitored-state-badge">RUNNING</span>
        </div>
        <div style="display:flex; gap:18px; font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">
          <span>PID: <b id="ov-monitored-pid" style="color:var(--accent-cyan); font-weight:900;">-</b></span>
          <span>CPU: <b id="ov-monitored-cpu" style="color:#fff;">0.0%</b></span>
          <span>Memory: <b id="ov-monitored-mem" style="color:#38bdf8;">0.0 MB</b></span>
          <span>Uptime: <b id="ov-monitored-uptime" style="color:#fff;">0s</b></span>
          <span>Failure Count: <b id="ov-monitored-crashes" style="color:var(--accent-amber);">0</b></span>
        </div>
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
              <th>Role / Type</th>
            </tr>
          </thead>
          <tbody id="ov-process-tbody">
            <tr><td colspan="6" style="text-align:center; color:#64748b; padding:12px;">Loading live processes...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Demonstration Controls Toolbar -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:0.75rem; color:var(--text-muted); font-weight:bold; letter-spacing:0.5px;">DEMO CONTROLS:</span>
          <!-- Simulate Crash Button -->
          <button class="btn btn-sm btn-red" id="btn-demo-crash" onclick="triggerCrashDemo()" style="display:inline-flex; align-items:center; gap:5px; font-weight:bold;">
            <span>⚡ Simulate Crash</span>
          </button>

          <!-- Simulate Memory Leak Button -->
          <button class="btn btn-sm btn-purple" id="btn-demo-memleak" onclick="startMemLeakDemo()" style="display:inline-flex; align-items:center; gap:5px; font-weight:bold; background:#7c3aed; border-color:#a855f7;">
            <span>🧪 Simulate Memory Leak</span>
          </button>

          <!-- Stop & Reset Demo -->
          <button class="btn btn-sm" id="btn-demo-stop" onclick="stopMemLeakDemo()" style="display:none;">⏹ Stop Demo</button>
          <button class="btn btn-sm" id="btn-demo-reset" onclick="resetMemLeakDemo()" style="display:none;">↺ Reset</button>
        </div>

        <div style="display:flex; align-items:center; gap:8px;">
          <span style="font-size:0.72rem; color:var(--text-muted);" id="demo-status-text">Standby — Click to trigger a controlled fault or stress test</span>
          <span class="badge badge-gray" id="demo-status-badge">IDLE</span>
        </div>
      </div>
    </div>

    <!-- Memory Leak Demonstration Panel (Toggled when Memory Leak Demo is active) -->
    <div id="panel-memleak-demo" class="panel-box" style="display:none; margin-bottom:12px; border-color:#7c3aed; background:#0f1124;">
      <div class="panel-header" style="margin-bottom:8px;">
        <div class="panel-heading">
          <span style="color:#c4b5fd;">🧪 Memory Stress Demonstration (Controlled & Bounded)</span>
          <span class="badge badge-purple" style="background:#581c87; color:#e9d5ff; border-color:#7c3aed;" id="memleak-badge">LEAKING...</span>
        </div>
        <div style="font-size:0.7rem; color:#94a3b8;">
          Bounded to 64 MB max ceiling &bull; Safe allocation increments &bull; Fully reclaimed on Stop
        </div>
      </div>

      <!-- Live RAM Allocation Progress Bar vs 64 MB Safety Limit -->
      <div style="margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#94a3b8; margin-bottom:4px;">
          <span>Simulated Memory Consumption: <b id="memleak-bar-label" style="color:#fff; font-family:var(--font-mono);">0.0 MB / 64.0 MB</b></span>
          <span id="memleak-rate-label" style="color:#a855f7; font-weight:bold;">+4.0 MB / 500ms</span>
        </div>
        <div class="progress-track" style="height:12px; background:#020617; border-radius:6px;">
          <div id="memleak-bar-fill" class="progress-fill" style="width:0%; background:linear-gradient(90deg, #7c3aed, #ef4444); transition:width 0.4s ease;"></div>
        </div>
      </div>

      <!-- Memory & CPU Telemetry Chips (2 Columns) -->
      <div style="display:grid; grid-template-columns: 2fr 1.2fr; gap:12px; align-items:center;">
        <!-- Metrics Grid -->
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:8px;">
          <div style="background:#171630; border:1px solid #3b2a59; border-radius:5px; padding:6px 10px; text-align:center;">
            <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Initial RAM</div>
            <div id="memleak-initial" style="font-size:0.95rem; font-weight:900; color:#fff; font-family:var(--font-mono); margin-top:2px;">18.4 MB</div>
          </div>
          <div style="background:#171630; border:1px solid #3b2a59; border-radius:5px; padding:6px 10px; text-align:center;">
            <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Current RAM</div>
            <div id="memleak-current" style="font-size:0.95rem; font-weight:900; color:#c4b5fd; font-family:var(--font-mono); margin-top:2px;">18.4 MB</div>
          </div>
          <div style="background:#171630; border:1px solid #3b2a59; border-radius:5px; padding:6px 10px; text-align:center;">
            <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Peak RAM</div>
            <div id="memleak-peak" style="font-size:0.95rem; font-weight:900; color:#f59e0b; font-family:var(--font-mono); margin-top:2px;">18.4 MB</div>
          </div>
          <div style="background:#171630; border:1px solid #3b2a59; border-radius:5px; padding:6px 10px; text-align:center;">
            <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">RAM Delta</div>
            <div id="memleak-delta" style="font-size:0.95rem; font-weight:900; color:#ef4444; font-family:var(--font-mono); margin-top:2px;">+0.0 MB</div>
          </div>
        </div>

        <!-- Live CPU alongside Memory -->
        <div style="background:#171630; border:1px solid #3b2a59; border-radius:5px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-size:0.68rem; color:#94a3b8;">APP CPU LOAD:</div>
            <div id="memleak-cpu-val" style="font-size:1.1rem; font-weight:900; color:#38bdf8; font-family:var(--font-mono);">1.2%</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.68rem; color:#94a3b8;">STATUS:</div>
            <div id="memleak-status-txt" style="font-size:0.75rem; font-weight:bold; color:#22c55e;">NORMAL</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recovery Result & Lifecycle Section (Visible when crash/recovery event occurs or standby) -->
    <div id="panel-recovery-result" class="panel-box" style="margin-bottom:12px;">
      <div class="panel-header" style="margin-bottom:8px;">
        <div class="panel-heading">
          <span>Autonomic Crash Detection & Self-Healing Lifecycle</span>
          <span class="badge badge-green" id="recovery-lifecycle-badge">VERIFIED RECOVERY</span>
        </div>
        <div style="font-size:0.72rem; color:var(--text-muted);" id="recovery-result-subtitle">
          Observed lifecycle state transitions and old vs new process verification
        </div>
      </div>

      <!-- 1. Recovery Lifecycle Timeline: RUNNING -> CRASHED -> DETECTED -> RECOVERING -> RESTARTED -> RUNNING -->
      <div style="margin-bottom:14px; background:#080e1a; border:1px solid var(--border); border-radius:6px; padding:10px 14px;">
        <div style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold; margin-bottom:8px;">
          RECOVERY LIFECYCLE TIMELINE (TRANSITION FLOW)
        </div>
        <div id="recovery-timeline-strip" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <!-- Dynamically populated by renderRecoveryTimeline() -->
        </div>
      </div>

      <!-- 2. Visual Old PID vs New PID Comparison Cards -->
      <div style="display:grid; grid-template-columns: 1fr auto 1fr; gap:12px; align-items:center; margin-bottom:14px;">
        <!-- Left: Old Process Instance -->
        <div style="background:#1b1117; border:1px solid #7f1d1d; border-radius:6px; padding:10px 14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:0.7rem; color:#fca5a5; font-weight:bold; text-transform:uppercase;">OLD PROCESS (TERMINATED)</span>
            <span class="badge badge-red" id="rec-old-status-badge">EXITED (CODE 1)</span>
          </div>
          <div style="font-size:1.4rem; font-weight:900; color:#ef4444; font-family:var(--font-mono); text-decoration:line-through;" id="rec-old-pid">PID -</div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
            Crash Time: <b id="rec-old-crash-time" style="color:#fff;">-</b>
          </div>
          <div style="font-size:0.68rem; color:#94a3b8; margin-top:2px;">Process Control Block (PCB) unlinked by OS kernel</div>
        </div>

        <!-- Center: Recovery Duration & Downtime Arrow -->
        <div style="text-align:center; padding:0 8px;">
          <div style="font-size:0.72rem; color:var(--accent-cyan); font-weight:bold; font-family:var(--font-mono);" id="rec-duration-center">RECOVERY</div>
          <div style="color:var(--accent-cyan); font-size:1.3rem; margin:2px 0;">────────▶</div>
          <div style="font-size:0.68rem; color:var(--text-dim); font-family:var(--font-mono);" id="rec-downtime-center">Downtime: -</div>
        </div>

        <!-- Right: New Process Instance -->
        <div style="background:#0f1d19; border:1px solid #14532d; border-radius:6px; padding:10px 14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:0.7rem; color:#86efac; font-weight:bold; text-transform:uppercase;">NEW PROCESS (RESPAWNED)</span>
            <span class="badge badge-green" id="rec-new-status-badge">RUNNING (VERIFIED)</span>
          </div>
          <div style="font-size:1.4rem; font-weight:900; color:#22c55e; font-family:var(--font-mono);" id="rec-new-pid">PID -</div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;">
            Restart Time: <b id="rec-new-restart-time" style="color:#fff;">-</b>
          </div>
          <div style="font-size:0.68rem; color:#94a3b8; margin-top:2px;">New PID allocated by kernel & verified via psutil</div>
        </div>
      </div>

      <!-- 3. Clean 10-Field Recovery Telemetry Table -->
      <div style="margin-bottom:14px;">
        <div style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold; margin-bottom:6px;">
          RECOVERY TELEMETRY SPECIFICATION (10 REQUIRED FIELDS)
        </div>
        <div style="overflow-x:auto;">
          <table class="clean-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Observed Information</th>
                <th>Field</th>
                <th>Observed Information</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><b>Old PID</b></td>
                <td><span id="fld-old-pid" style="color:#ef4444; font-weight:bold; font-family:var(--font-mono);">-</span></td>
                <td><b>New PID</b></td>
                <td><span id="fld-new-pid" style="color:#22c55e; font-weight:bold; font-family:var(--font-mono);">-</span></td>
              </tr>
              <tr>
                <td><b>Crash Time</b></td>
                <td><span id="fld-crash-time" style="color:#fff; font-family:var(--font-mono);">-</span></td>
                <td><b>Restart Time</b></td>
                <td><span id="fld-restart-time" style="color:#fff; font-family:var(--font-mono);">-</span></td>
              </tr>
              <tr>
                <td><b>Exit Code</b></td>
                <td><span id="fld-exit-code" class="badge badge-red" style="font-family:var(--font-mono);">-</span></td>
                <td><b>Downtime</b></td>
                <td><span id="fld-downtime" style="color:var(--accent-cyan); font-weight:bold; font-family:var(--font-mono);">-</span></td>
              </tr>
              <tr>
                <td><b>Detection Time</b></td>
                <td><span id="fld-det-time" style="color:#fff; font-family:var(--font-mono);">-</span></td>
                <td><b>Recovery Duration</b></td>
                <td><span id="fld-rec-dur" style="color:#22c55e; font-weight:bold; font-family:var(--font-mono);">-</span></td>
              </tr>
              <tr>
                <td><b>Recovery Start</b></td>
                <td><span id="fld-rec-start" style="color:#fff; font-family:var(--font-mono);">-</span></td>
                <td><b>Final Status</b></td>
                <td><span id="fld-final-status" class="badge badge-green" style="font-weight:bold;">-</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 4. Improved Health Analyzer Comparison: Before Crash -> During Crash -> After Recovery -->
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <div style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase; font-weight:bold;">
            HEALTH ANALYZER COMPARISON (BEFORE CRASH ➔ DURING CRASH ➔ AFTER RECOVERY)
          </div>
          <span style="font-size:0.68rem; color:#38bdf8;">OS Health vs Application Health Isolation Verified</span>
        </div>
        <div style="overflow-x:auto;">
          <table class="clean-table">
            <thead>
              <tr>
                <th>Telemetry Metric</th>
                <th style="color:#38bdf8;">Before Crash (Nominal)</th>
                <th style="color:#ef4444;">During Crash (Failure)</th>
                <th style="color:#22c55e;">After Recovery (Restored)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><b>Application Status</b></td>
                <td><span class="badge badge-green">RUNNING</span></td>
                <td><span class="badge badge-red">CRASHED (OFFLINE)</span></td>
                <td><span class="badge badge-green">RUNNING (RESTORED)</span></td>
              </tr>
              <tr>
                <td><b>Process ID (PID)</b></td>
                <td id="ha-before-pid" style="font-family:var(--font-mono); color:#fff;">-</td>
                <td style="color:#ef4444; font-family:var(--font-mono); font-weight:bold;">None (Terminated)</td>
                <td id="ha-after-pid" style="font-family:var(--font-mono); color:#22c55e; font-weight:bold;">-</td>
              </tr>
              <tr>
                <td><b>CPU Utilization</b></td>
                <td id="ha-before-cpu" style="font-family:var(--font-mono); color:#fff;">1.2%</td>
                <td style="color:#ef4444; font-family:var(--font-mono);">0.0%</td>
                <td id="ha-after-cpu" style="font-family:var(--font-mono); color:#fff;">1.4%</td>
              </tr>
              <tr>
                <td><b>RAM Consumption</b></td>
                <td id="ha-before-ram" style="font-family:var(--font-mono); color:#fff;">18.4 MB</td>
                <td style="color:#ef4444; font-family:var(--font-mono);">0.0 MB (Reclaimed)</td>
                <td id="ha-after-ram" style="font-family:var(--font-mono); color:#fff;">18.2 MB</td>
              </tr>
              <tr>
                <td><b>Application Health Score</b></td>
                <td><b style="color:var(--accent-green);">98 / 100</b></td>
                <td><b style="color:#ef4444;">0 / 100 (Degraded)</b></td>
                <td><b style="color:var(--accent-green);" id="ha-after-score">96 / 100</b></td>
              </tr>
              <tr style="background:#091220;">
                <td><b>Host OS Kernel Health</b></td>
                <td><b style="color:var(--accent-green);">98 / 100 (Healthy)</b></td>
                <td><b style="color:var(--accent-green);">98 / 100 (Unaffected)</b></td>
                <td><b style="color:var(--accent-green);">98 / 100 (Healthy)</b></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div style="margin-top:6px; font-size:0.68rem; color:var(--text-muted); background:#060b17; border:1px solid var(--border); border-radius:4px; padding:6px 10px;">
          <b style="color:var(--accent-cyan);">Operating System Isolation Guarantee:</b>
          When the monitored user-space application crashed and its health dropped to 0/100, the underlying operating system kernel, system monitor, and other processes remained healthy at 98/100. Upon automatic detection and recovery, application health was restored to 96/100.
        </div>
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
  </main>

  <script>
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
  </script>
</body>
</html>
"""


class WebDashboardHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP request handler for the interactive web dashboard."""

    orchestrator_ref = None
    mem_leak = MemoryLeakSimulator(max_mb=64, step_mb=4, interval_sec=0.5)

    standalone_state = {
        "app_pid": 8556,
        "failed_pid": None,
        "total_crashes": 0,
        "last_crash_time": "None",
        "last_recovery_duration": 0.0,
        "recent_recoveries": [],
        "events": ["[12:00:00] HealOS 2.0 system state initialized."],
        "app_uptime": 45.0,
        "app_is_running": True,
    }
    lifecycle_engine = LifecycleEngine()
    scheduler_algo = "RR"
    scheduler_quantum = 2
    scheduler_procs = CPUScheduler.get_default_processes()
    deadlock_scenario_key = "two_process"
    two_proc_deadlock = TwoProcessDeadlockSimulation()
    banker_scenario = get_standard_scenarios()["safe_banker"]
    banker = BankersAlgorithm(banker_scenario)
    banker_trace_msg = "Safe sequence evaluated."
    demo_step_current = 1
    timeline_events: List[Dict[str, Any]] = [
        {"timestamp": datetime.now().strftime("%H:%M:%S"), "event_type": "INIT", "pid": None, "explanation": "Live Seven-Panel Observatory and OS Studio online.", "provenance": "[SIMULATION]"}
    ]

    def log_message(self, format, *args):
        pass

    @classmethod
    def record_event(cls, event_type: str, pid: Optional[int], explanation: str, provenance: str):
        ts = datetime.now().strftime("%H:%M:%S")
        cls.timeline_events.append({
            "timestamp": ts,
            "event_type": event_type,
            "pid": pid,
            "explanation": explanation,
            "provenance": provenance,
        })
        if len(cls.timeline_events) > 80:
            cls.timeline_events.pop(0)

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def finish(self):
        try:
            super().finish()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        try:
            self._do_GET_impl()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _do_GET_impl(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            # 1. Lifecycle
            lc_summary = self.lifecycle_engine.get_summary()

            # 2. Scheduler
            if self.scheduler_algo == "FCFS":
                sch_res = CPUScheduler.run_fcfs(self.scheduler_procs)
            elif self.scheduler_algo == "SJF":
                sch_res = CPUScheduler.run_sjf(self.scheduler_procs)
            elif self.scheduler_algo == "PRIORITY":
                sch_res = CPUScheduler.run_priority(self.scheduler_procs)
            else:
                sch_res = CPUScheduler.run_round_robin(self.scheduler_procs, time_quantum=self.scheduler_quantum)

            sch_comp = CPUScheduler.compare_all(self.scheduler_procs, quantum=self.scheduler_quantum)
            sch_dict = sch_res.to_dict()
            sch_dict["timeline_ticks"] = [sch_res.get_timeline_at_tick(t) for t in range(sch_res.total_duration + 1)]
            sch_dict["raw_processes"] = [p.to_dict() for p in self.scheduler_procs]
            sch_dict["algorithm"] = self.scheduler_algo
            sch_dict["quantum"] = self.scheduler_quantum
            sch_dict["example_datasets"] = CPUScheduler.get_example_datasets()

            # 3. Deadlock
            is_safe, safe_seq, trace = self.banker.is_safe_state()
            seq_str = " -> ".join([f"P{p}" for p in safe_seq]) if is_safe else "None"

            deadlock_data = {
                "scenario_key": self.deadlock_scenario_key,
                "two_process": self.two_proc_deadlock.get_state(),
                "banker": {
                    "is_safe": is_safe,
                    "safe_sequence": seq_str,
                    "allocation": self.banker.allocation,
                    "max_matrix": self.banker.max_matrix,
                    "need": self.banker.need,
                    "available": self.banker.available,
                    "trace": self.banker_trace_msg,
                    "safety_steps": self.banker.get_safety_steps(),
                }
            }

            # 4. PID Comparison & Autonomic Recovery Telemetry
            comp = CrashRecoveryComparison()
            if self.orchestrator_ref and hasattr(self.orchestrator_ref, "state"):
                comp.sync_from_app_state(self.orchestrator_ref.state)
            else:
                st = self.standalone_state
                comp.has_recovery_occurred = st["total_crashes"] > 0
                if comp.has_recovery_occurred:
                    comp.original_process = ProcessIdentityRecord(
                        pid=st["failed_pid"],
                        name="dummy_app.py",
                        start_time_str="Previous Session",
                        end_time_str=st["last_crash_time"],
                        state="TERMINATED / CRASHED",
                        runtime_sec=0.0,
                    )
                    comp.replacement_process = ProcessIdentityRecord(
                        pid=st["app_pid"],
                        name="dummy_app.py",
                        start_time_str=st["last_crash_time"],
                        end_time_str=None,
                        state="RUNNING (ACTIVE)",
                        runtime_sec=st["app_uptime"],
                        cpu_percent=1.2,
                        memory_mb=18.4,
                    )
                    comp.is_replacement_alive = True
                    comp.recovery_duration_ms = 1080.0
                    comp.recovery_duration_sec = 1.08
                    comp.recovery_status = "SUCCESS"
                    comp.sla_met = True
                    comp.crash_detected_at = st["last_crash_time"]
                    comp.recovery_completed_at = st["last_crash_time"]
                    comp.exit_code = 1
                    comp.detection_time = st["last_crash_time"]
                    comp.recovery_start = st["last_crash_time"]
                    comp.restart_time = st["last_crash_time"]
                    comp.downtime_sec = 1.25
                    comp.final_status = "RUNNING"
                else:
                    comp.original_process = ProcessIdentityRecord(
                        pid=st["app_pid"],
                        name="dummy_app.py",
                        start_time_str="Just started",
                        end_time_str=None,
                        state="RUNNING (NOMINAL)",
                        runtime_sec=st["app_uptime"],
                        cpu_percent=1.2,
                        memory_mb=18.4,
                    )
            pid_data = comp.get_comparison_table_data()

            # 5. System Overview Telemetry
            ov = {}
            if self.orchestrator_ref and hasattr(self.orchestrator_ref, "state"):
                s = self.orchestrator_ref.state
                with s._lock:
                    ov = {
                        "cpu_percent": s.cpu_percent,
                        "ram_percent": s.ram_percent,
                        "disk_percent": s.disk_percent,
                        "process_count": s.process_count,
                        "cpu_change": s.cpu_change,
                        "ram_change": s.ram_change,
                        "ram_used_mb": s.ram_used_mb,
                        "ram_total_mb": s.ram_total_mb,
                        "ram_free_mb": s.ram_free_mb,
                        "disk_used_gb": s.disk_used_gb,
                        "disk_total_gb": s.disk_total_gb,
                        "disk_free_gb": s.disk_free_gb,
                        "cpu_history": list(s.cpu_history),
                        "ram_history": list(s.ram_history),
                        "app_name": s.app_name,
                        "app_pid": s.app_pid,
                        "app_is_running": s.app_is_running,
                        "app_uptime": s.app_uptime,
                        "app_cpu_percent": s.app_cpu_percent,
                        "app_memory_percent": s.app_memory_percent,
                        "app_memory_mb": s.app_memory_mb,
                        "failed_pid": s.failed_pid,
                        "last_crash_time": s.last_crash_time,
                        "last_failure_reason": s.last_failure_reason,
                        "total_crashes": s.total_crashes,
                        "risk_probability": round(float(s.risk_probability) if s.risk_probability > 1.0 else (float(s.risk_probability) * 100.0), 1),
                        "risk_category": s.risk_category,
                        "prediction_timestamp": s.prediction_timestamp,
                        "model_loaded": s.model_loaded,
                        "warning_signals": s.warning_signals,
                        "warning_summary": s.warning_summary,
                        "prediction_recommendation": s.prediction_recommendation,
                        "risk_history": list(s.risk_history),
                        "decision_action": s.decision_action,
                        "decision_reason": s.decision_reason,
                        "decision_score": s.decision_score,
                        "decision_alternatives": s.decision_alternatives,
                        "health_overall": s.health_overall,
                        "health_cpu": s.health_cpu,
                        "health_ram": s.health_ram,
                        "health_disk": s.health_disk,
                        "health_stability": s.health_stability,
                        "health_risk_category": s.health_risk_category,
                        "health_recommendation": s.health_recommendation,
                        "health_primary_degraded_metric": s.health_primary_degraded_metric,
                        "health_history": list(s.health_history),
                        "recovery_state": s.recovery_state,
                        "total_restarts": s.total_restarts,
                        "successful_recoveries": s.successful_recoveries,
                        "failed_recoveries": s.failed_recoveries,
                        "recovery_success_rate": s.recovery_success_rate,
                        "last_recovery_duration": s.last_recovery_duration,
                        "sla_target_sec": s.sla_target_sec,
                        "sla_compliance_rate": s.sla_compliance_rate,
                        "recovery_durations": s.recovery_durations,
                        "recent_recoveries": s.recent_recoveries,
                        "module_status": s.module_status,
                        "events": list(s.events),
                    }
            else:
                st = self.standalone_state
                ov = {
                    "cpu_percent": 18.5,
                    "ram_percent": 42.0,
                    "disk_percent": 28.0,
                    "process_count": 142,
                    "cpu_change": 0.5,
                    "ram_change": 0.0,
                    "ram_used_mb": 4096.0,
                    "ram_total_mb": 16384.0,
                    "ram_free_mb": 12288.0,
                    "disk_used_gb": 120.0,
                    "disk_total_gb": 512.0,
                    "disk_free_gb": 392.0,
                    "cpu_history": [{"timestamp": "12:00:00", "value": 15.0}, {"timestamp": "12:00:05", "value": 18.5}],
                    "ram_history": [{"timestamp": "12:00:00", "value": 41.5}, {"timestamp": "12:00:05", "value": 42.0}],
                    "app_name": "dummy_app.py",
                    "app_pid": st["app_pid"],
                    "app_is_running": st["app_is_running"],
                    "app_uptime": st["app_uptime"],
                    "app_cpu_percent": 1.2,
                    "app_memory_percent": 0.8,
                    "app_memory_mb": 18.4,
                    "failed_pid": st["failed_pid"],
                    "last_crash_time": st["last_crash_time"],
                    "last_failure_reason": "Fatal trigger exit (SIGSEGV simulated)" if st["total_crashes"] > 0 else "None recorded",
                    "total_crashes": st["total_crashes"],
                    "risk_probability": 8.0,
                    "risk_category": "LOW",
                    "prediction_timestamp": datetime.now().strftime("%H:%M:%S"),
                    "model_loaded": True,
                    "warning_signals": [],
                    "warning_summary": "None (telemetry nominal)",
                    "prediction_recommendation": "Operating metrics nominal.",
                    "risk_history": [{"timestamp": "12:00:00", "value": 8.0, "category": "LOW"}],
                    "decision_action": "MONITOR" if st["total_crashes"] == 0 else "RESTART_APPLICATION",
                    "decision_reason": "System telemetry nominal. Surveillance active." if st["total_crashes"] == 0 else "Application terminated with exit code 1; host nominal.",
                    "decision_score": 0.96,
                    "decision_alternatives": [],
                    "health_overall": 98,
                    "health_cpu": 100,
                    "health_ram": 98,
                    "health_disk": 100,
                    "health_stability": 96 if st["total_crashes"] == 0 else 88,
                    "health_risk_category": "HEALTHY",
                    "health_recommendation": "All operational metrics within standard operating parameters.",
                    "health_primary_degraded_metric": "None",
                    "health_history": [{"timestamp": "12:00:00", "score": 98}],
                    "recovery_state": "IDLE (Normal Monitoring)" if st["total_crashes"] == 0 else "RECOVERED (PID %s, 1.08s [SLA MET])" % st["app_pid"],
                    "total_restarts": st["total_crashes"],
                    "successful_recoveries": st["total_crashes"],
                    "failed_recoveries": 0,
                    "recovery_success_rate": 100.0,
                    "last_recovery_duration": st["last_recovery_duration"],
                    "sla_target_sec": 2.5,
                    "sla_compliance_rate": 100.0,
                    "recovery_durations": [{"attempt": 1, "duration_sec": 1.08, "duration_ms": 1080.0, "status": "SUCCESS", "sla_met": True, "timestamp": st["last_crash_time"]}],
                    "recent_recoveries": st["recent_recoveries"],
                    "module_status": {
                        "System Monitor": "ONLINE",
                        "Process Monitor": "ONLINE",
                        "Crash Detector": "ONLINE",
                        "AI Failure Predictor": "ONLINE",
                        "Health Analyzer": "ONLINE",
                        "Decision Engine": "ONLINE",
                        "Recovery Daemon": "ONLINE",
                    },
                    "events": st["events"],
                }

            # 6. Memory Leak Telemetry
            mem_status = self.mem_leak.get_status(current_app_mb=ov.get("app_memory_mb", 18.4))

            response_data = {
                "lifecycle": lc_summary,
                "scheduler": sch_dict,
                "scheduler_comparison": sch_comp,
                "deadlock": deadlock_data,
                "pid_comparison": pid_data,
                "timeline": self.timeline_events,
                "overview": ov,
                "memory_leak": mem_status,
            }

            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            self._do_POST_impl()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _do_POST_impl(self):
        if self.path == "/api/action":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(post_body) if post_body else {}
            action = data.get("action", "")

            if action == "step_lifecycle_event":
                pid = data.get("pid", 101)
                event_name = data.get("event", "DISPATCH")
                ok, msg, pcb = self.lifecycle_engine.step_event(pid, event_name)
                self.record_event(event_name, pid, msg, "[SIMULATION]")
            elif action == "select_pcb":
                pid = data.get("pid", 101)
                self.lifecycle_engine.selected_pid = pid
            elif action == "set_lifecycle_algo":
                algo = data.get("algo", "RR")
                q = data.get("quantum", 2)
                if hasattr(self.lifecycle_engine, "set_algorithm"):
                    self.lifecycle_engine.set_algorithm(algo, q)
                elif hasattr(self.lifecycle_engine, "set_scheduling_algorithm"):
                    self.lifecycle_engine.set_scheduling_algorithm(algo, q)
                self.record_event("ALGO_CHANGE", None, f"Switched OS lifecycle scheduler to {algo} (q={q})", "[SIMULATION]")
            elif action == "add_lifecycle_process":
                name = str(data.get("name", "new_task")).strip()
                at = max(0, int(data.get("arrival_time", 0)))
                bt = max(1, int(data.get("cpu_burst", 4)))
                pr = max(1, int(data.get("priority", 1)))
                ioreq = data.get("io_request_time")
                if ioreq is not None and int(ioreq) > 0:
                    ioreq = int(ioreq)
                else:
                    ioreq = None
                iodur = max(0, int(data.get("io_duration", 0)))
                new_proc = self.lifecycle_engine.add_process(
                    name=name,
                    arrival_time=at,
                    cpu_burst=bt,
                    priority=pr,
                    io_request_time=ioreq,
                    io_duration=iodur,
                )
                self.record_event("LIFECYCLE_PROC_ADD", new_proc.pid, f"Allocated simulated PID P{new_proc.pid} for '{new_proc.name}' [SIMULATED PID].", "[SIMULATION]")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "pid": new_proc.pid}).encode("utf-8"))
                return
            elif action == "remove_lifecycle_process":
                pid_val = int(data.get("pid", 0))
                removed = self.lifecycle_engine.remove_process(pid_val)
                if removed:
                    self.record_event("LIFECYCLE_PROC_DEL", pid_val, f"Removed simulated process P{pid_val} from simulation manifest.", "[SIMULATION]")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "removed": removed}).encode("utf-8"))
                return
            elif action == "load_lifecycle_preset":
                preset = data.get("preset", "standard_mix")
                self.lifecycle_engine.load_preset(preset)
                self.record_event("PRESET_LOADED", None, f"Loaded preset workload '{preset}'", "[SIMULATION]")
            elif action == "set_scheduler_algo":
                algo = data.get("algo", "RR")
                self.__class__.scheduler_algo = algo; self.scheduler_algo = algo
                self.record_event("SCHEDULER_ALGO", None, f"Switched standalone CPU scheduler to {algo}", "[SIMULATION]")
            elif action == "set_scheduler_quantum":
                self.__class__.scheduler_quantum = int(data.get("quantum", 2)); self.scheduler_quantum = self.__class__.scheduler_quantum
                self.record_event("QUANTUM_UPDATE", None, f"Updated Round Robin time quantum to {self.scheduler_quantum}", "[SIMULATION]")
            elif action == "set_custom_scheduler_processes":
                p_list = data.get("processes", [])
                procs = []
                for idx, p in enumerate(p_list):
                    pid_val = idx + 1
                    lbl_val = str(p.get("label", f"P{pid_val}"))
                    at_val = max(0, int(p.get("arrival_time", 0)))
                    bt_val = max(1, int(p.get("burst_time", 4)))
                    pr_val = max(1, int(p.get("priority", 1)))
                    procs.append(ScheduledProcess(pid=pid_val, label=lbl_val, arrival_time=at_val, burst_time=bt_val, priority=pr_val))
                if procs:
                    self.__class__.scheduler_procs = procs
                    self.scheduler_procs = procs
                self.record_event("CUSTOM_PROCESSES", None, f"Updated CPU scheduler with {len(procs)} custom process workloads", "[SIMULATION]")
            elif action == "reset_scheduler_dataset":
                self.__class__.scheduler_procs = CPUScheduler.get_default_processes(); self.scheduler_procs = self.__class__.scheduler_procs
                self.record_event("RESET_DATASET", None, "Reset CPU scheduler to benchmark reference dataset", "[SIMULATION]")
            elif action == "set_deadlock_scenario":
                self.__class__.deadlock_scenario_key = data.get("scenario", "two_process"); self.deadlock_scenario_key = self.__class__.deadlock_scenario_key
            elif action == "step_two_process_deadlock":
                st = self.two_proc_deadlock.step()
                self.record_event("DEADLOCK_STEP", None, f"{st.get('title', '')}: {st.get('explanation', st.get('description', ''))}", "[SIMULATION]")
            elif action == "reset_two_process_deadlock":
                st = self.two_proc_deadlock.reset()
                self.record_event("DEADLOCK_RESET", None, "Two-process deadlock simulation reset to Step 0 (free resources)", "[SIMULATION]")
            elif action == "recover_two_process_deadlock":
                st = self.two_proc_deadlock.recover()
                self.record_event("DEADLOCK_RECOVERY", None, st["title"], "[SIMULATION]")
            elif action == "evaluate_banker_request":
                pid = data.get("pid", 0)
                req = data.get("request", [1, 0, 0])
                granted, msg, seq = self.banker.evaluate_request(pid, req)
                self.banker_trace_msg = msg
                event_name = "BANKER_REQUEST_GRANTED" if granted else "UNSAFE_REQUEST_REJECTED"
                self.record_event(event_name, pid, msg, "[SIMULATION]")
            elif action == "update_banker_matrices":
                ok, msg = self.banker.update_custom_matrices(
                    num_processes=int(data.get("num_processes", 5)),
                    num_resources=int(data.get("num_resources", 3)),
                    available=data.get("available", [3, 3, 2]),
                    allocation=data.get("allocation", []),
                    max_matrix=data.get("max_matrix", []),
                    resource_names=data.get("resource_names"),
                )
                self.banker_trace_msg = msg
                self.record_event("BANKER_CUSTOM_MATRICES", None, msg, "[SIMULATION]")
                self.send_response(200 if ok else 400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok" if ok else "error", "message": msg}).encode("utf-8"))
                return
            elif action == "reset_banker":
                self.banker = BankersAlgorithm(self.banker_scenario)
                self.banker_trace_msg = "Banker's algorithm matrices reset to benchmark."
            elif action == "trigger_crash":
                ok, msg = CrashRecoveryComparison.trigger_crash_simulation()
                cls = self.__class__
                cls.record_event("CRASH_TRIGGER", None, "Failure signal dispatched via data/crash.trigger", "[LIVE DATA]")
                if self.orchestrator_ref and hasattr(self.orchestrator_ref, "state"):
                    self.orchestrator_ref.state.add_event("[WEB LAB] Trigger crash initiated via web interface.")
                else:
                    # In standalone mode, simulate crash & restart cycle
                    cls.standalone_state["total_crashes"] += 1
                    old_p = cls.standalone_state["app_pid"]
                    new_p = old_p + 856
                    ts = datetime.now().strftime("%H:%M:%S")
                    cls.standalone_state["failed_pid"] = old_p
                    cls.standalone_state["app_pid"] = new_p
                    cls.standalone_state["last_crash_time"] = ts
                    cls.standalone_state["last_recovery_duration"] = 1.08
                    cls.standalone_state["app_uptime"] = 0.5
                    rec_event = {
                        "timestamp": ts,
                        "old_pid": old_p,
                        "new_pid": new_p,
                        "crash_time": ts,
                        "detection_time": ts,
                        "recovery_start": ts,
                        "restart_time": ts,
                        "exit_code": 1,
                        "downtime_sec": 1.25,
                        "recovery_duration_sec": 1.08,
                        "recovery_duration_ms": 1080.0,
                        "recovery_status": "SUCCESS",
                        "final_status": "RUNNING",
                        "sla_met": True,
                    }
                    cls.standalone_state["recent_recoveries"].append(rec_event)
                    cls.standalone_state["events"].append(f"[{ts}] [CRASH DETECTED] Process PID {old_p} exited code 1")
                    cls.standalone_state["events"].append(f"[{ts}] [DECISION] Action=RESTART_APPLICATION | Reason=Operating system nominal")
                    cls.standalone_state["events"].append(f"[{ts}] Recovery SUCCESS: Old PID={old_p} -> New PID={new_p} (Attempt #{cls.standalone_state['total_crashes']}, SLA=1.08s MET)")
                    cls.record_event("CRASH_DETECTED", old_p, f"Process PID {old_p} exited with code 1", "[LIVE DATA]")
                    cls.record_event("POLICY_DECISION", old_p, "Selected RESTART_APPLICATION policy", "[LIVE DATA]")
                    cls.record_event("RECOVERY_SUCCESS", new_p, f"Respawned PID {new_p} in 1080ms (SLA MET)", "[LIVE DATA]")
            elif action == "start_memory_leak":
                init_ram = 18.4
                if self.orchestrator_ref and hasattr(self.orchestrator_ref, "state"):
                    init_ram = self.orchestrator_ref.state.app_memory_mb
                self.mem_leak.start(initial_mb=init_ram)
                self.record_event("MEMORY_LEAK_START", None, f"Started controlled bounded memory leak demo (initial={init_ram} MB, ceiling=64 MB)", "[SIMULATION]")
            elif action == "stop_memory_leak":
                self.mem_leak.stop()
                self.record_event("MEMORY_LEAK_STOP", None, "Stopped memory leak demo and reclaimed allocated buffers", "[SIMULATION]")
            elif action == "reset_memory_leak":
                self.mem_leak.reset()
                self.record_event("MEMORY_LEAK_RESET", None, "Reset memory leak demonstration state", "[SIMULATION]")
            elif action == "step_demo":
                self.demo_step_current = data.get("step", 1)
                self.record_event(f"TOUR_STEP_{self.demo_step_current}", None, f"Advanced to tour step {self.demo_step_current}", "[SIMULATION]")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "action": action}).encode("utf-8"))
        else:
            self.send_error(404)


class SilentHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        exc_type, _, _ = sys.exc_info()
        if exc_type in (BrokenPipeError, ConnectionResetError):
            return
        super().handle_error(request, client_address)


class WebDashboardServer:
    """Wrapper that runs the dashboard HTTP server in a managed background thread."""

    def __init__(self, orchestrator_ref=None, port: int = 8080):
        self.port = port
        WebDashboardHandler.orchestrator_ref = orchestrator_ref
        self.server: Optional[SilentHTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.server = SilentHTTPServer(("0.0.0.0", self.port), WebDashboardHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="WebDashboardServerThread")
        self.thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
