import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos1 = ws.find('let schedulerState =')
print("schedulerState pos:", pos1)

# Find comments or markers after pos1
for m in ['DEADLOCK', 'TAB 3', 'pollData']:
    p = ws.find(m, pos1)
    print(f"Marker '{m}' pos after schedulerState: {p}")
