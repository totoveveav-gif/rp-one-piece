--!strict
-- BaseService : crée les 8 bases, attribue une base à chaque joueur, le fait apparaître
-- dedans à chaque spawn, et libère la base quand il quitte le serveur.
--
-- Tout est décidé côté serveur : le client ne peut jamais choisir ni modifier sa base.
--
-- API publique (utilisée par les phases suivantes) :
--   BaseService.GetPlot(player)            -> Plot?
--   BaseService.GetLevel(player)           -> number
--   BaseService.SetLevel(player, level)
--   BaseService.GetUnlockedSlots(player)   -> { BasePart }
--   BaseService.SendHome(player)

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local BaseConfig = require(Shared:WaitForChild("Config"):WaitForChild("BaseConfig"))
local Net = require(Shared:WaitForChild("Net"))
local BaseBuilder = require(ServerScriptService:WaitForChild("Server"):WaitForChild("Builders"):WaitForChild("BaseBuilder"))

export type Plot = {
	Index: number,
	Model: Model,
	Origin: CFrame,
	Owner: Player?,
}

local BaseService = {}

local plots: { Plot } = {}
local plotByPlayer: { [Player]: Plot } = {}

local notifyRemote = Net.Event("Notify")

local function notify(player: Player, payload: { [string]: any })
	notifyRemote:FireClient(player, payload)
end

-- Position d'une base : 4 de chaque côté de la Monster Road, entrée tournée vers la route.
local function computeOrigin(index: number): CFrame
	local perSide = GameConfig.BASES_PER_SIDE
	local side = if index <= perSide then -1 else 1
	local row = (index - 1) % perSide
	local x = side * (GameConfig.ROAD_WIDTH / 2 + GameConfig.ROAD_TO_BASE_GAP + GameConfig.BASE_DEPTH / 2)
	local z = (row - (perSide - 1) / 2) * GameConfig.BASE_SPACING
	local center = Vector3.new(x, 0, z)
	-- LookVector (-Z local) pointe vers la route.
	return CFrame.lookAt(center, center + Vector3.new(-side, 0, 0))
end

-- Choisit une base libre. Si un ami est déjà sur le serveur, on prend la base libre la plus
-- proche de la sienne : jouer avec ses amis doit être naturel (voisins = entraide / rivalité).
local function choosePlot(player: Player): Plot?
	local friendPlots: { Plot } = {}
	for _, other in Players:GetPlayers() do
		local otherPlot = plotByPlayer[other]
		if other ~= player and otherPlot then
			local ok, isFriend = pcall(player.IsFriendsWithAsync, player, other.UserId)
			if ok and isFriend then
				table.insert(friendPlots, otherPlot)
			end
		end
	end

	-- IsFriendsWithAsync peut prendre du temps : on calcule les bases libres APRÈS les appels réseau.
	local best: Plot? = nil
	local bestDistance = math.huge
	for _, plot in plots do
		if plot.Owner == nil then
			if #friendPlots == 0 then
				return plot
			end
			for _, friendPlot in friendPlots do
				local distance = (plot.Origin.Position - friendPlot.Origin.Position).Magnitude
				if distance < bestDistance then
					bestDistance = distance
					best = plot
				end
			end
		end
	end
	return best
end

local function getSpawnCFrame(plot: Plot): CFrame
	local spawnPoint = plot.Model:FindFirstChild("SpawnPoint") :: BasePart
	-- Le joueur regarde vers le fond de la base (ses monstres), pas vers la route.
	return spawnPoint.CFrame * CFrame.Angles(0, math.rad(180), 0) + Vector3.new(0, 3, 0)
end

function BaseService.SendHome(player: Player)
	local plot = plotByPlayer[player]
	local character = player.Character
	if not plot or not character or not character.Parent then
		return
	end
	if not character:FindFirstChild("HumanoidRootPart") then
		return
	end
	character:PivotTo(getSpawnCFrame(plot))
end

function BaseService.GetPlot(player: Player): Plot?
	return plotByPlayer[player]
end

function BaseService.GetLevel(player: Player): number
	local plot = plotByPlayer[player]
	if not plot then
		return 1
	end
	return plot.Model:GetAttribute("Level") :: number
end

function BaseService.SetLevel(player: Player, level: number)
	local plot = plotByPlayer[player]
	if not plot then
		return
	end
	BaseBuilder.ApplyLevel(plot.Model, level)
end

