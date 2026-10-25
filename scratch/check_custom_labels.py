import sys
sys.path.insert(0, '.')
import time
import urllib.request
import json
from dashboard.web_server import WebDashboardServer

server = WebDashboardServer(port=8094)
server.start()
time.sleep(1.0)

try:
    custom_procs = [
        {"label": "P1", "arrival_time": 0, "burst_time": 3, "priority": 1},
        {"label": "P2", "arrival_time": 1, "burst_time": 5, "priority": 2},
        {"label": "P3", "arrival_time": 2, "burst_time": 2, "priority": 3}
    ]
    req_cust = urllib.request.Request(
        "http://127.0.0.1:8094/api/action",
        data=json.dumps({"action": "set_custom_scheduler_processes", "processes": custom_procs}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_cust) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Response:", res)

    with urllib.request.urlopen("http://127.0.0.1:8094/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        print("Raw processes in status:", d["scheduler"]["raw_processes"])
        labels = [p.get("label") or p.get("name") for p in d["scheduler"]["raw_processes"]]
        print("Labels:", labels)

finally:
    server.stop()
