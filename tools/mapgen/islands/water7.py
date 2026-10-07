"""Water Seven : cite de l'eau, canaux, grande fontaine, Galley-La, Dock 1."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "water7"
Z = 48
FACADES = [M.WIN_BLUE, M.WIN_CREAM, M.WIN_TERRA, M.WIN_WHITE, M.WIN_YELLOW, M.WIN_PINK]
ROOFS = [M.ROOF_ORANGE, M.ROOF_RED, M.ROOF_BLUE, M.ROOF_TEAL]


def sector_poly(cx, cy, r0, r1, a0, a1, n=4):
    pts = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((cx + math.cos(a) * r1, cy + math.sin(a) * r1))
    for a in (a1, a0):
        aa = math.radians(a)
        pts.append((cx + math.cos(aa) * r0, cy + math.sin(aa) * r0))
    return G.convex_hull_2d(pts)


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    # socle immerge (fond des canaux a -128)
    base = G.blob(X, Y, R, R, 22, 81, 0.04)
    w.add(G.poly_frustum(base, G.scale_poly(base, X, Y, 0.78), -768, -128, M.SAND))
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in base]

    # paliers centraux
    hub = G.ngon(X, Y, 1250, 14)
    K.quay_terrain(w, hub, Z, top=M.PAVING, side=M.STONE, flare=1.02)
    w.add(G.frustum(X, Y, 800, 760, Z, 260, 14, {"top": M.PAVING, "default": M.STONE}))
    # sommet de la ville plus haut (560 au lieu de 480) : silhouette en paliers vers la fontaine
    w.add(G.frustum(X, Y, 420, 390, 260, 560, 14, {"top": M.MARBLE, "default": M.STONE}))
    K.stairs(w, X - 96, Y - 1240, X + 96, Y - 760, Z, 260, "+y")
    K.stairs(w, X - 80, Y - 760, X + 80, Y - 390, 260, 560, "+y")

    # grande fontaine (la colonne de marbre, entierement cachee dans la colonne d'eau opaque, est retiree)
    for zb, rb in ((560, 360), (900, 260), (1200, 200)):
        w.add(G.frustum(X, Y, rb * 0.7, rb, zb, zb + 60, 16, {"top": M.WATERFALL, "default": M.MARBLE}))
    w.add(G.prism(X, Y, 150, 16, 620, 1430, M.WATERFALL))
    w.add(G.frustum(X, Y, 150, 330, 1430, 1580, 16, M.WATERFALL))
    w.add(G.frustum(X, Y, 330, 120, 1580, 1660, 16, M.WATERFALL))
    w.light((X, Y, 1680), (200, 240, 255), 1200, fifty=500, zero=1600)
    w.marker("Grande fontaine de Water Seven", (X, Y, 560), "lieu")

    # Galley-La Company
    info = K.building(w, X - 224, Y + 880, Z, 448, 288, floors=3, facade=M.WIN_BLUE, roof_kind="gable",
                      roof_mat=M.ROOF_BLUE, doors=(("-x", 0),), levels=2,
                      sign=M.sign_mat("galleyla", "GALLEY-LA COMPANY", sub="Iceburg"))
    K.furnish(w, info, "office", 170)
    w.marker("Galley-La Company", (X, Y + 1020, Z), "batiment")
    for i in range(6):
        # au bord du quai, face aux canaux radiaux (avant : dans l'axe de chaque pont, et a 270 deg
        # au milieu de l'escalier sud, pied enterre de 40 u dans la rampe)
        a = math.radians(i * 60)
        K.lamp(w, X + math.cos(a) * 1150, Y + math.sin(a) * 1150, Z)

    # quartiers peripheriques separes par des canaux
    secs = []
    for k in range(6):
        a0 = k * 60 + 6
        a1 = (k + 1) * 60 - 6
        poly = sector_poly(X, Y, 1460, 2560, a0, a1)
        K.quay_terrain(w, poly, Z, top=M.COBBLE, side=M.STONE, flare=1.02)
        secs.append((a0, a1))
        # pont vers le centre
        am = math.radians((a0 + a1) / 2)
        # quartier nord : pont decale de 20 deg (avant : il butait contre le dos de Galley-La)
        f = G.Frame(X, Y, 0, (a0 + a1) / 2 + (20 if k == 1 else 0))
        w.add(f.box(1180, -80, Z - 14, 1530, 80, Z + 3, {"top": M.PLANKS, "default": M.STONE}))
        for s in (-80, 72):
            w.add(f.box(1240, s, Z, 1470, s + 8, Z + 40, M.STONE))
        # pont entre quartiers
        g = G.Frame(X, Y, 0, a1 + 6)
        # le canal fait ~400-430 u de large ici (2 x r.tan6) : +-250 pour poser sur les deux quais
        w.add(g.box(1900, -250, Z - 14, 2060, 250, Z + 3, {"top": M.PLANKS, "default": M.STONE}))
        # batiments venitiens
        for j, (rr, da, bw, bd) in enumerate(((1700, -13, 256, 256), (1700, 13, 256, 256),
                                               (2180, -14, 320, 256), (2180, 14, 320, 256))):
            ang = (a0 + a1) / 2 + da
            bx = X + math.cos(math.radians(ang)) * rr
            by = Y + math.sin(math.radians(ang)) * rr
            idx = k * 4 + j
            if j < 2:
                door = "-x" if math.cos(math.radians(ang)) > 0.3 else ("+x" if math.cos(math.radians(ang)) < -0.3 else
                                                                      ("-y" if math.sin(math.radians(ang)) > 0 else "+y"))
                info = K.building(w, bx - bw / 2, by - bd / 2, Z, bw, bd, floors=2 + idx % 2,
                                  facade=FACADES[idx % len(FACADES)], roof_kind="hip",
                                  roof_mat=ROOFS[idx % len(ROOFS)], doors=((door, 0),), levels=1)
                K.furnish(w, info, "house", 171 + idx)
            else:
                K.block(w, bx - bw / 2, by - bd / 2, Z, bw, bd, 3 + idx % 2, FACADES[(idx + 2) % len(FACADES)],
                        "hip", ROOFS[(idx + 1) % len(ROOFS)])

    # Dock 1 (chantier naval) cote ouest
    dx, dy = X - 2950, Y - 200
    # plancher elargi cote -y : le pied de la grue (dy-760..dy-720) etait pose dans le vide
    w.add(G.box(dx - 300, dy - 800, Z - 12, dx + 700, dy + 700, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.STONE}))
    for i in range(5):
        for s in (-1, 1):
            w.add(G.box(dx - 280 + i * 220, dy + s * 600 - 16, Z, dx - 248 + i * 220, dy + s * 600 + 16, Z + 600,
                        M.IRON))
    w.add(G.box(dx - 320, dy - 660, Z + 600, dx + 640, dy + 660, Z + 640, {"default": M.METAL}))
    w.add(G.gable(dx - 340, dy - 680, dx + 660, dy + 680, Z + 640, 180, "x", M.ROOF_BLUE))
    sg = M.sign_mat("dock1", "DOCK 1", sub="Galley-La Company")
    w.add(G.box(dx - 340, dy - 200, Z + 560, dx - 330, dy + 200, Z + 660,
                {"-x": Mat(sg, fit=True), "default": M.WOOD_BEAM}))
    # navire en construction pose sur le plancher (quille a Z-3) ; mats (Z+60+0.695L) sous le plafond Z+600
    K.ship(w, dx + 100, dy, 180, 700, "pirate", z=Z + 60)
    # grue
    w.add(G.box(dx + 400, dy - 760, Z, dx + 440, dy - 720, Z + 900, M.IRON))
    w.add(G.box(dx + 100, dy - 760, Z + 900, dx + 700, dy - 720, Z + 940, M.IRON))
    w.marker("Dock 1 (chantier naval)", (dx, dy, Z), "lieu")

    # Franky House
    fx, fy = X - 1500, Y - 2500
    w.add(G.box(fx - 300, fy - 300, -128, fx + 300, fy + 300, Z + 3, {"top": M.PLANKS, "default": M.STONE}))
    info = K.building(w, fx - 192, fy - 128, Z, 384, 256, floors=2, facade=M.WIN_WOOD, roof_kind="flat",
                      roof_mat=M.PLANKS, doors=(("+y", 0),), sign=M.sign_mat("franky", "FRANKY HOUSE"),
                      levels=1)
    K.furnish(w, info, "storage", 190)

    # gare du Puffing Tom
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    a += math.radians(-55)
    f = G.Frame(X + math.cos(a) * 2560, Y + math.sin(a) * 2560, 0, math.degrees(a))
    # quai de gare plein jusqu'au fond (avant : dalle de 15 u posee sur une langue de terrain artificielle)
    w.add(f.box(-60, -220, -768, 900, 220, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.STONE}))
    for s in (-40, 40):
        w.add(f.box(-60, s - 4, Z, 2600, s + 4, Z + 8, M.IRON))
    for k in range(6):
        w.add(f.box(900 + k * 280, -70, -768, 940 + k * 280, 70, Z - 12, M.STONE))
    w.add(f.box(900, -70, Z - 12, 2600, 70, Z, M.PLANKS_DARK))
    w.marker("Gare du Puffing Tom", f.p(300, 0, Z), "lieu")
    K.ship(w, *f.p(500, 600)[:2], math.degrees(a), 900, "pirate")
    sg = M.sign_mat("w7", "WATER SEVEN", sub="La cite de l'eau")
    w.add(f.box(-80, -160, Z, -64, 160, Z + 130, {"+x": Mat(sg, fit=True), "-x": Mat(sg, fit=True),
                                                  "default": M.WOOD_BEAM}))
    K.env_cubemap(w, X, Y - 1000, Z + 128)
