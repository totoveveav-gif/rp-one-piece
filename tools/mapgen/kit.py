"""Kit d'architecture : batiments, toits, arbres, quais, navires, portails."""
import math
import zlib

import numpy as np

from . import geom as G
from . import materials as M
from .geom import Mat
from .vmf import add_output

T_WALL = 16     # epaisseur des murs
DOOR_W = 64
DOOR_H = 120


# ---------------------------------------------------------------------------
# Batiments
# ---------------------------------------------------------------------------

PLAIN = {M.WIN_WHITE: M.WHITE, M.WIN_MARINE: M.WHITE, M.WIN_CREAM: M.CREAM, M.WIN_PINK: M.PINK,
         M.WIN_YELLOW: M.YELLOW, M.WIN_BLUE: M.SKYBLUE, M.WIN_MINT: M.MINT, M.WIN_TERRA: M.TERRA,
         M.WIN_SAND: M.SANDSTONE, M.WIN_STONE: M.STONE_GREY, M.WIN_DARK: M.STONE_DARK,
         M.WIN_BRICK: M.BRICK, M.WIN_WOOD: M.PLANKS, M.WIN_SNOW: M.PLANKS_DARK, M.JP_WALL: M.WHITE}


def plain_of(facade):
    return PLAIN.get(facade, facade)

def _wall_pieces(axis, fixed0, fixed1, a0, a1, zb, zt, openings, spec):
    """Mur rectangulaire avec ouvertures. axis='x' : le mur court selon x."""
    out = []

    def mk(b0, b1, z0, z1):
        if b1 - b0 < 1 or z1 - z0 < 1:
            return
        if axis == "x":
            out.append(G.box(b0, fixed0, z0, b1, fixed1, z1, spec))
        else:
            out.append(G.box(fixed0, b0, z0, fixed1, b1, z1, spec))

    ops = sorted(openings, key=lambda o: o[0])
    cur = a0
    for c, wd, oz0, oz1 in ops:
        l, r = c - wd / 2, c + wd / 2
        mk(cur, l, zb, zt)
        mk(l, r, zb, oz0)
        mk(l, r, oz1, zt)
        cur = r
    mk(cur, a1, zb, zt)
    return out


def _roof_retex(roof_mat, end_mat, under_mat):
    def fn(f):
        nz = f.normal[2]
        if nz < -0.5:
            return under_mat
        if abs(nz) < 0.02:
            return end_mat
        return roof_mat
    return fn


def roof(w, kind, x0, y0, x1, y1, z, mat, end_mat, h=None, axis=None, under=None):
    """Toit pose en z sur le rectangle donne (deja deborde)."""
    under = under or M.WOOD_BEAM
    sx, sy = x1 - x0, y1 - y0
    if axis is None:
        axis = "x" if sx >= sy else "y"
    if h is None:
        h = 0.45 * (sy if axis == "x" else sx)
    if kind == "gable":
        b = G.gable(x0, y0, x1, y1, z, h, axis, mat)
        b.retexture(_roof_retex(mat, end_mat, under))
        w.add(b)
    elif kind == "hip":
        b = G.hip(x0, y0, x1, y1, z, h, mat)
        b.retexture(_roof_retex(mat, end_mat, under))
        w.add(b)
    elif kind == "flat":
        pass
    elif kind == "dome":
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dome(w, cx, cy, z, min(sx, sy) / 2, mat)
    return h


def dome(w, cx, cy, z, r, mat, sides=16, rings=4, under=None, spike=True):
    prev_r, prev_z = r, z
    for i in range(1, rings + 1):
        a = math.pi / 2 * i / (rings + 0.35)
        rr = r * math.cos(a)
        zz = z + r * math.sin(a)
        w.add(G.frustum(cx, cy, prev_r, rr, prev_z, zz, sides,
                        {"bottom": under or mat, "default": mat}))
        prev_r, prev_z = rr, zz
    if spike:
        w.add(G.frustum(cx, cy, prev_r, 0, prev_z, prev_z + r * 0.35, 8, M.GOLD))
    return prev_z


