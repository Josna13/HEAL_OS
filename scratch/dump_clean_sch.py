with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderScheduler(')
if idx != -1:
    print(text[idx-500:idx+2500].encode('ascii', errors='replace').decode('ascii'))
