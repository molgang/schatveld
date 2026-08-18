"""cadastre — Flurstück-grid (port van roblox/src/shared/Cadastre.lua).
Zelfde deterministische indeling als de Roblox-wereld: smalle marschstroken,
een Wurt bij Weddewarden in het westen, Deich/kust aan de westrand."""
from . import config

_parcels = []
_block_to_parcel = {}


def _key(c, r):
    return f"{c}:{r}"


def build(seed: int = None):
    global _parcels, _block_to_parcel
    _parcels = []
    _block_to_parcel = {}
    cols, rows = config.GRID["cols"], config.GRID["rows"]
    stripW = 4
    flur = 1
    zaehler = 100
    for c0 in range(0, cols, stripW):
        for seg in (0, 1):
            r0 = seg * (rows // 2)
            r1 = (rows // 2 - 1) if seg == 0 else rows - 1
            zaehler += 2
            nenner = 30 + (flur * 3 + seg) % 40
            wurt = (c0 <= 8 and seg == 0)
            use = "Wurt" if wurt else ("Deich" if c0 <= 1 else "Acker")
            coastal = (c0 <= 3)
            p = {
                "id": f"Weddewarden-{flur}-{zaehler}/{nenner}",
                "gemarkung": "Weddewarden", "flur": flur, "zaehler": zaehler,
                "nenner": nenner, "owner": None, "use": use, "blocks": [],
                "coastal": coastal, "wurt": wurt,
            }
            for c in range(c0, min(c0 + stripW, cols)):
                for r in range(r0, r1 + 1):
                    p["blocks"].append((c, r))
                    _block_to_parcel[_key(c, r)] = p
            _parcels.append(p)
            flur += 1


def parcel_at(col, row):
    return _block_to_parcel.get(_key(col, row))


def all_parcels():
    return _parcels


def context(col, row):
    p = parcel_at(col, row)
    if not p:
        return {"coastal": False, "wurt": False}
    return {"coastal": p["coastal"], "wurt": p["wurt"]}


build()
