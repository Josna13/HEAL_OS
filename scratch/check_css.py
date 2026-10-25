with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find(':root {')
end = text.find('}', start)
print(text[start:end+1])
