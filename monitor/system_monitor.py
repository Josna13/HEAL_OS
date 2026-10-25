"""
HealOS 2.0 - System Resource Monitor
Periodically gathers operating system metrics using psutil, calculates
temporal derivatives (CPU/RAM delta changes), logs samples to CSV,
and provides thread-safe access to the latest telemetry snapshot.
"""

import csv
import os
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import psutil

from config import (
    METRICS_FILE,
    SYSTEM_MONITOR_INTERVAL,
)
from logger.healos_logger import get_system_logger, get_error_logger


@dataclass
class SystemMetrics:
    """Snapshot of OS resource utilization."""
    timestamp: str
    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    ram_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    process_count: int
    cpu_change: float
    ram_change: float
    ram_free_mb: float = 0.0
    disk_free_gb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_CSV_WRITE_LOCK = threading.Lock()
_LAST_SNAPSHOT_LOCK = threading.Lock()
_GLOBAL_LAST_SAMPLE: Optional[SystemMetrics] = None


def get_system_stats(previous_sample: Optional[SystemMetrics] = None) -> SystemMetrics:
    """
    Collects an instantaneous snapshot of system resources.
    Safely calculates CPU and RAM change relative to previous_sample.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Safe CPU percentage (interval=None for non-blocking delta since last call)
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
    except Exception:
        cpu_percent = 0.0

    # Memory utilization
    try:
        mem = psutil.virtual_memory()
        ram_percent = float(mem.percent)
        ram_used_mb = round(mem.used / (1024 * 1024), 2)
        ram_total_mb = round(mem.total / (1024 * 1024), 2)
        ram_free_mb = round(mem.available / (1024 * 1024), 2)
    except Exception:
        ram_percent = 0.0
        ram_used_mb = 0.0
        ram_total_mb = 0.0
        ram_free_mb = 0.0

    # Disk utilization (target root or project drive)
    try:
        anchor = Path.cwd().anchor or "/"
        disk = psutil.disk_usage(anchor)
        disk_percent = float(disk.percent)
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        disk_free_gb = round(disk.free / (1024 ** 3), 2)
    except Exception:
        disk_percent = 0.0
        disk_used_gb = 0.0
        disk_total_gb = 0.0
        disk_free_gb = 0.0

    # Process count
    try:
        process_count = len(psutil.pids())
    except Exception:
        process_count = 0

    # Calculate temporal deltas
    if previous_sample:
        cpu_change = round(cpu_percent - previous_sample.cpu_percent, 2)
        ram_change = round(ram_percent - previous_sample.ram_percent, 2)
    else:
        cpu_change = 0.0
        ram_change = 0.0

    return SystemMetrics(
        timestamp=timestamp,
        cpu_percent=round(cpu_percent, 2),
        ram_percent=round(ram_percent, 2),
        ram_used_mb=ram_used_mb,
        ram_total_mb=ram_total_mb,
        disk_percent=round(disk_percent, 2),
        disk_used_gb=disk_used_gb,
        disk_total_gb=disk_total_gb,
        process_count=process_count,
        cpu_change=cpu_change,
        ram_change=ram_change,
        ram_free_mb=ram_free_mb,
        disk_free_gb=disk_free_gb,
    )


def append_metrics_to_csv(sample: SystemMetrics, csv_path: Path = METRICS_FILE) -> None:
    """Appends a single SystemMetrics sample to CSV file with automatic header creation."""
    with _CSV_WRITE_LOCK:
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            file_exists = csv_path.exists() and csv_path.stat().st_size > 0

            fieldnames = [
                "timestamp",
                "cpu_percent",
                "ram_percent",
                "ram_used_mb",
                "ram_total_mb",
                "disk_percent",
                "disk_used_gb",
                "disk_total_gb",
                "process_count",
                "cpu_change",
                "ram_change",
            ]

            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                if not file_exists:
                    writer.writeheader()
                writer.writerow(sample.to_dict())
        except Exception as e:
            get_error_logger().warning(f"Failed to append system metrics to CSV: {e}")


class SystemMonitor(threading.Thread):
    """
    Background worker that continuously samples system metrics at configured intervals.
    """

    def __init__(self, interval: float = SYSTEM_MONITOR_INTERVAL, csv_path: Path = METRICS_FILE):
        super().__init__(name="SystemMonitorThread", daemon=True)
        self.interval = interval
        self.csv_path = csv_path
        self._stop_event = threading.Event()
        self.last_sample: Optional[SystemMetrics] = None
        self._lock = threading.Lock()
        self.logger = get_system_logger()

        # Prime psutil cpu measurement
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def stop(self) -> None:
        """Signals the background monitor thread to terminate."""
        self._stop_event.set()

    def is_running(self) -> bool:
        """Returns True if monitoring thread is active."""
        return self.is_alive() and not self._stop_event.is_set()

    def get_latest_metrics(self) -> SystemMetrics:
        """Thread-safe retrieval of the most recent metrics sample."""
        with self._lock:
            if self.last_sample is not None:
                return self.last_sample
        # If not yet sampled, sample synchronously
        sample = get_system_stats()
        with self._lock:
            self.last_sample = sample
        return sample

    def run(self) -> None:
        """Periodic sampling loop."""
        self.logger.info(f"System Resource Monitor started (interval: {self.interval}s)")
        while not self._stop_event.is_set():
            try:
                sample = get_system_stats(previous_sample=self.last_sample)
                with self._lock:
                    self.last_sample = sample

                global _GLOBAL_LAST_SAMPLE
                with _LAST_SNAPSHOT_LOCK:
                    _GLOBAL_LAST_SAMPLE = sample

                append_metrics_to_csv(sample, self.csv_path)
            except Exception as e:
                get_error_logger().error(f"Error in SystemMonitor loop: {e}")

            self._stop_event.wait(self.interval)

        self.logger.info("System Resource Monitor stopped.")
