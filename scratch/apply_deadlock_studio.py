import sys
sys.path.insert(0, '.')
import shutil
import py_compile
import subprocess
import re

sys.stdout.reconfigure(encoding='utf-8')

print("Starting integration of Deadlock & Recovery Studio into dashboard/web_server.py...")

# Read source files
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

# Backup
shutil.copyfile('dashboard/web_server.py', 'dashboard/web_server.py.pre_deadlock_bak')
print("Backed up to dashboard/web_server.py.pre_deadlock_bak")

# 1. Add Deadlock CSS
deadlock_css = """
    /* Deadlock Lab Real-Time Animations */
    @keyframes pulse-red {
      0% { filter: drop-shadow(0 0 3px #ef4444); stroke-width: 3px; }
      50% { filter: drop-shadow(0 0 12px #ef4444); stroke-width: 4.5px; }
      100% { filter: drop-shadow(0 0 3px #ef4444); stroke-width: 3px; }
    }
    @keyframes pulse-node-deadlock {
      0% { filter: drop-shadow(0 0 4px #ef4444); }
      50% { filter: drop-shadow(0 0 16px #ef4444); }
      100% { filter: drop-shadow(0 0 4px #ef4444); }
    }
    .edge-cycle {
      animation: pulse-red 1.2s infinite ease-in-out;
    }
    .node-deadlocked {
      animation: pulse-node-deadlock 1.2s infinite ease-in-out;
    }
"""

if "@keyframes pulse-red" not in ws:
    pos_style = ws.find('</style>')
    ws = ws[:pos_style] + deadlock_css + ws[pos_style:]
    print("Added Deadlock CSS keyframes.")

# 2. Replace Tab 3 HTML
from scratch.generate_deadlock_studio import dl_tab_html

pos_t3_start = ws.find('<main id="tab-deadlock"')
# include preceding comment if present
pos_t3_comment = ws.rfind('<!-- ===================================================================== -->\n  <!-- TAB 3:', 0, pos_t3_start)
if pos_t3_comment != -1:
    pos_t3_start = pos_t3_comment

pos_t3_end = ws.find('</main>', pos_t3_start) + len('</main>')

print(f"Replacing Tab 3 HTML from {pos_t3_start} to {pos_t3_end}")
ws = ws[:pos_t3_start] + dl_tab_html.strip() + ws[pos_t3_end:]

# 3. Update playSound in JavaScript with all dedicated deadlock sound effects
pos_playsound = ws.find('function playSound(event) {')
pos_playsound_end = ws.find('// Generic Action Dispatcher', pos_playsound)

new_playsound = """function playSound(event) {
      if (!soundEnabled) return;
      // CPU Scheduling & General Simulation Sounds
      if (event === 'PROC_START' || event === 'DISPATCH' || event === 'RUNNING') {
        playTone(587, 'sine', 0.12, 0.035);
      } else if (event === 'PROC_PREEMPT' || event === 'PREEMPT' || event === 'BLOCKED') {
        playTone(330, 'square', 0.08, 0.025);
      } else if (event === 'PROC_COMPLETE' || event === 'COMPLETE') {
        playTone(880, 'sine', 0.2, 0.04);
      } else if (event === 'CRASH_WARN') {
        playTone(220, 'sawtooth', 0.25, 0.05);
      } else if (event === 'RECOVERY_PASS') {
        playTone(523, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(659, 'sine', 0.2, 0.04), 110);
      } else if (event === 'RECOVERY_FAIL') {
        playTone(370, 'sawtooth', 0.14, 0.05);
        setTimeout(() => playTone(185, 'sawtooth', 0.22, 0.05), 120);
      } else if (event === 'LEAK_WARN') {
        playTone(700, 'sine', 0.15, 0.035);
      } 
      // Dedicated Deadlock & Recovery Lab Sound Effects
      else if (event === 'RES_ACQUIRE') {
        // Resource acquired: short, soft confirmation sound
        playTone(587, 'sine', 0.10, 0.035);
      } else if (event === 'RES_REQUEST') {
        // Resource request: subtle click or request sound
        playTone(440, 'triangle', 0.06, 0.025);
      } else if (event === 'PROC_BLOCKED') {
        // Process blocked: distinct warning tone
        playTone(310, 'square', 0.12, 0.035);
      } else if (event === 'DEADLOCK_ALERT' || event === 'DEADLOCK_CYCLE' || event === 'DEADLOCK') {
        // Deadlock detected: clear, brief alert sound
        playTone(260, 'sawtooth', 0.32, 0.055);
      } else if (event === 'RECOVERY_START') {
        // Recovery begins: distinct transition sound
        playTone(415, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(554, 'sine', 0.18, 0.04), 100);
      } else if (event === 'RES_RELEASE') {
        // Resource released: soft release sound
        playTone(520, 'sine', 0.08, 0.03);
        setTimeout(() => playTone(390, 'sine', 0.12, 0.025), 70);
      } else if (event === 'PROC_UNBLOCK') {
        // Process unblocked: short confirmation sound
        playTone(659, 'sine', 0.12, 0.035);
      } else if (event === 'ALL_COMPLETE' || event === 'DEADLOCK_RESOLVED') {
        // All processes completed: distinct success sound
        playTone(523, 'sine', 0.12, 0.04);
        setTimeout(() => playTone(659, 'sine', 0.14, 0.04), 90);
        setTimeout(() => playTone(784, 'sine', 0.22, 0.045), 180);
      }
    }
"""

ws = ws[:pos_playsound] + new_playsound.strip() + "\n\n    " + ws[pos_playsound_end:]

# 4. Replace Deadlock JS Controller
with open('scratch/dl_studio_js.txt', 'r', encoding='utf-8') as f:
    dl_js_code = f.read().strip()

pos_dl_js_start = ws.find('// ==================== DEADLOCK LAB CONTROLLER ===========================')
if pos_dl_js_start == -1:
    pos_dl_js_start = ws.find('// ==================== REAL-TIME DEADLOCK VISUALIZATION & RECOVERY STUDIO =====================')
pos_dl_js_end = ws.find('// ==================== MAIN DATA POLLING LOOP ============================', pos_dl_js_start)

print(f"Replacing Deadlock JS from {pos_dl_js_start} to {pos_dl_js_end}")
ws = ws[:pos_dl_js_start] + dl_js_code + "\n\n    " + ws[pos_dl_js_end:]

# 5. In switchMainTab: ensure deadlock tab calls renderDeadlockView()
ws = ws.replace("if (tabId === 'deadlock') pollData();", "if (tabId === 'deadlock') { renderDeadlockView(); pollData(); }")

# Write out modified web_server.py
with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(ws)

print(f"dashboard/web_server.py updated successfully. Length: {len(ws)} chars.")

# Verify py_compile
py_compile.compile('dashboard/web_server.py', doraise=True)
print("py_compile PASSED: Valid Python syntax!")

# Verify JS syntax with node --check
m_script = re.search(r'<script>(.*?)</script>', ws, re.DOTALL)
if m_script:
    with open('scratch/extracted_full.js', 'w', encoding='utf-8') as f_js:
        f_js.write(m_script.group(1))
    res = subprocess.run(['node', '--check', 'scratch/extracted_full.js'], capture_output=True, text=True)
    if res.returncode == 0:
        print("node --check PASSED: 0 JS syntax errors across the entire dashboard!")
    else:
        print("node --check FAILED:\n", res.stderr)
        sys.exit(1)
else:
    print("Could not find <script> tag!")
    sys.exit(1)

print("Deadlock Lab upgrade applied and verified successfully.")
