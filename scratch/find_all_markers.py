import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find specific line ranges for key sections
markers = {
    'CSS_ROOT_START': 22,  # :root {
    'HTML_BODY_START': None,
    'TAB_OVERVIEW': None,
    'TAB_PROCESS_LAB': None,
    'TAB_RECOVERY': None,
    'TAB_DEADLOCK': None,
    'TAB_DIAGNOSTICS': None,
    'END_TABS': None,
    'SCRIPT_START': None,
    'STYLE_END': None,
    'renderWorkspace4': None,
    'renderWorkspace3': None,
    'renderOverviewExecutive': None,
}

for i, line in enumerate(lines):
    if '<body>' in line and markers['HTML_BODY_START'] is None:
        markers['HTML_BODY_START'] = i+1
    if 'id="tab-overview"' in line and markers['TAB_OVERVIEW'] is None:
        markers['TAB_OVERVIEW'] = i+1
    if 'id="tab-process-lab"' in line and markers['TAB_PROCESS_LAB'] is None:
        markers['TAB_PROCESS_LAB'] = i+1
    if 'id="tab-recovery"' in line and markers['TAB_RECOVERY'] is None:
        markers['TAB_RECOVERY'] = i+1
    if 'id="tab-deadlock"' in line and markers['TAB_DEADLOCK'] is None:
        markers['TAB_DEADLOCK'] = i+1
    if 'id="tab-diagnostics"' in line and markers['TAB_DIAGNOSTICS'] is None:
        markers['TAB_DIAGNOSTICS'] = i+1
    if '</div>' in line and markers['END_TABS'] is None and i > 1700:
        pass  # will figure out differently
    if '</style>' in line and markers['STYLE_END'] is None:
        markers['STYLE_END'] = i+1
    if '<script>' in line and markers['SCRIPT_START'] is None and i > 700:
        markers['SCRIPT_START'] = i+1
    if 'function renderWorkspace4' in line:
        markers['renderWorkspace4'] = i+1
    if 'function renderWorkspace3' in line:
        markers['renderWorkspace3'] = i+1
    if 'function renderOverviewExecutive' in line:
        markers['renderOverviewExecutive'] = i+1

for k, v in markers.items():
    print(f"  {k}: line {v}")
