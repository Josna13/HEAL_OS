"""
Unit and Integration Tests for HealOS 2.0 - OS Process Lifecycle & Scheduling Lab
Validates:
1. Valid process-state transitions (NEW -> READY -> RUNNING -> WAITING -> TERMINATED).
2. Prohibited/invalid process-state transitions (rejections and error checking).
3. First-Come, First-Served (FCFS) scheduling metrics.
4. Shortest Job First (SJF, non-preemptive) scheduling metrics.
5. Round Robin (RR) preemptive scheduling with time quantum.
6. Priority scheduling metrics (non-preemptive, lower number = higher priority).
7. Waiting time, Turnaround time, and Response time metric calculations.
8. Real PID comparison on successful recovery (different PIDs, PCB allocation logic).
9. Real PID comparison on recovery failure.
10. Timestamp and recovery duration / SLA calculation consistency.
11. Dijkstra's Banker's Algorithm safe-state detection and safe sequence derivation.
12. Banker's Algorithm unsafe resource-request rejection.
13. Deadlock detection via Wait-For Graph cycle detection.
14. Deadlock recovery simulation (process cancellation & resource preemption).
15. OS Lab dashboard rendering and resilience to missing or incomplete AppState telemetry.
"""

import pytest
import time
import json
import threading
from datetime import datetime

from dashboard.process_lifecycle import (
    ProcessState,
    TransitionReason,
    InvalidStateTransitionError,
    LifecycleProcess,
    LifecycleEngine,
)
from dashboard.cpu_scheduler import (
    ScheduledProcess,
    CPUScheduler,
    SchedulingResult,
)
from dashboard.pid_comparison import (
    ProcessIdentityRecord,
    CrashRecoveryComparison,
)
from dashboard.deadlock_lab import (
    get_standard_scenarios,
    BankersAlgorithm,
    DeadlockDetector,
    DeadlockRecoverySimulator,
    TwoProcessDeadlockSimulation,
)
from dashboard.dashboard import AppState, TerminalDashboard
from dashboard.os_lab import OSLabCoordinator


class TestProcessLifecycleStateMachine:
    """Tests 1 & 2: Process Lifecycle Valid & Invalid State Transitions."""

    def test_valid_state_transitions(self):
        """NEW -> READY -> RUNNING -> WAITING -> READY -> RUNNING -> TERMINATED."""
        p = LifecycleProcess(pid=501, name="test_daemon", cpu_burst_total=5)
        assert p.state == ProcessState.NEW

        # NEW -> READY
        rec1 = p.transition_to(ProcessState.READY, TransitionReason.ADMIT)
        assert p.state == ProcessState.READY
        assert rec1.from_state == ProcessState.NEW
        assert rec1.to_state == ProcessState.READY

        # READY -> RUNNING
        rec2 = p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)
        assert p.state == ProcessState.RUNNING

        # RUNNING -> WAITING (I/O)
        rec3 = p.transition_to(ProcessState.WAITING, TransitionReason.BLOCK_IO)
        assert p.state == ProcessState.WAITING

        # WAITING -> READY (I/O complete)
        rec4 = p.transition_to(ProcessState.READY, TransitionReason.IO_COMPLETE)
        assert p.state == ProcessState.READY

        # READY -> RUNNING
        p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)
        assert p.state == ProcessState.RUNNING

        # RUNNING -> TERMINATED (Normal exit)
        rec5 = p.transition_to(ProcessState.TERMINATED, TransitionReason.EXIT_NORMAL)
        assert p.state == ProcessState.TERMINATED
        assert p.terminated_at is not None
        assert len(p.history) == 6

    def test_invalid_state_transitions_rejected(self):
        """Prohibits illegal shortcuts: NEW -> RUNNING, WAITING -> RUNNING, TERMINATED -> READY."""
        p = LifecycleProcess(pid=502, name="bad_actor", cpu_burst_total=3)

        # Illegal: NEW -> RUNNING directly without being admitted to READY
        with pytest.raises(InvalidStateTransitionError):
            p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)

        # Move to READY then RUNNING then WAITING
        p.transition_to(ProcessState.READY, TransitionReason.ADMIT)
        p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)
        p.transition_to(ProcessState.WAITING, TransitionReason.BLOCK_IO)

        # Illegal: WAITING -> RUNNING directly without returning to READY queue
        with pytest.raises(InvalidStateTransitionError):
            p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)

        # Return to READY -> RUNNING -> TERMINATED
        p.transition_to(ProcessState.READY, TransitionReason.IO_COMPLETE)
        p.transition_to(ProcessState.RUNNING, TransitionReason.DISPATCH)
        p.transition_to(ProcessState.TERMINATED, TransitionReason.CRASH)

        # Illegal: TERMINATED -> READY (Dead processes cannot be re-admitted)
        with pytest.raises(InvalidStateTransitionError):
            p.transition_to(ProcessState.READY, TransitionReason.ADMIT)

    def test_lifecycle_engine_simulation_stepping(self):
        """Tests stepping and auto-scheduling inside LifecycleEngine."""
        engine = LifecycleEngine()
        summary = engine.get_summary()
        assert summary["total_processes"] >= 4
        assert summary["tick"] == 0

        # Step advances tick and logs events
        desc1 = engine.step()
        assert engine.clock_tick == 1
        assert len(engine.event_log) > 0

        # Reset returns to tick 0
        engine.reset()
        assert engine.clock_tick == 0


