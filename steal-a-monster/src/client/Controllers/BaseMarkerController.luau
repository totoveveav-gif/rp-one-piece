--!strict
-- BaseMarkerController : affiche "🏠 YOUR BASE" au-dessus de ta base, visible à travers les murs,
-- pour ne jamais être perdu (essentiel quand on revient d'un vol !).
-- Le marqueur se cache quand on est déjà dans sa base pour ne pas encombrer l'écran.
-- Purement visuel et local : le serveur reste seul maître de l'attribution des bases.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))

local HIDE_DISTANCE = 45 -- studs : en dessous, on est "chez soi"
local CHECK_INTERVAL = 0.5 -- pas besoin de vérifier à chaque frame

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
	gui.StudsOffsetWorldSpace = Vector3.new(0, 14, 0)
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

local function refreshVisibility()
	local currentMarker = marker
	local floor = homeFloor
	if not currentMarker or not floor then
		return
	end
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then
		currentMarker.Enabled = true
		return
	end
	currentMarker.Enabled = (root.Position - floor.Position).Magnitude > HIDE_DISTANCE
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

	task.spawn(function()
		while true do
			refreshVisibility()
			task.wait(CHECK_INTERVAL)
		end
	end)
end

return BaseMarkerController
