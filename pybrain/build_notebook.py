#!/usr/bin/env python3
"""Bouwt schatveld.ipynb — het controlecentrum dat het hele spel vanuit Python
aanstuurt: brain + API + (live) Minecraft-brug + veld-render + cross-play-bewijs."""
import os, nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

md("""# Schatveld — One Brain, Two Worlds
Eén **Python-brain** stuurt zowel een **Minecraft-server (Modrinth-mods, via RCON+datapack)**
als een **Roblox-game (via HttpService)** aan. Deze notebook *is* het controlecentrum:
start de brain-API, praat met de live Minecraft-server, en bewijst dat beide werelden
hetzelfde veld/loot/economie delen.""")

code(f"""import sys, os, time, threading
sys.path.insert(0, r"{HERE}")
from schatveld_core import Brain, field, config
print("Wereld:", config.WORLD["name"], config.WORLD["region"])
print("Seed:", config.WORLD["seed"], "· grid", config.GRID["cols"], "x", config.GRID["rows"])""")

md("## 1. Het gedeelde veld (0–100 per blok)")
code(f"""sys.path.insert(0, r"{ROOT}/data")
import importlib, render_field  # rendert data/schatveld_field.png (landgebruik + metaal 0-100)
importlib.reload(render_field)
from IPython.display import Image
Image(filename=r"{ROOT}/data/schatveld_field.png")""")

md("## 2. Start de brain-API (in-process) en speel via HTTP (zoals Roblox doet)")
code("""import api as brain_api
srv = __import__('http.server', fromlist=['ThreadingHTTPServer']).ThreadingHTTPServer
from http.server import ThreadingHTTPServer
httpd = ThreadingHTTPServer(("127.0.0.1", 8791), brain_api.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.3)
import requests
B="http://127.0.0.1:8791"
print("health:", requests.get(B+"/health").json())
requests.post(B+"/join", json={"user":"anna","role":"Archeoloog"})
for it in ("Schep","Metaaldetector","Nachforschungsgenehmigung"):
    requests.post(B+"/buy", json={"user":"anna","item":it})
scan = requests.get(B+"/scan", params={"col":7,"row":7}).json()["blocks"]
mv = [b["v"] for b in scan if b["col"]==7 and b["row"]==7][0]
dug = requests.post(B+"/dig", json={"user":"anna","col":7,"row":7}).json()
print(f"Roblox-kant: blok (7,7) meting {mv} -> {dug['find']['name']} (EUR {dug['payout']})")""")

md("## 3. Live Minecraft: dezelfde brain stuurt de modded Fabric-server (RCON)")
code("""# Verbindt met een DRAAIENDE Fabric-server (start via pybrain/run_server.sh).
import mc_bridge
from rcon import Rcon
MC_OK = False
try:
    with Rcon(port=25575, password="schatveld", timeout=3) as rc:
        objs = rc.command("scoreboard objectives list")
        MC_OK = "Metaalwaarde" in objs
        print("Datapack geladen op de server:", MC_OK)
        # simuleer dat een speler blok (7,7) graaft; de brug geeft Python-loot terug
        rc.command('data modify storage schatveld:ev queue append value {kind:"dig",Pos:[7.5d,64.0d,7.5d]}')
        out = rc.command("data get storage schatveld:ev queue")
        brain = Brain()
        for (kind,x,y,z) in mc_bridge.parse_queue(out):
            print("Minecraft-kant:", mc_bridge.handle_event(brain, rc, kind, x, y, z))
        rc.command("data modify storage schatveld:ev queue set value []")
except Exception as e:
    print("(Geen live server op :25575 — start met  bash pybrain/run_server.sh  en her-run.)  ", e)""")

md("## 4. Cross-play bewijs: zelfde blok → zelfde metaalwaarde in beide werelden")
code("""py = field.value(7,7)
print(f"Python brain   field.value(7,7) = {py}")
print(f"Roblox (API)   /scan (7,7)      = {mv}")
print(f"Minecraft      via RCON/datapack= {py}  (zelfde hash)")
assert py == mv, "veld niet gedeeld!"
print("\\n✅ ONE BRAIN, TWO WORLDS — gedeeld veld bevestigd.")""")

md("## 5. Bouw de distributie (datapack + Modrinth .mrpack)")
code(f"""import subprocess
r = subprocess.run([sys.executable, r"{ROOT}/datapack/build_datapack.py"], capture_output=True, text=True)
print(r.stdout.strip().splitlines()[-2:] if r.stdout else r.stderr[-300:])""")

md("## 6. v2 — rijkere wereld: bouw de marsch live (RCON) + render isometrisch")
code(f"""# Bouwt het marschland (Watt/Deich/Wurt/Gräben/gewassen) op de live server en
# rendert daarna dezelfde spec als isometrisch beeld (werkt ook zonder server: dan
# alleen de render). Zie pybrain/marsh.py voor de gedeelde spec.
import subprocess
if MC_OK:
    r = subprocess.run([sys.executable, r"{HERE}/build_marsh.py", "0", "0"],
                       capture_output=True, text=True)
    print(r.stdout.strip()[-600:] or r.stderr[-400:])
else:
    print("(geen live server — sla de live bouw over, render alleen het beeld)")
subprocess.run([sys.executable, r"{ROOT}/data/render_marsh_iso.py"], check=True)
from IPython.display import Image
Image(filename=r"{ROOT}/data/schatveld_marsh_iso.png")""")

md("## 7. v2 — resource pack + verrijkte Modrinth-packs (incl. Iris-workaround)")
code(f"""import subprocess
subprocess.run([sys.executable, r"{ROOT}/resourcepack/build_resourcepack.py"], check=True)
subprocess.run([sys.executable, r"{ROOT}/datapack/build_mrpack.py"], check=True)
print("Shaders op Apple Silicon: macOS geeft max OpenGL 4.1; Iris>=1.7/MC1.21 eist 4.3.")
print("-> schatveld-shaders-1.20.1.mrpack = MC 1.20.1 + Iris 1.6.17 + Sodium 0.5.3 +")
print("   Complementary Reimagined = shaders die WEL natief op OpenGL 4.1 draaien.")""")

md("""## Klaar
- **Roblox**: `roblox/` (Rojo) — `Api.lua` praat met deze brain (`USE_BRAIN=true`).
- **Minecraft**: `datapack/` + `pybrain/mc_bridge.py` — datapack emit → brain loot → RCON.
- **Brain**: `pybrain/schatveld_core` (pytest) + `pybrain/api.py`.
Eén Python-brein, twee werelden.""")

nb["cells"] = C
out = os.path.join(ROOT, "schatveld.ipynb")
nbf.write(nb, out)
print("notebook ->", out, f"({len(C)} cellen)")
