import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_ws_sch_start = ws.find('let schedulerState = {')
pos_ws_sch_end = ws.find('// =======================================================================\n    // TAB 3: DEADLOCK VISUALIZATION', pos_ws_sch_start)
ws_sch_js = ws[pos_ws_sch_start:pos_ws_sch_end]

# Find all functions defined inside ws_sch_js
funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', ws_sch_js)
print("Functions in ws_sch_js:", funcs)

# Check if there are duplicate functions or old studio code
for f in funcs:
    count = len(re.findall(r'function\s+' + f + r'\s*\(', ws_sch_js))
    if count > 1:
        print(f"DUPLICATE FUNCTION: {f} appears {count} times")
