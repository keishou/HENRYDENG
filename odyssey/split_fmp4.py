"""Split a fragmented MP4 into parts of at most LIMIT bytes, cut on fragment
boundaries, so a MediaSource player can append them one after another.

usage: python3 split_fmp4.py in_frag.mp4 OUT_DIR [limit_mb]
prints the {mime, parts} manifest the viewing page embeds.
"""
import json
import struct
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
limit = int(float(sys.argv[3]) * 1e6) if len(sys.argv) > 3 else 14_000_000
data = src.read_bytes()
out.mkdir(parents=True, exist_ok=True)

boxes, i = [], 0
while i < len(data):
    size, kind = struct.unpack(">I4s", data[i:i + 8])
    if size == 1:
        size = struct.unpack(">Q", data[i + 8:i + 16])[0]
    boxes.append((kind.decode("latin1"), i, i + size))
    i += size

init_end = next(e for k, s, e in boxes if k == "moov")
avcc = data.find(b"avcC", 0, init_end)
profile, compat, level = data[avcc + 5], data[avcc + 6], data[avcc + 7]
mime = f'video/mp4; codecs="avc1.{profile:02x}{compat:02x}{level:02x}, mp4a.40.2"'

# group moof+mdat pairs (plus anything trailing, e.g. mfra) into parts
chunks, cur_start = [], 0
frag_ends = [e for k, s, e in boxes if k == "mdat"]
last = 0
for e in frag_ends + [len(data)]:
    if e - cur_start > limit and last > cur_start:
        chunks.append((cur_start, last)); cur_start = last
    last = e
chunks.append((cur_start, len(data)))

parts = []
for n, (a, b) in enumerate(chunks):
    name = f"hd_{n:02d}.mp4"
    (out / name).write_bytes(data[a:b])
    parts.append(f"film/{name}")
    print(f"{name}: {(b - a) / 1e6:.1f} MB", file=sys.stderr)
print(json.dumps({"mime": mime, "parts": parts}))
