import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

ws = ws.replace("self.scheduler_procs = procs", "self.__class__.scheduler_procs = procs; self.scheduler_procs = procs")

with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(ws)

print("Fixed self.scheduler_procs = procs to self.__class__.scheduler_procs = procs")
