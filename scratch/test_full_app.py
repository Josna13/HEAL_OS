import urllib.request
import time
import json
import subprocess
import sys

print("Testing starting main.py --web --no-dashboard ...")
p = subprocess.Popen([sys.executable, "main.py", "--web", "--no-dashboard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
try:
    for i in range(15):
        time.sleep(1.0)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:8080/")
            print(f"HTTP GET / Status (after {i+1}s):", req.getcode())
            html = req.read().decode('utf-8')
            print("HTML length:", len(html))
            
            req_api = urllib.request.urlopen("http://127.0.0.1:8080/api/status")
            print("HTTP GET /api/status Status:", req_api.getcode())
            data = json.loads(req_api.read().decode('utf-8'))
            print("Overview CPU:", data.get('overview', {}).get('cpu_percent'))
            print("Overview RAM:", data.get('overview', {}).get('ram_percent'))
            print("Scheduler procs count:", len(data.get('scheduler', {}).get('raw_processes', [])))
            print("Deadlock state step:", data.get('deadlock', {}).get('two_process', {}).get('step'))
            print("ALL VERIFICATIONS SUCCEEDED!")
            break
        except Exception as e:
            if i >= 14:
                raise e
            print(f"Waiting... ({e})")
finally:
    p.terminate()
    try:
        p.wait(timeout=3)
    except:
        p.kill()
    print("Process cleanly terminated.")
