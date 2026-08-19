#!/usr/bin/env python3
"""Builds schatveld_modrinth_en.ipynb — an ENGLISH, pure Minecraft × Modrinth control
centre (no Roblox). Generates the datapack + resource pack + Modrinth mrpacks, lists
which assets (mods/shaderpack/resource pack/datapack) to use and why, builds the marsh
world live on a Fabric server over RCON, proves the Python loot brain, and explains how
to connect — including the Iris shader workaround for Apple Silicon (OpenGL 4.1)."""
import os, nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

md("""# Schatveld — Minecraft via Modrinth (pure Minecraft)
A treasure-hunting role-playing game set on the real marshland of **Weddewarden /
Land Wursten** (Bremerhaven-Nord, Germany), built entirely in **Minecraft Java 1.21.10**
with **Modrinth mods**, a **datapack**, and a **Python rules engine** ("brain") that
decides every find.

This notebook generates everything with Python, builds the world live on a Fabric server,
and explains **which assets** to install and **how to connect** (including the Iris shader
workaround for Apple Silicon).""")

code(f"""import subprocess, sys, os, socket, glob
ROOT = r"{ROOT}"
def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT)
    print((r.stdout or r.stderr).strip()[-800:]); return r
def port_up(p):
    s = socket.socket(); s.settimeout(1)
    try: s.connect(("127.0.0.1", p)); return True
    except OSError: return False
    finally: s.close()
print("working dir:", ROOT)""")

md("""## 1. Which assets do you use?
Everything below is fetched automatically at the correct version + sha512 from the
**Modrinth API** by `datapack/build_mrpack.py`. You do not download anything by hand.

### Game world — `schatveld-world-1.21.10.mrpack` (MC 1.21.10, Fabric)
| Asset | Type | Purpose | Needed? |
|---|---|---|---|
| **Fabric API** | mod (base) | required by every Fabric mod (server-side) | ✅ required |
| **BetterArcheology** | mod (gameplay) | brushes, suspicious blocks — fits the digging perfectly | ✅ recommended |
| **Sodium** | mod (render) | smooth framerate | ✅ client |
| **Lithium** | mod (tick) | faster server/world simulation | ✅ |
| **FerriteCore** | mod (memory) | lower RAM use | ⭘ optional |
| **EntityCulling** | mod (render) | skips rendering hidden entities | ⭘ optional |
| **Entity Model Features (EMF)** | mod (render) | custom entity models | ⭘ optional |
| **Entity Texture Features (ETF)** | mod (render) | custom entity textures (+ Fresh Animations) | ⭘ optional |
| **Schatveld datapack** | datapack | 0–100 per block, digging emits → brain loot | ✅ required |
| **Schatveld resource pack** | resource pack | metal detector + find textures (amber, fibula, coin, ploughshare, potsherd) | ✅ recommended |

### Shaders (Apple Silicon) — `schatveld-shaders-1.20.1.mrpack` (MC 1.20.1)
| Asset | Version | Purpose |
|---|---|---|
| **Iris** | 1.6.17 | shader loader that still runs on **OpenGL 4.1** (≥1.7 needs 4.3 → crashes on Mac) |
| **Sodium** | 0.5.3 | matches Iris 1.6.x |
| **Complementary Reimagined** | r5.8.1 | the shader pack (4.1-compatible) |

> **Why two packs?** macOS gives at most **OpenGL 4.1** (Apple froze OpenGL — you cannot
> upgrade it). So the game world runs on 1.21.10 **without** Iris (Sodium + EMF/ETF + the
> resource pack provide the visual upgrade); for real shaders you use the 1.20.1 pack.""")

md("""## 2. Which assets are truly required to make the game?
The game logic lives in the **Python brain** (`pybrain/schatveld_core/`) and the
**datapack** — not in mods. Minimum to make the metal-detecting + digging game work:
1. **Minecraft Java 1.21.10 + Fabric loader + Fabric API** (the only required mod).
2. **The Schatveld datapack** (`schatveld_datapack.zip`) — 0–100 per block, role menu,
   detector, dig events.
3. **The Python brain + bridge** (`pybrain/`) — computes the find (Schatzregal, `<10 =
   always rusty iron`) and hands it back over RCON. Run it with `bash pybrain/play.sh`.

All other mods and the shader pack are **optional polish**.""")

