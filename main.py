"""
HealOS 2.0 - Autonomous Self-Healing Operating System Orchestrator
Master Entry Point:
Single-command invocation starts the complete ecosystem:
- System Resource Monitoring
- Process Surveillance
- Machine Learning Failure Predictor
- Heuristic Health Analyzer
- Crash Detector
- AI Recovery Decision Engine
- Auto-Restart Daemon
- Real-Time Compact Terminal Dashboard

Usage:
    python3 main.py
    python3 main.py --train            # Train AI model prior to startup
    python3 main.py --demo-crash 2     # Run 2 automated crash-and-recovery demonstrations
    python3 main.py --no-dashboard     # Run headless with diagnostic console output
"""

import argparse
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    init_directories,
    MODEL_FILE,
    DUMMY_APP_SCRIPT,
    CRASH_TRIGGER_FILE,
    SYSTEM_MONITOR_INTERVAL,
    CRASH_DETECTOR_INTERVAL,
    DASHBOARD_REFRESH_INTERVAL,
)
from logger.healos_logger import get_system_logger, get_error_logger, log_event
from monitor.system_monitor import SystemMonitor, get_system_stats
from monitor.process_monitor import ProcessMonitor
from detector.crash_detector import CrashDetector, CrashEvent
from ai.predictor import FailurePredictor
from ai.decision_engine import RecoveryDecisionEngine
from ai.health_score import HealthAnalyzer
from ai.log_analyzer import LogAnalyzer
from ai.train_model import train_failure_model
from recovery.auto_restart import AutoRestart
from dashboard.dashboard import AppState, TerminalDashboard


