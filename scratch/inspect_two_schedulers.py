import re

with open('scratch/integrate_studio.py', 'r', encoding='utf-8') as f:
    s_text = f.read()

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    b_text = f.read()

print("integrate_studio.py length:", len(s_text))
print("build_clean_ui.py length:", len(b_text))

# Let's see what tab2 HTML in integrate_studio was:
m = re.search(r'new_tab2_html = """(.*?)"""', s_text, re.DOTALL)
if m:
    print("Found new_tab2_html in integrate_studio.py, length:", len(m.group(1)))
    # print first 50 lines
    lines = m.group(1).splitlines()[:50]
    for l in lines:
        print(l[:100].encode('ascii', errors='replace').decode('ascii'))
