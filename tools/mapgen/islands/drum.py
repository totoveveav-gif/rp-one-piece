"""Royaume de Drum : ile d'hiver, Drum Rockies, chateau, village de Bighorn."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "drum"
Z = 48


def peak(w, x, y, r, h, seed):
    w.add(G.boulder(x, y, Z + 60, r * 1.5, r * 1.4, 260, 500 + seed, {"default": M.ROCK, "top": M.SNOW}, 34,
                    flat_bottom=Z - 8))
    w.add(G.frustum(x, y, r * 1.04, r * 0.96, Z + 160, Z + h - 120, 24, {"default": M.ROCK, "top": M.SNOW},
                    rot=seed * 7))
    w.add(G.frustum(x, y, r * 1.08, r * 1.0, Z + h - 120, Z + h, 24, {"default": M.SNOW, "top": M.SNOW},
                    rot=seed * 7))
    return Z + h


def booth(w, x, y, z, target, name, sign):
    """Cabine de telepherique (teleportation a l'interieur)."""
    w.add(G.box(x - 96, y - 96, z, x + 96, y + 96, z + 8, M.PLANKS))
    for (a0, b0, a1, b1) in ((-96, -96, 96, -80), (-96, 80, 96, 96), (80, -80, 96, 80)):
        w.add(G.box(x + a0, y + b0, z + 8, x + a1, y + b1, z + 168, M.WIN_SNOW))
    w.add(G.box(x - 112, y - 112, z + 168, x + 112, y + 112, z + 184, M.ROOF_RED))
    w.add(G.box(x - 104, y - 60, z + 120, x - 96, y + 60, z + 164, {"-x": Mat(sign, fit=True), "default": M.WOOD_BEAM}))
    trig = G.box(x - 40, y - 64, z + 8, x + 64, y + 64, z + 120, M.TRIGGER)
    w.ent("trigger_teleport", brushes=trig, target=target, spawnflags=1, targetname="tp_" + name)
    w.light((x, y, z + 140), (255, 210, 160), 120)


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=91, top=M.SNOW, beach=M.SNOW, sides=20, jitter=0.08)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # Drum Rockies
    cx, cy = X + 200, Y + 700
    top = peak(w, cx, cy, 520, 2300, 1)
    peak(w, X - 1100, Y + 300, 360, 1600, 2)
    peak(w, X - 300, Y + 1700, 300, 1250, 3)
    peak(w, X + 1300, Y + 1500, 260, 1000, 4)
    # Drum Rockies de l'arriere-pays (dans l'anime, ces montagnes cylindriques sont partout)
    peak(w, X - 3100, Y + 1800, 400, 1500, 5)
    peak(w, X, Y + 2850, 340, 1300, 6)
    # chateau de Drum au sommet
    info = K.building(w, cx - 256, cy - 192, top, 512, 384, floors=2, facade=M.WIN_STONE, roof_kind="flat",
                      roof_mat=M.SNOW, doors=(("-y", 0),), door_kind="arch", door_w=128, door_h=160, levels=1,
                      trim=M.STONE_GREY, light_color=(255, 220, 190))
    K.furnish(w, info, "house", 200)
    t2 = info["top"]
    w.add(G.prism(cx, cy, 120, 12, t2, t2 + 160, M.STONE_GREY))
    K.dome(w, cx, cy, t2 + 160, 130, M.ROOF_RED, sides=12)
    for sx in (-1, 1):
        K.tower(w, cx + sx * 300, cy - 150, top, 70, 520, 10, M.STONE_GREY, M.ROOF_RED, 200, base=M.STONE_GREY)
    # mat decale du perron, drapeau tendu vers le vide (avant : traversait la facade du chateau)
    K.flagpole(w, cx - 170, cy - 260, top, M.FLAG_SH, 260, yaw=180)
    w.marker("Chateau de Drum", (cx, cy, top), "batiment")
    # telepherique
    bx, by = cx - 300, cy - 1200          # cabine basse decollee du chalet voisin (les toits se touchaient)
    s_up = M.sign_mat("tele_up", "TELEPHERIQUE", sub="Vers le chateau")
    s_dn = M.sign_mat("tele_dn", "TELEPHERIQUE", sub="Vers le village")
    booth(w, bx, by, Z, "drum_tele_haut", "drum_monter", s_up)
    # gare haute entierement posee sur le sommet (rayon 520), ouverture (-x) vers le parvis du chateau
    # (avant : a moitie dans le vide, ouverture au-dessus du precipice -> impossible de redescendre)
    tx, ty = cx + 150, cy - 350
    booth(w, tx, ty, top, "drum_tele_bas", "drum_descendre", s_dn)
    K.tp_destination(w, "drum_tele_haut", cx - 40, cy - 330, top + 16, 90)
    # arrivee en bas devant l'ouverture de la cabine (avant : a l'interieur du chalet voisin)
    K.tp_destination(w, "drum_tele_bas", bx - 170, by, Z + 16, -90)
    # cables accroches au bord sud du toit de la gare haute, au-dessus de la corniche de neige
    w.add(G.cylinder((bx, by, Z + 190), (tx - 50, ty - 126, top + 190), 4, 6, M.IRON))
    w.add(G.cylinder((bx + 30, by, Z + 190), (tx - 20, ty - 126, top + 190), 4, 6, M.IRON))
    w.marker("Telepherique de Drum", (bx, by, Z), "lieu")

    # village de Bighorn
    vx, vy = X - 200, Y - 1000
    K.plaza(w, (vx - 600, vy - 400, vx + 600, vy + 300), Z, M.COBBLE)
    lodges = [(-1000, -300, "+x", None), (-1000, 150, "+x", ("taverne_d", "TAVERNE", "bar")),
              (700, -350, "-x", ("hopital_d", "CLINIQUE", "house")), (700, 100, "-x", None),
              (-450, -900, "+y", None), (100, -900, "+y", ("magasin_d", "MAGASIN", "shop")),
              (-450, 450, "-y", None), (250, 450, "-y", None)]
    for i, (lx, ly, d, sg) in enumerate(lodges):
        info = K.building(w, vx + lx, vy + ly, Z, 320, 256, floors=2, facade=M.WIN_SNOW, roof_kind="gable",
                          roof_mat=M.SNOW, doors=((d, 0),), levels=1, inner=M.PLANKS_LIGHT,
                          sign=M.sign_mat(sg[0], sg[1]) if sg else None, light_color=(255, 200, 150))
        K.furnish(w, info, sg[2] if sg else "house", 201 + i)
    w.marker("Village de Bighorn", (vx, vy, Z), "lieu")
    for i in range(26):
        a = math.radians(i * 13.8)
        r = R * (0.48 + 0.18 * ((i * 7) % 5) / 5)
        px, py = X + math.cos(a) * r, Y + math.sin(a) * r
        # ni dans le village, ni dans un Drum Rocky ou son socle rocheux (rayon x 1.5)
        if math.hypot(px - vx, py - vy) < 1100 or any(
                math.hypot(px - qx, py - qy) < qr * 1.5 + 160
                for qx, qy, qr in ((cx, cy, 520), (X - 1100, Y + 300, 360), (X - 300, Y + 1700, 300),
                                   (X + 1300, Y + 1500, 260))):
            continue
        K.pine(w, px, py, Z, 420 + (i % 4) * 60, 140)

    # port
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    f = G.Frame(X + math.cos(a) * R * 0.68, Y + math.sin(a) * R * 0.68, 0, math.degrees(a))
    w.add(f.box(-100, -100, Z - 12, 1000, 100, Z + 3, {"top": M.PLANKS_DARK, "default": M.WOOD_BEAM}))
    for d in (200, 460, 720, 980):        # pieux : le ponton ne flotte plus au-dessus de la plage et de l'eau
        for s in (-1, 1):
            w.add(G.prism(*f.p(d, s * 84)[:2], 12, 6, -300, Z - 12, M.WOOD_BEAM))
    # navire au mouillage en eau profonde (avant : poupe echouee sur la plage)
    K.ship(w, *f.p(900, 400)[:2], math.degrees(a), 900, "pirate")
    sg = M.sign_mat("drum", "ROYAUME DE DRUM", sub="Ile d'hiver")
    w.add(f.box(-120, -150, Z, -104, 150, Z + 120, {"+x": Mat(sg, fit=True), "-x": Mat(sg, fit=True),
                                                    "default": M.WOOD_BEAM}))
    K.env_cubemap(w, vx, vy, Z + 128)
    K.env_cubemap(w, cx, cy - 300, top + 100)
