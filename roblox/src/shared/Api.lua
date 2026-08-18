--!strict
-- Api — HttpService-client naar de Python-brain (schatveld/pybrain/api.py).
-- Zo delen de Roblox-server en de Minecraft-server EXACT hetzelfde veld, dezelfde
-- loot-randomizer en dezelfde economie: één brain, twee werelden.
--
-- Zet in de game-instellingen "Allow HTTP Requests" AAN. In Studio-test bereikt
-- HttpService http://127.0.0.1:8791 (lokaal); in productie een publieke URL.
local HttpService = game:GetService("HttpService")

local Api = {}
Api.baseUrl = "http://127.0.0.1:8791"   -- pas aan naar je gehoste brain-URL

local function post(path: string, body: any): any?
	local ok, res = pcall(function()
		return HttpService:PostAsync(Api.baseUrl .. path,
			HttpService:JSONEncode(body), Enum.HttpContentType.ApplicationJson)
	end)
	if not ok then return nil end
	local ok2, decoded = pcall(function() return HttpService:JSONDecode(res) end)
	return ok2 and decoded or nil
end

local function get(path: string): any?
	local ok, res = pcall(function() return HttpService:GetAsync(Api.baseUrl .. path) end)
	if not ok then return nil end
	local ok2, decoded = pcall(function() return HttpService:JSONDecode(res) end)
	return ok2 and decoded or nil
end

function Api.health() return get("/health") end
function Api.join(user: string, role: string?) return post("/join", { user = user, role = role }) end
function Api.scan(col: number, row: number) return get(("/scan?col=%d&row=%d"):format(col, row)) end
function Api.dig(user: string, col: number, row: number) return post("/dig", { user = user, col = col, row = row }) end
function Api.buy(user: string, item: string) return post("/buy", { user = user, item = item }) end
function Api.plough(user: string, col: number, row: number, crop: string) return post("/plough", { user = user, col = col, row = row, crop = crop }) end
function Api.spray(user: string, col: number, row: number, agent: string, dose: number) return post("/spray", { user = user, col = col, row = row, agent = agent, dose = dose }) end
function Api.fine(cop: string, target: string, reason: string) return post("/fine", { cop = cop, target = target, reason = reason }) end
function Api.state(user: string) return get("/state?user=" .. HttpService:UrlEncode(user)) end

return Api
