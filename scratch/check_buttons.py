with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Looking for tab containers:")
for line in text.splitlines():
    if 'id="tab-' in line or "id='tab-" in line:
        print(line[:120].encode('ascii', errors='replace').decode('ascii'))

