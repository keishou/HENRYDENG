"""Blender-as-a-module (pip `bpy`) renderer benchmark.

Builds a tiny look-dev scene (subdivided Suzanne + sphere on a ground plane,
soft area key + sun + physical sky, 85 mm camera with shallow depth of field,
AgX view transform) and renders one 1920x1080 frame.

usage:
  python3 bpy_rendertest.py --engine CYCLES --samples 64 --out /path/frame.png
  python3 bpy_rendertest.py --engine EEVEE  --samples 64 --out /path/frame.png

Prints a single line `RESULT {json}` with the timings.
"""
import argparse
import json
import math
import os
import sys
import time

import bpy


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # --- ground plane: large, slightly rough warm-grey -----------------------
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.object
    gmat = bpy.data.materials.new("ground")
    gmat.use_nodes = True
    b = gmat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.32, 0.30, 0.28, 1)
    b.inputs["Roughness"].default_value = 0.65
    ground.data.materials.append(gmat)

    # --- Suzanne, subdivided + smooth, clay/skin-ish material with SSS -------
    bpy.ops.mesh.primitive_monkey_add(size=1.0, location=(0, 0, 0.72), rotation=(math.radians(-8), 0, math.radians(18)))
    suz = bpy.context.object
    mod = suz.modifiers.new("subsurf", "SUBSURF")
    mod.levels = 2
    mod.render_levels = 2
    bpy.ops.object.shade_smooth()
    smat = bpy.data.materials.new("clay")
    smat.use_nodes = True
    b = smat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.80, 0.55, 0.45, 1)
    b.inputs["Roughness"].default_value = 0.45
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.05
    suz.data.materials.append(smat)

    # --- a glossy sphere behind, to show DOF + reflections -------------------
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, segments=64, ring_count=32, location=(1.3, 1.6, 0.45))
    sph = bpy.context.object
    bpy.ops.object.shade_smooth()
    pmat = bpy.data.materials.new("glossy")
    pmat.use_nodes = True
    b = pmat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.05, 0.12, 0.25, 1)
    b.inputs["Roughness"].default_value = 0.12
    b.inputs["Coat Weight"].default_value = 0.6
    sph.data.materials.append(pmat)

    # a small sphere in the foreground (out of focus)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, segments=48, ring_count=24, location=(-0.9, -1.4, 0.18))
    fg = bpy.context.object
    bpy.ops.object.shade_smooth()
    fg.data.materials.append(pmat)

    # --- lights ---------------------------------------------------------------
    # large soft area key, camera-left, warm
    bpy.ops.object.light_add(type="AREA", location=(-2.6, -2.2, 2.8))
    key = bpy.context.object
    key.data.shape = "DISK"
    key.data.size = 2.5
    key.data.energy = 600
    key.data.color = (1.0, 0.86, 0.72)
    look_at(key, (0, 0, 0.7))
    # low-energy cool rim / sun from behind-right, soft angle
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 5))
    sun = bpy.context.object
    sun.data.energy = 2.0
    sun.data.angle = math.radians(6)
    sun.data.color = (0.85, 0.9, 1.0)
    sun.rotation_euler = (math.radians(55), 0, math.radians(150))

    # --- world: physical sky, dimmed so the area light is the key ------------
    world = bpy.data.worlds.new("sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(12)
    sky.sun_rotation = math.radians(210)
    sky.sun_disc = False
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.12

    # --- camera: 85 mm, f/1.8, focus on Suzanne ------------------------------
    bpy.ops.object.camera_add(location=(0.9, -5.2, 1.25))
    cam = bpy.context.object
    look_at(cam, (0, 0, 0.72))
    cam.data.lens = 85
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = suz
    cam.data.dof.aperture_fstop = 1.8
    scene.camera = cam

    # --- output / colour management ----------------------------------------
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    r.image_settings.file_format = "PNG"
    r.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Base Contrast"
    scene.view_settings.exposure = 0.0
    return scene


def look_at(obj, target):
    from mathutils import Vector

    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup_cycles(scene, samples, threads):
    scene.render.engine = "CYCLES"
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.01
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "ACCURATE"
    c.max_bounces = 8
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 8
    c.use_light_tree = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = threads
    return {
        "device": c.device,
        "samples": c.samples,
        "adaptive": c.use_adaptive_sampling,
        "adaptive_threshold": c.adaptive_threshold,
        "denoiser": c.denoiser,
        "denoise_passes": c.denoising_input_passes,
        "prefilter": c.denoising_prefilter,
        "max_bounces": c.max_bounces,
        "threads": scene.render.threads,
    }


def setup_eevee(scene, samples):
    eng = "BLENDER_EEVEE"
    scene.render.engine = eng
    e = scene.eevee
    e.taa_render_samples = samples
    info = {"engine_id": eng, "taa_render_samples": samples}
    for attr, val in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2), ("use_volumetric_shadows", False)):
        if hasattr(e, attr):
            try:
                setattr(e, attr, val)
                info[attr] = val
            except Exception as ex:  # noqa: BLE001
                info[attr] = f"error: {ex}"
    return info


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="CYCLES", choices=["CYCLES", "EEVEE"])
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    t0 = time.time()
    scene = build_scene()
    t_build = time.time() - t0
    if a.engine == "CYCLES":
        settings = setup_cycles(scene, a.samples, a.threads)
    else:
        settings = setup_eevee(scene, a.samples)
    settings["view_transform"] = scene.view_settings.view_transform
    settings["look"] = scene.view_settings.look
    settings["engine"] = scene.render.engine
    scene.render.filepath = a.out
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    t_render = time.time() - t1
    res = {
        "bpy": bpy.app.version_string,
        "build_hash": bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
        "settings": settings,
        "scene_build_s": round(t_build, 2),
        "render_s": round(t_render, 2),
        "out": a.out,
        "exists": os.path.exists(a.out),
    }
    print("RESULT " + json.dumps(res))


if __name__ == "__main__":
    main()
