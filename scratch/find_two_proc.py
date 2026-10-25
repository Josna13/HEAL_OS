import sys
sys.path.insert(0, '.')
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('TwoProcessDeadlock')
print("Position:", pos)
if pos != -1:
    print(text[pos-100:pos+800])
