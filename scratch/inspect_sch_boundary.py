import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_ws_start = ws.find('let schedulerState = {')
pos_dl = ws.find('renderDeadlock', pos_ws_start)
print("pos_ws_start:", pos_ws_start)
print("pos_dl:", pos_dl)

print("Snippet before renderDeadlock (last 500 chars before):")
print(ws[pos_dl-500:pos_dl])
