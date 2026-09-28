#!/usr/bin/env python3
"""A/V offset of an encoded film file against the song clock (BIBLE 9.10). Pass = |offset| <= 5 ms.

    claudepop/out/venv/bin/python claudepop/film/tools/av_offset.py FILE.mp4 [--ref pdoom.mp3] [--start 0] [--tol 5]

song.json times are on the gapless decode of pdoom.mp3 (the LAME header's 1105 priming samples skipped). A player shows
video frame f at f / 24 on the file's timeline, relative to the first video frame, and plays the audio samples at their
own timestamps. So the offset of a picture event at song time T is:
    offset = (time on the file timeline at which song time T is heard) - (time at which frame round(T * 24) is shown)
           = xcorr lag of the decoded audio (from its first sample) vs the gapless reference
             + first audio sample time - first video frame time       (both read with -copyts, edit lists applied)
Positive offset = the sound comes late. --start: song time of the file's first frame (for segments; default 0).
The two decodes are cross-correlated over three windows (onsets, 48 kHz mono); they must agree within 1 ms.
Prints JSON; exit 1 when out of tolerance. If a container plays the priming (about +23 ms), re-mux with the video
delayed: ffmpeg -itsoffset 0.023 -i video ... -c copy (encode.sh does this automatically).
"""
import argparse
import json
import re
import subprocess
import sys

import numpy as np

SR = 48000
MP3 = '/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3'


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def decode(path, extra=()):
    raw = subprocess.run([ffmpeg(), '-v', 'error', *extra, '-i', path, '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def first_pts(path, sel):
    """time (s) of the first packet of stream sel ('v:0' / 'a:0') on the file timeline, and the audio skip samples."""
    p = subprocess.run([ffmpeg(), '-v', 'error', '-copyts', '-i', path, '-map', f'0:{sel}', '-c', 'copy', '-frames:' + sel[0], '8',
                        '-f', 'framecrc', '-'], check=True, capture_output=True, text=True).stdout
    tb = re.search(r'#tb 0: (\d+)/(\d+)', p)
    num, den = int(tb.group(1)), int(tb.group(2))
    pts = [int(l.split(',')[2]) for l in p.splitlines() if l and not l.startswith('#')]
    return min(pts) * num / den


def decoded_start(path):
    """file-timeline time of the first DECODED audio sample (after skip-samples / edit lists): first pts from a decode."""
    p = subprocess.run([ffmpeg(), '-v', 'error', '-copyts', '-i', path, '-map', '0:a:0', '-frames:a', '1', '-f', 'framecrc', '-'],
                       check=True, capture_output=True, text=True).stdout
    tb = re.search(r'#tb 0: (\d+)/(\d+)', p)
    num, den = int(tb.group(1)), int(tb.group(2))
    pts = [int(l.split(',')[2]) for l in p.splitlines() if l and not l.startswith('#')]
    return pts[0] * num / den


def lag(ref, x, a, b, max_ms=150):
    """seconds by which x is late relative to ref over the song window [a, b) (x indexed from its own first sample)."""
    i0, i1 = int(a * SR), int(b * SR)
    r = ref[i0:i1]
    m = int(max_ms / 1000 * SR)
    seg = x[max(0, i0 - m):i1 + m]
    off0 = max(0, i0 - m) - i0
    n = 1 << int(np.ceil(np.log2(len(r) + len(seg))))
    c = np.fft.irfft(np.fft.rfft(seg, n) * np.conj(np.fft.rfft(r, n)), n)
    # c[k] = sum seg[j + k] r[j] -> x is late by (k + off0)
    ks = np.arange(-m, m + 1) - off0
    vals = c[ks % n]
    k = int(np.argmax(vals))
    fine = 0.0
    if 0 < k < len(vals) - 1:
        y0, y1, y2 = vals[k - 1], vals[k], vals[k + 1]
        fine = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    return (ks[k] + off0 + fine) / SR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--ref', default=MP3)
    ap.add_argument('--start', type=float, default=0.0, help='song time of the first frame of the file')
    ap.add_argument('--tol', type=float, default=5.0)
    a = ap.parse_args()
    ref = decode(a.ref)                                # the gapless decode (ffmpeg honours the LAME header)
    x = decode(a.file)
    v0 = first_pts(a.file, 'v:0')
    a0 = decoded_start(a.file)
    dur = len(x) / SR
    wins = [w for w in [(17.0, 22.0), (60.0, 65.0), (111.0, 116.0), (2.0, 7.0)] if w[0] >= a.start and w[1] <= a.start + dur - 0.5]
    if not wins:
        wins = [(a.start + 0.5, a.start + min(dur - 0.5, 6.0))]
    lags = []
    for w0, w1 in wins[:3]:
        # x sample j corresponds to song time a.start + j/SR if aligned; shift the reference window accordingly
        lr = lag(ref[int(a.start * SR):], x, w0 - a.start, w1 - a.start)
        lags.append(lr)
    L = float(np.median(lags))
    offset = L + (a0 - v0)
    # informational: what a player that ignores MP4 edit lists would do (it plays the MP3 priming)
    try:
        xi = decode(a.file, ('-ignore_editlist', '1'))
        w0, w1 = wins[0]
        li = lag(ref[int(a.start * SR):], xi, w0 - a.start, w1 - a.start)
        ignored = round((li + (a0 - v0)) * 1000, 2)
    except Exception:
        ignored = None
    rep = {'file': a.file, 'offset_if_editlist_ignored_ms': ignored, 'xcorr_lag_ms': round(L * 1000, 2), 'lags_ms': [round(v * 1000, 2) for v in lags],
           'first_video_s': round(v0, 5), 'first_audio_decoded_s': round(a0, 5), 'offset_ms': round(offset * 1000, 2),
           'tolerance_ms': a.tol, 'pass': bool(abs(offset * 1000) <= a.tol and (max(lags) - min(lags)) * 1000 <= 1.0)}
    print(json.dumps(rep, indent=1))
    return 0 if rep['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
