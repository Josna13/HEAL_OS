import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

target = """action == "set_custom_scheduler_processes":
                p_list = data.get("processes", [])
                procs = []
                for p in p_list:
                    lbl = p.get("label", "P1")
                    at = int(p.get("arrival_time", 0))
                    bt = int(p.get("burst_time", 4))
                    pr = int(p.get("priority", 1))
                    procs.append(ScheduledProcess(lbl, at, bt, pr))
                self.__class__.scheduler_procs = procs; self.scheduler_procs = procs"""

replacement = """action == "set_custom_scheduler_processes":
                p_list = data.get("processes", [])
                procs = []
                for idx, p in enumerate(p_list):
                    pid_val = idx + 1
                    lbl_val = str(p.get("label", f"P{pid_val}"))
                    at_val = max(0, int(p.get("arrival_time", 0)))
                    bt_val = max(1, int(p.get("burst_time", 4)))
                    pr_val = max(1, int(p.get("priority", 1)))
                    procs.append(ScheduledProcess(pid=pid_val, label=lbl_val, arrival_time=at_val, burst_time=bt_val, priority=pr_val))
                if procs:
                    self.__class__.scheduler_procs = procs
                    self.scheduler_procs = procs"""

if target in ws:
    ws = ws.replace(target, replacement)
    with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
        f.write(ws)
    print("Fixed ScheduledProcess instantiation in set_custom_scheduler_processes!")
else:
    print("Target not found!")
