"""Geometrie des brushes Source.

Chaque brush est un polyedre convexe construit a partir d'un nuage de points
(enveloppe convexe). Les faces gardent une specification de materiau qui est
resolue selon la normale de la face (dessus / dessous / cotes / direction).

Convention Source (Hammer) : les 3 points d'un plan sont donnes dans le sens
horaire vu de l'exterieur ; la normale sortante vaut (p3-p1) x (p2-p1).
"""
import math

import numpy as np
from scipy.spatial import ConvexHull


class Mat:
    """Materiau + options d'alignement de texture pour une face.

    fit    : la texture couvre exactement la face (panneaux, drapeaux...)
    origin : point d'alignement (decalage) de la texture
    scale  : (u, v) unites de map par tuile de texture (remplace le defaut)
    lms    : lightmapscale specifique
    """

    __slots__ = ("name", "fit", "origin", "scale", "lms", "flip")

    def __init__(self, name, fit=False, origin=None, scale=None, lms=None, flip=False):
        self.name = name
        self.fit = fit
        self.origin = origin
        self.scale = scale
        self.lms = lms
        self.flip = flip

    def __repr__(self):
        return f"Mat({self.name!r})"


def as_mat(m):
    return m if isinstance(m, Mat) else Mat(m)


def pick_material(spec, n):
    """Choisit le materiau d'une face selon sa normale sortante n."""
    if isinstance(spec, (str, Mat)):
        return as_mat(spec)
    nx, ny, nz = n
    if nz > 0.7 and "top" in spec:
        return as_mat(spec["top"])
    if nz < -0.7 and "bottom" in spec:
        return as_mat(spec["bottom"])
    if abs(nz) <= 0.7:
        if abs(nx) >= abs(ny):
            key = "+x" if nx > 0 else "-x"
        else:
            key = "+y" if ny > 0 else "-y"
        if key in spec:
            return as_mat(spec[key])
        if "side" in spec:
            return as_mat(spec["side"])
    if "slope" in spec and 0.05 < abs(nz) < 0.999:
        return as_mat(spec["slope"])
    for k in ("all", "default", "side", "top"):
        if k in spec:
            return as_mat(spec[k])
    raise ValueError(f"spec materiau sans defaut: {spec}")


class Face:
    __slots__ = ("plane_pts", "normal", "dist", "mat", "poly")

    def __init__(self, plane_pts, normal, dist, mat, poly):
        self.plane_pts = plane_pts  # 3 points entiers (ordre Valve, horaire)
        self.normal = normal
        self.dist = dist
        self.mat = mat
        self.poly = poly  # polygone CCW vu de l'exterieur (apercu)


class Brush:
    __slots__ = ("faces", "bbox")

    def __init__(self, faces):
        self.faces = faces
        allp = np.vstack([f.poly for f in faces])
        self.bbox = (allp.min(0), allp.max(0))

    def retexture(self, fn):
        for f in self.faces:
            f.mat = as_mat(fn(f))
        return self


def _sort_ccw(pts, n):
    c = pts.mean(0)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    d = pts - c
    ang = np.arctan2(d @ e2, d @ e1)
    return pts[np.argsort(ang)]


def _best_triangle(poly):
    """Trois sommets du polygone donnant le plus grand triangle (ordre CCW)."""
    m = len(poly)
    best, bi = -1, (0, 1, 2)
    if m <= 12:
        for i in range(m):
            for j in range(i + 1, m):
                for k in range(j + 1, m):
                    a = np.linalg.norm(np.cross(poly[j] - poly[i], poly[k] - poly[i]))
                    if a > best:
                        best, bi = a, (i, j, k)
    else:
        i = 0
        j = m // 3
        k = (2 * m) // 3
        bi = (i, j, k)
    return [poly[i] for i in bi]


