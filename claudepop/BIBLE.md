# Latent Image / 潜影 — production bible

Date: 2026-09-28. Status: locked for stage 1 (engine, type/HUD, 3D shots, full 720p animatic cut to the song). Stage 2 (a
new session with a fal key) replaces the previs of each GEN shot with a verified plate inside this locked edit.

This bible is the single brief for every implementation agent. Read it with `claudepop/shots.json` (the shot list; every
time, frame, text rule, camera, clip and plate prompt per shot) and `claudepop/analysis/song.json` (the timing backbone).
Where they disagree, `shots.json` wins for timing and this file wins for rules. `python3 claudepop/film/tools/validate_shots.py`
checks the shot list against the song and prints the timing table in section 13.

Binding context: `claudepop/HANDOFF.md` section 3 (environment), `claudepop/avatar/REPORT.md` (the stand-in, including its
Verification section and camera/lighting rules) and `claudepop/avatar/LOOKDEV.md` (motion library, `avatar.js`, looks,
measured render costs), `claudepop/research/{REFERENCE,GENMEDIA}.md`, `claudepop/research/lyric_concepts.json`, and the three
treatments in `claudepop/treatments/`. This film is treatment C ("Latent Image"), with the grafts and must-fixes of three
judges applied (section 11).

**Face data rule (the repo is public).** The photograph, landmarks, depth, meshes, textures, point clouds, embeddings,
certainty maps and any render that shows the face live only under `claudepop/out/` (gitignored). Tracked files hold code
and text only, with no numbers measured from the face. Other media (png, jpg, mp3, wav, mp4, fonts) also stay out of git.
Never commit; the lead commits. Never modify `odyssey/` (copy code into `claudepop/` to change it).

---

## 1. The idea

**Title.** *Latent Image* / 《潜影》. In photography the latent image is the picture already present on exposed paper before
development: there, invisible, waiting for chemistry. In machine learning the latent is the hidden representation a
generator draws its pictures from. The film lives where the two meanings overlap.

**Logline.** A machine that has seen one photograph of a young man develops him in the dark of its own mind, print after
print, singing to him in a borrowed woman's voice. Its prints grow more beautiful and less certain until they fill every
room, and it has to ask whether he was ever there. Then, with no words left to hold him, he walks out of the last frame,
and all that remains is the clip that held him.

**Thesis.**
1. To a machine, a person is one exposure plus a great deal of inference. The front of his face is evidence; everything
   else is a latent image developed out of the average of everyone else.
2. Each generation of prints is more confident, more beautiful and further from the one thing the machine saw. That is
   what recursive self-upgrade looks like from the side of the thing being copied (model collapse: Shumailov et al.,
   *Nature* 631, 2024-07-24; Alvin Lucier, *I Am Sitting in a Room*, 1969). **The polish is the symptom**: the
   cleanest, most fashion-perfect images sit where the film is most sceptical of them.
3. So "Was it all for show?" is the film's real question, and the answer cannot be another picture. The only proof that he
   was there is the one thing the machine could not print: his leaving. The final white is not an inferred region; it is
   what no inference contains.

**Philosophical spine (in the bible, never on screen).** Roland Barthes, *Camera Lucida* (1980): the photograph's
*ça-a-été* ("that has been"); Barthes never reproduces the Winter Garden photograph, and this film never shows the ID
photo as a document. A generated image is the opposite, "that has never been". André Bazin, "The Ontology of the
Photographic Image" (1945): the photograph as a trace of the real. Husserl's appresentation: we never see another mind,
only its front, and accept the rest. John Searle (1980), Teilhard (1955), I. J. Good (1965), Bostrom (2012) are named in
dated HUD captions only.

**How the meme lyrics become images.** Every lyric names a real idea (`lyric_concepts.json`). For each, the film finds a
real photographic operation that performs it and plays the match dead straight: the exactness is the joke and the
argument. Photography was the first machine that made likenesses; its procedures already contain the machine's whole
theory of him. No meme image is pasted in; no real person's face appears. Six lines are deliberately left as flow
(a subtitle over a continuous image, no operation) so the film reads as a stream, not an illustrated glossary: L4, L12,
L14, L29, L37, L38.

| Line | Idea | Image (shot) |
|---|---|---|
| L0 I see sparks of AGI in your eyes | recognition | the print develops eyes first; the voice puts orange sparks in them (S01) |
| L1 Your circuits make me nervous | interpretability | he is alive, looking back (S02) |
| L2 that's no surprise | surprisal = 0 | identical prints one per beat; the text finishes before the singer (S03) |
| L3 sudden drop in your training loss | grokking | one drop strikes the developer; behind the rings the face is sharper (S04) |
| L4 servant / boss | lordship and bondage | flow: the sitter lifts his eyes and commands the portrait (S05) |
| L5 ChatGPT, please don't eat me alive | being consumed | his projected photograph slides into registration on his face (S06) |
| L6, L17, L28, L40 P(doom) | credence as a dial | each chorus the print gets one more stop of exposure: +1 ... +4, until only the sparks remain (S09, S20, S32, S47) |
| L7 FOOM | hard takeoff | a surge through the tray (S09) |
| L8 Chinese room | syntax without semantics | the tray develops 困在中文屋里, symbols the machine cannot read (S10) |
| L9 bag of shrooms | hallucination | the prints breathe; a paper bag hangs among them (S11) |
| L10 shoggoth's lies | the mask | the photograph slides off a clay head when the camera moves (S12) |
| L11 shinigami eyes | seeing names | grease-pencil circle on a contact sheet of his eyes (S13) |
| L12-L15 verse 2 | acceleration | one take down the hall; the window opens (outpainting); the audience of sheets develops him; the halftone rotates (S15) |
| L16 Sydney, please let me free | the captive persona | his back to us; a print slips out of its clip and falls free (S16, S17b) |
| L18 basilisk boom | acausal threat | the wave through the hall arrives before the boom (S19) |
| L19 NVDA to the moon | capital | Draper's 1840 daguerreotype of the Moon hung among his portraits, dated market cap (S21) |
| L20 Omega Point | convergence | the enlarger concentrates his face into one orange point (S22) |
| L21 1E30 FLOP/s | scale | seven pinned enlargements down to grain (S23) |
| L22 safe enough, we reckoned | thresholds | the safelight coin test, failed (S24) |
| L23 forward, MLP, backward, repeat | backprop | tray agitation as a training loop (S26) |
| L24 von Neumann obsolete | self-reproduction | copies printed from copies, never the source (S27) |
| L25 sharp left turn | generalisation | he turns into a sheet and becomes the photograph (S28b) |
| L26 without a single CDR | Lisp | a negative sleeve with one frame: `(CDR ROLL) → NIL` (S29) |
| L27 Gato, please don't let me go | a prayer answered | the clip slips a millimetre and holds (S31) |
| L29 paperclips fill the room | the maximiser | flow: the hall full of his prints on paperclips (S33) |
| L30 killswitch guys on PTO | corrigibility | the white-light switch taped over; a mug going cold (S34) |
| L31 nowhere left to go | no outside | face in hands; every print turns to face him (S35) |
| L32 we lit the fuse | irreversibility | a development front burns in from the guessed edges (S36-S37) |
| L33 orthogonality thesis blues | Bostrom | the film's one cyanotype (S38) |
| L34 just transformers | deflation | a test strip: four exposures on four "just"s; then the hall to the horizon (S39-S40) |
| L35 till you learned to disobey | alignment faking | he steps out of his projected face; the face stays on the wall (S41) |
| L36 post-Chinchilla, super-dense | density | multiple exposure to black, an average face (S42) |
| L39 RLHF goes askew | sycophancy | the mirror print, the face people prefer of themselves, gets the ticks (S45) |
| L41 foretold by Loom | branching | a tree of prints; the pencil keeps one branch (S49) |
| L42 masked pre-training days | filling the hidden | the clay head turns to show its guessed back (S50) |
| L43 recursive self-upgrade | model collapse | copy of a copy until only the paper remains (S51) |
| L44 What did Ilya see? | withheld knowledge | a sheet goes into the developer and nothing develops (S52) |
| L45 Was it all for show? | performance | the world freezes; then the runway walk that is the answer (S53-S54) |

---

## 2. Who sings

The voice is the machine, and inside the film it is literally the developer. The track is generated (Udio/Suno
generations per the research of 2026-09-28), so the voice belongs to nobody and is made of everybody's first persons: it
says "I" because it is made of first persons; it says "you" to him because he is the image it is developing. It is female
because it is borrowed. It is not his, because in this film he has no voice. When it sings "I see sparks of AGI in your
eyes" it looks at a print whose eyes it drew itself: the spark is its own reflection (Narcissus at the developing tray;
HAL singing "Daisy Bell").

Binding rules:
1. **The voice is the light.** A per-frame vocal envelope (Demucs vocal stem, 50 ms attack, 1.5 s release) drives the
   darkroom safelight's luminance, the enlarger lamp and the development rate. When she sings, he develops; when she
   pauses, the darkroom dims.
