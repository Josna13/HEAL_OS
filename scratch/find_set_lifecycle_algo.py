with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'set_lifecycle_algo' in l:
        print(f"Line {i+1}:")
        for j in range(max(0, i-2), min(len(lines), i+8)):
            print(f"{j+1}: {repr(lines[j])}")
