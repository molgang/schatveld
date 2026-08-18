"""loot — realistische Land-Wursten vondsten + gewogen randomizer.
Port van roblox/src/shared/LootTables.lua. Regel: value<10 => altijd roestig ijzer.
Elke find heeft een 'mc'-veld (vanilla-item als stand-in) zodat de Minecraft-brug het
kan geven met /give, en de Roblox/API-kant dezelfde id/naam/waarde deelt."""
import random

RUSTY_IRON = {"id": "rusty_iron", "name": "Roestig ijzer", "kind": "scrap",
              "value": 2, "weight": 0, "state": False, "mc": "minecraft:iron_nugget"}

TABLE = [
    {"id": "plough_iron",  "name": "Ploegijzer (Pflugschar)",    "kind": "agrarian_iron", "value": 15,  "weight": 40, "mc": "minecraft:iron_ingot"},
    {"id": "horseshoe",    "name": "Hoefijzer",                  "kind": "agrarian_iron", "value": 20,  "weight": 30, "mc": "minecraft:iron_ingot"},
    {"id": "nails",        "name": "Handgesmede spijkers",       "kind": "agrarian_iron", "value": 8,   "weight": 45, "mc": "minecraft:iron_nugget"},
    {"id": "tool_scrap",   "name": "Gereedschapsschroot",        "kind": "agrarian_iron", "value": 12,  "weight": 35, "mc": "minecraft:iron_ingot"},
    {"id": "flint",        "name": "Feuerstein-knol",            "kind": "stone",         "value": 5,   "weight": 40, "mc": "minecraft:flint"},
    {"id": "huhnergott",   "name": "Hühnergott (gat-vuursteen)", "kind": "curio",         "value": 30,  "weight": 10, "mc": "minecraft:flint"},
    {"id": "quartz",       "name": "Kwartskei",                  "kind": "stone",         "value": 6,   "weight": 25, "mc": "minecraft:quartz"},
    {"id": "amber",        "name": "Barnsteen (Bernstein)",      "kind": "gem",           "value": 90,  "weight": 6,  "mc": "minecraft:amethyst_shard"},
    {"id": "sherd",        "name": "Aardewerkscherf",            "kind": "artifact",      "value": 25,  "weight": 18, "mc": "minecraft:brick"},
    {"id": "fibula",       "name": "Fibula (mantelspeld)",       "kind": "artifact",      "value": 160, "weight": 5,  "state": True, "mc": "minecraft:copper_ingot"},
    {"id": "coin_medieval","name": "Middeleeuwse munt",          "kind": "coin",          "value": 120, "weight": 6,  "mc": "minecraft:gold_nugget"},
    {"id": "coin_gold",    "name": "Gouden munt",                "kind": "coin",          "value": 350, "weight": 2,  "state": True, "mc": "minecraft:gold_ingot"},
    {"id": "throne_relic", "name": "Wurt-artefact (Thron-graf)", "kind": "artifact",      "value": 600, "weight": 1,  "state": True, "mc": "minecraft:emerald"},
]
for _e in TABLE:
    _e.setdefault("state", False)


def roll(v: int, coastal: bool, wurt: bool, rng: random.Random) -> dict:
    vf = v / 100.0
    weights = []
    for f in TABLE:
        w = float(f["weight"])
        if f["kind"] in ("agrarian_iron", "coin"):
            w *= 0.5 + vf * 1.5
        if f["kind"] == "stone":
            w *= 1.3 - vf
        if f["id"] == "amber" and coastal:
            w *= 4
        if f["kind"] == "artifact" and wurt:
            w *= 3
        weights.append(max(w, 0.01))
    total = sum(weights)
    pick = rng.uniform(0, total)
    acc = 0.0
    for i, f in enumerate(TABLE):
        acc += weights[i]
        if pick <= acc:
            return f
    return TABLE[0]
