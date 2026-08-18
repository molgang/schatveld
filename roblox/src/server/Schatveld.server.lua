--!strict
-- Schatveld — server-autoriteit. Alle spelregels, RNG-loot, geld en handhaving
-- draaien hier; de client stuurt alleen verzoeken (never trust the client).
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")

local Shared = RS:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("GameConfig"))
local MetalField = require(Shared:WaitForChild("MetalField"))
local LootTables = require(Shared:WaitForChild("LootTables"))
local Cadastre   = require(Shared:WaitForChild("Cadastre"))
local Net        = require(Shared:WaitForChild("Net"))
local Api        = require(Shared:WaitForChild("Api"))
-- ONE BRAIN: als de Python-brain (pybrain/api.py) bereikbaar is, is die de
-- autoriteit voor de vondst — exact hetzelfde resultaat als de Minecraft-wereld.
-- Anders valt de server terug op de lokale MetalField/LootTables.
local USE_BRAIN = true

Net.setupServer()
local WORLD_SEED = 20260818
Cadastre.build(WORLD_SEED)

local rng = Random.new(WORLD_SEED)
local store = DataStoreService:GetDataStore("Schatveld_v1")

type Profile = {
	role: string?, coins: number, rep: number,
	tools: {[string]: boolean}, permit: boolean,
	inv: {[string]: number},                 -- vondst-id -> aantal
	lastCropByParcel: {[string]: string},
	pesticideByParcel: {[string]: number},
	digLog: {{col: number, row: number, at: number}},   -- voor Politie-handhaving
}

local profiles: {[number]: Profile} = {}

local function newProfile(): Profile
	return { role = nil, coins = 250, rep = 0, tools = {}, permit = false,
		inv = {}, lastCropByParcel = {}, pesticideByParcel = {}, digLog = {} }
end

local function load(userId: number): Profile
	local ok, data = pcall(function() return store:GetAsync("p_" .. userId) end)
	if ok and typeof(data) == "table" then
		local p = newProfile()
		for k, v in pairs(data) do (p :: any)[k] = v end
		return p
	end
	return newProfile()
end

local function save(userId: number)
	local p = profiles[userId]; if not p then return end
	pcall(function() store:SetAsync("p_" .. userId, p) end)
end

local function notify(plr: Player, text: string, kind: string?)
	Net.event("Notify"):FireClient(plr, { text = text, kind = kind or "info" })
end

local function sync(plr: Player)
	local p = profiles[plr.UserId]; if not p then return end
	Net.event("StateSync"):FireClient(plr, {
		role = p.role, coins = p.coins, rep = p.rep, tools = p.tools,
		permit = p.permit, inv = p.inv,
	})
end

-- ---------- verbindingen ----------
Players.PlayerAdded:Connect(function(plr)
	profiles[plr.UserId] = load(plr.UserId)
	task.wait(0.5); sync(plr)
	notify(plr, "Welkom in Schatveld — Weddewarden (Land Wursten). Kies je rol.", "info")
end)
Players.PlayerRemoving:Connect(function(plr)
	save(plr.UserId); profiles[plr.UserId] = nil
end)
game:BindToClose(function() for id in pairs(profiles) do save(id) end end)

-- ---------- RemoteFunctions ----------
Net.func("GetField").OnServerInvoke = function(_plr, center)
	-- geef metaalwaarden rond een centrum-blok (detector-bereik).
	local out = {}
	local rng2 = GameConfig.METAL.detectorRange
	local cc, cr = math.floor(center.col or 0), math.floor(center.row or 0)
	for c = cc - rng2, cc + rng2 do
		for r = cr - rng2, cr + rng2 do
			if c >= 0 and r >= 0 and c < GameConfig.GRID.cols and r < GameConfig.GRID.rows then
				table.insert(out, { col = c, row = r, v = MetalField.value(c, r, WORLD_SEED) })
			end
		end
	end
	return out
end

Net.func("GetParcel").OnServerInvoke = function(_plr, b)
	local p = Cadastre.parcelAt(math.floor(b.col or 0), math.floor(b.row or 0))
	if not p then return nil end
	return { id = p.id, use = p.use, owner = p.owner, coastal = p.coastal, wurt = p.wurt }
end

