"""
HealOS 2.0 - Deadlock Detection, Avoidance & Recovery Lab (Section D)
Implements four fundamental operating system concurrency concepts:
1. Resource Allocation Graph (RAG) Modeling: Process nodes, resource instances, allocation and request edges.
2. Deadlock Avoidance (Banker's Algorithm): Available, Allocation, Max, Need matrices, safety check, and request evaluation.
3. Deadlock Detection: Wait-For Graph (WFG) cycle detection, blocked process enumeration.
4. Deadlock Recovery Simulation: Resource preemption, simulated process termination, and cycle clearing.

Disclaimer: All deadlock experiments use deterministic in-memory educational models; no real OS processes are killed.
"""

from typing import List, Dict, Tuple, Optional, Any
from copy import deepcopy


class DeadlockLabScenario:
    """Represents a selectable scenario in the Deadlock Lab."""

    def __init__(
        self,
        name: str,
        description: str,
        num_processes: int,
        num_resources: int,
        resource_names: List[str],
        available: List[int],
        allocation: List[List[int]],
        max_matrix: List[List[int]],
    ):
        self.name: str = name
        self.description: str = description
        self.num_processes: int = num_processes
        self.num_resources: int = num_resources
        self.resource_names: List[str] = resource_names
        self.available: List[int] = available
        self.allocation: List[List[int]] = allocation
        self.max_matrix: List[List[int]] = max_matrix


def get_standard_scenarios() -> Dict[str, DeadlockLabScenario]:
    """Provides standard educational scenarios for OS demonstrations."""
    # Scenario 1: Standard textbook safe state (5 processes P0-P4, 3 resource types A, B, C)
    safe_scenario = DeadlockLabScenario(
        name="Safe System State (Banker's Benchmark)",
        description="Classical textbook configuration with a guaranteed safe execution sequence <P1, P3, P4, P0, P2>.",
        num_processes=5,
        num_resources=3,
        resource_names=["CPU_Core", "RAM_Block", "Disk_Channel"],
        available=[3, 3, 2],
        allocation=[
            [0, 1, 0],  # P0
            [2, 0, 0],  # P1
            [3, 0, 2],  # P2
            [2, 1, 1],  # P3
            [0, 0, 2],  # P4
        ],
        max_matrix=[
            [7, 5, 3],  # P0
            [3, 2, 2],  # P1
            [9, 0, 2],  # P2
            [2, 2, 2],  # P3
            [4, 3, 3],  # P4
        ],
    )

    # Scenario 2: Classical 2-Process 2-Resource Circular Wait Deadlock
    two_process_deadlock = DeadlockLabScenario(
        name="Two-Process Circular Deadlock (P1-P2, R1-R2)",
        description="P1 holds R1 and requests R2; P2 holds R2 and requests R1. Classic circular wait condition.",
        num_processes=2,
        num_resources=2,
        resource_names=["Mutex_R1", "Mutex_R2"],
        available=[0, 0],
        allocation=[
            [1, 0],  # P1 holds R1
            [0, 1],  # P2 holds R2
        ],
        max_matrix=[
            [1, 1],  # P1 requests R2
            [1, 1],  # P2 requests R1
        ],
    )

    # Scenario 3: Circular Wait Deadlock (3 processes, 3 single-instance resources)
    deadlock_scenario = DeadlockLabScenario(
        name="Three-Process Circular Deadlock (RAG Cycle)",
        description="A circular wait loop: P0 holds R0 and requests R1; P1 holds R1 and requests R2; P2 holds R2 and requests R0.",
        num_processes=3,
        num_resources=3,
        resource_names=["Mutex_A", "Mutex_B", "Mutex_C"],
        available=[0, 0, 0],
        allocation=[
            [1, 0, 0],  # P0 holds Mutex_A
            [0, 1, 0],  # P1 holds Mutex_B
            [0, 0, 1],  # P2 holds Mutex_C
        ],
        max_matrix=[
            [1, 1, 0],  # P0 requests Mutex_B
            [0, 1, 1],  # P1 requests Mutex_C
            [1, 0, 1],  # P2 requests Mutex_A
        ],
    )

    return {
        "safe_banker": safe_scenario,
        "two_process_deadlock": two_process_deadlock,
        "circular_deadlock": deadlock_scenario,
    }


