#!/usr/bin/env python3
"""
build_datapack.py — genereert de Schatveld-datapack (Minecraft Java 1.21.x) én een
Modrinth .mrpack, zonder mod. Kernloop:
  * per blok een deterministische metaalwaarde 0..100 (scoreboard-hash van coords)
  * metaaldetector-item (carrot_on_a_stick + custom_data) dat de waarde meldt
  * graven (mined-objectives) geeft loot per waarde-band; < 10 = ALTIJD roestig ijzer
Realistische Land-Wursten-vondsten via vanilla-items als stand-in.
Draai:  python3 build_datapack.py   ->  build/schatveld_datapack.zip + schatveld.mrpack
"""
import json, os, shutil, zipfile, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
PACK = os.path.join(OUT, "schatveld_datapack")
NS = "schatveld"

def w(path, content):
    full = os.path.join(PACK, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2, ensure_ascii=False)
    open(full, "w", encoding="utf-8").write(content)

def mcf(path, lines):
    w(path, "\n".join(lines) + "\n")

# ---------------------------------------------------------------- pack.mcmeta
# pack_format 61 = 1.21.4; supported_formats-range dekt 1.21 .. 1.21.10 zodat de
# pack zonder "incompatible"-waarschuwing laadt over de hele 1.21-lijn.
w("pack.mcmeta", {
    "pack": {
        "description": "Schatveld Weddewarden — schatgraven in het Land-Wursten marschveld",
        "pack_format": 61,
        "supported_formats": {"min_inclusive": 48, "max_inclusive": 99},
    }
})

# ---------------------------------------------------------------- load / tick hooks
w("data/minecraft/tags/function/load.json", {"values": [f"{NS}:load"]})
w("data/minecraft/tags/function/tick.json", {"values": [f"{NS}:tick"]})

# ---- load: scoreboards + welkom ----
mcf(f"data/{NS}/function/load.mcfunction", [
    "# objectieven",
    "scoreboard objectives add sv_metal dummy \"Metaalwaarde\"",
    "scoreboard objectives add sv_x dummy",
    "scoreboard objectives add sv_z dummy",
    "scoreboard objectives add sv_role dummy \"Rol\"",
    "scoreboard objectives add sv_choose trigger",
    "scoreboard objectives add sv_coins dummy \"MolCoin\"",
    "# graven detecteren: mined-objectieven voor typische marsch-grondblokken",
    "scoreboard objectives add dig_dirt minecraft.mined:minecraft.dirt",
    "scoreboard objectives add dig_grass minecraft.mined:minecraft.grass_block",
    "scoreboard objectives add dig_coarse minecraft.mined:minecraft.coarse_dirt",
    "scoreboard objectives add dig_mud minecraft.mined:minecraft.mud",
    "scoreboard objectives add dig_clay minecraft.mined:minecraft.clay",
    "scoreboard objectives add dig_gravel minecraft.mined:minecraft.gravel",
    "scoreboard objectives add dig_sand minecraft.mined:minecraft.sand",
    "scoreboard objectives add dig_farm minecraft.mined:minecraft.farmland",
    "scoreboard objectives add dig_podzol minecraft.mined:minecraft.podzol",
    "# hash-constanten",
    "scoreboard players set #c101 sv_metal 101",
    "# event-queue init (one brain: Python leest hier de dig/scan-events)",
    "data modify storage schatveld:ev queue set value []",
    "tellraw @a {\"translate\":\"schatveld.loaded\",\"color\":\"gold\"}",
])

# ---- menu / rollen (alle tekst via translate-keys → taal volgt de client-instelling) ----
mcf(f"data/{NS}/function/menu.mcfunction", [
    "tellraw @s [\"\",{\"translate\":\"schatveld.menu.title\",\"color\":\"gold\",\"bold\":true},{\"text\":\"\\n\"},"
    "{\"translate\":\"schatveld.menu.choose\",\"color\":\"white\"},"
    "{\"translate\":\"schatveld.role.archeoloog\",\"color\":\"aqua\",\"clickEvent\":{\"action\":\"run_command\",\"value\":\"/function schatveld:role/archeoloog\"}},"
    "{\"text\":\"  \"},"
    "{\"translate\":\"schatveld.role.boer\",\"color\":\"green\",\"clickEvent\":{\"action\":\"run_command\",\"value\":\"/function schatveld:role/boer\"}},"
    "{\"text\":\"  \"},"
    "{\"translate\":\"schatveld.role.politie\",\"color\":\"blue\",\"clickEvent\":{\"action\":\"run_command\",\"value\":\"/function schatveld:role/politie\"}}]",
])
for role, code, item in (("archeoloog", 2, None), ("boer", 1, None), ("politie", 3, None)):
    lines = [f"scoreboard players set @s sv_role {code}",
             f"tag @s add sv_{role}",
             f"tellraw @s {{\"translate\":\"schatveld.role.chosen\",\"with\":[{{\"translate\":\"schatveld.role.{role}\"}}],\"color\":\"yellow\"}}"]
    if role == "archeoloog":
        lines.append("function schatveld:shop/give_detector")
        lines.append("give @s wooden_shovel[item_name={\"translate\":\"schatveld.item.shovel\"},"
                     "item_model=\"schatveld:shovel\",custom_data={sv_shovel:1b}]")
    elif role == "boer":
        # tractor-voertuigitem (custom 3D-model); rechtsklik = op-/afstappen (voertuigsysteem)
        lines.append("give @s minecraft:stick[item_model=\"schatveld:tractor\","
                     "item_name={\"translate\":\"schatveld.item.tractor\"},custom_data={sv_vehicle:\"tractor\"}]")
    elif role == "politie":
        lines.append("give @s minecraft:stick[item_model=\"schatveld:police_car\","
                     "item_name={\"translate\":\"schatveld.item.police_car\"},custom_data={sv_vehicle:\"police_car\"}]")
    mcf(f"data/{NS}/function/role/{role}.mcfunction", lines)

