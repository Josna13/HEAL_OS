import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
pos = text.find('set_custom_scheduler_processes')
print("Position:", pos)
if pos != -1:
    print(text[pos-100:pos+500])
