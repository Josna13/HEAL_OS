import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_t2 = ws.find('<main id="tab-process-lab"')
pos_t2_end = ws.find('</main>', pos_t2) + len('</main>')

print("Tab 2 length in web_server.py:", pos_t2_end - pos_t2)
print("First 300 chars:")
print(ws[pos_t2:pos_t2+300])
print("Last 300 chars:")
print(ws[pos_t2_end-300:pos_t2_end])
