import sys
sys.path.insert(0, '.')
import re

# Read current web_server.py
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

print("Current web_server.py length:", len(ws))

# Check where tab-deadlock is located
pos_dl_main = ws.find('<main id="tab-deadlock"')
pos_dl_main_end = ws.find('</main>', pos_dl_main) + len('</main>')
print(f"tab-deadlock found from {pos_dl_main} to {pos_dl_main_end} (length: {pos_dl_main_end - pos_dl_main})")

# Check where deadlock JS is located
pos_dl_js = ws.find('// ==================== DEADLOCK LAB CONTROLLER ===========================')
pos_dl_js_end = ws.find('// ==================== MAIN DATA POLLING LOOP ============================', pos_dl_js)
print(f"deadlock JS found from {pos_dl_js} to {pos_dl_js_end} (length: {pos_dl_js_end - pos_dl_js})")
