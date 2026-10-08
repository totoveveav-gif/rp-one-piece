--!strict
-- NotificationController : notifications animées (mobile-first).
--   Toast  : petit message empilé en haut de l'écran ("+1 MONSTER", "BASE LEVEL 3"...)
--   Banner : grand titre centré, un seul à la fois, file d'attente ("YOUR FIRST MONSTER!")
-- Le serveur les déclenche via le RemoteEvent "Notify" ; le client peut aussi les appeler.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Net = require(Shared:WaitForChild("Net"))

export type Payload = {
	Kind: string, -- "Toast" | "Banner"
	Title: string,
	Subtitle: string?,
	Color: Color3?,
	Duration: number?,
}

local MAX_TOASTS = 4
local DEFAULT_COLOR = Color3.fromRGB(255, 205, 70)
local DARK = Color3.fromRGB(24, 20, 40)

local NotificationController = {}

local screenGui: ScreenGui
local toastContainer: Frame
local bannerQueue: { Payload } = {}
local bannerRunning = false

local function corner(parent: Instance, radius: number)
	local c = Instance.new("UICorner")
	c.CornerRadius = UDim.new(0, radius)
	c.Parent = parent
end

local function stroke(parent: Instance, color: Color3, thickness: number)
	local s = Instance.new("UIStroke")
	s.Color = color
	s.Thickness = thickness
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = parent
end

-- Un CanvasGroup coupe tout ce qui dépasse de ses bords (dont le contour UIStroke).
-- On place donc la "carte" visible à l'intérieur avec une petite marge.
local function card(group: CanvasGroup, accent: Color3, radius: number, thickness: number): Frame
	local margin = thickness + 1
	local frame = Instance.new("Frame")
	frame.Name = "Card"
	frame.AnchorPoint = Vector2.new(0.5, 0.5)
	frame.Position = UDim2.fromScale(0.5, 0.5)
	frame.Size = UDim2.new(1, -margin * 2, 1, -margin * 2)
	frame.BackgroundColor3 = DARK
	frame.BackgroundTransparency = 0.1
	frame.ClipsDescendants = false
	frame.Parent = group
	corner(frame, radius)
	stroke(frame, accent, thickness)
	return frame
end

local function label(parent: Instance, text: string, maxTextSize: number): TextLabel
	local l = Instance.new("TextLabel")
	l.BackgroundTransparency = 1
	l.Font = GameConfig.FONT
	l.Text = text
	l.TextColor3 = Color3.new(1, 1, 1)
	l.TextScaled = true
	l.Parent = parent
	local constraint = Instance.new("UITextSizeConstraint")
	constraint.MaxTextSize = maxTextSize
	constraint.Parent = l
	local textStroke = Instance.new("UIStroke")
	textStroke.Color = Color3.new(0, 0, 0)
	textStroke.Thickness = 2
	textStroke.Parent = l
	return l
end

local function buildGui()
	local playerGui = Players.LocalPlayer:WaitForChild("PlayerGui")

	screenGui = Instance.new("ScreenGui")
	screenGui.Name = "NotificationsUI"
	screenGui.ResetOnSpawn = false
	screenGui.IgnoreGuiInset = true
	screenGui.DisplayOrder = 50
	screenGui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling

	toastContainer = Instance.new("Frame")
	toastContainer.Name = "Toasts"
	toastContainer.AnchorPoint = Vector2.new(0.5, 0)
	toastContainer.Position = UDim2.new(0.5, 0, 0, 64) -- sous la barre Roblox
	toastContainer.Size = UDim2.new(0.92, 0, 0.5, 0)
	toastContainer.BackgroundTransparency = 1
	toastContainer.Parent = screenGui

	local sizeConstraint = Instance.new("UISizeConstraint")
	sizeConstraint.MaxSize = Vector2.new(440, math.huge)
	sizeConstraint.Parent = toastContainer

	local layout = Instance.new("UIListLayout")
	layout.FillDirection = Enum.FillDirection.Vertical
	layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Padding = UDim.new(0, 8)
	layout.Parent = toastContainer

	screenGui.Parent = playerGui
end

local toastCounter = 0

