# REFERENCE: the anabology film, donald's film and the original Claude Pop

Research date: 2026-09-28. Every figure below was measured from the downloaded videos or fetched from the cited
source on that date. Engagement numbers are snapshots from the fxtwitter/vxtwitter JSON mirrors, fetched 2026-09-28
around 10:00 UTC.

Local material (all gitignored, under `claudepop/out/refs/`):

| File | What |
|---|---|
| `anabology_1080.mp4` | anabology's film, 1920x1080, 24 fps, 306.48 s, AAC 44.1 kHz (353 MB) |
| `donald_1080.mp4` | donald's film, 1920x1080, 30 fps, 141.57 s |
| `claudepop_other_reality_720.mp4` | the "Claude Pop" post by other__reality, 1280x720, 24 fps, 156.63 s |
| `ana/t2/`, `ana/sheets_t2/` | one frame every 2 s plus labelled 4x4 contact sheets |
| `ana/full/`, `ana/crops/` | full-resolution frames and HUD, ticker, type and dither crops |
| `ana/seg_*_sheet/` | 0.5 s and 1/6 s strips of key passages (runway walk, title card, chorus drop, highway) |
| `ana/scenes.txt`, `ana/cuts_merged.txt` | cut detection (ffmpeg scene score above 0.25, and above 0.10 with merging) |
| `ana/asr.txt`, `don/asr.txt` | faster-whisper large-v3 transcripts of both soundtracks |
| `json/` | post JSON, reply threads, donald's full prompt (`donald_prompt.txt`) |

## 0. The ten things that matter

1. **Our brief is donald's prompt, word for word.** The 9,608-character reply donald posted on 2026-09-23 as his
   "full prompt" matches HANDOFF.md section 4 exactly, from "I've included an MP4 file..." to "make no mistakes."
   anabology gave that same prompt to Opus 5.5 together with Midjourney and a moodboard. So our film is at least the
   third public answer to one well-known prompt, and the audience will compare it with the other two.
