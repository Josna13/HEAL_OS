import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the Recovery tab content
rec_start = None
dl_start = None
diag_start = None
tab3_end = None

for i, line in enumerate(lines):
    if 'id="tab-recovery"' in line and rec_start is None:
        rec_start = i
    if 'id="tab-deadlock"' in line and dl_start is None:
        dl_start = i
    if 'id="tab-diagnostics"' in line and diag_start is None:
        diag_start = i

print(f"Recovery tab: line {rec_start+1}")
print(f"Deadlock tab: line {dl_start+1}")
print(f"Diagnostics tab: line {diag_start+1}")

# Dump diagnostics tab
with open('scratch/diag_tab.txt', 'w', encoding='utf-8') as out:
    for j in range(diag_start, min(diag_start+250, len(lines))):
        out.write(f"{j+1}: {lines[j]}")
print("Dumped diagnostics tab")
