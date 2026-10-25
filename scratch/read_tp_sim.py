import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/deadlock_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('class TwoProcessDeadlockSimulation')
pos_end = text.find('class BankersAlgorithm', pos)
print(text[pos:pos_end])
