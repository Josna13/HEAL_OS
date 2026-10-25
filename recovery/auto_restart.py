"""
HealOS 2.0 - Automatic Recovery Service
Coordinates target application process lifecycle, consults the AI Recovery
Decision Engine upon crash detection, implements safe restart policies with
exponential cooldowns and retry limits, measures recovery latency, tracks old vs new PIDs,
and records verifiable telemetry to logs/recovery.log and logs/dummy_app.log.
"""

import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from config import (
    DUMMY_APP_SCRIPT,
    TARGET_APP_DISPLAY_NAME,
    DUMMY_APP_LOG_FILE,
    MAX_RESTART_ATTEMPTS,
    RESTART_COOLDOWN_SECONDS,
    RETRY_DELAY_SECONDS,
    RAPID_CRASH_WINDOW_SECONDS,
    MAX_CRASHES_IN_WINDOW,
    RECOVERY_SLA_TARGET_SECONDS,
    MAX_RECOVERY_HISTORY_BUFFER,
)
from detector.crash_detector import CrashDetector, CrashEvent
from ai.decision_engine import (
    RecoveryDecisionEngine,
    ACTION_RESTART,
    ACTION_LIMITED_RETRY,
    ACTION_WAIT_RETRY,
    ACTION_ALERT_USER,
    DecisionOutput,
)
from ai.log_analyzer import LogAnalyzer
from logger.healos_logger import get_system_logger, get_error_logger, log_event
from logger.recovery_logger import RecoveryLogger
from monitor.system_monitor import get_system_stats


