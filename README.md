# Schatveld Weddewarden

Een rollenspel over **schatgraven, boeren en handhaven** in het echte marschveld van
**Bremerhaven-Nord / Land Wursten** (Weddewarden, 53.6008 N, 8.5314 E). Twee
implementaties die hetzelfde spelconcept delen:

- **`roblox/`** — de volledige game (Luau + Rojo) voor Roblox Studio.
- **`datapack/`** — een Minecraft Java 1.21-datapack (geen mod) + Modrinth `.mrpack`.

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
