import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    clean = f.read()

pos = clean.find('schState')
print("schState pos in clean:", pos)
if pos != -1:
    print(clean[pos:pos+1000])

# Let's find what follows schState until deadlock
pos_dl = clean.find('Deadlock', pos)
print("Deadlock pos in clean after schState:", pos_dl)
if pos_dl != -1:
    print("Length of scheduler JS in clean:", pos_dl - pos)
    print("End snippet:\n", clean[pos_dl-300:pos_dl+100])
