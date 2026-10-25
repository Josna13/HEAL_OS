import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/cpu_scheduler.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('def get_timeline_at_tick')
pos2 = text.find('\n    def ', pos + 10)
print(text[pos:pos2])
