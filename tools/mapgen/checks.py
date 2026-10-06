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

    def hits(self, lo, hi, eps=0.5):
        lo = np.asarray(lo, float)
        hi = np.asarray(hi, float)
        cand = np.nonzero(np.all(self.mins < hi - eps, 1) & np.all(self.maxs > lo + eps, 1))[0]
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        out = []
        for i in cand:
            if self.pl[i] is None:
                self.pl[i] = _planes(self.items[i][1])
            sep = False
            for n, d in self.pl[i]:
                if np.all(corners @ n >= d - eps):
                    sep = True
                    break
            if not sep:
                out.append(self.items[i])
        return out


def run(world):
    S = Solids(world)
    problems = []
    for e in world.entities:
        if e.classname not in ("info_player_start", "info_teleport_destination", "info_target"):
            continue
        x, y, z = (float(v) for v in e.kv["origin"].split())
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
