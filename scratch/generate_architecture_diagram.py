"""
generate_architecture_diagram.py
Generates an ultra-clean, high-resolution System Architecture Diagram for HealOS
Matching the dark navy design system: #0B1220, #111C2E, #172438, #26364D, #22D3EE, #22C55E, #F59E0B, #EF4444
Outputs: E:\HealOs\HealOS_System_Architecture_Diagram.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle
import os

# Figure Setup
fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=150)
fig.patch.set_facecolor('#0B1220')
ax.set_facecolor('#0B1220')
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color Palette Constants
C_BG_CARD     = '#111C2E'
C_BG_SUB      = '#172438'
C_BG_ALT      = '#1A2A40'
C_BORDER      = '#26364D'
C_BORDER_HI   = '#2D4A6B'
C_CYAN        = '#22D3EE'
C_GREEN       = '#22C55E'
C_AMBER       = '#F59E0B'
C_RED         = '#EF4444'
C_PURPLE      = '#A855F7'
C_BLUE        = '#3B82F6'
C_TEXT_MAIN   = '#F1F5F9'
C_TEXT_MUTED  = '#94A3B8'
C_TEXT_DIM    = '#64748B'

def draw_card(ax, x, y, w, h, bg=C_BG_CARD, border=C_BORDER, lw=1.5, radius=0.8):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=bg, edgecolor=border, linewidth=lw, zorder=2
    )
    ax.add_patch(box)
    return box

def draw_arrow(ax, x1, y1, x2, y2, color=C_CYAN, lw=2.0, style='-|>', ls='-'):
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            linestyle=ls, mutation_scale=14, zorder=5
        )
    )

# ----------------- 1. HEADER BANNER -----------------
draw_card(ax, 3, 91.5, 94, 6.5, bg=C_BG_SUB, border=C_BORDER_HI, radius=0.6)

# Badge
badge = FancyBboxPatch((4.5, 93.0), 14, 3.5, boxstyle="round,pad=0,rounding_size=0.4",
                       facecolor=C_BG_CARD, edgecolor=C_CYAN, linewidth=1.2, zorder=3)
ax.add_patch(badge)
ax.text(11.5, 94.75, "SYSTEM ARCHITECTURE", color=C_CYAN, fontsize=9.5, fontweight='bold',
        ha='center', va='center', fontfamily='sans-serif', zorder=4)

ax.text(20.5, 95.0, "HealOS 2.0: Operating Systems Execution & Simulation Framework",
        color=C_TEXT_MAIN, fontsize=15, fontweight='bold', ha='left', va='center', fontfamily='sans-serif', zorder=4)
ax.text(20.5, 93.0, "End-to-End Component Hierarchy • Dual-Mode Telemetry & Simulation • Closed-Loop Autonomic Self-Healing",
        color=C_TEXT_MUTED, fontsize=9.5, ha='left', va='center', fontfamily='sans-serif', zorder=4)

# ----------------- 2. TIER 1: CLIENT PRESENTATION LAYER -----------------
draw_card(ax, 3, 67.5, 94, 21.5, bg=C_BG_CARD, border=C_CYAN, lw=1.8, radius=1.0)
ax.text(5.5, 86.8, "TIER 1: CLIENT PRESENTATION LAYER (SINGLE-PAGE BROWSER CONSOLE)",
        color=C_CYAN, fontsize=11, fontweight='bold', ha='left', va='center', fontfamily='sans-serif', zorder=4)
ax.text(5.5, 85.0, "Pure Vanilla HTML5 / CSS3 Design System • Native SVG & Canvas Graphics • Web Audio API Synthesizer (Zero External JS Bundles)",
        color=C_TEXT_MUTED, fontsize=8.5, ha='left', va='center', fontfamily='sans-serif', zorder=4)

# Tab 1 Card
draw_card(ax, 5.5, 69.5, 20.5, 14.0, bg=C_BG_SUB, border=C_CYAN, lw=1.2)
ax.text(15.75, 81.8, "TAB 1: SYSTEM OVERVIEW", color=C_CYAN, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=4)
t1_text = (
    "• Real-time CPU, RAM & Disk KPIs\n"
    "• Animated SVG Sparkline Curves\n"
    "• Dynamic 75% & 90% Thresholds\n"
    "• 'Simulate Crash' Trigger Button\n"
    "• 10-Field Old vs New PID Table\n"
    "• Bounded 64 MB Memory Stress"
)
ax.text(6.8, 75.5, t1_text, color=C_TEXT_MAIN, fontsize=8.0, va='center', fontfamily='sans-serif', zorder=4)

# Tab 2 Card
draw_card(ax, 28.0, 69.5, 20.5, 14.0, bg=C_BG_SUB, border=C_GREEN, lw=1.2)
ax.text(38.25, 81.8, "TAB 2: CPU SCHEDULING", color=C_GREEN, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=4)
t2_text = (
    "• Process Input Studio (PID, AT, BT, P)\n"
    "• FCFS, SJF, Round Robin (q=2), Priority\n"
    "• 3-Stage Pipeline: Ready -> CPU -> Done\n"
    "• Live Remaining Burst Countdown\n"
    "• Interactive SVG Gantt Timeline\n"
    "• Speed Controls (0.5x, 1x, 2x, 4x)"
)
ax.text(29.3, 75.5, t2_text, color=C_TEXT_MAIN, fontsize=8.0, va='center', fontfamily='sans-serif', zorder=4)

# Tab 3 Card
draw_card(ax, 50.5, 69.5, 20.5, 14.0, bg=C_BG_SUB, border=C_AMBER, lw=1.2)
ax.text(60.75, 81.8, "TAB 3: DEADLOCK LAB", color=C_AMBER, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=4)
t3_text = (
    "• 3 Scenarios: 3-Proc, 2-Proc, Banker\n"
    "• Animated SVG Resource Graph (RAG)\n"
    "• Tarjan's / DFS Wait-For-Graph Cycle\n"
    "• Pulsating Red Circular Wait Alert\n"
    "• Deterministic Victim Preemption\n"
    "• Banker's Safe Sequence Suite"
)
ax.text(51.8, 75.5, t3_text, color=C_TEXT_MAIN, fontsize=8.0, va='center', fontfamily='sans-serif', zorder=4)

# Web Audio API Card
draw_card(ax, 73.0, 69.5, 22.0, 14.0, bg=C_BG_SUB, border=C_PURPLE, lw=1.2)
ax.text(84.0, 81.8, "WEB AUDIO SYNTHESIZER", color=C_PURPLE, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=4)
t_audio_text = (
    "• Additive Synthesis Oscillators\n"
    "• 9 Discrete Synthesized Cues:\n"
    "  - RES_ACQUIRE, RES_REQUEST\n"
    "  - PROC_BLOCKED, DEADLOCK_ALERT\n"
    "  - RECOVERY_START, PROC_UNBLOCK\n"
    "  - ALL_COMPLETE, RECOVERY_FAIL"
)
ax.text(74.3, 75.5, t_audio_text, color=C_TEXT_MAIN, fontsize=8.0, va='center', fontfamily='sans-serif', zorder=4)

# Flow Arrows between Tier 1 and Tier 2
draw_arrow(ax, 15.75, 67.5, 15.75, 59.5, color=C_CYAN, lw=2.0)
draw_arrow(ax, 38.25, 67.5, 38.25, 59.5, color=C_GREEN, lw=2.0)
draw_arrow(ax, 60.75, 67.5, 60.75, 59.5, color=C_AMBER, lw=2.0)
draw_arrow(ax, 84.0, 67.5, 84.0, 59.5, color=C_PURPLE, lw=2.0)

# Communication Protocol Ribbon
ax.text(50.0, 63.5, "Bi-directional Asynchronous REST / JSON over HTTP (Port 8080) • 1 Hz Host Polling • Event Triggers",
        color=C_CYAN, fontsize=8.5, fontweight='bold', ha='center', va='center', fontfamily='sans-serif', zorder=6)

# ----------------- 3. TIER 2: BACKEND SERVER & REST DISPATCHER -----------------
draw_card(ax, 3, 46.5, 94, 12.5, bg=C_BG_CARD, border=C_GREEN, lw=1.8, radius=1.0)
ax.text(5.5, 56.8, "TIER 2: BACKEND REST & SIMULATION DISPATCHER (main.py / dashboard/web_server.py)",
        color=C_GREEN, fontsize=11, fontweight='bold', ha='left', va='center', fontfamily='sans-serif', zorder=4)

d_boxes = [
    ("ThreadingHTTPServer", "Python standard library multi-threaded HTTP server (port 8080)", C_CYAN, 5.5),
    ("Telemetry Dispatcher", "GET /api/status\nPolls psutil & supervisor state", C_GREEN, 28.0),
    ("Scheduler Dispatcher", "POST /api/scheduler/simulate\nCalculates timeline & metrics", C_AMBER, 50.5),
    ("Deadlock & Action Router", "POST /api/action, /api/deadlock\nPreemption, crash & resets", C_PURPLE, 73.0)
]
for d_title, d_desc, d_col, px in d_boxes:
    draw_card(ax, px, 48.0, 21.0, 7.2, bg=C_BG_SUB, border=d_col, lw=1.0)
    ax.text(px + 10.5, 53.4, d_title, color=d_col, fontsize=8.8, fontweight='bold', ha='center', va='center', zorder=4)
    ax.text(px + 10.5, 50.2, d_desc, color=C_TEXT_MAIN, fontsize=7.5, ha='center', va='center', zorder=4)

# Flow Arrows between Tier 2 and Tier 3
draw_arrow(ax, 15.75, 46.5, 12.0, 39.5, color=C_CYAN, lw=2.0)
draw_arrow(ax, 38.25, 46.5, 30.5, 39.5, color=C_GREEN, lw=2.0)
draw_arrow(ax, 50.5, 46.5, 49.5, 39.5, color=C_AMBER, lw=2.0)
draw_arrow(ax, 73.0, 46.5, 68.5, 39.5, color=C_RED, lw=2.0)
draw_arrow(ax, 84.0, 46.5, 87.5, 39.5, color=C_PURPLE, lw=2.0)

# ----------------- 4. TIER 3: CORE SIMULATION & SUBSYSTEM ENGINES -----------------
draw_card(ax, 3, 20.0, 94, 19.5, bg=C_BG_CARD, border=C_AMBER, lw=1.8, radius=1.0)
ax.text(5.5, 37.5, "TIER 3: CORE OS ENGINES & SUBSYSTEMS (VERIFIED PYTHON MODULES)",
        color=C_AMBER, fontsize=11, fontweight='bold', ha='left', va='center', fontfamily='sans-serif', zorder=4)

engines = [
    ("SYSTEM MONITOR", "monitor/system_monitor.py",
     "• Polling thread (1 Hz)\n• Aggregate CPU % & per-core\n• RAM (Total, Used, RSS, %)\n• Disk Storage (Used, Free GB)\n• Process descriptor table",
     C_CYAN, 4.5, 17.0),
    ("AUTONOMIC SUPERVISOR", "recovery/auto_restart.py",
     "• Closed-loop fault recovery\n• Monitored: apps/dummy_app.py\n• 6-State recovery machine:\n  RUNNING->CRASH->RECOVER\n• Exponential backoff (<2.0s)",
     C_GREEN, 23.0, 17.5),
    ("CPU SCHEDULER", "dashboard/cpu_scheduler.py",
     "• FCFS, SJF, RR (q=2), Priority\n• Queue & burst decrement\n• Turnaround Time: CT - AT\n• Waiting Time: TAT - BT\n• Gantt block slice generation",
     C_AMBER, 42.0, 17.0),
    ("DEADLOCK & RECOVERY", "dashboard/deadlock_lab.py",
     "• Tarjan / DFS Cycle Finding\n• Wait-For-Graph (WFG)\n• Victim selection heuristics\n• Resource preemption & release\n• Banker's safety vector math",
     C_RED, 61.0, 17.5),
    ("PID COMPARISON", "dashboard/pid_comparison.py",
     "• 10-Field Telemetry Tracker:\n  PID, PPID, Status, Exit Code,\n  CPU %, RSS, Threads, Lifetime,\n  Restart Latency, State\n• Pre vs Post Crash Telemetry",
     C_PURPLE, 80.0, 17.0)
]

for e_name, e_file, e_desc, e_col, px, pw in engines:
    draw_card(ax, px, 21.5, pw, 14.5, bg=C_BG_SUB, border=e_col, lw=1.2)
    ax.text(px + pw/2, 34.2, e_name, color=e_col, fontsize=8.8, fontweight='bold', ha='center', va='center', zorder=4)
    ax.text(px + pw/2, 32.5, e_file, color=C_TEXT_MUTED, fontsize=6.8, fontfamily='monospace', ha='center', va='center', zorder=4)
    ax.text(px + 0.8, 26.8, e_desc, color=C_TEXT_MAIN, fontsize=7.2, va='center', fontfamily='sans-serif', zorder=4)

# ----------------- 5. TIER 4: HARDWARE & HOST OS RUNTIME -----------------
draw_card(ax, 3, 2.0, 94, 15.5, bg=C_BG_CARD, border=C_PURPLE, lw=1.8, radius=1.0)
ax.text(5.5, 15.5, "TIER 4: SUPERVISED APPLICATION & HOST OPERATING SYSTEM KERNEL",
        color=C_PURPLE, fontsize=11, fontweight='bold', ha='left', va='center', fontfamily='sans-serif', zorder=4)

h_boxes = [
    ("Supervised Target Process (apps/dummy_app.py)",
     "• Monitored child process running in user space with heartbeat\n• Listens for SIGTERM / SIGKILL simulation signals\n• Bounded memory leak stress buffer (capped at 64 MB)",
     C_GREEN, 5.0, 31.0),
    ("Cross-Platform System Instrumentation (psutil 7.2.2)",
     "• Queries host /proc (Linux) or NtQuerySystemInformation (Windows)\n• Extracts per-process memory maps, CPU affinities & thread counts\n• Direct kernel signal trapping and exit code capture",
     C_CYAN, 38.0, 31.0),
    ("Host Operating System Kernel (Linux WSL / Windows 11)",
     "• Hardware CPU Cores (Multi-core time slicing & SMP affinity)\n• Physical RAM & Virtual Memory Paging System\n• Block Storage / Filesystem Hierarchy & OS Signal Bus",
     C_PURPLE, 71.0, 24.5)
]

for h_title, h_desc, h_col, px, pw in h_boxes:
    draw_card(ax, px, 3.5, pw, 10.5, bg=C_BG_SUB, border=h_col, lw=1.0)
    ax.text(px + pw/2, 12.3, h_title, color=h_col, fontsize=8.2, fontweight='bold', ha='center', va='center', zorder=4)
    ax.text(px + 1.0, 7.8, h_desc, color=C_TEXT_MAIN, fontsize=7.2, va='center', fontfamily='sans-serif', zorder=4)

# Flow Arrows to Tier 4
draw_arrow(ax, 28.5, 20.0, 20.5, 14.0, color=C_GREEN, lw=2.0)
draw_arrow(ax, 12.0, 20.0, 53.5, 14.0, color=C_CYAN, lw=2.0)
draw_arrow(ax, 87.5, 20.0, 83.0, 14.0, color=C_PURPLE, lw=2.0)

# Save high-resolution graphic
out_path = os.path.abspath(r"E:\HealOs\HealOS_System_Architecture_Diagram.png")
plt.tight_layout()
plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=200)
plt.close()
print("Success! High-resolution architecture diagram saved to:", out_path)
