"""
Unit tests for AI Failure Predictor (ai/predictor.py).
Tests:
- Deterministic normal conditions (LOW risk, nominal signals, timestamp)
- Deterministic elevated risk (High CPU, Memory saturation, Rapid surges)
- Specific measured warning signals extraction
- Repeated crashes factor in risk prediction
- Unavailable model handling (clear warnings, heuristic fallback active)
- Invalid input values sanitization (None, NaN, Inf, negatives, boundary extremes)
- Serialization to dictionary
"""

import math
import unittest
from pathlib import Path
from ai.predictor import FailurePredictor, PredictionResult


class TestFailurePredictor(unittest.TestCase):

    def setUp(self):
        self.predictor = FailurePredictor()

    def test_predictor_initialization(self):
        """Verifies predictor initializes and reports model availability status."""
        self.assertIsNotNone(self.predictor)
        self.assertIsInstance(self.predictor.is_model_available(), bool)

    def test_predict_risk_nominal_conditions(self):
        """Tests that nominal, relaxed resource usage yields LOW risk."""
        result: PredictionResult = self.predictor.predict_risk(
            cpu_percent=15.0,
            ram_percent=30.0,
            disk_percent=40.0,
            process_count=120,
            cpu_change=0.0,
            ram_change=0.0,
        )
        self.assertIsInstance(result, PredictionResult)
        self.assertGreaterEqual(result.risk_probability, 0.0)
        self.assertLessEqual(result.risk_probability, 100.0)
        self.assertEqual(result.risk_category, "LOW")
        self.assertTrue(result.is_synthetic_estimate)
        self.assertTrue(len(result.timestamp) > 0)

    def test_predict_risk_high_stress_conditions(self):
        """Tests that extreme resource exhaustion yields elevated risk."""
        result: PredictionResult = self.predictor.predict_risk(
            cpu_percent=95.0,
            ram_percent=96.0,
            disk_percent=94.0,
            process_count=450,
            cpu_change=30.0,
            ram_change=25.0,
        )
        self.assertIn(result.risk_category, ["MEDIUM", "HIGH"])
        self.assertGreater(result.risk_probability, 50.0)
        self.assertIn("CRITICAL", result.recommendation.upper())

    def test_fallback_heuristic_calculation(self):
        """Tests that fallback calculation responds proportionally to memory surge."""
        score_low = FailurePredictor._heuristic_fallback_probability(
            cpu=20.0, ram=30.0, disk=20.0, cpu_delta=0.0, ram_delta=0.0
        )
        score_high = FailurePredictor._heuristic_fallback_probability(
            cpu=90.0, ram=92.0, disk=85.0, cpu_delta=10.0, ram_delta=15.0
        )
        self.assertLess(score_low, 20.0)
        self.assertGreater(score_high, 70.0)

    def test_nonexistent_model_fallback(self):
        """Verifies graceful degradation when model path does not exist."""
        bogus_path = Path("ai/nonexistent_model_123.pkl")
        fallback_predictor = FailurePredictor(model_path=bogus_path)
        self.assertFalse(fallback_predictor.is_model_available())

        result = fallback_predictor.predict_risk(
            cpu_percent=20.0,
            ram_percent=25.0,
            disk_percent=30.0,
            process_count=100,
            cpu_change=0.0,
            ram_change=0.0,
        )
        self.assertFalse(result.model_loaded)
        self.assertIn(result.risk_category, ["LOW", "MEDIUM", "HIGH"])
        self.assertTrue(any("unavailable" in s.lower() for s in result.warning_signals))

    def test_heuristic_fallback_when_model_is_none(self):
        """Verifies predictor gracefully falls back to heuristic scoring when model is None."""
        self.predictor.model = None
        self.assertFalse(self.predictor.is_model_available())

        result = self.predictor.predict_risk(
            cpu_percent=10.0,
            ram_percent=20.0,
            disk_percent=15.0,
            process_count=80,
            cpu_change=0.0,
            ram_change=0.0,
        )
        self.assertFalse(result.model_loaded)
        self.assertEqual(result.risk_category, "LOW")
        self.assertGreaterEqual(result.risk_probability, 0.0)
        self.assertIn("Model Unavailable", result.recommendation)

    def test_resilience_to_boundary_inputs(self):
        """Verifies predictor clamps values properly on out-of-range inputs."""
        result = self.predictor.predict_risk(
            cpu_percent=150.0,
            ram_percent=200.0,
            disk_percent=100.0,
            process_count=999,
            cpu_change=50.0,
            ram_change=50.0,
        )
        self.assertLessEqual(result.risk_probability, 100.0)
        self.assertGreaterEqual(result.risk_probability, 0.0)
        self.assertEqual(result.risk_category, "HIGH")

    def test_deterministic_normal_conditions(self):
        """Verifies deterministic nominal inputs produce LOW risk with clean warning summary."""
        result = self.predictor.predict_risk(
            cpu_percent=12.0,
            ram_percent=28.0,
            disk_percent=35.0,
            process_count=110,
            cpu_change=0.0,
            ram_change=0.0,
            app_cpu_percent=0.5,
            app_memory_percent=1.2,
            recent_crashes_count=0,
        )
        self.assertEqual(result.risk_category, "LOW")
        self.assertLess(result.risk_probability, 35.0)
        self.assertTrue(len(result.timestamp) > 0)
        # In model loaded mode, nominal conditions produce 0 warnings
        if result.model_loaded:
            self.assertEqual(len(result.warning_signals), 0)
            self.assertIn("nominal", result.warning_summary.lower())

    def test_deterministic_elevated_risk_warning_signals(self):
        """Verifies specific measured warning signals for CPU contention and RAM surge."""
        result = self.predictor.predict_risk(
            cpu_percent=92.0,
            ram_percent=88.0,
            disk_percent=50.0,
            process_count=420,
            cpu_change=18.0,
            ram_change=10.0,
            app_cpu_percent=85.0,
            app_memory_percent=12.0,
            recent_crashes_count=0,
        )
        self.assertIn(result.risk_category, ["MEDIUM", "HIGH"])
        self.assertGreaterEqual(result.risk_probability, 50.0)

        # Verify only actually measured warning signals are present
        signals_text = " ".join(result.warning_signals)
        self.assertIn("High CPU", signals_text)
        self.assertIn("High memory", signals_text)
        self.assertIn("Surging CPU", signals_text)
        self.assertIn("Increasing memory", signals_text)
        self.assertIn("Process table", signals_text)

    def test_deterministic_repeated_crashes_signal(self):
        """Verifies repeated crashes are flagged in measured warning signals."""
        result = self.predictor.predict_risk(
            cpu_percent=20.0,
            ram_percent=30.0,
            disk_percent=40.0,
            process_count=100,
            cpu_change=0.0,
            ram_change=0.0,
            recent_crashes_count=3,
        )
        signals_text = " ".join(result.warning_signals)
        self.assertIn("Repeated crashes (3 recent)", signals_text)
        self.assertGreaterEqual(result.risk_probability, 40.0)

    def test_invalid_input_values_sanitization(self):
        """Verifies None, NaN, Inf, negatives, and type errors are sanitized safely."""
        result = self.predictor.predict_risk(
            cpu_percent=None,
            ram_percent=float("nan"),
            disk_percent=float("inf"),
            process_count=-50,
            cpu_change=-999.0,
            ram_change=None,
        )
        self.assertIsInstance(result, PredictionResult)
        self.assertGreaterEqual(result.risk_probability, 0.0)
        self.assertLessEqual(result.risk_probability, 100.0)
        self.assertIn(result.risk_category, ["LOW", "MEDIUM", "HIGH"])

    def test_prediction_result_to_dict(self):
        """Verifies serialization includes all required schema fields."""
        result = self.predictor.predict_risk(25.0, 35.0, 45.0, 120, 0.0, 0.0)
        d = result.to_dict()
        self.assertIn("risk_probability", d)
        self.assertIn("risk_category", d)
        self.assertIn("recommendation", d)
        self.assertIn("model_loaded", d)
        self.assertIn("timestamp", d)
        self.assertIn("warning_signals", d)
        self.assertIn("warning_summary", d)
        self.assertIn("is_synthetic_estimate", d)


if __name__ == "__main__":
    unittest.main()
