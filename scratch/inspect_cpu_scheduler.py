import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/cpu_scheduler.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of cpu_scheduler.py:", len(text))

# Let's inspect get_timeline_at_tick
pos = text.find('def get_timeline_at_tick')
if pos != -1:
    print(text[pos:pos+1000])
