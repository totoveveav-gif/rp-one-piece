--!strict
-- Main : point d'entrée unique du serveur.
-- Charge les services dans un ordre fixe, appelle Init() sur tous, puis Start() sur tous.
--   Init()  : construire / préparer (pas encore de joueurs gérés)
--   Start() : brancher les événements joueurs
-- Pour ajouter un service dans une phase future : créer le module dans "Services"
-- puis ajouter son nom dans SERVICE_ORDER.

local Services = script.Parent:WaitForChild("Services")

local SERVICE_ORDER = {
	"MapService",
	"BaseService",
}

type Service = {
	Init: ((self: any) -> ())?,
	Start: ((self: any) -> ())?,
}

local loaded: { [string]: Service } = {}

for _, name in SERVICE_ORDER do
	local module = Services:WaitForChild(name, 10)
	assert(module and module:IsA("ModuleScript"), `[Main] Service introuvable : {name}`)
	loaded[name] = (require :: any)(module)
end

for _, name in SERVICE_ORDER do
	local service = loaded[name]
	local init = service.Init
	if init then
		init(service)
	end
end

for _, name in SERVICE_ORDER do
	local service = loaded[name]
	local start = service.Start
	if start then
		start(service)
	end
end

print("[Steal a Monster] Serveur prêt ✅")
