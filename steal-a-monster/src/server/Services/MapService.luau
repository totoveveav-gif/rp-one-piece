--!strict
-- MapService : génère toute la map par script au démarrage du serveur.
-- Rien à construire à la main dans Studio.
--
-- Workspace
-- ├── Map          (sol, trottoirs, arbres, lampadaires, limites, spawn de secours)
-- ├── MonsterArea  (Monster Road + portail + marqueurs RoadStart / RoadEnd)
-- ├── EventArea    (arène des événements live + marqueur ArenaCenter)
-- └── Bases        (créé par BaseService)

local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local PartFactory = require(ServerScriptService:WaitForChild("Server"):WaitForChild("Util"):WaitForChild("PartFactory"))

local Part = PartFactory.Part

-- Couleurs de la direction artistique (cartoon, saturé, lisible)
local COLORS = {
	Grass = Color3.fromRGB(110, 196, 88),
	Sidewalk = Color3.fromRGB(232, 222, 196),
	Road = Color3.fromRGB(68, 48, 108),
	RoadGlow = Color3.fromRGB(195, 120, 255),
	PortalStone = Color3.fromRGB(48, 38, 74),
	PortalGlow = Color3.fromRGB(160, 80, 255),
	Gold = Color3.fromRGB(255, 205, 70),
	LampMetal = Color3.fromRGB(40, 40, 52),
	LampLight = Color3.fromRGB(255, 214, 150),
	ArenaFloor = Color3.fromRGB(64, 62, 86),
	White = Color3.new(1, 1, 1),
}

export type Anchors = {
	RoadStart: BasePart,
	RoadEnd: BasePart,
	ArenaCenter: BasePart,
	FallbackSpawn: SpawnLocation,
}

local MapService = {}
MapService.Anchors = (nil :: any) :: Anchors

local HALF_ROAD = GameConfig.ROAD_WIDTH / 2
local HALF_LENGTH = GameConfig.ROAD_LENGTH / 2
local PORTAL_Z = -HALF_LENGTH - 15
local EXIT_Z = HALF_LENGTH + 15
local ARENA_Z = EXIT_Z + 70
local ARENA_RADIUS = 45

-- Taille du terrain
local GROUND_HALF_X = 220
local GROUND_MIN_Z = PORTAL_Z - 70
local GROUND_MAX_Z = ARENA_Z + ARENA_RADIUS + 35

local function marker(name: string, position: Vector3, parent: Instance): Part
	return Part({
		Name = name,
		Size = Vector3.new(2, 2, 2),
		CFrame = CFrame.new(position),
		Transparency = 1,
		CanCollide = false,
		CanQuery = false,
		Parent = parent,
	})
end

-- Supprime le Baseplate / SpawnLocation du template Studio par défaut.
local function cleanupTemplate()
	for _, name in { "Baseplate", "SpawnLocation", "Map", "MonsterArea", "EventArea" } do
		local existing = workspace:FindFirstChild(name)
		if existing then
			existing:Destroy()
		end
	end
end

local function setupLighting()
	Lighting.ClockTime = 14.5
	Lighting.Brightness = 2.2
	Lighting.Ambient = Color3.fromRGB(70, 70, 90)
	Lighting.OutdoorAmbient = Color3.fromRGB(140, 140, 160)
	Lighting.EnvironmentDiffuseScale = 0.5
	Lighting.EnvironmentSpecularScale = 0.5
	Lighting.GlobalShadows = true

	for _, child in Lighting:GetChildren() do
		if child:IsA("Atmosphere") or child:IsA("PostEffect") then
			child:Destroy()
		end
	end

	local atmosphere = Instance.new("Atmosphere")
	atmosphere.Density = 0.28
	atmosphere.Offset = 0.25
	atmosphere.Color = Color3.fromRGB(205, 190, 255)
	atmosphere.Decay = Color3.fromRGB(110, 115, 135)
	atmosphere.Glare = 0.2
	atmosphere.Haze = 1.2
	atmosphere.Parent = Lighting

	local bloom = Instance.new("BloomEffect")
	bloom.Intensity = 0.5
	bloom.Size = 24
	bloom.Threshold = 1.6
	bloom.Parent = Lighting

	local color = Instance.new("ColorCorrectionEffect")
	color.Saturation = 0.15
	color.Contrast = 0.05
	color.Parent = Lighting

	local sunRays = Instance.new("SunRaysEffect")
	sunRays.Intensity = 0.06
	sunRays.Parent = Lighting
end

