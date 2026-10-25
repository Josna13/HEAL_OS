import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

pos_start = clean.find('let schState = {')
pos_end = clean.find('// =======================================================================\n    // TAB 3: DEADLOCK VISUALIZATION', pos_start)
clean_js = clean[pos_start:pos_end]

print("Length:", len(clean_js))
with open('scratch/clean_sch_js.txt', 'w', encoding='utf-8') as out:
    out.write(clean_js)

print("Saved to scratch/clean_sch_js.txt")
