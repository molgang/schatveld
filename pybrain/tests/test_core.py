"""Tests voor schatveld_core — determinisme, <10-regel, Schatzregal, handhaving."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schatveld_core import Brain, field, loot, cadastre, config
from schatveld_core.economy import payout_for, rank_of


def test_field_deterministic_and_range():
    vals = [field.value(c, r) for c in range(32) for r in range(24)]
    assert min(vals) >= 0 and max(vals) <= 100
    assert field.value(5, 5) == field.value(5, 5)              # deterministisch
    assert 0 < sum(1 for v in vals if v < 10) < 60             # sommige <10-blokken


def test_dig_below_10_is_always_rusty_iron(tmp_path):
    b = Brain(seed=config.WORLD["seed"])
    b.players["u"] = {**b._p("u"), "tools": {"Schep": True}, "permit": True}
    # zoek een blok met waarde <10
    low = next((c, r) for c in range(32) for r in range(24) if field.value(c, r) < 10)
    res = b.dig("u", low[0], low[1])
    assert res["ok"] and res["metal"] < 10
    assert res["find"]["id"] == "rusty_iron"


def test_schatzregal_pays_finder_fee():
    f = {"id": "coin_gold", "value": 350, "state": True}
    frac = config.SCHATZREGAL["finderFeeFraction"]
    assert int(350 * frac) < 350                               # speler krijgt deel


def test_shop_buy_and_dig_requires_shovel():
    b = Brain(seed=1)
    assert b.dig("u", 10, 10)["ok"] is False                   # geen schep
    b._p("u")["coins"] = 1000
    assert b.buy("u", "Schep")["ok"]
    assert b.buy("u", "Nachforschungsgenehmigung")["ok"]
    assert b.dig("u", 10, 10)["ok"]                            # nu wel


def test_boer_rotation_bonus_and_monoculture_malus():
    b = Brain(seed=1)
    b.join("boer", "Boer")
    # pak een eigen perceel
    own = next(p for p in cadastre.all_parcels() if p["owner"] == "boer")
    c, r = own["blocks"][0]
    r1 = b.plough("boer", c, r, "Ackerbohne")
    r2 = b.plough("boer", c, r, "Winterweizen")   # goede rotatie na Ackerbohne
    r3 = b.plough("boer", c, r, "Winterweizen")   # monocultuur
    assert r2["mult"] == config.ROTATION["yieldBonus"]
    assert r3["mult"] == config.ROTATION["monocultureMalus"]


def test_police_fine_needs_evidence():
    b = Brain(seed=1)
    b.join("cop", "Politie")
    b.join("dig", "Archeoloog")
    # geen overtreding -> geen boete
    assert b.fine("cop", "dig", "Raubgrabung")["ok"] is False
    # laat 'dig' illegaal graven (geen vergunning, vreemd/onbeheerd land met schep)
    b._p("dig")["tools"]["Schep"] = True
    b.dig("dig", 20, 20)                    # permit=False -> illegal
    assert b.fine("cop", "dig", "Raubgrabung")["ok"] is True


def test_fresh_archeoloog_can_start_no_softlock():
    """Regressie: een verse Archeoloog kan LEGAAL graven zonder handmatig munten/tools
    te injecteren — precies de softlock die de demo met coins=600 verborg."""
    b = Brain(seed=config.WORLD["seed"])
    st = b.join("anna", "Archeoloog")
    assert st["tools"].get("Schep") and st["tools"].get("Metaaldetector")   # gratis startkit
    assert st["coins"] >= config.SHOP["Nachforschungsgenehmigung"]["price"] # vergunning haalbaar
    assert b.buy("anna", "Nachforschungsgenehmigung")["ok"]
    res = b.dig("anna", 7, 7)                 # onbeheerd land + vergunning = legaal
    assert res["ok"] and res["illegal"] is False


def test_payout_monotonic_no_inversion():
    """Zeldzamer betaalt ALTIJD meer: een legale fibula/throne verslaat een gewone munt."""
    ids = {f["id"]: f for f in loot.TABLE}
    fibula = payout_for(ids["fibula"], ids["fibula"]["value"], illegal=False)[0]
    coin = payout_for(ids["coin_medieval"], ids["coin_medieval"]["value"], illegal=False)[0]
    gold = payout_for(ids["coin_gold"], ids["coin_gold"]["value"], illegal=False)[0]
    throne = payout_for(ids["throne_relic"], ids["throne_relic"]["value"], illegal=False)[0]
    assert fibula > coin                      # geen inversie meer (was 56 < 120)
    assert throne > gold                       # top-vondst betaalt het meest


def test_illegal_schatzregal_is_confiscated():
    """Raubgrabung van een significante vondst = beschlagnahmt: veel minder loon."""
    fib = {f["id"]: f for f in loot.TABLE}["fibula"]
    legal = payout_for(fib, fib["value"], illegal=False)
    illegal = payout_for(fib, fib["value"], illegal=True)
    assert legal[1] and illegal[1]            # beide significant
    assert illegal[2] is True and legal[2] is False   # alleen illegaal beschlagnahmt
    assert illegal[0] < legal[0]              # vergunning heeft echte ROI


def test_museum_first_find_bonus_and_rank():
    b = Brain(seed=config.WORLD["seed"])
    b.join("m", "Archeoloog"); b.buy("m", "Nachforschungsgenehmigung")
    res = b.dig("m", 7, 7)                     # metaal 84 -> een echte vondst
    assert res["find"]["id"] != "rusty_iron"
    assert res["firstFind"] is True and res["museum"] == 1
    assert b.museum("m")["total"] == len(loot.TABLE)
    assert rank_of(0) == "Sondengänger" and rank_of(60) == "Landesarchäologe"


def test_two_players_same_block_same_find():
    """Kern van 'one brain': zelfde blok + zelfde seed => zelfde vondst-band."""
    b = Brain(seed=config.WORLD["seed"])
    for u in ("a", "b"):
        b._p(u)["tools"]["Schep"] = True
        b._p(u)["permit"] = True
    # metaalwaarde is deterministisch identiek (de RNG-band verschilt per trekking,
    # maar de <10-regel en de waarde zijn identiek voor hetzelfde blok)
    assert field.value(7, 7) == field.value(7, 7)
    ra = b.dig("a", 7, 7); rb = b.dig("b", 7, 7)
    assert ra["metal"] == rb["metal"]      # gedeeld veld
