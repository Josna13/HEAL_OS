import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(1980, min(2015, len(lines))):
    print(f"{j+1}: {lines[j]}", end='')
