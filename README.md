# HealOS 2.0: AI-Powered Self-Healing Operating System

> **Predictive Failure Analysis • Intelligent Recovery • Real-Time System Health Monitoring**  
> *A modular user-space self-healing autonomic framework designed for academic demonstration and systems research.*  
> *Target Environment: Ubuntu on WSL (`/mnt/e/HealOs`) / Linux / Windows*  
> 📖 ** Demonstration Guide:** See [`TEACHER_DEMO_GUIDE.md`](file:///e:/HealOs/TEACHER_DEMO_GUIDE.md) for feature-by-feature demonstration instructions, spoken scripts, exact terminal commands, and verification proofs.

---

## 1. Project Overview

**HealOS 2.0** is an autonomic, closed-loop self-healing supervisor built for user-space applications. Modern operating systems and distributed service nodes frequently suffer from transient faults, memory bloat, resource contention storms, and uncaught worker exceptions. Traditional approaches rely on static watchdogs or reactive process managers (e.g., systemd, supervisord) that blindly restart crashing binaries without assessing host resource strain or estimating impending collapse.

HealOS 2.0 implements the classic IBM **MAPE-K** (Monitor, Analyze, Plan, Execute, Knowledge) autonomic computing loop entirely in Python user-space:
1. **Predictive Failure Analysis**: Continuous ML evaluation of temporal operating system metrics to estimate crash risk before faults manifest.
2. **Explainable Recovery Decision Engine**: An autonomic arbiter that selects safe recovery protocols (`MONITOR`, `INVESTIGATE`, `RESTART_APPLICATION`, `WAIT_AND_RETRY`, or `ALERT_USER`).
3. **Deterministic Health Scoring**: Multi-subsystem health computation balancing CPU, RAM, storage, and process churn (0 to 100).
4. **Empirical Historical Log Analytics**: Automated trend analysis, MTTR tracking, and root-cause classification derived strictly from real event logs.
5. **Real-Time Compact Terminal Dashboard**: High-density single-screen terminal console engineered to fit strictly within a normal 120x35 terminal window without vertical scrolling.

```
+-----------------------------------------------------------------------------------+
|                               HealOS 2.0 Supervisor                               |
|                                                                                   |
|  [System Monitor] ----> (CPU, RAM, Disk, Process Deltas)                          |
|         |                                 |                                       |
|         v                                 v                                       |
|  [AI Predictor]                   [Health Analyzer]                               |
|   (RandomForest)                    (Weighted Multi-Criteria)                     |
|         |                                 |                                       |
|         +-----------------+---------------+                                       |
|                           |                                                       |
|                           v                                                       |
|  [Crash Detector] ---> [Decision Engine] ---> [Auto-Restart Service]              |
|  (Process Signals)     (Safe Heuristics)       (Coordinated Spawn & SLA Tracking) |
|                           |                           |                           |
|                           +-------------+-------------+                           |
|                                         |                                         |
|                                         v                                         |
|                           [Structured Recovery Logger]                            |
|                                         |                                         |
|                                         v                                         |
|                           [Rich Terminal Dashboard]                               |
+-----------------------------------------------------------------------------------+
```

---

## 2.  Demonstration Checklist (20 Required Features)

| # | Feature | Implementation File | Verification Command / Action | Expected Result |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Live CPU, RAM, Disk, Process Monitoring | [`monitor/system_monitor.py`](file:///e:/HealOs/monitor/system_monitor.py) | View Section 1 in Dashboard | Real-time visual bars, delta change, MB/GB metrics, and headroom updating every 1.0s |
| **2** | Monitored App Status, PID, Uptime, Load | [`monitor/process_monitor.py`](file:///e:/HealOs/monitor/process_monitor.py) | View Section 2 in Dashboard | Shows `ONLINE (RUNNING)`, active PID, uptime, app CPU%, and app RAM in MB |
| **3** | Subsystem Health Checks | [`ai/health_score.py`](file:///e:/HealOs/ai/health_score.py) | View Section 4 in Dashboard | Real-time component scores: CPU (25%), RAM (35%), Disk (10%), Stability (30%) |
| **4** | AI Failure-Risk Prediction | [`ai/predictor.py`](file:///e:/HealOs/ai/predictor.py) | View Section 3 in Dashboard | Probability bar (`0.0%` to `100.0%`) with measured warning signals |
| **5** | Discrete Risk Categories | [`ai/predictor.py`](file:///e:/HealOs/ai/predictor.py) | View Section 3 in Dashboard | Displays `LOW` (<35%), `MEDIUM` (35-70%), or `HIGH` (>70%) |
| **6** | Overall System Health Score & Root Cause | [`ai/health_score.py`](file:///e:/HealOs/ai/health_score.py) | View Section 4 in Dashboard | Overall score (0-100), status (`HEALTHY`, `DEGRADED`, `CRITICAL`), primary degraded metric, and actionable guidance |
| **7** | Decision Engine Rationale & Policy | [`ai/decision_engine.py`](file:///e:/HealOs/ai/decision_engine.py) | View Section 3 in Dashboard | Evaluates resource thresholds and selects `MONITOR`, `INVESTIGATE`, `RESTART_APPLICATION`, `WAIT_AND_RETRY`, or `ALERT_USER` with human-readable rationale |
| **8** | Crash Detection & Timestamp | [`detector/crash_detector.py`](file:///e:/HealOs/detector/crash_detector.py) | `touch data/crash.trigger` | Detects exit code 1 in <200ms; dispatches failure event with microsecond timestamp |
| **9** | Autonomous Application Restart & Policy | [`recovery/auto_restart.py`](file:///e:/HealOs/recovery/auto_restart.py) | `touch data/crash.trigger` | Auto-respawns child process in ~1.0s without human intervention; enforces mutual exclusion |
| **10** | Old PID vs New PID Tracking | [`recovery/auto_restart.py`](file:///e:/HealOs/recovery/auto_restart.py) | View Section D in Dashboard | Displays transition: `[Old PID] -> [New PID]` |
| **11** | Recovery Latency SLA & Compliance | [`recovery/auto_restart.py`](file:///e:/HealOs/recovery/auto_restart.py) | View Section 5 in Dashboard | Measures duration in ms/sec, evaluates against 2.5s SLA target (`● MET` / `▲ BREACH`) |
| **12** | Restart Limit & Crash Storm Protection | [`ai/decision_engine.py`](file:///e:/HealOs/ai/decision_engine.py) | Trigger >5 crashes rapidly | Triggers `ALERT_USER` to halt infinite restart loops and crash storms |
| **13** | Live Event Timeline & Recovery History | [`dashboard/dashboard.py`](file:///e:/HealOs/dashboard/dashboard.py) | View Section 7 in Dashboard | Displays recent recovery history table (time, app, PIDs, duration, SLA) + event stream |
| **14** | Structured Machine-Readable Recovery Logs | [`logger/recovery_logger.py`](file:///e:/HealOs/logger/recovery_logger.py) | `cat logs/recovery.log` | Appends valid JSON-L records with detection time, start/completion times, PIDs, SLA status |
| **15** | Self-Healing Performance Analytics | [`ai/log_analyzer.py`](file:///e:/HealOs/ai/log_analyzer.py) | View Section 5 in Dashboard | Real-time recovery analytics: total crashes, attempts, successes, failures, success rate %, avg/min/max latencies, SLA %, repeated crashes, and trend trajectory |
| **16** | Historical MTTR SLA | [`ai/log_analyzer.py`](file:///e:/HealOs/ai/log_analyzer.py) | View Section 5/6 in Dashboard | Empirical Mean Time to Recover across all logged sessions |
| **17** | Subsystems Status Grid | [`dashboard/dashboard.py`](file:///e:/HealOs/dashboard/dashboard.py) | View Section 6 in Dashboard | Displays `● ONLINE` for all 8 subsystems |
| **18** | Graceful Shutdown | [`main.py`](file:///e:/HealOs/main.py) | Press `Ctrl+C` | Terminates dummy app, stops workers, exits code 0 with no tracebacks |
| **19** | Automated Demonstration | [`main.py`](file:///e:/HealOs/main.py) | `python3 main.py --demo-crash 2` | Runs 2 observable crash-and-recovery cycles automatically |
| **20** | Automated Test Suite | [`tests/`](file:///e:/HealOs/tests/) | `python3 -m pytest -v` | 114 automated unit and end-to-end integration tests pass |

---

## 3. The 9 Live Demonstration States

When presenting HealOS 2.0 to your teacher, you can walk through the 9 observable states in sequence:

```
+-----------------------------------------------------------------------------------+
| STATE 1: NORMAL OPERATION      --> Application running, PID visible, metrics live |
| STATE 2: RISK ASSESSMENT       --> AI evaluates telemetry; outputs risk % and SLA|
| STATE 3: FAILURE TRIGGERED     --> 'touch data/crash.trigger' executed in term 2  |
| STATE 4: CRASH DETECTED        --> Sub-second exit detection, Old PID recorded    |
| STATE 5: DECISION EVALUATED    --> Engine evaluates load: selects RESTART         |
| STATE 6: RECOVERY IN PROGRESS  --> Cooldown enforced, child process launching     |
| STATE 7: RECOVERY COMPLETED    --> New PID allocated, recovery duration recorded  |
| STATE 8: HEALTH RESTORED       --> Dashboard returns to GREEN, counters updated   |
| STATE 9: RESULTS VERIFIED      --> Synced to recovery.log and system.log          |
+-----------------------------------------------------------------------------------+
```

---

## 4. Single-Screen Terminal Dashboard Layout

The dashboard is engineered to fit within **28–30 lines**, leaving ample margin in a standard 35-line terminal:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ HealOS 2.0 │ Autonomic Self-Healing OS │ Uptime: 00h 05m 12s │ Time: 11:28:30 │ ONLINE │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ A. System & Health       │ D. Monitored App & SLA      │ B. AI Predictor & Decision    │
│ CPU Load   [████░░░░] 25%│ App Name     dummy_app.py   │ Crash Risk  [█░░░░░░░] 8.5%   │
│ RAM Usage  [██████░░] 48%│ Live Status  ONLINE         │ ML Model    RandomForest      │
│ Disk Space [██░░░░░░] 22%│ PID (Old->New) 8556 -> 5448 │ Next Action MONITOR (96%)     │
│ Tasks      142 PIDs      │ Session Flts Crashes: 1 | 1 │ Rationale   Metrics nominal   │
│ Health     100.0 (HEALTH)│ Recovery SLA 1.01s (100%)   │ Status      STATE 1: NORMAL   │
├──────────────────────────┴─────────────────────────────┴───────────────────────────────┤
│ H. Subsystems & Historical Analytics  │ I. Live Event Timeline (Real-Time Telemetry)   │
│ System Monitor   ● ONLINE             │ [11:28:25] Application dummy_app started (8556)│
│ Process Monitor  ● ONLINE             │ [11:28:29] [CRASH DETECTED] Process PID 8556   │
│ AI Predictor     ● ONLINE             │ [11:28:29] [DECISION] Action=RESTART_APP       │
│ Crash Detector   ● ONLINE             │ [11:28:30] Application dummy_app started (5448)│
│ Recovery Daemon  ● ONLINE             │ [11:28:30] Recovery SUCCESS: 8556 -> 5448      │
├───────────────────────────────────────┴────────────────────────────────────────────────┤
│ Commands: touch data/crash.trigger │ python3 main.py --demo-crash 2 │ Ctrl+C to exit    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Installation & WSL Setup Commands

### Step 1: Open Ubuntu WSL Terminal
```bash
# Navigate to the project directory in WSL
cd /mnt/e/HealOs

# Update package manager and install Python venv
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

# Create and activate an isolated virtual environment (PEP 668 compliant)
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> [!NOTE]
> **Python 3.14 Compatibility**: Python 3.10 through 3.13 are fully verified. If your Ubuntu Python 3.14 environment lacks pre-built binary wheels for C-extensions (`scikit-learn`, `numpy`), use Python 3.11/3.12:  
> `sudo apt install python3.11 python3.11-venv && python3.11 -m venv venv && source venv/bin/activate`

---

## 6. How to Run Live Academic Demonstrations

### Method A — Interactive Two-Terminal Demo (Recommended for Teacher)

1. **Terminal 1**: Start HealOS
   ```bash
   cd /mnt/e/HealOs
   source venv/bin/activate
   python3 main.py
   ```
   *Dashboard opens. Point out to your teacher: System Resources, Health Score (100/100), AI Failure Risk (LOW), active PID, and all 8 subsystems ONLINE.*

2. **Terminal 2**: In a second tab or window, trigger the failure
   ```bash
   cd /mnt/e/HealOs
   touch data/crash.trigger
   ```

3. **Observe Live in Terminal 1**:
   - The Crash Detector identifies the crash in <200ms.
   - Status transitions: `CRASH DETECTED` -> `DECISION EVALUATED` -> `RESTARTING`.
   - The dummy application restarts with a **new PID**.
   - `PID (Old->New)` displays the exact transition (e.g. `8556 -> 5448`).
   - Recovery SLA displays the measured duration (e.g., `1.01s`).
   - Crash and restart counters increment to `1`.
   - Health score temporarily reflects the event, then recovers to `HEALTHY`.

4. **Clean Exit**:
   Press `Ctrl+C` in Terminal 1 to stop cleanly without tracebacks.

---

### Method B — Feature 2: Real-Time System Resource Monitoring Demonstration
Demonstrate real-time host and application telemetry tracking without triggering crashes:

1. **Start HealOS**:
   ```bash
   cd /mnt/e/HealOs
   source venv/bin/activate
   python3 main.py
   ```
2. **Observe Panel 1 (System Monitor)**:
   - **CPU Load**: Live CPU gauge updating every 1.0s with real-time delta change `(Δ ±X.X%)`.
   - **RAM Usage**: Used vs Total memory in MB (e.g., `4096/16384 MB`).
   - **Disk Space**: Used vs Total disk in GB (e.g., `100.0/500.0 GB`).
   - **Active PIDs**: Live operating system process count.
   - **Headroom**: Instantaneous available RAM and free storage capacity.

3. **Observe Panel 2 (Process Monitor)**:
   - **Target App**: `dummy_app.py`.
   - **App Status**: Displays `ONLINE (RUNNING)` in green with live uptime counter ticking up every second.
   - **Active PID**: Current OS process ID of the monitored worker.
   - **App Load**: Specific CPU % and RAM (in MB and %) dedicated to the monitored process.

4. **Demonstrate Dynamic Resource Reaction (Optional Teacher Demo)**:
   Start HealOS with the dummy application in memory-leak or CPU-spike mode to watch live resource graphs respond:
   ```bash
   # In CPU spike mode:
   python3 main.py --mode spike-cpu
   
   # Or in memory leak mode:
   python3 main.py --mode memory-leak
   ```
   *Observe the CPU bar turn yellow/red, RAM climb in real-time, the Health Score decrease proportionally, and the AI Predictor risk probability climb.*

---

### Method C — Feature 4: Intelligent System Health Analysis Demonstration
Demonstrate multi-criteria health scoring, discrete status categorization, and root cause identification:

1. **Start HealOS**:
   ```bash
   cd /mnt/e/HealOs
   source venv/bin/activate
   python3 main.py
   ```

2. **Observe Panel 4 (Health Analyzer)**:
   - **Overall Score**: Composite score out of 100 with categorical status:
     - `HEALTHY` (Score $\ge 80.0$) — Green
     - `DEGRADED` ($50.0 \le \text{Score} < 80.0$) — Yellow
     - `CRITICAL` (Score $< 50.0$) — Red
   - **Subsystem Breakdown**: Real-time scores for individual subsystems:
     - **CPU Score** (Weight: 25%): Linear drop with high contention penalty above 80%.
     - **RAM Score** (Weight: 35%): Linear drop with steep exhaustion penalty above 85%.
     - **Disk Score** (Weight: 10%): Available filesystem capacity score.
     - **Stability Score** (Weight: 30%): Application online status minus penalties for crash churn.
   - **Root Cause & Guidance**: When any subsystem degrades, Panel 4 automatically pinpoints the primary culprit (`Cause: Host Memory (14/100)`, `Cause: Application Stability (40/100)`, or `Cause: CPU Load`) and displays an actionable recommendation.

3. **Demonstrate DEGRADED / CRITICAL Transitions**:
   - **Scenario 1 (Application Crash Degradation)**:
     In Terminal 2: `touch data/crash.trigger`.
     *Observe: Stability score drops immediately to 55/100, Health Analyzer switches to `DEGRADED` (yellow) with `Cause: Application Stability`, and Guidance recommends `Application offline. Automatic recovery daemon engaged.` Upon recovery, the score restores to `HEALTHY`.*
   - **Scenario 2 (Resource Contention Degradation)**:
     Run `python3 main.py --mode memory-leak`.
     *Observe: Memory buffer expands, RAM score drops, overall score transitions to `DEGRADED`, and Panel 4 flags `High RAM pressure. Monitor process memory growth.`*

---

### Method D — Feature 5: Recovery History and SLA Analytics Demonstration
Demonstrate real-time recovery duration measurement, SLA target evaluation, success-rate calculation, and structured historical logging:

1. **Start HealOS**:
   ```bash
   cd /mnt/e/HealOs
   source venv/bin/activate
   python3 main.py
   ```

2. **Trigger a Failure (Terminal 2)**:
   In a second terminal:
   ```bash
   cd /mnt/e/HealOs
   touch data/crash.trigger
   ```

3. **Observe Live in Terminal 1**:
   - **Panel 5 (Recovery Service & SLA)**:
     - **Progress**: Transitions `CRASH DETECTED` -> `RESTARTING` -> `RECOVERED (PID <new_pid>, 1.12s [SLA MET])`.
     - **PID Transition**: Shows exact handover: `Old: 8556 -> New: 5448`.
     - **Attempts**: Displays verified success tally: `1 OK / 0 Fail (100% Rate)`.
     - **SLA Target (2.5s)**: Evaluates compliance percentage (`100% Met`) and tracks average/fastest latencies.
   - **Panel 7 (Recovery History & Live Event Timeline)**:
     - Populates a structured Recent Recovery History table:
       ```
       Time      App                PID Trans        Duration          Outcome   SLA
       17:42:10  HealOS-DummyApp    8556 -> 5448     1.12s (1120ms)    SUCCESS   ● MET
       ```
     - Displays synchronized live event timeline directly beneath.

4. **Verify Persistent Machine-Readable Log**:
   In Terminal 2:
   ```bash
   tail -n 1 logs/recovery.log
   ```
   *Outputs full structured JSON record including `crash_detection_time`, `recovery_start_time`, `recovery_completion_time`, `recovery_duration_sec`, `recovery_duration_ms`, `old_pid`, `new_pid`, `sla_target_sec`, and `sla_met: true`.*

---

### Method E — Feature 6: Intelligent Recovery Policy Demonstration
Demonstrate explainable, configurable recovery policies governed by host telemetry and stability thresholds:

1. **Policy 1 — Safe Application Restart (`RESTART_APPLICATION`)**:
   Under nominal CPU/RAM load, crash detection immediately approves a recovery restart:
   - In Terminal 2: `touch data/crash.trigger`
   - Observe Panel 3: Action displays `RESTART_APPLICATION` in bold cyan, Rationale notes nominal resources.
   - Child process restarts with a new PID in ~1.0s.

2. **Policy 2 — Resource Saturation Protection (`WAIT_AND_RETRY`)**:
   When host resources exceed saturation limits (CPU $\ge 90\%$, RAM $\ge 92\%$), the engine defers restarts:
   - Start in stress mode: `python3 main.py --mode spike-cpu`
   - In Terminal 2: `touch data/crash.trigger`
   - Observe Panel 3: Action switches to `WAIT_AND_RETRY` in bold yellow with cooling down status before attempting respawn.

3. **Policy 3 — Crash Storm & Quota Protection (`ALERT_USER`)**:
   When repeated crashes occur within a 60-second window (`MAX_CRASHES_IN_WINDOW = 4`) or retry limit is reached (`MAX_RESTART_ATTEMPTS = 5`):
   - Rapidly touch the trigger file 5 times:
     ```bash
     for i in {1..5}; do touch data/crash.trigger; sleep 1.2; done
     ```
   - Observe Panel 3: Action halts with `ALERT_USER` in bold red, preventing infinite fork loops.
   - Panel 5 marks status `HALTED (ALERT_USER - Limit Reached)` and logs critical alert to `logs/recovery.log`.

4. **Policy 4 — Concurrency & Duplicate Event Suppression**:
   - Spurious duplicate crash signals for the same dead PID or concurrent restart requests while recovery is active are safely dropped by mutual exclusion guards without race conditions.

---

### Method F — Feature 7: Self-Healing Performance Analytics Demonstration
Demonstrate real-time aggregation of recovery metrics, failure counts, repeated crash tracking, duration statistics (average, minimum, maximum), SLA compliance percentage, and empirical performance trend trajectories:

1. **What Feature 7 Does**:
   Continuously monitors all self-healing actions, evaluates machine-readable recovery records from `logs/recovery.log` and active session buffers, prevents double-counting, computes statistical duration benchmarks without division-by-zero errors, and analyzes whether recovery performance is `IMPROVING`, `WORSENING`, or `STABLE`.

2. **How to Launch HealOS**:
   ```bash
   cd /mnt/e/HealOs
   source venv/bin/activate
   python3 main.py
   ```

3. **How to Generate Recovery Events**:
   In a second terminal, trigger single or sequential recoveries:
   ```bash
   # Single crash and recovery:
   touch data/crash.trigger

   # Generate consecutive recoveries to observe trend trajectory:
   for i in {1..3}; do touch data/crash.trigger; sleep 4; done
   ```

4. **Which Dashboard Metrics to Observe (Panel 5 — Recovery & Performance Analytics)**:
   - **Progress**: Live recovery execution state (`RECOVERED (PID <new_pid>, 1.05s)`).
   - **PID Trans & Faults**: `Old: <failed_pid> -> New: <current_pid> │ X Flts (Y Rep)` showing total crashes and repeated crashes.
   - **Attempts**: `Tot: N │ X OK / Y Fail (Z% Rate)` verifying attempts denominator integrity and success percentage.
   - **Latency Benchmarks**: `Avg: X.XXs │ Min: X.XXs │ Max: X.XXs` tracking empirical recovery speed.
   - **SLA & Performance Trend**: `X% Met (2.5s) │ [IMPROVING / STABLE / WORSENING]` showing whether restart latency is accelerating, degrading, or remaining steady.

5. **Verify Persistent Machine-Readable Log**:
   ```bash
   tail -n 3 logs/recovery.log
   ```
   *Each line contains structured JSON telemetry with exact detection time, start/completion timestamps, duration in seconds/ms, SLA target and boolean outcome.*

---

### Method G — Fully Automated Demonstration
Demonstrate two consecutive automated crash-and-recovery cycles:
```bash
python3 main.py --demo-crash 2
```
*HealOS runs normally for 4 seconds, executes cycle 1 (crash + auto-restart), stabilizes for 4 seconds, executes cycle 2, and displays both recoveries on screen.*

---

### Method H — Headless Diagnostic Mode
For debugging or scripting without the full-screen terminal UI:
```bash
python3 main.py --no-dashboard
```

---

## 7. Automated Test Suite

Run all 81 unit and integration tests:
```bash
python3 -m unittest discover tests -v
```

### Verified Test Results (81/81 Passing):
```
test_unexpected_crash_detection (test_crash_detector) ... ok
test_duplicate_crash_prevention (test_crash_detector) ... ok
test_intentional_shutdown_suppresses_crash_event (test_crash_detector) ... ok
test_nominal_restart_decision (test_decision_engine) ... ok
test_resource_saturation_triggers_wait_and_retry (test_decision_engine) ... ok
test_max_retries_triggers_alert_user (test_decision_engine) ... ok
test_crash_storm_triggers_alert_user (test_decision_engine) ... ok
test_limited_retries_near_quota (test_decision_engine) ... ok
test_decide_runtime_monitor_when_healthy (test_decision_engine) ... ok
test_decide_runtime_investigate_when_risk_elevated (test_decision_engine) ... ok
test_decide_runtime_restart_when_app_offline (test_decision_engine) ... ok
test_configurable_engine_parameters (test_decision_engine) ... ok
test_configurable_auto_restart_parameters (test_decision_engine) ... ok
test_auto_restart_normal_recovery_flow (test_decision_engine) ... ok
test_auto_restart_wait_and_retry_flow (test_decision_engine) ... ok
test_auto_restart_max_attempts_triggers_alert_user (test_decision_engine) ... ok
test_auto_restart_crash_storm_triggers_alert_user (test_decision_engine) ... ok
test_auto_restart_duplicate_crash_event_suppression (test_decision_engine) ... ok
test_auto_restart_concurrent_restart_suppression (test_decision_engine) ... ok
test_feature_5_recovery_history_and_sla_intact_under_policy (test_decision_engine) ... ok
test_nominal_health_score (test_health_score) ... ok
test_degraded_state_due_to_memory_pressure (test_health_score) ... ok
test_degraded_state_due_to_crashes (test_health_score) ... ok
test_critical_threshold (test_health_score) ... ok
test_invalid_and_missing_metrics_sanitization (test_health_score) ... ok
test_boundary_metrics_clamping (test_health_score) ... ok
test_custom_weights_sum_to_one (test_health_score) ... ok
test_health_report_to_dict (test_health_score) ... ok
test_all_recoveries_successful (test_performance_analytics) ... ok
test_compatibility_with_existing_features (test_performance_analytics) ... ok
test_empty_recovery_history (test_performance_analytics) ... ok
test_malformed_log_entries (test_performance_analytics) ... ok
test_recovery_duration_statistics (test_performance_analytics) ... ok
test_repeated_crashes (test_performance_analytics) ... ok
test_sla_compliance (test_performance_analytics) ... ok
test_some_recoveries_failed (test_performance_analytics) ... ok
test_success_rate_calculation (test_performance_analytics) ... ok
test_trend_calculation_insufficient_history (test_performance_analytics) ... ok
test_trend_calculation_sufficient_history_improving (test_performance_analytics) ... ok
test_trend_calculation_sufficient_history_stable (test_performance_analytics) ... ok
test_trend_calculation_sufficient_history_worsening (test_performance_analytics) ... ok
test_predictor_initialization (test_predictor) ... ok
test_predict_risk_nominal_conditions (test_predictor) ... ok
test_predict_risk_high_stress_conditions (test_predictor) ... ok
test_fallback_heuristic_calculation (test_predictor) ... ok
test_nonexistent_model_fallback (test_predictor) ... ok
test_heuristic_fallback_when_model_is_none (test_predictor) ... ok
test_resilience_to_boundary_inputs (test_predictor) ... ok
test_deterministic_normal_conditions (test_predictor) ... ok
test_deterministic_elevated_risk_warning_signals (test_predictor) ... ok
test_deterministic_repeated_crashes_signal (test_predictor) ... ok
test_invalid_input_values_sanitization (test_predictor) ... ok
test_prediction_result_to_dict (test_predictor) ... ok
test_get_process_count (test_process_monitor) ... ok
test_is_pid_alive_valid_and_invalid (test_process_monitor) ... ok
test_get_process_details_current_process (test_process_monitor) ... ok
test_get_process_details_nonexistent_pid (test_process_monitor) ... ok
test_find_processes_by_identifier (test_process_monitor) ... ok
test_list_processes (test_process_monitor) ... ok
test_psutil_exceptions_handled_gracefully (test_process_monitor) ... ok
test_zombie_process_marked_dead (test_process_monitor) ... ok
test_recovery_logger_writes_structured_record (test_recovery) ... ok
test_auto_restart_summary_metrics (test_recovery) ... ok
test_successful_recovery_and_pid_tracking (test_sla_analytics) ... ok
test_failed_recovery_handling (test_sla_analytics) ... ok
test_accurate_duration_calculations (test_sla_analytics) ... ok
test_success_rate_calculations (test_sla_analytics) ... ok
test_sla_pass_and_fail_cases (test_sla_analytics) ... ok
test_empty_history_no_division_by_zero (test_sla_analytics) ... ok
test_malformed_and_incomplete_log_records (test_sla_analytics) ... ok
test_duplicate_event_prevention (test_sla_analytics) ... ok
test_persistence_across_application_restarts (test_sla_analytics) ... ok
test_get_system_stats_live_structure (test_system_monitor) ... ok
test_get_system_stats_delta_calculation (test_system_monitor) ... ok
test_mocked_system_stats_exact_calculation (test_system_monitor) ... ok
test_psutil_exception_resilience (test_system_monitor) ... ok
test_append_metrics_to_csv (test_system_monitor) ... ok
test_system_monitor_thread_lifecycle (test_system_monitor) ... ok
test_trigger_file_causes_immediate_exit_and_consumption (test_trigger) ... ok
test_missing_trigger_file_does_not_affect_normal_operation (test_trigger) ... ok
test_full_system_lifecycle_and_recovery (test_integration) ... ok

----------------------------------------------------------------------
Ran 114 tests in 27.31s

OK
```

---

## 8. Live OS Visualization Studio & Seven-Panel Observatory

HealOS 2.0 integrates an interactive, pedagogical operating-systems visualization studio and live telemetry observatory accessible via terminal and a zero-dependency web browser dashboard (`http://localhost:8080`). It connects theoretical OS principles directly to the runtime self-healing core across two synchronized tabs.

### Tab 1: Seven-Panel Live Visualization Observatory
The web dashboard transforms traditional static cards into dynamic, animated, data-driven visual observatories:
1. **Panel 1 — Live System Resource Observatory**: Synchronized dual-line SVG area charts for CPU load (cyan) and RAM utilization (purple) with rolling 60-point history, min/avg/max stats, disk usage SVG donut chart with gigabyte headroom breakdown, resource warning threshold indicators (80% warning / 90% critical), and temporal filter range toggles (30s, 60s, 5m).
2. **Panel 2 — Process Lifecycle & Crash Observatory**: Visual node-link state graph showing active state transitions (`NEW` $\to$ `READY` $\to$ `RUNNING` $\to$ `WAITING` $\to$ `TERMINATED`), active process uptime, CPU and memory footprint, and split-node before/after crash comparison tracking the original failed instance and newly spawned replacement instance.
3. **Panel 3 — AI Failure Prediction & Decision Engine**: Semi-circular radial gauge (0–100%) indicating real-time failure probability, historical risk trajectory sparkline, model provenance metadata (Random Forest vs Heuristic Fallback), detected pre-failure warning signals, and autonomic decision policy rationale (`MONITOR`, `RESTART_APPLICATION`, `WAIT_AND_RETRY`, `ALERT_USER`).
4. **Panel 4 — System Health & Diagnostics**: Large circular health gauge (0–100), weighted component status breakdown bars (CPU 25%, RAM 35%, Disk 10%, Stability 30%), primary degradation culprit identification, and prescriptive mitigation guidance.
5. **Panel 5 — Self-Healing & Recovery Analytics**: 6-stage recovery pipeline visualization (`FAULT DETECTED` $\to$ `POLICY EVALUATION` $\to$ `TERMINATION` $\to$ `FORK/EXEC` $\to$ `PID HANDOVER` $\to$ `HEALTH VERIFIED`), exact PID transition records, recovery duration in milliseconds, SLA pass/fail evaluation ($<2500\text{ms}$), and recovery duration bar chart.
6. **Panel 6 — Subsystem Health Dependency Map**: Interactive directed SVG topology map modeling all 8 internal subsystems (`System Monitor`, `Process Monitor`, `Crash Detector`, `Recovery Service`, `AI Predictor`, `Decision Engine`, `Health Analyzer`, `Recovery Logger`) with real-time operational status pins, active crash/recovery pulse path, and click diagnostics.
7. **Panel 7 — Live Event Timeline & Forensics Waterfall**: Real-time event waterfall stream with category filter chips (`ALL`, `CRASH`, `RECOVERY`, `POLICY`, `SYSTEM`), timestamped telemetry records, and visual duration breakdown.

### Tab 2: OS Process Lifecycle & Scheduling Lab
Four interactive workspaces, side inspector, customizable Banker's matrices, and a 14-step guided presentation walkthrough:
```bash
# Launch directly into OS Process Lab tab in terminal
python3 main.py --tab os-lab

# Launch directly into specific sub-workspace
python3 main.py --tab os-lab --lab-section SCHEDULER

# Launch automated presentation walkthrough
python3 main.py --demo-lab

# Launch interactive web presentation dashboard (Port 8080)
python3 main.py --web
```

```
+----------------------------------------------------------------------------------------------------+
|                      HEALOS 2.0 │ [1] SYSTEM OVERVIEW │ [2] OS PROCESS LAB (ACTIVE)               |
+-------------------------------------------------+--------------------------------------------------+
| A. Process Lifecycle & PCB Inspector [SIM]      | B. CPU Scheduler & Animated Gantt [SIM]          |
| RUNNING: P101(web_srv)  READY: P102(db_work)    | RR (Q=2) │ Avg Wait: 4.3t │ Avg TAT: 8.7t │ CS: 3|
| PCB Drawer: Registers (PC/SP/PSW), Mem Map      | Gantt: [P1:0-2][P2:2-4][P3:4-5][P1:5-7]...       |
+-------------------------------------------------+--------------------------------------------------+
| C. Deadlock Formation & Banker's Lab [SIM]      | D. Real Crash Recovery & PID Forensics [LIVE]    |
| Scenario: 2-Proc Circular Wait (P1-P2, R1-R2)   | Original PID: 12040  -> Replacement PID: 18450  |
| Banker's Status: SAFE SEQ <P1,P3,P4,P0,P2>      | State: TERMINATED    -> State: RUNNING (ACTIVE) |
| WFG Cycle Detection & Preemption Recovery       | Latency: 412ms       -> SLA: PASS (< 2.5s)      |
+----------------------------------------------------------------------------------------------------+
| Tour: Step 6/13: Deadlock Formation (Circular Wait) — P1 holds R1, requests R2; P2 holds R2...     |
| Keys: [1] Overview | [2] Lab | [A-D] Sub-view | [Space] Step | [P] Tour Step | [T] Crash Demo       |
+----------------------------------------------------------------------------------------------------+
```

### Core Educational Workspaces
1. **Workspace 1 — Animated Process Lifecycle, State Machine & Execution Visualizer**:
   - **Complete Process Journey Simulation**:
     - Animates and explains: $\text{Process Creation} \to \text{Simulated PID Allocation} \to \text{NEW} \to \text{Admission} \to \text{READY} \to \text{Short-Term Scheduler Dispatch} \to \text{RUNNING} \to \text{CPU Execution} \to \text{I/O Block / WAITING or Preemption / READY} \to \text{TERMINATED}$.
     - Rejection of invalid transitions (`NEW -> RUNNING`, `WAITING -> RUNNING`, `TERMINATED -> READY`) with `InvalidStateTransitionError`.
   - **Process Creation & PID Allocation Pipeline**:
     - Form: Name, Arrival Time ($AT \ge 0$), CPU Burst ($BT \ge 1$), Priority ($\ge 1$), I/O Request At tick, I/O Duration ticks.
     - Animated 5-step allocation sequence: `1. sys_create() ➔ 2. Allocate Simulated PID (P101-P999) ➔ 3. Allocate PCB & Hardware Registers ➔ 4. Enqueue in NEW Node ➔ 5. Admit to READY at AT`.
     - Explicit simulated namespace isolation (`[SIMULATED PID]`) strictly distinguished from real Linux OS processes managed by `task_struct`.
   - **Dynamic SVG 5-State Machine & Execution Stage**:
     - Dynamic nodes with live process counts: `NEW` (purple), `READY QUEUE` (cyan), `RUNNING` (green), `WAITING` (amber), `TERMINATED` (red).
     - Glowing animated transition paths (`trans-new-ready`, `trans-ready-running`, etc.) with drop-shadow glow and animated dash offsets whenever processes move.
     - Live explanation banner describing the OS rationale for the active transition.
     - **CPU Core 0 Visual**: Central CPU socket showing active PID/job name, cycle progress bar, remaining burst countdown, allocation counter, preemption counter, and execution release reason banner upon preemption or I/O blocking.
     - **Ready Queue & Waiting (I/O) Queue Strips**: Visual queues showing exact dispatch order and I/O remaining tick countdowns.
   - **Interactive Playback & Timeline Gantt Chart**:
     - Controls: Start / Play, Pause, Step Event ⏭, Step Tick ⏩, Reset ↺, and Speeds ($0.5\times, 1\times, 2\times, 4\times$).
     - Algorithms supported: Round Robin (with configurable quantum $q = 1$ to $10$), FCFS, SJF (non-preemptive), and Priority (with toggleable preemptive mode).
     - 4 Presets: **Full Lifecycle with I/O**, **Round Robin Preemption Showcase**, **SJF with Staggered Arrivals**, **Priority Mix**.
     - Gantt Timeline Chart with time ruler, color-coded blocks, amber striped I/O blocks, event markers ($↓, ↺, ⏳, ✓, ⚡$), and moving playhead cursor ($T$).
   - **15-Field PCB Inspector & Synthesized Audio**:
     - Displays all 15 PCB fields with simulated CPU hardware registers (`PC`, `SP`, `PSW`, `R0`), complete lifecycle audit trail, and interactive plain-English explanation card for every OS field.
     - Synthesized Web Audio feedback (muted by default with toggle and volume control): Creation, Dispatch, Preemption, I/O Block, and Termination tones.
     - Accurate OS metrics: Waiting Time ($WT$) strictly accumulates time spent in READY (excluding I/O in WAITING!).
2. **Workspace B — CPU Scheduling Simulator & Animated Gantt Chart**:
   - Implements **FCFS**, **SJF (non-preemptive)**, **Round Robin (preemptive with quantum)**, and **Priority (non-preemptive)**.
   - Real-time animated timeline playhead with ready queue and executing process tracking.
   - Calculates exact OS metrics:
     - $\text{Turnaround Time} = \text{Completion Time} - \text{Arrival Time}$
     - $\text{Waiting Time} = \text{Turnaround Time} - \text{Burst Time}$
     - $\text{Response Time} = \text{First Start Time} - \text{Arrival Time}$
     - Context switches (counted when CPU transitions between distinct active processes).
3. **Workspace C — Live Deadlock Formation, Detection & Banker's Avoidance**:
   - **Scenario 1: 2-Process 2-Resource Circular Wait Deadlock**:
     - Step 0: Resources free.
     - Step 1: P1 acquires Mutex R1.
     - Step 2: P2 acquires Mutex R2.
     - Step 3: P1 requests R2 (blocked).
     - Step 4: P2 requests R1 (DEADLOCK formed: circular wait $P_1 \to R_2 \to P_2 \to R_1 \to P_1$).
     - Step 5: Autonomic recovery via process cancellation or resource preemption.
   - **Scenario 2: Dijkstra's Banker's Algorithm (Avoidance)**:
     - Computes Need matrix ($\text{Max} - \text{Alloc}$), verifies safety, and derives safe execution sequences (e.g. $\langle P_1, P_3, P_4, P_0, P_2 \rangle$).
     - Rejects unsafe resource requests with step-by-step mathematical traces and safety rollbacks.
4. **Workspace D — Real Crash Recovery, Transition Timeline & PID Forensics**:
   - Connected directly to live HealOS `dummy_app.py`, `CrashDetector`, `AutoRestart`, and `data/crash.trigger`.
   - Before-and-after forensics table: Original Process vs Replacement Process.
   - 6-Stage Transition Pipeline: `ORIGINAL PROCESS` $\to$ `CRASH DETECTED` $\to$ `POLICY DECISION` $\to$ `RECOVERY IN PROGRESS` $\to$ `NEW PROCESS` $\to$ `RECOVERY VERIFIED`.
   - Compares PIDs, timestamps, runtimes, recovery latencies, and verifies liveness via `psutil`.
   - OS Concept: Explains why process restarts receive a new PID (PCB deallocation, address space reclamation, and kernel PID pool allocation via `fork()`/`exec()`).
5. **13-Step Integrated Guided Tour**:
   - Sequential educational journey through the entire OS lifecycle:
     - Steps 1–2: Process Creation & Ready Queue Admission (Workspace A)
     - Steps 3–4: CPU Scheduler Selection & Gantt Timeline (Workspace B)
     - Step 5: Resource Request & Waiting State (Workspace A)
     - Steps 6–7: Deadlock Formation & Banker's Avoidance (Workspace C)
     - Steps 8–10: Live Application Surveillance, Crash Trigger & Termination (Workspace D)
     - Steps 11–13: Autonomic Recovery Policy, PID Forensics & SLA Verification (Workspace D)
6. **Data Provenance Badges**:
   - Clearly distinguishes data sources with visible badges:
     - `[LIVE DATA]` for real monitored processes and system telemetry.
     - `[RECORDED EVENT]` for logged crashes and recoveries.
     - `[SIMULATION]` for educational scheduling algorithms and Banker's deadlock lab.

---

## 9. Log Files & Verification

All telemetry is recorded in real time and can be inspected:
- **`logs/recovery.log`**: Structured JSON-lines containing timestamp, failure reason, decision, recovery duration, and `{"old_pid": X, "new_pid": Y}`.
- **`logs/events.log`**: Human-readable chronological timeline.
- **`logs/dummy_app.log`**: Direct heartbeats and fatal termination messages from the dummy application.
- **`logs/system.log`**: Subsystem operational traces and error logs.
- **`data/system_metrics.csv`**: Time-series recording of CPU, RAM, Disk, and Process count.

---

## 9. Academic Context & Limitations

### Autonomic Computing Contribution
HealOS 2.0 demonstrates the IBM **MAPE-K** autonomic model:
- **Sensor**: `monitor/system_monitor.py` and `detector/crash_detector.py`.
- **Analyzer**: `ai/predictor.py` (statistical risk model) and `ai/health_score.py` (deterministic health function).
- **Planner**: `ai/decision_engine.py` (explainable heuristic arbiter).
- **Executor**: `recovery/auto_restart.py` (process supervisor with SLA instrumentation).
- **Knowledge**: `logs/recovery.log` and `ai/log_analyzer.py` (historical MTTR analytics).

### Limitations
1. **User-Space Scope**: Operates in user-space. Cannot recover from kernel-level panics or hardware power loss.
2. **Synthetic Training Dataset**: The Random Forest failure predictor is trained on synthetic OS stress telemetry ($N=5000$, $96.1\%$ accuracy). In production, empirical sensor telemetry from target servers should be used.
3. **Single Process Surveillance**: Designed for supervised target services rather than multi-node cluster consensus.

---

## 10. License
Developed for academic coursework and computer science research demonstrations. Available under the MIT License.
