# Protagonist avatar (1/3): 3D stand-in and identity reference pack

Date: 2026-09-28. The code is in `claudepop/avatar/tools/`. Everything derived from the subject's photo is under
`claudepop/out/avatar/`, which git ignores: the photo itself, landmarks, meshes, textures, renders, embeddings and
the identity pack. This report is text only. It deliberately contains no numbers measured from the face (landmark
errors, similarity scores, face proportions); those are in `claudepop/out/avatar/check/*.json` and
`claudepop/out/avatar/identity/`.

## What was built

| Output (`claudepop/out/avatar/`) | What it is |
|---|---|
| `subject.glb` | Full-body protagonist, skinned to the MakeHuman default rig with the MPFB2 weights. Photo-textured face, hair, black knit henley with one gold button, dark trousers, dark shoes. About 63 k triangles, 163 bones, 5.7 MB, textures embedded. |
| `subject_camera.json` | The photo's own camera in the GLB frame, three.js-ready, plus the render camera used for fitting. |
| `subject_report.json` | Per-part triangle counts, floor offset and heights. |
| `bust/` | The odyssey single-view bust from the same photo: `bust.glb`, `points.bin` (point cloud) and `facemesh.json`. Kept for point-cloud and "reconstruction" shots. |
| `identity/` | Reference pack for the generative models, `identity.md` (prompt description, scorer usage and thresholds), the reference embedding and the calibration. |
| `check/` | Verification renders and sheets: `sheet_turn.jpg`, `sheet_head.jpg`, `sheet_photo_vs_render.jpg`, `sheet_pose.jpg`, `likeness*.{json,jpg}`, `intersections.json`, `similarity_hist.png`, and `final/` (individual PNGs). |

GLB conventions are the same as the output of `odyssey/body/retarget_mh.py`:

- Metres, Y up, the character faces +Z.
- Bone frames follow Blender's convention (+Y along the bone, MPFB roll), converted (x, y, z) → (x, z, −y).
- The rest pose is MakeHuman's A-pose.
- The model is shifted so the shoe soles sit at y = 0. The shift is stored in `asset.extras.floor_offset_m`. The
  `root_pos` in the motion files is already floor-based.

Triangle budget by part: photo fringe layer 16.7 k, skin 15.6 k, teeth 7.1 k (hidden; the first thing to drop if the
budget is tight), top 5.4 k, shoes 4.1 k, hair shell plus two fur shells 3 × 3.3 k, trousers 1.7 k, eyes 1.1 k. It
renders in about a second per frame at 1024² under SwiftShader.

## Method

1. **Photo.** `odyssey/model/rectify.py` runs with the README corners. They were verified on 4× zooms of the page
   corners: each lands on the photo corner. `analyze.py` produces 478 MediaPipe landmarks, a 6-class segmentation
   and Depth-Anything-V2 depth. `build_mesh.py` builds the bust. The odyssey code is unchanged.
2. **Body** (`mhscene.py`). MakeHuman macro targets: male, 25 years, East Asian, lean. The height slider is solved by
   bisection for 175 cm, which is an assumption. The MakeHuman assets are CC0 and were fetched and verified by
   `odyssey/body/fetch_makehuman.py`.
3. **Face fit** (`fit_face.py`), by analysis-by-synthesis, with no hand-placed correspondences:
   - Render the MakeHuman head with a small numpy renderer (`swr.py`) and run the same MediaPipe landmarker on the
     render. Each landmark found is traced back to the skin surface, which gives 478 MakeHuman ↔ MediaPipe
     correspondences.
   - Map the photo landmarks into the render frame with a 2D similarity, so the head keeps MakeHuman's size.
   - Compute a displacement at each correspondence. The image-plane part is lifted to metres at the landmark depth.
     The depth part is a damped difference of MediaPipe's own z (photo minus render), so MediaPipe's depth bias
     cancels.
   - Solve the displacement field as an affine term plus a thin-plate residual, with zero-residual anchors on the
     back of the skull and the neck. Mask it with the MPFB2 head-bone weights. The eyeballs move rigidly.
   - Re-render, re-detect and repeat. A final pass moves each eyeball so the rendered iris lands on the photo's iris.
