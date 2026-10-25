"""
Unit tests for AutoRestart Service and Recovery Logger (recovery/auto_restart.py, logger/recovery_logger.py).
Tests recovery lifecycle, log generation, and LogAnalyzer metrics parsing.
"""

import os
import tempfile
import unittest
from pathlib import Path
from recovery.auto_restart import AutoRestart
from logger.recovery_logger import RecoveryLogger
from ai.log_analyzer import LogAnalyzer
from detector.crash_detector import CrashEvent


class TestRecoveryAndLogging(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.recovery_log = self.temp_path / "test_recovery.log"

    def tearDown(self):
        from logger.recovery_logger import close_recovery_logger
        close_recovery_logger()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_recovery_logger_writes_structured_record(self):
        """Verifies RecoveryLogger logs all required fields exactly once."""
        # Temporarily redirect RECOVERY_LOG_FILE
        import logger.recovery_logger as rlog
        original_file = rlog.RECOVERY_LOG_FILE
        rlog.RECOVERY_LOG_FILE = self.recovery_log
        rlog._RECOVERY_LOGGER_INITIALIZED = False

        try:
            record = RecoveryLogger.log_recovery(
                app_name="dummy_app.py",
                failure_reason="Simulated SIGSEGV exit code 1",
                recovery_action="RESTART_APPLICATION",
                attempt_number=1,
                duration_seconds=0.45,
                status="SUCCESS",
                decision_reason="Nominal resources",
                decision_score=0.92,
            )

            self.assertEqual(record["application_name"], "dummy_app.py")
            self.assertEqual(record["recovery_status"], "SUCCESS")
            self.assertEqual(record["restart_attempt"], 1)

            # Analyze with LogAnalyzer
            analyzer = LogAnalyzer(log_path=self.recovery_log)
            report = analyzer.analyze()

            self.assertTrue(report.has_data)
            self.assertEqual(report.total_events, 1)
            self.assertEqual(report.successful_recoveries, 1)
            self.assertEqual(report.failed_recoveries, 0)
            self.assertEqual(report.success_rate, 100.0)
            self.assertEqual(report.avg_duration_sec, 0.45)
        finally:
            rlog.RECOVERY_LOG_FILE = original_file
            rlog._RECOVERY_LOGGER_INITIALIZED = False

    def test_auto_restart_summary_metrics(self):
        """Verifies AutoRestart initializes summary metrics accurately."""
        restart_service = AutoRestart()
        summary = restart_service.get_status_summary()

        self.assertIn("is_running", summary)
        self.assertEqual(summary["total_crashes"], 0)
        self.assertEqual(summary["total_restarts"], 0)
        self.assertEqual(summary["success_rate"], 100.0)
        self.assertIn("failed_pid", summary)
        self.assertIn("new_pid", summary)
        self.assertIn("recovery_state", summary)


if __name__ == "__main__":
    unittest.main()
