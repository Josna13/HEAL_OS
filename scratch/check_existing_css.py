with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

s_start = text.find('<style>')
s_end = text.find('</style>')
css = text[s_start:s_end]

for term in ['cpu-socket', 'gantt', 'lane', 'queue']:
    print(f"=== CSS with {term} ===")
    for line in css.split('\n'):
        if term in line.lower():
            print("  ", line.strip())
