import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Matches for schedulerComparisonOpen:")
for m in re.finditer(r'schedulerComparisonOpen', text):
    start = max(0, m.start() - 40)
    end = min(len(text), m.end() + 60)
    print(text[start:end].replace('\n', ' '))