class TwoProcessDeadlockSimulation:
    """
    Step-by-step interactive simulation of deadlock formation between two processes
    (P1, P2) and two single-instance resources (R1, R2).
    """

    def __init__(self):
        self.step_idx: int = 0
        self.max_steps: int = 5
        self.resource_names = ["Mutex_R1", "Mutex_R2"]

    def reset(self) -> None:
        self.step_idx = 0

    def step(self) -> Dict[str, Any]:
        if self.step_idx < self.max_steps:
            self.step_idx += 1
        return self.get_state()

    def prev_step(self) -> Dict[str, Any]:
        if self.step_idx > 0:
            self.step_idx -= 1
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """
        Returns full graph topology, allocations, outstanding requests,
        and explanations for the current step.
        """
        s = self.step_idx
        # Steps:
        # 0: Initial state (Both resources free)
        # 1: P1 acquires R1
        # 2: P2 acquires R2
        # 3: P1 requests R2 (Blocked)
        # 4: P2 requests R1 (DEADLOCK! Circular Wait)
        # 5: Recovery: Terminate P2 -> R2 freed -> P1 acquires R2 and finishes
        if s == 0:
            return {
                "step": 0,
                "title": "Step 0/5 — Initial State (Resources Free)",
                "explanation": "Processes P1 and P2 are initialized. Resources R1 and R2 are currently unallocated.",
                "allocation": [[0, 0], [0, 0]],
                "requests": [[0, 0], [0, 0]],
                "available": [1, 1],
                "p1_state": "READY",
                "p2_state": "READY",
                "is_deadlocked": False,
                "edges": [],
                "cycle": [],
                "blocked": [],
            }
        elif s == 1:
            return {
                "step": 1,
                "title": "Step 1/5 — P1 Acquires Resource R1",
                "explanation": "P1 requests and is granted Mutex_R1. R1 is allocated to P1 (Allocation edge: R1 -> P1).",
                "allocation": [[1, 0], [0, 0]],
                "requests": [[0, 0], [0, 0]],
                "available": [0, 1],
                "p1_state": "RUNNING",
                "p2_state": "READY",
                "is_deadlocked": False,
                "edges": [{"from": "R1", "to": "P1", "type": "allocation"}],
                "cycle": [],
                "blocked": [],
            }
        elif s == 2:
            return {
                "step": 2,
                "title": "Step 2/5 — P2 Acquires Resource R2",
                "explanation": "P2 requests and is granted Mutex_R2. R2 is allocated to P2 (Allocation edge: R2 -> P2).",
                "allocation": [[1, 0], [0, 1]],
                "requests": [[0, 0], [0, 0]],
                "available": [0, 0],
                "p1_state": "RUNNING",
                "p2_state": "RUNNING",
                "is_deadlocked": False,
                "edges": [
                    {"from": "R1", "to": "P1", "type": "allocation"},
                    {"from": "R2", "to": "P2", "type": "allocation"},
                ],
                "cycle": [],
                "blocked": [],
            }
        elif s == 3:
            return {
                "step": 3,
                "title": "Step 3/5 — P1 Requests R2 (Blocked)",
                "explanation": "P1 needs Mutex_R2 to complete, but R2 is held by P2. P1 is blocked waiting for R2 (Request edge: P1 -> R2).",
                "allocation": [[1, 0], [0, 1]],
                "requests": [[0, 1], [0, 0]],
                "available": [0, 0],
                "p1_state": "WAITING (BLOCKED on R2)",
                "p2_state": "RUNNING",
                "is_deadlocked": False,
                "edges": [
                    {"from": "R1", "to": "P1", "type": "allocation"},
                    {"from": "R2", "to": "P2", "type": "allocation"},
                    {"from": "P1", "to": "R2", "type": "request"},
                ],
                "cycle": [],
                "blocked": ["P1"],
            }
        elif s == 4:
            return {
                "step": 4,
                "title": "Step 4/5 — P2 Requests R1 (DEADLOCK FORMED)",
                "explanation": (
                    "P2 needs Mutex_R1 to complete, but R1 is held by P1. "
                    "P2 is blocked waiting for R1 (Request edge: P2 -> R1). "
                    "DEADLOCK: Circular wait condition formed: P1 -> R2 -> P2 -> R1 -> P1. "
                    "Neither process can proceed."
                ),
                "allocation": [[1, 0], [0, 1]],
                "requests": [[0, 1], [1, 0]],
                "available": [0, 0],
                "p1_state": "WAITING (BLOCKED)",
                "p2_state": "WAITING (BLOCKED)",
                "is_deadlocked": True,
                "edges": [
                    {"from": "R1", "to": "P1", "type": "allocation"},
                    {"from": "R2", "to": "P2", "type": "allocation"},
                    {"from": "P1", "to": "R2", "type": "request"},
                    {"from": "P2", "to": "R1", "type": "request"},
                ],
                "cycle": ["P1", "R2", "P2", "R1", "P1"],
                "blocked": ["P1", "P2"],
            }
        else:  # s == 5
            return {
                "step": 5,
                "title": "Step 5/5 — Deadlock Recovery (Process Cancellation)",
                "explanation": (
                    "Deadlock recovery initiated: Simulated preemption terminates P2, "
                    "reclaiming Mutex_R2. The circular wait cycle is broken. "
                    "P1 acquires R2, runs to completion, and releases all resources."
                ),
                "allocation": [[1, 1], [0, 0]],
                "requests": [[0, 0], [0, 0]],
                "available": [0, 0],
                "p1_state": "RUNNING -> COMPLETED",
                "p2_state": "TERMINATED (PREEMPTED)",
                "is_deadlocked": False,
                "edges": [
                    {"from": "R1", "to": "P1", "type": "allocation"},
                    {"from": "R2", "to": "P1", "type": "allocation"},
                ],
                "cycle": [],
                "blocked": [],
            }


