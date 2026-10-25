"""
HealOS 2.0 - AI Log Analyzer
Extracts historical telemetry from logs/recovery.log to evaluate recovery performance,
distribution of failure triggers, temporal crash frequencies, and trend trajectory.

NOTE: All statistics are derived strictly from empirical log entries.
If historical records are absent or sparse, an explicit 'insufficient data' status
is returned rather than generating synthetic metrics.
"""

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import RECOVERY_LOG_FILE, RECOVERY_SLA_TARGET_SECONDS
from logger.healos_logger import get_system_logger, get_error_logger


@dataclass
class LogAnalysisReport:
    """Encapsulates historical recovery analytics."""
    total_events: int
    successful_recoveries: int
    failed_recoveries: int
    success_rate: float
    avg_duration_sec: float
    fastest_duration_sec: float
    slowest_duration_sec: float
    most_affected_app: str
    most_common_failure_reason: str
    hourly_distribution: Dict[int, int]
    crash_trend: str
    suggested_action: str
    has_data: bool
    sla_target_sec: float = RECOVERY_SLA_TARGET_SECONDS
    sla_met_count: int = 0
    sla_compliance_rate: float = 100.0
    recent_recoveries: List[Dict[str, Any]] = None
    total_crashes: int = 0
    total_attempts: int = 0
    repeated_crashes: int = 0
    recovery_failures: int = 0
    performance_trend: str = "INSUFFICIENT DATA"
    performance_trend_details: str = "Awaiting recovery events"

    def __post_init__(self):
        if self.recent_recoveries is None:
            self.recent_recoveries = []
        if self.total_attempts == 0 and self.total_events > 0:
            self.total_attempts = self.total_events
        if self.total_crashes == 0 and self.total_events > 0:
            self.total_crashes = self.total_events
        if self.recovery_failures == 0 and self.failed_recoveries > 0:
            self.recovery_failures = self.failed_recoveries

    @property
    def min_duration_sec(self) -> float:
        return self.fastest_duration_sec

    @property
    def max_duration_sec(self) -> float:
        return self.slowest_duration_sec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_events,
            "total_crashes": self.total_crashes,
            "total_attempts": self.total_attempts,
            "successful_recoveries": self.successful_recoveries,
            "failed_recoveries": self.failed_recoveries,
            "success_rate": self.success_rate,
            "avg_duration_sec": self.avg_duration_sec,
            "fastest_duration_sec": self.fastest_duration_sec,
            "slowest_duration_sec": self.slowest_duration_sec,
            "min_duration_sec": self.fastest_duration_sec,
            "max_duration_sec": self.slowest_duration_sec,
            "sla_target_sec": self.sla_target_sec,
            "sla_met_count": self.sla_met_count,
            "sla_compliance_rate": self.sla_compliance_rate,
            "repeated_crashes": self.repeated_crashes,
            "recovery_failures": self.recovery_failures,
            "performance_trend": self.performance_trend,
            "performance_trend_details": self.performance_trend_details,
            "most_affected_app": self.most_affected_app,
            "most_common_failure_reason": self.most_common_failure_reason,
            "hourly_distribution": self.hourly_distribution,
            "crash_trend": self.crash_trend,
            "suggested_action": self.suggested_action,
            "has_data": self.has_data,
            "recent_recoveries": self.recent_recoveries,
        }