def building(w, x0, y0, z, sx, sy, floors=1, fh=160, facade=M.WIN_WHITE, inner=M.INTERIOR,
             floor_mat=M.PLANKS, roof_kind="gable", roof_mat=M.ROOF_RED, roof_h=None,
             roof_axis=None, overhang=24, doors=(("-y", 0),), door_kind="door",
             door_w=DOOR_W, door_h=DOOR_H, light=True, levels=None, base=M.STONE_GREY,
             trim=None, sign=None, awning=None, gable_mat=None, name=None, props=True,
             light_color=(255, 222, 180)):
    """Batiment axe-aligne ou l'on peut entrer.

    doors : liste de (cote, decalage) ; le decalage est en tuiles de 128
            depuis le centre du mur (les portes tombent entre deux fenetres).
    levels : nombre de niveaux accessibles (1 ou 2), le reste est plein.
    """
    t = T_WALL
    trim = trim or facade
    x1, y1 = x0 + sx, y0 + sy
    zf = z + 8
    H = floors * fh
    zt = zf + H
    if levels is None:
        levels = 2 if (floors >= 2 and sx >= 384 and sy >= 256) else 1
    levels = min(levels, floors)
    face = Mat(facade, origin=(x0, y0, zf + fh))
    face_m = {}
    for side in ("-y", "+y", "-x", "+x"):
        opp = {"-y": "+y", "+y": "-y", "-x": "+x", "+x": "-x"}[side]
        face_m[side] = {side: face, opp: inner, "top": trim, "bottom": inner, "default": inner}

    # socle + plancher
    w.add(G.box(x0 - 8, y0 - 8, z - 32, x1 + 8, y1 + 8, zf, {"top": floor_mat, "default": base}))

    # portes
    ops = {"-y": [], "+y": [], "-x": [], "+x": []}
    door_info = []
    for side, off in doors:
        if side in ("-y", "+y"):
            c = x0 + sx / 2 + off * 128
            c = x0 + round((c - x0) / 128) * 128 if sx >= 256 else x0 + sx / 2
            c = min(max(c, x0 + t + door_w / 2 + 8), x1 - t - door_w / 2 - 8)
        else:
            c = y0 + sy / 2 + off * 128
            c = y0 + round((c - y0) / 128) * 128 if sy >= 256 else y0 + sy / 2
            c = min(max(c, y0 + t + door_w / 2 + 8), y1 - t - door_w / 2 - 8)
        ops[side].append((c, door_w, zf, zf + door_h))
        door_info.append((side, c))

    # murs (avant/arriere pleine longueur, cotes entre les deux)
    w.add(_wall_pieces("x", y0, y0 + t, x0, x1, zf, zt, ops["-y"], face_m["-y"]))
    w.add(_wall_pieces("x", y1 - t, y1, x0, x1, zf, zt, ops["+y"], face_m["+y"]))
    w.add(_wall_pieces("y", x0, x0 + t, y0 + t, y1 - t, zf, zt, ops["-x"], face_m["-x"]))
    w.add(_wall_pieces("y", x1 - t, x1, y0 + t, y1 - t, zf, zt, ops["+x"], face_m["+x"]))

    ix0, iy0, ix1, iy1 = x0 + t, y0 + t, x1 - t, y1 - t
    # etage + rampe (le long d'un mur sans porte)
    door_sides = {d[0] for d in door_info}
    if levels >= 2:
        wall = next((s_ for s_ in ("+y", "-y", "+x", "-x") if s_ not in door_sides), None)
        if wall is None or (wall in ("+x", "-x") and sy < 384):
            levels = 1
    if levels >= 2:
        zs = zf + fh
        sl = {"top": floor_mat, "bottom": inner, "default": inner}
        rm = {"top": floor_mat, "default": inner}
        if wall in ("+y", "-y"):
            rx0, rx1 = ix0 + 24, ix0 + 24 + 256
            ry0, ry1 = (iy1 - 72, iy1) if wall == "+y" else (iy0, iy0 + 72)
            w.add(G.ramp(rx0, ry0, zf, rx1, ry1, zs, "+x", rm))
            if wall == "+y":
                w.add(G.box(ix0, iy0, zs - 8, ix1, ry0, zs, sl))
            else:
                w.add(G.box(ix0, ry1, zs - 8, ix1, iy1, zs, sl))
            w.add(G.box(rx1, ry0, zs - 8, ix1, ry1, zs, sl))
            w.add(G.box(ix0, ry0, zs - 8, rx0, ry1, zs, sl))
            gy0, gy1 = (ry0 - 6, ry0) if wall == "+y" else (ry1, ry1 + 6)
            w.add(G.box(rx0, gy0, zs, rx1 - 40, gy1, zs + 40, M.WOOD_BEAM))
        else:
            ry0, ry1 = iy0 + 24, iy0 + 24 + 256
            rx0, rx1 = (ix1 - 72, ix1) if wall == "+x" else (ix0, ix0 + 72)
            w.add(G.ramp(rx0, ry0, zf, rx1, ry1, zs, "+y", rm))
            if wall == "+x":
                w.add(G.box(ix0, iy0, zs - 8, rx0, iy1, zs, sl))
            else:
                w.add(G.box(rx1, iy0, zs - 8, ix1, iy1, zs, sl))
            w.add(G.box(rx0, ry1, zs - 8, rx1, iy1, zs, sl))
            w.add(G.box(rx0, iy0, zs - 8, rx1, ry0, zs, sl))
            gx0, gx1 = (rx0 - 6, rx0) if wall == "+x" else (rx1, rx1 + 6)
            w.add(G.box(gx0, ry0, zs, gx1, ry1 - 40, zs + 40, M.WOOD_BEAM))
    zc = zf + levels * fh
    if zc < zt:
        w.add(G.box(ix0, iy0, zc - 8, ix1, iy1, zc, {"bottom": inner, "default": inner}))

    # toit
    oh = overhang
    w.add(G.box(x0 - oh, y0 - oh, zt, x1 + oh, y1 + oh, zt + 12,
                {"top": roof_mat if roof_kind == "flat" else M.WOOD_BEAM,
                 "bottom": inner if True else trim, "default": M.WOOD_BEAM}))
    top = zt + 12
    if roof_kind == "flat":
        pm = {"default": trim, "top": M.STONE_GREY}
        w.add(G.box(x0 - oh, y0 - oh, top, x1 + oh, y0 - oh + 12, top + 32, pm))
        w.add(G.box(x0 - oh, y1 + oh - 12, top, x1 + oh, y1 + oh, top + 32, pm))
        w.add(G.box(x0 - oh, y0 - oh + 12, top, x0 - oh + 12, y1 + oh - 12, top + 32, pm))
        w.add(G.box(x1 + oh - 12, y0 - oh + 12, top, x1 + oh, y1 + oh - 12, top + 32, pm))
    else:
        roof(w, roof_kind, x0 - oh, y0 - oh, x1 + oh, y1 + oh, top, roof_mat,
             gable_mat or plain_of(facade),
             h=roof_h, axis=roof_axis)

    # portes (entites)
    for side, c in door_info:
        if door_kind == "door":
            make_door(w, side, c, x0, y0, x1, y1, zf, door_w, door_h)
        if sign:
            add_sign(w, side, c, x0, y0, x1, y1, zf + door_h + 14, sign)
            sign = None
        if awning:
            add_awning(w, side, c, x0, y0, x1, y1, zf + door_h + 4, awning)

    # eclairage interieur
    if light:
        for lv in range(levels):
            w.light(((ix0 + ix1) / 2, (iy0 + iy1) / 2, zf + lv * fh + fh - 28),
                    light_color, 160 + (sx * sy) / 2500)
    return {"inner": (ix0, iy0, ix1, iy1), "zf": zf, "zt": zt, "top": top, "doors": door_info,
            "levels": levels}


