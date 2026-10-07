"""Rendu Blender (Cycles) de la map a partir de build/preview.json.

    python tools/mapgen/render_blender.py [--shots nom1,nom2] [--samples 64] [--res 1600x900]
    (necessite le module bpy :  pip install bpy)

La geometrie est exactement celle des brushes du VMF (meme decoupe, memes UV),
on voit donc dans Blender ce qu'on aura dans GMod.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
S = 0.0254           # 1 unite Source = 1 pouce
SUN_YAW = 50
SUN_PITCH = -50

ROUGH = {"marble": 0.25, "gold": 0.3, "metal_plates": 0.45, "iron": 0.4, "glow_cyan": 1, "paint_red": 0.5,
         "paint_marine_blue": 0.5, "paint_white": 0.5, "paint_torii": 0.45, "hull_white": 0.6}
METAL = {"gold": 1.0, "metal_plates": 0.6, "iron": 0.7, "metal_bars": 0.6}
HAZE_COLOR = (0.62, 0.78, 0.95)
HAZE_LEVEL = 1.0
HAZE_MAX = 0.85
EMIT = {"portal_swirl": 4.0, "glow_cyan": 6.0, "glow_warm": 4.0}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.unit_settings.system = "METRIC"
    return sc


def blend_mat(name, base, base2, png_dir):
    """Materiau WorldVertexTransition : base -> base2 selon l'attribut de couleur 'alpha'."""
    short = name.split("/", 1)[1]
    mat = bpy.data.materials.new(short)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.9
    tex = []
    for b in (base, base2):
        t = nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(png_dir, b.split("/", 1)[1] + ".png"), check_existing=True)
        tex.append(t)
    attr = nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "alpha"
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    links.new(attr.outputs["Color"], mix.inputs["Factor"])
    links.new(tex[0].outputs["Color"], mix.inputs[6])
    links.new(tex[1].outputs["Color"], mix.inputs[7])
    links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return mat


def image_mat(name, png_dir):
    short = name.split("/", 1)[1]
    mat = bpy.data.materials.new(short)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        out = nodes.new("ShaderNodeOutputMaterial")
        links.new(bsdf.outputs[0], out.inputs[0])
    path = os.path.join(png_dir, short + ".png")
    if os.path.exists(path):
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path, check_existing=True)
        tex.interpolation = "Linear"
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if short in EMIT:
            links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = EMIT[short]
        if short == "metal_bars":
            links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        if short == "waterfall":
            links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = 0.4
    bsdf.inputs["Roughness"].default_value = ROUGH.get(short, 0.85)
    bsdf.inputs["Metallic"].default_value = METAL.get(short, 0.0)
    if short == "portal_swirl":
        bsdf.inputs["Alpha"].default_value = 0.75
    return mat


LEVELS = {1: -11264, 2: -3072, 3: 5120}


def level_of(z):
    for lv, sz in LEVELS.items():
        if sz - 1200 < z < sz + 3800:
            return lv
    return 0


def level_collection(lv):
    name = f"Niveau {lv}"
    if name not in bpy.data.collections:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return bpy.data.collections[name]


def build_geometry(data, png_dir):
    objs = []
    for name, d in data["materials"].items():
        verts = d["verts"]
        uvs = d["uvs"]
        short = name.split("/", 1)[1]
        alpha = d.get("alpha")
        mat = blend_mat(name, *d["blend"], png_dir) if "blend" in d else image_mat(name, png_dir)
        by_lv = {}
        for f in d["faces"]:
            by_lv.setdefault(level_of(verts[f[0]][2]), []).append(f)
        for lv, faces in by_lv.items():
            used = sorted({i for f in faces for i in f})
            remap = {o: n for n, o in enumerate(used)}
            vv = [(verts[i][0] * S, verts[i][1] * S, verts[i][2] * S) for i in used]
            ff = [[remap[i] for i in f] for f in faces]
            mesh = bpy.data.meshes.new(f"{short}_{lv}")
            mesh.from_pydata(vv, [], ff)
            uvl = mesh.uv_layers.new(name="UVMap")
            flat = []
            for poly in mesh.polygons:
                for li in poly.loop_indices:
                    flat.extend(uvs[used[mesh.loops[li].vertex_index]])
            uvl.data.foreach_set("uv", flat)
            if alpha is not None:
                ca = mesh.color_attributes.new("alpha", "FLOAT_COLOR", "POINT")
                cols = []
                for i in used:
                    a = alpha[i]
                    cols.extend((a, a, a, 1.0))
                ca.data.foreach_set("color", cols)
            mesh.update()
            ob = bpy.data.objects.new(f"{short}_{lv}", mesh)
            level_collection(lv).objects.link(ob)
            ob.data.materials.append(mat)
            objs.append(ob)
    return objs


