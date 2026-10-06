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
SKY_Z = 10240      # camera du skybox 3D
SKY_SCALE = 16


def environment(w):
    H = L.MAP_HALF
    with w.group("Ocean et ciel"):
        t = 128
        top = 7168
        bot = -1024
        # coque etanche (skybox)
        w.add_world(G.box(-H - t, -H - t, bot - t, H + t, H + t, bot, M.SKY))
        w.add_world(G.box(-H - t, -H - t, top, H + t, H + t, top + t, M.SKY))
        w.add_world(G.box(-H - t, -H - t, bot, -H, H + t, top, M.SKY))
        w.add_world(G.box(H, -H - t, bot, H + t, H + t, top, M.SKY))
        w.add_world(G.box(-H, -H - t, bot, H, -H, top, M.SKY))
        w.add_world(G.box(-H, H, bot, H, H + t, top, M.SKY))
        # fond marin + ocean
        w.add_world(G.box(-H, -H, bot, H, H, L.SEA_FLOOR, {"top": M.SEAFLOOR, "default": M.NODRAW}))
        w.add_world(G.box(-H, -H, L.SEA_FLOOR, H, H, 0, {"top": M.WATER, "default": M.NODRAW}))

        # lumiere du soleil
        w.ent("light_environment", (0, 0, 2048), pitch=SUN_PITCH, angles=(SUN_PITCH, SUN_YAW, 0),
              _light="255 242 220 520", _lightHDR="-1 -1 -1 1", _lightscaleHDR=1,
              _ambient="150 196 240 170", _ambientHDR="-1 -1 -1 1", _AmbientScaleHDR=1,
              SunSpreadAngle=4)
        w.ent("shadow_control", (0, 0, 2112), angles=(-SUN_PITCH, SUN_YAW, 0), color="110 120 140",
              distance=90, disableallshadows=0)
        w.ent("env_fog_controller", (0, 0, 2176), targetname="fog_mer", fogenable=1, fogblend=0,
              fogcolor="190 222 244", fogcolor2="190 222 244", fogstart=5000, fogend=26000,
              fogmaxdensity=0.6, farz=-1, fogdir="1 0 0", use_angles=0, angles="0 0 0",
              spawnflags=1)
        w.ent("water_lod_control", (0, 0, 2240), cheapwaterstartdistance=3000,
              cheapwaterenddistance=9000)
        w.ent("env_tonemap_controller", (0, 0, 2304), targetname="tonemap")
        # pont vers le Lua des portails (navires / constructions soudees)
        w.ent("lua_run", (0, 0, 2368), targetname="op_seagate_lua",
              Code="if OP_SeaGate then OP_SeaGate() end")

    # --- skybox 3D : ocean infini + Red Line a l'horizon -------------------
    with w.group("Skybox 3D"):
        sz0, sz1 = 9216, 13312
        sh = H
        w.add_world(G.box(-sh - t, -sh - t, sz0 - t, sh + t, sh + t, sz0, M.SKY))
        w.add_world(G.box(-sh - t, -sh - t, sz1, sh + t, sh + t, sz1 + t, M.SKY))
        w.add_world(G.box(-sh - t, -sh - t, sz0, -sh, sh + t, sz1, M.SKY))
        w.add_world(G.box(sh, -sh - t, sz0, sh + t, sh + t, sz1, M.SKY))
        w.add_world(G.box(-sh, -sh - t, sz0, sh, -sh, sz1, M.SKY))
        w.add_world(G.box(-sh, sh, sz0, sh, sh + t, sz1, M.SKY))
        w.add_world(G.box(-sh, -sh, sz0, sh, sh, SKY_Z - 48, {"top": M.SEAFLOOR, "default": M.NODRAW}))
        w.add_world(G.box(-sh, -sh, SKY_Z - 48, sh, sh, SKY_Z, {"top": M.WATER_SKY, "default": M.NODRAW}))
        w.ent("sky_camera", (0, 0, SKY_Z), scale=SKY_SCALE, fogenable=1, fogblend=0,
              fogcolor="190 222 244", fogcolor2="190 222 244", fogstart=12000, fogend=150000,
              fogmaxdensity=0.7, use_angles=0, fogdir="1 0 0", angles="0 0 0")
        # la Red Line : falaise rouge colossale au nord
        rl = 12800
        for i, (x0, x1, hh) in enumerate(((-15872, -9000, 900), (-9000, -2500, 1000), (-2500, 3800, 940),
                                          (3800, 10000, 1040), (10000, 15872, 920))):
            w.add(G.box(x0, rl + (i % 2) * 140, SKY_Z - 60, x1, rl + 1200, SKY_Z + hh,
                        {"top": M.SNOW, "default": M.ROCK_RED}))
        # iles lointaines (silhouettes)
        for (x, y, r, hh) in ((-7000, -6500, 260, 90), (8200, -7600, 340, 140), (-9800, 2400, 300, 70),
                              (6800, 5200, 220, 160), (-4200, 7400, 180, 60), (11000, -900, 260, 110),
                              (-12500, -2400, 400, 120), (2600, -12500, 300, 80)):
            w.add(G.frustum(x, y, r, r * 0.25, SKY_Z - 50, SKY_Z + hh, 9, {"top": M.GRASS_DARK, "default": M.ROCK}))
            w.add(G.frustum(x, y, r * 1.25, r * 0.95, SKY_Z - 50, SKY_Z + 4, 9, M.SAND))


def spawns(w):
    with w.group("Spawns"):
        for i in range(24):
            a = 2 * math.pi * i / 24
            r = 300 + 120 * (i % 3)
            w.ent("info_player_start", (math.cos(a) * r, -60 + math.sin(a) * r, 64),
                  angles=(0, (math.degrees(a) + 180) % 360, 0))


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
    for kind, title in (("ile", "Iles"), ("batiment", "Batiments"), ("lieu", "Lieux remarquables")):
        rows += [f"## {title}", "", "| Nom | Zone | X | Y | Z |", "|---|---|---:|---:|---:|"]
        for m in w.markers:
            if m["kind"] == kind:
                x, y, z = m["pos"]
                rows.append(f"| {m['name']} | {m['group']} | {x:.0f} | {y:.0f} | {z:.0f} |")
        rows.append("")
    rows += ["## Portails en mer (Portes de la Grand Line)", "",
             "| Depart | Destination | X | Y |", "|---|---|---:|---:|"]
    for s, d, x, y, _ in gates:
        rows.append(f"| {L.ISLANDS[s][0]} | {L.ISLANDS[d][0]} | {x:.0f} | {y:.0f} |")
    rows.append("| Enies Lobby (Portes de la Justice) | Impel Down | - | - |")
    rows.append("| Enies Lobby | Marineford | - | - |")
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
    with w.group("Portails"):
        gates = L.build_gates(w)
    mods = args.islands.split(",") if args.islands else ISLAND_MODULES
    for name in mods:
        mod = importlib.import_module(f".islands.{name}", __package__)
        with w.group(L.ISLANDS[name][0]):
            mod.build(w)
    print("construction", round(time.time() - t0, 1), "s", w.counts())
    errors, solved = validate(w)
    for e in errors[:40]:
        print("ERREUR", e)
    print("erreurs:", len(errors))
    from .checks import run as run_checks
    probs = run_checks(w)
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
        routes = []
        for s, d, *_ in gates:
            if s == L.HUB or d == L.HUB:
                continue
            routes.append((L.center(s), L.center(d)))
        wm = T.world_map(isl, routes)
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
