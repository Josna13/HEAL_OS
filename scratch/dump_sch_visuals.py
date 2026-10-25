with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function updateSchVisualsAtTick' in line:
        start_line = i
        break

with open('scratch/sch_visuals_snippet.txt', 'w', encoding='utf-8') as out:
    for j in range(start_line, min(start_line + 300, len(lines))):
        out.write(f"{j+1}: {lines[j]}")

print(f"Written from line {start_line+1} to scratch/sch_visuals_snippet.txt")
