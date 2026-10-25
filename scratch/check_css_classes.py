import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_css_end = ws.find('</style>')
css_text = ws[:pos_css_end]

classes_to_check = [
    'stage-grid', 'stage-card', 'stage-title', 'queue-token-list', 'proc-token',
    'cpu-socket', 'gantt-wrap', 'gantt-ruler', 'gantt-track', 'gantt-cursor'
]

print("Checking CSS classes in web_server.py:")
for c in classes_to_check:
    print(f"  .{c}:", f".{c}" in css_text)
