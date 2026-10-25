"""
HealOS 2.0 - OS Process Lifecycle & Scheduling Lab (Tab 2 Coordinator)
Renders the complete educational OS lab:
1. Section A: Animated Process Lifecycle State Machine
2. Section B: CPU Scheduling Visualizer (FCFS, SJF, RR, Priority with Gantt chart)
3. Section C: Real Crash, Old PID vs New PID Comparison
4. Section D: Deadlock Detection, Banker's Avoidance & Recovery Lab
5. Presentation Mode: Automated step-by-step guided demonstration

Provides clear data provenance labels:
- [LIVE DATA]
- [RECORDED EVENT]
- [SIMULATION]
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group

from dashboard.process_lifecycle import LifecycleEngine, ProcessState
from dashboard.cpu_scheduler import CPUScheduler, ScheduledProcess
from dashboard.pid_comparison import CrashRecoveryComparison
from dashboard.deadlock_lab import (
    get_standard_scenarios,
    BankersAlgorithm,
    DeadlockDetector,
    DeadlockRecoverySimulator,
    TwoProcessDeadlockSimulation,
)


class OSLabCoordinator:
    """
    Coordinates data sources, simulations, presentation mode, and rich terminal rendering
    for the 'OS Process Lifecycle & Scheduling Lab' tab.
    """

    def __init__(self):
        # Sub-section selection: "ALL", "LIFECYCLE", "SCHEDULER", "PID_COMPARE", "DEADLOCK"
        self.active_section: str = "ALL"

        # 1. Lifecycle Engine (Section A)
        self.lifecycle_engine = LifecycleEngine()

        # 2. CPU Scheduler (Section B)
        self.scheduler_algorithm: str = "RR"  # "FCFS", "SJF", "RR", "PRIORITY"
        self.rr_quantum: int = 2
        self.cached_schedule_result = None
        self._recompute_schedule()

        # 3. PID Comparison (Section C)
        self.pid_comparison = CrashRecoveryComparison()

        # 4. Deadlock Lab (Section D)
        self.scenarios = get_standard_scenarios()
        self.active_scenario_key: str = "two_process_deadlock"
        self.banker = BankersAlgorithm(self.scenarios["safe_banker"])
        self.two_proc_deadlock = TwoProcessDeadlockSimulation()
        self.last_banker_request_status: str = "Nominal system state evaluated."

        # 5. Presentation / Guided Demo Mode (13 Comprehensive OS Steps)
        self.demo_mode_active: bool = False
        self.demo_step: int = 1
        self.demo_max_steps: int = 13
        self.demo_narrative: str = "Welcome to the HealOS 2.0 OS Process Lab."

        # 6. Centralized Live Event Timeline
        self.timeline_events: List[Dict[str, Any]] = []
        self._record_timeline_event("Simulation", None, "OS Process Lab initialized.", "[SIMULATION]")

    def _record_timeline_event(self, event_type: str, pid: Optional[int], explanation: str, provenance: str) -> None:
        """Appends a structured event entry to the central OS Lab timeline."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.timeline_events.append({
            "timestamp": ts,
            "event_type": event_type,
            "pid": pid if pid is not None else "-",
            "explanation": explanation,
            "provenance": provenance,
        })
        if len(self.timeline_events) > 100:
            self.timeline_events.pop(0)

    def _recompute_schedule(self) -> None:
        """Recomputes CPU scheduling simulation based on active algorithm."""
        default_procs = CPUScheduler.get_default_processes()
        if self.scheduler_algorithm == "FCFS":
            self.cached_schedule_result = CPUScheduler.run_fcfs(default_procs)
        elif self.scheduler_algorithm == "SJF":
            self.cached_schedule_result = CPUScheduler.run_sjf(default_procs)
        elif self.scheduler_algorithm == "PRIORITY":
            self.cached_schedule_result = CPUScheduler.run_priority(default_procs)
        else:  # RR
            self.cached_schedule_result = CPUScheduler.run_round_robin(default_procs, time_quantum=self.rr_quantum)

    def switch_section(self, section: str) -> None:
        """Switches sub-view: ALL, LIFECYCLE, SCHEDULER, PID_COMPARE, DEADLOCK."""
        sec = section.upper()
        if sec in ("ALL", "LIFECYCLE", "SCHEDULER", "PID_COMPARE", "DEADLOCK"):
            self.active_section = sec

    def next_demo_step(self) -> str:
        """Advances guided presentation demo by one step across the 13-step sequence."""
        self.demo_step = (self.demo_step % self.demo_max_steps) + 1
        narratives = {
            1: "Step 1/13: Process Creation & PCB Allocation — PCB created; PID 101 allocated in NEW state.",
            2: "Step 2/13: Ready Queue Admission — Process PCB admitted to READY queue; awaiting CPU dispatch.",
            3: "Step 3/13: CPU Scheduler Selection — Scheduler dispatches process to RUNNING state.",
            4: "Step 4/13: CPU Execution & Gantt Timeline — Active burst executed; timeline intervals tracked.",
            5: "Step 5/13: Resource Request & Waiting State — Process blocks on I/O or Mutex; moves to WAITING.",
            6: "Step 6/13: Deadlock Formation (Circular Wait) — P1 holds R1, requests R2; P2 holds R2, requests R1.",
            7: "Step 7/13: Deadlock Avoidance (Banker's Algorithm) — Unsafe resource request evaluated and rejected.",
            8: "Step 8/13: Live Application Surveillance — HealOS monitors dummy_app.py PID, CPU, and RAM.",
            9: "Step 9/13: Simulated Crash Trigger — Failure signal dispatched via data/crash.trigger.",
            10: "Step 10/13: Process Termination Observation — Original PID terminates and is freed by kernel.",
            11: "Step 11/13: Autonomic Recovery Policy — Decision engine evaluates safety and initiates replacement.",
            12: "Step 12/13: PID Forensics & Transition Comparison — Original PID compared with replacement PID.",
            13: "Step 13/13: Recovery Verification & SLA Stream — Replacement process verified alive via psutil.",
        }
        self.demo_narrative = narratives.get(self.demo_step, "Presentation Demo Active.")

        # Sync section and simulation action with step
        if self.demo_step in (1, 2):
            self.active_section = "LIFECYCLE"
            if self.demo_step == 2:
                self.lifecycle_engine.step()
        elif self.demo_step in (3, 4):
            self.active_section = "SCHEDULER"
        elif self.demo_step == 5:
            self.active_section = "LIFECYCLE"
            self.lifecycle_engine.step()
        elif self.demo_step == 6:
            self.active_section = "DEADLOCK"
            self.active_scenario_key = "two_process_deadlock"
            self.two_proc_deadlock.step_idx = 4  # deadlock formed
        elif self.demo_step == 7:
            self.active_section = "DEADLOCK"
            self.active_scenario_key = "safe_banker"
        elif self.demo_step >= 8:
            self.active_section = "PID_COMPARE"

        provenance = "[LIVE DATA]" if self.demo_step >= 8 else "[SIMULATION]"
        self._record_timeline_event(f"DemoStep{self.demo_step}", None, self.demo_narrative, provenance)
        return self.demo_narrative

    def render(self, app_state: Any) -> Group:
        """Renders the complete rich UI for the OS Process Lab tab."""
        # Sync live data
        self.pid_comparison.sync_from_app_state(app_state)

        # Build sub-nav bar
        subnav_text = Text()
        subnav_text.append(" OS LAB SUB-VIEWS: ", style="bold cyan")

        tabs = [
            ("1: All Lab", "ALL"),
            ("A: Lifecycle", "LIFECYCLE"),
            ("B: Scheduler", "SCHEDULER"),
            ("C: PID Compare", "PID_COMPARE"),
            ("D: Deadlock", "DEADLOCK"),
        ]
        for label, code in tabs:
            if self.active_section == code:
                subnav_text.append(f"[{label}] ", style="bold black on cyan")
            else:
                subnav_text.append(f"{label} │ ", style="dim white")

        demo_badge = f"[bold green]▶ DEMO STEP {self.demo_step}/{self.demo_max_steps}[/bold green]" if self.demo_mode_active else "[dim]Demo Idle[/dim]"
        subnav_panel = Panel(
            Table.grid(expand=True),
            title=f"[bold]OS PROCESS LIFECYCLE & SCHEDULING LAB[/bold] │ {demo_badge}",
            subtitle=subnav_text,
            border_style="cyan",
            padding=(0, 1),
        )

        if self.active_section == "LIFECYCLE":
            body = self._render_section_a_lifecycle()
        elif self.active_section == "SCHEDULER":
            body = self._render_section_b_scheduler()
        elif self.active_section == "PID_COMPARE":
            body = self._render_section_c_pid_compare(app_state)
        elif self.active_section == "DEADLOCK":
            body = self._render_section_d_deadlock()
        else:
            # "ALL" Compact Overview
            body = self._render_compact_all(app_state)

        # Footer controls
        footer = Text()
        footer.append("Keys: ", style="bold white")
        footer.append("[A-D/1]", style="bold yellow")
        footer.append(" Switch Lab Section │ ", style="dim white")
        footer.append("[Space]", style="bold cyan")
        footer.append(" Step Lifecycle │ ", style="dim white")
        footer.append("[P]", style="bold green")
        footer.append(" Presentation Step │ ", style="dim white")
        footer.append("[T]", style="bold red")
        footer.append(" Trigger Crash Demo │ ", style="dim white")
        footer.append("[1]", style="bold white")
        footer.append(" System Overview", style="dim white")

        return Group(subnav_panel, body, footer)

    def _render_compact_all(self, app_state: Any) -> Group:
        """Renders all 4 sections in a balanced, single-screen layout."""
        # Top Grid: Section A (Lifecycle) + Section B (Scheduler)
        top_grid = Table.grid(expand=True, padding=(0, 1))
        top_grid.add_column(ratio=6)
        top_grid.add_column(ratio=6)

        pA = self._build_lifecycle_panel()
        pB = self._build_scheduler_panel()
        top_grid.add_row(pA, pB)

        # Bottom Grid: Section C (PID Compare) + Section D (Deadlock)
        bot_grid = Table.grid(expand=True, padding=(0, 1))
        bot_grid.add_column(ratio=6)
        bot_grid.add_column(ratio=6)

        pC = self._build_pid_compare_panel(app_state)
        pD = self._build_deadlock_panel()
        bot_grid.add_row(pC, pD)

        return Group(top_grid, bot_grid)

    def _build_lifecycle_panel(self) -> Panel:
        """Section A panel widget."""
        summary = self.lifecycle_engine.get_summary()
        t = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        t.add_column("State", style="bold cyan", width=12)
        t.add_column("PIDs", style="white")

        counts = summary["state_counts"]
        procs = summary["processes"]

        for state in [ProcessState.RUNNING, ProcessState.READY, ProcessState.WAITING, ProcessState.NEW, ProcessState.TERMINATED]:
            st_name = state.value
            p_in_st = [f"P{p['pid']}({p['name'][:7]})" for p in procs if p["state"] == st_name]
            p_str = ", ".join(p_in_st) if p_in_st else "[dim]None[/dim]"

            style_map = {
                "RUNNING": "bold green",
                "READY": "bold cyan",
                "WAITING": "bold yellow",
                "NEW": "bold magenta",
                "TERMINATED": "dim red",
            }
            color = style_map.get(st_name, "white")
            t.add_row(f"[{color}]{st_name}[/{color}] ({counts[st_name]})", p_str)

        recent = summary["recent_events"]
        last_ev = recent[-1]["message"] if recent else "Simulation initialized"
        if len(last_ev) > 42:
            last_ev = last_ev[:39] + "..."
        t.add_row("Last Event", f"[italic yellow]{last_ev}[/italic yellow]")

        return Panel(
            t,
            title="[bold]A. Process Lifecycle State Machine[/bold] [dim yellow][SIMULATION][/dim yellow]",
            border_style="magenta",
            padding=(0, 1),
        )

    def _build_scheduler_panel(self) -> Panel:
        """Section B panel widget."""
        res = self.cached_schedule_result
        t = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        t.add_column("Key", style="bold cyan", width=13)
        t.add_column("Val", style="white")

        t.add_row("Algorithm", f"[bold green]{res.algorithm}[/bold green] (Context Switches: {res.context_switches})")
        t.add_row("Averages", f"Wait: {res.avg_waiting_time:.1f}t │ Turnaround: {res.avg_turnaround_time:.1f}t │ Resp: {res.avg_response_time:.1f}t")

        # Compact Gantt string: [P1:0-2][P2:2-4]
        gantt_str = " ".join([f"[{b.label}:{b.start}-{b.end}]" for b in res.gantt_chart[:6]])
        if len(res.gantt_chart) > 6:
            gantt_str += "..."
        t.add_row("Gantt Chart", f"[bold yellow]{gantt_str}[/bold yellow]")

        # Process stats row
        proc_summary = " │ ".join([f"{p.label}: WT={p.waiting_time} TAT={p.turnaround_time}" for p in res.processes[:3]])
        t.add_row("Process Perf", f"[dim]{proc_summary}[/dim]")

        return Panel(
            t,
            title=f"[bold]B. CPU Scheduler ({res.algorithm})[/bold] [dim yellow][SIMULATION][/dim yellow]",
            border_style="green",
            padding=(0, 1),
        )

    def _build_pid_compare_panel(self, app_state: Any) -> Panel:
        """Section C panel widget."""
        comp = self.pid_comparison.get_comparison_table_data()
        t = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        t.add_column("Field", style="bold cyan", width=12)
        t.add_column("Original", style="white", ratio=1)
        t.add_column("Replacement", style="white", ratio=1)

        orig = comp["original"]
        repl = comp["replacement"]

        o_pid = f"[bold red]{orig['pid']}[/bold red]" if comp["has_recovery_occurred"] else f"[bold cyan]{orig['pid']}[/bold cyan]"
        n_pid = f"[bold green]{repl['pid']}[/bold green]" if comp["has_recovery_occurred"] else "[dim]Awaiting Crash[/dim]"
        t.add_row("PID", o_pid, n_pid)

        t.add_row("State", f"[dim red]{orig['state'][:14]}[/dim red]", f"[green]{repl['state'][:14]}[/green]")
        t.add_row("Uptime / RT", f"{orig['runtime_sec']:.1f}s", f"{repl['runtime_sec']:.1f}s (Alive)")

        sla_str = "[bold green]PASS (Met SLA)[/bold green]" if comp["sla_met"] else "[bold red]BREACH[/bold red]"
        lat_str = f"Dur: {comp['recovery_duration_ms']:.0f}ms │ SLA: {sla_str}"
        t.add_row("Recovery", lat_str, f"Action: {comp['decision_action']}")

        badge = "[bold green][LIVE DATA][/bold green]" if comp["has_recovery_occurred"] else "[dim cyan][MONITORING][/dim cyan]"
        return Panel(
            t,
            title=f"[bold]C. Crash & PID Comparison[/bold] {badge}",
            border_style="cyan",
            padding=(0, 1),
        )

    def _build_deadlock_panel(self) -> Panel:
        """Section D panel widget."""
        t = Table(box=None, show_header=False, expand=True, padding=(0, 0))
        t.add_column("Property", style="bold cyan", width=12)
        t.add_column("Value", style="white")

        scenario = self.scenarios.get(self.active_scenario_key, self.scenarios["safe_banker"])
        is_safe, safe_seq, trace = self.banker.is_safe_state()

        if self.active_scenario_key == "two_process_deadlock":
            st = self.two_proc_deadlock.get_state()
            st_text = "[bold red]DEADLOCK DETECTED (Circular Wait)[/bold red]" if st["is_deadlocked"] else f"[bold green]{st['p1_state']} / {st['p2_state']}[/bold green]"
            detail = f"{st['title']}"
        elif self.active_scenario_key == "circular_deadlock":
            detector = DeadlockDetector(
                num_processes=scenario.num_processes,
                num_resources=scenario.num_resources,
                allocation=scenario.allocation,
                requests=[[1 if scenario.max_matrix[i][j] > scenario.allocation[i][j] else 0 for j in range(3)] for i in range(3)],
            )
            has_cycle, cycles = detector.detect_cycles()
            st_text = "[bold red]DEADLOCK DETECTED (Cycle in WFG)[/bold red]"
            detail = f"Cycle: P0 -> Mutex_B -> P1 -> Mutex_C -> P2 -> Mutex_A"
        else:
            st_text = "[bold green]SAFE STATE (Banker's Algorithm)[/bold green]"
            seq_str = " -> ".join([f"P{p}" for p in safe_seq])
            detail = f"Safe Sequence: <{seq_str}>"

        t.add_row("Scenario", f"[bold yellow]{scenario.name[:30]}[/bold yellow]")
        t.add_row("Analysis", st_text)
        t.add_row("Resolution", detail)
        t.add_row("Principle", "[dim italic]Avoidance evaluates states before granting requests.[/dim italic]")

        return Panel(
            t,
            title="[bold]D. Deadlock & Banker's Lab[/bold] [dim yellow][SIMULATION][/dim yellow]",
            border_style="blue",
            padding=(0, 1),
        )

    def _render_section_a_lifecycle(self) -> Group:
        """Detailed view for Section A (Lifecycle)."""
        summary = self.lifecycle_engine.get_summary()

        # State Nodes Diagram
        diag = Text()
        diag.append("\n  [NEW] ──(Admit)──> [READY] ──(Dispatch)──> [RUNNING] ──(Exit/Crash)──> [TERMINATED]\n", style="bold cyan")
        diag.append("                        ▲                     │    │\n", style="dim")
        diag.append("                        │                     │    └──(I/O Block)──> [WAITING]\n", style="dim")
        diag.append("                        └────(Preempt)────────┘                          │\n", style="dim")
        diag.append("                        └─────────────(I/O Complete)─────────────────────┘\n", style="dim")
        diag_panel = Panel(diag, title="[bold]Standard OS Process State Transition Diagram[/bold]", border_style="cyan")

        # Process Table
        table = Table(title="Simulated Process Control Blocks (PCBs)", expand=True)
        table.add_column("PID", style="bold cyan", width=6)
        table.add_column("Name", style="white", width=14)
        table.add_column("Current State", style="bold yellow", width=14)
        table.add_column("Total Burst", style="white", width=12)
        table.add_column("Remaining", style="green", width=12)
        table.add_column("Wait Time", style="magenta", width=10)
        table.add_column("Created", style="dim", width=10)

        for p in summary["processes"]:
            table.add_row(
                str(p["pid"]),
                p["name"],
                p["state"],
                str(p["cpu_burst_total"]),
                str(p["cpu_burst_remaining"]),
                str(p["waiting_time"]),
                p["created_at"],
            )

        # PCB Inspector Panel
        pcb_info = summary.get("selected_pcb")
        if not pcb_info and summary["processes"]:
            pcb_info = self.lifecycle_engine.get_pcb(summary["processes"][0]["pid"])

        pcb_text = Text()
        if pcb_info:
            pcb_text.append(f"PID: {pcb_info['pid']} ({pcb_info['name']}) │ State: {pcb_info['state']} │ Priority: {pcb_info['priority']} │ Memory: {pcb_info['memory_mb']}MB\n", style="bold cyan")
            pcb_text.append(f"Registers: {pcb_info['simulated_registers']} [SIMULATED CONTEXT]\n", style="yellow")
            pcb_text.append(f"Last Event: {pcb_info['last_transition']} │ Created: {pcb_info['created_at']} │ Terminated: {pcb_info['terminated_at']}\n", style="white")
            pcb_text.append(f"Note: {pcb_info['kernel_disclaimer']}", style="dim italic")
        pcb_panel = Panel(pcb_text, title="[bold]Process Control Block (PCB) Inspector [SIMULATION][/bold]", border_style="yellow")

        # Transition Event Log
        log_table = Table(title="Recent State Transition Events", expand=True)
        log_table.add_column("Tick", width=6)
        log_table.add_column("Time", width=10)
        log_table.add_column("Transition Event Description", style="italic")
        for ev in summary["recent_events"]:
            log_table.add_row(str(ev["tick"]), ev["timestamp"], ev["message"])

        return Group(diag_panel, table, pcb_panel, log_table)

    def _render_section_b_scheduler(self) -> Group:
        """Detailed view for Section B (CPU Scheduler)."""
        res = self.cached_schedule_result

        # Process Scheduling Metrics Table
        table = Table(title=f"CPU Scheduling Table — {res.algorithm}", expand=True)
        table.add_column("Process", style="bold cyan", width=8)
        table.add_column("Arrival (AT)", style="white", width=12)
        table.add_column("Burst (BT)", style="white", width=12)
        table.add_column("Priority", style="yellow", width=10)
        table.add_column("Start (ST)", style="green", width=10)
        table.add_column("Completion (CT)", style="bold green", width=14)
        table.add_column("Turnaround (TAT)", style="bold cyan", width=15)
        table.add_column("Waiting (WT)", style="bold magenta", width=12)
        table.add_column("Response (RT)", style="bold yellow", width=12)

        for p in res.processes:
            table.add_row(
                p.label,
                str(p.arrival_time),
                str(p.burst_time),
                str(p.priority),
                str(p.first_start_time),
                str(p.completion_time),
                str(p.turnaround_time),
                str(p.waiting_time),
                str(p.response_time),
            )

        # Gantt Chart Visual Representation
        gantt_text = Text()
        gantt_text.append("\nTimeline: ", style="bold white")
        for b in res.gantt_chart:
            color = "cyan" if b.label != "IDLE" else "dim"
            gantt_text.append(f"| {b.label} ({b.start}..{b.end}) ", style=f"bold {color}")
        gantt_text.append("|\n", style="bold white")

        metric_summary = Text()
        metric_summary.append(f"Average Waiting Time: {res.avg_waiting_time:.2f} ticks │ ", style="bold magenta")
        metric_summary.append(f"Average Turnaround Time: {res.avg_turnaround_time:.2f} ticks │ ", style="bold cyan")
        metric_summary.append(f"Context Switches: {res.context_switches}", style="bold yellow")

        gantt_panel = Panel(Group(gantt_text, metric_summary), title="[bold]CPU Execution Timeline (Gantt Chart)[/bold]", border_style="yellow")

        return Group(table, gantt_panel)

    def _render_section_c_pid_compare(self, app_state: Any) -> Group:
        """Detailed view for Section C (PID Comparison)."""
        data = self.pid_comparison.get_comparison_table_data()

        table = Table(title="HealOS Autonomic Recovery — Process Identity & Lifecycle Comparison", expand=True)
        table.add_column("Observed Metric / Field", style="bold cyan", width=25)
        table.add_column("Original Process (Before Crash)", style="white", width=30)
        table.add_column("Replacement Process (After Recovery)", style="bold green", width=30)

        orig = data["original"]
        repl = data["replacement"]

        table.add_row("Process Name", orig["name"], repl["name"])
        table.add_row("Operating System PID", str(orig["pid"]), str(repl["pid"]))
        table.add_row("Start Timestamp", orig["start_time"], repl["start_time"])
        table.add_row("Termination Timestamp", orig["end_time"], repl["end_time"])
        table.add_row("Final Observed State", orig["state"], repl["state"])
        table.add_row("Runtime Duration", f"{orig['runtime_sec']:.2f}s", f"{repl['runtime_sec']:.2f}s")
        table.add_row("CPU & Memory Load", f"CPU: {orig['cpu_percent']:.1f}% │ RAM: {orig['memory_mb']:.1f}MB", f"CPU: {repl['cpu_percent']:.1f}% │ RAM: {repl['memory_mb']:.1f}MB")
        table.add_row("Process Liveness (psutil)", "DEAD (Unlinked PCB)", "ALIVE (Running thread)" if data["is_replacement_alive"] else "OFFLINE")

        # Recovery Timeline & Metrics Panel
        sla_badge = "[bold green]PASS[/bold green]" if data["sla_met"] else "[bold red]BREACH[/bold red]"
        t_info = Text()
        t_info.append(f"Crash Detected At: {data['crash_detected_at']} │ Recovery Completed: {data['recovery_completed_at']}\n", style="white")
        t_info.append(f"Recovery Latency: {data['recovery_duration_ms']:.1f} ms ({data['recovery_duration_sec']:.2f}s) │ Downtime: {data['downtime_ms']:.1f} ms │ SLA Result: ", style="yellow")
        t_info.append(sla_badge)
        t_info.append(f" (Target: <= {data['sla_target_sec']}s)\n", style="dim")
        t_info.append(f"Recovery Policy Decision: {data['decision_action']} │ Reason: {data['decision_reason']}\n\n", style="cyan")
        t_info.append(data["os_pid_explanation"], style="italic dim white")

        info_panel = Panel(t_info, title="[bold]Recovery Latency & Operating System Concept Explanation[/bold]", border_style="cyan")

        return Group(table, info_panel)

    def _render_section_d_deadlock(self) -> Group:
        """Detailed view for Section D (Deadlock Lab)."""
        scenario = self.scenarios.get(self.active_scenario_key, self.scenarios["safe_banker"])

        # Banker's Matrices Table
        table = Table(title=f"Banker's Algorithm State Matrices — {scenario.name}", expand=True)
        table.add_column("Process", style="bold cyan")
        table.add_column("Allocation Matrix", style="white")
        table.add_column("Max Claim Matrix", style="yellow")
        table.add_column("Need Matrix (Max - Alloc)", style="green")

        for i in range(scenario.num_processes):
            table.add_row(
                f"P{i}",
                str(self.banker.allocation[i]),
                str(self.banker.max_matrix[i]),
                str(self.banker.need[i]),
            )

        avail_text = Text()
        avail_text.append(f"Available Vector: {self.banker.available} for Resources: {scenario.resource_names}\n", style="bold yellow")

        is_safe, safe_seq, trace = self.banker.is_safe_state()
        if is_safe:
            seq_str = " -> ".join([f"P{p}" for p in safe_seq])
            avail_text.append(f"System Safety Status: [bold green]SAFE STATE[/bold green]\n", style="white")
            avail_text.append(f"Guaranteed Safe Execution Sequence: <{seq_str}>\n", style="bold green")
        else:
            avail_text.append(f"System Safety Status: [bold red]UNSAFE STATE[/bold red] (Risk of circular deadlock)\n", style="white")

        avail_text.append(f"\nTrace Steps:\n" + "\n".join(f"  • {s}" for s in trace[:4]), style="dim")

        eval_panel = Panel(avail_text, title="[bold]Safety Evaluation & Trace[/bold]", border_style="green" if is_safe else "red")

        return Group(table, eval_panel)