class TestCPUSchedulingAlgorithms:
    """Tests 3-7: FCFS, SJF, RR, Priority, Waiting, Turnaround, Response Times."""

    @pytest.fixture
    def benchmark_processes(self):
        return [
            ScheduledProcess(pid=1, label="P1", arrival_time=0, burst_time=6, priority=2),
            ScheduledProcess(pid=2, label="P2", arrival_time=2, burst_time=4, priority=1),
            ScheduledProcess(pid=3, label="P3", arrival_time=4, burst_time=2, priority=3),
        ]

    def test_fcfs_scheduling(self, benchmark_processes):
        """
        FCFS with Arrival=[0, 2, 4], Burst=[6, 4, 2]:
        P1: Start=0, End=6, Turnaround=6, Waiting=0, Response=0
        P2: Start=6, End=10, Turnaround=8, Waiting=4, Response=4
        P3: Start=10, End=12, Turnaround=8, Waiting=6, Response=6
        """
        result = CPUScheduler.run_fcfs(benchmark_processes)
        assert result.algorithm == "FCFS"
        p_map = {p.label: p for p in result.processes}

        p1 = p_map["P1"]
        assert p1.first_start_time == 0
        assert p1.completion_time == 6
        assert p1.turnaround_time == 6
        assert p1.waiting_time == 0
        assert p1.response_time == 0

        p2 = p_map["P2"]
        assert p2.first_start_time == 6
        assert p2.completion_time == 10
        assert p2.turnaround_time == 8
        assert p2.waiting_time == 4
        assert p2.response_time == 4

        p3 = p_map["P3"]
        assert p3.first_start_time == 10
        assert p3.completion_time == 12
        assert p3.turnaround_time == 8
        assert p3.waiting_time == 6
        assert p3.response_time == 6

        assert round(result.avg_waiting_time, 2) == round((0 + 4 + 6) / 3, 2)
        assert round(result.avg_turnaround_time, 2) == round((6 + 8 + 8) / 3, 2)
        assert result.context_switches == 2

    def test_sjf_non_preemptive_scheduling(self, benchmark_processes):
        """
        SJF Non-preemptive:
        At t=0, only P1 arrived -> runs 0..6
        At t=6, P2 (burst=4) and P3 (burst=2) have arrived.
        P3 has shortest burst (2) -> runs 6..8
        Then P2 runs 8..12
        """
        result = CPUScheduler.run_sjf(benchmark_processes)
        p_map = {p.label: p for p in result.processes}

        p3 = p_map["P3"]
        p2 = p_map["P2"]
        # P3 finishes before P2
        assert p3.completion_time < p2.completion_time
        assert p3.first_start_time == 6
        assert p3.completion_time == 8
        assert p3.waiting_time == 6 - 4  # Start - Arrival = 2
        assert p2.first_start_time == 8
        assert p2.completion_time == 12

    def test_round_robin_preemptive_scheduling(self, benchmark_processes):
        """
        Round Robin with Quantum=2:
        Verifies preemption, time slice expiration, and queue re-admission.
        """
        result = CPUScheduler.run_round_robin(benchmark_processes, time_quantum=2)
        assert "Round Robin" in result.algorithm
        assert result.time_quantum == 2

        # In RR, all processes must complete
        for p in result.processes:
            assert p.completion_time is not None
            assert p.turnaround_time == p.completion_time - p.arrival_time
            assert p.waiting_time == p.turnaround_time - p.burst_time
            assert p.response_time == p.first_start_time - p.arrival_time

        # Context switches must be positive in preemptive RR
        assert result.context_switches >= 2

    def test_priority_scheduling_non_preemptive(self, benchmark_processes):
        """
        Priority Non-preemptive (lower number = higher priority):
        At t=0: P1 runs (0..6)
        At t=6: P2 (priority 1) and P3 (priority 3) available.
        P2 has higher priority (1 < 3) -> runs before P3.
        """
        result = CPUScheduler.run_priority(benchmark_processes)
        p_map = {p.label: p for p in result.processes}

        p2 = p_map["P2"]
        p3 = p_map["P3"]
        assert p2.completion_time < p3.completion_time
        assert p2.first_start_time == 6
        assert p2.completion_time == 10
        assert p3.first_start_time == 10
        assert p3.completion_time == 12

    def test_compare_all_algorithms(self, benchmark_processes):
        """Verifies comparison matrix execution across FCFS, SJF, RR, and Priority."""
        res = CPUScheduler.compare_all(benchmark_processes, quantum=2)
        assert "FCFS" in res
        assert "SJF" in res
        assert "RR" in res
        assert "PRIORITY" in res
        for algo in ["FCFS", "SJF", "RR", "PRIORITY"]:
            assert "avg_waiting_time" in res[algo]
            assert "avg_turnaround_time" in res[algo]
            assert "context_switches" in res[algo]


