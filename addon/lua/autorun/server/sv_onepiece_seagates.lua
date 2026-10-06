--[[-------------------------------------------------------------------------
    rp_onepiece_grandline - Portes de la Grand Line

    La map teleporte deja les joueurs tout seule (trigger_teleport).
    Ce script ajoute la teleportation des NAVIRES ENTIERS : props soudes,
    vehicules, sieges et joueurs a bord arrivent ensemble, dans le bon sens,
    avec leur vitesse conservee.

    Fonctionnement : chaque portail contient un trigger_multiple nomme
    "tp_gate_<ile>_<destination>" qui appelle OP_SeaGate() via l'entite
    lua_run "op_seagate_lua". La destination est l'entite
    info_teleport_destination "arrive_<destination>".
---------------------------------------------------------------------------]]

if game.GetMap() ~= "rp_onepiece_grandline" then return end

local COOLDOWN = 4          -- secondes avant qu'une entite puisse reprendre un portail
local cooldown = setmetatable({}, { __mode = "k" })

local function disableNativeGates()
    -- quand ce script est present, il gere tout (joueurs compris)
    for _, t in ipairs(ents.FindByClass("trigger_teleport")) do
        if string.StartWith(t:GetName(), "tpn_gate_") then
            t:Fire("Disable")
        end
    end
end
hook.Add("InitPostEntity", "OP_SeaGates_Init", disableNativeGates)
hook.Add("PostCleanupMap", "OP_SeaGates_Init", disableNativeGates)

local function collectShip(ent)
    local group = {}
    local root = ent

    if ent:IsPlayer() then
        local veh = ent:GetVehicle()
        local ground = ent:GetGroundEntity()
        if IsValid(veh) then
            root = veh
        elseif IsValid(ground) and not ground:IsWorld() then
            root = ground
        else
            group[ent] = true
            return group, ent
        end
    end

    group[root] = true
    for _, e in pairs(constraint.GetAllConstrainedEntities(root) or {}) do
        group[e] = true
    end
    -- enfants / parents (sieges parentes, decorations...)
    for e in pairs(table.Copy(group)) do
        for _, c in ipairs(e:GetChildren()) do group[c] = true end
        local p = e:GetParent()
        if IsValid(p) then group[p] = true end
    end
    -- joueurs debout sur le pont
    for _, ply in ipairs(player.GetAll()) do
        if ply:Alive() and not IsValid(ply:GetVehicle()) and group[ply:GetGroundEntity()] then
            group[ply] = true
        end
    end
    return group, root
end

function OP_SeaGate()
    local ent, trig = ACTIVATOR, CALLER
    if not IsValid(ent) or not IsValid(trig) then return end
    if (cooldown[ent] or 0) > CurTime() then return end

    local dst = string.match(trig:GetName(), "^tp_gate_%w+_(%w+)$")
    if not dst then return end
    local dest = ents.FindByName("arrive_" .. dst)[1]
    if not IsValid(dest) then return end

    local group, root = collectShip(ent)
    local anchorPos = root:GetPos()
    local anchorYaw = root:IsPlayer() and root:EyeAngles().y or root:GetAngles().y
    local anchorAng = Angle(0, anchorYaw, 0)
    local destAng = Angle(0, dest:GetAngles().y, 0)
    local destPos = dest:GetPos()
    destPos.z = math.max(anchorPos.z, 4)       -- le niveau de la mer est le meme partout
    local turn = Angle(0, destAng.y - anchorYaw, 0)

    for e in pairs(group) do
        if IsValid(e) then
            cooldown[e] = CurTime() + COOLDOWN
            local parent = e:GetParent()
            local carried = IsValid(parent) and group[parent]
            local lp, la = WorldToLocal(e:GetPos(), e:GetAngles(), anchorPos, anchorAng)
            local np, na = LocalToWorld(lp, la, destPos, destAng)

            if e:IsPlayer() then
                if not IsValid(e:GetVehicle()) then
                    local vel = e:GetVelocity()
                    vel:Rotate(turn)
                    e:SetPos(np)
                    local ea = e:EyeAngles()
                    e:SetEyeAngles(Angle(ea.p, ea.y + turn.y, 0))
                    e:SetLocalVelocity(vel)
                end
            elseif not carried then
                local phys = e:GetPhysicsObject()
                local vel = IsValid(phys) and phys:GetVelocity() or e:GetVelocity()
                vel:Rotate(turn)
                e:SetPos(np)
                e:SetAngles(na)
                if IsValid(phys) then
                    phys:SetPos(np)
                    phys:SetAngles(na)
                    phys:SetVelocity(vel)
                    phys:Wake()
                end
            end
        end
    end
end
