import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

ws = ws.replace("f\"{st['title']}: {st['description']}\"", "f\"{st.get('title', '')}: {st.get('explanation', st.get('description', ''))}\"")

with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(ws)

print("Fixed KeyError on st['description'] in dashboard/web_server.py")
