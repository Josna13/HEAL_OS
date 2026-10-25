import sys
sys.path.insert(0, '.')
from dashboard.deadlock_lab import TwoProcessDeadlockSimulation

tp = TwoProcessDeadlockSimulation()
st = tp.step()
print("Keys:", list(st.keys()))
print("st:", st)
