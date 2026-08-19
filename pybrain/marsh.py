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
    "sand":     ("minecraft:sand",        (214, 204, 160)),   # onderliggend Geest-zand
    "sandstone":("minecraft:sandstone",   (200, 190, 150)),   # basislaag
    "grass":    ("minecraft:grass_block", (94, 140, 74)),
    "deich":    ("minecraft:grass_block", (78, 128, 66)),
    "farmland": ("minecraft:farmland",    (96, 72, 50)),
    # akker-STATEN (realistische patchwork van boerenvelden in verschillende stadia):
    "grain":     ("minecraft:hay_block",    (212, 186, 82)),  # rijp geel graan
    "grain_stub":("minecraft:packed_mud",   (170, 144, 98)),  # geoogst graan-stoppelveld
    "maize":     ("minecraft:moss_block",   (74, 150, 58)),   # mais (2 blokken hoog)
    "maize_stub":("minecraft:coarse_dirt",  (120, 100, 66)),  # geploegde mais-stoppel
    "ploughed":  ("minecraft:podzol",       (66, 48, 32)),    # vers zwart-geploegd
    "pasture":   ("minecraft:grass_block",  (96, 152, 72)),   # groen grasland/weide
    "path":     ("minecraft:dirt_path",   (132, 116, 82)),
    "road":     ("minecraft:gravel",       (112, 110, 116)),  # verharde weg (politie + tractor)
    "planks":   ("minecraft:oak_planks",  (164, 132, 86)),
    "log":      ("minecraft:oak_log",     (110, 88, 58)),
    "cobble":   ("minecraft:cobblestone", (122, 122, 126)),
    "roof":     ("minecraft:dark_oak_planks", (74, 56, 38)),
    "reed":     ("minecraft:bamboo",      (120, 150, 80)),
    "air":      ("minecraft:air",         None),   # None = niet renderen (leegmaken)
}

W, D = 48, 36        # marsch afmeting (x = west→oost, z = zuid→noord)
BASE = 63            # grondhoogte (y)


