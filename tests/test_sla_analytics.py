"""
Unit tests for Recovery History and SLA Analytics (recovery/auto_restart.py, logger/recovery_logger.py, ai/log_analyzer.py).
Tests:
- Successful recovery and correct PID tracking
- Failed recovery handling
- Accurate duration calculations (avg, fastest, slowest)
- Success-rate calculations (denominator integrity)
- SLA pass and fail cases
- Empty history handling (no division-by-zero)
- Malformed and incomplete log record resilience
- Duplicate recovery event prevention
- Persistence across application restarts
"""

import json
import tempfile
import unittest
from pathlib import Path

from config import RECOVERY_SLA_TARGET_SECONDS
from logger.recovery_logger import RecoveryLogger, close_recovery_logger
from ai.log_analyzer import LogAnalyzer, LogAnalysisReport


class TestRecoveryHistoryAndSLA(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_log_file = self.temp_path / "test_recovery.log"

    def tearDown(self):
        close_recovery_logger()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_successful_recovery_and_pid_tracking(self):
        """Verifies successful recovery records old PID, new PID, duration in ms/sec, and status SUCCESS."""
        import logger.recovery_logger as rlog
        orig_file = rlog.RECOVERY_LOG_FILE
        rlog.RECOVERY_LOG_FILE = self.test_log_file
        rlog._RECOVERY_LOGGER_INITIALIZED = False

        try:
            record = RecoveryLogger.log_recovery(
                app_name="HealOS-DummyApp",
                failure_reason="Simulated SIGSEGV exit code 1",
                recovery_action="RESTART_APPLICATION",
                attempt_number=1,
                duration_seconds=1.125,
                status="SUCCESS",
                decision_reason="Host resources nominal; automatic restart approved.",
                decision_score=0.95,
                old_pid=1234,
                new_pid=5678,
                crash_detection_time="2026-10-20 17:00:00",
                recovery_start_time="2026-10-20 17:00:00.100",
                recovery_completion_time="2026-10-20 17:00:01.225",
                sla_target_sec=2.5,
                sla_met=True,
            )

            self.assertEqual(record["application_name"], "HealOS-DummyApp")
            self.assertEqual(record["old_pid"], 1234)
            self.assertEqual(record["new_pid"], 5678)
            self.assertEqual(record["recovery_status"], "SUCCESS")
            self.assertEqual(record["recovery_duration_sec"], 1.125)
            self.assertEqual(record["recovery_duration_ms"], 1125.0)
            self.assertTrue(record["sla_met"])
            self.assertEqual(record["sla_target_sec"], 2.5)

            # Verify written JSON line
            content = self.test_log_file.read_text(encoding="utf-8").strip()
            parsed = json.loads(content)
            self.assertEqual(parsed["old_pid"], 1234)
            self.assertEqual(parsed["new_pid"], 5678)
            self.assertEqual(parsed["recovery_status"], "SUCCESS")
        finally:
            rlog.RECOVERY_LOG_FILE = orig_file
            rlog._RECOVERY_LOGGER_INITIALIZED = False

    def test_failed_recovery_handling(self):
        """Verifies failed recovery records FAILED status, duration, sla_met=False, and new_pid=None."""
        import logger.recovery_logger as rlog
        orig_file = rlog.RECOVERY_LOG_FILE
        rlog.RECOVERY_LOG_FILE = self.test_log_file
        rlog._RECOVERY_LOGGER_INITIALIZED = False

        try:
            record = RecoveryLogger.log_recovery(
                app_name="HealOS-DummyApp",
                failure_reason="Repeated crash storm",
                recovery_action="ALERT_USER",
                attempt_number=5,
                duration_seconds=0.0,
                status="FAILED",
                decision_reason="Max retry quota reached",
                decision_score=0.99,
                old_pid=9999,
                new_pid=None,
                sla_target_sec=2.5,
                sla_met=False,
            )

            self.assertEqual(record["recovery_status"], "FAILED")
            self.assertIsNone(record["new_pid"])
            self.assertEqual(record["old_pid"], 9999)
            self.assertFalse(record["sla_met"])
        finally:
            rlog.RECOVERY_LOG_FILE = orig_file
            rlog._RECOVERY_LOGGER_INITIALIZED = False

    def test_accurate_duration_calculations(self):
        """Verifies calculation of average, fastest, and slowest recovery duration."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.0, "timestamp": "2026-10-20 10:00:01", "restart_attempt": 1},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.5, "timestamp": "2026-10-20 10:05:01", "restart_attempt": 2},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 2.0, "timestamp": "2026-10-20 10:10:01", "restart_attempt": 3},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 10:15:01", "restart_attempt": 4},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report: LogAnalysisReport = analyzer.analyze()

        self.assertEqual(report.total_events, 4)
        self.assertEqual(report.successful_recoveries, 3)
        self.assertEqual(report.failed_recoveries, 1)
        self.assertAlmostEqual(report.avg_duration_sec, 1.5, places=2)
        self.assertAlmostEqual(report.fastest_duration_sec, 1.0, places=2)
        self.assertAlmostEqual(report.slowest_duration_sec, 2.0, places=2)

    def test_success_rate_calculations(self):
        """Verifies success rate calculation with explicit total attempts denominator."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.1, "timestamp": "2026-10-20 11:00:01", "restart_attempt": 1},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.2, "timestamp": "2026-10-20 11:02:01", "restart_attempt": 2},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.3, "timestamp": "2026-10-20 11:04:01", "restart_attempt": 3},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 11:06:01", "restart_attempt": 4},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        # Denominator = 4 (3 success + 1 fail); Rate = 3 / 4 * 100.0 = 75.0%
        self.assertEqual(report.total_events, 4)
        self.assertEqual(report.success_rate, 75.0)

    def test_sla_pass_and_fail_cases(self):
        """Verifies SLA target compliance calculation for passed and breached recoveries."""
        records = [
            # Event 1: SUCCESS within 2.5s SLA target -> MET
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.1, "sla_met": True, "timestamp": "2026-10-20 12:00:00", "restart_attempt": 1},
            # Event 2: SUCCESS within 2.5s SLA target -> MET
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 2.2, "sla_met": True, "timestamp": "2026-10-20 12:02:00", "restart_attempt": 2},
            # Event 3: SUCCESS exceeding 2.5s SLA target -> BREACH
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 3.8, "sla_met": False, "timestamp": "2026-10-20 12:04:00", "restart_attempt": 3},
            # Event 4: FAILED recovery -> BREACH
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "sla_met": False, "timestamp": "2026-10-20 12:06:00", "restart_attempt": 4},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertEqual(report.sla_met_count, 2)
        self.assertEqual(report.total_events, 4)
        # SLA Compliance = 2 / 4 * 100.0 = 50.0%
        self.assertEqual(report.sla_compliance_rate, 50.0)

    def test_empty_history_no_division_by_zero(self):
        """Verifies empty or missing log file handles safely without ZeroDivisionError."""
        nonexistent = self.temp_path / "does_not_exist.log"
        analyzer = LogAnalyzer(log_path=nonexistent)
        report = analyzer.analyze()

        self.assertFalse(report.has_data)
        self.assertEqual(report.total_events, 0)
        self.assertEqual(report.successful_recoveries, 0)
        self.assertEqual(report.failed_recoveries, 0)
        self.assertEqual(report.avg_duration_sec, 0.0)
        self.assertEqual(report.fastest_duration_sec, 0.0)
        self.assertEqual(report.slowest_duration_sec, 0.0)
        self.assertEqual(report.sla_compliance_rate, 100.0)
        self.assertEqual(len(report.recent_recoveries), 0)

    def test_malformed_and_incomplete_log_records(self):
        """Verifies malformed JSON, corrupted data, and blank lines are ignored cleanly."""
        corrupted_content = (
            "\n"                                            # Blank line
            "{bad json syntax\n"                            # Malformed JSON
            '{"recovery_status": "SUCCESS"}\n'             # Incomplete record (missing duration)
            "null\n"                                        # Not a dict
            '{"recovery_status": "SUCCESS", "recovery_duration_sec": "bad_float"}\n' # Invalid numeric
            '{"recovery_status": "SUCCESS", "recovery_duration_sec": 1.25, "timestamp": "2026-10-20 13:00:00", "restart_attempt": 1}\n' # Valid
        )
        self.test_log_file.write_text(corrupted_content, encoding="utf-8")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        records = analyzer.load_records()
        self.assertGreaterEqual(len(records), 1)

        report = analyzer.analyze()
        self.assertTrue(report.has_data)
        self.assertAlmostEqual(report.avg_duration_sec, 1.25, places=2)

    def test_duplicate_event_prevention(self):
        """Verifies duplicate log entries are not double-counted in analytics."""
        duplicate_record = {
            "timestamp": "2026-10-20 14:00:00",
            "restart_attempt": 1,
            "application_name": "HealOS-DummyApp",
            "failure_reason": "exit code 1",
            "recovery_duration_sec": 1.15,
            "recovery_status": "SUCCESS",
            "sla_met": True,
        }
        # Write identical record 3 times
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for _ in range(3):
                f.write(json.dumps(duplicate_record) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        records = analyzer.load_records(deduplicate=True)
        # Should deduplicate to exactly 1 event
        self.assertEqual(len(records), 1)

        report = analyzer.analyze()
        self.assertEqual(report.total_events, 1)

    def test_persistence_across_application_restarts(self):
        """Verifies recovery telemetry persists in logs/recovery.log and reloads cleanly."""
        import logger.recovery_logger as rlog
        orig_file = rlog.RECOVERY_LOG_FILE
        rlog.RECOVERY_LOG_FILE = self.test_log_file
        rlog._RECOVERY_LOGGER_INITIALIZED = False

        try:
            # First application session writes recovery event
            RecoveryLogger.log_recovery(
                app_name="HealOS-DummyApp",
                failure_reason="Crash #1",
                recovery_action="RESTART_APPLICATION",
                attempt_number=1,
                duration_seconds=1.05,
                status="SUCCESS",
                decision_reason="Session 1",
                decision_score=0.9,
                old_pid=1001,
                new_pid=1002,
                sla_target_sec=2.5,
                sla_met=True,
            )
            close_recovery_logger()

            # Second application session writes recovery event
            rlog._RECOVERY_LOGGER_INITIALIZED = False
            RecoveryLogger.log_recovery(
                app_name="HealOS-DummyApp",
                failure_reason="Crash #2",
                recovery_action="RESTART_APPLICATION",
                attempt_number=2,
                duration_seconds=1.25,
                status="SUCCESS",
                decision_reason="Session 2",
                decision_score=0.95,
                old_pid=1002,
                new_pid=1003,
                sla_target_sec=2.5,
                sla_met=True,
            )
            close_recovery_logger()

            # New analyzer instance loads both sessions
            analyzer = LogAnalyzer(log_path=self.test_log_file)
            report = analyzer.analyze()

            self.assertEqual(report.total_events, 2)
            self.assertEqual(report.successful_recoveries, 2)
            self.assertEqual(report.success_rate, 100.0)
            self.assertAlmostEqual(report.avg_duration_sec, 1.15, places=2)
            self.assertEqual(len(report.recent_recoveries), 2)
        finally:
            rlog.RECOVERY_LOG_FILE = orig_file
            rlog._RECOVERY_LOGGER_INITIALIZED = False


if __name__ == "__main__":
    unittest.main()
