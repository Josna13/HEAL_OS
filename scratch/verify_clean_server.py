import sys
sys.path.insert(0, '.')
import urllib.request
import time
import json
from dashboard.web_server import WebDashboardServer

s = WebDashboardServer(port=8082)
s.start()
time.sleep(1.5)
try:
    resp = urllib.request.urlopen('http://127.0.0.1:8082/')
    html = resp.read().decode('utf-8')
    print('HTML length:', len(html))
    print('HTTP code:', resp.getcode())
    print('Contains System Overview:', 'System Overview' in html)
    print('Contains CPU Scheduling:', 'CPU Scheduling' in html)
    print('Contains Deadlock:', 'Deadlock' in html)
    print('Contains OS Process Lifecycle:', 'OS Process Lifecycle' in html)
    print('Contains Core 0:', 'Core 0' in html)
    print('Contains Ready Queue:', 'Ready Queue' in html)
    print('Contains Gantt:', 'Gantt' in html)
    print('Contains RAG graph:', 'rag-graph-svg' in html)

    resp2 = urllib.request.urlopen('http://127.0.0.1:8082/api/status')
    data = json.loads(resp2.read().decode('utf-8'))
    print('API keys:', list(data.keys()))
    print('Lifecycle in data:', 'lifecycle' in data)
    print('Scheduler in data:', 'scheduler' in data)
    print('Deadlock in data:', 'deadlock' in data)
finally:
    s.stop()
    print('Server stopped.')