class HealOSOrchestrator:
    """
    Coordinates lifecycle, event wiring, and graceful shutdown of HealOS.
    """

    def __init__(
        self,
        auto_train: bool = False,
        no_dashboard: bool = False,
        demo_crash_count: int = 0,
        dummy_mode: str = "normal",
        initial_tab: str = "overview",
        lab_section: str = "ALL",
        demo_lab: bool = False,
        enable_web: bool = False,
        web_port: int = 8080,
    ):
        self.auto_train = auto_train
        self.no_dashboard = no_dashboard
        self.demo_crash_count = demo_crash_count
        self.dummy_mode = dummy_mode
        self.initial_tab = initial_tab
        self.lab_section = lab_section
        self.demo_lab = demo_lab
        self.enable_web = enable_web
        self.web_port = web_port

        self.logger = get_system_logger()
        self.state = AppState()
        self._shutdown_event = threading.Event()
        self._is_shutting_down = False

        # Subsystems
        self.system_monitor: SystemMonitor = None
        self.process_monitor: ProcessMonitor = None
        self.crash_detector: CrashDetector = None
        self.predictor: FailurePredictor = None
        self.health_analyzer: HealthAnalyzer = None
        self.log_analyzer: LogAnalyzer = None
        self.decision_engine: RecoveryDecisionEngine = None
        self.recovery_service: AutoRestart = None
        self.dashboard: TerminalDashboard = None
        self.web_server = None

    def initialize_subsystems(self) -> None:
        """Sequential initialization following architectural stages."""
        self.logger.info("==================================================")
        self.logger.info(" HealOS 2.0 Orchestrator Initializing")
        self.logger.info("==================================================")

        # 1. Ensure runtime directories exist
        init_directories()

        # 2. Check or train ML model
        if self.auto_train or not MODEL_FILE.exists():
            self.logger.info("AI model absent or auto-train requested. Training now...")
            self.state.add_event("Training AI Predictive Failure Model...")
            try:
                train_failure_model()
                self.state.add_event("AI model training complete.")
            except Exception as e:
                get_error_logger().error(f"Failed to auto-train model: {e}")
                self.state.add_event(f"[WARNING] Model training failed: {e}")

        # 3. Instantiate AI & Analysis Subsystems
        self.predictor = FailurePredictor(model_path=MODEL_FILE)
        self.health_analyzer = HealthAnalyzer()
        self.log_analyzer = LogAnalyzer()
        self.decision_engine = RecoveryDecisionEngine()

        # Update initial log analysis in state
        initial_log_report = self.log_analyzer.analyze()
        self.state.update_log_analysis(initial_log_report)

        # 4. Instantiate Crash Detector
        self.crash_detector = CrashDetector(
            interval=CRASH_DETECTOR_INTERVAL,
            on_crash_callback=self._on_crash_detected,
        )

        # 5. Instantiate Recovery Controller
        dummy_args = ["--mode", self.dummy_mode]
        self.recovery_service = AutoRestart(
            app_script=DUMMY_APP_SCRIPT,
            app_args=dummy_args,
            crash_detector=self.crash_detector,
            decision_engine=self.decision_engine,
        )

        # 6. Instantiate System Monitor
        self.system_monitor = SystemMonitor(interval=SYSTEM_MONITOR_INTERVAL)

        # 7. Instantiate Process Monitor
        self.process_monitor = ProcessMonitor()

        # 8. Start Monitored Application
        self.state.add_event(f"Starting target application '{DUMMY_APP_SCRIPT.name}'...")
        started = self.recovery_service.start_application()
        if not started:
            self.logger.error("Failed to start target application during initial boot.")
            self.state.set_module_status("Recovery Daemon", "ERROR")

        # 9. Start Background Threads
        self.system_monitor.start()
        self.crash_detector.start()

        # 10. Instantiate Terminal Dashboard
        if not self.no_dashboard:
            self.dashboard = TerminalDashboard(
                self.state,
                refresh_interval=DASHBOARD_REFRESH_INTERVAL,
                initial_tab=self.initial_tab,
                initial_section=self.lab_section,
            )
            self.dashboard.start()
        else:
            self.logger.info("Running in headless mode (--no-dashboard specified).")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] HealOS 2.0 running in headless mode. Subsystems ONLINE.", flush=True)

        # 11. Optional Web Dashboard Server
        if self.enable_web:
            try:
                from dashboard.web_server import WebDashboardServer
                self.web_server = WebDashboardServer(orchestrator_ref=self, port=self.web_port)
                self.web_server.start()
                self.logger.info(f"Interactive Web Dashboard active at http://localhost:{self.web_port}")
                self.state.add_event(f"Web Dashboard active at http://localhost:{self.web_port}")
            except Exception as e:
                self.logger.warning(f"Could not start web dashboard server: {e}")

        self.state.add_event("All HealOS 2.0 subsystems ONLINE and active.")
        log_event("HealOS 2.0 system boot sequence complete.")

    def _on_crash_detected(self, crash_event: CrashEvent) -> None:
        """
        Thread-safe event bridge from CrashDetector to AutoRestart and AppState.
        Executes recovery in a background worker to ensure monitoring and dashboard remain unblocked.
        """
        if self._is_shutting_down:
            return

        self.state.add_event(f"[CRASH DETECTED] Process PID {crash_event.pid} crashed")

        # Run recovery asynchronously so dashboard and monitoring remain responsive
        recovery_thread = threading.Thread(
            target=self._run_recovery_workflow,
            args=(crash_event,),
            daemon=True,
            name="RecoveryWorkerThread",
        )
        recovery_thread.start()

    def _run_recovery_workflow(self, crash_event: CrashEvent) -> None:
        """Executes recovery workflow, updates state transitions, and syncs log analysis."""
        self.recovery_service.handle_detected_crash(crash_event)

        # Update recovery summary and decision immediately
        summary = self.recovery_service.get_status_summary()
        self.state.update_recovery_status(summary)
        if self.recovery_service.last_decision:
            self.state.update_decision(self.recovery_service.last_decision)

        # Update historical log analytics
        if self.log_analyzer:
            report = self.log_analyzer.analyze()
            self.state.update_log_analysis(report)

        # Re-evaluate health score immediately
        metrics = self.system_monitor.get_latest_metrics()
        health = self.health_analyzer.calculate_health(
            cpu_percent=metrics.cpu_percent,
            ram_percent=metrics.ram_percent,
            disk_percent=metrics.disk_percent,
            is_app_running=summary["is_running"],
            recent_crashes_count=len(self.recovery_service.crash_timestamps),
            total_restarts=summary["total_restarts"],
        )
        self.state.update_health(health)

    def _demo_worker(self, cycles: int) -> None:
        """Automated demonstration worker running N controlled crash-and-recovery cycles."""
        self.logger.info(f"Automated demo worker started: {cycles} cycles scheduled.")
        self.state.add_event(f"[DEMO MODE] {cycles} crash-and-recovery cycles scheduled.")
        # Wait 4 seconds for teacher to view State 1 (Normal) and State 2 (Risk Assessment)
        time.sleep(4.0)

        for cycle in range(1, cycles + 1):
            if self._shutdown_event.is_set():
                break

            self.state.add_event(f"[DEMO {cycle}/{cycles}] Triggering simulated failure via crash.trigger...")
            self.logger.info(f"[DEMO {cycle}/{cycles}] Creating data/crash.trigger")
            try:
                CRASH_TRIGGER_FILE.parent.mkdir(parents=True, exist_ok=True)
                CRASH_TRIGGER_FILE.write_text("SIMULATED_TEST_CRASH", encoding="utf-8")
            except Exception as e:
                get_error_logger().error(f"Failed to create demo crash trigger: {e}")

            # Wait 5.5 seconds for crash detection, decision, and auto-restart to finish
            time.sleep(5.5)

            if cycle < cycles and not self._shutdown_event.is_set():
                # Allow 4 seconds of healthy observation before next cycle
                time.sleep(4.0)

        self.state.add_event(f"[DEMO MODE] Completed all {cycles} demonstration cycles successfully.")

    def _demo_lab_worker(self) -> None:
        """Automated tour of all 4 OS Process Lab sections for faculty presentation."""
        self.logger.info("Automated OS Process Lab demo worker started.")
        time.sleep(3.0)
        if self.dashboard:
            self.dashboard.switch_tab("os-lab")
            self.state.add_event("[DEMO LAB] Presentation mode started on OS Process Lab tab.")
            for step in range(1, 7):
                if self._shutdown_event.is_set():
                    break
                time.sleep(4.5)
                msg = self.dashboard.next_lab_demo_step()
                self.state.add_event(f"[DEMO LAB] {msg}")
            self.state.add_event("[DEMO LAB] Completed 6-step guided walkthrough.")

    def run(self) -> None:
        """Main orchestrator coordination loop."""
        self.initialize_subsystems()

        # Start automated demo worker if configured
        if self.demo_crash_count > 0:
            demo_thread = threading.Thread(
                target=self._demo_worker,
                args=(self.demo_crash_count,),
                daemon=True,
                name="DemoWorkerThread",
            )
            demo_thread.start()

        # Start automated lab walkthrough if configured
        if self.demo_lab:
            demo_lab_thread = threading.Thread(
                target=self._demo_lab_worker,
                daemon=True,
                name="DemoLabWorkerThread",
            )
            demo_lab_thread.start()

        last_headless_print = time.time()

        try:
            while not self._shutdown_event.is_set():
                # 1. Update system metrics in state
                metrics = self.system_monitor.get_latest_metrics()
                self.state.update_metrics(metrics)

                # 2. Update recovery and app status in state
                rec_summary = self.recovery_service.get_status_summary()
                self.state.update_recovery_status(rec_summary)

                # 3. Query process monitor for monitored application telemetry
                curr_pid = rec_summary.get("current_pid")
                if curr_pid and rec_summary.get("is_running"):
                    proc_info = self.process_monitor.get_process_details(curr_pid)
                    self.state.update_app_process_info(proc_info)
                else:
                    self.state.update_app_process_info(None)

                # 4. Update AI failure prediction in state
                pred = self.predictor.predict_risk(
                    cpu_percent=metrics.cpu_percent,
                    ram_percent=metrics.ram_percent,
                    disk_percent=metrics.disk_percent,
                    process_count=metrics.process_count,
                    cpu_change=metrics.cpu_change,
                    ram_change=metrics.ram_change,
                    app_cpu_percent=self.state.app_cpu_percent,
                    app_memory_percent=self.state.app_memory_percent,
                    recent_crashes_count=len(self.recovery_service.crash_timestamps),
                )
                self.state.update_prediction(pred)

                # 5. Continuous AI Decision Engine assessment during runtime
                runtime_decision = self.decision_engine.decide_runtime(
                    is_app_running=rec_summary["is_running"],
                    risk_category=pred.risk_category,
                    risk_probability=pred.risk_probability,
                    cpu_percent=metrics.cpu_percent,
                    ram_percent=metrics.ram_percent,
                    warning_signals=pred.warning_signals,
                )
                if rec_summary["is_running"]:
                    self.state.update_decision(runtime_decision)
                elif self.recovery_service.last_decision:
                    self.state.update_decision(self.recovery_service.last_decision)

                # 6. Update health score in state
                health = self.health_analyzer.calculate_health(
                    cpu_percent=metrics.cpu_percent,
                    ram_percent=metrics.ram_percent,
                    disk_percent=metrics.disk_percent,
                    is_app_running=rec_summary["is_running"],
                    recent_crashes_count=len(self.recovery_service.crash_timestamps),
                    total_restarts=rec_summary["total_restarts"],
                )
                self.state.update_health(health)

                # 7. If headless mode, emit periodic diagnostics
                if self.no_dashboard and (time.time() - last_headless_print >= 2.0):
                    last_headless_print = time.time()
                    now_str = datetime.now().strftime("%H:%M:%S")
                    status_lbl = "ONLINE" if rec_summary["is_running"] else "OFFLINE"
                    print(
                        f"[{now_str}] App: {status_lbl} (PID: {rec_summary['current_pid']}) [CPU: {self.state.app_cpu_percent:.1f}%, RAM: {self.state.app_memory_mb:.1f}MB] | "
                        f"Host: CPU {metrics.cpu_percent:.1f}% RAM {metrics.ram_percent:.1f}% Disk {metrics.disk_percent:.1f}% | "
                        f"Health: {health.overall_score}/100 ({health.risk_category}) | "
                        f"AI Risk: {pred.risk_probability:.1f}% ({pred.risk_category}) | "
                        f"Decision: {self.state.decision_action} | "
                        f"Crashes: {rec_summary['total_crashes']} Restarts: {rec_summary['total_restarts']}",
                        flush=True,
                    )

                # Sleep brief interval for loop coordination
                self._shutdown_event.wait(0.5)

        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Executes orderly, non-destructive shutdown of all components."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        self._shutdown_event.set()

        print("\n\n" + "=" * 60)
        print(" [!] HealOS 2.0: Initiating Graceful System Shutdown...")
        print("=" * 60)

        log_event("HealOS 2.0 shutdown initiated by operator.")
        self.logger.info("HealOS 2.0 shutting down...")

        # 1. Stop Dashboard
        if self.dashboard and self.dashboard.is_alive():
            print(" [*] Stopping Terminal Dashboard...")
            self.dashboard.stop()

        # 2. Stop Crash Detector
        if self.crash_detector and self.crash_detector.is_alive():
            print(" [*] Stopping Crash Detector...")
            self.crash_detector.mark_intentional_shutdown()
            self.crash_detector.stop()

        # 3. Gracefully Terminate Monitored Application
        if self.recovery_service:
            print(" [*] Terminating monitored application cleanly...")
            self.recovery_service.stop_application()

        # 4. Stop System Monitor
        if self.system_monitor and self.system_monitor.is_alive():
            print(" [*] Stopping System Monitor...")
            self.system_monitor.stop()

        # 5. Stop Web Dashboard Server if running
        if self.web_server:
            try:
                self.web_server.stop()
            except Exception:
                pass

        # Clean up any leftover trigger files
        try:
            if CRASH_TRIGGER_FILE.exists():
                CRASH_TRIGGER_FILE.unlink(missing_ok=True)
        except Exception:
            pass

        print(" [✓] All HealOS 2.0 subsystems stopped cleanly. Goodbye.")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="HealOS 2.0 - AI-Powered Self-Healing Operating System"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train the AI failure prediction model before launching",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Run in headless diagnostic mode without refreshing terminal UI",
    )
    parser.add_argument(
        "--demo-crash",
        type=int,
        default=0,
        metavar="COUNT",
        help="Automatically trigger N controlled crash-and-recovery demonstration cycles (e.g. --demo-crash 2)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="normal",
        choices=["normal", "crash-after", "memory-leak", "spike-cpu"],
        help="Execution mode for dummy application (default: normal)",
    )
    parser.add_argument(
        "--tab",
        type=str,
        default="overview",
        choices=["overview", "os-lab"],
        help="Initial dashboard tab ('overview' or 'os-lab')",
    )
    parser.add_argument(
        "--lab-section",
        type=str,
        default="ALL",
        choices=["ALL", "LIFECYCLE", "SCHEDULER", "PID_COMPARE", "DEADLOCK"],
        help="Initial sub-section within the OS Process Lab tab",
    )
    parser.add_argument(
        "--demo-lab",
        action="store_true",
        help="Run an automated presentation walkthrough of all 4 OS Process Lab sections",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch optional interactive web dashboard on http://localhost:8080",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="Port for optional web dashboard (default: 8080)",
    )

    args = parser.parse_args()

    orchestrator = HealOSOrchestrator(
        auto_train=args.train,
        no_dashboard=args.no_dashboard,
        demo_crash_count=args.demo_crash,
        dummy_mode=args.mode,
        initial_tab=args.tab,
        lab_section=args.lab_section,
        demo_lab=args.demo_lab,
        enable_web=args.web,
        web_port=args.web_port,
    )

    # Register signal handler for clean exit on SIGINT (Ctrl+C) and SIGTERM
    def sig_handler(signum, frame):
        orchestrator.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    orchestrator.run()


if __name__ == "__main__":
    main()
