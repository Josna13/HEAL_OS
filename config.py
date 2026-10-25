"""
HealOS 2.0 - Central Configuration Module
Defines system-wide paths, monitoring parameters, AI thresholds,
recovery limits, health weights, and environment settings.
All paths are anchored to the project root directory.
"""

from pathlib import Path
from typing import Dict, Any

# ==============================================================================
# Base Directory Anchoring
# ==============================================================================
BASE_DIR: Path = Path(__file__).resolve().parent

# Directory Paths
APPS_DIR: Path = BASE_DIR / "apps"
MONITOR_DIR: Path = BASE_DIR / "monitor"
DETECTOR_DIR: Path = BASE_DIR / "detector"
RECOVERY_DIR: Path = BASE_DIR / "recovery"
LOGGER_DIR: Path = BASE_DIR / "logger"
DASHBOARD_DIR: Path = BASE_DIR / "dashboard"
AI_DIR: Path = BASE_DIR / "ai"
LOGS_DIR: Path = BASE_DIR / "logs"
DATA_DIR: Path = BASE_DIR / "data"

# File Paths
DUMMY_APP_SCRIPT: Path = APPS_DIR / "dummy_app.py"
CRASH_TRIGGER_FILE: Path = DATA_DIR / "crash.trigger"

MODEL_FILE: Path = AI_DIR / "model.pkl"
DATASET_FILE: Path = AI_DIR / "dataset.csv"
METRICS_FILE: Path = DATA_DIR / "system_metrics.csv"

SYSTEM_LOG_FILE: Path = LOGS_DIR / "system.log"
ERROR_LOG_FILE: Path = LOGS_DIR / "error.log"
RECOVERY_LOG_FILE: Path = LOGS_DIR / "recovery.log"
EVENTS_LOG_FILE: Path = LOGS_DIR / "events.log"
DUMMY_APP_LOG_FILE: Path = LOGS_DIR / "dummy_app.log"

# ==============================================================================
# Target Monitored Application Configuration
# ==============================================================================
TARGET_APP_NAME: str = "dummy_app.py"
TARGET_APP_DISPLAY_NAME: str = "HealOS-DummyApp"
TARGET_APP_ARGS: list = []

# ==============================================================================
# Monitoring & Refresh Intervals (Seconds)
# ==============================================================================
SYSTEM_MONITOR_INTERVAL: float = 1.0       # Sampling rate for CPU/RAM/Disk
CRASH_DETECTOR_INTERVAL: float = 0.2       # Polling rate for process liveness
DASHBOARD_REFRESH_INTERVAL: float = 1.0    # Real-time dashboard refresh rate
TRIGGER_CHECK_INTERVAL: float = 0.1        # Sub-second trigger file inspection
MAX_METRICS_HISTORY: int = 1000            # In-memory metric history window

# ==============================================================================
# AI Predictive Failure Analyzer Settings
# ==============================================================================
# Synthetic risk categories based on ML model probability (0.0 to 1.0)
RISK_THRESHOLD_LOW: float = 0.35           # Below 35% probability = LOW
RISK_THRESHOLD_MEDIUM: float = 0.70        # 35% - 70% probability = MEDIUM
# Above 70% probability = HIGH

# Synthetic Dataset Generation Parameters
SYNTHETIC_DATASET_SIZE: int = 5000
RANDOM_SEED: int = 42

# Feature Column Names
FEATURE_COLUMNS = [
    "cpu_percent",
    "ram_percent",
    "disk_percent",
    "process_count",
    "cpu_change",
    "ram_change",
]
TARGET_COLUMN: str = "failure_risk"

# ==============================================================================
# AI Recovery Decision Engine & Auto-Restart Policies
# ==============================================================================
MAX_RESTART_ATTEMPTS: int = 5              # Max restarts before ALERT_USER
RESTART_COOLDOWN_SECONDS: float = 6.0      # Cooldown window between restarts
RETRY_DELAY_SECONDS: float = 1.0           # Observable transition delay before respawn
RAPID_CRASH_WINDOW_SECONDS: float = 60.0   # Window to detect crash storms
MAX_CRASHES_IN_WINDOW: int = 4             # Threshold for rapid crash alert

# Resource saturation thresholds for WAIT_AND_RETRY
RESOURCE_SATURATION_CPU: float = 90.0      # Defer restart if CPU > 90%
RESOURCE_SATURATION_RAM: float = 92.0      # Defer restart if RAM > 92%

# ==============================================================================
# Recovery SLA & Analytics Settings
# ==============================================================================
RECOVERY_SLA_TARGET_SECONDS: float = 2.5       # Recovery duration SLA target threshold (seconds)
MAX_RECENT_RECOVERIES_DISPLAY: int = 3         # Number of recent recovery events displayed in dashboard
MAX_RECOVERY_HISTORY_BUFFER: int = 100         # Maximum in-memory recovery events retained

# ==============================================================================
# System Health Analyzer Weights & Thresholds
# Total weights must sum to 1.0
# ==============================================================================
HEALTH_WEIGHT_CPU: float = 0.20
HEALTH_WEIGHT_RAM: float = 0.25
HEALTH_WEIGHT_DISK: float = 0.15
HEALTH_WEIGHT_STABILITY: float = 0.40

# Health Score Thresholds (0 to 100)
HEALTH_SCORE_HEALTHY: float = 80.0         # 80 - 100: Normal
HEALTH_SCORE_WARNING: float = 50.0         # 50 - 79: Warning
# 0 - 49: Critical

# ==============================================================================
# Logging and Event History
# ==============================================================================
EVENT_TIMELINE_LIMIT: int = 8              # Visible in compact dashboard timeline (35-row terminal)
IN_MEMORY_EVENT_LIMIT: int = 200           # Internal circular event buffer
LOG_MAX_BYTES: int = 5 * 1024 * 1024       # 5 MB per rotating log file
LOG_BACKUP_COUNT: int = 3                  # Keep 3 rotating backups


def init_directories() -> None:
    """Ensure all required runtime directories exist."""
    directories = [
        LOGS_DIR,
        DATA_DIR,
        AI_DIR,
        APPS_DIR,
        MONITOR_DIR,
        DETECTOR_DIR,
        RECOVERY_DIR,
        LOGGER_DIR,
        DASHBOARD_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
init_directories()
