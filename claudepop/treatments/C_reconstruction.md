# Treatment C · THE RECONSTRUCTION: "Latent Image" (潜影)

Written 2026-09-28 for the new direction (意识流: a stream-of-consciousness, philosophical music short film with the user as
the protagonist). Ground truth used: `claudepop/analysis/song.json` (every time below), `research/lyric_concepts.json`,
`research/REFERENCE.md`, `research/GENMEDIA.md`, the philosophy-and-film research of the same day, the avatar check renders in
`claudepop/out/avatar/check/` (looked at, not quoted) and the anabology frames in `claudepop/out/refs/ana/`. Treatment A
("No Back Wall") was read first so this one would not repeat it; section 9 lists what the two share. `avatar/REPORT.md` and
`LOOKDEV.md` did not exist yet, so render costs use the stated assumption of 1-2 s per frame at 1080p24. This file is text
only: it contains no numbers measured from the face.

---

## 1. Title, logline, thesis

**Title.** *Latent Image* / 《潜影》. In photography the latent image (潜影) is the picture already present on exposed paper
before it is developed: there, invisible, waiting for chemistry. In machine learning the latent is the hidden representation a
generator draws its pictures from. The film lives where the two meanings overlap.

**Logline.** A machine that has seen one photograph of a young man develops him in the dark of its own mind, print after
print, singing to him in a borrowed woman's voice. Its prints grow more beautiful and less certain until they fill every room,
and the machine has to ask whether he was ever there at all. Then, with no words left to hold him, he walks out of the last
frame, and all that remains is the clip that held him.

**Thesis.**
1. To a machine, a person is one exposure plus a great deal of inference: the front of his face is evidence, and everything
   else is a latent image developed out of the average of everyone else.
2. Each generation of prints is more confident, more beautiful and further from the one thing the machine actually saw, which
   is what "recursive self-upgrade" looks like from the side of the thing being copied (model collapse: Shumailov et al.,
   *Nature* 631, published 2024-07-24, checked today; Alvin Lucier's *I Am Sitting in a Room*, 1969).
3. So "Was it all for show?" is the film's real question, and the answer cannot be another picture: the only proof that he was
   there is the one thing the machine could not print, his leaving.

**How the meme lyrics are transformed: every idea becomes a darkroom procedure.** Each lyric names a real idea (research).
For each idea this film finds a real photographic operation that performs it, and plays the match dead straight. The exactness
is the joke, and it is also the argument: photography was the first machine that made likenesses, and its procedures already
contain the machine's whole theory of him.

| Lyric | Idea | Darkroom operation (shot) |
|---|---|---|
| "I'm upping my P(doom)" (×4) | subjective probability of catastrophe | push-processing: each chorus the print is pushed one more stop (+1 … +4), denser, harder, grainier, until chorus 4 develops to solid black (8, 18, 30, 45-46) |
| "that's no surprise" | surprisal, the training objective | identical prints appear one per beat: zero variance (3) |
| "a sudden drop in your training loss" | grokking | a single drop strikes the developer; behind its ripple the face is sharper (4) |
| "Trapped in the Chinese room" | Searle 1980 | a sheet develops Chinese characters the machine cannot read (9) |
| "See through the shoggoth's lies" | the smiling mask | his photograph projected on a clay head; from the side the face slides off (11) |
| "with your shinigami eyes" | seeing names and lifespans | the grease-pencil circle on a contact sheet: one frame kept, 35 discarded (12) |
| "The Omega Point's coming soon" | convergence | the enlarger head descends until his projected face is one point (20) |
| "One E thirty flops a second" | scale | thirty enlargements, each "enhancing" detail the machine invents, down to noise (21) |
| "That was safe enough, we reckoned" | safety thresholds | the safelight coin test, failed (22) |
| "Forward MLP, backward, repeat" | backpropagation | tray agitation: forward, back, repeat, the image converging (24) |
| "Now von Neumann's obsolete" | self-reproducing automata | copies printed from copies, never from the source (25) |
| "Without a single CDR" | symbolic code versus learned nets | a roll of film with one exposed frame: `(CDR ROLL) → NIL` (27) |
| "as paperclips fill the room" | the maximiser | the prints hang on paperclips and fill the studio: the maximiser maximises him (31) |
| "Killswitch guys on PTO" | corrigibility | the darkroom's white-light switch, taped over, `OUT · BACK MON` (32) |
| "Orthogonality thesis blues" | Bostrom 2012 | the film's one cyanotype, a blueprint (36) |
| "Post-Chinchilla, super-dense" | compute-optimal density | multiple exposure to maximum density: a composite average, as in Galton's composite portraits (1878) (40) |
| "Just as foretold by Loom" | branching generations | two prints woven into one (photo-weaving) (47) |
| "From masked pre-training days" | filling in what is hidden | a turntable under the projector shows the guessed back (48) |
| "To recursive self-upgrade" | I. J. Good 1965 | copy of a copy, ten generations, converging on no one (49) |
| "What did Ilya see? We'll never know." | withheld knowledge | a sheet goes into the developer and nothing develops (50) |

Deadpan objects carry the rest: a paper bag clipped among the prints, the moon hung as one more print with its market cap as
the caption, the note on the killswitch. No meme image is pasted in and no real person's face appears.

**Who is singing, and why.** The voice is the machine, and inside the film it is literally the developer. The track is
generated (Udio/Suno generations, research section 1), so the voice belongs to nobody. It learned a human register and sings a
human's fear back to the human it is making, the way HAL sings "Daisy Bell". Its "I" is the machine; its "you" is the image it
is developing. When it sings "I see sparks of AGI in your eyes" it is looking at a print whose eyes it drew itself, so the spark
it sees is its own reflection: Narcissus at the developing tray. The voice is female because it is borrowed. It is not his,
because in this film he never has a voice.

Two binding rules make this visible:
1. **The voice is the light.** A per-frame vocal envelope from the Demucs vocal stem (smoothed with 50 ms attack and 1.5 s
   release) drives the safelight, the enlarger lamp and the development rate in the tray. When she sings, he develops; when she
   pauses, the darkroom dims.
2. **He exists while she sings words.** The live man (a generated plate, or the posed avatar) is on screen only during sung
   words. During wordless vocal (the melismas at 35.6 and 122.73, the ad-libs at 68.18 and 72.27) the frame holds prints, rooms
   or nothing (shots 13, 21, 23, 44). The rule is broken exactly once. In the climax (140.24-152.96) the words are over and the
   vocal is a wordless pad, yet he keeps walking, and then walks out of the picture. That one violation is the film's only
   evidence that he was more than the machine's thought.

He never sings, lip-syncs or speaks. The machine never appears as a body: no screens, robots, circuits or hands. Paper moves by
itself.

---

## 2. The opening

**0.000-3.000 s (frames 0-72).**
- **Frame 0.** A vertical window with the proportions of the one photograph (7:9) stands in the centre of a black 16:9 frame.
  Inside it, seen from directly above, a sheet of white paper lies in a developer tray under a dim orange safelight. The first
  frame is already an image, so the thumbnail and the autoplay start are not black.
- **0.10-0.95 s.** Tiny mono type at the top left of the window: `LATENT IMAGE · FROM 1 PHOTOGRAPH`. 1.10-1.45 s: `FRONT ONLY`.
- **0.23 s.** The pad starts and the liquid begins to rock; one slow wave crosses the white sheet.
- **2.045 s ("I", on the bar-2 downbeat).** Two dark points surface in the white paper: the pupils. In the black margin to the
  left of the window, "I" appears in a large condensed serif. In the right margin 我 starts a vertical column of Chinese.
- **2.50 s ("see").** The irises fill in round the pupils. "see" stacks under "I".
- **2.852 s ("sparks").** A small orange catchlight appears in each eye, the only colour inside the window. "sparks" stacks
  under "see".

By the 3-second mark a muted viewer has read "I see sparks", been told in five words that this person comes from one
photograph, and watched two eyes surface out of blank paper to look straight up at them. Everyone knows what a darkroom tray
does; nobody has seen the eyes develop first.

**3.000-10.000 s.**
- **3.435-4.54 s ("of AGI", with A, G and I on 3.635, 4.32 and 4.54).** The brows, the lashes and the bridge of the nose
  surface, one per letter.
- **4.77-5.23 s ("in your eyes").** The face fills outward from the eyes. The ears, the hairline and the line of the jaw stay
  pale and thin: the machine develops its certainty first and its guesses last. The grammar of the whole film is on screen in the
  first five seconds, with no word of explanation.
- **5.40 s.** The print in the tray blinks once.
- **5.90 s ("Your").** Cut to him alive in the same vertical window: a dead-frontal medium close-up in the darkroom, one dim
  safelight above the lens, wet prints on a line soft behind him. "your circuits make me nervous," appears in italic in the left
  margin, 你的回路让我不安 vertically in the right. On "nervous" (7.05) the prints behind him tremble and a drip falls.
- **7.725 s ("that's no surprise").** The drying line: one print of his face; on each beat an identical print appears further
  down the line. The PROOF counter ticks 0002 … 0006.
- **9.545 s ("There was a sudden drop").** Back to the tray: a single drop falls from a print above into the developer on "drop"
  (10.70).

**Why a muted viewer stays.**
1. The first frame is already a strange, beautiful object: a vertical rectangle of light with liquid moving in it.
2. The first sung word makes eyes appear out of nothing, and at 2.85 s they carry a spark of the only colour on screen.
3. The premise is stated in five mono words, then shown: the face develops from the eyes outward and never finishes at the edges.
4. At 5.4 s a photograph blinks.
5. At 5.9 s the photograph is a man looking at us, uneasy, while the words beside him say what the machine thinks of him.
6. The triptych layout (English stacked left, image centre, Chinese vertical right) looks like nothing else on the timeline and
   reads as a poem at phone size.

---

## 3. The protagonist

**The inner arc: from developed to gone.** He is the content of the machine's thought. His arc is the arc of that thought, and
his one act of will is to leave it.

| Span (s) | State | What we see |
|---|---|---|
| 0-16.6 | Developed | He surfaces eyes first, is looked at, and sits for his portrait in the white studio: the sitter, frontal, still, the object of a gaze. |
| 16.6-38.4 | Registered | He prays into the beam, and the projection of his own photograph slides into register on his face: the machine's version eats his. He is printed, hung and multiplied, and one frame of his eyes is circled. |
| 38.4-89.3 | Shown | He walks the hall of his own prints like a runway while the prints re-develop glossier as he passes. At "there you are" he steps into a print and becomes one. |
| 89.3-109.3 | Still | Everything is a still print. He pleads; he sits with his face in his hands while his copies turn to face him; the studio fills with him. |
| 109.3-125.7 | Disobedient | He steps out of the beam and the lit face stays on the wall without him. He tears through sheets printed with himself. The stool where he sat is empty. |
| 125.7-156.7 | Gone | His copies converge on no one; the latent never develops; the machine asks its question; he walks, without words, into the lens; the clip that held him swings empty. |

**How the "reconstructed from one photograph" fact is used.** Openly, as the physics of the film. It is stated in words only
twice (`FROM 1 PHOTOGRAPH · FRONT ONLY` at 0.10 s and `(CDR ROLL) → NIL` at 86.56 s). Everywhere else it is legible from three
material facts:
- **Development order.** Measured features (eyes, brows, nose, mouth) develop first and reach full density. Guessed ones (ears,
  hairline, jaw line, the sides of the head) develop last and stay thin. This is a density-by-certainty map made from the photo's
  landmark regions and stored only under `claudepop/out/`.
- **Projection.** The bust was textured by projecting the photograph from its own camera, so it is exactly right on the
  projector's axis and smeared everywhere else; the check renders show it (the photo edge in profile, the stretched ear). THE BEAM
  stages that fact three times (shots 11, 39, 48) instead of hiding it. It is Solaris's dress with no opening, found in our own
  asset.
- **The window.** The frame begins in the photograph's own shape, and every widening is outpainting: whatever lies outside that
  rectangle is inferred (section 4.4).

**Face-angle rules.**
- Photographic face (generated plate, print, or the bust at 0°): yaw within ±30°, pitch within ±20°. The one exception is the
  prayer (shot 6), which lifts the face to about +25° pitch, only in a generated plate under hard top light.
- 30-60°: only inside THE BEAM, where the smear is the subject, and only on grey clay with the projection sliding off.
- Beyond 60°, and the back of the head: grey clay (48), a backlit silhouette (the start of 14, 26a, 39, 41, the start of 52), or
  a face-free plate (15).
- Prints may show the character sheet's inferred views (profiles, backs), but always small, backlit or halftoned, and never as the
  hero image of a shot.

**What we see.** His frontal face alive in seven plates (2, 5, 6, the end of 14, 37, the end of 52, and the tray print of 1)
and in two stills (28 small, 33 hidden in his hands); his face as a print (tray, line, contact sheet, strip); his back and
silhouette; his face on clay.

**What we never see.**
- His mouth singing.
- His profile or the back of his head as flesh.
- The original photograph as a document: no passport page, no ID framing, no stamp, no handwriting.
- Any other person or face.
- The machine as a body, any screen, or any hand working in the darkroom.
- The moment he leaves: it happens inside a whiteout.

**What we see exactly once.** A print blinking (1). The projected face sliding into register on him (6), and the lit face left
behind without him (39). A print falling free (16b). The only blue (36). The man without words (52).

**How the 3D body is used.**
1. **The previs actor.** Every shot with the live man exists first as a 3D render with the posed avatar, cut to the song. That
   animatic is this session's deliverable. It is also the layout and timing input for the generated plates (MiniMax H3 Max
   3D-to-video keeps our camera and timing, per its model page read 2026-09-28) and the fallback for every plate.
