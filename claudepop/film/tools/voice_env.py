#!/usr/bin/env python3
"""Vocal envelope for the film (BIBLE 2.1: the voice is the light) -> claudepop/out/film/data/voice_env.json (+ .png plot).

    claudepop/out/venv/bin/python claudepop/film/tools/voice_env.py [--stem PATH] [--mp3 PATH]

Method
  1. The Demucs vocal stem (out/audio/stems/htdemucs/pdoom_44k/vocals.wav) is checked against the gapless decode of
     pdoom.mp3 (the song.json clock): the sum of the four stems is cross-correlated with the mix; the lag is reported and
     removed, so envelope time == song time.
  2. RMS of the mono vocal stem in 20 ms windows every 10 ms -> dBFS.
  3. Level = clip((dB - floor) / (ceil - floor), 0, 1); floor -38 dBFS (5th percentile inside sung words: the stem
     carries ad-libs and reverb, so a lower floor saturates), ceil = the 99th percentile of the frames above the floor.
  4. One-pole follower on the level at 100 Hz: attack time constant 50 ms, release 1.5 s.
Output: { rate: 100, t0: 0, values: [...] (0..1, 4 decimals), frames24: [...] (the value at every film frame f / 24), ... }
Consumers: src/core/timeline.js env(t) (linear interpolation), the safelight (base * (0.55 + 0.45 * env)), the enlarger
lamp and the development rate. Text only; contains no face data.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(CP, 'out', 'film', 'data')
STEMS = os.path.join(CP, 'out', 'audio', 'stems', 'htdemucs', 'pdoom_44k')
MP3 = '/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3'
RATE = 100
ATTACK, RELEASE, FLOOR_DB = 0.05, 1.5, -38.0   # floor: the 5th percentile of the stem inside sung words (the stem is rarely silent)


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def decode(path, sr):
    raw = subprocess.run([ffmpeg(), '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def read_wav(path):
    import soundfile as sf
    x, sr = sf.read(path, always_2d=True)
    return x.mean(1), sr


def xcorr_lag(a, b, sr, max_ms=200):
    """lag (s) that best aligns b to a (positive: b is late)."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    A, B = np.fft.rfft(a, n), np.fft.rfft(b, n)
    c = np.fft.irfft(A.conj() * B, n)
    m = int(sr * max_ms / 1000)
    c = np.concatenate([c[-m:], c[:m + 1]])
    k = int(np.argmax(c)) - m
    if 0 < k + m < len(c) - 1:                         # parabolic sub-sample refinement
        y0, y1, y2 = c[k + m - 1], c[k + m], c[k + m + 1]
        k = k + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    return k / sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stem', default=os.path.join(STEMS, 'vocals.wav'))
    ap.add_argument('--mp3', default=MP3)
    a = ap.parse_args()
    voc, sr = read_wav(a.stem)
    # 1. alignment of the stems to the gapless decode (window 20-60 s: drums + vocals)
    mix = decode(a.mp3, sr)
    stems = voc.copy()
    for s in ('drums', 'bass', 'other'):
        p = os.path.join(STEMS, s + '.wav')
        if os.path.exists(p):
            x, _ = read_wav(p)
            stems[:min(len(stems), len(x))] += x[:min(len(stems), len(x))]
    w0, w1 = 20 * sr, 60 * sr
    lag = xcorr_lag(mix[w0:w1], stems[w0:w1], sr)
    shift = int(round(lag * sr))
    if shift > 0:
        voc = voc[shift:]
    elif shift < 0:
        voc = np.concatenate([np.zeros(-shift), voc])
    # 2. RMS 20 ms / hop 10 ms (window centred on t)
    dur = len(mix) / sr
    n = int(np.ceil(dur * RATE)) + 1
    win, hop = int(0.02 * sr), sr / RATE
    pad = np.concatenate([np.zeros(win), voc, np.zeros(win * 2)])
    idx = (np.arange(n) * hop).astype(int) + win - win // 2
    sq = np.concatenate([[0.0], np.cumsum(pad ** 2)])
    rms = np.sqrt(np.maximum(0, (sq[idx + win] - sq[idx]) / win))
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    voiced = db[db > FLOOR_DB]
    ceil = float(np.percentile(voiced, 99)) if len(voiced) else -10.0
    level = np.clip((db - FLOOR_DB) / (ceil - FLOOR_DB), 0, 1)
    # 4. follower
    ka, kr = 1 - np.exp(-1 / (RATE * ATTACK)), 1 - np.exp(-1 / (RATE * RELEASE))
    env = np.zeros(n)
    y = 0.0
    for i in range(n):
        x = level[i]
        y += (x - y) * (ka if x > y else kr)
        env[i] = y
    frames = int(round(dur * 24))
    f24 = np.interp(np.arange(frames) / 24, np.arange(n) / RATE, env)
    os.makedirs(OUT, exist_ok=True)
    doc = {
        '_about': 'Vocal envelope (Demucs vocal stem; 20 ms RMS; level = clip((dB - floor) / (ceil - floor)); one-pole follower, '
                  'attack 50 ms, release 1.5 s). Time = song.json clock (gapless decode). Built by film/tools/voice_env.py.',
        'source': os.path.relpath(a.stem, CP), 'rate': RATE, 't0': 0.0, 'attack_s': ATTACK, 'release_s': RELEASE,
        'floor_db': FLOOR_DB, 'ceil_db': round(ceil, 2), 'stem_lag_ms': round(lag * 1000, 2), 'duration': round(dur, 4),
        'n': n, 'values': [round(float(v), 4) for v in env], 'frames24': [round(float(v), 4) for v in f24],
    }
    path = os.path.join(OUT, 'voice_env.json')
    with open(path, 'w') as f:
        json.dump(doc, f, separators=(',', ':'))
    print(f'{path}: {n} values at {RATE} Hz, stem lag {lag * 1000:+.2f} ms (removed), ceil {ceil:.1f} dBFS, '
          f'mean {env.mean():.3f}, frac > 0.5 {np.mean(env > 0.5):.2f}')
    plot(env, path.replace('.json', '.png'), dur)


def plot(env, path, dur):
    """A 3000 x 360 strip: the envelope over the song, lyric line spans, section starts (review with the Read tool)."""
    from PIL import Image, ImageDraw
    song = json.load(open(os.path.join(CP, 'analysis', 'song.json')))
    W, H, top, bot = 3000, 360, 30, 300
    im = Image.new('RGB', (W, H), (10, 10, 9))
    d = ImageDraw.Draw(im)
    X = lambda t: int(t / dur * (W - 1))
    for l in song['lines']:
        d.rectangle([X(l['start']), bot + 12, X(l['end']), bot + 22], fill=(90, 90, 88))
    for s in song['sections']:
        d.line([X(s['t0']), top, X(s['t0']), bot], fill=(60, 60, 60))
        d.text((X(s['t0']) + 3, 6), s['name'], fill=(160, 160, 155))
    for t in range(0, int(dur) + 1, 10):
        d.text((X(t) + 2, bot + 30), f'{t}s', fill=(120, 120, 115))
    pts = [(X(i / RATE), bot - int(v * (bot - top))) for i, v in enumerate(env)]
    d.line(pts, fill=(250, 249, 245), width=2)
    im.save(path)
    print(path)


if __name__ == '__main__':
    sys.exit(main())
