"""Disposition generale des iles et des routes maritimes (portails)."""
import math

from . import geom as G
from . import kit as K
from . import materials as M

MAP_HALF = 15872          # interieur jouable : +/- 15872 unites
SEA_FLOOR = -768
LAND_Z = 48

# cle : (nom affiche, centre x, centre y, rayon du socle, sous-titre)
ISLANDS = {
    "sabaody": ("Archipel de Sabaody", 0, 0, 3200, "Carrefour de la Grand Line"),
    "marineford": ("Marineford", 0, 10600, 4200, "Quartier General de la Marine"),
    "enies": ("Enies Lobby", 10700, 11300, 2600, "Ile judiciaire du Gouvernement"),
    "impel": ("Impel Down", 12300, 4200, 1900, "Prison sous-marine"),
    "alabasta": ("Alabasta", 10800, -3300, 3600, "Royaume du desert"),
    "wano": ("Pays de Wano", 10300, -11500, 3200, "Capitale des Fleurs"),
    "loguetown": ("Loguetown", 0, -11000, 3300, "La ville du commencement et de la fin"),
    "fuchsia": ("Village de Fuchsia", -10900, -11300, 2600, "East Blue"),
    "baratie": ("Baratie", -5600, -6300, 1100, "Restaurant flottant"),
    "water7": ("Water Seven", -10800, -1700, 3600, "La cite de l'eau"),
    "drum": ("Royaume de Drum", -10800, 9900, 3200, "Ile d'hiver"),
}

# route de la Grand Line (chaque ile a un portail vers la suivante)
ROUTE = ["fuchsia", "baratie", "loguetown", "drum", "alabasta", "water7", "enies",
         "sabaody", "impel", "marineford", "wano"]
HUB = "sabaody"


def center(key):
    _, x, y, _, _ = ISLANDS[key]
    return x, y


def radius(key):
    return ISLANDS[key][3]


def gate_links():
    """Liste (ile, destination) des portails a construire."""
    links = []
    for k in ISLANDS:
        if k == HUB:
            for d in ISLANDS:
                if d != HUB:
                    links.append((k, d))
            continue
        nxt = ROUTE[(ROUTE.index(k) + 1) % len(ROUTE)]
        links.append((k, nxt))
        if nxt != HUB:
            links.append((k, HUB))
    # Portes de la Justice : Enies Lobby -> Impel Down et Marineford
    links.append(("enies", "impel"))
    links.append(("enies", "marineford"))
    return links


def arrival_point(key):
    """Point d'arrivee en mer (face au port de l'ile)."""
    x, y = center(key)
    R = radius(key)
    # le port fait face a Sabaody (ou au sud pour Sabaody)
    if key == HUB:
        ang = -math.pi / 2
    else:
        ang = math.atan2(-y, -x)
    ang += math.radians(PORT_SHIFT.get(key, 0))
    d = R + 480
    return (x + math.cos(ang) * d, y + math.sin(ang) * d, 24, math.degrees(ang) + 180)


PORT_SHIFT = {"marineford": 0, "enies": 25, "impel": -30, "alabasta": 20, "wano": 30,
              "loguetown": 0, "fuchsia": 0, "baratie": 0, "water7": 0, "drum": 10}

GATE_SPREAD = {}


def gate_position(src, dst, index_among_src, count_src):
    """Portail place sur la cote de src, oriente vers dst."""
    sx, sy = center(src)
    dx, dy = center(dst)
    ang = math.atan2(dy - sy, dx - sx)
    R = radius(src)
    # eviter le point d'arrivee : decaler l'angle si trop proche
    ax, ay, _, _ = arrival_point(src)
    a_arr = math.atan2(ay - sy, ax - sx)
    diff = (ang - a_arr + math.pi) % (2 * math.pi) - math.pi
    if abs(diff) < math.radians(28):
        ang = a_arr + math.copysign(math.radians(28), diff if diff else 1)
    d = R + 700
    x, y = sx + math.cos(ang) * d, sy + math.sin(ang) * d
    lim = MAP_HALF - 900
    if abs(x) > lim or abs(y) > lim:
        # rester dans la map : glisser le long du cercle vers l'interieur
        for k in range(1, 40):
            for s in (1, -1):
                a2 = ang + s * math.radians(4 * k)
                x2, y2 = sx + math.cos(a2) * d, sy + math.sin(a2) * d
                if abs(x2) <= lim and abs(y2) <= lim:
                    return x2, y2, math.degrees(a2)
    return x, y, math.degrees(ang)


