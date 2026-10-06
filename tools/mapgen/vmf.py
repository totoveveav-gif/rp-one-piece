"""Ecriture du VMF (source Hammer), validation des brushes et export apercu."""
import itertools
import json

import numpy as np

from .materials import MATS, TOOL_MATS
from .world import fmt_vec


# ---------------------------------------------------------------------------
# Axes de texture
# ---------------------------------------------------------------------------

def tex_axes(n):
    n = np.asarray(n, float)
    if abs(n[2]) > 0.999:
        return np.array([1.0, 0, 0]), np.array([0, -1.0, 0])
    u = np.cross([0, 0, 1.0], n)
    u /= np.linalg.norm(u)
    v = np.cross(u, n)
    v /= np.linalg.norm(v)
    return u, v


def mat_info(name):
    if name in MATS:
        return MATS[name]
    if name in TOOL_MATS:
        return TOOL_MATS[name]
    raise KeyError(f"materiau inconnu: {name}")


def face_texinfo(normal, poly, mat):
    """Retourne (u, v, su, sv, shu, shv, lms) pour une face."""
    info = mat_info(mat.name)
    W, H = info["px"]
    u, v = tex_axes(normal)
    if mat.flip:
        u = -u
    if mat.fit:
        pu = poly @ u
        pv = poly @ v
        su = max((pu.max() - pu.min()) / W, 1e-3)
        sv = max((pv.max() - pv.min()) / H, 1e-3)
        shu = -pu.min() / su
        shv = -pv.min() / sv
    else:
        tu, tv = mat.scale or info["tile"]
        su, sv = tu / W, tv / H
        o = np.asarray(mat.origin if mat.origin is not None else (0, 0, 0), float)
        shu = (-(o @ u) / su) % W
        shv = (-(o @ v) / sv) % H
    lms = mat.lms or info.get("lms", 32)
    return u, v, su, sv, shu, shv, lms


# ---------------------------------------------------------------------------
# Resolution plans -> polyedre (validation, comme vbsp)
# ---------------------------------------------------------------------------

def solve_brush(brush):
    planes = []
    for f in brush.faces:
        a, b, c = (np.asarray(p, float) for p in f.plane_pts)
        n = np.cross(c - a, b - a)
        n /= np.linalg.norm(n)
        planes.append((n, float(n @ a)))
    N = np.array([p[0] for p in planes])
    D = np.array([p[1] for p in planes])
    k = len(planes)
    combos = np.array(list(itertools.combinations(range(k), 3)))
    A = N[combos]
    bvec = D[combos]
    det = np.linalg.det(A)
    ok = np.abs(det) > 1e-7
    X = np.linalg.solve(A[ok], bvec[ok][..., None])[..., 0]
    inside = np.all(X @ N.T - D <= 0.02, axis=1)
    X = X[inside]
    if len(X) == 0:
        return None, "brush vide"
    X = np.unique(np.round(X, 3), axis=0)
    polys = []
    for i in range(k):
        on = X[np.abs(X @ N[i] - D[i]) < 0.02]
        if len(on) < 3:
            return None, f"face {i} ({brush.faces[i].mat.name}) inutile"
        from .geom import _sort_ccw
        poly = _sort_ccw(on, N[i])
        area = 0.0
        for j in range(1, len(poly) - 1):
            area += np.linalg.norm(np.cross(poly[j] - poly[0], poly[j + 1] - poly[0])) / 2
        if area < 0.5:
            return None, f"face {i} d'aire nulle"
        polys.append(poly)
    return polys, None


