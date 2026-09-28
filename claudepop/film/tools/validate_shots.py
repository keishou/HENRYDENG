#!/usr/bin/env python3
"""Validate claudepop/shots.json against claudepop/analysis/song.json, and print the BIBLE timing table.

    python3 claudepop/film/tools/validate_shots.py            # checks; exit 1 on any error
    python3 claudepop/film/tools/validate_shots.py --table    # also print the markdown timing table (BIBLE section 13)
    python3 claudepop/film/tools/validate_shots.py --json     # machine-readable report

Checks
  1. schema: required top-level and per-shot keys; source in {GEN, 3D, TYPE}; GEN shots carry a complete gen block
  2. tiling: first t0 = 0, every t1 = next t0, last t1 = song duration; frame spans contiguous; frame total = round(duration*24)
  3. anchors: every cut lies on a song.json time (beat, 8th or 16th grid, word onset or letter part, line start, extra-vocal
     onset, event) within 6 ms
  4. beat_hits and internal_cuts lie inside their shot (frame-level)
  5. lyric coverage: the frame of every lyric line's start falls in a shot that lists the line
  6. the live-man rule: where HE moves on screen (he_live, live_span) the span lies inside sung-word spans
     (line start - 2 frames .. line end + 6 frames, gaps under 0.6 s merged); rule_break shots are reported, not failed
  7. GEN plate usage: the used span of the plate equals the shot (or its GEN part) within 1 frame, and duration covers it
Text only: the files contain no face data.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FPS = 24
TOL = 0.006

song = json.load(open(os.path.join(ROOT, 'analysis', 'song.json')))
doc = json.load(open(os.path.join(ROOT, 'shots.json')))
shots = doc['shots']
errors, warnings, notes = [], [], []


def err(m): errors.append(m)
def warn(m): warnings.append(m)


# ---------------------------------------------------------------------------------------------------- 1 schema
TOP = ['fps', 'width', 'height', 'aspect', 'duration', 'bpm', 't0', 'sections', 'shots']
SHOT = ['id', 'section', 't0', 't1', 'lyric_lines', 'text_mode', 'text_layout', 'description', 'environment', 'camera',
        'motion_clips', 'look', 'motifs', 'beat_hits', 'transition_in', 'transition_out', 'module', 'source']
GEN = ['keyframe_prompt', 'video_model', 'video_prompt', 'duration', 'refs', 'fallback']
for k in TOP:
    if k not in doc: err(f'top-level key missing: {k}')
if doc.get('fps') != FPS: err(f'fps {doc.get("fps")} != {FPS}')
if abs(doc.get('duration', 0) - song['duration']) > 1e-4: err('duration differs from song.json')
if abs(doc.get('bpm', 0) - song['bpm']) > 1e-6 or abs(doc.get('t0', 0) - song['t0']) > 1e-6: err('bpm / t0 differ from song.json')
ids = set()
for s in shots:
    for k in SHOT:
        if k not in s: err(f'{s.get("id")}: key missing: {k}')
    if s['id'] in ids: err(f'duplicate id {s["id"]}')
    ids.add(s['id'])
    if s['source'] not in ('GEN', '3D', 'TYPE'): err(f'{s["id"]}: bad source {s["source"]}')
    if s['source'] == 'GEN':
        g = s.get('gen') or {}
        for k in GEN:
            if k not in g: err(f'{s["id"]}: gen.{k} missing')
    elif 'gen' in s:
        err(f'{s["id"]}: gen block on a non-GEN shot (use gen_upgrade for optional plates)')
secnames = [x['name'] for x in song['sections']]
for s in shots:
    if s['section'] not in secnames: err(f'{s["id"]}: unknown section {s["section"]}')
    else:
        sec = song['sections'][secnames.index(s['section'])]
        if not (sec['t0'] - 1e-4 <= s['t0'] < sec['t1']): err(f'{s["id"]}: t0 {s["t0"]} outside its section {s["section"]}')

# ---------------------------------------------------------------------------------------------------- 2 tiling
fr = lambda t: int(round(t * FPS))
if abs(shots[0]['t0']) > 1e-9: err('first shot does not start at 0')
for a, b in zip(shots, shots[1:]):
    if abs(a['t1'] - b['t0']) > 1e-9: err(f'gap/overlap between {a["id"]} ({a["t1"]}) and {b["id"]} ({b["t0"]})')
if abs(shots[-1]['t1'] - song['duration']) > 1e-4: err(f'last t1 {shots[-1]["t1"]} != duration {song["duration"]}')
total = 0
for s in shots:
    f0, f1 = fr(s['t0']), fr(s['t1'])
    if s.get('frames') and s['frames'] != [f0, f1]: err(f'{s["id"]}: frames {s["frames"]} != {[f0, f1]}')
    if f1 <= f0: err(f'{s["id"]}: empty after frame rounding')
    if s['t1'] - s['t0'] < 0.4: warn(f'{s["id"]}: shorter than 0.4 s ({f1 - f0} frames)')
    total += f1 - f0
if total != fr(song['duration']): err(f'frame total {total} != {fr(song["duration"])}')

# ---------------------------------------------------------------------------------------------------- 3 anchors
anchors = []
T0, BP = song['t0'], song['beat_period']
for k in range(0, 4 * len(song['beats']) + 4):
    anchors.append((round(T0 + k * BP / 4, 4), '16th' if k % 2 else ('beat' if k % 4 == 0 else '8th')))
for l in song['lines']:
    anchors.append((l['start'], f'L{l["i"]} start'))
    for wd in l['words']:
        anchors.append((wd['t'], f'L{l["i"]} "{wd["w"]}"'))
        for p in wd.get('parts') or []:
            anchors.append((p, f'L{l["i"]} part of "{wd["w"]}"'))
for e in song['extra_vocals']:
    anchors.append((e['t'], f'extra vocal {e["kind"]}'))
    for wd in e.get('words', []):
        anchors.append((wd['t'], f'extra vocal "{wd["w"]}"'))
for e in song['events']:
    anchors.append((e['t'], f'event {e["type"]}'))
anchors.append((0.0, 'file start'))


def anchor_of(t):
    best = min(anchors, key=lambda a: abs(a[0] - t))
    return best if abs(best[0] - t) <= TOL else None


cut_anchor = {}
for s in shots:
    a = anchor_of(s['t0'])
    if not a: err(f'{s["id"]}: cut at {s["t0"]} is not on a song.json time')
    else: cut_anchor[s['id']] = a[1]
    for c in s.get('internal_cuts', []):
        if not anchor_of(c): err(f'{s["id"]}: internal cut {c} is not on a song.json time')

# ---------------------------------------------------------------------------------------------------- 4 hits inside shot
for s in shots:   # frame-level: a hit may be the sung onset a few ms before the cut if it falls on the shot's first frame
    for h in s['beat_hits'] + s.get('internal_cuts', []):
        if not (fr(s['t0']) <= fr(h) <= fr(s['t1'])): err(f'{s["id"]}: hit {h} outside frames {fr(s["t0"])}-{fr(s["t1"])}')

# ---------------------------------------------------------------------------------------------------- 5 lyric coverage
for l in song['lines']:
    owner = [s for s in shots if fr(s['t0']) <= fr(l['start']) < fr(s['t1'])]
    if not owner or l['i'] not in owner[0]['lyric_lines']:
        err(f'line {l["i"]} ("{l["text"]}") starts at {l["start"]} but the shot there does not list it')
listed = {i for s in shots for i in s['lyric_lines']}
missing = [l['i'] for l in song['lines'] if l['i'] not in listed]
if missing: err(f'lines never listed: {missing}')

# ---------------------------------------------------------------------------------------------------- 6 live-man rule
spans = sorted([l['start'] - 2 / FPS, l['end'] + 6 / FPS] for l in song['lines'])
merged = []
for a, b in spans:
    if merged and a - merged[-1][1] < 0.6: merged[-1][1] = max(merged[-1][1], b)
    else: merged.append([a, b])
for s in shots:
    if not s.get('he_live'): continue
    a, b = s.get('live_span') or [s['t0'], s['t1']]
    ok = any(m0 <= a + 1e-6 and b - 1e-6 <= m1 for m0, m1 in merged)
    if not ok:
        if s.get('rule_break'): notes.append(f'{s["id"]}: HE on screen {a:.3f}-{b:.3f} outside sung words (the deliberate rule break)')
        else: err(f'{s["id"]}: HE on screen {a:.3f}-{b:.3f} outside sung-word spans')

# ---------------------------------------------------------------------------------------------------- 7 GEN usage
for s in shots:
    g = s.get('gen')
    if not g or not g.get('duration'): continue
    use = g.get('use')
    if not use: warn(f'{s["id"]}: gen.use missing'); continue
    part = s['t1'] - s['t0']
    if s['id'] == 'S15': part = s['t1'] - 50.49
    if s['id'] == 'S54': part = s['t1'] - 151.1447
    if abs((use[1] - use[0]) - part) > 1.01 / FPS: err(f'{s["id"]}: gen.use span {use[1] - use[0]:.3f} != used part {part:.3f}')
    if use[1] + 0.5 > g['duration'] + 1e-6: err(f'{s["id"]}: plate {g["duration"]} s too short for use {use} + 12-frame tail handle')
    if use[0] < 0.5 - 1e-6: err(f'{s["id"]}: no 12-frame head handle')

# ---------------------------------------------------------------------------------------------------- report
bysrc = {}
for s in shots:
    bysrc.setdefault(s['source'], 0.0)
    bysrc[s['source']] += s['t1'] - s['t0']
report = {'shots': len(shots), 'frames': total, 'duration': shots[-1]['t1'],
          'internal_cuts': sum(len(s.get('internal_cuts', [])) for s in shots),
          'seconds_by_source': {k: round(v, 2) for k, v in bysrc.items()},
          'gen_plates': sorted({s['gen']['plate'] for s in shots if s.get('gen')}),
          'errors': errors, 'warnings': warnings, 'notes': notes}

if '--json' in sys.argv:
    print(json.dumps(report, indent=1, ensure_ascii=False))
else:
    print(f'{len(shots)} shots, {report["internal_cuts"]} internal cuts, {total} frames, 0 -> {shots[-1]["t1"]} s')
    print('seconds by source:', report['seconds_by_source'], ' plates:', ', '.join(report['gen_plates']))
    for n in notes: print('NOTE ', n)
    for w in warnings: print('WARN ', w)
    for e in errors: print('ERROR', e)
    print('OK' if not errors else f'{len(errors)} ERROR(S)')

if '--table' in sys.argv:
    def lyr(s):
        return ', '.join(f'L{i}' for i in s['lyric_lines']) or '-'
    print()
    print('| # | Shot | t0-t1 (s) | Frames | Dur | Cut on | Lines · text | Image | Src | Module |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for n, s in enumerate(shots, 1):
        title = s.get('title', '')
        extra = ' **(rule break)**' if s.get('rule_break') else ''
        print(f'| {n} | {s["id"]} | {s["t0"]:.3f}-{s["t1"]:.3f} | {s["frames"][0]}-{s["frames"][1]} | {s["t1"] - s["t0"]:.2f} | '
              f'{cut_anchor.get(s["id"], "?")} | {lyr(s)} · {s["text_mode"]} | {title}{extra} | {s["source"]}'
              f'{" " + s["gen"]["plate"] if s.get("gen") else ""} | {s["module"]} |')

sys.exit(1 if errors else 0)