-- ---------- ChooseRole ----------
Net.event("ChooseRole").OnServerEvent:Connect(function(plr, role)
	local p = profiles[plr.UserId]; if not p then return end
	if not table.find(GameConfig.ROLES, role) then return end
	p.role = role
	-- Boer krijgt een paar eigen Flurstücke toegewezen.
	if role == "Boer" then
		local n = 0
		for _, parcel in ipairs(Cadastre.all()) do
			if parcel.use == "Acker" and not parcel.owner and n < 4 then
				parcel.owner = tostring(plr.UserId); n += 1
			end
		end
	end
	notify(plr, "Rol gekozen: " .. role, "good")
	sync(plr)
end)

-- ---------- Dig (Archeoloog primair; iedereen kan graven maar met gevolgen) ----------
Net.event("Dig").OnServerEvent:Connect(function(plr, b)
	local p = profiles[plr.UserId]; if not p then return end
	local col, row = math.floor(b.col or -1), math.floor(b.row or -1)
	if col < 0 or row < 0 then return end
	if not p.tools["Schep"] then notify(plr, "Je hebt een schep nodig (koop in de winkel).", "bad"); return end

	local parcel = Cadastre.parcelAt(col, row)
	-- juridische context: eigendom + vergunning (Schatzregal / §903 BGB / Nachforschung)
	local onOwnLand = parcel and parcel.owner == tostring(plr.UserId)
	local illegal = (not p.permit) or (parcel and parcel.owner and not onOwnLand)
	table.insert(p.digLog, { col = col, row = row, at = os.time(), illegal = illegal } :: any)

	-- One brain: vraag de Python-brain om de vondst (gedeeld met Minecraft).
	if USE_BRAIN then
		local api = Api.dig(tostring(plr.UserId), col, row)
		if api and api.ok then
			p.inv[api.find.id] = (p.inv[api.find.id] or 0) + 1
			p.coins += api.payout
			if api.schatzregal then p.rep += 5 end
			if api.illegal then p.rep -= 3 end
			local m = string.format("Metaalwaarde %d — gevonden: %s (via Python-brain, €%d)",
				api.metal, api.find.name, api.payout)
			if api.schatzregal then m ..= "  · Schatzregal → Land Bremen" end
			if api.illegal then m ..= "  ⚠ Raubgrabung" end
			notify(plr, m, api.illegal and "warn" or "good")
			sync(plr)
			return
		end
	end

	local ctx = Cadastre.context(col, row)
	local find, value = MetalField.dig(col, row, WORLD_SEED, ctx, rng)

	-- vondst afhandelen (Schatzregal: significante vondst → grotendeels staatsbezit)
	local payout = find.value
	local msg = string.format("Metaalwaarde %d — gevonden: %s", value, find.name)
	if find.state or find.value >= GameConfig.SCHATZREGAL.significantValue then
		payout = math.floor(find.value * GameConfig.SCHATZREGAL.finderFeeFraction)
		msg ..= string.format("  · Schatzregal: %s → Land Bremen, vindersloon €%d", find.name, payout)
		p.rep += 5
	end
	p.inv[find.id] = (p.inv[find.id] or 0) + 1
	p.coins += payout
	if illegal then
		p.rep -= 3
		msg ..= "  ⚠ zonder vergunning/op vreemd land = Raubgrabung (beboetbaar!)"
	end
	notify(plr, msg, illegal and "warn" or "good")
	sync(plr)
end)

-- ---------- Buy (winkel) ----------
Net.event("Buy").OnServerEvent:Connect(function(plr, key)
	local p = profiles[plr.UserId]; if not p then return end
	local item = GameConfig.SHOP[key]; if not item then return end
	if p.coins < item.price then notify(plr, "Te weinig geld voor " .. key, "bad"); return end
	p.coins -= item.price
	if item.tool then p.tools[item.tool] = true end
	if item.permit then p.permit = true end
	notify(plr, "Gekocht: " .. key, "good")
	sync(plr)
end)

