"""field — deterministische metaalwaarde 0..100 per blok.
Exacte port van roblox/src/shared/MetalField.lua (mix + value), geverifieerd in
data/render_field.py. Zowel de Roblox-client, de Minecraft-brug als de API lezen
hierdoor identieke waarden voor hetzelfde blok."""
from . import config

SEED = config.WORLD["seed"]


def mix(a: int, b: int, seed: int) -> int:
    a %= 8192; b %= 8192; seed %= 8192
    h = (a * 92821 + b * 68389 + seed * 40503) % 1000003
    return (h * 31 + a + b) % 101


def value(col: int, row: int, seed: int = SEED) -> int:
    base = mix(col, row, seed)
    cluster = mix(col // 4, row // 4, seed + 7)
    v = int(base * 0.7 + cluster * 0.3)
    return max(0, min(100, v))


def scan(cc: int, cr: int, seed: int = SEED, rng: int = None):
    """Detector-view: metaalwaarden rond een centrum-blok (detectorbereik)."""
    r = config.METAL["detectorRange"] if rng is None else rng
    cols, rows = config.GRID["cols"], config.GRID["rows"]
    out = []
    for c in range(cc - r, cc + r + 1):
        for rr in range(cr - r, cr + r + 1):
            if 0 <= c < cols and 0 <= rr < rows:
                out.append({"col": c, "row": rr, "v": value(c, rr, seed)})
    return out