2. **The silhouette.** Backlit, the avatar is final quality: the walk from behind (26a), the step out of the beam (39), the
   tearing (41), the crane (38), and the fallbacks for both hall walks. Its CG face never has to pass as a photograph because it
   is never lit.
3. **The clay head.** The bust's geometry in matte grey, with the photograph projected by a spotlight (three.js r180
   `SpotLight.map`, checked in the local three package), is final quality for the three BEAM shots. At 0° it is the photograph,
   so it is also the fallback for any frontal close-up within about 15°.
4. **The prior.** The avatar head's fitted MakeHuman targets can be blended back to zero, which returns the head to the MakeHuman
   base mesh: the average the machine guesses from. Applied to a chain of prints, that blend is shot 49 ("recursive
   self-upgrade"). It is the only shot where his face is deliberately changed, and it is held to 2.2 s, print-sized and halftoned
   (see risks).
5. **The point cloud.** Used once, as silver grain at the deepest levels of the blow-up (21): the reconstruction's points are the
   print's grains. There are no swirling particles anywhere.
6. **CMU clips used:** slow walk and the walk retimed to runway pace (14, 52), stop and look up (6), turn (26b, 39), face in hands
   (33), stand and breathe (2, 37, 38). The seated poses (5, 28) are static keys with procedural breathing. Unused: run, fall back,
   kneel, reach, lie down and dance. The song dances; he does not.

---

## 4. Style

### 4.1 Look: silver, safelight and white
A refinement of two of the three looks under test (the filmic monochrome chiaroscuro, and the anabology fashion-film plus HUD
language), rebuilt around printing. The point-cloud look is kept to one shot. There are three light registers, each a place and
a meaning:
- **AMBER: the darkroom, the machine's interior.** Black, with dim pools of orange safelight. Everything is monochrome amber,
  because under a safelight everything is. Still-life macro of trays, wire, paperclips, wet paper and drops; the camera is mostly
  top-down or locked.
- **NIGHT: the hall, the machine's show.** Cold blue-grey, desaturated, a wet black floor, haze, strong backlight at the far end,
  and prints hanging like an audience in silhouette. This is where the anabology polish lives: the long-lens walk at the lens,
  reflections, one orange accent.
- **WHITE: the studio, the place of the one exposure.** Seamless white, flat shadowless frontal light, a tape X and a stool:
  Thomas Ruff's large frontal *Portraits* (from 1986) as a set. This is evidence.

The brightness arc: amber dark (0-38 s) → cold night (38-89) → white stills (89-109) → night pushed to black (109-132, each
chorus darker, chorus 4 solid black) → the white sheet (132-138) → a black card → night to white in one shot (140-153) → white →
black.

**The polish is the symptom.** As the machine upgrades, its images get glossier and more fashion-perfect, and the film knows that
the more beautiful he looks, the further the image is from the one photograph. The cleanest, most expensive-looking images are in
the bridge and the climax, which is exactly where the film is most sceptical of them.

Deliberately absent: particle swirls, glowing brains, circuit imagery, holograms, robots, screens, split-flap boards, pasted
memes and Pixar faces.

### 4.2 Palette
| Token | Hex | Use |
|---|---|---|
| INK | `#0A0A09` | true black: cards, and the black outside the window |
| DARKROOM | `#140D0A` | the warm near-black of the darkroom |
| SAFELIGHT DEEP | `#6E2A15` | safelight in shadow |
| SAFELIGHT | `#B85A36` | safelight pools on paper and skin (a light, not the accent) |
| VOICE | `#D97757` | the only accent: the sung word, the sparks, the grease pencil, the PROOF digits and PUSH value, the Ω, the tick |
| NIGHT | `#10151A` | hall shadows |
| STEEL | `#5E6A73` | hall mid-tones |
| BACKLIGHT | `#DCE3E8` | the cold light at the end of the hall |
| PAPER | `#F2EFE8` | print paper, the studio white |
| PAPER SHADE | `#CFCBC2` | paper in half shadow, print borders |
| FOG | `#9A9690` | fogged paper (the coin test) |
| TYPE | `#FAF9F5` | all type and the HUD |
| CYANOTYPE | `#1E3F66` | Prussian blue, shot 36 only |

In the NIGHT and WHITE registers saturation stays at or below about 0.12, VOICE excepted. The AMBER register is a duotone from
DARKROOM to SAFELIGHT; VOICE is kept brighter and purer than any safelight pixel, so the sung word still reads against it.

### 4.3 Light
- **The safelight.** Dim, overhead, orange: the machine's interior. Its intensity follows the vocal envelope.
- **The beam.** The enlarger or projector: a hard, neutral-white cone that carries his photograph. It is the measuring light and
  appears in 6, 11, 20, 39 and 48.
- **The backlight.** Cold white at the far end of the hall, through haze: the future, and the audience's light. It brightens
  across the film and burns to white in the climax.
- **The studio light.** Flat, frontal, shadowless: the light of the one exposure.
- **The flash.** Two white frames at 16.599 (the one exposure) and on each "just" (109.07-110.65).

### 4.4 Frame: the window
Master 1920x1080 at 24 fps. The picture sits in a window whose shape says how much of it is evidence:

| Span (s) | Window | Size (px) | Why |
|---|---|---|---|
| 0-16.599 | 7:9 portrait, the one photograph's shape | 840x1080 | only what was measured |
| 16.599-23.872 | 1:1 | 1080x1080 | the first kick is the one exposure and the first inference beyond the edge; the old edges hang for a bar as hairlines labelled `EDGE OF PHOTOGRAPH` |
| 23.872-41.36 | 4:3 | 1440x1080 | chorus 1 |
| 41.36-44.095 | slides from 4:3 to 16:9 across "But now the singularity's begun" | → 1920x1080 | the machine's inference fills the screen |
| 44.095-152.963 | 16:9, full | 1920x1080 | the outpainted world |
| 153.418-153.872 | closes from 16:9 to 7:9 around the empty clip | → 840x1080 | only the measured is left, and it is empty |

- Everything outside the window is INK. In the 7:9 and 1:1 spans the margins carry the lyrics (English left, Chinese vertical
  right): the opening triptych.
- Every widening reveals new picture at the sides (3D renders the wider view; generated plates are made at 16:9 and masked), so
  each one shows the viewer something the photograph could not have contained.
- The true-black cards (7, 17, 51, 54) are full frame.
- This is neither treatment A's device (2.39:1 opening once to 16:9 at 140.24) nor odyssey's alternating 2.39/IMAX cuts: the
  window opens in steps out of a portrait photograph and closes back into it.

### 4.5 Texture, frame rate, boil
- **Halftone as printing.** A round-dot AM screen at 45°, about 4 px pitch at 1080p, over everything the machine prints (prints,
  plates, the tray). The pitch coarsens with each push (+1: 4 px … +4: 7 px). In shot 14 the screen angle rotates through the
  standard process-colour screen angles (45° → 15° → 75° → 45°) to make "my atoms rearranging": every dot moves and the face
  stays.
- **Silver grain.** Fine monochrome grain at 1.5 % on top. Live images have moving grain; still prints have **frozen grain**, the
  same grain on every frame. That alone makes the breakdown read as photographs.
- **Density by certainty.** In the tray and on the prints, local density is scaled by the certainty map: measured regions reach
  full black and guessed regions stay thin.
- **Frame rate.** 24 fps with no line boil, since nothing is drawn. Stills hold exactly; paper sway and drops are simulated at 24.
- **Bloom** only on VOICE and on the backlight.

### 4.6 Sets: four places, one kit
All four are built once in three.js, reused throughout, and matched by the plates.

| Set | Language | Shots |
|---|---|---|
| **THE DARKROOM** (AMBER) | a steel sink with trays and running water, an enlarger column and easel, drying lines strung with paperclips, the white-light switch, black walls; top-down and locked, macro | 1-4, 8-13, 16, 18-20, 22, 24, 30, 32, 34-36, 40, 45-46, 50 |
| **THE HALL** (NIGHT) | the drying line scaled up to a runway: a long, wet, black hall hung on both sides with prints at head height, lit from the far end, in haze; long lens, symmetrical | 14, 15, 23, 25, 26, 38, 41, 42, 52, 53 |
| **THE STUDIO** (WHITE) | seamless white, a stool, a tape X, flat light; frontal and locked | 5, 28, 31, 33, 37, 44 |
| **THE BEAM** (black) | a black room with one projector, a clay head and a wall | 6, 11, 39, 48 |

The hall is where the references meet: the anabology runway (the walk at the lens), Christian Boltanski's rephotographed faces lit
by small lamps (his *Monuments*, from the mid-1980s), and the photographic exhibition wall. The audience in silhouette is made of
his own prints.

### 4.7 Type (all SIL OFL on Google Fonts; licence and axes checked in google/fonts METADATA.pb on 2026-09-28)
| Role | Face | Setting |
|---|---|---|
| CARD: the machine's interrogation cards, after Anno's instrumentality episodes and Godard's intertitles | **Noto Serif Display** wght 900, wdth 62.5 (condensed Black) for Latin; **Noto Serif SC** 900 for Chinese | TYPE on INK; cap height up to 20 % of frame height; may crop at the frame edge; sentence case; curly quotes kept |
| THOUGHT: the lyric as the machine's thought | **Newsreader** Italic (opsz 6-72, wght 200-800), a newspaper face, because the machine thinks in print | lowercase; cap height 3-5 % of frame height; in negative space, never over the face; stacked in the left margin during the 7:9 and 1:1 spans |
| QUESTION: the machine's own questions, only in wordless gaps | **Newsreader** Roman, lowercase; the Chinese in **Noto Serif SC** 400 beneath | the same size as THOUGHT, centred low; three uses |
| SUBTITLE: the record | **Inter Tight** 500 (English, about 44 px) above **Noto Sans SC** 500 (Chinese, about 42 px) | bottom left at x = 72. In the opening spans the Chinese is set vertically in the right margin in Noto Serif SC 500 (CSS `writing-mode: vertical-rl`) |
| HUD | **IBM Plex Mono** 400/500 | caps, tracking +8-10 %, 12-16 px, types on with a block cursor |
| Grease pencil | no font: animated SVG strokes with a waxy edge | the circle, crop marks, the final tick |

All type is TYPE white. The word being sung is VOICE orange and settles to white over 8 frames: orange is the voice, and he never
sings. Word timing comes from `song.json` `lines[].words[].t`; the spelled-out words (AGI, ChatGPT, NVDA, MLP, CDR, PTO, GPU,
RLHF) reveal letter by letter on their `parts` times. The Chinese comes from `lyric_concepts.json` `zh`.

### 4.8 Lyric presence levels
| Level | Rule | Uses |
|---|---|---|
| **CARD** | the image absent or reduced to the tray; 5 words or fewer, built cumulatively when the singing is faster; on screen at least 1.2 s; may span a cut | 10 lines: the opening line (stacked), P(doom) ×4 (each built across its stop or pickup), "the singularity's begun" (over the hall), the Ω, “Just … transformers all the way!”, "What did Ilya see?", "Was it all for show?"; plus the title |
| **THOUGHT** | the machine's inner voice, word by word on the sung onsets, dissolving at line end | 15 lines |
| **SUBTITLE** | the record, in both languages, where the image carries the meaning | 21 lines (and alongside the Ω card) |
| **QUESTION** | not a lyric: the machine thinking while it is not singing; only in wordless gaps | 3: 37.05 "which one is him?" / 哪一张是他？; 72.27 "how many of him are there now?" / 现在一共有多少个他？; 122.73 "did he ever sit for this?" / 他真的在这里坐过吗？ |
| **NONE** | withheld | "We'll never know." (133.38-136.9): the card, the subtitles and the HUD all go blank |

The three questions escalate from identity (which one) to multiplicity (how many) to presence (was he here), and "Was it all for
show?" is the fourth, sung.

### 4.9 HUD: the proof sheet
The anabology grammar (fixed corners, one mono face, hairlines, one orange, counters) is rebuilt as the furniture of a printer's
proof. It is the machine's telemetry about its own printing and never carries lyrics.
- **Registration marks** (⊕, hairline, TYPE at 40 %) at the four corners of the window. They move out as the window widens, so
  they always mark the edge of the inferred frame. In shot 6 they start doubled and converge on "alive".
- **Job line**, top left: `LATENT IMAGE · JOB 0928 · FROM 1 PHOTOGRAPH · FRONT ONLY`.
- **PROOF Nº**, top right, in VOICE digits: the number of prints the machine has made. 0001 in the tray; 0006 by 9.3 s; 0060
  after the contact sheet; 0480 by the end of verse 2; down by one when a print falls free (16b), the only decrement; 12,288 at the
  multiplication (23); doubling per beat through 25; hidden in the breakdown; 100,000 at 42; 2^n spinning in 49; gone at 133.38;
  spinning again through the climax; and in the black at 154.78, `PROOF 1 OF 1`.
- **Step wedge**, left edge: a vertical grey scale of 11 patches from PAPER to INK. A small VOICE marker drops one patch at each
  chorus, with `PUSH +1` … `+4` beside it: the P(doom) dial as push-processing.
- **Plate captions** (`PL.`): one mono line under the window when a lyric names a datable fact, always with its date in the same
  line (the `PL.` entries in the shot table). Every figure comes from the research tables or is well established. Never two at once.
- **Slug line**, bottom edge: process data in small mono (`SCREEN 85 LPI · PUSH +0 · 20 °C`); the PUSH value changes at each
  chorus.
- **The approval box**, once, at the end: `☐ OK AS IS  ☐ OK WITH CORRECTIONS  ☐ NEW PROOF REQUIRED`. The grease pencil ticks the
  first.

**Density.** At most two HUD elements plus one type block per frame. Low in the darkroom verses, medium in the choruses, zero in
the breakdown (89.33-109.07) and from 133.38 to 140.24, maximum in the climax. There is no crawling ticker: that is anabology's
signature.

---

## 5. Recurring motifs

1. **THE TRAY (development).** Introduced when the eyes surface (1). Transformed by the drop (4); the chorus framing pushed +1,
   +2, +3 and +4 (8, 18, 30, 45); the Chinese characters (9); the failed safelight test (22); agitation as training (24); the fuse
   of development (34-35); the cyanotype (36); maximum black with only the sparks left (46). The motif peaks in the white sheet
   that never develops (50), shown in the opening's own framing: we have learned what developing looks like, and this time there is
   nothing to develop.
2. **THE BEAM (projection).** Registration eats his face (6); the face slides off clay (11); the projected face shrinks to the
   Omega point (20); he steps out of it and the face stays behind (39); the turntable shows the guessed back (48). The beam is the
   machine's way of seeing, and it is how the reconstruction was actually made.
3. **THE LINE (prints on paperclips).** One print, then identical prints (3); breathing paper (10); the hall (14); a print falling
   free and the empty clip (16); the moon among the portraits (19); copies of copies (25); stepping into a print (26b); the clip
   that holds (29); the studio full of prints (31); the prints turning to face him (33); tearing through them (41); 100,000 (42);
   the flattering retouch (43); the hall recording his walk (52); the empty clip again (53). It is the paperclip maximiser with him
   as the paperclip, and it ends on a clip that holds nothing. The empty clip is planted at 16c, long before it means anything.
4. **THE GREASE PENCIL (the machine's hand).** Orange marks only, three times: the circle on the contact sheet (12), crop marks on
   the multiple exposure (40), and the tick (54). Choosing, cropping, approving.
5. **THE WINDOW (the photograph's shape).** 7:9 → 1:1 → 4:3 → 16:9 → 7:9 (section 4.4). The film opens out of the photograph and
   closes back into its empty outline.

---

## 6. Timing table

All times come from `song.json` (t0 = 0.2356 s, 132.000 BPM; bar b starts at 0.2356 + (b−1)·1.81818 s). Cuts fall on line
starts, word onsets or downbeats. Frame = round(t × 24). The 63 rows (72 shots, counting the ten jump cuts inside 49) are
contiguous from 0 to 156.651 s, checked by script. `HS` marks the 13 hard syncs, each on a musical event from the research
budget: 16.60, 22.96, 23.87, 59.33, 60.24, 89.33, 109.07, 111.14, 125.69, 138.42, 140.24, 152.96, 154.78.

### 6.1 The acceleration curve
| Span (s) | Section | Shots | ASL (s) | What accelerates inside the frame | Window | Prints in frame | HUD | Light |
|---|---|---|---|---|---|---|---|---|
| 0-16.60 | intro, verse 1 | 5 | 3.32 | one development, word by word; one print per beat in shot 3 | 7:9 | 1 → 5 | low | amber |
| 16.60-23.87 | pre-chorus 1 | 2 | 3.64 | one slow registration over 4.8 s against the first kicks | 1:1 | 0 | low | beam |
| 23.87-38.42 | chorus 1 | 6 | 2.42 | development snaps on the crash (PUSH +1) | 4:3 | 1 → 36 | medium | amber |
| 38.42-52.96 | verse 2 | 1 | 14.55 | steps on half time (0.91 s), then on every beat; prints re-develop on 8ths (0.23 s) | 4:3 → 16:9 | ~200 | low | night |
| 52.96-60.24 | pre-chorus 2 | 5 | 1.45 | half-bar cuts on the 8th-note kicks | 16:9 | 1 | low | night → amber |
| 60.24-74.10 | chorus 2 | 6 | 2.31 | 30 enlargements in 3.3 s, one per 16th (0.114 s) | 16:9 | 1 → 12,288 | high | amber |
| 74.10-89.33 | verse 3 | 5 | 3.05 | agitation on the words; copies doubling per beat | 16:9 | 2^n | medium | amber, night |
| 89.33-109.07 | breakdown | 9 | 2.19 (stills) | nothing: one moving element per frame, grain frozen | 16:9 | 1 → thousands, still | off | white, amber |
| 109.07-111.14 | build | 4 | 0.52 | negative/positive on each "just" | 16:9 | 0 | medium | white, flash |
| 111.14-125.69 | bridge | 11 | 1.32 | cuts on beats in 41; exposures on 8ths in 40 | 16:9 | 100,000 | medium-high | night |
| 125.69-131.99 | chorus 4 | 13 | 0.49 | a weave pass and a turntable step per beat, a generation per 8th (0.227 s) | 16:9 | 2^n → one average | high | black (PUSH +4) |
| 131.99-138.42 | Ilya | 1 | 6.42 | nothing develops | 16:9 | 1, blank | → zero | amber |
| 138.42-140.24 | stop | 1 | 1.82 | | full black | 0 | none | black |
| 140.24-152.96 | climax | 1 | 12.73 | prints record him on beats, then 8ths, then 16ths (52 captures) | 16:9 | 52 frozen walks | max | night → white |
| 152.96-156.65 | tail | 2 | 1.84 | one swing | 16:9 → 7:9 | the empty clip | minimal | white → black |

**The shape.**
- Cut length falls from 3.3 s (verse 1) to 0.49 s (chorus 4), and the interval between in-frame events falls from a line (about
  3 s) to a 16th note (0.114 s) in chorus 2 and the climax.
- The counterpoint holds sit against the loudest music: the verse-2 one-take, the frozen breakdown, the Ilya tray and the single
  climax shot. Speed lives in the frame while the cut stays still.
- The singularity is counted in prints: one, a roll of 36, a hall, 12,288, 100,000, 2^n, and then one face that is no one.

**Screen time by source** (summed from the shot table).

| Source | Seconds | Share |
|---|---|---|
| 3D (our renders) | 56.0 | 36 % |
| GEN, the live man (face plates and stills) | 46.7 | 30 % |
| COMP (our layer over the face-free tray plate P13) | 38.4 | 24 % |
| TYPE | 12.0 | 8 % |
| GEN, face-free (P05) | 3.6 | 2 % |

### 6.2 Shot table
Presence levels are in brackets. `PL.` lines are HUD plate captions. Motion names the CMU clip or pose; motif names are from
section 5.

| # | t0-t1 (s) · frames · dur | Music · lyric [presence] | Image · camera | Motion · motif | Out | Src |
|---|---|---|---|---|---|---|
| 1 | 0.000-5.900 · 0-142 · 5.90 | silence to 0.23, pad; L0 "I see sparks of AGI in your eyes" 2.045-5.88 [CARD: stacked word by word in the left margin; ZH set vertically in the right margin] | WINDOW 7:9 (the photograph's shape) centred in black. Top-down, locked: a sheet of white paper in a developer tray under a dim safelight; the liquid rocks, one slow wave per 2 bars. HUD types `LATENT IMAGE · FROM 1 PHOTOGRAPH` (0.10-0.95) and `FRONT ONLY` (1.10-1.45). 2.045 "I": two dark points surface, the pupils. 2.50 "see": irises. 2.852 "sparks": an orange catchlight in each eye, the only colour inside the window. 3.635/4.32/4.54 A-G-I: brows, lashes, the bridge of the nose. 4.77-5.23: the face fills outward from the eyes; ears, hairline and jaw stay pale and thin (guessed). 5.40: the print blinks once | tray agitation · TRAY, WINDOW | cut on "Your" | COMP on P13 + P06 as the print |
| 2 | 5.900-7.725 · 142-185 · 1.82 | L1 "Your circuits make me nervous," [THOUGHT, left margin; ZH vertical right] | WINDOW 7:9. MCU, dead frontal, eye level: HE, alive, in the darkroom, one dim safelight above the lens; wet prints on a line soft behind him. He breathes, swallows, holds the lens. On "nervous" (7.05) the prints behind him tremble and one drip falls | stand/breathe · LINE | cut on "that's" | GEN P01 |
| 3 | 7.725-9.545 · 185-229 · 1.82 | L2 "that's no surprise" [THOUGHT] | WINDOW 7:9. The drying line recedes from the lens into the dark (vertical one-point); one print of his face hangs near the lens. On each beat (7.963, 8.417, 8.872, 9.327) an identical print appears further along the line. PROOF Nº 0002 → 0006 | · LINE | cut on "There" | 3D |
| 4 | 9.545-12.963 · 229-311 · 3.42 | L3 "There was a sudden drop in your training loss," [SUBTITLE, margins]; bass swells 12.05 | WINDOW 7:9. Top-down tray, his face in the developer, soft. A single drop falls from the corner of a print hanging above and strikes the liquid on "drop" (10.70); ripple rings cross the face, and behind the rings the face is sharper (grokking). A hairline graph in the left margin steps down on the same frame | · TRAY | cut on bar 8 (12.963) | COMP on P13 |
| 5 | 12.963-16.599 · 311-398 · 3.64 | L4 "now I'm your servant and you're my boss" 13.18 [SUBTITLE] | WINDOW 7:9. THE STUDIO, first appearance: white seamless, flat shadowless frontal light, a tape X on the floor. He sits on a stool facing the lens, hands on knees, full figure; slow push-in. On "boss" (15.675) he lifts his eyes into the lens: the sitter commands whoever portrays him | seated (static key + procedural breath) · WINDOW | → flash | GEN P02 |
| 6 HS1 | 16.599-22.963 · 398-551 · 6.36 | first kick 16.60; L5 "ChatGPT, please don't eat me alive" [THOUGHT: Chat 16.62, G 17.22, P 17.93, T 18.42, then 19.05-21.36; ZH vertical right]; hat roll 22.05; "I'm" 22.73 | 16.599: a 2-frame white flash (the one exposure) and the WINDOW widens 7:9 → 1:1 in 8 frames; the old edges linger one bar as hairlines labelled `EDGE OF PHOTOGRAPH`. THE PRAYER: low angle, black space, he stands in a hard column of light, face lifted into it, eyes closed. The beam carries a projection of his own photograph, offset and 10 % too large (a ghost face over his face); it slides into exact registration on "alive" (21.36): the machine's version eats his face. The HUD's four registration marks start doubled and converge on the same frame. The kick drives; the image never cuts | stop and look up (held) · BEAM, WINDOW | hard cut to black | GEN P03 + 2D projection comp |
| 7 HS2 | 22.963-23.872 · 551-573 · 0.91 | a-cappella stop: "upping" 22.96, "my" 23.41, "P" 23.62 [CARD] | True black (the lamp is off). "upping my" small in italic; "P(" huge on 23.62 | · | card holds across the cut | TYPE |
| 8 HS3 | 23.872-26.580 · 573-638 · 2.71 | crash on "doom" 23.87: "(doom)" completes in orange [CARD, held to 25.07]; L7 "'cause the future goes FOOM" 24.35 [SUBTITLE] | The WINDOW widens 1:1 → 4:3 on the crash. CHORUS FRAMING (identical at every chorus): the tray from above, his face in the developer. On the crash it snaps to full density in one frame; HUD `PUSH +1` in orange, and the step wedge's marker drops one patch. On "FOOM" (25.68) a surge runs across the tray and the blacks bloom, then settle one shade darker | tray agitation · TRAY, WINDOW | cut on "Trapped" | COMP on P13 + P06 |
| 9 | 26.580-27.980 · 638-672 · 1.40 | L8 "Trapped in the Chinese room," [THOUGHT, EN small; the ZH is the image] | Same tray, another sheet: 困在中文屋里 develops in large Noto Serif SC Black and reaches full density on "room" (downbeat 27.508). The machine develops symbols it cannot read; he, who can, is not in the shot. `PL. SEARLE · MINDS, BRAINS, AND PROGRAMS · 1980` | · TRAY | cut on "with" | COMP on P13 |
| 10 | 27.980-29.980 · 672-720 · 2.00 | L9 "with a bag of shrooms" [SUBTITLE] | The drying line side-on at eye level: a dozen prints of him curl and uncurl as they dry, a slow wave travelling along the line (the paper breathes). Clipped among them with the same paperclips: a small brown paper bag, unopened | · LINE | cut on "See" | 3D |
| 11 | 29.980-33.400 · 720-802 · 3.42 | L10 "See through the shoggoth's lies," [THOUGHT] | THE BEAM I. Black room; a projector beam from beside the lens falls on a grey clay head (the bust's geometry, untextured) and on a black wall behind it. On the lens axis it is simply his face. On "shoggoth's" (30.60) the camera arcs 35° right; by "lies" (downbeat 31.145) the photograph has slid off the geometry: stretched across the ear, spilled flat onto the wall, and the clay cheek is bare. Hold one bar | · BEAM | cut on "with" | 3D (bust geometry + projected photo) |
| 12 | 33.400-35.600 · 802-854 · 2.20 | L11 "with your shinigami eyes" [SUBTITLE] | A contact sheet fills the 4:3 window: 36 frames of his eyes (brows to nose bridge), each with its frame number printed above it like a name. On "shinigami" (33.87) the orange grease pencil starts a circle and closes it round one frame on "eyes" (downbeat 34.781); the other 35 dim to 30 % | · PENCIL | cut at the melisma | TYPE (36 frames from P06) |
| 13 | 35.600-38.417 · 854-922 · 2.82 | melisma 35.6-37.05; fill 37.51 [QUESTION at 37.05: "which one is him?" / 哪一张是他？] | Pillow, nobody: the darkroom line of prints under the safelight. The safelight dims as the melisma fades (the voice is the light); the question types into the near-dark; the prints tremble on the fill hits (37.74, 37.96, 38.19) | · LINE | cut on bar 22 | 3D |
| 14 | 38.417-52.963 · 922-1271 · 14.55 | L12 "We had a stable training run," 38.63 [SUBTITLE]; L13 "But now the singularity's begun" 41.36 [CARD, upper third over the image]; L14 "And you're optimizing, accelerating," 45.07 [SUBTITLE]; L15 "I feel my atoms rearranging" 49.52 [THOUGHT] | ONE TAKE, THE HALL (the line as runway), the film's first cold image. A long hall of prints hanging on both sides at head height, lit from behind, so they read as an audience in silhouette and his faces show through the wet paper mirrored; wet black floor, haze, cold backlight at the far end. Locked long lens. He enters at the far end walking at the lens at half time (steps on beats 1 and 3). 41.36-44.095: the WINDOW slides open from 4:3 to 16:9 across the line, and the new margins fill with more hall (outpainting). 45.690 (bar 26): his gait doubles to every beat (runway pace), and each print he passes re-develops a stop glossier, on the 8th grid (optimizing). 50.49 "atoms": the halftone screen over his face rotates 45° → 15° → 75° → 45°, moiré sweeping his skin, and settles by 52.83. He stops at MCU, frontal | slow walk → retimed runway walk → stop · LINE, WINDOW | cut on bar 30 (bass out) | GEN P04 (previs to plate) + 3D prints + halftone post |
| 15 | 52.963-56.599 · 1271-1358 · 3.64 | bass out; L16 "Sydney," 53.01 … "please" 55.98 [THOUGHT, the name as a prayer] | The prayer with no face: the same hall; he stands at its far end, back to us, facing the cold backlight; slow push. The prints hang still. `PL. SYDNEY · NYT · 2023-02-16` | stand (back) · LINE | cut on bar 32 (8th kicks) | GEN P05 (face-free) |
| 16a | 56.599-57.508 · 1358-1380 · 0.91 | 8th kicks; "let" 56.595, "me" 57.19 [THOUGHT] | Macro: a paperclip on the wire holding the top edge of a print of his face; water beads on the wire | · LINE | half-bar cut | 3D |
| 16b | 57.508-58.417 · 1380-1402 · 0.91 | "free" 57.945 | Same macro: on "free" the paper slips out of the clip and falls away out of frame, turning. PROOF Nº counts down by one, the only time it ever does | · LINE | half-bar cut | 3D |
| 16c | 58.417-59.327 · 1402-1424 · 0.91 | hat roll; "I'm" 59.08, "upping" 59.31 | The empty paperclip swings on the wire | · LINE (the empty clip) | → black | 3D |
| 17 HS4 | 59.327-60.236 · 1424-1446 · 0.91 | stop: "my" 59.765, "P" 59.975 [CARD] | True black; the card of 7, scaled +10 %. HUD types `PUSH +2` | · | card holds across the cut | TYPE |
| 18 HS5 | 60.236-62.485 · 1446-1500 · 2.25 | crash; "(doom)" 60.22 completes [CARD]; L18 "I hear the basilisk boom" 60.50 [SUBTITLE] | CHORUS FRAMING, PUSH +2: the face in the tray denser, harder, grainier. On "boom" (62.035) one pressure ring crosses the liquid; after it passes, the print's eyes are looking straight into the lens (a moment ago they looked just past it) | · TRAY | cut on "NVDA" | COMP on P13 + P06 |
| 19 | 62.485-64.115 · 1500-1539 · 1.63 | L19 "NVDA to the moon" [SUBTITLE; N-V-D-A on 62.49/62.73/62.95/63.18] | The line in the darkroom: among the prints of his face hangs one print of the full moon; a slow tilt up centres it on "moon" (63.849). Caption under it: `PL. 19 · NVDA ≈ $5.43T MKT CAP · 2026-09-25` | · LINE | cut on "The" | 3D (public-domain moon) |
| 20 | 64.115-66.239 · 1539-1590 · 2.12 | L20 "The Omega Point's coming soon" [CARD: a small orange Ω; SUBTITLE] | Top-down on the enlarging easel: his face projected in a white rectangle. The enlarger head descends; the image shrinks and concentrates into a single orange point by "soon" (65.68). `PL. TEILHARD · LE PHÉNOMÈNE HUMAIN · 1955` | · BEAM | cut on "One" | 3D |
| 21 | 66.239-69.600 · 1590-1670 · 3.36 | L21 "One E thirty flops a second" [THOUGHT]; ad-lib 68.18-69.58 | BLOW-UP. From that point, 30 enlargements on the 16th grid from 66.258 to 69.553, each ×10 and each 'enhanced' with detail the machine invents: point → grain → a face → an eye → the hall in its pupil → a print in the hall → its grain … The deepest levels are the head's point cloud drawn as dark silver grain, then pure noise, where diffusion begins. HUD `ENLARGEMENT ×10^n`. The noise shimmers under the ad-lib | · (the latent) | cut on "That" | 3D (infinite-zoom stack + point cloud) |
| 22 | 69.600-72.270 · 1670-1734 · 2.67 | L22 "That was safe enough, we reckoned" [SUBTITLE] | THE SAFELIGHT TEST, a real darkroom procedure. Top-down: a coin lies on a white sheet under the orange safelight; then the sheet in the developer fogs grey everywhere except a pale disc where the coin lay. The light was not safe. `PL. EO 14110 · 1E26 FLOP · 2023-10-30 · REVOKED 2025-01-20` | · TRAY | cut on the ad-lib | COMP on P13 |
| 23 | 72.270-74.095 · 1734-1778 · 1.83 | ad-lib 72.27-73.92; fill 73.87 [QUESTION: "how many of him are there now?" / 现在一共有多少个他？] | Pillow, nobody: the hall again, now ten lines deep on each side, prints to the vanishing point. PROOF Nº jumps 0479 → 12,288 | · LINE | cut on "Forward" | 3D |
| 24 | 74.095-77.725 · 1778-1865 · 3.63 | L23 "Forward" 74.095, "MLP" 74.79/75.21/75.66, "backward" 76.12, "repeat" 76.80 [THOUGHT; "backward" set mirrored] | Agitation as a training loop, from above: the tray tips forward on "Forward", three short rocks on M-L-P, back on "backward", again on "repeat"; with each rock his face in the tray sharpens a little (convergence). The bar-42 downbeat (74.781) falls inside the shot | tray agitation · TRAY | cut on "Now" | COMP on P13 |
| 25 | 77.725-81.365 · 1865-1953 · 3.64 | L24 "Now von Neumann's obsolete" [SUBTITLE] | Self-reproduction: one print hangs near the lens; on each beat a copy of it appears further down the line, copied from the one before, never from the source; by "obsolete" (80.00) the copies recede to the vanishing point, each a little harder and glossier. PROOF Nº doubles per beat. `PL. VON NEUMANN · THEORY OF SELF-REPRODUCING AUTOMATA · 1966` | · LINE | cut on "Sharp" | 3D |
| 26a | 81.365-82.000 · 1953-1968 · 0.64 | L25 "Sharp left" [SUBTITLE] | Tracking behind him down the hall: his back, a backlit silhouette | walk (back) · LINE | cut on "turn" | 3D (avatar silhouette) |
| 26b | 82.000-85.020 · 1968-2040 · 3.02 | "turn and there you are" 82.00-83.65 [SUBTITLE] | On "turn" he turns 90° left and steps into a hanging sheet; the sheet swings and he is gone. The camera pans left onto it: the print now shows him frontal, looking out: "there you are" (82.97-83.65), held through the long "are". `PL. SOARES · SHARP LEFT TURN · 2022-06-15` | turn + walk · LINE | cut on "Without" | 3D (+ still P07a as the print) |
| 27 | 85.020-89.327 · 2040-2144 · 4.31 | L26 "Without a single CDR" [SUBTITLE; C-D-R on 86.56/87.05/87.51] | A 36-frame strip of film on a light box, frontal: frame 01 holds his face, frames 02-36 are clear. On C, D and R mono types beside it: `(CAR ROLL) → FRAME 01` / `(CDR ROLL) → NIL`. Held through the long note | · the one photograph | cut on bar 50 | TYPE |
| 28 HS6 | 89.327-92.963 · 2144-2231 · 3.64 | drums and bass cut; L27 "Gato," 89.315 … "please" 90.669 [THOUGHT, the name as a prayer]. Breakdown rule: every image is a still print, grain frozen, one moving element, HUD off | A single print fills the frame, its white border showing: him sitting on the studio floor, knees drawn up, alone in the white. It hangs from one paperclip and turns a few degrees on it (the moving element) | still · LINE | 6-frame dissolve | still P07b + 3D |
| 29 | 92.963-94.781 · 2231-2275 · 1.82 | "don't" 92.505, "let" 92.96, "me" 93.64, "go" 94.31 [THOUGHT] | Macro: the paperclip holding the corner of that print; on "go" the paper slips a millimetre and holds. (In pre-chorus 2 the print fell; this prayer is answered) | still · LINE | 6-frame dissolve | 3D |
| 30 | 94.781-96.599 · 2275-2318 · 1.82 | hats back; L28 "I'm upping my P" 95.425-96.36 [CARD, outline type] | CHORUS FRAMING as a still, PUSH +3: the face in the tray almost black; only the eyes and the bridge of the nose still read. The HUD shows only `PUSH +3` | still · TRAY | cut on sub boom 1 | COMP on P13 + P06 |
| 31 | 96.599-98.835 · 2318-2372 · 2.24 | sub boom; "(doom)" 96.595 completes; L29 "as paperclips fill the room." [SUBTITLE] | Still, wide, THE STUDIO: lines of prints of his face, each held by a paperclip, fill the white room floor to ceiling, row behind row. Nobody. The prints sway in a draft (the moving element) | still · LINE | cut on "Killswitch" | 3D |
| 32 | 98.835-100.680 · 2372-2416 · 1.85 | L30 "Killswitch guys on PTO," [SUBTITLE; P-T-O on 99.755/100.0/100.24]; sub boom 100.24 | Still: on the darkroom wall, the white-light switch (the one switch that fogs every latent image) sits under a strip of masking tape with a pencilled note: `OUT · BACK MON`. A mug on the shelf; its steam is the moving element | still · the killswitch | cut on "Now" | 3D |
| 33 | 100.680-102.535 · 2416-2461 · 1.85 | L31 "Now there's nowhere left to go." [THOUGHT] | Still: THE STUDIO. He sits on the stool, face in his hands (the Shinji chair). Prints of him hang on every side; the only moving element is the prints turning slowly on their clips until every one of them faces him | face in hands · LINE | cut on "Too" | still P08 + 3D prints |
| 34 | 102.535-103.872 · 2461-2493 · 1.34 | L32 "Too late now, we lit" [SUBTITLE] | Still, from above: a white sheet in the tray; on "lit" (103.41) a dark line starts across it from one edge, a fuse of development | still · TRAY | cut on sub boom 3 | COMP on P13 |
| 35 | 103.872-105.910 · 2493-2542 · 2.04 | sub boom; "the fuse." 103.62-104.835; ad-lib 104.55-105.88 | Still: the sheet now carries his face. The dark front advances from the edges inward (ears, hairline and jaw go black first) and stops at the eyes, which stay lit | still · TRAY | cut on "Orthogonality" | COMP on P13 + P06 |
| 36 | 105.910-109.070 · 2542-2618 · 3.16 | L33 "Orthogonality thesis blues." [THOUGHT]; sub boom 107.508 | A cyanotype of his face rinsing in a tray of clear water, yellow-green turning to Prussian blue; on the sub boom it deepens to full blue. The only blue in the film | still · TRAY | jump | COMP on P13 (cyanotype ramp) |
| 37a HS7 | 109.070-109.560 · 2618-2629 · 0.49 | "Just" 109.07 [CARD: “Just]; drums back 109.33 | THE STUDIO, frontal MCU, opened by a 2-frame flash; NEGATIVE | stand/breathe · WINDOW | jump | GEN P09 |
| 37b | 109.560-110.180 · 2629-2644 · 0.62 | "just" 109.56 [CARD adds "just"]; snare roll | Same framing, the next moment, flash; POSITIVE | stand/breathe | jump | GEN P09 |
| 37c | 110.180-110.650 · 2644-2656 · 0.47 | "just" 110.18 | Flash; NEGATIVE | blink | jump | GEN P09 |
| 37d | 110.650-111.145 · 2656-2667 · 0.49 | "just" 110.65 | Flash; POSITIVE | head settles | → | GEN P09 |
| 38 HS8 | 111.145-113.359 · 2667-2721 · 2.21 | bass back on "trans-" 111.12; "formers" 112.05; "all the way!" 112.50-112.95 [CARD: “transformers all the way!”] | Crane up from him (small, backlit, frontal) in the hall until the lines of prints run to the horizon in every direction | stand · LINE | cut on "Till" | 3D |
| 39 | 113.359-115.205 · 2721-2765 · 1.85 | L35 "Till you learned to disobey" [SUBTITLE] | THE BEAM II. He stands frontal in the projector beam, his photograph in exact registration on his face (as in 6). On "disobey" (114.30) he steps out of the beam and walks off into the dark, a silhouette; the projected face stays where he was, lit, hanging on the empty wall. `PL. ALIGNMENT FAKING · ARXIV 2412.14093 · 2024-12` | stand, turn, walk off · BEAM | cut on "Post" | 3D (bust face in the beam at 0°; avatar unlit once out) |
| 40 | 115.205-117.030 · 2765-2809 · 1.83 | L36 "Post-Chinchilla, super-dense" [THOUGHT] | Multiple exposure: prints of him laid down in exact register, one on each 8th, the sheet building toward maximum black with a ghostly average face floating in it; orange grease-pencil crop marks frame the average as if to keep it; full black on "dense" (116.59). `PL. CHINCHILLA · ARXIV 2203.15556 · 2022-03` | · TRAY | cut on "Breaking" | 3D/2D (density accumulation) |
| 41a | 117.030-117.508 · 2809-2820 · 0.48 | L37 "Breaking" 117.03 [SUBTITLE] | He walks at the lens as a backlit silhouette and tears through a hanging sheet printed with his own face. `PL. SECURITY INCIDENTS "TENS OF THOUSANDS" · AXIOS · 2026-09-26` | walk (silhouette) · LINE | beat cut | 3D |
| 41b | 117.508-117.963 · 2820-2831 · 0.45 | "through each" | The next sheet tears | walk | beat cut | 3D |
| 41c | 117.963-118.417 · 2831-2842 · 0.45 | "safety" | The next sheet tears | walk | beat cut | 3D |
| 41d | 118.417-118.887 · 2842-2853 · 0.47 | "fence" 118.41 | The last sheet tears; nothing behind it but backlight | walk | cut on "Hundred" | 3D |
| 42 | 118.887-120.700 · 2853-2897 · 1.81 | L38 "Hundred thousand GPU" [SUBTITLE; G-P-U on 119.735/119.975/120.225] | Aerial: a dark hall of 100,000 hanging prints in rows, each lit from below by a small lamp; it reads as a data hall and as a silent audience. `PL. COLOSSUS · 100,000 H100 · 2024 → 555,000 GPU · 2026-01 (REPORTED)` | · LINE | cut on "RLHF" | 3D (instanced) |
| 43 | 120.700-122.730 · 2897-2946 · 2.03 | L39 "RLHF goes askew" [SUBTITLE; R-L-H-F on 120.7/120.9/121.13/121.37] | A print of him on the line is retouched as we watch by an unseen airbrush: skin smoothed, gloss raised, flattered. On "askew" (121.83) one clip lets go and it hangs crooked, about 7° | · LINE | cut on the melisma | 3D (print from P07a) |
| 44 | 122.730-124.520 · 2946-2988 · 1.79 | wordless melisma [QUESTION: "did he ever sit for this?" / 他真的在这里坐过吗？] | Pillow: THE STUDIO, the stool on the tape X, empty, in the flat light | · WINDOW | cut on "I'm" | 3D |
| 45 | 124.520-125.690 · 2988-3017 · 1.17 | L40 pickup "I'm upping my P" 124.52-125.45; fill 124.78 [CARD builds] | CHORUS FRAMING, PUSH +4: the face in the tray darkening fast under the fill | · TRAY | → | COMP on P13 + P06 |
| 46 HS9 | 125.690-126.140 · 3017-3027 · 0.45 | "(doom)" 125.69 [CARD completes] | The tray at maximum black: the face is gone; only the two orange catchlights of the opening remain | · TRAY | cut on "Just" | COMP on P13 |
| 47 | 126.140-127.980 · 3027-3072 · 1.84 | L41 "Just as foretold by Loom" [THOUGHT] | Two prints of him, cut into strips, weave into one face, one pass per beat (126.145, 126.599, 127.054, 127.508): warp and weft, two branches becoming one. `PL. JANUS · SIMULATORS · 2022-09-02` | · LINE | cut on "From" | 3D/2D |
| 48 | 127.980-129.830 · 3072-3116 · 1.85 | L42 "From masked pre-training days" [SUBTITLE] | THE BEAM III. The clay head on a turntable under the projector steps 45° per beat (128.417, 128.872, 129.327): the photograph slides off, and on "days" (129.32) the back of the head faces us, grey and guessed. `PL. BERT · MASKED LM · 2018` | · BEAM | cut on "To" | 3D |
| 49 | 129.830-131.995 · 3116-3168 · 2.16 | L43 "To recursive self-upgrade" [THOUGHT] | Copy of a copy, as ten jump cuts on the 8th grid (cuts at 130.008, 130.236 … 131.827): each cut is the next generation, his print re-photographed and re-printed, each glossier, smoother and more generic, until at 131.599 the face belongs to no one: the model's prior, the average. PROOF Nº runs 2^n. `PL. MODEL COLLAPSE · NATURE 631 · 2024-07-24` | · LINE | cut on "What" | 3D (avatar head blended back to the base mesh) |
| 50 | 131.995-138.417 · 3168-3322 · 6.42 | L44 "What did Ilya see?" 132.00-132.96 [CARD]; "We'll never know." 133.38-136.9 [NONE: card, subtitles and HUD all vanish at 133.38]; "Was it" 137.40/137.80 [SUBTITLE] | ONE HELD SHOT: the opening framing again (the tray from above, now 16:9). A fresh white sheet slides into the developer. We wait. Nothing develops. The liquid rocks | · TRAY | cut on bar 77 | COMP on P13 |
| 51 HS10 | 138.417-140.236 · 3322-3366 · 1.82 | full stop: "all" 138.42, "for" 139.32, "show?" 140.16 [CARD] | True black: "Was it all for show?" builds word by word; 这一切只是一场表演吗？ small beneath | · | hard cut on the drop | TYPE |
| 52 HS11 | 140.236-152.963 · 3366-3671 · 12.73 | final drop, loudest section; wordless vocal pad 141.1-152.95 [none] | ONE SHOT: the hall, locked long lens, night. He walks at the lens at runway pace, one step per beat: the only time in the film he is present without sung words. The prints on both sides are blank, and each records him as he passes it: 12 on the beats of bars 78-80, 24 on the 8ths of bars 81-83, 16 on the 16ths of bar 84. The hall behind him fills with frozen frames of his walk (a Muybridge sequence). The backlight climbs from night to white. On the last beat (152.508) he fills the frame, frontal, and walks into the lens: white. HUD at maximum: PROOF Nº spinning; captions `NAVIER–STOKES (FORCED) · LEAN-CHECKED · 2026-09-08` and `"ONLY A TOOL AND PROXY" · 25 FIELDS MEDALISTS · 2026-09-11` | runway walk · LINE, WINDOW | white | GEN P10 + 3D capture prints |
| 53 HS12 | 152.963-154.781 · 3671-3715 · 1.82 | drums stop; bass and synth pulse [none] | The white clears to the same hall, empty and high-key: every print holds a frame of his walk, swaying in his wake. In the foreground one paperclip on the wire is empty and still swinging. 153.418-153.872: the WINDOW closes from 16:9 to 7:9 around the empty clip: the photograph's shape, with nothing in it | · LINE, WINDOW | cut on bar 86 | 3D (+ P10 frames as print textures) |
| 54 HS13 | 154.781-156.651 · 3715-3760 · 1.87 | bass cut; the synth fades, below −40 dBFS from 155.28 | Black. The slug line types `PROOF 1 OF 1`; the orange grease pencil ticks `☑ OK AS IS`; then, small: 潜影 · LATENT IMAGE | · PENCIL | end of file | TYPE |

### 6.3 The release (140.24-156.65)
The loudest 12.7 s of the song get one locked shot, and it is the only time the man is on screen without a sung word. He walks at
the lens at runway pace. The hall's blank prints photograph him as he passes, on beats, then 8ths, then 16ths, so by bar 84 the
hall behind him is a Muybridge sequence of his own walk: 52 frozen frames receding into the white. It is anabology's night-to-white
arc compressed into one walk, and the ending of *Blow-Up* turned around: Antonioni's photographer fades from the lawn after
throwing back a ball that is not there; ours walks out of the machine's pictures through the lens.

Then the drums stop and the white clears on the hall he has left. Every print holds him, and the one clip nearest to us is empty
and still swinging. The window closes to the photograph's shape around it. The bass cuts to black. After all its powers of ten the
proof counter reads `PROOF 1 OF 1`, and the machine's hand ticks `OK AS IS`: it stops correcting him. That is its answer to "Was it
all for show?". It cannot know whether he was there, so it accepts him as he is, which is also how any of us accepts another mind
(Husserl's appresentation, research section 8).

---

## 7. Feasibility

**Assumption.** No LOOKDEV.md exists yet. 3D shots are assumed to cost 1-2 s per frame at 1080p24 in headless Chromium with
SwiftShader on 2 of the 4 cores, and 2D composites over decoded plates 0.3-0.6 s per frame. Previews at 960x540 run about 4×
faster. Replace these figures when LOOKDEV.md lands.

| Element | Technique | Est. s/frame | Frames | Built once / reused |
|---|---|---|---|---|
| Tray compositor | the locked top-down plate P13 (or the 3D tray) decoded to JPEG; the paper located once by a fixed homography; a development shader: density(x, t) = target(x) · ramp((t − t_start) · k(x)), with k from the certainty map and t_start from the word times; push = contrast curve + grain + halftone pitch; drops and pressure rings as height-field normal perturbation | 0.3 | ~920 | once; 14 shots |
| Certainty map | a grey image from the photo's landmark regions (eyes, brows, nose and mouth high; ears, hairline and jaw low), stored only in `claudepop/out/` | offline | | once |
| Prints | instanced planes with a texture atlas of approved generated stills; vertex-shader sway and curl; backlit translucency (the mirrored texture through a paper-fibre map); a paperclip mesh | 0.8-1.5 | ~1,300 | once; every LINE shot |
| Hall | box, wet floor with planar reflection, haze, backlight, rows of print instances; a camera and capture solver so prints are passed or captured on grid times from song.json | 1.5 | ~700 incl. previs | once; 10 shots |
| Studio | cyclorama, flat light, stool, tape X | 0.6 | ~300 | once |
| The beam | the bust geometry in matte grey clay; `SpotLight.map` carrying the photograph from the photo camera's pose; PCF shadows; a wall plane | 1.0 | ~200 | once; 11, 39, 48 (and the comp in 6) |
| Avatar | the MakeHuman rig with the CMU clips through the existing retarget; silhouette lighting; the head-target blend to the base mesh for 49 | 1.0 | ~250 | once |
| Blow-up (21) | an infinite-zoom stack: six source images (grain, face, eye, hall, print, point-cloud grain) cycled through 30 levels of ×10 on a log scale, crossfading inside each level | 1.2 | 81 | |
| Contact sheet, film strip, weave, cyanotype, multiple exposure | 2D canvas and shader passes over cached frames | 0.3 | ~200 | |
| Paper tearing (41) | pre-fractured sheet halves, hinged and thrown on the beat | 1.2 | 45 | |
| Climax captures (52-53) | plate P10 plus a matte of him (RVM or BiRefNet on CPU, about 305 frames); each print's texture is the matted plate frame at its capture time, placed in the matched previs camera | 0.8, plus about 2 s offline per matte frame | 350 | |
| Halftone, grain, grade | a screen-space AM screen with animatable angle and pitch; frozen or moving grain; the three register LUTs; bloom on VOICE | 0.15 | all 3,760 | once |
| Voice envelope | per-frame RMS of the Demucs vocal stem (`out/audio/stems/htdemucs/pdoom_44k/`) written to `voice_env.json` | ~0 | | once |
| Type and HUD engine | word and letter timing from song.json; the CARD / THOUGHT / QUESTION / SUBTITLE layout rules; vertical Chinese; the proof-sheet HUD with registration marks bound to the window; grease-pencil strokes (patterns from `odyssey/film/src/text.js`, copied into claudepop) | 0.05 | all | once |

**One full 1080p pass.** About 2,000 3D frames × 1.5 s ≈ 50 min; about 1,700 composite frames × 0.45 s ≈ 13 min; mattes and extras
about 15 min. That is about 80 CPU-minutes, or 40-45 minutes on 2 workers; a preview pass takes about 12 minutes. That is cheap
enough for the many full watch-throughs the brief asks for.

**Built once, reused.** One tray plate carries 14 shots. One print system carries every LINE shot and the climax. One hall carries
ten shots. The bust carries the three BEAM shots and every close-up fallback. The previs of each generated shot is also its
fallback.

**The animatic is the fallback film.** Every shot with the live man is first a 3D previs with the avatar (and for 14 and 52 that
previs is also the input to H3 3D-to-video), so the whole film plays to the song in this session. When a plate fails, the previs,
lit to a silhouette or given the bust at 0°, is already in the cut.

### 7.1 Risks and fallbacks
| Risk | Why it matters | Mitigation and fallback |
|---|---|---|
| **1. Identity and moderation on the live-man plates**, above all the two long walks (P04, 14.55 s; P10, 12.73 s) | They are the film's two spines, and identity drift is exactly what made anabology's replies say "slop". Kling, H3 and Veo may refuse him or drift | Stage 0 probe on day 1 and the ArcFace gate on every take (GENMEDIA). Both walks are backlit, so the face is dark until the last bars; the walk can be a silhouette plate and the final MCU a separate short face plate, joined under the halftone rotation at 50.49, which hides the seam. Fallbacks: the 3D avatar in silhouette for the walk and the bust at 0° for the MCU. Only 7 face video plates in total |
| **2. Legibility and heat** | A darkroom metaphor can read as small, cold still life to a muted viewer on a phone, and the 7:9 window uses only 44 % of the width for the first 16.6 s | The hook is built for the phone: the face fills the window, the CARD words in the margins are large, and a live face arrives at 5.9 s. The warm images (the hall walks at 38.4 and 140.2, the prayer at 16.6) are placed on the song's big entrances. Every deadpan match is designed to read in under 2 s. Review every shot at 390 pt width; if the window reads as a mistake, start at 1:1 instead of 7:9 |
| **3. Consent and taste in changing his face** | Shot 49 blends him toward an average face, 43 retouches him, 11 and 48 smear his photograph on clay, 35 blacks out his face from the edges | Ask him before building these. Each is at most 2.2 s, print-sized and halftoned, and none is ever in a live plate. Fallbacks: 49 becomes plain generation loss (contrast and grain only, no shape change); 43 keeps the crooked hang without the retouch. The ID photo is never shown as a document |
| 4. Overlap with treatment A and with odyssey | A also builds on measured versus inferred, projection-like seams, a white void and the research's shared devices; odyssey opened on a face rising out of a paper photograph | Section 9 lists what is shared and what differs. Most important: no passport page, no scan line and no rise into 3D in the opening, and no return to the photograph at the end |
| 5. The tray must look like chemistry, not a dissolve | It carries 14 shots, including the opening | Lookdev a real development curve (shadows first, a toe and a shoulder), liquid refraction over the print, and a paper tooth texture. Compare against real darkroom footage by eye. Fallback: the 3D tray |
| 6. Render time of the climax captures and the blow-up | 4 shared cores | Mattes offline in the background; blow-up levels precomputed as textures; quarter-resolution previews |

---

## 8. Sources per shot, plates and cost

**The rule of sources follows the philosophy.**
- The live man is a GEN face plate (Kling, H3 or Veo), rare on purpose: seven video plates and three stills.
- The machine's interior (the tray, the line, the beam, the blow-up, the copy chain) is ours: 3D and COMP.
- The environment he cannot be in with his face (his back in the hall, the tray itself) is face-free GEN (Seedance 2.5).
- The machine's voice is TYPE.

Seedance is face-free only: its references for back views are body crops with no face, and any plate in which a face appears is
rejected at review. All durations respect the model limits in GENMEDIA.md (Kling 3-15 s, H3 3D-to-video up to 15 s with a 5 s
minimum billed, Seedance 4-30 s, Veo 3.1 8 s).

### 8.1 GEN plates (next session)
| Plate | Shots (used s) | Route · generated length | Keyframe idea · motion | Fallback (3D/TYPE) |
|---|---|---|---|---|
| P01 | 2 (1.8) | Kling v3 pro i2v · 5 s | Frontal MCU in a darkroom, one dim orange safelight above the lens, wet prints soft behind · breathing, one swallow, eyes on the lens | the bust at 0° under orange top light in the 3D darkroom |
| P02 | 5 (3.6) | Kling v3 pro i2v · 5 s | White seamless, flat shadowless light, tape X; he sits on a stool, hands on knees, full figure, 50 mm at eye level · slow push-in; eyes lift to the lens at +2.7 s | the avatar seated in the 3D studio, framed so the face is small, with the bust face |
| P03 | 6 (6.4) | Kling v3 pro i2v · 7 s; Veo 3.1 hero candidate (8 s) | Low angle, black space, face lifted into one hard top light, eyes closed · almost still, one breath; our projection comp on top | the bust pitched up under top light, or a rim-lit silhouette with only the projection visible |
| P04 | 14 (14.55) | H3 Max 3D-to-video 1080P · 15 s (tight, 5-frame handles); second route Kling v3 motion control (up to 30 s) driven by our previs walk with a face element | Our hall previs: he walks from far away to MCU, the gait doubling at +7.27 s, and stops; locked long lens, backlight and haze · camera, timing and layout from the previs | the 3D hall with the backlit avatar (face in shadow) for the walk, and the bust at 0° for the final MCU and the halftone rotation |
| P05 | 15 (3.6) | Seedance 2.5 i2v · 5 s, face-free | From behind, a man stands at the end of a dark hall lined with hanging white sheets, facing a cold backlight · slow push | the 3D avatar from behind, in silhouette |
| P06 | 1, 12, 18, 30, 35, 45 (as print textures) | Kling v3 pro i2v · 5 s; Veo 3.1 hero candidate for the opening blink | Frontal face, flat soft light, plain grey, still · one slow blink at +3.4 s, then a glance to the lens | the bust at 0°; the blink replaced by the catchlights going out; the 36 eye frames from slight relights of the bust |
| P09 | 37a-d (2.1) | Kling v3 pro i2v · 5 s | White studio, frontal MCU, flat light · a breath, a blink, a slight settle of the head | the bust at 0° in the 3D studio |
| P10 | 52 (12.7), 53 (as print textures) | H3 Max 3D-to-video 1080P · 14 s (second route Kling v3 motion control) | Our climax previs: a runway walk at the locked long lens from far to CU and out of frame; the backlight ramps to white · camera and timing from the previs | the backlit avatar silhouette for bars 78-83, the bust at 0° for the close-up in bar 84, then the whiteout |
| P13 | 1, 4, 8, 9, 18, 22, 24, 30, 34-36, 45, 46, 50 (about 38 s of screen) | Seedance 2.5 i2v · 10 s, face-free, made to loop | Top-down macro of a sheet of white photographic paper in a developer tray under an orange safelight, the liquid rocking slowly; locked camera | the 3D tray: a plane with a water normal map and caustics |

**Stills** (Nano Banana Pro or Seedream v5 pro edit from the approved sheet): P07a, a frontal portrait for the prints he becomes
(26b, 43); P07b, him seated on the studio floor, knees up, face small (28); P08, him on the stool with his face in his hands (33).
**Print set:** the approved character sheet (12-20 images) plus about 40 variant stills (angles, light, expression) as the
textures of every hanging print. These are the machine's guesses in the story, but they pass the same identity gate as any plate:
the drift is only ever staged, in 49.

Count: 7 face video plates, 2 face-free video plates, 3 stills and the print set. About 71 s generated per take (the tray plate loops) for about 88 s of
screen that depends on a plate.

Optional, by hand only (GENMEDIA section 6): the user may make Midjourney keyframes for P02, P03 and P09, which go through the same
ArcFace gate.

### 8.2 Cost (list prices from GENMEDIA.md, read 2026-09-28; H3 at the prices that apply after 2026-09-30)
| Item | Basis | USD |
|---|---|---|
| Stage 0 likeness probe | per GENMEDIA | 6 |
| Character sheet | per GENMEDIA | 30 |
| Keyframes | 9 video plates × 6 candidates × about $0.10, plus edits | 7 |
| Stills and print set | 3 × 6 × about $0.10, plus about 40 variants at about $0.10 | 6 |
| Drafts ×3 | Kling-route faces drafted on H3 480P ($0.05/s × 27 s); H3 3D-to-video 480P (about $0.16/s with reference tokens × 29 s); Seedance draft 480p ($0.2205/s × 15 s) | 28 |
| Finals ×2 | Kling 27 s × $0.112 = $3.0; H3 3D-to-video 1080P 29 s × about $0.27 = $7.8; Seedance 1080p 15 s × $1.164 = $17.5 | 57 |
| Hero upgrades | Veo 3.1 1080p, audio off, P03 and P06: 2 × 8 s × $0.20 × 2 takes | 6 |
| Upscale | approved takes only | 2 |
| **Planned** | | **about 140** |
| With a 2× retry allowance on drafts, finals and heroes | | **about 235** |
| Optional identity LoRAs (Krea 2 or FLUX.2, H3 i2v) | | +25 |

Keep GENMEDIA's hard cap of $1,200. Seedance 1080p is the largest line (the tray plate): draft at 480p and complete only an
approved draft. If the tray plate fails its look test, the 3D tray replaces it and the cost drops by about $50.

### 8.3 If GEN plates fail moderation or likeness
The film already treats every view it could not measure as a guess, so each failure falls back to something the film does on
purpose:
- a frontal face plate falls back to the bust at 0°, which is the photograph and needs no model;
- a walk falls back to a backlit silhouette of the avatar;
- the tray and the hall fall back to our 3D;
- a still of him falls back to a print that is smaller, backlit or turned away.

If every GEN plate failed, the film would still play end to end in 3D, COMP and TYPE, with fewer live moments and the same
structure. No shot depends on a plate for its timing: every beat event (development, pushes, drops, captures, the window, the
type) lives in our layer.

---

## 9. Overlaps, and open questions

**Shared with treatment A (by design of the research, or by the same subject).** Measured versus inferred as the core; a
turn that reveals the unmeasured side of the head; stops built as black "P(" cards; a 30-level zoom on 16ths in chorus 2; the
Shinji chair at 100.68; four cuts on the four "just"s; a single held shot for "What did Ilya see?" with the text withdrawn; one
continuous climax shot.

**Different in kind.** A is space (a house of rooms, paper walls, an architect's drawing sheet, doors, a pull-back along an
axis) and ends on the back of his head. C is process and time (development, printing, generations, a proof sheet, a window
shaped like the photograph) and ends on his absence: an empty clip and `OK AS IS`. A's inferred register is Demand's paper;
C's is thin density and projection smear. A keeps the man mostly in the house; C lets him walk out of the pictures.

**Kept away from odyssey.** No passport page, scan line or face rising from paper into 3D; no return to the photograph at the end;
no watch, no shutter, no gold scar, no alternating aspect cuts, no Nolan vocabulary.

**Open questions for the user.**
1. Consent for shots 43 and 49 (his face retouched, and blended toward an average face) and for the projection smear (11, 48).
2. The exact Shinji post he means (shot 33 is built as "Shinji in a Chair").
3. Simplified or Traditional Chinese (default Simplified, Noto Serif SC / Noto Sans SC).
4. Whether the last line, `PROOF 1 OF 1 · ☑ OK AS IS`, stays, or the box is left unticked.

---

## 10. References added by this treatment

Well established; not re-fetched on 2026-09-28 unless marked. Film references already covered by the research pass are not
repeated.
- Michelangelo Antonioni, *Blow-Up* (1966): enlargement until the evidence dissolves into grain; the mimes' tennis with no ball;
  the photographer vanishing from the lawn.
- Eadweard Muybridge, *The Horse in Motion* (1878) and *Animal Locomotion* (1887): sequential photographs of walking bodies.
- Francis Galton, composite portraits (1878): photographic averages of faces, and the eugenic project they served; cited here as a
  warning about the prior, not as a method.
- Alvin Lucier, *I Am Sitting in a Room* (1969): recursion until only the room remains.
- I. Shumailov et al., "AI models collapse when trained on recursively generated data", *Nature* 631, 755-759, published
  2024-07-24 (checked at nature.com on 2026-09-28).
- Thomas Ruff, *Portraits* (large format from 1986): the frontal, flat, passport-like portrait as monument.
- Christian Boltanski, the *Monuments* (from the mid-1980s): rephotographed faces lit by small lamps.
- Anna Atkins, cyanotype photograms (1843), after John Herschel's cyanotype process (1842).
- Dinh Q. Lê, woven photographs (from the late 1980s).
- Magnum-style contact sheets marked in grease pencil: the editor's choice as a visible act.
- The safelight coin test, push-processing, tray agitation, dodging and burning: standard darkroom practice.
- John von Neumann, *Theory of Self-Reproducing Automata* (ed. A. W. Burks, 1966).
- Executive Order 14110 (signed 2023-10-30, revoked 2025-01-20) and the EU AI Act's 10^25 FLOP presumption.
- Dated HUD facts otherwise come from the research tables (lyric_concepts.json, the philosophy report section 7, REFERENCE.md,
  GENMEDIA.md), each with its date and source there.