def brush(points, spec):
    """Brush convexe a partir d'un nuage de points (arrondis a l'entier)."""
    P = np.round(np.asarray(points, dtype=float))
    P = np.unique(P, axis=0)
    if len(P) < 4:
        raise ValueError("brush degenere (moins de 4 points)")
    hull = ConvexHull(P)
    groups = []
    for simp, eq in zip(hull.simplices, hull.equations):
        n = eq[:3]
        pts = P[simp]
        for g in groups:
            if float(np.dot(g[0], n)) > 0.9995 and np.all(np.abs(pts @ g[0] - g[1]) < 0.75):
                g[2].update(simp.tolist())
                break
        else:
            groups.append([n, float(n @ pts[0]), set(simp.tolist())])
    faces = []
    for n, d, idx in groups:
        poly = _sort_ccw(P[sorted(idx)], n)
        a, b, c = _best_triangle(poly)
        # normale exacte des 3 points retenus
        nn = np.cross(b - a, c - a)
        ln = np.linalg.norm(nn)
        if ln < 1e-6:
            raise ValueError("face degeneree")
        nn /= ln
        mat = pick_material(spec, nn)
        faces.append(Face((a, c, b), nn, float(nn @ a), mat, poly))
    return Brush(faces)


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def box(x0, y0, z0, x1, y1, z1, spec):
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    za, zb = sorted((z0, z1))
    pts = [(x, y, z) for x in (xa, xb) for y in (ya, yb) for z in (za, zb)]
    return brush(pts, spec)


def ngon(cx, cy, r, sides, rot=0.0, ry=None):
    ry = r if ry is None else ry
    out = []
    for i in range(sides):
        a = math.radians(rot) + 2 * math.pi * i / sides
        out.append((cx + r * math.cos(a), cy + ry * math.sin(a)))
    return out


def prism(cx, cy, r, sides, z0, z1, spec, rot=None, ry=None):
    if rot is None:
        rot = 180.0 / sides
    pts = [(x, y, z) for (x, y) in ngon(cx, cy, r, sides, rot, ry) for z in (z0, z1)]
    return brush(pts, spec)


def frustum(cx, cy, r0, r1, z0, z1, sides, spec, rot=None, ry0=None, ry1=None):
    if rot is None:
        rot = 180.0 / sides
    pts = [(x, y, z0) for (x, y) in ngon(cx, cy, r0, sides, rot, ry0)]
    if r1 <= 0.5:
        pts.append((cx, cy, z1))
    else:
        pts += [(x, y, z1) for (x, y) in ngon(cx, cy, r1, sides, rot, ry1)]
    return brush(pts, spec)


def poly_frustum(poly0, poly1, z0, z1, spec):
    pts = [(x, y, z0) for (x, y) in poly0] + [(x, y, z1) for (x, y) in poly1]
    return brush(pts, spec)


def poly_prism(poly, z0, z1, spec):
    return poly_frustum(poly, poly, z0, z1, spec)


def ramp(x0, y0, z0, x1, y1, z1, rise, spec):
    """Rampe pleine montant vers la direction rise ('+x','-x','+y','-y')."""
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    za, zb = sorted((z0, z1))
    base = [(x, y, za) for x in (xa, xb) for y in (ya, yb)]
    if rise == "+x":
        top = [(xb, ya, zb), (xb, yb, zb)]
    elif rise == "-x":
        top = [(xa, ya, zb), (xa, yb, zb)]
    elif rise == "+y":
        top = [(xa, yb, zb), (xb, yb, zb)]
    else:
        top = [(xa, ya, zb), (xb, ya, zb)]
    return brush(base + top, spec)


def gable(x0, y0, x1, y1, z0, h, axis, spec):
    """Toit a deux pans (prisme triangulaire), faitage selon axis 'x' ou 'y'."""
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    base = [(xa, ya, z0), (xb, ya, z0), (xa, yb, z0), (xb, yb, z0)]
    if axis == "x":
        ym = (ya + yb) / 2
        ridge = [(xa, ym, z0 + h), (xb, ym, z0 + h)]
    else:
        xm = (xa + xb) / 2
        ridge = [(xm, ya, z0 + h), (xm, yb, z0 + h)]
    return brush(base + ridge, spec)


