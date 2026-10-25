import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'function setAlgorithm' in l:
        print(f"Line {i+1}: {l.strip()}")
        for j in range(i, i+15):
            print(f"{j+1}: {lines[j].strip()}")
        break
