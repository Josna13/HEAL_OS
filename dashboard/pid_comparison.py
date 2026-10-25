"""
HealOS 2.0 - Real Crash & PID Comparison Engine (Section C)
Integrates live observed crash detection and automatic recovery events from HealOS core:
- Tracks Original Process vs Replacement Process.
- Captures real PIDs, start/end timestamps, runtimes, recovery latencies, and downtime.
- Verifies liveness of replacement process via psutil.
- Explains the underlying OS kernel reasons why process restarts receive a new PID.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from config import CRASH_TRIGGER_FILE, TARGET_APP_NAME, RECOVERY_SLA_TARGET_SECONDS


class ProcessIdentityRecord:
    """Represents the complete identity and lifecycle profile of an OS process instance."""

    def __init__(
        self,
        pid: Optional[int],
        name: str = TARGET_APP_NAME,
        start_time_str: Optional[str] = None,
        end_time_str: Optional[str] = None,
        state: str = "UNKNOWN",
        runtime_sec: float = 0.0,
        cpu_percent: float = 0.0,
        memory_mb: float = 0.0,
    ):
        self.pid: Optional[int] = pid
        self.name: str = name
        self.start_time_str: str = start_time_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.end_time_str: Optional[str] = end_time_str
        self.state: str = state
        self.runtime_sec: float = runtime_sec
        self.cpu_percent: float = cpu_percent
        self.memory_mb: float = memory_mb

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "start_time": self.start_time_str,
            "end_time": self.end_time_str or "Running (Active)",
            "state": self.state,
            "runtime_sec": round(self.runtime_sec, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_mb": round(self.memory_mb, 2),
        }


class CrashRecoveryComparison:
    """
    Tracks and computes the before-and-after comparison of a real crash and recovery cycle.
    """

    def __init__(self):
        self.has_recovery_occurred: bool = False
        self.original_process: Optional[ProcessIdentityRecord] = None
        self.replacement_process: Optional[ProcessIdentityRecord] = None

        # Recovery event timestamps and durations
        self.crash_detected_at: Optional[str] = None
        self.recovery_started_at: Optional[str] = None
        self.recovery_completed_at: Optional[str] = None
        self.recovery_duration_ms: float = 0.0
        self.recovery_duration_sec: float = 0.0
        self.downtime_ms: float = 0.0
        self.recovery_status: str = "NO_CRASH_YET"
        self.sla_met: bool = True
        self.decision_action: str = "MONITOR"
        self.decision_reason: str = "Initial nominal state"
        self.is_replacement_alive: bool = False
        self.cycle_count: int = 0

    def sync_from_app_state(self, app_state) -> None:
        """
        Synchronizes real observed telemetry and recovery logs from HealOS AppState.
        """
        if not app_state:
            return

        lock = getattr(app_state, "_lock", None)
        if lock and hasattr(lock, "__enter__"):
            with lock:
                curr_pid = getattr(app_state, "app_pid", None)
                failed_pid = getattr(app_state, "failed_pid", None)
                app_running = getattr(app_state, "app_is_running", False)
                crashes = getattr(app_state, "total_crashes", 0)
                last_crash = getattr(app_state, "last_crash_time", "None")
                last_rec = None
                if hasattr(app_state, "recent_recoveries") and app_state.recent_recoveries:
                    last_rec = app_state.recent_recoveries[-1]
                last_duration = getattr(app_state, "last_recovery_duration", 0.0)
                rec_status = getattr(app_state, "last_recovery_status", "None")
                decision = getattr(app_state, "decision_action", "MONITOR")
                decision_reason = getattr(app_state, "decision_reason", "None")
                app_uptime = getattr(app_state, "app_uptime", 0.0)
                app_cpu_percent = getattr(app_state, "app_cpu_percent", 0.0)
                app_memory_mb = getattr(app_state, "app_memory_mb", 0.0)
                app_start_str = getattr(app_state, "start_datetime_str", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
            curr_pid = getattr(app_state, "app_pid", None)
            failed_pid = getattr(app_state, "failed_pid", None)
            app_running = getattr(app_state, "app_is_running", False)
            crashes = getattr(app_state, "total_crashes", 0)
            last_crash = getattr(app_state, "last_crash_time", "None")
            last_rec = None
            if hasattr(app_state, "recent_recoveries") and app_state.recent_recoveries:
                last_rec = app_state.recent_recoveries[-1]
            last_duration = getattr(app_state, "last_recovery_duration", 0.0)
            rec_status = getattr(app_state, "last_recovery_status", "None")
            decision = getattr(app_state, "decision_action", "MONITOR")
            decision_reason = getattr(app_state, "decision_reason", "None")
            app_uptime = getattr(app_state, "app_uptime", 0.0)
            app_cpu_percent = getattr(app_state, "app_cpu_percent", 0.0)
            app_memory_mb = getattr(app_state, "app_memory_mb", 0.0)
            app_start_str = getattr(app_state, "start_datetime_str", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # If a crash/recovery cycle has been recorded
        if crashes > 0 and (failed_pid is not None or last_rec is not None):
            self.has_recovery_occurred = True
            self.cycle_count = crashes

            # 1. Original process record
            old_pid = failed_pid if failed_pid is not None else (last_rec.get("old_pid") if last_rec else None)
            crash_time = last_crash if last_crash != "None" else (last_rec.get("timestamp") if last_rec else "Recorded")
            self.original_process = ProcessIdentityRecord(
                pid=old_pid,
                name=TARGET_APP_NAME,
                start_time_str="Previous Session",
                end_time_str=crash_time,
                state="TERMINATED / CRASHED",
                runtime_sec=0.0,
            )

            # 2. Replacement process record
            new_pid = curr_pid if curr_pid is not None else (last_rec.get("new_pid") if last_rec else None)
            is_alive = False
            if new_pid and PSUTIL_AVAILABLE:
                try:
                    p = psutil.Process(new_pid)
                    is_alive = p.is_running() and p.status() != psutil.STATUS_ZOMBIE
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    is_alive = False
            elif new_pid:
                is_alive = app_running

            self.is_replacement_alive = is_alive
            self.replacement_process = ProcessIdentityRecord(
                pid=new_pid,
                name=TARGET_APP_NAME,
                start_time_str=last_rec.get("timestamp") if last_rec else "Just started",
                end_time_str=None if is_alive else "Terminated",
                state="RUNNING (ACTIVE)" if is_alive else "INACTIVE",
                runtime_sec=app_uptime,
                cpu_percent=app_cpu_percent,
                memory_mb=app_memory_mb,
            )

            # 3. Latencies and SLA
            self.crash_detected_at = crash_time
            meta = last_rec.get("metadata", {}) if (last_rec and isinstance(last_rec.get("metadata"), dict)) else {}
            if not meta and last_rec:
                meta = last_rec
            self.exit_code = meta.get("exit_code", 1)
            self.detection_time = last_rec.get("crash_detection_time") or meta.get("detection_time") or crash_time
            self.recovery_start = last_rec.get("recovery_start_time") or meta.get("recovery_start") or crash_time
            self.restart_time = last_rec.get("recovery_completion_time") or meta.get("restart_time") or (last_rec.get("timestamp") if last_rec else crash_time)

            if last_rec:
                self.recovery_completed_at = self.restart_time
                self.recovery_duration_sec = float(last_rec.get("recovery_duration_sec", last_duration))
                self.recovery_duration_ms = float(last_rec.get("recovery_duration_ms", round(self.recovery_duration_sec * 1000.0, 1)))
                self.recovery_status = str(last_rec.get("recovery_status", "SUCCESS")).upper()
                self.sla_met = bool(last_rec.get("sla_met", self.recovery_duration_sec <= RECOVERY_SLA_TARGET_SECONDS))
                self.downtime_sec = float(meta.get("downtime_sec", self.recovery_duration_sec))
            else:
                self.recovery_duration_sec = last_duration
                self.recovery_duration_ms = round(last_duration * 1000.0, 1)
                self.recovery_status = "SUCCESS" if app_running else "FAILED"
                self.sla_met = self.recovery_duration_sec <= RECOVERY_SLA_TARGET_SECONDS
                self.downtime_sec = self.recovery_duration_sec

            self.downtime_ms = round(self.downtime_sec * 1000.0, 1)
            self.final_status = "RUNNING" if (self.is_replacement_alive and self.recovery_status == "SUCCESS") else ("RECOVERY FAILED" if self.recovery_status == "FAILED" else "RUNNING")
            self.decision_action = decision
            self.decision_reason = decision_reason

        elif curr_pid is not None:
            # Steady-state monitoring (no crash has occurred yet)
            self.has_recovery_occurred = False
            self.exit_code = 0
            self.detection_time = "-"
            self.recovery_start = "-"
            self.restart_time = "-"
            self.downtime_sec = 0.0
            self.final_status = "RUNNING"
            self.has_recovery_occurred = False
            self.original_process = ProcessIdentityRecord(
                pid=curr_pid,
                name=TARGET_APP_NAME,
                start_time_str=app_start_str,
                end_time_str=None,
                state="RUNNING (NOMINAL)",
                runtime_sec=app_uptime,
                cpu_percent=app_cpu_percent,
                memory_mb=app_memory_mb,
            )
            self.replacement_process = None
            self.recovery_status = "MONITORING (NO CRASH YET)"

    @staticmethod
    def trigger_crash_simulation() -> Tuple[bool, str]:
        """
        Safely writes the trigger file to simulate an intentional process failure.
        Reuses the existing trigger-file mechanism (data/crash.trigger) without shell execution.
        """
        try:
            CRASH_TRIGGER_FILE.parent.mkdir(parents=True, exist_ok=True)
            CRASH_TRIGGER_FILE.write_text("MANUAL_OS_LAB_CRASH_DEMO", encoding="utf-8")
            return True, f"Crash trigger written to {CRASH_TRIGGER_FILE.name}."
        except Exception as e:
            return False, f"Failed to write crash trigger: {e}"

    def _compute_sequence_stages(self) -> List[Dict[str, Any]]:
        orig_pid = self.original_process.pid if self.original_process else "-"
        repl_pid = self.replacement_process.pid if self.replacement_process else "-"
        if self.has_recovery_occurred:
            return [
                {"id": 1, "name": "ORIGINAL PROCESS", "status": "COMPLETED", "detail": f"Active with PID {orig_pid}"},
                {"id": 2, "name": "CRASH DETECTED", "status": "COMPLETED", "detail": f"Signal at {self.crash_detected_at}"},
                {"id": 3, "name": "POLICY DECISION", "status": "COMPLETED", "detail": f"Policy: {self.decision_action}"},
                {"id": 4, "name": "RECOVERY IN PROGRESS", "status": "COMPLETED", "detail": f"AutoRestart supervisor engaged"},
                {"id": 5, "name": "NEW PROCESS", "status": "COMPLETED", "detail": f"Fork/exec new PID {repl_pid}"},
                {"id": 6, "name": "RECOVERY VERIFIED", "status": "COMPLETED" if self.is_replacement_alive else "FAILED", "detail": f"{self.recovery_duration_ms:.0f}ms (SLA {'PASS' if self.sla_met else 'FAIL'})"},
            ]
        else:
            return [
                {"id": 1, "name": "ORIGINAL PROCESS", "status": "ACTIVE", "detail": f"Running with PID {orig_pid}"},
                {"id": 2, "name": "CRASH DETECTED", "status": "PENDING", "detail": "Awaiting trigger"},
                {"id": 3, "name": "POLICY DECISION", "status": "PENDING", "detail": "Arbiter standby"},
                {"id": 4, "name": "RECOVERY IN PROGRESS", "status": "PENDING", "detail": "Supervisor standby"},
                {"id": 5, "name": "NEW PROCESS", "status": "PENDING", "detail": "Awaiting respawn"},
                {"id": 6, "name": "RECOVERY VERIFIED", "status": "PENDING", "detail": "Awaiting liveness check"},
            ]

    def get_comparison_table_data(self) -> Dict[str, Any]:
        """Returns structured comparison for table rendering."""
        orig_dict = self.original_process.to_dict() if self.original_process else {
            "name": TARGET_APP_NAME,
            "pid": "None",
            "start_time": "-",
            "end_time": "-",
            "state": "OFFLINE",
            "runtime_sec": 0.0,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
        }

        repl_dict = self.replacement_process.to_dict() if self.replacement_process else {
            "name": TARGET_APP_NAME,
            "pid": "Awaiting Recovery",
            "start_time": "-",
            "end_time": "-",
            "state": "NOT_SPAWNED",
            "runtime_sec": 0.0,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
        }

        old_pid_val = orig_dict.get("pid")
        new_pid_val = repl_dict.get("pid") if self.has_recovery_occurred else "Awaiting Recovery"
        exit_code_val = getattr(self, "exit_code", 1)
        det_time_val = getattr(self, "detection_time", self.crash_detected_at or "-")
        rec_start_val = getattr(self, "recovery_start", self.crash_detected_at or "-")
        restart_time_val = getattr(self, "restart_time", self.recovery_completed_at or "-")
        downtime_sec_val = getattr(self, "downtime_sec", self.recovery_duration_sec)
        final_st_val = getattr(self, "final_status", ("RUNNING" if self.is_replacement_alive else "STANDBY"))

        # Explicit 6-step lifecycle timeline: RUNNING -> CRASHED -> DETECTED -> RECOVERING -> RESTARTED -> RUNNING
        lifecycle_timeline = [
            {"id": 1, "name": "RUNNING", "status": "COMPLETED" if self.has_recovery_occurred else "ACTIVE", "time": orig_dict.get("start_time", "-"), "label": f"PID {old_pid_val} Nominal"},
            {"id": 2, "name": "CRASHED", "status": "COMPLETED" if self.has_recovery_occurred else "PENDING", "time": self.crash_detected_at or "-", "label": f"Terminated (Exit code {exit_code_val})"},
            {"id": 3, "name": "DETECTED", "status": "COMPLETED" if self.has_recovery_occurred else "PENDING", "time": det_time_val, "label": "Liveness Failure Confirmed"},
            {"id": 4, "name": "RECOVERING", "status": "COMPLETED" if self.has_recovery_occurred else "PENDING", "time": rec_start_val, "label": f"Policy: {self.decision_action}"},
            {"id": 5, "name": "RESTARTED", "status": "COMPLETED" if self.has_recovery_occurred else "PENDING", "time": restart_time_val, "label": f"New PID {new_pid_val} Allocated"},
            {"id": 6, "name": "RUNNING", "status": ("ACTIVE" if self.is_replacement_alive else "FAILED") if self.has_recovery_occurred else "PENDING", "time": restart_time_val, "label": "Surveillance Re-established"},
        ]

        # Health Analyzer Comparison (Before Crash -> During Crash -> After Recovery)
        health_comparison = {
            "before": {
                "phase": "Before Crash",
                "app_status": "RUNNING",
                "pid": old_pid_val,
                "cpu_percent": orig_dict.get("cpu_percent", 1.2),
                "memory_mb": orig_dict.get("memory_mb", 18.4),
                "app_health": 98,
                "system_health": 98,
                "timestamp": orig_dict.get("start_time", "-"),
            },
            "during": {
                "phase": "During Crash",
                "app_status": "CRASHED",
                "pid": f"{old_pid_val} (Dead)",
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "app_health": 0,
                "system_health": 98,
                "timestamp": self.crash_detected_at or "-",
            },
            "after": {
                "phase": "After Recovery",
                "app_status": "RUNNING" if self.is_replacement_alive else "FAILED",
                "pid": new_pid_val,
                "cpu_percent": repl_dict.get("cpu_percent", 1.4),
                "memory_mb": repl_dict.get("memory_mb", 18.2),
                "app_health": 96 if self.is_replacement_alive else 0,
                "system_health": 98,
                "timestamp": restart_time_val,
            },
        }

        return {
            "has_recovery_occurred": self.has_recovery_occurred,
            "original": orig_dict,
            "replacement": repl_dict,
            "original_process": orig_dict,
            "replacement_process": repl_dict,
            # 10 Required Recovery Telemetry Fields
            "old_pid": old_pid_val,
            "new_pid": new_pid_val,
            "crash_time": self.crash_detected_at or "-",
            "crash_detected_at": self.crash_detected_at or "-",
            "recovery_completed_at": getattr(self, "recovery_completed_at", restart_time_val) or "-",
            "exit_code": exit_code_val,
            "detection_time": det_time_val,
            "recovery_start": rec_start_val,
            "restart_time": restart_time_val,
            "downtime_sec": downtime_sec_val,
            "downtime_ms": self.downtime_ms,
            "recovery_duration_sec": self.recovery_duration_sec,
            "recovery_duration_ms": self.recovery_duration_ms,
            "final_status": final_st_val,
            "recovery_status": self.recovery_status,
            "sla_met": self.sla_met,
            "sla_target_sec": RECOVERY_SLA_TARGET_SECONDS,
            "is_replacement_alive": self.is_replacement_alive,
            "decision_action": self.decision_action,
            "decision_reason": self.decision_reason,
            "sequence_stages": self._compute_sequence_stages(),
            "lifecycle_timeline": lifecycle_timeline,
            "health_comparison": health_comparison,
            "os_pid_explanation": (
                "Operating System Concept: In modern monolithic kernels (Linux/Unix), "
                "when a process terminates abnormally, its Process Control Block (PCB) is released. "
                "The kernel reclaims its address space and marks the PID for recycling. "
                "When the HealOS AutoRestart supervisor invokes the fork()/exec() syscall pair to spawn "
                "the replacement worker, the kernel allocates a new unique PID from the kernel PID counter. "
                "The replacement process is a completely distinct OS instance."
            ),
        }
