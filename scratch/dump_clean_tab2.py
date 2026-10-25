import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

import re
m = re.search(r'(<!--\s*=+\s*-->\s*<!--\s*TAB 2: CPU SCHEDULING.*?-->\s*<main id="tab-process-lab".*?</main>)', clean, re.DOTALL)
if m:
    with open('scratch/clean_tab2_html.txt', 'w', encoding='utf-8') as out:
        out.write(m.group(1))
    print("Clean tab2 HTML length:", len(m.group(1)))
else:
    print("Clean tab2 HTML not found!")
