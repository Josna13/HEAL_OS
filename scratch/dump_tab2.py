with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('<main id="tab-process-lab"')
end = text.find('</main>', start)
t2_html = text[start:end+7]
print(t2_html.encode('ascii', errors='replace').decode('ascii'))
