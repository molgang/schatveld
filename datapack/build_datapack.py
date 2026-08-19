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
        # 1.21.10 datapack-formaat = 88; 1.21.9+ vereist min_format/max_format ipv supported_formats
        "pack_format": 88,
        "min_format": 48,
        "max_format": 88,
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
    "# solo/standalone-modus AAN by default (loot uit de datapack zelf, geen brain nodig).",
    "# De Python-brug zet #solo op 0 zodra die verbindt → dan is de brain de autoriteit.",
    "scoreboard objectives add sv_flags dummy",
    "scoreboard players set #solo sv_flags 1",
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

# ---- STANDALONE onboarding: geef bij de eerste keer joinen automatisch de detector +
#      schep (draait op datapack-niveau, dus GEEN cheats nodig in singleplayer). Alleen in
#      solo-modus; op de server (brain) blijft de rolkeuze via het menu. ----
mcf(f"data/{NS}/function/on_join.mcfunction", [
    "tag @s add sv_started",
    "function schatveld:shop/give_detector",
    "give @s wooden_shovel[item_name={\"translate\":\"schatveld.item.shovel\"},"
    "item_model=\"schatveld:shovel\",custom_data={sv_shovel:1b}]",
    "tellraw @s {\"translate\":\"schatveld.loaded\",\"color\":\"gold\"}",
])

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
    # solo → datapack toont zelf de waarde; brain-modus → emit een scan-event
    "execute if score #solo sv_flags matches 1 run function schatveld:solo/detect",
    "execute if score #solo sv_flags matches 0 run function schatveld:emit_scan",
])
mcf(f"data/{NS}/function/emit_scan.mcfunction", [
    "data modify storage schatveld:ev tmp set value {kind:\"scan\"}",
    "data modify storage schatveld:ev tmp.Pos set from entity @s Pos",
    "data modify storage schatveld:ev queue append from storage schatveld:ev tmp",
])
mcf(f"data/{NS}/function/solo/detect.mcfunction", [
    "function schatveld:calc_metal",
    "title @s actionbar {\"translate\":\"schatveld.detector.reading\",\"with\":"
    "[{\"score\":{\"name\":\"@s\",\"objective\":\"sv_metal\"},\"bold\":true}],\"color\":\"aqua\"}",
])

# ---- graven detecteren (tick) → loot per band; <10 altijd roestig ijzer ----
DIG_OBJS = ["dig_dirt","dig_grass","dig_coarse","dig_mud","dig_clay","dig_gravel","dig_sand","dig_farm","dig_podzol"]
tick = []
for o in DIG_OBJS:
    tick.append(f"execute as @a[scores={{{o}=1..}}] run function schatveld:on_dig")
    tick.append(f"scoreboard players set @a {o} 0")
# standalone: nieuwe speler bij de eerste join automatisch uitrusten (geen cheats nodig)
tick.insert(0, "execute if score #solo sv_flags matches 1 as @a[tag=!sv_started] run function schatveld:on_join")
mcf(f"data/{NS}/function/tick.mcfunction", tick)

# ONE BRAIN: de datapack GEEFT geen loot meer zelf — hij EMIT het dig-event naar
# storage schatveld:ev queue; de Python-brug leest dit via RCON, berekent de vondst
# (identiek aan de Roblox-kant) en pusht die terug. Zo is Python de enige autoriteit.
mcf(f"data/{NS}/function/on_dig.mcfunction", [
    # solo → de datapack geeft zelf loot (per band, <10 = roestig ijzer); brain-modus → emit
    "execute if score #solo sv_flags matches 1 run function schatveld:solo/dig",
    "execute if score #solo sv_flags matches 0 run function schatveld:emit_dig",
])
# STANDALONE: geef loot uit de eigen loot-tabellen op basis van de scoreboard-metaalwaarde.
mcf(f"data/{NS}/function/solo/dig.mcfunction", [
    "function schatveld:calc_metal",
    "execute if score @s sv_metal matches ..9 run loot give @s loot schatveld:finds/rusty_iron",
    "execute if score @s sv_metal matches 10..39 run loot give @s loot schatveld:finds/finds_common",
    "execute if score @s sv_metal matches 40..69 run loot give @s loot schatveld:finds/finds_mid",
    "execute if score @s sv_metal matches 70.. run loot give @s loot schatveld:finds/finds_rich",
    "execute at @s run particle minecraft:block{block_state:{Name:\"minecraft:dirt\"}} ~ ~0.3 ~ 0.3 0.3 0.3 0.1 20",
    "execute at @s run playsound minecraft:block.gravel.break block @s ~ ~ ~ 1 1",
    "title @s actionbar {\"translate\":\"schatveld.dig.found_solo\",\"with\":"
    "[{\"score\":{\"name\":\"@s\",\"objective\":\"sv_metal\"}}],\"color\":\"green\"}",
])
mcf(f"data/{NS}/function/emit_dig.mcfunction", [
    "data modify storage schatveld:ev tmp set value {kind:\"dig\"}",
    "data modify storage schatveld:ev tmp.Pos set from entity @s Pos",
    "data modify storage schatveld:ev queue append from storage schatveld:ev tmp",
])

# ---------------------------------------------------------------- voertuigen (datapack-benadering)
# Boer=tractor (overal), Politie=politieauto (ALLEEN op de weg). Rechtsklik grond met het
# voertuig-item → berijd een bestuurbaar (getemd+gezadeld) paard; sluipen = parkeren,
# rechtsklik het paard = weer rijden (vanilla). Blok-tag = velden waar de politie niet mag.
w(f"data/{NS}/tags/block/field.json", {"values": [
    "minecraft:farmland", "minecraft:grass_block", "minecraft:moss_block",
    "minecraft:hay_block", "minecraft:podzol", "minecraft:coarse_dirt",
    "minecraft:packed_mud", "minecraft:rooted_dirt",
]})

