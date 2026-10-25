import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/deadlock_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of deadlock_lab.py:", len(text))
import re
print("Classes and functions in deadlock_lab.py:")
for m in re.finditer(r'(class\s+[a-zA-Z0-9_]+|def\s+[a-zA-Z0-9_]+)', text):
    print(m.group(0))
