with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Audio functions:")
for m in re.finditer(r'function playSound[^{]*\{', text):
    start = m.start()
    print(text[start:start+300])

print("\nAudio toggle / mute button:")
for line in text.splitlines():
    if 'sound' in line.lower() or 'audio' in line.lower() or 'mute' in line.lower():
        print(line[:120].encode('ascii', errors='replace').decode('ascii'))
