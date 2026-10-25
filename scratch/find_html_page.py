with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'HTML_PAGE = """' in l:
        print(f"HTML_PAGE starts at line {i+1}")
    if 'class WebDashboardHandler' in l:
        print(f"WebDashboardHandler at line {i+1}")
