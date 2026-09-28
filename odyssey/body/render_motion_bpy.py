#!/usr/bin/env python3
"""Motion previews of an animated body GLB with Blender (bpy module, Cycles CPU + OIDN): one clip per
call, rendered as a PNG sequence in a soft daylight studio, encoded to H.264, plus a contact sheet.

    python3 odyssey/body/render_motion_bpy.py odyssey/out/body/subject_animated.glb odyssey/out/body/previews \
        --clip walk_forward --name motion_walk --seconds 4 [--start 0] [--az 35] [--dist 6] [--track]
        [--res 960x540] [--samples 16] [--frames 0,12,24 (QA stills only)] [--sheet 8]

--az is the camera's azimuth around the character in his own frame, measured like a glTF yaw
(0 = in front of him, +90 = at his left, -90 = at his right, 180 = behind); the character is turned,
the camera, lights and backdrop stay put, and with --track the camera and lights follow the smoothed
root (walks).  Loop clips are played with wrap-around (--start may push the seam into the shot).
Clip actions are assigned to the armature and to the skin / outfit shape keys (the corrective
morph weights).  Frames go to <outdir>/<name>_frames/, the video to <outdir>/<name>.mp4, the sheet to
<outdir>/<name>_sheet.png (--frames-dir moves the frames elsewhere).
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_body_bpy as RB  # noqa: E402


def set_clip(name):
    act = bpy.data.actions[name]
    for o in bpy.data.objects:
        ad = None
        if o.type == "ARMATURE":
            ad = o.animation_data or o.animation_data_create()
            slot_id = "OB" + o.name
        elif o.type == "MESH" and o.data.shape_keys is not None:
            ad = o.data.shape_keys.animation_data or o.data.shape_keys.animation_data_create()
            slot_id = "KE" + o.name
        if ad is None:
            continue
        for tr in ad.nla_tracks:
            tr.mute = True
        ad.use_nla = False
        ad.action = act
        slot = next((s for s in act.slots if s.identifier == slot_id), None)
        if slot is not None:
            ad.action_slot = slot
        elif o.type == "MESH":
            ad.action = None
    fr = act.frame_range
    return int(round(fr[0])), int(round(fr[1]))


def floor_material(mat, base=(0.60, 0.58, 0.55)):
    """Very faint mottled concrete so the eye can read the ground moving under a tracking camera."""
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (base[0] * 0.93, base[1] * 0.93, base[2] * 0.92, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (base[0] * 1.04, base[1] * 1.04, base[2] * 1.04, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85


def studio(scene, lens=50):
    """Big warm off-white cyclorama (Blender Z up; the camera looks along +Y) with a soft wash on the
    back wall, a large soft key from camera-left, a low-power overhead for contact shadows, a cool
    fill and two rims.  Lights and camera hang under a rig empty that can follow the actor."""
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.66, 0.65, 0.64, 1)
    bg.inputs["Strength"].default_value = 0.12
    scene.world = world
    base = (0.70, 0.67, 0.63)
    cyc = RB.cyclorama(color=base, radius=3.0, depth=18.0, width=40.0, height=12.0, back_y=7.0)
    floor_material(cyc.data.materials[0], base)
    rig = bpy.data.objects.new("rig", None)
    scene.collection.objects.link(rig)
    lights = [RB.area_light("key", (-3.0, -3.6, 4.0), (0, 0, 1.1), 850, 2.4, (1.0, 0.94, 0.87), 1.8),
              RB.area_light("top", (0.3, 0.2, 4.6), (0, 0, 0), 320, 1.2, (1.0, 0.97, 0.94), 1.2),
              RB.area_light("fill", (4.0, -3.4, 1.6), (0, 0, 1.0), 150, 3.5, (0.90, 0.94, 1.0), 2.5),
              RB.area_light("rim_l", (-2.6, 2.6, 2.6), (0, 0, 1.3), 330, 1.0, (1.0, 0.95, 0.90), 2.2),
              RB.area_light("rim_r", (2.8, 2.4, 2.4), (0, 0, 1.2), 300, 1.0, (0.93, 0.96, 1.0), 2.2),
              RB.area_light("wash", (0.0, 3.0, 5.5), (0, 7.0, 1.6), 1100, 8.0, (1.0, 0.96, 0.9), 3.0)]
    for L in lights:
        L.parent = rig
        if L.name == "wash":
            L.visible_diffuse = True
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36.0
    cam = bpy.data.objects.new("cam", cd)
    scene.collection.objects.link(cam)
    cam.parent = rig
    scene.camera = cam
    return rig, cam


def vignette(path, strength=0.22):
    """Soft radial falloff towards the corners, applied in place to a rendered PNG."""
    from PIL import Image
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    h, w = im.shape[:2]
    y, x = np.mgrid[0:h, 0:w]
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    m = 1.0 - strength * np.clip((r - 0.35) / 0.65, 0, 1) ** 1.8
    Image.fromarray(np.clip(im * m[..., None] * 255 + 0.5, 0, 255).astype(np.uint8)).save(path)


def root_track(scene, arm, frames):
    """World position of the root bone head at each frame (Blender coords)."""
    pb = arm.pose.bones["root"]
    out = []
    for f in frames:
        scene.frame_set(int(f))
        out.append(tuple(arm.matrix_world @ pb.head))
    return np.array(out)


def gauss(x, sigma):
    if sigma <= 0 or len(x) < 3:
        return x
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    xp = np.pad(x, [(r, r)] + [(0, 0)] * (x.ndim - 1), mode="edge")
    return np.stack([np.convolve(xp[:, j], k, mode="valid") for j in range(x.shape[1])], 1)


def label_sheet(paths, times, out, cols=None, title=None, scale=0.5):
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = int(ims[0].width * scale), int(ims[0].height * scale)
    n = len(ims)
    cols = cols or min(n, 4)
    rows = (n + cols - 1) // cols
    top = 34 if title else 0
    sheet = Image.new("RGB", (cols * w, rows * h + top), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = tfont = ImageFont.load_default()
    if title:
        d.text((10, 7), title, fill=(235, 235, 235), font=tfont)
    for i, (im, t) in enumerate(zip(ims, times)):
        x, y = (i % cols) * w, top + (i // cols) * h
        sheet.paste(im.resize((w, h), Image.LANCZOS), (x, y))
        d.text((x + 8, y + 6), t, fill=(30, 30, 30), font=font)
    sheet.save(out)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("outdir")
    ap.add_argument("--clip", required=True)
    ap.add_argument("--name", default=None)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--start", type=float, default=0.0, help="clip time of the first frame (s)")
    ap.add_argument("--loop", action="store_true", help="wrap around the clip end (loop clips)")
    ap.add_argument("--az", type=float, default=25.0)
    ap.add_argument("--dist", type=float, default=6.0)
    ap.add_argument("--cam-h", type=float, default=1.15)
    ap.add_argument("--look-h", type=float, default=0.92)
    ap.add_argument("--lens", type=float, default=50.0)
    ap.add_argument("--track", action="store_true", help="camera + lights follow the smoothed root")
    ap.add_argument("--push", type=float, default=0.0, help="slow dolly-in over the shot (metres)")
    ap.add_argument("--res", default="960x540")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--frames", default=None, help="comma list of output frame indices (QA stills only)")
    ap.add_argument("--sheet", type=int, default=8, help="frames in the contact sheet")
    ap.add_argument("--exposure", type=float, default=-0.45)
    ap.add_argument("--look", default="AgX - Punchy")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--frames-dir", default=None, help="where the PNG frames go (default <outdir>/<name>_frames)")
    a = ap.parse_args(argv)
    name = a.name or f"motion_{a.clip}"
    out = Path(a.outdir)
    fdir = Path(a.frames_dir) if a.frames_dir else out / f"{name}_frames"
    fdir.mkdir(parents=True, exist_ok=True)
    RB.reset()
    scene = bpy.context.scene
    scene.render.fps = int(a.fps)
    top, arm, meshes = RB.import_glb(a.glb, action=None)
    RB.tune_materials(meshes)
    f0, f1 = set_clip(a.clip)
    loop_len = f1 - f0 if a.loop else None          # loop clips end on a copy of their first frame
    n_out = int(round(a.seconds * a.fps))
    src = []
    for i in range(n_out):
        f = f0 + int(round(a.start * a.fps)) + i
        if loop_len:
            f = f0 + (f - f0) % loop_len
        src.append(min(f, f1))
    top.rotation_mode = "XYZ"
    top.rotation_euler = Euler((top.rotation_euler.x, top.rotation_euler.y, math.radians(-a.az)))
    bpy.context.view_layer.update()
    rig, cam = studio(scene, a.lens)
    RB.cycles(scene, a.samples)
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = a.look
    except TypeError:
        scene.view_settings.look = "None"
    scene.view_settings.exposure = a.exposure
    W, H = (int(x) for x in a.res.split("x"))
    scene.render.resolution_x, scene.render.resolution_y = W, H
    # camera path: fixed, or following the smoothed root (unwrapped: loop wrap would jump)
    rt = root_track(scene, arm, src)
    if a.track:
        # continuous track even across loop wraps: integrate the per-frame motion, skipping wrap jumps
        d = np.diff(rt, axis=0)
        jump = np.linalg.norm(d[:, :2], axis=1) > 0.3
        d[jump] = np.median(d[~jump], axis=0) if (~jump).any() else 0
        cont = np.vstack([rt[:1], rt[:1] + np.cumsum(d, 0)])
        # if the clip wraps, move the character with the integrated root instead (see top offset below)
        base = gauss(cont, 10.0)
        base[:, 2] = 0
    else:
        base = np.zeros((n_out, 3))
        base[:, :2] = rt[:, :2].mean(0)
    info = {"clip": a.clip, "frames": [int(x) for x in src], "az": a.az, "track": a.track, "renders": []}
    frames_to_do = range(n_out) if a.frames is None else [int(x) for x in a.frames.split(",")]
    paths = {}
    t_start = time.time()
    for i in frames_to_do:
        scene.frame_set(src[i])
        # loop wrap under a tracking camera: shift the whole character by the integrated offset
        if a.track:
            off = cont[i] - rt[i]
            off[2] = 0
            top.location = Vector((off[0], off[1], 0.0))
        push = a.push * (i / max(1, n_out - 1))
        rig.location = Vector((base[i][0], base[i][1], 0))
        cam.location = Vector((0.0, -(a.dist - push), a.cam_h))
        tgt = Vector((0.0, 0.0, a.look_h))
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        p = fdir / f"f{i:04d}.png"
        t = RB.render(scene, p)
        vignette(p)
        paths[i] = p
        info["renders"].append(round(t, 1))
        print(f"{name} frame {i + 1}/{n_out} (clip frame {src[i]}): {t:.1f}s", flush=True)
    info["seconds_total"] = round(time.time() - t_start, 1)
    if a.frames is None and not a.no_video:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        mp4 = out / f"{name}.mp4"
        # a little temporal luma noise dithers the backdrop gradient (8-bit H.264 bands it otherwise)
        subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", str(fdir / "f%04d.png"),
                        "-vf", "noise=c0s=4:c0f=t+u", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "15",
                        "-preset", "slow", "-tune", "film", "-movflags", "+faststart", str(mp4)], check=True)
        info["mp4"] = str(mp4)
    done = sorted(paths)
    if len(done) > 1:
        k = min(a.sheet, len(done))
        pick = [done[int(round(j * (len(done) - 1) / (k - 1)))] for j in range(k)]
        sheet = label_sheet([paths[i] for i in pick], [f"t = {i / a.fps:.2f} s" for i in pick],
                            out / f"{name}_sheet.png", cols=4,
                            title=f"{name}: clip '{a.clip}', {len(done)} frames @ {a.fps:g} fps")
        info["sheet"] = str(sheet)
    (out / f"{name}_info.json").write_text(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
