--!strict
-- BaseBuilder : construit la géométrie d'une base et ses 7 niveaux visuels.
-- Ne contient AUCUNE logique de jeu (propriétaire, argent...) : c'est le rôle de BaseService.
--
-- Contenu d'un modèle "Base_N" :
--   Floor        sol (PrimaryPart)
--   Trim         bordure néon à la couleur de la base
--   Slots        30 socles "Slot_1".."Slot_30" (attribut Unlocked) + Attachment "MonsterAnchor"
--   Arch         arche d'entrée + panneau "Sign" (nom du propriétaire)
--   Gate         barrière laser invisible (activée par le système LOCK BASE en Phase 4)
--   SpawnPoint   point d'apparition du propriétaire
--   Deco         décor reconstruit à chaque changement de niveau
--
-- Repère local : origine au sol au centre de la base, -Z = côté route (entrée), +Z = fond.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local BaseConfig = require(Shared:WaitForChild("Config"):WaitForChild("BaseConfig"))
local PartFactory = require(ServerScriptService:WaitForChild("Server"):WaitForChild("Util"):WaitForChild("PartFactory"))

local Part = PartFactory.Part

local W = GameConfig.BASE_WIDTH
local D = GameConfig.BASE_DEPTH
local FT = GameConfig.BASE_FLOOR_HEIGHT -- hauteur du dessus du sol
local ENTRANCE = GameConfig.BASE_ENTRANCE_WIDTH
local WALL_T = 1.5
local ARCH_HEIGHT = 18

-- Grille des socles : 6 colonnes x 5 rangées, remplie du fond vers l'entrée
-- (les premiers monstres sont les plus éloignés de la route = plus durs à voler).
local SLOT_COLUMNS = { -30, -18, -6, 6, 18, 30 }
local SLOT_ROWS = { 22, 12, 2, -8, -18 }
local SLOT_DIAMETER = 7.5
local SLOT_HEIGHT = 1

local LOCKED_SLOT_COLOR = Color3.fromRGB(60, 60, 70)

type PartSpec = { Size: Vector3, Offset: CFrame }

local BaseBuilder = {}

local function getOrigin(model: Model): CFrame
	local floor = model:FindFirstChild("Floor") :: BasePart
	return floor.CFrame * CFrame.new(0, -FT / 2, 0)
end

local function accentOf(model: Model): Color3
	local value = model:GetAttribute("AccentColor")
	return if typeof(value) == "Color3" then value else Color3.new(1, 1, 1)
end

-------------------------------------------------------------------------------
-- Construction initiale (une seule fois par base, au démarrage du serveur)
-------------------------------------------------------------------------------

local function buildSlots(model: Model, origin: CFrame)
	local folder = Instance.new("Folder")
	folder.Name = "Slots"
	folder.Parent = model

	local index = 0
	for _, z in SLOT_ROWS do
		for _, x in SLOT_COLUMNS do
			index += 1
			local slot = Part({
				Name = "Slot_" .. index,
				Shape = Enum.PartType.Cylinder,
				Size = Vector3.new(SLOT_HEIGHT, SLOT_DIAMETER, SLOT_DIAMETER),
				CFrame = origin * CFrame.new(x, FT + SLOT_HEIGHT / 2, z) * CFrame.Angles(0, 0, math.rad(90)),
				Material = Enum.Material.SmoothPlastic,
				Parent = folder,
			})
			slot:SetAttribute("SlotIndex", index)
			slot:SetAttribute("Unlocked", false)

			-- Point d'ancrage du monstre (dessus du socle), orienté vers la route :
			-- les monstres "regardent" les visiteurs. Un Attachment stocke une position RELATIVE
			-- à sa pièce : on convertit donc la position monde voulue dans le repère du socle.
			local anchor = Instance.new("Attachment")
			anchor.Name = "MonsterAnchor"
			anchor.CFrame = slot.CFrame:ToObjectSpace(origin * CFrame.new(x, FT + SLOT_HEIGHT, z))
			anchor.Parent = slot
		end
	end
end

