#!/usr/bin/env python3
"""Chat-delivery test (BIBLE 9.10 delivery A; lane A): encode a stretch of rendered frames at the chat bitrate at 1080p
and at 720p (lanczos from the same 1080p frames), then compare frame grabs with the source frames.

    claudepop/out/venv/bin/python claudepop/film/tools/delivery_test.py --shots S01,S04 [--res 1080] [--kbps 1380]
        [--grabs 6,27,49,68,100,126,141,245,257,262,300] [--name s01s04]

The shots' frames (out/film/frames/<res>/) are joined in film order into one sequence (a gap between shots is simply
skipped), encoded exactly like encode.sh's chat delivery (two-pass x264 -preset slow, -b:v <kbps>k, maxrate 2400k,
bufsize 4800k, GOP 48, yuv420p) with the original MP3 stream copied for the same duration (the size accounting of the
real delivery; its sync is irrelevant here), once at the frames' size and once scaled to 1280x720 (lanczos).
Per grab frame (film frame numbers): SSIM / PSNR of each encode against the source (a) at 1920x1080 (720p upscaled
with lanczos, as a player does full screen) and (b) at 1170x658 (a phone's physical pixels for the 390 pt feed player),
plus a crop sheet source | 1080p | 720p of the window centre (the face) and of a flat mid-tone patch, at 1:1.
Writes out/film/deliver/test_<name>/ (both mp4s, grabs, crops_*.jpg, report.json).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))
MP3 = '/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3'


def ffmpeg():
    if os.environ.get('FFMPEG'):
        return os.environ['FFMPEG']
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def run(cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def grab(ff, mp4, idx, out):
    # frame-exact grab by index (select filter), decoded to RGB PNG
    run([ff, '-y', '-v', 'error', '-i', mp4, '-vf', f'select=eq(n\\,{idx})', '-vsync', '0', '-frames:v', '1', out])


def ssim_psnr(a, b):
    """Luma SSIM (8x8 windows, Gaussian-free box version) and PSNR of two same-size RGB uint8 arrays."""
    def y(im):
        x = im.astype(np.float64)
        return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    A, B = y(a), y(b)
    mse = float(((A - B) ** 2).mean())
    psnr = 99.0 if mse < 1e-9 else 10 * np.log10(255 ** 2 / mse)
    k = 8
    h, w = (A.shape[0] // k) * k, (A.shape[1] // k) * k
    A, B = A[:h, :w].reshape(h // k, k, w // k, k), B[:h, :w].reshape(h // k, k, w // k, k)
    ma, mb = A.mean((1, 3)), B.mean((1, 3))
    va, vb = A.var((1, 3)), B.var((1, 3))
    cov = ((A - ma[:, None, :, None]) * (B - mb[:, None, :, None])).mean((1, 3))
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    s = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
    return float(s.mean()), float(psnr)


def detail_energy(im):
    """Mean absolute Laplacian of luma: how much fine texture (halftone, grain, paper tooth) survives."""
    x = im.astype(np.float64)
    Y = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    lap = 4 * Y[1:-1, 1:-1] - Y[:-2, 1:-1] - Y[2:, 1:-1] - Y[1:-1, :-2] - Y[1:-1, 2:]
    return float(np.abs(lap).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', default='S01,S04')
    ap.add_argument('--res', type=int, default=1080)
    ap.add_argument('--kbps', type=int, default=1380)
    ap.add_argument('--grabs', default='6,27,49,68,100,126,141,245,257,262,300')
    ap.add_argument('--name', default=None)
    ap.add_argument('--crop', default=None, help='x,y,w,h of the face crop in 1920x1080 px (default: window centre)')
    a = ap.parse_args()
    ff = ffmpeg()
    doc = json.load(open(os.path.join(CP, 'shots.json')))
    want = a.shots.split(',')
    shots = [s for s in doc['shots'] if s['id'] in want]
    frames = [f for s in shots for f in range(s['frames'][0], s['frames'][1])]
    src_dir = os.path.join(CP, 'out/film/frames', str(a.res))
    miss = [f for f in frames if not os.path.exists(os.path.join(src_dir, f'{f:05d}.jpg'))]
    if miss:
        sys.exit(f'{len(miss)} frames missing in {src_dir} (first {miss[:8]}): render them first')
    name = a.name or ''.join(s['id'].lower() for s in shots)
    out = os.path.join(CP, 'out/film/deliver', f'test_{name}')
    os.makedirs(out, exist_ok=True)
    dur = len(frames) / doc['fps']
    tmp = tempfile.mkdtemp()
    try:
        for i, f in enumerate(frames):
            os.symlink(os.path.join(src_dir, f'{f:05d}.jpg'), os.path.join(tmp, f'{i:05d}.jpg'))
        res = {}
        for tag, scale in (('1080', None), ('720', '1280:720')):
            mp4 = os.path.join(out, f'chat_{tag}.mp4')
            vf = ['-vf', f'scale={scale}:flags=lanczos'] if scale else []
            cv = ['-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{a.kbps}k', '-maxrate', '2400k', '-bufsize', '4800k', '-g', '48', '-pix_fmt', 'yuv420p'] + vf
            inp = ['-framerate', str(doc['fps']), '-i', os.path.join(tmp, '%05d.jpg')]
            run([ff, '-y', '-v', 'error'] + inp + ['-frames:v', str(len(frames))] + cv + ['-pass', '1', '-an', '-f', 'mp4', os.devnull], cwd=tmp)
            run([ff, '-y', '-v', 'error'] + inp + ['-t', f'{dur:.4f}', '-i', MP3, '-map', '0:v:0', '-map', '1:a:0', '-frames:v', str(len(frames))]
                + cv + ['-pass', '2', '-c:a', 'copy', '-movflags', '+faststart', mp4], cwd=tmp)
            size = os.path.getsize(mp4)
            res[tag] = {'file': mp4, 'bytes': size, 'total_kbps': round(size * 8 / dur / 1000, 1)}
        grabs = [int(x) for x in a.grabs.split(',') if int(x) in frames]
        rows = []
        font = ImageFont.load_default()
        crops = []
        for f in grabs:
            idx = frames.index(f)
            src = np.asarray(Image.open(os.path.join(src_dir, f'{f:05d}.jpg')).convert('RGB'))
            H, W = src.shape[:2]
            row = {'frame': f}
            ims = {'source': src}
            for tag in ('1080', '720'):
                png = os.path.join(out, f'grab_{tag}_{f:05d}.png')
                grab(ff, res[tag]['file'], idx, png)
                im = Image.open(png).convert('RGB')
                full = np.asarray(im.resize((W, H), Image.LANCZOS)) if im.size != (W, H) else np.asarray(im)
                ims[tag] = full
                s_full, p_full = ssim_psnr(src, full)
                phone = (1170, 658)
                s_ph, p_ph = ssim_psnr(np.asarray(Image.fromarray(src).resize(phone, Image.LANCZOS)), np.asarray(Image.fromarray(full).resize(phone, Image.LANCZOS)))
                row[tag] = {'ssim_1080': round(s_full, 4), 'psnr_1080': round(p_full, 2), 'ssim_phone': round(s_ph, 4), 'psnr_phone': round(p_ph, 2)}
            # detail kept in the window centre (the face / print)
            cx, cy, cw, ch = [int(v) for v in a.crop.split(',')] if a.crop else (W // 2 - 210 * W // 1920, H // 2 - 180 * H // 1080, 420 * W // 1920, 360 * H // 1080)
            for tag in ('source', '1080', '720'):
                row.setdefault('detail', {})[tag] = round(detail_energy(ims[tag][cy:cy + ch, cx:cx + cw]), 2)
            crops.append((f, [Image.fromarray(ims[t][cy:cy + ch, cx:cx + cw]) for t in ('source', '1080', '720')]))
            rows.append(row)
        # crop sheet: rows of source | 1080p | 720p (the 720p upscaled back to 1080 lanczos), 1:1 at the source size
        cw_, ch_ = crops[0][1][0].size
        sheet = Image.new('RGB', (3 * cw_ + 40, len(crops) * (ch_ + 26) + 30), (18, 18, 18))
        d = ImageDraw.Draw(sheet)
        d.text((10, 8), f'source | chat 1080p {res["1080"]["total_kbps"]} kb/s | chat 720p {res["720"]["total_kbps"]} kb/s (upscaled lanczos)  1:1 crops', fill=(230, 230, 225), font=font)
        for i, (f, ims3) in enumerate(crops):
            y = 30 + i * (ch_ + 26)
            for j, im in enumerate(ims3):
                sheet.paste(im, (10 + j * (cw_ + 10), y))
            d.text((10, y + ch_ + 6), f'F{f}', fill=(200, 200, 195), font=font)
        sheet_path = os.path.join(out, 'crops.jpg')
        sheet.save(sheet_path, quality=92)
        mean = lambda tag, k: round(float(np.mean([r[tag][k] for r in rows])), 4)
        summary = {tag: {k: mean(tag, k) for k in ('ssim_1080', 'psnr_1080', 'ssim_phone', 'psnr_phone')} for tag in ('1080', '720')}
        report = {'shots': want, 'frames': len(frames), 'seconds': round(dur, 3), 'kbps': a.kbps, 'encodes': res, 'grabs': rows, 'mean': summary, 'crops': sheet_path}
        json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1)
        for tag in ('1080', '720'):
            print(f'chat {tag}p: {res[tag]["bytes"] / 1048576:.2f} MiB ({res[tag]["total_kbps"]} kb/s incl. audio)  mean SSIM full {summary[tag]["ssim_1080"]} '
                  f'PSNR {summary[tag]["psnr_1080"]} dB | phone SSIM {summary[tag]["ssim_phone"]} PSNR {summary[tag]["psnr_phone"]} dB')
        for r in rows:
            print(f'  F{r["frame"]:<4} 1080p ssim {r["1080"]["ssim_1080"]:.4f}/{r["1080"]["ssim_phone"]:.4f}  720p ssim {r["720"]["ssim_1080"]:.4f}/{r["720"]["ssim_phone"]:.4f}'
                  f'  detail src {r["detail"]["source"]} 1080p {r["detail"]["1080"]} 720p {r["detail"]["720"]}')
        print(f'crops: {sheet_path}\nreport: {os.path.join(out, "report.json")}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
