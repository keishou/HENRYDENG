# Protagonist avatar (2/3): motion library, three.js module and look-dev

Date: 2026-09-28. Code: `claudepop/avatar/tools/motion_lib.py`, `claudepop/avatar/tools/head_points.py`,
`claudepop/film/src/{avatar,post,hud}.js`, `claudepop/film/lookdev/`. Everything derived from the subject (motion data
bound to his skeleton, renders, the head point cloud) is under `claudepop/out/` (gitignored). This file is text only and
contains no numbers measured from the face.

## 1. Motion library

`motion_lib.py build` downloads the sources, retargets them onto the skeleton of `subject.glb` and writes
`claudepop/out/avatar/motion/<clip>.bin` plus `MANIFEST.json` (about 3 minutes on 1 core).

**Sources.** CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), BVH conversion by B. Hahne (cgspeed), raw files
from github.com/una-dinosauria/cmu-mocap, clip titles from its `cmu-mocap-index-text.txt` (v1.00, 2008-07-20; read
2026-09-28). Licence: free for any use; requested acknowledgement "The data used in this project was obtained from
mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." Candidates were first screened with
`odyssey/body/inspect_motion.py` stick-figure sheets (`out/avatar/motion/inspect/`).

**Method** (extends `odyssey/body/retarget_mh.py`, which is unchanged):
- World-space rotation deltas from the cgspeed T-pose, onto a calibration pose of the subject's own rest skeleton read
  from the GLB, so the local quaternions drop straight onto the three.js bones.
- Neck and head deltas come from the zero pose. The cgspeed T-pose pitches the head about 16° down, which otherwise
  leaves every clip with a permanent chin-up.
- Anti-candy-wrapper twist distribution:
  - forearm twist split 1/3 : 2/3 over lowerarm01/02, shin twist over lowerleg01/02;
  - upperarm01 / upperleg01 keep half of the humerus / femur twist.
- Spine and neck bends are split half and half where one CMU joint drives two MakeHuman bones.
- Unmapped bones (fingers, face) stay at rest.
- Heading normalisation: every clip starts at the origin facing +Z; walks travel along +Z.
- Foot lock with two-bone leg IK on heel and ball contact spans (3 passes); runs use looser contact thresholds.
- Per-frame floor contact from the skinned subject mesh (shoes, trousers, skin, top, hair).
- Loops: the best-matching cycle, seam residual removed linearly, foot lock and floor run on 3 chained copies.

**Format.** `<clip>.bin` is float32, frame-major, at 30 fps: root position, then one xyzw local quaternion per animated
bone (40 bones; the others stay at the GLB rest). Bone names have the dots already removed, as three.js does.

**Verification:**
- Skinned contact sheets through `avatar.js` itself, 6 times × 2 views per clip, all looked at:
  `out/avatar/motion/sheets/*.jpg`.
- Close-ups at each clip's maximum-twist frame and at knees, neck and hands-to-face: `out/avatar/motion/detail/`.
  No candy-wrapper is visible.
