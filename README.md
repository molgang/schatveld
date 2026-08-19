# Schatveld Weddewarden

Een rollenspel over **schatgraven, boeren en handhaven** in het echte marschveld van
**Bremerhaven-Nord / Land Wursten** (Weddewarden, 53.6008 N, 8.5314 E).

## One Brain, Two Worlds
Eén **autoritatieve Python-"brain"** (`pybrain/`) draait alle spelregels — het veld
0–100, de loot-randomizer, de economie en handhaving — en stuurt **twee werelden**
tegelijk aan die exact dezelfde staat delen:

```
        Python BRAIN (pybrain/schatveld_core + api.py)
          │ RCON (TCP)                    │ HTTP (HttpService)
   Minecraft (Fabric + Modrinth-mods     Roblox (Luau)
   + datapack die dig-events emit)        Api.lua → dezelfde brain
```

- **`pybrain/`** — de brain: `schatveld_core/` (pure Python, pytest 7/7), `api.py`
  (HTTP-API), `rcon.py` (mini-RCON, 0 deps), `mc_bridge.py` (datapack↔brain),
  en **`schatveld.ipynb`** — het controlecentrum dat alles vanuit Python aanstuurt.
- **`roblox/`** — de Roblox-game (Luau + Rojo); `Api.lua` praat met de brain (`USE_BRAIN=true`).
- **`datapack/`** — Minecraft Java 1.21-datapack + Modrinth `.mrpack`; de datapack emit
  graaf/detector-events naar `storage schatveld:ev`, de brain berekent de vondst en
  pusht die terug.

**Bewezen (live):** een echte lokale **Fabric 1.21.10-server met een Modrinth-mod**
(fabric-api) + de datapack; de brug injecteert een graaf-event → de brain rekent
metaalwaarde 84 → "Handgesmede spijkers" → geeft het item via RCON. Dezelfde
`field.value(7,7)=84` in de Roblox-API én Minecraft → één brein, twee werelden.

## v2 — bredere, grafisch rijkere wereld (Minecraft-zwaar)

Bovenop de MVP is er een **rijkere versie** met meer grafische objecten, echte shaders
en meer Modrinth-mods:

- **Marschwereld gebouwd** (`pybrain/marsh.py` + `pybrain/build_marsh.py`): het landschap
  van Weddewarden wordt **live via RCON** (`/fill`/`/setblock`) op de server gebouwd —
  Watt/water aan de westrand, een **Deich** (dijk), een verhoogde **Wurt** met boerderij,
  **Gräben** (sloten) tussen de percelen en **gewas-Flurstücke** (graan/aardappel/biet/
  klaver). `build_marsh.py` verifieert de bouw met `execute if block` (5/5 steekproeven ✓).
- **Resource pack** (`resourcepack/build_resourcepack.py`, PIL): procedurele 16×16-texturen
  die de stand-in-items vervangen door thematische vondsten — een echte **metaaldetector**,
  **barnsteen**, een bronzen **Wurt-fibula**, **gouden munt**, **roestige spijkers**,
  **ploegijzer** en een **potscherf**.
- **Verrijkte Modrinth-packs** (`datapack/build_mrpack.py`, echte versies + sha512 uit de
  Modrinth-API):
  - `schatveld-world-1.21.10.mrpack` — de spelwereld: Sodium/Lithium/FerriteCore/
    EntityCulling + **EMF/ETF** (entity-model/-texture-features) + **BetterArcheology** +
    fabric-api, mét de datapack én resource pack in `overrides/`.
  - `schatveld-shaders-1.20.1.mrpack` — **de Iris-workaround voor Apple Silicon** (zie hieronder).
- **Roblox-opfris** (`roblox/default.project.json`): `Lighting.Technology = Future` +
  Atmosphere (kust-nevel) + Bloom + SunRays + ColorCorrection, breedtegraad 53,6° N.
- **Demonstratie** (`data/render_marsh_iso.py`): een **isometrische voxel-render** van het
  écht-gebouwde marschland → `data/schatveld_marsh_iso.png`.

