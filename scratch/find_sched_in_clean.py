with open('scratch/build_clean_ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'scheduler', text, re.IGNORECASE)]
print(f"Found {len(matches)} occurrences of 'scheduler' in build_clean_ui.py:")
for idx in matches[:10]:
    line_start = text.rfind('\n', 0, idx)
    line_end = text.find('\n', idx)
    print(text[line_start+1:line_end][:100].encode('ascii', errors='replace').decode('ascii'))
