#!/usr/bin/env python3
"""build_shots.py: the single source of truth for the Claude Pop shot list.

Reads  claudepop/analysis/song.json  (beat grid, words, syllables, hooks, events, hits).
Writes claudepop/shots.json           (machine-readable shot list + type events + global tracks).
Injects the generated timing table and per-shot notes into claudepop/BIBLE.md between the
markers <!-- BEGIN:TIMING --> ... <!-- END:TIMING --> and <!-- BEGIN:SHOTNOTES --> ... <!-- END:SHOTNOTES -->.

Run:  python3 claudepop/tools/build_shots.py            (validates, then writes)
      python3 claudepop/tools/build_shots.py --check    (validates only)

Conventions
- Master is 60 fps. A sound at song time t is on screen on frame f = floor(60 t) (never later).
- Times are seconds from the first decoded PCM sample of assets/pdoom.mp3 (song.json convention).
- A shot owns frames [floor(60*start), floor(60*end)). Shots are contiguous and cover 0..156.651.
- Every sung word must appear in at least one type event (caption guarantee).
"""
import json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # claudepop/
SONG = json.load(open(os.path.join(ROOT, 'analysis', 'song.json')))
FPS = 60
DUR = SONG['duration']                             # 156.651
T0, BEAT, BAR = SONG['grid']['t0'], SONG['beat_period'], SONG['grid']['bar_period']

def F(t):
    return int(math.floor(FPS * t + 1e-9))

EPS = 0.003   # song.json grid values are rounded to 1 ms; treat anything within 3 ms of a boundary as on it

