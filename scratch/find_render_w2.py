with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'renderWorkspace2' in line or 'renderScheduler' in line:
        print(f"Line {i+1}: {line.strip()}")
