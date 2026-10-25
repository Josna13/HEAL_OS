import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos = ws.find('recover_two_process_deadlock')
if pos != -1:
    print(ws[pos-100:pos+300])