local function buildGround(map: Folder)
	local sizeZ = GROUND_MAX_Z - GROUND_MIN_Z
	Part({
		Name = "Ground",
		Size = Vector3.new(GROUND_HALF_X * 2, 4, sizeZ),
		CFrame = CFrame.new(0, -2, (GROUND_MIN_Z + GROUND_MAX_Z) / 2),
		Material = Enum.Material.Grass,
		Color = COLORS.Grass,
		Parent = map,
	})

	-- Trottoirs entre la route et les bases : guident le joueur vers les entrées.
	local sidewalkWidth = GameConfig.ROAD_TO_BASE_GAP
	for _, side in { -1, 1 } do
		Part({
			Name = "Sidewalk",
			Size = Vector3.new(sidewalkWidth, 0.3, GameConfig.ROAD_LENGTH),
			CFrame = CFrame.new(side * (HALF_ROAD + sidewalkWidth / 2), 0.15, 0),
			Material = Enum.Material.Pavement,
			Color = COLORS.Sidewalk,
			Parent = map,
		})
	end
end

local function buildRoad(area: Folder)
	Part({
		Name = "MonsterRoad",
		Size = Vector3.new(GameConfig.ROAD_WIDTH, 0.5, GameConfig.ROAD_LENGTH),
		CFrame = CFrame.new(0, 0.25, 0),
		Color = COLORS.Road,
		Parent = area,
	})

	for _, side in { -1, 1 } do
		Part({
			Name = "RoadEdge",
			Size = Vector3.new(1, 0.6, GameConfig.ROAD_LENGTH),
			CFrame = CFrame.new(side * (HALF_ROAD - 0.5), 0.3, 0),
			Material = Enum.Material.Neon,
			Color = COLORS.RoadGlow,
			Parent = area,
		})
	end

	-- Chevrons lumineux : montrent le sens de marche des monstres (portail -> arène).
	local arrows = Instance.new("Folder")
	arrows.Name = "Arrows"
	arrows.Parent = area
	local count = 10
	local step = (GameConfig.ROAD_LENGTH - 50) / (count - 1)
	for i = 0, count - 1 do
		local z = -HALF_LENGTH + 25 + i * step
		for _, side in { -1, 1 } do
			Part({
				Name = "Chevron",
				Size = Vector3.new(0.8, 0.1, 8.5),
				CFrame = CFrame.new(side * 3, 0.55, z - 3) * CFrame.Angles(0, math.rad(-45 * side), 0),
				Material = Enum.Material.Neon,
				Color = COLORS.RoadGlow,
				Transparency = 0.35,
				CanCollide = false,
				Parent = arrows,
			})
		end
	end
end

