"""Catalogue des materiaux de la map + export VTF/VMT (GMod) et PNG (Blender).

Toutes les textures sont dans materials/onepiece/ et sont generees ici :
aucun contenu externe n'est necessaire hormis Half-Life 2 (inclus dans GMod).
"""
import os

import numpy as np
from PIL import Image

from . import texgen as T

P = "onepiece/"

# name -> dict(tile=(u,v) unites, px=(w,h), surf, lms, kind, gen)
MATS = {}

TOOL_MATS = {
    "tools/toolsnodraw": {"tile": (64, 64), "px": (64, 64), "lms": 16},
    "tools/toolsskybox": {"tile": (64, 64), "px": (64, 64), "lms": 16},
    "tools/toolstrigger": {"tile": (64, 64), "px": (64, 64), "lms": 16},
    "tools/toolsplayerclip": {"tile": (64, 64), "px": (64, 64), "lms": 16},
    "tools/toolsclip": {"tile": (64, 64), "px": (64, 64), "lms": 16},
    "tools/toolsinvisible": {"tile": (64, 64), "px": (64, 64), "lms": 16},
}
NODRAW = "tools/toolsnodraw"
SKY = "tools/toolsskybox"
TRIGGER = "tools/toolstrigger"
CLIP = "tools/toolsplayerclip"


def reg(name, gen, tile=256, px=(512, 512), surf="default", lms=32, kind="lm", **extra):
    if isinstance(tile, (int, float)):
        tile = (tile, tile)
    MATS[P + name] = dict(gen=gen, tile=tile, px=px, surf=surf, lms=lms, kind=kind, **extra)
    return P + name


def _img(fn, *a, **k):
    return lambda: fn(*a, **k)


# --- terrains --------------------------------------------------------------
GRASS = reg("grass", _img(T.t_grass), 512, surf="grass", lms=64)
GRASS_DARK = reg("grass_dark", _img(T.t_grass, 8, (54, 120, 44), (88, 150, 52)), 512, surf="grass", lms=64)
SAND = reg("sand", _img(T.t_sand), 512, surf="sand", lms=64)
SEAFLOOR = reg("seafloor", _img(T.t_seafloor), 768, surf="sand", lms=128)
DESERT = reg("desert_sand", _img(T.t_desert), 512, surf="sand", lms=64)
SNOW = reg("snow", _img(T.t_snow), 512, surf="snow", lms=64)
ROCK = reg("rock", _img(T.t_rock), 512, surf="rock", lms=64)
ROCK_DARK = reg("rock_dark", _img(T.t_rock, 61, (96, 92, 96), (60, 58, 64)), 512, surf="rock", lms=64)
ROCK_RED = reg("rock_red", _img(T.t_rock, 62, (186, 82, 60), (130, 52, 40)), 512, surf="rock", lms=128)
DIRT = reg("dirt", _img(T.t_dirt), 512, surf="dirt", lms=64)

# --- bois ------------------------------------------------------------------
PLANKS = reg("planks", _img(T.t_planks), 128, surf="wood")
PLANKS_LIGHT = reg("planks_light", _img(T.t_planks, 11, (196, 152, 98)), 128, surf="wood")
PLANKS_DARK = reg("planks_dark", _img(T.t_planks, 12, (104, 66, 40)), 128, surf="wood")
PLANKS_RED = reg("planks_red", _img(T.t_planks, 13, (150, 50, 40)), 128, surf="wood")
HULL_WHITE = reg("hull_white", _img(T.t_planks, 14, (236, 234, 226), 8, (150, 150, 150), 0.05), 128, surf="wood")
HULL_YELLOW = reg("hull_yellow", _img(T.t_planks, 15, (230, 190, 96), 8, (130, 96, 40)), 128, surf="wood")
WOOD_BEAM = reg("wood_beam", _img(T.t_planks, 16, (96, 60, 36), 8, (60, 36, 20), 0.1, True), 128, surf="wood")
BARK = reg("bark_palm", _img(T.t_bark), 128, surf="wood")
MANGROVE = reg("bark_mangrove", _img(T.t_mangrove_bark), 512, surf="wood", lms=64)
LEAVES = reg("leaves", _img(T.t_leaves), 256, surf="grass")
PALM = reg("leaves_palm", _img(T.t_palm_leaves), 256, surf="grass")
CANOPY = reg("canopy_mangrove", _img(T.t_leaves, 17, (110, 186, 70), (60, 140, 50), (190, 230, 120)), 512,
             surf="grass", lms=64)
