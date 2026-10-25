with open('dashboard/pid_comparison.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def get_comparison_table_data' in l:
        out = "".join(lines[i:i+60])
        print(out.encode('ascii', errors='replace').decode('ascii'))
        break
