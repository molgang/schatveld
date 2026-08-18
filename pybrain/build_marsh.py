#!/usr/bin/env python3
"""build_marsh — plaatst het Schatveld-marschland LIVE op een draaiende Fabric-server
via RCON (/fill + /setblock), uit dezelfde spec als de iso-render (marsh.py). Bouwt bij
oorsprong OX,OZ (default 0,0). Verifieert daarna een steekproef met `execute if block`.
Gebruik:  python3 pybrain/build_marsh.py [OX OZ]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marsh
from rcon import Rcon

OX = int(sys.argv[1]) if len(sys.argv) > 1 else 0
OZ = int(sys.argv[2]) if len(sys.argv) > 2 else 0


def bid(key):
    return marsh.BLOCKS[key][0]


def build(rc):
    regions, points = marsh.build()
    n = 0
    for (x0, y0, z0, x1, y1, z1, key) in regions:
        rc.command(f"fill {OX+x0} {y0} {OZ+z0} {OX+x1} {y1} {OZ+z1} {bid(key)}")
        n += 1
    for (x, y, z, key) in points:
        rc.command(f"setblock {OX+x} {y} {OZ+z} {bid(key)}")
        n += 1
    return n, regions, points


def verify(rc, regions):
    """Steekproef: controleer een paar kenmerkende blokken met execute if block."""
    checks = [
        ("Watt-water westrand", 1, marsh.BASE, 5, "minecraft:water"),
        ("Deich-gras",          3, marsh.BASE + 3, 5, "minecraft:grass_block"),
        ("Graben-water",       12, marsh.BASE, 10, "minecraft:water"),
        ("Wurt-gras",           7, marsh.BASE + 2, 24, "minecraft:grass_block"),
        ("boerderij-dak",      11, marsh.BASE + 6, 27, "minecraft:dark_oak_planks"),
    ]
    ok = 0
    for (label, x, y, z, block) in checks:
        # 'execute if block' zonder run print "Test passed" bij een match (leesbaar via RCON)
        out = rc.command(f"execute if block {OX+x} {y} {OZ+z} {block}")
        hit = "passed" in out.lower()
        ok += hit
        print(f"   [{'v' if hit else 'x'}] {label:22s} @({x},{y},{z}) = {block}  ::  {out.strip()}")
    return ok, len(checks)


def main():
    try:
        rc = Rcon(port=25575, password="schatveld", timeout=5).connect()
    except Exception as e:
        print("Geen live server op :25575 — start met  bash pybrain/run_server.sh")
        print("(", e, ")")
        return 2
    try:
        print(f"Bouw marschland bij oorsprong ({OX},{OZ}) …")
        n, regions, points = build(rc)
        print(f"   {n} /fill+/setblock-opdrachten uitgevoerd "
              f"({marsh.W}×{marsh.D} blokken, {len(points)} details).")
        rc.command(f"say Schatveld-marschland gebouwd bij {OX} {OZ}")
        print("Verificatie (execute if block):")
        ok, tot = verify(rc, regions)
        print(f"-> {ok}/{tot} steekproeven kloppen.")
        return 0 if ok == tot else 1
    finally:
        rc.close()


if __name__ == "__main__":
    sys.exit(main())
