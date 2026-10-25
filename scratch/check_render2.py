with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos_render2 = text.find('function renderWorkspace2')
pos_end_render2 = text.find('function renderWorkspace3')

print(f"renderWorkspace2 from {pos_render2} to {pos_end_render2}")
print(text[pos_render2:pos_render2+1200].encode('ascii', errors='replace').decode('ascii'))