### Shaders op een Mac (Apple Silicon) — de Iris-workaround
macOS geeft **maximaal OpenGL 4.1** (Apple heeft OpenGL bevroren; dat is niet te
"upgraden"). **Iris ≥ 1.7 / MC 1.21 eist OpenGL 4.3** → daarom de crash. De betrouwbare
oplossing is **niet** een zware Zink/MoltenVK-vertaallaag (fragiel op macOS-GLFW), maar
shaders draaien op de **laatste 4.1-native combinatie**: **MC 1.20.1 + Iris 1.6.17 +
Sodium 0.5.3 + Complementary Reimagined** — precies wat `schatveld-shaders-1.20.1.mrpack`
levert (Iris-config zet de shader meteen aan). Installeer die pack via een Modrinth-launcher
en de shaders renderen **natief** op de M2. (De 1.21.10-spelwereld draait bewust zónder
Iris — daar geven Sodium + EMF/ETF + de resource pack de grafische upgrade zonder de 4.3-muur.)

Bouwen:
```
python3 resourcepack/build_resourcepack.py   # -> resourcepack/build/schatveld_resources.zip
python3 datapack/build_mrpack.py             # -> beide .mrpack's (echte Modrinth-versies)
python3 pybrain/build_marsh.py               # bouwt de marsch LIVE op de server (RCON) + verifieert
python3 data/render_marsh_iso.py             # -> data/schatveld_marsh_iso.png (demonstratie)
```

## v2.1 — gameplay & UX (uit een 7-agent-studie)

Een audit van de gameplay wees één cluster met de hoogste hefboom aan — "de eerste 60
seconden werkt écht en voelt als een metaaldetector" — plus een paar echte bugs. Doorgevoerd,
gespiegeld over **beide werelden** (Python-brain + Luau) met guard-tests (`pytest` 11/11):

- **Geen start-softlock meer**: een Archeoloog krijgt gratis **schep + metaaldetector** en
  €300, zodat de vergunning meteen te betalen is en legaal graven vanaf seconde 1 kan.
- **Detector voelt echt**: de metaalwaarde wordt nu **client-side** berekend (geen server-
  round-trip per frame meer) met een **nabijheidsmeter** + **ping** die sneller/hoger wordt
  bij metaal — plus een **vondst-kaart**, **deeltjes** en **geluid** bij het graven.
- **Vergunning heeft echte ROI**: een illegale (Raubgrabung) significante vondst wordt
  **beschlagnahmt** (10% i.p.v. 35% vindersloon); zeldzamer betaalt nu **altijd meer**
  (uitbetalingsvloer, geen inversie meer).
- **Landesmuseum**: eerste keer dat je een vondst-soort vindt = **Erstfund-bonus** (n/13);
  reputatie krijgt een zichtbare **rang** (Sondengänger → Landesarchäologe).
- **Politie-bug gefixt**: de agent klikt nu op een **blok** en de server zoekt de échte
  overtreder die daar illegaal groef/spoot (voorheen beboette je jezelf).
- **Doel-banner + duidelijke winkel**: een persistent rol-doel vervangt de verdwijnende
  toast; de winkel toont vaste volgorde, bezit/betaalbaarheid en de "legaal graven"-eis.

### Puur-Minecraft controlecentrum
`schatveld_modrinth.ipynb` (gegenereerd door `pybrain/build_modrinth_notebook.py`) is een
**pure Modrinth-Minecraft**-notebook (geen Roblox): welke assets/mods je gebruikt, de packs
genereren, de wereld live bouwen, en verbinden. Eén-commando-start: `bash pybrain/play.sh`
(server + brain + brug), stoppen met `bash pybrain/stop.sh`.

