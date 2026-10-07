"""Disposition generale : niveaux (mers), iles, passages entre niveaux, capitaineries."""
import math

import numpy as np

from . import geom as G
from . import kit as K
from . import materials as M

MAP_HALF = 15872          # interieur jouable de chaque niveau : +/- 15872 unites
SEA_FLOOR = -768
LAND_Z = 48
CEIL = 3584               # hauteur du ciel au-dessus de la mer, dans chaque niveau

# Trois niveaux (mers) empiles dans la meme map : chacun est un ocean complet et
# etanche. On passe de l'un a l'autre en bateau, entre deux gros rochers au bord.
# cle : (nom, altitude du niveau de la mer)
LEVELS = {
    1: ("East Blue", -11264),
    2: ("Grand Line", -3072),
    3: ("Nouveau Monde", 5120),
}

# cle : (nom affiche, centre x, centre y, rayon du socle, sous-titre)
ISLANDS = {
    "fuchsia": ("Village de Fuchsia", -7600, -6200, 2600, "East Blue"),
    "baratie": ("Baratie", 0, 7200, 1100, "Restaurant flottant"),
    "loguetown": ("Loguetown", 7400, -5200, 3300, "La ville du commencement et de la fin"),
    "drum": ("Royaume de Drum", -8000, 7200, 3200, "Ile d'hiver"),
    "water7": ("Water Seven", -8200, -7400, 3600, "La cite de l'eau"),
    "alabasta": ("Alabasta", 8000, -7200, 3600, "Royaume du desert"),
    "enies": ("Enies Lobby", 8400, 6600, 2600, "Ile judiciaire du Gouvernement"),
    "sabaody": ("Archipel de Sabaody", -8200, -7600, 3200, "Porte du Nouveau Monde"),
    "marineford": ("Marineford", -7600, 4800, 4200, "Quartier General de la Marine"),
    "impel": ("Impel Down", 8800, -8400, 1900, "Prison sous-marine"),
    "wano": ("Pays de Wano", 8200, 5600, 3200, "Capitale des Fleurs"),
}

# Grandes iles en relief (terrain.py). big = rayon de l'ile entiere ;
# peaks = (angle depuis l'arriere de l'ile, distance, hauteur, largeur) ;
# open = directions supplementaires ou la cote reste celle de la ville (ports).
SHAPES = {
    "fuchsia": dict(big=6200, biome="herbe", seed=11, mountains=320, hills=110, forest=0.75,
                    peaks=[(10, 3400, 1000, 1800), (-55, 3500, 450, 1200)], max_trees=70,
                    rock_alt=(1000, 1300)),   # mont Corvo boise, couronne rocheuse seulement
    "loguetown": dict(big=6000, biome="herbe", seed=12, mountains=260, hills=100, forest=0.5,
                      peaks=[(25, 3900, 480, 1600), (-35, 4300, 360, 1100)], max_trees=65),
    "drum": dict(big=5700, biome="neige", seed=13, mountains=420, hills=120, forest=0.8,
                 peaks=[(35, 3600, 650, 1500), (-40, 3900, 400, 1300)], max_trees=70),   # collines de neige
    "water7": dict(big=5000, biome="herbe", seed=14, custom_core=2750, mountains=200, hills=80, forest=0.6,
                   peaks=[(0, 3800, 450, 1000)], max_trees=80),
    "alabasta": dict(big=6200, biome="desert", seed=15, mountains=380, hills=150, forest=0,  # desert nu
                     peaks=[(0, 4200, 700, 1500), (70, 3900, 450, 900)], max_trees=45),
    "enies": dict(big=4400, biome="herbe", seed=16, custom_core=2300, land=32, mountains=260, hills=80, open=[-90],
                  forest=0.4, peaks=[(0, 3300, 500, 900)], max_trees=70),
    "sabaody": dict(big=5800, biome="tropical", seed=17, mountains=160, hills=90, forest=0.65, open=[-90],
                    peaks=[(-66, 3900, 420, 1500)], max_trees=120),   # colline boisee dans le lobe NO (0 tombait en mer)
    "marineford": dict(big=5700, biome="herbe", seed=18, custom_core=3900, land=64, mountains=300, hills=90,
                       forest=0.75, lobes=[(90, 75)], peaks=[(0, 4700, 600, 1000)], max_trees=90),
    "impel": dict(big=4600, biome="roche", seed=19, land=64, mountains=650, hills=120, forest=0,
                  peaks=[(0, 2900, 700, 900), (60, 3000, 500, 700)]),
    "wano": dict(big=6100, biome="wano", seed=20, mountains=380, hills=110, forest=0.7,
                 peaks=[(0, 3900, 1650, 1250), (-60, 3900, 600, 800)], max_trees=70),
}
ISLAND_LEVEL = {"fuchsia": 1, "baratie": 1, "loguetown": 1,
                "drum": 2, "water7": 2, "alabasta": 2, "enies": 2,
                "sabaody": 3, "marineford": 3, "impel": 3, "wano": 3}