def validate(world, limit=16000):
    errors = []
    all_brushes = []
    for b in world.world:
        all_brushes.append(("world", b))
    for g, lst in world.detail.items():
        for b in lst:
            all_brushes.append((g, b))
    for e in world.entities:
        for b in e.brushes:
            all_brushes.append((e.classname, b))
    solved = {}
    for owner, b in all_brushes:
        polys, err = solve_brush(b)
        if err:
            errors.append(f"[{owner}] {err} bbox={b.bbox[0].round()}..{b.bbox[1].round()}")
            continue
        allv = np.vstack(polys)
        if np.abs(allv).max() > limit + 512:
            errors.append(f"[{owner}] hors limites {allv.min(0)} {allv.max(0)}")
        ext = allv.max(0) - allv.min(0)
        if ext.min() < 1.0:
            errors.append(f"[{owner}] trop fin {ext}")
        solved[id(b)] = polys
    planes = set()
    for owner, b in all_brushes:
        for f in b.faces:
            n = np.round(f.normal, 4)
            d = round(float(f.dist), 1)
            planes.add(min(tuple(n) + (d,), tuple(-n) + (-d,)))
    world.bsp_planes = 2 * len(planes)
    if world.bsp_planes > 60000:
        errors.append(f"trop de plans : ~{world.bsp_planes} plans BSP (limite moteur 65536)")
    return errors, solved


# ---------------------------------------------------------------------------
# Ecriture VMF
# ---------------------------------------------------------------------------

class _Ids:
    def __init__(self):
        self.n = 1

    def __call__(self):
        self.n += 1
        return self.n


def _solid(out, b, ids, ind, visgroup=None, color="0 180 255"):
    t = "\t" * ind
    out.append(f"{t}solid\n{t}{{\n{t}\t\"id\" \"{ids()}\"\n")
    for f in b.faces:
        u, v, su, sv, shu, shv, lms = face_texinfo(f.normal, f.poly, f.mat)
        p = " ".join("(" + fmt_vec(q) + ")" for q in f.plane_pts)
        out.append(
            f"{t}\tside\n{t}\t{{\n"
            f"{t}\t\t\"id\" \"{ids()}\"\n"
            f"{t}\t\t\"plane\" \"{p}\"\n"
            f"{t}\t\t\"material\" \"{f.mat.name.upper()}\"\n"
            f"{t}\t\t\"uaxis\" \"[{u[0]:.6g} {u[1]:.6g} {u[2]:.6g} {shu:.4f}] {su:.6g}\"\n"
            f"{t}\t\t\"vaxis\" \"[{v[0]:.6g} {v[1]:.6g} {v[2]:.6g} {shv:.4f}] {sv:.6g}\"\n"
            f"{t}\t\t\"rotation\" \"0\"\n"
            f"{t}\t\t\"lightmapscale\" \"{lms}\"\n"
            f"{t}\t\t\"smoothing_groups\" \"0\"\n"
        )
        if f.disp is not None:
            out.append(_dispinfo(f.disp, t + "\t\t"))
        out.append(f"{t}\t}}\n")
    vg = f"{t}\t\t\"visgroupid\" \"{visgroup}\"\n" if visgroup else ""
    out.append(f"{t}\teditor\n{t}\t{{\n{t}\t\t\"color\" \"{color}\"\n{vg}"
               f"{t}\t\t\"visgroupshown\" \"1\"\n{t}\t\t\"visgroupautoshown\" \"1\"\n{t}\t}}\n")
    out.append(f"{t}}}\n")


def _dispinfo(d, t):
    n = 2 ** d["power"] + 1
    H = d["heights"]
    sx, sy, sz = d["start"]
    o = [f"{t}dispinfo\n{t}{{\n",
         f'{t}\t"power" "{d["power"]}"\n',
         f'{t}\t"startposition" "[{sx:g} {sy:g} {sz:g}]"\n',
         f'{t}\t"flags" "0"\n{t}\t"elevation" "0"\n{t}\t"subdiv" "0"\n']

    def rows(name, fn):
        o.append(f"{t}\t{name}\n{t}\t{{\n")
        for i in range(n if name != "triangle_tags" else n - 1):
            o.append(f'{t}\t\t"row{i}" "{fn(i)}"\n')
        o.append(f"{t}\t}}\n")

    rows("normals", lambda i: " ".join("0 0 1" for _ in range(n)))
    rows("distances", lambda i: " ".join(f"{max(0.0, H[i][j]):.2f}" for j in range(n)))
    rows("offsets", lambda i: " ".join("0 0 0" for _ in range(n)))
    rows("offset_normals", lambda i: " ".join("0 0 1" for _ in range(n)))
    A = d.get("alphas")
    rows("alphas", lambda i: " ".join(f"{A[i][j]:g}" if A else "0" for j in range(n)))
    rows("triangle_tags", lambda i: " ".join("9" for _ in range(2 * (n - 1))))
    o.append(f'{t}\tallowed_verts\n{t}\t{{\n{t}\t\t"10" "-1 -1 -1 -1 -1 -1 -1 -1 -1 -1"\n{t}\t}}\n')
    o.append(f"{t}}}\n")
    return "".join(o)


