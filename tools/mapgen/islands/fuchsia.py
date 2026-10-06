"""Village de Fuchsia (East Blue) : moulin, bar de Makino, mont Corvo."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "fuchsia"
Z = 48


def windmill(w, x, y, z):
    w.add(G.frustum(x, y, 150, 110, z, z + 520, 8, {"default": M.WHITE, "top": M.WOOD_BEAM}))
    w.add(G.frustum(x, y, 140, 0, z + 520, z + 700, 8, M.ROOF_THATCH))
    w.add(G.box(x - 28, y - 152, z + 8, x + 28, y - 140, z + 128, {"-y": Mat(M.DOOR, fit=True), "default": M.WOOD_BEAM}))
    hub = (x, y - 170, z + 520)
    parts = [G.cylinder((x, y - 120, z + 520), (x, y - 200, z + 520), 22, 8, M.WOOD_BEAM)]
    for i in range(4):
        a = math.radians(i * 90 + 20)
        d = (math.cos(a), math.sin(a))
        p0 = (hub[0] + d[0] * 30, hub[1], hub[2] + d[1] * 30)
        p1 = (hub[0] + d[0] * 440, hub[1], hub[2] + d[1] * 440)
        parts.append(G.cylinder(p0, p1, 8, 6, M.WOOD_BEAM))
        # toile de la pale
        q = (-d[1], d[0])
        pts = []
        for t in (0.25, 0.97):
            for wdt in (6, 70):
                pts.append((hub[0] + d[0] * 440 * t + q[0] * wdt, hub[1] - 4, hub[2] + d[1] * 440 * t + q[1] * wdt))
                pts.append((hub[0] + d[0] * 440 * t + q[0] * wdt, hub[1] + 4, hub[2] + d[1] * 440 * t + q[1] * wdt))
        parts.append(G.brush(pts, M.SAIL))
    w.ent("func_rotating", brushes=parts, origin=hub, spawnflags=1 | 8 | 64, maxspeed=20,
          fanfriction=20, volume=0, dmg=0, rendercolor="255 255 255", renderamt=255, angles="0 0 0")


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=71, top=M.GRASS, beach=M.SAND, sides=20, jitter=0.08)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # mont Corvo (au nord-ouest) + foret
    mx, my = X - 500, Y + 900
    w.add(G.frustum(mx, my, 1000, 520, Z - 8, Z + 420, 24, {"top": M.GRASS_DARK, "default": M.GRASS_DARK}, rot=7))
    w.add(G.boulder(mx - 150, my + 300, Z + 420, 420, 380, 360, 77, {"default": M.ROCK, "top": M.GRASS_DARK}, 30,
                    flat_bottom=Z + 400))
    for i in range(16):
        a = math.radians(i * 22.5)
        r = 760 + (i % 3) * 90
        K.round_tree(w, mx + math.cos(a) * r, my + math.sin(a) * r, Z, 360, 140, M.LEAVES)
    hut = K.building(w, mx - 128, my - 470, Z + 420, 256, 224, floors=1, facade=M.WIN_WOOD,
                     roof_kind="gable", roof_mat=M.ROOF_THATCH, doors=(("-y", 0),),
                     sign=M.sign_mat("dadan", "REPAIRE DE DADAN"))
    K.furnish(w, hut, "storage", 150)
    w.marker("Mont Corvo / repaire de Dadan", (mx, my, Z + 420), "lieu")
    K.stairs(w, mx - 64, my - 1000 - 300, mx + 64, my - 482, Z, Z + 426, "+y", M.STAIRS_WOOD, M.DIRT)

    # village
    vx, vy = X + 300, Y - 500
    K.plaza(w, (vx - 500, vy - 400, vx + 500, vy + 300), Z, M.DIRT)
    info = K.building(w, vx - 192, vy + 300, Z, 384, 320, floors=2, facade=M.WIN_WOOD, roof_kind="gable",
                      roof_mat=M.ROOF_RED, doors=(("-y", 0),),
                      sign=M.sign_mat("partys", "PARTY'S BAR", sub="Makino"), awning=M.AWN_RED)
    K.furnish(w, info, "bar", 151)
    w.marker("Party's Bar", (vx, vy + 460, Z), "batiment")
    houses = [(-900, -300, M.WIN_CREAM, M.ROOF_RED, "+x"), (-900, 100, M.WIN_WOOD, M.ROOF_THATCH, "+x"),
              (600, -350, M.WIN_YELLOW, M.ROOF_ORANGE, "-x"), (600, 50, M.WIN_WOOD, M.ROOF_THATCH, "-x"),
              (-300, -900, M.WIN_MINT, M.ROOF_RED, "+y"), (150, -900, M.WIN_PINK, M.ROOF_ORANGE, "+y")]
    for i, (lx, ly, fac, rf, d) in enumerate(houses):
        info = K.building(w, vx + lx, vy + ly, Z, 256, 256, floors=1 + (i % 2), facade=fac, roof_kind="gable",
                          roof_mat=rf, doors=((d, 0),), levels=1,
                          sign=M.sign_mat("maire", "MAIRIE") if i == 0 else None)
        K.furnish(w, info, "office" if i == 0 else "house", 152 + i)
    windmill(w, vx + 1100, vy + 500, Z)
    w.marker("Moulin", (vx + 1100, vy + 500, Z), "lieu")
    # champs
    for i in range(3):
        w.add(G.box(vx + 800, vy - 1100 + i * 260, Z - 8, vx + 1400, vy - 900 + i * 260, Z + 6,
                    {"top": [M.DIRT, M.GRASS_DARK, M.ROOF_THATCH][i], "default": M.DIRT}))
    for i in range(6):
        K.fence(w, vx + 780, vy - 1120 + i * 150, vx + 780, vy - 980 + i * 150, Z)

    # port
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    f = G.Frame(X + math.cos(a) * R * 0.68, Y + math.sin(a) * R * 0.68, 0, math.degrees(a))
    w.add(f.box(-100, -100, Z - 12, 900, 100, Z + 3, {"top": M.PLANKS_LIGHT, "default": M.WOOD_BEAM}))
    K.ship(w, *f.p(600, 420)[:2], math.degrees(a), 780, "merry")
    K.ship(w, *f.p(600, -420)[:2], math.degrees(a) + 180, 1050, "red")
    sm = M.sign_mat("fuchsia", "VILLAGE DE FUCHSIA", sub="East Blue")
    w.add(f.box(-120, -150, Z, -104, 150, Z + 120, {"+x": Mat(sm, fit=True), "-x": Mat(sm, fit=True),
                                                    "default": M.WOOD_BEAM}))
    K.env_cubemap(w, vx, vy, Z + 128)
    for i in range(10):
        w.ent("info_target", (vx - 300 + i * 60, vy - 200, Z + 16), targetname="spawn_pirate")