GATE_Y = 14200            # passages entre niveaux (bord nord / bord sud)
ARRIVE_Y = 12500


def sea_z(level):
    return LEVELS[level][1]


def center(key):
    _, x, y, _, _ = ISLANDS[key]
    return x, y


def radius(key):
    return ISLANDS[key][3]


def arrival_point(key):
    """Point en mer devant le port de l'ile (le port fait face au centre du niveau)."""
    x, y = center(key)
    R = radius(key)
    ang = math.atan2(-y, -x) + math.radians(PORT_SHIFT.get(key, 0))
    d = R + 480
    return (x + math.cos(ang) * d, y + math.sin(ang) * d, 24, math.degrees(ang) + 180)


PORT_SHIFT = {"impel": -20, "wano": 20, "alabasta": 15, "drum": 10}


def build_level_gates(w):
    """Deux gros rochers au bord de la map ; le passage entre eux mene au niveau suivant."""
    placed = []
    for lv in LEVELS:
        name = LEVELS[lv][0]
        with w.level(lv, sea_z(lv)), w.group(f"Niveau {lv} - {name}"):
            if lv + 1 in LEVELS:
                nxt = LEVELS[lv + 1][0]
                sm = M.sign_mat(f"lvl_{lv}_up", "\u2192 " + nxt.upper(), sub=f"Niveau {lv + 1}",
                                color=(255, 240, 190))
                K.level_gate(w, 0, GATE_Y, 90, sm, f"n{lv}_n{lv + 1}sud")
                K.tp_destination(w, f"arrive_n{lv}nord", 0, ARRIVE_Y, 24, -90)
                w.marker(f"Passage vers le niveau {lv + 1} ({nxt})", (0, GATE_Y, 0), "portail")
                placed.append((lv, lv + 1, 0, GATE_Y))
            if lv - 1 in LEVELS:
                prv = LEVELS[lv - 1][0]
                sm = M.sign_mat(f"lvl_{lv}_down", "\u2192 " + prv.upper(), sub=f"Niveau {lv - 1}",
                                color=(255, 240, 190))
                K.level_gate(w, 0, -GATE_Y, -90, sm, f"n{lv}_n{lv - 1}nord")
                K.tp_destination(w, f"arrive_n{lv}sud", 0, -ARRIVE_Y, 24, 90)
                w.marker(f"Passage vers le niveau {lv - 1} ({prv})", (0, -GATE_Y, 0), "portail")
                placed.append((lv, lv - 1, 0, -GATE_Y))
    return placed


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
    """Le sol de l'ile est genere par terrain.py (relief en displacements).
    Renvoie le contour de l'ile (pour la carte) et le contour de la ville."""
    _, cx, cy, R, _ = ISLANDS[key]
    return coast_poly(key), G.blob(cx, cy, R * 0.71, R * 0.71, sides, seed, 0.0, rot)


