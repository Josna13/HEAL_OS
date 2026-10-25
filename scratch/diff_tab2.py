import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

with open('scratch/build_crash_recovery_ui.py', 'r', encoding='utf-8') as f:
    crash = f.read()

# Extract Tab 2 HTML in clean
m_clean_tab2 = re.search(r'(<!--\s*=+\s*-->\s*<!--\s*TAB 2:.*?-->\s*<main id="tab-process-lab".*?</main>)', clean, re.DOTALL)
m_crash_tab2 = re.search(r'(<!--\s*=+\s*-->\s*<!--\s*TAB 2:.*?-->\s*<main id="tab-process-lab".*?</main>)', crash, re.DOTALL)

print("clean tab2 HTML found:", bool(m_clean_tab2))
print("crash tab2 HTML found:", bool(m_crash_tab2))

if m_clean_tab2 and m_crash_tab2:
    clean_html = m_clean_tab2.group(1)
    crash_html = m_crash_tab2.group(1)
    print(f"clean tab2 HTML len: {len(clean_html)}, crash tab2 HTML len: {len(crash_html)}")
    print("Are tab2 HTMLs identical?", clean_html == crash_html)

# Extract Scheduler JS in clean
m_clean_js = re.search(r'(let schState = \{.*?\n  // =+ DEADLOCK)', clean, re.DOTALL)
m_crash_js = re.search(r'(let schedulerState = \{.*?\n    // =+ DEADLOCK)', crash, re.DOTALL)

print("clean scheduler JS found:", bool(m_clean_js))
print("crash scheduler JS found:", bool(m_crash_js))

if m_clean_js:
    print(f"clean scheduler JS len: {len(m_clean_js.group(1))}")
if m_crash_js:
    print(f"crash scheduler JS len: {len(m_crash_js.group(1))}")
