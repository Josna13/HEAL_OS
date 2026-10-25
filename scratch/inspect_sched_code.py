import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    bc = f.read()

print("build_clean_ui.py has functions:")
bc_funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', bc)
for f in bc_funcs:
    print(" -", f)

pos_render = ws.find('function renderScheduler(')
print("\nIn web_server.py, renderScheduler is at pos:", pos_render)
if pos_render != -1:
    print("--- snippet of renderScheduler in web_server.py (first 1000 chars) ---")
    print(ws[pos_render:pos_render+1000])

# Also check where scheduler JS begins in web_server.py
pos_algo = ws.find('function setAlgorithm(')
print("\nIn web_server.py, setAlgorithm is at pos:", pos_algo)
if pos_algo != -1:
    print("--- snippet around setAlgorithm (first 1000 chars) ---")
    print(ws[pos_algo-200:pos_algo+1000])
