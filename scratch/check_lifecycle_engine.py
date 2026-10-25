with open('dashboard/process_lifecycle.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("LifecycleEngine methods:")
for m in re.finditer(r'def ([a-zA-Z0-9_]+)\(self', text):
    print(" -", m.group(1))
