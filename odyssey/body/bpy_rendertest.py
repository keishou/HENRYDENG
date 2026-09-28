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
    ap.add_argument("--out", required=True, help="png path; with --frames N, '#' is replaced by the frame index")
    ap.add_argument("--frames", type=int, default=1, help="render N frames in one process (camera orbits a little)")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--no-sss", action="store_true")
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.01, help="Cycles adaptive noise threshold")
    ap.add_argument("--persistent", action="store_true", help="Cycles persistent data between frames")
    a = ap.parse_args(argv)

    t0 = time.time()
    scene = build_scene()
    t_build = time.time() - t0
    if a.engine == "CYCLES":
        settings = setup_cycles(scene, a.samples, a.threads)
    else:
        settings = setup_eevee(scene, a.samples)
    rx, ry = (int(v) for v in a.res.split("x"))
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    if a.no_sss:
        bpy.data.materials["clay"].node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.0
    if a.engine == "CYCLES":
        scene.cycles.use_denoising = not a.no_denoise
        scene.cycles.adaptive_threshold = a.threshold
        scene.render.use_persistent_data = a.persistent
        settings["denoise"] = scene.cycles.use_denoising
        settings["adaptive_threshold"] = round(scene.cycles.adaptive_threshold, 4)
        settings["persistent_data"] = scene.render.use_persistent_data
    settings["res"] = f"{rx}x{ry}"
    settings["sss"] = not a.no_sss
    settings["view_transform"] = scene.view_settings.view_transform
    settings["look"] = scene.view_settings.look
    settings["engine"] = scene.render.engine
    import resource

    marks = []  # (t, stats) on phase changes, to split sync / sampling / denoise
    last = {"phase": None}

    def on_stats(stats):
        # stats look like "Fra:1 | Mem:.. | Sample 12/32" / "Denoising" / "Updating ..."
        s = str(stats)
        ph = s.split("|")[-1].strip()
        import re

        key = re.sub(r"[0-9.:]+", "", ph)
        if key != last["phase"]:
            last["phase"] = key
            marks.append((round(time.time() - t1, 2), ph[:80]))

    bpy.app.handlers.render_stats.append(on_stats)
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    la0 = os.getloadavg()[0]
    cam = scene.camera
    per_frame = []
    t_start = time.time()
    for f in range(a.frames):
        if f:
            # small orbit so every frame differs (like an animation)
            cam.location.x += 0.05
            look_at(cam, (0, 0, 0.72))
        scene.render.filepath = a.out.replace("#", f"{f:03d}")
        t1 = time.time()
        rf0 = resource.getrusage(resource.RUSAGE_SELF)
        bpy.ops.render.render(write_still=True)
        rf1 = resource.getrusage(resource.RUSAGE_SELF)
        per_frame.append({"wall_s": round(time.time() - t1, 2),
                          "cpu_s": round((rf1.ru_utime - rf0.ru_utime) + (rf1.ru_stime - rf0.ru_stime), 1)})
    t_render = time.time() - t_start
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    cpu_s = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    res = {
        "bpy": bpy.app.version_string,
        "build_hash": bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
        "settings": settings,
        "scene_build_s": round(t_build, 2),
        "render_s": round(t_render, 2),
        "cpu_s": round(cpu_s, 1),
        "effective_cores": round(cpu_s / max(t_render, 1e-6), 2),
        "loadavg_before": round(la0, 2),
        "loadavg_after": round(os.getloadavg()[0], 2),
        "per_frame": per_frame,
        "phases": [m for m in marks if any(k in m[1] for k in ("Sample", "Rendering", "enois", "Finished", "Time:", "Compiling", "Building BVH", "Importance"))][:60],
        "out": a.out,
    }
    print("RESULT " + json.dumps(res))


if __name__ == "__main__":
    main()
