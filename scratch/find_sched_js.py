import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find functions related to scheduler in web_server.py
matches = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
sched_funcs = [m for m in matches if any(w in m.lower() for w in ['sch', 'sched', 'gantt', 'algo', 'process', 'step', 'play', 'tick'])]
print("Scheduler-related JS functions found in web_server.py:")
for sf in sched_funcs:
    print(" -", sf)

# Let's inspect where scheduler JS starts in web_server.py
pos = text.find('// CPU Scheduling')
if pos == -1:
    pos = text.find('Scheduling')
print("Position of 'Scheduling' in text:", pos)
if pos != -1:
    print(text[pos:pos+1500])
