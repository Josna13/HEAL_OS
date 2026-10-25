import sys, os
sys.path.insert(0, os.path.abspath('.'))
from dashboard.cpu_scheduler import CPUScheduler

procs = CPUScheduler.get_default_processes()
res_rr = CPUScheduler.run_round_robin(procs, time_quantum=2)
res_fcfs = CPUScheduler.run_fcfs(procs)
res_sjf = CPUScheduler.run_sjf(procs)
res_prio = CPUScheduler.run_priority(procs)

print("Default processes:")
for p in procs:
    print(f"  P{p.pid} ({p.label}): AT={p.arrival_time}, BT={p.burst_time}, Prio={p.priority}")

print("\nRR Gantt blocks:")
for b in res_rr.gantt_chart:
    print(f"  {b.label}: [{b.start} -> {b.end}] duration={b.duration}")

print("\nRR timeline tick 0..5:")
for t in range(min(6, res_rr.total_duration + 1)):
    tl = res_rr.get_timeline_at_tick(t)
    print(f"  t={t}: active={tl['active_process']}, ready={tl['ready_queue']}, rem={tl['remaining_burst']}")
