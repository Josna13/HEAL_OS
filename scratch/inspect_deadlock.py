import re

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    c = f.read()

print('svg occurrences:', len(re.findall(r'<svg', c)))
print('deadlock elements:', re.findall(r'id="[^"]*deadlock[^"]*"', c))
print('graph elements:', re.findall(r'id="[^"]*graph[^"]*"', c))
print('rag elements:', re.findall(r'id="[^"]*rag[^"]*"', c))
