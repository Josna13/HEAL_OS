"""
Unit tests for Crash Detector (detector/crash_detector.py).
Tests liveness checking, duplicate suppression, and distinction between
intentional administrative shutdown and unexpected crash events.
"""

import subprocess
import sys
import time
import unittest
from detector.crash_detector import CrashDetector, CrashEvent


class TestCrashDetector(unittest.TestCase):

    def setUp(self):
        self.detector = CrashDetector(interval=0.1)
        self.detected_events = []

        def callback(event: CrashEvent):
            self.detected_events.append(event)

        self.detector.on_crash_callback = callback

    def tearDown(self):
        self.detector.stop()

    def test_unexpected_crash_detection(self):
        """Spawns a transient subprocess that exits with code 1; verifies CrashDetector catches it."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(1)"])
        proc.wait()  # Ensure it terminates

        self.detector.set_target(proc.pid, proc)
        event = self.detector.check_liveness()

        self.assertIsNotNone(event)
        self.assertEqual(event.pid, proc.pid)
        self.assertEqual(event.exit_code, 1)
        self.assertTrue(event.is_unexpected)
        self.assertEqual(len(self.detected_events), 1)

    def test_duplicate_crash_prevention(self):
        """Verifies that polling a terminated process twice does NOT dispatch duplicate events."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(42)"])
        proc.wait()

        self.detector.set_target(proc.pid, proc)
        event1 = self.detector.check_liveness()
        event2 = self.detector.check_liveness()

        self.assertIsNotNone(event1)
        self.assertIsNone(event2)
        self.assertEqual(len(self.detected_events), 1)

    def test_intentional_shutdown_suppresses_crash_event(self):
        """Verifies that mark_intentional_shutdown suppresses false crash alarms."""
        proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
        proc.wait()

        self.detector.set_target(proc.pid, proc)
        self.detector.mark_intentional_shutdown()
        event = self.detector.check_liveness()

        self.assertIsNone(event)
        self.assertEqual(len(self.detected_events), 0)


if __name__ == "__main__":
    unittest.main()
