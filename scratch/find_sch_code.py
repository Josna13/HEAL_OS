with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function setAlgorithm' in line:
        start_line = i
        break

print(f"Found function setAlgorithm at line {start_line+1}")
for j in range(start_line, min(start_line + 350, len(lines))):
    print(f"{j+1}: {lines[j]}", end='')