local function buildArch(model: Model, origin: CFrame, accent: Color3)
	local arch = Instance.new("Model")
	arch.Name = "Arch"

	local stone = Color3.fromRGB(58, 50, 78)
	for _, side in { -1, 1 } do
		Part({
			Name = "Pillar",
			Size = Vector3.new(3, ARCH_HEIGHT, 3),
			CFrame = origin * CFrame.new(side * (ENTRANCE / 2 + 1.4), FT + ARCH_HEIGHT / 2, -D / 2 + WALL_T / 2),
			Material = Enum.Material.Slate,
			Color = stone,
			Parent = arch,
		})
	end

	local sign = Part({
		Name = "Sign",
		Size = Vector3.new(ENTRANCE + 8, 5, 2),
		CFrame = origin * CFrame.new(0, FT + ARCH_HEIGHT + 1.5, -D / 2 + WALL_T / 2),
		Material = Enum.Material.Slate,
		Color = stone,
		Parent = arch,
	})
	-- La face "Front" (-Z local) regarde la route.
	PartFactory.SurfaceText(sign, Enum.NormalId.Front, "EMPTY BASE", Color3.new(1, 1, 1))

	Part({
		Name = "SignGlow",
		Size = Vector3.new(ENTRANCE + 8, 0.5, 2.2),
		CFrame = origin * CFrame.new(0, FT + ARCH_HEIGHT - 1.25, -D / 2 + WALL_T / 2),
		Material = Enum.Material.Neon,
		Color = accent,
		CanCollide = false,
		Parent = arch,
	})

	-- Plaque visible de loin : avatar + nom du propriétaire (lisible sur une vidéo TikTok).
	local billboard = Instance.new("BillboardGui")
	billboard.Name = "OwnerBillboard"
	-- Taille en studs (Scale) : la carte rétrécit avec la distance et n'encombre pas l'écran mobile.
	billboard.Size = UDim2.fromScale(15, 4)
	billboard.StudsOffsetWorldSpace = Vector3.new(0, 7, 0)
	billboard.MaxDistance = 250
	billboard.LightInfluence = 0
	billboard.Enabled = false

	local frame = Instance.new("Frame")
	frame.Name = "Card"
	frame.Size = UDim2.fromScale(1, 1)
	frame.BackgroundColor3 = Color3.fromRGB(25, 22, 40)
	frame.BackgroundTransparency = 0.15
	frame.Parent = billboard
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0.25, 0)
	corner.Parent = frame
	local stroke = Instance.new("UIStroke")
	stroke.Name = "Stroke"
	stroke.Color = accent
	stroke.Thickness = 3
	stroke.Parent = frame

	local avatar = Instance.new("ImageLabel")
	avatar.Name = "Avatar"
	avatar.BackgroundTransparency = 1
	avatar.Size = UDim2.fromScale(0.217, 0.8125)
	avatar.Position = UDim2.fromScale(0.025, 0.094)
	avatar.Parent = frame
	local avatarCorner = Instance.new("UICorner")
	avatarCorner.CornerRadius = UDim.new(1, 0)
	avatarCorner.Parent = avatar

	local nameLabel = Instance.new("TextLabel")
	nameLabel.Name = "OwnerName"
	nameLabel.BackgroundTransparency = 1
	nameLabel.Position = UDim2.fromScale(0.267, 0.094)
	nameLabel.Size = UDim2.fromScale(0.708, 0.47)
	nameLabel.Font = GameConfig.FONT
	nameLabel.TextScaled = true
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.TextColor3 = Color3.new(1, 1, 1)
	nameLabel.Text = ""
	nameLabel.Parent = frame

	local levelLabel = Instance.new("TextLabel")
	levelLabel.Name = "Level"
	levelLabel.BackgroundTransparency = 1
	levelLabel.Position = UDim2.fromScale(0.267, 0.5625)
	levelLabel.Size = UDim2.fromScale(0.708, 0.3125)
	levelLabel.Font = GameConfig.FONT
	levelLabel.TextScaled = true
	levelLabel.TextXAlignment = Enum.TextXAlignment.Left
	levelLabel.TextColor3 = accent
	levelLabel.Text = ""
	levelLabel.Parent = frame

	billboard.Parent = sign

	arch.PrimaryPart = sign
	arch.Parent = model
