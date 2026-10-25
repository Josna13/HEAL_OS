import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Length of dashboard/web_server.py: {len(text)} chars, {len(text.splitlines())} lines")

# Check for tab2 in web_server.py
tab2_pos = text.find('id="tab-process-lab"')
print("tab-process-lab position:", tab2_pos)
if tab2_pos != -1:
    snippet = text[tab2_pos:tab2_pos+500]
    print("tab2 snippet:\n", snippet)

# Check for schState or scheduler JS
print("schState in web_server.py:", 'schState' in text)
print("build_clean_ui elements:")
print("  gantt-cursor:", 'gantt-cursor' in text)
print("  CPU CORE 0:", 'CPU CORE 0' in text)
print("  READY QUEUE:", 'READY QUEUE' in text)
print("  COMPLETED JOBS:", 'COMPLETED JOBS' in text)
print("  renderGanttTrack:", 'renderGanttTrack' in text)
print("  renderInputTable:", 'renderInputTable' in text)
print("  renderInputRows:", 'renderInputRows' in text)

# Check sound effects
print("Sound effects / playTone:")
print("  playTone:", 'playTone' in text)
print("  SOUND_MAP:", 'SOUND_MAP' in text)
print("  btn-sound-toggle:", 'btn-sound-toggle' in text)

