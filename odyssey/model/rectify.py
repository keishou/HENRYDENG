"""Stage 0 — cut the pasted photo out of the passport page and square it up.

usage: python3 rectify.py page.jpg WORK_DIR "x,y x,y x,y x,y"
corners in page pixels: top-left, top-right, bottom-right, bottom-left of the photo.
Only the photo itself is kept; the page's handwriting and printed fields are discarded.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

page, work, corners = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
work.mkdir(parents=True, exist_ok=True)
src = np.float32([[float(v) for v in c.split(",")] for c in corners.split()])
N = 1024
M = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [N, 0], [N, N], [0, N]]))
img = cv2.imread(page)
cv2.imwrite(str(work / "photo_rect.png"), cv2.warpPerspective(img, M, (N, N), flags=cv2.INTER_CUBIC,
                                                               borderMode=cv2.BORDER_REPLICATE))
