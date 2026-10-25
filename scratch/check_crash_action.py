import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos = ws.find('trigger_crash')
if pos != -1:
    print(ws[pos-50:pos+800])

pos2 = ws.find('simulate_crash')
if pos2 != -1:
    print(ws[pos2-50:pos2+800])
