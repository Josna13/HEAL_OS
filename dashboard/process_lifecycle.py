"""
HealOS 2.0 - OS Process Lifecycle & Execution Simulator (Section A)
Deterministic, pedagogical state machine and execution engine modeling the complete
lifecycle of operating system processes:
PROCESS CREATION -> PID ASSIGNMENT -> NEW -> READY -> RUNNING -> WAITING (I/O) -> TERMINATED.

Enforces valid kernel state transitions, tracks Process Control Blocks (PCBs) with
simulated CPU registers, schedules processes via FCFS, SJF, Round Robin, and Priority,
models I/O blocking and unblocking, generates real-time Gantt timelines, and logs events.
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import copy


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"


class TransitionReason(Enum):
    ADMIT = "Admitted to Ready Queue"
    DISPATCH = "Dispatched by CPU Scheduler"
    PREEMPT = "Time Slice Expired / Preempted"
    BLOCK_IO = "Blocked Waiting for I/O / Event"
    IO_COMPLETE = "I/O Completed / Event Signaled"
    EXIT_NORMAL = "Execution Completed Normally"
    CRASH = "Fatal Error / Memory Fault / Crash Trigger"


VALID_TRANSITIONS: Dict[ProcessState, Dict[ProcessState, List[TransitionReason]]] = {
    ProcessState.NEW: {
        ProcessState.READY: [TransitionReason.ADMIT],
    },
    ProcessState.READY: {
        ProcessState.RUNNING: [TransitionReason.DISPATCH],
    },
    ProcessState.RUNNING: {
        ProcessState.READY: [TransitionReason.PREEMPT],
        ProcessState.WAITING: [TransitionReason.BLOCK_IO],
        ProcessState.TERMINATED: [TransitionReason.EXIT_NORMAL, TransitionReason.CRASH],
    },
    ProcessState.WAITING: {
        ProcessState.READY: [TransitionReason.IO_COMPLETE],
    },
    ProcessState.TERMINATED: {},
}


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal process state transition is attempted."""
    pass


class TransitionRecord:
    """Historical ledger entry for a process state transition."""

    def __init__(
        self,
        from_state: ProcessState,
        to_state: ProcessState,
        reason: TransitionReason,
        timestamp: Optional[str] = None,
        note: str = "",
        tick: int = 0,
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.note = note
        self.tick = tick

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "reason": self.reason.value,
            "timestamp": self.timestamp,
            "note": self.note,
            "tick": self.tick,
        }


