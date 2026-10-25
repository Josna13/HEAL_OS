import sys
sys.path.insert(0, '.')
import json
import urllib.request
from dashboard.web_server import WebDashboardServer

print("Starting test of Deadlock Studio...")

server = WebDashboardServer(port=8095)
server.start()

try:
    with urllib.request.urlopen("http://127.0.0.1:8095/") as resp:
        html = resp.read().decode('utf-8')

    # 1. HTML Elements Check
    required_ids = [
        'id="tab-deadlock"',
        'id="btn-dl-sc-three"',
        'id="btn-dl-sc-two"',
        'id="btn-dl-sc-banker"',
        'id="btn-dl-play"',
        'id="btn-dl-recover"',
        'id="btn-dlspd-05"',
        'id="btn-dlspd-1"',
        'id="btn-dlspd-2"',
        'id="btn-dlspd-4"',
        'id="dl-status-badge"',
        'id="dl-phase-badge"',
        'id="dl-step-indicator"',
        'id="dl-rag-type-badge"',
        'id="dl-cycle-warning-pill"',
        'id="rag-svg"',
        'id="rag-edges-group"',
        'id="rag-nodes-group"',
        'id="diag-cycle-procs"',
        'id="diag-victim-proc"',
        'id="diag-explanation-box"',
        'id="dl-event-feed"',
        'id="dl-timeline-count"',
        'id="mat-table-alloc"',
        'id="mat-table-max"',
        'id="mat-table-need"',
        'id="mat-vector-available"',
        'id="mat-safe-seq-str"',
        'id="mat-safe-pill"'
    ]

    for rid in required_ids:
        assert rid in html, f"Missing required HTML ID: {rid}"
    print(f"[OK] All {len(required_ids)} Deadlock Studio HTML elements verified present.")

    # 2. Sound Effects Check
    sound_cues = [
        'RES_ACQUIRE',
        'RES_REQUEST',
        'PROC_BLOCKED',
        'DEADLOCK_ALERT',
        'RECOVERY_START',
        'RES_RELEASE',
        'PROC_UNBLOCK',
        'ALL_COMPLETE',
        'RECOVERY_FAIL'
    ]
    for cue in sound_cues:
        assert f"'{cue}'" in html or f'"{cue}"' in html, f"Missing sound cue: {cue}"
    print(f"[OK] All {len(sound_cues)} Deadlock sound cues verified present in audio synthesizer.")

    # 3. Scenario Definitions Check
    assert "three_process:" in html
    assert "two_process:" in html
    assert "banker_safe:" in html
    assert "Step 6/11" in html or "CIRCULAR WAIT DEADLOCK" in html
    assert "P0 ➔ R1 ➔ P1 ➔ R2 ➔ P2 ➔ R0 ➔ P0" in html
    assert "P2 (Lowest rollback penalty)" in html or "Lowest Cost" in html
    print("[OK] Scenario definitions and step-by-step state machines verified.")

    # 4. Backend Deadlock Actions & Telemetry Check
    with urllib.request.urlopen("http://127.0.0.1:8095/api/status") as resp:
        d = json.loads(resp.read().decode('utf-8'))
        assert "deadlock" in d
        dl = d["deadlock"]
        assert "two_process" in dl
        assert "banker" in dl
        assert dl["banker"]["is_safe"] is True
    print("[OK] Backend deadlock telemetry in /api/status verified.")

    # Step action
    req_step = urllib.request.Request(
        "http://127.0.0.1:8095/api/action",
        data=json.dumps({"action": "step_two_process_deadlock"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_step) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"
    print("[OK] Backend step_two_process_deadlock action verified.")

    # Reset action
    req_reset = urllib.request.Request(
        "http://127.0.0.1:8095/api/action",
        data=json.dumps({"action": "reset_two_process_deadlock"}).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_reset) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        assert res.get("status") == "ok"
    print("[OK] Backend reset_two_process_deadlock action verified.")

    print("\n=========================================================")
    print(" ALL DEADLOCK STUDIO VERIFICATION TESTS PASSED 100%! ")
    print("=========================================================")

finally:
    server.stop()
    print("Test server stopped.")
