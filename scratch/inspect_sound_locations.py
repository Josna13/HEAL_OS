import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

target_lines = [1357, 1384, 1404, 1856, 2022]
for tl in target_lines:
    print(f"\n--- Around Line {tl} ---")
    start = max(0, tl - 5)
    end = min(len(lines), tl + 5)
    for i in range(start, end):
        print(f"{i+1:4d}: {lines[i].rstrip()}")