def _move_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)


def water(sc):
    mat = ocean_material()
    deep = bpy.data.materials.new("deep")
    deep.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.78, 0.66, 0.42, 1)
    H = 15872 * 8
    for lv, sz in LEVELS.items():
        bpy.ops.mesh.primitive_cube_add(size=1)
        ob = bpy.context.active_object
        ob.name = f"Ocean_{lv}"
        ob.scale = (H * 2 * S, H * 2 * S, 1100 * S)
        ob.location = (0, 0, (sz - 550) * S)
        ob.data.materials.append(mat)
        _move_to(ob, level_collection(lv))
        bpy.ops.mesh.primitive_plane_add(size=1)
        fl = bpy.context.active_object
        fl.scale = (H * 2 * S, H * 2 * S, 1)
        fl.location = (0, 0, (sz - 772) * S)
        fl.data.materials.append(deep)
        _move_to(fl, level_collection(lv))


def ocean_material():
    mat = bpy.data.materials.new("ocean")
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    glass = nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = (1, 1, 1, 1)
    glass.inputs["Transmission Weight"].default_value = 1.0
    glass.inputs["Roughness"].default_value = 0.03
    glass.inputs["IOR"].default_value = 1.333
    # vagues
    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 6
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.02
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], glass.inputs["Normal"])
    links.new(glass.outputs[0], out.inputs["Surface"])
    vol = nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.30, 0.80, 0.82, 1)
    vol.inputs["Density"].default_value = 0.09
    sca = nodes.new("ShaderNodeVolumeScatter")
    sca.inputs["Color"].default_value = (0.35, 0.88, 0.92, 1)
    sca.inputs["Density"].default_value = 0.03
    add = nodes.new("ShaderNodeAddShader")
    links.new(vol.outputs[0], add.inputs[0])
    links.new(sca.outputs[0], add.inputs[1])
    links.new(add.outputs[0], out.inputs["Volume"])
    return mat


def sky_and_sun(sc, strength=0.065):
    wd = bpy.data.worlds.new("Ciel")
    sc.world = wd
    nt = wd.node_tree
    nodes, links = nt.nodes, nt.links
    bg = nodes.get("Background") or nodes.new("ShaderNodeBackground")
    out = nodes.get("World Output") or nodes.new("ShaderNodeOutputWorld")
    sky = nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(-SUN_PITCH)
    # azimut du soleil = 90 deg - rotation (verifie par test d'ombre)
    sky.sun_rotation = math.radians(90 - (SUN_YAW + 180))
    sky.altitude = 200
    sky.air_density = 1.0
    sky.aerosol_density = 1.6
    sky.sun_intensity = 1.0
    sky.sun_disc = True
    links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    links.new(bg.outputs[0], out.inputs[0])


def bubbles(data):
    mat = bpy.data.materials.new("bulle")
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = 1.05
    b.inputs["Thin Wall"].default_value = True
    b.inputs["Base Color"].default_value = (0.85, 0.95, 1.0, 1)
    b.inputs["Thin Film Thickness"].default_value = 450
    for e in data["entities"]:
        if e["class"] == "prop_dynamic" and "sphere" in e.get("model", ""):
            x, y, z = (float(c) for c in e["origin"].split())
            r = 89 if "375" in e["model"] else 47
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r * S, location=(x * S, y * S, z * S),
                                                 segments=24, ring_count=12)
            o = bpy.context.active_object
            o.data.materials.append(mat)
            bpy.ops.object.shade_smooth()
            _move_to(o, level_collection(level_of(z)))