class TestCPUSchedulerUserInputs:
    """Tests for user-customizable CPU scheduling inputs, validation, and reference datasets."""

    def test_validate_process_inputs_valid(self):
        inputs = [
            {"label": "P1", "arrival_time": 0, "burst_time": 5, "priority": 2},
            {"label": "P2", "arrival_time": 1, "burst_time": 3, "priority": 1},
        ]
        ok, msg, procs = CPUScheduler.validate_process_inputs(inputs)
        assert ok is True
        assert "successfully" in msg
        assert len(procs) == 2
        assert procs[0].label == "P1"
        assert procs[0].burst_time == 5

    def test_validate_process_inputs_invalid_cases(self):
        # Empty list
        ok, err, procs = CPUScheduler.validate_process_inputs([])
        assert ok is False
        assert "empty" in err.lower()

        # Exceeds max 10
        too_many = [{"label": f"P{i}", "arrival_time": 0, "burst_time": 1, "priority": 1} for i in range(11)]
        ok, err, procs = CPUScheduler.validate_process_inputs(too_many)
        assert ok is False
        assert "10" in err and "Maximum" in err

        # Negative arrival time
        neg_arr = [{"label": "P1", "arrival_time": -1, "burst_time": 5, "priority": 1}]
        ok, err, procs = CPUScheduler.validate_process_inputs(neg_arr)
        assert ok is False
        assert "arrival" in err.lower()

        # Zero or negative burst time
        zero_burst = [{"label": "P1", "arrival_time": 0, "burst_time": 0, "priority": 1}]
        ok, err, procs = CPUScheduler.validate_process_inputs(zero_burst)
        assert ok is False
        assert "burst" in err.lower()

        # Duplicate labels
        dup_labels = [
            {"label": "P1", "arrival_time": 0, "burst_time": 2, "priority": 1},
            {"label": "P1", "arrival_time": 1, "burst_time": 3, "priority": 2},
        ]
        ok, err, procs = CPUScheduler.validate_process_inputs(dup_labels)
        assert ok is False
        assert "Duplicate" in err

    def test_get_example_datasets(self):
        datasets = CPUScheduler.get_example_datasets()
        assert "standard" in datasets
        assert "convoy_effect" in datasets
        assert "priority_mix" in datasets
        assert "staggered_arrivals" in datasets
        for name, procs in datasets.items():
            assert len(procs) >= 3
            ok, err, objs = CPUScheduler.validate_process_inputs(procs)
            assert ok is True, f"Dataset {name} failed validation: {err}"


class TestPIDComparisonAndRecovery:
    """Tests 8-10: PID Comparison, Recovery Success/Failure, and Durations."""

    def test_pid_comparison_on_successful_recovery(self):
        """Verifies original PID vs replacement PID tracking upon recovery."""
        comp = CrashRecoveryComparison()

        # Mock app_state with a recovery event
        class MockAppState:
            def __init__(self):
                self._lock = threading.Lock()
                self.app_pid = 18450
                self.failed_pid = 12040
                self.app_is_running = True
                self.total_crashes = 1
                self.last_crash_time = "14:02:10"
                self.app_uptime = 12.5
                self.app_cpu_percent = 0.5
                self.app_memory_mb = 18.2
                self.last_recovery_duration = 0.420
                self.last_recovery_status = "SUCCESS"
                self.decision_action = "RESTART_APPLICATION"
                self.decision_reason = "Nominal recovery policy"
                self.recent_recoveries = [{
                    "timestamp": "14:02:11",
                    "old_pid": 12040,
                    "new_pid": 18450,
                    "recovery_duration_sec": 0.420,
                    "recovery_duration_ms": 420.0,
                    "recovery_status": "SUCCESS",
                    "sla_met": True,
                }]

        mock_state = MockAppState()
        comp.sync_from_app_state(mock_state)

        data = comp.get_comparison_table_data()
        assert data["has_recovery_occurred"] is True
        assert data["original"]["pid"] == 12040
        assert data["replacement"]["pid"] == 18450
        assert data["original"]["pid"] != data["replacement"]["pid"]
        assert data["recovery_status"] == "SUCCESS"
        assert data["sla_met"] is True
        assert data["recovery_duration_ms"] == 420.0

    def test_pid_comparison_on_failed_recovery(self):
        """Verifies handling when recovery fails."""
        comp = CrashRecoveryComparison()

        class MockFailedState:
            def __init__(self):
                self._lock = threading.Lock()
                self.app_pid = None
                self.failed_pid = 9999
                self.app_is_running = False
                self.total_crashes = 1
                self.last_crash_time = "15:00:00"
                self.app_uptime = 0.0
                self.app_cpu_percent = 0.0
                self.app_memory_mb = 0.0
                self.last_recovery_duration = 3.5
                self.last_recovery_status = "FAILED"
                self.decision_action = "ALERT_USER"
                self.decision_reason = "Restart retry limit reached"
                self.recent_recoveries = [{
                    "timestamp": "15:00:03",
                    "old_pid": 9999,
                    "new_pid": None,
                    "recovery_duration_sec": 3.5,
                    "recovery_duration_ms": 3500.0,
                    "recovery_status": "FAILED",
                    "sla_met": False,
                }]

        comp.sync_from_app_state(MockFailedState())
        data = comp.get_comparison_table_data()
        assert data["recovery_status"] == "FAILED"
        assert data["sla_met"] is False
        assert data["replacement"]["state"] == "INACTIVE"

    def test_safe_trigger_creation_without_shell_exec(self):
        """Tests that trigger_crash_simulation writes data/crash.trigger safely and cleans up."""
        from dashboard.pid_comparison import CRASH_TRIGGER_FILE
        try:
            ok, msg = CrashRecoveryComparison.trigger_crash_simulation()
            assert ok is True
            assert "crash trigger" in msg.lower()
            assert CRASH_TRIGGER_FILE.exists()
        finally:
            CRASH_TRIGGER_FILE.unlink(missing_ok=True)


