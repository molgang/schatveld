"""marsh — het Schatveld-marschlandschap als een lijst box-regio's + detailblokken.
Eén bron voor zowel de live Minecraft-bouw (via /fill over RCON) als de isometrische
render (data/render_marsh_iso.py). Gethematiseerd op Weddewarden / Land Wursten:
Watt/water aan de westrand, een Deich (dijk), een verhoogde Wurt met boerderij, Gräben
(sloten) tussen de percelen, en gewas-Flurstücke.
"""

# blokdefinitie: sleutel -> (minecraft-id, kleur rgb voor de render)
BLOCKS = {
    "water":    ("minecraft:water",       (58, 104, 158)),
    "clay":     ("minecraft:clay",        (150, 158, 168)),
    "dirt":     ("minecraft:dirt",        (108, 84, 60)),
    "grass":    ("minecraft:grass_block", (94, 140, 74)),
    "deich":    ("minecraft:grass_block", (78, 128, 66)),
    "farmland": ("minecraft:farmland",    (96, 72, 50)),
    "wheat":    ("minecraft:hay_block",   (206, 182, 78)),   # rijp graan (render)
    "potato":   ("minecraft:rooted_dirt", (92, 128, 70)),    # aardappel-akker
    "beet":     ("minecraft:red_mushroom_block", (150, 96, 92)),
    "clover":   ("minecraft:moss_block",  (74, 132, 92)),
    "path":     ("minecraft:dirt_path",   (132, 116, 82)),
    "planks":   ("minecraft:oak_planks",  (164, 132, 86)),
    "log":      ("minecraft:oak_log",     (110, 88, 58)),
    "cobble":   ("minecraft:cobblestone", (122, 122, 126)),
    "roof":     ("minecraft:dark_oak_planks", (74, 56, 38)),
    "reed":     ("minecraft:bamboo",      (120, 150, 80)),
}

W, D = 48, 36        # marsch afmeting (x = west→oost, z = zuid→noord)
BASE = 63            # grondhoogte (y)


def build():
    """Return (regions, points): regions=[(x0,y0,z0,x1,y1,z1,key)], points=[(x,y,z,key)]."""
    regions, points = [], []

    def box(x0, z0, x1, z1, y0, y1, key):
        regions.append((x0, y0, z0, x1, y1, z1, key))

    # 1) basis: klei-maaiveld over het hele veld
    box(0, 0, W - 1, D - 1, BASE, BASE, "clay")

    # 2) Watt/zee aan de westrand (x 0-2), 1 lager, water
    box(0, 0, 2, D - 1, BASE, BASE, "water")

    # 3) Deich (dijk) x 3-4, +3 hoog, gras
    box(3, 0, 4, D - 1, BASE + 1, BASE + 3, "deich")
    box(3, 0, 4, D - 1, BASE, BASE, "dirt")

    # 4) Gräben (sloten): waterstroken elke 8 blokken (x 12,20,28,36,44), 1 breed
    for gx in (12, 20, 28, 36, 44):
        box(gx, 0, gx, D - 1, BASE, BASE, "water")

    # 5) Wurt (woonheuvel): x 6-15, z 22-33, verhoogd +2, gras op klei
    box(6, 22, 15, 33, BASE + 1, BASE + 2, "grass")
    # boerderij bovenop de Wurt
    fx, fz, fy = 9, 26, BASE + 3
    box(fx, fz, fx + 4, fz + 3, fy, fy + 2, "planks")          # muren (massief, render vult)
    box(fx, fz, fx + 4, fz + 3, fy, fy, "cobble")              # fundering
    box(fx - 1, fz - 1, fx + 5, fz + 4, fy + 3, fy + 3, "roof")  # dak (overstek)
    for cx in (fx, fx + 4):
        for cz in (fz, fz + 3):
            points.append((cx, fy + 1, cz, "log"))             # hoekbalken
    points.append((fx + 2, fy + 1, fz, "path"))                # deur

    # 6) gewas-Flurstücke: percelen tussen de Gräben, per strook een gewas
    crops = ["wheat", "potato", "beet", "clover"]
    strips = [(5, 11), (13, 19), (21, 27), (29, 35), (37, 43)]
    for i, (x0, x1) in enumerate(strips):
        for seg, (z0, z1) in enumerate([(0, 20), (22, D - 1)]):
            if x0 <= 15 and z0 >= 22:        # sla de Wurt-zone over
                continue
            crop = crops[(i + seg) % len(crops)]
            box(x0, z0, x1, z1, BASE, BASE, "farmland")
            box(x0, z0, x1, z1, BASE + 1, BASE + 1, crop)      # gewaslaag
    # 7) een pad langs de Deich
    box(5, 0, 5, D - 1, BASE, BASE, "path")

    return regions, points


def voxels():
    """Bouw een 3D-kleurgrid uit de regio's voor de isometrische render.
    Return (grid, size) waar grid[x][z] = lijst (y, rgb) top-down."""
    regions, points = build()
    hi = {}
    def put(x, y, z, key):
        if 0 <= x < W and 0 <= z < D:
            hi.setdefault((x, z), {})[y] = BLOCKS[key][1]
    for (x0, y0, z0, x1, y1, z1, key) in regions:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(y0, y1 + 1):
                    put(x, y, z, key)
    for (x, y, z, key) in points:
        put(x, y, z, key)
    return hi
