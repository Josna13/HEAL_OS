"""
HealOS 2.0 - CPU Scheduling Simulator & Visualizer (Section B)
Implements standard CPU scheduling algorithms:
1. First Come, First Served (FCFS)
2. Shortest Job First (SJF, Non-Preemptive)
3. Round Robin (RR, Configurable Quantum)
4. Priority Scheduling (Non-Preemptive, Lower Number = Higher Priority)

Computes exact OS metrics:
- Turnaround Time = Completion Time - Arrival Time
- Waiting Time    = Turnaround Time - Burst Time
- Response Time   = First Start Time - Arrival Time
- Context Switches: Counted whenever the CPU switches from one active process to a different active process.

Generates Gantt charts and tracks ready queues.
"""

from typing import List, Dict, Optional, Tuple, Any
from copy import deepcopy


class ScheduledProcess:
    """Attributes and metrics of a process in the CPU scheduling simulation."""

    def __init__(
        self,
        pid: int,
        label: str,
        arrival_time: int,
        burst_time: int,
        priority: int = 1,
    ):
        self.pid: int = pid
        self.label: str = label
        self.arrival_time: int = arrival_time
        self.burst_time: int = burst_time
        self.priority: int = priority  # 1 = highest priority

        # Metrics calculated upon completion
        self.first_start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.waiting_time: int = 0
        self.turnaround_time: int = 0
        self.response_time: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "label": self.label,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "first_start_time": self.first_start_time if self.first_start_time is not None else "-",
            "completion_time": self.completion_time if self.completion_time is not None else "-",
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
        }


class GanttBlock:
    """A contiguous interval of CPU execution in the Gantt chart."""

    def __init__(self, label: str, start: int, end: int):
        self.label: str = label
        self.start: int = start
        self.end: int = end

    @property
    def duration(self) -> int:
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
        }