class TestDeadlockAndBankersAlgorithm:
    """Tests 11-14: Banker's Algorithm, Safe Sequences, Unsafe Rejection, Cycle Detection."""

    def test_bankers_algorithm_safe_sequence_detection(self):
        """Standard 5-process benchmark has guaranteed safe sequence <P1, P3, P4, P0, P2>."""
        scenarios = get_standard_scenarios()
        banker = BankersAlgorithm(scenarios["safe_banker"])

        is_safe, safe_seq, trace = banker.is_safe_state()
        assert is_safe is True
        assert len(safe_seq) == 5
        # P1 must be first since its Need <= Available
        assert safe_seq[0] == 1
        assert len(trace) >= 5

    def test_bankers_algorithm_unsafe_request_rejection(self):
        """Rejects a resource request that would violate system safety."""
        scenarios = get_standard_scenarios()
        banker = BankersAlgorithm(scenarios["safe_banker"])

        # Request exceeding maximum claim -> rejected immediately
        granted, msg, seq = banker.evaluate_request(process_id=0, request_vector=[10, 10, 10])
        assert granted is False
        assert "exceeded maximum claim" in msg.lower()

        # Request exceeding currently available -> process must wait (Need is [7, 4, 3], Available is [3, 3, 2])
        granted, msg, seq = banker.evaluate_request(process_id=0, request_vector=[4, 2, 1])
        assert granted is False
        assert "must wait" in msg.lower()

        # Valid safe request (P1 requests [1, 0, 2])
        granted, msg, seq = banker.evaluate_request(process_id=1, request_vector=[1, 0, 2])
        assert granted is True
        assert "granted" in msg.lower()

    def test_banker_update_custom_matrices_validation(self):
        """Tests validation of custom matrix dimensions, bounds, and max-claim constraints."""
        scenarios = get_standard_scenarios()
        banker = BankersAlgorithm(scenarios["safe_banker"])

        # 1. Valid update: 3 processes, 2 resources
        ok, msg = banker.update_custom_matrices(
            num_processes=3,
            num_resources=2,
            available=[2, 3],
            allocation=[[1, 0], [0, 2], [1, 1]],
            max_matrix=[[2, 1], [1, 2], [2, 3]],
            resource_names=["CPU_Core", "RAM_Block"],
        )
        assert ok is True
        assert banker.n == 3
        assert banker.m == 2
        assert banker.available == [2, 3]
        # Need = Max - Alloc: P0 need is [1, 1], P1 need is [1, 0], P2 need is [1, 2]
        assert banker.need == [[1, 1], [1, 0], [1, 2]]

        # 2. Invalid: Available dimension mismatch
        ok, msg = banker.update_custom_matrices(
            num_processes=3,
            num_resources=2,
            available=[2, 3, 1],  # 3 items instead of 2
            allocation=[[1, 0], [0, 2], [1, 1]],
            max_matrix=[[2, 1], [1, 2], [2, 3]],
        )
        assert ok is False
        assert "dimension" in msg.lower()

        # 3. Invalid: Allocation exceeds Max claim
        ok, msg = banker.update_custom_matrices(
            num_processes=2,
            num_resources=2,
            available=[1, 1],
            allocation=[[3, 0], [0, 1]],  # 3 > 2
            max_matrix=[[2, 1], [1, 1]],
        )
        assert ok is False
        assert "exceeds" in msg.lower()

        # 4. Invalid: Negative value
        ok, msg = banker.update_custom_matrices(
            num_processes=2,
            num_resources=2,
            available=[-1, 1],
            allocation=[[0, 0], [0, 0]],
            max_matrix=[[1, 1], [1, 1]],
        )
        assert ok is False
        assert "non-negative" in msg.lower()

    def test_banker_get_safety_steps_structure(self):
        """Verifies step-by-step Work and Finish vector progression for safe and unsafe states."""
        scenarios = get_standard_scenarios()
        banker = BankersAlgorithm(scenarios["safe_banker"])

        # Test safe state steps
        res = banker.get_safety_steps()
        assert res["is_safe"] is True
        assert len(res["safe_sequence"]) == 5
        assert len(res["steps"]) == 6  # Step 0 initial + 5 process steps
        assert res["steps"][0]["step"] == 0
        assert res["steps"][0]["work"] == [3, 3, 2]
        assert res["steps"][0]["finish"] == [False, False, False, False, False]
        # After first step, candidate 1 (P1) is satisfied
        assert res["steps"][1]["candidate"] == 1
        assert res["steps"][1]["finish"][1] is True

        # Test unsafe state steps
        banker_unsafe = BankersAlgorithm(scenarios["two_process_deadlock"])
        unsafe_res = banker_unsafe.get_safety_steps()
        assert unsafe_res["is_safe"] is False
        assert len(unsafe_res["safe_sequence"]) < banker_unsafe.n

    def test_wait_for_graph_deadlock_cycle_detection(self):
        """Detects circular wait loop: P0 -> P1 -> P2 -> P0 in deadlocked scenario."""
        scenarios = get_standard_scenarios()
        deadlock_sc = scenarios["circular_deadlock"]

        detector = DeadlockDetector(
            num_processes=deadlock_sc.num_processes,
            num_resources=deadlock_sc.num_resources,
            allocation=deadlock_sc.allocation,
            requests=[
                [0, 1, 0],  # P0 requests Mutex_B
                [0, 0, 1],  # P1 requests Mutex_C
                [1, 0, 0],  # P2 requests Mutex_A
            ],
        )

        wfg = detector.build_wait_for_graph()
        assert 1 in wfg[0]  # P0 waits for P1
        assert 2 in wfg[1]  # P1 waits for P2
        assert 0 in wfg[2]  # P2 waits for P0

        has_cycle, cycles = detector.detect_cycles()
        assert has_cycle is True
        assert len(cycles) > 0

    def test_deadlock_recovery_simulation(self):
        """Tests simulated preemption/cancellation of deadlocked process."""
        avail = [0, 0, 0]
        alloc = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        reqs = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]

        # Terminating P1 should free Mutex_B, breaking the deadlock
        new_avail, new_alloc, new_reqs, msg = DeadlockRecoverySimulator.cancel_process(
            process_id=1,
            available=avail,
            allocation=alloc,
            requests=reqs,
        )

        assert new_avail[1] == 1  # Mutex_B released back to pool
        assert new_alloc[1] == [0, 0, 0]
        assert "Terminated P1" in msg

        # Re-check WFG: Cycle should be broken
        detector = DeadlockDetector(
            num_processes=3,
            num_resources=3,
            allocation=new_alloc,
            requests=new_reqs,
        )
        has_cycle, _ = detector.detect_cycles()
        assert has_cycle is False


