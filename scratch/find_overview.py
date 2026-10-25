import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the overview tab HTML
for i, line in enumerate(lines):
    if 'id="tab-overview"' in line:
        print(f"Overview tab start at line {i+1}")
        with open('scratch/overview_tab.txt', 'w', encoding='utf-8') as out:
            for j in range(i, min(i+350, len(lines))):
                out.write(f"{j+1}: {lines[j]}")
        break

# Key section markers
markers = ['TOUR_STORY', 'tourStep', 'startGuidedDemo', 'tab-diagnostics', 'tab-recovery', 'tab-deadlock']
for m in markers:
    for i, line in enumerate(lines):
        if m in line:
            print(f"  [{m}] at line {i+1}")
            break
