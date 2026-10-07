"""Loguetown : la ville du commencement et de la fin (echafaud de Gol D. Roger)."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "loguetown"
Z = 48

FACADES = [M.WIN_CREAM, M.WIN_PINK, M.WIN_YELLOW, M.WIN_BLUE, M.WIN_MINT, M.WIN_TERRA, M.WIN_BRICK, M.WIN_WHITE]
ROOFS = [M.ROOF_RED, M.ROOF_ORANGE, M.ROOF_BLUE, M.ROOF_TEAL, M.ROOF_DARK, M.ROOF_RED, M.ROOF_ORANGE]


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=61, top=M.GRASS, beach=M.SAND, sides=22, jitter=0.06,
                               rx=R, ry=R * 0.9)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # ---------- place centrale + echafaud de Roger -----------------------------
    K.plaza(w, (X - 900, Y - 700, X + 900, Y + 700), Z, M.COBBLE)
    zp = Z + 6
    ex, ey = X, Y + 150
    w.add(G.box(ex - 260, ey - 200, zp + 276, ex + 260, ey + 200, zp + 300, {"top": M.PLANKS, "default": M.WOOD_BEAM}))
    for sx in (-250, -10, 230):
        for sy in (-190, 170):
            w.add(G.box(ex + sx, ey + sy, zp, ex + sx + 20, ey + sy + 20, zp + 276, M.WOOD_BEAM))
    for sy in (-190, 170):
        w.add(G.cylinder((ex - 240, ey + sy + 10, zp + 20), (ex - 10, ey + sy + 10, zp + 260), 6, 6, M.WOOD_BEAM))
        w.add(G.cylinder((ex + 240, ey + sy + 10, zp + 20), (ex + 10, ey + sy + 10, zp + 260), 6, 6, M.WOOD_BEAM))
    w.add(G.box(ex - 260, ey - 200, zp + 300, ex + 260, ey - 192, zp + 340, M.WOOD_BEAM))
    w.add(G.box(ex - 260, ey + 192, zp + 300, ex + 260, ey + 200, zp + 340, M.WOOD_BEAM))
    for sx in (-120, 100):
        w.add(G.box(ex + sx, ey - 10, zp + 300, ex + sx + 20, ey + 10, zp + 560, M.WOOD_BEAM))
    w.add(G.box(ex - 140, ey - 14, zp + 540, ex + 140, ey + 14, zp + 570, M.WOOD_BEAM))
    K.stairs(w, ex + 260, ey - 64, ex + 260 + 560, ey + 64, zp, zp + 300, "-x", M.STAIRS_WOOD, M.PLANKS_DARK)
    w.marker("Echafaud de Gol D. Roger", (ex, ey, zp + 300), "lieu")
    sm = M.sign_mat("loguetown", "LOGUETOWN", sub="La ville du commencement et de la fin")
    w.add(G.box(ex - 200, ey - 214, zp + 196, ex + 200, ey - 206, zp + 270,
                {"-y": Mat(sm, fit=True), "default": M.WOOD_BEAM}))
    for i in range(6):
        K.lamp(w, X - 800 + i * 320, Y - 650, zp)
        K.lamp(w, X - 800 + i * 320, Y + 650, zp)
    K.env_cubemap(w, X, Y - 300, zp + 128)

    # ---------- rues + immeubles colores ----------------------------------------
    K.road(w, X, Y - 700, X, Y - 2600, Z, 256)
    K.road(w, X - 900, Y, X - 2150, Y, Z, 224)   # s'arrete avant la plage (avant : finissait au-dessus de l'eau)
    K.road(w, X + 900, Y, X + 2600, Y, Z, 224)
    K.road(w, X, Y + 700, X, Y + 2200, Z, 224)
    shops = {0: ("armes", "ARMURERIE", "Ipponmatsu", "shop"), 2: ("tailleur", "TAILLEUR", None, "shop"),
             4: ("bar_lt", "GOLD ROGER BAR", None, "bar"), 6: ("hotel_lt", "HOTEL", None, "house"),
             8: ("banque", "BANQUE", None, "office"), 10: ("journal", "JOURNAL", "Morgans", "office"),
             12: ("boulang", "BOULANGERIE", None, "shop"), 14: ("medecin", "MEDECIN", None, "house")}
    k = 0
    # rangees le long de la place (ouest / est)
    for side in (-1, 1):
        for j, ly in enumerate((-640, -250, 140, 520)):
            x0 = X + (side * 1000 if side > 0 else -1000 - 384)
            fac = FACADES[k % len(FACADES)]
            sg = shops.get(k)
            info = K.building(w, x0, Y + ly, Z, 384, 320, floors=2 + (k % 2), facade=fac,
                              roof_kind="gable", roof_mat=ROOFS[k % len(ROOFS)], roof_axis="y",
                              doors=(("-x" if side > 0 else "+x", 0),),
                              sign=M.sign_mat(sg[0], sg[1], sub=sg[2]) if sg else None,
                              awning=[M.AWN_RED, M.AWN_BLUE, M.AWN_GREEN][k % 3] if sg else None)
            K.furnish(w, info, sg[3] if sg else "house", 120 + k)
            k += 1
    # rangees nord / sud
    for side in (-1, 1):
        for j, lx in enumerate((-850, -430, 290, 700)):
            y0 = Y + (900 if side > 0 else -900 - 320)
            fac = FACADES[k % len(FACADES)]
            sg = shops.get(k)
            info = K.building(w, X + lx, y0, Z, 384 if j % 2 == 0 else 256, 320, floors=2 + (j % 2),
                              facade=fac, roof_kind="gable", roof_mat=ROOFS[k % len(ROOFS)], roof_axis="x",
                              doors=(("-y" if side > 0 else "+y", 0),),
                              sign=M.sign_mat(sg[0], sg[1], sub=sg[2]) if sg else None,
                              awning=[M.AWN_RED, M.AWN_BLUE, M.AWN_GREEN][k % 3] if sg else None)
            K.furnish(w, info, sg[3] if sg else "house", 120 + k)
            k += 1
    # pates de maisons en peripherie (decor plein)
    for i in range(14):
        a = math.radians(i * 25.7 + 8)
        r = 1950 + (i % 3) * 120
        bx, by = X + math.cos(a) * r, Y + math.sin(a) * r * 0.9
        if abs(bx - X) < 260 or abs(by - Y) < 240:
            continue
        K.block(w, bx - 160, by - 140, Z, 320, 280, 2 + i % 3, FACADES[(i + 3) % len(FACADES)],
                "gable", ROOFS[i % len(ROOFS)])

    # ---------- base de la Marine (Smoker) -------------------------------------
    mx, my = X + 1500, Y - 1650
    info = K.building(w, mx - 384, my - 256, Z, 768, 512, floors=3, facade=M.WIN_MARINE, roof_kind="hip",
                      roof_mat=M.ROOF_BLUE, doors=(("-x", 0),), door_kind="door", levels=2,
                      sign=M.sign_mat("marine_lt", "MARINE", sub="Base de Loguetown"))
    K.furnish(w, info, "office", 140)
    # tour accolee au mur est (avant : centree sur l'angle, un quart de tour dans les salles et le toit)
    K.tower(w, mx + 524, my + 116, Z, 110, 700, 12, M.WHITE, M.ROOF_BLUE, 220, band=M.MARINE_BLUE)
    K.flagpole(w, mx - 500, my - 300, Z, M.FLAG_MARINE, 420)
    w.marker("Base de la Marine de Loguetown", (mx, my, Z), "batiment")

    # ---------- port ----------------------------------------------------------
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    for off in (-700, 0, 700):
        f = G.Frame(X + math.cos(a) * R * 0.66 - math.sin(a) * off, Y + math.sin(a) * R * 0.6 + math.cos(a) * off,
                    0, math.degrees(a))
        w.add(f.box(0, -100, Z - 12, 1000, 100, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.WOOD_BEAM}))
        for d in range(200, 1000, 300):
            w.prop(K.P_CLEAT, f.p(d, 110, Z), 0)
    f = G.Frame(X + math.cos(a) * R * 0.66, Y + math.sin(a) * R * 0.6, 0, math.degrees(a))
    # navires a quai au bout des pontons, coque entierement dans l'eau
    # (avant : poupe du navire de la Marine et proue du pirate posees sur la plage)
    K.ship(w, *f.p(1150, 360)[:2], math.degrees(a) + 180, 900, "pirate")
    K.ship(w, *f.p(1100, -380)[:2], math.degrees(a), 1000, "marine")
    # arbres d'alignement le long des rues (avant : cercle a R*0.66 qui tombait dans les pates de
    # maisons et en tete du ponton central)
    for tx, ty in ((1600, 280), (1600, -280), (280, -1600), (-280, -1600), (280, 1550), (-280, 1550),
                   (-1600, -280)):
        K.round_tree(w, X + tx, Y + ty, Z, 300, 120)
