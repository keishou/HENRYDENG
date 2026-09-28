"""Curated CMU clips for the film + batch retarget to the MakeHuman default skeleton.

    python3 -m body.curate_motion          # writes .cache/motion/curated/*.npz + MANIFEST.json

Sources (all downloaded by raw URL into odyssey/.cache/motion/, gitignored):
  CMU Graphics Lab Motion Capture Database, 2010 "MotionBuilder-friendly" BVH
  conversion by Bruce Hahne (cgspeed), mirrored at github.com/una-dinosauria/cmu-mocap
  (raw: https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/SSS/SS_TT.bvh).
  License: free for research and commercial use, no restrictions (CMU + B. Hahne,
  READMEFIRST.txt).  Requested acknowledgement: "The data used in this project was
  obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217."
  MakeHuman default rig / weights / base mesh: MPFB2 (github.com/makehumancommunity/mpfb2), CC0.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body.retarget_mh import retarget, save_npz  # noqa: E402
from body.check_retarget_mesh import load_body, skin  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOTION = os.path.join(ROOT, ".cache", "motion")

# name, clip, category, suggested [start, end] seconds (after the T-pose frame), note
CURATED = [
    ("walk_slow_deliberate", "132_45", "slow contemplative walk / walk toward camera", [1.5, 11.5],
     "very slow, even, straight 4.5 m walk (~0.5 m/s steady); cleanest walk in the set"),
    ("walk_sad_headdown", "142_15", "slow contemplative walk / walk toward camera", [2.1, 11.8],
     "'Sad' stylized walk, head lowered; 4 straight ~4.5 m passes with 180-deg turns (others: 13.8-23.2, 25.2-34.2, 35.1-43.0 s)"),
    ("walk_relaxed", "142_13", "slow contemplative walk / walk toward camera", [1.5, 9.0],
     "'Relaxed' walk, neutral head; 4 straight passes (others: 11.2-19.0, 21.0-28.8, 31.3-39.1 s)"),
    ("walk_slow_stop_lookright", "104_35", "slow walk, starts and stops", [0.0, 8.9],
     "stand -> slow walk 4 m -> stop -> head turns ~45 deg right"),
    ("walk_slowdown_lookup", "82_14", "walk -> stop -> look up", [0.0, 7.5],
     "walks in, decelerates, stops and tilts the head up (~+25-30 deg) from ~4.5 s"),
    ("walk_depressed", "91_14", "slow contemplative walk", [2.6, 9.7],
     "'DepressedWalk', head low; back-and-forth with in-place 180 turns"),
    ("idle_standing", "77_02", "standing idle", [0.0, 7.8],
     "quiet standing, small weight shifts and head moves"),
    ("idle_wait", "137_28", "standing idle", [0.0, 31.0],
     "'Normal Wait': long idle with weight shifts, a few steps and glances"),
    ("idle_wait_bus_lookback", "40_10", "standing idle / look back over shoulder", [0.0, 51.8],
     "52 s waiting at a bus stop: shifts, steps, turns body (hips +-90 deg from start) and head (+-75 deg rel. hips) to look around"),
    ("turn_lookback", "76_10", "turn to look back over the shoulder", [0.0, 11.4],
     "stands and twists torso+head to look behind to both sides (hip +-70, head +-50 deg)"),
    ("sit_ground", "82_05", "sitting on the ground", [0.0, 18.7],
     "seated on the floor the whole clip, knees up, hands on knees / behind; looks around"),
    ("kneel_one_knee", "23_03", "kneeling", [0.0, 6.8],
     "steps in, goes down on one knee (hip low 1.5-4.1 s), stands up again"),
    ("sit_face_in_hands", "22_03", "sitting (on a stool) with face in hands", [0.0, 6.8],
     "needs a seat prop (hip ~0.7 m above feet); strong emotional pose"),
    ("turn_in_place_ccw", "69_16", "slow turn in place", [0.0, 9.4],
     "4 x ~90 deg step-turns = 360 deg over ~7 s"),
    ("turn_in_place_cw", "69_18", "slow turn in place", [0.0, 8.8],
     "opposite direction, 360 deg"),
]

RIG = os.path.join(MOTION, "makehuman", "mpfb2_rig.default.json")


def load_weights(path, n_body=13380):
    W, acc = {}, np.zeros(n_body)
    for b, lst in json.load(open(path))["weights"].items():
        arr = np.array(lst)
        if arr.ndim != 2:
            continue
        m = arr[:, 0] < n_body  # body vertices only (skip helper geometry)
        W[b] = (arr[m, 0].astype(int), arr[m, 1])
        np.add.at(acc, W[b][0], W[b][1])
    return {b: (i, w / np.maximum(acc[i], 1e-9)) for b, (i, w) in W.items()}


def floor_stats(r, V, W, step=6):
    """per-frame lowest body vertex (MakeHuman base mesh, no shoes) -> stats in metres."""
    mins = np.array([skin(V, W, r, f)[:, 1].min() for f in range(0, len(r["src_frames"]), step)])
    return dict(min=round(float(mins.min()), 3), median=round(float(np.median(mins)), 3), max=round(float(mins.max()), 3))


def main(fps=24.0):
    mh = os.path.join(MOTION, "makehuman")
    V, _ = load_body(os.path.join(mh, "mpfb2_base.obj"))
    V = V[:13380]
    W = load_weights(os.path.join(mh, "mpfb2_weights.default.json"))
    out_dir = os.path.join(MOTION, "curated")
    os.makedirs(out_dir, exist_ok=True)
    summary = json.load(open(os.path.join(MOTION, "sheets", "summary.json")))
    titles = json.load(open(os.path.join(MOTION, "cmu", "titles.json")))
    man = dict(
        fps=fps,
        coordinate_system="Y up, metres, floor at y=0; calibration pose faces +Z; bone frames = Blender convention (+Y along bone) converted (x,y,z)->(x,z,-y)",
        floor_note="base_mesh_lowest_vertex_y_m = per-frame lowest vertex of the naked MakeHuman base mesh skinned with this motion; every clip has ground contact in every frame, so subtract its median from root_pos/head_pos y for exact contact (add shoe sole thickness)",
        skeleton="MakeHuman default (163 bones), rest from MPFB2 rig.default.json (CC0)",
        npz_fields={
            "bones": "bone names (topological order)", "parents": "parent index (-1 root)",
            "root_pos": "(F,3) root bone head position", "head_pos": "(F,B,3) bone head positions",
            "local_quat": "(F,B,4) xyzw rotation of each bone frame relative to its parent bone frame",
            "world_quat": "(F,B,4) xyzw world orientation of each bone frame",
            "rest_local_quat": "(B,4) same as local_quat for the MakeHuman rest pose",
            "rest_head/rest_tail": "(B,3) rest bone head/tail (Y-up metres)",
        },
        source_license="CMU mocap: free for any use (mocap.cs.cmu.edu; cgspeed BVH by B. Hahne, no added restrictions)",
        acknowledgement="The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217.",
        clips=[],
    )
    for name, cid, cat, seg, note in CURATED:
        bvh = os.path.join(MOTION, "cmu", cid + ".bvh")
        r = retarget(RIG, bvh, fps)
        out = os.path.join(out_dir, f"{name}.npz")
        save_npz(r, out)
        s = summary.get(cid, {})
        man["clips"].append(dict(
            name=name, cmu_id=cid, cmu_title=titles.get(cid), category=cat, suggested_segment_s=seg, note=note,
            source_bvh=os.path.relpath(bvh, ROOT),
            source_url=f"https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{int(cid.split('_')[0]):03d}/{cid}.bvh",
            src_fps=120, src_frames=s.get("frames_total"), duration_s=s.get("duration_s"),
            out_npz=os.path.relpath(out, ROOT), out_frames=int(len(r["src_frames"])), root_scale=round(float(r["scale"]), 4),
            path_len_m=s.get("path_len_m"), mean_speed_mps=s.get("speed_mean_mps"),
            base_mesh_lowest_vertex_y_m=floor_stats(r, V, W),
        ))
        print(f"{name:26s} {cid:7s} -> {len(r['src_frames'])} frames")
    json.dump(man, open(os.path.join(out_dir, "MANIFEST.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
