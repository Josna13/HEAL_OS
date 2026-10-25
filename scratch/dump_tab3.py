with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<main id="tab-deadlock"')
end = text.find('</main>', start)
t3_html = text[start:end+7]
print(t3_html.encode('ascii', errors='replace').decode('ascii'))
