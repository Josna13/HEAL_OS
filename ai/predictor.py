"""
HealOS 2.0 - AI Predictive Failure Analyzer
Evaluates real-time system metrics against the trained Random Forest classifier
to compute a prototype crash-risk probability (0-100%), categorize threat level,
and generate preventive recommendations.

IMPORTANT ACADEMIC NOTICE:
Because this model is trained on synthetic OS telemetry, this output represents
a prototype risk estimation rather than a validated empirical prediction of real
application crash timing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import math
import warnings

try:
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except Exception:
    pass

try:
    import joblib
except ImportError:
    joblib = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

from config import (
    MODEL_FILE,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    FEATURE_COLUMNS,
)
from logger.healos_logger import get_system_logger, get_error_logger


@dataclass
class PredictionResult:
    """Encapsulates predictive analysis output and actionable recommendations."""
    risk_probability: float      # 0.0 to 100.0 %
    risk_category: str           # "LOW", "MEDIUM", "HIGH"
    recommendation: str          # Actionable system guidance
    model_loaded: bool           # True if scikit-learn model artifact is active
    timestamp: str = ""          # Prediction timestamp (e.g., "16:55:02")
    warning_signals: List[str] = field(default_factory=list) # Specific measured warning signals
    warning_summary: str = "None"
    is_synthetic_estimate: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_probability": self.risk_probability,
            "risk_category": self.risk_category,
            "recommendation": self.recommendation,
            "model_loaded": self.model_loaded,
            "timestamp": self.timestamp,
            "warning_signals": list(self.warning_signals),
            "warning_summary": self.warning_summary,
            "is_synthetic_estimate": self.is_synthetic_estimate,
        }


class FailurePredictor:
    """
    AI Failure Predictor utilizing scikit-learn Random Forest model.
    Includes robust fallback calculation if the model artifact has not been trained.
    """

    def __init__(self, model_path: Path = MODEL_FILE):
        self.model_path = model_path
        self.model = None
        self.logger = get_system_logger()
        self.load_model()

    def load_model(self) -> bool:
        """Loads trained model weights from disk."""
        if joblib is None:
            self.logger.warning(
                "joblib is not installed in current Python environment. "
                "AI Failure Predictor running in heuristic fallback mode. "
                "(To enable trained scikit-learn model, run inside virtual environment: source venv/bin/activate)"
            )
            self.model = None
            return False

        if not self.model_path.exists():
            self.logger.warning(
                f"Model file '{self.model_path}' not found. "
                "Predictor will use fallback rule-based risk estimation. "
                "Train the model using: python ai/train_model.py"
            )
            self.model = None
            return False

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.model = joblib.load(self.model_path)
            self.logger.info(f"AI Failure Predictor successfully loaded model: {self.model_path}")
            return True
        except Exception as e:
            get_error_logger().error(f"Failed to load model from {self.model_path}: {e}")
            self.model = None
            return False

    def is_model_available(self) -> bool:
        """Returns True if the ML model is currently active."""
        return self.model is not None

    def predict_risk(
        self,
        cpu_percent: float,
        ram_percent: float,
        disk_percent: float,
        process_count: int,
        cpu_change: float,
        ram_change: float,
        app_cpu_percent: float = 0.0,
        app_memory_percent: float = 0.0,
        recent_crashes_count: int = 0,
    ) -> PredictionResult:
        """
        Estimates failure risk from the provided telemetry features using
        the trained Random Forest classifier with graceful heuristic fallback.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. Input sanitization (gracefully handle None, NaN, strings, or extreme values)
        try:
            c_pct = float(cpu_percent) if cpu_percent is not None else 0.0
            r_pct = float(ram_percent) if ram_percent is not None else 0.0
            d_pct = float(disk_percent) if disk_percent is not None else 0.0
            p_cnt = int(process_count) if process_count is not None else 0
            c_chg = float(cpu_change) if cpu_change is not None else 0.0
            r_chg = float(ram_change) if ram_change is not None else 0.0
            a_cpu = float(app_cpu_percent) if app_cpu_percent is not None else 0.0
            a_mem = float(app_memory_percent) if app_memory_percent is not None else 0.0
            c_cnt = int(recent_crashes_count) if recent_crashes_count is not None else 0
        except (ValueError, TypeError):
            c_pct, r_pct, d_pct, p_cnt, c_chg, r_chg = 0.0, 0.0, 0.0, 0, 0.0, 0.0
            a_cpu, a_mem, c_cnt = 0.0, 0.0, 0

        # Handle NaN/Inf
        if math.isnan(c_pct) or math.isinf(c_pct): c_pct = 0.0
        if math.isnan(r_pct) or math.isinf(r_pct): r_pct = 0.0
        if math.isnan(d_pct) or math.isinf(d_pct): d_pct = 0.0
        if math.isnan(c_chg) or math.isinf(c_chg): c_chg = 0.0
        if math.isnan(r_chg) or math.isinf(r_chg): r_chg = 0.0

        # Clamp percentages to physical boundaries [0.0, 100.0]
        c_pct = max(0.0, min(100.0, c_pct))
        r_pct = max(0.0, min(100.0, r_pct))
        d_pct = max(0.0, min(100.0, d_pct))
        p_cnt = max(0, p_cnt)
        c_chg = max(-100.0, min(100.0, c_chg))
        r_chg = max(-100.0, min(100.0, r_chg))

        # 2. Extract strictly measured warning signals from actual metrics
        warning_signals: List[str] = []
        if c_pct >= 85.0:
            warning_signals.append(f"High CPU usage ({c_pct:.1f}%)")
        elif a_cpu >= 70.0:
            warning_signals.append(f"High app CPU ({a_cpu:.1f}%)")

        if r_pct >= 85.0:
            warning_signals.append(f"High memory usage ({r_pct:.1f}%)")

        if r_chg >= 8.0:
            warning_signals.append(f"Increasing memory consumption (+{r_chg:.1f}%)")

        if c_chg >= 15.0:
            warning_signals.append(f"Surging CPU consumption (+{c_chg:.1f}%)")

        if d_pct >= 90.0:
            warning_signals.append(f"Storage capacity near exhaustion ({d_pct:.1f}%)")

        if p_cnt >= 400:
            warning_signals.append(f"Process table contention ({p_cnt} tasks)")

        if c_cnt > 0:
            warning_signals.append(f"Repeated crashes ({c_cnt} recent)")

        # 3. Model Inference or Fallback
        model_loaded = False
        if self.model is not None:
            try:
                if pd is not None:
                    features = pd.DataFrame(
                        [[c_pct, r_pct, d_pct, p_cnt, c_chg, r_chg]],
                        columns=FEATURE_COLUMNS,
                    )
                elif np is not None:
                    features = np.array([[c_pct, r_pct, d_pct, p_cnt, c_chg, r_chg]])
                else:
                    features = [[c_pct, r_pct, d_pct, p_cnt, c_chg, r_chg]]

                # Binary classifier probabilities: [P(Normal), P(Risk)]
                proba = self.model.predict_proba(features)[0]
                risk_prob = float(proba[1]) * 100.0
                model_loaded = True
            except Exception as e:
                get_error_logger().warning(f"Error during ML inference, using fallback: {e}")
                risk_prob = self._heuristic_fallback_probability(c_pct, r_pct, d_pct, c_chg, r_chg)
                model_loaded = False
        else:
            # Model artifact absent or ML packages not installed
            risk_prob = self._heuristic_fallback_probability(c_pct, r_pct, d_pct, c_chg, r_chg)
            model_loaded = False

        if not model_loaded:
            warning_signals.append("ML model unavailable (using heuristic rules)")

        warning_summary = "; ".join(warning_signals) if warning_signals else "None (telemetry nominal)"

        # Factor in repeated crashes into risk score
        if c_cnt >= 3:
            risk_prob = max(risk_prob, 80.0)
        elif c_cnt >= 1:
            risk_prob = max(risk_prob, 40.0)

        risk_prob = max(0.0, min(100.0, round(risk_prob, 2)))

        # 4. Categorize risk according to thresholds
        prob_fraction = risk_prob / 100.0
        if prob_fraction < RISK_THRESHOLD_LOW:
            risk_category = "LOW"
            if model_loaded:
                recommendation = "Operating conditions optimal. Telemetry within nominal envelope."
            else:
                recommendation = "[WARNING: Model Unavailable] Heuristic estimate: conditions normal."
        elif prob_fraction < RISK_THRESHOLD_MEDIUM:
            risk_category = "MEDIUM"
            if warning_signals:
                recommendation = f"Moderate failure risk: {warning_summary}. Surveillance heightened."
            else:
                recommendation = "Moderate telemetry fluctuation. Standing by."
        else:
            risk_category = "HIGH"
            if warning_signals:
                recommendation = f"CRITICAL: {warning_summary}. Prepare recovery daemon."
            else:
                recommendation = "CRITICAL: High failure risk predicted. Proactive restart advised."

        return PredictionResult(
            risk_probability=risk_prob,
            risk_category=risk_category,
            recommendation=recommendation,
            model_loaded=model_loaded,
            timestamp=timestamp,
            warning_signals=warning_signals,
            warning_summary=warning_summary,
            is_synthetic_estimate=True,
        )

    @staticmethod
    def _heuristic_fallback_probability(
        cpu: float, ram: float, disk: float, cpu_delta: float, ram_delta: float
    ) -> float:
        """Calculates an explainable fallback risk score when the ML model is unavailable."""
        score = 5.0  # Baseline
        if ram > 85.0:
            score += 45.0
        elif ram > 70.0:
            score += 20.0

        if ram_delta > 10.0:
            score += 25.0

        if cpu > 88.0:
            score += 25.0
        elif cpu > 75.0:
            score += 10.0

        if disk > 90.0:
            score += 15.0

        return min(100.0, score)