class TestTwoProcessDeadlockSimulation:
    """Tests 2-process 2-resource interactive circular wait deadlock."""

    def test_two_process_deadlock_step_by_step(self):
        sim = TwoProcessDeadlockSimulation()
        assert sim.step_idx == 0
        s0 = sim.get_state()
        assert s0["step"] == 0
        assert s0["is_deadlocked"] is False
        assert s0["available"] == [1, 1]

        # Step 1: P1 acquires R1
        s1 = sim.step()
        assert s1["step"] == 1
        assert s1["allocation"][0] == [1, 0]
        assert s1["is_deadlocked"] is False

        # Step 2: P2 acquires R2
        s2 = sim.step()
        assert s2["step"] == 2
        assert s2["allocation"][1] == [0, 1]
        assert s2["is_deadlocked"] is False

        # Step 3: P1 requests R2 (Blocked)
        s3 = sim.step()
        assert s3["step"] == 3
        assert s3["requests"][0] == [0, 1]
        assert "P1" in s3["blocked"]
        assert s3["is_deadlocked"] is False

        # Step 4: P2 requests R1 (DEADLOCK formed: circular wait)
        s4 = sim.step()
        assert s4["step"] == 4
        assert s4["is_deadlocked"] is True
        assert len(s4["cycle"]) == 5
        assert s4["cycle"][0] == s4["cycle"][-1] == "P1"

        # Step 5: Recovery
        s5 = sim.step()
        assert s5["step"] == 5
        assert s5["is_deadlocked"] is False

        # Reset
        sim.reset()
        assert sim.step_idx == 0


