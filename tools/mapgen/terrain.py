"""Grandes iles naturelles en displacements (relief, plages, montagnes, forets).

Chaque ile garde sa ville (construite par son module, a plat) et recoit autour
un vrai terrain : cote irreguliere avec criques, plages, collines, montagnes,
forets. Le terrain est aplani automatiquement autour de chaque construction.

Le relief est decoupe en carreaux de 1024 unites (displacements de puissance 4,
sommets tous les 64 unites). Les carreaux voisins partagent exactement les
memes hauteurs sur leurs bords.
"""
import math

import numpy as np

from . import geom as G
from . import layout as L
from . import materials as M
from .geom import Mat

CELL = 1024
POWER = 4
STEP = CELL // (2 ** POWER)
BASE = L.SEA_FLOOR + 8          # face de base des carreaux (-760)

# rock_alt : altitudes ou la roche apparait (None = seulement sur les pentes raides)
BIOMES = {
    "herbe": dict(main=M.GRASS, beach=M.SAND, rock=M.ROCK, rock_alt=(650, 950), peak=None,
                  trees=("rond", "rond", "pin"), pine=M.PINE_GREEN),
    "tropical": dict(main=M.GRASS, beach=M.SAND, rock=M.ROCK, rock_alt=(650, 950), peak=None,
                     trees=("rond", "palmier")),
    "desert": dict(main=M.DESERT, beach=M.SAND, rock=M.SANDSTONE, rock_alt=(420, 700), peak=None,
                   trees=("palmier",)),
    "neige": dict(main=M.SNOW, beach=M.SAND, rock=M.ROCK, rock_alt=None, peak=None, trees=("pin",)),
    "wano": dict(main=M.GRASS_DARK, beach=M.SAND, rock=M.ROCK, rock_alt=(600, 900), peak=M.SNOW,
                 trees=("sakura", "pin", "sakura")),
    "roche": dict(main=M.ROCK_DARK, beach=M.SAND, rock=M.ROCK, rock_alt=(500, 800), peak=None, trees=()),
}


# ---------------------------------------------------------------------------
# Bruit
# ---------------------------------------------------------------------------

class Noise:
    def __init__(self, seed):
        self.t = np.random.default_rng(seed).random((256, 256))

    def value(self, x, y):
        xi = np.floor(x).astype(int)
        yi = np.floor(y).astype(int)
        fx, fy = x - xi, y - yi
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        t = self.t
        a = t[xi & 255, yi & 255]
        b = t[(xi + 1) & 255, yi & 255]
        c = t[xi & 255, (yi + 1) & 255]
        d = t[(xi + 1) & 255, (yi + 1) & 255]
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def fbm(self, x, y, scale, octaves=4):
        s, amp, tot, norm = 1.0 / scale, 1.0, 0.0, 0.0
        for o in range(octaves):
            tot = tot + amp * self.value(x * s + o * 31.7, y * s + o * 17.3)
            norm += amp
            amp *= 0.5
            s *= 2.0
        return tot / norm

    def ridged(self, x, y, scale, octaves=4):
        s, amp, tot, norm = 1.0 / scale, 1.0, 0.0, 0.0
        for o in range(octaves):
            n = 1 - np.abs(2 * self.value(x * s + o * 11.1, y * s + o * 7.7) - 1)
            tot = tot + amp * n * n
            norm += amp
            amp *= 0.5
            s *= 2.0
        return tot / norm


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def angdiff(a, b):
    return np.abs((a - b + np.pi) % (2 * np.pi) - np.pi)


# ---------------------------------------------------------------------------
# Forme d'une ile
# ---------------------------------------------------------------------------

