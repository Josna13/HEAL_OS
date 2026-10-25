import psutil
import os

my_pid = os.getpid()
orphans = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = p.info.get('cmdline') or []
        if any('dummy_app' in str(c) or 'main.py' in str(c) for c in cmdline):
            if p.pid != my_pid:
                orphans.append((p.pid, cmdline))
    except Exception:
        pass

print(f"Found {len(orphans)} orphaned processes:")
for pid, cmd in orphans:
    print(f"  PID {pid}: {cmd}")
    try:
        psutil.Process(pid).kill()
        print(f"    -> Killed PID {pid}")
    except Exception as e:
        print(f"    -> Could not kill: {e}")
