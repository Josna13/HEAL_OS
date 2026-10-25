import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    ws = f.read()

# Replace instance assignments in _do_POST_impl with self.__class__
ws = ws.replace("self.scheduler_algo = algo", "self.__class__.scheduler_algo = algo; self.scheduler_algo = algo")
ws = ws.replace("self.scheduler_quantum = int(data.get(\"quantum\", 2))", "self.__class__.scheduler_quantum = int(data.get(\"quantum\", 2)); self.scheduler_quantum = self.__class__.scheduler_quantum")
ws = ws.replace("self.scheduler_procs = new_procs", "self.__class__.scheduler_procs = new_procs; self.scheduler_procs = new_procs")
ws = ws.replace("self.scheduler_procs = CPUScheduler.get_default_processes()", "self.__class__.scheduler_procs = CPUScheduler.get_default_processes(); self.scheduler_procs = self.__class__.scheduler_procs")
ws = ws.replace("self.deadlock_scenario_key = data.get(\"scenario\", \"two_process\")", "self.__class__.deadlock_scenario_key = data.get(\"scenario\", \"two_process\"); self.deadlock_scenario_key = self.__class__.deadlock_scenario_key")

with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
    f.write(ws)

print("Updated scheduler state persistence across HTTP requests in dashboard/web_server.py.")
