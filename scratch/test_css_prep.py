import sys
sys.path.insert(0, '.')
import py_compile
import subprocess
import shutil

# Let's inspect where CSS keyframes can be added in web_server.py
with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

pos_style_end = ws.find('</style>')
print("Position of </style>:", pos_style_end)

pulse_css = """
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

print("CSS snippet ready.")