end

function BaseBuilder.Create(index: number, origin: CFrame, accent: Color3, parent: Instance): Model
	local model = Instance.new("Model")
	model.Name = "Base_" .. index
	model:SetAttribute("BaseIndex", index)
	model:SetAttribute("AccentColor", accent)
	model:SetAttribute("OwnerUserId", 0)
	model:SetAttribute("OwnerName", "")
	model:SetAttribute("Level", 1)

	local floor = Part({
		Name = "Floor",
		Size = Vector3.new(W, FT, D),
		CFrame = origin * CFrame.new(0, FT / 2, 0),
		Parent = model,
	})
	model.PrimaryPart = floor

	-- Bordure néon à la couleur de la base (identification immédiate)
	local trim = Instance.new("Folder")
	trim.Name = "Trim"
	trim.Parent = model
	local trimSpecs: { PartSpec } = {
		-- Collées contre la face intérieure des murs (visibles, pas de scintillement)
		{ Size = Vector3.new(W - 2 * WALL_T, 0.3, 1), Offset = CFrame.new(0, FT + 0.15, D / 2 - WALL_T - 0.5) },
		{ Size = Vector3.new(1, 0.3, D - 2 * WALL_T), Offset = CFrame.new(-(W / 2 - WALL_T - 0.5), FT + 0.15, 0) },
		{ Size = Vector3.new(1, 0.3, D - 2 * WALL_T), Offset = CFrame.new(W / 2 - WALL_T - 0.5, FT + 0.15, 0) },
		{ Size = Vector3.new(ENTRANCE, 0.3, 2), Offset = CFrame.new(0, FT + 0.15, -D / 2 + 1) },
	}
	for _, spec in trimSpecs do
		Part({
			Name = "TrimStrip",
			Size = spec.Size,
			CFrame = origin * spec.Offset,
			Material = Enum.Material.Neon,
			Color = accent,
			CanCollide = false,
			Parent = trim,
		})
	end

	buildSlots(model, origin)
	buildArch(model, origin, accent)

	local gate = Part({
		Name = "Gate",
		Size = Vector3.new(ENTRANCE, 12, 0.6),
		CFrame = origin * CFrame.new(0, FT + 6, -D / 2 + WALL_T / 2),
		Material = Enum.Material.Neon,
		Color = Color3.fromRGB(255, 60, 60),
		Transparency = 1,
		CanCollide = false,
		CanQuery = false,
		Parent = model,
	})
	gate:SetAttribute("Active", false)

	-- Le joueur apparaît près de l'entrée en regardant ses monstres.
	Part({
		Name = "SpawnPoint",
		Size = Vector3.new(4, 1, 4),
		CFrame = origin * CFrame.new(0, FT + 0.5, -D / 2 + 8),
		Transparency = 1,
		CanCollide = false,
		CanQuery = false,
		Parent = model,
	})

	local deco = Instance.new("Folder")
	deco.Name = "Deco"
	deco.Parent = model

	model.Parent = parent
	BaseBuilder.ApplyLevel(model, 1)
	return model
end

-------------------------------------------------------------------------------
-- Décor par niveau
-------------------------------------------------------------------------------

local function buildWalls(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel)
	local h = level.WallHeight
	local y = FT + h / 2
	local side = (W - ENTRANCE) / 2
	local specs: { PartSpec } = {
		{ Size = Vector3.new(W, h, WALL_T), Offset = CFrame.new(0, y, D / 2 - WALL_T / 2) }, -- fond
		{ Size = Vector3.new(WALL_T, h, D), Offset = CFrame.new(-W / 2 + WALL_T / 2, y, 0) }, -- gauche
		{ Size = Vector3.new(WALL_T, h, D), Offset = CFrame.new(W / 2 - WALL_T / 2, y, 0) }, -- droite
		{ Size = Vector3.new(side, h, WALL_T), Offset = CFrame.new(-(ENTRANCE / 2 + side / 2), y, -D / 2 + WALL_T / 2) }, -- avant gauche
		{ Size = Vector3.new(side, h, WALL_T), Offset = CFrame.new(ENTRANCE / 2 + side / 2, y, -D / 2 + WALL_T / 2) }, -- avant droite
	}
	for _, spec in specs do
		Part({
			Name = "Wall",
			Size = spec.Size,
			CFrame = origin * spec.Offset,
			Material = level.WallMaterial,
			Color = level.WallColor,
			Parent = deco,
		})
		if level.WallTrim then
			Part({
				Name = "WallTrim",
				Size = spec.Size * Vector3.new(1, 0, 1) + Vector3.new(0.6, 0.8, 0.6),
				CFrame = origin * spec.Offset * CFrame.new(0, h / 2 + 0.4, 0),
				Material = level.TrimMaterial,
				Color = level.TrimColor,
				Parent = deco,
			})
		end
	end