def build():
    """Return (regions, points): regions=[(x0,y0,z0,x1,y1,z1,key)], points=[(x,y,z,key)]."""
    regions, points = [], []

    def box(x0, z0, x1, z1, y0, y1, key):
        regions.append((x0, y0, z0, x1, y1, z1, key))

    # 0) maak de bovengrond leeg (verwijder oude verhoogde blokken van een vorige lay-out)
    box(0, 0, W - 1, D - 1, BASE + 1, BASE + 6, "air")

    # 1) fundament als een ECHTE grond-doorsnede (Land-Wursten marsch): Klei bovenop,
    #    daaronder ondergrond, dan Geest-zand, dan zandsteen als basis. Zo is water in de
    #    sloot max 1 blok diep (klei-vloer eronder) en zijn de velden geen bodemloos gat.
    box(0, 0, W - 1, D - 1, BASE - 2, BASE, "clay")           # Klei (maaiveld + ondergrond)
    box(0, 0, W - 1, D - 1, BASE - 4, BASE - 3, "dirt")       # ondergrond
    box(0, 0, W - 1, D - 1, BASE - 7, BASE - 5, "sand")       # Geest-zand
    box(0, 0, W - 1, D - 1, BASE - 9, BASE - 8, "sandstone")  # basislaag

    # 2) Watt/zee aan de westrand (x 0-2): water, 1 blok diep op de klei-vloer
    box(0, 0, 2, D - 1, BASE, BASE, "water")

    # 3) Deich (dijk) x 3-4, +3 hoog, gras
    box(3, 0, 4, D - 1, BASE + 1, BASE + 3, "deich")
    box(3, 0, 4, D - 1, BASE, BASE, "dirt")

    # 4-7) POLDERRASTER (echt Land-Wursten): 6×6-velden als EILANDEN, rondom omringd door
    #      SLOTEN (irrigatiewater), met WEGEN in de tussenstroken (sloot|weg|weg|sloot) en
    #      een BRUG van elke weg naar elk veld.
    FS = 6
    field_x = [5, 15, 25, 35]                 # begin-x van elke veld-kolom (gaps ertussen)
    field_z = [0, 10, 20, 30]                 # begin-z van elke veld-rij
    states = ["grain", "ploughed", "pasture", "maize", "grain_stub", "maize_stub"]

    # a) hele veldzone = sloten (water, 1 blok diep op de klei-vloer)
    box(5, 0, W - 1, D - 1, BASE, BASE, "water")
    # b) wegenraster (grind) in het midden van elke tussenstrook → er blijft aan weerszijden
    #    een 1-blok sloot langs elk veld staan (sloot|weg|weg|sloot)
    for rx in (12, 13, 22, 23, 32, 33, 42, 43):
        box(rx, 0, rx, D - 1, BASE, BASE, "road")
    for rz in (7, 8, 17, 18, 27, 28):
        box(5, rz, W - 1, rz, BASE, BASE, "road")
    # c) velden (eilanden) + gewas-staat; één cel = de Wurt met boerderij
    k = 0
    for fz in field_z:
        for fx in field_x:
            x1, z1 = min(fx + FS - 1, W - 1), min(fz + FS - 1, D - 1)
            if fx == 15 and fz == 20:         # Wurt-cel (woonheuvel + boerderij)
                box(fx, fz, x1, z1, BASE + 1, BASE + 2, "grass")
                hx, hz, hy = fx + 1, fz + 1, BASE + 3
                box(hx, hz, hx + 3, hz + 2, hy, hy + 2, "planks")
                box(hx, hz, hx + 3, hz + 2, hy, hy, "cobble")
                box(hx - 1, hz - 1, hx + 4, hz + 3, hy + 3, hy + 3, "roof")
                for cx in (hx, hx + 3):
                    for cz in (hz, hz + 2):
                        points.append((cx, hy + 1, cz, "log"))
                points.append((hx + 1, hy + 1, hz, "path"))     # deur
                continue
            st = states[k % len(states)]; k += 1
            box(fx, fz, x1, z1, BASE, BASE, "farmland")
            if st == "grain":   box(fx, fz, x1, z1, BASE + 1, BASE + 1, "grain")
            elif st == "maize": box(fx, fz, x1, z1, BASE + 1, BASE + 2, "maize")
            else:               box(fx, fz, x1, z1, BASE, BASE, st)
    # d) bruggen: van elk veld over de sloot naar de aangrenzende weg (rechts + onder, in het midden)
    for fz in field_z:
        for fx in field_x:
            bz, bx = min(fz + FS // 2, D - 1), min(fx + FS // 2, W - 1)
            if fx + FS < W:  box(fx + FS, bz, fx + FS, bz, BASE, BASE, "path")   # brug oostwaarts
            if fz + FS < D:  box(bx, fz + FS, bx, fz + FS, BASE, BASE, "path")   # brug zuidwaarts
    # e) voetpad langs de Deich-voet
    box(5, 0, 5, D - 1, BASE, BASE, "path")

    return regions, points


def voxels():
    """Bouw een 3D-kleurgrid uit de regio's voor de isometrische render.
    Return (grid, size) waar grid[x][z] = lijst (y, rgb) top-down."""
    regions, points = build()
    hi = {}
    def put(x, y, z, key):
        rgb = BLOCKS[key][1]
        if rgb is None:                       # lucht: verwijder deze cel (leegmaken)
            if 0 <= x < W and 0 <= z < D:
                hi.get((x, z), {}).pop(y, None)
            return
        if 0 <= x < W and 0 <= z < D:
            hi.setdefault((x, z), {})[y] = rgb
    for (x0, y0, z0, x1, y1, z1, key) in regions:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                for y in range(y0, y1 + 1):
                    put(x, y, z, key)
    for (x, y, z, key) in points:
        put(x, y, z, key)
    return hi
