with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'def test_pid_comparison_on_successful_recovery' in l:
        print("".join(lines[i:i+60]))
        break
