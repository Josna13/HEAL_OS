import sys
sys.path.insert(0, '.')
import urllib.request
import time
import json
from dashboard.web_server import WebDashboardServer

server = WebDashboardServer(port=8082)
server.start()
time.sleep(1.2)

try:
    resp = urllib.request.urlopen("http://127.0.0.1:8082/")
    html = resp.read().decode("utf-8")
    
    required_features = [
        # Design system colors
        ("--bg-base: #0B1220", "Theme base color #0B1220"),
        ("--bg-surface: #111C2E", "Theme surface color #111C2E"),
        ("--bg-card: #172438", "Theme card color #172438"),
        ("--border: #26364D", "Theme border color #26364D"),
        ("--accent-cyan: #22D3EE", "Theme accent cyan #22D3EE"),
        ("--accent-green: #22C55E", "Theme accent green #22C55E"),
        ("--accent-amber: #F59E0B", "Theme accent amber #F59E0B"),
        ("--accent-red: #EF4444", "Theme accent red #EF4444"),
        ("--text-main: #F1F5F9", "Theme text main #F1F5F9"),
        
        # Panel 1: System Monitor Disk additions
        ("ov-kpi-disk-bar", "Disk animated usage bar"),
        ("ov-kpi-disk-val", "Disk percentage label"),
        ("ov-kpi-disk-used", "Disk used GB breakdown"),
        ("ov-kpi-disk-free", "Disk free GB breakdown"),
        ("threshold-marker-90", "Disk 90% threshold marker"),
        
        # Memory Leak Simulation (Section 7)
        ("Controlled Memory Leak Simulation", "Memory leak panel title"),
        ("[SIMULATION — Not Host RAM]", "Non-host simulated RAM badge"),
        ("btn-memleak-start", "Memory leak Start/Pause toggle button"),
        ("memleak-bar", "Memory leak live animated consumption bar"),
        ("memleak-chart", "Memory leak time-series canvas chart"),
        ("memleak-trend", "Memory leak live trend label (STABLE / LEAKING / CRITICAL)"),
        ("memLeakRecover", "Memory leak autonomic recovery reclamation"),
        
        # Guided Faculty Demo 8 Steps (Section 9)
        ("Step 1/8: Live System Monitoring & Telemetry", "Tour Step 1: Live monitoring"),
        ("Step 2/8: Process Creation & Simulated PID Allocation", "Tour Step 2: PID assignment"),
        ("Step 3/8: CPU Scheduling & Animated Execution Studio", "Tour Step 3: CPU Execution Studio"),
        ("Step 4/8: Controlled Crash & Self-Healing Recovery", "Tour Step 4: Controlled crash"),
        ("Step 5/8: Deadlock Formation & Resource Allocation Graph", "Tour Step 5: Deadlock RAG"),
        ("Step 6/8: Banker's Algorithm Safe-Sequence Analysis", "Tour Step 6: Banker's safe sequence"),
        ("Step 7/8: Memory Leak Simulation & Trend Monitoring", "Tour Step 7: Memory leak simulation"),
        ("Step 8/8: Recovery History, AI Prediction & Diagnostics", "Tour Step 8: Diagnostics & recovery history"),
        
        # CPU Execution Studio (Section 4)
        ("CPU EXECUTION STUDIO", "CPU Execution Studio main stage"),
        ("card-algo-RR", "Round Robin algorithm card"),
        ("card-algo-SJF", "SJF algorithm card"),
        ("card-algo-FCFS", "FCFS algorithm card"),
        ("card-algo-PRIORITY", "Priority algorithm card"),
        ("cpu-socket-element", "Central Core 0 socket element"),
        ("live-ready-queue-strip", "Live ready queue dispatch strip"),
        ("process-execution-lanes", "Process execution horizontal lanes"),
        ("gantt-playback-cursor", "Gantt timeline moving cursor line"),
        ("inspector-metric-grid", "Selected process inspector metrics grid"),
        
        # Crash & Self-Healing (Section 5)
        ("Autonomic Self-Healing & Process Handover Studio", "Self-healing studio title"),
        ("6-Stage Autonomic Handover Pipeline", "6-stage handover pipeline"),
        ("val-orig-pid", "Original PID forensics field"),
        ("val-repl-pid", "Replacement PID forensics field"),
        ("waterfall-bar", "Recovery timing waterfall bar"),
        
        # Deadlock & Banker's Lab (Section 6)
        ("svg-rag", "Resource Allocation Graph SVG"),
        ("Dijkstra's Banker's Algorithm", "Banker's algorithm section"),
        ("tbody-banker-alloc", "Banker's allocation matrix"),
        ("tbody-banker-max", "Banker's maximum matrix"),
        ("tbody-banker-need", "Banker's need matrix"),
    ]
    
    print(f"Total requirements to verify: {len(required_features)}")
    all_passed = True
    for token, desc in required_features:
        found = token in html
        status = "PASS" if found else "FAIL"
        if not found:
            all_passed = False
            print(f"  [{status}] {desc} (Token: {token})")
    
    if all_passed:
        print(f"\nALL {len(required_features)} VERIFICATION CHECKS PASSED PERFECTLY!")
    else:
        print("\nSome verification checks failed.")
        
finally:
    server.stop()