4. **Silhouette fit** (`fit_shape.py`). Ear extent and lobe, neck width, and the shoulder line's width and height
   below the chin, measured on the photo's segmentation and on a render from the same camera. These are solved with
   MakeHuman's own modifiers (ear scale, shift and protrusion per side; neck width and length; torso width) by
   damped Gauss-Newton. The camera follows the head when a neck modifier moves it, so the photo alignment holds.
5. **Texture** (`bake_texture.py`):
   - The skin mesh is rasterised in UV space. Each texel is projected through the photo camera, z-tested and weighted
     by how frontal it is.
   - The photo is used for the face, ears and neck. Silhouette edges are ramped so no background, hair or collar
     colour bleeds in.
   - Above the brows the forehead uses body skin, because the photo's forehead is a patchwork of fringe strands.
   - Low-frequency colour is a harmonic field solved on the mesh vertices: photo colour where the photo sees the
     skin, MakeHuman body colour far from the head. Being on the vertices, it is continuous across UV seams. On top
     go MakeHuman's own high frequencies (colour-transferred young_asian_male skin), then a Laplacian-pyramid blend
     with the photo. Result: no visible seam at the face border.
   - Eyes: the photo's eyes (iris, sclera, catch-light) are projected onto the fitted eyeballs. Each iris is completed
     under the upper lid as a disc from its radial colour profile, so the iris turns with the eye bones.
   - Brows: a tinted MakeHuman eyebrow proxy.
6. **Hair** (`build_hair.py`):
   - Volume: MakeHuman `short02`, re-volumised per image angle (smoothed displacement, roots stay on the scalp) until
     the head-plus-hair silhouette from the photo camera matches the photo's.
   - The photo's hair is baked onto its frontal texels, and its front edge is carved to the photo's hairline.
   - Fringe: a 2.5D layer carrying the photo's own difference-matted strands. It sits 4–9 mm in front of the skin and
     hair, so it never enters the face, and fades only where broad regions are seen edge-on.
   - Scalp: skin under the hair is painted the root colour. The forehead seen between strands is excluded.
   - Material: dark albedo, `KHR_materials_anisotropy` along the combing direction, plus two alpha-tested fur shells.
7. **Clothes** (`build_clothes.py`):
   - Henley: grown from the body's own torso and arm faces (6 mm offset, Taubin-smoothed, a folded 3 mm edge at
     neckline, cuffs and hem). It shares the body's vertices, so it carries exactly the body's weights.
   - Neckline: the front follows the photo's collar line, the sides start where the collar meets the neck
     silhouette, and the back rises like a crew neck. The placket notch and gold button are placed where the photo
     shows them.
   - Trousers: MakeHuman `male_casualsuit03`, trouser part only, recoloured charcoal. Shoes: MakeHuman `shoes03`.
   - Skin hidden under the clothes is deleted, except for a ring kept under each garment edge.
8. **Export** (`export_glb.py`):
   - A GLB writer of our own (`avlib.py`).
   - The MPFB2 weights are reduced to the 4 largest per vertex and renormalised.
   - Proxy weights are interpolated from their MakeHuman reference vertices, as MakeHuman/MPFB do.
   - UV gutters are padded so sampling shows no seams.
9. **Verification** (`render_glb.mjs`, `contact_sheets.py`, `measure_likeness.py`, `check_intersections.py`):
   - three.js r180 in headless Chromium with SwiftShader, the same stack as the film.
   - Views: turntable, head close-ups, the photo's own camera (flat and look light), head at 0/20/35/50/90° under
     flat light, and a test pose.
   - The face landmarker runs on the photo-camera render; the mean landmark error is reported as a percentage of
     the outer-eye distance. A penetration check runs on the hair and clothes.

Problems found in renders and fixed during review:

- A dark "visor" was scalp paint under the fringe.
- The iris was greyed by the cornea shell.
- The collar sat too low because the MPFB head weights reach into the chest.
- A jagged fringe edge came from segmentation labelling the skin between strands as hair, and from grazing-angle
  fading of the fringe layer.
- The eyes sat too deep and the lashes read as eyeliner.

## Measured versus inferred