-- Arche générique (portail d'entrée / sortie).
local function buildArch(
	parent: Folder,
	name: string,
	z: number,
	signText: string,
	signFace: Enum.NormalId,
	glowColor: Color3
): Model
	local arch = Instance.new("Model")
	arch.Name = name

	for _, side in { -1, 1 } do
		Part({
			Name = "Pillar",
			Size = Vector3.new(5, 32, 5),
			CFrame = CFrame.new(side * (HALF_ROAD + 3), 16, z),
			Material = Enum.Material.Slate,
			Color = COLORS.PortalStone,
			Parent = arch,
		})
		local cap = Part({
			Name = "PillarGem",
			Shape = Enum.PartType.Ball,
			Size = Vector3.new(4, 4, 4),
			CFrame = CFrame.new(side * (HALF_ROAD + 3), 39.5, z),
			Material = Enum.Material.Neon,
			Color = glowColor,
			CanCollide = false,
			Parent = arch,
		})
		PartFactory.Light(cap, glowColor, 20, 1.5)
	end

	local beam = Part({
		Name = "Sign",
		Size = Vector3.new(GameConfig.ROAD_WIDTH + 14, 6, 3),
		CFrame = CFrame.new(0, 34, z),
		Material = Enum.Material.Slate,
		Color = COLORS.PortalStone,
		Parent = arch,
	})
	PartFactory.SurfaceText(beam, signFace, signText, COLORS.Gold, Color3.fromRGB(40, 20, 60))

	arch.PrimaryPart = beam
	arch.Parent = parent
	return arch
end

local function buildPortal(area: Folder)
	-- Le portail fait face à la route (+Z) : le texte est donc sur la face "Back" (+Z).
	local portal = buildArch(area, "MonsterPortal", PORTAL_Z, "👾 MONSTER PORTAL", Enum.NormalId.Back, COLORS.PortalGlow)

	local swirl = Part({
		Name = "PortalSwirl",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(1, 28, 28),
		CFrame = CFrame.new(0, 16, PORTAL_Z) * CFrame.Angles(0, math.rad(90), 0),
		Material = Enum.Material.Neon,
		Color = COLORS.PortalGlow,
		Transparency = 0.25,
		CanCollide = false,
		CastShadow = false,
		Parent = portal,
	})
	PartFactory.Sparkles(swirl, Color3.fromRGB(220, 170, 255), 14)
	PartFactory.Light(swirl, COLORS.PortalGlow, 30, 2)

	-- Mur derrière le portail : le joueur ne peut pas passer "dans" le portail.
	Part({
		Name = "PortalBack",
		Size = Vector3.new(GameConfig.ROAD_WIDTH + 10, 32, 2),
		CFrame = CFrame.new(0, 16, PORTAL_Z - 2.5),
		Material = Enum.Material.Slate,
		Color = COLORS.PortalStone,
		Parent = portal,
	})
end

local function buildExitAndArena(monsterArea: Folder, eventArea: Folder)
	-- Arche de sortie : texte côté route (-Z = face "Front").
	buildArch(monsterArea, "MonsterExit", EXIT_Z, "⚡ EVENT ZONE ⚡", Enum.NormalId.Front, COLORS.Gold)

	-- Chemin vers l'arène
	Part({
		Name = "ArenaPath",
		Size = Vector3.new(GameConfig.ROAD_WIDTH, 0.4, ARENA_Z - EXIT_Z - ARENA_RADIUS + 4),
		CFrame = CFrame.new(0, 0.2, (EXIT_Z + ARENA_Z - ARENA_RADIUS) / 2),
		Material = Enum.Material.Pavement,
		Color = COLORS.Sidewalk,
		Parent = eventArea,
	})

	local vertical = CFrame.Angles(0, 0, math.rad(90)) -- l'axe d'un cylindre Roblox est X : on le met debout
	Part({
		Name = "ArenaRing",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.8, ARENA_RADIUS * 2 + 4, ARENA_RADIUS * 2 + 4),
		CFrame = CFrame.new(0, 0.4, ARENA_Z) * vertical,
		Material = Enum.Material.Neon,
		Color = COLORS.Gold,
		Parent = eventArea,
	})
	Part({
		Name = "ArenaFloor",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(1, ARENA_RADIUS * 2, ARENA_RADIUS * 2),
		CFrame = CFrame.new(0, 0.5, ARENA_Z) * vertical,
		Material = Enum.Material.Slate,
		Color = COLORS.ArenaFloor,
		Parent = eventArea,
	})
	local pedestal = Part({
		Name = "BossPedestal",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(3, 18, 18),
		CFrame = CFrame.new(0, 2.5, ARENA_Z) * vertical,
		Material = Enum.Material.Marble,
		Color = COLORS.White,
		Parent = eventArea,
	})
	Part({
		Name = "BossPedestalGlow",
		Shape = Enum.PartType.Cylinder,
		Size = Vector3.new(0.2, 19, 19),
		CFrame = CFrame.new(0, 3.95, ARENA_Z) * vertical,
		Material = Enum.Material.Neon,
		Color = COLORS.Gold,
		CanCollide = false,
		Parent = eventArea,
	})
	PartFactory.Light(pedestal, COLORS.Gold, 24, 1.2)

	return marker("ArenaCenter", Vector3.new(0, 4, ARENA_Z), eventArea)
end

local function buildLamps(map: Folder)
	local lamps = Instance.new("Folder")
	lamps.Name = "Lamps"
	lamps.Parent = map
	local count = 10
	local step = (GameConfig.ROAD_LENGTH - 40) / (count - 1)
	for i = 0, count - 1 do
		local z = -HALF_LENGTH + 20 + i * step
		for _, side in { -1, 1 } do
			local x = side * (HALF_ROAD + 2)
			Part({
				Name = "LampPole",
				Size = Vector3.new(0.8, 12, 0.8),
				CFrame = CFrame.new(x, 6, z),
				Material = Enum.Material.Metal,
				Color = COLORS.LampMetal,
				Parent = lamps,
			})
			local head = Part({
				Name = "LampHead",
				Size = Vector3.new(2.4, 1.4, 2.4),
				CFrame = CFrame.new(x, 12.6, z),
				Material = Enum.Material.Neon,
				Color = COLORS.LampLight,
				CanCollide = false,
				Parent = lamps,
			})
			PartFactory.Light(head, COLORS.LampLight, 18, 1.2)
		end
	end
end