SAKURA = reg("sakura", _img(T.t_sakura), 256, surf="grass")
PINE = reg("pine_snow", _img(T.t_pine_snow), 256, surf="grass")

# --- maconnerie --------------------------------------------------------------
WHITE = reg("plaster_white", _img(T.t_plaster, 20, (242, 240, 234)), 256, surf="plaster")
CREAM = reg("plaster_cream", _img(T.t_plaster, 21, (240, 222, 186)), 256, surf="plaster")
PINK = reg("plaster_pink", _img(T.t_plaster, 22, (236, 178, 178)), 256, surf="plaster")
YELLOW = reg("plaster_yellow", _img(T.t_plaster, 23, (244, 214, 120)), 256, surf="plaster")
SKYBLUE = reg("plaster_blue", _img(T.t_plaster, 24, (150, 196, 230)), 256, surf="plaster")
MINT = reg("plaster_mint", _img(T.t_plaster, 25, (168, 222, 196)), 256, surf="plaster")
TERRA = reg("plaster_terracotta", _img(T.t_plaster, 26, (214, 128, 86)), 256, surf="plaster")
SANDSTONE = reg("sandstone", _img(T.t_plaster, 27, (226, 192, 140), 0.1), 256, surf="concrete")
INTERIOR = reg("interior_wall", _img(T.t_plaster, 28, (232, 220, 200), 0.05), 256, surf="plaster")
STONE = reg("stone_blocks", _img(T.t_bricks), 128, surf="concrete")
STONE_GREY = reg("stone_grey", _img(T.t_bricks, 30, (150, 154, 160), (100, 102, 108)), 128, surf="concrete")
STONE_DARK = reg("stone_dark", _img(T.t_bricks, 31, (82, 80, 88), (46, 44, 50), 8, 4), 192, surf="concrete")
SANDBLOCK = reg("sandstone_blocks", _img(T.t_bricks, 32, (226, 190, 136), (180, 146, 100)), 128, surf="concrete")
BRICK = reg("brick_red", _img(T.t_bricks, 33, (176, 84, 62), (210, 200, 186), 16, 8), 128, surf="brick")
COBBLE = reg("cobble", _img(T.t_cobble), 256, surf="concrete", lms=32)
PAVING = reg("paving_light", _img(T.t_cobble, 34, (226, 218, 200), (196, 188, 170), 40), 256, surf="concrete")
SANDPAVE = reg("paving_sand", _img(T.t_cobble, 35, (232, 200, 150), (206, 170, 120), 40), 256, surf="concrete")
MARBLE = reg("marble", _img(T.t_marble), 256, surf="concrete", kind="lm_env")
GOLD = reg("gold", _img(T.t_gold), 128, surf="metal", kind="lm_env")
METAL = reg("metal_plates", _img(T.t_metal), 128, surf="metal", kind="lm_env")
IRON = reg("iron", _img(T.t_flat, (52, 54, 60), 36, 0.12), 128, surf="metal", kind="lm_env")
BARS = reg("metal_bars", _img(T.t_bars), 64, surf="metal", kind="lm_alpha")

STAIRS = reg("stairs_stone", _img(T.t_stairs), 128, surf="concrete")
STAIRS_WOOD = reg("stairs_wood", _img(T.t_stairs, 81, (170, 118, 70)), 128, surf="wood")
STAIRS_SAND = reg("stairs_sand", _img(T.t_stairs, 82, (226, 192, 140)), 128, surf="concrete")

