"""Alabasta : desert, palais d'Alubarna, tour de l'horloge, Rain Dinners, oasis."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "alabasta"
Z = 48
ZP = 448  # plateau d'Alubarna


def sand_house(w, x, y, sx, sy, floors, seed, door="-y", sign=None, awning=None, kind="house"):
    info = K.building(w, x, y, Z, sx, sy, floors=floors, facade=M.WIN_SAND, inner=M.SANDSTONE,
                      floor_mat=M.SANDPAVE, roof_kind="flat", roof_mat=M.SANDPAVE, doors=((door, 0),),
                      trim=M.SANDSTONE, base=M.SANDBLOCK, sign=sign, awning=awning, levels=1,
                      light_color=(255, 214, 160))
    K.furnish(w, info, kind, seed)
    return info


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=41, top=M.DESERT, beach=M.SAND, sides=22, jitter=0.07,
                               rx=R, ry=R * 0.95)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # ---------- plateau d'Alubarna + palais ----------------------------------
    px, py = X + 200, Y + 1000
    mesa = G.blob(px, py, 1150, 950, 28, 42, 0.04)
    w.add(G.poly_frustum(G.scale_poly(mesa, px, py, 1.07), mesa, Z - 8, ZP,
                         {"top": M.SANDPAVE, "default": M.ROCK_SAND}))   # falaises ocre du plateau d'Alubarna
    # pied a 80 u devant la tour de l'horloge (avant : 150 u dedans) ; le haut arrive au ras du bord du
    # plateau (avant : marche de 22 a 28 u sous le rebord). Pente 37 deg, praticable.
    K.stairs(w, px - 160, py - 1480, px + 160, py - 950, Z, ZP + 2, "+y", M.STAIRS_SAND, M.SANDBLOCK)
    w.marker("Palais d'Alubarna", (px, py, ZP), "batiment")
    # palais
    info = K.building(w, px - 448, py - 200, ZP, 896, 512, floors=2, facade=M.WIN_SAND, inner=M.SANDSTONE,
                      floor_mat=M.MARBLE, roof_kind="flat", roof_mat=M.SANDPAVE, doors=(("-y", 0),),
                      door_kind="arch", door_w=160, door_h=200, trim=M.SANDSTONE, base=M.SANDBLOCK,
                      levels=2, light_color=(255, 220, 170))
    K.furnish(w, info, "office", 60)
    top = info["top"]
    w.add(G.prism(px, py + 56, 220, 16, top, top + 120, M.SANDSTONE))
    K.dome(w, px, py + 56, top + 120, 220, M.GOLD, sides=16)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        K.tower(w, px + sx * 448, py + 56 + sy * 256, ZP, 90, 620 + (60 if sy > 0 else 0), 12, M.SANDSTONE,
                M.ROOF_TEAL, cap="dome", base=M.SANDBLOCK)
    for i in range(8):
        a = math.radians(i * 45 + 22)
        K.palm(w, px + math.cos(a) * 820, py + math.sin(a) * 640, ZP, 380, seed=60 + i)
    for sx in (-170, 170):
        # drapeau tourne vers l'escalier (yaw 180) : avant il s'enfoncait de 88 u dans la facade du palais
        K.flagpole(w, px + sx, py - 280, ZP, M.AWN_PURPLE, 360, yaw=180)

    # ---------- ville basse ---------------------------------------------------
    K.plaza(w, G.ngon(X, Y - 700, 560, 12), Z, M.SANDPAVE)
    # tour de l'horloge
    cx, cy = X, Y - 700
    w.add(G.box(cx - 140, cy - 140, Z, cx + 140, cy + 140, Z + 900, {"default": M.SANDBLOCK, "top": M.SANDSTONE}))
    for side in ("-y", "+y", "-x", "+x"):
        f = {"-y": (cx - 110, cy - 146, cx + 110, cy - 140), "+y": (cx - 110, cy + 140, cx + 110, cy + 146),
             "-x": (cx - 146, cy - 110, cx - 140, cy + 110), "+x": (cx + 140, cy - 110, cx + 146, cy + 110)}[side]
        w.add(G.box(f[0], f[1], Z + 640, f[2], f[3], Z + 860, {side: Mat(M.CLOCK, fit=True), "default": M.GOLD}))
    w.add(G.box(cx - 170, cy - 170, Z + 900, cx + 170, cy + 170, Z + 940, M.SANDSTONE))
    K.dome(w, cx, cy, Z + 940, 150, M.ROOF_TEAL, sides=12)
    w.marker("Tour de l'horloge", (cx, cy, Z), "lieu")

    houses = [(-1500, -1300, 256, 256, 1, "-y"), (-1150, -1300, 320, 256, 2, "-y"),
              (-1500, -900, 256, 256, 1, "+x"), (-1450, -400, 320, 256, 2, "+x"),
              (700, -1350, 256, 256, 1, "-y"), (1050, -1350, 320, 256, 2, "-y"),
              (1400, -900, 256, 256, 1, "-x"), (1350, -450, 320, 256, 2, "-x"),
              (-700, -1800, 256, 256, 1, "+y"), (450, -1850, 256, 256, 1, "+y"),
              (-2100, -200, 256, 256, 1, "+x"), (-2050, 300, 256, 256, 1, "+x")]
    signs = {1: ("taverne", "TAVERNE", "bar"), 4: ("bazar", "BAZAR", "shop"), 5: ("hotel_ab", "HOTEL", "house"),
             8: ("forge", "FORGE", "storage")}
    for i, (lx, ly, sx, sy, fl, dr) in enumerate(houses):
        sg = signs.get(i)
        sand_house(w, X + lx, Y + ly, sx, sy, fl, 61 + i, dr,
                   sign=M.sign_mat(sg[0], sg[1]) if sg else None,
                   awning=[M.AWN_RED, M.AWN_BLUE, M.AWN_PURPLE, M.AWN_GREEN][i % 4] if sg else None,
                   kind=sg[2] if sg else "house")
    # marche : etals
    for i in range(6):
        sx = X - 450 + i * 180
        sy = Y - 1250
        w.add(G.box(sx - 50, sy - 30, Z, sx + 50, sy + 30, Z + 40, {"top": M.PLANKS, "default": M.PLANKS_DARK}))
        for dx in (-46, 42):
            w.add(G.box(sx + dx, sy - 30, Z, sx + dx + 4, sy - 26, Z + 112, M.WOOD_BEAM))  # sous l'auvent
        w.add(G.ramp(sx - 60, sy - 50, Z + 110, sx + 60, sy + 40, Z + 130, "+y",
                     [M.AWN_RED, M.AWN_BLUE, M.AWN_PURPLE, M.AWN_GREEN][i % 4]))
        w.prop(K.P_CRATE2, (sx, sy + 60, Z + 20), i * 30)

    # ---------- Rain Dinners (casino de Rainbase) ------------------------------
    rx, ry = X + 1900, Y + 900
    info = K.building(w, rx - 384, ry - 320, Z, 768, 640, floors=2, facade=M.WIN_SAND, inner=M.CARPET,
                      floor_mat=M.CARPET, roof_kind="flat", roof_mat=M.GOLD, doors=(("-y", 0), ("-x", 0)),
                      door_kind="arch", door_w=128, door_h=160, trim=M.GOLD, base=M.SANDBLOCK,
                      sign=M.sign_mat("rain", "RAIN DINNERS", sub="Casino", color=(255, 220, 90),
                                      board=(40, 90, 60)),
                      levels=1, light_color=(255, 200, 120))
    K.furnish(w, info, "bar", 70)
    top = info["top"]
    w.add(G.frustum(rx, ry, 470, 0, top, top + 520, 4, M.GOLD, rot=45))
    w.marker("Rain Dinners (casino)", (rx, ry, Z), "batiment")

    # ---------- oasis -----------------------------------------------------------
    ox, oy = X + 3300, Y + 500    # oasis dans les dunes pres de Rain Dinners (Rainbase)
    # margelle en anneau : avant, disque plein de 40 u avec 4 u d'eau dessus (socle, pas de bassin)
    ro, ri = G.ngon(ox, oy, 430, 14, 180 / 14), G.ngon(ox, oy, 400, 14, 180 / 14)
    for i in range(14):
        j = (i + 1) % 14
        w.add(G.brush([(p[0], p[1], z) for p in (ro[i], ro[j], ri[i], ri[j]) for z in (Z, Z + 40)],
                      M.SANDBLOCK))
    w.add_world(G.prism(ox, oy, 400, 14, Z + 4, Z + 34, {"top": M.WATER_OASIS, "default": M.NODRAW}))
    w.add(G.prism(ox, oy, 400, 14, Z - 4, Z + 4, M.SAND))
    for i in range(7):
        a = math.radians(i * 51)
        # pied 24 u plus bas (meme sommet) : le palmier cote plage (i = 3, sol ~22) ne flotte plus
        K.palm(w, ox + math.cos(a) * 520, oy + math.sin(a) * 520, Z - 24, 384 + 30 * (i % 3), seed=80 + i)
    w.marker("Oasis", (ox, oy, Z), "lieu")

    # ---------- port ----------------------------------------------------------
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    f = G.Frame(X + math.cos(a) * R * 0.68, Y + math.sin(a) * R * 0.68, 0, math.degrees(a))
    w.add(f.box(0, -110, Z - 12, 1000, 110, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.WOOD_BEAM}))
    w.add(f.box(1000, -420, Z - 12, 1150, 420, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.WOOD_BEAM}))
    # pilotis (le ponton et sa tete flottaient a 36 u au-dessus de l'eau et de la plage)
    for d, lat in ((360, (-96, 96)), (620, (-96, 96)), (880, (-96, 96)), (1075, (-400, -130, 130, 400))):
        for s in lat:
            w.add(f.box(d - 8, s - 8, L.SEA_FLOOR, d + 8, s + 8, Z - 12, M.WOOD_BEAM))
    # navire amarre le long de la tete du ponton, en eau profonde (avant : poupe a 60-120 u du rivage,
    # quille au ras du fond -> bateau echoue sur la plage)
    K.ship(w, *f.p(1100, -560)[:2], math.degrees(a), 900, "pirate")
    sm = M.sign_mat("alabasta", "ALABASTA", sub="Royaume du desert", board=(190, 140, 80))
    w.add(f.box(-30, -150, Z, -14, 150, Z + 120, {"+x": Mat(sm, fit=True), "-x": Mat(sm, fit=True),
                                                  "default": M.WOOD_BEAM}))

    # dunes & rochers
    # (-2300, -1300) et (-600, 2300) retirees : elles debordaient de 160 a 370 u au-dessus de la mer
    # (dalles plates a z 28 flottant sur la plage et l'eau). Graines des dunes gardees inchangees.
    for i, (lx, ly, r, h) in ((0, (1500, -2000, 500, 160)), (2, (2400, -600, 380, 200)),
                              (4, (1200, 2300, 360, 120))):
        w.add(G.boulder(X + lx, Y + ly, Z - 40, r * 1.4, r * 1.1, h * 0.9, 300 + i, M.DESERT, 36,
                        flat_bottom=Z - 20))
    K.env_cubemap(w, X, Y - 700, Z + 200)
    K.env_cubemap(w, px, py - 400, ZP + 128)
