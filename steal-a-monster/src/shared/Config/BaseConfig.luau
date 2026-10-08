--!strict
-- BaseConfig : les 7 niveaux de base.
-- Chaque niveau change visuellement la base ET débloque des emplacements de monstres.
-- (Le coût d'amélioration sera utilisé en Phase 5 ; il est déjà défini ici pour garder
-- une seule source de vérité.)

export type BaseLevel = {
	Name: string,
	Slots: number, -- nombre d'emplacements de monstres débloqués
	UpgradeCost: number, -- coût pour passer AU niveau suivant (0 = niveau max)

	FloorMaterial: Enum.Material,
	FloorColor: Color3,
	WallMaterial: Enum.Material,
	WallColor: Color3,
	-- Hauteur au-dessus du sol de la base. Saut par défaut = 7.2 et un socle ajoute 1 stud :
	-- il faut >= 8.5 pour qu'un mur ne soit PAS sautable (seul le niveau 1 l'est, exprès).
	WallHeight: number,
	TrimMaterial: Enum.Material,
	TrimColor: Color3,

	-- Décorations activées
	Torches: boolean,
	Pillars: boolean,
	Lamps: boolean,
	Banners: boolean,
	WallTrim: boolean,
	Crystals: boolean,
	Statue: boolean,
	Aura: boolean,
}

local BaseConfig = {}

BaseConfig.MAX_SLOTS = 30 -- = 6 colonnes x 5 rangées

BaseConfig.Levels = {
	{
		Name = "Starter Camp",
		Slots = 6,
		UpgradeCost = 1_500,
		FloorMaterial = Enum.Material.WoodPlanks,
		FloorColor = Color3.fromRGB(176, 128, 84),
		WallMaterial = Enum.Material.WoodPlanks,
		WallColor = Color3.fromRGB(124, 88, 58),
		WallHeight = 4,
		TrimMaterial = Enum.Material.Wood,
		TrimColor = Color3.fromRGB(95, 66, 42),
		Torches = true,
		Pillars = false,
		Lamps = false,
		Banners = false,
		WallTrim = false,
		Crystals = false,
		Statue = false,
		Aura = false,
	},
	{
		Name = "Stone Outpost",
		Slots = 8,
		UpgradeCost = 12_000,
		FloorMaterial = Enum.Material.Slate,
		FloorColor = Color3.fromRGB(120, 125, 135),
		WallMaterial = Enum.Material.Cobblestone,
		WallColor = Color3.fromRGB(150, 150, 160),
		WallHeight = 9.5,
		TrimMaterial = Enum.Material.Slate,
		TrimColor = Color3.fromRGB(95, 98, 108),
		Torches = true,
		Pillars = true,
		Lamps = false,
		Banners = false,
		WallTrim = false,
		Crystals = false,
		Statue = false,
		Aura = false,
	},
	{
		Name = "Iron Fortress",
		Slots = 12,
		UpgradeCost = 90_000,
		FloorMaterial = Enum.Material.Pavement,
		FloorColor = Color3.fromRGB(155, 145, 135),
		WallMaterial = Enum.Material.Brick,
		WallColor = Color3.fromRGB(170, 95, 72),
		WallHeight = 10,
		TrimMaterial = Enum.Material.DiamondPlate,
		TrimColor = Color3.fromRGB(110, 115, 125),
		Torches = false,
		Pillars = true,
		Lamps = true,
		Banners = false,
		WallTrim = true,
		Crystals = false,
		Statue = false,
		Aura = false,
	},
	{
		Name = "Royal Keep",
		Slots = 16,
		UpgradeCost = 600_000,
		FloorMaterial = Enum.Material.Marble,
		FloorColor = Color3.fromRGB(230, 228, 235),
		WallMaterial = Enum.Material.Sandstone,
		WallColor = Color3.fromRGB(232, 212, 172),
		WallHeight = 11,
		TrimMaterial = Enum.Material.Metal,
		TrimColor = Color3.fromRGB(240, 190, 60),
		Torches = false,
		Pillars = true,
		Lamps = true,
		Banners = true,
		WallTrim = true,
		Crystals = false,
		Statue = false,
		Aura = false,
	},
	{
		Name = "Crystal Citadel",
		Slots = 20,
		UpgradeCost = 4_000_000,
		FloorMaterial = Enum.Material.Marble,
		FloorColor = Color3.fromRGB(205, 225, 255),
		WallMaterial = Enum.Material.Glacier,
		WallColor = Color3.fromRGB(175, 215, 255),
		WallHeight = 12,
		TrimMaterial = Enum.Material.Neon,
		TrimColor = Color3.fromRGB(120, 200, 255),
		Torches = false,
		Pillars = true,
		Lamps = true,
		Banners = true,
		WallTrim = true,
		Crystals = true,
		Statue = false,
		Aura = false,
	},
	{
		Name = "Monster Palace",
		Slots = 24,
		UpgradeCost = 30_000_000,
		FloorMaterial = Enum.Material.Marble,
		FloorColor = Color3.fromRGB(250, 242, 225),
		WallMaterial = Enum.Material.Marble,
		WallColor = Color3.fromRGB(245, 236, 218),
		WallHeight = 13,
		TrimMaterial = Enum.Material.Foil,
		TrimColor = Color3.fromRGB(255, 200, 60),
		Torches = false,
		Pillars = true,
		Lamps = true,
		Banners = true,
		WallTrim = true,
		Crystals = true,
		Statue = true,
		Aura = false,
	},
	{
		Name = "Cosmic Throne",
		Slots = 30,
		UpgradeCost = 0,
		FloorMaterial = Enum.Material.SmoothPlastic,
		FloorColor = Color3.fromRGB(32, 22, 58),
		WallMaterial = Enum.Material.ForceField,
		WallColor = Color3.fromRGB(160, 95, 255),
		WallHeight = 14,
		TrimMaterial = Enum.Material.Neon,
		TrimColor = Color3.fromRGB(255, 220, 90),
		Torches = false,
		Pillars = true,
		Lamps = true,
		Banners = true,
		WallTrim = true,
		Crystals = true,
		Statue = true,
		Aura = true,
	},
} :: { BaseLevel }

BaseConfig.MAX_LEVEL = #BaseConfig.Levels

-- Ramène n'importe quel nombre dans 1..MAX_LEVEL (NaN -> 1 : NaN ~= NaN en Luau).
function BaseConfig.Clamp(level: number): number
	if level ~= level then
		return 1
	end
	return math.clamp(math.floor(level), 1, BaseConfig.MAX_LEVEL)
end

function BaseConfig.Get(level: number): BaseLevel
	return BaseConfig.Levels[BaseConfig.Clamp(level)]
end

return BaseConfig
