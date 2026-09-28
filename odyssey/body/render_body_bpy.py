#!/usr/bin/env python3
"""Studio turntable stills of a body GLB with Blender (bpy module, Cycles CPU + OIDN).

    python3 odyssey/body/render_body_bpy.py odyssey/out/body/body_base.glb odyssey/out/body/previews \
        [--samples 32] [--res 1080x1920] [--views front,three_quarter,side,back] [--closeups] [--action stand]

Imports the GLB exactly as exported (skinned, textured; the armature is posed by the GLB's "stand" clip),
builds a soft cyclorama studio (big key softbox, fill, two rims), and renders one PNG per view by turning
the character (camera and lights fixed), plus a contact sheet.  --closeups adds torso / hands / feet crops.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy  # noqa: E402
import numpy as np
from mathutils import Euler, Vector

VIEWS = {"front": 0.0, "three_quarter": -35.0, "side": -90.0, "back": 180.0, "three_quarter_back": 145.0}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_glb(path, action="stand"):
    bpy.ops.import_scene.gltf(filepath=str(path), bone_heuristic="BLENDER", guess_original_bind_pose=True)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)]
    for o in bpy.data.objects:  # importer helpers (e.g. the bone-shape Icosphere) stay out of the render
        if o.type == "MESH" and o not in meshes:
            o.hide_render = True
            o.hide_viewport = True
    # the character's top-level object (glTF root node "body_base")
    top = arm
    while top.parent is not None:
        top = top.parent
    if action:
        act = bpy.data.actions.get(action) or next((a for a in bpy.data.actions if a.name.startswith(action)), None)
        if act is not None:
            arm.animation_data_create()
            arm.animation_data.action = act
            try:
                if not arm.animation_data.action_slot and len(act.slots):
                    arm.animation_data.action_slot = act.slots[0]
            except AttributeError:
                pass
    bpy.context.scene.frame_set(0)
    return top, arm, meshes


def tune_materials(meshes):
    for o in meshes:
        for slot in o.material_slots:
            m = slot.material
            if m is None or not m.node_tree:
                continue
            bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf is None:
                continue
            name = m.name.lower()
            if name.startswith("skin"):
                bsdf.inputs["Subsurface Weight"].default_value = 0.25
                bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.25)
                bsdf.inputs["Subsurface Scale"].default_value = 0.006
                bsdf.inputs["Coat Weight"].default_value = 0.0
                bsdf.inputs["Specular IOR Level"].default_value = 0.45
            elif name.startswith("outfit"):
                # knit: soft sheen already comes from KHR_materials_sheen; make sure it is on
                if bsdf.inputs["Sheen Weight"].default_value < 0.05:
                    bsdf.inputs["Sheen Weight"].default_value = 0.35
                    bsdf.inputs["Sheen Roughness"].default_value = 0.45
                bsdf.inputs["Specular IOR Level"].default_value = 0.35
            elif name.startswith("eyes"):
                # a wet cornea, but a small soft catchlight (a big glassy one reads as a doll's eye)
                bsdf.inputs["Coat Weight"].default_value = 0.18
                bsdf.inputs["Coat Roughness"].default_value = 0.06
                # the eyeball's own (rough) specular lays a grey veil over the dark iris under big
                # softboxes; the coat alone gives the wet catchlight
                bsdf.inputs["Specular IOR Level"].default_value = 0.15
            elif name.startswith(("eyebrows", "eyelashes", "hair")):
                m.surface_render_method = "DITHERED" if hasattr(m, "surface_render_method") else None
                if name.startswith("hair"):
                    bsdf.inputs["Coat Weight"].default_value = 0.0
                    bsdf.inputs["Sheen Weight"].default_value = 0.1
                    bsdf.inputs["Sheen Roughness"].default_value = 0.5
                    bsdf.inputs["Specular IOR Level"].default_value = min(bsdf.inputs["Specular IOR Level"].default_value, 0.3)


def cyclorama(color=(0.62, 0.60, 0.57), radius=1.2, depth=6.0, width=14.0, height=6.0, back_y=2.2):
    """Floor + curved sweep + back wall (Blender Z up; the character stands at the origin facing -Y)."""
    import bmesh
    prof = []
    for i in range(24):  # floor from the front to the start of the curve
        prof.append((-depth + (depth + back_y - radius) * i / 23, 0.0))
    for i in range(1, 17):
        a = -math.pi / 2 + (math.pi / 2) * i / 16
        prof.append((back_y - radius + radius * math.cos(a) , radius + radius * math.sin(a)))
    for i in range(1, 9):
        prof.append((back_y, radius + (height - radius) * i / 8))
    bm = bmesh.new()
    rows = []
    for xi in (-width / 2, width / 2):
        rows.append([bm.verts.new((xi, y, z)) for (y, z) in prof])
    for j in range(len(prof) - 1):
        bm.faces.new((rows[0][j], rows[1][j], rows[1][j + 1], rows[0][j + 1]))
    me = bpy.data.meshes.new("cyc")
    bm.to_mesh(me)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cyclorama", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("cyc")
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.9
    me.materials.append(mat)
    return ob


def area_light(name, loc, target, power, size, color=(1, 1, 1), size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.color = color
    ld.shape = "RECTANGLE" if size_y else "DISK"
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def studio(scene, cam_dist=5.2, cam_h=1.02, look_h=0.92, lens=85, res=(1080, 1920)):
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.56, 0.58, 1)
    bg.inputs["Strength"].default_value = 0.08
    scene.world = world
    cyclorama()
    # key: big soft box front-left, above eye level (warm)
    area_light("key", (-2.6, -3.2, 3.0), (0, 0, 1.2), 420, 2.2, (1.0, 0.95, 0.9), 1.6)
    # fill: front-right, low, cool, very soft
    area_light("fill", (3.2, -2.8, 1.3), (0, 0, 1.0), 150, 3.0, (0.95, 0.97, 1.0), 2.0)
    # rims: behind left / right to separate the black knit from the backdrop
    area_light("rim_l", (-2.2, 2.0, 2.4), (0, 0, 1.3), 260, 0.8, (1.0, 0.97, 0.94), 2.0)
    area_light("rim_r", (2.3, 1.8, 2.2), (0, 0, 1.2), 230, 0.8, (0.95, 0.97, 1.0), 2.0)
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_fit = "AUTO"
    cam = bpy.data.objects.new("cam", cd)
    scene.collection.objects.link(cam)
    cam.location = (0.0, -cam_dist, cam_h)
    d = Vector((0, 0, look_h)) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    return cam


def cycles(scene, samples=32, threads=4):
    scene.render.engine = "CYCLES"
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    try:
        c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        c.denoising_prefilter = "ACCURATE"
    except Exception:
        pass
    c.max_bounces = 8
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transparent_max_bounces = 16
    c.use_light_tree = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False


def render(scene, path):
    scene.render.filepath = str(path)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


def gl2bl(p):
    """glTF (Y up, +Z forward) -> Blender (Z up, -Y forward)."""
    return Vector((p[0], -p[2], p[1]))


def portraits(scene, cam, top, a, out, info):
    """Face close-ups orbiting the head, and an orthographic front render framed exactly like the photo
    (eye centre and eye-chin distance), saved side by side with the photo."""
    from PIL import Image
    pj = json.loads(Path(a.portrait).read_text())["portrait"]
    eye = gl2bl(pj["eye_center_m"])
    chin = gl2bl(pj["chin_m"])
    top.rotation_euler = Euler((top.rotation_euler.x, top.rotation_euler.y, 0.0))
    head_c = eye + Vector((0, 0.035, 0.02))
    # turn the character about a vertical axis through the head (camera, lights and backdrop stay put)
    pivot = bpy.data.objects.new("head_pivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location = head_c
    bpy.context.view_layer.update()
    mw = top.matrix_world.copy()
    top.parent = pivot
    top.matrix_world = mw
    cam.data.type = "PERSP"
    cam.data.lens = 85
    scene.render.resolution_x, scene.render.resolution_y = 1200, 1500
    # portrait fill: a big soft source just above the camera (key : fill about 2 : 1 on the face), so the
    # lower face does not read lumpy from one-sided shading; small and diffuse in the eyes
    area_light("face_fill", tuple(head_c + Vector((0.15, -1.6, 0.35))), tuple(head_c), 60, 1.2, (1.0, 0.97, 0.94), 0.9)
    cam.location = head_c + Vector((0, -0.95, 0.03))
    cam.rotation_euler = (head_c + Vector((0, 0, -0.02)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    shots = () if a.photo_framing_only else (("front", 0), ("34", -35), ("side", -90), ("back", 180), ("34_left", 35))
    for name, yaw in shots:
        pivot.rotation_euler = Euler((0, 0, math.radians(yaw)))
        p = out / f"{a.prefix}closeup_face_{name}.png"
        dt = render(scene, p)
        info["renders"][f"closeup_face_{name}"] = {"path": str(p), "seconds": round(dt, 1)}
        print(f"closeup_face_{name}: {dt:.1f}s", flush=True)
    pivot.rotation_euler = Euler((0, 0, 0))
    # photo framing: orthographic, eye centre and chin at the photo's pixel positions
    W, H = pj["photo_size_px"]
    ex, ey = pj["photo_eye_center_px"]
    cx, cy = pj["photo_chin_px"]
    m_per_px = (eye.z - chin.z) / (cy - ey)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = m_per_px * max(W, H)
    scene.render.resolution_x, scene.render.resolution_y = W, H
    centre = Vector((eye.x - (ex - W / 2) * m_per_px, eye.y - 3.0, eye.z + (ey - H / 2) * m_per_px))
    cam.location = centre
    cam.rotation_euler = Euler((math.radians(90), 0, 0))
    p = out / f"{a.prefix}face_photo_framing.png"
    dt = render(scene, p)
    info["renders"]["face_photo_framing"] = {"path": str(p), "seconds": round(dt, 1)}
    if a.photo:
        ph = Image.open(a.photo).convert("RGB").resize((W, H))
        rd = Image.open(p).convert("RGB")
        sheet = Image.new("RGB", (2 * W, H))
        sheet.paste(rd, (0, 0))
        sheet.paste(ph, (W, 0))
        sheet.save(out / f"{a.prefix}face_vs_photo.png")
    cam.data.type = "PERSP"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("outdir")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--res", default="1080x1920")
    ap.add_argument("--views", default="front,three_quarter,side,back")
    ap.add_argument("--closeups", action="store_true")
    ap.add_argument("--closeups-only", action="store_true")
    ap.add_argument("--action", default="stand")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--portrait", default=None,
                    help="graft_info.json (graft_face.py): adds face close-ups and a photo-framed comparison")
    ap.add_argument("--photo", default=None, help="photo to put next to the photo-framed render")
    ap.add_argument("--portrait-only", action="store_true")
    ap.add_argument("--exposure", type=float, default=-0.45)
    ap.add_argument("--view", default="AgX", help="view transform (AgX, Standard, Filmic, ...)")
    ap.add_argument("--look", default="AgX - Punchy")
    ap.add_argument("--photo-framing-only", action="store_true")
    ap.add_argument("--hide", default="", help="comma-separated mesh names to hide (e.g. outfit,hair)")
    a = ap.parse_args(argv)
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    res = tuple(int(x) for x in a.res.split("x"))
    reset()
    scene = bpy.context.scene
    top, arm, meshes = import_glb(a.glb, a.action)
    tune_materials(meshes)
    for o in meshes:
        if any(o.name.startswith(h) for h in a.hide.split(",") if h):
            o.hide_render = True
    cam = studio(scene, res=res)
    cycles(scene, a.samples)
    scene.view_settings.exposure = a.exposure
    scene.view_settings.view_transform = a.view
    try:
        scene.view_settings.look = a.look
    except TypeError:
        scene.view_settings.look = "None"
    # measure the posed character (evaluated meshes)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        e = o.evaluated_get(dg)
        me = e.to_mesh()
        mw = e.matrix_world
        pts.extend([(mw @ v.co)[:] for v in me.vertices])
        e.to_mesh_clear()
    pts = np.array(pts)
    info = {"posed_bbox_blender_zup": [pts.min(0).round(3).tolist(), pts.max(0).round(3).tolist()],
            "objects": [o.name for o in meshes], "armature": arm.name,
            "actions": [x.name for x in bpy.data.actions], "renders": {}}
    print("posed bbox", info["posed_bbox_blender_zup"], flush=True)
    rendered = []
    if not (a.closeups_only or a.portrait_only):
        for v in a.views.split(","):
            top.rotation_mode = "XYZ"
            top.rotation_euler = Euler((top.rotation_euler.x, top.rotation_euler.y, math.radians(VIEWS[v])))
            p = out / f"{a.prefix}{v}.png"
            dt = render(scene, p)
            info["renders"][v] = {"path": str(p), "seconds": round(dt, 1)}
            rendered.append(p)
            print(f"{v}: {dt:.1f}s", flush=True)
    if a.closeups or a.closeups_only:
        top.rotation_euler = Euler((top.rotation_euler.x, top.rotation_euler.y, math.radians(-20)))
        shots = {"closeup_torso": ((0.0, -1.7, 1.45), (0.0, 0, 1.36), 85, (1200, 1200)),
                 "closeup_hands": ((0.0, -1.9, 1.0), (0.0, 0, 0.86), 60, (1400, 1000)),
                 "closeup_feet": ((0.35, -1.7, 0.4), (0.0, 0, 0.1), 60, (1200, 900))}
        for k, (loc, tgt, lens, r) in shots.items():
            cam.location = loc
            cam.data.lens = lens
            cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.render.resolution_x, scene.render.resolution_y = r
            p = out / f"{a.prefix}{k}.png"
            dt = render(scene, p)
            info["renders"][k] = {"path": str(p), "seconds": round(dt, 1)}
            print(f"{k}: {dt:.1f}s", flush=True)
    if a.portrait:
        portraits(scene, cam, top, a, out, info)
    if len(rendered) > 1:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in rendered]
        h = 1200
        ims = [im.resize((round(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
        sheet = Image.new("RGB", (sum(im.width for im in ims), h))
        x = 0
        for im in ims:
            sheet.paste(im, (x, 0))
            x += im.width
        sp = out / f"{a.prefix}turntable_sheet.png"
        sheet.save(sp)
        info["sheet"] = str(sp)
    (out / f"{a.prefix}render_info.json").write_text(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
