import re

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
sch_funcs = [fn for fn in funcs if any(k in fn.lower() for k in ['sch', 'algo', 'process', 'gantt', 'queue', 'tick', 'core'])]
print('Scheduler related functions count:', len(sch_funcs))
for fn in sch_funcs:
    print(' -', fn)
