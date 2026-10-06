"""Verifications de jouabilite (spawns, portes, portails) sur la map generee."""
import numpy as np

NONSOLID = {"trigger_teleport", "func_illusionary", "func_rotating", "trigger_multiple", "func_button"}
SKIP_MATS = {"onepiece/water_ocean", "onepiece/water_oasis", "onepiece/water_ocean_sky", "tools/toolsskybox"}


def _planes(b):
    out = []
    for f in b.faces:
        a, c, bb = (np.asarray(p, float) for p in f.plane_pts)
        n = np.cross(bb - a, c - a)
        n /= np.linalg.norm(n)
        out.append((n, float(n @ a)))
    return out


class Solids:
    def __init__(self, world):
        self.items = []
        for b in world.world:
            if any(f.mat.name in SKIP_MATS for f in b.faces):
                continue
            self.items.append(("world", b))
        for g, lst in world.detail.items():
            for b in lst:
                self.items.append((g, b))
        for e in world.entities:
            if e.classname in NONSOLID:
                continue
            for b in e.brushes:
                self.items.append((e.classname, b))
        self.mins = np.array([b.bbox[0] for _, b in self.items])
        self.maxs = np.array([b.bbox[1] for _, b in self.items])
        self.pl = [None] * len(self.items)
        self.vx = [None] * len(self.items)

    def hits(self, lo, hi, eps=0.5):
        lo = np.asarray(lo, float)
        hi = np.asarray(hi, float)
        cand = np.nonzero(np.all(self.mins < hi - eps, 1) & np.all(self.maxs > lo + eps, 1))[0]
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        out = []
        for i in cand:
            if self.pl[i] is None:
                self.pl[i] = _planes(self.items[i][1])
                self.vx[i] = np.vstack([f.poly for f in self.items[i][1].faces])
            V = self.vx[i]
            # axes de la boite (sommets du brush entierement d'un cote)
            if np.any(V.max(0) <= lo + eps) or np.any(V.min(0) >= hi - eps):
                continue
            sep = False
            for n, d in self.pl[i]:
                if np.all(corners @ n >= d - eps):
                    sep = True
                    break
            if not sep:
                out.append(self.items[i])
        return out


def run(world):
    from . import layout as L
    S = Solids(world)
    problems = []
    # chaque entite doit etre a l'interieur d'un niveau etanche (sinon : fuite)
    for e in world.entities:
        if "origin" not in e.kv:
            continue
        x, y, z = (float(v) for v in e.kv["origin"].split())
        ok = any(abs(x) < L.MAP_HALF and abs(y) < L.MAP_HALF and sz - 1024 < z < sz + L.CEIL
                 for _, sz in L.LEVELS.values())
        if not ok:
            problems.append(f"{e.classname} hors des niveaux etanches @ {x:.0f},{y:.0f},{z:.0f}")
    for e in world.entities:
        if e.classname not in ("info_player_start", "info_teleport_destination", "info_target"):
            continue
        x, y, z = (float(v) for v in e.kv["origin"].split())
        if e.kv.get("targetname", "").startswith("boat_spawn_"):
            h = S.hits((x - 130, y - 130, z - 14), (x + 130, y + 130, z + 110))
            if h:
                problems.append(f"bateau {e.kv['targetname']} bloque @ {x:.0f},{y:.0f} par "
                                f"{[(g, b.bbox[0].round().tolist()) for g, b in h][:2]}")
            continue
        h = S.hits((x - 17, y - 17, z + 2), (x + 17, y + 17, z + 72))
        if h:
            problems.append(f"{e.classname} {e.kv.get('targetname', '')} bloque @ {x:.0f},{y:.0f},{z:.0f} "
                            f"par {[g for g, _ in h][:3]}")
    # portes : devant et derriere doivent etre libres
    for e in world.entities:
        if e.classname != "func_door_rotating":
            continue
        b = e.brushes[0]
        lo, hi = b.bbox
        c = (lo + hi) / 2
        thin = int(np.argmin(hi - lo))
        for s in (-1, 1):
            plo, phi = lo.copy(), hi.copy()
            plo[2] += 6
            phi[2] -= 20
            plo[thin] = c[thin] + (16 if s > 0 else -56)
            phi[thin] = c[thin] + (56 if s > 0 else -16)
            for ax in (0, 1):
                if ax != thin:
                    plo[ax] += 6
                    phi[ax] -= 6
            h = S.hits(plo, phi)
            if h:
                problems.append(f"porte bloquee @ {c.round()} cote {s} par {[g for g, _ in h][:3]}")
    # portails : la zone de passage doit etre libre (eau)
    for e in world.entities:
        if e.classname != "trigger_multiple" or not e.kv.get("targetname", "").startswith("tp_gate"):
            continue
        V = np.vstack([f.poly for f in e.brushes[0].faces])
        c = V.mean(0)
        xy = V[:, :2] - c[:2]
        u, sv, vt = np.linalg.svd(xy, full_matrices=False)
        ax = vt[0]
        half = np.abs(xy @ ax).max()
        for t in np.linspace(-half + 70, half - 70, 5):
            p = c[:2] + ax * t
            h = S.hits((p[0] - 24, p[1] - 24, 4), (p[0] + 24, p[1] + 24, 300))
            if h:
                problems.append(f"portail {e.kv['targetname']} obstrue @ {p.round()} par {[g for g, _ in h][:3]}")
                break
    return problems


def _clip(subject, clip):
    """Intersection de deux polygones convexes 2D (Sutherland-Hodgman)."""
    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def inter(p1, p2, a, b):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = a
        x4, y4 = b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return p2
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = list(subject)
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q, a, b):
                if not inside(p, a, b):
                    out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p, a, b):
                out.append(inter(p, q, a, b))
    return out


def _area(poly):
    return 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly))))


def coplanar_tops(world, solved, min_area=400):
    """Faces du dessus superposees a la meme hauteur (scintillement en jeu)."""
    faces = {}
    for g, lst in world.detail.items():
        for b in lst:
            polys = solved.get(id(b))
            if polys is None:
                continue
            for f, poly in zip(b.faces, polys):
                if f.normal[2] > 0.999 and not f.mat.name.startswith("tools/"):
                    z = round(float(poly[0][2]))
                    p2 = [(float(p[0]), float(p[1])) for p in poly]
                    faces.setdefault(z, []).append((g, f.mat.name, p2, b))
    out = []
    for z, lst in faces.items():
        if len(lst) < 2:
            continue
        bb = [(min(p[0] for p in q[2]), min(p[1] for p in q[2]), max(p[0] for p in q[2]), max(p[1] for p in q[2]))
              for q in lst]
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[i][3] is lst[j][3]:
                    continue
                a, b = bb[i], bb[j]
                if a[0] >= b[2] or b[0] >= a[2] or a[1] >= b[3] or b[1] >= a[3]:
                    continue
                inter = _clip(lst[i][2], lst[j][2])
                if len(inter) >= 3 and _area(inter) > min_area:
                    out.append(f"surfaces superposees z={z} ({lst[i][0]}) {lst[i][1]} / {lst[j][1]} "
                               f"aire={_area(inter):.0f} pres de {inter[0][0]:.0f},{inter[0][1]:.0f}")
    return out