- The manifest records per clip:
  - the lowest point per frame (floor float / penetration);
  - foot skate per contact span (maximum drift from the span's median);
  - source and residual twist per segment.

Columns: skate is p90 / max in cm; floor is the lowest point relative to y = 0, in cm.

| Clip | s | Loop | Path m | Source (CMU id, segment) | Skate cm | Floor cm | Shows |
|---|---|---|---|---|---|---|---|
| walk_slow | 10.0 | no | 3.84 | 132_45 1.5-11.5 | 1.4 / 2.5 | -0.5..+0.5 | very slow straight walk (~0.45 m/s), head level: toward / away from camera |
| walk_slow_loop | 2.9 | 2.93 s, +1.18 m | 1.19 | 132_45 | 1.2 / 1.2 | -0.5..+0.4 | seamless cycle of walk_slow |
| walk_sad_headdown | 9.7 | no | 4.67 | 142_15 2.1-11.8 | 1.4 / 3.5 | -0.5..+0.6 | sad walk, head lowered |
| walk_relaxed | 7.5 | no | 4.70 | 142_13 1.5-9.0 | 1.7 / 4.1 | -0.8..+0.5 | relaxed walk, easy arm swing |
| walk_runway_loop | 1.3 | 1.30 s, +1.25 m | 1.22 | 142_04 2.0-7.5 | 1.6 / 1.6 | -1.0..+0.8 | confident 'cool' walk (~1 m/s): the runway walk |
| walk_attitude | 9.0 | no | 4.52 | 104_44 0-9.0 | 1.5 / 4.5 | -1.1..+0.8 | 'attitude' walk, chin up |
| walk_stop_lookright | 8.9 | no | 4.25 | 104_35 0-8.9 | 1.4 / 1.8 | -0.6..+0.7 | stands, walks ~4 m, stops, looks ~45° right |
| walk_stop_lookup | 7.5 | no | 3.80 | 82_14 0-7.5 | 1.3 / 1.4 | -0.4..+0.8 | walks in, stops and looks up (from ~4.5 s) |
| walk_depressed | 7.1 | no | 4.60 | 91_14 2.6-9.7 | 3.3 / 4.2 | -0.6..+0.8 | depressed walk, head low, one in-place 180° turn |
| idle_stand | 7.8 | no | 1.16 | 77_02 0-7.8 | 1.3 / 1.5 | -0.5..+0.4 | quiet standing, small shifts |
| idle_wait | 31.0 | no | 5.65 | 137_28 0-31 | 3.4 / 13.7 | -0.4..+0.5 | long wait: shifts, a few steps, glances |
| idle_lookaround_lookback | 51.8 | no | 11.14 | 40_10 0-51.8 | 2.3 / 10.2 | -1.8..+1.7 | bus-stop wait: turns body and head to look around and behind |
| look_back_over_shoulder | 11.4 | no | 0.87 | 76_10 0-11.4 | 2.0 / 3.0 | -0.4..+0.2 | twists to look back over each shoulder |
| sit_floor | 18.7 | no | 0.37 | 82_05 0-18.7 | 1.5 / 2.2 | -0.5..+0.7 | seated on the floor, knees up, looks around |
| kneel_one_knee | 6.8 | no | 1.42 | 23_03 0-6.8 | 2.5 / 3.8 | -0.5..+0.4 | goes down on one knee reaching a hand forward, rises |
| sit_stool_head_bowed | 6.0 | no | 0.18 | 22_03 0-6.0 | 1.3 / 1.4 | -1.2..+1.5 | seated (needs a ~0.6 m seat), elbows on knees, head bowed |
| turn_in_place_ccw | 9.4 | no | 0.93 | 69_16 0-9.4 | 2.1 / 2.2 | -0.7..+0.6 | slow 360° turn left in 4 step-turns |
| turn_in_place_cw | 8.8 | no | 0.71 | 69_18 0-8.8 | 1.6 / 4.4 | -0.9..+0.7 | slow 360° turn right |
| stand_breathe_loop | 2.4 | 2.40 s | 0.02 | 111_28 0-4.0 | 0.6 / 0.6 | 0..0 | near-motionless standing: base for procedural breath |
| stand_head_roll | 11.4 | no | 1.00 | 113_21 0-11.4 | 1.4 / 1.6 | -0.1..+0.2 | still stance, slow head roll back and around (look up) |
| lie_down_and_rise | 15.3 | no | 1.73 | 113_08 0-15.3 | 5.2 / 8.9 | -1.4..+1.8 | lowers to the floor, lies on the back, gets up |
| lie_down | 9.5 | no | 0.89 | 113_08 0-9.5 | 5.1 / 5.5 | -1.4..+1.3 | lowers to the floor and lies still |
| rise_from_lying | 6.3 | no | 0.86 | 113_08 9.0-15.3 | 6.5 / 8.9 | -1.4..+1.8 | from lying on the back to standing (faces +Z at the end) |
| fall_backwards | 3.2 | no | 0.28 | 90_18 0-3.2 | 0.9 / 1.1 | -3.4..+2.4 | legs go, falls flat on the back (~1.1 s), lies still |
| reach_forward | 11.0 | no | 1.36 | 15_06 1.5-12.5 | 1.5 / 1.6 | -0.1..+0.2 | leans and reaches one hand forward, repeated |
| face_in_hands_standing | 7.9 | no | 0.60 | 79_72 0-7.9 | 0.8 / 0.8 | -0.2..+0.1 | bends forward, hands to the face (crying, 1.8-6.2 s) |
| grief_standing | 13.3 | no | 0.39 | 80_45 0-13.3 | 0.5 / 0.5 | -0.5..+0.6 | hand to the face, head bowed, long and quiet |
| start_run | 2.8 | no | 3.86 | 127_03 0-2.75 | 2.8 / 3.0 | -1.4..+6.9 (flight) | from standing into a run (~4 m/s at the end) |
| run_loop | 0.8 | 0.80 s, +1.99 m | 1.92 | 16_36 0-1.55 | 2.9 / 2.9 | -1.1..+5.1 (flight) | seamless jog cycle (~2.6 m/s) |
| tai_chi_sway | 60.0 | no | 5.99 | 12_04 20-80 | 5.0 / 18.7 | -1.0..+1.3 | slow tai chi: understated sway under half-time 66 BPM |
| dance_expressive_arms | 9.4 | no | 1.79 | 05_02 0-9.4 | 4.2 / 4.3 | -1.5..+1.0 | modern dance: arm sweeps, a pirouette |
| dance_twist | 4.7 | no | 2.95 | 141_12 0-4.7 | 2.2 / 2.4 | -1.5..+1.5 | casual twist on the spot |
| arms_open_stretch | 3.1 | no | 0.44 | 143_30 0-3.1 | 1.4 / 1.4 | -2.3..+1.9 | both arms open wide and up (peak 1.4-2.0 s) |
| arms_out_balance | 7.2 | no | 0.15 | 49_18 2.0-9.2 | 1.5 / 1.8 | -0.1..+0.1 | arms held out, balancing on one leg |
| sit_down_get_up | 6.3 | no | 1.67 | 143_18 0-6.3 | 4.8 / 5.2 | -0.8..+0.9 | sits onto a ~0.45 m seat and gets up |

Tempo: `walk_runway_loop` has a 0.65 s step. At speed 0.715 its steps land on every beat of half-time 66 BPM (one step
per two beats of the song's 132 BPM). `beatSpeed()` computes this for any loop.

## 2. avatar.js (`claudepop/film/src/avatar.js`)

The API is documented at the top of the file. In short:
- `const av = await Avatar.load({ glb, manifest, clips })`, then `scene.add(av.root)`.
- `av.pose(clip, t, { loop, speed, rootMotion: true | false | 'lock', place: { x, z, yaw } })` returns a pose as plain data.
  - Loop clips chain cycles by the stored per-cycle displacement.
  - `false` walks in place.
  - `'lock'` also freezes the heading.
- `av.mix(a, b, w)`, `av.crossfade(a, b, t, t0, dur)`: per-bone slerp with a smoothstep weight.
- `av.sequence([{ clip, at, from, speed, fade, loop, rootMotion }], place)`: an edit on the film timeline. Each segment
  is placed so its root and heading continue the previous one; returns `{ pose(T), heading(T), segments }`.
- `av.apply(pose, layers, t)`: sets every bone (no state between frames), then adds the procedural layers:
  - `breath { amp, period, phase }`;
  - `look { target, weight, eyes, maxDeg }` for neck and head, plus eyes limited to 22°;
  - `noise { amp, seed }`, smooth seeded fbm;
  - `hands { curl }`, a relaxed finger curl.
- `av.setLook('photo' | 'clay' | 'silhouette' | 'ghost' | fn)`.
- Helpers: `av.heading`, `av.placePose`, `av.beatSpeed`, `av.bone`, `av.worldPos`, `av.headAnchor`, `av.meshes`,
  `av.origMat`.

Checked by `lookdev/avatar_test.mjs` (results in `out/lookdev/avatar_test.json`):
- `pose()` and `apply()` are pure: repeated samples and re-applies are bit-identical.
- Sequence cuts: root jump under 0.1 mm, heading jump under 0.02°.
- Root-motion lock holds x, z = 0 and a constant heading.
- A look-dev frame is pixel-identical when rendered out of order and in a fresh browser.

Companions:
- `post.js`: HDR target (4× MSAA), bloom plus halation, ACES, grade in display space (mono with split tone,
  saturation, contrast, lift / gain), vignette, HUD layer, grain, dot screen, scanlines, letterbox, 8-bit dither.
- `hud.js`: type and HUD primitives on a 1920×1080 design grid.
  - Fonts: Inter Tight, IBM Plex Mono, Barlow Condensed, Instrument Serif (SIL OFL; `film/fetch_fonts.sh` puts them in
    `out/fonts/`).
  - The HUD canvas is CPU-backed and uploaded as raw bytes. Under SwiftShader this cut the HUD cost from about 245 ms
    to about 30 ms per 720p frame.

## 3. Look-dev (`claudepop/film/lookdev/`, stills in `claudepop/out/lookdev/`)

Run `node capture.mjs stills`, then `node capture.mjs timing --workers 1|2`.
- Stills: `L{0..3}_{wide,medium,close}.jpg`, plus `lookdev_sheet.jpg` with all 12.
- Other tools: `motion_sheets.mjs` (motion contact sheets), `detail.mjs` (joint close-ups), `dbg.mjs` (evaluate code in
  the page and grab a frame).

- **L0 previs:** flat grey clay (alpha strands kept), grid runway, burned-in shot id / clip / timecode / frame / lyric;
  1280×720.
- **L1 chiaroscuro:** monochrome; one hard spot key sized for constant subject illuminance, soft shadows (2048² map), a
  faint cool back rim, a dust beam in the wide shot, 2.39:1 bars, grain and halation, a serif subtitle and a big serif
  word.
- **L2 runway:** the fashion-film × AI-economy HUD language:
  - night runway toward camera, a rain-wet planar mirror floor with puddle mask and animated ripples;
  - a feathered backlight panel, hard rim light, runway LEDs, GPU rain streaks;
  - crowd impostors rendered from the avatar itself as silhouettes;
  - cold desaturated grade, dot screen and scanlines;
  - HUD: corner crosses, labels, frame ruler, waveform, a boxed orange counter, a receipt card, a tracking bracket,
    and a bottom ticker of lyric-derived AI-economy copy (all numbers are invented placeholders);
  - one Claude-orange accent (#D97757) per frame.
- **L3 reconstruction:**
  - the body as about 48k points sampled on the skinned mesh (they follow every clip) plus world-height contour lines
    on the clothes;
  - the head from the photo point cloud (`bust/points.bin`, aligned to the head bone by `head_points.py`);
  - a noise-driven dissolve front where points drift up and re-form, an orange scan line;
  - HUD copy "measured 1 view · inferred 359°".

Render time per frame: consecutive 24 fps frames, 12 per shot × 3 shots after a warm-up, including the JPEG capture the
film uses. 4 cores, SwiftShader, 2026-09-28.

| Look | Size | 1 worker (median) | 2 workers (median per worker / effective) | 156.7 s × 24 fps = 3,761 frames |
|---|---|---|---|---|
| L0 | 1280×720 | 168 ms (effective 176) | 284 / 147 ms | 11.0 min / 9.2 min |
| L1 | 1920×1080 | 1181 ms (1277) | 1745 / 947 ms | 80 min / 59 min |
| L2 | 1920×1080 | 1499 ms (1491) | 2408 / 1199 ms | 94 min / 75 min |
| L3 | 1920×1080 | 795 ms (839) | 1227 / 605 ms | 53 min / 38 min |

Load (1-minute average) was 1.4 → 3.4 during the 1-worker run and 2.4 → 7.75 during the 2-worker run, with other
agents active. SwiftShader already spreads one browser over several threads, so 2 workers give only 1.2-1.35× the
throughput. Plan on 2 workers when the machine is otherwise idle.

## 4. Which look is strongest

**L2 is the strongest and should be the base language.**
- It is the only look in which the stand-in's weak points (smooth hair, fold-less knit, a face texture with baked
  frontal light) disappear. Backlight turns him into a silhouette with a rim, and the medium and close shots still read
  as him.
- It carries the lyric typography natively. The same grid holds large two-line chorus words, subtitle-size lines, tiny
  mono labels and the ticker, which is exactly the variable-presence type the brief asks for.
- It matches the user's reference register without copying it.
- It survives the swap to generative plates in the next session: plates of him walking a wet runway drop in under the
  same grade and HUD layer.

**L3 is the most original** and the most honest about the data (the front is measured, the back inferred). Use it as
the recurring "reconstruction" interruption ("I feel my atoms rearranging", 49.4-51.9 s; the photo-to-body opening),
not for the whole film.

**L1 is the most beautiful at wide and medium sizes.** Use it for the quiet dip (90-108 s). The hard key shows the
limits of the stand-in's face in close-up (the same lighting sensitivity step 1 measured), so close-ups in L1 should
come from plates.

**L0** is the animatic look: about 9-11 minutes for the whole song.

## 5. Defects and limits

- **Foot contact:**
  - The tai chi, dance and floor / prop clips are not foot-locked. Feet pivot or the body is on the ground. Skate p90
    is 4-7 cm; tai chi reaches 18.7 cm (a pivot over 20 s).
  - idle_wait has one 13.7 cm heel slide (2.6-4.4 s) and idle_lookaround_lookback a 10.2 cm one (44-50 s). Cut around
    these or add their spans to the foot lock.
  - Floor contact is enforced for the lowest point only: single limbs (hand, elbow) on the floor can sink up to about
    1.5 cm.
- **Loop seam:** walk_slow_loop has a 5.3° one-frame right-foot rotation at the seam.
- **Twist:** residual upperarm01 twist reaches 89° (sit_floor, hands behind) and 77° (dance_expressive_arms), because
  the source humerus twists 150-180°. Close-ups at those frames show no candy-wrapper under the sleeve, but the
  shoulder is the first place to look if a pose pinches.
- **Head and neck:** stand_head_roll at its head-back extreme (4-5 s) stretches the neck skin and shows the jagged
  collar edge; avoid close-ups there. The neck/head calibration fix removed a 16° chin-up that every clip had.
- **Fingers:** they are procedural (one constant relaxed curl). face_in_hands_standing reaches the face, but the fingers
  do not cover it; set `hands.curl` to 0 for flat palms. The face rig (jaw, lids, lips) is still unused.
- **Props:** sit_stool_head_bowed and sit_down_get_up need seat props.
- **Clip notes:**
  - kneel_one_knee is subject B of a two-person capture, reaching toward the other person.
  - The CMU actors' proportions differ from the subject's; the root is scaled by hip height.
  - The pelvis heading swings ±15° in walk_slow (that actor's hip rotation).
- **L2:**
  - The crowd is 2D silhouettes of the avatar in 7 poses: fine in silhouette, repetitive if studied.
  - The floor is a planar mirror plus ripples, with no splashes.
  - The Reflector renders the scene a second time, which accounts for about a quarter of L2's cost.
  - All HUD numbers are placeholders.
- **L3:**
  - The photo head is a single-view relief, flat from the side.
  - The dissolve front currently blows the top of the hair away. Pick the front height per shot.
  - The contour lines are world-height slices.
- **L1:**
  - The dust beam is subtle (only visible in the wide shot).
  - The black knit loses its edges without the rim light.
- **L0:** alpha fringe strands render as dark blobs; the grid shows moiré near the horizon.
- **Timing caveat:** other agents shared the machine during the measurements.

## 6. Rebuild

    claudepop/out/venv-avatar/bin/python claudepop/avatar/tools/motion_lib.py build   # fetch BVH + retarget + MANIFEST
    claudepop/out/venv-avatar/bin/python claudepop/avatar/tools/head_points.py         # L3 head point cloud
    cd claudepop/film && npm install && ./fetch_fonts.sh
    cd lookdev && export PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1
    node motion_sheets.mjs && node capture.mjs stills && node capture.mjs timing --workers 1 && node avatar_test.mjs

Dependencies: three 0.180 and playwright-core 1.56.1 (`claudepop/film/node_modules`), Chromium chromium-1194 with
SwiftShader, and the avatar venv (numpy, scipy, Pillow).

## Corrections after verification (avatar 3/3)

The verification pass changed a few things this document describes:
- `hair_front` no longer exists; the fringe strands are the mesh `hair_strands` (built by `claudepop/avatar/tools/build_strands.py`).
- The L0 defect "alpha fringe strands render as dark blobs" is fixed.
- `avatar.js`: the list of alpha-carrying parts now covers every hair part, the clay look uses hair textures for shape only, and edge softening is on for the base hair.
