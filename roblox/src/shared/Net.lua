--!strict
-- Net — centrale definitie van de RemoteEvents/Functions (server-authoritatief).
-- De server maakt ze aan; de client haalt ze op. Client stuurt alleen verzoeken;
-- alle validatie (rol, geld, cooldown, RNG-loot) gebeurt op de server.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Net = {}

local NAMES_EVENTS = {
	"ChooseRole",     -- client -> server: kies Boer/Archeoloog/Politie
	"Dig",            -- client -> server: graaf blok {col,row}
	"Buy",            -- client -> server: koop winkelitem {key}
	"Plough",         -- client -> server (Boer): ploeg + zaai {col,row,crop}
	"Spray",          -- client -> server (Boer): bespuit {col,row,agent,dose}
	"Fine",           -- client -> server (Politie): beboet {targetUserId,reason}
	"Notify",         -- server -> client: toast/HUD-melding {text,kind}
	"StateSync",      -- server -> client: profiel/HUD sync {coins,role,inv,rep}
	"FieldSync",      -- server -> client: metaalwaarden batch {seed}
}
local NAMES_FUNCS = {
	"GetField",       -- client -> server: vraag metaalwaarden rond speler
	"GetParcel",      -- client -> server: perceel-info bij blok
}

function Net.setupServer()
	local folder = Instance.new("Folder")
	folder.Name = "SchatveldNet"
	for _, n in ipairs(NAMES_EVENTS) do
		local ev = Instance.new("RemoteEvent"); ev.Name = n; ev.Parent = folder
	end
	for _, n in ipairs(NAMES_FUNCS) do
		local fn = Instance.new("RemoteFunction"); fn.Name = n; fn.Parent = folder
	end
	folder.Parent = ReplicatedStorage
	return folder
end

function Net.event(name: string): RemoteEvent
	local folder = ReplicatedStorage:WaitForChild("SchatveldNet")
	return folder:WaitForChild(name) :: RemoteEvent
end

function Net.func(name: string): RemoteFunction
	local folder = ReplicatedStorage:WaitForChild("SchatveldNet")
	return folder:WaitForChild(name) :: RemoteFunction
end

return Net