# --- toits -------------------------------------------------------------------
ROOF_RED = reg("roof_red", _img(T.t_roof), 128, surf="tile")
ROOF_BLUE = reg("roof_blue", _img(T.t_roof, 40, (54, 104, 178)), 128, surf="tile")
ROOF_ORANGE = reg("roof_orange", _img(T.t_roof, 41, (226, 128, 58)), 128, surf="tile")
ROOF_GREEN = reg("roof_green", _img(T.t_roof, 42, (62, 132, 96), 16, 8, False), 128, surf="tile")
ROOF_DARK = reg("roof_dark", _img(T.t_roof, 43, (64, 66, 78), 16, 8, False), 128, surf="tile")
ROOF_TEAL = reg("roof_teal", _img(T.t_roof, 44, (60, 170, 170)), 128, surf="tile")
ROOF_PURPLE = reg("roof_purple", _img(T.t_roof, 45, (130, 80, 160)), 128, surf="tile")
ROOF_THATCH = reg("roof_thatch", _img(T.t_planks, 46, (200, 160, 80), 8, (150, 110, 50), 0.15), 128, surf="wood")

# --- couleurs unies / tissus ------------------------------------------------
MARINE_BLUE = reg("paint_marine_blue", _img(T.t_flat, (44, 92, 176)), 256, surf="metal")
RED = reg("paint_red", _img(T.t_flat, (196, 40, 40)), 256, surf="wood")
BLACK = reg("paint_black", _img(T.t_flat, (30, 30, 34)), 256, surf="metal")
WHITE_PAINT = reg("paint_white", _img(T.t_flat, (246, 246, 244)), 256, surf="wood")
TORII = reg("paint_torii", _img(T.t_flat, (214, 56, 36)), 256, surf="wood")
CARPET = reg("carpet_red", _img(T.t_flat, (150, 28, 36), 37, 0.15), 128, surf="carpet")
AWN_RED = reg("fabric_red_white", _img(T.t_fabric_stripes, (210, 46, 46), (250, 246, 236)), 128, surf="carpet")
AWN_BLUE = reg("fabric_blue_white", _img(T.t_fabric_stripes, (40, 110, 190), (250, 246, 236)), 128, surf="carpet")
AWN_GREEN = reg("fabric_green", _img(T.t_fabric_stripes, (60, 150, 80), (240, 220, 120)), 128, surf="carpet")
AWN_PURPLE = reg("fabric_purple", _img(T.t_fabric_stripes, (130, 60, 160), (240, 200, 90)), 128, surf="carpet")
JP_WALL = reg("jp_wall", _img(T.t_jp_wall), (128, 160), surf="plaster")
WATERFALL = reg("waterfall", _img(T.t_waterfall), 256, surf="water", kind="scroll", lms=64)
PORTAL = reg("portal_swirl", _img(T.t_portal), 256, kind="unlit_add")
GLOW_WARM = reg("glow_warm", _img(T.t_flat, (255, 220, 140), 38, 0.0), 64, kind="unlit")
GLOW_CYAN = reg("glow_cyan", _img(T.t_flat, (120, 240, 255), 39, 0.0), 64, kind="unlit")

