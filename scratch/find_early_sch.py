import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[:3275]):
    if any(k in line.lower() for k in ['schstate', 'setalgorithm', 'switchprocesslabmode', 'togglealgorithmcomparison']):
        print(f"Line {i+1}: {line.strip()[:80]}")