def _relax(angles, fixed, sep, iters=400):
    """Ecarte des angles (degres) d'au moins sep, en evitant les angles fixes."""
    a = list(angles)
    for _ in range(iters):
        moved = False
        for i in range(len(a)):
            others = [a[j] for j in range(len(a)) if j != i] + fixed
            for o in others:
                d = (a[i] - o + 180) % 360 - 180
                if abs(d) < sep:
                    a[i] += (sep - abs(d)) * 0.5 * (1 if d >= 0 else -1) + (0.01 if d == 0 else 0)
                    moved = True
        if not moved:
            break
    return a


def build_gates(w):
    links = gate_links()
    placed = []
    by_src = {}
    for s, d in links:
        if s == "enies" and d in ("impel", "marineford"):
            continue  # construits par l'ile (Portes de la Justice)
        by_src.setdefault(s, []).append(d)
    for k in ISLANDS:
        ax, ay, az, ayaw = arrival_point(k)
        K.tp_destination(w, f"arrive_{k}", ax, ay, az, ayaw)
    for s, dests in by_src.items():
        sx, sy = center(s)
        R = radius(s) + 700
        ax, ay, _, _ = arrival_point(s)
        a_arr = math.degrees(math.atan2(ay - sy, ax - sx))
        want = [math.degrees(math.atan2(center(d)[1] - sy, center(d)[0] - sx)) for d in dests]
        sep = max(24.0, math.degrees(1500.0 / R))
        fixed = [a_arr] + EXTRA_BLOCKED.get(s, [])
        angs = _relax(want, fixed, sep)
        lim = MAP_HALF - 900
        for d, ang in zip(dests, angs):
            x, y = sx + math.cos(math.radians(ang)) * R, sy + math.sin(math.radians(ang)) * R
            if abs(x) > lim or abs(y) > lim:
                x, y = max(-lim, min(lim, x)), max(-lim, min(lim, y))
            name = ISLANDS[d][0].upper()
            sm = M.sign_mat(f"to_{d}", "\u2192 " + name, sub="Porte de la Grand Line",
                            color=(255, 240, 190))
            K.sea_gate(w, x, y, ang, sm, f"arrive_{d}", f"{s}_{d}")
            w.marker(f"Portail {ISLANDS[s][0]} -> {ISLANDS[d][0]}", (x, y, 0), "portail")
            placed.append((s, d, x, y, ang))
    return placed


# directions deja occupees par des elements de l'ile (degres)
EXTRA_BLOCKED = {"enies": [55, 130]}


def terrain(w, poly, cx, cy, land_z=LAND_Z, top=M.GRASS, beach=M.SAND, under=M.SAND,
            beach_frac=(0.86, 0.74, 0.71)):
    a, b, c = beach_frac
    p1 = G.scale_poly(poly, cx, cy, a)
    p2 = G.scale_poly(poly, cx, cy, b)
    p3 = G.scale_poly(poly, cx, cy, c)
    w.add(G.poly_frustum(poly, p1, SEA_FLOOR, -96, under))
    w.add(G.poly_frustum(p1, p2, -96, 16, beach))
    w.add(G.poly_frustum(p2, p3, 16, land_z, {"top": top, "default": beach}))
    return p3


def island_base(w, key, seed, land_z=LAND_Z, top=M.GRASS, beach=M.SAND, sides=22, jitter=0.07,
                rx=None, ry=None, rot=0.0):
    _, cx, cy, R, _ = ISLANDS[key]
    poly = G.blob(cx, cy, rx or R, ry or R, sides, seed, jitter, rot)
    land = terrain(w, poly, cx, cy, land_z, top, beach)
    return poly, land