md("""## 3. Generate the distribution with Python""")
code("""run(os.path.join(ROOT,"datapack","build_datapack.py"))
run(os.path.join(ROOT,"resourcepack","build_resourcepack.py"))
run(os.path.join(ROOT,"datapack","build_mrpack.py"))
for f in sorted(glob.glob(os.path.join(ROOT,"datapack","build","*.mrpack"))
                + glob.glob(os.path.join(ROOT,"resourcepack","build","*.zip"))):
    print("  ->", os.path.relpath(f, ROOT), os.path.getsize(f), "bytes")""")

md("""## 4. Import into the Modrinth launcher
1. Open the **Modrinth App** → **+ Add instance → From file**.
2. Choose `datapack/build/schatveld-world-1.21.10.mrpack` (the game world) — or
   `datapack/build/schatveld-shaders-1.20.1.mrpack` for shaders.
3. The launcher downloads every mod/shader pack automatically (versions from step 3).
4. **Play** the profile.

*(Already on this PC?* The profile **`chemlab`** runs MC 1.21.10 Fabric with exactly these
mods — you can use it right away.)""")

md("""## 5. Start the server backend
Run in a **terminal** (this blocks):
```
bash pybrain/play.sh      # Fabric server + Python brain + bridge, marsh already built
```""")
code("""for name, p in [("Fabric server (RCON)",25575), ("Minecraft (join)",25565), ("brain",8791)]:
    print(f"  {'✓' if port_up(p) else '·'} {name}: port {p} {'UP' if port_up(p) else 'down — run pybrain/play.sh'}")""")

md("## 6. Build the marsh world live (RCON) + verify")
code("""if port_up(25575):
    run(os.path.join(ROOT,"pybrain","build_marsh.py"), "0", "0")
else:
    print("(no server — run pybrain/play.sh and re-run)")""")

md("""## 7. Proof: the Python brain decides the find
The datapack emits a dig event; the brain computes the find (deterministic 0–100 field,
**< 10 = always rusty iron**) and gives the item with particles, sound and an action-bar
message.""")
code("""sys.path.insert(0, os.path.join(ROOT,"pybrain"))
if port_up(25575):
    from rcon import Rcon
    import mc_bridge
    from schatveld_core import Brain, field
    with Rcon(port=25575, password="schatveld", timeout=5) as rc:
        rc.command('data modify storage schatveld:ev queue append value {kind:"dig",Pos:[7.5d,64.0d,7.5d]}')
        out = rc.command("data get storage schatveld:ev queue")
        b = Brain()
        for (k,x,y,z) in mc_bridge.parse_queue(out):
            print("Minecraft dig ->", mc_bridge.handle_event(b, rc, k, x, y, z))
        rc.command("data modify storage schatveld:ev queue set value []")
    print("field.value(7,7) =", field.value(7,7), "(deterministic, = the datapack hash)")
else:
    print("(no server — skip)")""")

md("""## 8. Connect and play
In-game: **Multiplayer → Direct Connection →** `localhost` → **Join**. You spawn on the
marshland: **Deich** (dyke) · **Wurt** (dwelling mound) + farmhouse · **Gräben** (ditches) ·
crop parcels. Type `/function schatveld:menu` for your role + shovel + metal detector.

- **Metal detector**: right-click ground → metal value **0–100**.
- **Digging**: the brain decides the find; **< 10 = always rusty iron**, higher = agrarian
  iron / coins / (rare) amber, fibula, Wurt artefact. Significant finds fall under the
  **Schatzregal** (state property → finder's fee). Digging without a
  **Nachforschungsgenehmigung** (excavation permit) is *Raubgrabung* (illegal digging).""")

md("## 9. Demonstration render of the built world")
code(f"""run(os.path.join(ROOT,"data","render_marsh_iso.py"))
from IPython.display import Image
Image(filename=os.path.join(ROOT,"data","schatveld_marsh_iso.png"))""")

md("""## Done
Stop: `bash pybrain/stop.sh` · restart: `bash pybrain/play.sh`.
Pure Minecraft — datapack + Modrinth mods + Python brain, no extra client needed.""")

nb["cells"] = C
out = os.path.join(ROOT, "schatveld_modrinth_en.ipynb")
nbf.write(nb, out)
print("notebook ->", out, f"({len(C)} cells)")
