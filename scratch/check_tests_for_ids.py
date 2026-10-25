import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

found = []
for root, dirs, files in os.walk('tests'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'deadlock-status-badge' in c or 'rag-svg' in c:
                    found.append((p, 'found'))

print("Found in tests:", found)