def write_vmf(world, path, skyname="sky_day01_01", world_kv=None):
    ids = _Ids()
    vg_ids = {name: i + 1 for i, name in enumerate(world.visgroups)}
    out = []
    out.append('versioninfo\n{\n\t"editorversion" "400"\n\t"editorbuild" "8864"\n'
               '\t"mapversion" "1"\n\t"formatversion" "100"\n\t"prefab" "0"\n}\n')
    out.append("visgroups\n{\n")
    for name, i in vg_ids.items():
        out.append(f'\tvisgroup\n\t{{\n\t\t"name" "{name}"\n\t\t"visgroupid" "{i}"\n'
                   f'\t\t"color" "{(i * 67) % 255} {(i * 131) % 255} {(i * 197) % 255}"\n\t}}\n')
    out.append("}\n")
    out.append('viewsettings\n{\n\t"bSnapToGrid" "1"\n\t"bShowGrid" "1"\n'
               '\t"bShowLogicalGrid" "0"\n\t"nGridSpacing" "64"\n\t"bShow3DGrid" "0"\n}\n')
    out.append("world\n{\n")
    out.append(f'\t"id" "1"\n\t"mapversion" "1"\n\t"classname" "worldspawn"\n'
               f'\t"skyname" "{skyname}"\n\t"maxpropscreenwidth" "-1"\n'
               '\t"detailvbsp" "detail.vbsp"\n\t"detailmaterial" "detail/detailsprites"\n')
    for k, v in (world_kv or {}).items():
        out.append(f'\t"{k}" "{v}"\n')
    for b in world.world:
        _solid(out, b, ids, 1)
    out.append("}\n")
    # func_detail par groupe (un par visgroup, decoupe pour rester lisible)
    for gname, lst in world.detail.items():
        for chunk in range(0, len(lst), 400):
            out.append(f'entity\n{{\n\t"id" "{ids()}"\n\t"classname" "func_detail"\n')
            for b in lst[chunk:chunk + 400]:
                _solid(out, b, ids, 1, vg_ids.get(gname), "0 180 0")
            out.append(f'\teditor\n\t{{\n\t\t"color" "0 180 0"\n\t\t"visgroupid" "{vg_ids.get(gname, 1)}"\n'
                       '\t\t"visgroupshown" "1"\n\t\t"visgroupautoshown" "1"\n\t}\n}\n')
    for e in world.entities:
        out.append(f'entity\n{{\n\t"id" "{ids()}"\n\t"classname" "{e.classname}"\n')
        for k, v in e.kv.items():
            out.append(f'\t"{k}" "{v}"\n')
        if hasattr(e, "outputs"):
            out.append("\tconnections\n\t{\n")
            for name, val in e.outputs:
                out.append(f'\t\t"{name}" "{val}"\n')
            out.append("\t}\n")
        for b in e.brushes:
            _solid(out, b, ids, 1, vg_ids.get(e.group), "220 30 220")
        vg = f'\t\t"visgroupid" "{vg_ids[e.group]}"\n' if e.group in vg_ids else ""
        out.append(f'\teditor\n\t{{\n\t\t"color" "220 30 220"\n{vg}'
                   '\t\t"visgroupshown" "1"\n\t\t"visgroupautoshown" "1"\n'
                   '\t\t"logicalpos" "[0 0]"\n\t}\n}\n')
    out.append('cameras\n{\n\t"activecamera" "-1"\n}\n')
    out.append('cordon\n{\n\t"mins" "(-1024 -1024 -1024)"\n\t"maxs" "(1024 1024 1024)"\n\t"active" "0"\n}\n')
    with open(path, "w", newline="\r\n") as fh:
        fh.write("".join(out))