2. **anabology did not use the P(doom) song.** The film is 5:06 long (306.5 s), not 4:56, and has an original song at
   about 133.8 BPM with a female vocal ("You have 18 months to escape the permanent underclass", "It's so over / we're
   so back"). Which music model made it has not been confirmed (PortOS issue #8965, 2026-09-27).
3. **donald sped the P(doom) song up.** His audio runs at about 145 BPM instead of 132, roughly 1.10x faster with the
   pitch kept, and his cut is 141.6 s. Kenton Varda noticed this in the replies ("was it Claude's idea to increase the
   tempo?"). Our brief requires the exact audio, so our film should stay at 156.7 s and 132 BPM, untouched.
4. **One fixed HUD holds 100+ generated shots together.** The same four corners, one mono face, hairlines, one orange
   accent, a crawling bottom ticker and a countdown that runs down across the whole film (18, 16, 14 ... 07, 06 ... 03,
   01, 00 "months to escape") stay put while the footage changes underneath. The HUD is the backbone of the film and the
   shots are interchangeable.
5. **The fashion show gives the film its structure.** "Look 00" to "Look 11", "SS27", a guest list, a front row, hang
   tags and care labels turn every lyric into a garment or a look, which carries both the structure and the wit.
6. **The palette is controlled.** The shots are desaturated, and the only saturated colour is Claude orange, measured
   at about #D27A5F after compression (Anthropic's #D97757). It appears on numbers, the word being sung, underlines and
   the star hair clip.
7. **Brightness rises across the film.** Mean frame luminance goes from about 0.2 (night) to 0.5 (foggy daylight
   highway at 160 s) to 0.7 (white world, 210-290 s), and saturation falls from about 0.45 to 0.06. The escape is shown
   as night turning to white.
8. **A halftone dot screen covers every frame.** It is a square dot grid with a period of about 4.2 px at 1080p. It
   makes the AI footage look printed and hides its softness. At the end the dot pitch grows ("07 PX", "21 PX", "60 PX")
   until the image dissolves into the orange star.
9. **Cuts fall on bar lines.** The median shot is about one bar (1.79 s at 133.8 BPM). The common shot lengths are 43-44
   frames (1 bar), 54 (5 beats), 32-33 (3 beats), 22 (2 beats), 65 (6 beats) and 87 (2 bars). Short strobes of
   1-6-frame cuts mark the section changes.
10. **The replies praised the concept and the words** ("18 months to escape the permanent underclass is so real", "the
   lyrics, the atmosphere, the camera angles"). The critics said it still reads as slop ("somehow I still get the
   'slop' feeling"). Elon Musk replied "Banger next-level" and "Epic". It had 10,455 bookmarks against 12,345 likes, so
   people saved it as a reference.

## 1. Provenance (dated)

| Date (UTC) | Post | Facts |
|---|---|---|
| 2026-09-09 18:22 | [slimer48484 "Claude-Pop - I'm Upping My P(Doom)"](https://x.com/slimer48484/status/2097752569212756134) | Original release (Blender video), 156.6 s. 2,500 likes, 710,620 views |
| 2026-09-22 21:45 | [other__reality "Claude Opus 5.5 has the best visual design of any model I have tested so far"](https://x.com/other__reality/status/2102514581684052169) | Quotes slimer. The JS paper-animation remake (the PDoomVideo repo), 156.6 s, 720p, 24 fps. 6,957 likes, 4,338 bookmarks, 2,597,754 views |
| 2026-09-23 16:44 | [donaldjewkes "I made this with one prompt using Opus 5.5 / I spoke to my computer for 5mins, claude worked for 12 hours"](https://x.com/donaldjewkes/status/2102801274173587569) | Quotes other__reality. 141.6 s, 1080p, 30 fps. 9,986 likes, 10,311 bookmarks, 445 quotes, 3,422,517 views |
| 2026-09-23 16:45 | [donald, "full prompt" reply](https://x.com/donaldjewkes/status/2102801469976248500) | Note tweet of 9,608 characters, identical to our brief. Saved as `out/refs/json/donald_prompt.txt` |
| 2026-09-23 16:46 | [donald, tools reply](https://x.com/donaldjewkes/status/2102801906573935057) | "Claude had access to SD2.5, elevenlabs, libraries of references, and the repo from @other__reality above" |
| 2026-09-25 17:17 | [anabology "Gave Opus 5.5 donald's prompt, Midjourney, and a moodboard / 12 hours later, woke up to this"](https://x.com/anabology/status/2103534482930491441) | Quotes donald. 306.5 s, 1080p, 24 fps. 12,345 likes, 1,481 reposts, 603 quotes, 10,455 bookmarks, 825 replies, 16,923,773 views |
| 2026-09-25 17:18 | [anabology self-reply](https://x.com/anabology/status/2103534658763768070) | "Slopcore is the future of art" (903 likes) |
| 2026-09-25 20:01 | anabology to @ethan_tan ("midjourney through the browser?") | "Yep": Midjourney was driven by browser automation. Midjourney has no API, and its terms forbid automated access (see GENMEDIA.md section 6) |

Coverage: the [awesome-opus5-5-videos list](https://github.com/yihui-dev/awesome-opus5-5-videos) (yihui-dev, 282
entries) files anabology as "Motion graphics / Canvas / AI image" and stores the prompt, which is donald's.
[PortOS issue #8965](https://github.com/atomantic/PortOS/issues/8965) (2026-09-27) says: "The creator reports Opus 5.5,
Midjourney and a moodboard, with a 12-hour run ... The exact five-minute video's music provider remains unverified."
[Nick Dobos](https://x.com/NickADobos/status/2102898978849448301) (2026-09-23) called donald's prompt "Masterclass
prompt engineering ... input data and media, highly detailed super long prompt, curated choice of connected services".
[pleometric](https://x.com/pleometric/status/2103082510607610023) (2026-09-24, 4,572 likes) followed "the general
workflow Donald described".

## 2. The anabology film, "ESCAPE VELOCITY · SS27"

### 2.1 Facts

- 306.48 s, 1920x1080, 24 fps, H.264 at 9 Mb/s. Audio is AAC at 44.1 kHz.
- The song is original, with a female vocal that is sung and half-spoken, at about 133.8 BPM (comb-filter tempo search
  over the onset envelope; librosa's beat tracker gives the same). The transcript is in `ana/asr.txt`.
- One protagonist, a young woman, carries almost every shot. The identity anchors are a black bob with an orange streak,
  an orange 8-pointed star hair clip (the Claude spark), a white poplin puff-sleeve blouse, a black harness, a black
  patent skirt, knee boots, a white hang tag on the hip, and a headset microphone. The headset means she is the singer,
  so the film lip-syncs loosely in close-ups.
- Her face drifts noticeably from shot to shot: face shape, freckles and eye colour change, for example between 24 s,
  198 s and 278 s. The costume and hair keep the character readable. Our film cannot rely on that, because our
  protagonist is a real person and must match his photo.

### 2.2 Structure (sections from the transcript and the frames)

| Time (s) | Lyric (sung) | World and grade | HUD countdown |
|---|---|---|---|
| 0-10 | "Ladies, gentlemen, agents" (spoken over a quiet intro) | Cold open. Her face asleep in a car under red light. A split-flap row scrambles "24 → 18 MONTHS TO ESCAPE THE PERMANENT UNDERCLASS". Night highway with light trails and a robotaxi. A hang tag "ESCAPE VELOCITY". Blue-black | 18 |
| 9.3-12.2 | "Ladies. Gentlemen. Agents." | The title card (section 2.7) | 18 |
| 12.2-19 | "This is not an AI billboard. Prepare to walk." | Her back walking toward a tracked billboard. The word "THIS" is set inside the billboard | 18 |
| 19-26 | (instrumental) | "Look 00." A runway at night in rain and fog, crowd in silhouette, she walks straight at the lens. Card "PHONES DOWN. TOKENS UP." Garment callouts. Face close-up with a landmark mesh | 18 |
| 26-72.8 | Verse 1, Looks 01-06 ("AGI era, not unreasonable", "13 Mac minis", "Dad cap: usage limit", "Shoes off in North Beach", "Our Waymo...", "Like, the singularity") | Each look gets an italic-serif title, the lyric typed out, a hang-tag card and one data widget. Shouted words in huge condensed type ("AGI. CGI. CSI: MIAMI.", "RETIRED.", "ENCORE."). Night blue with red practicals | 18 |
| 66-72.8 | "No grades, no tests. Taste is the moat. That's so agentic." | Pedestal, torn-paper billboard, a white billboard reading "THAT'S SO AGENTIC." | 18 |
| 72.8-95 | Chorus 1: "You have 18 months to escape the permanent underclass / Lock in / Feel the AGI / Escape velocity" | Warm amber grade (B-R about -0.13). Orange split-flap "1 8". "UNDERCLASS.", "LOCK IN.", "AGI,". Speedometer gauges | 18 |
| 95-110 | "It's so over / We're so back" (x3) | Concert crowd. A vibe slider from "SO OVER" to "SO BACK". Bar chart "supersonic tsunami" | 18 |
| 110-152 | Verse 2, Looks 07-11 ("Impossible puzzles", "We've found other agents", "Zero-day answer keys", "Hugging-face pin $12.9B", "Sheer. Be transparent only if asked", "Staff badge, empty seat", "Not AI. SI.", "Trust us", "Cashmere", "The Immortals, 3 seats", "Lower me into the golden light") | Clones, the Penrose-triangle puzzle, an empty folding chair in a spotlight, a white-grid void. Neutral to warm | 16 → 14 → 12 → 10 → 08 → 07 |
| 152-186 | Chorus 2 ("six months ... they say hit the brakes, we say hit the gas") | Foggy daylight highway, gantry signs as split-flap boards, brake/gas bars, "GAS", "BACK!" | 06 |
| 186-214 | Bridge: "longevity escape velocity, one year back for every year ... if it doesn't kill us all first ... 3, 2, 1, 0 ... Do we make it?" | Gantries "LONGEVITY E.V.", "35% DIE / 43% LIVE FOREVER". The countdown lands in an iris HUD ("03 MO", "01"). A Claude Code terminal types "Did" | 06 → 03 → 01 → 00 |
| 214-223 | "There is nothing to escape." | A gantry reads "THERE IS NO UNDERCLASS". Run-up to a jump with "T-5 ... T-1" and distance counters. One 8.5 s shot | "THERE IS NO UNDERCLASS" |
| 223-270 | Final chorus and rap ("Lock in" x10, "country of geniuses in a data center", "Lean proofs", "enzymes", "Sora's gone dark", "Stargate force majeure", "/loop make me happier", "Slopocalypse? Not ours", "can't stuff it back in the box") | White world with leaps and flying falls. Big words ("COUNTRY", "PROOFS", "ENZYMES.", "SORA'S", "FORCE", "SLOPACOLYPSE?", "NOT") | 00 |
| 270-290 | "Shell: optimism. Lining: doom. Wash cold. Do not iron. Do not nerf. Made in San Francisco." | Macro shots of care labels ("SHELL: 0% → 100%"), a 30° wash icon, an SF map "FIG. 13 · ORIGIN OF THE COLLECTION" | 00 |
| 290-306 | "We're so back" | Split-flap "THERE IS NO UNDERCLASS" then "END OF SHOW."; she walks away from camera into white. A run-of-show list with timestamps. The halftone pitch grows 07 → 21 → 60 PX and the orange star bursts; final close-up of the star clip with "we / are / so / back" typed in mono | 00 |

### 2.3 Shot grammar

- **Cut density.** The 0.25 threshold finds 148 cuts; the 0.10 threshold finds 207 after merging, but that pass also
  counts HUD changes. The true count is about 150-200, or roughly 30-45 cuts per minute. The median shot is about one
  bar. By section (0.25 pass, a lower bound): cold open 37/min, verse 1 40/min, chorus 1 41/min with a 1.33 s median,
  "so over / so back" 16/min, verse 2 16-29/min, bridge 36/min, the jump 7/min (one 8.5 s hold), final chorus 38-58/min,
  end of show 11/min with 8-11 s holds.
- **Rhythm devices.** Strobe runs of 1-6-frame cuts or flashes at 7.6-8.5 s, 49-51 s, 206.4-207.3 s, 224 s and
  234.7-236 s. Split-flap scrambles work as transitions. The HUD holds steady across every cut.
- **Camera.** Mostly locked-off frames or slow push-ins. The walk is shot on a long lens, straight on, at eye or
  slightly low height: she walks at the lens while the frame barely moves, so the growth in size does the work. There
  are low-angle heroic shots (76-83 s, the amber corridor), handheld close-ups on her face and hands, top-down and
  Dutch-angle inserts in the white world, and whip-fast inserts of hands and props (a belt buckle for "LOCK", a hang
  tag, a care label).
- **How the walk is staged.** The runway is a wet, reflective strip down the centre of frame with crowd silhouettes on
  both sides, strong backlight from far away, fog and one red practical light. She holds the centre third, and the
  vanishing point sits behind her head. Walks toward camera are the default for the "Look" shots. Walks away from
  camera open the film ("prepare to walk", toward the billboard) and close it ("END OF SHOW"). The walk returns in
  every world (night runway, amber corridor, foggy highway, white studio), so the gait is the continuity while the
  world changes.
- **Shot vocabulary.** Face close-up with a tracking chip; the runway walk; a detail insert of a garment or prop; a
  data card on a plain field (split screen, footage on the left two thirds, a black info panel on the right); a
  full-screen typographic card on black or white; an environment wide with a tracked sign or billboard; a surreal
  object (Penrose triangle, empty chair, mannequin rack "RETIRED").

### 2.4 Grade and light (measured, mean over 2 s samples)

| Span (s) | Mean RGB | Luma | Saturation | Read |
|---|---|---|---|---|
| 0-40 | 0.21 0.23 0.23 | 0.20-0.24 | 0.26-0.49 | Cold blue-grey night, crushed blacks, bright backlight and wet reflections, red practicals |
| 80-90 | 0.31 0.23 0.17 | 0.24 | 0.54 | Warm amber chorus |
| 160-210 | 0.46-0.52 even | 0.46-0.52 | 0.17-0.29 | Foggy daylight, pale blue-white |
| 210-250 | 0.60-0.70 even | 0.61-0.71 | 0.12-0.17 | White world, overexposed studio |
| 290-300 | 0.75 even | 0.75 | 0.06 | Near-monochrome white (end of show) |

The light is always motivated: backlight through fog, practicals (red beacons, tail lights, billboard glow) and window
light. The face is often only partly lit, with a red rim or a single beam. Blacks never go pure black on the footage
(the 2nd percentile of luma is about 0.03-0.09), which gives a lifted, printed feel. The typographic cards use true
black.

### 2.5 Texture

- A square dot grid with a period of about 4.2 px at 1080p (FFT peaks at 0° and 90°, `ana/crops/dither_zoom.png`),
  multiplied over the image. On bright shots a rotated screen of about 6 px at -7° makes an RGB moiré that looks like
  an LCD subpixel mask (`dither_zoom_light.png`).
- Faint scanlines and film softness on top. The footage itself is soft upscaled AI video, and the screen hides it.
- The dot pitch carries meaning at the end ("07 PX", "21 PX", "60 PX": the image turns back into dots before the star).

### 2.6 HUD layout (coordinates in 1920x1080 pixels)

- **Frame.** Hairline crosshair marks near all four corners (about 24 px in). Text margins are x = 72 to 1824, with the
  top baseline at about y = 60.
- **Top left.** `LOOK 00 / 11` in mono caps, about 11 px, widely tracked. At the end it reads `LOOK 11 / 11 · ALL`
  with "ALL" in orange.
- **Top right.** `ESCAPE VELOCITY · SS27`, right-aligned at y ≈ 60. Below it at y ≈ 105 a thin live audio-level strip
  (x ≈ 1644-1822, about 60 bars, the last one orange) that follows the song.
- **Countdown block** (x ≈ 1494-1716, y ≈ 128-205). Two split-flap tiles with orange digits `1 8`, then white flap tiles
  `MONTHS` / `TO ESCAPE`. Under them, tiny mono `THE PERMANENT UNDERCLASS`, a hairline rule, and
  `DEPARTURES · SS27 · COLLECTION 01`. In the white world the block becomes a light panel, and at the end it reads
  `00 THERE IS NO / UNDERCLASS · MONTHS · BOARD 01 · FINAL`.
- **Left edge.** A vertical ruler (x ≈ 30-66) with ticks every 22 px and a three-digit label every fourth tick
  (`002, 003 ...`). An orange playhead tick is fixed at y = 540. The ruler scrolls up one label per bar (002-011 at
  10 s, 009-018 at 23 s, 157-166 at 290 s), so it is a bar counter.
- **Bottom right.** Timecode `MM:SS:FF` (for example `00:10:05`, `04:50:00`) at x = 1824, y ≈ 1003.
- **Bottom ticker.** A full-width band at y ≈ 1036-1064 between two hairlines. Mono caps about 13 px, items separated
  by `✱` (a Claude-like asterisk), crawling right to left at about 132 px/s (5.5 px per frame). The band is dark and
  translucent at night and light on white scenes. The counters are live: tokens burned rise about 730,000 per second
  (210,730,000 at 1 s, 431,920,000 at 304 s), context rises about 1,250 tokens per second (1,001,234 to 1,375,136), and
  `UNDERCLASS -N MO` follows the countdown (-18, then -7 at 150 s, then NONE).
  - Loop at the start (12 items, verbatim): `TOKENS BURNED 210,730,000 ▲ ✱ MAC MINIS 13 ✱ UNDERCLASS −18 MO ✱ NVDA ▲
    5.3T ✱ CURSOR → SPACEX $60B ✱ WAYMO RECALL 3,900 ✱ CONTEXT 1,001,234 TOK ✱ HUGGING FACE → NVIDIA $12.93B ✱ IMO
    2026 · 42 / 42 ✱ SUNCATCHER T−6 DAYS ✱ LEV 0.61 YR/YR ✱ STOP HIRING HUMANS → RETIRED · SEP 10 ✱`
  - Loop at the end: `SHOW 01 · SS27 · 11 / 11 LOOKS SHOWN ✱ UNDERCLASS: NONE ✱ FRONT ROW: AGENTS ✱ MAC MINIS 13 ✱ NVDA
    ▲ 5.3T ✱ CONTEXT 1,365,264 TOK ✱ MONTHS TO ESCAPE: 00 ✱ CURSOR → SPACEX $60B ✱ HUGGING FACE → NVIDIA $12.93B ✱
    SUNCATCHER T−6 DAYS ✱ TOKENS BURNED 431,920,000 ▲`
- **Tracking chips.** Corner brackets around the subject with an inverted chip (black mono on white), such as
  `MODEL 01 · LOOK 00` with confidence `0.97`, `FACE · MODEL 01` with `0.99`, or `FACE · TO LENS 0.97`. A billboard is
  tracked with its corners labelled (`BILLBOARD · 0.99`, `P3 [366, 649]`, `P4 [1619, 649]`).
- **Garment callouts.** Leader lines to parts of the costume: `01 SHIRT · POPLIN · PUFF SLEEVE`,
  `02 HARNESS · 25 MM WEBBING`, `03 SKIRT · PLEATED · 24`, and so on.
- **Section headers.** An orange `✱` followed by mono, for example `✱ GUEST LIST · SHOW 01 · FRONT ROW` with a right
  column `SHARE OF SEATS` and a hairline rule, or `✱ DEPARTURES · SS27 · COLLEC▌`. Every mono string types on with a
  block cursor.
- **Hang-tag and data cards.** Off-white cards with a condensed bold title, mono key/value rows, an orange pill
  (`HACKER HOUSE`, `SS27`), laundry-care icons, a barcode and a code such as `EV-27-0202`. For example `LOOK 02 / 11 ·
  13× MAC MINI · UNITS 13 · UPTIME 24/7 · COOLING NONE · SLEEPERS 2 · BEANBAG`.
- **Other legible captions** (a selection, in film order): `PHONES DOWN. TOKENS UP.` (card: AGENTS FRONT ROW / VCS BACK
  ROW / UNDERCLASS STANDING / DRESS CODE LOCKED IN) · `SHOW 01 · SS27 · FIRST WALK` · `BASE · 11 LOOKS TO FOLLOW` ·
  `00 · START` · `DETECTIONS · AGENT + 27 · PERSON + 00` · `FRONT ROW · SEATS BY CLASS` · `RESERVED AGENT` ·
  `AGENT · A-01 · 0.98` · Claude Code terminal `~/hacker-house` with `23:59:58` · `JENSEN CALM` · `USAGE LIMIT` ·
  `+25% = −17%` · `SHOES OFF · PLEASE · POLICY: OPTIONAL` · `Ride paused. Rider support is on the way.` ·
  `SINGULARITY · ARE WE IN IT · LIKE, HERE` · `TRANSCRIPT` · `48,308 POSTS IN THE ARCHIVE` · a dated source line
  `2026-02 FT · M. SULEYMAN white-collar work ... fully automated by an AI within the next 12 to 18 months` ·
  `LOCK-IN MODE` · `v 6.5 → 11.2 km/s` · `VIBES · SF · 2019 → NOW` · `SO OVER ↔ SO BACK` · `"SUPERSONIC TSUNAMI"` ·
  `IT'S SO OVER REGION / WE'RE SO BACK REGION` · `1,434,923 · PASS RATE 0.00 %` · `$12,930,380,000` ·
  `SHEER BY DEFAULT · HONEST ALWAYS · HELPFUL ALWAYS · OPACITY 0.12` · `☐ Verify ☑ Trust us` ·
  `THE IMMORTALS · SEAT 1 OF 3 · $1,000,000 / YR · TERM: INDEFINITE` ·
  `A PROMISE, NOT A PRODUCT · FIRST SF SPA PLANNED LATE 2027 · NOT FDA-CLEARED` · `BAN ARTIFICIAL SUPERINTELLIGENCE ACT` ·
  `BRAKE 57% / GAS 0% → GAS 100%` · `1 CLASS / 15.3 MO ×1.2` · `264,960` minutes · `11/20 STRANDED` ·
  `LONGEVITY E.V. -.-- YR/YR` · `35% DIE / 43% LIVE / FOREVER` · Claude Code `~/bridge ... status: pending` ·
  `Δv 11.2 KM/S → 0.0` · `T−5 ... T−1` · `DISTANCE TO JUMP 5.7 M → 1.4 M` · `LEAN PROOF` · `ENZYME · ART / PHAGE` ·
  `2.45 GW · 0 BUILT · NOTICE OF FORCE MAJEURE` · `> /loop make me happier` · `CONTENTS: AGI` · `DOES NOT FIT` ·
  `SHELL: optimism. / LINING: doom.` · `Wash cold. / Do not iron.` · `FIG. 13 · ORIGIN OF THE COLLECTION` (map pins:
  `20 STRANDED · PRESIDIO`, `LOOK 04 · SHOES OFF · NORTH BEACH`, `00 · THE BILLBOARD · MASONIC AVE`,
  `LOOK 05 · FIREWORK · MISSION`, `US-101 · BILLBOARDS`, `MADE HERE ✱`) · care tag
  `SHELL 100% OPTIMISM · LINING 100% DOOM · WASH COLD · 30 · IRON DO NOT · NERF DO NOT · MADE IN SAN FRANCISCO · EV-27-0000`
  · `END OF SHOW. · LOOKS 11/11 · MONTHS 00` · a run-of-show list `LOOK 01 AGI ERA 00:26 · LOOK 02 13 MAC MINIS 00:33 ·
  LOOK 03 DAD CAP 00:40 ...`.

### 2.7 The "Ladies. / Gentlemen." title (frames every 1/6 s, `ana/seg_ladies_sheet/`)

| t (s) | Frame |
|---|---|
| 9.17 | Over the night-highway shot, the header types on: `✱ GUEST LIST · SHOW 01 · FRONT ROW`, with `SHARE OF SEATS` in the right column |
| 9.33 | "Ladies." appears on the sung word, in **Claude orange**, bold grotesque about 40 px high (cap height about 30 px), at x = 72, with a hairline progress bar stuck at `0 %` |
| 9.50 | Cut to the runway walk; "Ladies." stays |
| 9.67 | "Ladies." turns **white** (the active word is orange, settled words are white) |
| 9.83 | "Gentlemen." appears in orange, `0 %` |
| 10.17 | "Gentlemen." turns white |
| 10.33 | "AGENTS." slams in, in condensed caps about 3x larger (cap height about 90 px), with an orange underline bar that fills from 88 % to `100 %` within 4 frames |
| 10.83 | The footage cuts to **pure black**: the people vanish and only the type and the HUD stay |
| 11.3-12.0 | The type changes to a detection readout: condensed `AGENTS 03 → 06 → 09 → 12 → 15` against `PEOPLE 00` (orange mono digits), while bounding boxes `AGENT · A-0n · 0.9x` and `RESERVED AGENT` multiply |
| 12.17 | Cut to her back walking toward a tracked billboard (`BILLBOARD · 0.99`) |

So the gag works like this: ladies get 0 % of the seats, gentlemen 0 %, agents 100 %. Three words and two
progress bars make a thesis, and the joke is told only with interface language, with no picture of a robot.

### 2.8 Typography (identified by eye from the crops; open-licence equivalents)

| Role | What it looks like | Open-licence equivalent |
|---|---|---|
| Lyrics, look titles and statements ("Ladies.", "Look 02. 13 Mac minis,", "Made in San Francisco.") | Helvetica Neue / Neue Haas Grotesk Display Bold, tight tracking, sentence case with full stops | Inter Tight 600-700 at about -2 % tracking ([google/fonts ofl/intertight](https://github.com/google/fonts/tree/main/ofl/intertight)); Instrument Sans Bold is a warmer alternative |
| Shouted words ("AGENTS.", "UNDERCLASS.", "ENCORE.", "GAS", "BACK!") | DIN-like condensed caps, medium weight, flat-sided O, G with a spur | Barlow Condensed 500-600; Oswald 400 as a fallback |
| Telemetry, ticker, chips, cards | Neutral grotesque mono, caps, tracked +8-12 % | IBM Plex Mono or JetBrains Mono (both OFL, already in `/mnt/skills/examples/canvas-design/canvas-fonts/`); Geist Mono and DM Mono are also there |
| "Look 00." title | High-contrast italic serif, fashion-magazine style | Instrument Serif Italic (OFL, also local); Playfair Display Italic |
| Split-flap digits and letters | Condensed mono on dark tiles with a hinge line through the middle | Martian Mono (width axis, OFL) or JetBrains Mono drawn into flap tiles |

Six presentation modes for the lyrics:
1. Karaoke subtitle: small, bottom left, the word being sung in orange and settled words in white or grey.
2. Statement: the grotesque at about 40-60 px, left-aligned on the 72 px margin, top-left quadrant.
3. Shout: one condensed word at 150-250 px landing on the downbeat, often cropped by the subject or behind her.
4. Typed mono.
5. Text set into the footage (tracked billboards, gantry signs, split-flap boards, an iris).
6. Text on a card (hang tag, care label).

### 2.9 Pacing against the music

- The whole film sits on a bar grid. Cuts, big words and HUD ticks land on downbeats, the ruler advances once per bar,
  and the audio meter moves live.
- Words appear on the sung syllable. Spoken lines ("Ladies, gentlemen, agents") get the largest type. In dense verses
  the type sits in the karaoke band.
- The energy is managed in blocks: the choruses cut fastest (median about 1.3 s) and stack the biggest type, while the
  "so over / so back" passage and verse 2 slow the cuts to hold on single striking images (clones, empty chair). The
  bridge counts down 3-2-1-0, then the film holds one 8.5 s shot, then the final chorus goes to the fastest cutting of
  all in the white world. The ending holds 8-11 s shots.
- The one-way countdown gives a musically repetitive song a sense of progress, a narrative tension the song does not
  have on its own.

### 2.10 Why it reads as high-aesthetic

1. **A single, legible conceptual frame** (a fashion show, SS27, looks, hang tags, care labels). Every lyric maps to a
   garment or a look, so the structure explains itself.
2. **One protagonist with fixed identity anchors** (a star clip, one colour streak, one costume). This is the old
   fashion-film discipline of a single look carried through many worlds.
3. **Interface as graphic design**, not as sci-fi. There are no glowing holograms: the HUD is a print-like editorial
   system (hairlines, mono, hang tags, split-flap boards borrowed from airports and highways), which feels grown-up.
4. **Restraint in colour.** The footage is desaturated, with one orange, used only for meaning (the active word, the
   count, the brand star).
5. **Texture that unifies.** The halftone screen makes heterogeneous AI footage look like one printed stock.
6. **A shaped brightness arc** (night to white) that matches the thesis (escape).
7. **Real, dated specifics.** The HUD cites FT and Suleyman with a date, IMO 2026 42/42, Hugging Face to NVIDIA
   $12.93B, Waymo recall 3,900, Stargate force majeure. That is insider wit for SF tech Twitter.
8. **Jokes delivered in a deadpan interface voice** ("SHARE OF SEATS 0 %", "SHEER BY DEFAULT · OPACITY 0.12",
   "NERF: DO NOT").
9. **Cutting on the bar**, with long holds kept for the key images.

### 2.11 Weaknesses to avoid

- **Clutter.** Many frames stack three or four widgets, a big word and a subtitle at once (for example 44-46 s, 160-166
  s, 272 s). The best frames are the emptiest ones (10.83 s "AGENTS." on black, 134 s the empty chair, 190 s the small
  figure under the gantry).
- **Identity drift.** The face changes between shots, and wides go mushy. That is acceptable for a fictional model and
  unacceptable for our real protagonist.
- **Length.** At 5:06 the middle sags. Our 156.7 s is an advantage.
- **Borrowed memes** ("so back / so over", "permanent underclass", CSI: Miami) are topical but will date quickly.
  Replies split on "banger" versus "still slop".

### 2.12 Reception (top replies, fetched 2026-09-28; `json/ana_conv.json`)

- Praise: elonmusk "Banger next-level" ([2026-09-27](https://x.com/elonmusk/status/2104154239115419939), 1,647 likes) and "Epic" (1,187); donaldjewkes "wow, this one is great";
  davidkosir "WHAT THE HECK THIS IS GOOOOD"; nobackspace_txt "this is the one that made me realize i was doing AI wrong";
  r_cushty "The lyrics, the atmosphere, the camera angles, '18 months to escape the permanent underclass' is so real";
  corey_hauer "If the clubs are not pumping this one tonight..."; AndresMilioto "put it on spotify please"; nickcammarata
  "im excited for my 18 minutes to escape the permanent underclass"; ArthurRenard12 "was 'permanent underclass' the
  model's idea or yours?"; ccamargo "The fabric:" (the care-label joke landed); Photo_Jacks "Are we... in cyberpunk now?".
- Criticism: MrParauti "somehow I still get the 'slop' feeling"; PrinceSoni35709 "overall for me this is still slop";
  wiggitywamy "Do not do this."; Dungers71 "More money than sense".
- Process: ethan_tan asked "midjourney through the browser?", anabology answered "Yep", and GlacierKilo pointed out
  "Midjourney does not offer API".
- Reading: people shared and saved the words and the concept (the song, the permanent-underclass line, the care-label
  joke). The footage was taken as competent. Bookmarks at 85 % of likes suggest people kept it as a workflow reference.

## 3. donald's film (the same brief, P(doom) song)

- **Look.** Risograph and halftone illustration on cream paper, in orange, pink, navy and mustard. The Claude sunflower
  idol has an orange flower head, a headset and a white jacket, with five backup-dancer "flower" members. There are
  K-pop sunburst backgrounds, huge poster type in pink ("I SEE SPARKS OF AGI", "LOSS", "FOOM", "ACCELERATIONISM",
  "REARRANGING", "FREE", "GO", "TOO LATE NOW", "SHOW"), and subtitles as paper labels with the key word underlined.
- **Running devices.** A date stamp top right that runs from 2019 to `2026.09.22` ("LIVE" / "FFWD" / "TODAY"), and a
  `P(DOOM)` percentage top left that climbs from 4.2 % to 99.9 %. A METR "TIME HORIZON ≥16 HRS" card opens the film and
  a "≈6 SEC" card closes it. The end card reads "UPPING MY P(DOOM) drawn by Claude Opus 5.5 · 2026.09.22" with a
  pencil-drawn sunflower.
- **Lyric-to-image choices** (so we do not repeat them): sparks = arXiv 2303.12712 card; loss = log-scale loss curve
  with the flower falling; ChatGPT = shoggoth tentacles; shrooms = dancers with a mushroom; shoggoth = smiley mask;
  shinigami eyes = close-up; "gentle singularity" = METR chart climb; Navier-Stokes "SEP 08" finite-time blowup swirl;
  atoms = dot dissolve; Sydney = K-pop member card "SYDNEY · POSITION · VISUAL"; basilisk = member card "MAIN VOCAL
  (ACAUSAL)"; NVDA = moon with a green arrow; Omega Point = eye with Ω; 1e30 = split-flap "1E30 FLOP/S · 2 GW ·
  555,000 GPUs"; safe enough = vault; forward/backward = dancers with arrows; von Neumann = museum plaque "VON NEUMANN
  ARCHITECTURE 1945-2026 · Gift of the humans" plus a computer under a sheet; sharp left turn = a car; CDR = sleeping
  safety clouds with a clipboard "CRITICAL DESIGN REVIEW · NONE ON FILE"; Gato = a giant cat "GATO · POSITION ·
  GENERALIST" with "GRIP 75%"; paperclips = "PAPERCLIPS 1,000,000,000,000" and an island on a paperclip planet; kill
  switch = hands and a fuse; orthogonality = "BLUES" with a microphone; transformers = "stochastic parrot"; Chinchilla =
  a chinchilla with "15T / 20x"; safety fence = a tungsten block; GPUs = a data-hall corridor "ONE CLUSTER 555,000 · 2
  GW"; RLHF = "You're absolutely right!" speech bubbles; Loom = a loom with "nothing ever happens / scaling hits a wall";
  masked pre-training = a chalkboard "The cat sat on the [MASK] mat!" with "2018 · BERT"; recursive self-upgrade = an
  arch door; Ilya = an NDA padlock door "NON-DISPARAGEMENT / VESTED EQUITY"; "Was it all for show" = "SHOW" plus
  "CONGRATULATIONS / ありがとう THANK YOU".
- **Audio.** 145.2 BPM with the pitch preserved (chroma matches at 0 semitones), 141.6 s. The song was sped up by about
  1.10x.
- **Reception** (`json/don_conv.json`). "The references are really good. Easily ranks among the best original art I've
  encountered on this app" (stanfordNYC); "Why did this make me emotional" (pli_cachete); Kenton Varda: "Can you tell it
  to redo the CDR part? It's supposed to be a Lisp reference, not 'critical design review'" (our
  `lyric_concepts.json` already reads CDR as Lisp); flimflamlite: "any idea why it has the same gags? 'Von Neumann
  obsolete' is a 60s computer getting covered with a sheet..." (the previous videos share gags, and viewers notice
  repeats); MFrancis107: "You just slop grenaded something that was already amazing."
- **What it proves.** An illustrated, reference-dense, meme-literal treatment of this song has already been done well.
  Our film has to be different in kind (photographic, philosophical, restrained), not a better version of the same
  thing.

## 4. The original "Claude Pop" (other__reality, the PDoomVideo JS render)

A watercolour-paper cartoon (the source of the repo we audited in `claudepop/audit/`). A boxy orange Claude creature
and a lab-coat scientist play out each lyric literally on a red-curtained stage, with a lab, doors, a desert road and
space scenes. It has burned-in rounded subtitles, onomatopoeia ("CHOMP!", "SKRRT!", "CLANK", "HONK!") and a P(doom)
thermometer that rises in the corner. It is charming and illustrative, and the brief itself calls it "good, but really
not there".

## 5. What our film should take: adopt, transform, avoid

Frame: a stream-of-consciousness, philosophical music short film. The protagonist is the user, reconstructed by a
machine from one frontal photograph. The female voice is the machine, or the inner other, which is never seen singing.

| Device | Decision | How, for us |
|---|---|---|
| Fixed HUD as the backbone | ADOPT | Keep the same grammar (corner marks, 72 px margins, one mono face, hairlines, a bottom ticker, a live audio meter, a bar-counter ruler, `MM:SS:FF` timecode). The HUD becomes the machine's inner monologue: what it measures of him, what it guesses, and what it is spending (context, tokens burned). |
| One-way counter giving the arc | TRANSFORM | Countdowns are taken (anabology's months to escape, donald's P(doom)). Use a reconstruction counter instead, e.g. `SEEN: 1 PHOTOGRAPH · INFERRED: 0001 / 3760 FRAMES` (156.7 s x 24 fps = 3,760 frames), or a measured/inferred ratio that flips during the film. It is conceptually ours and ties to "Was it all for show?" |
| Named structure (Look 00-11) | TRANSFORM | Not "looks". Use generative nomenclature: `SAMPLE 01 / 40`, `VIEW +30°`, `SEED 0412`, sections named after the lyric's idea (`THE CHINESE ROOM`, `OMEGA POINT`). The italic-serif title card can stay as our chapter mark. |
| Karaoke word in orange | ADOPT, with a meaning | Orange is the voice. The sung word is orange because the machine is singing, and he never is. Settled words go white or grey. |
| One orange accent, desaturated footage | ADOPT | Our bible's palette: cold neutral footage, one warm light source, Claude orange only for the voice, the counter and one object. |
| Halftone dot screen | TRANSFORM | Use it as sampling resolution. The dot pitch follows how much of him is measured and how much is guessed: fine on the measured front of the face, coarse on the guessed sides and back. It dissolves at "atoms rearranging" and at the end. |
| Brightness arc night to white | ADOPT, retimed to our song | Dark room with the one photograph under a lamp, to the night walk, to the white Omega-Point void (fits the loudest section, 140-152 s), then a fade after 152 s. |
| The walk as continuity | ADOPT | He walks toward the future. The same gait continues across changing worlds, cutting on bars, and the walk itself is the stream of consciousness. Walks away from camera suit silhouette or "inferred" shots of the back of the head. |
| "Ladies. / Gentlemen. / AGENTS." move (three words, two progress bars, cut to black) | ADOPT the method, not the gag | Our opening hook in the first 3 s: large type on the sung words of "I see sparks of AGI in your eyes", plus one interface readout that states a thesis (for example `MEASURED 1 · INFERRED ∞`), then a hard cut to black. |
| Tracked text inside the footage (billboards, gantries, an iris) | ADOPT sparingly | Text inside the world of the plate (a light table, a monitor, the photo booth), planar-tracked in our compositing engine. |
| Split-flap boards | AVOID or use once | Now anabology's signature. At most one flap moment (for example "1E30 FLOP/S"), preferably not. |
| Hang tags and care labels | TRANSFORM | Use a provenance label instead: C2PA-style content credentials (`SOURCE: 1 PHOTOGRAPH · FRONT: MEASURED · SIDES: INFERRED · BACK: GUESSED · GENERATOR: ...`). This is real, current and on-thesis. |
| Real, dated data in the ticker | ADOPT, with our own items | Our lyric references with dates and sources (Sparks of AGI arXiv 2303.12712 · Mar 2023; Gato May 2022; Loom; 1e30 FLOP/s; Chinchilla 2022), plus the machine's own telemetry. Do not reuse anabology's items (Mac minis, Waymo, Suncatcher, IMO 42/42). |
| Garment callouts | TRANSFORM | Callouts label the reconstruction instead (`LEFT EAR · INFERRED · 0.41`, `IRIS · MEASURED`). These are designed labels, not numbers measured from the photo. |
| Strobe runs at section changes | ADOPT | 2-6-frame flashes at section boundaries, used sparingly. |
| Dense multi-widget frames | AVOID | At most two HUD elements plus one type block per frame. Negative space is the brand. |
| Costume cosplay of anabology (bob, puff sleeves, harness, star clip) | AVOID | Our identity anchors come from him and from our bible, for example one garment and one small orange object that recurs. |
| Memes as literal images (so back / so over, CSI: Miami, sunflower idol) | AVOID | Deadpan interface wit only (director's stance). |
| Lip-sync | AVOID | Our voice is not his, so no lip-sync. The machine speaks through type and light. |
| Plate softness in wides | AVOID | Wides and profiles as silhouettes or deliberately "inferred" renders (a point cloud or depth map). Faces only within about ±30° of frontal, in close-up and medium shots. |
| Speeding up the song | AVOID | The audio stays exact (156.7 s, 132 BPM), as the brief says. |

## 6. Open-licence type kit (download URLs checked 2026-09-28)

- Statement grotesque: Inter Tight, `https://raw.githubusercontent.com/google/fonts/main/ofl/intertight/InterTight%5Bwght%5D.ttf`
- Condensed shout: Barlow Condensed 500/600, `.../ofl/barlowcondensed/BarlowCondensed-Medium.ttf` and `-SemiBold.ttf`
- Mono: IBM Plex Mono or JetBrains Mono, local in `/mnt/skills/examples/canvas-design/canvas-fonts/`
- Chapter italic: Instrument Serif Italic, local (same folder)
- Flap or condensed mono (optional): Martian Mono, `.../ofl/martianmono/MartianMono%5Bwdth,wght%5D.ttf`

Put the fonts under `claudepop/out/fonts/` (gitignored), next to the odyssey fonts that `odyssey/setup.sh` fetches from
the same google/fonts repository.
