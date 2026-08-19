#!/usr/bin/env python3
"""build_models — procedurele 3D item-modellen (Minecraft-cuboids, à la Blockbench)
voor de metaaldetector, schep, tractor en politieauto. Genereert per model:
  assets/schatveld/models/item/<id>.json   (elements + display + textures)
  assets/schatveld/items/<id>.json          (item-model-definitie, 1.21.4+ systeem)
en de gedeelde effen-kleur-texturen assets/schatveld/textures/item/col_<naam>.png.
Plus een preview-strip (data/schatveld_models_preview.png) via een eigen iso-rasterizer.
Wordt ingebakken door build_resourcepack.py.
"""
import io, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PALETTE = {
    "grey":  (150, 152, 162), "dark": (70, 72, 82),   "yellow": (226, 192, 70),
    "brown": (150, 110, 60),  "green": (80, 140, 55),  "dgreen": (55, 100, 45),
    "black": (28, 28, 32),    "white": (226, 228, 232),"blue":   (70, 110, 190),
    "red":   (200, 60, 60),   "steel": (120, 124, 136),
}

# De metaaldetector + schep zijn 2D pixel-art ICONEN (zie FLAT_ICONS) — een 3D-model
# ziet er in het kleine inventory-slot uit als 'een paar blokjes'. Tractor + politieauto
# blijven 3D (voertuig-items).
# elk 3D-model = lijst (from[x,y,z], to[x,y,z], kleur)  — 0..16 item-ruimte, y omhoog
MODELS = {
    "tractor": [
        ((3, 4, 3), (12, 8, 13), "green"),      # motorblok/chassis
        ((9, 4, 4), (14, 7, 12), "green"),      # neus
        ((4, 8, 5), (9, 13, 11), "dgreen"),     # cabine
        ((9, 8, 9), (10, 12, 10), "steel"),     # uitlaat
        ((0, 1, 8), (4, 8, 14), "black"),       # groot achterwiel L
        ((12, 1, 8), (16, 8, 14), "black"),     # groot achterwiel R
        ((2, 1, 3), (4, 5, 6), "black"),        # klein voorwiel L
        ((12, 1, 3), (14, 5, 6), "black"),      # klein voorwiel R
    ],
    "police_car": [
        ((2, 3, 2), (14, 6, 14), "white"),      # carrosserie
        ((5, 6, 4), (11, 9, 12), "white"),      # dak/cabine
        ((4, 6, 4), (5, 9, 12), "blue"),        # voorruit
        ((11, 6, 4), (12, 9, 12), "blue"),      # achterruit
        ((6, 9, 6), (8, 10, 10), "red"),        # zwaailicht rood
        ((8, 9, 6), (10, 10, 10), "blue"),      # zwaailicht blauw
        ((1, 1, 3), (3, 4, 6), "black"),        # wielen
        ((1, 1, 10), (3, 4, 13), "black"),
        ((13, 1, 3), (15, 4, 6), "black"),
        ((13, 1, 10), (15, 4, 13), "black"),
    ],
}

DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.88, 0.88, 0.88]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.5, 0.5, 0.5]},
    "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [0, 1.5, 0], "scale": [0.7, 0.7, 0.7]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, 1, 0], "scale": [0.7, 0.7, 0.7]},
}


def solid_png(rgb):
    a = np.zeros((16, 16, 4), np.uint8); a[:, :] = (*rgb, 255)
    b = io.BytesIO(); Image.fromarray(a, "RGBA").save(b, "PNG"); return b.getvalue()


# ---- 2D pixel-art iconen (metaaldetector + schep) — nette inventory-sprite ----
def _canvas():
    return np.zeros((16, 16, 4), np.uint8)

def _px(a, x, y, rgb, al=255):
    if 0 <= x < 16 and 0 <= y < 16:
        a[y, x] = (rgb[0], rgb[1], rgb[2], al)