function BaseService.GetUnlockedSlots(player: Player): { BasePart }
	local result: { BasePart } = {}
	local plot = plotByPlayer[player]
	if not plot then
		return result
	end
	local slots = plot.Model:FindFirstChild("Slots") :: Folder
	for _, slot in slots:GetChildren() do
		if slot:IsA("BasePart") and slot:GetAttribute("Unlocked") == true then
			table.insert(result, slot)
		end
	end
	table.sort(result, function(a, b)
		return (a:GetAttribute("SlotIndex") :: number) < (b:GetAttribute("SlotIndex") :: number)
	end)
	return result
end

local function assign(player: Player)
	if plotByPlayer[player] then
		return
	end

	local plot = choosePlot(player)
	if player.Parent ~= Players then
		return -- le joueur est parti pendant le choix
	end
	if not plot then
		warn(`[BaseService] Aucune base libre pour {player.Name}. Mets Max Players = {GameConfig.MAX_BASES}.`)
		notify(player, {
			Kind = "Banner",
			Title = "SERVER FULL",
			Subtitle = "No free base. Try another server!",
			Color = Color3.fromRGB(255, 90, 90),
		})
		return
	end

	plot.Owner = player
	plotByPlayer[player] = plot
	plot.Model:SetAttribute("OwnerUserId", player.UserId)
	plot.Model:SetAttribute("OwnerName", player.DisplayName)
	-- Phase 9 : le niveau viendra des données sauvegardées.
	BaseBuilder.ApplyLevel(plot.Model, 1)

	-- Attribut répliqué : le client s'en sert pour afficher le marqueur "YOUR BASE".
	player:SetAttribute("BaseIndex", plot.Index)

	BaseService.SendHome(player)

	notify(player, {
		Kind = "Banner",
		Title = "🏠 THIS IS YOUR BASE!",
		Subtitle = "Fill it with monsters. Protect it from thieves.",
		Color = plot.Model:GetAttribute("AccentColor"),
		Duration = 3.5,
	})
end

local function release(player: Player)
	local plot = plotByPlayer[player]
	if not plot then
		return
	end
	plotByPlayer[player] = nil
	plot.Owner = nil
	plot.Model:SetAttribute("OwnerUserId", 0)
	plot.Model:SetAttribute("OwnerName", "")
	BaseBuilder.ApplyLevel(plot.Model, 1)
end

local function onCharacterAdded(player: Player, character: Model)
	-- On attend que le personnage soit dans le Workspace et physiquement prêt,
	-- sinon le spawn par défaut de Roblox écrase notre téléportation.
	if not character.Parent then
		character.AncestryChanged:Wait()
	end
	if not character:WaitForChild("HumanoidRootPart", 10) then
		return
	end
	task.wait()
	if player.Character == character then
		BaseService.SendHome(player)
	end
end

-- Commandes de test (Roblox Studio uniquement) : "!lvl 1".."!lvl 7" et "!home".
local function onDebugChat(player: Player, message: string)
	local words = string.split(string.lower(message), " ")
	if words[1] == "!lvl" then
		local level = tonumber(words[2])
		if level then
			BaseService.SetLevel(player, level)
			local applied = BaseService.GetLevel(player)
			notify(player, {
				Kind = "Toast",
				Title = `BASE LEVEL {applied} • {string.upper(BaseConfig.Get(applied).Name)}`,
				Color = Color3.fromRGB(255, 205, 70),
			})
		end
	elseif words[1] == "!home" then
		BaseService.SendHome(player)
	end
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
	if GameConfig.STUDIO_DEBUG_COMMANDS and RunService:IsStudio() then
		player.Chatted:Connect(function(message)
			onDebugChat(player, message)
		end)
	end
	-- assign() téléporte le joueur si son personnage existe déjà ; sinon CharacterAdded s'en charge.
	assign(player)
end

function BaseService:Init()
	local existing = workspace:FindFirstChild("Bases")
	if existing then
		existing:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "Bases"
	folder.Parent = workspace

	for index = 1, GameConfig.MAX_BASES do
		local origin = computeOrigin(index)
		local accent = GameConfig.BASE_COLORS[index] or Color3.new(1, 1, 1)
		local model = BaseBuilder.Create(index, origin, accent, folder)
		table.insert(plots, {
			Index = index,
			Model = model,
			Origin = origin,
			Owner = nil,
		})
	end
end

function BaseService:Start()
	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(release)
	-- Joueurs déjà présents (cas du Play Solo dans Studio, où le joueur peut arriver avant ce script)
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end
end

return BaseService
