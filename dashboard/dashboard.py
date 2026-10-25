"""
HealOS 2.0 - Permanent Stable Terminal Dashboard
Single permanent dashboard displaying all monitoring modules simultaneously
without screen clearing, switching views, or flickering.

Sections displayed permanently together on one screen:
1. System Monitor             2. Process & Crash Detector
3. AI Predictor & Decision    4. Health Analyzer
5. Recovery Service & SLA     6. Subsystems Status
7. HealOS Logger & Timeline   8. Command Footer

Uses rich.live.Live for in-place cursor overwriting with zero terminal scrolling.
"""

import os
import shutil
import sys
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from config import (
    DASHBOARD_REFRESH_INTERVAL,
    EVENT_TIMELINE_LIMIT,
    SYSTEM_MONITOR_INTERVAL,
    RECOVERY_SLA_TARGET_SECONDS,
    MAX_RECENT_RECOVERIES_DISPLAY,
)
from dashboard.os_lab import OSLabCoordinator


def format_bar(value: float, max_val: float = 100.0, width: int = 10) -> str:
    """Generates a compact visual progress bar: [████░░░░] 45.0%"""
    ratio = max(0.0, min(1.0, value / max_val))
    filled_len = int(round(width * ratio))
    empty_len = width - filled_len
    return f"[{'█' * filled_len}{'░' * empty_len}] {value:4.1f}%"


