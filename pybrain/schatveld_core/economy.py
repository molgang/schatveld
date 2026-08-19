"""economy — de autoritatieve spel-brain (port van Schatveld.server.lua).
Houdt spelers/munten/inventaris/rollen bij, berekent graafuitkomsten (met de
gedeelde field/loot), en handhaaft kadaster/pesticide/Schatzregal. Deze klasse is
de ENIGE bron van waarheid; API én Minecraft-brug roepen dezelfde methodes aan."""
import json
import os
import random
from . import config, field, loot, cadastre


def new_profile():
    return {"role": None, "coins": config.STARTING["coins"], "rep": 0, "tools": {},
            "permit": False, "inv": {}, "lastCropByParcel": {},
            "pesticideByParcel": {}, "digLog": [], "museum": []}


def rank_of(rep):
    """Rep -> rangtitel (maakt reputatie zichtbare progressie)."""
    title = config.RANKS[0][1]
    for threshold, name in config.RANKS:
        if rep >= threshold:
            title = name
    return title


_LOOT_IDS = {f["id"] for f in loot.TABLE}


def payout_for(find, value, illegal):
    """Uitbetaling voor een vondst. Significante (Schatzregal) vondsten: legaal =
    max(35%, vloer) zodat zeldzamer altijd meer betaalt; illegaal = 10% heler-waarde
    (beschlagnahmt). Gewone vondsten: volle waarde. Retour (payout, significant, confiscated)."""
    significant = find["state"] or find["value"] >= config.SCHATZREGAL["significantValue"]
    if not significant:
        return find["value"], False, False
    if illegal:
        return int(find["value"] * config.SCHATZREGAL["illegalFeeFraction"]), True, True
    fee = int(find["value"] * config.SCHATZREGAL["finderFeeFraction"])
    floor = min(find["value"], config.PAYOUT["softCap"])
    return max(fee, floor), True, False