class LifecycleProcess:
    """
    Operating System Process Control Block (PCB) representation.
    Maintains all identity, timing, priority, burst, I/O profile, register states,
    and transition history.
    """

    def __init__(
        self,
        pid: int,
        name: str,
        arrival_time: int = 0,
        cpu_burst_total: int = 5,
        priority: int = 1,
        io_request_time: Optional[int] = None,
        io_duration: int = 0,
        memory_mb: float = 24.5,
        color: Optional[str] = None,
    ):
        self.pid: int = pid
        self.name: str = name
        self.arrival_time: int = max(0, arrival_time)
        self.cpu_burst_total: int = max(1, cpu_burst_total)
        self.cpu_burst_remaining: int = self.cpu_burst_total
        self.cpu_time_used: int = 0
        self.priority: int = max(1, priority)  # 1 = highest priority

        # I/O specification
        self.io_request_time: Optional[int] = io_request_time if (io_request_time is not None and io_request_time > 0) else None
        self.io_duration: int = max(0, io_duration)
        self.io_remaining: int = 0
        self.io_performed: bool = False
        self.memory_mb: float = memory_mb

        # Color palette for distinct visualization
        palette = ["#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b"]
        self.color: str = color or palette[(pid % len(palette))]

        # Execution and Lifecycle State
        self.state: ProcessState = ProcessState.NEW
        self.first_start_time: Optional[int] = None
        self.completion_time: Optional[int] = None
        self.waiting_time: int = 0  # Cumulative ticks in READY queue
        self.cpu_allocations_count: int = 0
        self.preemptions_count: int = 0

        self.history: List[TransitionRecord] = []
        self.created_at: str = datetime.now().strftime("%H:%M:%S")
        self.created_at_tick: int = 0
        self.terminated_at: Optional[str] = None

        # Simulated hardware architecture registers
        self.simulated_registers: Dict[str, str] = {
            "PC": hex(0x7FFD00 + pid * 0x10),
            "SP": hex(0x7FFF00 - pid * 0x20),
            "R0": hex(pid),
            "R1": "0x00A4",
            "PSW": "0x0200",
        }

    def transition_to(
        self,
        target_state: ProcessState,
        reason: TransitionReason,
        note: str = "",
        tick: int = 0,
    ) -> TransitionRecord:
        """
        Executes a validated state transition.
        Raises InvalidStateTransitionError if the transition violates OS design.
        """
        allowed_targets = VALID_TRANSITIONS.get(self.state, {})
        if target_state not in allowed_targets:
            raise InvalidStateTransitionError(
                f"Illegal transition for PID {self.pid} ({self.name}): "
                f"Cannot move directly from '{self.state.value}' to '{target_state.value}'. "
                f"Allowed destinations: {[s.value for s in allowed_targets.keys()] or 'None (Terminal state)'}."
            )

        allowed_reasons = allowed_targets[target_state]
        if reason not in allowed_reasons:
            raise InvalidStateTransitionError(
                f"Invalid reason '{reason.value}' for transition {self.state.value} -> {target_state.value}. "
                f"Allowed reasons: {[r.value for r in allowed_reasons]}."
            )

        record = TransitionRecord(
            from_state=self.state,
            to_state=target_state,
            reason=reason,
            note=note,
            tick=tick,
        )
        self.history.append(record)
        self.state = target_state

        if target_state == ProcessState.TERMINATED:
            self.terminated_at = record.timestamp

        return record

    @property
    def turnaround_time(self) -> Optional[int]:
        if self.completion_time is not None:
            return self.completion_time - self.arrival_time
        return None

    @property
    def response_time(self) -> Optional[int]:
        if self.first_start_time is not None:
            return self.first_start_time - self.arrival_time
        return None

    def clone(self) -> 'LifecycleProcess':
        """Creates an independent clone of this process with initial state."""
        cloned = LifecycleProcess(
            pid=self.pid,
            name=self.name,
            arrival_time=self.arrival_time,
            cpu_burst_total=self.cpu_burst_total,
            priority=self.priority,
            io_request_time=self.io_request_time,
            io_duration=self.io_duration,
            memory_mb=self.memory_mb,
            color=self.color,
        )
        return cloned

    def get_pcb_details(self) -> Dict[str, Any]:
        """Provides full Process Control Block inspector data with plain English explanations."""
        last_rec = self.history[-1] if self.history else None
        tat = self.turnaround_time
        rt = self.response_time

        field_explanations = {
            "pid": "Unique Process Identifier assigned within the simulated OS kernel namespace (e.g. P101).",
            "name": "Human-readable label of the workload executable binary or service.",
            "state": "Present stage in the 5-state process lifecycle (NEW, READY, RUNNING, WAITING, or TERMINATED).",
            "arrival_time": "The simulation clock tick at which the process arrives and is admitted from NEW to READY.",
            "first_start_time": "Simulation clock tick when the CPU scheduler first dispatches this process to execute.",
            "cpu_burst_total": "Total cumulative CPU execution time (in ticks) required for this process to complete.",
            "cpu_burst_remaining": "Remaining CPU execution ticks required before process finishes.",
            "completion_time": "Clock tick at which the process finishes execution and transitions to TERMINATED.",
            "turnaround_time": "Turnaround Time (TAT = CT - AT): Total elapsed duration from arrival to completion.",
            "waiting_time": "Waiting Time (WT): Total cumulative time spent in READY queue (excludes I/O time in WAITING).",
            "response_time": "Response Time (RT = ST - AT): Elapsed duration from arrival until first CPU allocation.",
            "priority": "Scheduling priority level (lower integer value represents higher scheduling urgency).",
            "cpu_allocations_count": "Number of times the short-term scheduler selected and dispatched this process to the CPU core.",
            "preemptions_count": "Number of times this process was involuntarily interrupted from RUNNING back to READY (e.g. quantum expired).",
            "io_profile": "Configured I/O event trigger time (tick) and duration in WAITING state.",
            "simulated_registers": "Simulated CPU hardware registers (Program Counter, Stack Pointer, General Registers, PSW).",
            "history": "Chronological audit trail of all lifecycle state transitions recorded in this process's PCB.",
        }

        return {
            "pid": self.pid,
            "name": self.name,
            "state": self.state.value,
            "arrival_time": self.arrival_time,
            "first_start_time": self.first_start_time if self.first_start_time is not None else "-",
            "cpu_burst_total": self.cpu_burst_total,
            "cpu_burst_remaining": self.cpu_burst_remaining,
            "cpu_time_used": self.cpu_time_used,
            "completion_time": self.completion_time if self.completion_time is not None else "-",
            "turnaround_time": tat if tat is not None else "-",
            "waiting_time": self.waiting_time,
            "response_time": rt if rt is not None else "-",
            "priority": self.priority,
            "cpu_allocations_count": self.cpu_allocations_count,
            "preemptions_count": self.preemptions_count,
            "io_request_time": self.io_request_time if self.io_request_time is not None else "None",
            "io_duration": self.io_duration,
            "io_remaining": self.io_remaining,
            "memory_mb": round(self.memory_mb, 1),
            "color": self.color,
            "created_at": self.created_at,
            "terminated_at": self.terminated_at or "N/A (Active)",
            "last_transition": f"{last_rec.from_state.value} -> {last_rec.to_state.value} ({last_rec.reason.value})" if last_rec else "PCB Allocated (NEW)",
            "simulated_registers": self.simulated_registers,
            "history": [h.to_dict() for h in self.history],
            "field_explanations": field_explanations,
            "data_provenance": "[SIMULATION]",
            "kernel_disclaimer": "Simulated process in user-space namespace; real Linux kernel processes manage task context in kernel struct task_struct.",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "state": self.state.value,
            "arrival_time": self.arrival_time,
            "priority": self.priority,
            "cpu_burst_total": self.cpu_burst_total,
            "cpu_burst_remaining": self.cpu_burst_remaining,
            "cpu_time_used": self.cpu_time_used,
            "waiting_time": self.waiting_time,
            "first_start_time": self.first_start_time,
            "completion_time": self.completion_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
            "cpu_allocations_count": self.cpu_allocations_count,
            "preemptions_count": self.preemptions_count,
            "io_request_time": self.io_request_time,
            "io_duration": self.io_duration,
            "io_remaining": self.io_remaining,
            "memory_mb": self.memory_mb,
            "color": self.color,
            "created_at": self.created_at,
            "terminated_at": self.terminated_at,
            "history_count": len(self.history),
            "simulated_registers": self.simulated_registers,
        }


