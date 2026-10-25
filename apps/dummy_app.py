"""
HealOS 2.0 - Dummy Monitored Application
Represents a production user-space worker service monitored by HealOS.
Features:
- High-frequency trigger file watcher (instant reaction < 100ms)
- Periodic heartbeat logging
- Clean signal handling for graceful shutdown (SIGINT, SIGTERM)
- Configurable failure simulation modes for academic testing
- Default mode is stable and runs indefinitely without crashing.
"""

import argparse
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Base configuration paths
BASE_DIR = Path(__file__).resolve().parent.parent
CRASH_TRIGGER_FILE = BASE_DIR / "data" / "crash.trigger"

RUNNING = True


def handle_shutdown_signal(signum, frame):
    """Graceful signal handler for termination requests."""
    global RUNNING
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DummyApp received {sig_name}. Shutting down gracefully...", flush=True)
    RUNNING = False


def trigger_watcher_loop():
    """
    Sub-second file watcher thread to ensure immediate reaction (<100ms)
    when data/crash.trigger is created.
    """
    while RUNNING:
        try:
            if CRASH_TRIGGER_FILE.exists() or os.path.exists(str(CRASH_TRIGGER_FILE)):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{now_str}] [ALERT] Detected crash trigger file: {CRASH_TRIGGER_FILE}", flush=True)
                try:
                    if CRASH_TRIGGER_FILE.exists():
                        CRASH_TRIGGER_FILE.unlink(missing_ok=True)
                    elif os.path.exists(str(CRASH_TRIGGER_FILE)):
                        os.remove(str(CRASH_TRIGGER_FILE))
                except Exception:
                    pass
                print(f"[{now_str}] [FATAL] Simulating critical segmentation fault / panic! Exiting with code 1...", flush=True)
                # Use os._exit to immediately terminate process
                os._exit(1)
        except Exception:
            pass
        time.sleep(0.08)


def main():
    parser = argparse.ArgumentParser(description="HealOS Dummy Target Application")
    parser.add_argument(
        "--mode",
        type=str,
        default="normal",
        choices=["normal", "crash-after", "memory-leak", "spike-cpu"],
        help="Operating mode (default: normal)",
    )
    parser.add_argument(
        "--crash-seconds",
        type=float,
        default=6.0,
        help="Seconds before simulated crash in 'crash-after' mode",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=2.0,
        help="Interval between heartbeat status messages (seconds)",
    )
    parser.add_argument(
        "--max-leak-mb",
        type=int,
        default=80,
        help="Upper boundary for simulated memory allocation (MB)",
    )

    args = parser.parse_args()

    # Register OS signal handlers for clean exit
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    pid = os.getpid()
    start_time = time.time()
    memory_buffer = []

    print(f"============================================================", flush=True)
    print(f" HealOS Monitored Application Started", flush=True)
    print(f" Process ID (PID)  : {pid}", flush=True)
    print(f" Execution Mode    : {args.mode.upper()}", flush=True)
    print(f" Heartbeat Rate    : Every {args.heartbeat_interval}s", flush=True)
    print(f" Trigger File Path : {CRASH_TRIGGER_FILE}", flush=True)
    print(f"============================================================", flush=True)

    # Launch dedicated trigger watcher thread
    watcher_thread = threading.Thread(target=trigger_watcher_loop, daemon=True, name="TriggerWatcherThread")
    watcher_thread.start()

    iteration = 0

    while RUNNING:
        iteration += 1
        elapsed = round(time.time() - start_time, 1)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Heartbeat emission
        print(f"[{now_str}] DummyApp (PID: {pid}) [Uptime: {elapsed}s] - Status: HEALTHY | Beat #{iteration}", flush=True)

        # 2. Simulated crash-after mode
        if args.mode == "crash-after" and elapsed >= args.crash_seconds:
            print(f"[{now_str}] [FATAL] 'crash-after' threshold ({args.crash_seconds}s) reached! Simulating unhandled exception...", flush=True)
            os._exit(1)

        # 3. Simulated memory-leak mode (controlled and safe)
        if args.mode == "memory-leak":
            current_allocated_mb = len(memory_buffer) * 5
            if current_allocated_mb < args.max_leak_mb:
                # Safely allocate ~5 MB per interval
                chunk = bytearray(5 * 1024 * 1024)
                memory_buffer.append(chunk)
                print(f"[{now_str}] [SIM-LEAK] Allocated 5MB (Total buffer: {len(memory_buffer) * 5} MB / {args.max_leak_mb} MB limit)", flush=True)
            elif elapsed > 15.0:
                print(f"[{now_str}] [FATAL] Simulated Out-Of-Memory (OOM) ceiling hit. Process crashing...", flush=True)
                os._exit(137)

        # 4. Simulated spike-cpu mode
        if args.mode == "spike-cpu":
            spin_start = time.time()
            while time.time() - spin_start < 0.3:
                _ = 3.14159 * 2.71828

        # Sleep in small increments for responsive shutdown signal & crash trigger detection
        sleep_steps = int(args.heartbeat_interval / 0.1)
        for _ in range(sleep_steps):
            if not RUNNING:
                break
            try:
                if CRASH_TRIGGER_FILE.exists() or os.path.exists(str(CRASH_TRIGGER_FILE)):
                    try:
                        CRASH_TRIGGER_FILE.unlink(missing_ok=True)
                    except Exception:
                        pass
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [FATAL] Main thread detected crash trigger! Exiting with code 1...", flush=True)
                    os._exit(1)
            except Exception:
                pass
            time.sleep(0.1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] DummyApp (PID: {pid}) cleanly terminated.", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
