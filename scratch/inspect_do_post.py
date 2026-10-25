import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_post = ws.find('def do_POST(')
print("do_POST pos:", pos_post)
if pos_post != -1:
    print(ws[pos_post:pos_post+3500])