def hip(x0, y0, x1, y1, z0, h, spec, ridge_frac=0.35):
    """Toit a quatre pans."""
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    base = [(xa, ya, z0), (xb, ya, z0), (xa, yb, z0), (xb, yb, z0)]
    cx, cy = (xa + xb) / 2, (ya + yb) / 2
    w, d = xb - xa, yb - ya
    if w >= d:
        hl = max(0.0, (w - d) / 2) + w * ridge_frac * 0.0
        ridge = [(cx - hl, cy, z0 + h), (cx + hl, cy, z0 + h)]
    else:
        hl = max(0.0, (d - w) / 2)
        ridge = [(cx, cy - hl, z0 + h), (cx, cy + hl, z0 + h)]
    if np.allclose(ridge[0], ridge[1]):
        ridge = [ridge[0]]
    return brush(base + ridge, spec)


def _perp_basis(axis):
    axis = axis / np.linalg.norm(axis)
    a = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0, 0])
    e1 = np.cross(axis, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    return e1, e2


def cylinder(p0, p1, r, sides, spec, r1=None):
    """Cylindre (ou tronc de cone) d'axe quelconque p0 -> p1."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    r1 = r if r1 is None else r1
    e1, e2 = _perp_basis(p1 - p0)
    pts = []
    for i in range(sides):
        a = 2 * math.pi * (i + 0.5) / sides
        d = math.cos(a) * e1 + math.sin(a) * e2
        pts.append(p0 + r * d)
        if r1 > 0.5:
            pts.append(p1 + r1 * d)
    if r1 <= 0.5:
        pts.append(p1)
    return brush(pts, spec)


class Frame:
    """Repere local : translation + rotation (yaw en degres)."""

    def __init__(self, x=0.0, y=0.0, z=0.0, yaw=0.0):
        self.o = np.array([x, y, z], float)
        self.yaw = yaw
        a = math.radians(yaw)
        self.c, self.s = math.cos(a), math.sin(a)

    def p(self, x, y, z=0.0):
        return (self.o[0] + x * self.c - y * self.s,
                self.o[1] + x * self.s + y * self.c,
                self.o[2] + z)

    def pts(self, lst):
        return [self.p(*q) for q in lst]

    def vec(self, x, y, z=0.0):
        return (x * self.c - y * self.s, x * self.s + y * self.c, z)

    def sub(self, x, y, z=0.0, yaw=0.0):
        X, Y, Z = self.p(x, y, z)
        return Frame(X, Y, Z, self.yaw + yaw)

    def box(self, x0, y0, z0, x1, y1, z1, spec):
        pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        return brush(self.pts(pts), spec)

    def hull(self, pts, spec):
        return brush(self.pts(pts), spec)

    def ramp(self, x0, y0, z0, x1, y1, z1, rise, spec):
        xa, xb = sorted((x0, x1))
        ya, yb = sorted((y0, y1))
        za, zb = sorted((z0, z1))
        base = [(x, y, za) for x in (xa, xb) for y in (ya, yb)]
        top = {"+x": [(xb, ya, zb), (xb, yb, zb)], "-x": [(xa, ya, zb), (xa, yb, zb)],
               "+y": [(xa, yb, zb), (xb, yb, zb)], "-y": [(xa, ya, zb), (xb, ya, zb)]}[rise]
        return brush(self.pts(base + top), spec)

    def cyl(self, a, b, r, sides, spec, r1=None):
        return cylinder(self.p(*a), self.p(*b), r, sides, spec, r1)


def convex_hull_2d(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def blob(cx, cy, rx, ry, sides, seed, jitter=0.08, rot=0.0):
    """Polygone convexe irregulier (forme d'ile)."""
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(sides):
        a = math.radians(rot) + 2 * math.pi * i / sides
        k = 1.0 + rng.uniform(-jitter, jitter)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return convex_hull_2d(pts)


def scale_poly(poly, cx, cy, s):
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in poly]
