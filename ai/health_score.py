"""
HealOS 2.0 - System Health Analyzer
Calculates composite and subsystem health scores (0 - 100) based on real-time
telemetry and process stability metrics.

NOTE: This is a deterministic multi-criteria scoring algorithm based on
weighted thresholds, NOT a statistical machine learning model.
"""

import math
from dataclasses import dataclass
from typing import Dict, Any

from config import (
    HEALTH_WEIGHT_CPU,
    HEALTH_WEIGHT_RAM,
    HEALTH_WEIGHT_DISK,
    HEALTH_WEIGHT_STABILITY,
    HEALTH_SCORE_HEALTHY,
    HEALTH_SCORE_WARNING,
)


@dataclass
class HealthScoreReport:
    """Encapsulates system and application health scores."""
    cpu_score: float
    ram_score: float
    disk_score: float
    stability_score: float
    overall_score: float
    risk_category: str           # "HEALTHY", "DEGRADED", "CRITICAL"
    recommendation: str
    weights: Dict[str, float]
    primary_degraded_metric: str = "None (All Nominal)"
    lowest_component_score: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_score": self.cpu_score,
            "ram_score": self.ram_score,
            "disk_score": self.disk_score,
            "stability_score": self.stability_score,
            "overall_score": self.overall_score,
            "risk_category": self.risk_category,
            "recommendation": self.recommendation,
            "primary_degraded_metric": self.primary_degraded_metric,
            "lowest_component_score": self.lowest_component_score,
            "weights": self.weights,
        }


