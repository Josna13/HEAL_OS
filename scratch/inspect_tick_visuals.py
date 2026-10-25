import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

pos_update = clean.find('function updateSchVisualsAtTick(')
print("updateSchVisualsAtTick pos:", pos_update)
if pos_update != -1:
    pos_next = clean.find('function schStep(', pos_update)
    print(clean[pos_update:pos_next])
