import sys
sys.path.insert(0, '.')

with open('tests/test_trigger.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace setUp to properly wait for any killed processes
target = """        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = p.info.get('cmdline') or []
                if any('dummy_app.py' in str(arg) for arg in cmdline):
                    if p.pid != os.getpid():
                        p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass"""

replacement = """        stray = []
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
            psutil.wait_procs(stray, timeout=2.0)"""

if target in text:
    text = text.replace(target, replacement)
    with open('tests/test_trigger.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated test_trigger.py setUp to wait for killed processes!")
else:
    print("Target not found in test_trigger.py")