local function buildTrees(map: Folder)
	local trees = Instance.new("Folder")
	trees.Name = "Trees"
	trees.Parent = map

	local rng = Random.new(7) -- graine fixe : la map est identique sur tous les serveurs
	local greens = {
		Color3.fromRGB(70, 170, 70),
		Color3.fromRGB(95, 190, 80),
		Color3.fromRGB(60, 150, 90),
		Color3.fromRGB(130, 200, 90),
	}
	local innerX = GameConfig.ROAD_WIDTH / 2 + GameConfig.ROAD_TO_BASE_GAP + GameConfig.BASE_DEPTH + 26

	local function tree(position: Vector3)
		local height = rng:NextNumber(8, 14)
		local crown = rng:NextNumber(11, 18)
		Part({
			Name = "Trunk",
			Shape = Enum.PartType.Cylinder,
			Size = Vector3.new(height, 2.4, 2.4),
			CFrame = CFrame.new(position + Vector3.new(0, height / 2, 0)) * CFrame.Angles(0, 0, math.rad(90)),
			Material = Enum.Material.Wood,
			Color = Color3.fromRGB(120, 82, 50),
			Parent = trees,
		})
		Part({
			Name = "Crown",
			Shape = Enum.PartType.Ball,
			Size = Vector3.new(crown, crown, crown),
			CFrame = CFrame.new(position + Vector3.new(0, height + crown * 0.3, 0)),
			Material = Enum.Material.Grass,
			Color = greens[rng:NextInteger(1, #greens)],
			Parent = trees,
		})
	end

	for _, side in { -1, 1 } do
		for _ = 1, 16 do
			local x = side * rng:NextNumber(innerX, GROUND_HALF_X - 12)
			local z = rng:NextNumber(GROUND_MIN_Z + 20, EXIT_Z)
			tree(Vector3.new(x, 0, z))
		end
	end
	-- Quelques arbres autour de l'arène
	for i = 1, 8 do
		local angle = (i / 8) * math.pi * 2 + rng:NextNumber(-0.2, 0.2)
		local radius = ARENA_RADIUS + rng:NextNumber(14, 26)
		local position = Vector3.new(math.cos(angle) * radius, 0, ARENA_Z + math.sin(angle) * radius)
		-- On évite le chemin d'accès à l'arène
		if math.abs(position.X) > GameConfig.ROAD_WIDTH then
			tree(position)
		end
	end
end

local function buildBoundaries(map: Folder)
	local folder = Instance.new("Folder")
	folder.Name = "Boundaries"
	folder.Parent = map
	local height = 120
	local sizeZ = GROUND_MAX_Z - GROUND_MIN_Z
	local centerZ = (GROUND_MIN_Z + GROUND_MAX_Z) / 2
	local walls = {
		{ Vector3.new(4, height, sizeZ), Vector3.new(GROUND_HALF_X + 2, height / 2, centerZ) },
		{ Vector3.new(4, height, sizeZ), Vector3.new(-GROUND_HALF_X - 2, height / 2, centerZ) },
		{ Vector3.new(GROUND_HALF_X * 2, height, 4), Vector3.new(0, height / 2, GROUND_MIN_Z - 2) },
		{ Vector3.new(GROUND_HALF_X * 2, height, 4), Vector3.new(0, height / 2, GROUND_MAX_Z + 2) },
	}
	for _, wall in walls do
		Part({
			Name = "InvisibleWall",
			Size = wall[1],
			CFrame = CFrame.new(wall[2]),
			Transparency = 1,
			CanQuery = false,
			Parent = folder,
		})
	end
end

local function buildFallbackSpawn(map: Folder): SpawnLocation
	-- Utilisé seulement une fraction de seconde : BaseService téléporte ensuite le joueur dans sa base.
	local spawn = Instance.new("SpawnLocation")
	spawn.Name = "FallbackSpawn"
	spawn.Anchored = true
	spawn.Size = Vector3.new(12, 1, 12)
	spawn.CFrame = CFrame.new(0, 0.5, PORTAL_Z + 25)
	spawn.Transparency = 1
	spawn.CanCollide = false
	spawn.CanQuery = false
	spawn.Neutral = true
	spawn.Duration = 0 -- pas de ForceField
	spawn.Parent = map
	local decal = spawn:FindFirstChildOfClass("Decal")
	if decal then
		decal:Destroy()
	end
	return spawn
end

function MapService:Init()
	cleanupTemplate()
	setupLighting()

	local map = Instance.new("Folder")
	map.Name = "Map"
	local monsterArea = Instance.new("Folder")
	monsterArea.Name = "MonsterArea"
	local eventArea = Instance.new("Folder")
	eventArea.Name = "EventArea"

	buildGround(map)
	buildRoad(monsterArea)
	buildPortal(monsterArea)
	local arenaCenter = buildExitAndArena(monsterArea, eventArea)
	buildLamps(map)
	buildTrees(map)
	buildBoundaries(map)
	local fallbackSpawn = buildFallbackSpawn(map)

	-- Marqueurs utilisés par les phases suivantes (marche des monstres, événements)
	local roadStart = marker("RoadStart", Vector3.new(0, 1, -HALF_LENGTH + 4), monsterArea)
	local roadEnd = marker("RoadEnd", Vector3.new(0, 1, HALF_LENGTH - 4), monsterArea)

	map.Parent = workspace
	monsterArea.Parent = workspace
	eventArea.Parent = workspace

	MapService.Anchors = {
		RoadStart = roadStart,
		RoadEnd = roadEnd,
		ArenaCenter = arenaCenter,
		FallbackSpawn = fallbackSpawn,
	}
end

return MapService
