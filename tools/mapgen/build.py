"""Point d'entree : genere la map rp_onepiece_grandline.

    python -m tools.mapgen.build            (map + textures + apercu)
    python -m tools.mapgen.build --no-tex   (sans regenerer les textures)
"""
import argparse
import importlib
import json
import math
import os
import time

from . import geom as G
from . import kit as K
from . import layout as L
from . import materials as M
from . import texgen as T
from .vmf import export_preview, validate, write_vmf
from .world import World

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAP_NAME = "rp_onepiece_grandline"
ISLAND_MODULES = ["sabaody", "marineford", "enies", "impel", "alabasta", "wano", "loguetown",
                  "fuchsia", "baratie", "water7", "drum"]

SUN_YAW = 50       # direction de propagation de la lumiere (vers le nord-est)
SUN_PITCH = -50    # vers le bas


def level_shell(w, lv):
    """Ocean etanche d'un niveau : coque skybox, fond marin, eau."""
    H = L.MAP_HALF
    t = 128
    bot, top = -1024, L.CEIL
    w.add_world(G.box(-H - t, -H - t, bot - t, H + t, H + t, bot, M.SKY))
    w.add_world(G.box(-H - t, -H - t, top, H + t, H + t, top + t, M.SKY))
    w.add_world(G.box(-H - t, -H - t, bot, -H, H + t, top, M.SKY))
    w.add_world(G.box(H, -H - t, bot, H + t, H + t, top, M.SKY))
    w.add_world(G.box(-H, -H - t, bot, H, -H, top, M.SKY))
    w.add_world(G.box(-H, H, bot, H, H + t, top, M.SKY))
    w.add_world(G.box(-H, -H, bot, H, H, L.SEA_FLOOR, {"top": M.SAND, "default": M.NODRAW}))
    w.add_world(G.box(-H, -H, L.SEA_FLOOR, H, H, 0, {"top": M.WATER, "default": M.NODRAW}))
    # quelques recifs pour animer la navigation
    import numpy as np
    rng = np.random.default_rng(lv * 17)
    reefs = []
    for i in range(7):
        for _ in range(200):
            x, y = rng.uniform(-12500, 12500, 2)
            if all(math.hypot(x - L.center(k)[0], y - L.center(k)[1]) > L.radius(k) + 1500
                   for k in L.ISLANDS if L.ISLAND_LEVEL[k] == lv) and abs(x) > 2200 and abs(y) < 11500 \
                    and all(math.hypot(x - a, y - b) > 2600 for a, b in reefs):
                break
        reefs.append((x, y))
        r = rng.uniform(260, 520)
        w.add(G.boulder(x, y, -420, r * 1.9, r * 1.6, 380, int(rng.integers(1 << 30)), M.SAND, 30,
                        flat_bottom=L.SEA_FLOOR))
        w.add(G.boulder(x, y, 0, r, r * 0.8, rng.uniform(220, 460), int(rng.integers(1 << 30)), M.ROCK, 26,
                        flat_bottom=-300))
        if i % 2 == 0:
            K.palm(w, x + r * 0.2, y, rng.uniform(60, 120), 300, seed=lv * 100 + i)


def red_line(w):
    """La Red Line : muraille rouge colossale et dechiquetee qui ferme le nord du Nouveau Monde."""
    import numpy as np
    from .geom import Mat
    H = L.MAP_HALF
    y0 = 13300
    red = Mat(M.ROCK_RED, scale=(1536, 1536), lms=128)
    w.add(G.box(-H, y0 + 900, L.SEA_FLOOR, H, H, L.CEIL, {"default": red, "top": M.SNOW}))
    rng = np.random.default_rng(5)
    x = -H
    while x < H:
        wd = rng.uniform(1700, 2600)
        cx = min(max(x + wd / 2, -H + wd * 0.62), H - wd * 0.62)
        hh = rng.uniform(2300, 3300)
        w.add(G.boulder(cx, y0 + 900, hh / 2 - 400, wd * 0.62, rng.uniform(650, 950), hh / 2 + 500,
                        int(rng.integers(1 << 30)), {"default": red, "top": M.SNOW}, 40, flat_bottom=L.SEA_FLOOR))
        if rng.uniform() < 0.6:
            w.add(G.boulder(min(max(cx + rng.uniform(-600, 600), -H + 800), H - 800), y0 + 250, 100,
                            rng.uniform(380, 700), rng.uniform(300, 520),
                            rng.uniform(500, 1100), int(rng.integers(1 << 30)), red, 30, flat_bottom=L.SEA_FLOOR))
        x += wd * 0.8
    w.marker("Red Line", (0, y0, 0), "lieu")


