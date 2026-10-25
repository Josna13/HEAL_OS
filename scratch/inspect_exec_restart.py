with open('recovery/auto_restart.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def _execute_application_restart' in l:
        print("".join(lines[i:i+60]))
        break
