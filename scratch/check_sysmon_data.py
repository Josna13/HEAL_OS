with open('tests/test_system_monitor.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'data', text, re.IGNORECASE)]
print("Found 'data' in test_system_monitor.py:", len(matches))
for p in matches:
    print(text[p-30:p+60])
