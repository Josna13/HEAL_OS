with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos_start = text.find('id="tab-process-lab"')
pos_end = text.find('id="tab-recovery"')

print(f"tab-process-lab starts at {pos_start}, ends at {pos_end}, length={pos_end - pos_start}")
