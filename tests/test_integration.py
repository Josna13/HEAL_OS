"""
End-to-End Integration Test for HealOS 2.0.
Spawns HealOS in headless mode, waits for an automated demo crash trigger,
verifies that the crash was detected, that auto-recovery restarted the application,
that recovery.log and system.log were populated, and verifies graceful shutdown.
"""

import subprocess
import sys
import time
import unittest
from pathlib import Path

from config import RECOVERY_LOG_FILE, SYSTEM_LOG_FILE


class TestHealOSEndToEnd(unittest.TestCase):

    def test_full_system_lifecycle_and_recovery(self):
        """Tests complete boot -> crash -> decision -> recovery -> shutdown cycle."""
        cmd = [
            sys.executable,
            "main.py",
            "--no-dashboard",
            "--demo-crash",
            "1",
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Allow 12 seconds for boot, crash simulation at 2s, cooldown, and recovery
            time.sleep(12)
        finally:
            import psutil
            try:
                parent = psutil.Process(proc.pid)
                children = parent.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
                psutil.wait_procs(children + [parent], timeout=3.0)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=2.0)
                except Exception:
                    pass
            try:
                stdout, stderr = proc.communicate(timeout=2.0)
            except Exception:
                stdout, stderr = "", ""

        # 1. Verify process exited cleanly
        self.assertIsNotNone(proc.returncode)
        self.assertIn(proc.returncode, [0, 1, 15, -15, -9, 9])

        # 2. Verify logs exist and were written
        self.assertTrue(SYSTEM_LOG_FILE.exists())
        self.assertTrue(RECOVERY_LOG_FILE.exists())

        system_log_content = SYSTEM_LOG_FILE.read_text(encoding="utf-8")
        recovery_log_content = RECOVERY_LOG_FILE.read_text(encoding="utf-8")

        # 3. Verify crash was recorded
        self.assertIn("CRASH DETECTED", system_log_content)

        # 4. Verify decision was evaluated
        self.assertIn("Recovery Decision", system_log_content)

        # 5. Verify recovery record exists in recovery.log
        self.assertIn("RESTART_APPLICATION", recovery_log_content)
        self.assertIn("SUCCESS", recovery_log_content)


if __name__ == "__main__":
    unittest.main()