| Measured from the photo | Inferred |
|---|---|
| The 2D face geometry: all 478 landmarks from the front. | Depth along the view axis: nose projection, chin and cheek volume in profile come from MediaPipe's depth estimate, applied as a damped difference on top of MakeHuman's average East Asian male. |
| Iris positions. | The back and top of the skull. |
| Ear outline and lobe height. | The ears seen from the side or back. |
| Neck width and the shoulder line just below the neck. | The body below the chest, the limbs, hands and feet: MakeHuman averages. |
| Skin colour and the frontal skin texture. | The skin texture outside the photo's view: MakeHuman's, colour-matched. |
| Hair colour, fringe strands, front hair silhouette and hairline. | The shape and length of the hair at the back and sides. |
| The collar line, placket notch and button position. | The rest of the clothing. |
| — | The height (175 cm, an assumption). |

## Assumptions

- Height 175 cm. Age 25 for the MakeHuman macro. Lean build.
- The photo camera is about 1.3 m from the face. Only the perspective strength depends on this.
- The photo is frontal and neutral, with gaze at the lens.
- Short, tapered back hair. The back is not in the photo.
- The henley is untucked, at MakeHuman's casual-shirt length. The trousers are charcoal jeans-cut and the shoes
  black.

## Limitations and remaining defects

- **Hair** is a stand-in:
  - It is a sculpted shell with fur shells: it reads as black hair with a soft sheen and the right silhouette, but
    looks like a smooth mass up close.
  - The fringe is a 2.5D photo layer: at about 90° it shows as a thin dark band over the forehead.
  - The hard alpha edges at the nape soften with `material.alphaToCoverage = true` on the `hair*` materials (MSAA
    on).
  - Final hair comes from the generative plates.
- **Face at larger angles:**
  - The face texture is the photo up to about 35–40° of yaw; beyond that it is colour-matched MakeHuman skin.
  - The photo's frontal lighting is baked in, with a faint lighter streak on the cheek at about 50°.
  - The profile shape is inferred.
- **Brows** are a tinted MakeHuman proxy.
- **Lighting sensitivity.** Under a dark, directional light the face reads less like him than under flat light,
  because the albedo already contains the photo's shading. Close-ups and hero shots come from the plates, as
  planned.
- **Knit top:** no cloth simulation or folds; the hem is slightly wavy, with a small notch at the centre back. The
  folded edge at each cuff dips a few millimetres into the wrist, hidden inside the sleeve.
- **Unused face rig.** The MPFB face bones are rigged and weighted but untested; no blend shapes were exported.
- **three.js bone names.** `GLTFLoader` removes the dots from node names (`upperarm01.L` becomes `upperarm01L`).
  Motion files from `retarget_mh.py` use the dotted names; strip the dots when binding.

## How to rebuild

```bash
claudepop/avatar/tools/build_all.sh            # venv, models, photo -> subject.glb -> renders -> identity pack -> calibration
claudepop/avatar/tools/build_all.sh --no-calib # skip the ~10-minute scorer calibration and its downloads
```

The single steps, in order: `fit_face.py`, `fit_shape.py`, `bake_texture.py`, `build_hair.py`, `build_clothes.py`,
`export_glb.py`, then `render_glb.mjs … --modes turn,head,photo,photolit,headflat,pose`, `contact_sheets.py`,
`measure_likeness.py`, `check_intersections.py`, `build_identity.py`, `face_similarity.py --build-ref` and
`face_similarity.py --calibrate`.

- Python runs in `claudepop/out/venv-avatar`: numpy 1.26, scipy, opencv-contrib 4.10, mediapipe 0.10.21,
  onnxruntime, trimesh with rtree, matplotlib.
- Node uses `claudepop/avatar/tools/node_modules` (three 0.180, playwright-core 1.56.1).
- Chromium is `/opt/pw-browsers/chromium-1194` with SwiftShader.
- Set `PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1`.

## Using it in the film

- **Load:** three.js `GLTFLoader`. One skinned mesh node per part, all bound to one skin. The hair uses
  `MeshPhysicalMaterial` with anisotropy, created automatically by the loader.
- **Motion:** the curated CMU clips from `odyssey/body/curate_motion.py` use the same skeleton and bone frames.
  Apply `local_quat` to the bones (names without dots) and `root_pos` to the root bone.
