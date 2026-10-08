--!strict
-- Net : point d'accès unique aux RemoteEvents / RemoteFunctions.
-- * Côté serveur : crée le dossier ReplicatedStorage.Remotes et tous les remotes listés.
-- * Côté client : attend qu'ils existent.
-- Pour ajouter un remote dans une phase future, il suffit de l'ajouter dans EVENTS / FUNCTIONS.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local EVENTS = {
	"Notify", -- serveur -> client : (payload: { Kind, Title, Subtitle?, Color?, Duration? })
}

local FUNCTIONS: { string } = {}

local Net = {}

local folder: Folder
if RunService:IsServer() then
	local existing = ReplicatedStorage:FindFirstChild("Remotes")
	if existing then
		existing:Destroy()
	end
	folder = Instance.new("Folder")
	folder.Name = "Remotes"
	for _, name in EVENTS do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
	end
	for _, name in FUNCTIONS do
		local remote = Instance.new("RemoteFunction")
		remote.Name = name
		remote.Parent = folder
	end
	folder.Parent = ReplicatedStorage
else
	folder = ReplicatedStorage:WaitForChild("Remotes") :: Folder
end

function Net.Event(name: string): RemoteEvent
	local remote = if RunService:IsServer() then folder:FindFirstChild(name) else folder:WaitForChild(name, 15)
	assert(remote and remote:IsA("RemoteEvent"), `[Net] RemoteEvent inconnu : {name}`)
	return remote
end

function Net.Function(name: string): RemoteFunction
	local remote = if RunService:IsServer() then folder:FindFirstChild(name) else folder:WaitForChild(name, 15)
	assert(remote and remote:IsA("RemoteFunction"), `[Net] RemoteFunction inconnue : {name}`)
	return remote
end

return Net
