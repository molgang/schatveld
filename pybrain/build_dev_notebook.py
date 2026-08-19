#!/usr/bin/env python3
"""Bouwt schatveld_dev.ipynb — een LIVE mod-/programmeer-notebook dat via RCON met de
draaiende localhost-server praat. Hiermee kun je in Python items programmeren, de wereld
bouwen, spel-logica toevoegen en de datapack herbouwen+herladen — allemaal live."""
import os, nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
nb = nbf.v4.new_notebook()
C = []
def md(s): C.append(nbf.v4.new_markdown_cell(s))
def code(s): C.append(nbf.v4.new_code_cell(s))

md("""# Schatveld — live modding in Python (via RCON)
Dit notebook praat **live** met de draaiende server (`bash pybrain/play.sh`). Je programmeert
**items** en **spel-logica** in Python en stuurt ze meteen naar de wereld — geen herstart nodig.
Voer de cellen van boven naar beneden uit.""")

md("## 1. Verbind met de server (RCON)")
code(f"""import sys, os, subprocess, json
sys.path.insert(0, r"{HERE}")
from rcon import Rcon
ROOT = r"{ROOT}"
rc = Rcon(port=25575, password="schatveld", timeout=8).connect()
def mc(cmd):
    "Voer een Minecraft-commando uit en geef het antwoord terug."
    out = rc.command(cmd); print(out.strip()[:300]); return out
mc("list")   # wie is er online?""")

md("""## 2. Programmeer een ITEM in Python
Een item = een basis-item + componenten (naam, 3D-model, lore, custom_data). Deze helper
bouwt de `give`-syntax op uit Python-waarden, zodat je items kunt genereren met code.""")
code('''def give_item(player, base, *, name=None, model=None, lore=None, count=1, data=None):
    comps = []
    if name:  comps.append(f'item_name={json.dumps(name, ensure_ascii=False)}')
    if model: comps.append(f'item_model="{model}"')
    if lore:  comps.append("lore=[" + ",".join(json.dumps(l, ensure_ascii=False) for l in lore) + "]")
    if data:  comps.append("custom_data=" + data)
    comp = ("[" + ",".join(comps) + "]") if comps else ""
    return mc(f"give {player} {base}{comp} {count}")

# voorbeeld: een 'Gouden Detector' (zelfde model, gouden naam, custom lore)
give_item("@a", "minecraft:carrot_on_a_stick",
          name={"text":"Golden Detector","color":"gold","bold":True},
          model="schatveld:metal_detector",
          lore=[{"text":"A finer coil — finds more gold","color":"yellow"}],
          data="{sv_detector:1b}")''')

md("## 3. Bouw / verander de WERELD met code (fill, setblock, structuren)")
code('''def fill(x0,y0,z0, x1,y1,z1, block): return mc(f"fill {x0} {y0} {z0} {x1} {y1} {z1} {block}")
def setblock(x,y,z, block):               return mc(f"setblock {x} {y} {z} {block}")

# voorbeeld: bouw met een Python-lus een klein muurtje van een gekozen blok
mc("forceload add 24 4 30 10")
for i in range(5):
    setblock(24+i, 66, 4, "minecraft:oak_fence")''')

md("""## 4. Voeg SPEL-LOGICA toe (scoreboard, functies, triggers)
Je kunt live scoreboard-regels en herhalende logica toevoegen. Voorbeeld: geef elke speler
die op een 'grain'-veld (hay_block) staat een klein bonuspunt.""")
code('''mc("scoreboard objectives add sv_bonus dummy")
# eenmalige tick-achtige regel (voer opnieuw uit om te herhalen, of zet in de datapack-tick):
mc('execute as @a at @s if block ~ ~-1 ~ minecraft:hay_block run scoreboard players add @s sv_bonus 1')
mc("scoreboard objectives setdisplay sidebar sv_bonus")   # toon het als sidebar''')

md("""## 5. Programmeer een LOOT-tabel in Python → schrijf 'm in de datapack → herlaad
Zo verander je de beloningen echt (permanent). Definieer de tiers in Python, genereer de
loot-JSON, schrijf die in de datapack-wereldmap en herlaad.""")
code('''def loot_table(entries):
    return {"type":"minecraft:chest","pools":[{"rolls":1,"entries":[
        {"type":"minecraft:item","name":mc_id,"weight":w,
         "functions":[{"function":"minecraft:set_count","count":{"min":c0,"max":c1}}]}
        for (mc_id,w,c0,c1) in entries]}]}

# voorbeeld: maak de 'rich'-band nog goudrijker
rich = loot_table([("minecraft:gold_ingot",40,1,2),
                   ("minecraft:iron_ingot",40,1,1),
                   ("minecraft:gold_block",5,1,1),   # jackpot!
                   ("minecraft:iron_nugget",15,1,3)])
# schrijf in de WERELD-datapack (server) + herlaad
import zipfile, io, shutil
world_dp = os.path.expanduser("~/Documents/schatveld/.mcserver/schatveld/datapacks/schatveld_datapack.zip")
# (voor een blijvende wijziging: pas datapack/build_datapack.py aan en run build; hier: snelle test)
print(json.dumps(rich, indent=1)[:300], "...")
print("Tip: plak deze JSON in datapack/build_datapack.py (finds_rich) voor een blijvende wijziging.")''')

md("## 6. Herbouw + herlaad de HELE datapack vanuit Python (na code-wijzigingen)")
code('''# na het aanpassen van datapack/build_datapack.py of pybrain/marsh.py:
subprocess.run([sys.executable, os.path.join(ROOT,"datapack","build_datapack.py")], check=True)
shutil.copy(os.path.join(ROOT,"datapack","build","schatveld_datapack.zip"),
            os.path.expanduser("~/Documents/schatveld/.mcserver/schatveld/datapacks/"))
mc("reload")   # laadt de nieuwe datapack live''')

md("## 7. Bouw het marschland opnieuw (bijv. na een lay-out-wijziging in marsh.py)")
code('''import marsh, importlib; importlib.reload(marsh)
regions, points = marsh.build()
mc("forceload add 0 0 47 47")
for (x0,y0,z0,x1,y1,z1,key) in regions:
    mc(f"fill {x0} {y0} {z0} {x1} {y1} {z1} {marsh.BLOCKS[key][0]}")
for (x,y,z,key) in points:
    mc(f"setblock {x} {y} {z} {marsh.BLOCKS[key][0]}")
print("marschland herbouwd uit marsh.py")''')

md("## 8. Vraag spel-toestand op (positie, scores, blokken)")
code('''who = mc("list")
mc("data get entity @p Pos")                                   # positie
mc("execute if block ~ ~-1 ~ #schatveld:field run say op een veld")  # sta ik op een veld?
mc("scoreboard players get @p sv_metal")                       # laatste detector-waarde''')

md("""## Klaar
- **Items**: `give_item(...)` — bouw items met Python-waarden.
- **Wereld**: `fill/setblock` + lussen, of `marsh.build()` opnieuw uitvoeren.
- **Logica**: scoreboard-regels live, of permanent in `datapack/build_datapack.py`.
- **Beloningen**: `loot_table(...)` → in `build_datapack.py` plakken → rebuild + `reload`.
Voor blijvende wijzigingen: pas de bouwscripts aan en run cel 6.""")
code("rc.close()")

nb["cells"] = C
out = os.path.join(ROOT, "schatveld_dev.ipynb")
nbf.write(nb, out)
print("notebook ->", out, f"({len(C)} cellen)")