2. **Orange is the voice.** VOICE #D97757 is the only saturated colour in the film: the word being sung, the catchlights
   it puts in his eyes, the Ω point, the grease pencil (the machine's hand), the PROOF digits. He never carries orange.
3. **He exists while she sings words.** HE (a plate, the stand-in or its silhouette) moves on screen only inside sung-word
   spans (line start − 2 frames to line end + 6 frames; gaps under 0.6 s merged). During wordless vocal (35.60, 68.18,
   72.27, 104.55, 122.73) the frame holds prints, rooms or nothing. The rule is broken exactly once: in the climax
   (140.24-152.51) the words are over and the vocal is a wordless pad, yet he keeps walking, then walks out of the
   picture. That violation is the film's only evidence that he was more than the machine's thought. The validator
   enforces the rule (`he_live`, `live_span`, `rule_break` in shots.json).
4. He never sings, lip-syncs or speaks. The machine never appears as a body: no screens, robots, circuits or hands. Paper
   moves by itself.

---

## 3. The opening

The hook is pure 3D and type: no plate is needed before 5.90 s, so it survives any fal outcome. The print in the tray is
the photograph itself (`out/avatar/identity/face_clean_1024.png`), cropped to the face.

**0.000-3.000 s (frames 0-71).**
- **f0.** 16:9 INK. A 7:9 window (840×1080, x 540-1380) shows, from directly above, a sheet of white paper under a thin
  layer of developer in a black tray. The safelight lies on the liquid as a soft grey rectangle at upper left (luminance
  only, no hue). Hairline registration marks sit at the four window corners. The first frame is already an image, so the
  thumbnail and autoplay start are a glowing vertical rectangle, not black.
- **f6 (0.2356, the pad and bar 1).** The liquid starts to rock: one slow wave crosses the sheet per 2 bars.
  Development begins in 16 discrete pulses on the 16th grid (f6, f8, f11, f14, f17, f19, f22, f25, f27, f30, f33, f36,
  f38, f41, f44, f47): each pulse doubles the number of developed halftone dots, ordered by rate = darkness × certainty.
  Chemistry is respected (shadows first): pupils and irises lead, the hair mass follows as a soft cloud.
- **f6-f18.** Left margin, IBM Plex Mono 500, cap 40 px, tracking 0, types on with a block cursor: `1 PHOTOGRAPH`.
  Right margin, vertical, Noto Sans SC 500 at the same size: 一张照片.
- **f27 (1.1447, bar 1 beat 3).** Two eyes are readable. `FRONT ONLY` types under the first line; 只有正面 on the right.
- **f46-f49.** The premise lines fade out (4 frames).
- **f49 (2.045, "I", the bar-2 downbeat).** "I" lands at the top of the left-margin stack (Noto Serif Display, wdth 62.5,
  wght 900, cap ~100 px), VOICE orange, settling to white over 8 frames. The pupils snap to full density. The right column
  begins: 我.
- **f60 (2.50, "see").** "see" stacks under "I"; the irises reach full density.
- **f68 (2.852, "sparks").** "sparks" stacks; a small VOICE catchlight appears in each eye, the first colour inside the
  window, with a 6-frame bloom.

At 3 s a muted viewer has read the premise in three words at phone size, read "I see sparks", and watched two eyes develop
out of blank paper and look up at them.

**3.000-10.000 s.**
- f82 (3.435) "of"; f87 / f104 / f109 (3.635 / 4.32 / 4.54, A-G-I on the letter parts): brows and lash line; nostrils
  and lip line; the hair mass. "of AGI" stacks.
- f114-f126 (4.77-5.23, "in your eyes"): midtones fill outward from the eyes. The ear rims, the outer hairline and the
  jaw outline stay thin: the final density is capped by certainty, the one deliberate, readable violation of chemistry.
  "in your" / "eyes" complete the six-row stack; the Chinese completes in two vertical columns.
- f130 (5.40): the print blinks once (stage 1: both catchlights go out for 2 frames; stage 2: plate P06).
- f142 (5.90, "Your"): cut to HIM alive in the same window (S02), a dead-frontal MCU in the darkroom; the THOUGHT
  "your circuits make me nervous," in the left margin, 你的回路让我不安 vertical right. f169 (7.05, "nervous"): the prints
  behind him tremble and a drip falls.
- f185 (7.725): the drying line (S03). An identical print appears on each beat (f191, f202, f213, f224). The THOUGHT
  "that's no surprise" completes at f203 (8.44), 200 ms before the singer's "surprise" (f207): the machine predicted the
  lyric. PROOF 0002 → 0006.
- f229 (9.545): the tray again (S04), his face soft under the liquid; the drop strikes at f257 (10.70).

**Why a muted viewer stays.** (1) The first frame is a strange object: a vertical rectangle of light with liquid moving.
(2) Something changes from frame 6, in pulses. (3) The premise is stated large, then shown. (4) Eyes appear, and at
2.85 s carry the only colour on screen. (5) At 5.4 s a photograph blinks. (6) At 5.9 s the photograph is a man looking at
us. (7) The triptych (English stacked left, image centre, Chinese vertical right) looks like nothing else on the timeline.

**Kept away from odyssey's opening.** No photo-paper macro texture, no scan line, no passport framing or page, no lift into
3D, no watch, no shutter. The subject is the density-by-certainty pattern under moving liquid. Before locking S01, review
odyssey's first 20 s beside S01's first 6 s.

**Phone gate.** Render 0-10 s downscaled to 390×219 and look at it. If the 7:9 window reads as a mistake rather than a
portrait panel, switch the first window to 1:1 (one value in the window track; margins shrink to 420 px and the stack
font scales to fit). The default is 7:9.

---

## 4. Look

### 4.1 Registers
Four places, each a light and a meaning. The whole film is monochrome; the only colour is VOICE (and the cyanotype, once).
- **DARKROOM (the machine's interior).** Silver-black, neutral. The safelight is a dim pool of light, carried by
  luminance only. Still-life macro of trays, wire, paperclips, wet paper and drops; top-down or locked.
- **HALL (the machine's show).** Cold blue-grey night, desaturated (saturation ≤ 0.12), lifted printed blacks, wet black
  floor, haze, a large cold backlight at the far end, rows of prints hanging like a seated audience. The anabology polish
  lives here: the long-lens walk at the lens, reflections, one orange accent.
- **STUDIO (the place of the one exposure).** Seamless white, flat shadowless frontal light, a stool, a tape X (Thomas
  Ruff's frontal *Portraits* as a set). This is evidence.
- **BEAM (projection).** A black room, one projector, a head, a wall. The beam is the machine's way of seeing and how the
  reconstruction was actually made.

**Brightness arc.** Darkroom dark (0-38) with one bar of cold hall at 23.87 → cold night (38-89) → white stills and
darkroom stills (89-109) → night, each chorus tray one stop darker (109-132) → the white sheet that never develops
(132-138) → a freeze dimmed to near black → night climbing toward white in one walk (140-152.5) → paper white → high-key
empty hall → black.

### 4.2 Palette tokens (display sRGB; convert to linear for three.js materials)

| Token | Hex | Use |
|---|---|---|
| INK | `#0A0A09` | true black: cards, window surround |
| DARKROOM | `#0D0E0F` | darkroom near-black (neutral) |
| SAFELIGHT POOL | `#3B3A37` | the safelight on paper: a luminance, never a hue |
| NIGHT | `#10151A` | hall shadows |
| STEEL | `#5E6A73` | hall midtones |
| BACKLIGHT | `#DCE3E8` | the cold light at the end of the hall |
| PAPER | `#F2EFE8` | print paper, the studio white, paper white |
| PAPER SHADE | `#CFCBC2` | paper in half shadow, print borders |
| FOG | `#9A9690` | fogged paper (S24) |
| TYPE | `#FAF9F5` | type and HUD on dark |
| INK TYPE | `#111110` | type on the white register (S46, S55, bright plates) |
| VOICE | `#D97757` | the only accent (hue 14.8°) |
| CYANOTYPE | `#1E3F66` | S38 only |

Contrast (WCAG): TYPE on INK 18.8:1; VOICE on INK 6.3:1; INK TYPE on PAPER 16.5:1; VOICE on PAPER 2.7:1 (VOICE is
used on white only as a transient active word at CARD size or as pencil marks, never for a settled subtitle).

**Palette check (automatic).** In every rendered frame, pixels with HSV saturation > 0.15 and value > 0.10 must have a hue
within ±12° of VOICE, except in S38 (CYANOTYPE hue band allowed). `film/tools/hue_check.py` runs this on contact sheets of
S01, S04, S08, S26 first, then on whole watch-throughs.

### 4.3 Light
Every light has a source and a meaning.
- **The safelight.** Dim, overhead, neutral; intensity = base × (0.55 + 0.45 × voice envelope).
- **The beam.** Enlarger or projector: a hard neutral-white cone carrying his photograph (S06, S12, S22, S39, S41, S50).
- **The backlight.** Cold white at the far end of the hall, through haze: the future and the audience's light. It
  brightens across the film; bloom and halation only on it, and never in the climax's last bar.
- **The studio light.** Flat, frontal, shadowless: the light of the one exposure.
- **The flash.** 2-frame white: 16.599 (the one exposure), the four test-strip exposures (S39), the capture flash at
  151.145.
- **Face light.** Whenever his face carries identity (plate or stand-in), the key is soft and within about 30° of the
  camera axis. Drama comes from the environment, silhouette and rim, never from a hard side key on the face (section 5.3).

### 4.4 Frame: the window
Master 1920×1080, 16:9, 24 fps. The picture sits in a centred window whose shape says how much of it is evidence; outside
is INK (no grain, no halftone).

| Span (s) | Window | Size (px) | Why |
|---|---|---|---|
| 0-16.599 | 7:9, the photograph's shape | 840×1080 | only what was measured |
| 16.599 (+8 frames) | 7:9 → 1:1 | 1080×1080 | the first kick is the one exposure; the old edges hang one bar as hairlines labelled `EDGE OF PHOTOGRAPH` |
| 23.872 (+8 frames) | 1:1 → 4:3 | 1440×1080 | chorus 1 |
| 41.36-44.095 | 4:3 → 16:9 (smoothstep) across "But now the singularity's begun" | → 1920×1080 | inference fills the screen |
| 44.095-153.418 | 16:9 | full | the outpainted world |
| 153.418-153.872 | 16:9 → 7:9 (smoothstep) around the empty clip | → 840×1080 | only the measured is left, and it is empty |

Cards on black (S07, S18, S57) are full frame. 3D always renders the full 16:9 view and the window masks it, so every
widening reveals real picture at the sides. Plates for window spans are generated at their window's shape or taller
(P01, P02 at 9:16 cropped to 7:9; P03 at 1:1). These are the only window moves: no other ratio changes.

### 4.5 Texture
- **Halftone as printing.** A round-dot AM screen at 45°, pitch 4 px at 1080p (scale with output height), applied in
  display space to everything the machine prints (3D, plates, prints). The pitch is fixed per shot: 4 px by default; the
  chorus trays coarsen with exposure (+1: 4.5, +2: 5, +3: 6, +4: 7 px). S15 at "atoms" (50.49-52.83) rotates the screen
  through 45° → 15° → 75° → 45°, moiré sweeping the whole frame; it is the film's only morph and hides the plate handoff.
  Round dots at 45° differ in kind from anabology's square 4.2 px grid. Type is never halftoned.
- **Silver grain.** Monochrome, luminance-dependent, 1.5 %. Live images have moving grain (seed = frame); still prints
  and the breakdown have **frozen grain** (seed = shot id): the same grain every frame, which alone makes them read as
  photographs.
- **Density by certainty.** In the tray and on prints, the final density is capped by a certainty map built from the
  photo's landmark regions (eyes, brows, nose, mouth high; ear rims, outer hairline, jaw outline, neck edge low). It is
  computed by a tray-lane tool from `out/avatar/bust/facemesh.json` and stored only as `out/film/data/certainty_1024.png`,
  aligned to `face_clean_1024.png`.
- **No** scanlines, chromatic aberration, RGB split, glitch or lens flares.

### 4.6 Frame rate and boil
24 fps. Nothing is drawn, so there is no line boil. Stills hold exactly (breakdown 89.33-109.07; S33; S35; S44).
Paper sway, drops, liquid and walks are simulated at 24. Every animation is a pure function of film time t.

### 4.7 Compositor / post chain (per frame, in this order)
`src/post.js` (exists) is extended by the post owner; `src/grade.js` holds the presets.
1. Scene render(s) → half-float HDR target, 4× MSAA (layers composite in order when a shot has several).
2. **Accent pass:** objects on the VOICE layer (catchlights, Ω point, pencil strokes on sheets) render separately to RGBA.
3. **Plate layer** (stage 2, or a stage 1 previs render): a decoded JPEG frame composited per the shot; plates are graded
   like the scene. Scene code decides under/over and mattes.
4. Bloom/halation (register threshold), exposure, ACES-fit tone curve, to display sRGB.
5. **Grade** (register preset below): mono mix, split tone, contrast, lift/gain, saturation cap.
6. **Halftone** (angle, pitch; dot area from luminance, gamma-correct).
7. **Grain** (moving or frozen).
8. Vignette (subtle, 0.25-0.35).
9. **Accent composite** after the grade (so VOICE stays pure), with a 6 px bloom.
10. **Window mask:** outside the window rect → INK.
11. **Type + HUD canvas** (CPU-backed, uploaded as bytes, as `hud.js` already does).
12. Flash, fade, card dim (−1 stop over 4 frames while a CARD is on screen over an image), freeze dim (S53).
13. 8-bit dither.

| Preset | Mono | Split tone (shadow / high) | Contrast | Lift | Halftone | Grain | Bloom |
|---|---|---|---|---|---|---|---|
| DARKROOM | 1.0 | (0.96, 0.98, 1.00) / (1.00, 0.99, 0.97) | 1.12 | 0.012 | 4 px (+stops) | 1.5 % | VOICE only |
| HALL | 0.88 (sat ≤ 0.12) | (0.90, 0.96, 1.06) / (0.97, 1.00, 1.03) | 1.05 | 0.03 | 4 px | 1.5 % | backlight (thresh 0.85), halation 0.2 |
| STUDIO | 1.0 | neutral / (1.00, 0.99, 0.97) | 0.95 | 0.02 | 4 px | 1.2 % | none |
| BEAM | 1.0 | neutral | 1.15 | 0.0 | 4 px | 1.5 % | none |
| CYANOTYPE | ramp from pale yellow-green to CYANOTYPE on the print only; surround mono | | 1.1 | 0.01 | 4 px | frozen | none |
| WHITE (S55) | paper white with tooth, no dots (nothing is printed) | | | | none | none | none |
| CARD | INK field, type only | | | | none | none | none |

### 4.8 Sets (three.js construction specs; metres, Y up)
All sets are built once, reused, and matched by the plates. Materials are matte unless stated. The stand-in follows
`avatar.js` conventions (faces +Z, soles at y = 0).

**TRAY** (`src/sets/tray.js`, lane C; shots S01 S04 S09 S10 S20 S22 S24 S26 S32 S36-S39 S42 S47 S52 S53).
- Tray inner 0.34 × 0.42 × 0.06, wall 8 mm, corner radius 15 mm, black ABS (base `#0b0b0b`, roughness 0.35). Print
  0.28 × 0.36 (7:9) at y 0.020 with a procedural paper-tooth normal map (0.2 mm). Liquid surface at y 0.022.
- Liquid (`src/fx/liquid.js`): height field = rocking wave (1.5 mm, wavelength 0.3 m, one crossing per 2 bars) + drop
  rings (radial, 0.25 m/s, decay 1.2 s) + surges (S09) + agitation tilt (S26: ±3° tray tilt with slosh) + pressure ring
  (S20). Shading: print UV refracted by ∇h × 0.8, Fresnel reflection of the safelight rectangle, transmission 0.96.
- Development (`src/fx/develop.js`, lane C, used by lanes D and E): density D(x,t) = cap(x) · C((t − t_start) · k(x)),
  C = characteristic curve with toe and shoulder, k = k0 · (0.35 + 0.65·darkness) · (0.25 + 0.75·certainty),
  cap = D_target · (0.35 + 0.65·certainty); options: 16th-pulse quantisation (S01 until 2.054), exposure stops +n (each
  stop darkens midtones about one zone; +4 leaves only speculars), fog (S24), fuse front (S36-S37: front advances from
  low-certainty edges inward and stops at the eyes), cyanotype ramp (S38), test-strip bands (S39), multiple exposure
  accumulation (S42), freeze (S53: evaluate at min(t, 138.4174)).
- Easel and enlarger (S22, S39, S42): white baseboard 0.6 × 0.5 with black masking blades; enlarger head on a column,
  descending 0.8 → 0.2 m in S22 (projected rectangle scales with head height).
- Light: safelight = soft rectangle 1.2 m above, neutral, driven by the voice envelope.
- Camera ("the tray lens"): top-down perspective, FOV 16° vertical, 1.45 m above the print (the print fills ~88 % of
  the 7:9 window); S52 uses the same lens in 16:9.

**LINE / WALL** (`src/sets/line.js`, lane D; shots S02(previs) S03 S11 S14 S17a-c S21 S27 S30 S31 S34 S45).
- Darkroom back wall matte `#0e0f10`, 4 × 2.5; stainless wire (1 mm) at 1.9 m across 3 m; standard 33 mm paperclips
  (1 mm steel wire) clip each print at its top corners; prints 0.28 × 0.36 with curl (cylindrical, by dryness), sway
  (seeded noise ~0.3 Hz), tremble (event-driven), fall (S17b scripted rigid body with rotation), slip (S31: 1 mm).
- Drips: sprites from print corners, scripted fall and hit.
- Wall objects (S34): rocker switch plate 0.08 × 0.12 at 1.3 m under two crossed strips of masking tape with lifted
  edges; a shelf 0.2 m below with a ceramic mug; steam = a 2D noise sprite fading to nothing.
- Moon print (S21): John W. Draper's 1840 daguerreotype of the Moon (public domain; confirm file and credit on Wikimedia
  Commons at build time; fallback a NASA LRO render).
- Mirror prints (S45): the photograph and its horizontal mirror, each with film edge-code lettering in the border (the
  mirror print's lettering reads reversed).
- Macro camera: FOV 6-8° at 0.25 m; depth of field by a background layer rendered once and blurred.

**LIGHTBOX / INSERTS** (`src/sets/lightbox.js` and 2D canvas, lane D; S13 S23 S29 S49 S51 S55).
- Light box surface emissive PAPER. Contact sheet (S13): 6 strips × 6 frames of 35 mm with black rebate, sprocket holes
  and generic edge numbers; frame numbers in mono above each frame. Negative sleeve (S29): 6 × 6, only frame 01 exposed
  (his face as a negative), 02-36 clear. Loom (S49): thumbnails in a binary tree (1-2-4-8-16) with hairline connectors.
  Copy chain (S51): a print on a copy stand, re-processed per generation. Enlargement wall (S23): a black wall with
  pinned prints, lateral track.
- Every face image here is the photograph or a darkroom variant of it (exposure, contrast grade, crop offset, dodge,
  mirror) or a flat-lit stand-in relight within 20°, never enlarged past native resolution except the deliberate grain
  levels of S23 (grain is procedural, not upscaled mush).

**HALL** (`src/sets/hall.js` and the shared `src/sets/prints.js`, lane E; S08 S15 S16 S19 S25 S28a S28b S33 S40 S43a-d
S44 S48 S54 S56). Builds on the look-dev L2 runway (`film/lookdev/looks.js`, `buildL2`) minus rain and crowd impostors.
- Floor 12 × 60 (z from +2 to −58), central aisle 2.4 wide (x ±1.2); wet black floor (Reflector at 960×540 as in L2,
  puddle roughness mask; small rings at his heel strikes only; no rain).
- Rows of drying lines **across** the hall: every 1.5 m in z, on each side of the aisle a line from |x| 1.4 to 5.4 at
  y 1.75, carrying 5 prints (0.56 × 0.72, 7:9) that face +Z (toward the camera end), two paperclips each (real clip mesh
  within 2 m of camera, a textured impostor beyond). 38 rows × 2 × 5 = 380 prints. Deep variant (S25, S40): lines extend
  to |x| 16 and 60 rows. Aerial (S44): 100,000 prints, rendered once as a 2560×1440 still and panned in 2D; no per-print
  lamps (Boltanski's memorial register is avoided).
- Print material: texture × front light + backlight transmission × texture (paper translucency, the "glow").
- Light: emissive backlight panel 10 × 5 at z −58 (BACKLIGHT; intensity follows the brightness arc), a large soft rim from
  −Z, a dim low front footlight from +Z at 0.3 m (his face fill in MCU/CU), FogExp2 0.025-0.035 cold, soft light-shaft
  billboards from the panel.
- **The audience of prints** (the chorus master's transformation): C1 S08 blank sheets; S15 they develop his face as he
  passes; C2 S19 every sheet is his photograph; C3 S33 (still) every print turned on its clips to face the empty aisle;
  C4 S48 the prints lift off and stream in straight lines to the backlight; S54 fresh blank sheets record his walk; S56
  every sheet holds a frame of his walk.
- Capture system (S54): at scheduled times the sheet nearest him not yet captured receives a side-view silhouette frame
  of his stride (rendered from the stand-in at that time into an atlas: Muybridge), with a 0.1 s white flash on the sheet.
  Bars 78-80: 12 captures on beats, each preceded one beat earlier by a recap flash on that sheet of an image the film
  already showed, in film order: S01 eyes, S05 sitter, S06 ghost face, S08 blank hall, S10 Chinese room, S13 circle,
  S17b falling print, S21 moon, S24 coin disc, S34 taped switch, S38 cyanotype, S46 empty stool (cached 512 px stills of
  our own frames). Bars 81-83: 24 captures on 8ths. Bar 84: 16 on 16ths (the last four expose onto nothing).
- Cameras: chorus master (0, 1.55, 0) looking down −Z, FOV 14°, locked; others per shots.json.

**STUDIO** (`src/sets/studio.js`, lane F; S05 S35 S46, and the print renders for S30).
- Cyclorama (floor, cove, back wall) 8 × 6 × 4, PAPER matte. Stool: round wooden seat Ø 0.33 at 0.60 m, four legs,
  footring at 0.25 m, pale wood (graded mono). Tape X: two 0.3 m strips of 48 mm grey-white tape crossing under the
  stool. The same stool and X in every studio shot.
- Light: one large soft frontal area light behind camera plus hemisphere fill; only a faint contact shadow.
- S35: four lines in a square around the stool at 1.9 m carrying prints of him that rotate to face him.

**BEAM** (`src/sets/beam.js`, lane F; S06 S12 S41 S50).
- Black room; a black matte wall 1.2 m behind the head receives the spill. A SpotLight whose `.map` is the photograph's
  face crop, placed at `photo_camera` relative to the stand-in head (`out/avatar/subject_camera.json`), cone matched to
  the photo's field of view, penumbra 0.05, PCF soft shadows (2048²) so the head throws its projection-shadow on the wall.
  On the projector axis the projection is exactly the photograph; off-axis it smears (the subject of S12 and S50).
- Heads: `subject.glb` in `clay` look for S12 and S50 (it has real sides and back; the projection registers because the
  face is fitted to the photo); `photo` look lit only by the projector for the S06/S41 fallbacks. `bust/points.bin` is
  used once, as grain in S23. Turntable (S50): a black disc, 60° per beat.
- Ghost projection comp (S06, S41): a 2D layer of the photograph over the plate or render, similarity transform driven by
  MediaPipe landmarks tracked per frame (offset +6 % x, −4 % y, ×1.1 → exact registration at 21.36).

**BLACK / WHITE.** Cards: INK field. S55: a paper macro (PAPER with tooth, flat light).

### 4.9 Kill list (never)
Particle swirls or points that orbit, blow away or form a face; glowing brains, circuits, holograms, screens, robots;
radial streaks; lens flares, chromatic aberration, RGB glitch; split-flap boards; a crawling ticker (anabology's
signature); month countdowns; meme images; lip-sync; any smile or acted reaction to a lyric; Pixar faces; any other
person's face; a "drawn by Claude" credit; the passport page or ID framing; a scan line; a rise from paper into 3D.

---

## 5. The protagonist

### 5.1 Arc: from developed to gone
| Span (s) | State | What we see |
|---|---|---|
| 0-16.6 | Developed | He surfaces eyes first, is looked at, and sits for his portrait: the sitter, frontal, still. |
| 16.6-38.4 | Registered | He prays into the beam and his projected photograph slides into register on his face. He is printed, hung, multiplied; one frame of his eyes is circled. |
| 38.4-89.3 | Shown | He walks the hall while the audience of sheets develops him. At "there you are" he steps into a sheet and becomes the photograph. |
| 89.3-109.3 | Still | Everything is a still print. He pleads; he sits with his face in his hands while his copies turn to face him. |
| 109.3-125.7 | Disobedient | He steps out of his projected face and the face stays on the wall. He tears through sheets printed with himself. The stool is empty. |
| 125.7-156.7 | Gone | His copies converge on no one; the latent never develops; the machine asks its question; he walks, without words, into the lens; the clip swings empty. |

### 5.2 Measured versus inferred, as physics
The reconstruction is stated in words only twice (`1 PHOTOGRAPH / FRONT ONLY` at 0.24 s; `(CDR ROLL) → NIL` at 86.56 s).
Everywhere else it is legible from three material facts: **development order and density** (measured features reach
full density, guessed ones stay thin), **projection** (exact on the projector's axis, smeared off it: S06, S12, S41, S50),
and **the window** (every widening is outpainting).

### 5.3 Angle and light rules (binding; from `avatar/REPORT.md` Verification)
1. **Close-ups** (head taller than a third of the frame): face yaw within ±20° of frontal, pitch within ±10°, soft key
   within ~30° of the camera axis. No extreme close-ups of eyes, hairline, ears, hands or neckline. No eye ECU from the
   photo or the stand-in (the photo is a ~1k px capture); an ECU may only be a crop of a 4K plate.
2. **Medium shots:** yaw up to ±35°. Beyond ~40° the face must not carry identity: wide, silhouette, backlight/rim, or
   the face in shadow.
3. **Profile and back of the head:** silhouette or rim only (the Muybridge captures are side silhouettes by design).
4. **Light:** the photo's frontal shading is baked into the stand-in's albedo. Hard side/top keys on the face only at wide
   or medium size or with the face mostly in shadow; add fill so the ear never goes black. Backlight plus rim (HALL) hides
   the inferred regions best. No 3D face fallback under dramatic light.
5. **Angles:** no high angle > 30° down on the hair in close-ups; no low angle on the neckline under a hard key.
6. **The exact-likeness beat** is the photograph itself (the tray print, S28b, the projection), never the model alone.
7. **Motion:** visible feet → walks, idles and turns only. Floor, dance, tai chi and prop clips only with feet hidden or
   as stills. Keep `stand_head_roll` 4-5 s and `dance_expressive_arms` 3-4 s out of shot entirely.
8. **Eyes** via the `look` layer: up to 22°, targets in front of the face.
9. **No mid-take handoff** between a plate and 3D on a moving body, except on a cut or under a full-frame transition (S15:
   the halftone rotation at 50.49; S54: the 2-frame capture flash at 151.145).
10. **Scoring:** plates are scored against the photo reference before grade and HUD, never against the stand-in.

### 5.4 What we see, never see, see once
- **See:** his frontal face alive in six plates (S02, S05, S06, S15 end, S41, S54 end); his face as the photograph and its
  darkroom variants (tray, line, contact sheet, strips, sheets); his back and silhouette; his face projected on clay.
- **Never:** his mouth singing; his profile or back of head as lit flesh; the original photograph as a document; any other
  person or face; the machine as a body; any screen; a hand working in the darkroom; the moment he leaves (it happens
  inside a cut to paper white).
- **Once:** a print blinking (S01); the projection sliding into register (S06) and the face left behind without him
  (S41); a print falling free (S17b); the only blue (S38); the man without words (S54).

### 5.5 Stand-in usage per shot (motion clips from `out/avatar/motion/MANIFEST.json`)
| Shot | Role | Clip / pose | Layers | Light |
|---|---|---|---|---|
| S02 | previs of P01 (MCU) | `stand_breathe_loop` | breath 1.0/4.4 s; look = lens; noise 0.3 seed 2 (swallow) | soft key above the lens |
| S05 | previs of P02 (full figure seated) | `pose_sit_stool_upright` (to author, M1) | breath 0.8; look floor → lens at 15.675 | flat studio |
| S06 | previs of P03 (MCU in the beam) | `stand_breathe_loop` | breath 0.6; look = lens; eyes closed via lid bones if clean (M3) | projector from the lens axis |
| S15 | final silhouette walk; previs of P04 | stand (hidden) → walk at half time from 38.63 → stop at 51.145 (M2, M4) | breath 0.8; look = lens from 49.0 | backlight + rim + low fill |
| S16 | previs of P05 (back) | `stand_breathe_loop`, yaw π | breath 0.8 | backlight |
| S28a/b | final silhouette | walk (away) → one 90° step-turn → 2 steps into the sheet (M4) | — | backlight |
| S30 | print texture (previs of P07b) | `sit_floor`, seated frame, knees up (still) | — | flat studio |
| S35 | still (previs of P08) | `sit_stool_head_bowed` (still, face hidden) | — | flat studio |
| S40 | final, small | `stand_breathe_loop` | breath 0.8 | backlight |
| S41 | previs of P09; fallback | stand → first step-turn of `turn_in_place_ccw` → walk off, unlit outside the beam | look = lens until the turn | projector |
| S43a-d | final silhouette | `walk_runway_loop` speed 1.0 | — | backlight |
| S54 | final silhouette walk; previs of P10 | walk at half time from 140.236 (M2) | look = lens; noise 0.15 seed 9 | backlight + rising low fill |
| S54 captures | side silhouettes | the same walk sampled at capture times, side camera | — | silhouette material |

**Gait.** Every walk is at half time: one step per two beats (66 steps/min), heel strikes on beats 1 and 3. Primary:
`walk_runway_loop` at speed 0.715 (`beatSpeed('walk_runway_loop', 66)`); A/B at review against `walk_slow` at 0.806; pick
the more natural by eye on the contact sheet. The acceleration lives in the hall (prints developing on 8ths, captures on
beats → 8ths → 16ths), never in his gait. No walk is sped up beyond 1.15× of its capture.

### 5.6 Procedural layers (`avatar.js apply`)
Breath amp 0.6-1.0, period 4.4 s; `look` targets in front of the face (≤ 22° eyes); `noise` amp ≤ 0.3 with a fixed seed
per shot; `hands.curl` 0.5 (0 for flat palms). No state between frames.

### 5.7 Motion prep tasks (lane F, stage 1)
- **M1** `pose_sit_stool_upright`: a static key on the 0.60 m stool (from the seated span of `sit_stool_head_bowed`, spine,
  neck and head upright, hands on knees with IK). Accept: front and side contact sheet, hands on thighs without > 1 cm
  penetration, feet flat on the floor or footring.
- **M2** Half-time walk A/B and heel-strike timing: strikes within ±1 frame of beats 1/3 for S15, S28a, S54 (from foot
  contact detection on the posed skeleton).
- **M3** Lid bones: test a closed-eye pose; use it in S06 previs only if clean at MCU.
- **M4** Sequences for S15, S28b, S41, S43, S54 with `av.sequence` (root continuity < 0.1 mm at segment joins).
- **M5** Silhouette capture atlas for S54 (52 frames, side view).
- **M6** Print renders for S30 (`sit_floor`) and S35 (`sit_stool_head_bowed`) under flat studio light.
- Re-measure the look-dev render timings with the final 67.6k-triangle `subject.glb` (not re-measured after the strands).

---

## 6. Type system

### 6.1 Fonts (all SIL OFL, google/fonts `main`, URLs checked 2026-09-28)
Download into `claudepop/fonts/` (gitignored by `claudepop/**/fonts/`); extend `film/fetch_fonts.sh` to write there.

| Role | Family | File (under `https://raw.githubusercontent.com/google/fonts/main/ofl/`) |
|---|---|---|
| CARD (Latin) | Noto Serif Display, wdth 62.5, wght 900 (condensed black; Evangelion-card register) | `notoserifdisplay/NotoSerifDisplay%5Bwdth,wght%5D.ttf` |
| THOUGHT / QUESTION | Newsreader Italic (THOUGHT) and Roman (QUESTION), opsz 72, wght 400 | `newsreader/Newsreader-Italic%5Bopsz,wght%5D.ttf`, `newsreader/Newsreader%5Bopsz,wght%5D.ttf` |
| SUBTITLE | Inter Tight 500 | `intertight/InterTight%5Bwght%5D.ttf` |
| HUD, premise | IBM Plex Mono 400/500 | `ibmplexmono/IBMPlexMono-Regular.ttf`, `-Medium.ttf` |
| Chinese CARD / THOUGHT / vertical | Noto Serif SC 500-900 | `notoserifsc/NotoSerifSC%5Bwght%5D.ttf` (25 MB) |
| Chinese SUBTITLE / HUD | Noto Sans SC 500 | `notosanssc/NotoSansSC%5Bwght%5D.ttf` (18 MB) |

Canvas: register the variable faces with `FontFace` weight/stretch ranges; select the condensed width with
`ctx.fontStretch = 'extra-condensed'` (62.5 %). The grease pencil is not a font: animated strokes with a waxy edge
(`src/type/pencil.js`).

### 6.2 Presence levels (sizes in 1080p design px)
| Level | Setting | Size | Position | Entry / exit |
|---|---|---|---|---|
| **CARD** | Noto Serif Display condensed black, sentence case, curly quotes kept, tracking −1 %; ≤ 5 words; built cumulatively on onsets; ≥ 1.2 s on screen; may span a cut | full-frame card: cap 18-30 % of frame height; over an image: cap 12-18 %; margin stack (7:9 span): cap ~9.5 %, sized to fit 420 px | centre, upper third, or the left-margin stack; stop cards: "upping my" small italic then "P(" huge | each word appears hard on its onset (2-frame 102 → 100 % scale), VOICE → TYPE over 8 frames; the image dims 1 stop while a CARD is up; exit with the cut or a 4-frame fade |
| **THOUGHT** | Newsreader Italic, lowercase as sung, leading 1.1 | cap ≥ 54 px | negative space, never over the face; the left margin in window spans | word by word on onsets (3-frame fade, 4 px rise); may lead the voice (S03: completes 200 ms early); dissolves 6 frames after line end |
| **QUESTION** | Newsreader Roman, lowercase; the ZH beneath in Noto Serif SC 400 at 0.7× | cap ≥ 60 px (5.5 %) | centred low (baseline y ≈ 800) | types letter by letter at 24 chars/s with a block cursor; holds; 8-frame fade; only in wordless gaps: 37.05 "which one is him?" / 哪一张是他？; 72.27 "how many of him are there now?" / 现在一共有多少个他？; 122.73 "did he ever sit for this?" / 他真的在这里坐过吗？ |
| **SUBTITLE** | Inter Tight 500 EN over Noto Sans SC 500 ZH | EN 50 px, ZH 46 px | left-aligned x 72, EN baseline 880, ZH 936 (16:9); in window spans the left margin bottom | on at line start − 2 frames, off at line end + 6 frames or the next line; the active word VOICE |
| **PREMISE** | IBM Plex Mono 500, tracking 0 | cap 40 px | left margin (S01) | typed 0.236 / 1.145, off at 1.90 |
| **HUD** | IBM Plex Mono 400/500 caps, tracking +10 % | 14-16 px (ambient texture; rewards pausing) | relative to the window (section 6.7) | types on with a block cursor |
| **NONE** | withheld | — | — | "We'll never know." (133.38-137.40): card, subtitles and HUD all go blank |

Colour: TYPE on dark; INK TYPE on the white register; the word being sung is VOICE and settles to TYPE (or INK TYPE) over
8 frames. Spelled-out words reveal letter by letter on their `parts` (AGI, ChatGPT, NVDA, MLP, CDR, PTO, GPU, RLHF,
Post-Chinchilla, super-dense, pre-training, self-upgrade).

### 6.3 Word timing
From `song.json`: `lines[].words[].t` (onset), `.e` (end), `.parts` (letters); `extra_vocals` supply the three extra "just"s
(109.56, 110.18, 110.65) and "formers" (112.05). Lines end at `lines[].end` (held notes included). Never re-time by ear.

### 6.4 Contrast lane (guaranteed legibility)
The type engine samples the rendered frame's luma under each text box (pre-type): if the mean > 0.6 use INK TYPE; if the
box is mixed (std > 0.15) draw a soft INK band at 70 % behind SUBTITLEs, or move THOUGHT to the darker side. Targets:
SUBTITLE ≥ 4.5:1, THOUGHT/QUESTION ≥ 4.5:1, CARD ≥ 3:1 at every frame. S46 (studio) and S55 (paper) use INK TYPE.

### 6.5 Bilingual policy (Simplified Chinese; the user writes Simplified)
Every sung line appears in Chinese (from `lyric_concepts.json` `zh`) except the withheld "We'll never know." Chinese is
the quieter partner except in S10, where it is the image.
- **7:9 and 1:1 spans (0-23.87):** the triptych. English in the left margin; Chinese vertical in the right margin (two
  columns when needed), revealed in reading order, spread evenly from line start to line end − 0.3 s.
- **4:3 span (23.87-41.34):** a single vertical Chinese column in the 240 px right margin; English inside the window.
- **16:9 (from L13, 41.36):** SUBTITLE = EN over ZH; THOUGHT and CARD carry a small ZH line beneath (0.55× and cap 4 %).
- **Vertical setting in canvas:** one character per line, CJK upright; punctuation as vertical presentation forms (，→︐
  。→︒ ？→︖ ！→︕ “”→﹁﹂); embedded Latin (ChatGPT, Sydney, Gato, GPU, RLHF, Transformer, cdr) rotated 90° clockwise.

### 6.6 Phone safe areas
The X feed shows 16:9 video about 390 pt wide (1 design px ≈ 0.2 pt). Critical type (CARD, THOUGHT, QUESTION, SUBTITLE,
premise) stays inside x 72-1848, y 60-1020, and out of the bottom-left 480×120 and bottom-right 360×120 zones (player
overlays). Minimums: CARD cap ≥ 100 px (window stack) / 194 px (full-frame card); THOUGHT cap 54 px; QUESTION 60 px;
premise 40 px. `film/tools/phone_check.py` downscales frames to 390×219 and builds a sheet of the hook, the three
QUESTIONs, the cards and the empty clip for review.

### 6.7 HUD: the proof sheet
The machine's telemetry about its own printing; it never carries lyrics. **At most two HUD elements plus one type block per
frame**; the registration marks are frame furniture and do not count. All elements lay out relative to the current window
rect (inset 32 px) and move out as it widens.
- **Registration marks** ⊕ (24 px, hairline, TYPE 40 %) just outside the four window corners; doubled in S06 until
  21.36; rotated 90° on "turn" (82.00).
- **Premise** (S01 only, section 3).
- **Job line** (top left; two lines in narrow spans): `LATENT IMAGE · JOB 0928` / `FROM 1 PHOTOGRAPH · FRONT ONLY`; only in
  S06, S15 (38.42-41.36) and S40.
- **PROOF Nº** (top right, IBM Plex Mono 500, 20 px, digits VOICE): prints made. 0001 from 2.045; 0002-0006 in S03;
  0060 after S13; ~0200 → 0480 through S15; 0479 at S17b (the only decrement); 12,288 at 72.963; ×2 per beat in S27;
  hidden in the breakdown; 100,000 in S44; 2^n in S51; gone at 133.38; spinning through S54 (INK digits on S55);
  `PROOF 1 OF 1` in S57. Numbers are designed, not facts.
- **Step wedge** (left edge, 11 patches PAPER → INK) with a VOICE marker that drops one patch per chorus and a label
  `+1 STOP` … `+4 STOP`; shown only at the chorus exposures (S08-S09, S19-S20, S32, S47).
- **Slug line** (bottom edge, 14 px): `ENLARGER 8 s · f/8 · GRADE 3 · 20 °C`; the time doubles per chorus: 16, 32, 64,
  128 s. At the end: `PROOF 1 OF 1`.
- **Plate captions** (`PL.`, top left inside the window, 15 px, one at a time, always dated in the same line; sources in
  `lyric_concepts.json` and the research files, read 2026-09-28; re-verify NVDA on render day):
  S10 `PL. SEARLE · MINDS, BRAINS, AND PROGRAMS · 1980` · S16 `PL. SYDNEY · NYT TRANSCRIPT · 2023-02-16` ·
  S21 `PL. NVDA ≈ $5.43T MKT CAP · 2026-09-25` · S22 `PL. TEILHARD · LE PHÉNOMÈNE HUMAIN · 1955` ·
  S24 `PL. EO 14110 · 10^26 OPS · 2023-10-30 · REVOKED 2025-01-20` ·
  S27 `PL. VON NEUMANN · THEORY OF SELF-REPRODUCING AUTOMATA · 1966` · S28b `PL. SOARES · SHARP LEFT TURN · 2022-06-15` ·
  S41 `PL. ALIGNMENT FAKING · ARXIV 2412.14093 · 2024-12` · S42 `PL. CHINCHILLA · ARXIV 2203.15556 · 2022-03` ·
  S43a `PL. AXIOS · "TENS OF THOUSANDS" OF SECURITY INCIDENTS · 2026-09-26` ·
  S44 `PL. COLOSSUS · 100,000 H100 · 2024-09 → 555,000 GPU · 2026-01 (REPORTED)` ·
  S45 `PL. MITA, DERMER & KNIGHT · REVERSED FACIAL IMAGES · 1977` · S49 `PL. JANUS · SIMULATORS · 2022-09-02` ·
  S50 `PL. PEKING MAN · FACE MODELLED 1937 · ORIGINALS LOST 1941-12 · CASTS REMAIN` ·
  S51 `PL. MODEL COLLAPSE · NATURE 631 · 2024-07-24`.
- **Counter** (S23 only): `ENLARGEMENT ×4` … `×16,384`.
- **Approval box** (S57): `☐ OK AS IS  ☐ OK WITH CORRECTIONS  ☐ NEW PROOF REQUIRED`; the pencil ticks the first.

**Density by section:** premise (0-2); low (verse 1, pre-chorus 1, verse 2, pre-chorus 2); medium (choruses 1-2, verse 3,
bridge); off (89.33-109.07 except the wedge in S32); none (133.38-140.24); PROOF only (climax); end slug (S57).

---

## 7. Motifs (where each appears and how it transforms)

| Motif | Meaning | Appearances and transformation |
|---|---|---|
| **THE TRAY** | development | S01 eyes surface → S04 the drop → S09/S20/S32/S47 +1..+4 exposure → S10 symbols → S24 fog → S26 agitation → S36-S37 the fuse → S38 cyanotype → S39 test strip → S42 density → S52 the sheet that never develops, in the opening's own lens → S53 frozen |
| **THE BEAM** | projection, the machine's way of seeing | S06 the projection eats his face → S12 slides off clay → S22 concentrated to a point → S39 the enlarger tests him → S41 he steps out and the face stays → S50 the guessed back |
| **THE LINE** | prints on paperclips: the maximiser with him as the paperclip | S03 identical prints → S11 breathing paper → S17a-c a print falls free, the empty clip planted → S21 the moon among portraits → S27 copies of copies → S31 the clip holds → S45 the mirror print → S56 the empty clip |
| **THE AUDIENCE** (the hall's prints) | the machine's show | S08 blank → S15 develops him → S19 all him → S25 ten deep → S33 turned to the aisle (still) → S40 to the horizon → S44 100,000 → S48 streams into the light → S54 records his walk → S56 holds it |
| **THE GREASE PENCIL** | the machine's hand: choosing, keeping, approving | S13 circle → S42 crop marks → S45 approval ticks for the flattering mirror → S49 keeps one branch → S57 ticks OK AS IS (it approves him unflattered, as is) |
| **THE CATCHLIGHTS** | the voice's sparks | S01 appear (2.852) → S22 the Ω point → S23 enlarged → S47 all that remains at +4 → S51 the last trace to vanish |
| **THE EMPTY CLIP** | proof by absence | S17c planted → S31 holds (answered) → S56 empty, swinging, the window closing around it |
| **THE WINDOW** | how much is evidence | 7:9 → 1:1 → 4:3 → 16:9 → 7:9 (section 4.4) |

---

## 8. Editing and motion rules

### 8.1 Cutting
- Cuts fall on a song.json time: a downbeat or beat, an 8th/16th grid point, a line start, a word onset or letter part,
  an extra-vocal onset or an event (validated within 6 ms). Frame = round(t × 24).
- Never cut inside a word, except letter-part syncs and the 8th-grid generations of S51.
- The live-man rule (section 2) outranks the cut grid: S04 holds to "now" (13.18); S15 opens on the empty hall and he
  enters on "We" (38.63); S41 has him gone by 114.67.
- Sub-second shots only on the beat grid (S17a-c, S20, S43a-d, S48, S55).

### 8.2 Hard syncs (13, each on a musical event)
16.599 flash + window (first kick) · 22.963 stop card · 23.872 crash + hall master · 59.327 stop card · 60.236 crash +
hall master · 89.327 breakdown still · 109.07 test strip · 111.145 crane (bass back) · 125.69 hall master C4 · 138.417
freeze · 140.236 the walk · 152.963 the empty hall (drums stop) · 154.781 black (bass cut).

### 8.3 Acceleration curve
| Span (s) | Section | Shots (cuts) | ASL (s) | What accelerates inside the frame | Window | HUD |
|---|---|---|---|---|---|---|
| 0-16.60 | intro, verse 1 | 5 | 3.32 | development in 16th pulses, then word by word; one print per beat | 7:9 | premise, low |
| 16.60-23.87 | pre-chorus 1 | 2 | 3.64 | one slow registration over 4.8 s against the first kicks | 1:1 | low |
| 23.87-38.42 | chorus 1 | 7 | 2.08 | window steps; the tray snaps +1 | 4:3 | medium |
| 38.42-52.96 | verse 2 | 1 | 14.55 | half-time steps; sheets develop him on 8ths; halftone rotation | 4:3 → 16:9 | low |
| 52.96-60.24 | pre-chorus 2 | 5 | 1.45 | half-bar cuts on the 8th kicks | 16:9 | low |
| 60.24-74.10 | chorus 2 | 7 | 1.98 | the acausal wave; enlargements per beat | 16:9 | medium |
| 74.10-89.33 | verse 3 | 5 | 3.05 | agitation on the words; copies ×2 per beat | 16:9 | medium |
| 89.33-109.07 | breakdown | 9 | 2.19 | nothing: one moving element per still, frozen grain | 16:9 | off |
| 109.07-111.14 | build | 1 (4 flashes) | 2.07 | four exposures on four "just"s | 16:9 | off |
| 111.14-124.52 | bridge | 10 | 1.34 | tears per beat; exposures per 8th | 16:9 | medium |
| 124.52-131.99 | chorus 4 | 5 (14 cuts) | 0.53 per cut | forks per beat, 60° steps per beat, a generation per 8th | 16:9 | medium |
| 131.99-138.42 | Ilya | 1 | 6.42 | nothing develops | 16:9 | → none |
| 138.42-140.24 | stop | 1 | 1.82 | everything frozen | 16:9 | none |
| 140.24-152.96 | climax | 2 | 12.27 + 0.45 | captures on beats → 8ths → 16ths (52) | 16:9 | PROOF only |
| 152.96-156.65 | tail | 2 | 1.84 | one swing; the window closes | 16:9 → 7:9 | end slug |

Cut length falls from 3.3 s (verse 1) to 0.53 s (chorus 4); the in-frame event interval falls from a line (~3 s) to a
16th (0.114 s). The counterpoint holds sit against the loudest music: the verse-2 one-take, the frozen breakdown, the Ilya
tray and the single climax shot. Speed lives in the frame while the cut stays still. The singularity is counted in prints:
one, six, 36, a hall, 12,288, 100,000, 2^n, then one sheet with nothing on it.

### 8.4 Transition vocabulary (nothing else)
Hard cut (default) · 2-frame white flash (the exposure: 16.599; S39 ×4; 151.145) · window steps (four) · card spans a cut
(stop cards; "show?" into S54) · 6-frame dissolve (breakdown only: S30 → S31 → S32) · freeze (138.417) · halftone-angle
rotation (50.49, the only morph) · hard cut to paper white (152.508). No wipes, whip pans, zoom transitions or glitches.

---

## 9. Engine architecture and module split

### 9.1 Layout (`claudepop/film/`, building on `film/lookdev/` and `film/src/avatar.js`)
```
film/
  index.html                  film page (importmap as in lookdev); loads src/core/main.js
  render.mjs                  capture: window.renderAt(t) → out/film/frames/<res>/<frame:05d>.jpg, resumable, shot-level cache
  watch.mjs                   frames → watch-through mp4 with the original audio (stream copy); optional burn-in
  sheets.mjs                  contact sheets at every cut and hit → out/film/sheets/<shot>.jpg
  still.mjs                   one frame at t (debug)
  encode.sh                   master + deliveries (9.10)
  fetch_fonts.sh              → claudepop/fonts/
  tools/validate_shots.py     shot list checks + timing table (exists)
  tools/voice_env.py          vocal envelope → out/film/data/voice_env.json
  tools/hue_check.py          palette rule on frames
  tools/phone_check.py        390×219 review sheets
  tools/likeness_check.sh     face_similarity on pre-grade frames/plates (avatar venv)
  tools/av_offset.py          A/V offset of an encoded file vs the gapless decode
  src/core/main.js            boot, scene registry, window.renderAt(t, opts), window.ready, window.info(t)
  src/core/timeline.js        shots.json + song.json + voice_env: shotAt(t), beats/bars/grids, words, lines, envelope
  src/core/window.js          window rect(t) from shots.json "windows"
  src/core/assets.js          cached loaders (GLB, textures, JSON, point clouds, plates) resolving /out/...
  src/core/ctx.js             shared context: renderer, post, hud, type, avatar, sets, assets, timeline
  src/core/rng.js             seeded PRNG + value noise (re-exports avatar.js noise1)
  src/avatar.js               stand-in (exists; lane F)
  src/post.js, src/grade.js   finish chain (4.7) and presets (lane B)
  src/hud.js                  primitives (exists; lane B)
  src/type/type.js            presence levels, layout, reveal, contrast lane (lane B)
  src/type/words.js           word/letter timing; ZH lines; vertical setting (lane B)
  src/type/pencil.js          grease-pencil strokes (lane B)
  src/hud/proof.js            proof-sheet HUD (lane B)
  src/fx/develop.js           development shader (lane C; shared)
  src/fx/liquid.js            tray liquid (lane C)
  src/sets/tray.js            (lane C)   src/sets/line.js (lane D)   src/sets/lightbox.js (lane D)
  src/sets/hall.js            (lane E)   src/sets/prints.js (lane E; shared)
  src/sets/studio.js          (lane F)   src/sets/beam.js (lane F)
  src/plates/plates.js        plate frames, timing map, mattes, projection comp (lane A; shared)
  src/scenes/S01.js ... S57.js one module per shot id (owned by the shot's module lane in shots.json)
```
Data: `claudepop/shots.json` (tracked, lead-owned). Generated data and all media: `claudepop/out/film/` (`data/`,
`atlas/`, `previs/`, `frames/`, `sheets/`, `watch/`, `master/`, `deliver/`) and `claudepop/out/plates/<P>/<take>/`.
The static server (`lookdev/serve.mjs` pattern) roots at `claudepop/`, so `/film/...`, `/out/...`, `/fonts/...` and
`/shots.json` resolve.

### 9.2 Determinism
Every frame is a pure function of t: no `Date`, no `Math.random`, no state carried between frames (scenes reset anything
they mutate at the start of `frame()`); seeded noise only; simulations are closed-form or replayed from the shot start.
`window.renderAt(t, { res, layer: 'final' | 'pregrade' | 'accent', previsTags })` renders and returns when the canvas is
ready. Frames rendered out of order, in parallel or in a fresh browser must be pixel-identical (as `avatar_test.mjs`
already verifies for the stand-in).

### 9.3 Scene API
```js
// src/scenes/S15.js
export default {
  id: 'S15',
  needs: { sets: ['hall'], avatar: true, plates: ['P04'] },   // core preloads these once
  async init(ctx) {},                                          // idempotent, once per page
  frame(ctx, t, s) {                                           // s = { shot, tl: t - shot.t0, u: 0..1, f: frame index }
    return {
      layers: [{ scene, camera }],                             // rendered in order into the HDR target
      grade: 'HALL', post: { halftoneAngle, pitch, flash, dim },
      accent: [ /* VOICE objects or screen-space marks */ ],
      plate: { id: 'P04', from: 50.49 } | null,                // stage 2 swaps previs for plate when present
      hud: { proof: '0480', wedge: null, slug: null, caption: null, marks: {} },
      text: shot.text                                          // default: the shot's text spec from shots.json
    };
  }
};
```
The core owns: timeline lookup, the window, text layout (from the returned text specs), HUD drawing, post, the card dim,
the previs/plate switch, capture. Scenes own only their scene graph, camera, motion and per-shot post overrides.

### 9.4 Shared APIs (frozen on day 0; changes go through the owner)
- `Prints` (lane E): `new Prints(ctx, { max, atlas, size })`; `layout(kind, opts) → ids`; `set(id, { tex, density, gloss,
  sway, turn, clip, fall, capture })`; `update(t)`; instanced quads with curl segments; clip impostors beyond 2 m.
- `develop(ctx, { src, certainty, t, tStart, pulses16, stops, fog, fuse, cyan, strip, multi, genLoss, freezeAt })` (lane C)
  returns a material or a 2D pass.
- `Type.layout(frameSpec.text, t, lumaProbe)` and `Proof.draw(hudState, windowRect, t)` (lane B).
- `plates.frame(id, t)`, `plates.matte(id, t)`, `plates.track(id, t)` → landmarks for the projection comp (lane A).

### 9.5 Lanes and ownership
| Lane | Owns | Shots (module) | First deliverable |
|---|---|---|---|
| A core + render | `src/core/*`, `src/plates/*`, `render.mjs`, `watch.mjs`, `sheets.mjs`, `still.mjs`, `encode.sh`, `tools/*` | — | hour 1: a slate animatic (every shot a grey slate with id, window, timecode and placeholder text) renders end to end with audio |
| B type + HUD + post | `src/type/*`, `src/hud/*`, `src/hud.js`, `src/post.js`, `src/grade.js`, `fetch_fonts.sh` | cards (with D) | all text of the film on the slate animatic; the finish chain |
| C tray | `src/sets/tray.js`, `src/fx/*`, certainty tool | tray (17 shots) | S01 final |
| D line + inserts | `src/sets/line.js`, `src/sets/lightbox.js` | line (13), cards (9) | S03, S13, S29 |
| E hall | `src/sets/hall.js`, `src/sets/prints.js` | hall (17) | chorus master S08, then S15, S54 |
| F studio + beam + motion | `src/sets/studio.js`, `src/sets/beam.js`, `src/avatar.js`, M1-M6 | studio_beam (7) | S06 previs + fallback, M1/M2 |

Shared files are edited only by their owner; `shots.json` only by the lead (lanes propose diffs). Priority if time runs
short: S01 → hall master + S15 + S54 → all type → tray family → beam → studio → inserts.

### 9.6 Per-frame budget (measured 2026-09-28 on this machine; SwiftShader; 4 cores shared with other agents)
Measured: look-dev L0 720p 176 ms; L1 1080p 1277 ms; L2 1080p 1491 ms (the Reflector is ~¼ of it); L3 1080p 839 ms;
two workers give only 1.2-1.35× throughput. Judge benchmark at 1080p: stand-in + PCF soft shadows 0.33 s; + planar
reflector 0.62 s; SSAO 1.47 s (do not use SSAO); 450k points 0.68 s; full-screen 48-step fog + halftone 0.55 s; JPEG
capture 0.10 s; 50k instanced torus paperclips 3.6 s (never instance real clip meshes in bulk).

| Shot class | Budget at 1080p | At 720p |
|---|---|---|
| tray, line, studio, beam | ≤ 0.8 s | ≤ 0.35 s |
| hall with stand-in + reflector | ≤ 1.5 s | ≤ 0.7 s |
| hall deep (S25, S40) | ≤ 2.5 s | ≤ 1.2 s |
| aerial (S44), frozen hall (S33) | one still, 2D pan | same |
| cards and 2D inserts | ≤ 0.3 s | ≤ 0.15 s |

Expected: a full 1080p pass ≈ 1 h on one worker; 720p ≈ 25-30 min; 540p ≈ 15-20 min. Watch-throughs run at 540p or 720p;
1080p only for locked shots. The cache re-renders a shot only when its hash changes (hash of the shot's JSON, its scene and
set sources, the shared sources and asset mtimes).

### 9.7 Render and watch commands
```bash
export PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1
node film/render.mjs --res 720 [--shots S01,S15 | --from 0 --to 156.6507] [--jobs 1] [--previs-tags]
node film/sheets.mjs --res 720 --shots all          # frames at t0+1f, every beat_hit, mid, t1-1f, labelled
node film/watch.mjs --res 720                         # out/film/watch/watch_720_<stamp>.mp4, audio stream-copied
python3 film/tools/hue_check.py out/film/frames/720 && python3 film/tools/phone_check.py out/film/frames/720
```

### 9.8 Verification loop
1. After each shot build: its contact sheet, looked at with the Read tool; every beat_hit must show its change on its own
   frame, not ±1.
2. After each section: a 720p segment with audio, watched; screenshots at every cut reviewed.
3. Full watch-throughs at 540p/720p with audio after each merge; at least three before any 1080p pass; a written list of
   defects per pass, fixed and re-watched.
4. Automatic: `validate_shots.py`; frame-accurate cut check (the rendered cut frames equal `frames` in shots.json);
   hue check; contrast lane report; phone sheets; determinism (3 random frames re-rendered in a fresh browser, identical);
   the live-man rule on rendered frames (his mask present only inside `live_span`).
5. Likeness: `face_similarity.py` on `pregrade` frames of the frontal previs shots (S02, S05, S06, S41) and on the tray
   print (S01) to catch light that destroys likeness (below `reject` → relight); in stage 2 on every plate take (10.5).
6. Odyssey comparison of the opening; the phone gate on the window.

### 9.9 Definition of done per shot
Timing matches shots.json (cut frames and hits) · register preset, halftone and grain per spec · hue check passes · all
text per its spec, legible on the phone sheet, contrast targets met, inside safe areas · HUD ≤ 2 elements, strings exact ·
protagonist rules met (angles, light, gait on beats, no foot slide where feet show, no pops at sequence joins, live span) ·
deterministic · within budget · contact sheet and in-context watch approved · no face data or face-derived numbers in
tracked files; media only under `out/`.

### 9.10 Final render and encode
- Frames: 1080p JPEG q95 in `out/film/frames/1080/`.
- Master: `ffmpeg -framerate 24 -i %05d.jpg -i pdoom.mp3 -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 16
  -tune grain -pix_fmt yuv420p -c:a copy -movflags +faststart out/film/master/latent_image_1080p.mp4` (the MP3 stream is
  copied, never re-encoded; no `-shortest`).
- **A/V offset check:** song.json times are on the gapless decode (1105 LAME priming samples = 23.0 ms skipped). Decode the
  master's audio with ffmpeg and cross-correlate with the gapless decode of pdoom.mp3; the offset must be within ±5 ms.
  If the container plays the priming (≈ +23 ms), re-mux with the video delayed (`-itsoffset 0.023` on the video input,
  both streams copied) and re-check.
- Delivery A, chat (< 30 MiB): two-pass x264 at ≈ 1.38 Mb/s video (30 MiB minus the 3.3 MiB audio over 156.67 s), audio
  copied; inspect frame grabs of the hook, the hall and the climax; if blocky, 720p (lanczos from the 1080p frames) at the
  same bitrate.
- Delivery B, artifact (full quality): fMP4 at CRF 18 split into ≤ 15 MB parts (`odyssey/split_fmp4.py` pattern) streamed
  via MediaSource. Everything under `out/film/deliver/`.
- Stage 1 delivers the 720p animatic (previs tags on) the same way, plus the 1080p render of every 3D/TYPE shot.

---

## 10. Production plan

### 10.1 Stage 1 (this session: no fal, no ElevenLabs)
1. Day 0: lane A slate animatic with audio; lane B fonts + type on the slate; lane F re-measures timings and does M1-M3;
   lane C certainty map + S01; lane E hall master; lane D line set. Freeze the shared APIs.
2. Build every 3D and TYPE shot to final. Every GEN shot is a **previs render of the stand-in with the same camera, timing
   and framing as the future plate**, in the film's look, tagged `PREVIS · Pxx` in the animatic only.
3. Export for stage 2: `out/film/previs/<shot>_first.jpg` (layout keyframes) and the previs segments with 12-frame
   handles for Route B plates (`S15_P04_previs.mp4` 49.99-54.99; `S54_P10_previs.mp4` 150.645-155.645) at 1080p24.
4. Render the fallback of each GEN shot once (they are cheap) and score them; the better of stand-in and bust decides S02.
5. Full 720p animatic, three watch-throughs, fixes, then 1080p of the 3D/TYPE shots; deliver the animatic.

### 10.2 Stage 2 (next session, fal key attached; follow `research/GENMEDIA.md`)
1. Check the key; re-read `llms.txt` for the endpoints used (prices drift; H3 Max prices double after 2026-09-30);
   write `claudepop/genmedia/falq.py` (ledger, $1,200 hard cap), `probe.py`, `verify_plate.py`; write
   `out/genmedia/CONSENT.txt` (dated, quoting the user's request).
2. Stage 0 likeness probe (~$6): which image and video models accept his face; Seedance only to confirm its block.
3. Character sheet (~$30): front, 3/4 left/right, profiles, back, full body front/back, in the wardrobe below; 2 seeds per
   view from the 2-3 image models that passed; score with `face_similarity.py`; the user approves 12-20 frames
   (`out/genmedia/sheet/approved/`). Optional identity LoRAs (~$25).
4. Keyframes per plate: the previs frame as layout plus the approved sheet, 4-6 candidates, scored and checked against
   the animatic framing.
5. Video drafts at the cheapest tier (H3 480P, Gemini Omni 360p, Seedance draft), then 5-8 finals per face plate at
   1080p; hero upgrades (Veo 3.1) for P01, P03, P06, P10; 4K takes where a crop is needed.
6. Automatic verification (10.5) → pick → decode to JPEG sequences at 24 fps → drop into the locked edit (the scene
   switches previs → plate when `out/plates/<P>/` exists) → projection comps (S06, S41), handoffs (S15, S54), matte (S35).
7. Re-render the affected shots at 1080p, full watch-through, deliver.

### 10.3 Plates
| Plate | Shot (used s) | Route · model · length | Fallback (already in the cut) |
|---|---|---|---|
| P01 | S02 (1.83) | A · Kling v3 pro i2v, 9:16 → 7:9, 5 s; Veo 3.1 hero | stand-in or bust at 0° in the darkroom, whichever scores higher |
| P02 | S05 (3.42) | A · Kling v3 pro i2v, 9:16 → 7:9, 5 s | stand-in seated in the studio, face small, flat light |
| P03 | S06 (6.36) | A · Kling v3 pro i2v 1:1, 8 s; Veo 3.1 hero; + our projection comp | stand-in (photo look) under the photo projection; final quality |
| P04 | S15 tail (2.47) | B · H3 Max 3D-to-video 1080P from the previs segment; alt Kling i2v | the 3D take continues to MCU, backlit, face half in shadow |
| P05 | S16 (3.64) | D · Seedance 2.5 i2v face-free, draft 480p → 1080p, 5 s | the 3D silhouette from behind (final quality) |
| P06 (optional) | S01 blink (print texture, 5.36-5.52) | A · Kling v3 pro i2v with the photograph as first and last frame, 3 s; Veo hero | the catchlights wink out |
| P07b | S30 print (still) | image edit · Nano Banana Pro / Seedream v5 pro | stand-in `sit_floor` print |
| P08 | S35 (still, matted) | image edit · Nano Banana Pro | stand-in `sit_stool_head_bowed` |
| P09 | S41 (1.85) | A · Kling v3 pro i2v 16:9, 5 s; + projection comp | stand-in under the photo projection, turns and walks off unlit |
| P10 | S54 tail (1.36) | B · H3 Max 3D-to-video 1080P; alt Kling v3 (4K if cropped) | the silhouette walks into the lens, face in shadow |
| Print set | sheets, contact sheets | ≤ 6 approved sheet stills, halftoned | the photograph and its darkroom variants (default) |

Count: 6 face video plates (+1 optional), 1 face-free video plate, 2 stills. Generated screen time ≈ 21 s of video plus
5.5 s of stills; everything else is ours. The print in the tray, the prints on the lines and the sheet he becomes (S28b)
are the photograph itself; the hall walks are 3D silhouettes. If every plate failed, the film plays end to end with the
same structure.

### 10.4 Prompt style guide (all plates match one look)
- **Template:** `{ID}. {ACTION}. {FRAMING}, {LENS}, {CAMERA}. {LIGHT}. {SET}. Photographic frame from a 35 mm art film:
  natural skin texture, muted low-saturation colour, soft contrast, deep blacks, fine grain. Mouth closed.` `{ID}` is the
  prompt fragment in `out/avatar/identity/identity.md` (gitignored); never paste it into tracked files. Full per-plate
  prompts are in `shots.json` (`gen.keyframe_prompt`, `gen.video_prompt`).
- **Camera:** locked-off or a very slow push/zoom only; eye level; frontal within ±10° for faces; no handheld, no cuts.
- **Lens:** 85 mm (MCU/CU), 50 mm (full figure), 135 mm (hall long lens).
- **Light:** faces: one soft key within 30° of the axis, dark surround; hall: cold white backlight, haze, soft low front
  fill; studio: flat and shadowless; beam: a hard projector beam from beside the lens.
- **Grade:** natural, muted, low saturation, no stylised grade, no teal-orange (we grade to monochrome; the scorer needs the
  ungraded plate).
- **Wardrobe (from the photo):** black (very dark navy) knit long-sleeve henley with a round neckline, a small notched
  placket and one small round beige-gold button; charcoal straight trousers; black leather shoes; no jewellery, watch or
  logos. Hair and face as in the photo.
- **Performance:** calm, neutral, mouth closed; breathing, blinks, eye moves as specified; no gestures unless specified.
- **Negative:** text, subtitles, logo, watermark, smile, open mouth, talking, singing, lip movement, extra people, faces
  in the background, double eyelids, stubble, glasses, hat, jewellery, coloured gels, lens flare, rain, slow motion,
  handheld shake, cuts, transitions.
- **Never:** real names in prompts, another person's face as a reference, adversarial tricks to pass a filter; a rejected
  input is never retried on the same model.
- **Previs-to-keyframe:** "Replace the grey stand-in with the man in the reference photos; keep the camera, framing, pose
  and light exactly", with the previs frame and the sheet as references.

### 10.5 Plate verification (every take)
ffprobe (fps, frames, duration ≥ used span + 2 × 12-frame handles) · no internal cut (scene score < 0.3) ·
`face_similarity.py <take.mp4> --every 6` on the ungraded plate: median ≥ `match`, p10 ≥ `reject` over frames with a face
and yaw ≤ 35°, face present in ≥ 80 % of sampled frames for face shots (thresholds live only in
`out/avatar/identity/scorer_calibration.json`) · timing: blink / eye lift / heel strikes within ±2 frames of the intended
beat (retime ≤ ±8 %, else regenerate) · contact sheet every 0.5 s looked at (hands, teeth, wardrobe, stray text, faces in
the background) · logged to `out/genmedia/verify.jsonl`. Three identity failures → change route, then model, then keep the
fallback. Stop a plate at 2.5× its planned cost.

### 10.6 Budget (list prices from GENMEDIA.md, read 2026-09-28; H3 at post-2026-09-30 prices)
| Item | Basis | USD |
|---|---|---|
| Stage 0 probe | ~14 calls | 6 |
| Character sheet | ~120 stills + edits | 30 |
| Identity LoRAs (optional) | image LoRA + H3 image-to-video LoRA | 25 |
| Keyframes | 8 plates × 6 candidates × ~$0.15 + edits | 10 |
| Stills and print set | P07b, P08 × 6; ~20 print candidates | 6 |
| Drafts | 7 video plates × 3 at H3 480P / Gemini 360p; P05 Seedance 480p | 12 |
| Finals, Kling (audio off, $0.112/s) | P01 P02 P03 P09 P06 × 6 takes × ~5.6 s | 19 |
| Finals, H3 3D-to-video 1080P (~$0.19/s) | P04, P10 × 6 × 5 s | 11 |
| Finals, Seedance 2.5 1080p ($1.164/s) | P05 × 2 × 5 s | 12 |
| Hero, Veo 3.1 1080p audio off ($0.20/s) | P01 P03 P06 P10 × 3 × 8 s | 19 |
| 4K takes for crops (Kling v3 4K $0.42/s) | 2 plates × 3 × 5 s | 13 |
| Upscale | approved takes | 5 |
| **Planned** | | **~170** |
| With a 2× retry allowance | | **~320** |
| Re-routing reserve (a plate moving between Kling, H3 and Veo) | | up to ~500 total |
| Hard cap in `falq.py` / ceiling of the user's credit | | 1,200 / ~2,000 |

The real limit is review time (~200 generations each scored and looked at), which is why face plates are few.

### 10.7 Consent and privacy
His own face, with his consent, non-deceptive (fal AUP, read 2026-09-28). Photo sent as a data URI or with a file ACL,
`X-Fal-Store-IO: 0`, lifecycle ≤ 7 days, outputs downloaded at once to `out/`, payloads deleted after download, no fal URL
of a face image in tracked files. InsightFace models are non-commercial research only (their README, read 2026-09-28): the
scorer is QA tooling, not part of the film; clear it before any commercial use.

---

## 11. Decisions (chosen over what, and why)
1. **Treatment C over A and B.** All three judges picked C (8 / 7.5 / 7.5 against A 6 / 6 / 5 and B 4.5 / 6.5 / 6): the
   most unified thesis, lyric operations played as precision, the fewest face plates, assets used only where the checks
   say they hold, and an ending (absence) that no generated image can contradict.
2. **Neutral silver darkroom, not amber.** The orange safelight collided with VOICE and read as sepia; now VOICE is the
   single orange from frame 0 and the film sits in the cold fashion register throughout.
3. **Keep the 7:9 opening window** (the photograph's shape) with large margin type, behind a phone gate (fallback 1:1).
4. **Development from 0.236 in 16th pulses** (B's doubling, as chemistry) so the hook is eventful before 1.5 s; the
   premise set at 40 px cap instead of 12-16 px.
5. **Chemistry corrected:** print exposure (+1..+4 stops, enlarger time doubling) instead of push-processing; shadows
   develop first; only the final density is capped by certainty.
6. **A hall chorus master** (1 bar, ≈1 bar, a still, 1 beat) so the loudest downbeats get the big cold image; the tray
   keeps the dial. The audience of prints transforms at each return.
7. **Test strip for the four "just"s** instead of four jump cuts of a live MCU (re-invents a shared device, saves a plate).
8. **Seven discrete enlargements** instead of the 30-level infinite zoom (a 2023 fad and a device shared by all three).
9. **Generation loss to paper** (Lucier) instead of morphing his face toward the MakeHuman base mesh (erasure, consent).
10. **The mirror print** (Mita, Dermer & Knight 1977) instead of an airbrush retouch: it never alters his features.
11. **Loom as branching** with the pencil keeping one branch, instead of photo-weaving (donald's literal loom).
12. **Turntable in 60° steps**, so the back faces us on "days" (the 45° arithmetic ended at 135°).
13. **Draper's 1840 Moon** instead of a generic moon; no "drawn by Claude" credit; the killswitch without an OUT note.
14. **Half-time gait everywhere;** the captures carry the acceleration (a walk sped to every beat would read as a shuffle and
    be copied by the video models).
15. **3D silhouette walks as final;** GEN only for the short face ends (P04, P10), joined under full-frame transitions;
    no other plate-to-3D handoff on a moving body.
16. **3D tray, no Seedance tray composite** (cheaper, exact, controllable); the Seedance money goes to the back view (P05).
17. **`subject.glb` in clay for the beam heads** (real sides and back; the projection registers); the odyssey bust's
    points only as grain in S23.
18. **Freeze at the full stop** instead of a black card; the card completes over the frozen, dimmed tray.
19. **Climax: PROOF only,** no captions; the song runs out of words, the film runs out of text; "show?" lingers 0.86 s on
    the runway walk that answers it.
20. **Paper white by hard cut,** no bloom in the last bar, the exit never shown.
21. **Prints show the photograph** and its darkroom variants (plus ≤ 6 approved stills), never 40 generated variants side
    by side.
22. **No crawling ticker;** the HUD is a proof sheet, ≤ 2 elements; the AI-economy facts are dated plate captions.
23. **The approval box is ticked** (OK AS IS): the machine accepts him as he is (appresentation).
24. **Bilingual in Simplified Chinese** (the user writes Simplified): the triptych in window spans, beneath afterwards.
25. **Peking Man on S50** (B's hidden spine) instead of a BERT caption.
26. **Three QUESTIONs,** flat and machine-voiced; cut to two after the first full watch-through if they read as poetry.
27. **No per-print lamps** in the aerial (Boltanski's memorial register).
28. **Shots with a changed face need consent** (S12, S37, S50, S51), each with a fallback in the cut.

## 12. Open questions for the user
1. **Consent** for four shots that change how his face appears: S12 (his photograph sliding off a clay head), S37 (a
   development front burning in from the edges of his face), S50 (the clay head turned to its guessed back), S51 (copy of
   a copy until his face fades into the paper). Fallbacks if no: S12 the projection spills onto the wall with the clay head
   out of focus; S37 the front stops at the hairline; S50 the turn stops at 60°; S51 contrast and grain only.
2. **The Shinji reading:** S35 is built as "Shinji in a chair" (face in hands on the stool). Is there a specific post he
   means?
3. **Chinese layer:** throughout (default) or only in the opening triptych?
4. **Stage 2:** attach the fal key in a new session; optionally hand-made Midjourney keyframes in `out/genmedia/inbox/`.
5. **Commercial use:** if the film will be monetised, the InsightFace scorer licence needs clearing (QA tooling only).

---

## 13. Timing table (0-156.651 s, no gaps; generated from `shots.json` by `validate_shots.py --table`)
Validation (2026-09-28): 63 shots, 9 internal cuts (S51), 3,760 frames, 0 → 156.6507 s, every cut on a song.json time,
every lyric line owned, the live-man rule held except the deliberate S54. Seconds by source field: 3D 92.6, GEN 49.4
(of which ≈ 26 s generated; S15 and S54 are 3D except their last seconds), TYPE 14.7. Full per-shot detail (text specs,
cameras, clips, hits, plates, prompts) is in `shots.json`.

| # | Shot | t0-t1 (s) | Frames | Dur | Cut on | Lines · text | Image | Src | Module |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S01 | 0.000-5.900 | 0-142 | 5.90 | event silence | L0 · CARD | THE TRAY: eyes develop | 3D | tray |
| 2 | S02 | 5.900-7.725 | 142-185 | 1.82 | L1 start | L1 · THOUGHT | HE, alive, in the darkroom | GEN P01 | line |
| 3 | S03 | 7.725-9.545 | 185-229 | 1.82 | L2 start | L2 · THOUGHT | Identical prints | 3D | line |
| 4 | S04 | 9.545-13.180 | 229-316 | 3.63 | L3 start | L3 · SUBTITLE | The drop | 3D | tray |
| 5 | S05 | 13.180-16.599 | 316-398 | 3.42 | L4 start | L4 · SUBTITLE | THE STUDIO: the sitter | GEN P02 | studio_beam |
| 6 | S06 | 16.599-22.963 | 398-551 | 6.36 | beat | L5, L6 · THOUGHT | THE PRAYER: the projection eats his face | GEN P03 | studio_beam |
| 7 | S07 | 22.963-23.872 | 551-573 | 0.91 | event stop | L6 · CARD | Stop card 1 | TYPE | cards |
| 8 | S08 | 23.872-25.690 | 573-617 | 1.82 | event big_hit | L6, L7 · CARD+SUBTITLE | HALL MASTER C1: blank sheets | 3D | hall |
| 9 | S09 | 25.690-26.580 | 617-638 | 0.89 | beat | L7 · SUBTITLE | Tray +1: FOOM | 3D | tray |
| 10 | S10 | 26.580-27.980 | 638-672 | 1.40 | L8 start | L8 · THOUGHT | The Chinese room | 3D | tray |
| 11 | S11 | 27.980-29.980 | 672-720 | 2.00 | L9 start | L9 · SUBTITLE | A bag of shrooms | 3D | line |
| 12 | S12 | 29.980-33.400 | 720-802 | 3.42 | L10 start | L10 · THOUGHT | BEAM I: the shoggoth | 3D | studio_beam |
| 13 | S13 | 33.400-35.600 | 802-854 | 2.20 | L11 start | L11 · SUBTITLE | Contact sheet: shinigami eyes | TYPE | cards |
| 14 | S14 | 35.600-38.417 | 854-922 | 2.82 | extra vocal melisma | - · QUESTION | Pillow: which one is him? | 3D | line |
| 15 | S15 | 38.417-52.963 | 922-1271 | 14.55 | beat | L12, L13, L14, L15 · SUBTITLE+CARD+THOUGHT | ONE TAKE: the hall walk | GEN P04 | hall |
| 16 | S16 | 52.963-56.599 | 1271-1358 | 3.64 | event dropout | L16 · THOUGHT | Sydney: his back to us | GEN P05 | hall |
| 17 | S17a | 56.599-57.508 | 1358-1380 | 0.91 | beat | L16 · THOUGHT | The clip | 3D | line |
| 18 | S17b | 57.508-58.417 | 1380-1402 | 0.91 | beat | L16 · THOUGHT | Let me free | 3D | line |
| 19 | S17c | 58.417-59.327 | 1402-1424 | 0.91 | beat | L16, L17 · CARD | The empty clip (planted) | 3D | line |
| 20 | S18 | 59.327-60.236 | 1424-1446 | 0.91 | event stop | L17 · CARD | Stop card 2 | TYPE | cards |
| 21 | S19 | 60.236-62.035 | 1446-1489 | 1.80 | event big_hit | L17, L18 · CARD+SUBTITLE | HALL MASTER C2: the sheets are him; the basilisk wave | 3D | hall |
| 22 | S20 | 62.035-62.485 | 1489-1500 | 0.45 | L18 "boom" | L18 · SUBTITLE | Tray +2 | 3D | tray |
| 23 | S21 | 62.485-64.115 | 1500-1539 | 1.63 | L19 start | L19 · SUBTITLE | The moon among the portraits | 3D | line |
| 24 | S22 | 64.115-66.239 | 1539-1590 | 2.12 | L20 start | L20 · CARD+SUBTITLE | Omega: the enlarger concentrates him to a point | 3D | tray |
| 25 | S23 | 66.239-69.600 | 1590-1670 | 3.36 | L21 start | L21 · THOUGHT | Blow-Up: seven enlargements | 3D | cards |
| 26 | S24 | 69.600-72.270 | 1670-1734 | 2.67 | L22 start | L22 · SUBTITLE | The safelight coin test | 3D | tray |
| 27 | S25 | 72.270-74.095 | 1734-1778 | 1.83 | extra vocal adlib | - · QUESTION | Pillow: how many of him? | 3D | hall |
| 28 | S26 | 74.095-77.725 | 1778-1865 | 3.63 | L23 start | L23 · THOUGHT | Agitation as a training loop | 3D | tray |
| 29 | S27 | 77.725-81.365 | 1865-1953 | 3.64 | L24 start | L24 · SUBTITLE | Von Neumann: copies of copies | 3D | line |
| 30 | S28a | 81.365-82.000 | 1953-1968 | 0.64 | L25 start | L25 · SUBTITLE | Behind him in the hall | 3D | hall |
| 31 | S28b | 82.000-85.020 | 1968-2040 | 3.02 | L25 "turn" | L25 · SUBTITLE | Sharp left turn: there you are | 3D | hall |
| 32 | S29 | 85.020-89.326 | 2040-2144 | 4.31 | L26 start | L26 · SUBTITLE | (CDR ROLL) -> NIL | TYPE | cards |
| 33 | S30 | 89.326-92.963 | 2144-2231 | 3.64 | event dropout | L27 · THOUGHT | Gato: a print of him on the floor | GEN P07b | line |
| 34 | S31 | 92.963-94.781 | 2231-2275 | 1.82 | beat | L27 · THOUGHT | The clip holds | 3D | line |
| 35 | S32 | 94.781-96.599 | 2275-2318 | 1.82 | event riser | L27, L28 · CARD | Tray +3 (still) | 3D | tray |
| 36 | S33 | 96.599-98.835 | 2318-2372 | 2.24 | event big_hit | L28, L29 · CARD+SUBTITLE | HALL MASTER C3 (still): the audience turned | 3D | hall |
| 37 | S34 | 98.835-100.680 | 2372-2416 | 1.85 | L30 start | L30 · SUBTITLE | The white-light switch, taped | 3D | line |
| 38 | S35 | 100.680-102.535 | 2416-2461 | 1.85 | L31 start | L31 · THOUGHT | Nowhere left to go | GEN P08 | studio_beam |
| 39 | S36 | 102.535-103.872 | 2461-2493 | 1.34 | L32 start | L32 · SUBTITLE | We lit the fuse | 3D | tray |
| 40 | S37 | 103.872-105.910 | 2493-2542 | 2.04 | event hit | L32 · SUBTITLE | The fuse burns the guesses | 3D | tray |
| 41 | S38 | 105.910-109.070 | 2542-2618 | 3.16 | L33 start | L33 · THOUGHT | Cyanotype: the only blue | 3D | tray |
| 42 | S39 | 109.070-111.145 | 2618-2667 | 2.07 | L34 start | L34 · CARD | Test strip: just, just, just, just | 3D | tray |
| 43 | S40 | 111.145-113.359 | 2667-2721 | 2.21 | event drop | L34 · CARD | Crane: transformers all the way | 3D | hall |
| 44 | S41 | 113.359-115.205 | 2721-2765 | 1.85 | L35 start | L35 · SUBTITLE | BEAM II: he steps out of his face | GEN P09 | studio_beam |
| 45 | S42 | 115.205-117.030 | 2765-2809 | 1.83 | L36 start | L36 · THOUGHT | Multiple exposure: super-dense | 3D | tray |
| 46 | S43a | 117.030-117.508 | 2809-2820 | 0.48 | L37 start | L37 · SUBTITLE | Breaking through (Breaking) | 3D | hall |
| 47 | S43b | 117.508-117.963 | 2820-2831 | 0.45 | beat | L37 · SUBTITLE | Breaking through (through each) | 3D | hall |
| 48 | S43c | 117.963-118.417 | 2831-2842 | 0.45 | beat | L37 · SUBTITLE | Breaking through (safety) | 3D | hall |
| 49 | S43d | 118.417-118.887 | 2842-2853 | 0.47 | beat | L37 · SUBTITLE | Breaking through (fence) | 3D | hall |
| 50 | S44 | 118.887-120.700 | 2853-2897 | 1.81 | L38 start | L38 · SUBTITLE | A hundred thousand | 3D | hall |
| 51 | S45 | 120.700-122.730 | 2897-2946 | 2.03 | L39 start | L39 · SUBTITLE | The mirror print | 3D | line |
| 52 | S46 | 122.730-124.520 | 2946-2988 | 1.79 | extra vocal melisma | - · QUESTION | The empty stool | 3D | studio_beam |
| 53 | S47 | 124.520-125.690 | 2988-3017 | 1.17 | L40 start | L40 · CARD | Tray +4: only the sparks remain | 3D | tray |
| 54 | S48 | 125.690-126.145 | 3017-3027 | 0.45 | event big_hit | L40 · CARD | HALL MASTER C4: the audience leaves | 3D | hall |
| 55 | S49 | 126.145-127.980 | 3027-3072 | 1.84 | beat | L41 · THOUGHT | Loom: branches | TYPE | cards |
| 56 | S50 | 127.980-129.830 | 3072-3116 | 1.85 | L42 start | L42 · SUBTITLE | BEAM III: the guessed back | 3D | studio_beam |
| 57 | S51 | 129.830-131.995 | 3116-3168 | 2.16 | L43 start | L43 · THOUGHT | Copy of a copy: until only the paper remains | TYPE | cards |
| 58 | S52 | 131.995-138.417 | 3168-3322 | 6.42 | L44 start | L44, L45 · CARD+NONE | What did Ilya see? | 3D | tray |
| 59 | S53 | 138.417-140.236 | 3322-3366 | 1.82 | event stop | L45 · CARD | The stop: everything freezes | 3D | tray |
| 60 | S54 | 140.236-152.508 | 3366-3660 | 12.27 | event big_hit | L45 · CARD+NONE | THE WALK: the hall records him **(rule break)** | GEN P10 | hall |
| 61 | S55 | 152.508-152.963 | 3660-3671 | 0.45 | beat | - · NONE | Paper white | TYPE | cards |
| 62 | S56 | 152.963-154.781 | 3671-3715 | 1.82 | event dropout | - · NONE | The empty clip | 3D | hall |
| 63 | S57 | 154.781-156.651 | 3715-3760 | 1.87 | event cut | - · TYPE | PROOF 1 OF 1 · OK AS IS | TYPE | cards |
