import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

# Find all occurrences of playSound and playTone in web_server.py
matches = list(re.finditer(r'(playTone|playSound)\s*\([^)]*\)', ws))
print(f"Total calls to playSound/playTone: {len(matches)}")
for m in matches:
    line_no = ws[:m.start()].count('\n') + 1
    print(f"Line {line_no}: {m.group(0)}")
