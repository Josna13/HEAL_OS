"""
Unit tests for System Health Analyzer (ai/health_score.py).
Tests subsystem scores (CPU, RAM, Disk, Stability), weighting normalization,
categorical risk assignment (HEALTHY, DEGRADED, CRITICAL), root cause identification,
and robust input sanitization.
"""

import math
import unittest
from ai.health_score import HealthAnalyzer, HealthScoreReport


class TestHealthAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = HealthAnalyzer()

    def test_nominal_health_score(self):
        """Tests that nominal utilization scores >= 80.0 and categorizes as HEALTHY."""
        report: HealthScoreReport = self.analyzer.calculate_health(
            cpu_percent=10.0,
            ram_percent=25.0,
            disk_percent=30.0,
            is_app_running=True,
            recent_crashes_count=0,
            total_restarts=0,
        )
        self.assertGreaterEqual(report.overall_score, 80.0)
        self.assertEqual(report.risk_category, "HEALTHY")
        self.assertGreaterEqual(report.stability_score, 90.0)
        self.assertEqual(report.primary_degraded_metric, "None (All Nominal)")
        self.assertIn("optimal", report.recommendation.lower())

    def test_degraded_state_due_to_memory_pressure(self):
        """Tests that severe RAM pressure produces a DEGRADED score with Host Memory as primary cause."""
        report: HealthScoreReport = self.analyzer.calculate_health(
            cpu_percent=20.0,
            ram_percent=86.0,
            disk_percent=20.0,
            is_app_running=True,
            recent_crashes_count=0,
            total_restarts=0,
        )
        self.assertGreaterEqual(report.overall_score, 50.0)
        self.assertLess(report.overall_score, 80.0)
        self.assertEqual(report.risk_category, "DEGRADED")
        self.assertIn("Host Memory", report.primary_degraded_metric)
        self.assertIn("RAM pressure", report.recommendation)

    def test_degraded_state_due_to_crashes(self):
        """Tests that process crash history penalizes stability and flags Application Stability."""
        report: HealthScoreReport = self.analyzer.calculate_health(
            cpu_percent=15.0,
            ram_percent=20.0,
            disk_percent=20.0,
            is_app_running=True,
            recent_crashes_count=2,
            total_restarts=2,
        )
        self.assertGreaterEqual(report.overall_score, 50.0)
        self.assertLess(report.overall_score, 80.0)
        self.assertEqual(report.risk_category, "DEGRADED")
        self.assertIn("Application Stability", report.primary_degraded_metric)
        self.assertIn("instability", report.recommendation.lower())

    def test_critical_threshold(self):
        """Tests that combined resource saturation and outage yields CRITICAL category."""
        report: HealthScoreReport = self.analyzer.calculate_health(
            cpu_percent=95.0,
            ram_percent=98.0,
            disk_percent=95.0,
            is_app_running=False,
            recent_crashes_count=4,
            total_restarts=4,
        )
        self.assertLess(report.overall_score, 50.0)
        self.assertEqual(report.risk_category, "CRITICAL")
        self.assertIn("CRITICAL", report.recommendation)

    def test_invalid_and_missing_metrics_sanitization(self):
        """Verifies None, NaN, Inf, negative numbers, and type errors are sanitized safely."""
        # 1. All None
        report_none = self.analyzer.calculate_health(
            cpu_percent=None,
            ram_percent=None,
            disk_percent=None,
            is_app_running=None,
            recent_crashes_count=None,
            total_restarts=None,
        )
        self.assertIsInstance(report_none, HealthScoreReport)
        self.assertFalse(math.isnan(report_none.overall_score))
        self.assertFalse(math.isinf(report_none.overall_score))

        # 2. NaN and Inf
        report_nan = self.analyzer.calculate_health(
            cpu_percent=float("nan"),
            ram_percent=float("inf"),
            disk_percent=float("-inf"),
            is_app_running=True,
        )
        self.assertIsInstance(report_nan, HealthScoreReport)
        self.assertGreaterEqual(report_nan.overall_score, 0.0)
        self.assertLessEqual(report_nan.overall_score, 100.0)

        # 3. String & type mismatch
        report_types = self.analyzer.calculate_health(
            cpu_percent="invalid",
            ram_percent=[100],
            disk_percent={"bad": 1},
            is_app_running=False,
        )
        self.assertIsInstance(report_types, HealthScoreReport)
        self.assertEqual(report_types.cpu_score, 100.0)  # defaulted 0% usage -> 100% health

    def test_boundary_metrics_clamping(self):
        """Verifies boundary values >100% or <0% are clamped to valid ranges."""
        report = self.analyzer.calculate_health(
            cpu_percent=250.0,
            ram_percent=-50.0,
            disk_percent=150.0,
            is_app_running=True,
            recent_crashes_count=-5,
            total_restarts=-1,
        )
        self.assertEqual(report.cpu_score, 0.0)      # clamped to 100% usage -> 0% health
        self.assertEqual(report.ram_score, 100.0)    # clamped to 0% usage -> 100% health
        self.assertEqual(report.disk_score, 0.0)     # clamped to 100% usage -> 0% health
        self.assertGreaterEqual(report.overall_score, 0.0)
        self.assertLessEqual(report.overall_score, 100.0)

    def test_custom_weights_sum_to_one(self):
        """Verifies weight normalization when custom coefficients are provided."""
        custom_analyzer = HealthAnalyzer(
            weight_cpu=2.0, weight_ram=2.0, weight_disk=1.0, weight_stability=5.0
        )
        total_w = (
            custom_analyzer.w_cpu
            + custom_analyzer.w_ram
            + custom_analyzer.w_disk
            + custom_analyzer.w_stability
        )
        self.assertAlmostEqual(total_w, 1.0, places=4)

    def test_health_report_to_dict(self):
        """Verifies serialization includes all required schema fields."""
        report = self.analyzer.calculate_health(
            cpu_percent=10.0,
            ram_percent=20.0,
            disk_percent=30.0,
            is_app_running=True,
        )
        d = report.to_dict()
        required_keys = [
            "cpu_score",
            "ram_score",
            "disk_score",
            "stability_score",
            "overall_score",
            "risk_category",
            "recommendation",
            "primary_degraded_metric",
            "lowest_component_score",
            "weights",
        ]
        for k in required_keys:
            self.assertIn(k, d)


if __name__ == "__main__":
    unittest.main()
