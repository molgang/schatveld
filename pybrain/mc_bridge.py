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


def _dig_feedback(rc, x, y, z, find, res):
    """Geef de vondst + juice (deeltjes/geluid/actionbar), volledig via translate-keys
    zodat de tekst de client-taal volgt (Opties → Taal)."""
    at = f"execute positioned {x:.2f} {y:.2f} {z:.2f} run"
    name = f'{{"translate":"schatveld.find.{find["id"]}"}}'
    # item met gelokaliseerde naam
    rc.command(f'{at} give @p[distance=..6] {find["mc"]}[minecraft:custom_name={name}] 1')
    rc.command(f'{at} particle minecraft:block{{block_state:{{Name:"minecraft:dirt"}}}} '
               f"{x:.2f} {y+0.5:.2f} {z:.2f} 0.3 0.3 0.3 0.1 30")
    rc.command(f"{at} playsound minecraft:block.gravel.break block @p[distance=..8] {x:.2f} {y:.2f} {z:.2f} 1 1")
    if res["schatzregal"] or res.get("firstFind"):
        rc.command(f"{at} playsound minecraft:entity.player.levelup block @p[distance=..8] {x:.2f} {y:.2f} {z:.2f} 1 1.4")
    color = "gold" if res["schatzregal"] else "green"
    parts = [f'{{"translate":"schatveld.dig.found","with":["{res["metal"]}",{name},"{res["payout"]}"],"color":"{color}"}}']
    if res.get("confiscated"):
        parts.append('{"text":"  "},{"translate":"schatveld.schatzregal.confiscated","color":"red"}')
    elif res["schatzregal"]:
        parts.append('{"text":"  "},{"translate":"schatveld.schatzregal.state","color":"gold"}')
    if res.get("illegal"):
        parts.append('{"text":"  "},{"translate":"schatveld.raubgrabung","color":"red"}')
    rc.command(f'{at} title @p[distance=..8] actionbar ["",{",".join(parts)}]')


def handle_event(brain, rc, kind, x, y, z):
    col, row = int(x // 1), int(z // 1)         # wereld-blokcoords = veld-coords
    v = field.value(col, row, brain.seed)
    if kind == "scan":
        col_color = "dark_gray" if v < 10 else ("gold" if v >= 70 else "yellow")
        rc.command(f"execute positioned {x:.2f} {y:.2f} {z:.2f} run "
                   f'tellraw @p[distance=..8] {{"translate":"schatveld.detector.reading",'
                   f'"with":[{{"text":"{v}","color":"{col_color}","bold":true}}],"color":"aqua"}}')
        return ("scan", v, None)
    # dig: laat de Brain de vondst bepalen (zelfde regels als Roblox)
    brain._p(MC_USER)["tools"]["Schep"] = True
    brain._p(MC_USER)["permit"] = True
    res = brain.dig(MC_USER, col, row)
    find = res["find"]
    _dig_feedback(rc, x, y, z, find, res)
    if res.get("firstFind"):
        rc.command(f'execute positioned {x:.2f} {y:.2f} {z:.2f} run tellraw @p[distance=..8] '
                   f'{{"translate":"schatveld.museum.new","with":['
                   f'{{"translate":"schatveld.find.{find["id"]}"}},"{res["museum"]}","{res["museumTotal"]}"],'
                   f'"color":"gold"}}')
    return ("dig", v, find["name"])


def run(host="127.0.0.1", port=25575, password="schatveld", poll=0.5, once=False):
    brain = Brain()

    def connect():
        rc = Rcon(host, port, password, timeout=10).connect()
        # brain-modus: zet solo/standalone UIT zodat de datapack niet óók loot geeft
        try:
            rc.command("scoreboard players set #solo sv_flags 0")
        except Exception:
            pass
        print(f"[bridge] verbonden met RCON {host}:{port} (brain-modus, solo=0)", flush=True)
        return rc

    rc = connect()
    i = 0
    while True:
        try:
            i += 1
            if i % 20 == 0:   # herbevestig brain-modus (na een /reload staat #solo weer op 1)
                rc.command("scoreboard players set #solo sv_flags 0")
            out = rc.command("data get storage schatveld:ev queue")
            events = parse_queue(out)
            if events:
                for (kind, x, y, z) in events:
                    r = handle_event(brain, rc, kind, x, y, z)
                    print(f"[bridge] {r}", flush=True)
                rc.command("data modify storage schatveld:ev queue set value []")
            if once:
                return events
            time.sleep(poll)
        except (TimeoutError, OSError, ConnectionError) as e:
            # transient (server pauzeert bij lege wereld / herstart) → herverbind i.p.v. crashen
            print(f"[bridge] RCON-fout, herverbinden: {e}", flush=True)
            try:
                rc.close()
            except Exception:
                pass
            time.sleep(2)
            try:
                rc = connect()
            except Exception as e2:
                print(f"[bridge] herverbinden mislukt: {e2}", flush=True)
                time.sleep(3)


if __name__ == "__main__":
    import sys
    pw = sys.argv[1] if len(sys.argv) > 1 else "schatveld"
    run(password=pw)
