with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

s_start = text.find('<style>')
s_end = text.find('</style>')
css = text[s_start:s_end]

pos = css.find('.cpu-socket-box {')
print(css[pos:pos+1200].encode('ascii', errors='replace').decode('ascii'))