class AutoRestart:
    """
    Central recovery controller managing process execution, fault recovery,
    old vs new PID telemetry, and operational boundaries.
    """

    def __init__(
        self,
        app_script: Path = DUMMY_APP_SCRIPT,
        app_args: Optional[List[str]] = None,
        crash_detector: Optional[CrashDetector] = None,
        decision_engine: Optional[RecoveryDecisionEngine] = None,
        max_restart_attempts: int = MAX_RESTART_ATTEMPTS,
        retry_delay_seconds: float = RETRY_DELAY_SECONDS,
        cooldown_seconds: float = RESTART_COOLDOWN_SECONDS,
        rapid_crash_window_seconds: float = RAPID_CRASH_WINDOW_SECONDS,
        max_crashes_in_window: int = MAX_CRASHES_IN_WINDOW,
    ):
        self.app_script = app_script
        self.app_args = app_args or []
        self.crash_detector = crash_detector
        self.max_restart_attempts = int(max_restart_attempts)
        self.retry_delay_seconds = float(retry_delay_seconds)
        self.cooldown_seconds = float(cooldown_seconds)
        self.rapid_crash_window_seconds = float(rapid_crash_window_seconds)
        self.max_crashes_in_window = int(max_crashes_in_window)

        if decision_engine is not None:
            self.decision_engine = decision_engine
        else:
            self.decision_engine = RecoveryDecisionEngine(
                max_attempts=self.max_restart_attempts,
                cooldown_seconds=self.cooldown_seconds,
                retry_delay_seconds=self.retry_delay_seconds,
                max_crashes_in_window=self.max_crashes_in_window,
            )

        self.logger = get_system_logger()
        self._lock = threading.Lock()

        # Concurrency and duplicate suppression guards
        self._handled_crash_pids: Set[int] = set()
        self._recovery_in_progress: bool = False

        # Target process references
        self.process: Optional[subprocess.Popen] = None
        self.current_pid: Optional[int] = None
        self.last_failed_pid: Optional[int] = None
        self.last_recovered_pid: Optional[int] = None
        self.app_start_time: float = 0.0
        self.is_intentionally_stopped: bool = False
        self.recovery_state: str = "IDLE (Normal Monitoring)"
        self.last_crash_time: str = "None"
        self.last_failure_reason: str = "None recorded"

        # Recovery metrics and history (Session counters)
        self.total_crashes: int = 0
        self.repeated_crashes: int = 0
        self.total_restarts: int = 0
        self.successful_recoveries: int = 0
        self.failed_recoveries: int = 0
        self.last_restart_timestamp: float = 0.0
        self.crash_timestamps: List[float] = []
        self.durations: List[float] = []
        self.sla_target_sec: float = float(RECOVERY_SLA_TARGET_SECONDS)
        self.sla_met_count: int = 0
        self.recovery_history: List[Dict[str, Any]] = []

        # Last recovery telemetry report
        self.last_recovery_event: Optional[Dict[str, Any]] = None
        self.last_decision: Optional[DecisionOutput] = None

    def start_application(self) -> bool:
        """
        Launches the target application as an isolated child subprocess.
        Ensures no duplicate instances are spawned.
        Redirects output to logs/dummy_app.log to prevent pipe buffer hangs.
        """
        with self._lock:
            # Terminate existing instance if still alive
            self._ensure_existing_process_killed()

            self.is_intentionally_stopped = False
            cmd = [sys.executable, str(self.app_script)] + self.app_args

            try:
                DUMMY_APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
                log_fd = open(DUMMY_APP_LOG_FILE, "a", encoding="utf-8")

                self.logger.info(f"Launching target application: {' '.join(cmd)}")
                self.process = subprocess.Popen(
                    cmd,
                    stdout=log_fd,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                self.current_pid = self.process.pid
                self.last_recovered_pid = self.current_pid
                self.app_start_time = time.time()
                self.logger.info(f"Target application started successfully. PID: {self.current_pid}")
                log_event(f"Application {TARGET_APP_DISPLAY_NAME} started with PID {self.current_pid}")

                # Notify crash detector
                if self.crash_detector:
                    self.crash_detector.set_target(self.current_pid, self.process)

                return True
            except Exception as e:
                get_error_logger().error(f"Failed to start target application: {e}")
                log_event(f"[ERROR] Failed to start application: {e}")
                return False

    def stop_application(self) -> None:
        """
        Gracefully terminates the target application.
        Informs the detector to prevent false crash events.
        """
        with self._lock:
            self.is_intentionally_stopped = True
            if self.crash_detector:
                self.crash_detector.mark_intentional_shutdown()

            if self.process and self.process.poll() is None:
                self.logger.info(f"Stopping application PID {self.process.pid} gracefully...")
                try:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2.0)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Application did not exit in 2s, sending SIGKILL...")
                        self.process.kill()
                        self.process.wait(timeout=1.0)
                except Exception as e:
                    get_error_logger().warning(f"Error terminating process: {e}")

            self.process = None
            self.current_pid = None

    def handle_detected_crash(self, crash_event: CrashEvent) -> None:
        """
        Orchestrates recovery workflow upon receipt of an unexpected crash signal.
        Enforces mutual exclusion to prevent concurrent recoveries and duplicate events.
        """
        with self._lock:
            if self.is_intentionally_stopped:
                self.logger.info("Ignoring crash event due to intentional administrative shutdown.")
                return

            if crash_event.pid in self._handled_crash_pids:
                self.logger.warning(
                    f"Duplicate crash event for PID {crash_event.pid} suppressed. Recovery already executed."
                )
                return

            if self._recovery_in_progress:
                self.logger.warning(
                    f"Concurrent restart requested for PID {crash_event.pid} while recovery already active. Suppressing attempt."
                )
                return

            self._recovery_in_progress = True
            self._handled_crash_pids.add(crash_event.pid)

            self.total_crashes += 1
            self.last_failed_pid = crash_event.pid
            self.last_crash_time = crash_event.timestamp
            self.last_failure_reason = crash_event.failure_reason
            self.recovery_state = f"CRASH DETECTED (PID {crash_event.pid})"
            now = time.time()
            self.crash_timestamps.append(now)

            # Purge crash timestamps outside window
            cutoff = now - self.rapid_crash_window_seconds
            self.crash_timestamps = [t for t in self.crash_timestamps if t >= cutoff]
            recent_crashes_count = len(self.crash_timestamps)

            if self.total_crashes > 1 or recent_crashes_count > 1:
                self.repeated_crashes += 1

            self.logger.warning(
                f"Handling crash #{self.total_crashes} for PID {crash_event.pid}. "
                f"Recent crashes in window: {recent_crashes_count}"
            )

        try:
            # 1. Collect real-time metrics
            metrics = get_system_stats()

            # 2. Consult AI Decision Engine
            with self._lock:
                current_restarts = self.total_restarts
                last_restart_time = self.last_restart_timestamp

            seconds_since_restart = (time.time() - last_restart_time) if last_restart_time > 0 else 999.0

            decision = self.decision_engine.decide(
                cpu_percent=metrics.cpu_percent,
                ram_percent=metrics.ram_percent,
                disk_percent=metrics.disk_percent,
                current_attempt=current_restarts,
                crashes_in_window=recent_crashes_count,
                failure_reason=crash_event.failure_reason,
                seconds_since_last_restart=seconds_since_restart,
            )

            with self._lock:
                self.last_decision = decision
                self.recovery_state = f"DECISION: {decision.action}"

            log_event(f"[DECISION] Action={decision.action} | Reason={decision.reason}")
            self.logger.info(f"Recovery Decision: Action={decision.action} Score={decision.confidence_score:.2f}")

            # 3. Execute Selected Safe Action
            if decision.action in (ACTION_RESTART, ACTION_LIMITED_RETRY):
                self._execute_application_restart(crash_event, decision)
            elif decision.action == ACTION_WAIT_RETRY:
                self.logger.info(f"WAIT_AND_RETRY: Cooling down {decision.delay_seconds}s before attempting restart...")
                log_event(f"WAIT_AND_RETRY: Cooling down {decision.delay_seconds}s before restart attempt...")
                with self._lock:
                    self.recovery_state = f"COOLDOWN ({decision.delay_seconds}s)"
                if decision.delay_seconds > 0:
                    time.sleep(decision.delay_seconds)
                self._execute_application_restart(crash_event, decision, delay_override=0.0)
            elif decision.action == ACTION_ALERT_USER:
                self.logger.critical(f"ALERT_USER: System halting automated recovery. {decision.reason}")
                log_event(f"[CRITICAL ALERT] Auto-restart halted. Admin intervention required.")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with self._lock:
                    self.failed_recoveries += 1
                    self.recovery_state = "HALTED (ALERT_USER - Limit Reached)"
                    self.last_recovery_event = RecoveryLogger.log_recovery(
                        app_name=TARGET_APP_DISPLAY_NAME,
                        failure_reason=crash_event.failure_reason,
                        recovery_action=decision.action,
                        attempt_number=self.total_restarts + 1,
                        duration_seconds=0.0,
                        status="FAILED",
                        decision_reason=decision.reason,
                        decision_score=decision.confidence_score,
                        extra_metadata={"old_pid": crash_event.pid, "new_pid": None},
                        old_pid=crash_event.pid,
                        new_pid=None,
                        crash_detection_time=crash_event.timestamp,
                        recovery_start_time=now_str,
                        recovery_completion_time=now_str,
                        sla_target_sec=self.sla_target_sec,
                        sla_met=False,
                    )
                    self.recovery_history.append(self.last_recovery_event)
                    if len(self.recovery_history) > MAX_RECOVERY_HISTORY_BUFFER:
                        self.recovery_history.pop(0)
        finally:
            with self._lock:
                self._recovery_in_progress = False

    def _execute_application_restart(
        self,
        crash_event: CrashEvent,
        decision: DecisionOutput,
        delay_override: Optional[float] = None,
    ) -> None:
        """Applies restart with execution timing, PID transition tracking, and outcome verification."""
        t_start = time.perf_counter()
        now_start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self.total_restarts += 1
            attempt_num = self.total_restarts
            self.last_restart_timestamp = time.time()
            self.recovery_state = f"RESTARTING (Attempt #{attempt_num})..."

        delay = delay_override if delay_override is not None else decision.delay_seconds
        if delay > 0:
            time.sleep(delay)

        success = self.start_application()

        # Confirm restarted application is running
        is_confirmed_alive = False
        with self._lock:
            if success and self.process and self.process.poll() is None:
                is_confirmed_alive = True

        t_end = time.perf_counter()
        now_end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = round(max(0.0, t_end - t_start), 3)

        status = "SUCCESS" if is_confirmed_alive else "FAILED"
        new_pid = self.current_pid if is_confirmed_alive else None
        is_sla_met = bool(status == "SUCCESS" and duration <= self.sla_target_sec)

        downtime_sec = round(max(0.001, time.time() - crash_event.detected_at), 3) if getattr(crash_event, "detected_at", None) else duration
        detection_time_str = datetime.fromtimestamp(crash_event.detected_at).strftime("%Y-%m-%d %H:%M:%S") if getattr(crash_event, "detected_at", None) else crash_event.timestamp
        actual_exit_code = crash_event.exit_code if crash_event.exit_code is not None else 1

        with self._lock:
            if is_confirmed_alive:
                self.successful_recoveries += 1
                self.last_recovered_pid = new_pid
                self.durations.append(duration)
                if is_sla_met:
                    self.sla_met_count += 1
                sla_tag = "SLA MET" if is_sla_met else "SLA BREACH"
                self.recovery_state = f"RECOVERED (PID {new_pid}, {duration}s [{sla_tag}])"
            else:
                self.failed_recoveries += 1
                self.recovery_state = f"FAILED (Old PID: {crash_event.pid})"

            self.last_recovery_event = RecoveryLogger.log_recovery(
                app_name=TARGET_APP_DISPLAY_NAME,
                failure_reason=crash_event.failure_reason,
                recovery_action=decision.action,
                attempt_number=attempt_num,
                duration_seconds=duration,
                status=status,
                decision_reason=decision.reason,
                decision_score=decision.confidence_score,
                extra_metadata={
                    "old_pid": crash_event.pid,
                    "new_pid": new_pid,
                    "exit_code": actual_exit_code,
                    "crash_time": crash_event.timestamp,
                    "detection_time": detection_time_str,
                    "recovery_start": now_start_str,
                    "restart_time": now_end_str,
                    "downtime_sec": downtime_sec,
                    "recovery_duration_sec": duration,
                    "final_status": "RUNNING" if is_confirmed_alive else "RECOVERY FAILED",
                },
                old_pid=crash_event.pid,
                new_pid=new_pid,
                crash_detection_time=crash_event.timestamp,
                recovery_start_time=now_start_str,
                recovery_completion_time=now_end_str,
                sla_target_sec=self.sla_target_sec,
                sla_met=is_sla_met,
            )
            self.recovery_history.append(self.last_recovery_event)
            if len(self.recovery_history) > MAX_RECOVERY_HISTORY_BUFFER:
                self.recovery_history.pop(0)

        sla_log_str = "● MET" if is_sla_met else "▲ BREACH"
        log_event(
            f"Recovery {status}: Old PID={crash_event.pid} -> New PID={new_pid} "
            f"(Attempt #{attempt_num}, SLA={duration}s [{sla_log_str}])"
        )

        # After 4 seconds of display, gently revert recovery_state back to IDLE
        def revert_state():
            time.sleep(4.0)
            with self._lock:
                if self.process and self.process.poll() is None:
                    self.recovery_state = "IDLE (Normal Monitoring)"
        threading.Thread(target=revert_state, daemon=True).start()

    def _ensure_existing_process_killed(self) -> None:
        """Internal helper to ensure any dangling process instance is cleanly closed."""
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
                self.process.wait(timeout=1.0)
            except Exception:
                pass
        self.process = None
        self.current_pid = None

    def get_status_summary(self) -> Dict[str, Any]:
        """Provides a thread-safe snapshot of recovery operations and SLA telemetry."""
        with self._lock:
            is_alive = False
            if self.process and self.process.poll() is None:
                is_alive = True

            uptime = round(time.time() - self.app_start_time, 1) if is_alive and self.app_start_time else 0.0
            total_attempts = self.successful_recoveries + self.failed_recoveries
            success_rate = (self.successful_recoveries / total_attempts * 100.0) if total_attempts > 0 else 100.0

            if self.durations:
                avg_dur = round(sum(self.durations) / len(self.durations), 3)
                fastest_dur = round(min(self.durations), 3)
                slowest_dur = round(max(self.durations), 3)
            else:
                avg_dur = 0.0
                fastest_dur = 0.0
                slowest_dur = 0.0

            sla_compliance = (self.sla_met_count / total_attempts * 100.0) if total_attempts > 0 else 100.0
            perf_trend, perf_trend_details = LogAnalyzer.compute_performance_trend(self.durations)

            return {
                "is_running": is_alive,
                "current_pid": self.current_pid,
                "failed_pid": self.last_failed_pid,
                "new_pid": self.last_recovered_pid,
                "app_uptime": uptime,
                "last_crash_time": self.last_crash_time,
                "last_failure_reason": self.last_failure_reason,
                "recovery_state": self.recovery_state,
                "total_crashes": self.total_crashes,
                "repeated_crashes": self.repeated_crashes,
                "total_attempts": total_attempts,
                "total_restarts": self.total_restarts,
                "successful_recoveries": self.successful_recoveries,
                "failed_recoveries": self.failed_recoveries,
                "recovery_failures": self.failed_recoveries,
                "success_rate": round(success_rate, 1),
                "sla_target_sec": self.sla_target_sec,
                "sla_met_count": self.sla_met_count,
                "sla_compliance_rate": round(sla_compliance, 1),
                "avg_duration_sec": avg_dur,
                "fastest_duration_sec": fastest_dur,
                "slowest_duration_sec": slowest_dur,
                "min_duration_sec": fastest_dur,
                "max_duration_sec": slowest_dur,
                "performance_trend": perf_trend,
                "performance_trend_details": perf_trend_details,
                "last_recovery": self.last_recovery_event,
                "last_decision": self.last_decision.to_dict() if self.last_decision else None,
                "recent_recoveries": list(self.recovery_history),
            }