def coast_poly(key, n=72):
    from .terrain import Island
    isl = Island(key)
    ths = np.linspace(-math.pi, math.pi, n, endpoint=False)
    rc = isl.coast(ths)
    return [(isl.cx + math.cos(t) * r, isl.cy + math.sin(t) * r) for t, r in zip(ths, rc)]


# capitaineries : position explicite (x, y, z, yaw, ponton) ou placement automatique
# (decalage angulaire depuis la direction du port, en degres)
HARBOR_OVERRIDE = {
    "marineford": lambda: (center("marineford")[0] - 1595, center("marineford")[1] - 2100, 64, 0, 560),
    "enies": lambda: (center("enies")[0] + 300, center("enies")[1] - 1500, 32, -90, 620),
}


def _harbor_free(S, x, y, z, yaw, pier):
    """Verifie que cabane, ponton et zone du bateau ne touchent rien (z relatif au niveau)."""
    f = G.Frame(x, y, 0, yaw)
    probes = [(0, 0, 130, 120)]                                   # cabane (au-dessus du sol)
    probes += [(d, 0, 70, 60) for d in range(200, int(96 + pier), 160)]   # ponton
    probes += [(96 + pier + 220, 0, 150, 0)]                      # bateau
    for px, py, half, zlo in probes:
        X, Y, _ = f.p(px, py)
        zl = z + 12 if zlo == 120 else (z + 12 if zlo == 60 else 4)
        if S.hits((X - half, Y - half, zl), (X + half, Y + half, zl + 120)):
            return False
    return True


def build_harbors(w):
    from .checks import Solids
    from .terrain import Island
    for k in ISLANDS:
        if k == "baratie":
            continue  # construit par l'ile (sur la nageoire)
        lv = ISLAND_LEVEL[k]
        dz = sea_z(lv)
        if k in HARBOR_OVERRIDE:
            x, y, z, yaw, pier = HARBOR_OVERRIDE[k]()
        else:
            S = _Shifted(Solids(w), dz)
            cx, cy = center(k)
            R = radius(k)
            spec = SHAPES.get(k, {})
            z = spec.get("land", LAND_Z)
            isl = Island(k) if k in SHAPES and not spec.get("custom_core") else None
            choice = None
            if isl is not None:
                # sur la cote de la ville (secteurs ouverts), ponton vers le large
                for sh in sorted(range(-44, 46, 4), key=abs):
                    for base in isl.opens:
                        a = base + math.radians(sh)
                        rc = float(isl.coast(np.array([a]))[0])
                        x, y = cx + math.cos(a) * (rc - 380), cy + math.sin(a) * (rc - 380)
                        if _harbor_free(S, x, y, z, math.degrees(a), 700):
                            choice = (x, y, math.degrees(a), 700)
                            break
                    if choice:
                        break
            else:
                ax, ay, _, _ = arrival_point(k)
                base = math.atan2(ay - cy, ax - cx)
                for sh in sorted(range(-170, 180, 8), key=abs):
                    a = base + math.radians(sh)
                    x, y = cx + math.cos(a) * R * 0.6, cy + math.sin(a) * R * 0.6
                    if _harbor_free(S, x, y, z, math.degrees(a), R * 0.28):
                        choice = (x, y, math.degrees(a), R * 0.28)
                        break
            if choice is None:
                raise RuntimeError(f"pas de place pour la capitainerie de {k}")
            x, y, yaw, pier = choice
        with w.level(lv, dz), w.group(ISLANDS[k][0]):
            K.harbor(w, k, x, y, z, yaw, pier)


class _Shifted:
    """Adapte une requete en z relatif au niveau vers les coordonnees du monde."""

    def __init__(self, S, dz):
        self.S, self.dz = S, dz

    def hits(self, lo, hi):
        return self.S.hits((lo[0], lo[1], lo[2] + self.dz), (hi[0], hi[1], hi[2] + self.dz))
