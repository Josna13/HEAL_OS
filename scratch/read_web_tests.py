with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def test_web_server' in l or 'def test_lifecycle_web' in l:
        print("".join(lines[i:i+40]))
