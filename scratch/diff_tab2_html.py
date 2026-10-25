import sys
import difflib
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

import re
m1 = re.search(r'(<main id="tab-process-lab".*?</main>)', clean, re.DOTALL)
m2 = re.search(r'(<main id="tab-process-lab".*?</main>)', ws, re.DOTALL)

if m1 and m2:
    lines1 = m1.group(1).splitlines()
    lines2 = m2.group(1).splitlines()
    diff = list(difflib.unified_diff(lines1, lines2, lineterm='', fromfile='clean', tofile='ws'))
    print("Diff in Tab 2 HTML (lines):", len(diff))
    for l in diff[:60]:
        print(l)
