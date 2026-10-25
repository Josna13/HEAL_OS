import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'set_custom_scheduler_processes', text)]
print("Found matches at:", matches)
for p in matches:
    print("--- MATCH AT", p, "---")
    print(text[p-50:p+350])
