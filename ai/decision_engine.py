"""
HealOS 2.0 - AI Recovery Decision Engine
Transparent, explainable decision-making engine that analyzes system stress,
failure context, recent restart frequency, and resource saturation to recommend
safe, non-destructive recovery actions and prevent infinite restart loops.

NOTE: This module employs an explainable heuristic decision framework rather than
a statistical machine learning model.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from config import (
    MAX_RESTART_ATTEMPTS,
    RESOURCE_SATURATION_CPU,
    RESOURCE_SATURATION_RAM,
    RESTART_COOLDOWN_SECONDS,
    RETRY_DELAY_SECONDS,
    MAX_CRASHES_IN_WINDOW,
)
from logger.healos_logger import get_system_logger


# Action Constants
ACTION_MONITOR = "MONITOR"
ACTION_INVESTIGATE = "INVESTIGATE"
ACTION_RESTART = "RESTART_APPLICATION"
ACTION_WAIT_RETRY = "WAIT_AND_RETRY"
ACTION_ALERT_USER = "ALERT_USER"
ACTION_LIMITED_RETRY = "RESTART_APPLICATION_WITH_LIMITED_RETRIES"
ACTION_RECOVERY_FAILED = "RECOVERY_FAILED"


@dataclass
class DecisionOutput:
    """Encapsulates the decision engine's evaluation and actionable outcome."""
    action: str
    reason: str
    confidence_score: float      # Heuristic confidence score (0.0 to 1.0)
    alternative_actions: List[str]
    recommended_next_step: str
    delay_seconds: float
    is_heuristic: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "confidence_score": self.confidence_score,
            "alternative_actions": self.alternative_actions,
            "recommended_next_step": self.recommended_next_step,
            "delay_seconds": self.delay_seconds,
            "is_heuristic": self.is_heuristic,
        }


