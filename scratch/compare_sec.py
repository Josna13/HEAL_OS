import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_clean_start = clean.find('let schState = {')
pos_clean_end = clean.find('// TAB 3: DEADLOCK', pos_clean_start)
clean_sec = clean[pos_clean_start:pos_clean_end]

pos_ws_start = ws.find('let schedulerState = {')
pos_ws_end = ws.find('// DEADLOCK', pos_ws_start)
ws_sec = ws[pos_ws_start:pos_ws_end]

print("CLEAN scheduler section length:", len(clean_sec))
print("WS scheduler section length:", len(ws_sec))

print("\n--- Functions in CLEAN ---")
import re
for fn in re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', clean_sec):
    print(" ", fn)

print("\n--- Functions in WS ---")
for fn in re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', ws_sec):
    print(" ", fn)
