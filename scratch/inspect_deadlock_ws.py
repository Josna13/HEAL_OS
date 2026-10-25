import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos = ws.find('function renderDeadlock(')
print(ws[pos:pos+2500])
