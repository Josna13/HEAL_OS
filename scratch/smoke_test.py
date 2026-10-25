import sys
sys.path.insert(0, '.')
import subprocess
import time
import urllib.request

# Test web server starts and all key UI elements are present
from dashboard.web_server import WebDashboardServer
server = WebDashboardServer(port=8081)
server.start()
time.sleep(1.5)

try:
    resp = urllib.request.urlopen("http://127.0.0.1:8081/")
    code = resp.getcode()
    html = resp.read().decode("utf-8")
    print(f"Status: {code}")
    print(f"HTML size: {len(html)}")
    
    checks = [
        "CPU EXECUTION STUDIO",
        "tab-process-lab",
        "tab-overview",
        "tab-deadlock",
        "tab-recovery",
        "gantt-playback-cursor",
        "live-ready-queue-strip",
        "inspector-metric-grid",
        "algo-selector-grid",
        "studio-toolbar",
    ]
    all_ok = True
    for check in checks:
        found = check in html
        status = "OK" if found else "MISSING"
        print(f"  [{status}] {check}")
        if not found:
            all_ok = False
    
    print("\n" + ("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"))
    
    # Check /api/status
    resp2 = urllib.request.urlopen("http://127.0.0.1:8081/api/status")
    status_json = resp2.read().decode("utf-8")
    import json
    data = json.loads(status_json)
    print(f"\nAPI /api/status keys: {list(data.keys())}")
    print(f"scheduler keys: {list(data.get('scheduler', {}).keys())}")
    
finally:
    server.stop()
    print("\nServer stopped.")