def denoise_to_png(sc, exr_path, png_path):
    """Debruitage Intel OIDN (couleur + albedo + normales) puis export PNG
    avec la gestion des couleurs de la scene (AgX)."""
    import numpy as np
    import OpenEXR
    import pyoidn

    f = OpenEXR.File(exr_path)
    parts = {p.name().split(".", 1)[1]: p for p in f.parts}

    def ch(part, keys):
        c = parts[part].channels
        if len(keys) == 1:
            return np.ascontiguousarray(c[keys[0]].pixels[..., :3], dtype=np.float32)
        return np.ascontiguousarray(np.stack([c[k].pixels for k in keys], -1), dtype=np.float32)

    color = ch("Combined", ["ViewLayer.Combined"])
    albedo = ch("Denoising Albedo", ["ViewLayer.Denoising Albedo"])
    normal = ch("Denoising Normal", ["ViewLayer.Denoising Normal.X", "ViewLayer.Denoising Normal.Y",
                                     "ViewLayer.Denoising Normal.Z"])
    # brume atmospherique (passe Mist), le ciel n'est pas touche
    if "Mist" in parts:
        mk = list(parts["Mist"].channels)[0]
        mist = np.asarray(parts["Mist"].channels[mk].pixels, np.float32)
        depth = np.asarray(parts["Denoising Depth"].channels["ViewLayer.Denoising Depth.Z"].pixels, np.float32)
        geo = (depth > 0) & (depth < 1e7)
        k = (np.clip(mist, 0, 1) * HAZE_MAX * geo)[..., None]
        haze = np.array(HAZE_COLOR, np.float32) * HAZE_LEVEL
        color = np.ascontiguousarray(color * (1 - k) + haze * k, dtype=np.float32)
    out = np.zeros_like(color)
    dev = pyoidn.Device()
    dev.commit()
    flt = pyoidn.Filter(dev, "RT")
    flt.set_image(pyoidn.OIDN_IMAGE_COLOR, color, pyoidn.OIDN_FORMAT_FLOAT3)
    flt.set_image(pyoidn.OIDN_IMAGE_ALBEDO, albedo, pyoidn.OIDN_FORMAT_FLOAT3)
    flt.set_image(pyoidn.OIDN_IMAGE_NORMAL, normal, pyoidn.OIDN_FORMAT_FLOAT3)
    flt.set_image(pyoidn.OIDN_IMAGE_OUTPUT, out, pyoidn.OIDN_FORMAT_FLOAT3)
    flt.set_bool("hdr", True)
    flt.commit()
    flt.execute()
    h, w = out.shape[:2]
    rgba = np.concatenate([out, np.ones((h, w, 1), np.float32)], -1)
    img = bpy.data.images.new("debruite", w, h, float_buffer=True)
    img.pixels.foreach_set(np.flipud(rgba).ravel())
    ims = sc.render.image_settings
    ims.media_type = "IMAGE"
    ims.file_format = "PNG"
    img.save_render(png_path, scene=sc)
    ims.media_type = "MULTI_LAYER_IMAGE"
    ims.file_format = "OPEN_EXR_MULTILAYER"
    ims.color_depth = "32"
    bpy.data.images.remove(img)
    os.remove(exr_path)


def export_blend(path):
    """Sauvegarde la scene ; textures copiees en JPG a cote du .blend (chemins relatifs)."""
    d = os.path.dirname(os.path.abspath(path))
    tex = os.path.join(d, "textures")
    os.makedirs(tex, exist_ok=True)
    from PIL import Image as PImage
    for img in bpy.data.images:
        src = bpy.path.abspath(img.filepath)
        if not img.filepath or not os.path.exists(src):
            continue
        name = os.path.splitext(os.path.basename(src))[0] + ".jpg"
        PImage.open(src).convert("RGB").save(os.path.join(tex, name), quality=88)
        img.filepath = "//textures/" + name
        img.reload()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path), compress=True, relative_remap=False)


def camera(sc, loc, target, lens=28):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    cam.clip_start = 0.5
    cam.clip_end = 20000
    ob = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(ob)
    ob.location = Vector(loc) * S
    d = Vector(target) * S - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = ob
    return ob