- **Photo camera:** `subject_camera.json` → `photo_camera` reproduces the passport framing exactly. It is used for
  the "reconstruction" beats (photo, then the model turning away from it). `render_glb.mjs` shows the projection
  matrix, including the principal-point offset.
- **Point-cloud and bust shots:** `bust/points.bin` and `bust/facemesh.json`, in the same format as `odyssey/film`.

## Identity pack and similarity scorer (for the next session's generative models)

- **Pack:** `claudepop/out/avatar/identity/`. It holds:
  - `face_clean_1024.png`: the passport framing on a clean neutral background; stamps and page removed through a
    soft matte; the face is not retouched.
  - `face_aligned_512.png` (FFHQ-style alignment), `face_crop_square.png`, `head_shoulders_4x5.png`.
  - Mattes (`matte.png`, `face_hair_matte.png`, `cutout_rgba.png`).
  - `identity.md`: a neutral visual description and prompt fragment, plus what not to add.

  Upload these only to the service the user has approved. Use `face_clean_1024.png` as the main reference/subject
  image and `face_aligned_512.png` wherever an aligned face crop is expected.
- **Scorer:** `claudepop/avatar/tools/face_similarity.py`. It runs InsightFace SCRFD-10G (two scales, so
  frame-filling close-ups are found), a 5-point alignment and ArcFace R50 trained on WebFace600K, all on CPU through
  onnxruntime. The output is the cosine similarity to the reference embedding. It accepts images, folders and videos
  (`--every N`) and writes JSON with the score, a verdict and a yaw proxy.

  ```bash
  cd claudepop/avatar/tools
  ../../out/venv-avatar/bin/python face_similarity.py plate.png frames/ clip.mp4 --every 12 --json scores.json
  ```

- **Calibration** (`calibrate_similarity.py`; results in `identity/scorer_calibration.json` and
  `check/similarity_hist.png`). Impostors: 400 LFW identities, 160 StyleGAN faces from thispersondoesnotexist.com,
  a young-male subset picked with the InsightFace gender/age model, and the unfitted MakeHuman head. Genuine and
  near-genuine: the photo under 15 degradations, and the avatar at several yaw angles under two lightings.
  - The thresholds sit above every impostor seen, with a margin. Scores between them should be checked by eye.
  - Near-profile faces are flagged `pose-unreliable`.
  - The numbers are in `identity/identity.md`.
  - Score plates before the grade and the HUD.
- **Licences:**
  - InsightFace code is MIT. Its pretrained models (buffalo_l) are "available for non-commercial research purposes
    only", with licensing through recognition-oss-pack@insightface.ai. Source: github.com/deepinsight/insightface
    README, read 2026-09-28. Clear this before commercial use.
  - MakeHuman and MPFB2 assets are CC0.
  - MediaPipe models are Apache-2.0.
  - LFW and the StyleGAN faces were used locally for calibration only and are not redistributed.

## Verification (avatar 3/3)

Date: 2026-09-28. An adversarial review of `subject.glb`, with fixes, done after the sections above; where they
disagree, this section is current. Text only: the measured values (landmark error, similarity scores, penetration
depths) are in the gitignored `claudepop/out/avatar/check/likeness.json`, `check/final_scores.json`,
`check/intersections.json`, `identity/scorer_calibration.json` and `identity/identity.md`. Review renders and
before/after sheets are in `claudepop/out/avatar/verify/` (`before_after_*.jpg`; `backup_v0/` holds the pre-review model
and code).

### What was checked

- **Photo camera against the rectified photo**: side by side, as a 50 % blend and at 2–4× zoom on eyes (shape, lids,
  lashes, sclera), brows, nose, mouth, jaw and face width, skin tone, hair silhouette and fringe, ears, neck, shoulders
  and collar. The landmark metric was re-run on the final build.
- **Head** at 0/20/35/50/90/180° under flat and look-dev light. Close-ups of the fringe at 30° and 60°, both ears at
  20/45/90°, the eyes, and the eyes turned ±22° in yaw and +15/−12° in pitch through the `look` layer.
- **Clothes**: collar front, side and back; cuffs from four sides; hem front and back; each with the skin or the top
  hidden as well.
