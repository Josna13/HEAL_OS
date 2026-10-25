with open('dashboard/deadlock_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
pos = text.find('class TwoProcessDeadlockSimulation')
if pos != -1:
    print(text[pos:pos+1500])