class TestPCBInspectorAndRegisters:
    """Tests PCB data structures, simulated registers, and memory mappings."""

    def test_pcb_details_structure(self):
        p = LifecycleProcess(pid=105, name="worker_app", cpu_burst_total=6)
        pcb = p.get_pcb_details()
        assert pcb["pid"] == 105
        assert pcb["name"] == "worker_app"
        assert pcb["simulated_registers"]["PC"].startswith("0x")
        assert "SP" in pcb["simulated_registers"]
        assert "R0" in pcb["simulated_registers"]
        assert "PSW" in pcb["simulated_registers"]
        assert pcb["state"] == "NEW"
        assert pcb["data_provenance"] == "[SIMULATION]"

    def test_lifecycle_engine_get_pcb(self):
        engine = LifecycleEngine()
        pids = list(engine.processes.keys())
        assert len(pids) > 0
        pcb = engine.get_pcb(pids[0])
        assert pcb is not None
        assert pcb["pid"] == pids[0]
        assert engine.get_pcb(999999) is None


class TestSchedulerTimelineAtTick:
    """Tests timeline playhead inspection for live scheduler animation."""

    def test_timeline_at_tick_inspection(self):
        procs = [
            ScheduledProcess(1, "P1", arrival_time=0, burst_time=3),
            ScheduledProcess(2, "P2", arrival_time=1, burst_time=2),
        ]
        result = CPUScheduler.run_fcfs(procs)

        t0 = result.get_timeline_at_tick(0)
        assert t0["tick"] == 0
        assert t0["current_process"] == "P1"

        t2 = result.get_timeline_at_tick(2)
        assert t2["tick"] == 2
        assert t2["current_process"] == "P1"

        t4 = result.get_timeline_at_tick(4)
        assert t4["tick"] == 4
        assert t4["current_process"] == "P2"
        assert "P1" in t4["completed"]

        t10 = result.get_timeline_at_tick(10)
        assert t10["is_finished"] is True
        assert len(t10["completed"]) == 2


