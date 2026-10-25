with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<main id="tab-overview">')
end = text.find('</main>', start)
overview_html = text[start:end+7]
print(overview_html.encode('ascii', errors='replace').decode('ascii'))
