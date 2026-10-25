import os
from pathlib import Path

for f in Path("tests").glob("test_*.py"):
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if ".start()" in l and "time" not in l and "start_time" not in l:
            print(f"{f.name}:{i+1}: {l.strip()}")
