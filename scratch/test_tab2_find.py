import os, sys, re, subprocess, py_compile
sys.path.insert(0, os.path.abspath('.'))

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    orig_code = f.read()

# Let's verify we can find the start and end of tab-process-lab
start_tag = '<div id="tab-process-lab" style="display: none;">'
end_tag = '<!-- ========================================================================= -->\n<!-- TAB 3: SELF-HEALING & RECOVERY -->'

assert start_tag in orig_code, "Could not find start_tag"
assert end_tag in orig_code, "Could not find end_tag"
print("Found tab-process-lab boundaries!")