def make_door(w, side, c, x0, y0, x1, y1, zf, dw=DOOR_W, dh=DOOR_H, mat=None):
    """Porte rotative (proprietaire DarkRP possible), s'ouvre vers l'interieur."""
    mat = mat or M.DOOR
    th = 4
    dmat = {"default": M.WOOD_BEAM}
    if side in ("-y", "+y"):
        wy = y0 + T_WALL / 2 if side == "-y" else y1 - T_WALL / 2
        bx0, bx1 = c - dw / 2, c + dw / 2
        b = G.box(bx0, wy - th / 2, zf, bx1, wy + th / 2, zf + dh - 1,
                  {"-y": Mat(mat, fit=True), "+y": Mat(mat, fit=True), **dmat})
        hinge = (bx0, wy, zf)
        t_dir = np.array([1, 0])
        inward = np.array([0, 1]) if side == "-y" else np.array([0, -1])
    else:
        wx = x0 + T_WALL / 2 if side == "-x" else x1 - T_WALL / 2
        by0, by1 = c - dw / 2, c + dw / 2
        b = G.box(wx - th / 2, by0, zf, wx + th / 2, by1, zf + dh - 1,
                  {"-x": Mat(mat, fit=True), "+x": Mat(mat, fit=True), **dmat})
        hinge = (wx, by0, zf)
        t_dir = np.array([0, 1])
        inward = np.array([1, 0]) if side == "-x" else np.array([-1, 0])
    rot = np.array([-t_dir[1], t_dir[0]])  # rotation +90 (anti-horaire)
    flags = 16 | 256 | 32  # sens unique + "utiliser" ouvre + bascule
    if not np.array_equal(rot, inward):
        flags |= 2
    w.ent("func_door_rotating", brushes=b, origin=(hinge[0], hinge[1], hinge[2] + dh / 2),
          spawnflags=flags, distance=90, speed=140, wait=-1, lip=0, dmg=0,
          noise1="doors/default_move.wav", noise2="doors/default_stop.wav",
          rendercolor="255 255 255", renderamt=255, spawnpos=0, health=0,
          forceclosed=0, solidbsp=0, disablereceiveshadows=0, angles="0 0 0")


def add_sign(w, side, c, x0, y0, x1, y1, z, mat, width=192, height=48):
    d = 6
    if side == "-y":
        b = G.box(c - width / 2, y0 - d, z, c + width / 2, y0, z + height,
                  {"-y": Mat(mat, fit=True), "default": M.WOOD_BEAM})
    elif side == "+y":
        b = G.box(c - width / 2, y1, z, c + width / 2, y1 + d, z + height,
                  {"+y": Mat(mat, fit=True), "default": M.WOOD_BEAM})
    elif side == "-x":
        b = G.box(x0 - d, c - width / 2, z, x0, c + width / 2, z + height,
                  {"-x": Mat(mat, fit=True), "default": M.WOOD_BEAM})
    else:
        b = G.box(x1, c - width / 2, z, x1 + d, c + width / 2, z + height,
                  {"+x": Mat(mat, fit=True), "default": M.WOOD_BEAM})
    w.add(b)


def add_awning(w, side, c, x0, y0, x1, y1, z, mat, width=160, depth=64):
    s = {"default": mat}
    if side == "-y":
        b = G.ramp(c - width / 2, y0 - depth, z - 24, c + width / 2, y0, z + 8, "+y", s)
    elif side == "+y":
        b = G.ramp(c - width / 2, y1, z - 24, c + width / 2, y1 + depth, z + 8, "-y", s)
    elif side == "-x":
        b = G.ramp(x0 - depth, c - width / 2, z - 24, x0, c + width / 2, z + 8, "+x", s)
    else:
        b = G.ramp(x1, c - width / 2, z - 24, x1 + depth, c + width / 2, z + 8, "-x", s)
    w.add(b)


def block(w, x0, y0, z, sx, sy, floors, facade, roof_kind="gable", roof_mat=M.ROOF_RED,
          fh=160, overhang=16, roof_h=None, roof_axis=None, base=M.STONE_GREY):
    """Batiment plein (decor de fond, peu couteux)."""
    zf = z + 8
    zt = zf + floors * fh
    face = Mat(facade, origin=(x0, y0, zf + fh))
    w.add(G.box(x0 - 8, y0 - 8, z - 32, x0 + sx + 8, y0 + sy + 8, zf, base))
    w.add(G.box(x0, y0, zf, x0 + sx, y0 + sy, zt, {"top": M.WOOD_BEAM, "bottom": base, "default": face}))
    if roof_kind == "flat":
        w.add(G.box(x0 - 8, y0 - 8, zt, x0 + sx + 8, y0 + sy + 8, zt + 24,
                    {"top": roof_mat, "default": M.STONE_GREY}))
        return zt + 24
    endm = plain_of(facade)
    w.add(G.box(x0 - overhang, y0 - overhang, zt, x0 + sx + overhang, y0 + sy + overhang, zt + 10,
                M.WOOD_BEAM))
    h = roof(w, roof_kind, x0 - overhang, y0 - overhang, x0 + sx + overhang, y0 + sy + overhang,
             zt + 10, roof_mat, endm, h=roof_h, axis=roof_axis)
    return zt + 10 + h


def tower(w, cx, cy, z, r, h, sides=16, wall=M.WHITE, roof_mat=M.ROOF_BLUE, roof_h=None,
          cap="cone", band=None, base=M.STONE_GREY):
    w.add(G.prism(cx, cy, r + 12, sides, z - 32, z + 24, base))
    w.add(G.prism(cx, cy, r, sides, z + 24, z + h, {"top": M.WOOD_BEAM, "default": wall}))
    top = z + h
    if band:
        w.add(G.prism(cx, cy, r + 10, sides, top - 40, top - 4, {"default": band}))
    if cap == "cone":
        rh = roof_h or r * 1.6
        w.add(G.frustum(cx, cy, r + 28, 0, top, top + rh, sides, {"bottom": M.WOOD_BEAM, "default": roof_mat}))
        return top + rh
    if cap == "dome":
        return dome(w, cx, cy, top, r + 8, roof_mat)
    if cap == "battlement":
        w.add(G.prism(cx, cy, r + 20, sides, top, top + 24, M.STONE_GREY))
        for i in range(sides):
            if i % 2:
                continue
            a = 2 * math.pi * (i + 0.5) / sides
            px, py = cx + math.cos(a) * (r + 8), cy + math.sin(a) * (r + 8)
            w.add(G.box(px - 14, py - 14, top + 24, px + 14, py + 14, top + 56, M.STONE_GREY))
        return top + 24
    return top