class Island:
    def __init__(self, key):
        spec = L.SHAPES[key]
        self.key = key
        self.spec = spec
        self.cx, self.cy = L.center(key)
        R = L.radius(key)
        self.land = spec.get("land", L.LAND_Z)
        self.core = spec.get("core", 0.77 * R)          # cote de la ville (rayon)
        self.custom_core = spec.get("custom_core")       # ile dont le centre est fait de brushes
        self.big = spec["big"]
        self.biome = BIOMES[spec["biome"]]
        ax, ay, _, _ = L.arrival_point(key)
        self.port = math.atan2(ay - self.cy, ax - self.cx)
        self.opens = [self.port] + [math.radians(a) for a in spec.get("open", [])]
        self.lobes = [(math.radians(a), math.radians(wd)) for a, wd in spec.get("lobes", [])]
        rng = np.random.default_rng(spec.get("seed", 1))
        self.harm = [(m, rng.uniform(-1, 1) * 0.16 / m ** 0.5, rng.uniform(0, 6.283)) for m in range(2, 9)]
        self.noise = Noise(spec.get("seed", 1) + 1000)
        back = self.port + math.pi
        self.peaks = []
        for a, dist, h, rad in spec.get("peaks", []):
            ang = back + math.radians(a)
            self.peaks.append((self.cx + math.cos(ang) * dist, self.cy + math.sin(ang) * dist, h, rad))
        self.footprints = np.zeros((0, 4))

    def extension(self, th):
        """0 = cote de la ville (pas d'extension), 1 = grande ile."""
        if self.lobes:
            f = np.zeros_like(th)
            for a, wd in self.lobes:
                f = np.maximum(f, 1 - smooth(wd * 0.6, wd, angdiff(th, a)))
            return f
        dmin = np.full_like(th, 10.0)
        for a in self.opens:
            dmin = np.minimum(dmin, angdiff(th, a))
        return smooth(math.radians(50), math.radians(105), dmin)

    def coast(self, th):
        n = sum(c * np.cos(m * th + p) for m, c, p in self.harm)
        big = self.big * (1 + n)
        f = self.extension(th)
        return self.core + np.maximum(big - self.core, 0) * f

    def natural(self, X, Y):
        dx, dy = X - self.cx, Y - self.cy
        r = np.hypot(dx, dy)
        th = np.arctan2(dy, dx)
        rc = self.coast(th)
        d = rc - r
        sea = -760 * smooth(0, 950, -d) ** 0.85
        base = self.land * smooth(0, 380, d)
        nz = self.noise
        sp = self.spec
        relief = (sp.get("hills", 90) * nz.fbm(X, Y, 1400, 3)
                  + sp.get("mountains", 300) * nz.ridged(X, Y, 2600, 4) ** 1.6)
        for px, py, ph, pr in self.peaks:
            q = np.hypot(X - px, Y - py) / pr
            relief = relief + ph * np.exp(-q * q * 1.6) * (0.85 + 0.3 * nz.fbm(X, Y, 500, 2))
        if self.custom_core:
            # autour d'une ville en brushes : relief qui monte doucement, pas de mur colle aux quais
            zone = smooth(self.custom_core + 700, self.custom_core + 2200, r)
        else:
            zone = smooth(self.core * 0.85, self.core + 900, r)
        h = np.where(d < 0, sea, base + relief * zone * smooth(250, 1100, d))
        if self.custom_core:
            # le centre est construit en brushes : ici le terrain reste sous l'eau
            inner = r - self.custom_core
            h = np.where(inner < 0, -760, np.minimum(h, -120 + (self.land + 120) * smooth(0, 900, inner)
                                                      + np.maximum(h - self.land, 0)))
        return np.maximum(h, -760)

    def coast_distance(self, X, Y):
        dx, dy = X - self.cx, Y - self.cy
        return self.coast(np.arctan2(dy, dx)) - np.hypot(dx, dy)

    def height(self, X, Y):
        h = self.natural(X, Y)
        if len(self.footprints):
            D = self.footprint_distance(X, Y)
            m = 1 - smooth(150, 700, D)
            if not self.custom_core:
                # la plage garde sa pente : pas d'aplanissement au bord de l'eau
                m = m * smooth(120, 420, self.coast_distance(X, Y))
            allowed = h > -300
            if self.custom_core:
                allowed &= np.hypot(X - self.cx, Y - self.cy) > self.custom_core
            h = np.where(allowed, h * (1 - m) + self.land * m, h)
        return h

    def footprint_distance(self, X, Y):
        D = np.full(X.shape, 1e9)
        for x0, y0, x1, y1 in self.footprints:
            ddx = np.maximum(np.maximum(x0 - X, X - x1), 0)
            ddy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
            D = np.minimum(D, np.hypot(ddx, ddy))
        return D

    def bounds(self):
        R = self.big * 1.3 + 1100
        return self.cx - R, self.cy - R, self.cx + R, self.cy + R


# ---------------------------------------------------------------------------
# Constructions a respecter (aplanir autour)
# ---------------------------------------------------------------------------

TREE_MATS = {M.BARK, M.PALM, M.LEAVES, M.CANOPY, M.SAKURA, M.PINE, M.PINE_GREEN, M.MANGROVE}
DOCK_MATS = {M.PLANKS_LIGHT, M.PLANKS_DARK, M.PLANKS}


