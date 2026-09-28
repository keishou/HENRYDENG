# Rough protagonist screen-coverage metric: share of pixels close to Clawd's body colour (PAL.clay #D97757 after paper multiply),
# plus the karaoke-bar share. Heuristic (wood floors / warm skies can leak in); used only for order-of-magnitude claims.
import cv2, numpy as np, glob, os, json
rows = []
for f in sorted(glob.glob('frames/*.png') + glob.glob('frames_extra/*.png'), key=lambda p: float(os.path.basename(p)[1:-4].replace('_', '.'))):
    im = cv2.imread(f)[:, :, ::-1].astype(np.int32)  # RGB
    ref = np.array([205, 112, 82])                    # clay after ~6% multiply darkening
    d = np.sqrt(((im - ref) ** 2).sum(-1))
    m = (d < 34).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    biggest = stats[1:, cv2.CC_STAT_AREA].max() / m.size if n > 1 else 0
    hmax = stats[1:, cv2.CC_STAT_HEIGHT][stats[1:, cv2.CC_STAT_AREA].argmax()] / m.shape[0] if n > 1 else 0
    rows.append(dict(t=float(os.path.basename(f)[1:-4].replace('_', '.')), clay_px=round(float(m.mean()), 4), biggest_blob=round(float(biggest), 4), biggest_blob_h=round(float(hmax), 3)))
json.dump(rows, open('tools/coverage.json', 'w'), indent=0)
a = np.array([r['biggest_blob'] for r in rows]); h = np.array([r['biggest_blob_h'] for r in rows])
print('frames', len(rows), 'median biggest clay blob area %.3f, median height %.3f; frames with blob height > .35: %d' % (np.median(a), np.median(h), (h > .35).sum()))
for r in rows: print(r)
