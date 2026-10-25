import os, sys, re, subprocess, py_compile
sys.path.insert(0, os.path.abspath('.'))

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect the exact lines where tab-process-lab starts and ends
start_marker = '<div id="tab-process-lab" style="display: none;">'
end_marker = '<!-- ========================================================================= -->\n<!-- TAB 3: SELF-HEALING & RECOVERY -->'

assert start_marker in text
assert end_marker in text

pos_start = text.find(start_marker)
pos_end = text.find(end_marker)

print(f"tab-process-lab located: {pos_start} to {pos_end}")
