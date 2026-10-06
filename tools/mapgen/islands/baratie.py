"""Baratie : le restaurant flottant en forme de poisson."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "baratie"


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    yaw = 30
    f = G.Frame(X, Y, 0, yaw)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(f.p(px, py)[:2]) for px, py in ((-900, -350), (900, -350), (1150, 0),
                                                                  (900, 350), (-900, 350), (-1100, 0))]
    DZ = 96  # pont principal
    hull = [(-950, -380), (700, -380), (1150, 0), (700, 380), (-950, 380), (-1100, 0)]
    bot = [(-850, -240), (650, -240), (1000, 0), (650, 240), (-850, 240), (-980, 0)]
    w.add(f.hull([(x, y, DZ) for x, y in hull] + [(x, y, -260) for x, y in bot],
                 {"top": M.PLANKS_LIGHT, "default": M.HULL_YELLOW}))
    # tete de poisson (proue)
    w.add(f.hull([(1100, -200, 40), (1100, 200, 40), (1100, -200, 380), (1100, 200, 380),
                  (1500, 0, 160), (1450, 0, 300)], {"default": M.HULL_YELLOW}))
    for s in (-1, 1):
        w.add(f.hull([(1280 + dx, s * 120 + dy, 260 + dz) for dx in (-40, 40) for dy in (-30, 30)
                      for dz in (-40, 40)], M.WHITE_PAINT))
        w.add(f.hull([(1300 + dx, s * 150 + dy, 260 + dz) for dx in (-20, 20) for dy in (-12, 12)
                      for dz in (-20, 20)], M.BLACK))
    # nageoires laterales (plateformes de combat)
    for s in (-1, 1):
        w.add(f.hull([(-500, s * 380, DZ - 20), (300, s * 380, DZ - 20), (-500, s * 380, DZ),
                      (300, s * 380, DZ), (-350, s * 900, DZ - 20), (100, s * 900, DZ - 20),
                      (-350, s * 900, DZ), (100, s * 900, DZ)], {"top": M.PLANKS, "default": M.HULL_YELLOW}))
    # queue
    w.add(f.hull([(-1100, 0, 60), (-1100, 0, 400), (-1450, -300, 600), (-1450, 300, 600),
                  (-1450, -300, -100), (-1450, 300, -100), (-1100, -40, 200), (-1100, 40, 200)],
                 M.HULL_YELLOW))
    # restaurant (2 etages)
    rx0, ry0 = f.p(-640, -288)[:2]
    # batiment axe-aligne dans le repere : on le construit en local via un Frame sans rotation
    g = G.Frame(X, Y, 0, yaw)
    sx, sy, H = 1024, 576, 360
    walls = {"default": Mat(M.WIN_TERRA), "top": M.WOOD_BEAM}
    inner = M.INTERIOR
    # murs (avec grande entree cote proue)
    x0, y0 = -640, -288
    x1, y1 = x0 + sx, y0 + sy
    t = 16
    for (a0, b0, a1, b1) in ((x0, y0, x1, y0 + t), (x0, y1 - t, x1, y1), (x0, y0 + t, x0 + t, y1 - t)):
        w.add(g.box(a0, b0, DZ, a1, b1, DZ + H, {"default": inner}))
    w.add(g.box(x1 - t, y0 + t, DZ, x1, -96, DZ + H, inner))
    w.add(g.box(x1 - t, 96, DZ, x1, y1 - t, DZ + H, inner))
    w.add(g.box(x1 - t, -96, DZ + 200, x1, 96, DZ + H, inner))
    # habillage exterieur (facade fenetres) en coques fines
    for (a0, b0, a1, b1) in ((x0 - 4, y0 - 4, x1 + 4, y0), (x0 - 4, y1, x1 + 4, y1 + 4), (x0 - 4, y0, x0, y1)):
        w.add(g.box(a0, b0, DZ, a1, b1, DZ + H, Mat(M.WIN_TERRA, origin=(0, 0, DZ + 160))))
    w.add(g.box(x0 - 32, y0 - 32, DZ + H, x1 + 32, y1 + 32, DZ + H + 12, {"default": M.WOOD_BEAM, "bottom": inner}))
    w.add(g.hull([(x0 - 40, y0 - 40, DZ + H + 12), (x1 + 40, y0 - 40, DZ + H + 12), (x0 - 40, y1 + 40, DZ + H + 12),
                  (x1 + 40, y1 + 40, DZ + H + 12), (x0 + 200, 0, DZ + H + 220), (x1 - 200, 0, DZ + H + 220)],
                 {"default": M.ROOF_TEAL, "bottom": M.WOOD_BEAM}))
    sm = M.sign_mat("baratie", "BARATIE", sub="Restaurant flottant", color=(255, 240, 200), board=(150, 40, 40))
    w.add(g.box(x1 + 4, -200, DZ + 220, x1 + 12, 200, DZ + 320, {"+x": Mat(sm, fit=True), "default": M.WOOD_BEAM}))
    # interieur : tables + comptoir
    for i in range(4):
        for j in (-1, 1):
            w.prop(K.P_TABLE, g.p(-520 + i * 220, j * 150, DZ + 18), 0)
            w.prop(K.P_CHAIR, g.p(-560 + i * 220, j * 150, DZ + 20), yaw)
            w.prop(K.P_CHAIR, g.p(-480 + i * 220, j * 150, DZ + 20), yaw + 180)
    w.add(g.box(-620, -260, DZ, -560, 120, DZ + 44, {"top": M.PLANKS, "default": M.PLANKS_DARK}))
    w.prop(K.P_STOVE, g.p(-600, 200, DZ + 20), yaw)
    for p in ((-300, 0), (100, 0)):
        w.light(g.p(p[0], p[1], DZ + H - 40), (255, 214, 170), 420)
    # mats & drapeaux
    for mx in (-860, 520):
        w.add(g.cyl((mx, 0, DZ), (mx, 0, DZ + 900), 12, 6, M.WOOD_BEAM, r1=8))
        w.add(g.box(mx - 2, 0, DZ + 760, mx + 2, 160, DZ + 880,
                    {"+x": Mat(M.FLAG_SH, fit=True), "-x": Mat(M.FLAG_SH, fit=True), "default": M.SAIL}))
    # escaliers depuis l'eau (nageurs)
    for s in (-1, 1):
        w.add(g.ramp(-200, s * 900, -64, 0, s * 1100, DZ - 20, "-y" if s > 0 else "+y",
                     {"top": Mat(M.STAIRS_WOOD, scale=(128, 400)), "default": M.WOOD_BEAM}))
    w.marker("Restaurant Baratie", (X, Y, DZ), "batiment")
    K.env_cubemap(w, *g.p(0, 0, DZ + 120))
