import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

print("File size:", len(ws), "lines:", len(ws.splitlines()))

# Check Main Tabs in web_server.py HTML:
m = re.findall(r'<main id="([^"]+)"', ws)
print("Main tabs in web_server.py:", m)

# Check sound functions in web_server.py:
pos_sound = ws.find('function playTone(')
if pos_sound != -1:
    print("\nplayTone snippet:\n", ws[pos_sound:pos_sound+800])

# Check sound toggle
pos_toggle = ws.find('function toggleSound(')
if pos_toggle != -1:
    print("\ntoggleSound snippet:\n", ws[pos_toggle:pos_toggle+600])

# Check crash demo and memory leak demo in web_server.py
print("\nChecking crash demo & memory leak in web_server.py:")
print("  triggerCrashDemo:", 'triggerCrashDemo' in ws)
print("  startMemLeakDemo:", 'startMemLeakDemo' in ws)
print("  renderRecoverySection:", 'renderRecoverySection' in ws)
print("  renderMemoryLeakPanel:", 'renderMemoryLeakPanel' in ws)
print("  Deadlock Lab:", 'renderDeadlock' in ws)