# --- facades (fenetre par tuile de 128 x 160) -------------------------------
FH = 160
WIN_WHITE = reg("win_white", _img(T.t_windows, (242, 240, 234), 40, (60, 100, 180), None), (128, FH), surf="plaster")
WIN_MARINE = reg("win_marine", _img(T.t_windows, (244, 244, 240), 41, (44, 92, 176), None, (70, 130, 210)), (128, FH), surf="plaster")
WIN_CREAM = reg("win_cream", _img(T.t_windows, (240, 222, 186), 42, (250, 250, 246), (60, 130, 80)), (128, FH), surf="plaster")
WIN_PINK = reg("win_pink", _img(T.t_windows, (236, 178, 178), 43, (250, 250, 246), (70, 110, 170)), (128, FH), surf="plaster")
WIN_YELLOW = reg("win_yellow", _img(T.t_windows, (244, 214, 120), 44, (250, 250, 246), (60, 120, 160)), (128, FH), surf="plaster")
WIN_BLUE = reg("win_blue", _img(T.t_windows, (150, 196, 230), 45, (250, 250, 246), (230, 230, 230)), (128, FH), surf="plaster")
WIN_MINT = reg("win_mint", _img(T.t_windows, (168, 222, 196), 46, (250, 250, 246), (180, 80, 60)), (128, FH), surf="plaster")
WIN_TERRA = reg("win_terracotta", _img(T.t_windows, (214, 128, 86), 47, (250, 240, 220), (60, 110, 90)), (128, FH), surf="plaster")
WIN_SAND = reg("win_sandstone", _img(T.t_windows, (226, 192, 140), 48, (180, 130, 80), None, (40, 60, 90), True), (128, FH), surf="concrete")
WIN_STONE = reg("win_stone", _img(T.t_windows, (150, 154, 160), 49, (90, 90, 96), None, (40, 60, 90), True), (128, FH), surf="concrete")
WIN_DARK = reg("win_dark", _img(T.t_windows, (82, 80, 88), 50, (50, 48, 54), None, (200, 80, 40), False, True), (128, FH), surf="concrete")
WIN_BRICK = reg("win_brick", _img(T.t_windows, (176, 84, 62), 51, (240, 236, 226), (40, 70, 120)), (128, FH), surf="brick")
WIN_WOOD = reg("win_wood", _img(T.t_windows, (156, 108, 66), 52, (240, 220, 180), None, (90, 140, 180)), (128, FH), surf="wood")
WIN_SNOW = reg("win_snowlodge", _img(T.t_windows, (120, 78, 50), 53, (240, 240, 240), (170, 40, 40), (250, 200, 120)), (128, FH), surf="wood")

# --- portes / panneaux / drapeaux (textures ajustees a la face) ---------------
DOOR = reg("door_wood", _img(T.door), 64, px=(256, 512), surf="wood")
DOOR_BIG = reg("door_double", _img(T.door, 512, 512, (110, 64, 34), True), 64, surf="wood")
DOOR_IRON = reg("door_iron", _img(T.door, 512, 512, (70, 72, 80), True), 64, surf="metal")
FLAG_SH = reg("flag_strawhat", _img(T.flag_strawhat), 64, surf="carpet")
FLAG_MARINE = reg("flag_marine", _img(T.flag_marine), 64, surf="carpet")
SAIL = reg("sail_plain", _img(T.sail), 64, surf="carpet")
SAIL_MARINE = reg("sail_marine", _img(T.sail, 512, 512, "marine"), 64, surf="carpet")
SAIL_SH = reg("sail_strawhat", _img(T.sail, 512, 512, "strawhat"), 64, surf="carpet")
SAIL_STRIPES = reg("sail_stripes", _img(T.sail, 512, 512, "stripes"), 64, surf="carpet")
KANJI_JUSTICE = reg("kanji_justice", _img(T.kanji, "正義"), 64, px=(1024, 512), surf="carpet")
KANJI_MARINE = reg("kanji_marine", _img(T.kanji, "海軍", 1024, 512, (250, 250, 248), (40, 86, 170), (40, 86, 170)),
                   64, px=(1024, 512), surf="concrete")
KANJI_WANO = reg("kanji_wano", _img(T.kanji, "和の国", 1024, 512, (214, 56, 36), (250, 236, 200)), 64,
                 px=(1024, 512), surf="wood")
CLOCK = reg("clock_face", _img(T.clock_face), 64, surf="concrete")

PLASTER_CABINS = [RED, MARINE_BLUE, YELLOW, MINT, PINK, TERRA, SKYBLUE, WHITE_PAINT]


def paint_cycle(i):
    return PLASTER_CABINS[i % len(PLASTER_CABINS)]


SIGNS = {}


def sign_mat(key, text, sub=None, **kw):
    name = reg("sign_" + key, _img(T.sign, text, 512, 128, sub=sub, **kw), 64, px=(512, 128), surf="wood")
    SIGNS[key] = name
    return name


GROVES = {}


def grove_mat(num):
    if num not in GROVES:
        GROVES[num] = reg(f"grove_{num}", _img(T.grove, num), 64, surf="wood")
    return GROVES[num]


