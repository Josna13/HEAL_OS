import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

sections = {
    'Overview tab': (789, 250),
    'Recovery tab': (1412, 150),
    'Deadlock tab': (1519, 150),
    'Diagnostics tab': (1647, 150),
    'TOUR_STORY': (2001, 80),
}

for name, (start_line, count) in sections.items():
    with open(f'scratch/section_{name.replace(" ", "_")}.txt', 'w', encoding='utf-8') as out:
        for j in range(start_line-1, min(start_line-1+count, len(lines))):
            out.write(f"{j+1}: {lines[j]}")
    print(f"Wrote section: {name} ({count} lines from line {start_line})")