def stairs(w, x0, y0, x1, y1, z0, z1, rise, mat=M.STAIRS, side_mat=None):
    """Escalier (rampe praticable avec texture de marches de 16 unites)."""
    run = abs(x1 - x0) if rise in ("+x", "-x") else abs(y1 - y0)
    h = abs(z1 - z0)
    slope = math.hypot(run, h)
    nsteps = max(1, round(h / 16))
    tile_v = slope / nsteps * 8
    top = Mat(mat, scale=(128, tile_v))
    w.add(G.ramp(x0, y0, z0, x1, y1, z1, rise, {"top": top, "slope": top, "default": side_mat or M.STONE_GREY}))


def plaza(w, poly_or_rect, z, mat=M.PAVING, thick=6, edge=M.STONE_GREY):
    if len(poly_or_rect) == 4 and not isinstance(poly_or_rect[0], (tuple, list)):
        x0, y0, x1, y1 = poly_or_rect
        w.add(G.box(x0, y0, z - 16, x1, y1, z + thick, {"top": mat, "default": edge}))
    else:
        w.add(G.poly_prism(poly_or_rect, z - 16, z + thick, {"top": mat, "default": edge}))
    return z + thick


def road(w, x0, y0, x1, y1, z, width=192, mat=M.COBBLE):
    """Route droite entre deux points (boite orientee)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    f = G.Frame(x0, y0, z, yaw)
    w.add(f.box(0, -width / 2, -16, L, width / 2, 6, {"top": mat, "default": M.STONE_GREY}))


def fence(w, x0, y0, x1, y1, z, h=40, mat=M.WOOD_BEAM, t=8):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    f = G.Frame(x0, y0, z, math.degrees(math.atan2(dy, dx)))
    w.add(f.box(0, -t / 2, 0, L, t / 2, h, mat))


def lamp(w, x, y, z, color=(255, 214, 150), bright=220):
    w.prop("models/props_c17/lamppost03a_off.mdl", (x, y, z), 0, fade=(6000, 7500))
    w.light((x, y, z + 150), color, bright)


# ---------------------------------------------------------------------------
# Vegetation
# ---------------------------------------------------------------------------

def palm(w, x, y, z, h=360, seed=0, lean=None):
    rng = np.random.default_rng(seed)
    if lean is None:
        a = rng.uniform(0, 2 * math.pi)
        lean = (math.cos(a) * h * 0.18, math.sin(a) * h * 0.18)
    top = np.array([x + lean[0], y + lean[1], z + h])
    w.add(G.cylinder((x, y, z - 16), top, 16, 8, M.BARK, r1=11))
    n = 6
    rot0 = rng.uniform(0, 360)
    for i in range(n):
        a = math.radians(rot0 + i * 360 / n + rng.uniform(-12, 12))
        d = np.array([math.cos(a), math.sin(a), 0])
        p = np.array([-d[1], d[0], 0])
        L = rng.uniform(150, 200)
        pts = [top + p * 8, top - p * 8,
               top + d * L * 0.5 + p * 26 + [0, 0, 22], top + d * L * 0.5 - p * 26 + [0, 0, 22],
               top + d * L + [0, 0, -L * 0.42]]
        pts = pts + [q + [0, 0, -5] for q in pts]
        w.add(G.brush(pts, M.PALM))
    w.add(G.prism(top[0], top[1], 16, 6, top[2] - 18, top[2] + 6, M.PALM))


def round_tree(w, x, y, z, h=300, r=120, mat=M.LEAVES, trunk=M.BARK, sides=12):
    w.add(G.cylinder((x, y, z - 16), (x, y, z + h * 0.55), 14, 8, trunk, r1=10))
    w.add(G.boulder(x, y, z + h * 0.7, r, r, h * 0.32, int(abs(x * 7 + y * 13)) % 99991, mat, 26))


def pine(w, x, y, z, h=420, r=130, mat=M.PINE):
    w.add(G.cylinder((x, y, z - 16), (x, y, z + h * 0.3), 14, 6, M.BARK, r1=10))
    for k, (a, b, rr) in enumerate(((0.2, 0.55, 1.0), (0.45, 0.8, 0.75), (0.68, 1.0, 0.5))):
        w.add(G.frustum(x, y, r * rr, 0, z + h * a, z + h * b, 12, mat, rot=k * 22))


def bush(w, x, y, z, r=48, mat=M.LEAVES):
    w.add(G.frustum(x, y, r, r * 0.55, z - 8, z + r * 0.9, 7, mat))


def mangrove(w, x, y, z, r=200, h=1300, canopy=900, grove=None, face_yaw=-90):
    """Mangrove geante de l'archipel de Sabaody."""
    w.add(G.frustum(x, y, r * 1.9, r * 1.05, z - 24, z + 140, 16, M.MANGROVE))
    w.add(G.prism(x, y, r, 16, z + 140, z + h, M.MANGROVE))
    # racines
    for i in range(5):
        a = math.radians(i * 72 + 15)
        p0 = (x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, z + 260)
        p1 = (x + math.cos(a) * r * 2.6, y + math.sin(a) * r * 2.6, z - 20)
        w.add(G.cylinder(p0, p1, r * 0.22, 6, M.MANGROVE, r1=r * 0.12))
    # branches + canopee
    for i in range(4):
        a = math.radians(i * 90 + 45)
        p0 = (x, y, z + h * 0.8)
        p1 = (x + math.cos(a) * canopy * 0.55, y + math.sin(a) * canopy * 0.55, z + h * 0.97)
        w.add(G.cylinder(p0, p1, r * 0.3, 6, M.MANGROVE, r1=r * 0.15))
    rng = np.random.default_rng(int(abs(x) + abs(y)) % 9973)
    w.add(G.boulder(x, y, z + h * 1.06, canopy * 0.78, canopy * 0.78, h * 0.16, int(rng.integers(1 << 30)),
                    M.CANOPY, 36))
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        d = canopy * rng.uniform(0.45, 0.7)
        rr = canopy * rng.uniform(0.32, 0.45)
        bx, by = x + math.cos(a) * d, y + math.sin(a) * d
        zb = z + h * rng.uniform(0.9, 1.02) + i * 7
        w.add(G.boulder(bx, by, zb + rr * 0.3, rr, rr, rr * 0.42, int(rng.integers(1 << 30)), M.CANOPY, 30))
    if grove is not None:
        mat = M.grove_mat(grove)
        f = G.Frame(x, y, z, face_yaw)
        # plaque peinte sur le tronc, face vers face_yaw
        w.add(f.box(r * 0.92, -110, 300, r * 0.92 + 8, 110, 520,
                    {"+x": Mat(mat, fit=True), "default": M.MANGROVE}))


