with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'elif action == "[^"]+":|if action == "[^"]+":', text)
for m in matches:
    print(m)
