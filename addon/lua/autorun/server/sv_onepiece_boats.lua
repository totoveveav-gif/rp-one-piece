--[[-------------------------------------------------------------------------
    rp_onepiece_grandline - Capitaineries (location de bateaux)

    Chaque port a une capitainerie avec un bouton rouge "LOUER UN BATEAU".
    Le bateau apparait au bout du ponton (info_target "boat_spawn_<ile>").

    Reglages (console serveur / server.cfg) :
      op_boat_vehicle  "Airboat"  nom dans la liste des vehicules GMod
                                  (ou classe d'entite d'un addon de bateaux)
      op_boat_price    "0"        prix en argent DarkRP (0 = gratuit)
      op_boat_cooldown "15"       delai entre deux locations (secondes)

    Un joueur n'a qu'un bateau loue a la fois : en louer un nouveau
    supprime l'ancien. Le bateau est supprime quand le joueur se deconnecte.
---------------------------------------------------------------------------]]

if game.GetMap() ~= "rp_onepiece_grandline" then return end

local cvVehicle = CreateConVar("op_boat_vehicle", "Airboat", FCVAR_ARCHIVE,
    "Vehicule loue a la capitainerie (liste Vehicles ou classe d'entite)")
local cvPrice = CreateConVar("op_boat_price", "0", FCVAR_ARCHIVE, "Prix DarkRP de la location")
local cvCooldown = CreateConVar("op_boat_cooldown", "15", FCVAR_ARCHIVE, "Delai entre deux locations")

local rented = {}

local function say(ply, msg)
    ply:ChatPrint("[Capitainerie] " .. msg)
end

local function spawnBoat(name, pos, ang)
    local data = list.Get("Vehicles")[name]
    local ent
    if data then
        ent = ents.Create(data.Class)
        if not IsValid(ent) then return end
        ent:SetModel(data.Model)
        for k, v in pairs(data.KeyValues or {}) do
            ent:SetKeyValue(k, v)
        end
        ent.VehicleName = name
        ent.VehicleTable = data
    else
        ent = ents.Create(name)
        if not IsValid(ent) then return end
    end
    ent:SetPos(pos)
    ent:SetAngles(ang)
    ent:Spawn()
    ent:Activate()
    return ent
end

function OP_BoatRental()
    local ply, btn = ACTIVATOR, CALLER
    if not IsValid(ply) or not ply:IsPlayer() or not IsValid(btn) then return end
    if (ply.OPBoatNext or 0) > CurTime() then
        say(ply, "Patientez encore " .. math.ceil(ply.OPBoatNext - CurTime()) .. " s.")
        return
    end

    local key = string.match(btn:GetName(), "^boat_btn_(%w+)$")
    local spot = key and ents.FindByName("boat_spawn_" .. key)[1]
    if not IsValid(spot) then return end

    for _, e in ipairs(ents.FindInSphere(spot:GetPos(), 160)) do
        if e:IsVehicle() or e:IsPlayer() or (e:GetMoveType() == MOVETYPE_VPHYSICS and not e:IsWorld()) then
            say(ply, "Le bout du ponton est encombre, degagez la place.")
            return
        end
    end

    local price = cvPrice:GetInt()
    if price > 0 and ply.canAfford then
        if not ply:canAfford(price) then
            say(ply, "Il vous faut " .. price .. " pour louer un bateau.")
            return
        end
        ply:addMoney(-price)
    end

    if IsValid(rented[ply]) then rented[ply]:Remove() end
    local boat = spawnBoat(cvVehicle:GetString(), spot:GetPos(), spot:GetAngles())
    if not IsValid(boat) then
        say(ply, "Vehicule introuvable : verifiez op_boat_vehicle.")
        return
    end
    rented[ply] = boat
    ply.OPBoatNext = CurTime() + cvCooldown:GetFloat()
    if boat.CPPISetOwner then boat:CPPISetOwner(ply) end
    if boat.keysOwn then boat:keysOwn(ply) end
    say(ply, "Votre bateau vous attend au bout du ponton. Bon vent !")
end

hook.Add("PlayerDisconnected", "OP_BoatRental_Cleanup", function(ply)
    if IsValid(rented[ply]) then rented[ply]:Remove() end
    rented[ply] = nil
end)
