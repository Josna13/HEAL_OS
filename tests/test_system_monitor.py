"""
Unit tests for System Resource Monitor (monitor/system_monitor.py).
Tests:
- Live psutil telemetry gathering (CPU, RAM, Disk, PIDs, deltas)
- Mocked deterministic metrics calculations
- Exception resilience against psutil failures
- CSV persistence and header handling
- SystemMonitor background thread lifecycle
"""

import os
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch, MagicMock

import psutil
from monitor.system_monitor import (
    SystemMetrics,
    get_system_stats,
    append_metrics_to_csv,
    SystemMonitor,
)


class TestSystemMonitor(unittest.TestCase):

    def test_get_system_stats_live_structure(self):
        """Verifies that live get_system_stats() populates all metric fields accurately."""
        sample: SystemMetrics = get_system_stats()
        self.assertIsInstance(sample, SystemMetrics)
        self.assertTrue(len(sample.timestamp) > 0)
        self.assertGreaterEqual(sample.cpu_percent, 0.0)
        self.assertLessEqual(sample.cpu_percent, 100.0)
        self.assertGreaterEqual(sample.ram_percent, 0.0)
        self.assertLessEqual(sample.ram_percent, 100.0)
        self.assertGreaterEqual(sample.ram_used_mb, 0.0)
        self.assertGreater(sample.ram_total_mb, 0.0)
        self.assertGreaterEqual(sample.disk_percent, 0.0)
        self.assertLessEqual(sample.disk_percent, 100.0)
        self.assertGreaterEqual(sample.disk_used_gb, 0.0)
        self.assertGreater(sample.disk_total_gb, 0.0)
        self.assertGreater(sample.process_count, 0)
        self.assertEqual(sample.cpu_change, 0.0)
        self.assertEqual(sample.ram_change, 0.0)

    def test_get_system_stats_delta_calculation(self):
        """Verifies CPU and RAM change calculation when previous sample is provided."""
        prev = SystemMetrics(
            timestamp="2026-01-01 12:00:00",
            cpu_percent=25.0,
            ram_percent=40.0,
            ram_used_mb=4000.0,
            ram_total_mb=10000.0,
            disk_percent=50.0,
            disk_used_gb=100.0,
            disk_total_gb=200.0,
            process_count=150,
            cpu_change=0.0,
            ram_change=0.0,
        )

        curr = get_system_stats(previous_sample=prev)
        self.assertEqual(curr.cpu_change, round(curr.cpu_percent - prev.cpu_percent, 2))
        self.assertEqual(curr.ram_change, round(curr.ram_percent - prev.ram_percent, 2))

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.disk_usage")
    @patch("psutil.pids")
    def test_mocked_system_stats_exact_calculation(
        self, mock_pids, mock_disk, mock_mem, mock_cpu
    ):
        """Tests deterministic metric conversions with mocked psutil telemetry."""
        mock_cpu.return_value = 52.5

        MemTuple = namedtuple("vmem", ["percent", "used", "total", "available"])
        mock_mem.return_value = MemTuple(
            percent=65.0,
            used=4 * 1024 * 1024 * 1024,       # 4096 MB
            total=16 * 1024 * 1024 * 1024,     # 16384 MB
            available=12 * 1024 * 1024 * 1024, # 12288 MB
        )

        DiskTuple = namedtuple("sdiskusage", ["percent", "used", "total", "free"])
        mock_disk.return_value = DiskTuple(
            percent=42.0,
            used=100 * (1024 ** 3),  # 100 GB
            total=500 * (1024 ** 3),  # 500 GB
            free=400 * (1024 ** 3),   # 400 GB
        )

        mock_pids.return_value = list(range(220))

        sample = get_system_stats()
        self.assertEqual(sample.cpu_percent, 52.5)
        self.assertEqual(sample.ram_percent, 65.0)
        self.assertEqual(sample.ram_used_mb, 4096.0)
        self.assertEqual(sample.ram_total_mb, 16384.0)
        self.assertEqual(sample.ram_free_mb, 12288.0)
        self.assertEqual(sample.disk_percent, 42.0)
        self.assertEqual(sample.disk_used_gb, 100.0)
        self.assertEqual(sample.disk_total_gb, 500.0)
        self.assertEqual(sample.disk_free_gb, 400.0)
        self.assertEqual(sample.process_count, 220)

    @patch("psutil.cpu_percent", side_effect=RuntimeError("psutil CPU failure"))
    @patch("psutil.virtual_memory", side_effect=RuntimeError("psutil RAM failure"))
    @patch("psutil.disk_usage", side_effect=RuntimeError("psutil Disk failure"))
    @patch("psutil.pids", side_effect=RuntimeError("psutil PID failure"))
    def test_psutil_exception_resilience(self, mock_pids, mock_disk, mock_mem, mock_cpu):
        """Verifies get_system_stats handles unexpected psutil failures gracefully without throwing."""
        sample = get_system_stats()
        self.assertIsInstance(sample, SystemMetrics)
        self.assertEqual(sample.cpu_percent, 0.0)
        self.assertEqual(sample.ram_percent, 0.0)
        self.assertEqual(sample.disk_percent, 0.0)
        self.assertEqual(sample.process_count, 0)

    def test_append_metrics_to_csv(self):
        """Verifies append_metrics_to_csv creates headers and appends records properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "metrics_test.csv"
            sample1 = get_system_stats()
            sample2 = get_system_stats(previous_sample=sample1)

            append_metrics_to_csv(sample1, csv_path=csv_path)
            append_metrics_to_csv(sample2, csv_path=csv_path)

            self.assertTrue(csv_path.exists())
            lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
            # 1 header line + 2 data lines = 3 lines
            self.assertEqual(len(lines), 3)
            self.assertIn("timestamp,cpu_percent,ram_percent", lines[0])

    def test_system_monitor_thread_lifecycle(self):
        """Verifies SystemMonitor background thread starts, samples, and terminates cleanly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "live_metrics.csv"
            monitor = SystemMonitor(interval=0.1, csv_path=csv_path)
            self.assertFalse(monitor.is_running())

            monitor.start()
            self.assertTrue(monitor.is_running())

            latest = monitor.get_latest_metrics()
            self.assertIsInstance(latest, SystemMetrics)

            monitor.stop()
            monitor.join(timeout=2.0)
            self.assertFalse(monitor.is_running())


if __name__ == "__main__":
    unittest.main()
