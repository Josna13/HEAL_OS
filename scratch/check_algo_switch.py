import sys
sys.path.insert(0, '.')
import time
import urllib.request
import json
from dashboard.web_server import WebDashboardServer

server = WebDashboardServer(port=8093)
server.start()
time.sleep(1.0)

try:
    req_algo = urllib.request.Request(
        "http://127.0.0.1:8093/api/action",
        data=json.dumps({"action": "set_scheduler_algo", "algo": "FCFS"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_algo) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("set_scheduler_algo response:", res)

    with urllib.request.urlopen("http://127.0.0.1:8093/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        print("Scheduler algorithm in /api/status:", repr(d["scheduler"]["algorithm"]))

finally:
    server.stop()
