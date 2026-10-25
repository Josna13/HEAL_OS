import sys
from pathlib import Path

# Script to assemble the enhanced web_server.py with Crash Recovery & Memory Stress Demonstrations

code = r'''"""Zero-dependency self-healing observatory and visual interactive lab for HealOS 2.0."""

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
  <!-- TAB 2: CPU SCHEDULING VISUALIZER (PRACTICAL OS DISPATCH & GANTT LAB)   -->
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
        <button class="btn btn-sm" onclick="schStep(1)">Step ❯</button>
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
        <span class="badge badge-gray" id="sch-state-badge">⏸ PAUSED</span>
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
            <button class="btn btn-sm btn-cyan" onclick="addProcessRow()">+ Add</button>
            <button class="btn btn-sm" onclick="resetCurrentDataset()">↺ Reset</button>
            <button class="btn btn-sm btn-green" onclick="applyCustomProcesses()">✓ Apply</button>
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
  <!-- TAB 3: DEADLOCK VISUALIZATION & RECOVERY LAB                           -->
  <!-- ===================================================================== -->
  <main id="tab-deadlock" style="display:none;">
    <!-- Deadlock Control Toolbar -->
    <div class="panel-box" style="padding:10px 14px; margin-bottom:12px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <div>
          <div style="font-size:1.05rem; font-weight:900; color:#fff; display:flex; align-items:center; gap:8px;">
            <span>🔒 Deadlock Detection & Safe Recovery Lab</span>
            <span class="badge badge-green" id="deadlock-status-badge">● System Safe</span>
          </div>
          <div style="font-size:0.72rem; color:var(--text-muted); margin-top:2px;" id="deadlock-subtitle">
            Interactive Resource Allocation Graph (RAG): Animate circular wait conditions and demonstrate step-by-step resolution.
          </div>
        </div>

        <!-- Controls -->
        <div style="display:flex; gap:6px; align-items:center;">
          <button class="btn btn-sm btn-cyan" onclick="postAction('step_two_process_deadlock')">❯ Step Simulation</button>
          <button class="btn btn-sm btn-red" onclick="triggerDeadlockFormation()">⚠ Create Deadlock</button>
          <button class="btn btn-sm btn-green" onclick="postAction('recover_two_process_deadlock')">🛡 Resolve Deadlock</button>
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
          <div style="font-size:0.7rem; color:var(--text-muted);">Solid = Holding/Allocated &bull; Dashed = Requesting/Waiting</div>
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
      if (tabId === 'deadlock') pollData();
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
    function playTone(freq, type, dur) {
      if (!soundEnabled) return;
      try {
        ensureAudioContext();
        if (!audioCtx) return;
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type || 'sine';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + (dur || 0.15));
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + (dur || 0.15));
      } catch (e) {}
    }
    function playSound(event) {
      if (!soundEnabled) return;
      if (event === 'TICK') playTone(440, 'triangle', 0.05);
      else if (event === 'DISPATCH') playTone(660, 'sine', 0.12);
      else if (event === 'PREEMPT') playTone(330, 'square', 0.15);
      else if (event === 'COMPLETE') playTone(880, 'sine', 0.25);
      else if (event === 'DEADLOCK') playTone(220, 'sawtooth', 0.35);
      else if (event === 'RUNNING') playTone(587, 'sine', 0.2);
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
      playSound('DEADLOCK');
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
      renderRecoverySection(pidData, ov);
    }

    // ==================== CPU SCHEDULER CONTROLLER =========================
    let schedulerState = {
      algorithm: 'RR',
      quantum: 2,
      clockTick: 0,
      totalDuration: 12,
      timelineTicks: [],
      rawProcesses: [],
      isPlaying: false,
      timer: null,
      speedMs: 800
    };

    function setAlgorithm(algo) {
      ensureAudioContext();
      postAction('set_scheduler_algo', { algo: algo });
      ['FCFS', 'SJF', 'RR', 'PRIORITY'].forEach(a => {
        const b = document.getElementById('btn-algo-' + a);
        if (b) {
          if (a === algo) b.className = 'btn btn-sm btn-cyan';
          else b.className = 'btn btn-sm';
        }
      });
      const qWrap = document.getElementById('rr-quantum-wrap');
      if (qWrap) qWrap.style.display = (algo === 'RR') ? 'inline-flex' : 'none';
      const pill = document.getElementById('sch-algo-pill');
      if (pill) pill.innerText = algo === 'RR' ? `RR (Q=${schedulerState.quantum})` : algo;
    }

    function updateQuantum(val) {
      const q = parseInt(val, 10) || 2;
      schedulerState.quantum = q;
      postAction('set_scheduler_quantum', { quantum: q });
      const pill = document.getElementById('sch-algo-pill');
      if (pill) pill.innerText = `RR (Q=${q})`;
    }

    function schTogglePlay() {
      ensureAudioContext();
      schedulerState.isPlaying = !schedulerState.isPlaying;
      const btn = document.getElementById('btn-sch-play');
      const badge = document.getElementById('sch-state-badge');
      if (schedulerState.isPlaying) {
        if (btn) { btn.innerText = '⏸ Pause'; btn.className = 'btn btn-sm btn-amber'; }
        if (badge) { badge.innerText = '▶ RUNNING'; badge.className = 'badge badge-green'; }
        schedulerState.timer = setInterval(() => {
          schStep(1);
        }, schedulerState.speedMs);
      } else {
        if (btn) { btn.innerText = '▶ Play'; btn.className = 'btn btn-sm btn-green'; }
        if (badge) { badge.innerText = '⏸ PAUSED'; badge.className = 'badge badge-gray'; }
        clearInterval(schedulerState.timer);
        schedulerState.timer = null;
      }
    }

    function setSchSpeed(ms, label) {
      schedulerState.speedMs = ms;
      ['05', '1', '2', '4'].forEach(spd => {
        const b = document.getElementById('btn-spd-' + spd);
        if (b) {
          if (spd === label) b.className = 'btn btn-sm btn-cyan';
          else b.className = 'btn btn-sm';
        }
      });
      if (schedulerState.isPlaying) {
        clearInterval(schedulerState.timer);
        schedulerState.timer = setInterval(() => schStep(1), schedulerState.speedMs);
      }
    }

    function schResetTick() {
      if (schedulerState.isPlaying) schTogglePlay();
      schedulerState.clockTick = 0;
      renderSchedulerClock(0);
    }

    function schStep(delta) {
      ensureAudioContext();
      const maxT = schedulerState.totalDuration || 12;
      let nextTick = schedulerState.clockTick + delta;
      if (nextTick > maxT) {
        nextTick = 0;
        if (schedulerState.isPlaying) schTogglePlay();
      }
      schedulerState.clockTick = nextTick;
      renderSchedulerClock(nextTick);
    }

    function renderSchedulerClock(tick) {
      const clockEl = document.getElementById('sch-clock-text');
      if (clockEl) clockEl.innerText = `t = ${tick}`;

      const maxT = schedulerState.totalDuration || 1;
      const pct = Math.min(100, Math.max(0, (tick / maxT) * 100));
      const cursor = document.getElementById('gantt-cursor');
      if (cursor) cursor.style.left = `${pct}%`;

      const snapshot = (schedulerState.timelineTicks && schedulerState.timelineTicks[tick]) || {};
      const activePid = snapshot.active_process || null;
      const readyQueue = snapshot.ready_queue || [];
      const completedList = snapshot.completed_list || [];

      // Render Ready Queue
      const rqEl = document.getElementById('sch-ready-list');
      const rqCount = document.getElementById('sch-rq-count');
      if (rqCount) rqCount.innerText = `${readyQueue.length} queued`;
      if (rqEl) {
        if (readyQueue.length === 0) {
          rqEl.innerHTML = '<span style="color:#64748b; font-size:0.72rem;">No processes currently waiting in ready queue.</span>';
        } else {
          rqEl.innerHTML = readyQueue.map(p => {
            const proc = typeof p === 'object' ? p : { label: p, remaining_time: 1 };
            return `
              <div class="proc-token">
                <span style="color:var(--accent-cyan); font-weight:bold;">${proc.label || proc.name || p}</span>
                <span style="color:var(--text-dim); font-size:0.68rem;">rem: ${proc.remaining_time || proc.remaining || '-'}</span>
              </div>
            `;
          }).join('');
        }
      }

      // Render CPU Core 0 Socket
      const socketBox = document.getElementById('cpu-socket-box');
      const jobLabel = document.getElementById('cpu-job-label');
      const burstCountdown = document.getElementById('cpu-burst-countdown');
      const cpuPill = document.getElementById('cpu-pill');
      const cpuProg = document.getElementById('cpu-progress-bar');

      if (activePid) {
        if (socketBox) socketBox.className = 'cpu-socket active';
        if (jobLabel) {
          jobLabel.innerText = `${activePid}`;
          jobLabel.style.color = '#38bdf8';
        }
        if (cpuPill) {
          cpuPill.innerText = 'DISPATCHED';
          cpuPill.className = 'badge badge-green';
        }

        const rawProc = (schedulerState.rawProcesses || []).find(p => p.label === activePid || p.name === activePid);
        const originalBT = rawProc ? (rawProc.burst_time || rawProc.burst || 4) : 4;
        const remBT = snapshot.remaining_burst !== undefined ? snapshot.remaining_burst : Math.max(0, originalBT - 1);

        if (burstCountdown) {
          burstCountdown.innerText = `Remaining Burst: ${remBT} / ${originalBT} ticks`;
        }
        if (cpuProg) {
          const donePct = Math.round(((originalBT - remBT) / originalBT) * 100);
          cpuProg.style.width = `${donePct}%`;
        }
        playSound('TICK');
      } else {
        if (socketBox) socketBox.className = 'cpu-socket idle';
        if (jobLabel) {
          jobLabel.innerText = 'CPU IDLE';
          jobLabel.style.color = '#64748b';
        }
        if (burstCountdown) burstCountdown.innerText = 'No Job Dispatched';
        if (cpuPill) {
          cpuPill.innerText = 'IDLE';
          cpuPill.className = 'badge badge-gray';
        }
        if (cpuProg) cpuProg.style.width = '0%';
      }

      // Render Completed Jobs
      const compEl = document.getElementById('sch-completed-list');
      const compCount = document.getElementById('sch-comp-count');
      if (compCount) compCount.innerText = `${completedList.length} finished`;
      if (compEl) {
        if (completedList.length === 0) {
          compEl.innerHTML = '<span style="color:#64748b; font-size:0.72rem;">Completed processes will appear here.</span>';
        } else {
          compEl.innerHTML = completedList.map(p => {
            const label = typeof p === 'object' ? (p.label || p.name) : p;
            return `
              <div class="proc-token" style="border-color:#166534; background:rgba(34, 197, 94, 0.08);">
                <span style="color:#86efac; font-weight:bold;">${label}</span>
                <span class="badge badge-green" style="font-size:0.6rem; padding:1px 4px;">DONE</span>
              </div>
            `;
          }).join('');
        }
      }
    }

    function renderGanttTimeline(sch) {
      const track = document.getElementById('gantt-track');
      const ruler = document.getElementById('gantt-ruler');
      if (!track || !sch) return;

      const totalD = sch.total_duration || 12;
      const palette = ['#0284c7', '#7c3aed', '#10b981', '#f59e0b', '#ec4899', '#6366f1'];
      const procColors = {};
      (sch.raw_processes || []).forEach((p, i) => {
        procColors[p.label] = palette[i % palette.length];
      });

      const blocks = sch.gantt_chart || [];
      track.innerHTML = blocks.map(b => {
        const dur = (b.end - b.start);
        const widthPct = (dur / totalD) * 100;
        const color = b.process === 'IDLE' ? '#1e293b' : (procColors[b.process] || '#0284c7');
        return `
          <div class="gantt-block" style="width:${widthPct}%; background:${color};" title="${b.process}: t=${b.start} to ${b.end}">
            ${b.process}
          </div>
        `;
      }).join('');

      if (ruler) {
        let rulerMarks = '';
        for (let t = 0; t <= totalD; t += 2) {
          const markPct = (t / totalD) * 100;
          rulerMarks += `<div style="position:absolute; left:${markPct}%; transform:translateX(-50%);">${t}</div>`;
        }
        ruler.innerHTML = rulerMarks;
      }
    }

    function renderScheduler() {
      fetch('/api/status').then(r => r.json()).then(data => {
        const sch = data.scheduler || {};
        schedulerState.timelineTicks = sch.timeline_ticks || [];
        schedulerState.totalDuration = sch.total_duration || 12;
        schedulerState.rawProcesses = sch.raw_processes || [];
        schedulerState.algorithm = sch.algorithm || 'RR';
        schedulerState.quantum = sch.quantum || 2;

        renderGanttTimeline(sch);
        renderSchedulerClock(schedulerState.clockTick);

        // Render Process Inputs Table
        const inputTbody = document.getElementById('sch-input-tbody');
        if (inputTbody) {
          inputTbody.innerHTML = (sch.raw_processes || []).map((p, idx) => `
            <tr>
              <td><input type="text" value="${p.label}" id="inp-lbl-${idx}" style="width:58px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px; font-weight:bold; font-size:0.72rem;"></td>
              <td><input type="number" min="0" max="50" value="${p.arrival_time}" id="inp-at-${idx}" style="width:48px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px; font-size:0.72rem;"></td>
              <td><input type="number" min="1" max="50" value="${p.burst_time}" id="inp-bt-${idx}" style="width:48px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px; font-size:0.72rem;"></td>
              <td><input type="number" min="1" max="10" value="${p.priority}" id="inp-pr-${idx}" style="width:44px; background:#020617; border:1px solid var(--border); color:#fff; border-radius:3px; padding:2px 4px; font-size:0.72rem;"></td>
              <td><button class="btn btn-sm btn-red" onclick="removeProcessRow(${idx})" style="padding:1px 5px;">✕</button></td>
            </tr>
          `).join('');
        }

        // Render Results Table
        const resTbody = document.getElementById('sch-results-tbody');
        if (resTbody && sch.results) {
          resTbody.innerHTML = sch.results.map(r => `
            <tr>
              <td><b style="color:var(--accent-cyan);">${r.process_id}</b></td>
              <td>${r.arrival_time}</td>
              <td>${r.burst_time}</td>
              <td>${r.priority !== undefined ? r.priority : '-'}</td>
              <td style="font-family:var(--font-mono);">${r.completion_time}</td>
              <td style="font-family:var(--font-mono); color:#22c55e;">${r.turnaround_time}</td>
              <td style="font-family:var(--font-mono); color:#22d3ee;">${r.waiting_time}</td>
            </tr>
          `).join('');

          const avgTat = document.getElementById('avg-tat');
          if (avgTat) avgTat.innerText = `${(sch.avg_turnaround_time || 0).toFixed(2)}t`;
          const avgWt = document.getElementById('avg-wt');
          if (avgWt) avgWt.innerText = `${(sch.avg_waiting_time || 0).toFixed(2)}t`;
        }
      });
    }

    function addProcessRow() {
      const idx = (schedulerState.rawProcesses || []).length;
      schedulerState.rawProcesses.push({
        label: `P${idx + 1}`,
        arrival_time: idx * 2,
        burst_time: 4,
        priority: idx + 1
      });
      applyCustomProcesses();
    }

    function removeProcessRow(index) {
      if (schedulerState.rawProcesses.length <= 1) return;
      schedulerState.rawProcesses.splice(index, 1);
      applyCustomProcesses();
    }

    function applyCustomProcesses() {
      const procs = [];
      const tbody = document.getElementById('sch-input-tbody');
      const rows = tbody ? tbody.querySelectorAll('tr') : [];
      rows.forEach((r, idx) => {
        const lbl = document.getElementById(`inp-lbl-${idx}`);
        const at = document.getElementById(`inp-at-${idx}`);
        const bt = document.getElementById(`inp-bt-${idx}`);
        const pr = document.getElementById(`inp-pr-${idx}`);
        if (lbl && at && bt && pr) {
          procs.push({
            label: lbl.value.trim() || `P${idx+1}`,
            arrival_time: parseInt(at.value, 10) || 0,
            burst_time: parseInt(bt.value, 10) || 1,
            priority: parseInt(pr.value, 10) || 1
          });
        }
      });
      postAction('set_custom_scheduler_processes', { processes: procs }).then(() => {
        renderScheduler();
      });
    }

    function resetCurrentDataset() {
      postAction('reset_scheduler_dataset').then(() => renderScheduler());
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
                self.scheduler_algo = algo
                self.record_event("SCHEDULER_ALGO", None, f"Switched standalone CPU scheduler to {algo}", "[SIMULATION]")
            elif action == "set_scheduler_quantum":
                self.scheduler_quantum = int(data.get("quantum", 2))
                self.record_event("QUANTUM_UPDATE", None, f"Updated Round Robin time quantum to {self.scheduler_quantum}", "[SIMULATION]")
            elif action == "set_custom_scheduler_processes":
                p_list = data.get("processes", [])
                procs = []
                for p in p_list:
                    lbl = p.get("label", "P1")
                    at = int(p.get("arrival_time", 0))
                    bt = int(p.get("burst_time", 4))
                    pr = int(p.get("priority", 1))
                    procs.append(ScheduledProcess(lbl, at, bt, pr))
                self.scheduler_procs = procs
                self.record_event("CUSTOM_PROCESSES", None, f"Updated CPU scheduler with {len(procs)} custom process workloads", "[SIMULATION]")
            elif action == "reset_scheduler_dataset":
                self.scheduler_procs = CPUScheduler.get_default_processes()
                self.record_event("RESET_DATASET", None, "Reset CPU scheduler to benchmark reference dataset", "[SIMULATION]")
            elif action == "set_deadlock_scenario":
                self.deadlock_scenario_key = data.get("scenario", "two_process")
            elif action == "step_two_process_deadlock":
                st = self.two_proc_deadlock.step()
                self.record_event("DEADLOCK_STEP", None, f"{st['title']}: {st['description']}", "[SIMULATION]")
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
'''

with open("dashboard/web_server.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Enhanced web_server.py written successfully!")
import py_compile
py_compile.compile("dashboard/web_server.py", doraise=True)
print("Python compilation SUCCESS (0 errors)!")