def _outline(a, col=(24, 22, 30)):
    # donkere rand rond alle niet-transparante pixels → leest scherp op 16px
    out = a.copy()
    for y in range(16):
        for x in range(16):
            if a[y, x, 3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 16 and 0 <= ny < 16 and a[ny, nx, 3] > 0:
                        out[y, x] = (col[0], col[1], col[2], 255); break
    return out

def icon_metal_detector():
    a = _canvas()
    grey=(168,172,184); greyD=(122,126,140); box=(72,76,92); screen=(96,224,140)
    yel=(236,202,84); yelD=(192,160,62); hole=(58,60,72); hi=(255,230,150)
    cx, cy = 7.5, 12.3                               # zoekspoel = gevulde schijf
    for y in range(16):
        for x in range(16):
            d = (x-cx)**2 + ((y-cy)*1.35)**2
            if d <= 15: _px(a, x, y, yel if d > 5 else hole)
    _px(a,4,12,hi); _px(a,5,11,hi)                  # glans op de spoel
    for y in range(3,11):                           # steel (dik)
        _px(a,7,y,grey); _px(a,8,y,greyD)
    for x in range(6,10): _px(a,x,2,box)            # handvat
    for y in range(4,8):                            # controle-box
        for x in range(9,13): _px(a,x,y,box)
    _px(a,10,5,screen); _px(a,11,5,screen)          # groen schermpje
    return _outline(a)

def icon_shovel():
    a = _canvas()
    brown=(164,120,66); brownD=(122,90,50); steel=(176,180,192); steelD=(124,128,142); hi=(220,224,234)
    for x in range(6,10): _px(a,x,1,brownD)         # D-grip
    for y in range(2,9):                            # steel (dik)
        _px(a,7,y,brown); _px(a,8,y,brownD)
    for (x0,x1,y) in [(5,10,9),(4,11,10),(4,11,11),(4,11,12),(5,10,13),(6,9,14)]:  # spade-blad
        for x in range(x0,x1+1): _px(a,x,y,steel)
        _px(a,x0,y,steelD); _px(a,x1,y,steelD)
    _px(a,6,10,hi); _px(a,6,11,hi)                  # glans
    return _outline(a)

FLAT_ICONS = {"metal_detector": icon_metal_detector, "shovel": icon_shovel}


def model_json(boxes):
    cols = sorted({c for _, _, c in boxes})
    textures = {c: f"schatveld:item/col_{c}" for c in cols}
    textures["particle"] = f"schatveld:item/col_{cols[0]}"
    els = []
    for (f, t, c) in boxes:
        faces = {d: {"texture": f"#{c}", "uv": [0, 0, 16, 16]}
                 for d in ("north", "south", "east", "west", "up", "down")}
        els.append({"from": list(f), "to": list(t), "faces": faces})
    return {"textures": textures, "elements": els, "display": DISPLAY}


# ------- eigen iso-preview van de cuboids -------
def voxelize(boxes, N=16):
    grid = {}
    for (f, t, c) in boxes:
        for x in range(f[0], t[0]):
            for y in range(f[1], t[1]):
                for z in range(f[2], t[2]):
                    if 0 <= x < N and 0 <= y < N and 0 <= z < N:
                        grid[(x, y, z)] = PALETTE[c]
    return grid


def render_preview(out):
    TW, TH, CH = 6, 3, 4
    flat = list(FLAT_ICONS)
    solid = list(MODELS)
    names = flat + solid
    cellw = 200
    W, H = cellw * len(names), 260
    img = Image.new("RGB", (W, H), (22, 26, 34)); d = ImageDraw.Draw(img, "RGBA")
    def fnt(s):
        for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
            try: return ImageFont.truetype(p, s)
            except Exception: pass
        return ImageFont.load_default()
    def shade(c, fr): return tuple(max(0, min(255, int(v * fr))) for v in c)
    for i, name in enumerate(names):
        if name in FLAT_ICONS:                       # 2D icoon: 9× vergroot (zoals inventory)
            sprite = Image.fromarray(FLAT_ICONS[name](), "RGBA").resize((144, 144), Image.NEAREST)
            img.paste(sprite, (i * cellw + (cellw - 144) // 2, 60), sprite)
        else:                                        # 3D-model: iso-voxel
            grid = voxelize(MODELS[name]); ox = i * cellw + cellw // 2; oy = 150
            for (x, y, z) in sorted(grid, key=lambda k: (k[0] + k[2], k[1], k[0] + k[2])):
                rgb = grid[(x, y, z)]
                cx = ox + (x - z) * TW; cy = oy + (x + z) * TH - y * CH
                d.polygon([(cx - TW, cy), (cx, cy + TH), (cx, cy + TH + CH), (cx - TW, cy + CH)], fill=shade(rgb, .72))
                d.polygon([(cx + TW, cy), (cx, cy + TH), (cx, cy + TH + CH), (cx + TW, cy + CH)], fill=shade(rgb, .52))
                d.polygon([(cx, cy - TH), (cx + TW, cy), (cx, cy + TH), (cx - TW, cy)], fill=rgb)
        tag = "2D-icoon" if name in FLAT_ICONS else "3D-model"
        d.text((i * cellw + 14, 224), f"{name}  ({tag})", font=fnt(13), fill=(226, 214, 120))
    d.text((14, 12), "Schatveld — item-iconen: metaaldetector + schep = 2D pixel-sprite, "
           "tractor + politieauto = 3D", font=fnt(14), fill=(150, 220, 255))
    img.save(out); print("preview ->", out, f"({W}x{H})")


def write_all():
    base = os.path.join(HERE, "build", "models_assets")
    tex = os.path.join(base, "assets/schatveld/textures/item")
    mdl = os.path.join(base, "assets/schatveld/models/item")
    itm = os.path.join(base, "assets/schatveld/items")
    for p in (tex, mdl, itm): os.makedirs(p, exist_ok=True)
    for name, rgb in PALETTE.items():
        open(os.path.join(tex, f"col_{name}.png"), "wb").write(solid_png(rgb))
    for name, boxes in MODELS.items():
        json.dump(model_json(boxes), open(os.path.join(mdl, f"{name}.json"), "w"), indent=2)
        json.dump({"model": {"type": "minecraft:model", "model": f"schatveld:item/{name}"}},
                  open(os.path.join(itm, f"{name}.json"), "w"), indent=2)
    # 2D pixel-art iconen: texture + item/generated-model + items-entry
    for name, fn in FLAT_ICONS.items():
        b = io.BytesIO(); Image.fromarray(fn(), "RGBA").save(b, "PNG")
        open(os.path.join(tex, f"{name}.png"), "wb").write(b.getvalue())
        json.dump({"parent": "minecraft:item/generated",
                   "textures": {"layer0": f"schatveld:item/{name}"}},
                  open(os.path.join(mdl, f"{name}.json"), "w"), indent=2)
        json.dump({"model": {"type": "minecraft:model", "model": f"schatveld:item/{name}"}},
                  open(os.path.join(itm, f"{name}.json"), "w"), indent=2)
    print(f"assets -> {base}  ({len(MODELS)} 3D-modellen, {len(FLAT_ICONS)} 2D-iconen, "
          f"{len(PALETTE)} kleur-texturen)")
    return base


if __name__ == "__main__":
    write_all()
    render_preview(os.path.join(ROOT, "data", "schatveld_models_preview.png"))
