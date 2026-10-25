import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/process_lifecycle.py', 'r', encoding='utf-8') as f:
    plc = f.read()

print("Length of process_lifecycle.py:", len(plc))

# Let's see what methods process_lifecycle has
import re
print("Classes and methods in process_lifecycle.py:")
for m in re.finditer(r'(class\s+[a-zA-Z0-9_]+|def\s+[a-zA-Z0-9_]+)', plc):
    print(m.group(0))