### Zelf draaien (Python + Minecraft)
```
python3 pybrain/api.py &                 # de brain-API (poort 8791)
bash    pybrain/run_server.sh            # lokale Fabric-server + Modrinth-mod + datapack (Java 21 in .mcserver/)
python3 pybrain/mc_bridge.py schatveld   # de brug: datapack-events -> brain-loot -> RCON
jupyter notebook schatveld.ipynb         # of: het complete controlecentrum
```
(De server + Java 21 leven in `.mcserver/`, buiten git. `run_server.sh` en het
`.ipynb` regelen de rest.)

---

De twee front-ends afzonderlijk (werken ook standalone):
- **`roblox/`** — de volledige game (Luau + Rojo) voor Roblox Studio.
- **`datapack/`** — een Minecraft Java 1.21-datapack (geen mod nodig) + Modrinth `.mrpack`.

## Concept

Kies een rol:

| Rol | Doel |
|---|---|
| **Archeoloog** | Koop schep + **metaaldetector** in de winkel; zoek en graaf. De detector toont per blok een **getal 0–100** (kans op metaalhoudend materiaal). Graven vereist een **Nachforschungsgenehmigung** (vergunning) — anders is het *Raubgrabung*. |
| **Boer** | Bescherm je **Flurstücke** (kadaster) tegen schatgravers, doe een goede **gewasrotatie** met ploegen, en houd je aan de **pesticide-regels**. |
| **Politie** | Beboet schatgravers zonder vergunning en boeren die te veel/verboden pesticide gebruiken of niet-eigen land (kadastraal) gebruiken. |

**De 0–100-regel:** elk blok heeft een deterministische metaalwaarde. **< 10 = altijd
roestig ijzer.** Hoger = kans op agrarisch ijzer, munten, en (zeldzaam) barnsteen,
Fibulae en Wurt-artefacten. Significante vondsten vallen onder het **Schatzregal**
(staatsbezit → de speler krijgt vindersloon).

## Realisme (gegrond, zie `data/grounding.md`)

- **Landschap**: Marsch/Klei achter de Außenweser-Deich; Gräben/Siele/Schöpfwerke;
  een verhoogde **Wurt** (woonheuvel) zoals Weddewarden / Feddersen Wierde.
- **Vondsten**: roestig agrarisch ijzer (zeer algemeen), Feuerstein/Hühnergott en
  kwarts (algemeen), barnsteen (occasioneel, kust), munten (zeldzaam), Wurt-
  artefacten (zeer zeldzaam). **Geen diamanten** — dat past niet bij de regio.
- **Recht**: Flurstück/Gemarkung/Flur-kadaster (ALKIS), Schatzregal (sinds 2023 in
  alle 16 Länder), Nachforschungsgenehmigung, §903 BGB (eigendom), §4a PflSchAnwV
  (5–10 m bufferzone tot water), §68 PflSchG (boetes tot €50.000).

## Roblox draaien

1. Installeer [Rojo](https://rojo.space) + Roblox Studio met de Rojo-plugin.
2. `cd roblox && rojo serve` → in Studio: Rojo-plugin → **Connect**.
3. Play. De server bouwt het veld (768 Flurstück-blokken); kies je rol; koop in de
   winkel (**B**); beweeg de muis over blokken om de metaalwaarde te zien.

Structuur: `src/shared` → ReplicatedStorage · `src/server` → ServerScriptService ·
`src/client` → StarterPlayerScripts. Server-autoritatief (loot-RNG, geld en
handhaving draaien uitsluitend op de server).

## Minecraft-datapack draaien

```
cd datapack && python3 build_datapack.py         # -> build/schatveld_datapack.zip + schatveld.mrpack
```

- Kopieer `build/schatveld_datapack.zip` naar `<wereld>/datapacks/` (1.21–1.21.10).
- In-game: `/function schatveld:menu` → kies rol → detector.
- Rechtsklik grond met de detector = metaalwaarde 0–100. Graven (dirt/grass/mud/
  clay/…) geeft vondsten; **< 10 = altijd roestig ijzer**.
- Of installeer `schatveld.mrpack` via een Modrinth-launcher.

## Licentie
Intern bedrijfsproject (molgang / VirtualV). Vrij te gebruiken en uit te breiden.
