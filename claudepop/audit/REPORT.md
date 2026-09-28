# Audit of the previous P(doom) video
_Written from the preproduction workflow's structured result: the subagent could not save its markdown report itself._
## Key findings
1. # Audit: previous 'I'm Upping My P(doom)' video (/home/user/johnheibel/pdoomvideo, commit fa546a3, 2026-09-25)

**Scope.** I read README, STORYBOARD.md, ANIMATION_GUIDE.md, studio.html, render.mjs, src/core.js, clawd.js, cast.js, props.js, timeline.js and lyrics.js, and skimmed all 9 src/ch/*.js chapters and legacy/. I got the project rendering headless on this 4-core machine with no GPU. Then I rendered the **16 requested frames plus 41 supplementary frames** (about one per shot) at 960x540 (painted at 1920x1080 and downscaled in-page) and looked at every one. I also measured per-frame cost with an instrumented pass, and analysed the song's tempo and loudness against the video's hard-coded timing. The clone is untouched except node_modules/ (git status is clean).

**Outputs (under /home/user/HENRYDENG/claudepop/audit/):**
- frames/: the 16 requested PNGs
- contact_sheet.png: 4x4 grid labelled with time, chapter and lyric
- frames_extra/ and contact_sheet_extra.png: the 41 extra frames
- tools/render_linux.mjs: the adapted renderer
- tools/stats.mjs and tools/stats.json: timings, draw-call census, on-screen character sizes, full shot list
- tools/grid_fit.py, drift.py, energy.py: tempo, beat-grid and loudness analysis, with beatgrid.json, local_tempo.json and energy_2s.json
- perf/: one frame rendered on both canvas paths, plus a diff image
- fonts/: local copies of the Google Fonts
- tools/contact_sheet.py: the contact-sheet builder
2. ## TL;DR

The previous video is a 7.9k-line, hand-authored p5.js + p5.brush watercolour cartoon (written by Claude with parallel sub-agents). Clawd, the orange Claude Code box, and a chibi 'Researcher' act out every lyric as a literal sight-gag inside a stage-show frame. It has 62 shots (mean 2.53 s) and ends on 'it was all a play' plus a curtain call. It is charming, coherent and tidy, and it is exactly 'good but not there'.

Why it isn't there, ranked:
1. **No star.** The protagonist is a rectangle with slit eyes: median 18% of frame height, and 40% or more in only 2 of 57 frames. The female vocal has no body, face, lip-sync or choreography on screen.
2. **Wrong clock.** Everything is timed to 88 BPM, but the song is about 132 BPM four-on-the-floor. The video's beat is therefore a 3-against-2 against the kick, and every other hit lands on an off-beat.
3. **Energy map inverted.** The loudest music (the drop at 110 s, the peak at 140-152 s) gets the calmest, emptiest pictures. The one real breakdown (90-108 s, about 6 dB quieter) gets the busiest gags and a 'BOOM'.
4. **Text treated as an enemy.** The storyboard rule is 'keep it text-light', and the only lyric text is a constant-rate karaoke pill fixed at bottom centre.
5. **Rebus illustration plus an ironic 'school play' frame.** It is toothless for SF tech Twitter.
6. **Weak hook.** A curtain title card, then a dim wide shot in which Clawd is 8-10% of frame height.
7. **Cheapness tells.** Flat outlined rectangles, clip-art props, a screen-locked static paper overlay, a corner HUD thermometer, and whip-pan frames that are just coloured bars.
3. ## 1. How it is built

**Page and timeline**
- studio.html loads p5 2.3.3 and p5.brush 2.2.3 on a hidden WEBGL canvas and composites into a visible 2D canvas.
- Fonts: Permanent Marker for titles and SFX, Shantell Sans 800 for karaoke.
- timeline.js registers chapters with `chapter(name, start, end, [[t0, shotFn]...])`. `drawWorld(t)` calls `shotFn(t, lt, dur)`, which paints the whole frame.
- On top of each shot it adds: the corner P(doom) meter during choruses (`pdoomAt` steps 8→34→61→86→99.9% per beat), brush wipes at 1.5/38.5/73.0/109.4 s, and karaoke.

**Determinism and rendering**
- Every frame is a pure function of t: `hash(i)` gives stable per-object randomness, and `jit()` jitter comes from `random()` reseeded per 'boil' frame.
- That makes render.mjs parallel, out-of-order and resumable (atomic .tmp renames). It also has a contact-sheet mode for visual checks.

**Code census**
- 1,181 `paint()` call sites and 361 `inkLine()` call sites.
- `clawd()` is called from 70 places, `researcher()` from 47, lettering from only 29.
- Chapters were written by parallel sub-agents from ANIMATION_GUIDE.md.
4. ## 1.2 How the paper/brush look is achieved (in render order)

1. **Paper** (core.js:155 `makePaper`). A one-off Canvas2D texture: #F3EBDC base, 70 radial brown stains (alpha up to 0.045) and 1,400 short curved fibre strokes. It is drawn first every frame and is **screen-locked**: the camera does not move it and it never changes per drawing.
2. **Shapes** go through `paint(pts,o)` (core.js:98), one call per shape:
   - `wash`: a flat polygon. Used for all character colour.
   - `fill`: p5.brush watercolour, a Tyler-Hobbs-style polygon-deformation fill. The polygon is recursively grown with bleed modifiers into about 24 low-alpha layers on a CPU 2D mask, then 80-110+ random 'erase' circles add texture (node_modules/p5.brush/src/fill/fill.js).
   - `hatch`: hatching, used only in the wipes.
   - Outline: one continuous tapered stroke with the custom 'ink' brush (core.js:175: weight 5, scatter .25, pressure [1.15,.75], grain 40).
3. **Pigment compositing** is the key to the look. p5.brush blends each colour's mask into the framebuffer through a fragment shader (src/core/gl/shader.frag). The shader does spectral Kubelka-Munk mixing (spectral.js, 38-band reflectance) plus an edge-darkening term from dFdx/dFdy. That is where the real-pigment overlap darkening and the dried-edge rims come from. A composite pass runs on every colour or mode change, so cost scales with shape count.
4. **Boil** (core.js:195). `randomSeed(1000+floor(T*12))` re-rolls all jitter and the watercolour's randomness at 12 fps, so lines and fills shimmer 'on twos'.
5. **Lettering.** Canvas2D text with an ink drop shadow and pop overshoot, projected through the camera with `toScreen()`. `flushLetters()` (core.js:141) composites the text into the painting (a one-triangle dummy fill forces p5.brush to flush first), so later paint can cover it.
6. **Post.** A static per-pixel grain (55% of pixels darkened by up to 34 levels) and a warm vignette are multiplied over the frame. The karaoke is drawn on top of the grain, so it reads as UI, not print.

**Net read.** Backgrounds (sunbursts, skies, glows) look truly watercoloured. Characters and props look like flat vector art with a textured outline, because they are all `wash` polygons by design. The paper behaves like a filter, not like paper.
5. ## 1.3 Performance (measured on this machine)

**Setup:** Chromium 1194 headless, ANGLE on SwiftShader (CPU), 4 cores shared with other jobs.

**Two canvas paths** (compared at t=3 s):
- **Faithful path:** the default GPU-style 2D canvas on SwiftShader, which matches the author's d3d11 GPU path. **About 125 s per 1080p frame** (67 s paint plus 57 s readback/flush).
- **Fast path:** add `--disable-accelerated-2d-canvas --disable-gpu-compositing`. **About 16 s per frame**, roughly 8x faster. Low-alpha watercolour glows come out a little weaker (mean absolute difference 6/255; see perf/).

**Fast path across 57 frames** (single worker, instrumented pass):
- **Median 18.4 s per 1080p frame**; mean 19.3 s; range 5.3-42.8 s; p90 31.2 s.
- The guide's budget was 2.5 s, and at most about 4 s, on the author's GPU.

**What a frame is made of** (median per frame, max in brackets):
- 112 `paint()` shapes (433): 39 watercolour fills (132), 88 flat washes (385), 47 ink outlines (142)
- 44 `inkLine` strokes (210)
- about 1,250 polygon vertices
- 0 letters (14)

Frame time correlates with the watercolour fill count (r=0.51) far more than with the total shape count (r=0.19).

**Full-render estimate.** 3,759 frames at 24 fps is about **19 CPU-hours** single-worker in fast mode. Extra workers barely help: SwiftShader funnels every page through one GPU process, so 2 workers give only about 1.3-1.5x. The new project needs a painterly stack whose expensive passes run once per layer or are pre-baked, not once per shape per frame.
6. ## 1.4 Getting it to render (the adapted renderer)

The adapted renderer is `audit/tools/render_linux.mjs`. It lives outside the clone and points at it with `--root`. Changes from render.mjs:

1. Chrome path set to /opt/pw-browsers/chromium-1194/chrome-linux/chrome, and `--use-angle=d3d11` replaced with `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`.
2. Google Fonts are served from audit/fonts/ by puppeteer request interception, and every other external request is aborted. Headless Chromium can't reach fonts.googleapis.com here, so `networkidle0` and `document.fonts.load` would otherwise hang or silently fall back. The script logs 'fonts loaded: true'.
3. The CPU-canvas flags are the default; `--faithful` switches back to the GPU-style canvas path.
4. `--disable-background-networking --disable-component-update` stops Chromium's proxy-denied calls home.
5. ffmpeg comes from imageio_ffmpeg.
6. `--w=960` downscales in-page.
7. `--stills` writes timings.json.

The modes `--stills`, `--sheet` and `--clip` are kept; `--clip` muxes the untouched mp3.

Example:
```
node tools/render_linux.mjs --root=/home/user/johnheibel/pdoomvideo --stills=3,12 --w=960 --workers=2 --out=frames
```
7. ## 2. What works (keep the spirit)

- **Coherent hand-made look.** Warm paper, ink that boils at 12 fps, and real Kubelka-Munk watercolour skies. It reads as painted, not vector and not 3D.
- **Every lyric gets an idea, and several are strong:**
  - the lunchbox-mouth CHOMP to black, re-opening from inside the mouth as the chorus stage (22.5→23 s)
  - the shoggoth's smiley mask being yanked off (29.5-33.4 s)
  - Clawd's eyes turning to stars ('sparks of AGI', about 4-5 s)
  - the red shinigami close-up (34 s): the strongest of the 16 frames
  - the Omega Point galaxy spiral (65.2 s): the best composition
  - the sleeping cloud 'CDR' guards
  - the one-point-perspective GPU aisle (119.8 s)
  - the chalkboard 'The cat sat on the [MASK]'
- **The P(doom) number going up** is the right Twitter-native device, but it is staged as a small HUD thermometer.
- **Animation craft encoded in code:**
  - `mood()` changes expressions with a squint, a squash take and an emote pop instead of snapping
  - backOut/elasticOut overshoot and anticipation
  - motivated transitions (whip, iris, heart pop, mouth close)
  - cameras that always move
- **Engineering.** Pure-function frames, deterministic randomness, a resumable parallel renderer, contact sheets, and a guide good enough that parallel agents stayed on-model.
- **The only K-pop moment is the dance break (35.5-38.5 s)**: a riser, a travelling spin-wave in the back line, the lead in the centre and a confetti hit. It is also the frame that feels most like a music video.
8. ## 3.1 Critique: character appeal

- **Clawd is a logo, not a performer.** A 10u x 6u rectangle with stub legs and arms and two slit eyes. Its acting is eye swaps and hat swaps (party, crown, hard hat, fedora, wizard, top). There is no hair, no hands, no costume language, and no mouth that could lip-sync.
- **The 'I' of the song is the wrong body.** The song is sung by a woman, but her lines are given to a generic dot-eyed chibi Researcher. Nobody sings on screen.
- **Small on screen.** Measured size of the largest Clawd per frame (legs and camera zoom included):
  - median 18% of frame height, interquartile range 16-25%
  - 40% or more in only 2 of 57 frames (34 s close-up 55%, 57 s Sydney 46%)
  - under 15% in 10 of 57 frames
  - only 8-10% at 1.8 s and 3 s
  - The guide's own target was about 40% in chorus and dance shots.
  - The Researcher's median is 25%.
- **Guests are mostly recoloured boxes.** Sydney is a pink box with a bow, Gato is a box with cat ears, and the RLHF panel is four copies of the same sprite. Only the shoggoth and the chinchilla are distinct designs.
9. ## 3.2 Critique: pacing vs the music (measured)

### The beat grid is wrong
core.js sets `BPM=88, OFF=0.21`, but the song is 132 BPM.

**Evidence from the kick:**
- Kick and percussive onsets sit on a 0.2273 s pulse.
- The kick-band profile over 8 pulses is [0.89, 0.25, 1.0, 0.19, 0.99, 0.32, 0.88, 0.18]: a kick every 2 pulses, i.e. **every 0.4545 s = 132 BPM four-on-the-floor**.
- Kick autocorrelation is 0.71 at a 2-pulse lag vs 0.18 at a 3-pulse lag.
- A least-squares fit to kick onsets gives 132.00 BPM, period 0.45453 s, first beat about 0.22 s, median residual 7.7 ms.
- Sliding 8 s windows give 131.6-132.4 BPM with a stable phase (no drift), except two ambiguous windows in the intro and the breakdown.

**Independent cross-checks:**
- https://github.com/mexicat/pdoom-video (README fetched 2026-09-28) reports '132.007 BPM'.
- The sibling analysis at claudepop/analysis/song.json has bpm 132, t0 0.235 s.

**Consequence.** 88 is exactly 2/3 of 132. Old beat n falls at 0.21+n·0.682 s: even n land on every third real beat, and **odd n land exactly on the off-beat 'and'**. So every `pulse()`, `move()` bounce, `pumpH()` stroke and beat-keyed cut alternates on and off the kick, and the dancing feels floaty.

**Karaoke is not synced to the voice.** It sweeps at a constant 0.45 + 0.075 s per character from each subtitle's start (timeline.js:110).

### The energy map is inverted
Loudness from 2 s RMS in dBFS (energy_2s.json):
- **0-2 s**, intro, -30 dBFS: a curtain title card.
- **2-16 s**, verse, -23: a dark lab with a tiny Clawd.
- **24-54 s** and **60-88 s**, full band, about -18: the busy middle chapters.
- **90-108 s**, breakdown, -22 to -25 (percussion -29 to -36): the video's busiest stretch. Cliff drop, paperclip flood, beach, planet, lit fuse, and a **BOOM with a white flash at about 105 s**.
- **110-136 s**, the drop, -16.3 to -17: a **calm teal tower-of-Clawds tilt**, clicker training and a chinchilla, all small, static and centred.
- **138-140 s**, a stop ('Was it all for show?'): the reveal. This one lands.
- **140-152 s**, the **loudest part of the song** at about -15, with no lines in lyrics.js: a wide, static curtain call of small characters bowing.

### Cutting
The 62 shots (mean 2.53 s, median 2.23 s, range 0.5-6.3 s) cut on subtitle-line boundaries rather than phrase downbeats. Cut density is never used as an intensity lever.
10. ## 3.3-3.4 Critique: hook and typography

### Hook
- 0-1.5 s: red curtains open on 'I'M UPPING MY P(DOOM)' in Permanent Marker while Clawd pops out of a trapdoor.
- Then a brush wipe into a dim indigo over-the-shoulder lab, with Clawd at 8-10% of frame height asleep on a CRT.
- The first strong image (star-eyes close-up) arrives at about 4 s.
- In muted autoplay the first frame is the thumbnail. A theatre curtain signals 'kids' show', and the dim wide shot that follows gives the eye nothing to lock onto.
- The opening is lyric-forward, which is good, but it is a static title card, not kinetic type.

### Typography
- The storyboard explicitly bans lyric signage ('Keep it text-light… no signs that repeat the lyric'). The brief wants the opposite.
- **Karaoke** is one design for all 156 s: Shantell Sans 800 at 50 px in a dark ink pill at y 978-1070, centred and drawn above the grain.
  - It reads as a subtitle UI and covers the bottom 9%.
  - The guide makes every shot keep action above y 960, which pushes every composition up and into the centre.
- **The only big type is about 8 SFX** (FOOM, SKRRT!, HONK!, BOOM, CHOMP!, SLAM!, POP!, CRASH!) in drop-shadowed Permanent Marker, an early-2010s webcomic look. They are still among the most memorable frames (25.5 s FOOM, 83 s SKRRT!) precisely because they are big type.
- **Key lyric words never appear as type in the world** ('Chinese room', 'CDR', 'Loom', 'Omega Point', 'Chinchilla', 'orthogonality'). The viewer has to decode the rebus from a subtitle while watching another part of the screen.
11. ## 3.5-3.8 Critique: composition, readability, repetition, concept, cheapness

### Composition
- **The proscenium is the default:** centred, eye-level, mid-to-wide and symmetric. 16 of the 57 sampled frames are the same red-curtain stage.
- There is little scale contrast, no rule-of-thirds 'lyric left / character right' layouts, and almost no deliberate negative space.
- **Dead frames:**
  - 12 s: a pink ellipse on empty cream; the loss curve doesn't read
  - 50 s: pastel dots on flat pink
  - 88 s: whip-pan colour bars
  - 126 s: a literal loom, half the frame black
  - 136.3 s: darkness
  - 142-150 s: the top 55% is backdrop
- **Clutter where the action is:**
  - 23.25 s: the mouth-iris leaves white tooth wedges along the bottom
  - 25.5 s: the FOOM rocket is buried in puffs
  - 61 s: the basilisk is not visible at the sampled beat
- **The corner P(doom) thermometer is a game HUD** and competes with the stage meter.

### Repetition
- The same orange rectangle appears in about 95% of frames (54 of 57 call `clawd()`).
- The same sunburst stage and curtains appear in all 4 choruses and the finale.
- The same karaoke pill, the same wooden floor, and the same shock shorthand (hair spikes plus sweat drop) throughout.
- The chorus escalation (party → pyro → paperclips → red alarm) is mostly a recolour of one set.

### Concept and zeitgeist
- 'A stage show that goes off the rails… it was all for show' turns the song's real vertigo into a school play and tells the viewer none of it was real. That is the wrong emotional answer for an audience living inside the acceleration discourse.
- The references are the 2023 LessWrong canon (shoggoth, basilisk, Sydney, Gato, Chinchilla, paperclips, Loom, Ilya), illustrated literally and cutely. There is nothing from the current timeline mood: no vertical charts, no math being eaten, no agents, no datacentre scale.
- It never uses the internet's own visual language (screenshots, posts, benchmark tables, terminals) as material, even though the protagonist is a terminal mascot. Concrete current events are left to the zeitgeist audit and are not asserted here.

### Cheapness tells
- Rectangle-with-outline characters.
- Clip-art props: treadmill, beach umbrella, museum mainframe, cacti, contour-line hills.
- Flat parallax, flat confetti rectangles, and 'dissolves' made of about 100 plain dots.
- Low-alpha blob glows.
- Paper that never moves or changes.
- Overall it reads as a very well-made Flash cartoon, the genre `legacy/flash-version.html` itself names.
12. ## 4. Notes on the 16 requested frames

- **3 s** (lab): atmospheric, but a small subject (Clawd about 10% of frame height), low contrast and a cropped head.
- **12 s** (loss ride / burst): a dead frame; the loss curve is not legible.
- **24 s** (chorus 1): Clawd pogos on the pump with the meter at 10% and a row of party-hat Clawds plus the Researcher. Readable, but symmetric and with no star.
- **31 s** (shoggoth): a good big shoggoth design; Clawd is a bystander at left.
- **34 s** (shinigami): a crimson close-up with red eyes and speed wedges. The best graphic frame.
- **44 s** (singularity): gym, black hole, Researcher flapping in the doorway. Reads OK, but everything is small.
- **50 s** (atoms): dots on pink. Near-empty.
- **55 s** (Sydney): a cute heart cage, but Sydney is a recoloured box.
- **61 s** (basilisk boom): a cracked floor and a flame; the monster misses the sample.
- **67 s** (1e30 flops): a GPU card with galaxy fans and an odometer. Flat execution.
- **80 s** (von Neumann): a clip-art museum mainframe. Literal.
- **88 s**: a whip-pan frame of colour bars.
- **98 s** (paperclips): Clawd surfs a paperclip wave. Energetic and readable.
- **110 s** (the drop): a calm teal sky over a Clawd stack. Wrong energy.
- **126 s** (Loom): a literal loom, half-empty, with the karaoke not yet shown.
- **138 s** (all for show): the backstage reveal reads, but it is staged flat.

**The 41 extra frames confirm the pattern.** The best images are one big graphic idea filling the frame: 5 s star-eyes, 28.7 s shroom swirl, 34 s, the 36.8 s dance line, the 65.2 s spiral, 83 s SKRRT!, the 119.8 s GPU aisle. The worst are wide, centred tableaux of small characters: 19.5, 27.2, 46.5, 63.7, 71.5, 86.5, 101.5, 116.2 and 142-150 s.
13. ## 5. Reusable code and ideas

### Port nearly as-is
- The pure-function frame contract and the chapter/shot registry (timeline.js:8,29).
- The resumable parallel renderer with contact-sheet mode (render.mjs; Linux port at audit/tools/render_linux.mjs).
- The timing kit (core.js:9-47): `seg`, array-valued `kf` keyframes, `ease`/`easeOut`/`easeIn`/`backOut`/`elasticOut`, `frac`, `wob`, `hash`, `shakeXY`.
- The camera and letter projection (`camBegin`/`camEnd`/`toScreen`, `letter()`): world-space type that moves with the camera.
- `flushLetters()` (core.js:141): paint can occlude type, so type lives inside the image. This is the key trick for lyrics embedded in the scene.
- `irisShape(pts)` (core.js:64): reveal masks of any star-shaped outline (mouth, heart, keyhole, logo), good for match cuts.
- `mood()` (clawd.js:211) for the idol's face changes.
- `move()` (clawd.js:222), the beat-driven dance library, after moving it to the 132 grid and adding 8-count choreography.
- The 12 fps boil via `randomSeed(floor(T*12))`, extended to the paper.
- The ink brush definition (core.js:175).
- The brush-stroke wipe (timeline.js:73), used sparingly.
- The P(doom) counter concept (`pdoomAt`), restaged as giant type rather than a HUD.

### Rewrite
- **Beat grid:** BEAT=0.45453, t0 about 0.22-0.235. Better still, drive hits from an event list of kick, snare and vocal onsets, and keep bar/phrase indices for choreography.
- **Karaoke:** word- or syllable-level forced alignment instead of constant-rate sweeps.
- **Characters:** designed, layered characters instead of wash rectangles. Keep the draw/armL/armR hook pattern for props.
- **Paper:** a sheet per drawing, meaning a per-boil offset or swap, camera-coupled parallax, fibre lighting, deckled or taped inserts, and mis-registration.

### Storyboard ideas worth keeping
The CHOMP-to-black and reveal from inside the mouth; the shoggoth mask yank; eyes turning to stars; the sleeping 'CDR' cloud guards; the Omega spiral; the GPU aisle push; the P(doom) counter as a through-line; the Ilya door with light leaking out and chains.
14. ## 6. Implications for the new video

1. **Frame 1 is the hook.** A huge kinetic lyric word plus the idol's face within the first 12 frames. No curtain and no dim wide shot.
2. **Lock to 132 BPM and to the real energy map.** Go biggest at 110 s and 140-152 s, strip back at 90-108 s, and use the 138 s stop as a silence or freeze gag.
3. **A star.** A personified Claude idol (sunburst/spark motif, feminine, K-pop direction), lip-synced and at 40-70% of frame height in choruses. Box-Clawd becomes a backup dancer or mascot cameo.
4. **Typography as set design.** Lyrics painted into the world through the camera (`letter()` + `flushLetters()` pattern), alternating subtitle-size and full-bleed, with calm negative space reserved for the giant words.
5. **Speed as structure.** Cut density, camera speed and the counter visibly accelerate across the song, instead of one stage that changes colour.
6. **Physical paper.** Cut-paper or collage layers with parallax, shadows and mis-registration, plus brutalist inserts of recognisable internet artefacts. Keep watercolour for skies and washes.
7. **A cheaper painterly stack** so an iteration takes minutes on this CPU box. p5.brush's per-shape spectral composites run about 18 s per frame here.
15. ## Sources

- **The previous video:** https://github.com/JohnHeibel/PDoomVideo. Its README says it was made with Claude Opus 5.5 in two generations, links the video at https://youtu.be/8j-hR4fJywU, and credits https://x.com/slimer48484/status/2097752569212756134 as inspiration (x.com is not openable here).
- **Lyric interpretation:** https://docs.osmarks.net/hypha/p(doom)_song_objectively_correct_interpretation. The egress proxy blocks it; not read.
- **Tempo cross-check and provenance:** https://github.com/mexicat/pdoom-video, fetched 2026-09-28. It reports '132.007 BPM', and says the song was 'generated with Udio and released in November 2024' and 'This video uses the Claude-Pop version made with Suno, posted by deckard in September 2026'. I have not verified that assets/pdoom.mp3 (156.65 s) is that exact generation; only duration and tempo are consistent.
- **p5.brush internals:** v2.2.3 source in node_modules (src/fill/fill.js, src/core/gl/shader.frag), https://github.com/acamposuribe/p5.brush.
- **All tempo, energy, timing and size numbers** are my own measurements (librosa on the untouched mp3; instrumented headless renders). Onset phases are ±30 ms.

## Artifacts
- `/home/user/HENRYDENG/claudepop/audit/contact_sheet.png`
- `/home/user/HENRYDENG/claudepop/audit/contact_sheet_extra.png`
- `/home/user/HENRYDENG/claudepop/audit/frames/ (t003_00.png, t012_00.png, t024_00.png, t031_00.png, t034_00.png, t044_00.png, t050_00.png, t055_00.png, t061_00.png, t067_00.png, t080_00.png, t088_00.png, t098_00.png, t110_00.png, t126_00.png, t138_00.png + timings.json)`
- `/home/user/HENRYDENG/claudepop/audit/frames_extra/ (41 supplementary frames 0.9-154 s)`
- `/home/user/HENRYDENG/claudepop/audit/tools/render_linux.mjs`
- `/home/user/HENRYDENG/claudepop/audit/tools/stats.mjs`
- `/home/user/HENRYDENG/claudepop/audit/tools/stats.json`
- `/home/user/HENRYDENG/claudepop/audit/tools/contact_sheet.py`
- `/home/user/HENRYDENG/claudepop/audit/tools/grid_fit.py`
- `/home/user/HENRYDENG/claudepop/audit/tools/beatgrid.json`
- `/home/user/HENRYDENG/claudepop/audit/tools/drift.py`
- `/home/user/HENRYDENG/claudepop/audit/tools/local_tempo.json`
- `/home/user/HENRYDENG/claudepop/audit/tools/energy.py`
- `/home/user/HENRYDENG/claudepop/audit/tools/energy_2s.json`
- `/home/user/HENRYDENG/claudepop/audit/tools/meter_check.py`
- `/home/user/HENRYDENG/claudepop/audit/tools/coverage.json`
- `/home/user/HENRYDENG/claudepop/audit/perf/t003_faithful_gpu2dcanvas.png`
- `/home/user/HENRYDENG/claudepop/audit/perf/t003_fast_cpu2dcanvas.png`
- `/home/user/HENRYDENG/claudepop/audit/perf/t003_absdiff_x4.png`
- `/home/user/HENRYDENG/claudepop/audit/fonts/`

## Caveats
- REPORT.md was not written. The Write tool refused it (the harness bans subagent report .md files), and I did not route around that block with Bash. The full report is in key_findings, in section order, ready to be saved to /home/user/HENRYDENG/claudepop/audit/REPORT.md.
- Frames were rendered on the fast path (CPU 2D canvas). It is about 8x faster than the default GPU-style canvas path on SwiftShader, but low-alpha watercolour glows come out a little weaker than in the author's GPU render (mean absolute difference 6/255 at t=3; see audit/perf/). Linework, flat colour and composition match.
- Per-frame timings were measured on a shared machine (other workflow jobs were using CPU). The instrumented single-worker pass gives a median of 18.4 s per 1080p frame. Earlier two-worker renders measured 17-108 s per frame under contention (tools/render_frames.log, render_extra.log).
- Character sizes come from instrumenting `clawd()`/`researcher()` with the p5 model-matrix scale (camera zoom included). They ignore the characters' internal sx/sy squash and don't count chorus 1's private `miniClawd` background dancers. tools/coverage.json holds a cruder colour-mask cross-check that leaks on wood floors; don't quote it on its own.
- The tempo and grid findings (132 BPM, first beat about 0.22-0.235 s) agree with an independent public analysis and with the sibling claudepop/analysis/song.json. The claim that 140-152 s has no timed lyrics comes from lyrics.js alone; whether there are vocals there wasn't checked (no stem separation run).
- Two sources could not be read: docs.osmarks.net (lyric interpretation) is blocked by the egress proxy, and the x.com inspiration post can't be opened.
- /home/user/HENRYDENG is a git repo that another process appears to auto-commit (log shows 'work in progress' commits touching claudepop/audit). I made no commits and pushed nothing. The pdoomvideo clone has no changes apart from the gitignored node_modules/.