# ---------------------------------------------------------------------------
# Quais & navires
# ---------------------------------------------------------------------------

def dock(w, x0, y0, x1, y1, z=24, posts=True, mat=M.PLANKS_LIGHT):
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    w.add(G.box(xa, ya, z - 12, xb, yb, z + 3, {"top": mat, "default": M.WOOD_BEAM}))
    if posts:
        step = 256
        xs = list(np.arange(xa + 16, xb - 15, step)) + [xb - 16]
        ys = list(np.arange(ya + 16, yb - 15, step)) + [yb - 16]
        if xb - xa > yb - ya:
            pts = [(px, py) for px in xs for py in (ya + 16, yb - 16)]
        else:
            pts = [(px, py) for py in ys for px in (xa + 16, xb - 16)]
        for px, py in pts:
            w.add(G.prism(px, py, 12, 6, -300, z + 16, M.WOOD_BEAM))


def ship(w, x, y, yaw, L=900, style="marine", z=0, name=None):
    """Navire decoratif (pont praticable). Proue vers +x local."""
    f = G.Frame(x, y, z, yaw)
    B = L * 0.26
    hull = {"marine": M.HULL_WHITE, "merry": M.HULL_YELLOW, "pirate": M.PLANKS_DARK,
            "red": M.PLANKS_RED}[style]
    sail = {"marine": M.SAIL_MARINE, "merry": M.SAIL_SH, "pirate": M.SAIL,
            "red": M.SAIL_STRIPES}.get(style, M.SAIL)
    deck_z = L * 0.075
    top = [(-L * 0.46, -B / 2), (L * 0.18, -B / 2), (L * 0.5, 0), (L * 0.18, B / 2), (-L * 0.46, B / 2)]
    bot = [(-L * 0.40, -B * 0.3), (L * 0.16, -B * 0.3), (L * 0.44, 0), (L * 0.16, B * 0.3), (-L * 0.40, B * 0.3)]
    pts = [(px, py, deck_z) for px, py in top] + [(px, py, -L * 0.09) for px, py in bot]
    w.add(f.hull(pts, {"top": M.PLANKS_LIGHT, "default": hull}))
    # liseres / bastingage
    rail = M.MARINE_BLUE if style == "marine" else M.WOOD_BEAM
    for sgn in (-1, 1):
        w.add(f.hull([(-L * 0.46, sgn * B / 2, deck_z), (L * 0.18, sgn * B / 2, deck_z),
                      (-L * 0.46, sgn * (B / 2 - 8), deck_z), (L * 0.18, sgn * (B / 2 - 8), deck_z),
                      (-L * 0.46, sgn * B / 2, deck_z + 28), (L * 0.18, sgn * B / 2, deck_z + 28),
                      (-L * 0.46, sgn * (B / 2 - 8), deck_z + 28), (L * 0.18, sgn * (B / 2 - 8), deck_z + 28)],
                     rail))
    if style == "marine":
        for sgn in (-1, 1):
            w.add(f.hull([(-L * 0.455, sgn * (B / 2 + 1), deck_z - 30), (L * 0.18, sgn * (B / 2 + 1), deck_z - 30),
                          (-L * 0.455, sgn * (B / 2 - 6), deck_z - 30), (L * 0.18, sgn * (B / 2 - 6), deck_z - 30),
                          (-L * 0.455, sgn * (B / 2 + 1), deck_z - 14), (L * 0.18, sgn * (B / 2 + 1), deck_z - 14),
                          (-L * 0.455, sgn * (B / 2 - 6), deck_z - 14), (L * 0.18, sgn * (B / 2 - 6), deck_z - 14)],
                         M.MARINE_BLUE))
    # chateau arriere
    w.add(f.box(-L * 0.46, -B / 2 + 4, deck_z, -L * 0.30, B / 2 - 4, deck_z + 96,
                {"top": M.PLANKS_LIGHT, "default": hull}))
    w.add(f.hull([(-L * 0.30, -B * 0.3, deck_z), (-L * 0.30, B * 0.3, deck_z),
                  (-L * 0.22, -B * 0.3, deck_z), (-L * 0.22, B * 0.3, deck_z),
                  (-L * 0.30, -B * 0.3, deck_z + 96), (-L * 0.30, B * 0.3, deck_z + 96)],
                 {"default": M.PLANKS_LIGHT, "side": hull}))
    # mats & voiles
    masts = [0.0] if style == "merry" else ([-0.12, 0.16] if L < 1100 else [-0.18, 0.02, 0.22])
    for mx in masts:
        mh = L * 0.62
        w.add(f.cyl((mx * L, 0, deck_z), (mx * L, 0, deck_z + mh), 12, 6, M.WOOD_BEAM, r1=8))
        sw = B * 1.2
        for k, (zz, hh) in enumerate(((0.22, 0.26), (0.52, 0.2))):
            z0 = deck_z + mh * zz
            z1 = z0 + mh * hh
            ww = sw * (1.0 if k == 0 else 0.8)
            w.add(f.box(mx * L + 14, -ww / 2, z0, mx * L + 20, ww / 2, z1,
                        {"+x": Mat(sail, fit=True), "-x": Mat(sail, fit=True), "default": M.SAIL}))
            w.add(f.cyl((mx * L + 12, -ww / 2 - 10, z1 + 6), (mx * L + 12, ww / 2 + 10, z1 + 6), 5, 6, M.WOOD_BEAM))
        flag = M.FLAG_MARINE if style == "marine" else M.FLAG_SH
        if mx == masts[-1]:
            w.add(f.box(mx * L - 2, 0, deck_z + mh - 70, mx * L + 2, 90, deck_z + mh - 10,
                        {"+x": Mat(flag, fit=True), "-x": Mat(flag, fit=True), "default": M.SAIL}))
    # beaupre
    w.add(f.cyl((L * 0.42, 0, deck_z + 10), (L * 0.68, 0, deck_z + 90), 8, 6, M.WOOD_BEAM, r1=4))
    if style == "merry":
        # tete de mouton
        w.add(f.hull([(L * 0.5 + dx, dy, deck_z + 30 + dz) for dx in (-26, 26) for dy in (-26, 26)
                      for dz in (-10, 40)] + [(L * 0.5 + 40, 0, deck_z + 20)], M.WHITE_PAINT))
        for sgn in (-1, 1):
            w.add(f.cyl((L * 0.5, sgn * 22, deck_z + 60), (L * 0.5 - 10, sgn * 40, deck_z + 46), 8, 6, M.HULL_YELLOW))
    elif style == "marine":
        w.add(f.hull([(L * 0.5 + dx, dy, deck_z + 10 + dz) for dx in (-30, 30) for dy in (-30, 30)
                      for dz in (0, 50)] + [(L * 0.5 + 56, 0, deck_z + 26)], M.MARINE_BLUE))
    # canons sur les flancs
    if style in ("marine", "pirate", "red"):
        for i in range(4):
            cx = -L * 0.25 + i * L * 0.14
            for sgn in (-1, 1):
                w.add(f.cyl((cx, sgn * (B / 2 - 20), deck_z - 34), (cx, sgn * (B / 2 + 30), deck_z - 34),
                            8, 6, M.IRON))
    return f