- **Motion through `avatar.js`** (the film's code path): all 35 contact sheets regenerated, plus joint close-ups on
  `walk_runway_loop`, `stand_head_roll` (head-back extreme), `dance_expressive_arms` (arm up, hand on head), `sit_floor`
  (hands behind), `look_back_over_shoulder`, `face_in_hands_standing`, `reach_forward` and `kneel_one_knee`: shoulders,
  elbows, wrists, cuffs, hem, collar and fringe.
- **Look-dev**: stills L0–L3 re-rendered with the final model; `lookdev/avatar_test.mjs` passes.
- **Identity scorer** on every check render; the calibration was re-run (thresholds unchanged).
- **Rebuild**: `build_all.sh --no-calib` from the photo ran twice at the end and produced a byte-identical `subject.glb`.

### Defects found and fixed

1. **Fringe.** The 2.5D photo layer read as dark paint drips with hard cut-outs from the front, a visor from the side
   and torn shards at the temples, and was cut off in a straight line at the brows. The fringe is now about 300 ribbon
   strands (new `build_strands.py`):
   - They are traced along the photo's own strand orientation, with a difference matte against the forehead skin
     deciding where hair is.
   - Each strand roots over the hair shell and falls onto the forehead 3.5–6.5 mm off the skin.
   - They are textured with a fibre alpha map and carry a tangent for the anisotropic highlight.
   - The photo layer is no longer exported (`build_hair.py` still computes it for colours and visibility).
2. **Bald scalp.** The scalp-paint exclusion meant for the forehead seen between strands covered the whole top of the
   head (bright hair pixels counted as "visible skin"), so skin showed through every gap in the hair cards. The per-gap
   carve also cut slots that read as pink stripes from below. Now one smooth fringe zone is carved (forehead between the
   outer eye corners, below a hairline arc, the cut edge ending in clump tips); everything else under the hair is root
   colour.
3. **Cap line at the carved edge.**
   - The fur shells are carved further back.
   - Alpha to coverage stays off the fur shells; on them it dithered the edge into a dotted light line.
   - Strands also start over the shell (sparser, wider) and cross the edge.
   - The skin just under the edge gets the root colour, and the forehead a soft fringe shadow.
4. **Eyes.** MakeHuman's lash cards (even shortened, upper lid only) read as a grey mascara comb; they are removed, and
   the photo texture carries the lash line. The MakeHuman sclera around the photo aperture was paper white and showed
   as white wedges at the eye corners; it is now matched to the photo's lid-shadowed eye white. A glossier eye for a
   live catch-light was tried and rejected: without a cornea it becomes a milky blob on the iris.
5. **Brows.** The tinted brow proxy read heavier than the photo, where the brows are under the fringe; it is now
   faint.
6. **Cheek streak.** The photo booth's side-light highlights along the face edge were baked into the albedo and showed
   as a light streak at 35–50° of yaw. They are removed where the surface turns away, and the low-frequency skin colour
   uses a masked blur, so no page or ear colour bleeds in.
7. **Saw-toothed collar, cuffs and hem in motion.** The garment edges had smoothed positions but unsmoothed skin
   weights (alternating neck- and chest-weighted base vertices), so any neck or arm motion pulled them back into saw
   teeth. The weights are now smoothed along the edges like the positions. The first three rings inside each edge are
   relaxed tangentially, never inward: an inward version let the trouser waistband poke through at the back, which was
   caught in review. The "pie-crust" wave from per-vertex normals is gone.
8. **Button** sheared when the neck moved (per-vertex nearest weights); it is now skinned rigidly.
9. **Clay look (L0)** turned every hair part black (albedo times clay grey), and the carved shell would have
   reappeared. Clay now uses the hair maps for alpha only, and the alpha-part pattern in `avatar.js` covers every hair
   part.
10. **Temples.** Carving reached the side hair and cut it into a jagged edge; the carve is now limited to the forehead.
    Strands are confined to the head's silhouette (a tuft stuck out above the crown).
11. **Tooling.**
    - `render_glb.mjs --modes views --views FILE.json` renders review close-ups.
    - `check_intersections.py` now checks the ribbon strands (their vertices sit on transparent ribbon edges and were
      skipped).
    - `build_all.sh` runs `build_strands.py` and `check_intersections.py`.

### Superseded statements above

- **Parts:** 67.6 k triangles in total: strands 21.8 k, skin 15.6 k, teeth 7.1 k, top 5.4 k, shoes 4.1 k, hair shell
  plus two fur shells 3 × 3.3 k, trousers 1.7 k, eyes 1.1 k, brows 0.2 k. 7.2 MB. There is no `hair_front` and no
  `eyelashes` part; the fringe mesh is `hair_strands`.
- **Hair method** (step 6 above): the fringe is ribbon strands, the shell is carved over the fringe zone, and the fur
  shells use their own texture.
- **Top:** the knit top's skin weights are smoothed along its edges, and the button is rigid.
- **Identity pack:** the stand-in rows in `identity/identity.md` were re-measured.

### Remaining defects

- **Hair:**
  - The mass is still MakeHuman `short02`: a smooth helmet silhouette without strand break-up at the top and back,
    unlike the photo's wavy, flyaway volume.
  - The sideburn edges stipple.
  - A faint tone step remains where the shell meets the fringe strands.
  - The fringe follows the photo's pattern and density but is re-synthesised, so from the photo camera it matches the
    exact strands less closely than the old photo layer did (the frontal identity score is a little lower; realism at
    every other angle is much higher).
- **Face:**
  - The lower face at 3/4 is fuller than the photo's narrow jaw (inferred depth).
  - The face outline is still the weakest landmark region.
  - The profile is inferred.
  - A faint trace of the cheek highlight remains at about 50°.
- **Eyes:** the iris is a low-resolution photo projection with the photo's catch-light baked in, and there is no cornea.
  Eye turns up to 22° stay clean.
- **Clothes:** the neckline is a polyline of roughly 1 cm segments (coarse MakeHuman mesh), visible under a hard key.
- **Hands:** MakeHuman averages with procedural fingers, large in close-up. Hand-to-head contacts sink into the hair
  (`dance_expressive_arms` around 3.7 s).
- **Motion:** foot sliding as in LOOKDEV.md. `stand_head_roll` stretches the neck at its head-back extreme.
- **Ears:** a small glint shows on each helix top through the side hair. In L1's hard key the concha falls into a hard
  black shadow (look-dev lighting).
- **Penetration check:** it flags about a dozen sleeve vertices at the cuffs. They are 2–3 cm from any remaining skin
  vertex (the forearm skin under the sleeve is deleted), where the nearest-vertex normal test does not apply; the cuff
  close-ups show no poke-through.
- **Mouth:** closed only (no blend shapes, jaw untested), so no lip sync.

### Camera and lighting rules for the film

1. **Close-ups** (head taller than about a third of the frame): face yaw within ±20° of the photo axis, pitch within
   ±10°, soft key within about 30° of the camera axis. No extreme close-ups of eyes, hairline, ears, hands or neckline.
2. **Medium shots:** yaw up to ±35°. Beyond about 40° the face must not carry identity: go wide, silhouette,
   backlight/rim, motion blur or the face in shadow.
3. **Profile and back of the head:** silhouette or rim light only. The profile, skull and back hair are inferred.
4. **Light:** the photo's frontal shading is baked into the albedo.
   - Hard side or top keys on the face (L1) only at wide or medium size, or with the face mostly in shadow.
   - Add fill so the ear does not go black.
   - Backlight plus rim (L2) hides the inferred regions best.
5. **Angles:** no high angles on the hair in close-ups (more than about 30° down), and no low angles on the neckline
   under a hard key.
6. **The exact-likeness beat** (photo, then the model turning away): start from the photo itself and dissolve into the
   render from `photo_camera`. Do not rely on the model alone for the frontal likeness.
7. **Motion:**
   - Clips with visible feet: walks, idles and turns only.
   - Tai chi, dance, floor and prop clips (not foot-locked) only with the feet out of frame or hidden.
   - Keep `stand_head_roll` 4–5 s and the hand-on-head frames of `dance_expressive_arms` (3–4 s) out of close-ups.
8. **Eyes** through the `look` layer: up to 22° is clean. Keep targets in front of the face.
9. **Identity scoring:** score generated plates against the photo reference (`identity/`) before the grade and the HUD,
   never against the stand-in.
