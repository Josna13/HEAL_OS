with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'orchestrator_ref' in l:
        print(f"{i+1}: {l.strip()}")
