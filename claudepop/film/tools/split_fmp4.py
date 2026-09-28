#!/usr/bin/env python3
"""Split a fragmented MP4 into parts of at most LIMIT MB, cut on fragment boundaries, for a MediaSource player
(BIBLE 9.10 delivery B; the odyssey/split_fmp4.py pattern, with the codec string read from the file so an MP3 audio
track (stream-copied pdoom.mp3) gets mp4a.6B instead of AAC's mp4a.40.2).

    python3 claudepop/film/tools/split_fmp4.py in_frag.mp4 OUT_DIR [limit_mb=15] [--prefix part]
Writes OUT_DIR/<prefix>_NN.mp4 and OUT_DIR/manifest.json = { mime, parts, bytes }; prints the manifest.
"""
import json
import struct
import sys
from pathlib import Path


def boxes(data, start=0, end=None):
    i, end = start, len(data) if end is None else end
    while i + 8 <= end:
        size, kind = struct.unpack('>I4s', data[i:i + 8])
        hdr = 8
        if size == 1:
            size, hdr = struct.unpack('>Q', data[i + 8:i + 16])[0], 16
        elif size == 0:
            size = end - i
        yield kind.decode('latin1'), i, i + size, hdr
        i += size


def codecs(data, moov):
    k, s, e, h = moov
    out = []
    avcc = data.find(b'avcC', s, e)
    if avcc > 0:
        p, c, l = data[avcc + 5], data[avcc + 6], data[avcc + 7]
        out.append(f'avc1.{p:02x}{c:02x}{l:02x}')
    mp4a = data.find(b'mp4a', s, e)
    if mp4a > 0:
        esds = data.find(b'esds', mp4a, e)
        dcd = data.find(b'\x04', esds + 12, esds + 40)   # DecoderConfigDescriptor tag; objectTypeIndication follows the size
        j = dcd + 1
        while data[j] & 0x80:
            j += 1
        oti = data[j + 1]
        out.append('mp4a.40.2' if oti == 0x40 else f'mp4a.{oti:02X}')
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    prefix = sys.argv[sys.argv.index('--prefix') + 1] if '--prefix' in sys.argv else 'part'
    if '--prefix' in sys.argv:
        a.remove(prefix)
    src, out = Path(a[0]), Path(a[1])
    limit = int(float(a[2]) * 1e6) if len(a) > 2 else 15_000_000
    data = src.read_bytes()
    out.mkdir(parents=True, exist_ok=True)
    top = list(boxes(data))
    moov = next(b for b in top if b[0] == 'moov')
    mime = f'video/mp4; codecs="{", ".join(codecs(data, moov))}"'
    chunks, cur, last = [], 0, 0
    for e in [b[2] for b in top if b[0] == 'mdat'] + [len(data)]:
        if e - cur > limit and last > cur:
            chunks.append((cur, last))
            cur = last
        last = e
    chunks.append((cur, len(data)))
    parts = []
    for n, (s, e) in enumerate(chunks):
        name = f'{prefix}_{n:02d}.mp4'
        (out / name).write_bytes(data[s:e])
        parts.append(name)
        print(f'{name}: {(e - s) / 1e6:.1f} MB', file=sys.stderr)
    man = {'mime': mime, 'parts': parts, 'bytes': len(data)}
    (out / 'manifest.json').write_text(json.dumps(man, indent=1))
    print(json.dumps(man))


if __name__ == '__main__':
    main()