def veh_adv(kind, value):
    w(f"data/{NS}/advancement/deploy_{kind}.json", {
        "criteria": {"use": {"trigger": "minecraft:item_used_on_block", "conditions": {
            "item": {"predicates": {"minecraft:custom_data": "{sv_vehicle:\"%s\"}" % value}}}}},
        "rewards": {"function": f"{NS}:vehicle/deploy_{kind}"}})
veh_adv("tractor", "tractor")
veh_adv("police", "police_car")

def deploy_fn(kind, key, tag):
    return [
        f"advancement revoke @s only schatveld:deploy_{kind}",
        "summon minecraft:horse ~ ~ ~ {Tame:1b,SaddleItem:{id:\"minecraft:saddle\",count:1},"
        f"Tags:[\"sv_new\",\"{tag}\",\"sv_vehicle\"],CustomNameVisible:1b,"
        f"CustomName:'{{\"translate\":\"schatveld.item.{key}\"}}'}}",
        "ride @s mount @e[tag=sv_new,limit=1,sort=nearest,distance=..4]",
        "tag @e[tag=sv_new] remove sv_new",
        f"title @s actionbar {{\"translate\":\"schatveld.vehicle.boarded\","
        f"\"with\":[{{\"translate\":\"schatveld.item.{key}\"}}],\"color\":\"green\"}}",
    ]
mcf(f"data/{NS}/function/vehicle/deploy_tractor.mcfunction", deploy_fn("tractor", "tractor", "sv_tractor"))
mcf(f"data/{NS}/function/vehicle/deploy_police.mcfunction", deploy_fn("police", "police_car", "sv_police"))

# politieauto van de weg af (boven een veld-blok) → berijder eraf + waarschuwing (elke tick)
mcf(f"data/{NS}/function/vehicle/police_check.mcfunction", [
    "execute as @e[tag=sv_police] at @s if block ~ ~-1 ~ #schatveld:field on passengers run "
    "title @s actionbar {\"translate\":\"schatveld.vehicle.police_offroad\",\"color\":\"red\"}",
    "execute as @e[tag=sv_police] at @s if block ~ ~-1 ~ #schatveld:field on passengers run ride @s dismount",
])
with open(os.path.join(PACK, f"data/{NS}/function/tick.mcfunction"), "a", encoding="utf-8") as f:
    f.write("function schatveld:vehicle/police_check\n")

# 5-blok-interactie (politie ↔ boer): /function schatveld:interact — alleen binnen 5 blokken
mcf(f"data/{NS}/function/interact.mcfunction", [
    "execute as @s at @s if entity @a[distance=0.01..5] run title @s actionbar "
    "{\"translate\":\"schatveld.vehicle.interact\",\"with\":[{\"selector\":\"@p[distance=0.01..5]\"}],\"color\":\"aqua\"}",
    "execute as @s at @s unless entity @a[distance=0.01..5] run title @s actionbar "
    "{\"translate\":\"schatveld.vehicle.too_far\",\"color\":\"gray\"}",
])

# ---------------------------------------------------------------- loot tables
def loot(entries, rolls=1):
    return {"type": "minecraft:chest", "random_sequence": f"{NS}:finds",
            "pools": [{"rolls": rolls, "entries": entries}]}
def item(mc, weight, key, count=(1,1)):
    # gelokaliseerde vondstnaam via translate-key (werkt in solo én brain-modus).
    # 1.21: de loot-functie heet 'minecraft:set_name' met target 'custom_name' (niet set_custom_name).
    return {"type": "minecraft:item", "name": mc, "weight": weight,
            "functions": [{"function":"minecraft:set_count","count":{"min":count[0],"max":count[1]}},
                          {"function":"minecraft:set_name","name":{"translate":key},"target":"custom_name"}]}

# Realistische Land-Wursten-vondsten (vanilla-items als stand-in), namen via translate-keys.
w(f"data/{NS}/loot_table/finds/rusty_iron.json",
  loot([ item("minecraft:iron_nugget", 1, "schatveld.find.rusty_iron", (1,3)) ]))
w(f"data/{NS}/loot_table/finds/finds_common.json",
  loot([ item("minecraft:iron_nugget", 40, "schatveld.find.nails", (2,5)),
         item("minecraft:iron_ingot", 25, "schatveld.find.plough_iron"),
         item("minecraft:flint", 40, "schatveld.find.flint", (1,4)),
         item("minecraft:iron_ingot", 20, "schatveld.find.horseshoe"),
         item("minecraft:quartz", 25, "schatveld.find.quartz", (1,3)) ]))
w(f"data/{NS}/loot_table/finds/finds_mid.json",
  loot([ item("minecraft:iron_ingot", 30, "schatveld.find.tool_scrap", (1,2)),
         item("minecraft:brick", 22, "schatveld.find.sherd", (1,3)),
         item("minecraft:flint", 12, "schatveld.find.huhnergott"),
         item("minecraft:gold_nugget", 14, "schatveld.find.coin_medieval", (1,2)),
         item("minecraft:iron_ingot", 20, "schatveld.find.plough_iron") ]))
w(f"data/{NS}/loot_table/finds/finds_rich.json",
  loot([ item("minecraft:gold_ingot", 8, "schatveld.find.coin_gold"),
         item("minecraft:amethyst_shard", 6, "schatveld.find.amber", (1,2)),
         item("minecraft:copper_ingot", 12, "schatveld.find.fibula"),
         item("minecraft:emerald", 4, "schatveld.find.throne_relic"),
         item("minecraft:gold_nugget", 20, "schatveld.find.coin_hoard", (2,6)) ]))

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