def environment(w):
    with w.group("Ocean et ciel"):
        w.ent("light_environment", (0, 0, 0), pitch=SUN_PITCH, angles=(SUN_PITCH, SUN_YAW, 0),
              _light="255 242 220 520", _lightHDR="-1 -1 -1 1", _lightscaleHDR=1,
              _ambient="150 196 240 170", _ambientHDR="-1 -1 -1 1", _AmbientScaleHDR=1,
              SunSpreadAngle=4)
        w.ent("shadow_control", (0, 0, 64), angles=(-SUN_PITCH, SUN_YAW, 0), color="110 120 140",
              distance=90, disableallshadows=0)
        w.ent("env_fog_controller", (0, 0, 128), targetname="fog_mer", fogenable=1, fogblend=0,
              fogcolor="196 224 244", fogcolor2="196 224 244", fogstart=6000, fogend=24000,
              fogmaxdensity=0.75, farz=-1, fogdir="1 0 0", use_angles=0, angles="0 0 0",
              spawnflags=1)
        w.ent("water_lod_control", (0, 0, 192), cheapwaterstartdistance=3000,
              cheapwaterenddistance=9000)
        w.ent("env_tonemap_controller", (0, 0, 256), targetname="tonemap")
        # ponts vers le Lua : passages entre niveaux et capitaineries
        w.ent("lua_run", (0, 0, 320), targetname="op_seagate_lua",
              Code="if OP_SeaGate then OP_SeaGate() end")
        w.ent("lua_run", (0, 0, 384), targetname="op_boat_lua",
              Code="if OP_BoatRental then OP_BoatRental() end")
    for lv, (name, z) in L.LEVELS.items():
        with w.level(lv, z), w.group(f"Niveau {lv} - {name}"):
            level_shell(w, lv)
            if lv == 3:
                red_line(w)


