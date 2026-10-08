--!strict
-- Main (client) : point d'entrée unique côté joueur.
-- Démarre les contrôleurs dans l'ordre. Les phases suivantes ajouteront les leurs ici.

local Controllers = script.Parent:WaitForChild("Controllers")

local NotificationController = require(Controllers:WaitForChild("NotificationController"))
local BaseMarkerController = require(Controllers:WaitForChild("BaseMarkerController"))

NotificationController.Start()
BaseMarkerController.Start()
