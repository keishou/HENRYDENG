#!/usr/bin/env python3
"""Validate claudepop/shots.json against claudepop/analysis/song.json, and print the BIBLE timing table.

    python3 claudepop/film/tools/validate_shots.py            # checks; exit 1 on any error
    python3 claudepop/film/tools/validate_shots.py --table    # also print the markdown timing table (BIBLE section 13)
    python3 claudepop/film/tools/validate_shots.py --json     # machine-readable report

Every timing check runs twice: in SECONDS (song.json times, 6 ms tolerance) and in FRAMES (f = round(t * 24), rounded
half up exactly like the core's tl.frameOf = Math.round(t * fps); a shot covers frames [frames[0], frames[1])). The
frame result is binding for what renders; a seconds-only miss that the frames accept is reported as a NOTE.

Checks
  1. schema: required top-level and per-shot keys; source in {GEN, 3D, TYPE}; GEN shots carry a complete gen block;
     dur = t1 - t0; each shot starts inside its section (seconds and frames); flags.faceSafe lists exactly the
     consent shots
  2. tiling: first t0 = 0, every t1 = next t0, last t1 = song duration (seconds); frames[] = [round(t0*24), round(t1*24)],
     contiguous, non-empty, first 0, last = top-level frames = round(duration*24) (frames)
  3. cuts on song times and on frames: every cut (shot t0 and internal_cuts) lies on a song.json time (beat, 8th or
     16th grid, word onset or letter part, line start, extra-vocal onset, event) within 6 ms, AND on the same frame as
     that time; internal cuts lie strictly inside their shot's frames, ascending, one per frame
  4. beat_hits: inside [frames[0], frames[1]) and never two hits on one frame (frames); inside [t0, t1) (seconds: a hit
     up to half a frame before the cut that lands on the shot's first frame is a NOTE); ascending (warn); a hit that is
     not a song.json time (onset, word end, grid, event, line start/end) is listed as a NOTE (designed moments)
  5. lyric coverage: the shot that holds each lyric line's start lists the line (frames: the start frame; seconds: the
     start time, 6 ms tolerance)
  6. the live-man rule: where HE moves on screen (he_live, live_span) the span lies inside sung-word spans
     (seconds: line start - 2/24 s .. line end + 6/24 s, gaps under 0.6 s merged; frames: [round(start*24) - 2,
     round(end*24) + 6), gaps under 0.6 s = 14.4 frames merged; live frames [round(a*24), round(b*24))); the live span
     lies inside its shot; rule_break shots are reported, not failed
  7. GEN plate usage: the used span of the plate equals the shot (or its GEN part) within 1 frame, with 12-frame head and
     tail handles inside the plate duration (seconds and frames)
  8. timed text / HUD fields (text[].on/off/until/from, hud job_line/edge_labels/marks_rotate/none_from) fall inside
     their shot (frames; a CARD may hold to its shot's last frame)
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
def note(m): notes.append(m)


def fr(t):   # the core's frame rounding (tl.frameOf = Math.round(t * fps): half up, not Python's half-even)
    return int(math.floor(t * FPS + 0.5))


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
    if 'dur' in s and abs(s['dur'] - (s['t1'] - s['t0'])) > 5e-4:
        err(f'{s["id"]}: dur {s["dur"]} != t1 - t0 = {s["t1"] - s["t0"]:.4f}')
secnames = [x['name'] for x in song['sections']]
for s in shots:
    if s['section'] not in secnames: err(f'{s["id"]}: unknown section {s["section"]}')
    else:
        sec = song['sections'][secnames.index(s['section'])]
        if not (sec['t0'] - 1e-4 <= s['t0'] < sec['t1']): err(f'{s["id"]}: t0 {s["t0"]} outside its section {s["section"]} (seconds)')
        if not (fr(sec['t0']) <= fr(s['t0']) < fr(sec['t1'])):
            err(f'{s["id"]}: first frame {fr(s["t0"])} outside its section {s["section"]} frames {fr(sec["t0"])}-{fr(sec["t1"])}')
fs = (doc.get('flags') or {}).get('faceSafe')
consent = sorted(s['id'] for s in shots if s.get('consent'))
if fs is None:
    if consent: warn(f'flags.faceSafe missing (consent shots: {consent})')
else:
    if sorted(fs.get('shots', [])) != consent:
        err(f'flags.faceSafe.shots {fs.get("shots")} != shots with consent: true {consent}')
    for i in fs.get('shots', []):
        if i not in ids: err(f'flags.faceSafe names unknown shot {i}')
    if not isinstance(fs.get('default'), bool): err('flags.faceSafe.default is not a boolean')

# ---------------------------------------------------------------------------------------------------- 2 tiling
if abs(shots[0]['t0']) > 1e-9: err('first shot does not start at 0')
for a, b in zip(shots, shots[1:]):
    if abs(a['t1'] - b['t0']) > 1e-9: err(f'gap/overlap between {a["id"]} ({a["t1"]}) and {b["id"]} ({b["t0"]})')
if abs(shots[-1]['t1'] - song['duration']) > 1e-4: err(f'last t1 {shots[-1]["t1"]} != duration {song["duration"]}')
total = 0
for s in shots:
    f0, f1 = fr(s['t0']), fr(s['t1'])
    if not s.get('frames'): err(f'{s["id"]}: frames missing')
    elif s['frames'] != [f0, f1]: err(f'{s["id"]}: frames {s["frames"]} != {[f0, f1]}')
    if f1 <= f0: err(f'{s["id"]}: empty after frame rounding')
    if s['t1'] - s['t0'] < 0.4: warn(f'{s["id"]}: shorter than 0.4 s ({f1 - f0} frames)')
    total += f1 - f0
for a, b in zip(shots, shots[1:]):   # the stored frame spans themselves must tile (what the core reads)
    if a.get('frames') and b.get('frames') and a['frames'][1] != b['frames'][0]:
        err(f'frame gap/overlap between {a["id"]} {a["frames"]} and {b["id"]} {b["frames"]}')
if shots[0].get('frames') and shots[0]['frames'][0] != 0: err('first shot does not start on frame 0')
if total != fr(song['duration']): err(f'frame total {total} != {fr(song["duration"])}')
if doc.get('frames') is not None and doc['frames'] != fr(song['duration']):
    err(f'top-level frames {doc["frames"]} != round(duration * 24) = {fr(song["duration"])}')
if shots[-1].get('frames') and shots[-1]['frames'][1] != fr(song['duration']):
    err(f'last frame {shots[-1]["frames"][1]} != {fr(song["duration"])}')

# ---------------------------------------------------------------------------------------------------- 3 cuts on song times / frames
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
# hits may also sit on a word end, a line end or an event end (never a cut)
hit_anchors = anchors + [(wd['e'], f'L{l["i"]} end of "{wd["w"]}"') for l in song['lines'] for wd in l['words'] if wd.get('e')] \
    + [(l['end'], f'L{l["i"]} end') for l in song['lines']] + [(e['t_end'], f'event {e["type"]} end') for e in song['events'] if e.get('t_end')]


def anchor_of(t, pool=anchors):
    best = min(pool, key=lambda a: abs(a[0] - t))
    return best if abs(best[0] - t) <= TOL else None


cut_anchor = {}
for s in shots:
    f0, f1 = fr(s['t0']), fr(s['t1'])
    a = anchor_of(s['t0'])
    if not a: err(f'{s["id"]}: cut at {s["t0"]} is not on a song.json time (seconds)')
    else:
        cut_anchor[s['id']] = a[1]
        if fr(a[0]) != f0: err(f'{s["id"]}: cut at {s["t0"]} (frame {f0}) is off the frame of its song time {a[0]} {a[1]} (frame {fr(a[0])})')
    ics = s.get('internal_cuts', [])
    for c in ics:
        a = anchor_of(c)
        if not a: err(f'{s["id"]}: internal cut {c} is not on a song.json time (seconds)')
        elif fr(a[0]) != fr(c): err(f'{s["id"]}: internal cut {c} (frame {fr(c)}) is off the frame of its song time {a[0]} (frame {fr(a[0])})')
        if not (s['t0'] < c < s['t1']): err(f'{s["id"]}: internal cut {c} outside {s["t0"]}-{s["t1"]} (seconds)')
        if not (f0 < fr(c) < f1): err(f'{s["id"]}: internal cut {c} (frame {fr(c)}) not strictly inside frames {f0}-{f1}')
    if ics != sorted(ics): err(f'{s["id"]}: internal_cuts not ascending')
    icf = [fr(c) for c in ics]
    if len(set(icf)) != len(icf): err(f'{s["id"]}: two internal cuts on one frame {sorted(f for f in set(icf) if icf.count(f) > 1)}')

# ---------------------------------------------------------------------------------------------------- 4 beat_hits
for s in shots:
    f0, f1 = fr(s['t0']), fr(s['t1'])
    hits = s['beat_hits']
    for h in hits:
        fh = fr(h)
        in_frames = f0 <= fh < f1
        if not in_frames: err(f'{s["id"]}: hit {h} (frame {fh}) outside frames [{f0}, {f1})')
        if h >= s['t1'] - 1e-9: err(f'{s["id"]}: hit {h} at or after the shot end {s["t1"]} (seconds)')
        elif h < s['t0'] - TOL:
            if in_frames: note(f'{s["id"]}: hit {h} is {1000 * (s["t0"] - h):.1f} ms before the cut {s["t0"]} (seconds) but on the shot\'s first frame {f0}')
            else: err(f'{s["id"]}: hit {h} before the cut {s["t0"]} (seconds)')
        if not anchor_of(h, hit_anchors):
            near = min(hit_anchors, key=lambda a: abs(a[0] - h))
            note(f'{s["id"]}: hit {h} is not a song.json time (nearest {near[0]} {near[1]}, {1000 * (h - near[0]):+.0f} ms): a designed moment')
    hf = [fr(h) for h in hits]
    dup = sorted(f for f in set(hf) if hf.count(f) > 1)
    for f in dup: err(f'{s["id"]}: two hits on frame {f}: {[h for h in hits if fr(h) == f]}')
    if hits != sorted(hits): warn(f'{s["id"]}: beat_hits not ascending')

# ---------------------------------------------------------------------------------------------------- 5 lyric coverage
for l in song['lines']:
    owner = [s for s in shots if fr(s['t0']) <= fr(l['start']) < fr(s['t1'])]
    if not owner or l['i'] not in owner[0]['lyric_lines']:
        err(f'line {l["i"]} ("{l["text"]}") starts at {l["start"]} (frame {fr(l["start"])}) but the shot on that frame does not list it')
    owner_s = [s for s in shots if s['t0'] - TOL <= l['start'] < s['t1'] - TOL]
    if not owner_s or l['i'] not in owner_s[0]['lyric_lines']:
        if owner and l['i'] in owner[0]['lyric_lines']:
            note(f'line {l["i"]} starts at {l["start"]}: the shot at that time (seconds) does not list it, the shot on its frame does')
        else: err(f'line {l["i"]} ("{l["text"]}") starts at {l["start"]} but the shot at that time does not list it (seconds)')
listed = {i for s in shots for i in s['lyric_lines']}
missing = [l['i'] for l in song['lines'] if l['i'] not in listed]
if missing: err(f'lines never listed: {missing}')

# ---------------------------------------------------------------------------------------------------- 6 live-man rule
GAP = 0.6


def merge(spans, gap):
    out = []
    for a, b in sorted(spans):
        if out and a - out[-1][1] < gap: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out


merged = merge([[l['start'] - 2 / FPS, l['end'] + 6 / FPS] for l in song['lines']], GAP)            # seconds
merged_f = merge([[fr(l['start']) - 2, fr(l['end']) + 6] for l in song['lines']], GAP * FPS)       # frames, half-open
for s in shots:
    if not s.get('he_live'):
        if s.get('live_span'): warn(f'{s["id"]}: live_span without he_live')
        continue
    a, b = s.get('live_span') or [s['t0'], s['t1']]
    fa, fb = fr(a), fr(b)
    if not (s['t0'] - TOL <= a < b <= s['t1'] + TOL): err(f'{s["id"]}: live_span {a}-{b} outside the shot {s["t0"]}-{s["t1"]} (seconds)')
    if not (fr(s['t0']) <= fa < fb <= fr(s['t1'])): err(f'{s["id"]}: live frames [{fa}, {fb}) outside the shot frames [{fr(s["t0"])}, {fr(s["t1"])})')
    ok_s = any(m0 <= a + 1e-6 and b - 1e-6 <= m1 for m0, m1 in merged)
    ok_f = any(m0 <= fa and fb <= m1 for m0, m1 in merged_f)
    for ok, what in ((ok_s, f'{a:.3f}-{b:.3f} s'), (ok_f, f'frames [{fa}, {fb})')):
        if ok: continue
        if s.get('rule_break'): note(f'{s["id"]}: HE on screen {what} outside sung words (the deliberate rule break)')
        else: err(f'{s["id"]}: HE on screen {what} outside sung-word spans')

# ---------------------------------------------------------------------------------------------------- 7 GEN usage
GEN_PART_T0 = {'S15': 50.49, 'S54': 151.1447}   # shots that are 3D until a handoff under a full-frame transition
for s in shots:
    g = s.get('gen')
    if not g or not g.get('duration'): continue
    use = g.get('use')
    if not use: warn(f'{s["id"]}: gen.use missing'); continue
    p0 = GEN_PART_T0.get(s['id'], s['t0'])
    part = s['t1'] - p0
    if abs((use[1] - use[0]) - part) > 1.01 / FPS: err(f'{s["id"]}: gen.use span {use[1] - use[0]:.3f} != used part {part:.3f} (seconds)')
    if use[1] + 0.5 > g['duration'] + 1e-6: err(f'{s["id"]}: plate {g["duration"]} s too short for use {use} + 12-frame tail handle (seconds)')
    if use[0] < 0.5 - 1e-6: err(f'{s["id"]}: no 12-frame head handle (seconds)')
    n_film, n_plate = fr(s['t1']) - fr(p0), fr(use[1]) - fr(use[0])
    if abs(n_film - n_plate) > 1: err(f'{s["id"]}: plate frames {n_plate} (use {use}) != film frames {n_film} of the used part')
    if fr(use[0]) < 12: err(f'{s["id"]}: head handle {fr(use[0])} frames < 12')
    if fr(g['duration']) - (fr(use[0]) + n_film) < 12: err(f'{s["id"]}: tail handle {fr(g["duration"]) - (fr(use[0]) + n_film)} frames < 12')

# ---------------------------------------------------------------------------------------------------- 8 timed text / HUD fields
for s in shots:
    f0, f1 = fr(s['t0']), fr(s['t1'])
    timed = []
    for i, tx in enumerate(s.get('text') or []):
        for k in ('on', 'off', 'until', 'from'):
            if k in tx: timed += [(f'text[{i}].{k}', v) for v in (tx[k] if isinstance(tx[k], list) else [tx[k]])]
    h = s.get('hud') or {}
    for k in ('job_line', 'edge_labels', 'marks_rotate', 'none_from'):
        v = h.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool): timed.append((f'hud.{k}', v))
        elif isinstance(v, list): timed += [(f'hud.{k}', x) for x in v]
    for name, v in timed:
        if not isinstance(v, (int, float)) or isinstance(v, bool): continue
        if not (f0 <= fr(v) <= f1): err(f'{s["id"]}: {name} {v} (frame {fr(v)}) outside the shot frames [{f0}, {f1}]')

# ---------------------------------------------------------------------------------------------------- report
bysrc = {}
for s in shots:
    bysrc.setdefault(s['source'], 0.0)
    bysrc[s['source']] += s['t1'] - s['t0']
report = {'shots': len(shots), 'frames': total, 'duration': shots[-1]['t1'],
          'internal_cuts': sum(len(s.get('internal_cuts', [])) for s in shots),
          'beat_hits': sum(len(s['beat_hits']) for s in shots),
          'seconds_by_source': {k: round(v, 2) for k, v in bysrc.items()},
          'gen_plates': sorted({s['gen']['plate'] for s in shots if s.get('gen')}),
          'errors': errors, 'warnings': warnings, 'notes': notes}

if '--json' in sys.argv:
    print(json.dumps(report, indent=1, ensure_ascii=False))
else:
    print(f'{len(shots)} shots, {report["internal_cuts"]} internal cuts, {report["beat_hits"]} beat hits, {total} frames, 0 -> {shots[-1]["t1"]} s')
    print('seconds by source:', report['seconds_by_source'], ' plates:', ', '.join(report['gen_plates']))
    for n in notes: print('NOTE ', n)
    for w in warnings: print('WARN ', w)
    for e in errors: print('ERROR', e)
    print('OK (seconds and frames)' if not errors else f'{len(errors)} ERROR(S)')

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
