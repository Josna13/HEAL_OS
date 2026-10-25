with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'two_proc' in l or 'deadlock' in l:
        if i > 4500:
            print(f"Line {i+1}: {l.strip()[:100]}")