# --- eau ----------------------------------------------------------------------
WATER = reg("water_ocean", None, 512, kind="water", surf="water")
WATER_SKY = reg("water_ocean_sky", None, 512, kind="water", surf="water")
WATER_OASIS = reg("water_oasis", None, 512, kind="water", surf="water")
WORLD_MAP = reg("world_map", None, 64, px=(1024, 1024), surf="wood")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _vmt(name, info):
    base = name
    kind = info["kind"]
    surf = info["surf"]
    if kind == "lm":
        return ('"LightmappedGeneric"\n{\n'
                f'\t"$basetexture" "{base}"\n\t"$surfaceprop" "{surf}"\n}}\n')
    if kind == "lm_env":
        return ('"LightmappedGeneric"\n{\n'
                f'\t"$basetexture" "{base}"\n\t"$surfaceprop" "{surf}"\n'
                '\t"$envmap" "env_cubemap"\n\t"$envmaptint" "[.18 .18 .18]"\n'
                '\t"$normalmapalphaenvmapmask" "0"\n}\n')
    if kind == "lm_alpha":
        return ('"LightmappedGeneric"\n{\n'
                f'\t"$basetexture" "{base}"\n\t"$surfaceprop" "{surf}"\n'
                '\t"$alphatest" "1"\n\t"$alphatestreference" "0.5"\n\t"$nocull" "1"\n}\n')
    if kind == "scroll":
        return ('"LightmappedGeneric"\n{\n'
                f'\t"$basetexture" "{base}"\n\t"$surfaceprop" "{surf}"\n'
                '\t"$selfillum" "0"\n'
                '\t"Proxies"\n\t{\n\t\t"TextureScroll"\n\t\t{\n'
                '\t\t\t"texturescrollvar" "$basetexturetransform"\n'
                '\t\t\t"texturescrollrate" "0.6"\n\t\t\t"texturescrollangle" "90"\n\t\t}\n\t}\n}\n')
    if kind == "unlit_add":
        return ('"UnlitGeneric"\n{\n'
                f'\t"$basetexture" "{base}"\n\t"$additive" "1"\n\t"$nocull" "1"\n'
                '\t"Proxies"\n\t{\n\t\t"TextureScroll"\n\t\t{\n'
                '\t\t\t"texturescrollvar" "$basetexturetransform"\n'
                '\t\t\t"texturescrollrate" "0.15"\n\t\t\t"texturescrollangle" "45"\n\t\t}\n\t}\n}\n')
    if kind == "unlit":
        return f'"UnlitGeneric"\n{{\n\t"$basetexture" "{base}"\n}}\n'
    raise ValueError(kind)


def _water_vmt(fogcolor, fogend, cheap=False, beneath=None, tool="onepiece/water_tool"):
    s = '"Water"\n{\n\t"%compilewater" "1"\n'
    s += f'\t"%tooltexture" "{tool}"\n'
    s += '\t"$surfaceprop" "water"\n'
    if beneath is None:
        s += '\t"$abovewater" "0"\n'
    else:
        s += '\t"$abovewater" "1"\n'
        s += f'\t"$bottommaterial" "{beneath}"\n'
        s += '\t"$underwateroverlay" "effects/water_warp01"\n'
    s += '\t"$envmap" "env_cubemap"\n'
    s += '\t"$refracttexture" "_rt_WaterRefraction"\n\t"$refractamount" "0.25"\n'
    s += '\t"$refracttint" "[0.80 0.98 0.98]"\n'
    if beneath is not None:
        s += '\t"$reflecttexture" "_rt_WaterReflection"\n\t"$reflectamount" "0.6"\n'
        s += '\t"$reflecttint" "[0.85 0.95 1]"\n\t"$reflectentities" "0"\n'
    if cheap:
        s += '\t"$forcecheap" "1"\n\t"$envmaptint" "[0.5 0.6 0.65]"\n'
    else:
        s += '\t"$cheapwaterstartdistance" "3000"\n\t"$cheapwaterenddistance" "9000"\n'
        s += '\t"$envmaptint" "[0.4 0.5 0.55]"\n'
    s += '\t"$normalmap" "onepiece/water_normal"\n\t"$bumpframe" "0"\n'
    s += '\t"$scale" "[1 1]"\n'
    s += f'\t"$fogenable" "1"\n\t"$fogcolor" "{{{fogcolor[0]} {fogcolor[1]} {fogcolor[2]}}}"\n'
    s += f'\t"$fogstart" "0"\n\t"$fogend" "{fogend}"\n'
    s += ('\t"Proxies"\n\t{\n\t\t"AnimatedTexture"\n\t\t{\n\t\t\t"animatedtexturevar" "$normalmap"\n'
          '\t\t\t"animatedtextureframenumvar" "$bumpframe"\n\t\t\t"animatedtextureframerate" "0"\n\t\t}\n'
          '\t\t"TextureScroll"\n\t\t{\n\t\t\t"texturescrollvar" "$bumptransform"\n'
          '\t\t\t"texturescrollrate" "0.03"\n\t\t\t"texturescrollangle" "45"\n\t\t}\n\t}\n')
    s += '}\n'
    return s


