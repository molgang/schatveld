--!strict
-- MetalField — deterministische metaalwaarde 0..100 per blok + graaf-uitkomst.
--
-- De waarde is een reproduceerbare hash van (col,row) + wereld-seed, zodat de
-- detector telkens hetzelfde toont en client/server het eens zijn. Exact dezelfde
-- LCG-mix wordt in de Minecraft-datapack gebruikt, zodat beide games "hetzelfde
-- veld" delen.
local GameConfig = require(script.Parent.GameConfig)
local LootTables = require(script.Parent.LootTables)

local MetalField = {}

-- Deterministische integer-mix → 0..100 (blijft ruim binnen 2^53, geen precisieverlies).
local function mix(a: number, b: number, seed: number): number
	a = a % 8192; b = b % 8192; seed = seed % 8192
	local h = (a * 92821 + b * 68389 + seed * 40503) % 1000003
	h = (h * 31 + a + b) % 101
	return h
end

-- Publieke: metaalwaarde 0..100 voor een blok (deterministisch).
function MetalField.value(col: number, row: number, seed: number): number
	local base = mix(math.floor(col), math.floor(row), seed)
	-- lichte ruimtelijke clustering: "hotspots" rond wurten geven hogere waarden
	local cluster = mix(math.floor(col / 4), math.floor(row / 4), seed + 7)
	local v = math.floor(base * 0.7 + cluster * 0.3)
	return math.clamp(v, 0, 100)
end

-- Bepaal de vondst bij het graven van een blok.
-- Regels: value < 10  → ALTIJD roestig ijzer.
--         anders      → gewogen loot, zwaarte schaalt met value + context.
-- context = { coastal = bool, wurt = bool } uit Cadastre.
function MetalField.dig(col: number, row: number, seed: number, context: {coastal: boolean?, wurt: boolean?}, rng: Random)
	local v = MetalField.value(col, row, seed)
	if v < GameConfig.METAL.rustyThreshold then
		return LootTables.RUSTY_IRON, v
	end
	local find = LootTables.roll(v, context or {}, rng)
	return find, v
end

return MetalField
