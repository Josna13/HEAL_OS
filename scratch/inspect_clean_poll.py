import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

pos = clean.find('function pollData(')
if pos != -1:
    print(clean[pos:pos+500])
