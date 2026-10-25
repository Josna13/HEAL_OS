with open('dashboard/web_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = '''            elif action == "add_lifecycle_process":
                name = data.get("name", "new_task")
                at = int(data.get("arrival_time", 0))
                bt = int(data.get("cpu_burst", 4))
                pr = int(data.get("priority", 2))
                io_req = data.get("io_request_time")
                io_dur = data.get("io_duration", 2)
                p = self.lifecycle_engine.add_process(name, at, bt, pr, io_req, io_dur)
                self.record_event("PROCESS_CREATED", p.pid, f"Created PCB for '{name}' (BT={bt}, Priority={pr})", "[SIMULATION]")
            elif action == "remove_lifecycle_process":
                pid = data.get("pid", 101)
                self.lifecycle_engine.remove_process(pid)
                self.record_event("PROCESS_REMOVED", pid, f"Removed process PID {pid} from lifecycle studio", "[SIMULATION]")'''

replacement = '''            elif action == "add_lifecycle_process":
                name = str(data.get("name", "new_task")).strip()
                at = max(0, int(data.get("arrival_time", 0)))
                bt = max(1, int(data.get("cpu_burst", 4)))
                pr = max(1, int(data.get("priority", 1)))
                ioreq = data.get("io_request_time")
                if ioreq is not None and int(ioreq) > 0:
                    ioreq = int(ioreq)
                else:
                    ioreq = None
                iodur = max(0, int(data.get("io_duration", 0)))
                new_proc = self.lifecycle_engine.add_process(
                    name=name,
                    arrival_time=at,
                    cpu_burst=bt,
                    priority=pr,
                    io_request_time=ioreq,
                    io_duration=iodur,
                )
                self.record_event("LIFECYCLE_PROC_ADD", new_proc.pid, f"Allocated simulated PID P{new_proc.pid} for '{new_proc.name}' [SIMULATED PID].", "[SIMULATION]")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "pid": new_proc.pid}).encode("utf-8"))
                return
            elif action == "remove_lifecycle_process":
                pid_val = int(data.get("pid", 0))
                removed = self.lifecycle_engine.remove_process(pid_val)
                if removed:
                    self.record_event("LIFECYCLE_PROC_DEL", pid_val, f"Removed simulated process P{pid_val} from simulation manifest.", "[SIMULATION]")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "removed": removed}).encode("utf-8"))
                return'''

if target in text:
    text = text.replace(target, replacement)
    with open('dashboard/web_server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("web_server.py updated!")
else:
    print("Target not found in web_server.py!")

with open('scratch/build_crash_recovery_ui.py', 'r', encoding='utf-8') as f:
    btext = f.read()

if target in btext:
    btext = btext.replace(target, replacement)
    with open('scratch/build_crash_recovery_ui.py', 'w', encoding='utf-8') as f:
        f.write(btext)
    print("build_crash_recovery_ui.py updated!")
else:
    print("Target not found in build_crash_recovery_ui.py!")