class SchedulingResult:
    """Consolidated outcome of a scheduling simulation run."""

    def __init__(
        self,
        algorithm: str,
        processes: List[ScheduledProcess],
        gantt_chart: List[GanttBlock],
        context_switches: int,
        time_quantum: Optional[int] = None,
    ):
        self.algorithm: str = algorithm
        self.processes: List[ScheduledProcess] = processes
        self.gantt_chart: List[GanttBlock] = gantt_chart
        self.context_switches: int = context_switches
        self.time_quantum: Optional[int] = time_quantum

        # Aggregate averages
        n = len(processes)
        self.avg_waiting_time: float = sum(p.waiting_time for p in processes) / n if n > 0 else 0.0
        self.avg_turnaround_time: float = sum(p.turnaround_time for p in processes) / n if n > 0 else 0.0
        self.avg_response_time: float = sum(p.response_time for p in processes) / n if n > 0 else 0.0

    def get_timeline_at_tick(self, tick: int) -> Dict[str, Any]:
        """Provides simulated timeline state at time tick 'tick'."""
        max_time = max((p.completion_time or 0) for p in self.processes) if self.processes else 0
        clamped_tick = min(max(0, tick), max_time)

        # Determine currently executing process
        current_proc = "IDLE"
        for block in self.gantt_chart:
            if block.start <= clamped_tick < block.end:
                current_proc = block.label
                break

        # Calculate executed burst up to clamped_tick for each process
        remaining_burst = {}
        states = {}
        ready = []
        completed = []

        for p in self.processes:
            executed = 0
            for block in self.gantt_chart:
                if block.label == p.label and block.start < clamped_tick:
                    executed += min(clamped_tick, block.end) - block.start
            rem = max(0, p.burst_time - executed)
            remaining_burst[p.label] = rem

            if clamped_tick < p.arrival_time:
                states[p.label] = "NEW"
            elif rem == 0 and (p.completion_time is not None and clamped_tick >= p.completion_time):
                states[p.label] = "TERMINATED"
                completed.append(p.label)
            elif p.label == current_proc:
                states[p.label] = "RUNNING"
            else:
                states[p.label] = "READY"
                ready.append(p.label)

        # Detect context switch at this tick
        is_context_switch = False
        for i, block in enumerate(self.gantt_chart):
            if block.start == clamped_tick and clamped_tick > 0:
                prev_block = self.gantt_chart[i - 1] if i > 0 else None
                if prev_block and prev_block.label != "IDLE" and block.label != "IDLE" and prev_block.label != block.label:
                    is_context_switch = True
                break

        # Generate human-readable decision explanation
        if current_proc == "IDLE":
            decision_reason = f"CPU is IDLE at tick {clamped_tick}. No processes in ready queue; awaiting next arrival."
        elif self.algorithm.startswith("FCFS"):
            decision_reason = f"{current_proc} is executing on CPU based on First-Come, First-Served arrival order."
        elif self.algorithm.startswith("SJF"):
            matching = [p for p in self.processes if p.label == current_proc]
            b_val = matching[0].burst_time if matching else 0
            decision_reason = f"{current_proc} was dispatched with shortest burst ({b_val}t) among ready processes."
        elif "Round Robin" in self.algorithm:
            decision_reason = f"{current_proc} is executing in active time slice (Quantum={self.time_quantum}t). Remaining: {remaining_burst.get(current_proc, 0)}t."
        elif "Priority" in self.algorithm:
            matching = [p for p in self.processes if p.label == current_proc]
            p_val = matching[0].priority if matching else 1
            decision_reason = f"{current_proc} was dispatched with highest priority (Priority {p_val}) among ready jobs."
        else:
            decision_reason = f"{current_proc} is currently executing on CPU at tick {clamped_tick}."

        return {
            "tick": clamped_tick,
            "max_tick": max_time,
            "current_process": current_proc,
            "active_process": current_proc if current_proc != "IDLE" else None,
            "ready_queue": ready,
            "completed": completed,
            "remaining_burst": remaining_burst,
            "states": states,
            "decision_reason": decision_reason,
            "is_context_switch": is_context_switch,
            "is_finished": (clamped_tick >= max_time and max_time > 0),
        }

    @property
    def total_duration(self) -> int:
        return max((p.completion_time or 0) for p in self.processes) if self.processes else 0

    def to_dict(self) -> Dict[str, Any]:
        dur = self.total_duration
        return {
            "algorithm": self.algorithm,
            "time_quantum": self.time_quantum,
            "context_switches": self.context_switches,
            "total_duration": dur,
            "max_duration": dur,
            "avg_waiting_time": round(self.avg_waiting_time, 2),
            "avg_turnaround_time": round(self.avg_turnaround_time, 2),
            "avg_response_time": round(self.avg_response_time, 2),
            "processes": [p.to_dict() for p in self.processes],
            "process_metrics": [p.to_dict() for p in self.processes],
            "gantt": [b.to_dict() for b in self.gantt_chart],
            "gantt_chart": [b.to_dict() for b in self.gantt_chart],
        }


