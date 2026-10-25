"""
Unit tests for AI Recovery Decision Engine (ai/decision_engine.py).
Tests rule logic: RESTART_APPLICATION, WAIT_AND_RETRY,
RESTART_APPLICATION_WITH_LIMITED_RETRIES, and ALERT_USER.
"""

import time
import unittest
from unittest.mock import patch, MagicMock
from ai.decision_engine import (
    RecoveryDecisionEngine,
    ACTION_MONITOR,
    ACTION_INVESTIGATE,
    ACTION_RESTART,
    ACTION_WAIT_RETRY,
    ACTION_ALERT_USER,
    ACTION_LIMITED_RETRY,
    DecisionOutput,
)
from config import (
    MAX_RESTART_ATTEMPTS,
    MAX_CRASHES_IN_WINDOW,
    RESOURCE_SATURATION_CPU,
    RESOURCE_SATURATION_RAM,
)
from detector.crash_detector import CrashEvent
from monitor.system_monitor import SystemMetrics
from recovery.auto_restart import AutoRestart


class TestRecoveryDecisionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RecoveryDecisionEngine()

    def _make_metrics(
        self,
        cpu_percent: float = 15.0,
        ram_percent: float = 35.0,
        disk_percent: float = 40.0,
        cpu_change: float = 0.0,
        ram_change: float = 0.0,
    ) -> SystemMetrics:
        return SystemMetrics(
            timestamp="2026-10-20 18:00:00",
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            ram_used_mb=4000.0,
            ram_total_mb=16000.0,
            disk_percent=disk_percent,
            disk_used_gb=100.0,
            disk_total_gb=500.0,
            process_count=100,
            cpu_change=cpu_change,
            ram_change=ram_change,
        )

    def test_nominal_restart_decision(self):
        """Under nominal load and initial failure, engine authorizes RESTART_APPLICATION."""
        decision: DecisionOutput = self.engine.decide(
            cpu_percent=15.0,
            ram_percent=40.0,
            disk_percent=30.0,
            current_attempt=0,
            crashes_in_window=1,
            failure_reason="Process exited with code 1",
        )
        self.assertEqual(decision.action, ACTION_RESTART)
        self.assertGreater(decision.confidence_score, 0.8)
        self.assertTrue(decision.is_heuristic)

    def test_resource_saturation_triggers_wait_and_retry(self):
        """When host RAM or CPU exceeds saturation ceiling, engine selects WAIT_AND_RETRY."""
        decision: DecisionOutput = self.engine.decide(
            cpu_percent=94.0,
            ram_percent=85.0,
            disk_percent=30.0,
            current_attempt=1,
            crashes_in_window=1,
            failure_reason="OOM",
        )
        self.assertEqual(decision.action, ACTION_WAIT_RETRY)
        self.assertGreater(decision.delay_seconds, 0.0)

    def test_max_retries_triggers_alert_user(self):
        """When current attempts reach MAX_RESTART_ATTEMPTS, engine mandates ALERT_USER."""
        decision: DecisionOutput = self.engine.decide(
            cpu_percent=10.0,
            ram_percent=20.0,
            disk_percent=30.0,
            current_attempt=MAX_RESTART_ATTEMPTS,
            crashes_in_window=1,
        )
        self.assertEqual(decision.action, ACTION_ALERT_USER)
        self.assertIn("Halt auto-restarts", decision.reason)

    def test_crash_storm_triggers_alert_user(self):
        """When frequent crashes occur in the sliding window, engine halts restarts."""
        decision: DecisionOutput = self.engine.decide(
            cpu_percent=10.0,
            ram_percent=20.0,
            disk_percent=30.0,
            current_attempt=1,
            crashes_in_window=MAX_CRASHES_IN_WINDOW + 1,
        )
        self.assertEqual(decision.action, ACTION_ALERT_USER)
        self.assertIn("Crash storm", decision.reason)

    def test_limited_retries_near_quota(self):
        """When only 1-2 attempts remain before maximum, action is RESTART_APPLICATION_WITH_LIMITED_RETRIES."""
        decision: DecisionOutput = self.engine.decide(
            cpu_percent=20.0,
            ram_percent=30.0,
            disk_percent=30.0,
            current_attempt=MAX_RESTART_ATTEMPTS - 1,
            crashes_in_window=1,
        )
        self.assertEqual(decision.action, ACTION_LIMITED_RETRY)
        self.assertGreater(decision.delay_seconds, 0.0)

    def test_decide_runtime_monitor_when_healthy(self):
        """Verifies runtime decision is MONITOR under healthy baseline."""
        decision = self.engine.decide_runtime(
            is_app_running=True,
            risk_category="LOW",
            risk_probability=12.0,
            cpu_percent=25.0,
            ram_percent=40.0,
        )
        self.assertEqual(decision.action, ACTION_MONITOR)
        self.assertGreaterEqual(decision.confidence_score, 0.9)

    def test_decide_runtime_investigate_when_risk_elevated(self):
        """Verifies runtime decision is INVESTIGATE under elevated risk or pressure."""
        decision = self.engine.decide_runtime(
            is_app_running=True,
            risk_category="HIGH",
            risk_probability=88.0,
            cpu_percent=88.0,
            ram_percent=91.0,
        )
        self.assertEqual(decision.action, ACTION_INVESTIGATE)
        self.assertIn("Elevated failure risk", decision.reason)

    def test_decide_runtime_restart_when_app_offline(self):
        """Verifies runtime decision recommends RESTART when app is offline."""
        decision = self.engine.decide_runtime(
            is_app_running=False,
            risk_category="LOW",
            risk_probability=10.0,
            cpu_percent=15.0,
            ram_percent=30.0,
        )
        self.assertEqual(decision.action, ACTION_RESTART)

    def test_configurable_engine_parameters(self):
        """Verifies that RecoveryDecisionEngine accepts and respects custom thresholds and limits."""
        custom_engine = RecoveryDecisionEngine(
            max_attempts=2,
            saturation_cpu=70.0,
            saturation_ram=75.0,
            cooldown_seconds=1.5,
            retry_delay_seconds=0.5,
            max_crashes_in_window=2,
        )
        self.assertEqual(custom_engine.max_attempts, 2)
        self.assertEqual(custom_engine.saturation_cpu, 70.0)
        self.assertEqual(custom_engine.saturation_ram, 75.0)
        self.assertEqual(custom_engine.cooldown_seconds, 1.5)
        self.assertEqual(custom_engine.retry_delay_seconds, 0.5)
        self.assertEqual(custom_engine.max_crashes_in_window, 2)

        # CPU at 72% exceeds custom saturation_cpu=70.0 -> WAIT_AND_RETRY
        dec_resource = custom_engine.decide(
            cpu_percent=72.0, ram_percent=40.0, disk_percent=30.0,
            current_attempt=0, crashes_in_window=0
        )
        self.assertEqual(dec_resource.action, ACTION_WAIT_RETRY)

        # Attempt 2 reaches custom max_attempts=2 -> ALERT_USER
        dec_attempts = custom_engine.decide(
            cpu_percent=10.0, ram_percent=20.0, disk_percent=30.0,
            current_attempt=2, crashes_in_window=0
        )
        self.assertEqual(dec_attempts.action, ACTION_ALERT_USER)

        # 3 crashes in window exceeds custom max_crashes_in_window=2 -> ALERT_USER
        dec_storm = custom_engine.decide(
            cpu_percent=10.0, ram_percent=20.0, disk_percent=30.0,
            current_attempt=0, crashes_in_window=3
        )
        self.assertEqual(dec_storm.action, ACTION_ALERT_USER)

    def test_configurable_auto_restart_parameters(self):
        """Verifies that AutoRestart initializes with custom operational thresholds."""
        custom_engine = RecoveryDecisionEngine(max_attempts=3)
        service = AutoRestart(
            decision_engine=custom_engine,
            max_restart_attempts=3,
            retry_delay_seconds=0.2,
            cooldown_seconds=0.5,
            rapid_crash_window_seconds=30.0,
            max_crashes_in_window=2,
        )
        self.assertEqual(service.max_restart_attempts, 3)
        self.assertEqual(service.retry_delay_seconds, 0.2)
        self.assertEqual(service.cooldown_seconds, 0.5)
        self.assertEqual(service.rapid_crash_window_seconds, 30.0)
        self.assertEqual(service.max_crashes_in_window, 2)
        self.assertIs(service.decision_engine, custom_engine)

    def test_auto_restart_normal_recovery_flow(self):
        """Verifies that AutoRestart executes safe RESTART_APPLICATION upon crash under nominal load."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)

        def fake_start():
            service.process = MagicMock()
            service.process.poll.return_value = None
            service.current_pid = 9999
            return True

        service.start_application = fake_start
        crash = CrashEvent(
            pid=1001,
            timestamp="2026-10-20 18:00:00",
            exit_code=1,
            failure_reason="SIGSEGV exit code 1",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=15.0, ram_percent=35.0, disk_percent=40.0,
                cpu_change=0.0, ram_change=0.0
            )
            service.handle_detected_crash(crash)

        self.assertEqual(service.total_crashes, 1)
        self.assertEqual(service.total_restarts, 1)
        self.assertEqual(service.successful_recoveries, 1)
        self.assertEqual(service.last_failed_pid, 1001)
        self.assertEqual(service.last_recovered_pid, 9999)
        self.assertIsNotNone(service.last_recovery_event)
        self.assertEqual(service.last_recovery_event["recovery_status"], "SUCCESS")
        self.assertEqual(service.last_recovery_event["old_pid"], 1001)
        self.assertEqual(service.last_recovery_event["new_pid"], 9999)
        self.assertEqual(service.last_decision.action, ACTION_RESTART)

    def test_auto_restart_wait_and_retry_flow(self):
        """Verifies that AutoRestart cools down under resource saturation then successfully recovers."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)

        def fake_start():
            service.process = MagicMock()
            service.process.poll.return_value = None
            service.current_pid = 8888
            return True

        service.start_application = fake_start
        crash = CrashEvent(
            pid=1002,
            timestamp="2026-10-20 18:01:00",
            exit_code=1,
            failure_reason="OOM Exit",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=95.0, ram_percent=40.0, disk_percent=40.0,
                cpu_change=5.0, ram_change=0.0
            )
            service.handle_detected_crash(crash)

        self.assertEqual(service.last_decision.action, ACTION_WAIT_RETRY)
        self.assertEqual(service.total_restarts, 1)
        self.assertEqual(service.successful_recoveries, 1)
        self.assertEqual(service.last_recovered_pid, 8888)
        self.assertEqual(service.last_recovery_event["recovery_status"], "SUCCESS")

    def test_auto_restart_max_attempts_triggers_alert_user(self):
        """Verifies that AutoRestart halts restarts and alerts user when retry quota is exhausted."""
        service = AutoRestart(max_restart_attempts=3, retry_delay_seconds=0.001, cooldown_seconds=0.001)
        service.total_restarts = 3  # Quota reached

        service.start_application = MagicMock()
        crash = CrashEvent(
            pid=1003,
            timestamp="2026-10-20 18:02:00",
            exit_code=1,
            failure_reason="Persistent Crash",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=20.0, ram_percent=30.0, disk_percent=30.0,
                cpu_change=0.0, ram_change=0.0
            )
            service.handle_detected_crash(crash)

        self.assertEqual(service.last_decision.action, ACTION_ALERT_USER)
        service.start_application.assert_not_called()
        self.assertEqual(service.failed_recoveries, 1)
        self.assertEqual(service.total_restarts, 3)  # Did not increment restart count
        self.assertIn("HALTED", service.recovery_state)
        self.assertEqual(service.last_recovery_event["recovery_status"], "FAILED")
        self.assertIsNone(service.last_recovery_event["new_pid"])

    def test_auto_restart_crash_storm_triggers_alert_user(self):
        """Verifies that AutoRestart stops restarts and alerts user when rapid crash threshold is exceeded."""
        service = AutoRestart(max_crashes_in_window=3, rapid_crash_window_seconds=60.0, retry_delay_seconds=0.001)
        now = time.time()
        service.crash_timestamps = [now - 10, now - 8, now - 5]
        service.start_application = MagicMock()

        crash = CrashEvent(
            pid=1004,
            timestamp="2026-10-20 18:03:00",
            exit_code=1,
            failure_reason="Crash Storm",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=20.0, ram_percent=30.0, disk_percent=30.0,
                cpu_change=0.0, ram_change=0.0
            )
            service.handle_detected_crash(crash)

        self.assertEqual(service.last_decision.action, ACTION_ALERT_USER)
        service.start_application.assert_not_called()
        self.assertEqual(service.failed_recoveries, 1)
        self.assertIn("HALTED", service.recovery_state)

    def test_auto_restart_duplicate_crash_event_suppression(self):
        """Verifies that duplicate crash signals for the same PID are suppressed."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)

        def fake_start():
            service.process = MagicMock()
            service.process.poll.return_value = None
            service.current_pid = 7777
            return True

        service.start_application = fake_start
        crash = CrashEvent(
            pid=1005,
            timestamp="2026-10-20 18:04:00",
            exit_code=1,
            failure_reason="Crash",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=15.0, ram_percent=30.0, disk_percent=30.0,
                cpu_change=0.0, ram_change=0.0
            )
            # First crash event
            service.handle_detected_crash(crash)
            self.assertEqual(service.total_crashes, 1)
            self.assertEqual(service.total_restarts, 1)

            # Duplicate crash event with identical PID
            service.handle_detected_crash(crash)
            self.assertEqual(service.total_crashes, 1)
            self.assertEqual(service.total_restarts, 1)

    def test_auto_restart_concurrent_restart_suppression(self):
        """Verifies that concurrent restart attempts while recovery is active are safely rejected."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)
        service.start_application = MagicMock()

        # Mark recovery currently in progress
        service._recovery_in_progress = True

        crash = CrashEvent(
            pid=1006,
            timestamp="2026-10-20 18:05:00",
            exit_code=1,
            failure_reason="Concurrent Race",
            is_unexpected=True,
            detected_at=time.time(),
        )
        service.handle_detected_crash(crash)

        # Must be suppressed immediately
        self.assertEqual(service.total_crashes, 0)
        self.assertEqual(service.total_restarts, 0)
        service.start_application.assert_not_called()

    def test_feature_5_recovery_history_and_sla_intact_under_policy(self):
        """Verifies that Recovery History and SLA telemetry remain fully functional under Feature 6 policy."""
        service = AutoRestart(retry_delay_seconds=0.001, cooldown_seconds=0.001)
        service.sla_target_sec = 2.5

        def fake_start():
            service.process = MagicMock()
            service.process.poll.return_value = None
            service.current_pid = 5555
            return True

        service.start_application = fake_start
        crash = CrashEvent(
            pid=1007,
            timestamp="2026-10-20 18:06:00",
            exit_code=1,
            failure_reason="Policy Check",
            is_unexpected=True,
            detected_at=time.time(),
        )

        with patch("recovery.auto_restart.get_system_stats") as mock_stats:
            mock_stats.return_value = self._make_metrics(
                cpu_percent=15.0, ram_percent=30.0, disk_percent=30.0,
                cpu_change=0.0, ram_change=0.0
            )
            service.handle_detected_crash(crash)

        self.assertEqual(len(service.recovery_history), 1)
        entry = service.recovery_history[0]
        self.assertEqual(entry["application_name"], "HealOS-DummyApp")
        self.assertEqual(entry["old_pid"], 1007)
        self.assertEqual(entry["new_pid"], 5555)
        self.assertEqual(entry["recovery_status"], "SUCCESS")
        self.assertTrue(entry["sla_met"])
        self.assertIn("RESTART_APPLICATION", entry["recovery_action"])


if __name__ == "__main__":
    unittest.main()