# ---------------------------------------------------------------------------
# Teleportation (geree par le Lua : seuls les bateaux passent)
# ---------------------------------------------------------------------------

def gate_triggers(w, trig, gid):
    """trigger_multiple qui appelle le Lua (sv_onepiece_seagates.lua) : seuls les
    bateaux (vehicules, props soudes et leur equipage) traversent le portail."""
    e = w.ent("trigger_multiple", brushes=trig, targetname=f"tp_gate_{gid}", spawnflags=1 | 2 | 8 | 64,
              wait=0.1, StartDisabled=0)
    add_output(e, "OnStartTouch", "op_seagate_lua", "RunCode")


def tp_destination(w, name, x, y, z, yaw):
    w.ent("info_teleport_destination", (x, y, z), targetname=name, angles=(0, yaw, 0))


def env_cubemap(w, x, y, z):
    w.ent("env_cubemap", (x, y, z), cubemapsize=0)


def button_toggle(w, x0, y0, z0, x1, y1, z1, target, mat=M.RED):
    b = G.box(x0, y0, z0, x1, y1, z1, mat)
    e = w.ent("func_button", brushes=b, spawnflags=1 | 1024, speed=5, wait=3, lip=2,
              sounds=0, movedir="0 0 0", rendercolor="255 255 255", renderamt=255)
    add_output(e, "OnPressed", target, "Toggle")
    return e


# ---------------------------------------------------------------------------
# Mobilier (props Half-Life 2, inclus dans GMod)
# ---------------------------------------------------------------------------

P_TABLE = "models/props_c17/furnituretable001a.mdl"
P_CHAIR = "models/props_c17/furniturechair001a.mdl"
P_CRATE = "models/props_junk/wood_crate001a.mdl"
P_CRATE2 = "models/props_junk/wood_crate002a.mdl"
P_BARREL = "models/props_c17/oildrum001.mdl"
P_BLUEBARREL = "models/props_borealis/bluebarrel001.mdl"
P_BENCH = "models/props_c17/bench01a.mdl"
P_CUPBOARD = "models/props_c17/furniturecupboard001a.mdl"
P_COUCH = "models/props_interiors/furniture_couch01a.mdl"
P_STOVE = "models/props_c17/furniturestove001a.mdl"
P_BED = "models/props_c17/furniturebed001a.mdl"
P_DRAWER = "models/props_c17/furnituredrawer001a.mdl"
P_CLEAT = "models/props_borealis/mooring_cleat01.mdl"
P_PALLET = "models/props_junk/wood_pallet001a.mdl"