class CPUScheduler:
    """
    Simulates CPU scheduling algorithms deterministically.
    """

    @staticmethod
    def get_default_processes() -> List[ScheduledProcess]:
        """Provides a standard benchmark process set for classroom demonstrations."""
        return [
            ScheduledProcess(pid=1, label="P1", arrival_time=0, burst_time=7, priority=2),
            ScheduledProcess(pid=2, label="P2", arrival_time=2, burst_time=4, priority=1),
            ScheduledProcess(pid=3, label="P3", arrival_time=4, burst_time=1, priority=3),
            ScheduledProcess(pid=4, label="P4", arrival_time=5, burst_time=4, priority=2),
        ]

    @staticmethod
    def get_example_datasets() -> Dict[str, List[Dict[str, Any]]]:
        """Returns standard classroom reference datasets for comparative scheduling experiments."""
        return {
            "standard": [
                {"pid": 1, "label": "P1", "arrival_time": 0, "burst_time": 7, "priority": 2},
                {"pid": 2, "label": "P2", "arrival_time": 2, "burst_time": 4, "priority": 1},
                {"pid": 3, "label": "P3", "arrival_time": 4, "burst_time": 1, "priority": 3},
                {"pid": 4, "label": "P4", "arrival_time": 5, "burst_time": 4, "priority": 2},
            ],
            "convoy_effect": [
                {"pid": 1, "label": "P1", "arrival_time": 0, "burst_time": 12, "priority": 3},
                {"pid": 2, "label": "P2", "arrival_time": 1, "burst_time": 2, "priority": 1},
                {"pid": 3, "label": "P3", "arrival_time": 2, "burst_time": 2, "priority": 2},
                {"pid": 4, "label": "P4", "arrival_time": 3, "burst_time": 1, "priority": 1},
            ],
            "priority_mix": [
                {"pid": 1, "label": "P1", "arrival_time": 0, "burst_time": 4, "priority": 3},
                {"pid": 2, "label": "P2", "arrival_time": 1, "burst_time": 5, "priority": 1},
                {"pid": 3, "label": "P3", "arrival_time": 2, "burst_time": 2, "priority": 4},
                {"pid": 4, "label": "P4", "arrival_time": 3, "burst_time": 3, "priority": 2},
            ],
            "staggered_arrivals": [
                {"pid": 1, "label": "P1", "arrival_time": 0, "burst_time": 3, "priority": 2},
                {"pid": 2, "label": "P2", "arrival_time": 4, "burst_time": 5, "priority": 1},
                {"pid": 3, "label": "P3", "arrival_time": 6, "burst_time": 2, "priority": 3},
            ],
        }

    @staticmethod
    def validate_process_inputs(processes_data: List[Dict[str, Any]]) -> Tuple[bool, str, List[ScheduledProcess]]:
        """
        Validates user-submitted process definitions for scheduling simulation.
        Enforces:
        - Non-empty list (1 to 10 processes)
        - Unique labels
        - Integer arrival_time >= 0
        - Integer burst_time > 0
        - Integer priority >= 1
        """
        if not processes_data or not isinstance(processes_data, list):
            return False, "Process list cannot be empty.", []

        if len(processes_data) > 10:
            return False, "Maximum 10 processes allowed for simulation visualization.", []

        seen_labels = set()
        validated: List[ScheduledProcess] = []

        for idx, item in enumerate(processes_data):
            if not isinstance(item, dict):
                return False, f"Process row {idx + 1} is not a valid object.", []

            raw_pid = item.get("pid", idx + 1)
            raw_label = str(item.get("label", f"P{idx + 1}")).strip()
            if not raw_label:
                raw_label = f"P{idx + 1}"

            if raw_label in seen_labels:
                return False, f"Duplicate process label '{raw_label}'. Labels must be unique.", []
            seen_labels.add(raw_label)

            try:
                pid = int(raw_pid)
            except (ValueError, TypeError):
                pid = idx + 1

            try:
                at = int(item.get("arrival_time", 0))
                if at < 0:
                    return False, f"Process {raw_label}: Arrival time cannot be negative (got {at}).", []
            except (ValueError, TypeError):
                return False, f"Process {raw_label}: Arrival time must be an integer.", []

            try:
                bt = int(item.get("burst_time", 1))
                if bt <= 0:
                    return False, f"Process {raw_label}: Burst time must be greater than zero (got {bt}).", []
            except (ValueError, TypeError):
                return False, f"Process {raw_label}: Burst time must be an integer > 0.", []

            try:
                prio = int(item.get("priority", 1))
                if prio < 1:
                    prio = 1
            except (ValueError, TypeError):
                prio = 1

            validated.append(ScheduledProcess(pid=pid, label=raw_label, arrival_time=at, burst_time=bt, priority=prio))

        return True, "Processes validated successfully.", validated

    @staticmethod
    def run_fcfs(processes_input: List[ScheduledProcess]) -> SchedulingResult:
        """First Come, First Served (FCFS) Scheduling."""
        procs = [deepcopy(p) for p in processes_input]
        procs.sort(key=lambda p: (p.arrival_time, p.pid))

        current_time = 0
        gantt: List[GanttBlock] = []
        context_switches = 0
        last_running: Optional[str] = None

        for p in procs:
            if current_time < p.arrival_time:
                # CPU is idle
                gantt.append(GanttBlock("IDLE", current_time, p.arrival_time))
                current_time = p.arrival_time

            start_t = current_time
            end_t = current_time + p.burst_time

            if last_running is not None and last_running != "IDLE" and last_running != p.label:
                context_switches += 1

            p.first_start_time = start_t
            p.completion_time = end_t
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.response_time = p.first_start_time - p.arrival_time

            gantt.append(GanttBlock(p.label, start_t, end_t))
            last_running = p.label
            current_time = end_t

        return SchedulingResult("FCFS", procs, gantt, context_switches)

    @staticmethod
    def run_sjf(processes_input: List[ScheduledProcess]) -> SchedulingResult:
        """Shortest Job First (SJF, Non-Preemptive) Scheduling."""
        procs = [deepcopy(p) for p in processes_input]
        n = len(procs)
        completed = 0
        current_time = 0
        gantt: List[GanttBlock] = []
        context_switches = 0
        last_running: Optional[str] = None
        is_completed = [False] * n

        while completed < n:
            # Find eligible processes that have arrived and not yet completed
            eligible = [
                (i, p) for i, p in enumerate(procs)
                if not is_completed[i] and p.arrival_time <= current_time
            ]

            if not eligible:
                # CPU is idle until next process arrives
                next_arr = min(p.arrival_time for i, p in enumerate(procs) if not is_completed[i])
                gantt.append(GanttBlock("IDLE", current_time, next_arr))
                current_time = next_arr
                last_running = "IDLE"
                continue

            # Pick shortest burst time; tie-breaker: arrival_time then pid
            eligible.sort(key=lambda item: (item[1].burst_time, item[1].arrival_time, item[1].pid))
            idx, p = eligible[0]

            start_t = current_time
            end_t = current_time + p.burst_time

            if last_running is not None and last_running != "IDLE" and last_running != p.label:
                context_switches += 1

            p.first_start_time = start_t
            p.completion_time = end_t
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.response_time = p.first_start_time - p.arrival_time

            gantt.append(GanttBlock(p.label, start_t, end_t))
            last_running = p.label
            current_time = end_t
            is_completed[idx] = True
            completed += 1

        return SchedulingResult("SJF", procs, gantt, context_switches)

    @staticmethod
    def run_priority(processes_input: List[ScheduledProcess]) -> SchedulingResult:
        """Priority Scheduling (Non-Preemptive, Lower Number = Higher Priority)."""
        procs = [deepcopy(p) for p in processes_input]
        n = len(procs)
        completed = 0
        current_time = 0
        gantt: List[GanttBlock] = []
        context_switches = 0
        last_running: Optional[str] = None
        is_completed = [False] * n

        while completed < n:
            eligible = [
                (i, p) for i, p in enumerate(procs)
                if not is_completed[i] and p.arrival_time <= current_time
            ]

            if not eligible:
                next_arr = min(p.arrival_time for i, p in enumerate(procs) if not is_completed[i])
                gantt.append(GanttBlock("IDLE", current_time, next_arr))
                current_time = next_arr
                last_running = "IDLE"
                continue

            # Lowest integer = highest priority
            eligible.sort(key=lambda item: (item[1].priority, item[1].arrival_time, item[1].pid))
            idx, p = eligible[0]

            start_t = current_time
            end_t = current_time + p.burst_time

            if last_running is not None and last_running != "IDLE" and last_running != p.label:
                context_switches += 1

            p.first_start_time = start_t
            p.completion_time = end_t
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.response_time = p.first_start_time - p.arrival_time

            gantt.append(GanttBlock(p.label, start_t, end_t))
            last_running = p.label
            current_time = end_t
            is_completed[idx] = True
            completed += 1

        return SchedulingResult("Priority (Non-Preemptive)", procs, gantt, context_switches)

    @staticmethod
    def run_round_robin(processes_input: List[ScheduledProcess], time_quantum: int = 2) -> SchedulingResult:
        """Round Robin (RR) Preemptive Scheduling with Time Quantum."""
        if time_quantum <= 0:
            time_quantum = 1

        procs = [deepcopy(p) for p in processes_input]
        procs.sort(key=lambda p: (p.arrival_time, p.pid))
        n = len(procs)

        remaining_burst = {p.pid: p.burst_time for p in procs}
        proc_map = {p.pid: p for p in procs}

        current_time = 0
        ready_queue: List[int] = []  # PIDs in queue
        arrived_pids = set()
        gantt: List[GanttBlock] = []
        context_switches = 0
        last_running_pid: Optional[int] = None
        completed_count = 0

        # Admit processes arrived at time 0
        for p in procs:
            if p.arrival_time <= current_time:
                ready_queue.append(p.pid)
                arrived_pids.add(p.pid)

        while completed_count < n:
            if not ready_queue:
                # Find earliest future arrival
                un_arrived = [p for p in procs if p.pid not in arrived_pids]
                if un_arrived:
                    next_time = min(p.arrival_time for p in un_arrived)
                    gantt.append(GanttBlock("IDLE", current_time, next_time))
                    current_time = next_time
                    for p in procs:
                        if p.arrival_time <= current_time and p.pid not in arrived_pids:
                            ready_queue.append(p.pid)
                            arrived_pids.add(p.pid)
                    last_running_pid = None
                    continue
                else:
                    break

            pid = ready_queue.pop(0)
            p = proc_map[pid]

            if last_running_pid is not None and last_running_pid != pid:
                context_switches += 1

            if p.first_start_time is None:
                p.first_start_time = current_time

            exec_time = min(remaining_burst[pid], time_quantum)
            start_t = current_time
            end_t = current_time + exec_time

            gantt.append(GanttBlock(p.label, start_t, end_t))
            current_time = end_t
            remaining_burst[pid] -= exec_time
            last_running_pid = pid

            # Check for new arrivals during this execution interval
            for other in procs:
                if other.arrival_time <= current_time and other.pid not in arrived_pids:
                    ready_queue.append(other.pid)
                    arrived_pids.add(other.pid)

            if remaining_burst[pid] > 0:
                # Not finished, re-queue at end of ready queue
                ready_queue.append(pid)
            else:
                p.completion_time = current_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.burst_time
                p.response_time = p.first_start_time - p.arrival_time
                completed_count += 1

        # Consolidate adjacent gantt blocks for the same label if consecutive
        consolidated_gantt: List[GanttBlock] = []
        for block in gantt:
            if consolidated_gantt and consolidated_gantt[-1].label == block.label and consolidated_gantt[-1].end == block.start:
                consolidated_gantt[-1].end = block.end
            else:
                consolidated_gantt.append(block)

        return SchedulingResult(f"Round Robin (Q={time_quantum})", procs, consolidated_gantt, context_switches, time_quantum)

    @classmethod
    def compare_all(cls, processes_input: List[ScheduledProcess], quantum: int = 2) -> Dict[str, Any]:
        """Runs FCFS, SJF, Round Robin, and Priority on the exact same dataset for comparative analysis."""
        fcfs = cls.run_fcfs(processes_input)
        sjf = cls.run_sjf(processes_input)
        rr = cls.run_round_robin(processes_input, time_quantum=quantum)
        priority = cls.run_priority(processes_input)
        return {
            "FCFS": {
                "algorithm": "FCFS",
                "avg_waiting_time": round(fcfs.avg_waiting_time, 2),
                "avg_turnaround_time": round(fcfs.avg_turnaround_time, 2),
                "avg_response_time": round(fcfs.avg_response_time, 2),
                "context_switches": fcfs.context_switches,
            },
            "SJF": {
                "algorithm": "SJF (Non-Preemptive)",
                "avg_waiting_time": round(sjf.avg_waiting_time, 2),
                "avg_turnaround_time": round(sjf.avg_turnaround_time, 2),
                "avg_response_time": round(sjf.avg_response_time, 2),
                "context_switches": sjf.context_switches,
            },
            "RR": {
                "algorithm": f"Round Robin (Q={quantum})",
                "avg_waiting_time": round(rr.avg_waiting_time, 2),
                "avg_turnaround_time": round(rr.avg_turnaround_time, 2),
                "avg_response_time": round(rr.avg_response_time, 2),
                "context_switches": rr.context_switches,
            },
            "PRIORITY": {
                "algorithm": "Priority (Non-Preemptive)",
                "avg_waiting_time": round(priority.avg_waiting_time, 2),
                "avg_turnaround_time": round(priority.avg_turnaround_time, 2),
                "avg_response_time": round(priority.avg_response_time, 2),
                "context_switches": priority.context_switches,
            },
        }