end

local CORNERS = {
	Vector2.new(-W / 2, -D / 2),
	Vector2.new(W / 2, -D / 2),
	Vector2.new(-W / 2, D / 2),
	Vector2.new(W / 2, D / 2),
}

local function buildPillars(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel)
	-- Centrés sur les coins du sol : ils partent du sol du terrain (y = 0) pour ne pas flotter.
	local top = FT + level.WallHeight + 3
	for _, corner in CORNERS do
		Part({
			Name = "Pillar",
			Size = Vector3.new(3.5, top, 3.5),
			CFrame = origin * CFrame.new(corner.X, top / 2, corner.Y),
			Material = level.TrimMaterial == Enum.Material.Neon and Enum.Material.Marble or level.TrimMaterial,
			Color = level.TrimColor,
			Parent = deco,
		})
	end
end

local function buildTorches(deco: Folder, origin: CFrame)
	for _, side in { -1, 1 } do
		local x = side * (ENTRANCE / 2 + 4)
		Part({
			Name = "TorchStick",
			Size = Vector3.new(0.6, FT + 6, 0.6),
			CFrame = origin * CFrame.new(x, (FT + 6) / 2, -D / 2 - 1), -- planté dans le trottoir
			Material = Enum.Material.Wood,
			Color = Color3.fromRGB(100, 70, 45),
			CanCollide = false, -- sinon il sert d'échelle pour passer le mur
			Parent = deco,
		})
		local flame = Part({
			Name = "TorchFlame",
			Size = Vector3.new(1.1, 1.4, 1.1),
			CFrame = origin * CFrame.new(x, FT + 6.6, -D / 2 - 1),
			Material = Enum.Material.Neon,
			Color = Color3.fromRGB(255, 150, 50),
			CanCollide = false,
			Parent = deco,
		})
		PartFactory.Light(flame, Color3.fromRGB(255, 160, 80), 14, 1.5)
	end
end

local function buildLamps(deco: Folder, origin: CFrame, accent: Color3)
	for _, corner in CORNERS do
		-- Légèrement à l'intérieur des coins
		local x = corner.X * 0.9
		local z = corner.Y * 0.85
		Part({
			Name = "LampPole",
			Size = Vector3.new(0.7, 8, 0.7),
			CFrame = origin * CFrame.new(x, FT + 4, z),
			Material = Enum.Material.Metal,
			Color = Color3.fromRGB(45, 45, 55),
			CanCollide = false, -- pas d'échelle pour s'échapper par-dessus le mur
			Parent = deco,
		})
		local bulb = Part({
			Name = "LampBulb",
			Shape = Enum.PartType.Ball,
			Size = Vector3.new(2, 2, 2),
			CFrame = origin * CFrame.new(x, FT + 8.6, z),
			Material = Enum.Material.Neon,
			Color = accent,
			CanCollide = false,
			Parent = deco,
		})
		PartFactory.Light(bulb, accent, 16, 1)
	end
end

