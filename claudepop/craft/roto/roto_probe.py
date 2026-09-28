"""Rotoscope-assist probe: times MediaPipe Tasks (pose, face, multiclass segmentation) + OpenCV line extraction
on a frame upscaled to 1920x1080, CPU only. Emits the kind of per-frame JSON the JS renderer would consume.
    python3 roto_probe.py <image> <models_dir> [out.json]
Plates in production: ffmpeg -i plate.mp4 -vf fps=24 frames/%05d.png, then run this per frame in VIDEO mode
(detect_for_video with monotonically increasing timestamps) so the tracker smooths between frames.
"""
import sys, time, json
import numpy as np, cv2, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision as V

img_path, models = sys.argv[1], sys.argv[2]
out_json = sys.argv[3] if len(sys.argv) > 3 else None
bgr = cv2.imread(img_path)
h0, w0 = bgr.shape[:2]; s = min(1920 / w0, 1080 / h0)
frame = np.full((1080, 1920, 3), 235, np.uint8)
r = cv2.resize(bgr, (int(w0 * s), int(h0 * s)), interpolation=cv2.INTER_CUBIC)
frame[:r.shape[0], :r.shape[1]] = r
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
mpimg = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
T = {}
def timed(name, fn, n=3):
    fn(); t = time.perf_counter()
    for _ in range(n): res = fn()
    T[name] = round((time.perf_counter() - t) / n * 1000, 1); return res

pose = V.PoseLandmarker.create_from_options(V.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=f"{models}/pose_landmarker_full.task"),
        num_poses=4, output_segmentation_masks=True))
pr = timed('pose_full_4people_ms', lambda: pose.detect(mpimg))
face = V.FaceLandmarker.create_from_options(V.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=f"{models}/face_landmarker.task"),
        output_face_blendshapes=True, num_faces=2))
fr = timed('face_478pts_blendshapes_ms', lambda: face.detect(mpimg))
seg = V.ImageSegmenter.create_from_options(V.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path=f"{models}/selfie_multiclass_256x256.tflite"),
        output_category_mask=True))
sr = timed('segment_multiclass_ms', lambda: seg.segment(mpimg))

# classical line extraction for "trace the plate" strokes: bilateral -> Canny -> contours -> Douglas-Peucker polylines
def lines():
    g = cv2.cvtColor(cv2.bilateralFilter(frame, 9, 60, 60), cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 60, 140)
    cs, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    return [cv2.approxPolyDP(c, 1.5, False).reshape(-1, 2).tolist() for c in cs if cv2.arcLength(c, False) > 40]
polys = timed('canny_contours_dp_ms', lines)
# region outlines from the segmentation mask (hair / face-skin / body-skin / clothes) -> fill shapes
def regions():
    m = sr.category_mask.numpy_view(); out = {}
    for k, name in enumerate(['background', 'hair', 'body_skin', 'face_skin', 'clothes', 'others']):
        if k == 0: continue
        cs, _ = cv2.findContours((m == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out[name] = [cv2.approxPolyDP(c, 2.0, True).reshape(-1, 2).tolist() for c in cs if cv2.contourArea(c) > 400]
    return out
reg = timed('mask_regions_ms', regions)

res = {'timing_ms': T, 'n_people': len(pr.pose_landmarks), 'n_faces': len(fr.face_landmarks), 'n_line_polys': len(polys),
       'n_line_points': int(sum(len(p) for p in polys)), 'regions': {k: len(v) for k, v in reg.items()}}
if fr.face_blendshapes:
    bs = {c.category_name: round(c.score, 3) for c in fr.face_blendshapes[0]}
    res['mouth_blendshapes_sample'] = {k: bs[k] for k in ['jawOpen', 'mouthFunnel', 'mouthPucker', 'mouthSmileLeft', 'eyeBlinkLeft'] if k in bs}
print(json.dumps(res, indent=1))
if out_json:
    json.dump({'pose': [[(round(l.x, 4), round(l.y, 4), round(l.z, 4), round(l.visibility, 3)) for l in p] for p in pr.pose_landmarks],
               'face': [[(round(l.x, 4), round(l.y, 4)) for l in f] for f in fr.face_landmarks], 'lines': polys[:400], 'regions': reg}, open(out_json, 'w'))
