"""Marineford : QG de la Marine, place d'Oris, echafaud, baie, murs de siege."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat
from ..vmf import add_output

KEY = "marineford"
Z = 64


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]

    def P(lx, ly):
        return (X + lx, Y + ly)

    def pts(lst):
        return [P(a, b) for a, b in lst]

    main = pts([(-3300, 380), (3300, 380), (3550, 1600), (2900, 3200), (0, 3650), (-2900, 3200), (-3550, 1600)])
    west = pts([(-3300, 420), (-1450, 420), (-1250, -900), (-1550, -2500), (-2250, -3000), (-3200, -2500), (-3650, -900)])
    east = [(2 * X - x, y) for (x, y) in west]
    for poly in (main, west, east):
        K.quay_terrain(w, G.convex_hull_2d(poly), Z, top=M.GRASS, side=M.STONE_GREY)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in G.convex_hull_2d(main + west + east)]

    # ---------- place d'Oris -------------------------------------------------
    K.plaza(w, (X - 1450, Y + 380, X + 1450, Y + 1750), Z, M.PAVING)
    K.plaza(w, (X - 3100, Y + 600, X - 1450, Y + 1500), Z, M.COBBLE)
    K.plaza(w, (X + 1450, Y + 600, X + 3100, Y + 1500), Z, M.COBBLE)
    zp = Z + 6
    K.env_cubemap(w, X, Y + 800, zp + 128)

    # echafaud (execution)
    ex, ey = X, Y + 1050
    w.add(G.frustum(ex, ey, 300, 230, zp, zp + 440, 4, {"top": M.STONE_GREY, "default": M.STONE}, rot=45))
    w.add(G.box(ex - 224, ey - 160, zp + 440, ex + 224, ey + 160, zp + 480,
                {"top": M.PLANKS, "default": M.WOOD_BEAM}))
    for sx in (-200, 200):
        w.add(G.box(ex + sx - 10, ey - 10, zp + 480, ex + sx + 10, ey + 10, zp + 760, M.WOOD_BEAM))
    w.add(G.box(ex - 230, ey - 14, zp + 740, ex + 230, ey + 14, zp + 770, M.WOOD_BEAM))
    K.stairs(w, ex - 64, ey + 160, ex + 64, ey + 900, zp, zp + 480, "-y")
    for sx in (-72, 64):
        w.add(G.box(ex + sx, ey + 160, zp + 480, ex + sx + 8, ey + 260, zp + 520, M.WOOD_BEAM))
    for sx in (-200, 200):
        K.flagpole(w, ex + sx, ey - 170, zp + 480, M.FLAG_MARINE, 300)
    w.marker("Echafaud de la place d'Oris", (ex, ey, zp + 480), "lieu")

    # ---------- QG de la Marine ----------------------------------------------
    hx0, hy0 = X - 896, Y + 1856
    info = K.building(w, hx0, hy0, Z, 1792, 640, floors=4, facade=M.WIN_MARINE, roof_kind="flat",
                      roof_mat=M.STONE_GREY, doors=(("-y", 0), ("-y", -4), ("-y", 4)), door_kind="arch",
                      door_w=192, door_h=200, levels=2, trim=M.WHITE, overhang=16,
                      light_color=(255, 240, 220))
    K.furnish(w, info, "office", 10)
    top = info["top"]
    # emblem "MARINE" au-dessus de l'entree
    w.add(G.box(X - 300, hy0 - 10, Z + 300, X + 300, hy0, Z + 600,
                {"-y": Mat(M.FLAG_MARINE, fit=True), "default": M.WHITE}))
    # tour centrale
    tx0, ty0 = X - 288, hy0 + 64
    K.block(w, tx0, ty0, top + 24, 576, 512, 5, M.WIN_MARINE, roof_kind="hip", roof_mat=M.ROOF_BLUE,
            overhang=64, roof_h=220)
    tz = top + 24 + 8 + 5 * 160
    w.add(G.box(X - 300, ty0 - 12, tz - 330, X + 300, ty0, tz - 30,
                {"-y": Mat(M.KANJI_MARINE, fit=True), "default": M.WHITE}))
    w.add(G.box(X - 300, ty0 + 512, tz - 330, X + 300, ty0 + 524, tz - 30,
                {"+y": Mat(M.KANJI_JUSTICE, fit=True), "default": M.WHITE}))
    # second niveau de toit + fleche
    w.add(G.box(X - 160, ty0 + 96, tz + 220, X + 160, ty0 + 416, tz + 380, Mat(M.WHITE)))
    K.roof(w, "hip", X - 220, ty0 + 36, X + 220, ty0 + 476, tz + 380, M.ROOF_BLUE, M.WHITE, h=180)
    w.add(G.frustum(X, ty0 + 256, 30, 0, tz + 540, tz + 900, 8, M.GOLD))
    # ailes : tours rondes
    for sx in (-1, 1):
        K.tower(w, X + sx * 1080, hy0 + 320, Z, 190, 980, 12, M.WHITE, M.ROOF_BLUE, 360, band=M.MARINE_BLUE)
        K.block(w, X + (sx < 0 and -1500 or 1100), hy0 + 120, Z, 400, 400, 3, M.WIN_MARINE, "hip",
                M.ROOF_BLUE)
    # bouton des murs de siege (dans le hall)
    bx, by = X - 300, hy0 + 560
    K.button_toggle(w, bx - 16, by - 8, Z + 50, bx + 16, by, Z + 82, "marineford_murs", M.RED)
    sg = M.sign_mat("murs", "MURS DE SIEGE", sub="Utiliser le bouton rouge")
    w.add(G.box(bx - 96, by, Z + 100, bx + 96, by + 6, Z + 148,
                {"-y": Mat(sg, fit=True), "default": M.WOOD_BEAM}))
    w.marker("QG de la Marine", (X, hy0 + 320, Z), "batiment")

    # drapeaux de la place
    for i in range(-3, 4):
        K.flagpole(w, X + i * 360, Y + 1720, zp, M.FLAG_MARINE, 380)
    for i in range(6):
        K.lamp(w, X - 1300 + i * 520, Y + 460, zp)

    # ---------- bras ouest : casernes & entrainement --------------------------
    for j, (bx0, by0) in enumerate(((-3200, -400), (-3200, -1000))):
        info = K.building(w, X + bx0, Y + by0, Z, 640, 384, floors=2, facade=M.WIN_MARINE,
                          roof_kind="gable", roof_mat=M.ROOF_BLUE, doors=(("+x", 0),),
                          sign=M.sign_mat(f"caserne{j}", f"CASERNE {j + 1}", sub="Marine"))
        K.furnish(w, info, "barracks", 20 + j)
    K.plaza(w, (X - 2400, Y - 1900, X - 1700, Y - 700), Z, M.DIRT)
    for k in range(4):
        w.prop(K.P_CRATE, (X - 2300 + k * 160, Y - 1850, Z + 26), k * 20)
    K.fence(w, X - 2400, Y - 1900, X - 1700, Y - 1900, Z)
    K.fence(w, X - 2400, Y - 700, X - 1700, Y - 700, Z)
    info = K.building(w, X - 3100, Y - 2200, Z, 384, 384, floors=1, facade=M.WIN_STONE, roof_kind="flat",
                      roof_mat=M.STONE_GREY, doors=(("+x", 0),), sign=M.sign_mat("armurerie_m", "ARSENAL"))
    K.furnish(w, info, "storage", 22)
    K.lighthouse(w, X - 2050, Y - 2600, Z)

    # ---------- bras est : hopital, cantine, residences -----------------------
    info = K.building(w, X + 2560, Y - 400, Z, 640, 384, floors=2, facade=M.WIN_WHITE, roof_kind="gable",
                      roof_mat=M.ROOF_RED, doors=(("-x", 0),),
                      sign=M.sign_mat("hopital", "HOPITAL", sub="Marine"))
    K.furnish(w, info, "house", 23)
    info = K.building(w, X + 2560, Y - 1100, Z, 640, 384, floors=1, facade=M.WIN_CREAM, roof_kind="gable",
                      roof_mat=M.ROOF_ORANGE, doors=(("-x", 0),),
                      sign=M.sign_mat("cantine", "CANTINE"))
    K.furnish(w, info, "restaurant", 24)
    for k, (lx, ly, fac) in enumerate(((1700, -2250, M.WIN_PINK), (2150, -2250, M.WIN_YELLOW))):
        info = K.building(w, X + lx, Y + ly, Z, 320, 256, floors=2, facade=fac, roof_kind="hip",
                          roof_mat=M.ROOF_RED, doors=(("+y", 0),), levels=1)
        K.furnish(w, info, "house", 25 + k)
    K.lighthouse(w, X + 2050, Y - 2600, Z)

    # ---------- quartier arriere (familles) ------------------------------------
    for i, (lx, ly, fac, rf) in enumerate(((-2300, 2650, M.WIN_CREAM, M.ROOF_RED),
                                           (-1700, 2900, M.WIN_BLUE, M.ROOF_ORANGE),
                                           (1500, 2900, M.WIN_PINK, M.ROOF_BLUE),
                                           (2100, 2650, M.WIN_YELLOW, M.ROOF_RED))):
        info = K.building(w, X + lx, Y + ly, Z, 384, 256, floors=2, facade=fac, roof_kind="gable",
                          roof_mat=rf, doors=(("-y", 0),), levels=1)
        K.furnish(w, info, "house", 30 + i)
    for i in range(8):
        K.round_tree(w, X - 2600 + i * 740, Y + 3250 - (i % 2) * 200, Z, 300, 130)

    # ---------- canons sur les quais de la baie --------------------------------
    for k in range(7):
        ly = -2300 + k * 380
        K.cannon(w, X - 1420, Y + ly, Z, 0)
        K.cannon(w, X + 1420, Y + ly, Z, 180)
    for k in range(8):
        K.cannon(w, X - 1300 + k * 370, Y + 430, Z, -90)

    # ---------- port militaire : quais bas + navires ----------------------------
    for sx in (-1, 1):
        K.dock(w, X + sx * 1250, Y - 1600, X + sx * 980, Y - 300, 24)
        K.water_steps(w, X + sx * 1250 + (0 if sx < 0 else -0), Y - 300, X + sx * 980, Y + 380, 24, Z,
                      "+y")
    K.ship(w, X - 600, Y - 1200, 90, 1200, "marine")
    K.ship(w, X + 600, Y - 1500, 90, 1200, "marine")
    K.ship(w, X, Y - 3600, 0, 1300, "marine")
    w.prop(K.P_CLEAT, (X - 1000, Y - 900, 24), 0)
    w.prop(K.P_CLEAT, (X + 1000, Y - 900, 24), 0)
    # rampes de sortie de l'eau a l'exterieur
    K.water_steps(w, X - 3800, Y - 900, X - 3600, Y - 600, -64, Z, "+x")
    K.water_steps(w, X + 3600, Y - 900, X + 3800, Y - 600, -64, Z, "-x")

    # ---------- murs de siege (sortent de la mer) -------------------------------
    segs = [(-1500, -2750, -500, -2690), (-500, -2780, 500, -2720), (500, -2750, 1500, -2690)]
    for i, (a0, b0, a1, b1) in enumerate(segs):
        b = G.box(X + a0, Y + b0, -980, X + a1, Y + b1, -60,
                  {"top": M.STONE_GREY, "default": M.WHITE})
        band = G.box(X + a0 - 4, Y + b0 - 4, -400, X + a1 + 4, Y + b1 + 4, -320, M.MARINE_BLUE)
        w.ent("func_door", brushes=[b, band], targetname="marineford_murs", movedir="-90 0 0",
              spawnflags=0, speed=70, wait=-1, lip=40, dmg=0, forceclosed=0,
              noise1="doors/default_move.wav", noise2="doors/default_stop.wav",
              rendercolor="255 255 255", renderamt=255, loopmovesound=1, spawnpos=0,
              origin=(X + (a0 + a1) / 2, Y + (b0 + b1) / 2, -520))
    w.marker("Murs de siege (bouton dans le QG)", (X, Y - 2740, 0), "lieu")

    # spawn Marine
    for i in range(8):
        w.ent("info_target", (X - 1300 + i * 90, Y + 1350, zp + 16), targetname="spawn_marine")
