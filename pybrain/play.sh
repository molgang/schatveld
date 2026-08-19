#!/usr/bin/env bash
# play.sh — start de COMPLETE Schatveld-backend met één commando:
#   1) Fabric 1.21.10-server (.mcserver, met datapack + de gebouwde marsch-wereld)
#   2) Python-brain-API (:8791)
#   3) de brug (datapack-graafevents -> brain-loot -> RCON give/tellraw)
# Daarna verbind je met de Modrinth-client 'chemlab' (óók 1.21.10) via Direct Connect.
set -e
ROOT="$HOME/Documents/schatveld"
cd "$ROOT"

up() { python3 -c "import socket,sys; s=socket.socket();
try:
    s.settimeout(1); s.connect(('127.0.0.1',$1)); print('up')
except OSError: sys.exit(1)" 2>/dev/null; }

echo "[1/4] Fabric-server…"
if up 25575; then echo "   server draait al (RCON 25575)"; else
  bash pybrain/run_server.sh
  python3 - <<'PY'
import socket,struct,time,sys
def ready():
    try:
        s=socket.create_connection(("127.0.0.1",25575),1)
        p=struct.pack("<ii",3,3)+b"schatveld\x00\x00"; s.sendall(struct.pack("<i",len(p))+p)
        s.settimeout(2); s.recv(4096); s.close(); return True
    except Exception: return False
for i in range(90):
    if ready(): print(f"   RCON klaar na ~{i}s"); sys.exit(0)
    time.sleep(1)
print("   RCON niet klaar"); sys.exit(1)
PY
fi

echo "[2/4] Marschland bouwen (idempotent)…"
python3 pybrain/build_marsh.py 0 0 2>&1 | tail -1

echo "[3/4] Brain-API (:8791)…"
if up 8791; then echo "   brain draait al"; else
  nohup python3 pybrain/api.py > /tmp/schatveld_brain.log 2>&1 &
  echo "   gestart (pid $!)"
fi

echo "[4/4] Brug (datapack-events -> brain-loot)…"
pkill -f "mc_bridge.py" 2>/dev/null || true
nohup python3 pybrain/mc_bridge.py schatveld > /tmp/schatveld_bridge.log 2>&1 &
echo "   gestart (pid $!)  · log: /tmp/schatveld_bridge.log"

cat <<'DONE'

────────────────────────────────────────────────────────────────
✓ Schatveld draait.  Nu spelen in Minecraft:
  1. Open de  Modrinth App  →  profiel  chemlab  →  Play
  2. In-game:  Multiplayer  →  Direct Connection  →  Server Address:  localhost
     (of:  Add Server → localhost)  →  Join Server
  3. Loop naar het marschland bij spawn (x0..47, z0..35): Deich, Wurt met
     boerderij, Gräben, gewaspercelen. Typ  /function schatveld:menu  voor je rol,
     schep en metaaldetector. Rechtsklik grond met de detector = metaalwaarde 0–100;
     graven = de Python-brain bepaalt de vondst (<10 = altijd roestig ijzer).
  Stoppen:  bash pybrain/stop.sh
────────────────────────────────────────────────────────────────
DONE