def spawns(w):
    """Spawns sur la place de Loguetown (niveau 1, East Blue)."""
    x, y = L.center("loguetown")
    with w.level(1, L.sea_z(1)), w.group("Spawns"):
        for i in range(24):
            sx = x - 715 + (i % 12) * 130
            sy = y - 560 + (i // 12) * 130
            w.ent("info_player_start", (sx, sy, 64), angles=(0, 90, 0))


def write_packlist(path):
    """Liste pour bspzip -addlist (chemin interne / chemin sur disque)."""
    mdir = os.path.join(ROOT, "addon", "materials", "onepiece")
    lines = []
    for fn in sorted(os.listdir(mdir)):
        lines.append(f"materials/onepiece/{fn}")
        lines.append(f"addon/materials/onepiece/{fn}")
    with open(path, "w", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")


def write_places(w, gates, path):
    rows = ["# Lieux et coordonnees de rp_onepiece_grandline", "",
            "Genere automatiquement par `tools/mapgen/build.py`. Les coordonnees sont en unites Hammer",
            "(utilisables pour les spawns DarkRP, les PNJ, les zones...).", ""]
    rows += ["## Niveaux", "", "| Niveau | Mer | Niveau de la mer (Z) | Iles |", "|---|---|---:|---|"]
    for lv, (name, z) in L.LEVELS.items():
        isl = ", ".join(L.ISLANDS[k][0] for k in L.ISLANDS if L.ISLAND_LEVEL[k] == lv)
        rows.append(f"| {lv} | {name} | {z} | {isl} |")
    rows.append("")
    for kind, title in (("ile", "Iles"), ("batiment", "Batiments"), ("lieu", "Lieux remarquables")):
        rows += [f"## {title}", "", "| Nom | Niveau | Zone | X | Y | Z |", "|---|---:|---|---:|---:|---:|"]
        for m in w.markers:
            if m["kind"] == kind:
                x, y, z = m["pos"]
                rows.append(f"| {m['name']} | {m['level']} | {m['group']} | {x:.0f} | {y:.0f} | {z:.0f} |")
        rows.append("")
    rows += ["## Passages entre niveaux (deux rochers au bord de la map)", "",
             "| Depuis | Vers | X | Y |", "|---|---|---:|---:|"]
    for s, d, x, y in gates:
        rows.append(f"| Niveau {s} ({L.LEVELS[s][0]}) | Niveau {d} ({L.LEVELS[d][0]}) | {x:.0f} | {y:.0f} |")
    rows.append("| Enies Lobby (Portes de la Justice, niveau 2) | Impel Down (niveau 3) | - | - |")
    rows += ["", "## Points d'arrivee (info_teleport_destination)", "", "| Nom | X | Y | Z |", "|---|---:|---:|---:|"]
    for e in w.entities:
        if e.classname == "info_teleport_destination":
            x, y, z = (float(v) for v in e.kv["origin"].split())
            rows.append(f"| {e.kv['targetname']} | {x:.0f} | {y:.0f} | {z:.0f} |")
    with open(path, "w") as fh:
        fh.write("\n".join(rows) + "\n")


def build(args):
    t0 = time.time()
    w = World()
    environment(w)
    spawns(w)
    gates = L.build_level_gates(w)
    mods = args.islands.split(",") if args.islands else ISLAND_MODULES
    for name in mods:
        mod = importlib.import_module(f".islands.{name}", __package__)
        lv = L.ISLAND_LEVEL[name]
        with w.level(lv, L.sea_z(lv)), w.group(L.ISLANDS[name][0]):
            mod.build(w)
    if not args.islands:
        L.build_harbors(w)
    from .terrain import build_all
    for k, (n, t) in build_all(w).items():
        print(f"  terrain {k}: {n} carreaux de relief, {t} arbres")
    print("construction", round(time.time() - t0, 1), "s", w.counts())
    errors, solved = validate(w)
    for e in errors[:40]:
        print("ERREUR", e)
    print("plans BSP estimes:", getattr(w, "bsp_planes", "?"), "/ 65536")
    print("erreurs:", len(errors))
    from .checks import coplanar_tops, run as run_checks, terrain_checks
    probs = run_checks(w) + coplanar_tops(w, solved) + terrain_checks(w)
    for pb in probs:
        print("JOUABILITE", pb)
    print("problemes de jouabilite:", len(probs))

    out_src = os.path.join(ROOT, "maps", "src")
    os.makedirs(out_src, exist_ok=True)
    write_vmf(w, os.path.join(out_src, MAP_NAME + ".vmf"))
    build_dir = os.path.join(ROOT, "tools", "mapgen", "build")
    os.makedirs(build_dir, exist_ok=True)
    export_preview(w, solved, os.path.join(build_dir, "preview.json"))
    with open(os.path.join(build_dir, "markers.json"), "w") as fh:
        json.dump({"markers": w.markers, "gates": gates}, fh, indent=1)
    if not args.islands:
        write_places(w, gates, os.path.join(ROOT, "LIEUX.md"))

    if not args.no_tex:
        isl = [m for m in w.markers if m["kind"] == "ile"]
        wm = T.world_map(isl, {lv: n for lv, (n, _) in L.LEVELS.items()})
        M.export_all(os.path.join(ROOT, "addon"), os.path.join(build_dir, "png"),
                     extra={M.WORLD_MAP: wm})
        write_packlist(os.path.join(out_src, "packlist.txt"))
    print("termine en", round(time.time() - t0, 1), "s")
    return w, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tex", action="store_true")
    ap.add_argument("--islands", default="")
    args = ap.parse_args()
    build(args)


if __name__ == "__main__":
    main()
