--!strict
-- LootTables — realistische vondsten voor een Noord-Duits marschveld (Land Wursten).
-- Gegrond op onderzoek: roestig agrarisch ijzer zeer algemeen; Feuerstein/Hühnergott
-- en kwarts algemeen als "gems"; barnsteen (Bernstein) occasioneel aan de kust;
-- middeleeuwse/vroegmoderne munten zeldzaam, goudschat zeer zeldzaam; Wurten-
-- artefacten (Fibeln, aardewerk, "Thron-graf") als zeldzame beschavingsvondst.
-- GEEN diamanten/saffieren — dat breekt de realiteit.
local LootTables = {}

export type Find = {
	id: string, name: string, kind: string, value: number, weight: number,
	state: boolean?, -- true = valt onder het Schatzregal (staatsbezit)
}

LootTables.RUSTY_IRON = { id = "rusty_iron", name = "Roestig ijzer", kind = "scrap", value = 2, weight = 0 } :: Find

-- Basistabel (weight = relatieve kans; wordt geschaald met metaalwaarde/context).
local TABLE: {Find} = {
	{ id = "plough_iron",  name = "Ploegijzer (Pflugschar)",       kind = "agrarian_iron", value = 15,  weight = 40 },
	{ id = "horseshoe",    name = "Hoefijzer",                     kind = "agrarian_iron", value = 20,  weight = 30 },
	{ id = "nails",        name = "Handgesmede spijkers",          kind = "agrarian_iron", value = 8,   weight = 45 },
	{ id = "tool_scrap",   name = "Gereedschapsschroot",           kind = "agrarian_iron", value = 12,  weight = 35 },
	{ id = "flint",        name = "Feuerstein-knol",               kind = "stone",         value = 5,   weight = 40 },
	{ id = "huhnergott",   name = "Hühnergott (gat-vuursteen)",    kind = "curio",         value = 30,  weight = 10 },
	{ id = "quartz",       name = "Kwartskei",                     kind = "stone",         value = 6,   weight = 25 },
	{ id = "amber",        name = "Barnsteen (Bernstein)",         kind = "gem",           value = 90,  weight = 6 },
	{ id = "sherd",        name = "Aardewerkscherf",               kind = "artifact",      value = 25,  weight = 18 },
	{ id = "fibula",       name = "Fibula (mantelspeld)",          kind = "artifact",      value = 160, weight = 5,  state = true },
	{ id = "coin_medieval",name = "Middeleeuwse munt",             kind = "coin",          value = 120, weight = 6 },
	{ id = "coin_gold",    name = "Gouden munt",                   kind = "coin",          value = 350, weight = 2,  state = true },
	{ id = "throne_relic", name = "Wurt-artefact (Thron-graf)",    kind = "artifact",      value = 600, weight = 1,  state = true },
}

-- Gewogen trekking; zwaarte schaalt met metaalwaarde v (0..100) en context.
function LootTables.roll(v: number, context: {coastal: boolean?, wurt: boolean?}, rng: Random): Find
	local vf = v / 100                      -- 0..1
	local total = 0
	local weights: {number} = {}
	for i, f in ipairs(TABLE) do
		local w = f.weight
		-- hoge metaalwaarde → meer metaal (ijzer/munt/fibula), minder steen
		if f.kind == "agrarian_iron" or f.kind == "coin" then w = w * (0.5 + vf * 1.5) end
		if f.kind == "stone" then w = w * (1.3 - vf) end
		-- context: kust → barnsteen vaker; wurt → artefacten vaker
		if f.id == "amber" and context.coastal then w = w * 4 end
		if f.kind == "artifact" and context.wurt then w = w * 3 end
		weights[i] = math.max(w, 0.01)
		total += weights[i]
	end
	local pick = rng:NextNumber(0, total)
	local acc = 0
	for i, f in ipairs(TABLE) do
		acc += weights[i]
		if pick <= acc then return f end
	end
	return TABLE[1]
end

LootTables.ALL = TABLE
return LootTables
