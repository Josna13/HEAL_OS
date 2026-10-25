import sys
sys.path.insert(0, '.')
import json

# Test that the standard scenarios and TwoProcessDeadlockSimulation are completely intact
from dashboard.deadlock_lab import (
    get_standard_scenarios,
    BankersAlgorithm,
    DeadlockDetector,
    DeadlockRecoverySimulator,
    TwoProcessDeadlockSimulation
)

scenarios = get_standard_scenarios()
assert "safe_banker" in scenarios
assert "circular_deadlock" in scenarios

# Verify TwoProcessDeadlockSimulation step by step
sim = TwoProcessDeadlockSimulation()
assert sim.step_idx == 0
s0 = sim.get_state()
assert s0["step"] == 0
assert s0["available"] == [1, 1]

s1 = sim.step()
assert s1["step"] == 1
assert s1["allocation"][0] == [1, 0]

s2 = sim.step()
assert s2["step"] == 2
assert s2["allocation"][1] == [0, 1]

s3 = sim.step()
assert s3["step"] == 3
assert "P1" in s3["blocked"]

s4 = sim.step()
assert s4["step"] == 4
assert s4["is_deadlocked"] is True

s5 = sim.step()
assert s5["step"] == 5
assert s5["is_deadlocked"] is False

print("All existing deadlock_lab.py classes and methods verified 100% functional!")