def collect_footprints(w, isl, dz):
    group = L.ISLANDS[isl.key][0]
    brushes = list(w.detail.get(group, []))
    for e in w.entities:
        if e.group == group:
            brushes.extend(e.brushes)
    rects = []
    land = isl.land
    for b in brushes:
        lo, hi = b.bbox
        zlo, zhi = lo[2] - dz, hi[2] - dz
        if not (land - 90 <= zlo <= land + 40 and zhi >= land + 4):
            continue
        mats = {f.mat.name for f in b.faces}
        if mats & TREE_MATS:
            continue
        top = [f for f in b.faces if f.normal[2] > 0.99]
        if top and top[0].mat.name in DOCK_MATS and zhi - zlo < 24:
            continue
        rects.append((lo[0], lo[1], hi[0], hi[1]))
    for e in w.entities:
        if e.group == group and "origin" in e.kv and e.classname in (
                "prop_static", "info_target", "info_player_start", "info_teleport_destination"):
            x, y, z = (float(v) for v in e.kv["origin"].split())
            if land - 90 <= z - dz <= land + 120:
                rects.append((x - 40, y - 40, x + 40, y + 40))
    isl.footprints = np.array(rects) if rects else np.zeros((0, 4))


# ---------------------------------------------------------------------------
# Carreaux de displacement + forets
# ---------------------------------------------------------------------------

def _mat_pair(isl, H, S):
    bio = isl.biome
    if H.max() < -60:
        return M.SAND, None        # fond marin : meme sable que le reste du fond
    sand = 1 - smooth(28, 60, H)
    alt = isl.spec.get("rock_alt", bio["rock_alt"])
    rock = smooth(0.65, 1.0, S) + (smooth(alt[0], alt[1], H) if alt else 0)
    # pas de roche sous l'eau ni sur la plage (sinon herbe visible sous l'eau)
    rock = np.clip(rock, 0, 1) * smooth(60, 120, H)
    if bio["peak"] is not None and H.max() > 1050:
        return M.blend(bio["rock"], bio["peak"]), smooth(1050, 1250, H)
    if sand.max() > 0.02:
        return M.blend(bio["main"], bio["beach"]), sand
    if rock.max() > 0.02:
        return M.blend(bio["main"], bio["rock"]), rock
    return bio["main"], None


def build_island(w, key, dz):
    isl = Island(key)
    collect_footprints(w, isl, dz)
    x0, y0, x1, y1 = isl.bounds()
    gx0, gy0 = int(math.floor(x0 / CELL)), int(math.floor(y0 / CELL))
    gx1, gy1 = int(math.ceil(x1 / CELL)), int(math.ceil(y1 / CELL))
    lim = L.MAP_HALF
    n = 2 ** POWER + 1
    count = 0
    for gx in range(gx0, gx1):
        for gy in range(gy0, gy1):
            px0, py0 = gx * CELL, gy * CELL
            if px0 < -lim or py0 < -lim or px0 + CELL > lim or py0 + CELL > lim:
                continue
            xs = px0 + np.arange(n) * STEP
            ys = py0 + np.arange(n) * STEP
            X, Y = np.meshgrid(xs, ys)          # ligne i = y, colonne j = x
            H = isl.height(X, Y)
            if H.max() <= -750:
                continue
            gy_, gx_ = np.gradient(H, STEP)
            S = np.hypot(gx_, gy_)
            mat, alpha = _mat_pair(isl, H, S)
            heights = (H - BASE).round(2).tolist()
            b = G.disp_patch(px0, py0, px0 + CELL, py0 + CELL, BASE, heights,
                             Mat(mat, lms=64), POWER)
            if alpha is not None:
                for f in b.faces:
                    if f.disp is not None:
                        f.disp["alphas"] = (alpha * 255).round(1).tolist()
            w.add_world(b)
            count += 1
    trees = plant_forest(w, isl)
    return isl, count, trees


