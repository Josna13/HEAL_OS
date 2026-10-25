# HealOS 2.0 — Comprehensive UI & Feature Upgrade Plan

## Current State (Verified)
- **File**: `dashboard/web_server.py` (228KB, ~4100 lines)
- **Tests**: 114/114 passing
- **Web server**: WebDashboardServer class, runs on port 8080
- **Start command**: `python main.py --web` (adds `--web` flag which calls `WebDashboardServer`)
- **Python**: 3.11.1 (Windows), also compatible with 3.14 (WSL/Linux)

## Current Tab Structure
1. `tab-overview` (line 789) - 5 KPI cards + trend chart + launchpad
2. `tab-process-lab` (line 951) - CPU Execution Studio (completed)
3. `tab-recovery` (line 1412) - Self-healing & recovery
4. `tab-deadlock` (line 1519) - Deadlock & Banker's lab
5. `tab-diagnostics` (line 1647) - Diagnostics & telemetry

## What Needs to Be Added/Fixed

### A. Color System (CSS Variables)
Current: `#070d18`, `#0c1322`, etc. (close but not exact per spec)
Required: Update to match spec exactly:
- Main bg: `#0B1220`
- Panel bg: `#111C2E`
- Elevated: `#172438`
- Borders: `#26364D`
- Accent: `#22D3EE`
- Healthy: `#22C55E`
- Warning: `#F59E0B`
- Error: `#EF4444`
- Secondary: `#94A3B8`
- Text: `#F1F5F9`

### B. Memory Leak Simulation (NEW TAB or section)
Currently: **NOT PRESENT**
Need: Add memory leak simulation mode with:
- Live animated bar + time-series graph
- Simulated (not real RAM) memory accumulation
- Start/Pause/Reset/Recover controls
- Clear "SIMULATION" label
- Show trend and explanation

### C. Guided Faculty Demo (PRESENT - enhance)
Currently: `TOUR_STORY` and guided demo present but needs 8 steps per spec

### D. Crash & Self-Healing Demo Enhancement
Currently: Recovery tab exists
Need: Make more visual with side-by-side PID comparison and timeline animation

### E. Disk Usage (Overview)
Currently: RAM and CPU bars present, need disk bar

### F. WSL/Ubuntu startup instructions
The app runs on both Windows (python) and WSL/Linux (python3)
WSL command: `cd /mnt/e/HealOs && source venv/bin/activate && python3 main.py --web`

## Key Implementation Tasks

### Task 1: Update CSS design system
### Task 2: Add memory leak simulation to Diagnostics tab
### Task 3: Enhance Overview with disk metric
### Task 4: Enhance recovery tab with animated timeline
### Task 5: Add disk/disk-free to API
### Task 6: Make guided demo 8-step
### Task 7: Add memory leak API endpoint and JS
### Task 8: Final smoke test + pytest
