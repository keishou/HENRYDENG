#!/usr/bin/env bash
# Fetch the third-party models and fonts (not stored in git) and install dependencies.
set -euo pipefail
cd "$(dirname "$0")"
MODELS=${MODELS:-.cache/models}; mkdir -p "$MODELS" film/assets/fonts
pip install numpy scipy pillow opencv-python-headless mediapipe onnxruntime trimesh soundfile imageio-ffmpeg
get() { [ -s "$2" ] || curl -sSL -o "$2" "$1"; }
get https://github.com/fabio-sim/Depth-Anything-ONNX/releases/download/v2.0.0/depth_anything_v2_vits.onnx "$MODELS/depth_anything_v2_vits.onnx"
get https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task "$MODELS/face_landmarker.task"
get https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite "$MODELS/selfie_multiclass.tflite"
get https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj "$MODELS/canonical_face_model.obj"
F=https://raw.githubusercontent.com/google/fonts/main/ofl
get "$F/shipporimincho/ShipporiMincho-Regular.ttf" film/assets/fonts/ShipporiMincho-Regular.ttf
get "$F/shipporimincho/ShipporiMincho-Bold.ttf" film/assets/fonts/ShipporiMincho-Bold.ttf
get "$F/ebgaramond/EBGaramond%5Bwght%5D.ttf" "film/assets/fonts/EBGaramond[wght].ttf"
get "$F/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf" "film/assets/fonts/EBGaramond-Italic[wght].ttf"
get "$F/jost/Jost%5Bwght%5D.ttf" "film/assets/fonts/Jost[wght].ttf"
(cd film && npm install --no-audit --no-fund)
echo "ready"
