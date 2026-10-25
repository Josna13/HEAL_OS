import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

for line in text.splitlines()[:20]:
    if 'import' in line:
        print(line)
