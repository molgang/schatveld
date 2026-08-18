"""config — centrale afstemming (port van roblox/src/shared/GameConfig.lua).
Eén bron van waarheid, gedeeld door de HTTP-API en de Minecraft-brug."""

WORLD = {
    "name": "Weddewarden",
    "region": "Land Wursten · Bremerhaven-Nord",
    "lat": 53.6008, "lon": 8.5314,
    "seed": 20260818,
}

GRID = {"cols": 32, "rows": 24, "block": 8, "baseY": 0}

ROLES = ["Boer", "Archeoloog", "Politie"]

METAL = {"rustyThreshold": 10, "detectorRange": 3}

SHOP = {
    "Schep": {"price": 50, "tool": "Schep", "desc": "graven (basis)"},
    "Metaaldetector": {"price": 180, "tool": "Metaaldetector",
                       "desc": "toont metaalwaarde 0–100 per blok"},
    "Nachforschungsgenehmigung": {"price": 300, "permit": True,
        "desc": "opgravingsvergunning — zonder is graven Raubgrabung"},
    "Zeef": {"price": 90, "tool": "Zeef", "desc": "meer kans op kleine vondsten"},
}

CROPS = ["Winterweizen", "Zuckerrübe", "Kartoffel", "Ackerbohne", "Kleegras"]
ROTATION = {
    "goodAfter": {
        "Winterweizen": ["Zuckerrübe", "Kartoffel", "Ackerbohne", "Kleegras"],
        "Zuckerrübe": ["Winterweizen", "Ackerbohne", "Kleegras"],
        "Kartoffel": ["Winterweizen", "Ackerbohne", "Kleegras"],
        "Ackerbohne": ["Winterweizen", "Zuckerrübe", "Kartoffel"],
        "Kleegras": ["Winterweizen", "Zuckerrübe", "Kartoffel"],
    },
    "yieldBonus": 1.35, "monocultureMalus": 0.6,
}

PESTICIDE = {
    "bufferToDitch": 5, "bufferBare": 10, "maxDosePerParcel": 3,
    "banned": ["Aldicarb", "Paraquat", "Atrazin"],
}

FINES = {
    "Raubgrabung": 500, "TrespassDig": 400, "PesticideOveruse": 350,
    "PesticideBuffer": 300, "PesticideBanned": 800,
}

SCHATZREGAL = {"finderFeeFraction": 0.35, "significantValue": 200}
