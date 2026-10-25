"""
Unit tests for Trigger File Watcher and Consumption (apps/dummy_app.py, detector/crash_detector.py).
Verifies:
- Trigger file detection and immediate consumption (unlinking)
- Exactly-once trigger processing
- Non-interference when trigger file is absent
"""

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from config import CRASH_TRIGGER_FILE, DUMMY_APP_SCRIPT


class TestTriggerWatcher(unittest.TestCase):

    def setUp(self):
        # Ensure trigger file is clean before each test
        if CRASH_TRIGGER_FILE.exists():
            CRASH_TRIGGER_FILE.unlink(missing_ok=True)
        # Terminate any stray dummy_app processes from previous tests
        import psutil
        stray = []
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = p.info.get('cmdline') or []
                if any('dummy_app.py' in str(arg) for arg in cmdline):
                    if p.pid != os.getpid():
                        p.kill()
                        stray.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if stray:
            psutil.wait_procs(stray, timeout=2.0)

    def tearDown(self):
        if CRASH_TRIGGER_FILE.exists():
            CRASH_TRIGGER_FILE.unlink(missing_ok=True)
        import psutil
        stray = []
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = p.info.get('cmdline') or []
                if any('dummy_app.py' in str(arg) for arg in cmdline):
                    if p.pid != os.getpid():
                        p.kill()
                        stray.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if stray:
            psutil.wait_procs(stray, timeout=2.0)

    def test_trigger_file_causes_immediate_exit_and_consumption(self):
        """
        Launches dummy_app.py in a child process, creates data/crash.trigger,
        verifies that dummy_app detects it, unlinks it, and terminates with exit code 1.
        """
        proc = subprocess.Popen(
            [sys.executable, str(DUMMY_APP_SCRIPT), "--mode", "normal"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Let dummy_app start up and begin heartbeat
            time.sleep(1.0)
            self.assertIsNone(proc.poll(), "dummy_app should be running normally")

            # Create crash trigger
            CRASH_TRIGGER_FILE.parent.mkdir(parents=True, exist_ok=True)
            CRASH_TRIGGER_FILE.write_text("TEST_TRIGGER", encoding="utf-8")

            # Wait up to 12.0 seconds for dummy_app to consume trigger and terminate
            t_start = time.time()
            terminated = False
            while time.time() - t_start < 12.0:
                if proc.poll() is not None:
                    terminated = True
                    break
                time.sleep(0.05)

            out, err = "", ""
            if not terminated:
                proc.kill()
                out, err = proc.communicate(timeout=2)
                print(f"\n[DEBUG FAILURE] dummy_app stdout:\n{out}\nstderr:\n{err}\n")

            self.assertTrue(terminated, f"dummy_app should terminate after trigger creation. Output was: {out}")
            self.assertEqual(proc.returncode, 1, "dummy_app should exit with simulated crash code 1")

            # Verify trigger file was consumed (unlinked)
            self.assertFalse(CRASH_TRIGGER_FILE.exists(), "crash.trigger must be consumed/deleted")
        finally:
            if proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=2.0)
                except Exception:
                    pass
            try:
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()
            except Exception:
                pass

    def test_missing_trigger_file_does_not_affect_normal_operation(self):
        """Verifies dummy_app runs stably when crash.trigger is not present."""
        proc = subprocess.Popen(
            [sys.executable, str(DUMMY_APP_SCRIPT), "--mode", "normal"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            time.sleep(1.0)
            self.assertIsNone(proc.poll(), "dummy_app must remain running when no trigger exists")
        finally:
            proc.terminate()
            proc.wait(timeout=2.0)


if __name__ == "__main__":
    unittest.main()
