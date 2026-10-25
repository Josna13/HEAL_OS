with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    c1 = f.read()
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    c2 = f.read()

s1 = c1.find('id="tab-process-lab"')
e1 = c1.find('id="tab-deadlock"')

s2 = c2.find('id="tab-process-lab"')
e2 = c2.find('id="tab-deadlock"')

print('build_clean_ui tab2 HTML length:', e1 - s1)
print('web_server tab2 HTML length:', e2 - s2)
print('Are HTML identical?', c1[s1:e1] == c2[s2:e2])

# Now compare JS functions for scheduler:
js1_s = c1.find('// ==================== CPU SCHEDULER CONTROLLER')
js1_e = c1.find('// ==================== DEADLOCK LAB CONTROLLER')

js2_s = c2.find('// ==================== CPU SCHEDULER CONTROLLER')
js2_e = c2.find('// ==================== DEADLOCK LAB CONTROLLER')

print('JS1 length:', js2_e - js2_s)
print('Are JS identical?', c1[js1_s:js1_e] == c2[js2_s:js2_e])
