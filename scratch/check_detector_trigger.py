with open('detector/crash_detector.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'trigger', text, re.IGNORECASE)]
print("Found trigger in crash_detector.py:", len(matches))
for p in matches:
    print(text[p-50:p+100])
