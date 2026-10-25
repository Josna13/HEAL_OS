with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("First 25 lines of dashboard/web_server.py:")
for j in range(min(25, len(lines))):
    print(f"{j+1}: {lines[j]}", end='')
