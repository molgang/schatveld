--!strict
-- Schatveld client — UI + input. Toont per blok de metaalwaarde 0..100 (detector),
-- laat de speler graven/ploegen/bespuiten/beboeten via de gekozen modus, en rendert
-- HUD, rolkeuze, winkel en meldingen. Alle beslissingen worden server-side gevalideerd.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")

local plr = Players.LocalPlayer
local Shared = RS:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("GameConfig"))
local MetalField = require(Shared:WaitForChild("MetalField"))   -- detector rekent client-side
local Net = require(Shared:WaitForChild("Net"))
local SEED = GameConfig.WORLD.seed                              -- ÉÉN seedbron (= server)

local state = { role = nil :: string?, coins = 0, rep = 0, tools = {}, permit = false, mode = "Graven" }

-- ---------- UI-helpers ----------
local gui = Instance.new("ScreenGui"); gui.Name = "SchatveldUI"; gui.ResetOnSpawn = false
gui.Parent = plr:WaitForChild("PlayerGui")

local function mkFrame(pos, size, color)
	local f = Instance.new("Frame"); f.Position = pos; f.Size = size
	f.BackgroundColor3 = color or Color3.fromRGB(18,24,32); f.BackgroundTransparency = 0.1
	f.BorderSizePixel = 0; f.Parent = gui
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0,10); c.Parent = f
	return f
end
local function mkText(parent, pos, size, txt, sz, color)
	local t = Instance.new("TextLabel"); t.Position = pos; t.Size = size; t.BackgroundTransparency = 1
	t.Text = txt; t.Font = Enum.Font.GothamMedium; t.TextSize = sz or 16
	t.TextColor3 = color or Color3.fromRGB(235,242,248); t.TextXAlignment = Enum.TextXAlignment.Left
	t.Parent = parent; return t
end
local function mkButton(parent, pos, size, txt, cb)
	local b = Instance.new("TextButton"); b.Position = pos; b.Size = size; b.Text = txt
	b.Font = Enum.Font.GothamBold; b.TextSize = 15; b.TextColor3 = Color3.fromRGB(235,242,248)
	b.BackgroundColor3 = Color3.fromRGB(40,58,78); b.BorderSizePixel = 0; b.AutoButtonColor = true
	b.Parent = parent
	local c = Instance.new("UICorner"); c.CornerRadius = UDim.new(0,8); c.Parent = b
	b.Activated:Connect(cb); return b
end

-- HUD (rechtsboven)
local hud = mkFrame(UDim2.new(1,-262,0,12), UDim2.fromOffset(250,150))
local hCoins = mkText(hud, UDim2.fromOffset(12,8), UDim2.fromOffset(226,20), "€ —", 18, Color3.fromRGB(245,205,80))
local hRole  = mkText(hud, UDim2.fromOffset(12,34), UDim2.fromOffset(226,20), "Rol: —")
local hRep   = mkText(hud, UDim2.fromOffset(12,56), UDim2.fromOffset(226,20), "Reputatie: 0", 14)
local hMuseum= mkText(hud, UDim2.fromOffset(12,78), UDim2.fromOffset(226,20), "Museum: 0/13", 14, Color3.fromRGB(210,180,240))
local hMode  = mkText(hud, UDim2.fromOffset(12,102), UDim2.fromOffset(226,20), "Modus: Graven", 15, Color3.fromRGB(140,220,180))

-- Persistente doel-banner (boven-midden) — vervangt de verdwijnende toast als leidraad.
local objFrame = mkFrame(UDim2.new(0.5,-320,0,46), UDim2.fromOffset(640,30), Color3.fromRGB(24,32,44))
objFrame.BackgroundTransparency = 0.25
local objLbl = mkText(objFrame, UDim2.fromOffset(12,5), UDim2.fromOffset(616,20), "", 14, Color3.fromRGB(150,220,255))
objLbl.TextXAlignment = Enum.TextXAlignment.Center
objFrame.Visible = false

-- Detector-nabijheidsmeter (links-onder van het dradar-getal): vult mee met de max
-- metaalwaarde in het bereik — koud→heet. Plus een 'ping' die sneller/hoger wordt.
local meter = mkFrame(UDim2.new(0.5,-90,1,-104), UDim2.fromOffset(180,16), Color3.fromRGB(14,18,26))
local meterFill = Instance.new("Frame"); meterFill.Size = UDim2.fromScale(0,1)
meterFill.BackgroundColor3 = Color3.fromRGB(90,150,120); meterFill.BorderSizePixel = 0; meterFill.Parent = meter
local mfc = Instance.new("UICorner"); mfc.CornerRadius = UDim.new(0,8); mfc.Parent = meterFill
local meterLbl = mkText(meter, UDim2.fromOffset(6,-1), UDim2.fromOffset(168,18), "", 12, Color3.fromRGB(230,235,245))
meterLbl.TextXAlignment = Enum.TextXAlignment.Center
meter.Visible = false

