import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

# Tab 2 HTML in clean:
m_clean_tab2 = re.search(r'(<main id="tab-process-lab".*?</main>)', clean, re.DOTALL)
m_ws_tab2 = re.search(r'(<main id="tab-process-lab".*?</main>)', ws, re.DOTALL)

print("clean tab2 len:", len(m_clean_tab2.group(1)) if m_clean_tab2 else None)
print("ws tab2 len:", len(m_ws_tab2.group(1)) if m_ws_tab2 else None)

# Tab 2 JS in clean:
# Let's find the start and end of scheduler JS in clean
pos_clean_sch_start = clean.find('let schState = {')
pos_clean_sch_end = clean.find('// =======================================================================\n    // TAB 3: DEADLOCK VISUALIZATION', pos_clean_sch_start)
clean_sch_js = clean[pos_clean_sch_start:pos_clean_sch_end]

# Tab 2 JS in web_server.py:
pos_ws_sch_start = ws.find('let schedulerState = {')
if pos_ws_sch_start == -1:
    pos_ws_sch_start = ws.find('let schState = {')
pos_ws_sch_end = ws.find('// =======================================================================\n    // TAB 3: DEADLOCK VISUALIZATION', pos_ws_sch_start)
ws_sch_js = ws[pos_ws_sch_start:pos_ws_sch_end]

print("clean_sch_js len:", len(clean_sch_js))
print("ws_sch_js len:", len(ws_sch_js))

# Let's inspect differences in JS
print("\n--- Start of clean_sch_js (first 400 chars) ---")
print(clean_sch_js[:400])

print("\n--- Start of ws_sch_js (first 400 chars) ---")
print(ws_sch_js[:400])
