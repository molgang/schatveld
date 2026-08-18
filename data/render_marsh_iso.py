#!/usr/bin/env python3
"""render_marsh_iso — isometrische voxel-render van het écht-gebouwde Schatveld-
marschland (dezelfde `pybrain/marsh.py`-spec die `build_marsh.py` live in Minecraft
plaatst). Painter's-algoritme met top/links/rechts-vlakbelichting; pure numpy + PIL.
Output: data/schatveld_marsh_iso.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pybrain"))
import marsh

TW, TH, CH = 7, 4, 5          # tegel halfbreedte, halfhoogte, kubushoogte (px)
FLOOR = marsh.BASE - 1         # onderkant van de geëxtrudeerde prisma's


def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)


def render():
    hi = marsh.voxels()                       # {(x,z): {y: rgb}}
    # heightmap-oppervlak per kolom
    surf = {}
    for (x, z), col in hi.items():
        y = max(col)
        surf[(x, z)] = (y, col[y])

    def proj(x, y, z):
        sx = (x - z) * TW
        sy = (x + z) * TH - (y - FLOOR) * CH
        return sx, sy

    xs = [proj(x, s[0], z) for (x, z), s in surf.items()]
    minx = min(p[0] for p in xs) - TW * 2
    maxx = max(p[0] for p in xs) + TW * 2
    miny = min(proj(x, s[0], z)[1] for (x, z), s in surf.items()) - TH * 2
    maxy = max(proj(x, FLOOR, z)[1] for (x, z), s in surf.items()) + CH + TH * 2
    def fnt(sz):
        for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                  "/System/Library/Fonts/Helvetica.ttc"):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
        return ImageFont.load_default()

    TITLE = "SCHATVELD — marschland Weddewarden (Land Wursten)"
    SUB = ("isometrische render van de live in Minecraft gebouwde wereld — "
           "Watt · Deich · Wurt + boerderij · Gräben · gewas-Flurstücke")
    PAD_T = 78
    text_w = max(int(fnt(26).getlength(TITLE)), int(fnt(14).getlength(SUB))) + 48
    W = max(int(maxx - minx) + 40, text_w)
    H = int(maxy - miny) + PAD_T + 60
    ox = -minx + 20
    oy = -miny + PAD_T

    # lucht-gradiënt
    img = Image.new("RGB", (W, H), (18, 22, 30))
    top, bot = (30, 42, 66), (14, 17, 24)
    px = img.load()
    for yy in range(H):
        t = yy / H
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for xx in range(W):
            px[xx, yy] = c
    d = ImageDraw.Draw(img, "RGBA")

    # teken van achter (kleine x+z) naar voren (grote x+z)
    for (x, z) in sorted(surf, key=lambda k: (k[0] + k[1], k[0])):
        y, rgb = surf[(x, z)]
        cx = proj(x, y, z)[0] + ox
        cy = proj(x, y, z)[1] + oy
        is_water = rgb == marsh.BLOCKS["water"][1]
        # skirt-hoogte tot de vloer
        skirt = (y - FLOOR) * CH
        top_c = shade(rgb, 1.0)
        left_c = shade(rgb, 0.72)
        right_c = shade(rgb, 0.52)
        # linker verticale vlak
        d.polygon([(cx - TW, cy), (cx, cy + TH),
                   (cx, cy + TH + skirt), (cx - TW, cy + skirt)], fill=left_c)
        # rechter verticale vlak
        d.polygon([(cx + TW, cy), (cx, cy + TH),
                   (cx, cy + TH + skirt), (cx + TW, cy + skirt)], fill=right_c)
        # bovenvlak (ruit); water iets doorschijnend + glans
        if is_water:
            d.polygon([(cx, cy - TH), (cx + TW, cy), (cx, cy + TH), (cx - TW, cy)],
                      fill=(top_c[0], top_c[1], top_c[2], 235))
            d.line([(cx - TW + 2, cy - 1), (cx, cy + TH - 1)], fill=(150, 190, 230, 120), width=1)
        else:
            d.polygon([(cx, cy - TH), (cx + TW, cy), (cx, cy + TH), (cx - TW, cy)], fill=top_c)

    # titel + onderschrift
    d.text((22, 20), TITLE, font=fnt(26), fill=(230, 194, 41))
    d.text((24, 52), SUB, font=fnt(14), fill=(200, 210, 224))

    # legenda
    leg = [("Watt / Gräben (water)", "water"), ("Deich (dijk)", "deich"),
           ("Wurt + boerderij", "planks"), ("graan", "wheat"),
           ("aardappel", "potato"), ("biet", "beet"), ("klaver", "clover")]
    lx, ly = 24, H - 44
    for i, (label, key) in enumerate(leg):
        col = marsh.BLOCKS[key][1]
        bx = lx + (i % 4) * 220
        by = ly + (i // 4) * 20
        d.rectangle([bx, by, bx + 14, by + 14], fill=col, outline=(60, 66, 78))
        d.text((bx + 20, by), label, font=fnt(13), fill=(206, 214, 226))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schatveld_marsh_iso.png")
    img.save(out)
    print("iso-render ->", out, f"({W}x{H})")
    return out


if __name__ == "__main__":
    render()
