"""Impel Down : la grande prison sous-marine (cellules verrouillables)."""
import math

from .. import geom as G
from .. import kit as K
from .. import layout as L
from .. import materials as M
from ..geom import Mat

KEY = "impel"
Z = 64


def cell_block(w, x0, y0, z, ncells=6, cw=144, depth=176):
    """Bloc de cellules : chaque cellule a une porte a barreaux (func_door)."""
    sx = ncells * cw + 32
    sy = depth + 320
    info = K.building(w, x0, y0, z, sx, sy, floors=2, facade=M.WIN_DARK, inner=M.STONE_DARK,
                      floor_mat=M.STONE_GREY, roof_kind="flat", roof_mat=M.STONE_DARK,
                      doors=(("-y", 0),), door_kind="arch", door_w=128, door_h=144, levels=1,
                      trim=M.STONE_DARK, base=M.STONE_DARK, light_color=(255, 140, 90))
    ix0, iy0, ix1, iy1 = info["inner"]
    zf = info["zf"]
    by = iy1 - depth
    for i in range(1, ncells):
        cx = ix0 + i * cw
        w.add(G.box(cx, by, zf, cx + 16, iy1, zf + 152, M.STONE_DARK))
    for i in range(ncells):
        cx0 = ix0 + i * cw + 16
        cx1 = cx0 + cw - 16
        # barreaux fixes + porte coulissante
        w.add(G.box(cx0, by, zf, cx0 + 24, by + 8, zf + 152, M.BARS))
        door = G.box(cx0 + 24, by, zf, cx1 - 8, by + 8, zf + 136, M.BARS)
        w.ent("func_door", brushes=door, targetname=f"impel_cellule_{i + 1}", movedir="0 0 0",
              spawnflags=256 | 32, speed=80, wait=-1, lip=12, dmg=0, forceclosed=0,
              noise1="doors/default_move.wav", noise2="doors/default_stop.wav",
              rendercolor="255 255 255", renderamt=255, spawnpos=0, locked_sentence=0)
        w.add(G.box(cx1 - 8, by, zf, cx1, by + 8, zf + 152, M.BARS))
        w.add(G.box(cx0, by, zf + 136, cx1, by + 8, zf + 152, M.IRON))
        w.light((cx0 + cw / 2, iy1 - 60, zf + 130), (255, 150, 90), 60)
        w.prop(K.P_BED, (cx0 + 40, iy1 - 70, zf + 20), 90)
    return info


def build(w):
    name, X, Y, R, sub = L.ISLANDS[KEY]
    poly, land = L.island_base(w, KEY, seed=31)
    w.marker(name, (X, Y, 0), "ile")
    w.markers[-1]["poly"] = [list(p) for p in poly]

    # forteresse centrale
    w.add(G.frustum(X, Y + 200, 760, 700, Z, Z + 120, 8, M.STONE_DARK))
    w.add(G.prism(X, Y + 200, 700, 8, Z + 120, Z + 1000, {"default": Mat(M.WIN_DARK, origin=(X, Y, Z + 280)),
                                                         "top": M.STONE_DARK}))
    w.add(G.prism(X, Y + 200, 740, 8, Z + 1000, Z + 1060, M.IRON))
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        K.tower(w, X + math.cos(a) * 700, Y + 200 + math.sin(a) * 700, Z, 110, 1200, 8, M.STONE_DARK,
                M.ROOF_DARK, 240)
    w.add(G.prism(X, Y + 200, 300, 8, Z + 1060, Z + 1700, {"default": Mat(M.WIN_DARK, origin=(X, Y, Z)),
                                                          "top": M.STONE_DARK}))
    w.add(G.frustum(X, Y + 200, 360, 0, Z + 1700, Z + 2050, 8, M.ROOF_DARK))
    # panneau plaque sur la face nord de l'octogone (apotheme 700*cos(22.5) = 647), cote port/arrivee,
    # entre les tours de 67.5 et 112.5 deg (bord interieur a +-166)
    w.add(G.box(X - 150, Y + 200 + 645, Z + 720, X + 150, Y + 200 + 657, Z + 870,
                {"+y": Mat(M.sign_mat("impel", "IMPEL DOWN", sub="Prison du Gouvernement Mondial",
                                      color=(255, 120, 90), board=(60, 60, 66)), fit=True), "default": M.IRON}))

    # bloc de cellules devant la forteresse
    info = cell_block(w, X - 480, Y - 1092, Z)   # 32 u plus au sud : le toit ne rentre plus dans les tours
    w.marker("Impel Down - bloc de cellules", (X, Y - 900, Z), "batiment")
    # bureau du directeur
    info = K.building(w, X + 560, Y - 1060, Z, 384, 320, floors=2, facade=M.WIN_DARK, inner=M.STONE_DARK,
                      roof_kind="flat", roof_mat=M.STONE_DARK, doors=(("-y", 0),),
                      sign=M.sign_mat("directeur", "DIRECTION"), trim=M.STONE_DARK, base=M.STONE_DARK)
    K.furnish(w, info, "office", 50)

    # port + navires de la Marine (+ arrivee depuis les Portes de la Justice)
    ax, ay, az, ayaw = L.arrival_point(KEY)
    K.tp_destination(w, "arrive_impel", ax, ay, az, ayaw)
    a = math.atan2(ay - Y, ax - X)
    px, py = X + math.cos(a) * R * 0.78, Y + math.sin(a) * R * 0.78
    f = G.Frame(px, py, 0, math.degrees(a))
    # jetee pleine jusqu'au fond, qui part du sol plat (avant : flottait a z=12 et commencait 56 u au-dessus de la plage)
    w.add(f.box(-420, -160, -768, 700, 160, 67, {"top": M.STONE_GREY, "default": M.STONE_DARK}))
    K.ship(w, *f.p(650, 520)[:2], math.degrees(a), 1100, "marine")   # poupe en eau profonde (quille hors du fond)
    for s in (-1, 1):
        K.flagpole(w, *f.p(600, s * 140)[:2], 64, M.FLAG_MARINE, 300)

    # torches & rochers
    for i in range(10):
        a = math.radians(i * 36)
        lx, ly = X + math.cos(a) * 900, Y + 200 + math.sin(a) * 900
        if ly < Y - 540:
            # 252 et 288 deg tombaient dans les cellules 2 et 6 (a travers le lit et le plafond) :
            # on les met de part et d'autre de la porte du bloc (porte en X + 32)
            lx, ly = X + 32 + (170 if lx > X else -170), Y - 1170
        K.lamp(w, lx, ly, Z, (255, 140, 80), 260)
    a_arr = math.atan2(L.arrival_point(KEY)[1] - Y, L.arrival_point(KEY)[0] - X)
    for i in range(7):
        a = math.radians(i * 51 + 20)
        da = abs((a - a_arr + math.pi) % (2 * math.pi) - math.pi)
        if da < math.radians(30) or da > math.radians(60):
            continue   # au-dela de 60 deg du port, R*1.05 est en pleine terre : rocher enterre
        rx, ry = X + math.cos(a) * R * 1.05, Y + math.sin(a) * R * 1.05
        w.add(G.boulder(rx, ry, -100 + 60 * (i % 3), 240, 200, 520 + 120 * (i % 3), 900 + i, M.ROCK_DARK, 26,
                        flat_bottom=-768))
    K.env_cubemap(w, X, Y - 1300, Z + 128)   # en plein air devant le bloc (Y-600 tombait dans la cellule 4)
