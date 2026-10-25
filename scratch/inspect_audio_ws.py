import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos = ws.find('let audioCtx = null;')
if pos == -1:
    pos = ws.find('audioCtx')

print("audio snippet in ws:")
print(ws[pos-50:pos+1500])
