import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_post = ws.find('def _do_POST_impl(')
actions = re.findall(r'action\s*==\s*["\']([^"\']+)["\']', ws[pos_post:])
print("Actions handled in _do_POST_impl:")
for a in actions:
    print(" -", a)
