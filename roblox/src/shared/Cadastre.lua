--!strict
-- Cadastre — Flurstück-kataster voor het speelveld (echt Duits model).
-- Hiërarchie: Gemarkung > Flur > Flurstück (Zähler/Nenner, bv. 234/34).
-- Elk grid-blok hoort bij een Flurstück; eigendom + vergunning zitten hierop.
-- Geometrie is in echte Länder open data (ALKIS/INSPIRE); dit model kan later
-- met echte GeoJSON-parcels worden gevuld (zie loadGeoJSON).
local GameConfig = require(script.Parent.GameConfig)

local Cadastre = {}

export type Parcel = {
	id: string,          -- "Weddewarden-3-234/34"
	gemarkung: string,
	flur: number,
	zaehler: number,
	nenner: number?,
	owner: string?,      -- speler-userId of "Land Bremen" / nil = onbeheerd
	use: string,         -- "Acker" | "Grünland" | "Wurt" | "Deich" | "Wasser"
	blocks: {{col: number, row: number}},
	coastal: boolean,
	wurt: boolean,       -- ligt op/bij een Wurt (dwelling mound) → artefacten
}

-- Deterministische parcel-indeling van het grid: rechthoekige Flurstücke
-- (marsch-percelen zijn typisch lange smalle stroken haaks op de Deich).
local parcels: {Parcel} = {}
local blockToParcel: {[string]: Parcel} = {}

local function key(col: number, row: number): string
	return col .. ":" .. row
end

function Cadastre.build(seed: number)
	parcels = {}
	blockToParcel = {}
	local cols, rows = GameConfig.GRID.cols, GameConfig.GRID.rows
	local stripW = 4                       -- smalle marschstroken (4 blokken breed)
	local flur = 1
	local zaehler = 100
	for c0 = 0, cols - 1, stripW do
		-- de Deich/kust ligt aan de westrand (col 0..1) → coastal
		for seg = 0, 1 do
			local r0 = seg * math.floor(rows / 2)
			local r1 = (seg == 0) and math.floor(rows / 2) - 1 or rows - 1
			zaehler += 2
			local nenner = 30 + (flur * 3 + seg) % 40
			local use = "Acker"
			-- een Wurt-dorp (Weddewarden) in het midden-westen
			local wurt = (c0 <= 8 and seg == 0)
			if wurt then use = "Wurt" end
			if c0 <= 1 then use = "Deich" end
			local coastal = (c0 <= 3)
			local p: Parcel = {
				id = string.format("Weddewarden-%d-%d/%d", flur, zaehler, nenner),
				gemarkung = "Weddewarden", flur = flur, zaehler = zaehler, nenner = nenner,
				owner = nil, use = use, blocks = {}, coastal = coastal, wurt = wurt,
			}
			for c = c0, math.min(c0 + stripW - 1, cols - 1) do
				for r = r0, r1 do
					table.insert(p.blocks, { col = c, row = r })
					blockToParcel[key(c, r)] = p
				end
			end
			table.insert(parcels, p)
			flur += 1
		end
	end
end

function Cadastre.parcelAt(col: number, row: number): Parcel?
	return blockToParcel[key(col, row)]
end

function Cadastre.all(): {Parcel}
	return parcels
end

-- Ken willekeurige akker-percelen toe aan een boer-speler.
function Cadastre.assignOwner(parcelId: string, owner: string)
	for _, p in ipairs(parcels) do
		if p.id == parcelId then p.owner = owner end
	end
end

-- Context voor de loot-roll (kust/wurt) uit het perceel onder het blok.
function Cadastre.context(col: number, row: number): {coastal: boolean, wurt: boolean}
	local p = Cadastre.parcelAt(col, row)
	if not p then return { coastal = false, wurt = false } end
	return { coastal = p.coastal, wurt = p.wurt }
end

-- Latere uitbreiding: echte ALKIS/INSPIRE GeoJSON-parcels inladen.
-- function Cadastre.loadGeoJSON(features) ... end

return Cadastre
