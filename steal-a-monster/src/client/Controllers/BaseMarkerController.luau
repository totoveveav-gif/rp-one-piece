--!strict
-- BaseMarkerController : tout ce qui aide le joueur à se repérer par rapport à SA base.
--   * Marqueur "🏠 YOUR BASE ▼" au-dessus de ta base, visible à travers les murs
--     (essentiel quand on revient d'un vol !). Caché quand tu es déjà chez toi.
--   * Caméra : après chaque apparition, elle est recalée pour regarder tes monstres.
-- Purement visuel et local : le serveur reste seul maître de l'attribution des bases.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))

local HOME_MARGIN = 2 -- studs autour du sol de la base qui comptent encore comme "chez soi"
local CHECK_INTERVAL = 0.5 -- pas besoin de vérifier à chaque frame
local CAMERA_SNAP_TIMEOUT = 5

local player = Players.LocalPlayer

local BaseMarkerController = {}

local marker: BillboardGui? = nil
local homeFloor: BasePart? = nil

local function buildMarker(adornee: BasePart, accent: Color3): BillboardGui
	local gui = Instance.new("BillboardGui")
	gui.Name = "YourBaseMarker"
	gui.Adornee = adornee
	gui.AlwaysOnTop = true
	gui.Size = UDim2.fromOffset(190, 64)
	-- Même point d'ancrage que le haut de la carte du propriétaire (OwnerBillboard : 7 + 4/2 studs),
	-- puis décalé de sa propre hauteur vers le haut : jamais de chevauchement, à toute distance.
	gui.StudsOffsetWorldSpace = Vector3.new(0, 9, 0)
	gui.SizeOffset = Vector2.new(0, 0.6)
	gui.LightInfluence = 0
	gui.ResetOnSpawn = false

	local text = Instance.new("TextLabel")
	text.Name = "Label"
	text.BackgroundTransparency = 1
	text.Size = UDim2.new(1, 0, 0.62, 0)
	text.Font = GameConfig.FONT
	text.TextScaled = true
	text.Text = "🏠 YOUR BASE"
	text.TextColor3 = Color3.new(1, 1, 1)
	text.Parent = gui
	local textStroke = Instance.new("UIStroke")
	textStroke.Color = accent
	textStroke.Thickness = 3
	textStroke.Parent = text

	local arrow = Instance.new("TextLabel")
	arrow.Name = "Arrow"
	arrow.BackgroundTransparency = 1
	arrow.Position = UDim2.fromScale(0, 0.58)
	arrow.Size = UDim2.new(1, 0, 0.42, 0)
	arrow.Font = GameConfig.FONT
	arrow.TextScaled = true
	arrow.Text = "▼"
	arrow.TextColor3 = accent
	arrow.Parent = gui

	gui.Parent = player:WaitForChild("PlayerGui")
	return gui
end

local function setupForBase(baseIndex: number)
	if marker then
		marker:Destroy()
		marker = nil
	end
	homeFloor = nil

	local bases = workspace:WaitForChild("Bases", 15)
	local model = bases and bases:WaitForChild("Base_" .. baseIndex, 15)
	local arch = model and model:WaitForChild("Arch", 15)
	local sign = arch and arch:WaitForChild("Sign", 15)
	local floor = model and model:WaitForChild("Floor", 15)
	if not (model and sign and sign:IsA("BasePart") and floor and floor:IsA("BasePart")) then
		warn("[BaseMarker] Base introuvable côté client (Workspace.StreamingEnabled doit être désactivé)")
		return
	end

	local accentValue = model:GetAttribute("AccentColor")
	local accent = if typeof(accentValue) == "Color3" then accentValue else Color3.new(1, 1, 1)
	marker = buildMarker(sign, accent)
	homeFloor = floor
end

-- Vrai si la position est au-dessus du sol de notre base (+ petite marge).
local function isAtHome(position: Vector3): boolean
	local floor = homeFloor
	if not floor then
		return false
	end
	local relative = floor.CFrame:PointToObjectSpace(position)
	return math.abs(relative.X) <= floor.Size.X / 2 + HOME_MARGIN
		and math.abs(relative.Z) <= floor.Size.Z / 2 + HOME_MARGIN
end

local function refreshVisibility()
	local currentMarker = marker
	if not currentMarker then
		return
	end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	currentMarker.Enabled = not (root and isAtHome(root.Position))
end

-- Le personnage apparaît d'abord au spawn de secours, et la caméra Roblox se cale sur cette
-- direction-là. On attend que la téléportation serveur soit arrivée (root dans notre base),
-- puis on oriente la caméra dans le dos du joueur, vers ses monstres.
local function snapCameraWhenHome(character: Model)
	local root = character:WaitForChild("HumanoidRootPart", 10)
	if not (root and root:IsA("BasePart")) then
		return
	end
	local deadline = os.clock() + CAMERA_SNAP_TIMEOUT
	while os.clock() < deadline and character.Parent and player.Character == character do
		if isAtHome(root.Position) then
			RunService.RenderStepped:Wait()
			local camera = workspace.CurrentCamera
			local look = root.CFrame.LookVector
			camera.CFrame = CFrame.lookAt(root.Position - look * 12 + Vector3.new(0, 5, 0), root.Position + look * 6)
			return
		end
		RunService.Heartbeat:Wait()
	end
end

function BaseMarkerController.Start()
	local function onBaseIndexChanged()
		local index = player:GetAttribute("BaseIndex")
		if typeof(index) == "number" then
			task.spawn(setupForBase, index)
		end
	end
	player:GetAttributeChangedSignal("BaseIndex"):Connect(onBaseIndexChanged)
	onBaseIndexChanged()

	player.CharacterAdded:Connect(function(character)
		task.spawn(snapCameraWhenHome, character)
	end)
	if player.Character then
		task.spawn(snapCameraWhenHome, player.Character)
	end

	task.spawn(function()
		while true do
			refreshVisibility()
			task.wait(CHECK_INTERVAL)
		end
	end)
end

return BaseMarkerController
