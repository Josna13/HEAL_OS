import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_t3 = ws.find('<main id="tab-deadlock"')
pos_t3_end = ws.find('</main>', pos_t3) + len('</main>')

print(f"Tab 3 length: {pos_t3_end - pos_t3} characters")
print("First 800 chars:\n", ws[pos_t3:pos_t3+800])
print("\nLast 800 chars:\n", ws[pos_t3_end-800:pos_t3_end])
