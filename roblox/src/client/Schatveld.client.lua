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
local Net = require(Shared:WaitForChild("Net"))

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
local hud = mkFrame(UDim2.new(1,-250,0,12), UDim2.fromOffset(238,120))
local hCoins = mkText(hud, UDim2.fromOffset(12,8), UDim2.fromOffset(214,20), "€ —", 18, Color3.fromRGB(245,205,80))
local hRole  = mkText(hud, UDim2.fromOffset(12,34), UDim2.fromOffset(214,20), "Rol: —")
local hRep   = mkText(hud, UDim2.fromOffset(12,58), UDim2.fromOffset(214,20), "Reputatie: 0")
local hMode  = mkText(hud, UDim2.fromOffset(12,82), UDim2.fromOffset(214,20), "Modus: Graven", 15, Color3.fromRGB(140,220,180))

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
local shopFrame
local function toggleShop()
	if shopFrame then shopFrame:Destroy(); shopFrame = nil; return end
	shopFrame = mkFrame(UDim2.new(0,12,0.5,-140), UDim2.fromOffset(300,300))
	mkText(shopFrame, UDim2.fromOffset(12,8), UDim2.fromOffset(276,22), "🛒 Winkel", 18)
	local y = 40
	for key, item in pairs(GameConfig.SHOP) do
		local b = mkButton(shopFrame, UDim2.fromOffset(12,y), UDim2.fromOffset(276,52),
			string.format("%s — €%d", key, item.price), function()
				Net.event("Buy"):FireServer(key)
			end)
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

-- ---------- server -> client ----------
Net.event("Notify").OnClientEvent:Connect(function(d) showToast(d.text, d.kind) end)
Net.event("StateSync").OnClientEvent:Connect(function(s)
	state.role, state.coins, state.rep = s.role, s.coins, s.rep
	state.tools, state.permit = s.tools or {}, s.permit
	hCoins.Text = "€ " .. tostring(s.coins)
	hRole.Text = "Rol: " .. tostring(s.role or "—")
	hRep.Text = "Reputatie: " .. tostring(s.rep)
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

RunService.RenderStepped:Connect(function()
	if os.clock() > toastUntil then toast.Text = "" end
	local part, col, row = blockUnderMouse()
	if part then
		hoverBB.Adornee = part; hoverBB.Enabled = true
		if state.tools["Metaaldetector"] then
			local v = Net.func("GetField"):InvokeServer({ col = col, row = row })
			-- server geeft batch; zoek dit blok
			local val
			for _, e in ipairs(v) do if e.col == col and e.row == row then val = e.v end end
			hoverLbl.Text = tostring(val or "?")
			hoverLbl.TextColor3 = (val or 0) < GameConfig.METAL.rustyThreshold
				and Color3.fromRGB(180,140,120)        -- <10 = roestig ijzer
				or (val or 0) >= 70 and Color3.fromRGB(245,215,90) or Color3.fromRGB(230,235,245)
		else
			hoverLbl.Text = "?"; hoverLbl.TextColor3 = Color3.fromRGB(160,170,180)
		end
	else
		hoverBB.Enabled = false
	end
end)

mouse.Button1Down:Connect(function()
	local part, col, row = blockUnderMouse()
	if not part then return end
	if state.mode == "Graven" then
		Net.event("Dig"):FireServer({ col = col, row = row })
	elseif state.mode == "Ploegen" then
		local crop = GameConfig.CROPS[cropIndex]
		cropIndex = (cropIndex % #GameConfig.CROPS) + 1
		Net.event("Plough"):FireServer({ col = col, row = row, crop = crop })
	elseif state.mode == "Bespuiten" then
		Net.event("Spray"):FireServer({ col = col, row = row, agent = "Standaard", dose = 1 })
	elseif state.mode == "Beboeten" then
		-- politie: klik op een blok = beboet de dichtstbijzijnde speler die er groef.
		-- (vereenvoudigd: stuur reden op basis van context; server verifieert)
		Net.event("Fine"):FireServer({ targetUserId = plr.UserId, reason = "Raubgrabung" })
	end
end)

UIS.InputBegan:Connect(function(i, gp)
	if gp then return end
	if i.KeyCode == Enum.KeyCode.B then toggleShop() end
end)

showRolePicker()
print("[Schatveld] client UI geladen")
