import sys
sys.path.insert(0, '.')

import urllib.request
import time
from dashboard.web_server import WebDashboardServer

server = WebDashboardServer(orchestrator_ref=None, port=8889)
server.start()
time.sleep(1.2)

# Make GET /
req = urllib.request.urlopen("http://127.0.0.1:8889/")
code = req.getcode()
content = req.read().decode("utf-8")
print(f"GET / -> Status code: {code}, Content length: {len(content)}")
assert code == 200
assert "CPU EXECUTION STUDIO" in content
assert "tab-process-lab" in content
assert "gantt-playback-cursor" in content
assert "live-ready-queue-strip" in content
assert "inspector-metric-grid" in content
print("HTML verification passed!")

# Make GET /api/status
req_status = urllib.request.urlopen("http://127.0.0.1:8889/api/status")
status_code = req_status.getcode()
status_json = req_status.read().decode("utf-8")
print(f"GET /api/status -> Status code: {status_code}, Length: {len(status_json)}")
assert status_code == 200
assert "scheduler" in status_json
print("All server endpoint tests PASSED!")

server.stop()
print("Server stopped cleanly.")