local function buildBanners(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel, accent: Color3)
	for _, x in { -24, 0, 24 } do
		local height = math.min(level.WallHeight - 1, 10)
		Part({
			Name = "Banner",
			Size = Vector3.new(6, height, 0.3),
			CFrame = origin * CFrame.new(x, FT + level.WallHeight - height / 2 - 0.5, D / 2 - WALL_T - 0.2),
			Material = Enum.Material.Fabric,
			Color = accent,
			CanCollide = false,
			Parent = deco,
		})
		Part({
			Name = "BannerRod",
			Size = Vector3.new(7, 0.4, 0.4),
			CFrame = origin * CFrame.new(x, FT + level.WallHeight - 0.3, D / 2 - WALL_T - 0.2),
			Material = level.TrimMaterial,
			Color = level.TrimColor,
			Parent = deco,
		})
	end
end

local function buildCrystals(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel, accent: Color3)
	for _, corner in CORNERS do
		local h = level.WallHeight + 8
		local crystal = Part({
			Name = "Crystal",
			Size = Vector3.new(3, h, 3),
			CFrame = origin
				* CFrame.new(corner.X, FT + level.WallHeight + 3 + h / 2, corner.Y)
				* CFrame.Angles(0, math.rad(45), math.rad(8)),
			Material = Enum.Material.Neon,
			Color = accent,
			Transparency = 0.15,
			CanCollide = false,
			CastShadow = false,
			Parent = deco,
		})
		PartFactory.Sparkles(crystal, accent, 2)
	end
end

-- Statue géante d'un monstre derrière la base : posée sur un socle haut pour dépasser des murs
-- et être visible de toute la map. Seul le socle (trop haut pour être sauté) est solide :
-- le reste ne doit pas servir d'escalier pour entrer par-dessus le mur du fond.
local function buildStatue(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel, accent: Color3)
	local lift = level.WallHeight - 2
	local base = origin * CFrame.new(0, lift, D / 2 + 7)
	local gold = level.TrimColor
	local material = level.TrimMaterial == Enum.Material.Neon and Enum.Material.Foil or level.TrimMaterial
	Part({
		Name = "StatuePedestal",
		Size = Vector3.new(12, lift + 4, 10),
		CFrame = origin * CFrame.new(0, (lift + 4) / 2, D / 2 + 7),
		Material = Enum.Material.Marble,
		Color = Color3.fromRGB(240, 236, 228),
		Parent = deco,
	})
	Part({
		Name = "StatueBody",
		Shape = Enum.PartType.Ball,
		Size = Vector3.new(11, 11, 11),
		CFrame = base * CFrame.new(0, 9.5, 0),
		Material = material,
		Color = gold,
		CanCollide = false,
		Parent = deco,
	})
	Part({
		Name = "StatueHead",
		Shape = Enum.PartType.Ball,
		Size = Vector3.new(8, 8, 8),
		CFrame = base * CFrame.new(0, 17, -1),
		Material = material,
		Color = gold,
		CanCollide = false,
		Parent = deco,
	})
	for _, side in { -1, 1 } do
		PartFactory.Wedge({
			Name = "StatueHorn",
			Size = Vector3.new(1.2, 4, 2),
			CFrame = base * CFrame.new(side * 2.6, 22, -1) * CFrame.Angles(0, math.rad(180), math.rad(-15 * side)),
			Material = material,
			Color = gold,
			CanCollide = false,
			Parent = deco,
		})
		Part({
			Name = "StatueEye",
			Shape = Enum.PartType.Ball,
			Size = Vector3.new(1.6, 1.6, 1.6),
			CFrame = base * CFrame.new(side * 1.7, 17.8, -4.6),
			Material = Enum.Material.Neon,
			Color = accent,
			CanCollide = false,
			Parent = deco,
		})
	end
end

-- Anneau cosmique flottant au-dessus de la base (niveau 7), fait de segments néon.
local function buildAura(deco: Folder, origin: CFrame, level: BaseConfig.BaseLevel, accent: Color3)
	local radius = W / 2 + 4
	local segments = 32
	local y = FT + level.WallHeight + 10
	local length = 2 * math.pi * radius / segments + 0.3 -- léger chevauchement : pas de trous
	for i = 1, segments do
		local angle = (i / segments) * 2 * math.pi
		local position = Vector3.new(math.cos(angle) * radius, y, math.sin(angle) * radius)
		local tangent = Vector3.new(-math.sin(angle), 0, math.cos(angle))
		local segment = Part({
			Name = "AuraRing",
			Size = Vector3.new(0.8, 0.8, length),
			CFrame = origin * CFrame.lookAt(position, position + tangent),
			Material = Enum.Material.Neon,
			Color = accent,
			Transparency = 0.25,
			CanCollide = false,
			CanQuery = false,
			CastShadow = false,
			Parent = deco,
		})
		if i % 8 == 0 then
			PartFactory.Sparkles(segment, level.TrimColor, 2)
		end
	end
