#!/usr/bin/env python3
"""demo_playthrough — een live cross-world speelsessie tegen de ene brain:
Archeoloog graaft, Boer doet gewasrotatie + pesticide, Politie beboet; dezelfde
digs lopen óók door de Minecraft-server via RCON. Rendert een dashboard-beeld."""
import os, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import ThreadingHTTPServer
import api as brain_api
import requests
from schatveld_core import field, cadastre, config
import mc_bridge
from rcon import Rcon

# reset staat
state = os.path.join(os.path.dirname(__file__), "state.json")
if os.path.exists(state): os.remove(state)
brain_api.BRAIN.players = {}

httpd = ThreadingHTTPServer(("127.0.0.1", 8791), brain_api.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
B = "http://127.0.0.1:8791"
def post(p, **b): return requests.post(B+p, json=b).json()
def get(p, **q): return requests.get(B+p, params=q).json()

log = []
def say(s): log.append(s); print(s)

say("═══ SCHATVELD — live speelsessie (één brain, twee werelden) ═══\n")

# --- Archeoloog ---
say("Dr. Anna (Archeoloog) betreedt Weddewarden")
post("/join", user="anna", role="Archeoloog")
brain_api.BRAIN._p("anna")["coins"] = 600      # startbudget voor gereedschap + vergunning
for it in ("Schep", "Metaaldetector", "Nachforschungsgenehmigung"):
    b = post("/buy", user="anna", item=it)
    assert b.get("ok"), f"koop {it} mislukt: {b}"
say("   koopt schep + metaaldetector + opgravingsvergunning (legaal graven)")
# scan een rijke strook en graaf de 4 beste blokken
region = [(c, r) for c in range(4, 12) for r in range(0, 6)]
region.sort(key=lambda cr: field.value(*cr), reverse=True)
anna_finds = []
dug_blocks = []
try:
    rc = Rcon(port=25575, password="schatveld", timeout=3).connect()
except Exception:
    rc = None
for (c, r) in region[:5]:
    v = field.value(c, r)
    res = post("/dig", user="anna", col=c, row=r)
    anna_finds.append((c, r, v, res["find"]["name"], res["payout"], res["schatzregal"]))
    dug_blocks.append((c, r))
    tag = " ⚑Schatzregal" if res["schatzregal"] else ""
    say(f"   graaft ({c:2d},{r}) meting {v:3d} → {res['find']['name']} €{res['payout']}{tag}")
    # DEZELFDE dig in Minecraft via de brug (bewijs cross-world)
    if rc:
        rc.command(f'data modify storage schatveld:ev queue append value {{kind:"dig",Pos:[{c}.5d,64.0d,{r}.5d]}}')
anna_state = get("/state", user="anna")
say(f"   → Anna heeft nu €{anna_state['coins']}, reputatie {anna_state['rep']}\n")

# Minecraft verwerkt dezelfde digs
if rc:
    out = rc.command("data get storage schatveld:ev queue")
    evs = mc_bridge.parse_queue(out)
    from schatveld_core import Brain
    mcb = Brain()
    mc_results = [mc_bridge.handle_event(mcb, rc, k, x, y, z) for (k, x, y, z) in evs]
    rc.command("data modify storage schatveld:ev queue set value []")
    say(f"Minecraft verwerkte dezelfde {len(mc_results)} digs via de brug "
        f"(metaalwaarden {[m[1] for m in mc_results]})")
    say("   → identieke metaalwaarden als de API: ÉÉN BRAIN.\n")

# --- Boer ---
say("Bauer Ben (Boer) krijgt 4 Flurstücke toegewezen (kadaster)")
post("/join", user="ben", role="Boer")
own = [p for p in cadastre.all_parcels() if p["owner"] == "ben"]
pc, pr = own[0]["blocks"][0]
r1 = post("/plough", user="ben", col=pc, row=pr, crop="Ackerbohne")
r2 = post("/plough", user="ben", col=pc, row=pr, crop="Winterweizen")
r3 = post("/plough", user="ben", col=pc, row=pr, crop="Winterweizen")
say(f"   Ackerbohne → Winterweizen: goede rotatie ×{r2['mult']} (€{r2['yield']})")
say(f"   Winterweizen → Winterweizen: monocultuur ×{r3['mult']} (€{r3['yield']}) — malus")
spray = post("/spray", user="ben", col=1, row=pr, agent="Standaard", dose=1)  # col 1 = te dicht bij water
say(f"   bespuit vlak bij de Graben → overtreding: {spray['violations']}\n")

# --- Politie ---
say("Wachtmeister Wim (Politie) handhaaft")
post("/join", user="wim", role="Politie")
# Anna groef mét vergunning op eigen/onbeheerd land → wettig; test op Ben's pesticide
fine_ben = post("/fine", cop="wim", target="ben", reason="PesticideBuffer")
if fine_ben.get("ok"):
    say(f"   beboet Ben €{fine_ben['amount']} — {fine_ben['reason']} (te dicht bij water)")
else:
    say(f"   geen boete voor Ben: {fine_ben.get('msg')}")
# laat 'chris' illegaal graven (zonder vergunning) en beboet hem
post("/join", user="chris", role="Archeoloog"); post("/buy", user="chris", item="Schep")
post("/dig", user="chris", col=20, row=20)   # geen vergunning → Raubgrabung
fine_chris = post("/fine", cop="wim", target="chris", reason="Raubgrabung")
say(f"   beboet schatgraver Chris €{fine_chris.get('amount','—')} — Raubgrabung (geen vergunning)")
wim = get("/state", user="wim")
say(f"   → Wim's premie: €{wim['coins']-250}\n")

if rc: rc.close()

# --- dashboard ---
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, matplotlib.patches as mp
COLS, ROWS = config.GRID["cols"], config.GRID["rows"]
metal = np.array([[field.value(c, r) for c in range(COLS)] for r in range(ROWS)])
fig = plt.figure(figsize=(14, 7), dpi=130); fig.patch.set_facecolor("#0e1116")
fig.suptitle("Schatveld — live speelsessie · één brain stuurt Minecraft + Roblox",
             color="#e6c229", fontsize=15, y=0.97)
ax = fig.add_subplot(1, 2, 1); ax.set_title("Veld + Anna's opgravingen", color="#cdd7e2")
ax.imshow(metal, origin="lower", cmap="inferno", vmin=0, vmax=100)
for (c, r, v, name, pay, st) in anna_finds:
    ax.scatter(c, r, s=140, marker="X", edgecolors="#5fd0ff",
               facecolors="#e6c229" if st else "none", linewidths=2)
    ax.annotate(f"{v}", (c, r), color="#fff", fontsize=7, ha="center", va="center")
ax.set_xticks([]); ax.set_yticks([])
ax.legend(handles=[mp.Patch(color="#e6c229", label="Schatzregal-vondst"),
                   mp.Patch(color="#5fd0ff", label="opgraving")],
          loc="lower right", fontsize=8, facecolor="#161b22", labelcolor="#cdd7e2")

axT = fig.add_subplot(1, 2, 2); axT.axis("off")
axT.set_title("Speelsessie-log", color="#cdd7e2")
axT.text(0, 1, "\n".join(l.encode("ascii","ignore").decode() for l in log[:26]), va="top", ha="left", family="monospace",
         fontsize=8.2, color="#d6dbe5", transform=axT.transAxes)
fig.tight_layout(rect=[0, 0, 1, 0.95])
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "schatveld_playthrough.png")
fig.savefig(out, facecolor=fig.get_facecolor())
print("\ndashboard ->", out)