-- Detector-ping (ingebouwd Roblox-geluid rbxasset://, geen upload nodig). Ook hergebruikt
-- als vondst-'chime' met hogere toonhoogte (ongeldige SoundId's falen stil, dus veilig).
local ping = Instance.new("Sound"); ping.SoundId = "rbxasset://sounds/electronicpingshort.wav"
ping.Volume = 0.5; ping.Parent = plr:WaitForChild("PlayerGui")
local function playPing(pitch: number, vol: number?)
	ping.PlaybackSpeed = pitch; ping.Volume = vol or 0.5; ping:Play()
end

-- Toast (midden-boven)
local toast = mkText(gui, UDim2.new(0.5,-300,0,14), UDim2.fromOffset(600,26), "", 16)
toast.TextXAlignment = Enum.TextXAlignment.Center
local toastUntil = 0
local function showToast(text, kind)
	toast.Text = text
	toast.TextColor3 = kind == "bad" and Color3.fromRGB(255,120,110)
		or kind == "warn" and Color3.fromRGB(245,190,90)
		or kind == "good" and Color3.fromRGB(140,230,170) or Color3.fromRGB(230,238,246)
	toastUntil = os.clock() + 4
end

-- Metaalwaarde-label boven het blok onder de muis (BillboardGui).
local hoverBB = Instance.new("BillboardGui"); hoverBB.Size = UDim2.fromOffset(64,32)
hoverBB.AlwaysOnTop = true; hoverBB.Enabled = false; hoverBB.Parent = gui
local hoverLbl = Instance.new("TextLabel"); hoverLbl.Size = UDim2.fromScale(1,1)
hoverLbl.BackgroundColor3 = Color3.fromRGB(10,14,20); hoverLbl.BackgroundTransparency = 0.25
hoverLbl.TextScaled = true; hoverLbl.Font = Enum.Font.GothamBold
hoverLbl.TextColor3 = Color3.fromRGB(245,240,220); hoverLbl.Text = "?"; hoverLbl.Parent = hoverBB
local hbCorner = Instance.new("UICorner"); hbCorner.CornerRadius = UDim.new(0,6); hbCorner.Parent = hoverLbl

-- ---------- rolkeuze ----------
local roleFrame
local function showRolePicker()
	if roleFrame then roleFrame:Destroy() end
	roleFrame = mkFrame(UDim2.new(0.5,-230,0.5,-90), UDim2.fromOffset(460,180))
	mkText(roleFrame, UDim2.fromOffset(16,10), UDim2.fromOffset(430,24), "Kies je rol — Schatveld Weddewarden", 18)
	local desc = {
		Boer = "Bescherm je land, doe goede gewasrotatie, houd je aan pesticide-regels.",
		Archeoloog = "Koop schep + metaaldetector, zoek en graaf (met vergunning!).",
		Politie = "Beboet schatgravers en boeren die de regels overtreden.",
	}
	local x = 16
	for _, role in ipairs(GameConfig.ROLES) do
		local b = mkButton(roleFrame, UDim2.fromOffset(x,44), UDim2.fromOffset(140,90), role, function()
			Net.event("ChooseRole"):FireServer(role)
			roleFrame:Destroy(); roleFrame = nil
		end)
		mkText(b, UDim2.fromOffset(6,54), UDim2.fromOffset(128,34), desc[role], 11).TextWrapped = true
		x += 148
	end
end

-- ---------- winkel ----------
local SHOP_ORDER = { "Schep", "Nachforschungsgenehmigung", "Metaaldetector", "Zeef" }
local shopFrame
local function ownsItem(item): boolean
	if item.permit then return state.permit == true end
	return item.tool ~= nil and state.tools[item.tool] == true
end
local function toggleShop()
	if shopFrame then shopFrame:Destroy(); shopFrame = nil; return end
	shopFrame = mkFrame(UDim2.new(0,12,0.5,-160), UDim2.fromOffset(300,330))
	mkText(shopFrame, UDim2.fromOffset(12,8), UDim2.fromOffset(276,22), "🛒 Winkel", 18)
	mkText(shopFrame, UDim2.fromOffset(12,30), UDim2.fromOffset(276,16),
		"Legaal graven: Schep + Nachforschungsgenehmigung", 11, Color3.fromRGB(150,220,255))
	local y = 50
	for _, key in ipairs(SHOP_ORDER) do
		local item = GameConfig.SHOP[key]
		local owned = ownsItem(item)
		local afford = state.coins >= item.price
		local label = owned and string.format("✓ %s — in bezit", key)
			or string.format("%s — €%d%s", key, item.price, afford and "" or "  (te duur)")
		local b = mkButton(shopFrame, UDim2.fromOffset(12,y), UDim2.fromOffset(276,52), label, function()
			if not owned then Net.event("Buy"):FireServer(key) end
		end)
		b.BackgroundColor3 = owned and Color3.fromRGB(30,44,36)
			or afford and Color3.fromRGB(40,58,78) or Color3.fromRGB(46,40,44)
		b.AutoButtonColor = not owned
		mkText(b, UDim2.fromOffset(8,30), UDim2.fromOffset(264,18), item.desc, 11)
		y += 58
	end
end

-- ---------- modusknoppen (afhankelijk van rol) ----------
local modeBar = mkFrame(UDim2.new(0.5,-260,1,-58), UDim2.fromOffset(520,46))
local function rebuildModes()
	for _, ch in ipairs(modeBar:GetChildren()) do if ch:IsA("TextButton") then ch:Destroy() end end
	local modes = { Archeoloog = {"Graven"}, Boer = {"Ploegen","Bespuiten"}, Politie = {"Beboeten"} }
	local list = modes[state.role or ""] or {"Graven"}
	local x = 8
	for _, m in ipairs(list) do
		mkButton(modeBar, UDim2.fromOffset(x,7), UDim2.fromOffset(150,32), m, function()
			state.mode = m; hMode.Text = "Modus: " .. m
		end); x += 158
	end
	mkButton(modeBar, UDim2.fromOffset(x,7), UDim2.fromOffset(120,32), "Winkel", toggleShop)
	state.mode = list[1]; hMode.Text = "Modus: " .. list[1]
end

-- ---------- vondst-kaart + deeltjes ----------
local lastDigPart: BasePart? = nil
local RARITY = { scrap = Color3.fromRGB(150,140,130), stone = Color3.fromRGB(150,160,170),
	agrarian_iron = Color3.fromRGB(180,150,110), curio = Color3.fromRGB(150,200,170),
	gem = Color3.fromRGB(245,200,80), coin = Color3.fromRGB(240,215,120),
	artifact = Color3.fromRGB(220,150,240) }

local function dirtBurst(part: BasePart)
	local a = Instance.new("Attachment"); a.Parent = part
	local e = Instance.new("ParticleEmitter"); e.Parent = a
	e.Texture = "rbxasset://textures/particles/smoke_main.dds"
	e.Color = ColorSequence.new(Color3.fromRGB(120,92,60))
	e.Lifetime = NumberRange.new(0.4,0.7); e.Speed = NumberRange.new(6,10)
	e.SpreadAngle = Vector2.new(180,180); e.Rate = 0; e.Rotation = NumberRange.new(0,360)
	e.Size = NumberSequence.new(0.6)
	e:Emit(26)
	task.delay(1, function() a:Destroy() end)
end

local function showFoundCard(dig)
	local col = RARITY[dig.kind] or Color3.fromRGB(230,235,245)
	local card = mkFrame(UDim2.new(0.5,-150,0,84), UDim2.fromOffset(300,74), Color3.fromRGB(20,26,34))
	local bar = Instance.new("Frame"); bar.Size = UDim2.fromOffset(6,74); bar.Position = UDim2.fromOffset(0,0)
	bar.BackgroundColor3 = col; bar.BorderSizePixel = 0; bar.Parent = card
	mkText(card, UDim2.fromOffset(16,8), UDim2.fromOffset(276,22), dig.name, 16, col)
	mkText(card, UDim2.fromOffset(16,32), UDim2.fromOffset(276,18),
		string.format("metaal %d · €%d", dig.value, dig.payout), 13)
	local banner = dig.confiscated and "⚑ Schatzregal → beschlagnahmt"
		or dig.schatzregal and "⚑ Schatzregal → Land Bremen"
		or dig.illegal and "⚠ Raubgrabung" or (dig.firstFind and "★ Neu im Landesmuseum!" or "")
	if banner ~= "" then
		mkText(card, UDim2.fromOffset(16,50), UDim2.fromOffset(276,18), banner, 12,
			dig.illegal and Color3.fromRGB(255,120,110) or Color3.fromRGB(245,205,90))
	end
	if lastDigPart then dirtBurst(lastDigPart) end
	-- vondst-'chime': hoger bij waardevollere/bijzondere vondst
	playPing(dig.schatzregal and 1.9 or (0.9 + dig.value/100), 0.6)
	task.delay(3.5, function() card:Destroy() end)
end

-- ---------- server -> client ----------
Net.event("Notify").OnClientEvent:Connect(function(d)
	showToast(d.text, d.kind)
	if d.dig then showFoundCard(d.dig) end
end)
Net.event("StateSync").OnClientEvent:Connect(function(s)
	state.role, state.coins, state.rep = s.role, s.coins, s.rep
	state.tools, state.permit = s.tools or {}, s.permit
	hCoins.Text = "€ " .. tostring(s.coins)
	hRole.Text = "Rol: " .. tostring(s.role or "—")
	hRep.Text = string.format("Reputatie: %d · %s", s.rep, s.rank or "—")
	hMuseum.Text = string.format("Museum: %d/%d", s.museum or 0, s.museumTotal or 13)
	if s.objective and s.objective ~= "" then
		objLbl.Text = "🎯 " .. s.objective; objFrame.Visible = true
	end
	if shopFrame then shopFrame:Destroy(); shopFrame = nil; toggleShop() end   -- ververs bezit/prijzen
	if s.role then rebuildModes() elseif not roleFrame then showRolePicker() end
end)

-- ---------- input: hover-nummer + klik-actie ----------
local mouse = plr:GetMouse()
local cropIndex = 1

local function blockUnderMouse(): (BasePart?, number, number)
	local t = mouse.Target
	if t and t:IsDescendantOf(workspace) and t:GetAttribute("col") ~= nil then
		return t, t:GetAttribute("col") :: number, t:GetAttribute("row") :: number
	end
	return nil, -1, -1
end

-- Detector is nu client-side (MetalField is deterministisch + gedeeld) → GÉÉN server-
-- round-trip per frame meer. Zwaar rekenwerk (buurschap-max) alleen bij blokwissel.
local lastHoverKey, nbMax, nextBeep = "", 0, 0
RunService.RenderStepped:Connect(function()
	if os.clock() > toastUntil then toast.Text = "" end
	local part, col, row = blockUnderMouse()
	if part and state.tools["Metaaldetector"] then
		hoverBB.Adornee = part; hoverBB.Enabled = true
		local key = col .. "," .. row
		if key ~= lastHoverKey then
			lastHoverKey = key
			local v = MetalField.value(col, row, SEED)          -- lokaal, geen network
			local rng = GameConfig.METAL.detectorRange
			local mx = 0
			for c = col - rng, col + rng do for r = row - rng, row + rng do
				local vv = MetalField.value(c, r, SEED); if vv > mx then mx = vv end
			end end
			nbMax = mx
			hoverLbl.Text = tostring(v)
			hoverLbl.TextColor3 = v < GameConfig.METAL.rustyThreshold and Color3.fromRGB(180,140,120)
				or v >= 70 and Color3.fromRGB(245,215,90) or Color3.fromRGB(230,235,245)
			meter.Visible = true
			meterFill.Size = UDim2.fromScale(math.clamp(mx/100, 0, 1), 1)
			meterFill.BackgroundColor3 = Color3.fromRGB(math.clamp(70+mx*1.7,70,255),
				math.clamp(160-mx*0.5,90,160), math.clamp(120-mx*0.9,40,120))
			meterLbl.Text = string.format("detector · max nabij: %d", mx)
		end
		-- nabijheids-ping: koud = traag/laag, heet (≥70) = snel/hoog (echte detector-feel)
		if os.clock() >= nextBeep then
			local t = nbMax / 100
			playPing(0.7 + t * 1.6, 0.3 + t * 0.3)
			nextBeep = os.clock() + (0.9 - t * 0.78)
		end
	elseif part then
		hoverBB.Adornee = part; hoverBB.Enabled = true
		hoverLbl.Text = "?"; hoverLbl.TextColor3 = Color3.fromRGB(160,170,180)
		meter.Visible = false; lastHoverKey = ""
	else
		hoverBB.Enabled = false; meter.Visible = false; lastHoverKey = ""
	end
end)

mouse.Button1Down:Connect(function()
	local part, col, row = blockUnderMouse()
	if not part then return end
	if state.mode == "Graven" then
		lastDigPart = part                       -- onthoud voor de deeltjes-burst
		Net.event("Dig"):FireServer({ col = col, row = row })
	elseif state.mode == "Ploegen" then
		local crop = GameConfig.CROPS[cropIndex]
		cropIndex = (cropIndex % #GameConfig.CROPS) + 1
		showToast("Zaai: " .. crop .. "  (klik opnieuw voor het volgende gewas)", "info")
		Net.event("Plough"):FireServer({ col = col, row = row, crop = crop })
	elseif state.mode == "Bespuiten" then
		Net.event("Spray"):FireServer({ col = col, row = row, agent = "Standaard", dose = 1 })
	elseif state.mode == "Beboeten" then
		-- politie: klik op het BLOK; de server zoekt de echte overtreder daar.
		Net.event("Fine"):FireServer({ col = col, row = row })
	end
end)

UIS.InputBegan:Connect(function(i, gp)
	if gp then return end
	if i.KeyCode == Enum.KeyCode.B then toggleShop() end
end)

showRolePicker()
print("[Schatveld] client UI geladen")
