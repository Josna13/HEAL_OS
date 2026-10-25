with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('class WebDashboardHandler')
end = text.find('class WebDashboardServer', start)
print(text[start:end].encode('ascii', errors='replace').decode('ascii'))