function NotificationController.Toast(title: string, color: Color3?, duration: number?)
	local accent = color or DEFAULT_COLOR

	-- Limite le nombre de toasts visibles : on retire les plus anciens.
	local existing = {}
	for _, child in toastContainer:GetChildren() do
		if child:IsA("CanvasGroup") then
			table.insert(existing, child)
		end
	end
	table.sort(existing, function(a, b)
		return a.LayoutOrder < b.LayoutOrder
	end)
	for i = 1, #existing - MAX_TOASTS + 1 do
		existing[i]:Destroy()
	end

	toastCounter += 1
	local toast = Instance.new("CanvasGroup")
	toast.Name = "Toast"
	toast.LayoutOrder = toastCounter
	toast.Size = UDim2.new(1, 0, 0, 54)
	toast.BackgroundTransparency = 1
	toast.GroupTransparency = 1
	local body = card(toast, accent, 14, 3)

	local text = label(body, title, 26)
	text.Position = UDim2.new(0, 16, 0, 6)
	text.Size = UDim2.new(1, -28, 1, -12)

	local scale = Instance.new("UIScale")
	scale.Scale = 0.7
	scale.Parent = toast

	toast.Parent = toastContainer

	TweenService:Create(scale, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	TweenService:Create(toast, TweenInfo.new(0.2), { GroupTransparency = 0 }):Play()

	task.delay(duration or 2.5, function()
		if not toast.Parent then
			return
		end
		local fade = TweenService:Create(toast, TweenInfo.new(0.3), { GroupTransparency = 1 })
		fade:Play()
		fade.Completed:Wait()
		toast:Destroy()
	end)
end

local function playBanner(payload: Payload)
	local accent = payload.Color or DEFAULT_COLOR

	local banner = Instance.new("CanvasGroup")
	banner.Name = "Banner"
	banner.AnchorPoint = Vector2.new(0.5, 0.5)
	banner.Position = UDim2.fromScale(0.5, 0.3)
	banner.Size = UDim2.new(0.9, 0, 0, 124)
	banner.BackgroundTransparency = 1
	banner.GroupTransparency = 1
	local body = card(banner, accent, 22, 4)

	local sizeConstraint = Instance.new("UISizeConstraint")
	sizeConstraint.MaxSize = Vector2.new(640, 124)
	sizeConstraint.Parent = banner

	local title = label(body, payload.Title, 54)
	title.Position = UDim2.new(0, 16, 0, 8)
	title.Size = UDim2.new(1, -32, if payload.Subtitle then 0.6 else 1, if payload.Subtitle then -8 else -16)
	local gradient = Instance.new("UIGradient")
	gradient.Color = ColorSequence.new(Color3.new(1, 1, 1), accent)
	gradient.Rotation = 90
	gradient.Parent = title

	if payload.Subtitle then
		local subtitle = label(body, payload.Subtitle, 24)
		subtitle.Position = UDim2.new(0, 16, 0.6, 0)
		subtitle.Size = UDim2.new(1, -32, 0.4, -10)
		subtitle.TextColor3 = Color3.fromRGB(225, 225, 240)
	end

	local scale = Instance.new("UIScale")
	scale.Scale = 0.4
	scale.Parent = banner

	banner.Parent = screenGui

	TweenService:Create(scale, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	TweenService:Create(banner, TweenInfo.new(0.25), { GroupTransparency = 0 }):Play()

	task.wait(payload.Duration or 3)

	local out = TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	TweenService:Create(banner, out, { GroupTransparency = 1, Position = UDim2.fromScale(0.5, 0.24) }):Play()
	local shrink = TweenService:Create(scale, out, { Scale = 0.85 })
	shrink:Play()
	shrink.Completed:Wait()
	banner:Destroy()
end

function NotificationController.Banner(payload: Payload)
	table.insert(bannerQueue, payload)
	if bannerRunning then
		return
	end
	bannerRunning = true
	task.spawn(function()
		while #bannerQueue > 0 do
			local nextPayload = table.remove(bannerQueue, 1) :: Payload
			playBanner(nextPayload)
		end
		bannerRunning = false
	end)
end

-- Le serveur est la seule source de ces messages, mais on valide quand même le format
-- (un module client ne doit jamais planter sur une donnée inattendue).
local function onNotify(raw: any)
	if typeof(raw) ~= "table" or typeof(raw.Title) ~= "string" then
		return
	end
	local payload: Payload = {
		Kind = if raw.Kind == "Banner" then "Banner" else "Toast",
		Title = raw.Title,
		Subtitle = if typeof(raw.Subtitle) == "string" then raw.Subtitle else nil,
		Color = if typeof(raw.Color) == "Color3" then raw.Color else nil,
		Duration = if typeof(raw.Duration) == "number" then math.clamp(raw.Duration, 0.5, 10) else nil,
	}
	if payload.Kind == "Banner" then
		NotificationController.Banner(payload)
	else
		NotificationController.Toast(payload.Title, payload.Color, payload.Duration)
	end
end

function NotificationController.Start()
	buildGui()
	Net.Event("Notify").OnClientEvent:Connect(onNotify)
end

return NotificationController