class AppState:
    """
    Centralized, thread-safe state container shared across all HealOS subsystems.
    Guarantees consistent, atomic metric reads for the permanent dashboard.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.start_time: float = time.time()
        self.start_datetime_str: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. System Monitor Telemetry
        self.cpu_percent: float = 0.0
        self.cpu_change: float = 0.0
        self.ram_percent: float = 0.0
        self.ram_change: float = 0.0
        self.ram_used_mb: float = 0.0
        self.ram_total_mb: float = 0.0
        self.disk_percent: float = 0.0
        self.disk_used_gb: float = 0.0
        self.disk_total_gb: float = 0.0
        self.ram_free_mb: float = 0.0
        self.disk_free_gb: float = 0.0
        self.process_count: int = 0

        # 2. Process Monitor & Crash Detector
        self.app_name: str = "dummy_app.py"
        self.app_is_running: bool = False
        self.app_pid: Optional[int] = None
        self.app_uptime: float = 0.0
        self.app_cpu_percent: float = 0.0
        self.app_memory_percent: float = 0.0
        self.app_memory_mb: float = 0.0
        self.failed_pid: Optional[int] = None
        self.last_crash_time: str = "None"
        self.last_failure_reason: str = "None recorded"
        self.total_crashes: int = 0

        # 3. AI Failure Predictor
        self.risk_probability: float = 0.0
        self.risk_category: str = "LOW"
        self.prediction_timestamp: str = "None"
        self.model_loaded: bool = False
        self.warning_signals: List[str] = []
        self.warning_summary: str = "None (telemetry nominal)"
        self.prediction_recommendation: str = "Operating metrics nominal."

        # 4. System Health Analyzer
        self.health_overall: float = 100.0
        self.health_cpu: float = 100.0
        self.health_ram: float = 100.0
        self.health_disk: float = 100.0
        self.health_stability: float = 100.0
        self.health_risk_category: str = "HEALTHY"
        self.health_recommendation: str = "All subsystems operational."
        self.health_primary_degraded_metric: str = "None (All Nominal)"

        # 5. AI Decision Engine
        self.decision_action: str = "MONITOR"
        self.decision_reason: str = "System telemetry nominal. Surveillance active."
        self.decision_score: float = 0.96
        self.decision_alternatives: List[str] = ["INVESTIGATE"]

        # 6. Recovery Service (SLA & Sessions)
        self.recovery_state: str = "IDLE (Normal Monitoring)"
        self.total_restarts: int = 0
        self.successful_recoveries: int = 0
        self.failed_recoveries: int = 0
        self.recovery_success_rate: float = 100.0
        self.last_recovery_duration: float = 0.0
        self.last_recovery_time: str = "None"
        self.last_recovery_status: str = "None"
        self.sla_target_sec: float = float(RECOVERY_SLA_TARGET_SECONDS)
        self.sla_met_count: int = 0
        self.sla_compliance_rate: float = 100.0
        self.recovery_avg_duration: float = 0.0
        self.recovery_fastest_duration: float = 0.0
        self.recovery_slowest_duration: float = 0.0
        self.recent_recoveries: List[Dict[str, Any]] = []
        self.repeated_crashes: int = 0
        self.recovery_failures: int = 0
        self.recovery_trend: str = "INSUFFICIENT DATA"
        self.recovery_trend_details: str = "Awaiting recovery events"

        # 7. Historical Analytics (from logs/recovery.log)
        self.log_total_recoveries: int = 0
        self.log_avg_duration_sec: float = 0.0
        self.log_trend: str = "INSUFFICIENT DATA"

        # 8. Subsystems Status
        self.module_status: Dict[str, str] = {
            "System Monitor": "ONLINE",
            "Process Monitor": "ONLINE",
            "AI Predictor": "ONLINE",
            "Health Analyzer": "ONLINE",
            "Crash Detector": "ONLINE",
            "Decision Engine": "ONLINE",
            "Recovery Daemon": "ONLINE",
            "Logger": "ONLINE",
        }

        # 9. HealOS Logger & Live Event Timeline
        self.events: deque = deque(maxlen=EVENT_TIMELINE_LIMIT)
        self.add_event("HealOS 2.0 system state initialized.")

        # Rolling historical metrics for synchronized charts
        self.cpu_history: deque = deque(maxlen=60)
        self.ram_history: deque = deque(maxlen=60)
        self.risk_history: deque = deque(maxlen=60)
        self.health_history: deque = deque(maxlen=60)
        self.recovery_durations: List[Dict[str, Any]] = []

    def add_event(self, description: str) -> None:
        """Appends a timestamped event into the rolling timeline."""
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            self.events.append(f"[{ts}] {description}")

    def get_events(self) -> List[str]:
        """Returns snapshot of events."""
        with self._lock:
            return list(self.events)

    def update_metrics(self, m) -> None:
        """Updates system resource telemetry."""
        with self._lock:
            self.cpu_percent = m.cpu_percent
            self.cpu_change = m.cpu_change
            self.ram_percent = m.ram_percent
            self.ram_change = m.ram_change
            self.ram_used_mb = m.ram_used_mb
            self.ram_total_mb = m.ram_total_mb
            self.disk_percent = m.disk_percent
            self.disk_used_gb = m.disk_used_gb
            self.disk_total_gb = m.disk_total_gb
            self.process_count = m.process_count
            self.ram_free_mb = getattr(m, "ram_free_mb", 0.0)
            self.disk_free_gb = getattr(m, "disk_free_gb", 0.0)
            ts = datetime.now().strftime("%H:%M:%S")
            self.cpu_history.append({"timestamp": ts, "value": self.cpu_percent})
            self.ram_history.append({"timestamp": ts, "value": self.ram_percent, "used_mb": self.ram_used_mb, "total_mb": self.ram_total_mb})

    def update_app_process_info(self, info: Optional[Any]) -> None:
        """Updates monitored application process resource metrics."""
        with self._lock:
            if info:
                self.app_cpu_percent = getattr(info, "cpu_percent", 0.0)
                self.app_memory_percent = getattr(info, "memory_percent", 0.0)
                self.app_memory_mb = getattr(info, "memory_mb", 0.0)
            else:
                self.app_cpu_percent = 0.0
                self.app_memory_percent = 0.0
                self.app_memory_mb = 0.0

    def update_prediction(self, pred) -> None:
        """Updates AI predictive analytics."""
        with self._lock:
            self.risk_probability = pred.risk_probability
            self.risk_category = pred.risk_category
            self.prediction_recommendation = pred.recommendation
            self.model_loaded = pred.model_loaded
            self.prediction_timestamp = getattr(pred, "timestamp", "None")
            self.warning_signals = getattr(pred, "warning_signals", [])
            self.warning_summary = getattr(pred, "warning_summary", "None (telemetry nominal)")
            ts = datetime.now().strftime("%H:%M:%S")
            self.risk_history.append({
                "timestamp": ts,
                "value": round(self.risk_probability * 100, 1),
                "category": self.risk_category,
            })

    def update_health(self, h) -> None:
        """Updates deterministic health score outputs."""
        with self._lock:
            self.health_overall = h.overall_score
            self.health_cpu = h.cpu_score
            self.health_ram = h.ram_score
            self.health_disk = h.disk_score
            self.health_stability = h.stability_score
            self.health_risk_category = h.risk_category
            self.health_recommendation = h.recommendation
            self.health_primary_degraded_metric = getattr(h, "primary_degraded_metric", "None (All Nominal)")
            ts = datetime.now().strftime("%H:%M:%S")
            self.health_history.append({
                "timestamp": ts,
                "value": round(self.health_overall, 1),
                "cpu": round(self.health_cpu, 1),
                "ram": round(self.health_ram, 1),
                "disk": round(self.health_disk, 1),
                "stability": round(self.health_stability, 1),
                "category": self.health_risk_category,
            })

    def update_recovery_status(self, summary: Dict[str, Any]) -> None:
        """Updates application and recovery tracking metrics."""
        with self._lock:
            self.app_is_running = summary.get("is_running", False)
            self.app_pid = summary.get("current_pid")
            self.app_uptime = summary.get("app_uptime", 0.0)

            if summary.get("failed_pid") is not None:
                self.failed_pid = summary.get("failed_pid")
            if summary.get("last_crash_time"):
                self.last_crash_time = summary.get("last_crash_time")
            if summary.get("last_failure_reason"):
                self.last_failure_reason = summary.get("last_failure_reason")
            if summary.get("recovery_state"):
                self.recovery_state = summary.get("recovery_state")

            self.total_crashes = summary.get("total_crashes", 0)
            self.total_restarts = summary.get("total_restarts", 0)
            self.successful_recoveries = summary.get("successful_recoveries", 0)
            self.failed_recoveries = summary.get("failed_recoveries", 0)
            self.recovery_success_rate = summary.get("success_rate", 100.0)
            self.sla_target_sec = summary.get("sla_target_sec", self.sla_target_sec)
            self.sla_met_count = summary.get("sla_met_count", self.sla_met_count)
            self.sla_compliance_rate = summary.get("sla_compliance_rate", self.sla_compliance_rate)
            self.recovery_avg_duration = summary.get("avg_duration_sec", self.recovery_avg_duration)
            self.recovery_fastest_duration = summary.get("fastest_duration_sec", self.recovery_fastest_duration)
            self.recovery_slowest_duration = summary.get("slowest_duration_sec", self.recovery_slowest_duration)
            self.repeated_crashes = summary.get("repeated_crashes", self.repeated_crashes)
            self.recovery_failures = summary.get("recovery_failures", self.failed_recoveries)
            if "performance_trend" in summary:
                self.recovery_trend = summary["performance_trend"]
            if "performance_trend_details" in summary:
                self.recovery_trend_details = summary["performance_trend_details"]

            if "recent_recoveries" in summary and summary["recent_recoveries"]:
                self.recent_recoveries = list(summary["recent_recoveries"])
                self.recovery_durations = [
                    {
                        "attempt": r.get("attempt", idx + 1),
                        "duration_ms": r.get("duration_ms", 0.0),
                        "duration_sec": r.get("duration_sec", 0.0),
                        "status": r.get("status", "SUCCESS"),
                        "sla_met": r.get("sla_met", True),
                        "timestamp": r.get("timestamp", "-"),
                    }
                    for idx, r in enumerate(self.recent_recoveries)
                ]

            if "recent_recoveries" in summary and summary["recent_recoveries"]:
                self.recent_recoveries = summary["recent_recoveries"]

            last_rec = summary.get("last_recovery")
            if last_rec:
                self.last_recovery_time = last_rec.get("timestamp", "None")
                self.last_recovery_duration = float(last_rec.get("recovery_duration_sec", 0.0))
                self.last_recovery_status = last_rec.get("recovery_status", "None")

    def update_decision(self, dec) -> None:
        """Updates active decision engine assessment."""
        with self._lock:
            self.decision_action = dec.action
            self.decision_reason = dec.reason
            self.decision_score = dec.confidence_score
            self.decision_alternatives = dec.alternative_actions

    def update_log_analysis(self, report) -> None:
        """Updates historical log analytics."""
        with self._lock:
            self.log_total_recoveries = report.total_events
            self.log_avg_duration_sec = report.avg_duration_sec
            self.log_trend = report.crash_trend
            if getattr(report, "has_data", False):
                self.recovery_fastest_duration = report.fastest_duration_sec
                self.recovery_slowest_duration = report.slowest_duration_sec
                self.sla_compliance_rate = getattr(report, "sla_compliance_rate", self.sla_compliance_rate)
                if hasattr(report, "performance_trend") and report.performance_trend != "INSUFFICIENT DATA":
                    self.recovery_trend = report.performance_trend
                    self.recovery_trend_details = getattr(report, "performance_trend_details", self.recovery_trend_details)
                elif not self.recent_recoveries and hasattr(report, "performance_trend"):
                    self.recovery_trend = report.performance_trend
                    self.recovery_trend_details = getattr(report, "performance_trend_details", self.recovery_trend_details)
                if hasattr(report, "repeated_crashes") and self.repeated_crashes == 0:
                    self.repeated_crashes = report.repeated_crashes
                if hasattr(report, "recovery_failures") and self.failed_recoveries == 0:
                    self.recovery_failures = report.recovery_failures
                if not self.recent_recoveries and getattr(report, "recent_recoveries", None):
                    self.recent_recoveries = report.recent_recoveries

    def set_module_status(self, module_name: str, status: str) -> None:
        """Updates health status of a specific HealOS subsystem."""
        with self._lock:
            self.module_status[module_name] = status


class TerminalDashboard(threading.Thread):
    """
    Renders ONE permanent, flicker-free terminal dashboard displaying all modules.
    Supports top-level tab navigation:
      - Tab 1: System Overview (HealOS 2.0 Autonomic Health & Recovery Panels 1-7)
      - Tab 2: OS Process Lab (Lifecycle, CPU Scheduler, PID Comparison, Deadlock Lab)
    Updates values in-place via rich.live.Live with interactive keyboard tab switching.
    """

    def __init__(
        self,
        state: AppState,
        refresh_interval: float = DASHBOARD_REFRESH_INTERVAL,
        initial_tab: str = "overview",
        initial_section: str = "ALL",
    ):
        super().__init__(name="DashboardThread", daemon=True)
        self.state = state
        self.refresh_interval = refresh_interval
        self._stop_event = threading.Event()
        self.console = Console() if RICH_AVAILABLE else None
        self.active_tab: str = initial_tab
        self.os_lab = OSLabCoordinator()
        if initial_section:
            self.os_lab.switch_section(initial_section)
        self._input_thread: Optional[threading.Thread] = None

    def stop(self) -> None:
        """Signals dashboard thread to terminate."""
        self._stop_event.set()

    def switch_tab(self, tab: str) -> None:
        """Switches active dashboard tab ('overview' or 'os-lab')."""
        norm = tab.strip().lower()
        if norm in ("overview", "system", "1"):
            self.active_tab = "overview"
        elif norm in ("os-lab", "process-lab", "lab", "2"):
            self.active_tab = "os-lab"

    def switch_lab_section(self, section: str) -> None:
        """Switches lab sub-section: ALL, LIFECYCLE, SCHEDULER, PID_COMPARE, DEADLOCK."""
        self.active_tab = "os-lab"
        self.os_lab.switch_section(section)

    def step_lab(self) -> str:
        """Steps lifecycle simulation by 1 tick."""
        return self.os_lab.lifecycle_engine.step()

    def next_lab_demo_step(self) -> str:
        """Advances guided presentation walkthrough."""
        return self.os_lab.next_demo_step()

    def _start_input_listener(self) -> None:
        """Starts non-blocking keyboard listener for interactive tab navigation."""
        self._input_thread = threading.Thread(
            target=self._keyboard_listener_loop,
            daemon=True,
            name="DashboardKeyListener",
        )
        self._input_thread.start()

    def _handle_keypress(self, key: str) -> None:
        """Dispatches keypress to tab navigation or simulation controls."""
        if key == "1":
            self.active_tab = "overview"
        elif key == "2":
            self.active_tab = "os-lab"
        elif key in ("a", "l"):
            self.active_tab = "os-lab"
            self.os_lab.switch_section("LIFECYCLE")
        elif key == "b":
            self.active_tab = "os-lab"
            self.os_lab.switch_section("SCHEDULER")
        elif key == "c":
            self.active_tab = "os-lab"
            self.os_lab.switch_section("PID_COMPARE")
        elif key == "d":
            self.active_tab = "os-lab"
            self.os_lab.switch_section("DEADLOCK")
        elif key == "p":
            if self.active_tab == "os-lab":
                self.os_lab.next_demo_step()
        elif key in ("s", " "):
            if self.active_tab == "os-lab":
                self.os_lab.lifecycle_engine.step()
        elif key == "r":
            if self.active_tab == "os-lab":
                self.os_lab.lifecycle_engine.reset()
        elif key == "t":
            from dashboard.pid_comparison import CrashRecoveryComparison
            CrashRecoveryComparison.trigger_crash_simulation()
            self.state.add_event("[LAB] Demo crash trigger created via key 'T'.")

    def _keyboard_listener_loop(self) -> None:
        """Safely listens for terminal input without crashing non-interactive terminals."""
        try:
            if sys.platform == "win32":
                import msvcrt
                while not self._stop_event.is_set():
                    if msvcrt.kbhit():
                        ch = msvcrt.getch()
                        try:
                            key = ch.decode("utf-8", errors="ignore").lower()
                            self._handle_keypress(key)
                        except Exception:
                            pass
                    time.sleep(0.08)
            else:
                import termios
                import tty
                import select

                if not sys.stdin.isatty():
                    return

                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd)
                    while not self._stop_event.is_set():
                        r, _, _ = select.select([sys.stdin], [], [], 0.1)
                        if r:
                            ch = sys.stdin.read(1)
                            self._handle_keypress(ch.lower())
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            # Piped / CI / background fallback
            pass

    def run(self) -> None:
        """Execution loop for terminal dashboard."""
        self._start_input_listener()

        if RICH_AVAILABLE and self.console:
            initial_renderable = self._build_dashboard()
            with Live(
                initial_renderable,
                console=self.console,
                auto_refresh=False,
                transient=False,
                refresh_per_second=2,
            ) as live:
                while not self._stop_event.is_set():
                    try:
                        renderable = self._build_dashboard()
                        live.update(renderable, refresh=True)
                    except Exception:
                        pass
                    self._stop_event.wait(self.refresh_interval)
        else:
            # Plain terminal fallback without screen flicker
            sys.stdout.write("\033[2J\033[H")  # Clear once on initial startup
            sys.stdout.flush()
            while not self._stop_event.is_set():
                try:
                    self._render_plain()
                except Exception:
                    pass
                self._stop_event.wait(self.refresh_interval)

    def _get_uptime_str(self) -> str:
        """Computes human-readable runtime."""
        elapsed = int(time.time() - self.state.start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        return f"{hrs:02d}h {mins:02d}m {secs:02d}s"

    def _build_dashboard(self) -> Group:
        """
        Constructs the permanent single-screen dashboard layout (approx 29 lines).
        All 9 modules reside in fixed permanent positions.
        """
        uptime_str = self._get_uptime_str()
        now_str = datetime.now().strftime("%H:%M:%S")

        # -------------------------------------------------------------
        # Header (Permanent Banner with Integrated Tab Navigation)
        # -------------------------------------------------------------
        tab1_style = "bold black on cyan" if self.active_tab == "overview" else "dim white"
        tab2_style = "bold black on cyan" if self.active_tab == "os-lab" else "dim white"

        header_text = Text()
        header_text.append(" HEALOS 2.0 ", style="bold cyan")
        header_text.append("│ ", style="bold white")
        header_text.append("[1] SYSTEM OVERVIEW ", style=tab1_style)
        header_text.append("│ ", style="dim white")
        header_text.append("[2] OS PROCESS LAB ", style=tab2_style)
        header_text.append(f"│ Uptime: {uptime_str} │ Time: {now_str} │ Status: ", style="yellow")
        header_text.append("ONLINE", style="bold green" if self.state.app_is_running else "bold red")
        header_panel = Panel(header_text, style="blue", padding=(0, 1))

        # If OS Process Lab tab is active, render its dedicated educational view
        if self.active_tab == "os-lab":
            lab_view = self.os_lab.render(self.state)
            return Group(header_panel, lab_view)

        # -------------------------------------------------------------
        # Row 1: 3 Fixed Panels
        # [1] System Monitor │ [2] Process & Crash Detector │ [3] AI Predictor & Decision
        # -------------------------------------------------------------
        row1_grid = Table.grid(expand=True, padding=(0, 1))
        row1_grid.add_column(ratio=4)
        row1_grid.add_column(ratio=4)
        row1_grid.add_column(ratio=4)

        # Panel 1: System Monitor
        p1_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p1_table.add_column("K", style="bold cyan", width=10)
        p1_table.add_column("V", style="white")

        cpu_col = "red" if self.state.cpu_percent > 85 else ("yellow" if self.state.cpu_percent > 70 else "green")
        ram_col = "red" if self.state.ram_percent > 85 else ("yellow" if self.state.ram_percent > 75 else "green")
        disk_col = "red" if self.state.disk_percent > 90 else ("yellow" if self.state.disk_percent > 75 else "green")
        p1_table.add_row("CPU Load", f"[{cpu_col}]{format_bar(self.state.cpu_percent)}[/] (Δ {self.state.cpu_change:+.1f}%)")
        p1_table.add_row("RAM Usage", f"[{ram_col}]{format_bar(self.state.ram_percent)}[/] ({self.state.ram_used_mb:.0f}/{self.state.ram_total_mb:.0f}MB)")
        p1_table.add_row("Disk Space", f"[{disk_col}]{format_bar(self.state.disk_percent)}[/] ({self.state.disk_used_gb:.1f}/{self.state.disk_total_gb:.1f}GB)")
        p1_table.add_row("Active PIDs", f"{self.state.process_count} active tasks")
        p1_table.add_row("Headroom", f"Free RAM: {self.state.ram_free_mb:.0f}MB | Free Disk: {self.state.disk_free_gb:.1f}GB")
        p1_panel = Panel(p1_table, title="[bold]1. System Monitor[/bold]", border_style="cyan", padding=(0, 1))

        # Panel 2: Process Monitor & Crash Detector
        p2_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p2_table.add_column("K", style="bold magenta", width=11)
        p2_table.add_column("V", style="white")

        app_status_badge = "[bold green]ONLINE (RUNNING)[/bold green]" if self.state.app_is_running else "[bold red]STOPPED (CRASHED)[/bold red]"
        p2_table.add_row("App Name", f"{self.state.app_name}")
        p2_table.add_row("App Status", app_status_badge)
        p2_table.add_row("Active PID", f"[bold cyan]{self.state.app_pid or 'None'}[/bold cyan] (Uptime: {self.state.app_uptime:.0f}s)")
        p2_table.add_row("App Load", f"CPU: {self.state.app_cpu_percent:.1f}% | RAM: {self.state.app_memory_mb:.1f}MB ({self.state.app_memory_percent:.1f}%)")
        clean_reason = self.state.last_failure_reason
        if len(clean_reason) > 28:
            clean_reason = clean_reason[:25] + "..."
        p2_table.add_row("Last Crash", f"{self.state.last_crash_time} ({clean_reason})")
        p2_panel = Panel(p2_table, title="[bold]2. Process & Crash Detector[/bold]", border_style="magenta", padding=(0, 1))

        # Panel 3: AI Failure Predictor & Decision Engine
        p3_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p3_table.add_column("K", style="bold yellow", width=11)
        p3_table.add_column("V", style="white")

        risk_col = "red" if self.state.risk_category == "HIGH" else ("yellow" if self.state.risk_category == "MEDIUM" else "green")
        model_str = "[bold green]RandomForest[/bold green]" if self.state.model_loaded else "[bold red]UNAVAILABLE (Rule)[/bold red]"
        ts_str = f"[{self.state.prediction_timestamp}]" if self.state.prediction_timestamp != "None" else ""
        
        p3_table.add_row("Crash Risk", f"[{risk_col}]{format_bar(self.state.risk_probability)} ({self.state.risk_category})[/]")
        p3_table.add_row("AI Model", f"{model_str} {ts_str}".strip())
        
        clean_signals = self.state.warning_summary
        if len(clean_signals) > 30:
            clean_signals = clean_signals[:27] + "..."
        sig_col = "red" if self.state.risk_category == "HIGH" else ("yellow" if self.state.risk_category == "MEDIUM" else "dim")
        p3_table.add_row("Warn Signal", f"[{sig_col}]{clean_signals}[/{sig_col}]")

        dec_action = self.state.decision_action
        if dec_action == "ALERT_USER":
            dec_col = "bold red"
        elif dec_action == "WAIT_AND_RETRY":
            dec_col = "bold yellow"
        elif "RESTART" in dec_action:
            dec_col = "bold cyan"
        elif dec_action == "INVESTIGATE":
            dec_col = "bold yellow"
        else:
            dec_col = "bold green"

        p3_table.add_row("Decision", f"[{dec_col}]{dec_action}[/{dec_col}] ({self.state.decision_score * 100:.0f}%)")
        short_reason = self.state.decision_reason
        if len(short_reason) > 30:
            short_reason = short_reason[:27] + "..."
        p3_table.add_row("Rationale", f"[dim]{short_reason}[/dim]")
        p3_panel = Panel(p3_table, title="[bold]3. AI Predictor & Decision[/bold]", border_style="yellow", padding=(0, 1))

        row1_grid.add_row(p1_panel, p2_panel, p3_panel)

        # -------------------------------------------------------------
        # Row 2: 3 Fixed Panels
        # [4] Health Analyzer │ [5] Recovery Service │ [6] Subsystems Status
        # -------------------------------------------------------------
        row2_grid = Table.grid(expand=True, padding=(0, 1))
        row2_grid.add_column(ratio=4)
        row2_grid.add_column(ratio=4)
        row2_grid.add_column(ratio=4)

        # Panel 4: Health Analyzer
        p4_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p4_table.add_column("K", style="bold green", width=10)
        p4_table.add_column("V", style="white")

        health_col = "green" if self.state.health_risk_category == "HEALTHY" else ("yellow" if self.state.health_risk_category in ("WARNING", "DEGRADED") else "red")
        p4_table.add_row("Overall", f"[{health_col}][bold]{self.state.health_overall:4.1f}/100 ({self.state.health_risk_category})[/bold][/]")
        p4_table.add_row("Components", f"CPU: {self.state.health_cpu:.0f} │ RAM: {self.state.health_ram:.0f} │ Disk: {self.state.health_disk:.0f}")
        cause_col = "dim" if self.state.health_risk_category == "HEALTHY" else ("yellow" if self.state.health_risk_category in ("WARNING", "DEGRADED") else "red")
        clean_cause = self.state.health_primary_degraded_metric
        if len(clean_cause) > 20:
            clean_cause = clean_cause[:18] + ".."
        p4_table.add_row("Stability", f"Stab: {self.state.health_stability:.0f} │ Cause: [{cause_col}]{clean_cause}[/{cause_col}]")
        short_guide = self.state.health_recommendation
        if len(short_guide) > 34:
            short_guide = short_guide[:31] + "..."
        p4_table.add_row("Guidance", f"[italic]{short_guide}[/italic]")
        p4_panel = Panel(p4_table, title="[bold]4. Health Analyzer[/bold]", border_style="green", padding=(0, 1))

        # Panel 5: Recovery Service & Performance Analytics
        p5_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p5_table.add_column("K", style="bold blue", width=11)
        p5_table.add_column("V", style="white")

        old_pid_str = str(self.state.failed_pid) if self.state.failed_pid else "None"
        new_pid_str = str(self.state.app_pid) if self.state.app_pid else "None"
        clean_rec_state = self.state.recovery_state
        if len(clean_rec_state) > 28:
            clean_rec_state = clean_rec_state[:25] + "..."
        p5_table.add_row("Progress", f"[bold yellow]{clean_rec_state}[/bold yellow]")

        crashes_badge = f"{self.state.total_crashes} Flts ({self.state.repeated_crashes} Rep)"
        p5_table.add_row("PID Trans", f"Old: [dim]{old_pid_str}[/dim] -> New: [bold cyan]{new_pid_str}[/bold cyan] │ {crashes_badge}")

        tot_attempts = self.state.successful_recoveries + self.state.failed_recoveries
        p5_table.add_row(
            "Attempts",
            f"Tot: {tot_attempts} │ [green]{self.state.successful_recoveries} OK[/green] / [red]{self.state.failed_recoveries} Fail[/red] ([bold green]{self.state.recovery_success_rate:.0f}%[/bold green])",
        )

        # Durations min/max/avg
        if self.state.successful_recoveries > 0 or self.state.failed_recoveries > 0 or self.state.recovery_avg_duration > 0:
            p5_table.add_row(
                "Latency",
                f"Avg: {self.state.recovery_avg_duration:.2f}s │ Min: {self.state.recovery_fastest_duration:.2f}s │ Max: {self.state.recovery_slowest_duration:.2f}s",
            )
        else:
            p5_table.add_row("Latency", "Avg: 0.00s │ Min: 0.00s │ Max: 0.00s")

        sla_pct = self.state.sla_compliance_rate
        sla_col = "green" if sla_pct >= 80.0 else ("yellow" if sla_pct >= 50.0 else "red")

        trend_str = self.state.recovery_trend
        if "IMPROVING" in trend_str:
            trend_col = "bold green"
        elif "WORSENING" in trend_str:
            trend_col = "bold red"
        elif "STABLE" in trend_str:
            trend_col = "bold yellow"
        else:
            trend_col = "dim"

        p5_table.add_row(
            "SLA & Trend",
            f"[{sla_col}]{sla_pct:.0f}% Met[/{sla_col}] ({self.state.sla_target_sec:.1f}s) │ [{trend_col}]{trend_str}[/{trend_col}]",
        )

        p5_panel = Panel(p5_table, title="[bold]5. Recovery & Performance Analytics[/bold]", border_style="blue", padding=(0, 1))

        # Panel 6: Subsystems Status (2 columns x 4 rows)
        p6_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        p6_table.add_column("M1", style="cyan", ratio=1)
        p6_table.add_column("S1", ratio=1)
        p6_table.add_column("M2", style="cyan", ratio=1)
        p6_table.add_column("S2", ratio=1)

        mods = list(self.state.module_status.items())
        for i in range(0, len(mods), 2):
            m1_name, m1_st = mods[i]
            m2_name, m2_st = mods[i + 1] if i + 1 < len(mods) else ("", "")
            s1_col = "[green]● ON[/green]" if m1_st == "ONLINE" else f"[red]● {m1_st[:3]}[/red]"
            s2_col = "[green]● ON[/green]" if m2_st == "ONLINE" else f"[red]● {m2_st[:3]}[/red]"
            p6_table.add_row(m1_name[:10], s1_col, m2_name[:10], s2_col)

        p6_panel = Panel(p6_table, title="[bold]6. System Status[/bold]", border_style="white", padding=(0, 1))

        row2_grid.add_row(p4_panel, p5_panel, p6_panel)

        # -------------------------------------------------------------
        # Row 3: Panel 7: Recovery History & Live Event Timeline
        # -------------------------------------------------------------
        p7_grid = Table.grid(expand=True, padding=(0, 0))
        p7_grid.add_column(ratio=1)

        rec_hist = self.state.recent_recoveries
        if rec_hist:
            hist_table = Table(
                box=None,
                show_header=True,
                header_style="bold cyan",
                expand=True,
                padding=(0, 1),
            )
            hist_table.add_column("Time", style="dim white", width=9)
            hist_table.add_column("App", style="white", width=18)
            hist_table.add_column("PID Trans", style="cyan", width=16)
            hist_table.add_column("Duration", style="yellow", width=14)
            hist_table.add_column("Outcome", width=10)
            hist_table.add_column("SLA", width=10)

            for rec in rec_hist[-MAX_RECENT_RECOVERIES_DISPLAY:]:
                t_str = rec.get("timestamp", "").split()[-1] if rec.get("timestamp") else "None"
                app_n = str(rec.get("application_name", "dummy_app"))[:17]
                o_pid = str(rec.get("old_pid") if rec.get("old_pid") is not None else "-")
                n_pid = str(rec.get("new_pid") if rec.get("new_pid") is not None else "-")
                pid_t = f"{o_pid} -> {n_pid}"
                try:
                    d_sec = float(rec.get("recovery_duration_sec", 0.0))
                except (ValueError, TypeError):
                    d_sec = 0.0
                d_ms = rec.get("recovery_duration_ms", round(d_sec * 1000.0, 1))
                dur_str = f"{d_sec:.2f}s ({d_ms:.0f}ms)"
                st = str(rec.get("recovery_status", "UNKNOWN")).upper()
                st_str = "[bold green]SUCCESS[/bold green]" if st == "SUCCESS" else f"[bold red]{st}[/bold red]"
                is_met = bool(rec.get("sla_met", False))
                sla_str = "[bold green]● MET[/bold green]" if is_met else "[bold red]▲ BREACH[/bold red]"

                hist_table.add_row(t_str, app_n, pid_t, dur_str, st_str, sla_str)

            p7_grid.add_row(hist_table)
            p7_grid.add_row(Text("─" * 70, style="dim"))

        events = self.state.get_events()
        event_table = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        event_table.add_column("Event", style="white")

        if not events:
            event_table.add_row("[dim]No events logged yet.[/dim]")
        else:
            num_events_to_show = 2 if rec_hist else 4
            for ev in events[-num_events_to_show:]:
                if "[CRASH" in ev or "[FATAL" in ev or "[ERROR" in ev:
                    event_table.add_row(f"[bold red]{ev}[/bold red]")
                elif "[DECISION" in ev:
                    event_table.add_row(f"[bold yellow]{ev}[/bold yellow]")
                elif "Recovery SUCCESS" in ev or "started with PID" in ev:
                    event_table.add_row(f"[bold green]{ev}[/bold green]")
                else:
                    event_table.add_row(f"[cyan]{ev}[/cyan]")

        p7_grid.add_row(event_table)

        p7_panel = Panel(
            p7_grid,
            title="[bold]7. Recovery History & Live Event Timeline (Telemetry & SLA Stream)[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )

        # -------------------------------------------------------------
        # Footer (Permanent Instructions)
        # -------------------------------------------------------------
        footer_text = Text()
        footer_text.append("Tabs: ", style="bold white")
        footer_text.append("[1] Overview", style="bold cyan")
        footer_text.append(" │ ", style="dim")
        footer_text.append("[2] OS Lab", style="bold yellow")
        footer_text.append(" │ Commands: ", style="bold white")
        footer_text.append("touch data/crash.trigger", style="bold yellow")
        footer_text.append(" │ ", style="dim white")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" (quit)", style="dim white")

        return Group(header_panel, row1_grid, row2_grid, p7_panel, footer_text)

    def _render_plain(self) -> None:
        """ANSI in-place fallback without screen clearing to prevent flashing."""
        uptime_str = self._get_uptime_str()
        now_str = datetime.now().strftime("%H:%M:%S")

        tot_attempts = self.state.successful_recoveries + self.state.failed_recoveries
        lines = [
            "=" * 80,
            f" HEALOS 2.0 │ Uptime: {uptime_str} │ Time: {now_str} │ App: {'ONLINE' if self.state.app_is_running else 'CRASHED'}",
            "=" * 80,
            f"[1. SYSTEM]  CPU: {format_bar(self.state.cpu_percent)} │ RAM: {format_bar(self.state.ram_percent)} │ Tasks: {self.state.process_count}",
            f"[2. PROCESS] App: {self.state.app_name} │ PID: {self.state.app_pid} (Old: {self.state.failed_pid}) │ Uptime: {self.state.app_uptime:.0f}s",
            f"[3. AI PRED] Risk: {self.state.risk_category} ({self.state.risk_probability:.1f}%) │ Action: {self.state.decision_action}",
            f"[4. HEALTH]  Score: {self.state.health_overall:.1f}/100 ({self.state.health_risk_category}) │ Stability: {self.state.health_stability:.0f}",
            f"[5. PERFORMANCE] Crashes: {self.state.total_crashes} ({self.state.repeated_crashes} Rep) │ Att: {tot_attempts} ({self.state.successful_recoveries} OK/{self.state.failed_recoveries} Fail, {self.state.recovery_success_rate:.0f}%) │ Lat: Avg {self.state.recovery_avg_duration:.2f}s (Min:{self.state.recovery_fastest_duration:.2f}s, Max:{self.state.recovery_slowest_duration:.2f}s) │ SLA: {self.state.sla_compliance_rate:.0f}% │ Trend: {self.state.recovery_trend}",
            "-" * 80,
            "[7. TIMELINE]",
        ]
        for ev in self.state.get_events()[-4:]:
            lines.append(f"  {ev}")
        lines.append("-" * 80)
        lines.append("Trigger demo crash: touch data/crash.trigger │ Exit: Ctrl+C")

        # In-place repositioning using ANSI escape \033[H (cursor home)
        output = "\033[H" + "\n".join(lines) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()
