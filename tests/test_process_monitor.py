"""
Unit tests for Process Monitor (monitor/process_monitor.py).
Tests:
- Process counting and liveness detection
- Process detail retrieval (PID, Name, CPU, RAM, Memory in MB, Cmdline)
- Process querying by identifier
- Safe handling of NoSuchProcess, AccessDenied, and Zombie processes
"""

import os
import unittest
from unittest.mock import patch, MagicMock

import psutil
from monitor.process_monitor import ProcessMonitor, ProcessInfo


class TestProcessMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = ProcessMonitor()

    def test_get_process_count(self):
        """Verifies process count returns positive integer of active OS tasks."""
        count = ProcessMonitor.get_process_count()
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_is_pid_alive_valid_and_invalid(self):
        """Verifies PID liveness verification for active and invalid PIDs."""
        my_pid = os.getpid()
        self.assertTrue(ProcessMonitor.is_pid_alive(my_pid))
        self.assertFalse(ProcessMonitor.is_pid_alive(-1))
        self.assertFalse(ProcessMonitor.is_pid_alive(0))
        self.assertFalse(ProcessMonitor.is_pid_alive(9999999))

    def test_get_process_details_current_process(self):
        """Verifies detailed telemetry retrieval for the active test runner process."""
        my_pid = os.getpid()
        info = ProcessMonitor.get_process_details(my_pid)

        self.assertIsNotNone(info)
        self.assertIsInstance(info, ProcessInfo)
        self.assertEqual(info.pid, my_pid)
        self.assertTrue(len(info.name) > 0)
        self.assertGreaterEqual(info.cpu_percent, 0.0)
        self.assertGreaterEqual(info.memory_percent, 0.0)
        self.assertGreater(info.memory_mb, 0.0)
        self.assertGreater(info.create_time, 0.0)

        # Verify serialization
        data = info.to_dict()
        self.assertEqual(data["pid"], my_pid)
        self.assertEqual(data["memory_mb"], info.memory_mb)

    def test_get_process_details_nonexistent_pid(self):
        """Verifies nonexistent PID returns None without raising exceptions."""
        info = ProcessMonitor.get_process_details(9999999)
        self.assertIsNone(info)

    def test_find_processes_by_identifier(self):
        """Verifies finding active processes by executable name or cmdline token."""
        matches = self.monitor.find_processes_by_identifier("python")
        self.assertIsInstance(matches, list)
        self.assertGreaterEqual(len(matches), 1)

        # Bogus identifier should return empty list
        no_matches = self.monitor.find_processes_by_identifier("nonexistent_unique_process_tag_12345")
        self.assertEqual(len(no_matches), 0)

    def test_list_processes(self):
        """Verifies listing active system processes respects limit parameter."""
        procs = self.monitor.list_processes(limit=8)
        self.assertIsInstance(procs, list)
        self.assertLessEqual(len(procs), 8)
        self.assertGreater(len(procs), 0)
        self.assertIsInstance(procs[0], ProcessInfo)

    @patch("psutil.Process")
    def test_psutil_exceptions_handled_gracefully(self, mock_process_cls):
        """Verifies NoSuchProcess and AccessDenied are caught cleanly."""
        mock_process_cls.side_effect = psutil.NoSuchProcess(pid=888)
        self.assertIsNone(ProcessMonitor.get_process_details(888))
        self.assertFalse(ProcessMonitor.is_pid_alive(888))

        mock_process_cls.side_effect = psutil.AccessDenied(pid=1)
        self.assertIsNone(ProcessMonitor.get_process_details(1))
        self.assertFalse(ProcessMonitor.is_pid_alive(1))

    @patch("psutil.Process")
    def test_zombie_process_marked_dead(self, mock_process_cls):
        """Verifies zombie processes are treated as dead."""
        mock_proc = MagicMock()
        mock_proc.is_running.return_value = True
        mock_proc.status.return_value = psutil.STATUS_ZOMBIE
        mock_process_cls.return_value = mock_proc

        self.assertFalse(ProcessMonitor.is_pid_alive(555))


if __name__ == "__main__":
    unittest.main()
