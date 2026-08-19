#!/usr/bin/env bash
# stop.sh — sla de wereld op en stop de complete Schatveld-backend netjes.
ROOT="$HOME/Documents/schatveld"; cd "$ROOT"
echo "world opslaan + server stoppen…"
python3 - <<'PY'
import sys; sys.path.insert(0,"pybrain")
from rcon import Rcon
try:
    with Rcon(port=25575,password="schatveld",timeout=5) as rc:
        print("  ", rc.command("save-all flush").strip())
        print("  ", rc.command("stop").strip())
except Exception as e:
    print("   (server al gestopt)", e)
PY
pkill -f "pybrain/mc_bridge.py" 2>/dev/null && echo "brug gestopt" || true
pkill -f "pybrain/api.py" 2>/dev/null && echo "brain-API gestopt" || true
echo "klaar."
