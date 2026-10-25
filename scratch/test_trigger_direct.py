import sys
import os
import subprocess
import time
from pathlib import Path

BASE = Path(".").resolve()
trigger = BASE / "data" / "crash.trigger"
app = BASE / "apps" / "dummy_app.py"

print("Trigger path:", trigger)
print("Trigger exists currently:", trigger.exists())

p = subprocess.Popen([sys.executable, str(app), "--mode", "normal"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
try:
    time.sleep(0.5)
    print("Process running, poll:", p.poll())
    trigger.parent.mkdir(parents=True, exist_ok=True)
    trigger.write_text("CRASH_NOW", encoding="utf-8")
    print("Wrote trigger. Exists now:", trigger.exists())
    for i in range(20):
        time.sleep(0.1)
        poll = p.poll()
        if poll is not None:
            print(f"Terminated at step {i} with code {poll}!")
            break
        print(f"Still running, step {i}, trigger exists: {trigger.exists()}")
    out, err = p.communicate(timeout=2)
    print("STDOUT:\n", out)
    print("STDERR:\n", err)
finally:
    if p.poll() is None:
        p.kill()