class Brain:
    def __init__(self, state_path=None, seed=None):
        self.seed = seed if seed is not None else config.WORLD["seed"]
        self.rng = random.Random(self.seed)
        self.state_path = state_path
        self.players = {}          # user -> profile
        cadastre.build(self.seed)
        if state_path and os.path.exists(state_path):
            try:
                self.players = json.load(open(state_path, encoding="utf-8"))
            except Exception:
                self.players = {}

    # -- persistentie --
    def save(self):
        if self.state_path:
            json.dump(self.players, open(self.state_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    def _p(self, user):
        if user not in self.players:
            self.players[user] = new_profile()
        return self.players[user]

    # -- lezen --
    def scan(self, col, row):
        return field.scan(col, row, self.seed)

    def parcel(self, col, row):
        p = cadastre.parcel_at(col, row)
        if not p:
            return None
        return {"id": p["id"], "use": p["use"], "owner": p["owner"],
                "coastal": p["coastal"], "wurt": p["wurt"]}

    def state(self, user):
        p = self._p(user)
        return {"role": p["role"], "coins": p["coins"], "rep": p["rep"],
                "rank": rank_of(p["rep"]), "tools": p["tools"], "permit": p["permit"],
                "inv": p["inv"], "museum": len(p.get("museum", [])),
                "museumTotal": len(loot.TABLE),
                "objective": config.OBJECTIVES.get(p["role"] or "", "")}

    def museum(self, user):
        p = self._p(user)
        collected = p.get("museum", [])
        total = len(loot.TABLE)
        return {"collected": collected, "total": total,
                "pct": round(100 * len(collected) / total) if total else 0}

    # -- acties --
    def join(self, user, role=None):
        p = self._p(user)
        if role and role in config.ROLES:
            p["role"] = role
            if role == "Boer":
                n = 0
                for parcel in cadastre.all_parcels():
                    if parcel["use"] == "Acker" and not parcel["owner"] and n < 4:
                        parcel["owner"] = user
                        n += 1
            elif role == "Archeoloog" and not p["tools"].get("Metaaldetector"):
                # startkit: schep + detector gratis + munten tot aan de vergunning,
                # zodat legaal graven meteen mogelijk is (fixet de softlock).
                for tool in config.STARTING["archeoloogKit"]:
                    p["tools"][tool] = True
                p["coins"] = max(p["coins"], config.STARTING["archeoloogCoins"])
        self.save()
        return self.state(user)

    def buy(self, user, key):
        p = self._p(user)
        item = config.SHOP.get(key)
        if not item:
            return {"ok": False, "msg": "onbekend item"}
        if p["coins"] < item["price"]:
            return {"ok": False, "msg": f"te weinig geld voor {key}"}
        p["coins"] -= item["price"]
        if item.get("tool"):
            p["tools"][item["tool"]] = True
        if item.get("permit"):
            p["permit"] = True
        self.save()
        return {"ok": True, "msg": f"gekocht: {key}", "coins": p["coins"]}

    def dig(self, user, col, row):
        """Graafuitkomst — de kern. Zelfde regels als de Luau-server."""
        p = self._p(user)
        if not p["tools"].get("Schep"):
            return {"ok": False, "msg": "je hebt een schep nodig"}
        v = field.value(col, row, self.seed)
        parcel = cadastre.parcel_at(col, row)
        on_own = parcel and parcel["owner"] == user
        illegal = (not p["permit"]) or (parcel and parcel["owner"] and not on_own)
        p["digLog"].append({"col": col, "row": row, "illegal": bool(illegal)})

        if v < config.METAL["rustyThreshold"]:
            find = loot.RUSTY_IRON
        else:
            ctx = cadastre.context(col, row)
            find = loot.roll(v, ctx["coastal"], ctx["wurt"], self.rng)

        payout, schatz, confiscated = payout_for(find, find["value"], bool(illegal))
        if schatz and not illegal:
            p["rep"] += 5          # legaal aangemelde significante vondst
        elif illegal:
            p["rep"] -= 5 if schatz else 3   # Raubgrabung: zwaarder bij Schatzregal

        # Landesmuseum: eerste keer dat je deze vondst-soort vindt = Erstfund-bonus.
        first_find = find["id"] in _LOOT_IDS and find["id"] not in p["museum"]
        if first_find:
            p["museum"].append(find["id"])
            payout += int(find["value"] * config.MUSEUM["erstfundBonusFraction"])
            p["rep"] += config.MUSEUM["erstfundRep"]

        p["inv"][find["id"]] = p["inv"].get(find["id"], 0) + 1
        p["coins"] += payout
        self.save()
        return {"ok": True, "metal": v, "find": find, "payout": payout,
                "schatzregal": schatz, "confiscated": confiscated,
                "illegal": bool(illegal), "firstFind": first_find,
                "museum": len(p["museum"]), "museumTotal": len(loot.TABLE),
                "rep": p["rep"], "rank": rank_of(p["rep"]), "coins": p["coins"]}

    def plough(self, user, col, row, crop):
        p = self._p(user)
        if p["role"] != "Boer":
            return {"ok": False, "msg": "alleen een boer kan ploegen"}
        parcel = cadastre.parcel_at(col, row)
        if not parcel or parcel["owner"] != user:
            return {"ok": False, "msg": "dit Flurstück is niet van jou"}
        if crop not in config.CROPS:
            return {"ok": False, "msg": "onbekend gewas"}
        prev = p["lastCropByParcel"].get(parcel["id"])
        mult = 1.0
        if prev == crop:
            mult = config.ROTATION["monocultureMalus"]
        elif prev and crop in config.ROTATION["goodAfter"].get(prev, []):
            mult = config.ROTATION["yieldBonus"]
        yield_ = int(40 * mult)
        p["coins"] += yield_
        p["lastCropByParcel"][parcel["id"]] = crop
        p["pesticideByParcel"][parcel["id"]] = 0
        self.save()
        return {"ok": True, "yield": yield_, "mult": round(mult, 2),
                "coins": p["coins"], "crop": crop}

    def spray(self, user, col, row, agent="Standaard", dose=1):
        p = self._p(user)
        if p["role"] != "Boer":
            return {"ok": False, "msg": "alleen een boer kan bespuiten"}
        parcel = cadastre.parcel_at(col, row)
        if not parcel:
            return {"ok": False, "msg": "geen perceel"}
        viol = []
        if parcel["owner"] != user:
            viol.append("vreemd Flurstück (§903 BGB)")
        if agent in config.PESTICIDE["banned"]:
            viol.append(f"verboden middel {agent}")
        if col <= config.PESTICIDE["bufferToDitch"]:
            viol.append("te dicht bij water (§4a PflSchAnwV)")
        dose_total = p["pesticideByParcel"].get(parcel["id"], 0) + dose
        p["pesticideByParcel"][parcel["id"]] = dose_total
        if dose_total > config.PESTICIDE["maxDosePerParcel"]:
            viol.append("te veel pesticide")
        if viol:
            p["rep"] -= len(viol)
        self.save()
        return {"ok": len(viol) == 0, "violations": viol}

    def fine(self, cop_user, target_user, reason):
        cop = self._p(cop_user)
        if cop["role"] != "Politie":
            return {"ok": False, "msg": "alleen de Politie kan beboeten"}
        tp = self._p(target_user)
        amount = config.FINES.get(reason)
        if not amount:
            return {"ok": False, "msg": "onbekende reden"}
        valid = False
        if reason in ("Raubgrabung", "TrespassDig"):
            valid = any(d.get("illegal") for d in tp["digLog"])
        elif reason.startswith("Pesticide"):
            valid = any(d > config.PESTICIDE["maxDosePerParcel"]
                        for d in tp["pesticideByParcel"].values()) or tp["rep"] < 0
        if not valid:
            return {"ok": False, "msg": "geen bewijs voor deze overtreding"}
        tp["coins"] = max(0, tp["coins"] - amount)
        cop["coins"] += int(amount * 0.1)
        cop["rep"] += 4
        self.save()
        return {"ok": True, "amount": amount, "reason": reason,
                "target_coins": tp["coins"]}
