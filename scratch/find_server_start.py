with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines[-50:]):
    print(l.strip())
