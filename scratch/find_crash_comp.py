with open('dashboard/os_lab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'class CrashRecoveryComparison' in l or 'def trigger_crash_simulation' in l:
        print(f"{i+1}: {l.strip()}")
