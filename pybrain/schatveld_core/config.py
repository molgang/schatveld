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

# Startkapitaal + rol-startkit (ÉÉN bron; Lua/Minecraft/demo lezen dit, geen losse literals).
# Archeoloog krijgt schep + detector gratis en genoeg munten om de vergunning te kopen,
# zodat de kern-loop meteen legaal te spelen is (geen Raubgrabung-softlock).
STARTING = {"coins": 250, "archeoloogKit": ["Schep", "Metaaldetector"], "archeoloogCoins": 300}

# Objectief per rol (eerste doel; vervangt de verdwijnende toast).
OBJECTIVES = {
    "Archeoloog": "Koop een Nachforschungsgenehmigung (€300), zoek blokken met hoge "
                  "metaalwaarde en graaf legaal.",
    "Boer": "Ploeg je 4 Flurstücke met góede vruchtwisseling (wissel het gewas!).",
    "Politie": "Betrap een Raubgräber of pesticide-overtreder en beboet hem.",
}

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

SCHATZREGAL = {"finderFeeFraction": 0.35, "significantValue": 200,
               # legaal: 35% vindersloon; illegaal: object wordt beschlagnahmt, alleen
               # 10% heler-waarde. Zo verdient de €300-vergunning zich terug (echte ROI).
               "illegalFeeFraction": 0.10}

# Uitbetalingsvloer: een significante vondst betaalt nooit minder dan de duurste
# gewone vondst (=coin_medieval 120), zodat zeldzamer ALTIJD meer oplevert (geen inversie).
PAYOUT = {"softCap": 130}

# Landesmuseum: eerste keer dat je een vondst-soort vindt = Erstfund-bonus.
MUSEUM = {"erstfundBonusFraction": 0.5, "erstfundRep": 2}

# Reputatie-rangen (maakt rep zichtbaar/betekenisvol als progressie).
RANKS = [(-999, "Verdächtig"), (0, "Sondengänger"), (10, "Feldforscher"),
         (25, "Denkmalpfleger"), (50, "Landesarchäologe")]
