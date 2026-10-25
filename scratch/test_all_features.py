import sys
sys.path.insert(0, '.')
import time
import urllib.request
import json
from dashboard.web_server import WebDashboardServer

print("Starting WebDashboardServer on port 8089 for feature verification...")
server = WebDashboardServer(port=8089)
server.start()
time.sleep(1.0)

try:
    # 1. Normal Application Monitoring
    print("\n--- TEST 1: Normal Application Monitoring ---")
    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ov = data['overview']
        print(f"App: {ov.get('app_name')}, PID: {ov.get('app_pid')}, Running: {ov.get('app_is_running')}")
        print(f"CPU: {ov.get('cpu_percent')}%, RAM: {ov.get('ram_percent')}%, Host Health: {ov.get('health_overall')}")
        assert ov.get('app_name') == 'dummy_app.py'
        assert ov.get('app_pid') is not None
        print("[OK] Normal monitoring verified.")

    # 2. Manual Crash Demonstration & Automatic Detection
    print("\n--- TEST 2: Manual Crash Demonstration ---")
    req_crash = urllib.request.Request(
        "http://127.0.0.1:8089/api/action",
        data=json.dumps({"action": "trigger_crash"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_crash) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Action trigger_crash response:", res)
        assert res.get("status") == "ok"

    # 3. Successful Recovery with Old/New Process Identification & 10 Fields
    print("\n--- TEST 3: Successful Recovery & Process Identification ---")
    time.sleep(0.5)
    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        pid_data = data['pid_comparison']
        print("Recovery occurred:", pid_data.get('has_recovery_occurred'))
        print("Old PID:", pid_data.get('old_pid'))
        print("New PID:", pid_data.get('new_pid'))
        print("Exit Code:", pid_data.get('exit_code'))
        print("Recovery Duration:", pid_data.get('recovery_duration_sec'), "s")
        print("Downtime:", pid_data.get('downtime_sec'), "s")
        print("Final Status:", pid_data.get('final_status'))
        print("Lifecycle stages count:", len(pid_data.get('lifecycle_timeline', [])))
        
        assert pid_data.get('has_recovery_occurred') is True
        assert pid_data.get('old_pid') != pid_data.get('new_pid')
        assert pid_data.get('final_status') == 'RUNNING'
        assert len(pid_data.get('lifecycle_timeline', [])) == 6
        print("[OK] Crash recovery and process identification verified.")

    # 4. Improved Health Analyzer Comparison
    print("\n--- TEST 4: Health Analyzer Before/During/After Comparison ---")
    hc = pid_data.get('health_comparison', {})
    print("Before Phase:", hc.get('before', {}).get('phase'), "- App Health:", hc.get('before', {}).get('app_health'), "- Sys Health:", hc.get('before', {}).get('system_health'))
    print("During Phase:", hc.get('during', {}).get('phase'), "- App Health:", hc.get('during', {}).get('app_health'), "- Sys Health:", hc.get('during', {}).get('system_health'))
    print("After Phase:", hc.get('after', {}).get('phase'), "- App Health:", hc.get('after', {}).get('app_health'), "- Sys Health:", hc.get('after', {}).get('system_health'))
    assert hc.get('during', {}).get('app_health') == 0
    assert hc.get('during', {}).get('system_health') == 98
    print("[OK] Health Analyzer isolation verified (app failed while OS kernel remained nominal).")

    # 5. Memory Leak Demo: Start and observe RAM increasing
    print("\n--- TEST 5: Memory Leak Demo (Start & Observe Growth) ---")
    req_mem = urllib.request.Request(
        "http://127.0.0.1:8089/api/action",
        data=json.dumps({"action": "start_memory_leak"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_mem) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Action start_memory_leak response:", res)

    # Poll over 2 seconds to observe real memory growth
    time.sleep(1.6)
    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ml = data['memory_leak']
        print(f"Memory Leak Status: {ml.get('status')}")
        print(f"Initial: {ml.get('initial_mb')} MB | Current: {ml.get('current_mb')} MB | Delta: +{ml.get('delta_mb')} MB | Peak: {ml.get('peak_mb')} MB")
        assert ml.get('allocated_mb') > 0
        assert ml.get('current_mb') > ml.get('initial_mb')
        print("[OK] Memory growth observed in real time.")

    # 6. Memory Leak Demo: Stop Demo and verify memory released
    print("\n--- TEST 6: Memory Leak Demo (Stop & Release) ---")
    req_stop = urllib.request.Request(
        "http://127.0.0.1:8089/api/action",
        data=json.dumps({"action": "stop_memory_leak"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_stop) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Action stop_memory_leak response:", res)

    time.sleep(0.3)
    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ml = data['memory_leak']
        print(f"Post-stop Status: {ml.get('status')}, Allocated: {ml.get('allocated_mb')} MB")
        assert ml.get('is_running') is False
        assert ml.get('allocated_mb') == 0.0
        print("[OK] Memory buffers cleanly cleared and collected.")

    # 7. Memory Leak Demo: Reset Demo
    print("\n--- TEST 7: Memory Leak Demo (Reset) ---")
    req_reset = urllib.request.Request(
        "http://127.0.0.1:8089/api/action",
        data=json.dumps({"action": "reset_memory_leak"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_reset) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Action reset_memory_leak response:", res)

    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ml = data['memory_leak']
        assert ml.get('status') == 'IDLE'
        print("[OK] Memory leak state reset to baseline IDLE.")

    # 8. CPU and RAM Monitoring After Both Demonstrations
    print("\n--- TEST 8: Steady-State Monitoring After Both Demos ---")
    with urllib.request.urlopen("http://127.0.0.1:8089/api/status") as resp:
        data = json.loads(resp.read().decode('utf-8'))
        ov = data['overview']
        print(f"Final CPU: {ov.get('cpu_percent')}%, RAM: {ov.get('ram_percent')}%, Health: {ov.get('health_overall')}")
        assert ov.get('cpu_percent') >= 0
        assert ov.get('ram_percent') >= 0
        print("[OK] Steady-state telemetry operational.")

    print("\n==========================================")
    print(" ALL 8 SYSTEM VERIFICATION TESTS PASSED! ")
    print("==========================================")

finally:
    server.stop()
    print("Verification server stopped.")
