with open('dashboard/deadlock_lab.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('if s == 4:')
if pos != -1:
    print(text[pos:pos+1500])