# ---- winkel: geef de metaaldetector (carrot_on_a_stick + custom_data + 3D-model) ----
mcf(f"data/{NS}/function/shop/give_detector.mcfunction", [
    "give @s carrot_on_a_stick[item_name={\"translate\":\"schatveld.item.detector\",\"color\":\"aqua\"},"
    "item_model=\"schatveld:metal_detector\","
    "custom_data={sv_detector:1b},"
    "lore=[{\"translate\":\"schatveld.item.detector.lore\",\"color\":\"gray\"}]]",
    "tellraw @s {\"translate\":\"schatveld.detector.received\",\"color\":\"green\"}",
])

# ---- metaalwaarde berekenen voor de speler-positie (deterministische hash) ----
# We lezen de blokcoords van de speler (Pos) → sv_x, sv_z, reduceren mod 101 en
# mixen tot 0..100. Zelfde CONCEPT als de Roblox-hash (niet bit-identiek).
mcf(f"data/{NS}/function/calc_metal.mcfunction", [
    "execute store result score @s sv_x run data get entity @s Pos[0] 1",
    "execute store result score @s sv_z run data get entity @s Pos[2] 1",
    "# reduceer mod 101 (blijf binnen int-bereik)",
    "scoreboard players operation @s sv_x %= #c101 sv_metal",
    "scoreboard players operation @s sv_z %= #c101 sv_metal",
    "# fix negatieve rest",
    "execute if score @s sv_x matches ..-1 run scoreboard players add @s sv_x 101",
    "execute if score @s sv_z matches ..-1 run scoreboard players add @s sv_z 101",
    "# metal = (x*31 + z*17 + x*z) % 101",
    "scoreboard players operation @s sv_metal = @s sv_x",
    "scoreboard players operation @s sv_metal *= #c31 sv_const",
    "scoreboard players operation #tz sv_const = @s sv_z",
    "scoreboard players operation #tz sv_const *= #c17 sv_const",
    "scoreboard players operation @s sv_metal += #tz sv_const",
    "scoreboard players operation #xz sv_const = @s sv_x",
    "scoreboard players operation #xz sv_const *= @s sv_z",
    "scoreboard players operation @s sv_metal += #xz sv_const",
    "scoreboard players operation @s sv_metal %= #c101 sv_metal",
])
# consts voor calc
mcf(f"data/{NS}/function/load_const.mcfunction", [
    "scoreboard objectives add sv_const dummy",
    "scoreboard players set #c31 sv_const 31",
    "scoreboard players set #c17 sv_const 17",
])
# haak load_const aan load
with open(os.path.join(PACK, f"data/{NS}/function/load.mcfunction"), "a", encoding="utf-8") as f:
    f.write("function schatveld:load_const\n")

# ---- detector gebruikt op blok → meld de waarde ----
w(f"data/{NS}/advancement/use_detector.json", {
    "criteria": {"use": {"trigger": "minecraft:item_used_on_block", "conditions": {
        # partial match via predicates (SNBT) — robuust voor byte-waarde 1b
        "item": {"predicates": {"minecraft:custom_data": "{sv_detector:1b}"}}
    }}},
    "rewards": {"function": f"{NS}:on_detect"}
})
mcf(f"data/{NS}/function/on_detect.mcfunction", [
    "advancement revoke @s only schatveld:use_detector",
    "# emit een scan-event; de Python-brug leest de metaalwaarde uit het gedeelde veld",
    "data modify storage schatveld:ev tmp set value {kind:\"scan\"}",
    "data modify storage schatveld:ev tmp.Pos set from entity @s Pos",
    "data modify storage schatveld:ev queue append from storage schatveld:ev tmp",
])

# ---- graven detecteren (tick) → loot per band; <10 altijd roestig ijzer ----
DIG_OBJS = ["dig_dirt","dig_grass","dig_coarse","dig_mud","dig_clay","dig_gravel","dig_sand","dig_farm","dig_podzol"]
tick = []
for o in DIG_OBJS:
    tick.append(f"execute as @a[scores={{{o}=1..}}] run function schatveld:on_dig")
    tick.append(f"scoreboard players set @a {o} 0")
mcf(f"data/{NS}/function/tick.mcfunction", tick)

