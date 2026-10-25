import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_play_sound = ws.find('function playSound(event)')
pos_play_sound_end = ws.find('// Generic Action Dispatcher', pos_play_sound)
print(ws[pos_play_sound:pos_play_sound_end])
