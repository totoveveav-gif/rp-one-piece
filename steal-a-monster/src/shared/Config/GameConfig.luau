--!strict
-- GameConfig : réglages globaux du jeu (lus par le serveur ET le client).
-- Aucune donnée sensible ici : le client peut lire ce module.

local GameConfig = {}

GameConfig.GAME_NAME = "STEAL A MONSTER"

-- Mets la même valeur dans Game Settings > Places > Max Players.
GameConfig.MAX_BASES = 8
GameConfig.BASES_PER_SIDE = 4

-- Layout de la map (en studs). La "Monster Road" suit l'axe Z au centre (X = 0).
GameConfig.ROAD_WIDTH = 28
GameConfig.ROAD_LENGTH = 470
GameConfig.ROAD_TO_BASE_GAP = 18
GameConfig.BASE_SPACING = 88 -- distance entre deux bases du même côté

-- Dimensions d'une base (repère local : -Z = côté route / entrée).
GameConfig.BASE_WIDTH = 76 -- largeur (parallèle à la route)
GameConfig.BASE_DEPTH = 60 -- profondeur (perpendiculaire à la route)
GameConfig.BASE_FLOOR_HEIGHT = 1.2
GameConfig.BASE_ENTRANCE_WIDTH = 18

-- Couleur d'identité de chaque base (index 1..MAX_BASES).
GameConfig.BASE_COLORS = {
	Color3.fromRGB(255, 85, 85), -- rouge
	Color3.fromRGB(80, 160, 255), -- bleu
	Color3.fromRGB(90, 220, 120), -- vert
	Color3.fromRGB(255, 200, 60), -- or
	Color3.fromRGB(190, 110, 255), -- violet
	Color3.fromRGB(255, 140, 200), -- rose
	Color3.fromRGB(70, 225, 225), -- cyan
	Color3.fromRGB(255, 150, 60), -- orange
}

-- Commandes de debug (!lvl, !home) : uniquement actives dans Roblox Studio.
GameConfig.STUDIO_DEBUG_COMMANDS = true

-- Police "cartoon" utilisée partout.
GameConfig.FONT = Enum.Font.FredokaOne

return GameConfig
