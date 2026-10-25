import sys
sys.path.insert(0, '.')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the CSS :root block
for i, line in enumerate(lines):
    if ':root {' in line:
        print(f"CSS :root at line {i+1}")
        for j in range(i, min(i+80, len(lines))):
            print(f"{j+1}: {lines[j]}", end='')
        break
