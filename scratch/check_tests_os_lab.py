with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("test_os_lab.py test functions:")
for l in text.splitlines():
    if l.startswith('def test_'):
        print(l)