def furnish(w, info, kind, seed=0, counter_mat=M.PLANKS_DARK):
    """Mobilier simple ; le "fond" de la piece est le mur oppose a la premiere porte."""
    ix0, iy0, ix1, iy1 = info["inner"]
    zf = info["zf"]
    cx, cy = (ix0 + ix1) / 2, (iy0 + iy1) / 2
    door = info["doors"][0][0] if info.get("doors") else "-y"
    # repere local : +v = vers le fond, u = lateral
    if door == "-y":
        U, V = (1, 0), (0, 1)
        hu, hv = (ix1 - ix0) / 2, (iy1 - iy0) / 2
    elif door == "+y":
        U, V = (-1, 0), (0, -1)
        hu, hv = (ix1 - ix0) / 2, (iy1 - iy0) / 2
    elif door == "-x":
        U, V = (0, -1), (1, 0)
        hu, hv = (iy1 - iy0) / 2, (ix1 - ix0) / 2
    else:
        U, V = (0, 1), (-1, 0)
        hu, hv = (iy1 - iy0) / 2, (ix1 - ix0) / 2
    base_yaw = math.degrees(math.atan2(V[1], V[0]))

    def P(u, v, z=0.0):
        return (cx + U[0] * u + V[0] * v, cy + U[1] * u + V[1] * v, zf + z)

    def rect(u0, v0, u1, v1, z0, z1, spec):
        a = P(u0, v0)
        b = P(u1, v1)
        return G.box(a[0], a[1], zf + z0, b[0], b[1], zf + z1, spec)

    rng = np.random.default_rng(seed)
    if info.get("levels", 1) >= 2:
        hv_free = hv - 90
    else:
        hv_free = hv
    if kind in ("bar", "restaurant"):
        w.add(rect(-hu * 0.6, hv_free - 72, hu * 0.4, hv_free - 32, 0, 44,
                   {"top": M.PLANKS, "default": counter_mat}))
        n = max(1, int((2 * hu - 120) // 170))
        for i in range(n):
            u = -hu + 100 + i * 170
            w.prop(P_TABLE, P(u, -hv * 0.15, 18), rng.integers(0, 4) * 90)
            w.prop(P_CHAIR, P(u - 40, -hv * 0.15, 20), base_yaw - 90)
            w.prop(P_CHAIR, P(u + 40, -hv * 0.15, 20), base_yaw + 90)
        w.prop(P_BARREL, P(hu - 40, hv_free - 40, 0), 0)
    elif kind == "shop":
        w.add(rect(-hu * 0.5, hv_free - 110, hu * 0.5, hv_free - 74, 0, 44,
                   {"top": M.PLANKS, "default": counter_mat}))
        w.prop(P_CRATE, P(-hu + 40, hv_free - 40, 20), 10)
        w.prop(P_CRATE2, P(hu - 40, hv_free - 40, 20), 0)
        w.prop(P_CUPBOARD, P(hu - 30, 0, 40), base_yaw + 90)
    elif kind == "office":
        w.add(rect(-64, hv * 0.15, 64, hv * 0.15 + 44, 0, 36, {"default": M.PLANKS_DARK}))
        w.prop(P_CHAIR, P(0, hv * 0.15 + 80, 20), base_yaw + 180)
        w.prop(P_CUPBOARD, P(-hu + 30, 0, 40), base_yaw - 90)
        w.prop(P_DRAWER, P(hu - 24, 0, 20), base_yaw + 90)
    elif kind == "house":
        w.prop(P_BED, P(hu - 60, hv_free - 60, 20), base_yaw + 180)
        w.prop(P_TABLE, P(0, 0, 18), 0)
        w.prop(P_CHAIR, P(-40, 0, 20), base_yaw)
        w.prop(P_STOVE, P(-hu + 30, hv_free - 30, 20), base_yaw + 180)
    elif kind == "storage":
        for i in range(5):
            w.prop(P_CRATE, P(rng.uniform(-hu + 40, hu - 40), rng.uniform(0, hv_free - 40), 20),
                   rng.integers(0, 90))
        w.prop(P_BARREL, P(hu - 40, hv_free - 40, 0), 0)
    elif kind == "barracks":
        n = max(1, int((2 * hu - 80) // 96))
        for i in range(n):
            w.prop(P_BED, P(-hu + 56 + i * 96, hv_free - 60, 20), base_yaw + 90)


# ---------------------------------------------------------------------------
# Elements divers
# ---------------------------------------------------------------------------

def cannon(w, x, y, z, yaw, L=110):
    f = G.Frame(x, y, z, yaw)
    w.add(f.box(-40, -32, 0, 30, 32, 26, M.PLANKS_DARK))
    for s in (-1, 1):
        w.add(f.cyl((0, s * 34, 20), (0, s * 26, 20), 22, 8, M.WOOD_BEAM))
    w.add(f.cyl((-30, 0, 40), (L, 0, 48), 16, 8, M.IRON, r1=12))


def flagpole(w, x, y, z, flag, h=420, yaw=0, size=(160, 110)):
    w.add(G.prism(x, y, 6, 6, z, z + h, M.WHITE_PAINT))
    w.add(G.prism(x, y, 10, 6, z + h, z + h + 12, M.GOLD))
    f = G.Frame(x, y, z, yaw)
    fw, fh_ = size
    w.add(f.box(-2, 8, h - fh_ - 10, 2, 8 + fw, h - 10,
                {"+x": Mat(flag, fit=True), "-x": Mat(flag, fit=True), "default": M.SAIL}))


def lighthouse(w, x, y, z, h=900, r=110, wall=M.WHITE, band=M.RED, cap=M.ROOF_RED):
    w.add(G.frustum(x, y, r + 40, r + 20, z - 40, z + 30, 12, M.STONE_GREY))
    n = 5
    seg = h / n
    for i in range(n):
        rr0 = r - i * 8
        rr1 = r - (i + 1) * 8
        w.add(G.frustum(x, y, rr0, rr1, z + 30 + i * seg, z + 30 + (i + 1) * seg, 12,
                        {"default": band if i % 2 else wall, "top": M.STONE_GREY}))
    top = z + 30 + h
    w.add(G.prism(x, y, r, 12, top, top + 16, M.IRON))
    w.add(G.prism(x, y, r * 0.55, 12, top + 16, top + 110, M.GLOW_WARM))
    w.add(G.frustum(x, y, r * 0.75, 0, top + 110, top + 200, 12, cap))
    w.light((x, y, top + 60), (255, 230, 170), 2500, fifty=600, zero=2600)
    return top


def quay_terrain(w, poly, z_top, top=M.PAVING, side=M.STONE_GREY, flare=1.05):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    base = G.scale_poly(poly, cx, cy, flare)
    w.add(G.poly_frustum(base, poly, -768, z_top, {"top": top, "default": side}))
    from .relief import register
    register(w, poly, z_top, top)


def water_steps(w, x0, y0, x1, y1, z0, z1, rise, mat=M.STONE_GREY):
    """Escalier/rampe pour sortir de l'eau."""
    w.add(G.ramp(x0, y0, z0, x1, y1, z1, rise, {"top": mat, "default": mat}))


# ---------------------------------------------------------------------------
# Capitainerie : location de bateaux (gere par sv_onepiece_boats.lua)
# ---------------------------------------------------------------------------

def harbor(w, key, x, y, z, yaw, pier=520, sign=None):
    """Cabane de capitainerie face a la mer (+x local) + ponton + point d'apparition du bateau.

    Le bouton "boat_btn_<cle>" appelle OP_BoatRental() ; le bateau apparait
    sur "boat_spawn_<cle>", au bout du ponton.
    """
    f = G.Frame(x, y, z, yaw)
    # cabane ouverte vers le ponton
    w.add(f.box(-96, -96, -24, 96, 96, 10, {"top": M.PLANKS, "default": M.WOOD_BEAM}))
    w.add(f.box(-96, -96, 10, -80, 96, 150, Mat(M.PLANKS_LIGHT, scale=(128, 128))))
    w.add(f.box(-80, -96, 10, 96, -80, 150, Mat(M.PLANKS_LIGHT, scale=(128, 128))))
    w.add(f.box(-80, 80, 10, 96, 96, 150, Mat(M.PLANKS_LIGHT, scale=(128, 128))))
    w.add(f.hull([(-112, -112, 150), (112, -112, 150), (-112, 112, 150), (112, 112, 150),
                  (-112, -112, 160), (112, -112, 160), (-112, 112, 160), (112, 112, 160),
                  (0, -112, 230), (0, 112, 230)], {"default": M.ROOF_TEAL, "bottom": M.WOOD_BEAM}))
    sg = sign or M.sign_mat("capitainerie", "CAPITAINERIE", sub="Location de bateaux",
                            color=(255, 240, 190), board=(40, 80, 140))
    w.add(f.box(96, -88, 104, 104, 88, 148, {"+x": Mat(sg, fit=True), "default": M.WOOD_BEAM}))
    # bouton (mur du fond, cote interieur)
    btn = f.box(-80, -14, 54, -76, 14, 82, M.RED)
    e = w.ent("func_button", brushes=btn, targetname=f"boat_btn_{key}", spawnflags=1 | 1024,
              speed=5, wait=2, lip=2, sounds=0, rendercolor="255 255 255", renderamt=255)
    add_output(e, "OnPressed", "op_boat_lua", "RunCode")
    w.add(f.box(-80, -40, 90, -77, 40, 120, {"+x": Mat(M.sign_mat("louer", "LOUER UN BATEAU",
                                                                  board=(150, 40, 40)), fit=True),
                                             "default": M.WOOD_BEAM}))
    w.light(f.p(0, 0, 130), (255, 220, 170), 90)
    # ponton
    w.add(f.box(96, -64, -6, 96 + pier, 64, 9, {"top": M.PLANKS_LIGHT, "default": M.WOOD_BEAM}))
    for d in range(200, int(pier) + 1, 220):
        for s in (-1, 1):
            w.add(G.prism(*f.p(96 + d, s * 56)[:2], 8, 6, -400, z + 18, M.WOOD_BEAM))
    w.prop(P_CLEAT, f.p(96 + pier - 30, 70, 6), yaw)
    # bateau : apparait a cote du bout du ponton
    w.ent("info_target", f.p(96 + pier + 220, 0, -z + 18), targetname=f"boat_spawn_{key}",
          angles=(0, yaw, 0))
    w.marker(f"Capitainerie ({key})", (x, y, z), "lieu")


# ---------------------------------------------------------------------------
# Passage entre niveaux : deux enormes rochers, le teleporteur est entre eux
# ---------------------------------------------------------------------------

def level_gate(w, x, y, yaw, sign_mat, gid, gap=1100):
    """yaw = direction de traversee. Le passage (gap) laisse passer un grand navire."""
    f = G.Frame(x, y, 0, yaw)
    rng = np.random.default_rng(zlib.crc32(gid.encode()))
    for s in (-1, 1):
        cy = s * (gap / 2 + 620)
        # gros rochers empiles (formes organiques)
        bx, by = f.p(0, cy)[:2]
        w.add(G.boulder(bx, by, -200, 780, 640, 760, rng.integers(1 << 30), M.ROCK, 34, flat_bottom=-768))
        tx, ty = f.p(rng.uniform(-80, 80), cy + s * 40)[:2]
        w.add(G.boulder(tx, ty, 1100, 560, 470, 1250, rng.integers(1 << 30), M.ROCK, 34))
        px, py = f.p(rng.uniform(-60, 60), cy + s * 90)[:2]
        w.add(G.boulder(px, py, 2150, 300, 260, 420, rng.integers(1 << 30), M.ROCK, 26))
        for k in range(3):
            ox, oy = rng.uniform(-520, 520), s * rng.uniform(250, 650)
            px, py = f.p(ox, cy + oy)[:2]
            r = rng.uniform(280, 430)
            w.add(G.boulder(px, py, rng.uniform(-200, 250), r, r * 0.85, rng.uniform(500, 800),
                            rng.integers(1 << 30), M.ROCK_DARK, 26, flat_bottom=-768))
        # torches sur les rochers
        w.light(f.p(-300, s * (gap / 2 + 120), 420), (255, 190, 120), 1600, fifty=500, zero=1800)
        # panneau sur pilotis devant le rocher, face aux navires
        if s < 0:
            for py in (-gap / 2 - 60, -gap / 2 - 360):
                w.add(G.prism(*f.p(-420, py)[:2], 14, 6, -500, 340, M.WOOD_BEAM))
            w.add(f.box(-430, -gap / 2 - 420, 240, -414, -gap / 2 - 0, 360,
                        {"-x": Mat(sign_mat, fit=True), "+x": Mat(sign_mat, fit=True), "default": M.WOOD_BEAM}))
    # brume tourbillonnante (visuel) + declencheur reserve aux bateaux
    memb = f.box(-3, -gap / 2 - 40, -96, 3, gap / 2 + 40, 900,
                 {"+x": Mat(M.PORTAL, fit=True), "-x": Mat(M.PORTAL, fit=True), "default": M.NODRAW})
    w.ent("func_illusionary", brushes=memb, rendermode=0, renderamt=255, disableshadows=1)
    gate_triggers(w, f.box(-64, -gap / 2 + 20, -560, 64, gap / 2 - 20, 900, M.TRIGGER), gid)
    w.light(f.p(0, 0, 360), (130, 230, 255), 2400, fifty=600, zero=2200)
    w.light(f.p(-500, 0, 200), (130, 230, 255), 1200, fifty=500, zero=1600)
