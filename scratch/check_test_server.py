with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in [715, 970]:
    print(f"Around line {idx}:")
    for j in range(max(0, idx-5), min(len(lines), idx+15)):
        print(f"  {j+1}: {lines[j].strip()}")
