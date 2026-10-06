"""Relief naturel (displacements) sur les zones libres des iles.

Chaque carreau garde des bords a hauteur 0 : il se raccorde toujours au terrain
plat voisin, quel que soit le sens de lecture des sommets par VBSP.
"""
import math

import numpy as np

from . import geom as G
from . import materials as M
from .checks import Solids

CELL = 768
POWER = 4
AMPLITUDES = {
    M.GRASS: (0, 50, 90, 140, 170),
    M.GRASS_DARK: (40, 90, 140, 180),
    M.DESERT: (40, 80, 130, 170),
    M.SNOW: (60, 110, 160, 200),
}
TREE_MATS = {M.BARK, M.PALM, M.LEAVES, M.CANOPY, M.SAKURA, M.PINE, M.MANGROVE}


def register(w, poly, z, mat):
    """Appele par les fonctions de terrain : surface plate pouvant recevoir du relief."""
    if mat not in AMPLITUDES:
        return
    dx, dy = w._dxy
    w.hill_surfaces.append(([(x + dx, y + dy) for x, y in poly], z + w._dz, mat))


def _inside(poly, x, y, margin):
    n = len(poly)
    # sens du polygone
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area > 0 else -1
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey) or 1
        cross = (ex * (y - ay) - ey * (x - ax)) / L * s
        if cross < margin:
            return False
    return True


def _heights(rng, amp, power=POWER):
    n = 2 ** power + 1
    u = np.linspace(0, 1, n)
    eu, ev = rng.uniform(0.7, 1.4, 2)
    wu = np.sin(np.pi * u ** eu) ** 2
    wv = np.sin(np.pi * u ** ev) ** 2
    a, b, ph = rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(0, 6.28)
    V, U = np.meshgrid(u, u, indexing="ij")
    irr = 1 + 0.3 * np.sin(2 * np.pi * (a * U + b * V) + ph)
    H = amp * np.outer(wv, wu) * irr
    H[0, :] = H[-1, :] = H[:, 0] = H[:, -1] = 0
    return [[round(float(v), 2) for v in row] for row in H]


def add_hills(w):
    S = Solids(w)
    keep = [i for i, (_, b) in enumerate(S.items) if b.faces[0].mat.name not in TREE_MATS]
    S.items = [S.items[i] for i in keep]
    S.mins, S.maxs = S.mins[keep], S.maxs[keep]
    S.pl = [None] * len(S.items)
    S.vx = [None] * len(S.items)
    points = []
    for e in w.entities:
        if e.classname in ("prop_static", "info_target", "info_teleport_destination", "info_player_start",
                           "func_button") and "origin" in e.kv:
            points.append(tuple(float(v) for v in e.kv["origin"].split()))
    points = np.array(points) if points else np.zeros((0, 3))
    count = 0
    taken = set()   # cellules de 384 deja occupees
    with w.group("Relief"):
        for cell, power in ((768, 4), (384, 3)):
            k = cell // 384
            for poly, z, mat in w.hill_surfaces:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                for gx in range(int(math.floor(min(xs) / cell)), int(math.ceil(max(xs) / cell))):
                    for gy in range(int(math.floor(min(ys) / cell)), int(math.ceil(max(ys) / cell))):
                        x0, y0 = gx * cell, gy * cell
                        x1, y1 = x0 + cell, y0 + cell
                        sub = {(gx * k + i, gy * k + j, round(z)) for i in range(k) for j in range(k)}
                        if sub & taken:
                            continue
                        if not all(_inside(poly, cx, cy, 64) for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))):
                            continue
                        if S.hits((x0 + 4, y0 + 4, z + 2), (x1 - 4, y1 - 4, z + 420)):
                            continue
                        if len(points):
                            m = ((points[:, 0] > x0 - 48) & (points[:, 0] < x1 + 48) & (points[:, 1] > y0 - 48) &
                                 (points[:, 1] < y1 + 48) & (points[:, 2] > z - 64) & (points[:, 2] < z + 400))
                            if m.any():
                                continue
                        rng = np.random.default_rng(((gx * 73856093) ^ (gy * 19349663) ^ int(z) ^ cell)
                                                    & 0xFFFFFFFF)
                        amp = float(rng.choice(AMPLITUDES[mat])) * cell / 768
                        taken |= sub
                        if amp <= 0:
                            continue
                        w.add_world(G.disp_patch(x0, y0, x1, y1, z + 1, _heights(rng, amp, power), mat, power))
                        count += 1
    return count