class LogAnalyzer:
    """
    Parses and aggregates recorded recovery operations from logs/recovery.log.
    """

    def __init__(self, log_path: Path = RECOVERY_LOG_FILE):
        self.log_path = log_path
        self.logger = get_system_logger()

    def load_records(self, deduplicate: bool = True) -> List[Dict[str, Any]]:
        """Parses JSON-lines from recovery.log safely with robust error handling and deduplication."""
        if not self.log_path.exists():
            return []

        records = []
        seen_events = set()
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if isinstance(entry, dict):
                            # Normalize recovery status safely
                            raw_st = entry.get("recovery_status")
                            entry["recovery_status"] = str(raw_st).upper() if raw_st is not None else "UNKNOWN"

                            # Normalize numeric fields if present
                            if "recovery_duration_sec" in entry:
                                try:
                                    entry["recovery_duration_sec"] = float(entry["recovery_duration_sec"])
                                except (ValueError, TypeError):
                                    entry.pop("recovery_duration_sec", None)

                            # Deduplication guard: ignore duplicate identical records
                            if deduplicate:
                                dedup_key = (
                                    entry.get("timestamp"),
                                    entry.get("restart_attempt") or entry.get("attempt_number"),
                                    entry.get("application_name"),
                                    entry.get("failure_reason"),
                                    entry.get("recovery_duration_sec"),
                                )
                                if dedup_key in seen_events:
                                    continue
                                seen_events.add(dedup_key)

                            records.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            get_error_logger().error(f"Error reading recovery log {self.log_path}: {e}")

        return records

    @staticmethod
    def compute_performance_trend(
        durations: List[float],
        min_events: int = 2,
    ) -> Tuple[str, str]:
        """
        Analyzes recovery durations over time (chronological order) to identify performance trajectory.
        Returns:
            (trend_category, trend_details)
            trend_category is one of: 'IMPROVING', 'WORSENING', 'STABLE', 'INSUFFICIENT DATA'
        """
        valid_durations = []
        for d in durations:
            try:
                val = float(d)
                if val > 0:
                    valid_durations.append(val)
            except (ValueError, TypeError):
                continue

        if len(valid_durations) < min_events:
            return "INSUFFICIENT DATA", f"({len(valid_durations)} valid durations, min {min_events} required)"

        window = valid_durations[-10:] if len(valid_durations) > 10 else valid_durations

        if len(window) == 2:
            d1, d2 = window[0], window[1]
            delta = d2 - d1
            pct = (delta / d1 * 100.0) if d1 > 0 else 0.0
            if delta < -0.05 and pct <= -5.0:
                return "IMPROVING", f"Faster: {d1:.2f}s -> {d2:.2f}s ({pct:+.1f}%)"
            elif delta > 0.05 and pct >= 5.0:
                return "WORSENING", f"Slower: {d1:.2f}s -> {d2:.2f}s ({pct:+.1f}%)"
            else:
                return "STABLE", f"Consistent: ~{(d1 + d2) / 2:.2f}s ({pct:+.1f}%)"

        half = len(window) // 2
        older_half = window[:half]
        recent_half = window[half:]

        avg_older = sum(older_half) / len(older_half)
        avg_recent = sum(recent_half) / len(recent_half)
        delta = avg_recent - avg_older
        pct = (delta / avg_older * 100.0) if avg_older > 0 else 0.0

        if delta < -0.05 and pct <= -5.0:
            return "IMPROVING", f"Faster: {avg_older:.2f}s -> {avg_recent:.2f}s ({pct:+.1f}%)"
        elif delta > 0.05 and pct >= 5.0:
            return "WORSENING", f"Slower: {avg_older:.2f}s -> {avg_recent:.2f}s ({pct:+.1f}%)"
        else:
            return "STABLE", f"Consistent: ~{(avg_older + avg_recent) / 2:.2f}s ({pct:+.1f}%)"

    def analyze(self) -> LogAnalysisReport:
        """
        Processes historical logs and compiles a comprehensive analytics report
        including SLA metrics and recent recovery history.
        """
        records = self.load_records()

        if not records:
            return LogAnalysisReport(
                total_events=0,
                successful_recoveries=0,
                failed_recoveries=0,
                success_rate=100.0,
                avg_duration_sec=0.0,
                fastest_duration_sec=0.0,
                slowest_duration_sec=0.0,
                most_affected_app="N/A",
                most_common_failure_reason="No recorded failures",
                hourly_distribution={},
                crash_trend="INSUFFICIENT DATA (0 records)",
                suggested_action="System nominal. No historical recovery events logged yet.",
                has_data=False,
                sla_target_sec=RECOVERY_SLA_TARGET_SECONDS,
                sla_met_count=0,
                sla_compliance_rate=100.0,
                recent_recoveries=[],
                total_crashes=0,
                total_attempts=0,
                repeated_crashes=0,
                recovery_failures=0,
                performance_trend="INSUFFICIENT DATA",
                performance_trend_details="No recorded recovery events in log.",
            )

        total_events = len(records)
        successes = sum(1 for r in records if r.get("recovery_status") == "SUCCESS")
        failures = sum(1 for r in records if r.get("recovery_status") == "FAILED")
        success_rate = round((successes / total_events) * 100.0, 1) if total_events > 0 else 100.0

        durations = [
            float(r["recovery_duration_sec"])
            for r in records
            if r.get("recovery_status") == "SUCCESS" and "recovery_duration_sec" in r
        ]

        if durations:
            avg_dur = round(sum(durations) / len(durations), 3)
            fastest_dur = round(min(durations), 3)
            slowest_dur = round(max(durations), 3)
        else:
            avg_dur = 0.0
            fastest_dur = 0.0
            slowest_dur = 0.0

        # Calculate SLA target compliance
        sla_met_count = 0
        for r in records:
            if "sla_met" in r:
                if bool(r["sla_met"]):
                    sla_met_count += 1
            else:
                if r.get("recovery_status") == "SUCCESS":
                    try:
                        dur = float(r.get("recovery_duration_sec", 999.0))
                        if dur <= RECOVERY_SLA_TARGET_SECONDS:
                            sla_met_count += 1
                    except (ValueError, TypeError):
                        pass

        sla_compliance_rate = round((sla_met_count / total_events) * 100.0, 1) if total_events > 0 else 100.0

        # Performance trend calculation across recorded durations
        perf_trend, perf_trend_details = LogAnalyzer.compute_performance_trend(durations)

        # Repeated crashes and failure counts
        repeated_crashes = 0
        prev_dt = None
        for r in records:
            is_rep = False
            att = r.get("restart_attempt") or r.get("attempt_number")
            if att is not None:
                try:
                    if int(att) > 1:
                        is_rep = True
                except (ValueError, TypeError):
                    pass

            ts_str = r.get("timestamp") or r.get("iso_timestamp")
            curr_dt = None
            if ts_str:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        curr_dt = datetime.strptime(ts_str.split(".")[0], fmt.split(".")[0])
                        break
                    except ValueError:
                        continue

            if not is_rep and curr_dt and prev_dt and (curr_dt - prev_dt).total_seconds() <= 60.0:
                is_rep = True

            if curr_dt:
                prev_dt = curr_dt

            if is_rep:
                repeated_crashes += 1

        app_counts = Counter(r.get("application_name", "Unknown") for r in records)
        most_affected_app = app_counts.most_common(1)[0][0] if app_counts else "Unknown"

        reason_counts = Counter(r.get("failure_reason", "Unspecified") for r in records)
        most_common_reason = reason_counts.most_common(1)[0][0] if reason_counts else "Unspecified"

        # Hourly distribution
        hourly = Counter()
        timestamps = []
        for r in records:
            ts_str = r.get("timestamp") or r.get("iso_timestamp")
            if ts_str:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        dt = datetime.strptime(ts_str.split(".")[0], fmt.split(".")[0])
                        hourly[dt.hour] += 1
                        timestamps.append(dt)
                        break
                    except ValueError:
                        continue

        # Trend analysis (requires at least 4 data points)
        if total_events < 4:
            crash_trend = f"INSUFFICIENT DATA ({total_events} events, min 4 required)"
        else:
            half = total_events // 2
            first_half_rate = half
            second_half_rate = total_events - half

            if second_half_rate > first_half_rate * 1.5:
                crash_trend = "INCREASING (Accelerating crash frequency detected)"
            elif second_half_rate < first_half_rate * 0.7:
                crash_trend = "DECREASING (System stabilizing)"
            else:
                crash_trend = "STABLE (Uniform distribution of recovery events)"

        # Suggest corrective actions based on empirical findings
        if "137" in most_common_reason or "OOM" in most_common_reason.upper():
            suggested_action = "Investigate memory consumption or allocate higher RAM limits for worker processes."
        elif "exit code 1" in most_common_reason or "exception" in most_common_reason.lower():
            suggested_action = "Review application traceback in logs/error.log to fix unhandled runtime exception."
        elif success_rate < 70.0:
            suggested_action = "Low recovery success rate. Verify application runtime dependencies and port collisions."
        elif total_events > 10:
            suggested_action = "High cumulative restart count. Recommend application profiling or architecture review."
        else:
            suggested_action = "Automatic recovery performing nominally within configured SLA parameters."

        return LogAnalysisReport(
            total_events=total_events,
            successful_recoveries=successes,
            failed_recoveries=failures,
            success_rate=success_rate,
            avg_duration_sec=avg_dur,
            fastest_duration_sec=fastest_dur,
            slowest_duration_sec=slowest_dur,
            most_affected_app=most_affected_app,
            most_common_failure_reason=most_common_reason,
            hourly_distribution=dict(hourly),
            crash_trend=crash_trend,
            suggested_action=suggested_action,
            has_data=True,
            sla_target_sec=RECOVERY_SLA_TARGET_SECONDS,
            sla_met_count=sla_met_count,
            sla_compliance_rate=sla_compliance_rate,
            recent_recoveries=records[-10:],
            total_crashes=total_events,
            total_attempts=total_events,
            repeated_crashes=repeated_crashes,
            recovery_failures=failures,
            performance_trend=perf_trend,
            performance_trend_details=perf_trend_details,
        )
