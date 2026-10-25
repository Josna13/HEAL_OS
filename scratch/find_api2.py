import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Dump the /api/status handler
for i in range(4477, min(4477+400, len(lines))):
    with open('scratch/api_handler.txt', 'w', encoding='utf-8') as out:
        for j in range(4477, min(4477+400, len(lines))):
            out.write(f"{j+1}: {lines[j]}")
    break

# Also find the overview data construction
for i, line in enumerate(lines):
    if '"overview"' in line and ('standalone_state' in line or 'resp' in line or 'json' in line.lower()):
        if i > 4000:
            print(f"Line {i+1}: {line.strip()[:120]}")
            break

print("Done")
