import re

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

tabs = re.findall(r'<button class="nav-tab[^"]*"[^>]*>(.*?)</button>', text, re.DOTALL)
print('Nav Tabs found:')
for t in tabs:
    clean_t = re.sub(r'<[^>]+>', '', t).strip()
    print(' -', repr(clean_t))

tab_divs = re.findall(r'<div id="tab-[^"]*"', text)
print('Tab divs found:', tab_divs)
