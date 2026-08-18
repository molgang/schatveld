--!strict
-- WorldBuilder — bouwt het speelveld (grid van Flurstück-blokken) in de Workspace,
-- gethematiseerd als Noord-Duits marschland: kleigrond, een Deich aan de westrand,
-- Gräben (sloten) tussen de stroken, en een verhoogde Wurt bij Weddewarden.
local RS = game:GetService("ReplicatedStorage")
local Shared = RS:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("GameConfig"))
local Cadastre   = require(Shared:WaitForChild("Cadastre"))

Cadastre.build(20260818)

local G = GameConfig.GRID
local root = Instance.new("Model"); root.Name = "Schatveld"
local blocks = Instance.new("Folder"); blocks.Name = "Blocks"; blocks.Parent = root

local USE_COLOR = {
	Acker   = Color3.fromRGB(120, 96, 66),   -- bruine klei-akker
	["Grünland"] = Color3.fromRGB(96, 132, 74),
	Wurt    = Color3.fromRGB(110, 120, 90),   -- verhoogde woonheuvel
	Deich   = Color3.fromRGB(88, 120, 78),    -- grasdijk
	Wasser  = Color3.fromRGB(60, 96, 130),
}

for r = 0, G.rows - 1 do
	for c = 0, G.cols - 1 do
		local parcel = Cadastre.parcelAt(c, r)
		local use = parcel and parcel.use or "Acker"
		local part = Instance.new("Part")
		part.Anchored = true
		part.Size = Vector3.new(G.block, use == "Wurt" and 3 or 1, G.block)
		local y = G.baseY + (use == "Wurt" and 1.5 or 0)
		part.Position = Vector3.new((c - G.cols/2) * G.block, y, (r - G.rows/2) * G.block)
		part.Color = USE_COLOR[use] or USE_COLOR.Acker
		part.Material = (use == "Deich" or use == "Grünland") and Enum.Material.Grass or Enum.Material.Ground
		part.TopSurface = Enum.SurfaceType.Smooth
		part:SetAttribute("col", c)
		part:SetAttribute("row", r)
		part:SetAttribute("use", use)
		part:SetAttribute("parcel", parcel and parcel.id or "")
		part.Name = string.format("B_%d_%d", c, r)
		part.Parent = blocks
	end
end

-- Gräben (smalle waterstroken) tussen de percelen-segmenten (visueel).
local ditch = Instance.new("Part")
ditch.Anchored = true; ditch.Size = Vector3.new(G.cols * G.block, 0.4, 1.5)
ditch.Position = Vector3.new(0, G.baseY + 0.3, 0)
ditch.Color = USE_COLOR.Wasser; ditch.Material = Enum.Material.Water; ditch.Name = "Graben"
ditch.Parent = root

root.Parent = workspace

-- Een bordje bij de Wurt (sfeer + herkenbaarheid).
local sign = Instance.new("Part")
sign.Anchored = true; sign.Size = Vector3.new(6, 2, 0.3)
sign.Position = Vector3.new((-G.cols/2 + 4) * G.block, G.baseY + 3, (-G.rows/2 + 4) * G.block)
sign.Color = Color3.fromRGB(60, 44, 30); sign.Name = "WurtSign"; sign.Parent = workspace
local sg = Instance.new("SurfaceGui"); sg.Face = Enum.NormalId.Front; sg.Parent = sign
local lbl = Instance.new("TextLabel"); lbl.Size = UDim2.fromScale(1,1); lbl.BackgroundTransparency = 1
lbl.TextScaled = true; lbl.TextColor3 = Color3.fromRGB(240,230,200)
lbl.Text = "Wurt Weddewarden · Land Wursten"; lbl.Parent = sg

print("[Schatveld] veld gebouwd: " .. (G.cols * G.rows) .. " Flurstück-blokken")
