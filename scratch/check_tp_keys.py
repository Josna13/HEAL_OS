import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

from dashboard.deadlock_scenario import TwoProcessDeadlockScenario
tp = TwoProcessDeadlockScenario()
st = tp.step()
print("Keys in tp.step():", list(st.keys()))
print("st:", st)

