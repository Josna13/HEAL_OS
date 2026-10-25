"""
HealOS 2.0 - Application Crash Detector
Monitors target application process liveness, differentiates between
deliberate administrative shutdowns and unexpected failures, prevents duplicate
crash notifications, and dispatches failure events to the recovery controller.
Includes active surveillance for data/crash.trigger to ensure immediate (<200ms) detection.
"""

import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Set
import psutil

from config import CRASH_DETECTOR_INTERVAL, CRASH_TRIGGER_FILE
from logger.healos_logger import get_system_logger, get_error_logger, log_event


@dataclass
class CrashEvent:
    """Encapsulates telemetry regarding a detected process termination."""
    pid: int
    timestamp: str
    exit_code: Optional[int]
    failure_reason: str
    is_unexpected: bool
    detected_at: float


class CrashDetector(threading.Thread):
    """
    Continuous detector for application failures and ungraceful exits.
    """

    def __init__(
        self,
        interval: float = CRASH_DETECTOR_INTERVAL,
        on_crash_callback: Optional[Callable[[CrashEvent], None]] = None,
    ):
        super().__init__(name="CrashDetectorThread", daemon=True)
        self.interval = interval
        self.on_crash_callback = on_crash_callback
        self.logger = get_system_logger()

        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Tracked process reference
        self.target_pid: Optional[int] = None
        self.target_popen = None  # subprocess.Popen instance if launched internally
        self.intentional_stop: bool = False

        # Set of PIDs that have already triggered a crash event (prevents duplicates)
        self._processed_crashes: Set[int] = set()

    def set_target(self, pid: Optional[int], popen_obj=None) -> None:
        """Assigns or updates the application process under surveillance."""
        with self._lock:
            self.target_pid = pid
            self.target_popen = popen_obj
            self.intentional_stop = False
            if pid:
                self.logger.info(f"CrashDetector monitoring target PID: {pid}")

    def mark_intentional_shutdown(self) -> None:
        """Informs the detector that the application is intentionally being stopped."""
        with self._lock:
            self.intentional_stop = True

    def stop(self) -> None:
        """Stops the monitoring thread."""
        self._stop_event.set()

    def check_liveness(self) -> Optional[CrashEvent]:
        """
        Single-pass liveness assessment. Returns a CrashEvent if an unexpected
        termination is detected for the first time; otherwise returns None.
        """
        with self._lock:
            pid = self.target_pid
            popen = self.target_popen
            intentional = self.intentional_stop

        if pid is None:
            return None

        # Check if already processed to prevent duplicate alerts
        if pid in self._processed_crashes:
            return None

        # Proactive trigger file check: if data/crash.trigger exists, ensure process is terminated
        try:
            if CRASH_TRIGGER_FILE.exists() and not intentional:
                self.logger.info(f"CrashDetector observed crash trigger file: {CRASH_TRIGGER_FILE}")
                try:
                    CRASH_TRIGGER_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
                # If popen is available, terminate it immediately
                if popen is not None and popen.poll() is None:
                    try:
                        popen.terminate()
                        popen.wait(timeout=0.3)
                    except Exception:
                        try:
                            popen.kill()
                        except Exception:
                            pass
        except Exception:
            pass

        is_dead = False
        exit_code: Optional[int] = None

        # Method 1: Subprocess Popen inspection if available
        if popen is not None:
            ret = popen.poll()
            if ret is not None:
                is_dead = True
                exit_code = ret

        # Method 2: System PID inspection via psutil
        if not is_dead:
            try:
                proc = psutil.Process(pid)
                if not proc.is_running() or proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                    is_dead = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                is_dead = True
            except Exception:
                pass

        if not is_dead:
            return None

        # Process has terminated
        with self._lock:
            self._processed_crashes.add(pid)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if intentional:
            self.logger.info(f"Target process PID {pid} stopped intentionally. No crash event triggered.")
            log_event(f"Process PID {pid} stopped intentionally.")
            return None

        # Classify failure reason
        if exit_code is not None:
            if exit_code == 0:
                failure_reason = f"Process PID {pid} exited with code 0 unexpectedly without intentional shutdown"
            elif exit_code == 137:
                failure_reason = f"Process PID {pid} killed with SIGKILL (Exit code 137 - likely OOM killer or external kill)"
            else:
                failure_reason = f"Process PID {pid} crashed with fatal exit code {exit_code}"
        else:
            failure_reason = f"Process PID {pid} disappeared abruptly from operating system process table"

        event = CrashEvent(
            pid=pid,
            timestamp=now_str,
            exit_code=exit_code,
            failure_reason=failure_reason,
            is_unexpected=True,
            detected_at=time.time(),
        )

        self.logger.warning(f"CRASH DETECTED: {failure_reason}")
        log_event(f"[CRASH DETECTED] {failure_reason}")

        # Dispatch callback
        if self.on_crash_callback:
            try:
                self.on_crash_callback(event)
            except Exception as e:
                get_error_logger().error(f"Error in on_crash_callback: {e}")

        return event

    def run(self) -> None:
        """Periodic background polling loop."""
        self.logger.info("Application Crash Detector thread active.")
        while not self._stop_event.is_set():
            try:
                self.check_liveness()
            except Exception as e:
                get_error_logger().error(f"Error in CrashDetector run loop: {e}")

            self._stop_event.wait(self.interval)

        self.logger.info("Application Crash Detector thread stopped.")
