"""
Unit tests for Feature 7: Self-Healing Performance Analytics.
(ai/log_analyzer.py, recovery/auto_restart.py, dashboard/dashboard.py)

Tests cover:
- Empty recovery history (no ZeroDivisionError, safe defaults)
- All recoveries successful (100% success rate, duration stats)
- Some recoveries failed (correct denominator, failed recoveries count)
- Success-rate calculation
- Recovery-duration statistics (average, minimum, maximum)
- SLA compliance rate calculations
- Malformed log entries and corrupted JSON resilience
- Repeated crashes and failure counts
- Trend calculation with insufficient history (<2 events) and sufficient history (improving, worsening, stable)
- Compatibility with Features 1-6 components
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from config import RECOVERY_SLA_TARGET_SECONDS
from ai.log_analyzer import LogAnalyzer, LogAnalysisReport
from recovery.auto_restart import AutoRestart
from detector.crash_detector import CrashEvent
from monitor.system_monitor import SystemMetrics
from dashboard.dashboard import AppState


class TestSelfHealingPerformanceAnalytics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_log_file = self.temp_path / "test_recovery.log"

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_empty_recovery_history(self):
        """Verifies empty or non-existent log file handles safely without ZeroDivisionError."""
        nonexistent = self.temp_path / "absent.log"
        analyzer = LogAnalyzer(log_path=nonexistent)
        report = analyzer.analyze()

        self.assertFalse(report.has_data)
        self.assertEqual(report.total_events, 0)
        self.assertEqual(report.total_crashes, 0)
        self.assertEqual(report.total_attempts, 0)
        self.assertEqual(report.successful_recoveries, 0)
        self.assertEqual(report.failed_recoveries, 0)
        self.assertEqual(report.repeated_crashes, 0)
        self.assertEqual(report.recovery_failures, 0)
        self.assertEqual(report.success_rate, 100.0)
        self.assertEqual(report.avg_duration_sec, 0.0)
        self.assertEqual(report.fastest_duration_sec, 0.0)
        self.assertEqual(report.slowest_duration_sec, 0.0)
        self.assertEqual(report.min_duration_sec, 0.0)
        self.assertEqual(report.max_duration_sec, 0.0)
        self.assertEqual(report.sla_compliance_rate, 100.0)
        self.assertEqual(report.performance_trend, "INSUFFICIENT DATA")

    def test_all_recoveries_successful(self):
        """Verifies analytics when 100% of recorded recovery operations succeed."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.10, "timestamp": "2026-10-20 12:00:00", "restart_attempt": 1, "sla_met": True},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.20, "timestamp": "2026-10-20 12:05:00", "restart_attempt": 1, "sla_met": True},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.30, "timestamp": "2026-10-20 12:10:00", "restart_attempt": 1, "sla_met": True},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertTrue(report.has_data)
        self.assertEqual(report.total_events, 3)
        self.assertEqual(report.total_crashes, 3)
        self.assertEqual(report.successful_recoveries, 3)
        self.assertEqual(report.failed_recoveries, 0)
        self.assertEqual(report.success_rate, 100.0)
        self.assertEqual(report.sla_compliance_rate, 100.0)
        self.assertAlmostEqual(report.avg_duration_sec, 1.20, places=2)
        self.assertAlmostEqual(report.min_duration_sec, 1.10, places=2)
        self.assertAlmostEqual(report.max_duration_sec, 1.30, places=2)

    def test_some_recoveries_failed(self):
        """Verifies proper calculation of failure counts and rates when recoveries fail."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.0, "timestamp": "2026-10-20 13:00:00", "restart_attempt": 1, "sla_met": True},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 13:05:00", "restart_attempt": 2, "sla_met": False},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.5, "timestamp": "2026-10-20 13:10:00", "restart_attempt": 3, "sla_met": True},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 13:15:00", "restart_attempt": 4, "sla_met": False},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertEqual(report.total_events, 4)
        self.assertEqual(report.successful_recoveries, 2)
        self.assertEqual(report.failed_recoveries, 2)
        self.assertEqual(report.recovery_failures, 2)
        self.assertEqual(report.success_rate, 50.0)
        # Only successful recoveries are included in duration statistics
        self.assertAlmostEqual(report.avg_duration_sec, 1.25, places=2)
        self.assertAlmostEqual(report.min_duration_sec, 1.0, places=2)
        self.assertAlmostEqual(report.max_duration_sec, 1.5, places=2)

    def test_success_rate_calculation(self):
        """Verifies success rate calculation with explicit total attempts denominator."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.2, "timestamp": "2026-10-20 14:00:00", "restart_attempt": 1},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.4, "timestamp": "2026-10-20 14:02:00", "restart_attempt": 2},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.1, "timestamp": "2026-10-20 14:04:00", "restart_attempt": 3},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 14:06:00", "restart_attempt": 4},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 14:08:00", "restart_attempt": 5},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertEqual(report.total_attempts, 5)
        self.assertEqual(report.successful_recoveries, 3)
        self.assertEqual(report.failed_recoveries, 2)
        # 3 / 5 * 100.0 = 60.0%
        self.assertEqual(report.success_rate, 60.0)

    def test_recovery_duration_statistics(self):
        """Verifies calculation of average, minimum, and maximum recovery duration."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 0.85, "timestamp": "2026-10-20 15:00:00", "restart_attempt": 1},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.25, "timestamp": "2026-10-20 15:05:00", "restart_attempt": 2},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 2.10, "timestamp": "2026-10-20 15:10:00", "restart_attempt": 3},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertAlmostEqual(report.min_duration_sec, 0.85, places=2)
        self.assertAlmostEqual(report.fastest_duration_sec, 0.85, places=2)
        self.assertAlmostEqual(report.max_duration_sec, 2.10, places=2)
        self.assertAlmostEqual(report.slowest_duration_sec, 2.10, places=2)
        expected_avg = round((0.85 + 1.25 + 2.10) / 3, 3)
        self.assertAlmostEqual(report.avg_duration_sec, expected_avg, places=3)

    def test_sla_compliance(self):
        """Verifies SLA compliance percentage under mixed compliant and breached events."""
        records = [
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.0, "sla_met": True, "timestamp": "2026-10-20 16:00:00", "restart_attempt": 1},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 2.0, "sla_met": True, "timestamp": "2026-10-20 16:02:00", "restart_attempt": 2},
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 3.2, "sla_met": False, "timestamp": "2026-10-20 16:04:00", "restart_attempt": 3},
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "sla_met": False, "timestamp": "2026-10-20 16:06:00", "restart_attempt": 4},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertEqual(report.sla_met_count, 2)
        self.assertEqual(report.total_events, 4)
        # 2 / 4 * 100.0 = 50.0%
        self.assertEqual(report.sla_compliance_rate, 50.0)

    def test_malformed_log_entries(self):
        """Verifies that corrupted JSON, blank lines, and invalid fields are skipped safely."""
        malformed_data = (
            "\n"
            "{not a valid json string\n"
            '{"broken": true\n'
            '{"recovery_status": "SUCCESS", "recovery_duration_sec": "not_a_number"}\n'
            '{"recovery_status": "SUCCESS", "recovery_duration_sec": 1.45, "timestamp": "2026-10-20 17:00:00", "restart_attempt": 1}\n'
        )
        self.test_log_file.write_text(malformed_data, encoding="utf-8")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertTrue(report.has_data)
        self.assertEqual(report.total_events, 2)
        self.assertEqual(report.successful_recoveries, 2)
        self.assertAlmostEqual(report.avg_duration_sec, 1.45, places=2)

    def test_repeated_crashes(self):
        """Verifies detection and tallying of repeated crashes (attempt > 1 and temporal proximity)."""
        records = [
            # Attempt 1: First crash
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.0, "timestamp": "2026-10-20 18:00:00", "restart_attempt": 1},
            # Attempt 2: Repeated crash
            {"recovery_status": "SUCCESS", "recovery_duration_sec": 1.1, "timestamp": "2026-10-20 18:00:30", "restart_attempt": 2},
            # Attempt 3: Another repeated crash
            {"recovery_status": "FAILED", "recovery_duration_sec": 0.0, "timestamp": "2026-10-20 18:01:00", "restart_attempt": 3},
        ]
        with open(self.test_log_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        analyzer = LogAnalyzer(log_path=self.test_log_file)
        report = analyzer.analyze()

        self.assertEqual(report.repeated_crashes, 2)
        self.assertEqual(report.recovery_failures, 1)

    def test_trend_calculation_insufficient_history(self):
        """Verifies that trend reports INSUFFICIENT DATA when fewer than 2 data points exist."""
        # 0 events
        trend, details = LogAnalyzer.compute_performance_trend([])
        self.assertEqual(trend, "INSUFFICIENT DATA")
        self.assertIn("min 2 required", details)

        # 1 event
        trend, details = LogAnalyzer.compute_performance_trend([1.25])
        self.assertEqual(trend, "INSUFFICIENT DATA")
        self.assertIn("1 valid durations", details)

    def test_trend_calculation_sufficient_history_improving(self):
        """Verifies trend calculation detects IMPROVING recovery times (latencies decreasing)."""
        # Latencies getting faster
        durations = [2.2, 1.9, 1.6, 1.2, 0.9, 0.75]
        trend, details = LogAnalyzer.compute_performance_trend(durations)
        self.assertEqual(trend, "IMPROVING")
        self.assertIn("Faster", details)

        # 2-event improving test
        trend_2, details_2 = LogAnalyzer.compute_performance_trend([1.8, 1.1])
        self.assertEqual(trend_2, "IMPROVING")

    def test_trend_calculation_sufficient_history_worsening(self):
        """Verifies trend calculation detects WORSENING recovery times (latencies increasing)."""
        # Latencies getting slower
        durations = [0.8, 0.9, 1.1, 1.5, 1.9, 2.4]
        trend, details = LogAnalyzer.compute_performance_trend(durations)
        self.assertEqual(trend, "WORSENING")
        self.assertIn("Slower", details)

        # 2-event worsening test
        trend_2, details_2 = LogAnalyzer.compute_performance_trend([1.0, 1.7])
        self.assertEqual(trend_2, "WORSENING")

    def test_trend_calculation_sufficient_history_stable(self):
        """Verifies trend calculation detects STABLE recovery times within normal variance."""
        durations = [1.02, 0.99, 1.01, 1.03, 0.98, 1.00]
        trend, details = LogAnalyzer.compute_performance_trend(durations)
        self.assertEqual(trend, "STABLE")
        self.assertIn("Consistent", details)

        # 2-event stable test
        trend_2, details_2 = LogAnalyzer.compute_performance_trend([1.05, 1.06])
        self.assertEqual(trend_2, "STABLE")

    def test_compatibility_with_existing_features(self):
        """Verifies that AutoRestart and AppState expose all Feature 7 performance analytics fields."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)
        summary = service.get_status_summary()

        self.assertIn("total_crashes", summary)
        self.assertIn("total_attempts", summary)
        self.assertIn("successful_recoveries", summary)
        self.assertIn("failed_recoveries", summary)
        self.assertIn("repeated_crashes", summary)
        self.assertIn("recovery_failures", summary)
        self.assertIn("success_rate", summary)
        self.assertIn("avg_duration_sec", summary)
        self.assertIn("min_duration_sec", summary)
        self.assertIn("max_duration_sec", summary)
        self.assertIn("sla_compliance_rate", summary)
        self.assertIn("performance_trend", summary)
        self.assertIn("performance_trend_details", summary)

        # Verify AppState synchronization
        state = AppState()
        state.update_recovery_status(summary)

        self.assertEqual(state.repeated_crashes, 0)
        self.assertEqual(state.recovery_failures, 0)
        self.assertEqual(state.recovery_trend, "INSUFFICIENT DATA")

        # Simulate 2 recoveries on AutoRestart
        def fake_start():
            service.process = MagicMock()
            service.process.poll.return_value = None
            service.current_pid = 9999
            return True

        service.start_application = fake_start

        # First crash
        crash1 = CrashEvent(
            pid=1001,
            timestamp="2026-10-20 18:00:00",
            exit_code=1,
            failure_reason="Crash #1",
            is_unexpected=True,
            detected_at=time.time(),
        )
        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = SystemMetrics(
                timestamp="2026-10-20 18:00:00",
                cpu_percent=15.0,
                ram_percent=35.0,
                ram_used_mb=4000.0,
                ram_total_mb=16000.0,
                disk_percent=40.0,
                disk_used_gb=100.0,
                disk_total_gb=500.0,
                process_count=100,
                cpu_change=0.0,
                ram_change=0.0,
            )
            service.handle_detected_crash(crash1)

        # Second crash (repeated)
        crash2 = CrashEvent(
            pid=1002,
            timestamp="2026-10-20 18:00:30",
            exit_code=1,
            failure_reason="Crash #2",
            is_unexpected=True,
            detected_at=time.time(),
        )
        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = SystemMetrics(
                timestamp="2026-10-20 18:00:30",
                cpu_percent=15.0,
                ram_percent=35.0,
                ram_used_mb=4000.0,
                ram_total_mb=16000.0,
                disk_percent=40.0,
                disk_used_gb=100.0,
                disk_total_gb=500.0,
                process_count=100,
                cpu_change=0.0,
                ram_change=0.0,
            )
            service.handle_detected_crash(crash2)

        summary2 = service.get_status_summary()
        self.assertEqual(summary2["total_crashes"], 2)
        self.assertEqual(summary2["repeated_crashes"], 1)
        self.assertEqual(summary2["successful_recoveries"], 2)
        self.assertEqual(summary2["success_rate"], 100.0)
        self.assertIn(summary2["performance_trend"], ("IMPROVING", "WORSENING", "STABLE"))

        state.update_recovery_status(summary2)
        self.assertEqual(state.total_crashes, 2)
        self.assertEqual(state.repeated_crashes, 1)
        self.assertEqual(state.successful_recoveries, 2)
        self.assertIn(state.recovery_trend, ("IMPROVING", "WORSENING", "STABLE"))


if __name__ == "__main__":
    unittest.main()
