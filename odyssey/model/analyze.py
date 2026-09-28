"""Stage 1 — read the photo: landmarks, semantic parts, monocular depth.

Input : photo_rect.png  (rectified 1024x1024 passport photo)
Output: analysis.npz    (landmarks, class map, disparity) + debug PNGs
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

WORK = Path(sys.argv[1])
MODELS = Path(sys.argv[2])

bgr = cv2.imread(str(WORK / "photo_rect.png"))
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
H, W = rgb.shape[:2]

# ---------------------------------------------------------------- landmarks
fl = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=mpt.BaseOptions(model_asset_path=str(MODELS / "face_landmarker.task")),
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=1))
res = fl.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
lm = np.array([[p.x * W, p.y * H, p.z * W] for p in res.face_landmarks[0]], np.float32)
face_mat = np.array(res.facial_transformation_matrixes[0], np.float32)
blend = {b.category_name: b.score for b in res.face_blendshapes[0]}
fl.close()
print("landmarks", lm.shape, "z range", lm[:, 2].min(), lm[:, 2].max())

# ---------------------------------------------------------------- parts
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=mpt.BaseOptions(model_asset_path=str(MODELS / "selfie_multiclass.tflite")),
    output_category_mask=True, output_confidence_masks=True))
sres = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
conf = np.stack([np.squeeze(m.numpy_view()) for m in sres.confidence_masks], -1)  # H,W,6
seg.close()
cls = conf.argmax(-1).astype(np.uint8)  # 0 bg 1 hair 2 body-skin 3 face-skin 4 clothes 5 other
print("class histogram", np.bincount(cls.ravel(), minlength=6))

# ---------------------------------------------------------------- depth
sess = ort.InferenceSession(str(MODELS / "depth_anything_v2_vits.onnx"),
                            providers=["CPUExecutionProvider"])
x = cv2.resize(rgb, (518, 518), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
x = x.transpose(2, 0, 1)[None].astype(np.float32)
disp = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]
# flip-averaged pass reduces the model's left/right bias
disp_f = sess.run(None, {sess.get_inputs()[0].name: x[..., ::-1].copy()})[0][0][:, ::-1]
disp = 0.5 * (disp + disp_f)
disp = cv2.resize(disp, (W, H), interpolation=cv2.INTER_CUBIC)
print("disparity range", disp.min(), disp.max())

np.savez_compressed(WORK / "analysis.npz", lm=lm, face_mat=face_mat, cls=cls,
                    conf=conf.astype(np.float16), disp=disp.astype(np.float32))

# ---------------------------------------------------------------- debug views
dbg = bgr.copy()
for x_, y_, _ in lm:
    cv2.circle(dbg, (int(x_), int(y_)), 1, (0, 255, 255), -1)
palette = np.array([[0, 0, 0], [40, 40, 220], [80, 200, 240], [120, 200, 120],
                    [200, 80, 40], [200, 0, 200]], np.uint8)
d8 = cv2.normalize(disp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
row = np.hstack([dbg, cv2.addWeighted(bgr, 0.4, palette[cls], 0.6, 0),
                 cv2.applyColorMap(d8, cv2.COLORMAP_INFERNO)])
cv2.imwrite(str(WORK / "debug_analysis.jpg"), cv2.resize(row, (1536, 512)))