class RecoveryDecisionEngine:
    """
    Evaluates operating state and failure circumstances to choose safe recovery actions without
    jeopardizing overall host stability.
    """

    def __init__(
        self,
        max_attempts: int = MAX_RESTART_ATTEMPTS,
        saturation_cpu: float = RESOURCE_SATURATION_CPU,
        saturation_ram: float = RESOURCE_SATURATION_RAM,
        cooldown_seconds: float = RESTART_COOLDOWN_SECONDS,
        retry_delay_seconds: float = RETRY_DELAY_SECONDS,
        max_crashes_in_window: int = MAX_CRASHES_IN_WINDOW,
    ):
        self.logger = get_system_logger()
        self.max_attempts = int(max_attempts)
        self.saturation_cpu = float(saturation_cpu)
        self.saturation_ram = float(saturation_ram)
        self.cooldown_seconds = float(cooldown_seconds)
        self.retry_delay_seconds = float(retry_delay_seconds)
        self.max_crashes_in_window = int(max_crashes_in_window)

    def decide_runtime(
        self,
        is_app_running: bool,
        risk_category: str,
        risk_probability: float,
        cpu_percent: float,
        ram_percent: float,
        warning_signals: Optional[List[str]] = None,
    ) -> DecisionOutput:
        """
        Continuous runtime evaluation when application is active.
        Recommends MONITOR when nominal or INVESTIGATE when risk is elevated.
        """
        if not is_app_running:
            return DecisionOutput(
                action=ACTION_RESTART,
                reason="Monitored application is offline. Autonomous restart required.",
                confidence_score=0.95,
                alternative_actions=[ACTION_WAIT_RETRY],
                recommended_next_step="Authorize restart and verify process initialization.",
                delay_seconds=0.0,
            )

        warn_desc = f" Signals: {'; '.join(warning_signals[:2])}." if warning_signals else ""

        if risk_category == "HIGH" or cpu_percent >= 85.0 or ram_percent >= 85.0:
            return DecisionOutput(
                action=ACTION_INVESTIGATE,
                reason=(
                    f"Elevated failure risk predicted ({risk_probability:.1f}%, Level: {risk_category}).{warn_desc} "
                    f"Host load: CPU {cpu_percent}%, RAM {ram_percent}%."
                ),
                confidence_score=0.88,
                alternative_actions=[ACTION_MONITOR],
                recommended_next_step="Inspect process memory growth or prepare recovery daemon for potential failure.",
                delay_seconds=0.0,
            )
        elif risk_category == "MEDIUM" or cpu_percent >= 70.0 or ram_percent >= 75.0:
            return DecisionOutput(
                action=ACTION_INVESTIGATE,
                reason=f"Moderate risk level ({risk_probability:.1f}%).{warn_desc} Telemetry fluctuation detected.",
                confidence_score=0.80,
                alternative_actions=[ACTION_MONITOR],
                recommended_next_step="Observe application memory allocation rate.",
                delay_seconds=0.0,
            )

        return DecisionOutput(
            action=ACTION_MONITOR,
            reason="Application and host metrics nominal. Continuous surveillance active.",
            confidence_score=0.96,
            alternative_actions=[ACTION_INVESTIGATE],
            recommended_next_step="Maintain standard monitoring interval.",
            delay_seconds=0.0,
        )

    def decide(
        self,
        cpu_percent: float,
        ram_percent: float,
        disk_percent: float,
        current_attempt: int,
        crashes_in_window: int = 0,
        failure_reason: str = "Unknown",
        seconds_since_last_restart: Optional[float] = None,
    ) -> DecisionOutput:
        """
        Analyzes failure parameters upon a detected crash and selects optimal recovery protocol.
        """
        # Rule 1: Exceeded maximum allowed restart attempts -> ALERT_USER
        if current_attempt >= self.max_attempts:
            return DecisionOutput(
                action=ACTION_ALERT_USER,
                reason=(
                    f"Maximum restart attempt ceiling ({self.max_attempts}) reached. "
                    "Halt auto-restarts to prevent infinite crash loop."
                ),
                confidence_score=0.98,
                alternative_actions=[ACTION_WAIT_RETRY],
                recommended_next_step="Inspect logs/error.log and investigate root cause before manual restart.",
                delay_seconds=0.0,
            )

        # Rule 2: Rapid crash storm detection
        if crashes_in_window >= self.max_crashes_in_window:
            return DecisionOutput(
                action=ACTION_ALERT_USER,
                reason=(
                    f"Crash storm detected ({crashes_in_window} crashes within surveillance window). "
                    "Preventing immediate respawn."
                ),
                confidence_score=0.95,
                alternative_actions=[ACTION_WAIT_RETRY, ACTION_LIMITED_RETRY],
                recommended_next_step="Check system resource starvation or bad application configuration.",
                delay_seconds=0.0,
            )

        # Rule 3: Host resource saturation -> WAIT_AND_RETRY
        if cpu_percent >= self.saturation_cpu or ram_percent >= self.saturation_ram:
            return DecisionOutput(
                action=ACTION_WAIT_RETRY,
                reason=(
                    f"Host under severe resource saturation (CPU: {cpu_percent}%, RAM: {ram_percent}%). "
                    "Deferring application restart to avoid compounding OS strain."
                ),
                confidence_score=0.88,
                alternative_actions=[ACTION_ALERT_USER, ACTION_LIMITED_RETRY],
                recommended_next_step=f"Hold recovery for {self.cooldown_seconds}s cooldown to allow resources to stabilize.",
                delay_seconds=self.cooldown_seconds,
            )

        # Rule 4: Approaches maximum retry limit -> RESTART_APPLICATION_WITH_LIMITED_RETRIES
        remaining_budget = self.max_attempts - current_attempt
        if remaining_budget <= 2:
            return DecisionOutput(
                action=ACTION_LIMITED_RETRY,
                reason=(
                    f"Subsequent recovery attempt {current_attempt + 1}/{self.max_attempts}. "
                    f"Operating under limited retry quota ({remaining_budget} attempts remaining)."
                ),
                confidence_score=0.82,
                alternative_actions=[ACTION_RESTART, ACTION_WAIT_RETRY],
                recommended_next_step="Apply throttled startup delay and notify operators if instability continues.",
                delay_seconds=self.retry_delay_seconds * 2,
            )

        # Rule 5: Nominal system conditions -> RESTART_APPLICATION
        return DecisionOutput(
            action=ACTION_RESTART,
            reason=(
                f"Operating system metrics nominal (CPU: {cpu_percent}%, RAM: {ram_percent}%, "
                f"Disk: {disk_percent}%). Attempt {current_attempt + 1}/{self.max_attempts} authorized."
            ),
            confidence_score=0.92,
            alternative_actions=[ACTION_WAIT_RETRY],
            recommended_next_step="Spawn isolated child process and monitor initialization heartbeat.",
            delay_seconds=self.retry_delay_seconds,
        )