# ONE BRAIN: de datapack GEEFT geen loot meer zelf — hij EMIT het dig-event naar
# storage schatveld:ev queue; de Python-brug leest dit via RCON, berekent de vondst
# (identiek aan de Roblox-kant) en pusht die terug. Zo is Python de enige autoriteit.
mcf(f"data/{NS}/function/on_dig.mcfunction", [
    "function schatveld:emit_dig",
])
mcf(f"data/{NS}/function/emit_dig.mcfunction", [
    "data modify storage schatveld:ev tmp set value {kind:\"dig\"}",
    "data modify storage schatveld:ev tmp.Pos set from entity @s Pos",
    "data modify storage schatveld:ev queue append from storage schatveld:ev tmp",
])

# ---------------------------------------------------------------- loot tables
def loot(entries, rolls=1):
    return {"type": "minecraft:chest", "random_sequence": f"{NS}:finds",
            "pools": [{"rolls": rolls, "entries": entries}]}
def item(mc, weight, name, count=(1,1), lore=None):
    e = {"type": "minecraft:item", "name": mc, "weight": weight,
         "functions": [{"function":"minecraft:set_count","count":{"min":count[0],"max":count[1]}},
                       {"function":"minecraft:set_custom_name","name":{"text":name}}]}
    if lore:
        e["functions"].append({"function":"minecraft:set_lore","lore":[{"text":lore}]})
    return e

# Realistische Land-Wursten-vondsten (vanilla-items als stand-in).
w(f"data/{NS}/loot_table/finds/rusty_iron.json",
  loot([ item("minecraft:iron_nugget", 1, "Roestig ijzer", (1,3), "roestig agrarisch ijzer") ]))
w(f"data/{NS}/loot_table/finds/finds_common.json",
  loot([ item("minecraft:iron_nugget", 40, "Handgesmede spijkers", (2,5)),
         item("minecraft:iron_ingot", 25, "Ploegijzer (Pflugschar)"),
         item("minecraft:flint", 40, "Feuerstein-knol", (1,4)),
         item("minecraft:iron_ingot", 20, "Hoefijzer"),
         item("minecraft:quartz", 25, "Kwartskei", (1,3)) ]))
w(f"data/{NS}/loot_table/finds/finds_mid.json",
  loot([ item("minecraft:iron_ingot", 30, "Gereedschapsschroot", (1,2)),
         item("minecraft:brick", 22, "Aardewerkscherf", (1,3)),
         item("minecraft:flint", 12, "Hühnergott (gat-vuursteen)", lore="talisman"),
         item("minecraft:gold_nugget", 14, "Middeleeuwse munt", (1,2)),
         item("minecraft:iron_ingot", 20, "Ploegijzer") ]))
w(f"data/{NS}/loot_table/finds/finds_rich.json",
  loot([ item("minecraft:gold_ingot", 8, "Gouden munt", lore="Schatzregal: eigendom Land Bremen"),
         item("minecraft:amethyst_shard", 6, "Barnsteen (Bernstein)", (1,2)),
         item("minecraft:copper_ingot", 12, "Fibula (mantelspeld)", lore="Wurt-artefact"),
         item("minecraft:emerald", 4, "Wurt-artefact (Thron-graf)", lore="Schatzregal"),
         item("minecraft:gold_nugget", 20, "Munthoard", (2,6)) ]))

# ---------------------------------------------------------------- README in de pack
w("README.txt",
  "Schatveld Weddewarden datapack\n"
  "Rol kiezen + detector:  /function schatveld:menu\n"
  "Detector: rechtsklik op grond -> metaalwaarde 0-100.\n"
  "Graven (dirt/grass/mud/clay/...) geeft vondsten; <10 = altijd roestig ijzer.\n")

# ---------------------------------------------------------------- zip + mrpack
os.makedirs(OUT, exist_ok=True)
zip_path = os.path.join(OUT, "schatveld_datapack.zip")
if os.path.exists(zip_path): os.remove(zip_path)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _dirs, files in os.walk(PACK):
        for fn in files:
            fp = os.path.join(base, fn)
            z.write(fp, os.path.relpath(fp, PACK))
print("datapack ->", zip_path, os.path.getsize(zip_path), "bytes")

# .mrpack (Modrinth modpack) met de datapack onder overrides/datapacks/
def sha(fp, algo):
    h = hashlib.new(algo)
    h.update(open(fp, "rb").read())
    return h.hexdigest()
mrpack = os.path.join(OUT, "schatveld.mrpack")
if os.path.exists(mrpack): os.remove(mrpack)
index = {
    "formatVersion": 1, "game": "minecraft", "versionId": "1.0.0",
    "name": "Schatveld Weddewarden", "summary": "Schatgraven in het Land-Wursten marschveld (datapack)",
    "files": [],
    "dependencies": {"minecraft": "1.21.4"},
}
with zipfile.ZipFile(mrpack, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("modrinth.index.json", json.dumps(index, indent=2, ensure_ascii=False))
    # datapack als loose override (kopieert naar wereld/datapacks bij install via een launcher die dat ondersteunt)
    z.write(zip_path, "overrides/datapacks/schatveld_datapack.zip")
print("mrpack   ->", mrpack, os.path.getsize(mrpack), "bytes")
