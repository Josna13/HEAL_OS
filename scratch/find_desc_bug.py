import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

import re
matches = [m.start() for m in re.finditer(r"st\s*\[\s*['\"]description['\"]\s*\]", ws)]
print("Occurrences of st['description']:", matches)
for p in matches:
    print(ws[p-50:p+150])
