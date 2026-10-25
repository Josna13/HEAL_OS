with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'def test_[a-zA-Z0-9_]+', text)
print(f"Found {len(matches)} tests:")
for m in matches[:15]:
    print(" ", m)
