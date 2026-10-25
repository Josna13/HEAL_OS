import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos = ws.find('action == "trigger_crash"')
if pos != -1:
    print(ws[pos:pos+1000])
