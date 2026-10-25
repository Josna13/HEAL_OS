import sys
sys.path.insert(0, '.')
import time
import urllib.request
import json
from dashboard.web_server import WebDashboardServer

print("Starting WebDashboardServer on port 8092 for comprehensive verification...")
server = WebDashboardServer(port=8092)
server.start()
time.sleep(1.0)

try:
    # 1. HTML Verification
    print("\n--- TEST 1: HTML Verification ---")
    with urllib.request.urlopen("http://127.0.0.1:8092/") as resp:
        html = resp.read().decode('utf-8')
        assert resp.status == 200
        print(f"HTML response length: {len(html)} chars")

        required_elements = [
            'id="tab-overview"',
            'id="tab-process-lab"',
            'id="tab-deadlock"',
            'id="btn-sound-toggle"',
            'btn-algo-FCFS',
            'btn-algo-SJF',
            'btn-algo-RR',
            'btn-algo-PRIORITY',
            'sch-algo-pill',
            'btn-sch-play',
            'sch-clock-text',
            'sch-state-badge',
            'sch-ready-list',
            'sch-rq-count',
            'cpu-socket-box',
            'cpu-job-label',
            'cpu-burst-countdown',
            'cpu-progress-bar',
            'sch-comp-count',
            'sch-completed-list',
            'gantt-track',
            'gantt-cursor',
            'gantt-ruler',
            'sch-input-tbody',
            'sch-results-tbody',
            'avg-tat',
            'avg-wt',
            # Tab 1 Crash & Leak
            'btn-demo-crash',
            'panel-memleak-demo',
            'btn-demo-stop',
            'btn-demo-reset',
            'recovery-timeline-strip',
            # Tab 3 Deadlock
            'rag-svg',
            'deadlock-status-badge'
        ]

        for elem in required_elements:
            assert elem in html, f"Missing required HTML element: {elem}"
        print(f"[OK] All {len(required_elements)} core HTML elements verified present.")

    # 2. Scheduler Telemetry & Timeline in /api/status
    print("\n--- TEST 2: Scheduler Telemetry in /api/status ---")
    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert "scheduler" in data
        sch = data["scheduler"]
        print("Algorithm:", sch.get("algorithm"))
        print("Quantum:", sch.get("quantum"))
        print("Total Duration:", sch.get("total_duration"))
        print("Processes count:", len(sch.get("raw_processes", [])))
        print("Gantt blocks:", len(sch.get("gantt", [])))
        print("Timeline ticks count:", len(sch.get("timeline_ticks", [])))
        print("Process metrics count:", len(sch.get("process_metrics", [])))

        assert sch.get("total_duration") > 0
        assert len(sch.get("raw_processes", [])) >= 3
        assert len(sch.get("gantt", [])) > 0
        assert len(sch.get("timeline_ticks", [])) == sch.get("total_duration") + 1
        
        # Verify tick 0
        t0 = sch["timeline_ticks"][0]
        print("Tick 0 active process:", t0.get("active_process"))
        print("Tick 0 ready queue:", t0.get("ready_queue"))
        print("Tick 0 remaining burst:", t0.get("remaining_burst"))
        assert "active_process" in t0
        assert "ready_queue" in t0
        assert "remaining_burst" in t0
        assert "states" in t0
        print("[OK] Scheduler timeline ticks match frontend specification.")

    # 3. Scheduler Algorithm Switching & Quantum Updates
    print("\n--- TEST 3: Scheduler Algorithm Switching ---")
    for algo in ["FCFS", "SJF", "PRIORITY", "RR"]:
        req_algo = urllib.request.Request(
            "http://127.0.0.1:8092/api/action",
            data=json.dumps({"action": "set_scheduler_algo", "algo": algo}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_algo) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            assert res.get("status") == "ok"
        
        with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
            d = json.loads(resp.read().decode('utf-8'))
            assert d["scheduler"]["algorithm"] == algo
            print(f"[OK] Successfully switched algorithm to {algo}.")

    req_q = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "set_scheduler_quantum", "quantum": 3}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_q) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        assert d["scheduler"]["quantum"] == 3
        print("[OK] Successfully updated Round Robin quantum to 3.")

    # 4. Custom Process Inputs in Scheduler
    print("\n--- TEST 4: Custom Process Inputs in Scheduler ---")
    custom_procs = [
        {"label": "P1", "arrival_time": 0, "burst_time": 3, "priority": 1},
        {"label": "P2", "arrival_time": 1, "burst_time": 5, "priority": 2},
        {"label": "P3", "arrival_time": 2, "burst_time": 2, "priority": 3}
    ]
    req_cust = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "set_custom_scheduler_processes", "processes": custom_procs}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_cust) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        labels = [p["label"] for p in d["scheduler"]["raw_processes"]]
        assert labels == ["P1", "P2", "P3"]
        assert d["scheduler"]["total_duration"] == 10
        print("[OK] Custom process set accepted and simulated accurately.")

    # 5. Crash Recovery Demonstration
    print("\n--- TEST 5: Crash Recovery Demonstration ---")
    req_crash = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "trigger_crash"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_crash) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    time.sleep(0.5)
    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        pid_data = d["pid_comparison"]
        assert pid_data["has_recovery_occurred"] is True
        assert pid_data["old_pid"] != pid_data["new_pid"]
        print(f"[OK] Crash recovery verified: Old PID {pid_data['old_pid']} -> New PID {pid_data['new_pid']}.")

    # 6. Memory Leak Demonstration
    print("\n--- TEST 6: Memory Leak Demonstration ---")
    req_leak = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "start_memory_leak"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_leak) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    time.sleep(1.2)
    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        ml = d["memory_leak"]
        assert ml["is_running"] is True
        assert ml["allocated_mb"] > 0
        print(f"[OK] Memory leak active: {ml['allocated_mb']} MB allocated.")

    req_stop = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "stop_memory_leak"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_stop) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        assert d["memory_leak"]["is_running"] is False
        assert d["memory_leak"]["allocated_mb"] == 0.0
        print("[OK] Memory buffers stopped and cleared.")

    # 7. Deadlock Simulation
    print("\n--- TEST 7: Deadlock Simulation ---")
    req_dl = urllib.request.Request(
        "http://127.0.0.1:8092/api/action",
        data=json.dumps({"action": "step_two_process_deadlock"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_dl) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"

    with urllib.request.urlopen("http://127.0.0.1:8092/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        tp = d["deadlock"]["two_process"]
        assert tp["step"] == 1
        print(f"[OK] Deadlock step {tp['step']} verified.")

    print("\n=======================================================")
    print(" ALL 7 COMPREHENSIVE SUITE VERIFICATION TESTS PASSED! ")
    print("=======================================================")

finally:
    server.stop()
    print("Verification server stopped.")