class BankersAlgorithm:
    """
    Implements Dijkstra's Banker's Algorithm for deadlock avoidance.
    Computes Need matrix, evaluates system safety, and checks safety of incoming resource requests.
    """

    def __init__(self, scenario: DeadlockLabScenario):
        self.scenario = scenario
        self.n: int = scenario.num_processes
        self.m: int = scenario.num_resources
        self.resource_names: List[str] = scenario.resource_names
        self.available: List[int] = list(scenario.available)
        self.allocation: List[List[int]] = [list(r) for r in scenario.allocation]
        self.max_matrix: List[List[int]] = [list(r) for r in scenario.max_matrix]
        self.need: List[List[int]] = self._calculate_need_matrix()

    def _calculate_need_matrix(self) -> List[List[int]]:
        """Need[i][j] = Max[i][j] - Allocation[i][j]"""
        need = []
        for i in range(self.n):
            row = []
            for j in range(self.m):
                row.append(max(0, self.max_matrix[i][j] - self.allocation[i][j]))
            need.append(row)
        return need

    def update_custom_matrices(
        self,
        num_processes: int,
        num_resources: int,
        available: List[int],
        allocation: List[List[int]],
        max_matrix: List[List[int]],
        resource_names: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Validates user-provided matrices and updates Banker's algorithm instance.
        Enforces validation rules:
        - Non-negative integers
        - Matching dimensions
        - Allocation <= Max
        """
        if num_processes <= 0 or num_resources <= 0:
            return False, "Error: Processes and resources must be positive integers."

        if len(available) != num_resources:
            return False, f"Error: Available vector dimension ({len(available)}) does not match resource count ({num_resources})."

        if len(allocation) != num_processes or len(max_matrix) != num_processes:
            return False, "Error: Allocation and Max matrix row counts must match process count."

        for i in range(num_processes):
            if len(allocation[i]) != num_resources or len(max_matrix[i]) != num_resources:
                return False, f"Error: Row {i} column count must match resource count ({num_resources})."

            for j in range(num_resources):
                alloc_val = allocation[i][j]
                max_val = max_matrix[i][j]
                if alloc_val < 0 or max_val < 0 or available[j] < 0:
                    return False, "Error: All matrix entries and available resources must be non-negative integers."
                if alloc_val > max_val:
                    return False, f"Error: Allocation ({alloc_val}) exceeds Maximum claim ({max_val}) for P{i}, resource {j}."

        self.n = num_processes
        self.m = num_resources
        self.available = [int(v) for v in available]
        self.allocation = [[int(v) for v in r] for r in allocation]
        self.max_matrix = [[int(v) for v in r] for r in max_matrix]
        self.resource_names = resource_names or [f"Res_{j}" for j in range(num_resources)]
        self.need = self._calculate_need_matrix()
        return True, "Matrices updated and validated successfully."

    def get_safety_steps(self) -> Dict[str, Any]:
        """Returns step-by-step progress of the safety check including Work and Finish vectors."""
        work = list(self.available)
        finish = [False] * self.n
        steps = []
        safe_sequence = []

        steps.append({
            "step": 0,
            "work": list(work),
            "finish": list(finish),
            "action": f"Initial state. Available Work = {work}",
            "candidate": None,
        })

        while len(safe_sequence) < self.n:
            found = False
            for i in range(self.n):
                if not finish[i]:
                    can_allocate = all(self.need[i][j] <= work[j] for j in range(self.m))
                    if can_allocate:
                        for j in range(self.m):
                            work[j] += self.allocation[i][j]
                        finish[i] = True
                        safe_sequence.append(i)
                        found = True
                        steps.append({
                            "step": len(safe_sequence),
                            "work": list(work),
                            "finish": list(finish),
                            "action": f"P{i} satisfied (Need {self.need[i]} <= Work). Process runs to completion and frees Allocation {self.allocation[i]} -> New Work = {work}",
                            "candidate": i,
                        })
                        break
            if not found:
                break

        is_safe = (len(safe_sequence) == self.n)
        return {
            "is_safe": is_safe,
            "safe_sequence": safe_sequence,
            "safe_sequence_str": " -> ".join([f"P{p}" for p in safe_sequence]) if is_safe else "None",
            "steps": steps,
        }


    def is_safe_state(self) -> Tuple[bool, List[int], List[str]]:
        """
        Safety Algorithm:
        Returns (is_safe, safe_sequence, trace_steps).
        """
        work = list(self.available)
        finish = [False] * self.n
        safe_sequence: List[int] = []
        trace: List[str] = []

        trace.append(f"Initial Available Vector Work = {work}")

        while len(safe_sequence) < self.n:
            found = False
            for i in range(self.n):
                if not finish[i]:
                    # Check if Need[i] <= Work
                    can_allocate = all(self.need[i][j] <= work[j] for j in range(self.m))
                    if can_allocate:
                        for j in range(self.m):
                            work[j] += self.allocation[i][j]
                        finish[i] = True
                        safe_sequence.append(i)
                        found = True
                        trace.append(
                            f"Step {len(safe_sequence)}: P{i} satisfied (Need {self.need[i]} <= Work). "
                            f"Process completes and frees Allocation {self.allocation[i]} -> New Work = {work}"
                        )
                        break

            if not found:
                break

        is_safe = (len(safe_sequence) == self.n)
        if not is_safe:
            unfinished = [f"P{i}" for i in range(self.n) if not finish[i]]
            trace.append(f"Safety check FAILED: Cannot satisfy remaining processes {unfinished}. State is UNSAFE.")

        return is_safe, safe_sequence, trace

    def evaluate_request(
        self, process_id: int, request_vector: List[int]
    ) -> Tuple[bool, str, List[int]]:
        """
        Resource Request Algorithm:
        Checks if granting request_vector to process_id leaves the system in a safe state.
        """
        if process_id < 0 or process_id >= self.n:
            return False, f"Invalid process ID P{process_id}.", []

        # 1. Check if Request <= Need
        for j in range(self.m):
            if request_vector[j] > self.need[process_id][j]:
                return False, (
                    f"Error: Process P{process_id} exceeded maximum claim. "
                    f"Request {request_vector} > Need {self.need[process_id]} for resource '{self.resource_names[j]}'."
                ), []

        # 2. Check if Request <= Available
        for j in range(self.m):
            if request_vector[j] > self.available[j]:
                return False, (
                    f"Process P{process_id} must wait: Resources unavailable. "
                    f"Requested {request_vector[j]} of '{self.resource_names[j]}' but only {self.available[j]} available."
                ), []

        # 3. Pretend to allocate
        backup_avail = list(self.available)
        backup_alloc = [list(r) for r in self.allocation]
        backup_need = [list(r) for r in self.need]

        for j in range(self.m):
            self.available[j] -= request_vector[j]
            self.allocation[process_id][j] += request_vector[j]
            self.need[process_id][j] -= request_vector[j]

        # 4. Check safety
        is_safe, safe_seq, trace = self.is_safe_state()

        if is_safe:
            seq_str = " -> ".join([f"P{p}" for p in safe_seq])
            return True, f"Request GRANTED: System remains in SAFE state. Safe sequence: <{seq_str}>.", safe_seq
        else:
            # Roll back allocation
            self.available = backup_avail
            self.allocation = backup_alloc
            self.need = backup_need
            return False, (
                f"Request REJECTED by Banker's Avoidance Policy: Granting {request_vector} to P{process_id} "
                f"would lead to an UNSAFE state (risk of deadlock)."
            ), []


class DeadlockDetector:
    """
    Constructs the Wait-For Graph (WFG) and detects circular dependencies.
    """

    def __init__(self, num_processes: int, num_resources: int, allocation: List[List[int]], requests: List[List[int]]):
        self.n: int = num_processes
        self.m: int = num_resources
        self.allocation: List[List[int]] = allocation
        self.requests: List[List[int]] = requests

    def build_wait_for_graph(self) -> Dict[int, List[int]]:
        """
        Builds adjacency list for Wait-For Graph:
        P_i -> P_k exists if P_i requests a resource instance currently held by P_k.
        """
        wfg: Dict[int, List[int]] = {i: [] for i in range(self.n)}

        for i in range(self.n):
            for res_idx in range(self.m):
                if self.requests[i][res_idx] > 0:
                    # Find which process holds this resource
                    for k in range(self.n):
                        if k != i and self.allocation[k][res_idx] > 0:
                            if k not in wfg[i]:
                                wfg[i].append(k)
        return wfg

    def detect_cycles(self) -> Tuple[bool, List[List[int]]]:
        """
        Detects cycles in the directed Wait-For Graph using DFS.
        Returns (has_cycle, cycles_list).
        """
        wfg = self.build_wait_for_graph()
        visited = [0] * self.n  # 0=unvisited, 1=visiting, 2=visited
        cycles: List[List[int]] = []

        def dfs(node: int, path: List[int]):
            visited[node] = 1
            path.append(node)

            for neighbor in wfg.get(node, []):
                if visited[neighbor] == 1:
                    # Cycle detected
                    idx = path.index(neighbor)
                    cycle = path[idx:] + [neighbor]
                    cycles.append(cycle)
                elif visited[neighbor] == 0:
                    dfs(neighbor, path)

            path.pop()
            visited[node] = 2

        for i in range(self.n):
            if visited[i] == 0:
                dfs(i, [])

        return (len(cycles) > 0), cycles


class DeadlockRecoverySimulator:
    """
    Simulates recovery interventions:
    - Release held resource
    - Cancel process
    - Rollback
    """

    @staticmethod
    def cancel_process(
        process_id: int,
        available: List[int],
        allocation: List[List[int]],
        requests: List[List[int]],
    ) -> Tuple[List[int], List[List[int]], List[List[int]], str]:
        """Terminates process_id and returns all its allocated resources to available pool."""
        new_avail = list(available)
        new_alloc = [list(r) for r in allocation]
        new_reqs = [list(r) for r in requests]

        if 0 <= process_id < len(allocation):
            freed = list(new_alloc[process_id])
            for j in range(len(new_avail)):
                new_avail[j] += freed[j]
                new_alloc[process_id][j] = 0
                new_reqs[process_id][j] = 0
            return new_avail, new_alloc, new_reqs, f"Terminated P{process_id}. Reclaimed resources: {freed}."
        return new_avail, new_alloc, new_reqs, f"Invalid process P{process_id}."

    @staticmethod
    def release_resource(
        process_id: int,
        resource_idx: int,
        count: int,
        available: List[int],
        allocation: List[List[int]],
    ) -> Tuple[List[int], List[List[int]], str]:
        """Preempts resource from process_id without terminating the process."""
        new_avail = list(available)
        new_alloc = [list(r) for r in allocation]

        if 0 <= process_id < len(allocation) and 0 <= resource_idx < len(available):
            actual_release = min(count, new_alloc[process_id][resource_idx])
            new_alloc[process_id][resource_idx] -= actual_release
            new_avail[resource_idx] += actual_release
            return new_avail, new_alloc, f"Preempted {actual_release} instance(s) of resource {resource_idx} from P{process_id}."
        return new_avail, new_alloc, "Invalid preemption target."