def plant_forest(w, isl):
    sp = isl.spec
    density = sp.get("forest", 0.5)
    kinds = isl.biome["trees"]
    if density <= 0 or not kinds:
        return 0
    rng = np.random.default_rng(sp.get("seed", 1) + 77)
    x0, y0, x1, y1 = isl.bounds()
    step = 380
    xs = np.arange(x0, x1, step)
    ys = np.arange(y0, y1, step)
    X, Y = np.meshgrid(xs, ys)
    X = X + rng.uniform(-150, 150, X.shape)
    Y = Y + rng.uniform(-150, 150, Y.shape)
    H = isl.height(X, Y)
    Hx = isl.height(X + 40, Y)
    Hy = isl.height(X, Y + 40)
    slope = np.hypot(Hx - H, Hy - H) / 40
    D = isl.footprint_distance(X, Y) if len(isl.footprints) else np.full(X.shape, 1e9)
    forest = isl.noise.fbm(X + 999, Y - 333, 1800, 3)
    ok = ((H > isl.land + 6) & (H < 1150) & (slope < 0.55) & (D > 420) & (forest > 1 - density * 0.85)
          & (np.abs(X) < L.MAP_HALF - 300) & (np.abs(Y) < L.MAP_HALF - 300))
    if isl.custom_core:
        ok &= np.hypot(X - isl.cx, Y - isl.cy) > isl.custom_core + 400
    idx = np.argwhere(ok)
    cap = sp.get("max_trees", 130)
    if len(idx) > cap:
        idx = idx[rng.choice(len(idx), cap, replace=False)]
    for k, (i, j) in enumerate(idx):
        x, y, z = float(X[i, j]), float(Y[i, j]), float(H[i, j])
        kind = kinds[k % len(kinds)]
        if kind == "pin" or (H[i, j] > 750 and "pin" in kinds):
            tree_pine(w, x, y, z, rng, isl.biome.get("pine", M.PINE))
        elif kind == "palmier":
            from . import kit as K
            K.palm(w, x, y, z - 8, rng.uniform(320, 440), seed=int(rng.integers(1 << 30)), fronds=4)
        elif kind == "sakura":
            tree_round(w, x, y, z, rng, M.SAKURA)
        else:
            tree_round(w, x, y, z, rng, M.LEAVES)
    return len(idx)


def _trunk_or(mat):
    def fn(f):
        return M.BARK if f.normal[2] < -0.25 else mat
    return fn


def tree_pine(w, x, y, z, rng, mat=M.PINE):
    """Sapin d'une seule piece, peu de faces (budget de plans du moteur)."""
    h = rng.uniform(480, 720)
    r = h * rng.uniform(0.24, 0.3)
    a0 = rng.uniform(0, 6.28)
    # pied court et large : plus de "toupie" posee sur sa pointe (meme nombre de points et de faces)
    pts = [(x + math.cos(a0 + a) * r * 0.3, y + math.sin(a0 + a) * r * 0.3, z - 40) for a in (0, 2.09, 4.19)]
    pts += [(x + math.cos(a0 + a) * r, y + math.sin(a0 + a) * r, z + h * 0.12)
            for a in np.linspace(0, 6.28, 5, endpoint=False)]
    pts.append((x, y, z + h))
    w.add(G.brush(pts, mat).retexture(_trunk_or(mat)))


def tree_round(w, x, y, z, rng, mat):
    """Arbre feuillu d'une seule piece (tronc + houppier), peu de faces."""
    h = rng.uniform(380, 560)
    r = h * rng.uniform(0.32, 0.42)
    a0 = rng.uniform(0, 6.28)
    # houppier arrondi : deux couronnes decalees + sommet (moins "diamant")
    # pied large et enterre : l'arbre ne tient plus en equilibre sur une pointe
    pts = [(x + math.cos(a0 + a) * r * 0.22, y + math.sin(a0 + a) * r * 0.22, z - 40) for a in (0, 2.09, 4.19)]
    pts += [(x + math.cos(a0 + a) * r * 0.8, y + math.sin(a0 + a) * r * 0.8, z + h * 0.4)
            for a in (0, 1.571, 3.142, 4.712)]
    pts += [(x + math.cos(a0 + a + 0.785) * r, y + math.sin(a0 + a + 0.785) * r, z + h * 0.72)
            for a in (0, 1.571, 3.142, 4.712)]
    pts.append((x, y, z + h * 0.97))
    w.add(G.brush(pts, mat).retexture(_trunk_or(mat)))


def build_all(w):
    stats = {}
    islands = {}
    for key in L.SHAPES:
        lv = L.ISLAND_LEVEL[key]
        dz = L.sea_z(lv)
        with w.level(lv, dz), w.group(L.ISLANDS[key][0]):
            isl, n, t = build_island(w, key, dz)
        islands[key] = isl
        stats[key] = (n, t)
    w.terrain = islands
    return stats
