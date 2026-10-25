import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

matches = [m.start() for m in re.finditer(r"['\"]scheduler['\"]\s*:", ws)]
print("Occurrences of 'scheduler':", matches)
for p in matches:
    print("--- around", p, "---")
    print(ws[p-50:p+350])
