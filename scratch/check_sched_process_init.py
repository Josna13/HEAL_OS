import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/cpu_scheduler.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('class ScheduledProcess')
print(text[pos:pos+500])
