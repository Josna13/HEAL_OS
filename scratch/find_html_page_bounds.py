with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'HTML_PAGE =' in l or 'class WebDashboardHandler' in l or 'class SilentHTTPServer' in l:
        print(f"{i+1}: {l.strip()}")