def load_shots():
    """Plans de camera : shots.json + un plan automatique par ile.

    Coordonnees en unites Source ; z relatif au niveau de la mer du niveau.
    "island": cle -> x, y relatifs au centre de l'ile.
    """
    with open(os.path.join(BUILD, "markers.json")) as fh:
        markers = json.load(fh)["markers"]
    isl = {m["group"]: m for m in markers if m["kind"] == "ile"}
    from_key = {}
    with open(os.path.join(HERE, "shots.json")) as fh:
        raw = json.load(fh)
    keys = raw.pop("_iles")
    for key, label in keys.items():
        from_key[key] = isl[label]
    shots = {}
    # plan automatique de chaque ile, vu depuis le large (cote centre du niveau)
    for key, m in from_key.items():
        cx, cy = m["pos"][:2]
        poly = m["poly"]
        R = max(math.hypot(x - cx, y - cy) for x, y in poly)
        d = math.hypot(cx, cy) or 1
        ux, uy = -cx / d, -cy / d
        loc = (cx + ux * R * 1.75 + uy * R * 0.55, cy + uy * R * 1.75 - ux * R * 0.55, R * 0.75)
        shots[key] = dict(level=m["level"], loc=loc, target=(cx, cy, 350), lens=24)
        # vues de controle rapprochees (revue des cotes) : 4 angles autour de l'ile
        a0 = math.atan2(uy, ux)
        for k in range(4):
            a = a0 + k * math.pi / 2
            loc = (cx + math.cos(a) * R * 1.12, cy + math.sin(a) * R * 1.12, R * 0.22)
            tgt = (cx + math.cos(a) * R * 0.35, cy + math.sin(a) * R * 0.35, 120)
            shots[f"{key}_revue{k + 1}"] = dict(level=m["level"], loc=loc, target=tgt, lens=22, revue=True)
    for name, v in raw.items():
        v = dict(v)
        if "island" in v:
            m = from_key[v["island"]]
            cx, cy = m["pos"][:2]
            v["loc"] = (cx + v["loc"][0], cy + v["loc"][1], v["loc"][2])
            v["target"] = (cx + v["target"][0], cy + v["target"][1], v["target"][2])
            v["level"] = m["level"]
        shots[name] = v
    return shots


def use_shot(sc, shot):
    lv = shot["level"]
    sz = LEVELS[lv]
    for c in bpy.data.collections:
        if c.name.startswith("Niveau "):
            c.hide_render = c.name != f"Niveau {lv}"
    loc = (shot["loc"][0], shot["loc"][1], shot["loc"][2] + sz)
    tgt = (shot["target"][0], shot["target"][1], shot["target"][2] + sz)
    return camera(sc, loc, tgt, shot.get("lens", 24))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--res", default="1600x900")
    ap.add_argument("--out", default=os.path.join(ROOT, "previews"))
    ap.add_argument("--blend", default="")
    ap.add_argument("--only-blend", action="store_true")
    a = ap.parse_args(argv)
    with open(os.path.join(BUILD, "preview.json")) as fh:
        data = json.load(fh)
    SHOTS = load_shots()
    sc = reset()
    build_geometry(data, os.path.join(BUILD, "png"))
    water(sc)
    sky_and_sun(sc)
    bubbles(data)
    w, h = (int(v) for v in a.res.split("x"))
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.cycles.samples = a.samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 6
    sc.cycles.volume_bounces = 0
    sc.cycles.transparent_max_bounces = 8
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.view_layers[0].cycles.denoising_store_passes = True
    sc.view_layers[0].use_pass_mist = True
    sc.world.mist_settings.start = 300
    sc.world.mist_settings.depth = 5500
    sc.world.mist_settings.falloff = "LINEAR"
    sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"
    sc.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    sc.render.image_settings.color_depth = "32"
    os.makedirs(a.out, exist_ok=True)
    if a.shots == "revue":
        names = [n for n in SHOTS if SHOTS[n].get("revue")]
    elif a.shots:
        names = a.shots.split(",")
    else:
        names = [n for n in SHOTS if not SHOTS[n].get("revue")]
    if a.blend:
        for n in SHOTS:
            if SHOTS[n].get("revue"):
                continue   # vues de controle : pas de camera dans la scene exportee
            ob = use_shot(sc, SHOTS[n])
            ob.name = "Camera_" + n
        use_shot(sc, SHOTS["niveau1"])
        for c in bpy.data.collections:
            c.hide_render = False
        export_blend(a.blend)
        if a.only_blend:
            return
    for n in names:
        use_shot(sc, SHOTS[n])
        exr = os.path.join(a.out, n + ".exr")
        sc.render.filepath = exr
        bpy.ops.render.render(write_still=True)
        denoise_to_png(sc, exr, os.path.join(a.out, n + ".png"))
        print("rendu", n, flush=True)


if __name__ == "__main__":
    main()