def add_output(ent, name, target, inp, param="", delay=0, times=-1):
    if not hasattr(ent, "outputs"):
        ent.outputs = []
    sep = ","
    ent.outputs.append((name, f"{target}{sep}{inp}{sep}{param}{sep}{delay}{sep}{times}"))


# ---------------------------------------------------------------------------
# Export pour l'apercu Blender
# ---------------------------------------------------------------------------

def export_preview(world, solved, path):
    """Faces visibles groupees par materiau, avec parametres UV identiques a Source."""
    by_mat = {}

    def push(b, kind):
        polys = solved.get(id(b))
        if polys is None:
            return
        for f, poly in zip(b.faces, polys):
            name = f.mat.name
            if name in TOOL_MATS:
                continue
            info = MATS[name]
            if info.get("kind") == "water":
                continue
            u, v, su, sv, shu, shv, _ = face_texinfo(f.normal, poly, f.mat)
            alph = None
            W, H = info["px"]
            d = by_mat.setdefault(name, {"verts": [], "faces": [], "uvs": []})
            if info.get("kind") == "blend":
                d["blend"] = [info["base"], info["base2"]]
            polys_out = [poly]
            if f.disp is not None:
                # grille deformee (lignes selon y, colonnes selon x)
                n = 2 ** f.disp["power"] + 1
                x0, y0, z0 = f.disp["start"]
                xs = poly[:, 0]
                ys = poly[:, 1]
                dx = (xs.max() - xs.min()) / (n - 1)
                dy = (ys.max() - ys.min()) / (n - 1)
                hh = f.disp["heights"]
                aa = f.disp.get("alphas")
                G = [[np.array([x0 + j * dx, y0 + i * dy, z0 + hh[i][j]]) for j in range(n)] for i in range(n)]
                polys_out = [np.array([G[i][j], G[i][j + 1], G[i + 1][j + 1], G[i + 1][j]])
                             for i in range(n - 1) for j in range(n - 1)]
                if aa is not None:
                    alph = [[aa[i][j], aa[i][j + 1], aa[i + 1][j + 1], aa[i + 1][j]]
                            for i in range(n - 1) for j in range(n - 1)]
            for k, pp in enumerate(polys_out):
                if info.get("kind") == "blend":
                    al = alph[k] if f.disp is not None and f.disp.get("alphas") is not None else [0] * len(pp)
                    d.setdefault("alpha", []).extend(round(float(a) / 255, 3) for a in al)
                uv = []
                for p in pp:
                    tu = (p @ u / su + shu) / W
                    tv = (p @ v / sv + shv) / H
                    uv.append((round(float(tu), 5), round(float(1.0 - tv), 5)))
                base = len(d["verts"])
                d["verts"].extend([[round(float(c), 2) for c in p] for p in pp])
                d["faces"].append(list(range(base, base + len(pp))))
                d["uvs"].extend(uv)

    for b in world.world:
        push(b, "world")
    for lst in world.detail.values():
        for b in lst:
            push(b, "detail")
    for e in world.entities:
        if e.classname in ("trigger_teleport", "trigger_multiple"):
            continue
        for b in e.brushes:
            push(b, e.classname)
    ents = []
    for e in world.entities:
        if "origin" in e.kv:
            ents.append({"class": e.classname, **{k: v for k, v in e.kv.items()}})
    with open(path, "w") as fh:
        json.dump({"materials": by_mat, "entities": ents, "markers": world.markers}, fh)