class HealthAnalyzer:
    """
    Computes transparent multi-subsystem health scores from OS metrics
    and application stability history.
    """

    def __init__(
        self,
        weight_cpu: float = HEALTH_WEIGHT_CPU,
        weight_ram: float = HEALTH_WEIGHT_RAM,
        weight_disk: float = HEALTH_WEIGHT_DISK,
        weight_stability: float = HEALTH_WEIGHT_STABILITY,
    ):
        # Normalize weights if necessary
        total = weight_cpu + weight_ram + weight_disk + weight_stability
        self.w_cpu = weight_cpu / total
        self.w_ram = weight_ram / total
        self.w_disk = weight_disk / total
        self.w_stability = weight_stability / total

    def calculate_health(
        self,
        cpu_percent: float,
        ram_percent: float,
        disk_percent: float,
        is_app_running: bool,
        recent_crashes_count: int = 0,
        total_restarts: int = 0,
    ) -> HealthScoreReport:
        """
        Calculates health scores (0 to 100) across all subsystems with robust sanitization
        and root-cause identification for degraded scores.
        """
        # 0. Sanitize inputs (gracefully handle None, NaN, Inf, strings, out-of-range values)
        try:
            c_pct = float(cpu_percent) if cpu_percent is not None else 0.0
            r_pct = float(ram_percent) if ram_percent is not None else 0.0
            d_pct = float(disk_percent) if disk_percent is not None else 0.0
            app_alive = bool(is_app_running)
            c_cnt = int(recent_crashes_count) if recent_crashes_count is not None else 0
            r_cnt = int(total_restarts) if total_restarts is not None else 0
        except (ValueError, TypeError):
            c_pct, r_pct, d_pct = 0.0, 0.0, 0.0
            app_alive = False
            c_cnt, r_cnt = 0, 0

        if math.isnan(c_pct) or math.isinf(c_pct): c_pct = 0.0
        if math.isnan(r_pct) or math.isinf(r_pct): r_pct = 0.0
        if math.isnan(d_pct) or math.isinf(d_pct): d_pct = 0.0

        c_pct = max(0.0, min(100.0, c_pct))
        r_pct = max(0.0, min(100.0, r_pct))
        d_pct = max(0.0, min(100.0, d_pct))
        c_cnt = max(0, c_cnt)
        r_cnt = max(0, r_cnt)

        # 1. CPU Health Score: Inverted utilization with nonlinear penalty above 80%
        if c_pct < 80.0:
            cpu_score = max(0.0, 100.0 - c_pct)
        else:
            cpu_score = max(0.0, 20.0 - ((c_pct - 80.0) * 1.0))

        # 2. RAM Health Score: Inverted utilization with nonlinear penalty above 85%
        if r_pct < 85.0:
            ram_score = max(0.0, 100.0 - r_pct)
        else:
            ram_score = max(0.0, 15.0 - ((r_pct - 85.0) * 1.0))

        # 3. Disk Health Score
        disk_score = max(0.0, 100.0 - d_pct)

        # 4. Application Stability Score (Base: 100, penalties for outages and crash churn)
        stability_score = 100.0
        if not app_alive:
            stability_score -= 45.0
        stability_score -= min(40.0, c_cnt * 15.0)
        stability_score -= min(15.0, r_cnt * 3.0)
        stability_score = max(0.0, min(100.0, stability_score))

        # Round individual scores
        cpu_score = round(cpu_score, 1)
        ram_score = round(ram_score, 1)
        disk_score = round(disk_score, 1)
        stability_score = round(stability_score, 1)

        # 5. Composite Weighted Overall Score
        overall = (
            (cpu_score * self.w_cpu)
            + (ram_score * self.w_ram)
            + (disk_score * self.w_disk)
            + (stability_score * self.w_stability)
        )
        overall_score = round(max(0.0, min(100.0, overall)), 1)

        # 6. Identify the actual metric responsible for degraded score
        components = [
            ("Application Stability", stability_score, "stability"),
            ("Host Memory", ram_score, "ram"),
            ("CPU Load", cpu_score, "cpu"),
            ("Disk Storage", disk_score, "disk"),
        ]
        worst_name, worst_score, worst_key = min(components, key=lambda x: x[1])

        # 7. Categorization & Actionable Guidance
        if overall_score >= HEALTH_SCORE_HEALTHY:
            risk_category = "HEALTHY"
            primary_degraded_metric = "None (All Nominal)"
            recommendation = "All monitored subsystems operating within optimal performance envelopes."
        elif overall_score >= HEALTH_SCORE_WARNING:
            risk_category = "DEGRADED"
            primary_degraded_metric = f"{worst_name} ({worst_score:.0f}/100)"
            if worst_key == "stability":
                if not app_alive:
                    recommendation = "Application offline. Automatic recovery daemon engaged."
                else:
                    recommendation = f"Application instability detected ({c_cnt} recent crashes). Review crash logs."
            elif worst_key == "ram":
                recommendation = f"High RAM pressure ({r_pct:.1f}% used). Monitor process memory growth."
            elif worst_key == "cpu":
                recommendation = f"Elevated CPU contention ({c_pct:.1f}% used). Throttle background tasks."
            else:
                recommendation = f"Low disk headroom ({d_pct:.1f}% used). Purge temporary log archives."
        else:
            risk_category = "CRITICAL"
            primary_degraded_metric = f"{worst_name} ({worst_score:.0f}/100)"
            if not app_alive:
                recommendation = "CRITICAL: Monitored application offline. Auto-restart initiated."
            elif r_pct >= 90.0 or c_pct >= 90.0:
                recommendation = f"CRITICAL SATURATION: {worst_name} exhausted. Immediate recovery required."
            else:
                recommendation = f"CRITICAL IMPAIRMENT: Severe degradation in {worst_name}."

        return HealthScoreReport(
            cpu_score=cpu_score,
            ram_score=ram_score,
            disk_score=disk_score,
            stability_score=stability_score,
            overall_score=overall_score,
            risk_category=risk_category,
            recommendation=recommendation,
            primary_degraded_metric=primary_degraded_metric,
            lowest_component_score=worst_score,
            weights={
                "cpu": round(self.w_cpu, 2),
                "ram": round(self.w_ram, 2),
                "disk": round(self.w_disk, 2),
                "stability": round(self.w_stability, 2),
            },
        )
