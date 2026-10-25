import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('tests/test_os_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('test_wait_for_graph_deadlock_cycle_detection')
print(text[pos:pos+3000])
