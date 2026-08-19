--!strict
-- GameConfig — centrale afstemming voor Schatveld Weddewarden.
-- Gegrond op echte data: Bremerhaven-Nord / Land Wursten marschlandschap,
-- Flurstück-kataster, Schatzregal (vondsten = staatsbezit), pesticide-recht.
local GameConfig = {}

-- Wereldanker (echte plaats): Weddewarden, Bremerhaven-Nord (Land Wursten).
GameConfig.WORLD = {
	name = "Weddewarden",
	region = "Land Wursten · Bremerhaven-Nord",
	lat = 53.6008, lon = 8.5314,           -- 53°36'03"N 8°31'53"E
	landscape = "Marsch (Klei) achter de Außenweser-Deich",
	seed = 20260818,                       -- ÉÉN seedbron (client+server+MC lezen dit)
}

-- Grid: elk blok = 1 Flurstück-cel op het maaiveld.
GameConfig.GRID = {
	cols = 32, rows = 24,       -- 32×24 = 768 blokken
	block = 8,                  -- studs per blok
	baseY = 0,
}

-- Rollen (Duitse context).
GameConfig.ROLES = { "Boer", "Archeoloog", "Politie" }

-- Metaal-detector: leest per blok een waarde 0..100 (kans op metaalhoudend materiaal).
GameConfig.METAL = {
	rustyThreshold = 10,        -- < 10 = ALTIJD roestig ijzer (opdracht-regel)
	detectorRange = 3,          -- blokken rondom de speler die de detector toont
}

-- Winkel (Archeoloog koopt gereedschap; prijzen in MolCoin/€-fantasie).
GameConfig.SHOP = {
	Schep       = { price = 50,  tool = "Schep",       desc = "graven (basis)" },
	Metaaldetector = { price = 180, tool = "Metaaldetector", desc = "toont metaalwaarde 0–100 per blok" },
	Nachforschungsgenehmigung = { price = 300, permit = true,
		desc = "opgravingsvergunning — zonder dit is graven Raubgrabung (§ DSchG)" },
	Zeef        = { price = 90,  tool = "Zeef",        desc = "meer kans op kleine vondsten" },
}

-- Boer: gewasrotatie (goede rotatie = bonus, monocultuur = malus).
GameConfig.CROPS = { "Winterweizen", "Zuckerrübe", "Kartoffel", "Ackerbohne", "Kleegras" }
GameConfig.ROTATION = {
	-- realistische vruchtwisseling: vlinderbloemigen (Ackerbohne/Kleegras) herstellen N
	goodAfter = {
		Winterweizen = { "Zuckerrübe", "Kartoffel", "Ackerbohne", "Kleegras" },
		Zuckerrübe   = { "Winterweizen", "Ackerbohne", "Kleegras" },
		Kartoffel    = { "Winterweizen", "Ackerbohne", "Kleegras" },
		Ackerbohne   = { "Winterweizen", "Zuckerrübe", "Kartoffel" },
		Kleegras     = { "Winterweizen", "Zuckerrübe", "Kartoffel" },
	},
	yieldBonus = 1.35,          -- goede rotatie
	monocultureMalus = 0.6,     -- zelfde gewas na elkaar
}

-- Pesticide-recht (echt): §4a PflSchAnwV afstand tot water, §68 PflSchG boetes.
GameConfig.PESTICIDE = {
	bufferToDitch = 5,          -- min. 5 m met gesloten plantendek, anders 10 m (blokken≈m)
	bufferBare = 10,
	maxDosePerParcel = 3,       -- boven = "te veel pesticide" -> overtreding
	banned = { "Aldicarb", "Paraquat", "Atrazin" },  -- verboden werkzame stoffen
}

-- Boetes die de Politie kan uitschrijven (indicatief, gebaseerd op OWi-kaders).
GameConfig.FINES = {
	Raubgrabung        = 500,   -- graven zonder vergunning (Ordnungswidrigkeit)
	TrespassDig        = 400,   -- graven op niet-eigen Flurstück (§903 BGB)
	PesticideOveruse   = 350,   -- te veel pesticide
	PesticideBuffer    = 300,   -- te dicht bij water (§4a PflSchAnwV)
	PesticideBanned    = 800,   -- verboden middel (§68 PflSchG)
}

-- Schatzregal: significante vondsten worden staatsbezit; speler krijgt vindersloon.
GameConfig.SCHATZREGAL = {
	finderFeeFraction = 0.35,   -- legaal aangemeld: speler ontvangt dit aandeel
	significantValue = 200,     -- vondsten >= dit vallen onder het Schatzregal
	illegalFeeFraction = 0.10,  -- Raubgrabung: beschlagnahmt, slechts heler-waarde
}

-- Uitbetalingsvloer: significante vondst betaalt nooit minder dan de duurste gewone
-- vondst -> zeldzamer levert ALTIJD meer op (geen inversie).
GameConfig.PAYOUT = { softCap = 130 }

-- Startkapitaal + rol-startkit (mirror van config.STARTING; ÉÉN bron per wereld).
GameConfig.STARTING = {
	coins = 250,
	archeoloogKit = { "Schep", "Metaaldetector" },
	archeoloogCoins = 300,
}

-- Landesmuseum: eerste vondst-soort = Erstfund-bonus.
GameConfig.MUSEUM = { erstfundBonusFraction = 0.5, erstfundRep = 2 }

-- Eerste doel per rol (vervangt de verdwijnende toast).
GameConfig.OBJECTIVES = {
	Archeoloog = "Koop een Nachforschungsgenehmigung (€300), zoek hoge metaalwaarden en graaf legaal.",
	Boer = "Ploeg je 4 Flurstücke met góede vruchtwisseling (wissel het gewas!).",
	Politie = "Betrap een Raubgräber of pesticide-overtreder en beboet hem.",
}

-- Reputatie-rangen (maakt rep zichtbare progressie).
GameConfig.RANKS = {
	{ -999, "Verdächtig" }, { 0, "Sondengänger" }, { 10, "Feldforscher" },
	{ 25, "Denkmalpfleger" }, { 50, "Landesarchäologe" },
}
function GameConfig.rankOf(rep: number): string
	local title = GameConfig.RANKS[1][2]
	for _, r in ipairs(GameConfig.RANKS) do
		if rep >= r[1] then title = r[2] end
	end
	return title
end

return GameConfig
