import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_clock = ws.find('function renderSchedulerClock(')
print("renderSchedulerClock in WS:")
print(ws[pos_clock:pos_clock+2500])
