#!/usr/bin/env bash
# Rebuild the protagonist avatar end to end (CPU only, about 15 min plus downloads).
# Everything the scripts write lives under claudepop/out/ and odyssey/.cache/ (both gitignored): the photo, meshes,
# textures, renders and the identity pack are subject data and must never be committed.
#
#   claudepop/avatar/tools/build_all.sh [--no-calib]
set -euo pipefail
TOOLS="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$TOOLS/../../.." && pwd)"
OUT="$REPO/claudepop/out/avatar"
VENV="$REPO/claudepop/out/venv-avatar"
MODELS="$REPO/odyssey/.cache/models"
PAGE="$REPO/claudepop/out/subject/page.jpg"
CORNERS="113,229 857,166 916,930 159,964"   # photo corners on the page (TL TR BR BL), checked in check/rect_corners.png
export PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1
mkdir -p "$OUT/work" "$OUT/check" "$OUT/identity" "$OUT/bust" "$MODELS/insightface"

# 0. environment (own venv: the song agent's claudepop/out/venv is left alone)
if [ ! -x "$VENV/bin/python" ]; then python3 -m venv "$VENV"; fi
PY="$VENV/bin/python"
"$PY" -m pip install -q numpy==1.26.4 scipy pillow opencv-contrib-python==4.10.0.84 mediapipe==0.10.21 onnxruntime \
    trimesh rtree matplotlib imageio-ffmpeg
(cd "$TOOLS" && npm install --no-audit --no-fund >/dev/null)

# 1. third-party models (same sources as odyssey/setup.sh) + InsightFace buffalo_l for the similarity scorer
get() { [ -s "$2" ] || curl -sSL -o "$2" "$1"; }
get https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx "$MODELS/depth_anything_v2_vits.onnx"
get https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task "$MODELS/face_landmarker.task"
get https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite "$MODELS/selfie_multiclass.tflite"
get https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj "$MODELS/canonical_face_model.obj"
if [ ! -s "$MODELS/insightface/buffalo_l/w600k_r50.onnx" ]; then
  get https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip "$MODELS/insightface/buffalo_l.zip"
  "$PY" -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$MODELS/insightface/buffalo_l.zip" "$MODELS/insightface/buffalo_l"
fi

# 2. photo -> rectified photo, landmarks/segmentation/depth, single-view bust (odyssey pipeline, unchanged)
"$PY" "$REPO/odyssey/model/rectify.py" "$PAGE" "$OUT/work" "$CORNERS"
"$PY" "$REPO/odyssey/model/analyze.py" "$OUT/work" "$MODELS"
"$PY" "$REPO/odyssey/model/build_mesh.py" "$OUT/work" "$MODELS" "$OUT/bust"

# 3. MakeHuman CC0 assets (verified download into odyssey/.cache/makehuman)
"$PY" "$REPO/odyssey/body/fetch_makehuman.py"

# 4. avatar
cd "$TOOLS"
"$PY" fit_face.py            # landmark fit of the MakeHuman head (analysis-by-synthesis)
"$PY" fit_shape.py           # ears, neck, shoulders from the photo silhouette
"$PY" bake_texture.py        # photo projection + colour-matched skin, eyes
"$PY" build_hair.py          # re-volumised short02, carved over the fringe zone, scalp / fringe shadow
"$PY" build_strands.py       # fringe as ribbon strands traced along the photo's strand directions
"$PY" build_clothes.py       # knit henley, trousers, shoes, button
"$PY" export_glb.py          # -> claudepop/out/avatar/subject.glb (+ subject_camera.json, subject_report.json)

# 5. verification renders (three.js / SwiftShader) and metrics
node render_glb.mjs "$OUT/subject.glb" "$OUT/check/final" --modes turn,head,photo,photolit,headflat,pose
"$PY" contact_sheets.py "$OUT/check/final"
"$PY" measure_likeness.py "$OUT/check/final/photo_cam.png"
"$PY" check_intersections.py

# 6. identity pack + similarity scorer
"$PY" build_identity.py
"$PY" face_similarity.py --build-ref
if [ "${1:-}" != "--no-calib" ]; then
  mkdir -p "$OUT/calib/tpdne"
  [ -s "$OUT/calib/lfw-funneled.tgz" ] || curl -sSL -o "$OUT/calib/lfw-funneled.tgz" https://ndownloader.figshare.com/files/5976018
  for i in $(seq 1 160); do f="$OUT/calib/tpdne/tp_$i.jpg"; [ -s "$f" ] || { curl -sS -A "Mozilla/5.0" -o "$f" "https://thispersondoesnotexist.com/random-person.jpeg?$i"; sleep 1.2; }; done
  "$PY" face_similarity.py --calibrate
fi
echo "done: $OUT/subject.glb"
