#!/usr/bin/env python3
"""build_resourcepack — genereert een Schatveld-resource pack met procedurele 16×16
pixel-art texturen (PIL) die de vanilla stand-in-items van de loot vervangen door
thematische vondsten + een echte metaaldetector. Output: build/schatveld_resources.zip
"""
import io, json, math, os, zipfile
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)
N = 16


def canvas():
    return np.zeros((N, N, 4), dtype=np.uint8)


def px(a, x, y, rgb, al=255):
    if 0 <= x < N and 0 <= y < N:
        a[y, x] = (rgb[0], rgb[1], rgb[2], al)


def disc(a, cx, cy, r, rgb, al=255):
    for y in range(N):
        for x in range(N):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                px(a, x, y, rgb, al)


def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def metal_detector():
    a = canvas()
    shaft = (150, 152, 162); dark = (92, 94, 104); coil = (226, 192, 70)
    for y in range(2, 12):                      # steel
        px(a, 7, y, shaft); px(a, 8, y, shaft); px(a, 8, y, shade(shaft, .8))
    for x in range(5, 11):                       # handvat
        px(a, x, 1, dark); px(a, x, 2, dark)
    # zoekspoel (ring) onderaan
    for y in range(N):
        for x in range(N):
            dd = (x - 7.5) ** 2 + ((y - 13) * 1.4) ** 2
            if 6 < dd < 16:
                px(a, x, y, coil)
            elif dd <= 6:
                px(a, x, y, shade(coil, .55))
    return a


def amber():
    a = canvas()
    base = (232, 168, 40)
    for y in range(N):
        for x in range(N):
            dx, dy = abs(x - 8), abs(y - 8)
            if dx + dy <= 6:                      # ruit-gem
                f = 1.15 - (dx + dy) / 14
                al = 235 if dx + dy < 6 else 170
                px(a, x, y, shade(base, f), al)
    for x in range(6, 9):
        px(a, x, 5, (255, 224, 150), 220)         # glans
    return a


def wurt_relic():
    a = canvas()               # bronzen fibula (boogspeld)
    bronze = (168, 116, 60); verd = (86, 150, 116)
    for t in range(0, 180, 8):
        x = int(8 + 6 * math.cos(math.radians(t)))
        y = int(11 - 6 * math.sin(math.radians(t)))
        px(a, x, y, bronze); px(a, x, y + 1, shade(bronze, .7))
    for (vx, vy) in [(5, 8), (11, 9), (8, 5)]:
        px(a, vx, vy, verd)                       # verdigris
    for x in range(4, 13):
        px(a, x, 12, shade(bronze, .8))           # naald
    return a


def gold_coin():
    a = canvas()
    disc(a, 8, 8, 6, (150, 120, 40))
    disc(a, 8, 8, 5, (228, 190, 72))
    disc(a, 8, 8, 3, (245, 214, 110))
    for x in range(6, 11):
        px(a, x, 8, (176, 140, 48))               # emboss-streep
    return a


def rusty_nails():
    a = canvas()
    rust = (146, 84, 46); drk = (92, 50, 28)
    for i, off in enumerate((-3, 1)):
        for k in range(9):
            x = 5 + off + k // 2; y = 3 + k
            px(a, x, y, rust); px(a, x + 1, y, shade(rust, .75))
        px(a, 5 + off, 2, drk); px(a, 6 + off, 2, drk)   # kop
    return a


def ploughshare():
    a = canvas()               # gesmede ijzeren ploegschaar (driehoek)
    steel = (152, 156, 166)
    for y in range(3, 14):
        w = int((y - 3) * 0.7)
        for x in range(8 - w, 8 + w + 1):
            px(a, x, y, steel)
        px(a, 8 - w, y, (210, 214, 224))          # snijkant-glans
    return a


def potsherd():
    a = canvas()               # terracotta-scherf
    terra = (172, 92, 58)
    pts = [(4, 6), (5, 5), (6, 5), (7, 6), (8, 7), (9, 9), (9, 11),
           (8, 12), (6, 12), (5, 11), (4, 9)]
    for y in range(N):
        for x in range(N):
            if 4 <= x <= 10 and 5 <= y <= 12 and (x + y) % 1 == 0:
                if (x - 7) ** 2 + (y - 8) ** 2 <= 13:
                    px(a, x, y, shade(terra, 0.85 + ((x * y) % 5) / 20))
    for x in range(5, 10):
        px(a, x, 7, (120, 60, 40))                # beschildering
    return a


TEX = {
    "carrot_on_a_stick": metal_detector,   # = de metaaldetector
    "amethyst_shard": amber,               # = barnsteen
    "emerald": wurt_relic,                 # = Wurt-artefact (fibula)
    "gold_ingot": gold_coin,               # = gouden munt
    "iron_nugget": rusty_nails,            # = roestige spijkers
    "iron_ingot": ploughshare,             # = ploegijzer
    "brick": potsherd,                     # = potscherf
}


def pack_icon():
    a = canvas()
    for y in range(N):
        for x in range(N):
            px(a, x, y, (46, 78, 54) if (x + y) % 6 else (60, 96, 66))
    disc(a, 8, 9, 4, (226, 192, 70))       # gouden vondst op het veld
    for x in range(2, 14):
        px(a, x, 3, (58, 104, 158))        # water-horizon
    return a


def main():
    out = os.path.join(BUILD, "schatveld_resources.zip")
    mcmeta = {
        "pack": {
            # 1.21.10 resource-pack-formaat = 69; 1.21.9+ vereist min_format/max_format
            "pack_format": 69,
            "min_format": 34,
            "max_format": 69,
            "description": "Schatveld — vondsten & metaaldetector (Weddewarden)",
        }
    }
    # 3D item-modellen (metaaldetector/schep/tractor/politieauto) genereren
    import build_models
    models_base = build_models.write_all()

    # taalbestanden (en_us = basis; de/fr/ru/... vullen aan → speler kiest in Opties → Taal)
    lang_dir = os.path.join(HERE, "lang")
    langs = sorted(f for f in os.listdir(lang_dir) if f.endswith(".json")) if os.path.isdir(lang_dir) else []

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps(mcmeta, indent=2))
        b = io.BytesIO(); Image.fromarray(pack_icon(), "RGBA").save(b, "PNG")
        z.writestr("pack.png", b.getvalue())
        for item, fn in TEX.items():
            b = io.BytesIO()
            Image.fromarray(fn(), "RGBA").save(b, "PNG")
            z.writestr(f"assets/minecraft/textures/item/{item}.png", b.getvalue())
        # modellen + items + effen-kleur-texturen inbakken
        for root, _dirs, files in os.walk(models_base):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, models_base))
        # lang-bestanden
        for lf in langs:
            with open(os.path.join(lang_dir, lf), encoding="utf-8") as fh:
                z.writestr(f"assets/schatveld/lang/{lf}", fh.read())
    print(f"resource pack -> {out}  ({len(TEX)} vondst-texturen, "
          f"{len(build_models.MODELS)} 3D-modellen, {len(langs)} talen)")
    return out


if __name__ == "__main__":
    main()