-- ---------- Plough (Boer): gewasrotatie ----------
Net.event("Plough").OnServerEvent:Connect(function(plr, b)
	local p = profiles[plr.UserId]; if not p then return end
	if p.role ~= "Boer" then notify(plr, "Alleen een boer kan ploegen/zaaien.", "bad"); return end
	local parcel = Cadastre.parcelAt(math.floor(b.col or 0), math.floor(b.row or 0))
	if not parcel or parcel.owner ~= tostring(plr.UserId) then
		notify(plr, "Dit Flurstück is niet van jou (kadaster).", "bad"); return
	end
	local crop = b.crop
	if not table.find(GameConfig.CROPS, crop) then return end
	local prev = p.lastCropByParcel[parcel.id]
	local mult = 1.0
	if prev == crop then
		mult = GameConfig.ROTATION.monocultureMalus
	elseif prev and table.find(GameConfig.ROTATION.goodAfter[prev] or {}, crop) then
		mult = GameConfig.ROTATION.yieldBonus
	end
	local yield = math.floor(40 * mult)
	p.coins += yield
	p.lastCropByParcel[parcel.id] = crop
	p.pesticideByParcel[parcel.id] = 0   -- nieuw seizoen
	notify(plr, string.format("%s gezaaid op %s — oogst €%d (rotatie ×%.2f)", crop, parcel.id, yield, mult),
		mult >= 1 and "good" or "warn")
	sync(plr)
end)

-- ---------- Spray (Boer): pesticide-regels ----------
Net.event("Spray").OnServerEvent:Connect(function(plr, b)
	local p = profiles[plr.UserId]; if not p then return end
	if p.role ~= "Boer" then return end
	local col, row = math.floor(b.col or 0), math.floor(b.row or 0)
	local parcel = Cadastre.parcelAt(col, row)
	if not parcel then return end
	local violations = {}
	if parcel.owner ~= tostring(plr.UserId) then table.insert(violations, "vreemd Flurstück (§903 BGB)") end
	if table.find(GameConfig.PESTICIDE.banned, b.agent) then table.insert(violations, "verboden middel " .. tostring(b.agent)) end
	-- afstand tot water: kolom 0..1 = Deich/water → buffer
	if col <= (GameConfig.PESTICIDE.bufferToDitch) then table.insert(violations, "te dicht bij water (§4a PflSchAnwV)") end
	local dose = (p.pesticideByParcel[parcel.id] or 0) + (tonumber(b.dose) or 1)
	p.pesticideByParcel[parcel.id] = dose
	if dose > GameConfig.PESTICIDE.maxDosePerParcel then table.insert(violations, "te veel pesticide") end
	if #violations > 0 then
		p.rep -= #violations
		notify(plr, "⚠ Pesticide-overtreding: " .. table.concat(violations, ", ") .. " (beboetbaar door Politie)", "warn")
	else
		notify(plr, "Bespoten binnen de regels.", "good")
	end
	sync(plr)
end)

-- ---------- Fine (Politie): handhaving ----------
Net.event("Fine").OnServerEvent:Connect(function(plr, data)
	local cop = profiles[plr.UserId]; if not cop or cop.role ~= "Politie" then
		notify(plr, "Alleen de Politie kan beboeten.", "bad"); return end
	local target = Players:GetPlayerByUserId(tonumber(data.targetUserId) or -1)
	if not target then return end
	local tp = profiles[target.UserId]; if not tp then return end
	local reason = data.reason
	local amount = GameConfig.FINES[reason]
	if not amount then return end
	-- controleer of de overtreding echt bestaat (server verifieert)
	local valid = false
	if reason == "Raubgrabung" or reason == "TrespassDig" then
		for _, d in ipairs(tp.digLog) do if (d :: any).illegal then valid = true break end end
	elseif reason:sub(1, 9) == "Pesticide" then
		valid = tp.rep < 0 or false
		for _pid, dose in pairs(tp.pesticideByParcel) do if dose > GameConfig.PESTICIDE.maxDosePerParcel then valid = true end end
	end
	if not valid then notify(plr, "Geen bewijs voor deze overtreding.", "bad"); return end
	tp.coins = math.max(0, tp.coins - amount)
	cop.coins += math.floor(amount * 0.1)   -- premie/administratie
	cop.rep += 4
	notify(target, string.format("🚔 Boete €%d — %s", amount, reason), "bad")
	notify(plr, string.format("Boete uitgeschreven: €%d aan %s (%s)", amount, target.Name, reason), "good")
	sync(plr); sync(target)
end)

print("[Schatveld] server actief — Weddewarden, seed " .. WORLD_SEED)