def save_vtf(arr, path, alpha=False, normal=False):
    from srctools.vtf import VTF, ImageFormats, VTFFlags

    arr = np.asarray(arr)
    if arr.dtype != np.uint8:
        arr = T.to_img(arr)
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        a = np.full((h, w, 1), 255, np.uint8)
        arr = np.concatenate([arr, a], 2)
    flags = VTFFlags.EMPTY
    if normal:
        fmt = ImageFormats.BGR888
        flags |= VTFFlags.NORMAL
    elif alpha:
        fmt = ImageFormats.DXT5
        flags |= VTFFlags.EIGHTBITALPHA
    else:
        fmt = ImageFormats.DXT1
    vtf = VTF(w, h, (7, 2), fmt=fmt, flags=flags)
    vtf.get().copy_from(arr.tobytes(), ImageFormats.RGBA8888)
    vtf.compute_mipmaps()
    with open(path, "wb") as fh:
        vtf.save(fh)


def export_all(content_dir, png_dir, extra=None, only=None):
    """Genere toutes les textures. extra: dict nom -> image (ex: carte du monde)."""
    mdir = os.path.join(content_dir, "materials", "onepiece")
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    extra = extra or {}
    for name, info in MATS.items():
        short = name.split("/", 1)[1]
        if only and short not in only:
            continue
        if info["kind"] == "water":
            continue
        if name in extra:
            img = extra[name]
        elif info["gen"] is None:
            continue
        else:
            img = info["gen"]()
        if isinstance(img, Image.Image):
            arr = np.asarray(img.convert("RGBA" if info["kind"] == "lm_alpha" else "RGB"))
        else:
            arr = T.to_img(img)
        Image.fromarray(arr).save(os.path.join(png_dir, short + ".png"))
        save_vtf(arr, os.path.join(mdir, short + ".vtf"), alpha=info["kind"] == "lm_alpha")
        with open(os.path.join(mdir, short + ".vmt"), "w") as fh:
            fh.write(_vmt(name, info))
    if only:
        return
    # eau
    nm = T.water_normal()
    save_vtf(nm, os.path.join(mdir, "water_normal.vtf"), normal=True)
    Image.fromarray(T.to_img(nm)).save(os.path.join(png_dir, "water_normal.png"))
    tool = T.t_flat((40, 150, 170))
    save_vtf(tool, os.path.join(mdir, "water_tool.vtf"))
    with open(os.path.join(mdir, "water_tool.vmt"), "w") as fh:
        fh.write('"LightmappedGeneric"\n{\n\t"$basetexture" "onepiece/water_tool"\n}\n')
    sea = (28, 132, 150)
    files = {
        "water_ocean": _water_vmt(sea, 1100, beneath="onepiece/water_ocean_beneath"),
        "water_ocean_beneath": _water_vmt(sea, 1100),
        "water_ocean_sky": _water_vmt((40, 120, 150), 400, cheap=True,
                                      beneath="onepiece/water_ocean_beneath"),
        "water_oasis": _water_vmt((40, 150, 140), 300, beneath="onepiece/water_oasis_beneath"),
        "water_oasis_beneath": _water_vmt((40, 150, 140), 300),
    }
    for k, v in files.items():
        with open(os.path.join(mdir, k + ".vmt"), "w") as fh:
            fh.write(v)
