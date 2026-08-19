"""mc_bridge.py — de Minecraft-kant van de 'one brain'.
Polt via RCON de storage-queue die de datapack bij graven/detector vult, laat de
gedeelde Brain de vondst berekenen (identiek aan de Roblox/API-kant), en pusht het
resultaat terug naar de modded server (give + tellraw). Datapack = detector,
Python = loot-autoriteit.
"""
import re
import time

from schatveld_core import Brain, field, config, cadastre, loot
from rcon import Rcon

MC_USER = "mc_player"           # gedeeld MC-profiel in de Brain (MVP: één wereld)

# --- SNBT-parse van 'data get storage schatveld:ev queue' ---
_ENTRY = re.compile(r"\{[^{}]*\}")
_KIND = re.compile(r'kind:\s*"(\w+)"')
_POS = re.compile(r"Pos:\s*\[([^\]]+)\]")


def parse_queue(snbt: str):
    """Haal (kind, x, y, z) uit de storage-uitvoer van Minecraft."""
    events = []
    for m in _ENTRY.finditer(snbt):
        blk = m.group(0)
        k = _KIND.search(blk)
        p = _POS.search(blk)
        if not k or not p:
            continue
        nums = [float(x.strip().rstrip("dfsbL")) for x in p.group(1).split(",")]
        if len(nums) >= 3:
            events.append((k.group(1), nums[0], nums[1], nums[2]))
    return events


def _mc_give(rc, x, y, z, mc_item, count, msg, color="green", special=False):
    # geef aan de dichtstbijzijnde speler bij de graaflocatie + juice (deeltjes/geluid/actionbar)
    at = f"execute positioned {x:.2f} {y:.2f} {z:.2f} run"
    rc.command(f"{at} give @p[distance=..6] {mc_item} {count}")
    # aarde-explosie + graafgeluid; bijzondere vondst = extra klank
    rc.command(f'{at} particle minecraft:block{{block_state:{{Name:"minecraft:dirt"}}}} '
               f"{x:.2f} {y+0.5:.2f} {z:.2f} 0.3 0.3 0.3 0.1 30")
    rc.command(f"{at} playsound minecraft:block.gravel.break block @p[distance=..8] {x:.2f} {y:.2f} {z:.2f} 1 1")
    if special:
        rc.command(f"{at} playsound minecraft:entity.player.levelup block @p[distance=..8] {x:.2f} {y:.2f} {z:.2f} 1 1.4")
    rc.command(f'{at} title @p[distance=..8] actionbar {{"text":"{msg}","color":"{color}"}}')


def handle_event(brain, rc, kind, x, y, z):
    col, row = int(x // 1), int(z // 1)         # wereld-blokcoords = veld-coords
    v = field.value(col, row, brain.seed)
    if kind == "scan":
        col_color = "dark_gray" if v < 10 else ("gold" if v >= 70 else "yellow")
        rc.command(f"execute positioned {x:.2f} {y:.2f} {z:.2f} run "
                   f'tellraw @p[distance=..8] ["",{{"text":"Detector (Python-brain): ","color":"aqua"}},'
                   f'{{"text":"{v}","color":"{col_color}","bold":true}},{{"text":"/100","color":"gray"}}]')
        return ("scan", v, None)
    # dig: laat de Brain de vondst bepalen (zelfde regels als Roblox)
    brain._p(MC_USER)["tools"]["Schep"] = True
    brain._p(MC_USER)["permit"] = True
    res = brain.dig(MC_USER, col, row)
    find = res["find"]
    label = find["name"].replace('"', "'")
    if res.get("confiscated"):
        tag = " [Schatzregal -> beschlagnahmt]"
    elif res["schatzregal"]:
        tag = " [Schatzregal -> Land Bremen]"
    else:
        tag = ""
    special = res["schatzregal"] or res.get("firstFind")
    _mc_give(rc, x, y, z, find["mc"], 1,
             f"metaal {res['metal']} -> {label} (EUR {res['payout']}){tag}",
             "gold" if res["schatzregal"] else "green", special=special)
    if res.get("firstFind"):
        rc.command(f'execute positioned {x:.2f} {y:.2f} {z:.2f} run tellraw @p[distance=..8] '
                   f'["",{{"text":"Neu im Landesmuseum: ","color":"gold","bold":true}},'
                   f'{{"text":"{label} ({res["museum"]}/{res["museumTotal"]})","color":"yellow"}}]')
    return ("dig", v, find["name"])


def run(host="127.0.0.1", port=25575, password="schatveld", poll=0.5, once=False):
    brain = Brain()
    with Rcon(host, port, password) as rc:
        print(f"[bridge] verbonden met RCON {host}:{port}")
        while True:
            out = rc.command("data get storage schatveld:ev queue")
            events = parse_queue(out)
            if events:
                for (kind, x, y, z) in events:
                    r = handle_event(brain, rc, kind, x, y, z)
                    print(f"[bridge] {r}")
                rc.command("data modify storage schatveld:ev queue set value []")
            if once:
                return events
            time.sleep(poll)


if __name__ == "__main__":
    import sys
    pw = sys.argv[1] if len(sys.argv) > 1 else "schatveld"
    run(password=pw)
