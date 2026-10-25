with open('recovery/auto_restart.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def _execute_application_restart' in l:
        out = "".join(lines[i:i+80])
        print(out.encode('ascii', errors='replace').decode('ascii'))
        break
