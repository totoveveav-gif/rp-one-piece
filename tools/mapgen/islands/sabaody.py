"""Archipel de Sabaody : carrefour, mangroves geantes, bulles, grande roue."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "sabaody"


def ferris_wheel(w, cx, cy, hub_z, r=420):
    # supports fixes (A de chaque cote)
    for sy in (-70, 70):
        for sx in (-1, 1):
            w.add(G.cylinder((cx + sx * 300, cy + sy, 54), (cx, cy + sy, hub_z), 14, 6, M.WHITE_PAINT))
    w.add(G.cylinder((cx, cy - 90, hub_z), (cx, cy + 90, hub_z), 22, 8, M.GOLD))
    # roue tournante
    parts = []
    n = 16
    rim = [(cx + r * math.cos(2 * math.pi * i / n), cy, hub_z + r * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    for i in range(n):
        parts.append(G.cylinder(rim[i], rim[(i + 1) % n], 9, 6, M.paint_cycle(i)))
    for i in range(0, n, 2):
        parts.append(G.cylinder((cx, cy, hub_z), rim[i], 5, 6, M.WHITE_PAINT))
    for i in range(1, n, 2):
        x, _, z = rim[i]
        mat = [M.PLASTER_CABINS[i // 2 % len(M.PLASTER_CABINS)]][0]
        parts.append(G.prism(x, cy, 34, 8, z - 34, z + 34, mat, rot=22.5))
    parts.append(G.cylinder((cx, cy - 40, hub_z), (cx, cy + 40, hub_z), 30, 8, M.GOLD))
    w.ent("func_rotating", brushes=parts, origin=(cx, cy, hub_z), spawnflags=1 | 8 | 64,
          maxspeed=6, fanfriction=20, volume=0, dmg=0, solidbsp=0, rendercolor="255 255 255",
          renderamt=255, angles="0 0 0")
    w.light((cx, cy - 200, hub_z), (255, 200, 240), 600, fifty=300, zero=900)


def build(w):
    name, cx, cy, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=11, top=M.GRASS, sides=24, jitter=0.06)
    w.marker(name, (cx, cy, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]
    z = L.LAND_Z
    # le contenu est dessine autour de (0, 0) puis deplace sur l'ile
    with w.shift(cx, cy):

        # place centrale + carte du monde
        top = K.plaza(w, G.ngon(0, 0, 720, 8, 22.5), z, M.PAVING)
        w.add(G.box(-200, -8, top, 200, 8, top + 16, M.WOOD_BEAM))
        w.add(G.box(-200, -6, top + 16, 200, 6, top + 316,
                    {"+y": Mat(M.WORLD_MAP, fit=True), "-y": Mat(M.WORLD_MAP, fit=True), "default": M.WOOD_BEAM}))
        for sx in (-216, 200):
            w.add(G.box(sx, -12, top, sx + 16, 12, top + 360, M.WOOD_BEAM))
        w.add(G.box(-240, -24, top + 340, 240, 24, top + 360, M.ROOF_TEAL))
        sm = M.sign_mat("sabaody", "ARCHIPEL DE SABAODY", sub="Carrefour de la Grand Line")
        w.add(G.box(-160, -10, top + 362, 160, 10, top + 422,
                    {"+y": Mat(sm, fit=True), "-y": Mat(sm, fit=True), "default": M.WOOD_BEAM}))
        for a in range(8):
            ang = math.radians(a * 45 + 22.5)
            K.lamp(w, math.cos(ang) * 650, math.sin(ang) * 650, top)
        for a in range(4):
            ang = math.radians(a * 90 + 45)
            w.prop(K.P_BENCH, (math.cos(ang) * 520, math.sin(ang) * 520, top + 2), (a * 90 + 45 + 90) % 360)
        K.env_cubemap(w, 0, -400, top + 128)

        # routes
        K.road(w, 0, -700, 0, -2250, z)
        K.road(w, 700, 0, 2000, 0, z)
        K.road(w, -700, 0, -2000, 0, z)
        K.road(w, 0, 700, 0, 1150, z, 160)
        for i, y in enumerate(range(-900, -2100, -300)):
            K.lamp(w, 150, y, z + 6)
            K.lamp(w, -150, y - 150, z + 6)

        # mangroves geantes
        for ang, num in ((40, 1), (140, 13), (225, 24), (315, 41)):
            a = math.radians(ang)
            K.mangrove(w, math.cos(a) * 1950, math.sin(a) * 1950, z, r=170, h=1300, canopy=720,
                       grove=num, face_yaw=ang + 180)
        K.mangrove(w, 0, 2080, z, r=150, h=1450, canopy=640, grove=70, face_yaw=-90)

        # Maison des ventes (NE)
        info = K.building(w, 700, 250, z, 512, 448, floors=2, facade=M.WIN_CREAM, roof_kind="hip",
                          roof_mat=M.ROOF_PURPLE, doors=(("-x", 0), ("-y", 0)), door_kind="arch",
                          door_w=128, door_h=144, sign=M.sign_mat("auction", "MAISON DES VENTES", sub="Groove 1"),
                          awning=M.AWN_PURPLE, levels=1)
        K.furnish(w, info, "office")
        w.marker("Maison des ventes", (956, 474, z), "batiment")
        info = K.building(w, 600, 860, z, 384, 384, floors=3, facade=M.WIN_BLUE, roof_kind="gable",
                          roof_mat=M.ROOF_BLUE, doors=(("-x", 0),), sign=M.sign_mat("hotel", "HOTEL SABAODY"))
        K.furnish(w, info, "house", 1)

        # Bar de Shakky + boutique (NO)
        info = K.building(w, -1084, 300, z, 384, 320, floors=2, facade=M.WIN_WOOD, roof_kind="gable",
                          roof_mat=M.ROOF_ORANGE, doors=(("+x", 0),),
                          sign=M.sign_mat("shakky", "SHAKKY'S BAR", sub="Rip-off bar"), awning=M.AWN_RED)
        K.furnish(w, info, "bar", 2)
        w.marker("Bar de Shakky", (-892, 460, z), "batiment")
        info = K.building(w, -984, 760, z, 256, 256, floors=1, facade=M.WIN_PINK, roof_kind="hip",
                          roof_mat=M.ROOF_RED, doors=(("+x", 0),), sign=M.sign_mat("boutique", "BOUTIQUE"),
                          awning=M.AWN_BLUE)
        K.furnish(w, info, "shop", 3)

        # Atelier de coating + armurerie (SO)
        info = K.building(w, -1212, -698, z, 512, 448, floors=2, facade=M.WIN_TERRA, roof_kind="gable",
                          roof_mat=M.ROOF_DARK, doors=(("+x", 0), ("-y", 1)), door_kind="arch", door_w=128,
                          door_h=144, sign=M.sign_mat("coating", "ATELIER DE COATING", sub="Rayleigh"),
                          levels=1)
        K.furnish(w, info, "storage", 4)
        info = K.building(w, -560, -1160, z, 256, 256, floors=1, facade=M.WIN_STONE, roof_kind="gable",
                          roof_mat=M.ROOF_RED, doors=(("+y", 0),), sign=M.sign_mat("armory", "ARMURERIE"),
                          awning=M.AWN_RED)
        K.furnish(w, info, "shop", 5)

        # Poste de la Marine + epicerie (SE)
        info = K.building(w, 700, -698, z, 384, 384, floors=2, facade=M.WIN_MARINE, roof_kind="flat",
                          roof_mat=M.STONE_GREY, doors=(("-x", 0),), sign=M.sign_mat("marine_post", "MARINE",
                                                                                      sub="Poste de Sabaody"))
        K.furnish(w, info, "office", 6)
        w.add(G.prism(1084 - 40, -698 + 40, 6, 6, info["top"], info["top"] + 260, M.WHITE_PAINT))
        w.add(G.box(1084 - 38, -698 + 40, info["top"] + 180, 1084 - 34, -698 + 160, info["top"] + 250,
                    {"+x": Mat(M.FLAG_MARINE, fit=True), "-x": Mat(M.FLAG_MARINE, fit=True), "default": M.SAIL}))
        info = K.building(w, 304, -1160, z, 256, 256, floors=1, facade=M.WIN_YELLOW, roof_kind="hip",
                          roof_mat=M.ROOF_GREEN, doors=(("+y", 0),), sign=M.sign_mat("store", "EPICERIE"),
                          awning=M.AWN_GREEN)
        K.furnish(w, info, "shop", 7)

        # Sabaody Park : grande roue
        ferris_wheel(w, 0, 1500, 560)
        K.plaza(w, (-560, 1250, 560, 1750), z, M.PAVING)
        # arche d'entree du parc
        for sx in (-260, 220):
            w.add(G.box(sx, 1160, z, sx + 40, 1200, z + 300, M.paint_cycle(3)))
        pk = M.sign_mat("park", "SABAODY PARK", color=(255, 250, 220), board=(190, 60, 120))
        w.add(G.box(-300, 1166, z + 300, 300, 1194, z + 380,
                    {"-y": Mat(pk, fit=True), "+y": Mat(pk, fit=True), "default": M.RED}))

        # portique d'accueil au port
        for sx in (-260, 220):
            w.add(G.box(sx, -2140, z, sx + 40, -2100, z + 320, M.WOOD_BEAM))
        w.add(G.box(-300, -2134, z + 320, 300, -2106, z + 400,
                    {"-y": Mat(sm, fit=True), "+y": Mat(sm, fit=True), "default": M.WOOD_BEAM}))

        # quais
        K.dock(w, -128, -3300, 128, -2150, z)
        K.dock(w, -1000, -2950, -780, -1950, z)
        K.dock(w, 780, -2950, 1000, -1950, z)
        K.dock(w, -780, -3000, -128, -2850, z, posts=False)
        for x in (-900, 900):
            for y in (-2700, -2400):
                w.prop(K.P_CLEAT, (x + (110 if x > 0 else -110), y, z), 0)
        for i in range(6):
            w.prop(K.P_CRATE, (60 - (i % 2) * 120, -2300 - i * 120, z + 20), i * 25)
        K.ship(w, -470, -3150, 90, 820, "merry")
        K.ship(w, 1420, -2650, 90, 900, "red")

        # palmiers en bord de plage
        for i, ang in enumerate((0, 18, 70, 110, 160, 190, 250, 285, 345, 330, 200)):
            a = math.radians(ang)
            K.palm(w, math.cos(a) * 2120, math.sin(a) * 2120, z, 380 + 40 * (i % 3), seed=i)

        # bulles de Sabaody (sans collision)
        import numpy as np
        rng = np.random.default_rng(7)
        for i in range(26):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(300, 2100)
            model = "models/hunter/misc/sphere375x375.mdl" if i % 3 == 0 else "models/hunter/misc/sphere2x2.mdl"
            w.ent("prop_dynamic", (math.cos(a) * r, math.sin(a) * r, z + rng.uniform(220, 1200)),
                  model=model, solid=0, rendermode=1, renderamt=70, rendercolor="190 235 255",
                  disableshadows=1, DisableBoneFollowers=1, angles=(0, 0, 0))
