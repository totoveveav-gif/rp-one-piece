"""Enies Lobby : ile judiciaire, tribunal, Tour de la Justice, Portes de la Justice."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "enies"
ZP = 320  # hauteur du plateau


def gates_of_justice(w, x, y, yaw):
    """Les Portes de la Justice : portail geant vers Impel Down."""
    f = G.Frame(x, y, 0, yaw)
    W = 1100
    for s in (-1, 1):
        # piliers colossaux
        w.add(f.box(-220, s * (W / 2) - (0 if s > 0 else 360), -768, 220, s * (W / 2) + (360 if s > 0 else 0), 1500,
                    {"top": M.STONE_GREY, "default": M.STONE}))
        w.add(f.box(-250, s * (W / 2) - (0 if s > 0 else 390), 1500, 250,
                    s * (W / 2) + (390 if s > 0 else 0), 1580, M.MARINE_BLUE))
        # battants entrouverts
        # battant ouvert a 35 degres depuis sa charniere
        a = math.radians(-s * 35)
        L_ = W / 2
        p0 = (0, s * W / 2)
        p1 = (-math.sin(a) * L_, s * W / 2 - s * math.cos(a) * L_)
        pts = []
        for (px, py) in (p0, p1):
            for dz in (0, 1400):
                for t in (-30, 30):
                    pts.append((px + t, py, dz))
        w.add(f.hull(pts, {"default": M.IRON, "top": M.STONE_GREY}))
    # linteau avec le symbole du Gouvernement Mondial
    w.add(f.box(-240, -W / 2 - 360, 1580, 240, W / 2 + 360, 1700, {"default": M.STONE_GREY}))
    sm = M.sign_mat("justice", "PORTES DE LA JUSTICE", sub="→ IMPEL DOWN", color=(255, 236, 170))
    w.add(f.box(-250, -420, 1250, -240, 420, 1450, {"-x": Mat(sm, fit=True), "default": M.STONE_GREY}))
    w.add(f.box(240, -420, 1250, 250, 420, 1450, {"+x": Mat(sm, fit=True), "default": M.STONE_GREY}))
    memb = f.box(-3, -W / 2 + 40, -64, 3, W / 2 - 40, 1100,
                 {"+x": Mat(M.PORTAL, fit=True), "-x": Mat(M.PORTAL, fit=True), "default": M.NODRAW})
    w.ent("func_illusionary", brushes=memb, rendermode=0, renderamt=255, disableshadows=1)
    K.gate_triggers(w, f.box(-48, -W / 2 + 40, -560, 48, W / 2 - 40, 1100, M.TRIGGER), "enies_impel")
    w.light(f.p(0, 0, 500), (140, 220, 255), 3000, fifty=700, zero=2500)


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly = G.blob(X, Y, R, R * 0.9, 18, 21, 0.06)
    # base : plage basse + falaise jusqu'au plateau
    low = L.terrain(w, poly, X, Y, 32, top=M.SAND, beach=M.SAND)
    cliff = G.blob(X, Y + 150, R * 0.6, R * 0.52, 32, 22, 0.05)
    w.add(G.poly_frustum(G.scale_poly(cliff, X, Y + 150, 1.08), cliff, 0, ZP, {"top": M.GRASS, "default": M.ROCK}))
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # cascades sur les falaises
    for ang in (200, 330):
        a = math.radians(ang)
        cx, cy = X + math.cos(a) * R * 0.62, Y + 150 + math.sin(a) * R * 0.54
        f = G.Frame(cx, cy, 0, ang)
        w.add(f.box(-10, -150, 20, 30, 150, ZP + 10, {"+x": M.WATERFALL, "default": M.WATERFALL}))
        w.add(f.box(-60, -200, 30, 160, 200, 40, M.WATERFALL))

    # porte principale au niveau du quai + grand escalier
    gx, gy = X - 300, Y - R * 0.52 - 40
    K.dock(w, gx - 240, gy - 900, gx + 240, gy - 260, 32)
    for sx in (-340, 180):
        K.block(w, gx + sx, gy - 260, 32, 160, 200, 4, M.WIN_STONE, "flat", M.STONE_GREY)
    w.add(G.box(gx - 180, gy - 260, 32 + 8 + 520, gx + 180, gy - 60, 32 + 8 + 640, M.STONE_GREY))
    mg = M.sign_mat("enies", "ENIES LOBBY", sub="Ile judiciaire")
    w.add(G.box(gx - 170, gy - 268, 32 + 540, gx + 170, gy - 260, 32 + 620,
                {"-y": Mat(mg, fit=True), "default": M.STONE_GREY}))
    K.stairs(w, gx - 128, gy - 260, gx + 128, gy + 520, 32, ZP + 6, "+y")
    w.marker("Porte principale d'Enies Lobby", (gx, gy - 260, 32), "lieu")

    # ville avant
    for i, (lx, ly, fac, rf) in enumerate(((-1100, -300, M.WIN_STONE, M.ROOF_BLUE), (-1150, 150, M.WIN_WHITE, M.ROOF_BLUE),
                                           (500, -350, M.WIN_CREAM, M.ROOF_DARK), (550, 100, M.WIN_WHITE, M.ROOF_BLUE))):
        info = K.building(w, X + lx, Y + ly, ZP, 384, 256, floors=2, facade=fac, roof_kind="gable",
                          roof_mat=rf, doors=(("+x" if lx < 0 else "-x", 0),), levels=1)
        K.furnish(w, info, "barracks" if i % 2 else "office", 40 + i)
    K.plaza(w, (X - 600, Y - 500, X + 400, Y + 500), ZP, M.PAVING)

    # tribunal (temple a colonnes)
    tx, ty = X - 100, Y + 600
    w.add(G.box(tx - 520, ty - 80, ZP, tx + 520, ty + 640, ZP + 48, {"top": M.MARBLE, "default": M.STONE}))
    K.stairs(w, tx - 320, ty - 240, tx + 320, ty - 80, ZP, ZP + 48, "+y", M.STAIRS)
    info = K.building(w, tx - 448, ty + 80, ZP + 48, 896, 512, floors=2, facade=M.WIN_WHITE, roof_kind="flat",
                      roof_mat=M.STONE_GREY, doors=(("-y", 0),), door_kind="arch", door_w=160, door_h=200,
                      levels=1, trim=M.MARBLE, light_color=(255, 245, 230))
    K.furnish(w, info, "office", 45)
    for i in range(8):
        cx = tx - 455 + i * 130
        w.add(G.prism(cx, ty - 20, 26, 10, ZP + 48, ZP + 48 + 340, M.MARBLE))
    w.add(G.box(tx - 500, ty - 70, ZP + 388, tx + 500, ty + 80, ZP + 416, M.MARBLE))
    K.roof(w, "gable", tx - 520, ty - 90, tx + 520, ty + 600, ZP + 420, M.ROOF_BLUE, M.MARBLE, h=150, axis="y")
    w.marker("Tribunal d'Enies Lobby", (tx, ty, ZP), "batiment")

    # pont de l'hesitation + Tour de la Justice
    k0x, k0y = X - 100, Y + 1700
    w.add(G.frustum(k0x, k0y, 520, 380, -768, ZP + 4, 10, {"top": M.PAVING, "default": M.ROCK}))
    w.add(G.box(k0x - 64, ty + 600, ZP - 24, k0x + 64, k0y - 360, ZP + 6, {"top": M.PLANKS, "default": M.WOOD_BEAM}))
    for s in (-64, 56):
        w.add(G.box(k0x + s, ty + 600, ZP + 6, k0x + s + 8, k0y - 360, ZP + 46, M.WOOD_BEAM))
    info = K.building(w, k0x - 192, k0y - 192, ZP, 384, 384, floors=9, facade=M.WIN_WHITE, roof_kind="hip",
                      roof_mat=M.ROOF_BLUE, roof_h=360, doors=(("-y", 0),), levels=2, overhang=40)
    K.furnish(w, info, "office", 46)
    for s in (-1, 1):
        K.tower(w, k0x + s * 230, k0y + 140, ZP, 70, 1100, 10, M.WHITE, M.ROOF_BLUE, 200)
    w.marker("Tour de la Justice", (k0x, k0y, ZP), "batiment")

    # palmiers, lampadaires, drapeaux
    for i in range(10):
        a = math.radians(i * 36 + 10)
        K.palm(w, X + math.cos(a) * R * 0.75, Y + math.sin(a) * R * 0.66, 32, 340, seed=100 + i)
    for i in range(4):
        K.flagpole(w, X - 500 + i * 300, Y - 480, ZP + 6, M.FLAG_MARINE, 320)
    K.env_cubemap(w, X, Y, ZP + 140)

    # Portes de la Justice (vers Impel Down, au niveau 3)
    gjx, gjy = X + 400, Y + 3300
    gates_of_justice(w, gjx, gjy, 90)
    w.marker("Portes de la Justice -> Impel Down", (gjx, gjy, 0), "portail")
