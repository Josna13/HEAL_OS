import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_crash_recovery_ui.py', 'r', encoding='utf-8') as f:
    bcr = f.read()

print("build_crash_recovery_ui.py length:", len(bcr))
print("schedulerState in bcr:", 'schedulerState' in bcr)
print("schState in bcr:", 'schState' in bcr)

# Let's see what tabs bcr defines
import re
print("Functions in bcr:")
for fn in re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', bcr):
    print(" -", fn)
