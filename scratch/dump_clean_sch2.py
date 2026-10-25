with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderGanttTrack(')
if idx != -1:
    print(text[idx:idx+3500].encode('ascii', errors='replace').decode('ascii'))
