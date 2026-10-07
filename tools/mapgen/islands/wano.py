"""Pays de Wano : chateau du shogun, torii, maisons japonaises, cerisiers, pagode."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "wano"
Z = 48
ZC = 560  # colline du chateau (le donjon domine la Capitale, comme dans l'anime)


def torii(w, x, y, z, yaw, wd=360, h=420):
    f = G.Frame(x, y, z, yaw)
    for s in (-1, 1):
        w.add(f.cyl((0, s * wd / 2, -10), (0, s * wd / 2 * 0.95, h), 18, 8, M.TORII))
        w.add(f.cyl((0, s * wd / 2, -10), (0, s * wd / 2, 30), 26, 8, M.BLACK))
    w.add(f.box(-16, -wd / 2 - 40, h - 70, 16, wd / 2 + 40, h - 40, M.TORII))
    w.add(f.hull([(-22, -wd / 2 - 90, h), (22, -wd / 2 - 90, h), (-22, wd / 2 + 90, h), (22, wd / 2 + 90, h),
                  (-24, -wd / 2 - 100, h + 34), (24, -wd / 2 - 100, h + 34), (-24, wd / 2 + 100, h + 34),
                  (24, wd / 2 + 100, h + 34)], {"top": M.BLACK, "default": M.TORII}))


def jp_roof(w, x0, y0, x1, y1, z, h, mat=M.ROOF_DARK, flare=48):
    """Toit japonais : avant-toit large + toit a croupe."""
    w.add(G.box(x0 - flare, y0 - flare, z, x1 + flare, y1 + flare, z + 10, {"default": M.WOOD_BEAM, "top": mat}))
    b = G.hip(x0 - flare * 0.6, y0 - flare * 0.6, x1 + flare * 0.6, y1 + flare * 0.6, z + 10, h, mat)
    b.retexture(lambda f: M.WOOD_BEAM if f.normal[2] < -0.5 else mat)
    w.add(b)


def machiya(w, x, y, sx, sy, seed, door="-y", sign=None, floors=2, kind="house"):
    info = K.building(w, x, y, Z, sx, sy, floors=floors, facade=M.JP_WALL, inner=M.PLANKS_LIGHT,
                      floor_mat=M.PLANKS_LIGHT, roof_kind="flat", roof_mat=M.ROOF_DARK, doors=((door, 0),),
                      trim=M.WOOD_BEAM, base=M.STONE_GREY, sign=sign, levels=1, overhang=0,
                      light_color=(255, 200, 150))
    jp_roof(w, x, y, x + sx, y + sy, info["top"] + 32, 110)   # pose sur le parapet du toit plat (il traversait le toit)
    K.furnish(w, info, kind, seed)
    return info


def sakura(w, x, y, z, s=1.0):
    w.add(G.cylinder((x, y, z - 16), (x + 20 * s, y, z + 180 * s), 16 * s, 6, M.WOOD_BEAM, r1=10 * s))
    w.add(G.frustum(x + 20 * s, y, 140 * s, 190 * s, z + 150 * s, z + 230 * s, 9, M.SAKURA))
    w.add(G.frustum(x + 20 * s, y, 190 * s, 80 * s, z + 230 * s, z + 330 * s, 9, M.SAKURA))


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=51, top=M.GRASS, beach=M.SAND, sides=20, jitter=0.08)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # ---------- colline du chateau (remparts en pierre inclines) ---------------
    hx, hy = X + 200, Y + 900
    w.add(G.frustum(hx, hy, 1150, 900, Z - 8, ZC, 20, {"top": M.GRASS_DARK, "default": M.STONE_GREY}, rot=15))
    K.stairs(w, hx - 128, hy - 1130 - 740, hx + 128, hy - 1000 + 120, Z, ZC + 2, "+y")
    w.add(G.box(hx - 560, hy - 400, ZC, hx + 560, hy + 560, ZC + 6, {"top": M.PAVING, "default": M.STONE_GREY}))
    # tenshu : 4 etages degressifs
    sizes = [(640, 512, 200), (512, 400, 180), (400, 300, 170), (288, 224, 160)]
    z = ZC
    info = None
    for i, (sx, sy, hh) in enumerate(sizes):
        x0, y0 = hx - sx / 2, hy + 80 - sy / 2
        if i == 0:
            info = K.building(w, x0, y0, z, sx, sy, floors=1, fh=hh, facade=M.JP_WALL, inner=M.PLANKS_LIGHT,
                              floor_mat=M.PLANKS_LIGHT, roof_kind="flat", roof_mat=M.ROOF_DARK,
                              doors=(("-y", 0),), door_kind="arch", door_w=128, door_h=150, levels=1,
                              trim=M.WOOD_BEAM, overhang=0, light_color=(255, 210, 160))
            K.furnish(w, info, "office", 100)
            z = info["top"] + 32   # avant-toit pose sur le parapet du toit plat (il percait le toit vert)
        else:
            w.add(G.box(x0, y0, z, x0 + sx, y0 + sy, z + hh,
                        {"default": Mat(M.JP_WALL, origin=(x0, y0, z + hh), scale=(128, hh)), "top": M.WOOD_BEAM}))
            z += hh
        jp_roof(w, x0, y0, x0 + sx, y0 + sy, z, 70 if i < 3 else 150, M.ROOF_GREEN, flare=80 - i * 8)
        z += 10 + (20 if i < 3 else 0)   # etage suivant enfonce dans le toit (avant +40 : 12-16 u de vide dessous)
    # shachihoko dans l'axe du faitage (avant : en travers, les bouts 42 u au-dessus des pans)
    w.add(G.box(hx - 40, hy + 80 - 16, z + 120, hx + 40, hy + 80 + 16, z + 170, M.GOLD))
    # enseigne plaquee sur le 2e etage et posee sur le 1er toit (avant : flottait 31 u au-dessus, 56 u devant le mur)
    w.add(G.box(hx - 240, hy + 80 - 206, ZC + 280, hx + 240, hy + 80 - 200, ZC + 440,
                {"-y": Mat(M.KANJI_WANO, fit=True), "default": M.WOOD_BEAM}))
    for s in (-1, 1):
        K.tower(w, hx + s * 560, hy - 360, ZC, 80, 260, 8, M.WHITE, M.ROOF_GREEN, 120, base=M.STONE_GREY)
    w.marker("Chateau du Shogun (Capitale des Fleurs)", (hx, hy, ZC), "batiment")
    # cerisiers hors des avant-toits du donjon et plus devant sa porte (avant : 6 couronnes dans le 1er toit)
    for dx, dy in ((-250, 620), (250, 620), (-640, 150), (620, 150)):
        sakura(w, hx + dx, hy + dy, ZC + 6, 0.9)

    # ---------- allee des torii -----------------------------------------------
    K.road(w, hx, Y - 2160, hx, hy - 1900, Z, 224, M.PAVING)   # avant Y-2300 : bout de dalle 13-17 u au-dessus du sable
    for k in range(4):
        torii(w, hx, Y - 2100 + k * 420, Z + 6, 90)
    w.marker("Allee des torii", (hx, Y - 1500, Z), "lieu")

    # ---------- quartier de machiya -------------------------------------------
    rows = [(-1000, -600), (-1900, -1150), (-1900, -600), (-1900, -50), (-1000, -1700), (-1000, -1150),
            (900, -1700), (900, -1150), (1600, -1700), (1600, -1150), (1600, -600), (1600, -50)]
    signs = {1: ("izakaya", "IZAKAYA", "bar"), 4: ("dojo", "DOJO", "storage"),
             7: ("forgeron", "FORGERON", "shop"), 9: ("ryokan", "RYOKAN", "house")}
    for i, (lx, ly) in enumerate(rows):
        door = "+x" if lx < 0 else "-x"
        sg = signs.get(i)
        machiya(w, X + lx, Y + ly, 384, 320, 101 + i, door,
                sign=M.sign_mat(sg[0], sg[1], board=(60, 40, 30), color=(250, 230, 200)) if sg else None,
                kind=sg[2] if sg else "house")
    # colonne gauche ecartee des machiya ; plus d'arbre dans le rempart (Y+20) ni sur la capitainerie (Y-1900)
    for i in range(2, 8):
        sakura(w, X - 450 + (i % 2) * 1050 + (i // 2) * 30, Y - 1900 + (i // 2) * 480, Z)

    # ---------- pagode a 5 etages ----------------------------------------------
    gx, gy = X - 1500, Y + 1300
    z = Z
    for i in range(5):
        s = 300 - i * 40
        w.add(G.box(gx - s / 2, gy - s / 2, z, gx + s / 2, gy + s / 2, z + 110,
                    {"default": Mat(M.PLANKS_RED, scale=(128, 128)), "top": M.WOOD_BEAM}))
        z += 110
        jp_roof(w, gx - s / 2, gy - s / 2, gx + s / 2, gy + s / 2, z, 40, M.ROOF_DARK, 70)
        z += 22   # etage suivant enfonce dans le toit (avant +50 : pose sur la pointe, 21-27 u de vide autour)
    w.add(G.prism(gx, gy, 10, 8, z, z + 260, M.GOLD))
    w.marker("Pagode", (gx, gy, Z), "lieu")

    # ---------- port ----------------------------------------------------------
    ax, ay, _, _ = L.arrival_point(KEY)
    a = math.atan2(ay - Y, ax - X)
    f = G.Frame(X + math.cos(a) * R * 0.68, Y + math.sin(a) * R * 0.68, 0, math.degrees(a))
    w.add(f.box(0, -110, Z - 12, 1100, 110, Z + 3, {"top": M.PLANKS_DARK, "default": M.WOOD_BEAM}))
    for d in (420, 760, 1080):          # pieux jusqu'au fond (le ponton flottait sans appui)
        for s in (-1, 1):
            w.add(G.prism(*f.p(d, s * 96)[:2], 10, 6, -760, Z - 12, M.WOOD_BEAM))
    # torii EN TRAVERS du ponton, a son entree sur la terre ferme (avant : dans l'axe du ponton,
    # un poteau au milieu du passage)
    torii(w, *f.p(0, 0)[:2], Z, math.degrees(a), 300, 380)
    K.ship(w, *f.p(1000, 380)[:2], math.degrees(a), 950, "red")   # a flot (avant : poupe echouee sur la plage)
    # 65/200/245/335 deg retires : tronc dans le ryokan, couronnes dans 3 machiya et dans le rempart
    for i in (0, 2, 3, 6):
        a2 = math.radians(i * 45 + 20)
        sakura(w, X + math.cos(a2) * R * 0.62, Y + math.sin(a2) * R * 0.62, Z, 1.2)
    K.env_cubemap(w, X, Y - 1000, Z + 150)