class LifecycleEngine:
    """
    Deterministic, interactive Process Execution Teaching Simulator.
    Simulates:
    - Creation and simulated PID allocation
    - Admission to READY queue at arrival time
    - Short-term CPU scheduler dispatching (FCFS, SJF, RR, Priority)
    - Instruction execution progress & remaining burst countdown
    - Preemption on quantum expiry or higher priority arrival
    - I/O blocking (RUNNING -> WAITING) and interrupt completion (WAITING -> READY)
    - Process termination and PCB cleanup
    - Real-time Gantt timeline tracking, metrics calculation, and event logging
    """

    def __init__(self):
        self.processes: Dict[int, LifecycleProcess] = {}
        self.initial_specs: List[Dict[str, Any]] = []
        self.algorithm: str = "RR"  # "RR", "FCFS", "SJF", "PRIORITY"
        self.time_quantum: int = 2
        self.priority_preemptive: bool = False

        self.clock_tick: int = 0
        self.current_slice: int = 0
        self.active_pid: Optional[int] = None
        self.active_transition: Optional[Dict[str, Any]] = None
        self.is_playing: bool = False
        self.is_finished: bool = False
        self.speed: float = 1.0
        self.selected_pid: Optional[int] = 101
        self.pid_counter: int = 100

        self.gantt_chart: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

        self._initialize_default_preset("full_lifecycle_io")

    @staticmethod
    def get_presets() -> Dict[str, Dict[str, Any]]:
        """Classroom demonstration reference scenarios."""
        return {
            "full_lifecycle_io": {
                "name": "Full Lifecycle with I/O (Recommended Demo)",
                "description": "4 processes demonstrating creation, arrival, scheduling, execution, I/O blocking, unblocking, and termination.",
                "algorithm": "RR",
                "quantum": 2,
                "priority_preemptive": False,
                "processes": [
                    {"name": "web_server", "arrival_time": 0, "burst_time": 5, "priority": 2, "io_request_time": 2, "io_duration": 3},
                    {"name": "db_worker", "arrival_time": 1, "burst_time": 4, "priority": 1, "io_request_time": None, "io_duration": 0},
                    {"name": "calc_job", "arrival_time": 3, "burst_time": 3, "priority": 3, "io_request_time": None, "io_duration": 0},
                    {"name": "log_daemon", "arrival_time": 5, "burst_time": 2, "priority": 2, "io_request_time": None, "io_duration": 0},
                ],
            },
            "rr_preemption": {
                "name": "Round Robin Time-Slicing & Preemption",
                "description": "Multiple processes arriving at T=0 showing involuntary preemption and context switches.",
                "algorithm": "RR",
                "quantum": 2,
                "priority_preemptive": False,
                "processes": [
                    {"name": "batch_job_A", "arrival_time": 0, "burst_time": 6, "priority": 2, "io_request_time": None, "io_duration": 0},
                    {"name": "batch_job_B", "arrival_time": 0, "burst_time": 5, "priority": 1, "io_request_time": None, "io_duration": 0},
                    {"name": "batch_job_C", "arrival_time": 1, "burst_time": 4, "priority": 3, "io_request_time": None, "io_duration": 0},
                ],
            },
            "sjf_arrival": {
                "name": "Shortest Job First (SJF) Arrival Ordering",
                "description": "Non-preemptive SJF selecting arrived shortest jobs to minimize average waiting time.",
                "algorithm": "SJF",
                "quantum": 2,
                "priority_preemptive": False,
                "processes": [
                    {"name": "heavy_compute", "arrival_time": 0, "burst_time": 7, "priority": 2, "io_request_time": None, "io_duration": 0},
                    {"name": "quick_query", "arrival_time": 1, "burst_time": 2, "priority": 1, "io_request_time": None, "io_duration": 0},
                    {"name": "medium_task", "arrival_time": 2, "burst_time": 4, "priority": 3, "io_request_time": None, "io_duration": 0},
                ],
            },
            "priority_mix": {
                "name": "Priority Scheduling (High vs Low Urgency)",
                "description": "Processes dispatched according to priority urgency (Priority 1 = highest).",
                "algorithm": "PRIORITY",
                "quantum": 2,
                "priority_preemptive": True,
                "processes": [
                    {"name": "background_sync", "arrival_time": 0, "burst_time": 5, "priority": 3, "io_request_time": None, "io_duration": 0},
                    {"name": "realtime_audio", "arrival_time": 1, "burst_time": 3, "priority": 1, "io_request_time": None, "io_duration": 0},
                    {"name": "gui_renderer", "arrival_time": 2, "burst_time": 4, "priority": 2, "io_request_time": None, "io_duration": 0},
                ],
            },
        }

    def _initialize_default_preset(self, preset_key: str = "full_lifecycle_io") -> None:
        """Initializes simulation with a chosen preset scenario."""
        presets = self.get_presets()
        preset = presets.get(preset_key, presets["full_lifecycle_io"])

        self.processes.clear()
        self.initial_specs.clear()
        self.event_log.clear()
        self.gantt_chart.clear()
        self.clock_tick = 0
        self.current_slice = 0
        self.active_pid = None
        self.active_transition = None
        self.is_playing = False
        self.is_finished = False
        self.pid_counter = 100

        self.algorithm = preset.get("algorithm", "RR")
        self.time_quantum = preset.get("quantum", 2)
        self.priority_preemptive = preset.get("priority_preemptive", False)

        for p_def in preset["processes"]:
            self.add_process(
                name=p_def["name"],
                burst=p_def["burst_time"],
                arrival=p_def.get("arrival_time", 0),
                priority=p_def.get("priority", 1),
                io_request=p_def.get("io_request_time"),
                io_duration=p_def.get("io_duration", 0),
            )

        # Initial admissions at T=0
        for p in self.processes.values():
            if p.arrival_time == 0:
                self.admit_process(p.pid)

        pids = list(self.processes.keys())
        self.selected_pid = pids[0] if pids else None
        self._log_event("[T=0] Simulation environment initialized. Ready for execution.", None, "INIT", None, None)

    def allocate_pid(self) -> int:
        """Generates the next unique simulated PID."""
        self.pid_counter += 1
        return self.pid_counter

    def add_process(
        self,
        name: str,
        burst: int = 5,
        arrival: int = 0,
        priority: int = 1,
        io_request: Optional[int] = None,
        io_duration: int = 0,
        pid: Optional[int] = None,
        **kwargs: Any,
    ) -> LifecycleProcess:
        """Creates a process and allocates a simulated PID."""
        actual_burst = kwargs.get("cpu_burst", kwargs.get("burst_time", burst))
        actual_arrival = kwargs.get("arrival_time", arrival)
        actual_io_req = kwargs.get("io_request_time", io_request)
        actual_io_dur = kwargs.get("io_duration", io_duration)
        assigned_pid = pid if pid is not None else self.allocate_pid()
        proc = LifecycleProcess(
            pid=assigned_pid,
            name=name,
            arrival_time=actual_arrival,
            cpu_burst_total=actual_burst,
            priority=priority,
            io_request_time=actual_io_req,
            io_duration=actual_io_dur,
        )
        self.processes[assigned_pid] = proc
        self.initial_specs.append({
            "pid": assigned_pid,
            "name": name,
            "burst_time": actual_burst,
            "arrival_time": actual_arrival,
            "priority": priority,
            "io_request_time": actual_io_req,
            "io_duration": actual_io_dur,
        })
        self._log_event(
            f"[T={self.clock_tick}] PCB created for P{assigned_pid} ({name}) [AT={actual_arrival}, BT={actual_burst}, Prio={priority}]. State: NEW.",
            assigned_pid,
            "CREATE",
            None,
            "NEW",
        )
        return proc

    def remove_process(self, pid: int) -> bool:
        """Removes a process from the simulation."""
        if pid in self.processes and len(self.processes) > 1:
            del self.processes[pid]
            self.initial_specs = [s for s in self.initial_specs if s.get("pid") != pid]
            if self.active_pid == pid:
                self.active_pid = None
                self.current_slice = 0
            if self.selected_pid == pid:
                pids = list(self.processes.keys())
                self.selected_pid = pids[0] if pids else None
            self._log_event(f"[T={self.clock_tick}] Process P{pid} removed from simulation.", pid, "REMOVE", None, None)
            return True
        return False

    def admit_process(self, pid: int) -> bool:
        """Transitions process from NEW to READY upon arrival."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.NEW:
            proc.transition_to(ProcessState.READY, TransitionReason.ADMIT, f"Admitted at T={self.clock_tick}", tick=self.clock_tick)
            self._log_event(
                f"[T={self.clock_tick}] P{pid} ({proc.name}) arrived -> Admitted to READY queue.",
                pid,
                "ADMIT",
                "NEW",
                "READY",
            )
            return True
        return False

    def dispatch_process(self, pid: int) -> bool:
        """Scheduler picks process from READY to RUNNING."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.READY:
            if proc.first_start_time is None:
                proc.first_start_time = self.clock_tick
            proc.cpu_allocations_count += 1
            proc.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH, f"Dispatched by {self.algorithm}", tick=self.clock_tick)
            self.active_pid = pid
            self.current_slice = 0
            self._log_event(
                f"[T={self.clock_tick}] Scheduler dispatched P{pid} ({proc.name}) -> CPU ALLOCATED [{self.algorithm}].",
                pid,
                "DISPATCH",
                "READY",
                "RUNNING",
            )
            return True
        return False

    def preempt_process(self, pid: int, reason_text: str = "Time slice expired") -> bool:
        """Moves process from RUNNING back to READY."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.RUNNING:
            proc.preemptions_count += 1
            proc.transition_to(ProcessState.READY, TransitionReason.PREEMPT, reason_text, tick=self.clock_tick)
            if self.active_pid == pid:
                self.active_pid = None
                self.current_slice = 0
            self._log_event(
                f"[T={self.clock_tick}] P{pid} ({proc.name}) {reason_text} -> RUNNING ➔ READY.",
                pid,
                "PREEMPT",
                "RUNNING",
                "READY",
            )
            return True
        return False

    def block_process(self, pid: int) -> bool:
        """Moves process from RUNNING to WAITING on I/O."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.RUNNING:
            proc.io_performed = True
            proc.io_remaining = proc.io_duration
            proc.transition_to(ProcessState.WAITING, TransitionReason.BLOCK_IO, f"Blocked on I/O for {proc.io_duration}t", tick=self.clock_tick)
            if self.active_pid == pid:
                self.active_pid = None
                self.current_slice = 0
            self._log_event(
                f"[T={self.clock_tick}] P{pid} ({proc.name}) issued I/O request -> RUNNING ➔ WAITING ({proc.io_duration}t).",
                pid,
                "BLOCK_IO",
                "RUNNING",
                "WAITING",
            )
            return True
        return False

    def unblock_process(self, pid: int) -> bool:
        """Moves process from WAITING to READY when I/O completes."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.WAITING:
            proc.transition_to(ProcessState.READY, TransitionReason.IO_COMPLETE, "I/O completed", tick=self.clock_tick)
            self._log_event(
                f"[T={self.clock_tick}] P{pid} ({proc.name}) I/O completed -> WAITING ➔ READY.",
                pid,
                "IO_COMPLETE",
                "WAITING",
                "READY",
            )
            return True
        return False

    def terminate_process(self, pid: int, is_crash: bool = False) -> bool:
        """Moves process from RUNNING to TERMINATED."""
        proc = self.processes.get(pid)
        if proc and proc.state == ProcessState.RUNNING:
            proc.completion_time = self.clock_tick
            reason = TransitionReason.CRASH if is_crash else TransitionReason.EXIT_NORMAL
            note = "Segmentation fault / Trigger crash" if is_crash else "Normal execution complete"
            proc.transition_to(ProcessState.TERMINATED, reason, note, tick=self.clock_tick)
            if self.active_pid == pid:
                self.active_pid = None
                self.current_slice = 0
            self._log_event(
                f"[T={self.clock_tick}] P{pid} ({proc.name}) execution completed -> TERMINATED.",
                pid,
                "TERMINATE",
                "RUNNING",
                "TERMINATED",
            )
            return True
        return False

    def _select_next_process(self, ready_procs: List[LifecycleProcess]) -> LifecycleProcess:
        """Selects the next process from READY according to the active algorithm."""
        if self.algorithm == "SJF":
            return min(ready_procs, key=lambda p: (p.cpu_burst_remaining, p.arrival_time, p.pid))
        elif self.algorithm == "PRIORITY":
            return min(ready_procs, key=lambda p: (p.priority, p.arrival_time, p.pid))
        elif self.algorithm == "FCFS":
            return min(ready_procs, key=lambda p: (p.arrival_time, p.pid))
        else:
            # Round Robin: largest waiting time in READY (longest since arrival/last queue entry)
            return max(ready_procs, key=lambda p: (p.waiting_time, -p.arrival_time, -p.pid))

    def _record_gantt_slice(self, pid: Optional[int], label: str, start: int, end: int, slice_type: str) -> None:
        """Records a continuous CPU or IDLE block in the Gantt timeline."""
        if self.gantt_chart and self.gantt_chart[-1]["pid"] == pid and self.gantt_chart[-1]["end"] == start:
            self.gantt_chart[-1]["end"] = end
        else:
            is_switch = False
            if (
                self.gantt_chart
                and self.gantt_chart[-1]["pid"] != pid
                and pid is not None
                and self.gantt_chart[-1]["pid"] is not None
            ):
                is_switch = True
            self.gantt_chart.append({
                "pid": pid,
                "label": label,
                "start": start,
                "end": end,
                "type": slice_type,
                "is_context_switch": is_switch,
            })

    def step_tick(self) -> Dict[str, Any]:
        """
        Advances the simulation by 1 logical clock tick.
        Coordinates arrivals, I/O timers, CPU burst decrements, preemption, and dispatches.
        """
        if self.is_finished:
            return {
                "action": "COMPLETE",
                "message": f"Tick {self.clock_tick}: All processes have completed execution.",
                "tick": self.clock_tick,
                "is_finished": True,
            }

        t = self.clock_tick
        self.active_transition = None
        transition_events = []

        # 1. Check Arrivals at tick t: NEW -> READY
        for p in list(self.processes.values()):
            if p.state == ProcessState.NEW and p.arrival_time <= t:
                self.admit_process(p.pid)
                self.active_transition = {
                    "pid": p.pid,
                    "name": p.name,
                    "from": "NEW",
                    "to": "READY",
                    "reason": f"Arrival time {p.arrival_time} reached -> Admitted to READY queue",
                    "arrow": "trans-new-ready",
                }
                transition_events.append(self.active_transition)

        # 2. Check I/O Waiting processes: decrement and unblock
        for p in list(self.processes.values()):
            if p.state == ProcessState.WAITING:
                p.io_remaining -= 1
                if p.io_remaining <= 0:
                    self.unblock_process(p.pid)
                    self.active_transition = {
                        "pid": p.pid,
                        "name": p.name,
                        "from": "WAITING",
                        "to": "READY",
                        "reason": f"I/O duration completed -> Returned to READY queue",
                        "arrow": "trans-waiting-ready",
                    }
                    transition_events.append(self.active_transition)

        # 3. Check currently RUNNING process
        running_proc = self.processes.get(self.active_pid) if self.active_pid is not None else None
        if running_proc and running_proc.state != ProcessState.RUNNING:
            running_proc = None
            self.active_pid = None

        if running_proc:
            running_proc.cpu_time_used += 1
            running_proc.cpu_burst_remaining -= 1
            self.current_slice += 1

            self._record_gantt_slice(running_proc.pid, running_proc.name, t, t + 1, "CPU")

            # A. Process completed burst?
            if running_proc.cpu_burst_remaining <= 0:
                self.terminate_process(running_proc.pid)
                self.active_transition = {
                    "pid": running_proc.pid,
                    "name": running_proc.name,
                    "from": "RUNNING",
                    "to": "TERMINATED",
                    "reason": f"CPU burst complete -> TERMINATED",
                    "arrow": "trans-running-term",
                }
                transition_events.append(self.active_transition)

            # B. Process requested I/O?
            elif (
                running_proc.io_request_time is not None
                and running_proc.cpu_time_used >= running_proc.io_request_time
                and not running_proc.io_performed
            ):
                self.block_process(running_proc.pid)
                self.active_transition = {
                    "pid": running_proc.pid,
                    "name": running_proc.name,
                    "from": "RUNNING",
                    "to": "WAITING",
                    "reason": f"Issued I/O request (Duration: {running_proc.io_duration}t) -> WAITING",
                    "arrow": "trans-running-waiting",
                }
                transition_events.append(self.active_transition)

            # C. Preemption check (RR quantum expiry or Preemptive Priority)
            else:
                should_preempt = False
                preempt_reason = ""
                ready_count = sum(1 for p in self.processes.values() if p.state == ProcessState.READY)

                if self.algorithm == "RR" and self.current_slice >= self.time_quantum and ready_count > 0:
                    should_preempt = True
                    preempt_reason = f"Time quantum ({self.time_quantum}t) expired"
                elif self.algorithm == "PRIORITY" and self.priority_preemptive and ready_count > 0:
                    min_prio = min(p.priority for p in self.processes.values() if p.state == ProcessState.READY)
                    if min_prio < running_proc.priority:
                        should_preempt = True
                        preempt_reason = "Higher-priority job ready in queue"

                if should_preempt:
                    self.preempt_process(running_proc.pid, preempt_reason)
                    self.active_transition = {
                        "pid": running_proc.pid,
                        "name": running_proc.name,
                        "from": "RUNNING",
                        "to": "READY",
                        "reason": f"{preempt_reason} -> Returned to READY queue",
                        "arrow": "trans-running-ready",
                    }
                    transition_events.append(self.active_transition)

        # 4. If CPU is idle, dispatch next ready process
        if self.active_pid is None:
            ready_procs = [p for p in self.processes.values() if p.state == ProcessState.READY]
            if ready_procs:
                selected = self._select_next_process(ready_procs)
                self.dispatch_process(selected.pid)
                self.active_transition = {
                    "pid": selected.pid,
                    "name": selected.name,
                    "from": "READY",
                    "to": "RUNNING",
                    "reason": f"Dispatched by {self.algorithm} scheduler -> CPU ALLOCATED",
                    "arrow": "trans-ready-running",
                }
                transition_events.append(self.active_transition)
            else:
                all_done = all(p.state == ProcessState.TERMINATED for p in self.processes.values())
                if all_done:
                    self.is_finished = True
                    self._log_event(f"[T={t+1}] All {len(self.processes)} processes have finished execution.", None, "ALL_COMPLETE", None, None)
                else:
                    self._record_gantt_slice(None, "IDLE", t, t + 1, "IDLE")

        # 5. Accumulate waiting time for processes in READY queue
        for p in self.processes.values():
            if p.state == ProcessState.READY and p.pid != self.active_pid:
                p.waiting_time += 1

        self.clock_tick += 1
        return {
            "tick": self.clock_tick,
            "active_transition": self.active_transition,
            "events": transition_events,
            "is_finished": self.is_finished,
        }

    def step_event(self) -> Dict[str, Any]:
        """Advances simulation to the next meaningful event boundary."""
        if self.is_finished:
            return self.get_summary()

        for _ in range(50):
            res = self.step_tick()
            if res.get("events") or res.get("is_finished"):
                break
        return self.get_summary()

    def step(self) -> str:
        """
        Maintains API compatibility with previous step() method.
        Advances simulation by 1 logical tick and returns human-readable summary.
        """
        res = self.step_tick()
        if self.active_transition:
            trans = self.active_transition
            return f"Tick {self.clock_tick}: P{trans['pid']} {trans['from']} -> {trans['to']} ({trans['reason']})"
        elif self.active_pid:
            p = self.processes[self.active_pid]
            return f"Tick {self.clock_tick}: P{p.pid} ({p.name}) executing on CPU ({p.cpu_burst_remaining}t left)."
        elif self.is_finished:
            return f"Tick {self.clock_tick}: All processes have completed execution."
        else:
            return f"Tick {self.clock_tick}: CPU IDLE - Awaiting next process arrival."

    def reset(self) -> None:
        """Restores the initial process specifications and resets simulation state."""
        saved_specs = copy.deepcopy(self.initial_specs)
        saved_algo = self.algorithm
        saved_q = self.time_quantum
        saved_prio_preempt = self.priority_preemptive

        self.processes.clear()
        self.event_log.clear()
        self.gantt_chart.clear()
        self.clock_tick = 0
        self.current_slice = 0
        self.active_pid = None
        self.active_transition = None
        self.is_playing = False
        self.is_finished = False

        self.algorithm = saved_algo
        self.time_quantum = saved_q
        self.priority_preemptive = saved_prio_preempt

        if saved_specs:
            for s in saved_specs:
                self.add_process(
                    name=s["name"],
                    burst=s["burst_time"],
                    arrival=s["arrival_time"],
                    priority=s["priority"],
                    io_request=s["io_request_time"],
                    io_duration=s["io_duration"],
                    pid=s["pid"],
                )
            for p in self.processes.values():
                if p.arrival_time == 0:
                    self.admit_process(p.pid)
            pids = list(self.processes.keys())
            self.selected_pid = pids[0] if pids else None
        else:
            self._initialize_default_preset("full_lifecycle_io")

        self._log_event(f"[T=0] Simulation reset to initial state.", None, "RESET", None, None)

    def load_preset(self, preset_key: str) -> None:
        """Loads and activates a reference teaching preset."""
        self._initialize_default_preset(preset_key)

    def set_algorithm(self, algo: str, quantum: int = 2, priority_preemptive: bool = False, **kwargs: Any) -> None:
        """Configures the CPU scheduling policy."""
        actual_q = kwargs.get("time_quantum", quantum)
        if algo in ("RR", "FCFS", "SJF", "PRIORITY"):
            self.algorithm = algo
            self.time_quantum = max(1, min(10, actual_q))
            self.priority_preemptive = bool(priority_preemptive)
            self._log_event(
                f"[T={self.clock_tick}] CPU scheduler algorithm changed to {algo} (Q={self.time_quantum}, Preemptive={self.priority_preemptive}).",
                None,
                "ALGO_CHANGE",
                None,
                None,
            )

    def toggle_play(self) -> bool:
        """Toggles play / pause state."""
        self.is_playing = not self.is_playing
        return self.is_playing

    def set_speed(self, speed: float) -> None:
        """Sets simulation speed (0.5x, 1x, 2x, 4x)."""
        self.speed = max(0.5, min(4.0, speed))

    def _log_event(
        self,
        msg: str,
        pid: Optional[int] = None,
        event_type: str = "INFO",
        from_state: Optional[str] = None,
        to_state: Optional[str] = None,
    ) -> None:
        """Appends a timestamped structured event to the simulation log."""
        self.event_log.append({
            "tick": self.clock_tick,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": msg,
            "pid": pid,
            "event_type": event_type,
            "from_state": from_state,
            "to_state": to_state,
        })
        if len(self.event_log) > 100:
            self.event_log.pop(0)

    def get_pcb(self, pid: int) -> Optional[Dict[str, Any]]:
        """Returns detailed PCB data for process inspector."""
        p = self.processes.get(pid)
        return p.get_pcb_details() if p else None

    def get_ready_queue_pids(self) -> List[int]:
        """Returns ready queue PIDs in exact dispatch order."""
        ready_procs = [p for p in self.processes.values() if p.state == ProcessState.READY]
        if not ready_procs:
            return []
        if self.algorithm == "SJF":
            sorted_procs = sorted(ready_procs, key=lambda p: (p.cpu_burst_remaining, p.arrival_time, p.pid))
        elif self.algorithm == "PRIORITY":
            sorted_procs = sorted(ready_procs, key=lambda p: (p.priority, p.arrival_time, p.pid))
        elif self.algorithm == "FCFS":
            sorted_procs = sorted(ready_procs, key=lambda p: (p.arrival_time, p.pid))
        else:
            sorted_procs = sorted(ready_procs, key=lambda p: (-p.waiting_time, p.arrival_time, p.pid))
        return [p.pid for p in sorted_procs]

    def get_summary(self) -> Dict[str, Any]:
        """Provides full snapshot for UI rendering, inspection, and telemetry serialization."""
        state_counts = {s.value: 0 for s in ProcessState}
        for p in self.processes.values():
            state_counts[p.state.value] += 1

        selected_pcb = self.get_pcb(self.selected_pid) if self.selected_pid else None
        active_proc = self.processes.get(self.active_pid).to_dict() if self.active_pid is not None else None
        ready_pids = self.get_ready_queue_pids()
        ready_procs = [self.processes[pid].to_dict() for pid in ready_pids if pid in self.processes]
        waiting_procs = [p.to_dict() for p in self.processes.values() if p.state == ProcessState.WAITING]

        # Aggregate metrics
        finished = [p for p in self.processes.values() if p.state == ProcessState.TERMINATED]
        n_fin = len(finished)
        avg_wt = sum(p.waiting_time for p in finished) / n_fin if n_fin > 0 else 0.0
        avg_tat = sum((p.turnaround_time or 0) for p in finished) / n_fin if n_fin > 0 else 0.0
        avg_rt = sum((p.response_time or 0) for p in finished) / n_fin if n_fin > 0 else 0.0
        context_switches = sum(1 for b in self.gantt_chart if b.get("is_context_switch"))

        return {
            "tick": self.clock_tick,
            "is_playing": self.is_playing,
            "is_finished": self.is_finished,
            "speed": self.speed,
            "algorithm": self.algorithm,
            "time_quantum": self.time_quantum,
            "priority_preemptive": self.priority_preemptive,
            "total_processes": len(self.processes),
            "state_counts": state_counts,
            "processes": [p.to_dict() for p in self.processes.values()],
            "active_pid": self.active_pid,
            "active_process": active_proc,
            "current_slice": self.current_slice,
            "ready_queue_pids": ready_pids,
            "ready_queue": ready_procs,
            "waiting_queue": waiting_procs,
            "gantt_chart": self.gantt_chart,
            "active_transition": self.active_transition,
            "recent_events": self.event_log[-20:],
            "selected_pid": self.selected_pid,
            "selected_pcb": selected_pcb,
            "avg_waiting_time": round(avg_wt, 2),
            "avg_turnaround_time": round(avg_tat, 2),
            "avg_response_time": round(avg_rt, 2),
            "context_switches": context_switches,
            "presets": {k: {"name": v["name"], "desc": v["description"], "algo": v["algorithm"]} for k, v in self.get_presets().items()},
        }
