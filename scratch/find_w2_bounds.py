with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function renderWorkspace2' in line:
        w2_start = i
    if 'let wasDeadlocked = false;' in line:
        w2_end = i

print(f"renderWorkspace2 starts at line {w2_start+1}, ends before line {w2_end+1}")