class TestOSLabCoordinatorAndDashboardIntegration:
    """Tests 14 & 15: Rendering and Resilience to Incomplete Data."""

    def test_os_lab_coordinator_rendering_resilience(self):
        """Ensures OSLabCoordinator renders cleanly even with an empty/initial AppState."""
        coord = OSLabCoordinator()
        state = AppState()

        # Render all sections without exceptions
        for sec in ["ALL", "LIFECYCLE", "SCHEDULER", "PID_COMPARE", "DEADLOCK"]:
            coord.switch_section(sec)
            renderable = coord.render(state)
            assert renderable is not None

    def test_guided_presentation_step_progression(self):
        """Tests advancing through all 13 presentation steps."""
        coord = OSLabCoordinator()
        steps_seen = set()

        for _ in range(13):
            narrative = coord.next_demo_step()
            assert "Step" in narrative
            steps_seen.add(coord.demo_step)

        # All 13 steps must have been visited
        assert len(steps_seen) == 13
        assert steps_seen == set(range(1, 14))

    def test_terminal_dashboard_tab_switching(self):
        """Verifies TerminalDashboard tab switching between overview and os-lab."""
        state = AppState()
        dash = TerminalDashboard(state, initial_tab="overview")
        assert dash.active_tab == "overview"

        # Switch to OS Lab tab
        dash.switch_tab("os-lab")
        assert dash.active_tab == "os-lab"

        # Switch sub-section
        dash.switch_lab_section("SCHEDULER")
        assert dash.os_lab.active_section == "SCHEDULER"

        # Switch back to overview
        dash.switch_tab("overview")
        assert dash.active_tab == "overview"

    def test_web_server_endpoints(self):
        """Tests that WebDashboardServer starts, serves HTML and status JSON, and stops cleanly."""
        import urllib.request
        from dashboard.web_server import WebDashboardServer
        server = WebDashboardServer(port=8899)
        server.start()
        try:
            time.sleep(0.3)
            # Test GET /
            with urllib.request.urlopen("http://127.0.0.1:8899/") as resp:
                assert resp.status == 200
                html = resp.read().decode("utf-8")
                assert "OS Process Lifecycle" in html

            # Test GET /api/status
            with urllib.request.urlopen("http://127.0.0.1:8899/api/status") as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode("utf-8"))
                assert "lifecycle" in data
                assert "scheduler" in data
                assert "timeline_ticks" in data["scheduler"]
                assert "raw_processes" in data["scheduler"]
                assert len(data["scheduler"]["timeline_ticks"]) > 0
                assert "active_process" in data["scheduler"]["timeline_ticks"][0]
                assert "scheduler_comparison" in data
                assert "pid_comparison" in data
                assert "deadlock" in data

            # Test POST /api/action (set_custom_scheduler_processes)
            custom_req = urllib.request.Request(
                "http://127.0.0.1:8899/api/action",
                data=json.dumps({
                    "action": "set_custom_scheduler_processes",
                    "processes": [
                        {"label": "ProcA", "arrival_time": 0, "burst_time": 6, "priority": 1},
                        {"label": "ProcB", "arrival_time": 2, "burst_time": 3, "priority": 2},
                    ]
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(custom_req) as resp:
                assert resp.status == 200
                custom_res = json.loads(resp.read().decode("utf-8"))
                assert custom_res["status"] == "ok"

            # Test POST /api/action (reset_scheduler_dataset)
            reset_ds_req = urllib.request.Request(
                "http://127.0.0.1:8899/api/action",
                data=json.dumps({
                    "action": "reset_scheduler_dataset",
                    "dataset": "standard"
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(reset_ds_req) as resp:
                assert resp.status == 200
                reset_res = json.loads(resp.read().decode("utf-8"))
                assert reset_res["status"] == "ok"

            # Test POST /api/action (set_scheduler_quantum)
            post_req = urllib.request.Request(
                "http://127.0.0.1:8899/api/action",
                data=json.dumps({"action": "set_scheduler_quantum", "quantum": 3}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(post_req) as resp:
                assert resp.status == 200
                post_res = json.loads(resp.read().decode("utf-8"))
                assert post_res["status"] == "ok"

            # Test POST /api/action (trigger_crash)
            crash_req = urllib.request.Request(
                "http://127.0.0.1:8899/api/action",
                data=json.dumps({"action": "trigger_crash"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(crash_req) as resp:
                assert resp.status == 200
                crash_res = json.loads(resp.read().decode("utf-8"))
                assert crash_res["status"] == "ok"

            # Test GET /api/status after crash
            with urllib.request.urlopen("http://127.0.0.1:8899/api/status") as resp:
                assert resp.status == 200
                status_after = json.loads(resp.read().decode("utf-8"))
                pid_info = status_after["pid_comparison"]
                assert pid_info["has_recovery_occurred"] is True
                assert pid_info["original"]["pid"] is not None
                assert pid_info["replacement"]["pid"] is not None
                assert pid_info["recovery_status"] == "SUCCESS"
                assert pid_info["sla_met"] is True

        finally:
            from config import CRASH_TRIGGER_FILE
            CRASH_TRIGGER_FILE.unlink(missing_ok=True)
            server.stop()


class TestLifecycleVisualizerEngineAndEndpoints:
    """Comprehensive tests for the Interactive OS Process Execution Visualizer (Workspace 1)."""

    def test_process_lifecycle_creation_and_pid_allocation(self):
        """Validates simulated PID allocation, PCB initialization, and 15-field inspector metadata."""
        engine = LifecycleEngine()
        initial_count = len(engine.processes)

        # Allocate simulated PID and create process
        proc = engine.add_process(
            name="crypto_worker",
            burst=6,
            arrival=2,
            priority=3,
            io_request=2,
            io_duration=3,
        )
        assert proc.pid > 100
        assert proc.name == "crypto_worker"
        assert proc.cpu_burst_total == 6
        assert proc.cpu_burst_remaining == 6
        assert proc.arrival_time == 2
        assert proc.priority == 3
        assert proc.io_request_time == 2
        assert proc.io_duration == 3
        assert proc.state == ProcessState.NEW

        # Verify 15-field PCB inspection
        pcb = proc.get_pcb_details()
        required_fields = [
            "pid",
            "name",
            "state",
            "arrival_time",
            "first_start_time",
            "cpu_burst_total",
            "cpu_burst_remaining",
            "completion_time",
            "waiting_time",
            "turnaround_time",
            "response_time",
            "priority",
            "cpu_allocations_count",
            "preemptions_count",
            "history",
        ]
        for field in required_fields:
            assert field in pcb, f"Missing required PCB field: {field}"

        assert pcb["data_provenance"] == "[SIMULATION]"
        assert "field_explanations" in pcb
        assert "waiting_time" in pcb["field_explanations"]

        # Test process removal
        removed = engine.remove_process(proc.pid)
        assert removed is True
        assert proc.pid not in engine.processes

    def test_process_lifecycle_io_blocking_and_waiting_time(self):
        """
        Validates the complete process journey through I/O blocking:
        NEW -> READY -> RUNNING -> WAITING (I/O) -> READY -> RUNNING -> TERMINATED.
        Validates that waiting time strictly excludes time spent blocked on I/O.
        """
        engine = LifecycleEngine()
        engine.processes.clear()
        engine.initial_specs.clear()

        # Add single process with I/O: burst 3, arrives at 0, requests I/O after 1 burst, duration 2 ticks
        p = engine.add_process(
            name="io_proc",
            burst=3,
            arrival=0,
            priority=1,
            io_request=1,
            io_duration=2,
        )
        engine.admit_process(p.pid)
        assert p.state == ProcessState.READY

        # Tick 0 -> 1: Dispatched from READY to CPU RUNNING
        res1 = engine.step_tick()
        assert p.state == ProcessState.RUNNING
        assert p.waiting_time == 0  # No waiting

        # Tick 1 -> 2: Executes 1 tick on CPU -> triggers I/O block -> WAITING
        res2 = engine.step_tick()
        assert p.cpu_time_used == 1
        assert p.state == ProcessState.WAITING
        assert p.io_remaining == 2
        assert p.waiting_time == 0  # No ready queue waiting

        # Tick 2 -> 3: In WAITING, I/O remaining decrements 2 -> 1
        res3 = engine.step_tick()
        assert p.state == ProcessState.WAITING
        assert p.io_remaining == 1
        assert p.waiting_time == 0  # Still in WAITING, not in READY!

        # Tick 3 -> 4: In WAITING, I/O completes (1 -> 0) -> Unblocks to READY -> Dispatched
        res4 = engine.step_tick()
        assert p.io_remaining == 0
        assert p.cpu_time_used >= 1

        # Step until completion
        while not engine.is_finished and engine.clock_tick < 15:
            engine.step_tick()

        assert p.state == ProcessState.TERMINATED
        assert p.completion_time is not None
        tat = p.turnaround_time
        assert tat == p.completion_time - p.arrival_time
        # Waiting time strictly excludes time spent in WAITING for I/O!
        assert p.waiting_time == 0

    def test_process_lifecycle_rr_preemption(self):
        """Validates Round Robin quantum expiry and involuntary preemption."""
        engine = LifecycleEngine()
        engine.load_preset("rr_preemption")
        assert engine.algorithm == "RR"
        assert engine.time_quantum == 2

        # Step ticks and observe preemption in events
        preemptions_observed = False
        for _ in range(8):
            res = engine.step_tick()
            events = res.get("events", [])
            for e in events:
                if e.get("from") == "RUNNING" and e.get("to") == "READY":
                    preemptions_observed = True
                    assert "trans-running-ready" in e.get("arrow", "")
                    break
            if preemptions_observed:
                break

        assert preemptions_observed is True

    def test_process_lifecycle_presets_and_algorithms(self):
        """Validates all preset scenarios and algorithm switching."""
        engine = LifecycleEngine()
        presets = ["full_lifecycle_io", "rr_preemption", "sjf_arrival", "priority_mix"]
        for p_key in presets:
            engine.load_preset(p_key)
            assert len(engine.processes) >= 3
            assert engine.clock_tick == 0
            summary = engine.get_summary()
            assert summary["tick"] == 0
            assert "ready_queue" in summary

        # Test algorithm switching
        engine.set_algorithm("SJF")
        assert engine.algorithm == "SJF"
        engine.set_algorithm("PRIORITY", priority_preemptive=True)
        assert engine.algorithm == "PRIORITY"
        assert engine.priority_preemptive is True
        engine.set_algorithm("FCFS")
        assert engine.algorithm == "FCFS"

    def test_lifecycle_web_endpoints(self):
        """Integration test for web server lifecycle endpoints."""
        import urllib.request
        from dashboard.web_server import WebDashboardServer, WebDashboardHandler

        server = WebDashboardServer(port=8898)
        server.start()
        time.sleep(0.4)

        try:
            # 1. Test GET /api/status lifecycle payload
            with urllib.request.urlopen("http://127.0.0.1:8898/api/status") as resp:
                assert resp.status == 200
                data = json.loads(resp.read().decode("utf-8"))
                assert "lifecycle" in data
                lc = data["lifecycle"]
                assert "state_counts" in lc
                assert "processes" in lc
                assert "ready_queue" in lc
                assert "selected_pcb" in lc
                assert lc["selected_pcb"]["data_provenance"] == "[SIMULATION]"

            # 2. Test POST /api/action (set_lifecycle_algo)
            req_algo = urllib.request.Request(
                "http://127.0.0.1:8898/api/action",
                data=json.dumps({"action": "set_lifecycle_algo", "algo": "RR", "quantum": 3}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req_algo) as resp:
                assert resp.status == 200

            # 3. Test POST /api/action (add_lifecycle_process)
            req_add = urllib.request.Request(
                "http://127.0.0.1:8898/api/action",
                data=json.dumps({
                    "action": "add_lifecycle_process",
                    "name": "telemetry_svc",
                    "arrival_time": 0,
                    "cpu_burst": 5,
                    "priority": 2,
                    "io_request_time": 2,
                    "io_duration": 2,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req_add) as resp:
                assert resp.status == 200
                add_res = json.loads(resp.read().decode("utf-8"))
                assert add_res["status"] == "ok"
                new_pid = add_res["pid"]
                assert new_pid > 100

            # 4. Test POST /api/action (step_lifecycle_tick)
            req_step = urllib.request.Request(
                "http://127.0.0.1:8898/api/action",
                data=json.dumps({"action": "step_lifecycle_tick"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req_step) as resp:
                assert resp.status == 200

            # 5. Test POST /api/action (select_pcb)
            req_sel = urllib.request.Request(
                "http://127.0.0.1:8898/api/action",
                data=json.dumps({"action": "select_pcb", "pid": new_pid}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req_sel) as resp:
                assert resp.status == 200

            # 6. Test POST /api/action (restart_lifecycle)
            req_reset = urllib.request.Request(
                "http://127.0.0.1:8898/api/action",
                data=json.dumps({"action": "restart_lifecycle"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req_reset) as resp:
                assert resp.status == 200

        finally:
            server.stop()

