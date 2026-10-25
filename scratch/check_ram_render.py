with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function renderOverviewExecutive' in l:
        print(f"renderOverviewExecutive at line {i+1}")
        for j in range(i, min(i+60, len(lines))):
            print(f"{j+1}: {lines[j]}", end='')
        break