end

-- Applique (ou ré-applique) le visuel d'un niveau. Appelé par BaseService.
function BaseBuilder.ApplyLevel(model: Model, levelNumber: number)
	local clamped = BaseConfig.Clamp(levelNumber)
	local level = BaseConfig.Get(clamped)
	local origin = getOrigin(model)
	local accent = accentOf(model)

	local floor = model:FindFirstChild("Floor") :: BasePart
	floor.Material = level.FloorMaterial
	floor.Color = level.FloorColor

	local deco = model:FindFirstChild("Deco") :: Folder
	deco:ClearAllChildren()

	buildWalls(deco, origin, level)
	if level.Pillars then
		buildPillars(deco, origin, level)
	end
	if level.Torches then
		buildTorches(deco, origin)
	end
	if level.Lamps then
		buildLamps(deco, origin, accent)
	end
	if level.Banners then
		buildBanners(deco, origin, level, accent)
	end
	if level.Crystals then
		buildCrystals(deco, origin, level, accent)
	end
	if level.Statue then
		buildStatue(deco, origin, level, accent)
	end
	if level.Aura then
		buildAura(deco, origin, level, accent)
	end

	-- Socles : débloqués = couleur de la base, verrouillés = sombres et translucides.
	local slots = model:FindFirstChild("Slots") :: Folder
	for _, slot in slots:GetChildren() do
		if slot:IsA("BasePart") then
			local index = slot:GetAttribute("SlotIndex") :: number
			local unlocked = index <= level.Slots
			slot:SetAttribute("Unlocked", unlocked)
			slot.Color = if unlocked then accent else LOCKED_SLOT_COLOR
			slot.Material = if unlocked then Enum.Material.Neon else Enum.Material.SmoothPlastic
			slot.Transparency = if unlocked then 0.1 else 0.7
		end
	end

	model:SetAttribute("Level", clamped)
	BaseBuilder.RefreshSign(model)
end

-- Met à jour panneau + plaque au-dessus de l'entrée.
function BaseBuilder.RefreshSign(model: Model)
	local arch = model:FindFirstChild("Arch") :: Model
	local sign = arch:FindFirstChild("Sign") :: BasePart
	local surfaceLabel = (sign:FindFirstChild("Text_Front") :: SurfaceGui):FindFirstChild("Label") :: TextLabel
	local billboard = sign:FindFirstChild("OwnerBillboard") :: BillboardGui
	local card = billboard:FindFirstChild("Card") :: Frame

	local ownerId = model:GetAttribute("OwnerUserId") :: number
	local ownerName = model:GetAttribute("OwnerName") :: string
	local levelNumber = model:GetAttribute("Level") :: number
	local level = BaseConfig.Get(levelNumber)
	local accent = accentOf(model)

	if ownerId ~= 0 then
		surfaceLabel.Text = string.upper(ownerName) .. "'S BASE"
		surfaceLabel.TextColor3 = accent
		billboard.Enabled = true
		local avatar = card:FindFirstChild("Avatar") :: ImageLabel
		local nameLabel = card:FindFirstChild("OwnerName") :: TextLabel
		local levelLabel = card:FindFirstChild("Level") :: TextLabel
		avatar.Image = `rbxthumb://type=AvatarHeadShot&id={ownerId}&w=150&h=150`
		nameLabel.Text = ownerName
		levelLabel.Text = `LVL {levelNumber} • {string.upper(level.Name)}`
	else
		surfaceLabel.Text = "EMPTY BASE"
		surfaceLabel.TextColor3 = Color3.new(1, 1, 1)
		billboard.Enabled = false
	end
end

return BaseBuilder
