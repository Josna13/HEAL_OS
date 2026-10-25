import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/os_lab/cpu_scheduler.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('def validate_process_inputs')
print("Position:", pos)
if pos != -1:
    print(text[pos:pos+700])
