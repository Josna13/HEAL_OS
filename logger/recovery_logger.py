"""
HealOS 2.0 - Recovery Event Logger
Records structured recovery operations into logs/recovery.log.
Ensures thread-safe logging and guarantees each recovery operation
is recorded exactly once with complete decision and performance telemetry.
"""

import json
import logging
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional

from config import (
    RECOVERY_LOG_FILE,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    RECOVERY_SLA_TARGET_SECONDS,
)
from logger.healos_logger import get_system_logger

_RECOVERY_LOGGER_LOCK = threading.Lock()
_RECOVERY_LOGGER_INITIALIZED = False


def _get_raw_recovery_logger() -> logging.Logger:
    """Configures internal file logger for recovery events."""
    global _RECOVERY_LOGGER_INITIALIZED
    logger = logging.getLogger("healos.recovery_file")
    logger.setLevel(logging.INFO)

    with _RECOVERY_LOGGER_LOCK:
        if not _RECOVERY_LOGGER_INITIALIZED:
            RECOVERY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                filename=str(RECOVERY_LOG_FILE),
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            # Use raw message format so structured JSON lines are clean
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.handlers.clear()
            logger.addHandler(handler)
            logger.propagate = False
            _RECOVERY_LOGGER_INITIALIZED = True

    return logger


def close_recovery_logger() -> None:
    """Closes all handlers on the recovery file logger to release file locks."""
    global _RECOVERY_LOGGER_INITIALIZED
    with _RECOVERY_LOGGER_LOCK:
        logger = logging.getLogger("healos.recovery_file")
        for h in list(logger.handlers):
            h.close()
            logger.removeHandler(h)
        _RECOVERY_LOGGER_INITIALIZED = False


class RecoveryLogger:
    """
    Structured logger for tracking application recovery actions.
    Appends structured JSON records to recovery.log and syncs to system log.
    """

    @staticmethod
    def log_recovery(
        app_name: str,
        failure_reason: str,
        recovery_action: str,
        attempt_number: int,
        duration_seconds: float,
        status: str,
        decision_reason: str,
        decision_score: float,
        extra_metadata: Optional[Dict[str, Any]] = None,
        old_pid: Optional[int] = None,
        new_pid: Optional[int] = None,
        crash_detection_time: Optional[str] = None,
        recovery_start_time: Optional[str] = None,
        recovery_completion_time: Optional[str] = None,
        sla_target_sec: Optional[float] = None,
        sla_met: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Logs a single recovery event with complete machine-readable telemetry.

        Args:
            app_name: Name or path of the target application.
            failure_reason: Observed trigger or exit code.
            recovery_action: Action taken (e.g. RESTART_APPLICATION).
            attempt_number: 1-indexed attempt number.
            duration_seconds: Time taken to complete recovery in seconds.
            status: SUCCESS or FAILED.
            decision_reason: Human-readable explanation of why action was chosen.
            decision_score: Confidence/heuristic score (0.0 to 1.0).
            extra_metadata: Optional supplementary dictionary.
            old_pid: Failed process ID.
            new_pid: Recovered process ID (confirmed alive).
            crash_detection_time: Timestamp when fault was detected.
            recovery_start_time: Timestamp when restart procedure began.
            recovery_completion_time: Timestamp when recovery was confirmed.
            sla_target_sec: Maximum latency threshold for SLA compliance.
            sla_met: Boolean flag indicating if recovery satisfied SLA target.

        Returns:
            The structured dictionary written to logs/recovery.log.
        """
        now_dt = datetime.now()
        target_sla = float(sla_target_sec) if sla_target_sec is not None else float(RECOVERY_SLA_TARGET_SECONDS)
        clean_status = status.upper()

        # Extract PIDs from extra_metadata if not passed as dedicated arguments
        if old_pid is None and extra_metadata:
            old_pid = extra_metadata.get("old_pid")
        if new_pid is None and extra_metadata:
            new_pid = extra_metadata.get("new_pid")

        dur_sec = max(0.0, float(duration_seconds))
        dur_ms = round(dur_sec * 1000.0, 2)

        if sla_met is None:
            is_sla_met = bool(clean_status == "SUCCESS" and dur_sec <= target_sla)
        else:
            is_sla_met = bool(sla_met)

        record: Dict[str, Any] = {
            "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "iso_timestamp": now_dt.isoformat(),
            "application_name": app_name,
            "old_pid": old_pid,
            "new_pid": new_pid,
            "crash_detection_time": crash_detection_time or "None",
            "recovery_start_time": recovery_start_time or "None",
            "recovery_completion_time": recovery_completion_time or "None",
            "recovery_duration_sec": round(dur_sec, 4),
            "recovery_duration_ms": dur_ms,
            "restart_attempt": int(attempt_number),
            "attempt_number": int(attempt_number),
            "recovery_status": clean_status,
            "sla_target_sec": round(target_sla, 2),
            "sla_target_ms": round(target_sla * 1000.0, 1),
            "sla_met": is_sla_met,
            "failure_reason": failure_reason,
            "recovery_action": recovery_action,
            "decision_explanation": decision_reason,
            "decision_score": round(float(decision_score), 4),
        }

        if extra_metadata:
            record["metadata"] = extra_metadata

        json_line = json.dumps(record)

        # Thread-safe write to logs/recovery.log
        raw_logger = _get_raw_recovery_logger()
        with _RECOVERY_LOGGER_LOCK:
            raw_logger.info(json_line)

        # Also emit a summary entry to system.log for operator convenience
        sys_logger = get_system_logger()
        sla_flag = "SLA_MET" if is_sla_met else "SLA_BREACH"
        sys_logger.info(
            f"RECOVERY RECORD: app={app_name} action={recovery_action} "
            f"attempt={attempt_number} status={clean_status} duration={dur_sec:.3f}s ({dur_ms:.1f}ms) "
            f"[{sla_flag}] old_pid={old_pid} new_pid={new_pid} "
            f"score={decision_score:.2f} reason='{decision_reason}'"
        )

        return record
