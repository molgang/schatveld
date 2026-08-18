# Grounding — bronnen achter de realisme-keuzes

Gegenereerd via een geverifieerde research-workflow (Opus-agents, WebFetch/curl op de.wikipedia.org, gesetze-im-internet.de, create.roblox.com, minecraft.wiki, modrinth support).

## Geografie (Bremerhaven-Nord / Land Wursten)
- Weddewarden = Wurtendorf, zuidelijkste nederzetting van Land Wursten, Bremerhaven-Nord; 53.6008 N, 8.5314 E (de.wikipedia.org/wiki/Weddewarden).
- Wurt/Warft = door mensen opgeworpen woonheuvel tegen stormvloed; opgebouwd uit mest+klei, vanaf 3e eeuw v.Chr. (de.wikipedia.org/wiki/Wurt).
- Feddersen Wierde (bij Wremen) = archetypisch opgegraven Wurtendorf, 1e eeuw v.Chr.–5e eeuw n.Chr., ~26 Wohnstallhäuser (de.wikipedia.org/wiki/Feddersen_Wierde).
- Marsch = vlak, kalkrijk Klei-land achter Watt/Deich; ontwatering via Gräben/Wettern/Siele/Schöpfwerke; ingepolderd = Koog/Groden/Polder (de.wikipedia.org/wiki/Marschland).

## Vondsten (loot-realisme)
- Barnsteen (Bernstein) spoelt occasioneel aan de Noordzeekust aan, meest losse kleine stukken → lage frequentie, kleine waarde (de.wikipedia.org/wiki/Bernstein).
- Roestig agrarisch ijzer (Pflugschar, hoefijzers, spijkers, schroot) is zeer algemeen in Noord-Duitse akkers.
- Feuerstein-knollen met natuurlijk gat ('Hühnergötter') als talisman; kwarts algemeen; GEEN diamanten in deze regio (de.wikipedia.org/wiki/Feuerstein).

## Recht (kadaster, Schatzregal, pesticide)
- Flurstück = kleinste kadaster-eenheid; Gemarkung>Flur>Flurstück; ID Zähler/Nenner (bv. 234/34) (de.wikipedia.org/wiki/Flurstück).
- ALKIS verenigt geometrie (ALK) + register (ALB); parcelgeometrie is open data (INSPIRE WFS/ATOM) in o.a. NRW/Niedersachsen/Bremen — eigenaarsnamen NIET.
- Schatzregal: sinds 1-7-2023 in alle 16 Länder → significante vondsten worden staatsbezit (Denkmalschutzgesetze, Art. 73 EGBGB) (de.wikipedia.org/wiki/Schatzregal).
- Nachforschungsgenehmigung nodig om te zoeken/graven; zonder = Raubgrabung (Ordnungswidrigkeit; §304 StGB) (de.wikipedia.org/wiki/Nachforschungsgenehmigung).
- §903 BGB: eigenaar mag anderen van elke inwerking uitsluiten; §59 BNatSchG: betreden van paden mag, graven niet.
- §4a PflSchAnwV: geen pesticide binnen 10 m van water (5 m met gesloten plantendek) (gesetze-im-internet.de/pflschanwv_1992/__4a.html).
- §68 PflSchG: boetes tot €50.000 (o.a. onjuiste/ontbrekende toepassingsregistratie); records 3 jaar (EU 1107/2009 Art. 67).

## Roblox (API's)
- ServerScriptService/ServerStorage (server), ReplicatedStorage (shared+Remotes), StarterPlayer/StarterGui (client) (create.roblox.com/docs/projects/data-model).
- ModuleScript-patroon; Rojo default.project.json met $className/$path (rojo.space/docs/v7/project-format).
- Per-blok getal via BillboardGui/SurfaceGui; gereedschap via Tool+Backpack/StarterPack; DataStoreService (UpdateAsync+pcall); server-authoritatieve RNG (never trust client).

## Minecraft-datapack (1.21)
- pack_format: 1.21=48, 1.21.4=61, 1.21.5=71; 1.21.9+ min_format/max_format. Wij: pack_format 61 + supported_formats 48..99.
- Custom item via components: custom_data/item_name/item_model (carrot_on_a_stick[custom_data={sv_detector:1b}]).
- item_used_on_block advancement detecteert detector-gebruik; geen 'mined'-advancement → scoreboard minecraft.mined:<block>.
- Weighted loot_table met random_sequence; per-blok 0-100 via scoreboard-hash van coords (geen native hash).
- Modrinth: standalone 'datapack'-project of .mrpack met modrinth.index.json + overrides/ (support.modrinth.com mrpack).

