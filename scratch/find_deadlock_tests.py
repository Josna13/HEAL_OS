import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk('tests'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'deadlock' in c.lower() or 'banker' in c.lower():
                    print(f"Found in {p}:")
                    for m in re.finditer(r'def\s+(test_[a-zA-Z0-9_]+)', c):
                        if 'deadlock' in m.group(1).lower() or 'banker' in m.group(1).lower():
                            print(f"  - {m.group(1)}")