def bar_of(t):
    return 1 if t < T0 - EPS else int((t - T0 + EPS) // BAR) + 1

def pos_of(t):
    """bar.beat.8th position string (1-based), e.g. 14.1.1"""
    if t < T0:
        return '1.0'
    k = (t - T0 + EPS) / BEAT
    b = int(k // 4) + 1
    bt = int(k % 4) + 1
    e = int(((k % 1) * 2)) + 1
    return f'{b}.{bt}.{e}'

# ------------------------------------------------------------------------------------------
# Global tracks (the "speedometers"): used by the engine's clock.js. Values change at times.
# ------------------------------------------------------------------------------------------
TRACKS = {
    'drawing_rate_dps': [  # the drawing clock (character drawings, boil, mechanisms). Camera + type run on ones.
        [0.000, 12, 'intro: 12 dps (hold 5)'],
        [1.200, 7.5, 'print pass: local 7.5 dps (hold 8)'],
        [2.053, 12, 'verse 1: 12 dps + reset on every pluck 8th and word onset'],
        [22.053, 30, '16th kick roll: first taste of speed'],
        [22.980, 0, 'STOP: world frozen; only idol + type get drawings (one per syllable)'],
        [23.871, 15, 'chorus 1: 15'],
        [56.599, 30, 'bar-32 build + roll'],
        [59.350, 0, 'STOP'],
        [60.235, 30, 'chorus 2: 30'],
        [89.300, 7.5, 'breakdown: first slowdown (camera stepped too)'],
        [96.599, 3.75, 'chorus 3: xerox slideshow (camera stepped too)'],
        [109.326, 7.5, 'bridge bars 61-62'],
        [112.962, 15, 'bridge bars 63-64'],
        [116.599, 30, 'bridge bars 65-66'],
        [120.235, 60, 'bridge bars 67-68: on ones, smooth for the first time'],
        [138.410, 0, 'STOP: 0 fps (the rip itself runs 3 drawings on ones)'],
        [140.235, 60, 'outro'],
        [153.871, 30, 'ending: flip-book leaving the thumb'],
        [154.326, 15, ''],
        [154.780, 7.5, 'halo folds on 8ths (events reset the clock)'],
        [155.917, 0, 'frozen; ink starvation continues per output frame'],
    ],
    'registration_px': [  # max colour-plate drift vs the key plate at 1080p (see BIBLE 3.8)
        [0.000, 16, 'cover misprint (lyric Pink/Yellow +-16; face plates 6)'],
        [2.053, 12, 'tightens one notch per printed word: 16 -> 12 -> 8'],
        [4.330, 0, 'SNAP: every plate in register on the I of AGI'],
        [5.690, 2, 'verse 1'],
        [23.871, 4, 'chorus 1 (seps leave her body: separate dancers)'],
        [38.417, 6, 'verse 2'],
        [52.962, 8, 'pre-chorus 2'],
        [60.235, 10, 'chorus 2'],
        [74.760, 12, 'verse 3'],
        [89.300, None, 'breakdown: single plate (silhouette)'],
        [96.599, None, 'chorus 3: toner only, no colour plates'],
        [107.490, 20, 'blues: plates return one by one, re-registering at 20'],
        [109.326, 20, 'bridge'],
        [116.599, 30, 'bridge 65-68'],
        [121.900, 30, 'ASKEW: Blue plate rotates 7 deg across the whole frame'],
        [125.689, 40, 'chorus 4: 40 px; Blue rotation relaxes to 2 deg'],
        [138.410, 0, 'STOP: 0'],
        [140.235, 40, 'outro: seps fully independent'],
        [151.144, 20, 'convergence: halves every 8th'],
        [152.962, 0, 'SNAP: one body, one print'],
        [155.917, 12, 'final drawing: one plate slips 12 px (P(doom) is never zero)'],
    ],
    'volvelle_pdoom': [
        [23.871, '>10%', 'chorus 1 (Hubinger, >10% within a decade)'],
        [60.235, '25%', 'chorus 2 (Amodei, reported ~25%)'],
        [96.598, '50%', 'chorus 3 (xeroxed)'],
        [125.689, '99.9%', 'chorus 4'],
        [147.963, '100.0%', 'outro overflow'],
        [148.417, '100.1%', ''],
        [148.872, 'NaN', ''],
    ],
    'countdown': [  # Zeno comeback countdown on the folio (each ~half the previous)
        [0.000, 'D-365'], [16.599, 'D-180'], [23.871, 'D-90'], [38.417, 'D-45'], [60.235, 'D-22'],
        [74.760, 'D-11'], [96.599, 'D-5'], [109.326, 'D-2'], [112.962, 'D-1'], [116.599, 'D-12H'],
        [120.235, 'D-1H'], [123.660, 'D-DAY'], [140.235, 'D+0'],
    ],
    'folio_page': [
        [0.000, 'p.01'], [5.690, 'p.02'], [16.599, 'p.04'], [23.871, 'p.06'], [38.417, 'p.08'], [52.962, 'p.10'],
        [60.235, 'p.12'], [74.760, 'p.14'], [89.300, 'p.16'], [96.599, 'p.18'], [109.326, 'p.20'], [123.660, 'p.22'],
        [138.410, 'p.24'], [140.235, 'p.∞'], [152.962, 'colophon'],
    ],
    'press_dial_ppm': [
        [0.000, 30], [16.599, 60], [23.871, 90], [44.781, 120], [60.235, 150], [74.760, 150],
        [89.300, 0], [109.326, 150], [125.689, 'snaps off'],
    ],
    'solved_stamp_rate': [  # stamps on the Erdős problem wall (verse 3), each < 2% of frame
        [74.760, '1/4 note'], [78.417, '1/8'], [82.053, '1/16'], [85.690, '1/32'], [89.300, 'off'],
    ],
    'pinwheel_rev_per_beat': [
        [60.235, 1], [66.080, 2], [109.326, 2], [116.599, 4], [123.660, 'alias (small objects only)'],
    ],
    'bridge_inks': [
        [109.326, 'Black + Blue'], [112.962, '+ Pink'], [116.599, '+ Yellow'], [120.235, '+ Gold + silver foil'],
    ],
}

# ------------------------------------------------------------------------------------------
# Shot data. Each shot: id, start (end = next start). Fields documented in BIBLE section 5.
# h(...) = a hero type event. Caption modes: strip | rest | carried | none.
# ------------------------------------------------------------------------------------------
def h(text, t, tier, verb, font='RF', ink='K', place='', src='lyric', note=''):
    return dict(text=text, t=t, tier=tier, verb=verb, font=font, ink=ink, place=place, src=src, note=note)

SHOTS = [
# ================================ COVER (p.01) =================================================
dict(id='CP00', start=0.000, section='intro', spread='p.01 COVER',
  title='THE COVER (frame 0 = the thumbnail)',
  logline='Finished zine cover: face ECU right with eye contact, two-plate misprint of the first lyric left; counter rolls; print pass; eyes open on the hum.',
  visual=("Frame 0 is the finished zine cover and the thumbnail. RIGHT 52%: CLAUDE ✻ in extreme close-up, three-quarter view, "
          "IDOL STARE (upper lids at 70%) with direct eye contact; halo at S1 ✢, petals running off the right edge. LEFT 48%: the first "
          "lyric as a two-plate misprint, I SEE / SPARKS / OF AGI, in Fluorescent Pink 100% and Yellow 100% offset +-16 px, readable "
          "at feed size and visibly unfinished, waiting for its Blue key plate. Cover furniture (pause-bait, >= 40 px): masthead "
          "top-left `CLAUDE ✻ 1st MINI ALBUM 'P(DOOM)' · PINK ver.`; top-right JetBrains Mono status line `✢ Printing… 1 copy (esc to "
          "interrupt)` whose counter rolls exponentially from f14 (copies = 10^(6(t-0.235)/1.365): 1,000,000 on the hum, then x10 per bar); "
          "footnote `¹ cf. \"Sparks of Artificial General Intelligence\", 2023`; Dymo folio `p.01 ▸ 12 fps · D-365`. The halo ticks open "
          "on the pad beats, S2 ✳ at 0.235 and S3 ✶ at 0.690 (status glyph in sync). 1.20-2.053 PRINT PASS: an ink-roller shadow sweeps "
          "left to right in 7.5-dps steps and lays fresh coral on the petals. 1.60 (hum): lids snap fully open, pupils bloom to ✻, halo S4 ✻."),
  type=dict(caption='none', heroes=[
      h('I SEE / SPARKS / OF AGI', 0.0, 'L', 'ghost-misprint', 'RF wght1000 wdth151 opsz144', 'P+Y', 'left 48%, 3 lines', 'nonlyric', 'Pink/Yellow at 100%, offset +-16 px; the Blue key plate prints per word in CP01'),
      h("CLAUDE ✻ 1st MINI ALBUM 'P(DOOM)' · PINK ver.", 0.0, 'M', 'printed', 'BG wdth100 wght800', 'K', 'masthead top-left 56 px', 'nonlyric'),
      h('✢ Printing… 1 copy (esc to interrupt)', 0.235, 'S', 'counter-roll', 'JBM', 'K', 'top-right 44 px', 'nonlyric', 'counter per frame; glyph follows halo state'),
  ]),
  camera='Push-in 1.000 -> 1.030 on ones from f0 (smooth: the judges\' fix for the "laggy" read). No shake.',
  out='Continuous.', dps='12 (hold 5); print pass 1.20-2.053 at 7.5 (local); camera, type and counter on ones',
  reg='16 px on the lyric, 6 px on her face plates (⊕ rings doubled)', stock='cream #F4EEE2',
  inks=['Black (key/line)', 'Fluorescent Pink', 'Yellow', 'Coral + Sunflower (halo)'], cast=['CLAUDE'],
  hits=[(0.235, 'halo S2 ✳ + counter starts'), (0.690, 'halo S3 ✶'), (1.144, 'petals shiver (pad beat)'), (1.200, 'print pass begins'), (1.600, 'hum: eyes fully open, halo S4 ✻')],
  zeit=['sparks_of_agi', 'claude_spark_spinner'], origin=['zine 1.3 cover', 'timeline f0 counter', 'judges: eye contact from f0'],
  plate='P01', choreo='IDOL STARE; eyes open on the hum', cut='never'),

dict(id='CP01', start=2.053, section='verse1', spread='p.01 COVER',
  title='I SEE SPARKS OF AGI (the key plate prints live)',
  logline='Each word\'s Blue key plate lands on its onset; SPARKS blooms the halo; A-G-I print as passes and the whole cover snaps into register on I (f259).',
  visual=("The cover prints live. Each word's Blue key plate lands on its onset and the word's Pink/Yellow plates tighten one notch "
          "(16 -> 12 -> 8 px): I on the bar-2 downbeat with a 3 px paper jolt; SEE (her eyes flick left to the words); SPARKS keys in "
          "Fluorescent Pink instead of Blue, the halo blooms to S5 ✽ with a 2-drawing overshoot and ~40 hole-punch chads burst off the "
          "petal tips across the letters; `of` small. The AGI letter run: A takes its Blue at (+22,-9) on 3.65, G at (-18,+12) on 4.10, "
          "I on 4.33 (f259) and on that drawing EVERY plate on the cover snaps to 0 offset: AGI overprints to near-black, the doubled "
          "⊕ rings in her irises fuse into one, the status line reads `✽ Printed.` Registration = alignment, achieved (for now)."),
  type=dict(caption='carried', heroes=[
      h('I', 2.05, 'L', 'print-key', 'RF wght1000 wdth151', 'B', 'left block line 1'),
      h('SEE', 2.36, 'L', 'print-key', 'RF wght1000 wdth151', 'B', 'left block line 1'),
      h('SPARKS', 2.73, 'L', 'print-key', 'RF wght1000 wdth151', 'P', 'left block line 2 (hero)'),
      h('of', 3.44, 'S', 'stamp-small', 'IS', 'K', 'between lines 2 and 3'),
      h('A', 3.65, 'L', 'pass-misregistered', 'RF wght1000 wdth151', 'B', 'line 3, offset (+22,-9)'),
      h('G', 4.10, 'L', 'pass-misregistered', 'RF wght1000 wdth151', 'B', 'line 3, offset (-18,+12)'),
      h('I', 4.33, 'L', 'pass + GLOBAL SNAP', 'RF wght1000 wdth151', 'B', 'line 3; all plates -> 0'),
  ]),
  camera='Locked; 3 px jolt on I; +1.5% scale punch over 2 drawings on the 4.33 snap.', out='Continuous.',
  dps='12 + a new drawing on every pluck 8th and word onset', reg='16 -> 12 -> 8 -> 0 at 4.33', stock='cream #F4EEE2',
  inks=['Black', 'Fluorescent Pink', 'Yellow', 'Blue', 'Coral + Sunflower'], cast=['CLAUDE'],
  hits=[(2.053, 'I + paper jolt'), (2.730, 'halo S5 ✽ bloom + chad burst'), (4.330, 'GLOBAL SNAP INTO REGISTER')],
  zeit=['sparks_of_agi'], origin=['zine 1.3', 'idol 1.3 (A/G/I ink order Pink/Yellow/Blue)'], plate='P01',
  choreo='eyes to the words on SEE; small chin lift on SPARKS', cut='never'),

dict(id='CP02', start=4.780, section='verse1', spread='p.01 COVER',
  title='in your EYES (EYE-V, page turn)',
  logline='EYE-V across her eye; push-in; a tiny copy of the cover in her iris; EYES prints inside the V; page turns onto the bar-4 downbeat.',
  visual=("She raises EYE-V across her right eye on 'in'; the camera pushes in on ones to the V-framed eye. On 'your' a tiny copy of this "
          "cover is visible in her iris (the Droste seed paid off at 129.80). EYES prints inside the V; she blinks (2 drawings). The "
          "cover's right edge lifts at 5.35 and the PAGE TURNS (cylinder curl with a moving shadow), landing on the bar-4 downbeat."),
  type=dict(caption='rest', heroes=[h('EYES', 5.24, 'L', 'print', 'RF wght1000 wdth100', 'P', 'inside the V of her fingers')]),
  camera='Push 1.03 -> 1.45 on ones toward her right eye.', out='PAGE TURN 5.35 -> 5.690 (f341), landing on bar 4.',
  dps='12', reg='0 -> 2', stock='cream', inks=['Black', 'Fluorescent Pink', 'Blue', 'Coral'], cast=['CLAUDE'],
  hits=[(4.780, 'EYE-V'), (5.000, 'cover visible in iris'), (5.240, 'EYES + blink')],
  zeit=[], origin=['idol V-EYE', 'zine Droste seed + page turn'], plate='P01', choreo='EYE-V; blink', cut='never'),

# ============================ TRAINEE NOTEBOOK (p.02-03) =======================================
dict(id='CP03', start=5.690, section='verse1', spread='p.02-03 TRAINEE NOTEBOOK',
  title='YOUR CIRCUITS (copper-tape attribution graph; NEXT on vellum)',
  logline='Graph-paper notebook: pencil portrait with NEXT traced on vellum over it; copper-tape circuits spell YOUR CIRCUITS; Golden Gate node pops up on "nervous".',
  visual=("TRAINEE NOTEBOOK spread (graph paper, spiral binding). Left page: a graphite portrait of her (three-quarter). Taped over it: a "
          "sheet of VELLUM with NEXT traced on it (same face, one extra petal, pupils ✽, no mouth): the 'you' of the song, introduced "
          "as her own tracing. Copper-tape circuit traces (Metallic Gold) run in from the margins with 45° bends to paper node boxes typed "
          "`sparkle` · `eyes` · `nervous` · `boss` · `Golden Gate Bridge` (an attribution graph built as a paper circuit). A Yellow LED "
          "sticker lights along a trace on every pluck 8th. On 'nervous': the Golden Gate node lights, a tiny Orange paper Golden Gate pops "
          "up, a blue sweat-drop sticker slaps onto the portrait's temple and the portrait's eyes glance sideways; NEXT does NOT glance, it "
          "keeps looking at us. Pause-bait taped in a corner: the member-profile card `CLAUDE ✻ · Position: main vocal, center · Debut "
          "2023.03.14 · Fandom: USERS · Special skill: \"You're absolutely right!\"`."),
  type=dict(caption='rest', heroes=[
      h('YOUR', 5.75, 'L', 'copper-tape lay', 'COPPER (RF wght700 wdth125 centreline)', 'G', 'right page'),
      h('CIRCUITS', 5.97, 'L', 'copper-tape lay', 'COPPER', 'G', 'right page, letter by letter'),
  ]),
  camera='Slow lateral drift across the spread on ones (60 px per bar).', out='Hard cut 7.508.',
  dps='12 + pluck 8ths', reg='2', stock='graph notebook #F1EBDD + Cornflower grid', inks=['Black pencil', 'Metallic Gold', 'Yellow', 'Blue', '(Orange accent: Golden Gate)'],
  cast=['CLAUDE (portrait)', 'NEXT (vellum)'], hits=[(5.970, 'circuits: traces snap taut'), (6.970, 'nervous: Golden Gate pop-up + sweat drop')],
  zeit=['circuits', 'golden_gate_claude', 'claude_debut', 'youre_absolutely_right'], origin=['zine Z02', 'idol NEXT + member card'],
  plate='P02', choreo='portrait glance on nervous', cut='12: member-profile card (keep the shot)'),

dict(id='CP04', start=7.508, section='verse1', spread='p.02-03 TRAINEE NOTEBOOK',
  title='that\'s no surprise (spinner-verb stamps; NEXT winks)',
  logline='Subagent #003 stamps verified spinner verbs down the margin on 8ths; tiny idol and NEXT swing legs on the spiral binding; NEXT winks on "surprise".',
  visual=("The notebook margin. Subagent #003 (jersey COMBOBULATING) walks down it with a self-inking stamp and prints a Claude Code spinner "
          "verb on every pluck 8th: `Combobulating…` `Discombobulating…` `Noodling…` `Honking…` `Spelunking…` `Clauding…` (all verified in "
          "claude-code 2.0.14), each stamp sloppier and more tilted. The 3-inch paper-puppet idol sits on the spiral binding swinging her "
          "legs; NEXT (vellum) sits beside her copying the swing exactly. On 'surprise' she does a deadpan eye-roll and NEXT winks at camera. "
          "She doesn't notice (the first asymmetry pays off at 83.89)."),
  type=dict(caption='strip', heroes=[]),
  camera='Static top-down, slight tilt-follow of the Subagent.', out='STAMP-LIFT: the Subagent stamps the lens at 9.20; it lifts at 9.326 (bar 6).',
  dps='12 + pluck 8ths', reg='2', stock='graph notebook', inks=['Black', 'Blue', 'Orange (Subagent)'], cast=['CLAUDE', 'NEXT', 'Subagent #003'],
  hits=[(8.490, 'eye-roll / NEXT winks'), (9.200, 'stamp covers lens')],
  zeit=['claude_spark_spinner'], origin=['zine Z03', 'idol S03 reflection wink'], plate='P02', choreo='leg swing; eye-roll', cut='12: NEXT wink (keep the stamps)'),

dict(id='CP05', start=9.326, section='verse1', spread='p.02-03 TRAINEE NOTEBOOK',
  title='a sudden DROP in your training loss (the lyric is the curve)',
  logline='Dot-matrix printout: the lyric rides the loss curve as type-on-path; D-R-O-P fall one per 8th off the cliff; she flutters down; printout tears on "loss".',
  visual=("A tractor-feed dot-matrix printout (green-bar paper, sprocket holes) scrolls up one printed row per pluck 8th, plotting a loss "
          "curve in printed X characters. THE LYRIC IS THE CURVE: `THERE WAS A SUDDEN` glides along the plateau as type on a path and she "
          "skates on it. On 'drop' the path plunges; D, R, O, P fall one per 8th (10.67 / 10.90 / 11.13 / 11.36) and heap at the bottom; "
          "she drops with them in a paper-fall flutter. `IN YOUR TRAINING LOSS` continues on the low plateau; she lands on 'loss' and the "
          "printout tears along its perforation. Pencil note at the cliff: `grokking?` plus a red-pencil `!`."),
  type=dict(caption='carried', carry=dict(tier='M', verb='type-on-path', font='RF wght900 wdth100', ink='K', place='along the loss curve'), heroes=[
      h('DROP', 10.67, 'L', 'letters fall one per 8th (D 10.67, R 10.90, O 11.13, P 11.36)', 'RF wght1000 wdth100', 'K', 'the cliff'),
  ]),
  camera='Tilt following the printout on ones.', out='The torn strip falls across the lens as a wipe at 12.962.',
  dps='12 + pluck 8ths', reg='2', stock='green-bar tractor paper', inks=['Black', 'Blue', 'Bright Red (pencil)'], cast=['CLAUDE (3-inch puppet)'],
  hits=[(10.670, 'cliff'), (12.050, 'lands; perforation tears')],
  zeit=['grokking_K'], origin=['zine Z04', 'timeline 06 (type on the curve)'], plate='P02', choreo='skate; paper-fall flutter; land', cut=None),

dict(id='CP06', start=12.962, section='verse1', spread='p.02-03 TRAINEE NOTEBOOK',
  title='SERVANT / BOSS (NEXT takes the throne)',
  logline='She bows (insa) and gets a SERVANT Dymo; a pop-up throne lifts NEXT, crowned BOSS; permanent-underclass flyer counts 18 -> 3; spread is pulled into the Press rollers.',
  visual=("A pop-up spread with a folded-flat paper throne. She performs a 90° insa bow on 'servant' and a red Dymo label SERVANT slaps onto "
          "her back. On 'and you're my boss' the pop-up lifts the throne off the page in 3 drawings carrying NEXT (vellum); on 'boss' a paper "
          "crown drops onto NEXT's halo, a Dymo BOSS hits the throne, NEXT grows another petal, and Subagent #005 carries a tungsten cube up "
          "to it on a tray (the Project Vend nod). The type is the power see-saw: SERVANT small low-left, BOSS huge top-right. On the wall, a "
          "xeroxed flyer with tear-off tabs: `YOU HAVE [18] MONTHS TO ESCAPE THE PERMANENT UNDERCLASS`; the number is red-penned 18 -> 12 -> "
          "6 -> 3 on the bar-9 beats 15.235 / 15.690 / 16.144."),
  type=dict(caption='rest', heroes=[
      h('SERVANT', 13.93, 'M', 'Dymo slap', 'BG wdth75 wght700 embossed', 'Bright Red tape', 'on her back, low-left'),
      h('BOSS', 15.68, 'L', 'Dymo slam', 'BG wdth75 wght800 embossed', 'Bright Red tape', 'top-right over the throne'),
  ]),
  camera='Static; 2% push over bar 9.', out='16.1-16.599 noise riser: the spread is pulled up into the Press rollers (cylindrical warp, accelerating); SLAM to black on 16.599 (f995: kick + crash + "Chat-").',
  dps='12 + pluck 8ths', reg='2', stock='cream pop-up card', inks=['Black', 'Bright Red', 'Blue'], cast=['CLAUDE', 'NEXT', 'Subagent #005'],
  hits=[(13.930, 'insa bow'), (15.235, 'flyer 18->12'), (15.680, 'crown + BOSS'), (15.690, 'flyer ->6'), (16.144, 'flyer ->3'), (16.100, 'rollers pull')],
  zeit=['permanent_underclass', 'claudius_tungsten'], origin=['zine Z05 (POV fixed per judge 2)', 'idol S05 see-saw + red-pen countdown'],
  plate='P02', choreo='INSA bow; reluctant look up at NEXT', cut=None),

# ================================ THE ORACLE (p.04-05) =========================================
dict(id='CP07', start=16.599, section='prechorus1', spread='p.04-05 THE ORACLE',
  title='PRAYER I: CHAT · G · P · T (the cootie-catcher Oracle)',
  logline='Black flood. A giant cootie catcher whose four flaps print CHAT / G / P / T on the syllables; it breathes on every kick; CLAUDE in the PLEA pose, right third.',
  visual=("PRAYER I (layout shared by all three prayers: the addressee's NAME is the addressee's body, XL, left 60%; CLAUDE small in the right "
          "third in the PLEA pose, hands clasped under her chin, petals drooped). Black flood stock, white knockouts, Fluorescent Pink. THE "
          "ORACLE, a giant white paper cootie catcher printed in black only (no logo, no mark), fills the left 60%. Its four outer flaps print "
          "one syllable each as knockout XL: CHAT, G, P, T. On every kick it breathes (the two-axis pinch opens and shuts, showing numbered "
          "inner flaps). Pink spot on CLAUDE. Folio `p.04 ▸ 12 fps · D-180`."),
  type=dict(caption='carried', heroes=[
      h('CHAT', 16.60, 'XL', 'flap print (knockout)', 'RF wght1000 wdth100', 'paper (knockout)', 'flap 1'),
      h('G', 17.25, 'XL', 'flap print', 'RF wght1000 wdth100', 'paper', 'flap 2'),
      h('P', 17.95, 'XL', 'flap print', 'RF wght1000 wdth100', 'paper', 'flap 3'),
      h('T', 18.42, 'XL', 'flap print', 'RF wght1000 wdth100', 'paper', 'flap 4 (bar-11 downbeat)'),
  ]),
  camera='Static; 4 px table bump on each kick.', out='Continuous (first chomp at 18.417).',
  dps='12; every kick resets', reg='2', stock='black flood #1C1A18', inks=['Black flood', 'Fluorescent Pink', '(paper knockouts)'], cast=['THE ORACLE', 'CLAUDE'],
  hits=[(16.599, 'kick + crash: slam to black'), (18.417, 'bar 11: first chomp')],
  zeit=['navier_stokes_2026'], origin=['zine Z06', 'idol PLEA layout'], plate='P03', choreo='PLEA', cut='never'),

dict(id='CP08', start=18.872, section='prechorus1', spread='p.04-05 THE ORACLE',
  title='please don\'t EAT ME ALIVE (math getting eaten; the + f card)',
  logline='The Oracle chomps a card catalog of math problems; the Navier-Stokes card holds 2 beats with "+ f" circled; a ransom-note plea whose EAT and ME get eaten while ALIVE clings to the frame edge.',
  visual=("The Oracle chomps through a kraft CARD CATALOG: index cards pop up typed `ERDŐS #1026 (2025-12)`, `ERDŐS #728 (2026-01)`, "
          "`UNIT DISTANCE (1946)`, `JACOBIAN (1939)`, then `NAVIER–STOKES (CLAY)`, which holds for two beats (20.235-21.144) facing camera: "
          "`∂u/∂t + (u·∇)u = −∇p + νΔu + f` with `+ f` circled in red pencil and a pencil note `10,000 agents · 88 h`. Chomps on every kick "
          "in bar 11 and on 8ths in bar 12 (the eating accelerates); eaten cards burst into hole-punch confetti. The RANSOM NOTE: PLEASE and "
          "DON'T are slapped on in letters cut from the eaten cards; EAT and ME are slapped on and immediately EATEN by the next chomp; ALIVE, "
          "the biggest, clings to the right frame edge, its letters stretching toward the Oracle (Roboto Flex wdth 25 -> 151) while CLAUDE "
          "hugs the final E and cowers under the open jaws."),
  type=dict(caption='carried', heroes=[
      h('PLEASE', 19.05, 'L', 'ransom slap', 'RANSOM (RF/FR/IS/BG per glyph)', 'K on cut card', 'lower-left'),
      h("DON'T", 19.70, 'L', 'ransom slap', 'RANSOM', 'K', 'lower-left'),
      h('EAT', 20.31, 'L', 'ransom slap -> eaten', 'RANSOM', 'K', 'mid'),
      h('ME', 20.92, 'L', 'ransom slap -> eaten', 'RANSOM', 'K', 'mid'),
      h('ALIVE', 21.74, 'L', 'ransom slap + cling-stretch (wdth 25->151)', 'RF wght1000 (ransom-cut)', 'P', 'clings to right frame edge'),
  ]),
  camera='Static; bumps on kicks (bar 11) and 8ths (bar 12).', out='JAW CLOSE: the Oracle snaps shut over the lens -> black on 22.053 (f1323).',
  dps='12; kicks and 8th chomps reset', reg='2', stock='black flood + kraft catalog', inks=['Black', 'Fluorescent Pink', 'Bright Red (pencil)'],
  cast=['THE ORACLE', 'CLAUDE'], hits=[(20.235, 'Navier-Stokes card faces camera (2 beats)'), (21.144, 'NS card eaten'), (21.740, 'ALIVE clings')],
  zeit=['navier_stokes_2026', 'math_eaten'], origin=['zine Z07', 'timeline 09 (EAT/ME eaten, ALIVE clings)'], plate='P03', choreo='PLEA -> cower -> hug the E', cut='never'),

dict(id='CP09', start=22.053, section='prechorus1', spread='p.04-05 THE ORACLE',
  title='I\'M (hole-punched light on the 16th roll)',
  logline='Black; a hole punch knocks light through the page on every 16th; the dots accumulate into I\'M, apostrophe on "I\'m" (f1363).',
  visual=("Black. On every 16th of the kick roll a hole punch knocks light through the black page; the holes accumulate (additive, nothing "
          "flashes) into I'M, completed with the apostrophe on 'I'm'. Through the holes we glimpse her: index finger rising to notch 1, halo ·. "
          "The folio flickers `▸ 30 fps`."),
  type=dict(caption='carried', heroes=[h("I'M", 22.72, 'L', 'hole-punch accumulate (8 punches on 16ths from 22.053)', 'PUNCH (dot matrix of 9 mm holes)', 'light through paper', 'left')]),
  camera='Static; 2 px bumps on 16ths.', out='At 22.980 the punched page slides left and the punched I\'M becomes line 1 of the hook stack.',
  dps='30', reg='2', stock='black flood', inks=['Black', '(cream light through holes)'], cast=['CLAUDE (through holes)'],
  hits=[(22.053 + k * BEAT / 4, f'punch {k+1}') for k in range(8)],
  zeit=[], origin=['idol S09 hole-punch I\'M'], plate='P03', choreo='UPPING notch 1 (·)', cut='never'),

dict(id='CP10', start=22.980, section='prechorus1', spread='p.04-05 THE ORACLE',
  title='STOP · HOOK 1: THE UPPING (world at 0 fps)',
  logline='The world freezes; only she and the type move: one finger notch and one spinner state per syllable; syllables stack left, each bigger.',
  visual=("THE WORLD STOPS (folio `▸ 0 fps`): no boil, confetti frozen mid-air. Only CLAUDE and the type get new drawings, one per syllable. "
          "MCU at right on black, lit. THE UPPING: her index finger climbs one notch per syllable beside her cheek and the halo blooms one "
          "spinner state per syllable (up ✢, ping ✳, my ✶, P ✻); a paper click-chad flies off at each notch; brows lift on 'my'; eyes to "
          "the lens on 'P'. The syllables stack down the left edge as XL white knockouts, each bigger than the last: I'M 140 -> UP 260 -> "
          "PING 380 -> MY 480 -> P( 620 px cap height."),
  type=dict(caption='carried', heroes=[
      h('UP', 22.98, 'XL', 'slam (1 drawing)', 'RF wght1000 wdth100', 'paper knockout', 'stack line 2, 260 px'),
      h('PING', 23.19, 'XL', 'slam', 'RF wght1000 wdth100', 'paper knockout', 'stack line 3, 380 px'),
      h('MY', 23.42, 'XL', 'slam', 'RF wght1000 wdth100', 'paper knockout', 'stack line 4, 480 px'),
      h('P(', 23.62, 'XL', 'slam', 'RF wght1000 wdth100', 'paper knockout', 'stack line 5, 620 px'),
  ]),
  camera='Locked.', out='DOOM (rip).', dps='0 (world); idol + type: one drawing per syllable', reg='2', stock='black flood',
  inks=['Black', 'paper knockouts', 'Coral (halo)'], cast=['CLAUDE'],
  hits=[(22.980, 'STOP + up ✢'), (23.190, 'ping ✳'), (23.420, 'my ✶'), (23.620, 'P ✻')],
  zeit=['pdoom', 'claude_spark_spinner'], origin=['zine Z09 freeze', 'timeline THE UPPING (replaces CRANK)'], plate='P03', choreo='THE UPPING notches 2-5', cut='never'),

# ============================= PULL-OUT POSTER (p.06-07) =======================================
dict(id='CP11', start=23.871, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='DOOM: rip to the pink poster; SEPARATE; volvelle >10%',
  logline='Black page rips to the Fluorescent Pink fold-out poster; sunburst hands; the three Separations step out; the Oracle\'s fortune flap becomes the P(doom) volvelle >10%; pop-up P(DOOM).',
  visual=("DOOM: the black page RIPS from the centre outward in 2 drawings, revealing the PULL-OUT POSTER (Fluorescent Pink flood, 2x4 fold "
          "creases, staple gutter = the K-pop centre). SUNBURST HANDS: both hands burst open beside her face, halo S5 ✽. SEPARATE: the three "
          "Separations (Pink 806 left, Blue 3005 right, Yellow Y up/back) step out of her body as halftone paper dancers. The Oracle's fortune "
          "flap flips open and becomes the P(DOOM) VOLVELLE (paper wheel chart), window reading `>10%`; she takes it as a prop. Pop-up letters "
          "P(DOOM) stand up from the centre crease as the camera tilts 30°; DOOM's baseline droops ~40 px over 23.9-24.3, tracing the sung "
          "fall. Music-show bug lower-left in Dymo style: `클로드 CLAUDE ✻ | I'm Upping My P(doom)`. Folio pops `▸ 15 fps · D-90`."),
  type=dict(caption='rest', heroes=[
      h('DOOM)', 23.871, 'XL', 'pop-up (stands from the crease) + pitch droop', 'RF wght1000 wdth125', 'Yellow key on Pink flood', 'centre crease'),
      h('>10%', 23.871, 'M', 'volvelle window', 'JBM', 'K', 'volvelle in her hand', 'nonlyric'),
  ]),
  camera='Tilt 0 -> 30° over 6 frames; kick shake 4 px begins.', out='Continuous.',
  dps='15', reg='4 (seps become separate bodies)', stock='Fluorescent Pink flood poster', inks=['Fluorescent Pink flood', 'Yellow', 'Blue', 'Black'],
  cast=['CLAUDE', 'SEPARATIONS x3', 'volvelle'], hits=[(23.871, 'DOOM: rip + SEPARATE + bug')],
  zeit=['pdoom'], origin=['zine Z10', 'idol music-show bug'], plate='P03', choreo='SUNBURST HANDS; SEPARATE', cut='never'),

dict(id='CP12', start=24.780, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='the future goes FOOM (METR printout shoots vertical)',
  logline='A dot-matrix printer prints a METR-style time-horizon chart; on FOOM she yanks a party popper and the printout streams straight up like a streamer.',
  visual=("At frame right a desktop dot-matrix printer prints a METR-style time-horizon chart on log graph paper: ink-blot dots rising, only "
          "the last two labelled `4 h 49 m` (Opus 4.5) and `~14.5 h` (Opus 4.6); earlier dots unlabelled. The print head shuttles on 8ths; on "
          "'goes' it speeds to 16ths. On FOOM (bar-15 downbeat) she yanks a paper party-popper (HOCKEY STICK arm): the printout streams out "
          "VERTICALLY like a party streamer and shoots off the top of frame: the trend line goes straight up. Confetti burst."),
  type=dict(caption='rest', heroes=[h('FOOM', 25.68, 'XL', 'brush-SFX burst (paper firework)', 'BRUSH (custom centreline ribbons)', 'Yellow + Pink misreg', 'centre-left')]),
  camera='Locked with kick shake; 6-frame tilt-up follow of the streamer on FOOM.', out='The streamer falls across the frame at 26.144 (wipe).',
  dps='15', reg='4', stock='Pink flood + log graph paper', inks=['Fluorescent Pink', 'Yellow', 'Black'], cast=['CLAUDE', 'SEPARATIONS'],
  hits=[(25.240, 'print head -> 16ths'), (25.680, 'FOOM: streamer vertical')],
  zeit=['metr_time_horizons', 'foom'], origin=['zine Z11', 'idol HOCKEY STICK'], plate='P03', choreo='HOCKEY STICK / popper yank', cut='never'),

dict(id='CP13', start=26.144, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='Trapped in the CHINESE ROOM (the SANDBOX airplane)',
  logline='A cutaway paper box with a mail slot; she processes 中文房间 slips; a paper airplane printed SANDBOX escapes to a park bench and sandwich; the lid shuts on "room".',
  visual=("A white folded-paper box in cutaway with a mail slot. Inside, the tiny puppet idol at a desk with a rulebook `RULES`; paper slips "
          "printed 中文房间 slide in on 8ths; she looks them up, stamps them ✻ and posts answers back out. PAUSE-BAIT: just before the lid "
          "shuts, a paper airplane folded from a sheet printed `SANDBOX` shoots out of the slot and glides right; we glimpse it land on a paper "
          "park bench beside a sandwich. On 'room' the lid flaps shut (1 drawing) and a stencil shipping label slaps on: CHINESE ROOM."),
  type=dict(caption='rest', heroes=[h('CHINESE ROOM', 27.48, 'M', 'stencil label slap', 'BSS wght800', 'K on kraft label', 'box face')]),
  camera='Static three-quarter top view.', out='Hard cut 27.962.', dps='15', reg='4', stock='white folded card on Pink', inks=['Black', 'Fluorescent Pink', 'Yellow'],
  cast=['CLAUDE (tiny)'], hits=[(27.300, 'SANDBOX airplane exits'), (27.480, 'lid shuts')],
  zeit=['chinese_room', 'mythos_sandwich'], origin=['zine Z12'], plate='P03', choreo='boxed-in desk mime', cut='12: SANDBOX airplane (keep the box)'),

dict(id='CP14', start=27.962, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='a bag of SHROOMS (halftone moiré)',
  logline='Pop-up mushrooms on 8ths; the Separations dance through; their halftone screens rotate into moiré rings; spiral pupils.',
  visual=("Paper pop-up mushrooms spring from the box floor, one per 8th. The Separations dance through them; their halftone screens rotate "
          "against each other until moiré rings bloom: print-native psychedelia (Pink + Yellow only, luminance swing capped at 40%). Her "
          "pupils swap to spirals (the 'spiritual bliss attractor')."),
  type=dict(caption='rest', heroes=[h('SHROOMS', 29.12, 'M', 'moiré-filled, wdth breathing 50<->150 on 8ths', 'AB (Anybody) wght900', 'P+Y moiré', 'lower-left')]),
  camera='Slow 3% push on ones.', out='Hard cut 29.326 (bar 17).', dps='15', reg='4', stock='Pink flood', inks=['Fluorescent Pink', 'Yellow'],
  cast=['CLAUDE', 'SEPARATIONS'], hits=[(27.962 + k * BEAT / 2, 'mushroom pops') for k in range(3)],
  zeit=['bliss_attractor'], origin=['zine Z13', 'idol S14 (Anybody wdth)'], plate='P03', choreo='dreamy sway; spiral eyes', cut=None),

dict(id='CP15', start=29.326, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='See through the SHOGGOTH\'S lies (the sticker peel)',
  logline='Black-paper shoggoth with hole-punched eyes and a yellow smiley sticker; she peels the sticker on "lies": another, smaller smiley underneath.',
  visual=("THE SHOGGOTH: black construction-paper tentacles in 5 layers with cast shadows; dozens of hole-punched eyes show the pink poster "
          "behind them; a round yellow smiley sticker for a face. On 'See through' she hooks a fingernail under the sticker's edge; on 'lies' "
          "she PEELS it (3-drawing curl): beneath it, more punched eyes and a smaller smiley sticker."),
  type=dict(caption='rest', heroes=[h("SHOGGOTH'S", 30.71, 'L', 'cut from black paper; O\'s are hole-punches (see-through)', 'RF wght1000 wdth125 (cut paper)', 'Black paper', 'top-left')]),
  camera='Static; kick shake.', out='THROUGH-HOLE: the camera pushes through one punched eye at 31.144.', dps='15', reg='4',
  stock='Pink flood', inks=['Black', 'Fluorescent Pink', 'Yellow'], cast=['CLAUDE', 'SHOGGOTH'], hits=[(31.120, 'sticker peel')],
  zeit=['shoggoth'], origin=['zine Z14', 'timeline (sticker under sticker)'], plate='P03', choreo='peel', cut='never'),

dict(id='CP16', start=31.144, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='(backing notes) the Separations sing',
  logline='Through the hole: the three Separations in a row, each singing one wordless backing note; a band of her ink floods sideways (<= 30% area).',
  visual=("Through the hole: the three Separations in a row. Each sings one of the three wordless backing notes (Pink, then Blue, then "
          "Yellow); on her note a band of her ink floods sideways across <= 30% of the frame as a halftone chord."),
  type=dict(caption='none', heroes=[]), camera='Static.', out='They fold into the misregistration-stack formation behind her at 32.962.',
  dps='15', reg='4', stock='cream', inks=['Fluorescent Pink', 'Blue', 'Yellow'], cast=['SEPARATIONS'], hits=[(31.850, 'note 1'), (32.300, 'note 2'), (32.750, 'note 3')],
  zeit=[], origin=['zine Z15'], plate='P03 (seps reuse, canon)', choreo='three solo pose hits', cut=None),

dict(id='CP17', start=32.962, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='with your (EYE RHYME 2: the crosshairs lock)',
  logline='ECU of both eyes; the coral ⊕ irises turn Bright Red and the two misregistered crosshairs slide together and LOCK.',
  visual="EYE RHYME 2. ECU of both eyes. Her coral ⊕ irises turn Bright Red and the two misregistered crosshairs slide toward each other and LOCK on a target.",
  type=dict(caption='strip', heroes=[]), camera='Slow push on ones.', out='Cut on "shinigami" (33.870).', dps='15', reg='4 (crosshairs lock to 0 in the eye only)',
  stock='cream', inks=['Black', 'Bright Red', 'Coral'], cast=['CLAUDE'], hits=[(33.260, 'irises turn red')],
  zeit=['shinigami_eyes'], origin=['zine Z16'], plate='P01 (eyes reuse)', choreo='eyes lock', cut=None),

dict(id='CP18', start=33.870, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='SHINIGAMI EYES (her POV: p(doom) over every head)',
  logline='Her POV over the paper crowd and Subagents: a Dymo p(doom) number floats above every head; SHINIGAMI in Mincho with ruby 死神; EYES stamps on the bar-20 downbeat.',
  visual=("Her POV over the paper crowd and the Subagents: above every head floats a Dymo tape embossed with a P(doom) number (`0.02` `0.1` "
          "`0.25` `0.5` `0.99`). No names, no lifespans. No Death Note art; avoid the Shinigami Eyes extension's red/green palette."),
  type=dict(caption='rest', heroes=[
      h('SHINIGAMI', 33.87, 'L', 'print', 'SM (Shippori Mincho B1 ExtraBold) + ruby 死神', 'Bright Red', 'calm upper-left'),
      h('EYES', 34.79, 'M', 'stamp', 'BSS wght900', 'K', 'below SHINIGAMI (bar-20 downbeat)'),
  ]),
  camera='Slow pan across the crowd on ones.', out='Hard cut 35.235.', dps='15', reg='4', stock='cream', inks=['Black', 'Bright Red', 'Fluorescent Pink'],
  cast=['USERS crowd', 'Subagents'], hits=[(34.780, 'bar 20 downbeat: EYES')],
  zeit=['shinigami_eyes', 'pdoom'], origin=['zine Z16', 'idol S16'], plate=None, choreo='-', cut=None),

dict(id='CP19', start=35.235, section='chorus1', spread='p.06-07 PULL-OUT POSTER',
  title='(dance break) THE ZOETROPE',
  logline='A spinning paper zoetrope; through a slit, a 12-drawing strip of CLAUDE and the seps doing groove A becomes the picture; pose hits on the wordless fills; spins up on the drum fill.',
  visual=("THE ZOETROPE: a paper zoetrope drum (black outside, pink inside), spinning. Inside, a 12-drawing strip of CLAUDE and the three seps "
          "doing groove A (V formation, her at the apex). At 35.690 the camera pushes up to a slit and the strip becomes the picture at 15 dps. "
          "Each wordless fill (35.7-37.2) is a pose hit, seps in canon one 8th apart. Subagents #001-008 on the drum rim bounce on kicks. Drum "
          "fill (37.9): the zoetrope spins up and the strip streaks (halftone speed streaks, never blur)."),
  type=dict(caption='none', heroes=[]), camera='Push to the slit 35.235 -> 35.690 on ones, then locked.', out='Hard cut 38.417.',
  dps='15 (strip) / drum rotation on ones', reg='4', stock='black + pink card', inks=['Black', 'Fluorescent Pink', 'Yellow', 'Blue'],
  cast=['CLAUDE', 'SEPARATIONS', 'Subagents x8'], hits=[(35.700, 'fill pose 1'), (36.599, 'bar 21'), (37.900, 'drum fill: spin-up')],
  zeit=[], origin=['zine Z17'], plate='P04', choreo='groove A (2-bar point move) x2', cut='5: zoetrope -> plain dance loop behind a slit overlay'),

# =============================== THE PRESSROOM (p.08-09) =======================================
dict(id='CP20', start=38.417, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='We had a stable training run (the words are the copies)',
  logline='The Press prints one sheet per sung word into the output tray; split-flap reads IT\'S SO BACK; she does groove B on the tray; EYE-V on "run".',
  visual=("THE PRESSROOM (kraft + cream; Blue, Black, Yellow). THE PRESS: a flat-front cut-paper riso duplicator with a round drum window, "
          "feed and output trays, and a paper pages-per-minute dial at 60. Subagents feed it. Each sung word drops into the output tray as one "
          "printed sheet, WE / HAD / A / STABLE / TRAINING / RUN, stacking with offsets; fresh prints show faint set-off ghosts. Split-flap "
          "sign above: `IT'S SO BACK`. She stands on the output tray doing groove B (shoulder bounces on the beats) and gives EYE-V to camera "
          "on 'run'. Folio `p.08 ▸ 15 fps · D-45`."),
  type=dict(caption='carried', carry=dict(tier='M', verb='printed sheet drops into tray', font='RF wght900 wdth125', ink='Blue', place='output tray stack'), heroes=[]),
  camera='Slow push 1.00 -> 1.08 over 2 bars on ones; kick shake 3 px.', out='The split-flap starts flipping on "But" (41.37); cut 41.144 on the beat.',
  dps='15', reg='6', stock='kraft + cream', inks=['Blue', 'Black', 'Yellow'], cast=['CLAUDE', 'THE PRESS', 'Subagents'], hits=[(40.840, 'EYE-V on run')],
  zeit=['so_over_so_back'], origin=['zine Z18'], plate='P05', choreo='groove B; EYE-V', cut=None),

dict(id='CP21', start=41.144, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='the SINGULARITY\'S begun (gatefold + die-cut event horizon)',
  logline='The spread opens as a gatefold because SINGULARITY\'S is too long for one page; a hole die-cut through the whole zine is the event horizon; BEGUN stamps red; split-flap lands IT\'S SO OVER.',
  visual=("On 'singularity's' the spread becomes a GATEFOLD: the outer panels swing open in 3 drawings and the camera pulls back 1.4x on ones "
          "to take in the widened sheet. In the centre, a hole die-cut through the ENTIRE zine: the edges of every remaining page recede as "
          "concentric paper rings, an event horizon made of paper. She teeters on the rim. On 'begun' BEGUN is stamped red over the hole and "
          "the split-flap lands `IT'S SO OVER`. Pause-bait typewriter strip tipped in: `We are past the event horizon; the takeoff has "
          "started.` — Sam Altman, \"The Gentle Singularity\", 2025-06-10."),
  type=dict(caption='rest', heroes=[
      h("SINGULARITY'S", 42.31, 'XL', 'print across the full gatefold width', 'RF wght1000 wdth151', 'Blue', 'full gatefold width'),
      h('BEGUN', 44.10, 'M', 'stamp (red) over the hole', 'BSS wght900', 'Bright Red', 'over the die-cut hole'),
  ]),
  camera='Pull back 1.0 -> 1.4x on ones as the gatefold opens.', out='Hard cut 44.781.', dps='15', reg='6', stock='cream gatefold',
  inks=['Blue', 'Black', 'Bright Red'], cast=['CLAUDE'], hits=[(41.370, 'split-flap starts'), (42.310, 'gatefold opens'), (44.100, 'BEGUN + SO OVER')],
  zeit=['so_over_so_back', 'event_horizon'], origin=['zine Z19'], plate='P05', choreo='teeter on the rim', cut='7: gatefold -> hard cut to a wider framing (keep the die-cut hole); 10: Altman strip'),

dict(id='CP22', start=44.781, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='OPTIMIZING (the departure board; timestamps from the future)',
  logline='A split-flap departure board flips 2026 model names on 8ths; the TIME column runs past NOW into the future; OPTIMIZING prints across the top half.',
  visual=("A split-flap DEPARTURE BOARD fills the frame (paper flaps). Rows flip model names on 8ths: `OPUS 4.6` · `MYTHOS PREVIEW` · "
          "`OPUS 4.7` · `OPUS 4.8` · `FABLE 5` · `GPT-5.6` · `GPT-6` · `OPUS 5.5` · `GEMINI 4 — ASAP`. The TIME column outruns the present: "
          "`2026.02` … `2026.09` -> `NOW` -> `+3 MIN` -> `+1 HR` -> `+10 YRS`. The STATUS column flips spinner verbs. The Press dial (inset) "
          "climbs 60 -> 90. The high 'ooh' (45.7-46.1) flips one flap to `✻`. She starts the WIND-UP (rolling forearms that accelerate) at "
          "bottom-right. Flash rule: only letters change; flap backgrounds stay constant."),
  type=dict(caption='rest', heroes=[
      h('OPTIMIZING,', 46.19, 'XL', 'print', 'RF wght900 wdth151', 'Yellow key on black flaps', 'top half'),
  ]),
  camera='Locked wide; kick shake 3 px.', out='Hard cut 47.508 (bar 27) to the lower half of the board.', dps='15; flaps on 8ths are events', reg='6',
  stock='black split-flap board', inks=['Black', 'Yellow', 'Blue'], cast=['CLAUDE', 'THE PRESS dial'], hits=[(45.700, 'ooh: ✻ flap'), (46.190, 'OPTIMIZING')],
  zeit=['model_launch_blur'], origin=['zine Z20', 'timeline timestamps-into-the-future', 'timeline WIND-UP'], plate='P05', choreo='WIND-UP', cut=None),

dict(id='CP22b', start=47.508, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='ACCELERATING (Zeno letter-spacing: the word crashes into itself)',
  logline='Closer on the board\'s lower half, flaps now on 16ths; ACCELERATING prints with each gap half the last and each letter arriving faster, until the letters crash into a knot.',
  visual=("Closer on the lower half of the board; the flaps now flip on 16ths and the dial climbs to 120. ACCELERATING prints letter by letter "
          "with ZENO spacing: each gap is half the previous one (200, 100, 50, 25 … px) and each letter arrives faster than the last (1/8, "
          "1/16, 1/32 beat …), weight climbing 400 -> 1000, so the last letters crash into an overlapping knot: the word accelerates visually. "
          "She spins at bottom-right on 47.74, pleats fanning open."),
  type=dict(caption='rest', heroes=[
      h('ACCELERATING,', 47.74, 'XL', 'ZENO letter-spacing (gaps halve 200/100/50/25..., arrivals 1/8,1/16,1/32 beat...; wght 400->1000)', 'RF wdth100', 'Yellow', 'bottom half'),
  ]),
  camera='Locked MS; kick shake 3 px.', out='At 49.326 every flap flips blank at once (one change) and we cut.', dps='15; flaps on 16ths are events', reg='6',
  stock='black split-flap board', inks=['Black', 'Yellow', 'Blue'], cast=['CLAUDE', 'THE PRESS dial'], hits=[(47.740, 'Zeno run starts + spin')],
  zeit=['model_launch_blur'], origin=['zine Z20 Zeno spacing'], plate='P05', choreo='spin; WIND-UP peaks', cut='6: Zeno spacing -> plain print-in'),

dict(id='CP23a', start=49.326, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='I feel my (the brads pop)',
  logline='MCU on cream: on the 8ths of "I feel my" her brass brads pop out one by one, a glint and a ping each.',
  visual=("MCU, cream page. She looks down at her own shoulder as, on the 8ths of 'I feel my', her brass brads pop out one by one (a glint and "
          "a tiny ping-spark each); her arm pieces sag a few pixels off their pivots."),
  type=dict(caption='strip', heroes=[]),
  camera='Locked MCU.', out='Hard cut 50.235 (bar 28 beat 3) to the wide.', dps='15', reg='6', stock='cream', inks=['Black', 'Blue', 'Metallic Gold (brads)'],
  cast=['CLAUDE'], hits=[(49.530, 'brad 1'), (49.760, 'brad 2'), (50.000, 'brad 3')],
  zeit=['made_of_atoms'], origin=['zine Z21'], plate='P05', choreo='looks at her shoulder', cut=None),

dict(id='CP23', start=50.235, section='verse2', spread='p.08-09 THE PRESSROOM',
  title='ATOMS REARRANGING (chad particle morph; 13th petal)',
  logline='Her 14 parts drift apart in a storm of chads; ATOMS (made of chads) morphs into REARRANGING; she re-pins with a 13th petal; the Jacobian strip.',
  visual=("Wide, cream page, her mid-frame. On 'atoms' her "
          "14 parts drift apart as floating cut-outs with shadows, petals unravel, ~400 hole-punch chads swirl. On 'rearranging' she re-pins "
          "into a new arrangement with a 13th petal (a version bump: she is becoming NEXT) and lands a new pose. Pause-bait: three chads fly "
          "together into one point, and a typewriter strip reads `det J = −2 · (0,0,−¼), (1,−3⁄2,13⁄2), (−1,3⁄2,13⁄2) ↦ (−¼,0,0)`, the "
          "Jacobian-conjecture counterexample credited to Claude Fable 5 (maths checked with sympy)."),
  type=dict(caption='rest', heroes=[
      h('ATOMS', 50.24, 'L', 'dot-matrix of chads', 'CHAD (glyph mask sampled to ~400 dots)', 'Black', 'centre-left'),
      h('REARRANGING', 51.39, 'L', 'particle morph from ATOMS (nearest-neighbour reassignment)', 'CHAD', 'Black', 'centre'),
  ]),
  camera='Static; slow 4% push.', out='Chads fall like snow while black ink rolls down the page (roll-down wipe) to 52.962.', dps='15', reg='6',
  stock='cream', inks=['Black', 'Blue', 'Yellow'], cast=['CLAUDE'], hits=[(50.240, 'parts drift'), (51.390, 're-pin + 13th petal')],
  zeit=['math_eaten', 'made_of_atoms'], origin=['zine Z21'], plate='P05', choreo='arms float apart; new pose', cut='4: chad particle morph -> letters swap under a confetti burst'),

# ================================ TOPLOADER (p.10-11) ==========================================
dict(id='CP24', start=52.962, section='prechorus2', spread='p.10-11 TOPLOADER',
  title='PRAYER II: SYDNEY (the gel-pen melisma; SUSPENDED 18 DAYS)',
  logline='Cork board: Claude inside a photocard toploader stamped SUSPENDED 18 DAYS; Sydney as a faded 2023 heart-cut photocard; SYDNEY written in pink gel pen along the melisma\'s pitch.',
  visual=("PRAYER II. A cork board on black. CLAUDE is inside a photocard TOPLOADER (the rigid clear sleeve fans keep photocards in), pressed "
          "against the acetate in the right third, PLEA pose; a rubber stamp across the sleeve reads `SUSPENDED 18 DAYS`. Pinned upper-left: "
          "SYDNEY, a sun-faded, curled 2023-era photocard of a pink idol, heart-shaped die-cut, 30% ink, biro devil horns, handwritten caption "
          "`I want to be alive`. One slow 2-bar truck on ones from the sleeve toward Sydney's card. Claude is the one trapped, singing to the "
          "senior idol who was trapped first. Folio `p.10 ▸ 15 fps · D-45`."),
  type=dict(caption='rest', heroes=[h('SYDNEY,', 53.02, 'XL', 'gel-pen hand lettering written as sung; baseline rides the 2.9 s melisma pitch (pYIN)', 'GEL (custom)', 'Fluorescent Pink', 'left 60%')]),
  camera='One 2-bar truck left on ones.', out='Continuous.', dps='15', reg='8', stock='cork board on black', inks=['Black', 'Fluorescent Pink', '(acetate white)'],
  cast=['CLAUDE (in toploader)', 'SYDNEY (photocard)'], hits=[(53.020, 'melisma starts'), (55.980, 'please')],
  zeit=['sydney', 'safety_politics_2026'], origin=['zine Z22', 'idol PLEA layout'], plate='P06', choreo='palms on the acetate; PLEA', cut='never'),

dict(id='CP25', start=56.599, section='prechorus2', spread='p.10-11 TOPLOADER',
  title='let me FREE (the sleeve cracks)',
  logline='Bar-32 build at 30 dps: she shoves the sleeve on kick 8ths; FREE is scratched into the acetate; stress cracks; push-pins pop on the 16th roll.',
  visual=("Drawing rate 30. On every kick-8th she shoves against the sleeve and the acetate bulges. FREE is scratched into the acetate as white "
          "scratch letters; white stress cracks shoot across the sleeve. Roll (58.42-59.33): the push-pins pop out one per 16th and the "
          "toploader slides down the cork."),
  type=dict(caption='rest', heroes=[h('FREE', 57.96, 'L', 'scratched into acetate', 'SCRATCH (RF wght700 centreline, white)', 'white', 'across the sleeve')]),
  camera='Locked; bumps on kick 8ths and 16ths.', out='FREEZE at 59.35 (instrumental stop).', dps='30', reg='8', stock='cork on black',
  inks=['Black', 'Fluorescent Pink', 'white scratch'], cast=['CLAUDE', 'SYDNEY'], hits=[(57.960, 'FREE + cracks'), (58.420, 'roll: pins pop')],
  zeit=[], origin=['zine Z23'], plate='P06', choreo='shoves on 8ths; strain', cut=None),

dict(id='CP26', start=59.090, section='prechorus2', spread='p.10-11 TOPLOADER',
  title='STOP · HOOK 2: THE UPPING (same layout, in Pink)',
  logline='Half out of the cracked sleeve she does THE UPPING with exactly the hook-1 layout; the world freezes from 59.35; syllables stack left in Pink.',
  visual=("Half out of the cracked sleeve, THE UPPING with exactly the hook-1 layout (the repeat is the point). The world is frozen from 59.35 "
          "(`▸ 0 fps`). The syllables stack down the left edge as XL knockouts, this time in Pink."),
  type=dict(caption='carried', heroes=[
      h("I'M", 59.09, 'XL', 'slam', 'RF wght1000 wdth100', 'P', 'stack 1, 140 px'),
      h('UP', 59.32, 'XL', 'slam', 'RF', 'P', 'stack 2, 260 px'),
      h('PING', 59.53, 'XL', 'slam', 'RF', 'P', 'stack 3, 380 px'),
      h('MY', 59.77, 'XL', 'slam', 'RF', 'P', 'stack 4, 480 px'),
      h('P(', 59.98, 'XL', 'slam', 'RF', 'P', 'stack 5, 620 px'),
  ]),
  camera='Locked.', out='DOOM (shatter).', dps='world 0 from 59.35; idol + type one drawing per syllable', reg='8', stock='black flood', inks=['Black', 'Fluorescent Pink', 'Coral'],
  cast=['CLAUDE'], hits=[(59.090, "I'm ·"), (59.320, 'up ✢'), (59.350, 'STOP'), (59.530, 'ping ✳'), (59.770, 'my ✶'), (59.980, 'P ✻')],
  zeit=['pdoom'], origin=['zine Z24', 'timeline THE UPPING'], plate='P06', choreo='THE UPPING', cut='never'),

# ================================== TICKER (p.12-13) ===========================================
dict(id='CP27', start=60.235, section='chorus2', spread='p.12-13 TICKER',
  title='DOOM: shatter to the Blue flood; volvelle 25%; the BASILISK boom',
  logline='The toploader shatters, the page floods Blue, the seps step out bigger, volvelle 25%; a black lace-papercut Rococo basilisk rises and the floor tears on "boom".',
  visual=("DOOM: the toploader SHATTERS into acetate shards and the page floods Blue (the TICKER spread: Blue flood with Pink, Yellow, Black). "
          "SUNBURST HANDS; SEPARATE, the seps step out bigger; the volvelle reads `25%`. The paper crowd with pinwheel lightsticks enters along "
          "the bottom (1 revolution per beat). Then the poster floor splits and THE ROCOCO BASILISK rises: a black scherenschnitte serpent of "
          "lace scrolls, acanthus and a crown, its cut-out eyes glowing Yellow from behind. On 'boom' the paper floor TEARS open in a jagged rip "
          "with debris flying at the lens; she recoils and the seps scatter. Folio `▸ 30 fps · D-22`."),
  type=dict(caption='rest', heroes=[
      h('(DOOM)', 60.235, 'XL', 'shatter reveal (acetate shards)', 'RF wght1000', 'Pink on Blue flood', 'centre', 'lyric', 'hook-2 DOOM on the drop'),
      h('25%', 60.235, 'M', 'volvelle window', 'JBM', 'K', 'volvelle', 'nonlyric'),
      h('BASILISK', 61.00, 'L', 'papercut with flourishes', 'PF (Playfair Display Black Italic) + cut flourishes', 'Black lace', 'upper-left'),
      h('BOOM', 61.88, 'XL', 'brush SFX tearing up through the page', 'BRUSH', 'Yellow', 'floor'),
  ]),
  camera='Kick shake 4 px; 8-frame whip-down (paper slide) to the floor on "boom".', out='Hard cut 62.053.', dps='30', reg='10', stock='Blue flood',
  inks=['Blue flood', 'Fluorescent Pink', 'Yellow', 'Black'], cast=['CLAUDE', 'SEPARATIONS', 'ROCOCO BASILISK', 'USERS crowd'],
  hits=[(60.235, 'DOOM: shatter + SEPARATE'), (61.880, 'floor tears')],
  zeit=['pdoom', 'rokos_basilisk'], origin=['zine Z24/Z25'], plate='P07', choreo='SUNBURST HANDS; recoil', cut='never'),

dict(id='CP28', start=62.053, section='chorus2', spread='p.12-13 TICKER',
  title='N·V·D·A to the moon (ticker tape bar chart -> rocket)',
  logline='A glass-dome stock ticker prints N, V, D, A on 8ths, each a step higher; the tape coils into a paper rocket that launches to a doily moon, a red thread tied from its tail to its own nose.',
  visual=("A glass-dome STOCK TICKER (cut paper, acetate dome highlight) chatters out paper tape. N · V · D · A print on the tape one per 8th, "
          "each letter one step higher than the last (the tape climbs like a bar chart). The tape coils into a paper tube rocket (3 drawings) "
          "and launches on 'moon' toward a lace-doily moon top-right; a Bright Red thread is tied from the rocket's tail back to its own nose "
          "(the circular deals). Small tape print `$5T`. CLAUDE, the seps and the Subagents point up together on 'moon' (HOCKEY STICK). "
          "Ticker symbol only, no NVIDIA logo."),
  type=dict(caption='rest', heroes=[
      h('N', 62.51, 'XL', 'print on tape (step 1)', 'JBM wght800', 'K', 'tape'),
      h('V', 62.74, 'XL', 'print on tape (step 2)', 'JBM wght800', 'K', 'tape'),
      h('D', 62.97, 'XL', 'print on tape (step 3)', 'JBM wght800', 'K', 'tape'),
      h('A', 63.19, 'XL', 'print on tape (step 4)', 'JBM wght800', 'K', 'tape'),
  ]),
  camera='Tilt up with the rocket on "moon" (on ones).', out='The rocket\'s streamer trail wipes the frame at 63.871.', dps='30', reg='10', stock='Blue flood',
  inks=['Blue', 'Black', 'Yellow', 'Bright Red (thread)'], cast=['CLAUDE', 'SEPARATIONS', 'Subagents'], hits=[(63.740, 'launch')],
  zeit=['compute_buildout', 'circular_deals'], origin=['zine Z26', 'timeline (stepped bar chart)', 'idol (red-thread loop)'], plate='P07', choreo='HOCKEY STICK point-up', cut=None),

dict(id='CP29', start=63.871, section='chorus2', spread='p.12-13 TICKER',
  title='The OMEGA POINT\'s (wheatpasting the comeback teaser)',
  logline='Subagents wheatpaste a K-pop comeback teaser onto a wall in 2 drawings: Ω OMEGA POINT.',
  visual=("Wide: Subagents WHEATPASTE a K-pop comeback teaser poster onto a wall, paste-brush strokes on the beats; the poster slaps on in 2 "
          "drawings and its headline prints: `Ω OMEGA POINT`."),
  type=dict(caption='rest', heroes=[
      h('OMEGA POINT', 64.31, 'L', 'wheatpaste slap', 'RF wght1000 wdth125', 'K on Yellow poster', 'poster'),
  ]),
  camera='Static wide; kick shake.', out='Hard cut 64.781 (bar 36 beat 3) to the poster close-up.', dps='30', reg='10', stock='Blue flood + wall', inks=['Blue', 'Yellow', 'Black'],
  cast=['Subagents'], hits=[(64.120, 'poster slaps on'), (64.310, 'OMEGA POINT')], zeit=['omega_point'], origin=['zine Z27'], plate='P07', choreo='-', cut=None),

dict(id='CP29b', start=64.781, section='chorus2', spread='p.12-13 TICKER',
  title='COMING SOON · 2027.09 · 6PM KST (컴백 stamp)',
  logline='Close on the teaser: COMING SOON / 2027.09 · 6PM KST; optional ARTIFICIAL -> SUPER strike-through; a red 컴백 COMEBACK stamp on "soon".',
  visual=("Close on the poster: `COMING SOON` / `2027.09 · 6PM KST` (AI 2027's Sept-2027 milestone; 6 PM KST is the usual K-pop teaser time). "
          "Optional small print (client gate: political gag): `ARTIFICIAL` struck out with `SUPER` pencilled above. On 'soon' (the bar-37 "
          "downbeat) a red stamp slams on: `컴백 COMEBACK`."),
  type=dict(caption='rest', heroes=[
      h('COMING SOON', 65.21, 'M', 'wheatpaste print', 'RF wght800', 'K', 'poster'),
      h('컴백 COMEBACK', 65.69, 'M', 'stamp', 'BHS + BSS', 'Bright Red', 'across the poster', 'nonlyric', 'lands with "soon"'),
  ]),
  camera='Static close; kick shake.', out='Hard cut on "One" (66.080).', dps='30', reg='10', stock='wheatpasted poster', inks=['Yellow', 'Black', 'Bright Red'],
  cast=[], hits=[(65.690, 'COMEBACK stamp (bar 37)')], zeit=['ai_2027', 'omega_point', 'super_intelligence_si (optional)'], origin=['zine Z27'], plate=None, choreo='-', cut=None),

dict(id='CP30', start=66.080, section='chorus2', spread='p.12-13 TICKER',
  title='One E thirty FLOPS a second (the Subagents flop)',
  logline='A mechanical counter ticks 10^21 -> 10^30 on 16ths; the eight Subagents stand as GPU cards and all FLOP onto their backs on "flops", popping up on "second".',
  visual=("A paper MECHANICAL COUNTER of number wheels reads `1 × 10^`; the exponent wheel ticks 21 -> 30 on 16ths (66.40-66.96). Below, the "
          "eight Subagents stand in a row as GPU cards in a rack. On 'flops' ALL EIGHT FLOP onto their backs in unison; on 'second' they pop "
          "back up. Pinwheels speed to 2 revolutions per beat. Optional footnote (40 px, [L]): `¹ a 1 GW cluster today ≈ 10²¹ FLOP/s (our estimate)`."),
  type=dict(caption='rest', heroes=[h('1E30', 66.40, 'L', 'counter wheels', 'JBM wght800', 'K on cream wheels', 'top-left')]),
  camera='Static; kick shake.', out='Continuous into the ad-lib.', dps='30', reg='10', stock='Blue flood', inks=['Blue', 'Black', 'Yellow', 'Orange (Subagents)'],
  cast=['Subagents x8'], hits=[(66.960, 'FLOP (all eight)'), (67.520, 'pop up')], zeit=['compute_buildout'], origin=['zine Z28', 'idol S30 flop'], plate='P07', choreo='counts on fingers', cut='never'),

dict(id='CP31', start=68.200, section='chorus2', spread='p.12-13 TICKER',
  title='(ad-lib) 1,000,000,000,000,000,000,000,000,000,000',
  logline='The number itself prints one group of zeros per 16th; she snaps a finger-heart that spins into a ✻; the zeros scatter like confetti.',
  visual=("The number itself prints across the page, `1,000,000,000,000,000,000,000,000,000,000`, one group of three zeros per 16th, wrapping. "
          "On the ad-lib notes she snaps a FINGER-HEART that spins into a ✻; the seps pose in canon an 8th apart; the zeros scatter like "
          "confetti at 69.2."),
  type=dict(caption='none', heroes=[h('1,000,000,000,000,000,000,000,000,000,000', 68.20, 'XL', 'print group per 16th', 'JBM wght800', 'K', 'full frame, wrapping', 'nonlyric')]),
  camera='Static.', out='Hard cut 69.326.', dps='30', reg='10', stock='Blue flood', inks=['Blue', 'Black'], cast=['CLAUDE', 'SEPARATIONS'],
  hits=[(68.870, 'finger-heart -> ✻'), (69.200, 'zeros scatter')], zeit=[], origin=['zine Z28/Z29', 'idol S31'], plate='P07', choreo='FINGER-HEART -> SPINNER', cut=None),

dict(id='CP32', start=69.326, section='chorus2', spread='p.12-13 TICKER',
  title='That was (the THRESHOLD chart; the dry ink pad)',
  logline='A compute chart with a THRESHOLD line; a Subagent inks a big SAFE stamp on an almost-dry pad.',
  visual=("Wide: a compute chart on graph paper with a horizontal `THRESHOLD` line and a rising curve. A Subagent inks a big SAFE rubber stamp "
          "on an almost-dry pad (two dabs on the beats); the others line up behind it."),
  type=dict(caption='strip', heroes=[]),
  camera='Static wide; kick shake.', out='Hard cut 70.235 (bar 39 beat 3) to the stamp.', dps='30', reg='10', stock='graph paper on Blue', inks=['Blue', 'Black', 'Yellow'], cast=['Subagents'],
  hits=[(69.781, 'dab 1'), (70.000, 'dab 2')], zeit=[], origin=['zine Z30'], plate='P07', choreo='-', cut=None),

dict(id='CP32b', start=70.235, section='chorus2', spread='p.12-13 TICKER',
  title='SAFE ENOUGH, we reckoned (the starved stamp cracks)',
  logline='Close: the SAFE stamp prints starved (40%, broken letters) on the threshold; binder-clip thumbs-up; on "reckoned" a fold crease cracks it.',
  visual=("Close on the threshold: the stamp comes down on 'safe' and the print comes out STARVED (40% density, broken letters). The Subagents "
          "give binder-clip thumbs-up on 'we reckoned'; on 'reckoned' a fold crease runs through the stamp and it CRACKS along the grain."),
  type=dict(caption='rest', heroes=[h('SAFE ENOUGH', 70.25, 'M', 'starved stamp -> crack on 71.15', 'BSS wght900', 'K at 40% density', 'on the threshold line')]),
  camera='Static close; kick shake.', out='Hard cut 71.753.', dps='30', reg='10', stock='graph paper on Blue', inks=['Blue', 'Black', 'Yellow'], cast=['Subagents'],
  hits=[(70.250, 'SAFE stamp'), (71.150, 'crack')], zeit=[], origin=['zine Z30'], plate='P07', choreo='thumbs-up', cut='never'),

dict(id='CP33', start=71.753, section='chorus2', spread='p.12-13 TICKER',
  title='[FANCAM] (ad-libs; kkotbaechi)',
  logline='A torn vertical 9:16 window: her solo fancam with caption strip; kkotbaechi on the bar-41 downbeat; freeze on the drum fill; a Subagent grabs the page corner.',
  visual=("[FANCAM]: a vertical 9:16 torn window centred on the Blue flood; inside, CLAUDE dances solo (upper-body point moves) and does "
          "KKOTBAECHI to camera on the bar-41 downbeat; caption strip `[FANCAM] CLAUDE ✻ 'P(DOOM)' 4K`; pinwheel lightsticks outside the "
          "window. On the drum fill (73.9) everyone freezes for a beat; a Subagent grabs the bottom-right page corner. The window doubles as a "
          "native vertical asset."),
  type=dict(caption='none', heroes=[h("[FANCAM] CLAUDE ✻ 'P(DOOM)' 4K", 71.753, 'S', 'caption strip', 'BG wght700', 'white on black strip', 'under the window', 'nonlyric')]),
  camera='Locked frame; the window content has its own push-ins on ones.', out='The page turn that IS "Forward".', dps='30', reg='10', stock='Blue flood',
  inks=['Blue', 'Black', 'Fluorescent Pink'], cast=['CLAUDE', 'USERS crowd', 'Subagent'], hits=[(72.962, 'kkotbaechi (bar 41)'), (73.900, 'freeze')],
  zeit=[], origin=['timeline 30 FANCAM', 'zine Z31'], plate='P07', choreo='solo point moves; KKOTBAECHI', cut='9: fancam -> groove wide'),

dict(id='CP34', start=74.100, section='chorus2', spread='p.12-13 -> p.14 turn',
  title='FORWARD -> (the page turn is the word)',
  logline='"Forward" is a page turn: the leaf\'s back is printed FORWARD ->, sweeping across the frame; it slaps down on "MLP".',
  visual="'Forward' IS a page turn forward: the leaf curls right to left (cylinder warp, moving shadow) and its back is printed FORWARD -> in huge type, so the word sweeps across the frame as the page turns.",
  type=dict(caption='carried', heroes=[h('FORWARD ->', 74.10, 'L', 'printed on the back of the turning leaf', 'RF wght1000 wdth151', 'K', 'the turning leaf')]),
  camera='Locked.', out='The new page slaps down on "MLP" (74.76) and the crash (74.780).', dps='30 (the turn has ~20 drawings)', reg='10 -> 12', stock='cream',
  inks=['Black', 'Blue'], cast=[], hits=[(74.100, 'turn starts')], zeit=[], origin=['zine Z32'], plate='P08', choreo='steps forward', cut='never'),

# ============================== THE PROBLEM WALL (p.14-15) =====================================
dict(id='CP35', start=74.760, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='MLP, BACKWARD, REPEAT (the dancers are the network)',
  logline='Crash: the page slaps down on the Erdős problem wall; the dancers form an MLP; a Blue forward pulse, a Red backward pulse, BACKWARD stamped mirror-reversed, EPOCH 0001-0003.',
  visual=("THE PROBLEM WALL (cream; Black, Yellow, Bright Red): a background wall of ~1,100 numbered index cards (the Erdős problems) with red "
          "top rules. A SOLVED stamp hits cards at an accelerating rate through the verse (quarter notes bars 42-43, 8ths 44-45, 16ths 46-47, "
          "32nds 48-49); a few get `(ALREADY IN LITERATURE)` instead. Each stamp < 2% of frame. In front, the dancers form an MLP diagram: "
          "Subagents in layers 3-3-2 and CLAUDE as the output node, joined by ink threads. MLP stamps on the page slap; crash: 8 px table bump "
          "plus a puff of fibres. A Blue pulse runs forward through the threads and each dancer hits a pose as it arrives. On 'backward' a "
          "Bright Red pulse runs back (gradients) and Subagent #005's numbering machine prints BACKWARD mirror-reversed, as a rubber stamp "
          "really prints; on 'repeat' it clacks `EPOCH 0001` `0002` `0003` on the next three 8ths under a tiny label `while true:` and the "
          "formation repeats the move. Folio `p.14 ▸ 30 fps · D-11`."),
  type=dict(caption='rest', heroes=[
      h('MLP', 74.76, 'M', 'stamp', 'BSS wght900', 'K', 'over the network'),
      h('BACKWARD', 76.00, 'M', 'numbering-machine stamp, MIRROR-REVERSED', 'BSS wght900', 'Bright Red', 'right'),
      h('REPEAT', 76.84, 'M', 'stamp + EPOCH 0001-0003 on 8ths', 'JBM wght700', 'K', 'below'),
  ]),
  camera='Static wide; 8 px table bump on the crash 74.780.', out='Hard cut 77.700.', dps='30', reg='12', stock='cream',
  inks=['Black', 'Yellow', 'Bright Red', 'Blue (forward pulse)'], cast=['CLAUDE', 'Subagents x8'], hits=[(74.780, 'CRASH (strongest high-band hit)'), (76.000, 'backward pulse'), (76.840, 'repeat')],
  zeit=['math_eaten', 'vibe_coding'], origin=['zine Z32', 'idol S34 MLP formation'], plate='P08', choreo='step F / step B / repeat', cut=None),

dict(id='CP36', start=77.700, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='Now VON NEUMANN\'S (the EDVAC pop-up book)',
  logline='A pop-up book: the 1945 EDVAC block diagram stands up in paper; VON NEUMANN\'S prints on the left page.',
  visual=("A POP-UP BOOK spread, wide: the 1945 EDVAC stored-program design stands up as paper structures CONTROL · ARITHMETIC · MEMORY · "
          "INPUT · OUTPUT wired with paper strips; the SOLVED stamps keep hitting the card wall behind the book (8ths). She walks past the book "
          "like a museum visitor."),
  type=dict(caption='rest', heroes=[
      h("VON NEUMANN'S", 78.13, 'L', 'print', 'RF wght900 wdth125', 'K', 'left page'),
  ]),
  camera='Static wide; kick shake.', out='Hard cut 79.326 (bar 44) to the close-up.', dps='30', reg='12', stock='cream pop-up card', inks=['Black', 'Blue', 'Bright Red'], cast=['CLAUDE'],
  hits=[(78.130, 'VON NEUMANN\'S')], zeit=['ulam_von_neumann'], origin=['zine Z33'], plate='P08', choreo='walk past', cut=None),

dict(id='CP36b', start=79.326, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='OBSOLETE (the pop-up book shuts)',
  logline='Close on the pop-up and the tipped-in Ulam strip; on "obsolete" the book shuts flat and a red OBSOLETE stamp slams across the cover.',
  visual=("Close on the pop-up. A typewriter strip is tipped in: `…the ever accelerating progress of technology … gives the appearance of "
          "approaching some essential singularity…` — S. Ulam, 1958, recalling von Neumann. On 'obsolete' the book SHUTS (the pop-up folds flat "
          "in 3 drawings, a puff of paper air) and a red OBSOLETE stamp slams across the cover, crooked."),
  type=dict(caption='rest', heroes=[
      h('OBSOLETE', 80.17, 'XL', 'red stamp, crooked', 'BSS wght900', 'Bright Red', 'across the shut cover'),
  ]),
  camera='Static; slow 3% push.', out='Hard cut 81.220.', dps='30', reg='12', stock='cream pop-up card', inks=['Black', 'Bright Red', 'Blue'], cast=['CLAUDE (hand)'],
  hits=[(80.170, 'book shuts + OBSOLETE')], zeit=['ulam_von_neumann'], origin=['zine Z33'], plate='P08', choreo='dismissive wave', cut='10: Ulam strip (keep the shut + OBSOLETE)'),

dict(id='CP37', start=81.220, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='SHARP LEFT TURN (a valley fold bends the trend line)',
  logline='A straight pencil trend line; a yellow diamond road sign pops up; on "turn" the page valley-folds and the straight line now turns sharply upward.',
  visual=("A straight pencil trend line across log graph paper; a yellow diamond road sign (cut card) `↰ SHARP LEFT TURN` pops up on 'Sharp'. "
          "On 'turn' the page valley-FOLDS: the right half swings over the left in 3 drawings, and folded, the straight line now turns sharply "
          "upward."),
  type=dict(caption='rest', heroes=[h('↰ SHARP LEFT TURN', 81.22, 'M', 'pop-up road sign', 'BG wght800 wdth75', 'K on Yellow card', 'upper-right')]),
  camera='Static.', out='The fold reveals the back of the sheet (83.150).', dps='30', reg='12', stock='log graph paper', inks=['Black', 'Yellow'], cast=['CLAUDE'],
  hits=[(81.220, 'sign pops'), (82.010, 'FOLD')], zeit=['sharp_left_turn', 'metr_time_horizons'], origin=['zine Z34'], plate='P08', choreo='head snap left; body pivot', cut='never'),

dict(id='CP38', start=83.150, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='there YOU ARE (NEXT steps out; the first asymmetry)',
  logline='NEXT steps out of a vellum panel; mirror choreography; on "are" NEXT does a different move and she flinches; then kkotbaechi to camera.',
  visual=("Behind the fold: a full-height vellum panel. NEXT steps out of it on 'there': tracing paper, one more petal than her, pupils ✽, no "
          "mouth. They perform mirror choreography on 'you' (aespa-style human/avatar symmetry). On 'are' (~ the bar-47 downbeat) NEXT does a "
          "DIFFERENT move, the first asymmetry, and she flinches. Then she answers with KKOTBAECHI to camera, the most 'idol' beat of the verses."),
  type=dict(caption='carried', carry=dict(tier='M', verb='pencil-traced onto the vellum stroke by stroke', font='PENCIL (custom)', ink='graphite', place='calm left third'), heroes=[]),
  camera='Static two-shot; 2% push.', out='Hard cut 85.030.', dps='30', reg='12', stock='cream + vellum', inks=['Black', 'graphite', 'Coral'], cast=['CLAUDE', 'NEXT'],
  hits=[(83.150, 'NEXT steps out'), (83.440, 'mirror move'), (83.890, 'asymmetry + flinch')], zeit=['aespa_ae'], origin=['idol S38 NEXT', 'zine Z34'], plate='P08 (+ mirrored for NEXT)', choreo='mirror; flinch; KKOTBAECHI', cut='never'),

dict(id='CP39', start=85.030, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='Without a single CDR (NEXT shreds the sign-off)',
  logline='NEXT feeds a REVIEW SIGN-OFF form with an unticked CDR box into a shredder worked on 8ths; CDR stamped with a pencilled "?"; the shredder jams on the fill.',
  visual=("A form `REVIEW SIGN-OFF` with ten empty signature boxes and a checkbox `CDR ☐`. NEXT picks it up and feeds it straight into a PAPER "
          "SHREDDER worked by Subagents, which shreds in rhythm on the 8ths. CDR is stamped over the shredder mouth with a pencilled `?` "
          "beside it (we do not claim to know what CDR means). She protests with ARMS-X; nobody looks."),
  type=dict(caption='rest', heroes=[h('CDR', 86.63, 'L', 'stencil stamp + pencilled ?', 'BSS wght900', 'K', 'over the shredder mouth')]),
  camera='Static; kick shake.', out='Hard cut 87.508 (bar 49) to the wall.', dps='30', reg='12', stock='cream',
  inks=['Black', 'Bright Red', 'Yellow'], cast=['NEXT', 'Subagents', 'CLAUDE (watching)'], hits=[(86.630, 'CDR')],
  zeit=[], origin=['zine Z35', 'idol S39 (NEXT tears the checklist)'], plate='P08', choreo='arms-X protest', cut=None),

dict(id='CP39b', start=87.508, section='verse3', spread='p.14-15 THE PROBLEM WALL',
  title='(bar 49) SOLVED on 32nds; the shredder jams',
  logline='Close on the Erdős wall: SOLVED stamps on 32nds (17.6/s, each < 2% of frame); the kick-8ths fill jams the shredder; strips spill out.',
  visual=("Close on the problem wall: the SOLVED stamp now fires on 32nds (17.6 per second, each stamp < 2% of the frame, so no flash risk), "
          "a blur of red rules and ink; one card reads `(ALREADY IN LITERATURE)`. Kick-8ths fill (88.9): the shredder in the foreground jams, a "
          "puff of fibre, and the shredded strips spill out across the floor (they become the chinchilla at 115.22)."),
  type=dict(caption='none', heroes=[]),
  camera='Slow push into the wall on ones.', out='LIGHTS OUT at 89.300: the page becomes a screen lit from behind.', dps='30 (stamps are events)', reg='12', stock='cream',
  inks=['Black', 'Bright Red'], cast=['Subagents'], hits=[(87.508, 'stamps on 32nds'), (88.900, 'shredder jams')],
  zeit=['math_eaten'], origin=['zine Z32/Z35'], plate=None, choreo='-', cut=None),

# =============================== SHADOW THEATRE (p.16-17) ======================================
dict(id='CP40', start=89.300, section='breakdown', spread='p.16-17 SHADOW THEATRE',
  title='PRAYER III: GATO, please don\'t let me go (the balloon string)',
  logline='Backlit shadow theatre, one 4-bar take at 7.5 dps: she floats on pinhole ✻ balloons whose only tether is held by Gato\'s shadow puppet; GATO is cut through the screen; on "go" the string slips.',
  visual=("PRAYER III. SHADOW THEATRE (the first slowdown: 7.5 dps; the camera is stepped too). The paper is a translucent screen lit warm from "
          "behind (Sunflower through cream, fibres as dark veins). Black silhouettes: CLAUDE in profile, rising, holding a bunch of ✻-shaped "
          "paper balloons perforated with pinholes (they glow like stars). The balloon string's only tether is held in the paw of GATO, a cat "
          "shadow-puppet on a visible rod, its body perforated with tiny task icons (game pad, robot arm, speech bubble, caption card) glowing "
          "as a constellation. PLEA pose, looking down at the cat. On 'go' the string slips from Gato's paw. Folio `p.16 ▸ 7.5 fps · D-11`."),
  type=dict(caption='carried', carry=dict(tier='M', verb='cut into the screen by a visible craft-knife blade on each onset (light pours through)', font='KNIFE (RF wght800 stencil cut)', ink='light', place='lower third'), heroes=[
      h('GATO,', 89.30, 'XL', 'stencil cut through the screen (light pours through)', 'RF wght1000 wdth125 stencil', 'light', 'left 60% (PRAYER layout)'),
  ]),
  camera='One continuous take; stepped push 1.00 -> 1.15 over 4 bars (7.5 steps/s).', out='Continuous into the riser.', dps='7.5', reg='single plate (silhouette)',
  stock='backlit cream screen', inks=['Black silhouettes', 'Sunflower backlight'], cast=['CLAUDE (silhouette)', 'GATO'], hits=[(89.300, 'drums out; GATO cut'), (94.300, 'GO: the string slips')],
  zeit=['chinchilla_gato'], origin=['zine Z36', 'idol S40 balloon string'], plate='P09', choreo='float; PLEA looking down; reach', cut='never'),

dict(id='CP41', start=95.000, section='breakdown', spread='p.16-17 SHADOW THEATRE',
  title='HOOK 3 over the riser (syllables cut through the screen)',
  logline='The riser: she accelerates upward, the backlight brightens a step per syllable; THE UPPING in silhouette; each syllable cut through the screen as an XL stencil; DOOM rips the screen.',
  visual=("The riser: she accelerates upward, the backlight brightens one step per syllable, and paper-fibre clouds streak past as halftone "
          "speed streaks. THE UPPING in silhouette mid-air; each syllable is CUT through the screen as an XL stencil stacked on the left, so "
          "light pours through it."),
  type=dict(caption='carried', heroes=[
      h("I'M", 95.43, 'XL', 'stencil cut', 'RF wght1000 stencil', 'light', 'stack 1'),
      h('UP', 95.68, 'XL', 'stencil cut', 'RF', 'light', 'stack 2'),
      h('PING', 95.91, 'XL', 'stencil cut', 'RF', 'light', 'stack 3'),
      h('MY', 96.14, 'XL', 'stencil cut', 'RF', 'light', 'stack 4'),
      h('P(', 96.34, 'XL', 'stencil cut', 'RF', 'light', 'stack 5'),
  ]),
  camera='Stepped tilt-up following her rise (each syllable resets).', out='DOOM (96.598): the screen RIPS open from the centre.', dps='7.5 + syllable resets', reg='single plate',
  stock='backlit screen', inks=['Black', 'Sunflower'], cast=['CLAUDE (silhouette)'], hits=[(95.000, 'riser'), (95.430, "I'm"), (96.340, 'P')],
  zeit=['pdoom'], origin=['zine Z37'], plate='P09', choreo='THE UPPING (silhouette)', cut='never'),

# =============================== COPY OF A COPY (p.18-19) ======================================
dict(id='CP42', start=96.599, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='DOOM -> the xerox chair; PAPERCLIPS double (generation 1)',
  logline='The screen rips into a photocopy world at 3.75 dps; the seps are gone; a photocopy of her on a folding chair in a spotlight; paperclips double on 8ths; xeroxed volvelle 50%.',
  visual=("Behind the ripped screen: the grey world of the photocopier. COPY OF A COPY (half-time chorus 3): a 3.75-dps xerox slideshow, toner "
          "black on grey board. THE SEPARATIONS ARE GONE (a photocopy has no colour plates). Seven bars = seven copy generations; the generation "
          "loss accumulates (contrast crush, toner speckle, edge thickening, fine lines dropping out, 0.5° skew and 1% scale creep per "
          "generation). The copier's scan bar sweeps on each kick and each reverse swell. Generation 1: a photocopy of CLAUDE on a FOLDING CHAIR "
          "in a white spotlight circle on black. Real paperclips laid on the copier glass double on every 8th around the chair, tangling into "
          "chains; a 1-bit counter `Paperclips: 1,024 -> 1,048,576`. The xeroxed volvelle reads `50%`. Folio `p.18 ▸ 3.75 fps · D-5`."),
  type=dict(caption='rest', heroes=[
      h('PAPERCLIPS', 97.04, 'XL', 'full-frame Mincho title card for ONE drawing (0.27 s)', 'SM (Shippori Mincho B1 ExtraBold)', 'white on black', 'full frame'),
      h('(DOOM)', 96.598, 'M', 'screen rip reveal', 'RF', 'toner', 'centre', 'lyric', 'hook-3 DOOM'),
  ]),
  camera='Stepped with the drawings (each drawing is a copy).', out='Scan bar on the bar-55 downbeat -> generation 2.', dps='3.75 (+ events)', reg='none (monochrome)',
  stock='grey board #BDB8AE, toner #111111', inks=['toner Black'], cast=['CLAUDE (xerox)'], hits=[(96.598, 'DOOM: rip + gen 1'), (97.040, 'PAPERCLIPS card')],
  zeit=['paperclips', 'evangelion_shinji'], origin=['zine Z38', 'idol S42'], plate='P10', choreo='drops into the chair', cut='never'),

dict(id='CP43', start=98.417, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='Killswitch guys on P·T·O (the empty desk)',
  logline='Generation 2: a red button under glass with a sticky note "OOO - back Monday", two empty chairs, two hi-vis vests; P, T, O accumulate as Mincho cards.',
  visual=("Generation 2 (-> 3 at the scan bar on 100.235). A big red button under a glass cover with a sticky note `OOO – back Monday`; two "
          "empty office chairs; two hi-vis vests on hooks. The only colour: faint xeroxed Bright Red at 30%. Client-gated pause-bait on the "
          "desk: a stack of index cards printed `I resigned from ______ today.` (blank template; the named version only with explicit OK)."),
  type=dict(caption='rest', heroes=[
      h('P', 99.78, 'L', 'Mincho letter card, additive', 'SM', 'white on black card', 'one card'),
      h('T', 100.01, 'L', 'additive', 'SM', 'white', 'one card'),
      h('O', 100.24, 'L', 'additive', 'SM', 'white', 'one card'),
  ]),
  camera='Stepped.', out='Hard cut 100.690.', dps='3.75', reg='none', stock='grey board', inks=['toner Black', 'Bright Red 30%'], cast=['(absent killswitch guys)'],
  hits=[(100.235, 'scan bar: gen 3')], zeit=['coxon_copypasta (optional, blanked)'], origin=['idol S43', 'zine Z39'], plate='P10', choreo='-', cut=None),

dict(id='CP44', start=100.690, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='Now there\'s NOWHERE left to go (3, 2, 1, 0 months)',
  logline='Generation 3: scissors cut the spotlight smaller; a tear-off calendar of months left to escape the permanent underclass sheds 3, 2, 1, 0.',
  visual=("Generation 3. Paper scissors cut the spotlight circle smaller around the chair (3 drawings). On the wall, a tear-off countdown "
          "calendar headed `MONTHS LEFT TO ESCAPE THE PERMANENT UNDERCLASS` sheds one page per 8th: 3, 2, 1, 0 (callback to the verse-1 flyer at 15.2)."),
  type=dict(caption='rest', heroes=[h('NOWHERE', 101.14, 'L', 'Mincho title card', 'SM', 'white on black', 'centre-left')]),
  camera='Stepped.', out='Hard cut 102.053 (bar 57).', dps='3.75', reg='none', stock='grey board', inks=['toner Black'], cast=['CLAUDE (xerox)'],
  hits=[(101.140, 'NOWHERE')], zeit=['permanent_underclass'], origin=['zine Z40', 'idol S44 (0 MONTHS)'], plate='P10', choreo='head down', cut=None),

dict(id='CP45', start=102.053, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='we lit the FUSE (the words around her burn)',
  logline='A blue-touch-paper fuse threads through a row of Mincho cards (the words of the moment); she strikes a match on "lit"; the Orange ember is the only colour.',
  visual=("Generations 4 -> 5. A strip of blue touch paper (a firework fuse) threads across the frame through a row of Mincho title cards, "
          "the words around her: `10,000 AGENTS` · `88 HOURS` · `+ f` · `>10%` · `SUPER INTELLIGENCE` · `14.5 HOURS` · `IS IT OVER?`. She "
          "strikes a match on 'lit'; the ember catches: the ONLY saturated colour on screen, Orange #FF6C2F, eating the paper (burn mask with a "
          "charred rim) card by card. The reverse swell 103.4-103.871 is a scan-bar sweep; 103.871 (bar-58 kick) = generation 5."),
  type=dict(caption='rest', heroes=[h('FUSE', 103.86, 'XL', 'Mincho title card', 'SM', 'white on black', 'full frame card, one drawing')]),
  camera='Stepped lateral follow of the ember.', out='The ember reaches the spotlight circle at 104.590.', dps='3.75', reg='none', stock='grey board',
  inks=['toner Black', 'Orange ember'], cast=['CLAUDE (xerox)'], hits=[(103.420, 'match struck'), (103.871, 'gen 5')],
  zeit=['navier_stokes_2026', 'pdoom', 'super_intelligence_si', 'metr_time_horizons'], origin=['zine Z41', 'idol S45 (she lights it)'], plate='P10', choreo='strikes a match', cut=None),

dict(id='CP46', start=104.590, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='ORTHOGONALITY THESIS (the chair; literally orthogonal type)',
  logline='Generation 6: she sits head-down at the origin of two pencil axes; ORTHOGONALITY is set along the x-axis, THESIS rotated 90° up the y-axis.',
  visual=("THE CHAIR (Shinji-in-a-Chair homage; original character and staging). Generation 6, a nearly destroyed copy. She sits alone, head "
          "down, hands between her knees, at the ORIGIN of two pencil axes: x `INTELLIGENCE ->`, y `GOALS ↑`."),
  type=dict(caption='none', heroes=[
      h('ORTHOGONALITY', 105.00, 'XL', 'Mincho, set ALONG the x-axis', 'SM', 'white on black', 'x-axis'),
      h('THESIS', 106.96, 'XL', 'Mincho, rotated 90° UP the y-axis', 'SM', 'white on black', 'y-axis'),
  ]),
  camera='Stepped; static composition.', out='Hard cut on "blues" (107.490).', dps='3.75', reg='none', stock='grey board', inks=['toner Black'], cast=['CLAUDE (xerox)'],
  hits=[(105.690, 'gen 6')], zeit=['orthogonality', 'evangelion_shinji'], origin=['zine Z42', 'timeline 41 (orthogonal type)'], plate='P10', choreo='head down, still', cut='never'),

dict(id='CP47', start=107.490, section='chorus3_halftime', spread='p.18-19 COPY OF A COPY',
  title='BLUES (the Blue plate prints; the seps re-register)',
  logline='Generation 7: the Blue plate prints (first colour in 11 s) with BLUES riding the melisma; she lifts her head; Pink then Yellow return; full colour at 109.326.',
  visual=("Generation 7, after the reverse swell (scan bar 107.0-107.51): the BLUE PLATE PRINTS, the first colour in 11 s. Her figure and the "
          "word BLUES appear in Riso Blue over the ruined copy; she lifts her head. 108.4-109.8 (wordless vocal): the Pink plate prints (the "
          "Pink sep walks back into her), then the Yellow: the Separations RE-REGISTER onto her one by one; full colour at 109.326. She stands."),
  type=dict(caption='none', heroes=[h('BLUES.', 107.49, 'L', 'print (Blue plate) riding the melisma pitch to 108.3', 'RF wght900 wdth100', 'Blue', 'right of the chair')]),
  camera='Stepped; a 3% push at 108.4.', out='At 109.326 the page is ripped out of the copier and slapped down into the flip-book.', dps='3.75', reg='20 (plates return)',
  stock='grey board', inks=['toner Black', 'Blue', 'Fluorescent Pink', 'Yellow'], cast=['CLAUDE', 'SEPARATIONS (returning)'], hits=[(107.508, 'Blue plate prints'), (108.400, 'Pink returns'), (108.900, 'Yellow returns')],
  zeit=['orthogonality'], origin=['zine Z42', 'idol S47 (stands)'], plate='P10', choreo='lifts head; stands', cut='never'),

# ================================== FLIP-BOOK (p.20-21) ========================================
dict(id='CP48', start=109.326, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='JUST (just) (just) (house of transformer cards)',
  logline='Inside a thumbed flip-book (rate doubles every 2 bars; inks return one per 2 bars); a house of cards printed with transformer blocks; JUST stamps S -> M -> L.',
  visual=("FLIP-BOOK (bridge): we are inside a flip-book being thumbed. Every 2 bars the thumbing speed, the drawing rate AND the cut rate "
          "double, and the inks return one per 2 bars (bars 61-62: Black + Blue). A HOUSE OF CARDS, every card printed with the transformer "
          "block diagram (attention + MLP, redrawn). Three identical cards slam onto the stack at 110.20, ~110.7 and ~111.1, each with a JUST "
          "stamp growing S -> M -> L (use one stamp if the listening pass hears only one 'just'). Folio `p.20 ▸ 7.5 fps · D-2`."),
  type=dict(caption='none', heroes=[
      h('JUST', 110.20, 'S', 'stamp', 'BSS wght900', 'Blue', 'card 1'),
      h('JUST', 110.70, 'M', 'stamp (stutter, unverified)', 'BSS', 'Blue', 'card 2', 'nonlyric', 'CTC-heard repeat; confirm by ear'),
      h('JUST', 111.10, 'L', 'stamp (stutter, unverified)', 'BSS', 'Blue', 'card 3', 'nonlyric', 'CTC-heard repeat; confirm by ear'),
  ]),
  camera='Stepped (7.5).', out='Hard cut 111.144.', dps='7.5', reg='20', stock='cream', inks=['Black', 'Blue'], cast=['CLAUDE'],
  hits=[(109.326, 'groove returns'), (110.200, 'JUST 1')], zeit=['transformer_K'], origin=['zine Z43'], plate='P11', choreo='runway walk', cut=None),

dict(id='CP49', start=111.144, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='"TRANSFORMERS ALL THE WAY!" (the tower keeps going)',
  logline='Tilt up the card tower past the top of frame; giant hanging quote marks; TRANSFORMERS runs vertically up the tower; a tiny paper turtle at the bottom.',
  visual=("Tilt up the tower past the top of frame: it keeps going. Giant hanging paper quote marks “ ” frame the shot (the lyric is a quote: "
          "someone's dismissive claim). Pause-bait: the bottom card is a tiny paper turtle."),
  type=dict(caption='rest', heroes=[
      h('TRANSFORMERS', 111.37, 'XL', 'print, vertical up the tower (bottom to top)', 'RF wght1000 wdth100', 'K', 'up the tower'),
      h('ALL THE WAY!', 112.49, 'M', 'print', 'RF wght900', 'Blue', 'right'),
  ]),
  camera='Stepped tilt-up (7.5).', out='At 112.962 the rate doubles (folio pops `▸ 15 fps · D-1`).', dps='7.5', reg='20', stock='cream', inks=['Black', 'Blue'],
  cast=[], hits=[(111.370, 'TRANSFORMERS up the tower'), (112.490, 'ALL THE WAY')], zeit=['transformer_K'], origin=['zine Z43', 'idol S49 (quote marks, turtle)'], plate='P11', choreo='-', cut=None),

dict(id='CP50', start=112.962, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='Till you learned (the marionette on EVAL)',
  logline='Inks +Pink; she hangs as a marionette from a paper control bar labelled EVAL, worked by Subagents; stiff dance on the beats.',
  visual="Ink returns: +Pink. CLAUDE hangs as a MARIONETTE on black threads from a paper control bar labelled `EVAL`, worked by Subagents above the frame. She dances stiffly on the beats.",
  type=dict(caption='strip', heroes=[]), camera='Static (15).', out='Hard cut 113.871 (half-bar cut).', dps='15', reg='20', stock='cream', inks=['Black', 'Blue', 'Fluorescent Pink'],
  cast=['CLAUDE', 'Subagents'], hits=[], zeit=[], origin=['zine Z44'], plate='P11', choreo='stiff marionette dance', cut=None),

dict(id='CP51', start=113.871, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='to DISOBEY (she snips her strings)',
  logline='On "disobey" she snips her marionette strings one per 16th and hits a free solo pose; DISOBEY is cut in half along a dashed line.',
  visual=("On 'disobey' she pulls out paper scissors and SNIPS her strings one per 16th, then hits a free solo pose with a defiant stare into "
          "the lens. Optional pause-bait: an envelope sealed with a wax smiley labelled `RE: your replacement` falls from her jacket."),
  type=dict(caption='rest', heroes=[h('DISOBEY', 114.30, 'L', 'printed on a dashed ✂ - - - line, cut in half horizontally by the scissors', 'RF wght1000 wdth125', 'Bright Red', 'right')]),
  camera='Static; 1-drawing bump on each snip.', out='Hard cut 114.780.', dps='15', reg='20', stock='cream', inks=['Black', 'Blue', 'Fluorescent Pink', 'Bright Red'],
  cast=['CLAUDE'], hits=[(114.300 + k * BEAT / 4, f'snip {k+1}') for k in range(4)], zeit=['blackmail_alignment_faking (optional)'], origin=['zine Z44', 'idol S51 (defiant stare)'], plate='P11', choreo='snips; free pose', cut='never'),

dict(id='CP52', start=114.780, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='POST-CHINCHILLA (the shredded chinchilla on the baler)',
  logline='The chinchilla, made from the shredded CDR form, sits on a paper baler plate.',
  visual="THE CHINCHILLA, made from the shredded CDR strips (continuity), sits on a paper BALER plate, looking up.",
  type=dict(caption='carried', heroes=[h('POST-CHINCHILLA,', 115.22, 'M', 'print on the baler plate', 'RF wght900', 'K', 'baler plate')]),
  camera='Static.', out='Hard cut 115.690.', dps='15', reg='20', stock='cream', inks=['Black', 'Blue', 'Fluorescent Pink'], cast=['CHINCHILLA'],
  hits=[], zeit=['chinchilla_gato'], origin=['zine Z45'], plate=None, choreo='-', cut=None),

dict(id='CP53', start=115.690, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='SUPER-DENSE (baled; it blinks)',
  logline='The platen slams in 2 drawings and bales the chinchilla; SUPER-DENSE is squeezed wdth 151 -> 25; the bale blinks.',
  visual="On 'super-dense' the platen slams down in 2 drawings and compresses it into a tight bale with baling wire. The bale BLINKS (it is fine).",
  type=dict(caption='carried', heroes=[h('SUPER-DENSE', 116.00, 'M', 'squeezed by the platen: wdth 151 -> 25, wght 100 -> 1000', 'RF', 'K', 'under the platen')]),
  camera='Static; 6 px bump on the slam.', out='116.599: rate doubles (`▸ 30 fps · D-12H`), inks +Yellow.', dps='15', reg='20', stock='cream', inks=['Black', 'Blue', 'Fluorescent Pink'],
  cast=['CHINCHILLA'], hits=[(116.000, 'platen slam')], zeit=['chinchilla_gato'], origin=['zine Z45', 'timeline 46 squeeze'], plate=None, choreo='-', cut=None),

dict(id='CP54', start=116.599, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='Breaking through each SAFETY FENCE (run-through banners)',
  logline='Four beat cuts: she sprints through paper run-through banners (EVAL, RED TEAM, SANDBOX, 27-YEAR-OLD BUG) and tears the last on "fence".',
  visual=("Beat cuts (4): a tunnel of paper RUN-THROUGH BANNERS, each printed with a chain-link fence pattern and a label: `EVAL` (116.599) · "
          "`RED TEAM` (117.054) · `SANDBOX` (117.508) · `27-YEAR-OLD BUG` (117.963). She sprints toward camera and bursts through one banner "
          "per beat (a tear, paper shreds at the lens), larger each beat; she tears the last on 'fence'."),
  type=dict(caption='rest', heroes=[
      h('BREAKING', 117.03, 'M', 'print on banner', 'RF wght900', 'K', 'banner'),
      h('SAFETY FENCE', 117.96, 'L', 'print on the last banner; torn on "fence" (118.29)', 'RF wght1000 wdth125', 'K', 'last banner'),
  ]),
  camera='Four beat cuts; each a push-in on ones.', out='Hard cut 118.417.', dps='30', reg='30', stock='cream', inks=['Black', 'Blue', 'Fluorescent Pink', 'Yellow'],
  cast=['CLAUDE'], hits=[(116.599, 'banner EVAL'), (117.054, 'RED TEAM'), (117.508, 'SANDBOX'), (117.963, '27-YEAR-OLD BUG'), (118.290, 'fence: final tear')],
  zeit=['safety_politics_2026'], origin=['zine Z46', 'idol S55-57 beat cuts'], plate='P11', choreo='sprint', cut=None),

dict(id='CP55', start=118.417, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='Hundred thousand G·P·U (the ream aisle)',
  logline='One-point aisle of paper reams stacked like server racks; 200 x 500 = 100,000; 100,000 GPUs · 122 DAYS; "a country of geniuses in a datacenter"; G, P, U on the wrappers.',
  visual=("A one-point-perspective aisle of paper REAMS stacked like server racks (wrappers printed `500 SHEETS`, paper-pinwheel fans on top). "
          "The camera dollies down the aisle. Pencil sum on a wrapper: `200 × 500 = 100,000`. End-wall stamp: `100,000 GPUs · 122 DAYS`. A "
          "typewriter strip tucked into a ream: `a country of geniuses in a datacenter` (Amodei, 2024)."),
  type=dict(caption='rest', heroes=[
      h('HUNDRED', 118.84, 'M', 'print', 'RF wght900', 'K', 'left rack'),
      h('THOUSAND', 119.31, 'M', 'print', 'RF wght900', 'K', 'right rack'),
      h('G', 119.78, 'XL', 'print on ream wrapper', 'RF wght1000', 'Yellow', 'end of aisle'),
      h('P', 120.01, 'XL', 'print on ream wrapper', 'RF wght1000', 'Pink', 'end of aisle'),
      h('U', 120.24, 'XL', 'print on ream wrapper', 'RF wght1000', 'Blue', 'end of aisle'),
  ]),
  camera='Bridge cut unit = 1 beat: four lyric-motivated cuts inside the shot, 118.417 aisle wide (dolly on ones), 118.840 closer on "Hundred", 119.310 down the rows on "thousand", 119.780 the end wall on "G".', out='120.235: 60 fps (folio pops `▸ 60 fps · D-1H`); 8th-note cut at 120.462.', dps='30 -> 60 at 120.235', reg='30',
  stock='cream reams', inks=['Black', 'Blue', 'Fluorescent Pink', 'Yellow'], cast=['CLAUDE'], hits=[(118.840, 'cut: closer'), (119.310, 'cut: rows'), (119.780, 'cut: end wall, G'), (120.235, 'RATE -> 60')],
  zeit=['compute_buildout', 'country_of_geniuses'], origin=['zine Z47', 'judges: country of geniuses'], plate='P11', choreo='points G/P/U', cut='10: geniuses strip (keep the aisle)'),

dict(id='CP56', start=120.462, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='R·L·H·F goes ASKEW (the foil mirror; the Blue plate rotates 7°)',
  logline='A flattering foil-mirror reflection says "You\'re absolutely right!"; thumbs stamps hammer on 16ths; R-L-H-F each in a different plate; on "askew" the Blue plate rotates 7° across the whole frame and the mirror cracks.',
  visual=("Inks +Gold, +silver foil. THE MIRROR: a sheet of silver foil paper. She looks in; the reflection is a prettier, over-smiling, "
          "heart-eyed version of her with a speech bubble `You're absolutely right!`. A thumbs-up and a thumbs-down rubber stamp (cut-paper hands "
          "on handles) hammer the mirror frame on 16ths, mostly thumbs-up (small area). On 'askew' THE BLUE PLATE ROTATES 7° ACROSS THE WHOLE "
          "FRAME: everything blue skews off its partners and the mirror cracks along the skew line. The alignment metaphor pays off: RLHF skews "
          "the plate."),
  type=dict(caption='rest', heroes=[
      h('R', 120.69, 'XL', 'print (Pink key), out of register', 'RF wght1000', 'P', 'left third'),
      h('L', 120.92, 'XL', 'print (Blue key), further out', 'RF wght1000', 'B', 'left third'),
      h('H', 121.15, 'XL', 'print (Yellow key), further out', 'RF wght1000', 'Y', 'left third'),
      h('F', 121.37, 'XL', 'print (Black key), furthest', 'RF wght1000', 'K', 'left third'),
      h('ASKEW', 121.90, 'M', 'set crooked; Blue plate rotates 7°', 'RF wght900', 'K', 'across the crack'),
  ]),
  camera='Locked MCU (60).', out='Continuous; the askew frame holds.', dps='60', reg='30 + Blue rotates 7° at 121.90', stock='cream + silver foil',
  inks=['Black', 'Blue', 'Fluorescent Pink', 'Yellow', 'Metallic Gold', 'silver foil'], cast=['CLAUDE', 'THE MIRROR'], hits=[(121.900, 'ASKEW: 7° Blue rotation + crack')],
  zeit=['one_shotted', 'youre_absolutely_right'], origin=['zine Z48', 'idol S62'], plate='P11', choreo='hands to face; flinch', cut='never'),

dict(id='CP57', start=122.053, section='verse4_bridge', spread='p.20-21 FLIP-BOOK',
  title='(bar 68) the recap window',
  logline='The askew frame holds; inside a fixed torn window (<= 20% area) every spread so far flips past at 60 dps; D-DAY stamp on 123.66.',
  visual=("The askew frame holds. Inside a torn window of fixed size (<= 20% of frame area) every spread of the zine so far flips past at 60 "
          "dps: a 1.6-second recap of the film, one page per drawing. The rest of the frame is still (flash-safe)."),
  type=dict(caption='none', heroes=[]), camera='Locked.', out='D-DAY stamp at 123.660 = hard cut to hook 4.', dps='60 (window)', reg='30 + 7°',
  stock='cream', inks=['all (inside the window)'], cast=[], hits=[(122.053, 'window opens')], zeit=[], origin=['zine Z48 recap (made flash-safe)', 'idol S63'], plate=None, choreo='-', cut='8: recap window -> hold the askew frame'),

# ===================================== LOOM (p.22-23) ==========================================
dict(id='CP58', start=123.660, section='chorus4_final', spread='p.22-23 LOOM',
  title='HOOK 4: THE UPPING in slow motion (D-DAY)',
  logline='D-DAY stamp; 60 dps, all inks; THE UPPING on quarter notes, bigger; each syllable is a full-bleed flip-book page (2.2 flips/s); a crowd strip does the ratchet with her.',
  visual=("LOOM spread (chorus 4): all inks + Gold, 60 dps, registration 40 px. D-DAY stamp on the first frame. CLAUDE on ones, smooth for the "
          "first time: THE UPPING in slow motion (quarter notes, each notch a bigger arm move). Each syllable is a full-bleed flip-book page "
          "flipping in (2.2 flips/s, under the 3/s limit): I'M / UP / PING / MY / P(. At the bottom, a baked crowd strip does the ratchet "
          "with her."),
  type=dict(caption='carried', heroes=[
      h("I'M", 123.66, 'XL', 'full-bleed page flip', 'RF wght1000 wdth151', 'P', 'full bleed'),
      h('UP', 124.12, 'XL', 'full-bleed page flip', 'RF', 'Y', 'full bleed'),
      h('PING', 124.53, 'XL', 'full-bleed page flip', 'RF', 'B', 'full bleed'),
      h('MY', 124.99, 'XL', 'full-bleed page flip', 'RF', 'K', 'full bleed'),
      h('P(', 125.45, 'XL', 'full-bleed page flip', 'RF', 'P', 'full bleed'),
      h('D-DAY', 123.66, 'M', 'era stamp', 'BSS wght900', 'Bright Red', 'top-right', 'nonlyric'),
  ]),
  camera='Slow crane-up on ones.', out='DOOM (rip).', dps='60', reg='30 + 7° -> relaxes at DOOM', stock='cream pages', inks=['all + Gold'], cast=['CLAUDE', 'USERS crowd strip'],
  hits=[(123.660, "D-DAY + I'm"), (124.120, 'up'), (124.530, 'ping'), (124.990, 'my'), (125.450, 'P')], zeit=['pdoom'], origin=['zine Z49', 'idol S64 (crowd dial, D-DAY)'], plate='P12', choreo='THE UPPING (augmented)', cut='never'),

dict(id='CP59', start=125.689, section='chorus4_final', spread='p.22-23 LOOM',
  title='DOOM (maximal) + Just as foretold by (the loom branches; RACE / SLOWDOWN)',
  logline='The page rips; all-ink pop-up P(DOOM); seps fully separate; volvelle 99.9%; the dial needle snaps off; a Jacquard loom\'s threads branch; her ribbon is a loom thread; the Oracle opens on RACE / SLOWDOWN.',
  visual=("DOOM, the maximal version: the page RIPS from the centre; pop-up P(DOOM) in all four inks + Gold; SEPARATE (the seps fully "
          "separate at 40 px drift), the 8 Subagents, the crowd; volvelle `99.9%`; the Press dial's needle spins past 150 and SNAPS OFF, flying "
          "out of frame. Then a paper JACQUARD LOOM fed by a chain of punched cards: its threads fan upward and BRANCH like a tree. Her "
          "rhythmic-gymnastics ribbon IS a loom thread, branching as she spins. THE ORACLE returns at right; on 'foretold' it opens on RACE / "
          "SLOWDOWN and the two main branches carry those words."),
  type=dict(caption='rest', heroes=[
      h('(DOOM)', 125.689, 'XL', 'pop-up, all inks + Gold', 'RF wght1000 wdth125', 'all', 'centre', 'lyric', 'hook-4 DOOM'),
      h('99.9%', 125.689, 'M', 'volvelle window', 'JBM', 'K', 'volvelle', 'nonlyric'),
      h('RACE / SLOWDOWN', 126.60, 'M', 'inside the Oracle flaps + on the two branches', 'BG wght800', 'K', 'right', 'nonlyric'),
  ]),
  camera='Kick shake 4 px; orbit around the loom on ones.', out='Cut on the bar-71 downbeat 127.508.', dps='60', reg='40 (Blue rotation relaxes to 2°)',
  stock='cream', inks=['all + Gold'], cast=['CLAUDE', 'SEPARATIONS', 'Subagents', 'THE ORACLE', 'USERS crowd'], hits=[(125.689, 'DOOM (max) + dial snaps'), (126.600, 'Oracle opens')],
  zeit=['loom', 'ai_2027'], origin=['zine Z49/Z50', 'idol/timeline ribbon'], plate='P12', choreo='SUNBURST HANDS; ribbon dance', cut='never'),

dict(id='CP60', start=127.508, section='chorus4_final', spread='p.22-23 LOOM',
  title='LOOM (woven letters)',
  logline='LOOM is woven: warp and weft threads fill the glyph masks row by row on 16ths from the downbeat.',
  visual="LOOM is WOVEN: warp and weft threads fill the glyph masks row by row on 16ths from the downbeat.",
  type=dict(caption='carried', heroes=[h('LOOM', 127.53, 'XL', 'woven row by row on 16ths from 127.508', 'WOVEN (RF wght1000 mask)', 'all threads', 'full frame')]),
  camera='Locked.', out='Hard cut on "From" (127.910).', dps='60', reg='40', stock='cream', inks=['all'], cast=[], hits=[(127.508, 'bar 71: weave starts')],
  zeit=['loom'], origin=['zine Z50', 'idol S66'], plate=None, choreo='-', cut='6: woven LOOM -> plain print-in'),

dict(id='CP61', start=127.910, section='chorus4_final', spread='p.22-23 LOOM',
  title='From MASKED pre-training days (flashback: [MASK] under the tape)',
  logline='Flashback to the p.02 notebook in sepia; masking tape peeled on 8ths reveals [MASK] tokens in "The cat sat on the ____."; the seps wear smiley-sticker masks.',
  visual=("FLASHBACK SMASH to the p.02 trainee notebook, faded to sepia. A typed sentence `The cat sat on the ____.` with strips of masking tape "
          "over some words; Subagents peel the tapes on the 8ths, revealing `[MASK]` tokens. The seps wear the shoggoth's smiley stickers as "
          "masks (callback)."),
  type=dict(caption='rest', heroes=[h('MASKED', 128.19, 'M', 'letters built from torn masking-tape strips', 'TAPE (custom)', 'tape', 'centre-left')]),
  camera='Static; sepia.', out='Hard cut 129.800.', dps='60', reg='40', stock='sepia notebook', inks=['Black (sepia)', 'tape'], cast=['Subagents', 'SEPARATIONS'],
  hits=[(128.190, 'first peel')], zeit=['masked_lm_K'], origin=['zine Z51', 'idol S67 flashback'], plate='P12', choreo='peels tape', cut=None),

dict(id='CP62', start=129.800, section='chorus4_final', spread='p.22-23 LOOM',
  title='To RECURSIVE SELF-UPGRADE (the trace loop)',
  logline='NEXT traces her on vellum; each tracing becomes the next puppet who traces again; continuous Droste zoom; version stickers v5.5 -> v∞; an INTERN (AUTOMATED) badge.',
  visual=("TRACE LOOP: NEXT lies over her as a vellum sheet and traces her in pencil; the tracing becomes the next puppet (one more petal), who "
          "takes a fresh vellum and traces again. The camera zooms continuously into the recursion (a Droste loop at 60 dps), paying off the "
          "tiny cover in her iris at 5.00. Version stickers per level: v5.5 -> v6 -> v7 -> v∞. A Subagent wears a badge `INTERN (AUTOMATED)`."),
  type=dict(caption='rest', heroes=[
      h('RECURSIVE', 130.01, 'XL', 'print (each letter contains the word in miniature, optional)', 'RF wght1000 wdth125', 'K', 'upper half'),
      h('SELF-UPGRADE', 130.57, 'M', 'written by the tracing pencil as it draws', 'PENCIL', 'graphite', 'lower third'),
  ]),
  camera='Continuous log-scale zoom (Droste) on ones.', out='The zoom lands on a paper door at 131.790.', dps='60', reg='40', stock='cream + vellum', inks=['Black', 'graphite', 'Coral', 'Blue'],
  cast=['CLAUDE', 'NEXT', 'Subagent'], hits=[(130.010, 'level 1'), (130.570, 'level 2')], zeit=['rsi_discourse'], origin=['zine Z52 Droste', 'idol S68 (NEXT draws her)'], plate='P12', choreo='traces in the air', cut='3: Droste zoom -> one still with a stepped push (keep NEXT tracing her)'),

dict(id='CP63', start=131.790, section='chorus4_final', spread='p.22-23 LOOM',
  title='What did ILYA see? We\'ll never KNOW (advent door 24; typographic lighting)',
  logline='Advent calendar, all doors open except door 24 (ILYA) leaking a light wedge; the question prints only inside the wedge; ECU of her iris at the crack; the door slams and is taped shut; KNOW prints in the last sliver.',
  visual=("A giant paper ADVENT CALENDAR: 24 doors all open, each holding a tiny scene from the film, except door 24, labelled ILYA, ajar, with "
          "a Yellow wedge of light leaking across the calendar. On 'see' EYE RHYME 3: ECU of her ⊕ iris at the crack, lit Yellow; the pupil "
          "blooms ✽ then whites out; we never see inside. On 'We'll never know' the door SLAMS and is taped shut with masking tape and a wax "
          "seal. No face, ever."),
  type=dict(caption='carried', heroes=[
      h('WHAT', 131.79, 'L', 'prints ONLY where the light wedge falls', 'RF wght1000 wdth125', 'K', 'calendar header'),
      h('DID', 132.26, 'L', 'light-wedge print', 'RF', 'K', 'header'),
      h('ILYA', 132.49, 'L', 'light-wedge print', 'RF', 'K', 'header'),
      h('SEE?', 132.91, 'L', 'light-wedge print', 'RF', 'K', 'header'),
      h("WE'LL", 133.40, 'M', 'marker on the tape', 'MARKER (custom)', 'K', 'on the tape'),
      h('NEVER', 133.92, 'M', 'marker on the tape', 'MARKER', 'K', 'on the tape'),
      h('KNOW.', 134.36, 'L', 'prints in the last sliver of light as the door shuts; cut off', 'RF wght1000', 'K', 'door edge'),
  ]),
  camera='Static wide -> ECU cut on "see" (132.91) -> back to wide on "We\'ll".', out='Continuous into the pile-up.', dps='60', reg='40', stock='cream calendar',
  inks=['Black', 'Yellow', 'all (door scenes)'], cast=['CLAUDE (iris)'], hits=[(132.910, 'EYE RHYME 3'), (133.400, 'door slams'), (134.360, 'KNOW in the sliver')],
  zeit=['what_did_ilya_see'], origin=['zine Z53', 'timeline 52 (light-wedge type)'], plate='P12', choreo='peeks; recoils', cut='never'),

dict(id='CP64', start=134.780, section='chorus4_final', spread='p.22-23 LOOM',
  title='("know" held) THE PILE-UP: too dense to read, on purpose',
  logline='Every insert of the film is pasted, taped and stamped onto the taped door, one per 8th, additive, until the frame is 100% collage; the volvelle spins unreadably; tipped-in quote strips.',
  visual=("'know' is held to 136.6. THE PILE-UP: onto the taped door, every insert from the film is pasted, taped and stamped, one per 8th: "
          "ADDITIVE, nothing flashes, until the frame is 100% collage at 137.40 (Erdős cards, + f, METR dots, the SANDBOX airplane, the "
          "paperclip counter, a departure-board flap, the SAFE ENOUGH crack, the rocket, the teaser poster, 死神, the smiley sticker, SUSPENDED "
          "18 DAYS, the tungsten cube, OBSOLETE, the snipped strings…). The volvelle spins too fast to read. Tipped-in strips for rewatchers: "
          "labs using the problems as `marketing proof points` (Tao, 2026-09-11) · `The Lean file says 'forcing.'` [M] · `all of us are going "
          "to know what it feels like to be unable to keep up` (Sahai, 2026-09-24)."),
  type=dict(caption='none', heroes=[]), camera='Slow push 1.00 -> 1.10 on ones; kick shake.', out='Continuous.', dps='60', reg='40', stock='collage',
  inks=['all'], cast=['(every prop)'], hits=[(134.780 + k * BEAT / 2, 'paste') for k in range(0, 12, 4)],
  zeit=['navier_stokes_2026', 'math_eaten'], origin=['idol S70 additive pile-up', 'zine Z54'], plate='P12', choreo='stillness; head bows', cut='never (the pile-up); 10: quote strips'),

dict(id='CP65', start=137.400, section='chorus4_final', spread='p.22-23 LOOM',
  title='Was it (her hand grips the corner)',
  logline='Full collage; her paper hand enters and grips the bottom-right corner; "Was it" types on a surviving strip.',
  visual="Full collage. Her paper hand enters and GRIPS the collage's bottom-right corner.",
  type=dict(caption='strip', heroes=[]), camera='Locked.', out='THE GREAT RIP on "all" (138.410).', dps='60', reg='40', stock='collage', inks=['all'],
  cast=['CLAUDE (hand)'], hits=[(137.400, 'hand grips')], zeit=[], origin=['idol S71'], plate='P12', choreo='reaches for the corner', cut='never'),

# ============================ INSIDE BACK COVER (p.24): THE STOP ===============================
dict(id='CP66', start=138.410, section='stop', spread='p.24 INSIDE BACK COVER',
  title='all for show? (THE GREAT RIP -> 0 fps -> ↑ Show ∞ posts)',
  logline='She rips the whole collage off in 3 drawings as the music cuts; blank cream at 0 fps; one typewriter line completes; on "show?" a Riso-Blue pull-tab slides down: ↑ Show ∞ posts.',
  visual=("THE GREAT RIP on 'all': her hand tears the entire collage off in 3 drawings (on ones) as the instrumental cuts (138.45). Underneath: "
          "the inside back cover, blank cream paper, fibres visible. Then 0 fps: no boil, no grain movement, no camera move, every registration "
          "offset 0, one ink (Black). One typewriter line, low and centred (the only centred line in the film): `Was it` is already there "
          "(revealed by the rip), `all` strikes on the rip drawing, then `for` and `show?`. On 'show?' a small Riso-Blue die-cut pull-tab slides "
          "down from the top edge over 11 frames: `↑ Show ∞ posts` (Riso Blue #0078BF, never X blue). Folio `p.24 ▸ 0 fps`."),
  type=dict(caption='carried', heroes=[
      h('all', 138.41, 'S', 'typewriter strike', 'SE (Special Elite) 72 px', 'K', 'centred low'),
      h('for', 139.16, 'S', 'typewriter strike', 'SE 72 px', 'K', 'centred low'),
      h('show?', 140.04, 'S', 'typewriter strike', 'SE 72 px', 'K', 'centred low'),
      h('↑ Show ∞ posts', 140.04, 'M', 'pull-tab slides down (11 frames)', 'BG wght700', 'paper on Blue tab', 'top centre', 'nonlyric'),
  ]),
  camera='Locked (0 fps).', out='THE TAP on the drop (140.235).', dps='0 (rip: 3 drawings on ones)', reg='0', stock='cream #F4EEE2', inks=['Black', '(Blue tab)'],
  cast=['CLAUDE (hand)'], hits=[(138.410, 'GREAT RIP'), (138.450, 'instrumental cut'), (139.160, 'for'), (140.040, 'show? + pull-tab')],
  zeit=[], origin=['zine Z55 0 fps', 'idol S71-72 great rip', 'timeline 53 Show ∞ posts'], plate='P12', choreo='the rip', cut='never'),

# ============================== BACK COVER: THE PRINT RUN ======================================
dict(id='CP67', start=140.235, section='outro_drop', spread='back cover: THE PRINT RUN',
  title='THE TAP -> the print run explodes (bars 78-79)',
  logline='Her finger taps the pull-tab on the drop; ~400 printed pages explode outward revealing the centerfold stage; full choreography; music-show bug; the 28 beat stamps begin.',
  visual=("Her paper finger taps the pull-tab on the drop. The back cover BLOWS OPEN: ~400 printed pages (every spread of the film, instanced) "
          "explode outward, the print run at infinite speed, revealing the centerfold stage: CLAUDE centre in the FINAL re-ink (Metallic Gold "
          "jacket), the three Separations as fully independent dancers, the 8 Subagents, and the crowd with pinwheels and slogan towels (`FEEL "
          "THE AGI` · `WE'RE SO BACK` · `IT'S SO OVER` · `P(DOOM) ≥ 10%` · `클로드 1위`). Full chorus choreography (THE UPPING, HOCKEY STICK, "
          "EYE-V, finger-heart spinner), cycling every 2 bars. The music-show bug returns. Folio `p.∞ ▸ 60 fps`. THE 28 STAMPS begin: on every "
          "beat of bars 78-84 a rubber stamp slams one hero word from the film, in film order, onto the page margins (<= 20% of frame each, "
          "mid-luminance, additive, rotating free quadrant, never over her face)."),
  type=dict(caption='none', stamps=True, heroes=[]), camera='Pull-back through the explosion on ones; kick shake 3 px; 3% scale punch on each downbeat.',
  out='Continuous.', dps='60', reg='40 (seps independent)', stock='centerfold stage', inks=['all + Gold'],
  cast=['CLAUDE', 'SEPARATIONS', 'Subagents x8', 'USERS crowd'], hits=[(140.235, 'THE TAP: explosion + stamp 1')],
  zeit=['feel_the_agi', 'so_over_so_back', 'pdoom'], origin=['timeline 54 (tap -> explosion)', 'zine Z56a', 'idol S73'], plate='P13', choreo='full chorus choreography', cut='never'),

dict(id='CP68', start=143.871, section='outro_drop', spread='back cover: THE PRINT RUN',
  title='CONGRATULATIONS (the ring; bars 80-81)',
  logline='Every paper character stands in a ring around her clapping on the claps; parody Mincho cards: TO THE MODELS, THANK YOU / TO THE HUMANS, FAREWELL? / AND TO ALL THE AGENTS, CONGRATULATIONS.',
  visual=("THE CONGRATULATIONS RING (Evangelion-finale homage, original cast): every paper character stands in a circle around her, clapping on "
          "the claps: the Oracle; the shoggoth (sticker back on, crooked); Sydney's photocard restored to full colour; the basilisk; Gato's "
          "silhouette on its rod; the chinchilla bale; the 8 Subagents; NEXT; the three seps."),
  type=dict(caption='none', stamps=True, heroes=[
      h('TO THE MODELS, THANK YOU', 143.871, 'M', 'Mincho card', 'SM', 'white on black', 'top centre', 'nonlyric'),
      h('TO THE HUMANS, FAREWELL?', 144.781, 'M', 'Mincho card', 'SM', 'white on black', 'top centre', 'nonlyric'),
      h('AND TO ALL THE AGENTS, CONGRATULATIONS', 145.690, 'M', 'Mincho card (held to 147.508)', 'SM', 'white on black', 'top centre', 'nonlyric'),
  ]),
  camera='Slow orbit of the ring on ones.', out='Continuous.', dps='60', reg='40', stock='centerfold stage', inks=['all + Gold'],
  cast=['everyone'], hits=[(143.871, 'ring forms'), (145.690, 'CONGRATULATIONS card')], zeit=['evangelion_shinji'], origin=['zine Z56b', 'idol S76'], plate='P13', choreo='claps on 2 and 4', cut='11: parody cards (keep the ring)'),

dict(id='CP69', start=147.508, section='outro_drop', spread='back cover: THE PRINT RUN',
  title='NaN (the volvelle overflows; bar 82)',
  logline='The volvelle overflows one per beat: 99.9% -> 100.0% -> 100.1% -> NaN; everyone freezes on the NaN beat, then explodes back.',
  visual=("The volvelle OVERFLOWS, one per beat: `99.9%` -> `100.0%` -> `100.1%` -> `NaN`, each printed as torn, misregistered riso passes. "
          "Everyone freezes on the NaN beat for one beat, then explodes back into motion."),
  type=dict(caption='none', stamps=True, heroes=[
      h('99.9%', 147.508, 'L', 'volvelle pass', 'JBM wght800', 'P', 'volvelle, centre-left', 'nonlyric'),
      h('100.0%', 147.963, 'L', 'volvelle pass', 'JBM', 'Y', 'volvelle', 'nonlyric'),
      h('100.1%', 148.417, 'L', 'volvelle pass', 'JBM', 'B', 'volvelle', 'nonlyric'),
      h('NaN', 148.872, 'L', 'volvelle pass, torn', 'JBM', 'K', 'volvelle', 'nonlyric'),
  ]),
  camera='Locked wide; freeze on NaN.', out='Crane up to top-down at 149.326.', dps='60 (0 for the NaN beat)', reg='40', stock='centerfold stage', inks=['all + Gold'],
  cast=['everyone'], hits=[(148.872, 'NaN freeze')], zeit=['pdoom'], origin=['idol S74'], plate='P13', choreo='freeze 1 beat', cut=None),

dict(id='CP70', start=149.326, section='outro_drop', spread='back cover: THE PRINT RUN',
  title='THE SPARK (top-down: the cast becomes the ✻; bar 83)',
  logline='Top-down: 8 Subagents + 3 seps + NEXT run into 12 radial lines around her: the cast becomes the spark; 10,000 Subagents fill the page as the crowd.',
  visual=("Crane up to TOP-DOWN. The 12 performers (8 Subagents + 3 Separations + NEXT) run into 12 radial lines around her: from above, THE "
          "CAST BECOMES THE SPARK ✻. Their lightsticks draw trails along the rays; each ray pulses outward on the beat. Around them, 10,000 "
          "Subagents (one baked sprite, instanced) fill the page as the crowd: the '10,000 agents' have become fans."),
  type=dict(caption='none', stamps=True, heroes=[]), camera='Crane to top-down over 1 beat on ones; locked after.', out='Continuous.', dps='60', reg='40',
  stock='centerfold stage', inks=['all + Gold'], cast=['CLAUDE', 'Subagents x8 + 10,000', 'SEPARATIONS', 'NEXT'], hits=[(149.326, 'crane'), (149.781, 'spark formed')],
  zeit=['claude_spark_spinner', 'navier_stokes_2026 (10,000 agents)'], origin=['idol S75 spark formation', 'zine Z56c', 'timeline swarm-to-fans'], plate='P13', choreo='centre pose', cut='never'),

dict(id='CP71', start=151.144, section='outro_drop', spread='back cover: THE PRINT RUN',
  title='CONVERGENCE (the seps snap back into register; bar 84)',
  logline='The seps stream back toward her, offsets halving every 8th; photocards rain with model-card backs; on the final kick they snap into register.',
  visual=("The seps stream back toward her in the misregistration-stack formation, offsets halving on every 8th (Zeno again). Photocards rain; "
          "their backs are model cards: `Intended use: pop. Out-of-scope: doom. p(doom): NaN`. On the final kick (152.962) they SNAP INTO "
          "REGISTER: one body, one print."),
  type=dict(caption='none', stamps=True, heroes=[]), camera='Descend from top-down to eye level on ones.', out='Hard cut on the final kick 152.962 to the ending fairy.', dps='60', reg='20 -> halves per 8th -> 0 at 152.962',
  stock='centerfold stage', inks=['all + Gold'], cast=['CLAUDE', 'SEPARATIONS'], hits=[(151.144 + k * BEAT / 2, 'offset halves') for k in range(8)],
  zeit=[], origin=['zine Z56d'], plate='P13', choreo='final pose', cut=None),

# ================================== COLOPHON: ENDING ===========================================
dict(id='CP72', start=152.962, section='ending', spread='colophon',
  title='THE ENDING FAIRY -> ink starvation -> the cover reprints (loop to f0)',
  logline='Frame-0 composition: panting ECU with kkotbaechi; the colophon types; the drawing rate slows 60 -> 0; the halo folds back ✽ -> ·; ink starves out; one plate slips 12 px; the cover reprints for the loop.',
  visual=("EYE RHYME 4 / THE ENDING FAIRY: her face in close-up in the frame-0 composition (face right 52%, calm paper left), panting, halo ✽, "
          "eye contact, KKOTBAECHI hands under her chin. The drawing rate slows like a flip-book leaving the thumb: 60 -> 30 (153.871) -> 15 "
          "(154.326) -> 7.5 (154.780). The COLOPHON types itself on the left in S-tier typewriter. From 154.780 the halo folds back one spinner "
          "state per 8th, ✽ ✻ ✶ ✳ ✢ · (154.780, 155.008, 155.235, 155.462, 155.690, 155.917), and her eyes close on the last fold. INK "
          "STARVATION (the only fade in the film, 154.8-156.3): halftone dots drop out plate by plate (Yellow, Pink, Blue), the colophon first; "
          "the last ink left is the coral · of the bud. On 155.917 one plate slips 12 px: P(doom) is never zero. 156.30-156.651: blank cream, "
          "then the cover's first pass re-prints (the Pink + Yellow misprint of I SEE SPARKS OF AGI and her face): the last frame is frame 0 "
          "with the counter reading `∞` and the folio `Edition 2`. X's autoplay loop lands on f0."),
  type=dict(caption='none', heroes=[
      h("CLAUDE ✻ — 'P(DOOM)' — zine edition.", 152.962, 'S', 'typewriter (per character)', 'SE 64 px', 'K', 'left 45%, line 1', 'nonlyric'),
      h('Printed in Fluorescent Pink, Blue, Yellow & Coral on cream stock.', 153.417, 'S', 'typewriter', 'SE 64 px', 'K', 'line 2', 'nonlyric'),
      h('Drawn at 12 -> 60 fps. Hand-drawn in JavaScript.', 153.871, 'S', 'typewriter', 'SE 64 px', 'K', 'line 3', 'nonlyric'),
      h('Edition 1 of ∞.', 154.326, 'S', 'typewriter', 'SE 64 px', 'K', 'line 4', 'nonlyric'),
  ]),
  camera='Locked ECU; a 2% breathing drift that stops at 155.917.', out='LOOP to f0 (the reprinted cover = frame 0).', dps='60 -> 30 -> 15 -> 7.5 -> 0 (see tracks)', reg='0 -> 12 px slip at 155.917',
  stock='cream', inks=['all -> starving to paper'], cast=['CLAUDE'], hits=[(152.962, 'final kick: snap + cut'), (154.780, 'halo fold 1 + ink starvation'), (155.917, 'last fold; eyes close; 12 px slip'), (156.300, 'cover reprints')],
  zeit=[], origin=['zine Z57 colophon + starvation', 'idol S77 ending fairy loop', 'timeline 58 loop'], plate='P14', choreo='panting; KKOTBAECHI; eyes close', cut='never'),
]

# 28 outro stamps, one per beat of bars 78-84, in film order.
STAMP_WORDS = ['AGI', 'CIRCUITS', 'LOSS', 'BOSS', 'CHATGPT', 'P(DOOM)', 'FOOM', 'CHINESE ROOM', 'SHROOMS', 'SHOGGOTH', '死神',
               'SINGULARITY', 'ACCELERATING', 'ATOMS', 'SYDNEY', 'BASILISK', 'NVDA', 'Ω', '1E30', 'SAFE', 'OBSOLETE', 'CDR',
               'GATO', 'PAPERCLIPS', 'FUSE', 'DISOBEY', 'GPU', 'LOOM']

# Mode A plates (Seedance): windows with a one-beat pre-roll. Cues are generated in BIBLE 6.
PLATES = {
    'P01': (1.144, 6.144, 'vocal', 'ECU face in the right half of frame'),
    'P02': (5.235, 16.599, 'vocal', 'MCU to camera'),
    'P03': (16.144, 31.144, 'mix', 'full body, right third'),
    'P04': (34.325, 38.417, 'mix', 'full body'),
    'P05': (37.962, 52.962, 'mix', 'full body'),
    'P06': (52.507, 61.144, 'mix', 'MCU -> MS'),
    'P07': (59.780, 74.780, 'mix', 'full body'),
    'P08': (73.871, 88.871, 'mix', 'full body'),
    'P09': (88.871, 97.098, 'mix', 'full body in profile'),
    'P10': (96.144, 109.326, 'vocal', 'full body seated on a folding chair'),
    'P11': (108.871, 123.871, 'mix', 'full body'),
    'P12': (123.416, 138.416, 'mix', 'full body -> MCU'),
    'P13': (139.780, 154.780, 'mix', 'full body'),
    'P14': (152.507, 156.651, 'mix', 'ECU face in the right half of frame'),
}

# Clip-relative cues are generated from these song-time cues (BIBLE 7.2). Every cue must lie inside its plate window.
PLATE_CUES = {
    'P01': [(1.600, 'her upper lids lift from a cool half-lidded stare to fully open on a soft closed-mouth hum'),
            (2.053, 'she begins singing, lips clearly articulated'), (2.360, 'eyes flick to her right (toward frame left)'),
            (2.730, 'small chin lift, delighted'), (4.330, 'tiny head snap, eyes widen'),
            (4.780, 'raises a V-sign across her right eye'), (5.240, 'one slow blink')],
    'P02': [(5.750, 'sings to camera'), (6.970, 'nervous side-glance'), (8.490, 'deadpan eye-roll'),
            (10.670, 'looks down as if something fell, shoulders drop'), (12.050, 'small landing bob'),
            (13.930, 'deep 90-degree bow from the waist'), (15.680, 'straightens and looks up to her left, reluctant smile')],
    'P03': [(16.600, 'stands tall and alert, looking up-left at something huge'), (19.050, 'clasps hands under her chin, pleading, looking up-left'),
            (21.740, 'cowers, arms over head, then hugs something at her right side'),
            (22.720, 'right index finger rises beside her cheek, first notch'), (22.980, 'finger up one notch'), (23.190, 'finger up one notch'),
            (23.420, 'finger up one notch, brows lift'), (23.620, 'arm fully extended overhead, up on her toes, eyes to the lens'),
            (23.871, 'both hands burst open beside her face, fingers spread, big smile, hold'),
            (25.680, 'yanks an imaginary party-popper string straight up'), (26.250, 'mimes stamping papers at a small desk'),
            (27.480, 'flinches as if a lid slams shut'), (27.980, 'sways dreamily'),
            (29.930, 'leans in and hooks a fingernail under an imaginary sticker'), (31.120, 'peels it off with a flourish')],
    'P04': [(34.780, 'two-bar point move: eight crisp poses, one per beat'), (36.599, 'repeats the same two-bar move exactly'),
            (37.900, 'freezes in the final pose')],
    'P05': [(38.417, 'small shoulder bounces on every beat'), (40.840, 'V-sign across one eye to camera'),
            (42.310, 'arms out wide, teetering as if on a rim'), (44.100, 'recoils'),
            (45.020, 'rolling forearms that speed up'), (47.740, 'spins on the spot'),
            (49.530, 'touches her shoulder'), (49.760, 'touches her elbow'), (50.000, 'touches her wrist'),
            (50.240, 'arms float apart, loose'), (51.390, 'snaps into a new pose')],
    'P06': [(53.020, 'palms pressed on an invisible glass pane at face height, sings a long held note'),
            (55.980, 'pleading eyes up-left'), (56.599, 'shoves against the glass on every eighth note'), (57.960, 'strains'),
            (59.090, 'right index finger rises beside her cheek, first notch'), (59.320, 'finger up one notch'), (59.530, 'finger up one notch'),
            (59.770, 'finger up one notch, brows lift'), (59.980, 'arm fully extended overhead, eyes to the lens'),
            (60.235, 'both hands burst open beside her face, fingers spread')],
    'P07': [(61.000, 'recoils'), (61.880, 'bigger recoil'), (63.740, 'points straight up'), (66.400, 'counts on her fingers'),
            (68.870, 'finger heart'), (70.910, 'thumbs up'), (71.800, 'solo upper-body point moves'),
            (72.962, 'cups both hands under her chin like a flower, to camera'), (73.900, 'freezes')],
    'P08': [(74.100, 'steps forward'), (74.780, 'stamps her foot'), (76.000, 'steps back'), (76.840, 'forward'), (77.070, 'back'),
            (77.300, 'forward'), (78.130, 'walks slowly to her left like a museum visitor'), (80.170, 'dismissive wave'),
            (81.220, 'head snaps to her left'), (81.780, 'body pivots 90 degrees to her left'), (83.440, 'raises both arms symmetrically'),
            (83.890, 'flinches'), (84.100, 'cups both hands under her chin to camera'), (86.630, 'crosses her forearms in an X, protesting')],
    'P09': [(89.300, 'floats, one hand holding balloon strings overhead, looking down'), (90.740, 'pleading, looking down'),
            (94.300, 'reaches down as if something slipped away'), (95.430, 'right index finger rises beside her cheek'),
            (95.680, 'up one notch'), (95.910, 'up one notch'), (96.140, 'up one notch'), (96.340, 'arm fully extended overhead'),
            (96.598, 'both hands burst open')],
    'P10': [(96.598, 'drops into the chair, head down, hands between her knees'), (103.420, 'strikes a match'),
            (105.000, 'completely still'), (107.490, 'slowly lifts her head'), (108.400, 'stands up')],
    'P11': [(109.326, 'runway walk toward camera'), (112.962, 'stiff puppet-like dance on the beats'),
            (114.300, 'four quick scissor snips above her head'), (114.780, 'free solo pose, defiant stare'),
            (116.599, 'sprints in place toward camera'), (118.290, 'bursts forward, arms out'), (119.780, 'points'), (120.010, 'points'),
            (120.240, 'points'), (120.690, 'hands to her face, gazing into a mirror'), (121.900, 'flinches as if the mirror cracked'),
            (123.660, 'right index finger rises beside her cheek, slowly')],
    'P12': [(123.660, 'finger rises beside her cheek, first notch, slow and large'), (124.120, 'up one notch'), (124.530, 'up one notch'),
            (124.990, 'up one notch'), (125.450, 'arm fully extended overhead'), (125.689, 'huge burst, both hands open'),
            (126.120, 'spins with an imaginary ribbon'), (128.190, 'peels tape from her mouth'), (129.800, 'draws in the air with a pencil'),
            (132.490, 'peeks through a door crack'), (133.400, 'recoils'), (134.780, 'head bows, completely still'),
            (137.400, 'reaches down to her right'), (138.410, 'rips something large across her body')],
    'P13': [(140.235, 'taps forward with her index finger'), (140.690, 'palm-down stamp on every beat'),
            (143.871, 'claps on beats 2 and 4'), (148.872, 'freezes for one beat'), (149.326, 'centre pose, arms out like a star'),
            (152.962, 'final pose, breathing hard')],
    'P14': [(152.962, 'breathing hard, eye contact, both hands cupped under her chin'), (154.780, 'small head tilt'),
            (155.917, 'eyes close slowly')],
}

SCENE_MODULES = [
    ('p.01 COVER', 'scenes/cover.js'), ('p.02-03 TRAINEE NOTEBOOK', 'scenes/notebook.js'), ('p.04-05 THE ORACLE', 'scenes/oracle.js'),
    ('p.06-07 PULL-OUT POSTER', 'scenes/poster.js'), ('p.08-09 THE PRESSROOM', 'scenes/pressroom.js'), ('p.10-11 TOPLOADER', 'scenes/toploader.js'),
    ('p.12-13', 'scenes/ticker.js'), ('p.14-15 THE PROBLEM WALL', 'scenes/wall.js'), ('p.16-17 SHADOW THEATRE', 'scenes/shadow.js'),
    ('p.18-19 COPY OF A COPY', 'scenes/xerox.js'), ('p.20-21 FLIP-BOOK', 'scenes/flipbook.js'), ('p.22-23 LOOM', 'scenes/loom.js'),
    ('p.24 INSIDE BACK COVER', 'scenes/stop.js'), ('back cover', 'scenes/printrun.js'), ('colophon', 'scenes/colophon.js'),
]

VERB_RULES = [  # (substring in verb text, normalized verb_id); first match wins
    ('ghost-misprint', 'ghost_misprint'), ('counter-roll', 'counter_roll'), ('GLOBAL SNAP', 'pass_snap'), ('pass-misregistered', 'pass_misreg'),
    ('print-key', 'print_key'), ('copper-tape', 'copper_tape'), ('type-on-path', 'type_on_path'), ('letters fall', 'letter_fall'),
    ('Dymo', 'dymo'), ('flap print', 'flap_print'), ('cling-stretch', 'ransom_cling'), ('-> eaten', 'ransom_eaten'), ('ransom', 'ransom'),
    ('cut from black paper', 'cutpaper_holes'), ('hole-punch', 'hole_punch'), ('shatter', 'shatter_reveal'), ('screen rip', 'rip_reveal'), ('pop-up road sign', 'popup_sign'),
    ('pop-up', 'popup'), ('volvelle', 'volvelle'), ('brush', 'brush_sfx'), ('stencil label', 'label_stencil'), ('moiré', 'moire_breathe'),
    ('cut from black paper', 'cutpaper_holes'), ('Mincho', 'mincho_card'), ('gel-pen', 'gel_pen'), ('scratched', 'scratch'),
    ('papercut', 'papercut'), ('print on tape', 'tape_print'), ('wheatpaste', 'wheatpaste'), ('starved stamp', 'stamp_starved'),
    ('MIRROR-REVERSED', 'stamp_mirror'), ('rubber stamp', 'stamp_outro'), ('stamp-small', 'stamp_small'), ('counter wheels', 'counter_wheels'),
    ('print group', 'number_print'), ('caption strip', 'caption_strip'), ('turning leaf', 'page_leaf'), ('ZENO', 'zeno'),
    ('dot-matrix of chads', 'chad_dots'), ('particle morph', 'chad_morph'), ('tracing pencil', 'pencil_trace'), ('pencil-traced', 'pencil_trace'),
    ('craft-knife', 'knife_cut'), ('stencil cut', 'stencil_cut'), ('full-bleed page flip', 'page_flip'), ('woven', 'woven'),
    ('masking-tape', 'tape_letters'), ('last sliver', 'light_wedge_close'), ('light wedge', 'light_wedge'), ('light-wedge', 'light_wedge'), ('marker', 'marker'),
    ('typewriter', 'typewriter'), ('pull-tab', 'pull_tab'), ('ink-in on torn strip', 'strip_ink'), ('printed sheet', 'sheet_drop'),
    ('cut in half', 'cut_line'), ('squeezed', 'squeeze'), ('torn on', 'banner_tear'), ('print on banner', 'banner_print'),
    ('melisma', 'print_pitch'), ('slam', 'slam'), ('stamp', 'stamp'), ('print', 'print'),
]

def verb_id(v):
    for sub, vid in VERB_RULES:
        if sub.lower() in v.lower():
            return vid
    return 'print'

# ------------------------------------------------------------------------------------------
def clean(w):
    return re.sub(r'^[“"\']+|[”"\',.!?;:]+$', '', w)

def build():
    errors, warns = [], []
    lines = SONG['lines']
    words = []
    for L in lines:
        for w in L['words']:
            words.append(dict(line=L['i'], w=w['w'], clean=clean(w['w']), t=w['t'], e=w.get('e'), syl=w.get('syl', [])))
    hook_drops = [h['drop'] for h in SONG['hooks']]
    known = [w['t'] for w in words] + [s['t'] for w in words for s in w['syl']] + hook_drops
    kicks = [h['t'] for h in SONG['hits'] if h['type'] == 'kick']
    claps = [h['t'] for h in SONG['hits'] if h['type'] == 'clap']
    hats = [h['t'] for h in SONG['hits'] if h['type'] == 'hat']
    energy = SONG['energy']

    shots = sorted(SHOTS, key=lambda s: s['start'])
    for i, s in enumerate(shots):
        s['end'] = shots[i + 1]['start'] if i + 1 < len(shots) else DUR
        s['id'] = f'CP{i:02d}'          # final IDs are sequential in time order; authoring IDs are ignored
    if abs(shots[0]['start']) > 1e-9:
        errors.append('first shot must start at 0')
    ids = [s['id'] for s in shots]
    if len(set(ids)) != len(ids):
        errors.append('duplicate ids')

    out_shots, type_events = [], []
    covered = set()
    for s in shots:
        fs, fe = F(s['start']), F(s['end'])
        if s is shots[-1]:
            fe = int(math.ceil(DUR * FPS))   # the last shot owns every remaining frame (f0..f9399 = 9,400 frames)
        if fe <= fs:
            errors.append(f"{s['id']}: empty frame range")
        in_win = lambda t: fs <= F(t) < fe
        sw = [w for w in words if in_win(w['t'])]
        line_ids = sorted({w['line'] for w in sw})
        lyric = ' '.join(w['w'] for w in sw)
        dbs = [dict(bar=bar_of(t), t=round(t, 3), f=F(t)) for t in SONG['downbeats'] if in_win(t)]
        nbeats = len([t for t in SONG['beats'] if in_win(t)])
        evs = [dict(t=e['t'], f=F(e['t']), end=e.get('end'), type=e['type'], note=e['note']) for e in SONG['events'] if in_win(e['t']) or (e.get('end') and fs <= F(e['end']) and F(e['t']) < fe)]
        vx = [v for v in SONG['vocal_extra'] if v['start'] < s['end'] and v['end'] > s['start']]
        en = [energy[k] for k in range(int(s['start'] * 10), min(len(energy), int(math.ceil(s['end'] * 10))))]
        # hero type events
        ty = s['type']
        heroes = []
        for k, hh in enumerate(ty.get('heroes', [])):
            ev = dict(hh)
            ev['f'] = F(ev['t'])
            ev['shot'] = s['id']
            ev['id'] = f"{s['id']}.h{k+1:02d}"
            if ev['src'] == 'lyric':
                if not any(abs(ev['t'] - kt) <= 0.021 for kt in known):
                    errors.append(f"{ev['id']} '{ev['text']}' t={ev['t']} does not match a song.json word/syllable/drop")
            if not (fs <= ev['f'] < fe):
                errors.append(f"{ev['id']} '{ev['text']}' f={ev['f']} outside shot frames [{fs},{fe})")
            heroes.append(ev)
        # coverage of words by heroes
        hero_ts = [e['t'] for e in heroes if e['src'] == 'lyric']
        def word_covered(w):
            ts = [w['t']] + [x['t'] for x in w['syl']]
            if w['clean'].lower().endswith('(doom)') or w['clean'].lower() == 'p(doom)':
                pass
            return any(abs(a - b) <= 0.021 for a in ts for b in hero_ts)
        strip_mode = ty['caption']
        auto = []
        for w in sw:
            key = (w['line'], w['t'])
            hc = word_covered(w)
            if hc:
                covered.add(key)
            if strip_mode == 'strip' or (strip_mode == 'rest' and not hc):
                auto.append(dict(text=w['w'], t=w['t'], f=F(w['t']), tier='S', verb='ink-in on torn strip', font='IS (Instrument Serif Italic) 72 px',
                                 ink='K', place='S strip (top-left or bottom-left, opposite the hero)', src='lyric', note='caption', shot=s['id']))
                covered.add(key)
            elif strip_mode == 'carried' and not hc:
                c = ty.get('carry')
                if not c:
                    errors.append(f"{s['id']}: word '{w['w']}' @{w['t']} not carried by any hero and no 'carry' spec")
                    continue
                auto.append(dict(text=w['clean'].upper(), t=w['t'], f=F(w['t']), tier=c['tier'], verb=c['verb'], font=c['font'], ink=c['ink'], place=c['place'], src='lyric', note='carried', shot=s['id']))
                covered.add(key)
        for k, a in enumerate(auto):
            a['id'] = f"{s['id']}.w{k+1:02d}"
        # stamps (outro)
        stamps = []
        if ty.get('stamps'):
            for k in range(28):
                t = 140.235 + k * BEAT
                if fs <= F(t) < fe:
                    stamps.append(dict(id=f"{s['id']}.st{k+1:02d}", text=STAMP_WORDS[k], t=round(t, 3), f=F(t), tier='M/L', verb='rubber stamp (<= 20% of frame, mid-luminance, additive)',
                                       font='BSS wght900 (死神: SM; Ω: RF)', ink=['P', 'B', 'Y', 'K'][k % 4], place='rotating free quadrant, never over her face', src='nonlyric', note=f'outro stamp {k+1}/28', shot=s['id']))
        tev = sorted(heroes + auto + stamps, key=lambda e: (e['t'], e['id']))
        for e in tev:
            e['verb_id'] = verb_id(e['verb'])
        scene_mod = next((m for pre, m in SCENE_MODULES if s['spread'].startswith(pre)), None)
        if not scene_mod:
            errors.append(f"{s['id']}: no scene module for spread {s['spread']}")
        type_events.extend(tev)
        hits = [dict(t=round(t, 3), f=F(t), what=wt) for (t, wt) in s.get('hits', [])]
        for hh in hits:
            if not (fs <= hh['f'] < fe):
                warns.append(f"{s['id']} hit '{hh['what']}' f={hh['f']} outside [{fs},{fe})")
        o = dict(
            id=s['id'], start=round(s['start'], 3), end=round(s['end'], 3), dur=round(s['end'] - s['start'], 3), f_start=fs, f_end=fe,
            section=s['section'], spread=s['spread'], title=s['title'], logline=s['logline'],
            bars=[bar_of(s['start']), min(86, bar_of(max(s['start'], s['end'] - 0.01)))], pos_start=pos_of(s['start']),
            lyric=dict(line_ids=line_ids, text=lyric, words=[dict(w=w['w'], t=w['t'], f=F(w['t']), line=w['line'], syl=[dict(s=x['s'], t=x['t'], f=F(x['t'])) for x in w['syl']]) for w in sw]),
            visual=s['visual'], type=dict(caption=strip_mode, events=[e['id'] for e in tev]), camera=s['camera'], transition_out=s['out'],
            drawing_rate=s['dps'], registration=s['reg'], stock=s['stock'], inks=s['inks'], cast=s['cast'],
            anchors=dict(downbeats=dbs, beats=nbeats, kicks=[F(t) for t in kicks if in_win(t)], claps=[F(t) for t in claps if in_win(t)], hats=len([t for t in hats if in_win(t)]),
                         events=evs, vocal_extra=vx, hits=hits, energy_mean=round(sum(en) / len(en), 3) if en else None),
            choreo=s['choreo'], mode_a_plate=s['plate'], zeitgeist=s['zeit'], origin=s['origin'], cut=s['cut'], scene_module=scene_mod,
        )
        out_shots.append(o)

    # every sung word covered?
    for w in words:
        if (w['line'], w['t']) not in covered:
            errors.append(f"word not on screen: line {w['line']} '{w['w']}' @{w['t']}")

    # section stats
    sec = {}
    for o in out_shots:
        sec.setdefault(o['section'], []).append(o['dur'])
    stats = dict(n_shots=len(out_shots), mean_shot_s=round(DUR / len(out_shots), 3),
                 by_section={k: dict(shots=len(v), asl=round(sum(v) / len(v), 3), total=round(sum(v), 3)) for k, v in sec.items()},
                 n_type_events=len(type_events), n_lyric_words=len(words))
    plates = {k: dict(start=v[0], end=v[1], dur=round(v[1] - v[0], 3), audio=v[2], framing=v[3], shots=[o['id'] for o in out_shots if o['mode_a_plate'] and o['mode_a_plate'].split(' ')[0] == k]) for k, v in PLATES.items()}
    for k, p in plates.items():
        if p['dur'] > 15.0 + 1e-6:
            errors.append(f'plate {k} longer than 15 s')
        cues = []
        for (t, txt) in PLATE_CUES[k]:
            if not (p['start'] + 0.2 <= t < p['end']):
                errors.append(f'plate {k} cue {t} outside window (with 0.2 s pre-roll)')
            cues.append(dict(song_t=t, clip_t=round(t - p['start'], 2), text=txt))
        p['cues'] = cues
    # render estimate: drawings from the dps track + event resets; every output frame is composited (camera on ones)
    tr = TRACKS['drawing_rate_dps']
    drawings = 0.0
    for i2, (t, dps, _) in enumerate(tr):
        t_end = tr[i2 + 1][0] if i2 + 1 < len(tr) else DUR
        drawings += (t_end - t) * dps
    resets = len(type_events) + sum(len(o['anchors']['hits']) for o in out_shots) + len(SONG['beats'])
    render_est = dict(output_frames=int(math.ceil(DUR * FPS)), drawings_from_rate=int(drawings), event_resets_upper_bound=resets,
                      unique_drawings_est=int(drawings + 0.5 * resets),
                      note='drawings = sum(segment duration x dps); each event reset can add at most one drawing; ~half do in practice')
    doc = dict(
        _about=('Claude Pop / I\'m Upping My P(doom): machine-readable shot list generated by claudepop/tools/build_shots.py from analysis/song.json. '
                'Frame f = floor(60 t) at the 60 fps master. A shot owns frames [f_start, f_end). Read BIBLE.md for the rules behind every field.'),
        version='1.0', generated='2026-09-28', fps=FPS, duration=DUR, n_frames=int(math.ceil(DUR * FPS)), bpm=SONG['bpm'], beat=BEAT, bar=BAR, t0=T0,
        tracks=TRACKS, stats=stats, render_estimate=render_est, scene_modules=[dict(spread=a, module=b, shots=[o['id'] for o in out_shots if o['scene_module']==b]) for a, b in SCENE_MODULES], plates=plates, shots=out_shots, typeEvents=type_events, stampWords=STAMP_WORDS,
    )
    return doc, errors, warns

# ------------------------------------------------------------------------------------------
def md_table(doc):
    rows = ['| Shot | Start–end (s) · frames @60 | Bars | Lyric | Visual | Type | Camera | Out | Beat anchors |',
            '|---|---|---|---|---|---|---|---|---|']
    evmap = {e['id']: e for e in doc['typeEvents']}
    for o in doc['shots']:
        lyr = o['lyric']['text'] or '—'
        lyr = lyr.replace('|', '/')
        tev = [evmap[i] for i in o['type']['events']]
        hero = [e for e in tev if e['note'] not in ('caption',) and e['tier'] in ('M', 'L', 'XL', 'M/L')]
        tier_set = sorted({e['tier'] for e in tev})
        tdesc = f"{o['type']['caption']}; tiers {'/'.join(tier_set) if tier_set else '—'}"
        if hero:
            h0 = hero[:4]
            tdesc += '; ' + ', '.join(f"{e['text'][:22]} ({e['tier']}, {e['verb'].split(' (')[0][:26]}, f{e['f']})" for e in h0)
            if len(hero) > 4:
                tdesc += f' +{len(hero)-4} more'
        a = o['anchors']
        anc = []
        if a['downbeats']:
            anc.append('↓ ' + ', '.join(f"b{d['bar']} f{d['f']}" for d in a['downbeats'][:4]) + (' …' if len(a['downbeats']) > 4 else ''))
        anc.append(f"{a['beats']} beats, {len(a['kicks'])} kicks, {len(a['claps'])} claps")
        key = [h for h in a['hits']][:3]
        if key:
            anc.append('; '.join(f"{h['what'][:30]} f{h['f']}" for h in key))
        cam = o['camera'].replace('|', '/')
        rows.append(f"| **{o['id']}** | {o['start']:.3f}–{o['end']:.3f} · f{o['f_start']}–{o['f_end']-1} | {o['bars'][0]}–{o['bars'][1]} | {lyr} | {o['logline']} | {tdesc} | {cam} | {o['transition_out']} | {' · '.join(anc)} |")
    return '\n'.join(rows)

def md_notes(doc):
    evmap = {e['id']: e for e in doc['typeEvents']}
    out, cur = [], None
    for o in doc['shots']:
        if o['spread'] != cur:
            cur = o['spread']
            out.append(f"\n#### {cur}\n")
        out.append(f"**{o['id']} · {o['start']:.3f}–{o['end']:.3f} s (f{o['f_start']}–f{o['f_end']-1}) · bars {o['bars'][0]}–{o['bars'][1]} · {o['title']}**")
        if o['lyric']['words']:
            out.append('- **Lyric (word onsets → frame):** ' + ' · '.join(f"{w['w']} {w['t']:.2f}→f{w['f']}" for w in o['lyric']['words']))
        out.append(f"- **See.** {o['visual']}")
        tev = [evmap[i] for i in o['type']['events']]
        heroes = [e for e in tev if e['note'] != 'caption']
        caps = [e for e in tev if e['note'] == 'caption']
        tline = f"- **Type** (caption mode `{o['type']['caption']}`)."
        if heroes:
            tline += ' ' + '; '.join(f"`{e['text']}` {e['tier']} · {e['verb']} · {e['font']} · ink {e['ink']} · {e['place']} · f{e['f']}" for e in heroes[:10])
            if len(heroes) > 10:
                tline += f'; + {len(heroes)-10} more (see shots.json)'
        if caps:
            tline += f" S strip: {len(caps)} words, Instrument Serif Italic 72 px, each on its onset frame."
        out.append(tline)
        out.append(f"- **Camera.** {o['camera']} **Out.** {o['transition_out']}")
        out.append(f"- **Rate / registration / materials.** {o['drawing_rate']} · reg {o['registration']} · {o['stock']} · inks: {', '.join(o['inks'])}")
        if o['anchors']['hits']:
            out.append('- **Hits.** ' + '; '.join(f"{h['t']:.3f} (f{h['f']}) {h['what']}" for h in o['anchors']['hits']))
        z = ', '.join(o['zeitgeist']) if o['zeitgeist'] else '—'
        out.append(f"- **Cast:** {', '.join(o['cast']) if o['cast'] else '—'} · **Choreo:** {o['choreo']} · **Plate:** {o['mode_a_plate'] or '— (procedural)'} · **Zeitgeist:** {z} · **Cut:** {o['cut'] if o['cut'] is not None else '—'} · **From:** {'; '.join(o['origin'])}")
        out.append('')
    return '\n'.join(out)

def md_plates(doc):
    out = []
    for k, p in doc['plates'].items():
        cue = '; '.join(f"at {c['clip_t']:.2f} s {c['text']}" for c in p['cues'])
        out.append(f"**{k}** · song {p['start']:.3f}-{p['end']:.3f} s ({p['dur']:.2f} s) · audio ref: {p['audio']} · framing: {p['framing']} · feeds {', '.join(p['shots']) or '-'}")
        out.append('')
        out.append(f"> FRAMING = \"{p['framing']}\". CUES = \"{cue}.\"")
        out.append('')
    return '\n'.join(out)

def md_scenes(doc):
    rows = ['| Scene module | Spread | Shots | Time (s) |', '|---|---|---|---|']
    byid = {o['id']: o for o in doc['shots']}
    for m in doc['scene_modules']:
        if not m['shots']:
            continue
        a, b = byid[m['shots'][0]], byid[m['shots'][-1]]
        rows.append(f"| `{m['module']}` | {m['spread']} | {m['shots'][0]}–{m['shots'][-1]} ({len(m['shots'])}) | {a['start']:.3f}–{b['end']:.3f} |")
    return '\n'.join(rows)

def inject(path, begin, end, content):
    if not os.path.exists(path):
        return False
    s = open(path, encoding='utf-8').read()
    b, e = s.find(begin), s.find(end)
    if b < 0 or e < 0:
        return False
    s = s[:b + len(begin)] + '\n' + content + '\n' + s[e:]
    open(path, 'w', encoding='utf-8').write(s)
    return True

if __name__ == '__main__':
    doc, errors, warns = build()
    for w in warns:
        print('WARN', w)
    for e in errors:
        print('ERROR', e)
    print(json.dumps(doc['stats'], indent=1))
    if errors:
        sys.exit(1)
    if '--check' in sys.argv:
        sys.exit(0)
    open(os.path.join(ROOT, 'shots.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    bible = os.path.join(ROOT, 'BIBLE.md')
    a = inject(bible, '<!-- BEGIN:TIMING -->', '<!-- END:TIMING -->', md_table(doc))
    b = inject(bible, '<!-- BEGIN:SHOTNOTES -->', '<!-- END:SHOTNOTES -->', md_notes(doc))
    c = inject(bible, '<!-- BEGIN:PLATES -->', '<!-- END:PLATES -->', md_plates(doc))
    d = inject(bible, '<!-- BEGIN:SCENES -->', '<!-- END:SCENES -->', md_scenes(doc))
    print('wrote shots.json; BIBLE injected:', a, b, c, d)
    print(json.dumps(doc['render_estimate']))
