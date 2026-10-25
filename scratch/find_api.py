import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find what the API /api/status returns for disk
for i, line in enumerate(lines):
    if 'disk' in line.lower() and ('api' in line.lower() or 'status' in line.lower() or 'json' in line.lower()):
        if i > 4000:  # In the Python handler section
            print(f"Line {i+1}: {line.strip()[:100]}")

# Find the do_GET handler for /api/status
for i, line in enumerate(lines):
    if 'def do_GET' in line:
        print(f"\ndo_GET at line {i+1}")
        break
