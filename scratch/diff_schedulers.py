import difflib

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    c1 = f.read()

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    c2 = f.read()

# Tab 2 HTML
s1 = c1.find('<main id="tab-process-lab"')
e1 = c1.find('</main>', s1) + 7

s2 = c2.find('<main id="tab-process-lab"')
e2 = c2.find('</main>', s2) + 7

html1 = c1[s1:e1].splitlines()
html2 = c2[s2:e2].splitlines()

diff_html = list(difflib.unified_diff(html1, html2, lineterm=''))
print(f"HTML Diff ({len(diff_html)} lines):")
for l in diff_html[:40]:
    print(l.encode('ascii', errors='replace').decode('ascii'))

# Tab 2 JS
js1_s = c1.find('// ==================== CPU SCHEDULER CONTROLLER')
js1_e = c1.find('// ==================== DEADLOCK LAB CONTROLLER')

js2_s = c2.find('// ==================== CPU SCHEDULER CONTROLLER')
js2_e = c2.find('// ==================== DEADLOCK LAB CONTROLLER')

js1 = c1[js1_s:js1_e].splitlines()
js2 = c2[js2_s:js2_e].splitlines()

diff_js = list(difflib.unified_diff(js1, js2, lineterm=''))
print(f"\nJS Diff ({len(diff_js)} lines):")
for l in diff_js[:40]:
    print(l.encode('ascii', errors='replace').decode('ascii'))
