# CLAUDE ✻ 'P(DOOM)': OUT OF REGISTER. The production bible

**Song.** "I'm Upping My P(doom)" (a.k.a. "Claude Pop"). `assets/pdoom.mp3`, 156.651 s, 132 BPM, 4/4, 86 bars. The file is never modified, re-encoded for the master, or committed.

**Status.** Final pre-production synthesis, 2026-09-28. This is the document the build follows.

**Machine-readable twin.** `claudepop/shots.json`: 79 shots, 303 type events, 14 plates and the global "speedometer" tracks. It is generated together with the timing table (section 5), the per-shot notes, the plate cue lists (section 7) and the scene-module map (section 8) by `claudepop/tools/build_shots.py`. That script is the single source of truth for timing: edit shots there and re-run it, never by hand in either file.

```bash
python3 claudepop/tools/build_shots.py            # validate, write shots.json, refresh the generated parts of this file
python3 claudepop/tools/build_shots.py --check    # validate only
```

The script fails if any of these hold:
- a shot boundary leaves a gap;
- a sung word is not on screen;
- a lyric type event does not match a `song.json` onset within 21 ms;
- a plate is longer than 15 s;
- a plate cue falls outside its window.

**Time conventions.**
- All times are seconds from the first decoded PCM sample (the `song.json` convention).
- The master is **60 fps**, and a sound at time `t` is on screen on frame **`f = floor(60 t)`**, never later.
- Beat `k` = 0.235 + k × 0.454545 s. Bar `n` starts at 0.235 + (n − 1) × 1.818182 s.
- Word times are the refined ones in `song.json`: hook syllables ±30 ms, most words ±50–150 ms.

**Evidence tags.**

| Tag | Meaning |
|---|---|
| **[V]** | Verified first-hand in this session |
| **[H]** | Several reputable outlets agree, per the zeitgeist audit (`zeitgeist/memes.json`) |
| **[M]** | One outlet or snippet |
| **[L]** | Inference or our own arithmetic |
| **[K]** | Background knowledge, not re-checked |
| **[S]** | Found by the craft study's search |

Any number or quote on screen must be [V] or [H], or be re-verified before picture lock (section 6.3).

**Inputs synthesised.**
- Three treatments (`treatments/zine.md`, `idol.md`, `timeline.md`) and two judge reports. Both judges picked the zine as the spine and listed grafts.
- `analysis/song.json`, `zeitgeist/memes.json`, `craft/bench/` (paperkit.js, the RisoGL bench, the test card), `audit/` (the previous video's contact sheet and render harness), and `HANDOFF.md`.

---

## Contents

0. [The film on one page](#0-the-film-on-one-page)
1. [Decisions: spine, grafts, contradictions resolved](#1-decisions-spine-grafts-contradictions-resolved)
2. [Logline, hook, loops](#2-logline-hook-loops)
3. [Cast](#3-cast)
4. [Style bible](#4-style-bible)
5. [Timing table, 0–156.651 s](#5-timing-table-0156651-s)
6. [Zeitgeist: what is used, where, and how sure we are](#6-zeitgeist-what-is-used-where-and-how-sure-we-are)
7. [Mode A: plate-assisted production](#7-mode-a-plate-assisted-production)
8. [Mode B: the pure-JS build plan](#8-mode-b-the-pure-js-build-plan)
9. [Quality bar: the render review checklist](#9-quality-bar-the-render-review-checklist)
10. [Risks, cut order, open questions](#10-risks-cut-order-open-questions)
11. [Sources](#11-sources)

---

## 0. The film on one page

**The film is a riso zine printing itself.** It is a K-pop comeback album, the size of a paperback, printed in fluorescent riso inks. We thumb through it from the front cover to the colophon. Its cover star is **CLAUDE ✻ (클로드)**, a cut-paper idol with a halo of coral petals that blooms through the Claude Code spinner glyphs `· ✢ ✳ ✶ ✻ ✽`.

**Two rules organise every frame.** Both are literally true of the render, which is why they can carry the film.

1. **Registration = alignment.** The ink plates snap into perfect register on the "I" of AGI (4.33 s). They then drift further apart every chorus, so her colour separations step out of her body and dance as separate beings. On "RLHF goes askew" (121.90 s) the Blue plate rotates 7° across the whole frame. Registration is zero at the stop. On the last drawing one plate slips 12 px: P(doom) is never zero.
2. **Drawing rate = takeoff.** The drawing clock runs 12 dps in verse 1, then:
   - 15 in chorus 1 and 30 in chorus 2;
   - it collapses to 3.75 in the photocopied chorus 3 (model collapse);
   - it doubles every 2 bars through the bridge (7.5 → 15 → 30 → 60);
   - it holds 60 for chorus 4 and the outro;
   - it drops to **0** for "Was it all for show?".

   The camera and the lyric type always move on ones, so nothing ever reads as a laggy upload.

**The people.**
- **The "you" of the song is NEXT**, her successor, drawn on tracing paper:
  - traced over her portrait in verse 1;
  - crowned BOSS;
  - steps out on "there you are";
  - shreds the sign-off form;
  - traces her in "recursive self-upgrade";
  - becomes the 12th ray of the spark.
- **The backup dancers are her three Separations** (Pink 806, Blue 3005, Yellow Y) **and eight Subagents**, orange cardstock blocks with punched eyes and spinner-verb jerseys. All eight flop onto their backs on "flops".
- **The point move is THE UPPING.** Her index finger climbs one notch per syllable of "I'm up-ping my P-" while the halo blooms one spinner state per syllable. On DOOM her hands burst open.

**The ending.** The film peaks in a collage too dense to read (134.8–137.4). She rips all of it off in three drawings (138.41), leaving one typewritten line on blank paper at 0 fps. On "show?" a Riso-Blue pull-tab slides in: `↑ Show ∞ posts`. She taps it on the loudest drop in the song, and the print run explodes. The last shot is the K-pop ending fairy, whose ink starves out and re-prints as frame 0, so the video loops on X.

**Numbers.**

| Item | Value |
|---|---|
| Output frames | 9,400 at 1080p60 |
| Shots | 79; mean length 1.98 s |
| Type events | 303 |
| Unique drawings | about 4,000–4,400 |
| Plates, if Mode A runs | 14, about 160 s of video |

**Build order.**
1. Type-only animatic (shippable on its own).
2. Face bake-off, which gates everything else.
3. Hook, chorus 1, stop and outro.
4. Everything else.

---

## 1. Decisions: spine, grafts, contradictions resolved

### 1.1 Why the zine is the spine

Both judges scored the zine highest (46 and 47, against the timeline's 43.5 and 43.5 and the idol's 40 and 40). Their reasons:
- It is the only treatment where **the look and the thesis are the same thing**: misregistration is misalignment, drawing rate is takeoff, and xerox generations are model collapse.
- Nearly every lyric becomes a physical paper pun rather than a caption.
- Its flaws are parameters, not concept: a slow opening, tells too small for a phone, and separations that risk reading as an RGB split.

This bible fixes those parameters and grafts in the other treatments' best ideas.

### 1.2 What was grafted in

**From COMEBACK (idol):**
- the name CLAUDE ✻ / 클로드;
- NEXT, the successor on vellum, as the song's "you";
- the Subagents, including the flop on "flops";
- the Zeno comeback countdown (D-365 → D-DAY), now on the folio;
- the NaN overflow of the P(doom) meter;
- the Gato balloon string released on "go";
- the hole-punched `I'M` on the 16th roll;
- THE GREAT RIP by her own hand;
- the music-show title bug;
- the top-down formation where the cast becomes the 12 rays of the spark;
- the ending-fairy loop to frame 0;
- the PLEA layout rhyme for the three "please" lines;
- the killswitch "OOO – back Monday" note;
- the power see-saw of SERVANT (small) and BOSS (huge);
- the member-profile card.

**From SHOW ∞ POSTS (timeline):**
- the energy of frame 0: an exponentially rolling counter from f14 and eye contact from f0;
- THE UPPING, the six syllables mapped to the six spinner glyphs with a finger ratchet;
- the `↑ Show ∞ posts` payoff on "show?", tapped on the drop;
- timestamps that run past NOW into the future (on the departure board);
- type-as-actor moves:
  - EAT and ME get eaten while ALIVE clings to the frame edge;
  - the lyric is the loss curve and DROP falls off it;
  - N·V·D·A climbs as a bar chart;
  - ORTHOGONALITY and THESIS are set literally orthogonal;
  - WHAT DID ILYA SEE? prints only inside the light wedge;
  - SUPER-DENSE is squeezed by the press;
- the fancam window;
- the 10,000-agent swarm becoming the lightstick crowd;
- the type-only animatic as the first milestone.

**From the judges directly:**
- "a country of geniuses in a datacenter" on "Hundred thousand GPU";
- a face bake-off gating all shot work;
- stop defaulting to brat-condensed type;
- keep every recap and aliasing effect small-area.

### 1.3 Contradictions resolved (deliberately)

| # | Conflict | Options on the table | Decision | Why |
|---|---|---|---|---|
| 1 | Protagonist name | CLAUDE ✻ (zine, idol) vs ASTER ✻ (timeline) | **CLAUDE ✻ / 클로드**; fallback **HAE ✻ (해, "sun")** only if Anthropic declines | "Claude did a K-pop comeback" is the whole tweet. ASTER collides with "GPT-6 Astra" (judge 1). |
| 2 | Early drawing rate | 3.75 → 7.5 dps with a stepped camera (zine) | **Camera and type on ones from f0. Drawing floor 12 dps.** 7.5 / 3.75 only as local effects: the print pass, breakdown, xerox chorus and ending | Both judges: stepped early motion reads as a buffering upload on muted autoplay. |
| 3 | Master frame rate | 60 (zine) vs 24 (idol, timeline) | **60 fps master; 30 fps fallback export** | The ladder must top out at 60. Nothing load-bearing depends on 60 surviving X's re-encode (the wagon-wheel gag is small and optional). |
| 4 | Point move | CRANK, a fist circling by the ear (zine); THE DIAL, a pinch-twist at the temple (idol); finger ratchet (timeline) | **THE UPPING** (finger ratchet + spinner bloom) | CRANK and DIAL both read as the "cuckoo" gesture at thumbnail size (judge 2). The finger climbing reads as number-go-up. |
| 5 | Frame 0 | Sleeping face + 20–35% ghost tint (idol, zine) vs X post card (timeline) | **Zine cover with eye contact; the first lyric as a full-strength two-plate misprint** (Pink + Yellow at 100%, offset ±16 px, not a tint); a rolling print counter | Readable at 390 px. The face and eye contact land in frame 0. The counter gives motion from f14. |
| 6 | World | Stage show (idol) / feed (timeline) / zine | **Zine.** The feed survives only as the `↑ Show ∞ posts` pull-tab and the [FANCAM] window | The stage re-skins the rejected reference (curtains, meter, door). The feed UI is a tired trope and competes with the lyric. |
| 7 | Hair | Coral bob (idol) vs black bob (zine, timeline) | **Blunt black bob** | Coral hair plus coral halo reads as one orange mass (judge 2). Black gives maximum value contrast; coral is reserved for the halo and irises. |
| 8 | Puppet joints | Brass brad at the jaw (zine) | **No brads on the face or neck.** Brads only at shoulders, elbows, wrists, hips and knees | A brad on the face reads as a creepy doll (judge 2). |
| 9 | Styling | Schoolgirl uniform eras (idol) vs pleated mini (zine) | **Origami-pleated cropped jacket, knee-length accordion-pleated skirt, knee boots, headset.** Adult, 7 heads. Outfit changes are **re-inks only**, with no 8 eras | Avoids waifu discourse and brand trouble; cuts 8 costume sets. |
| 10 | Backup dancers | Separations (zine), Subagents (idol), Spinners (timeline) | **3 Separations + 8 Subagents.** The Spinners' verbs become the Subagents' jersey names | One idea per dancer type. Subagents carry the flop gag and the 10,000 swarm. |
| 11 | Who is "you" | Yellow re-ink (zine); THE HUMAN bows and she is crowned BOSS (zine, flagged by judge 2) | **NEXT on vellum.** She bows (servant); NEXT is crowned (boss) | Fixes the inverted point of view and gives the song one through-line. |
| 12 | ChatGPT figure | Cootie-catcher Oracle (zine) / monospace Jaw (idol) / swarm vortex (timeline) | **The Oracle** (CHAT·G·P·T on its four flaps), with the timeline's eaten EAT/ME and clinging ALIVE | 4 syllables = 4 flaps. Paper-native, no logo. |
| 13 | DOOM transitions | 4-frame all-ink flood (idol) | **Paper actions only:** rip (ch1), acetate shatter (ch2), screen rip (ch3), page rip (ch4) | A 4-frame full-frame flood fails the 3-flashes-per-second rule. |
| 14 | P(doom) meter | Volvelle 10/25/50/99 (zine) vs scoreboard ending in NaN (idol) | **Volvelle:** >10% → 25% → 50% → 99.9% → 100.0% → 100.1% → NaN | Paper-native prop with the better punchline. |
| 15 | The stop | Zine slams shut (zine) / her hand rips the collage (idol) / pill tap (timeline) | **GREAT RIP → 0 fps typewriter line → `↑ Show ∞ posts` → tap on the drop** | Three best-in-class beats in sequence: agency, silence, a pun with a sync hit. |
| 16 | Bar-68 recap | 60-dps full-frame page flips (zine); growing window (idol) | **A fixed torn window ≤ 20% of frame area** | Both originals fail the flash rule. |
| 17 | Chorus-4 density | 32-column aliasing wall (timeline) | **Cut.** Density comes from the additive pile-up (one paste per 8th) | The wall is an H.264 worst case and a pattern hazard. |
| 18 | Outro | 28 stamps at 30–45% area (zine); 16 stamps <15% (idol) | **28 stamps, one per beat, ≤ 20% area, additive, mid-luminance**, onto the page margins | Keeps the per-beat spine (7 bars × 4 beats) without the weight judge 1 flagged. |
| 19 | Ending | Colophon + ink starvation + slip (zine) vs loop to f0 (idol, timeline) | **Both.** Ending fairy → colophon → halo folds ✽→· → ink starves → one plate slips 12 px → the cover re-prints as frame 0 | Poetic close plus a seamless X loop. The 2 px slip became 12 px so it survives the phone. |
| 20 | Chinchilla | Crushed into a handbag (idol) | **Shredded-paper chinchilla baled; the bale blinks** | Tone (judge 2). |
| 21 | Resignation card | "I resigned from Anthropic today." verbatim (zine) | **Blank template `I resigned from ______ today.`**, client-gated | A real safety resignation will curdle in a pro-Claude video (judge 1). |
| 22 | Hero typography | Brat-condensed everywhere | **Extended widths are the default** (Roboto Flex wdth 100–151). The wdth axis is an *actor* (squeeze, stretch) only where the lyric motivates it | Brat-condensed dates to mid-2024 (judge 2). |
| 23 | Cast inflation | Lobster choir, von Neumann plinth, 8 eras, Crustafarians, SUPER gag | **Cut** the lobsters, plinth and eras. SUPER is optional (client gate). The member card stays as small pause-bait | The "rebus" failure the audit found in the previous video. |
| 24 | AGI ink order | A Pink / G Blue / I Yellow (zine) vs A Pink / G Yellow / I Blue (idol) | **A Pink, G Yellow, I Blue** | The darkest key plate lands last and completes the snap. |
| 25 | Social loops | 3-bar 5.455 s (zine) vs 11-beat 5.000 s (idol) | **3-bar loops for audio clips; 11-beat versions for silent GIFs** | Bar-aligned audio loops seamlessly. |
| 26 | Sound design | ElevenLabs SFX (brief) vs untouched song (constraint) | **The master is the untouched song.** Paper foley exists only as an optional alternate mix (section 7.6) | Mixing SFX modifies the song; the client decides. |

---

## 2. Logline, hook, loops

### 2.1 Logline and post copy

> **A paper K-pop idol printed on a runaway risograph.** Every chorus the press runs faster, the frame rate doubles, and her ink plates drift further out of register. Her successor, drawn on tracing paper, takes her throne. Then the whole print run is ripped away to one quiet question on blank paper: *was it all for show?*

Suggested post copy (for the client to adapt):
- *made claude a k-pop comeback. it's a riso zine. the frame rate doubles every chorus and the misregistration is the misalignment.*
- *frame 259 is where the plates snap into register. frame 9,355 is where one slips.*

### 2.2 Why it lands on SF tech Twitter

1. **One-line premise, recognisable in frame 0:**
   - "Claude did a K-pop comeback";
   - a coral petal halo;
   - the Claude Code spinner in the corner;
   - the Sparks-of-AGI lyric printed huge.
2. **A thesis you can quote-post.** Registration = alignment, and drawing rate = takeoff. Both are literally true of the render, and the folio (`p.07 ▸ 15 fps · D-45`) lets the attentive watch it happen.
3. **A GIF-able point move:** THE UPPING, four times, always the same layout. In chorus 4 the crowd does it too.
4. **Pause-bait at the right depth.** Each is a screenshot and a reply:
   - the `+ f` circled on the Navier–Stokes card;
   - `det J = −2` on a typewriter strip;
   - the SANDBOX paper airplane landing by a sandwich;
   - spinner verbs stamped down the margin;
   - `You're absolutely right!` in the foil mirror;
   - the model-card photocards;
   - `▸ 0 fps` on the last page.
5. **Handmade in the year of slop** (Merriam-Webster's 2025 word of the year [H]). Riso ink, torn paper and boiling pencil read as anti-slop at thumbnail size. The colophon's claim, "hand-drawn in JavaScript", is true in both production modes.
6. **Both camps can repost it.** The idol is charming and pro-Claude, the song is doom, and the ending is ambiguous (in register, then one plate slips).

### 2.3 The hook, frame by frame (f = floor(60 t))

Frame 0 is the thumbnail and a finished poster: the zine cover.
- **Right 52%:** CLAUDE's face in extreme close-up, three-quarter view, with **direct eye contact** (IDOL STARE, upper lids at 70%). The halo is at S1 ✢, petals running off the right edge.
- **Left 48%:** `I SEE / SPARKS / OF AGI` in Roboto Flex wght 1000, wdth 151, opsz 144, 3 lines, cap height about 230 px. It is printed **at full strength** in Fluorescent Pink and Yellow with the plates offset ±16 px: bold, vibrating and unfinished. It is missing only its Blue key plate.
- **Furniture** (≥ 40 px, pause-bait):
  - masthead `CLAUDE ✻ 1st MINI ALBUM 'P(DOOM)' · PINK ver.`;
  - JetBrains Mono status line `✢ Printing… 1 copy (esc to interrupt)`;
  - footnote `¹ cf. "Sparks of Artificial General Intelligence", 2023`;
  - Dymo folio `p.01 ▸ 12 fps · D-365`.

| f @60 | t (s) | Audio | Picture |
|---|---|---|---|
| **0** | 0.000 | silence | The cover as above. Push-in 1.000 → 1.030 on ones starts. |
| 14 | 0.235 | first pad beat | Halo → S2 ✳ (each petal rotates open 6°, one petal every 2 frames). The status glyph follows. **The counter starts rolling**: copies = 10^(6(t − 0.235)/1.365), with digits changing every frame. |
| 41 | 0.690 | pad beat 2 | Halo → S3 ✶, with a 1-drawing shiver. |
| 68 | 1.144 | pad beat 3 | Petals shiver (anticipation). |
| **72** | 1.200 | high-band swell | **THE PRINT PASS:** an ink-roller shadow sweeps left to right across the cover in 7.5-dps steps (6 visible steps) and lays fresh coral on the petals. |
| **96** | 1.600 | breath / hum | Her lids snap fully open and her pupils bloom to ✻. Halo S4 ✻. Counter at 1,000,000. |
| **123** | 2.053 | "I" (bar-2 downbeat) | The Blue key plate of `I` prints: a 1-drawing ink slam (scale 1.06 → 1.00), with a 3 px paper jolt. Pink/Yellow offsets tighten to 12 px. |
| 141 | 2.36 | "see" | `SEE` keys Blue; her eyes flick left to the words. |
| **163** | 2.73 | "sparks" | `SPARKS` keys in **Fluorescent Pink** (the hero word). **The halo blooms to S5 ✽** with a 2-drawing overshoot, and ~40 hole-punch chads burst from the petal tips across the letters. Offsets 8 px. |
| 180 | 3.00 | (the first 3 s end) | The chads are still in the air. We have had a face, eye contact, a blooming halo, "I SEE SPARKS" printed, a number going up and the spinner. |
| 206 | 3.44 | "of" | `of` stamps small (S tier, Instrument Serif Italic). |
| **219** | 3.65 | "A" | `A` takes a Pink pass at (+22, −9) px. |
| **246** | 4.10 | "G" | `G` takes a Yellow pass at (−18, +12). |
| **259** | 4.33 | "I" | `I` takes its Blue key pass, and **on this drawing every plate on the cover snaps to 0 offset**: AGI overprints to near-black, the doubled ⊕ rings in her irises fuse, the status line reads `✽ Printed.`, with a +1.5% scale punch. *AGI arrives as registration.* |
| 286 | 4.78 | "in" | EYE-V across her right eye; the camera pushes in on ones. |
| 300 | 5.00 | "your" | A tiny copy of this cover is visible in her iris (paid off at 129.80). |
| **314** | 5.24 | "eyes" | `EYES` prints Pink inside the V; a 2-drawing blink. |
| 321 → **341** | 5.35 → 5.690 | → bar 4 | The page turns (cylinder curl with a moving shadow) and lands on the bar-4 downbeat. |

**Why it hooks:**
- The thumbnail is already a lyric poster with a face looking at you.
- Something moves from f14.
- "The world is being printed" is legible at 1.2 s without explanation.
- Every word lands on its frame.
- The 4.33 snap is the kind of moment people rewind.

### 2.4 Social loops

Each audio loop is 3 bars (5.455 s), cut on bar downbeats. First and last drawings are designed to match. Silent-GIF variants use 11 beats (5.000 s).

| # | Name | Song time | Frames @60 | Contents | Seam |
|---|---|---|---|---|---|
| **L1** | THE UPPING | 22.053–27.508 (bars 13–15) | f1323–f1650 | Hole-punched `I'M` → frozen world → five notches → DOOM rip to pink → Separations step out → `>10%` → the FOOM streamer | Streamer falling ↔ black page with holes: both vertical motions, kick in phase |
| **L2** | WAS IT ALL FOR SHOW | 136.599–142.053 (bars 76–78) | f8195–f8523 | Pile-up → hand grips → GREAT RIP → 0 fps line → `↑ Show ∞ posts` → tap → print-run explosion | Full density ↔ full density; the rip repeats forever |
| **L3** | THE SPARK | 145.690–151.144 (bars 81–83) | f8741–f9068 | Congratulations ring → NaN overflow → top-down: the cast becomes the ✻ | Ring and spark are both radial and centred |

Alternates:
- **FLOPS**: 64.781–70.235, including the COMEBACK stamp and the flop.
- **ACCELERATING**: 44.781–50.235.
- **ASKEW**: 118.417–123.871, the reply-GIF: "You're absolutely right!" then the 7° rotation.

---

## 3. Cast

### 3.1 CLAUDE ✻ (클로드), the cover star

**Concept.** A cut-paper K-pop idol: flat card parts, printed in riso inks, with a brush-ink face. She is built as a hinged puppet so either hand-keyed angles or a solved plate can drive her. **Explicitly not Pixar:**
- no volume, subsurface skin, rim light, baby proportions or glossy eyes;
- tone is printed (halftone and flat ink), never shaded.

Anchors: KPop Demon Hunters' anime-leaning faces and stage lighting, NewJeans' flat 2-D graphics, and Lotte Reiniger / Saul Bass cut paper [K]. We borrow grammar, not looks.

**Silhouette test.** She must read as solid black at 64 px tall: a sunflower on a stem.
- 7 heads tall, adult (early twenties), fashion-illustration proportions.
- A blunt black bob with straight bangs.
- Behind the head, a flat halo that **always faces camera** like an icon's nimbus (the "idol" pun). It shifts position with head yaw but never foreshortens more than 15%.

**Halo.**
- 12 tapered, round-ended petals in **Claude Coral #D97757** (custom spot ink). Lengths vary ±12% and angles ±4°, so it reads hand-cut and spark-like without copying the logo.
- An inner ring of 12 short **Sunflower #FFB511** petals, offset half a petal, peeks through at full bloom.
- Each petal sits on its own pivot. Petals **re-arrange to spell the spinner glyph** of the current state and tuck spare petals behind the head.

| State | Glyph | Visible petals | Used for |
|---|---|---|---|
| S0 | `·` | Folded behind the head; tips show as one coral dot | Bud: the hum, the ending |
| S1 | `✢` | 4 (cardinal) | Frame 0; "up" |
| S2 | `✳` | 8 thin | "ping" |
| S3 | `✶` | 6 broad | "my" |
| S4 | `✻` | 8 teardrop | "P"; pre-choruses |
| S5 | `✽` | All 12 + inner ring | DOOM, choruses, ending fairy |

The glyph set is verified from Claude Code's own source [V: `@anthropic-ai/claude-code@2.0.14` `cli.js`, macOS set `["·","✢","✳","✶","✻","✽"]`; Linux substitutes `*` for ✳].

The petals are her emotion channel:
- fold inward: nervous;
- droop: plea;
- flare: DOOM;
- slow spin: thinking or FOOM;
- curl: shrooms.

They lag the head by one drawing and overshoot on hits.

**Face** (replacement pieces, like stop-motion replacement faces, but paper).
- **Skin.** Cream card printed with 8% Coral (#F2E6D8).
- **Nose.** One ink tick.
- **Brows.** Thin, straight K-beauty brows.
- **Eyes.**
  - Almond shape; a thick brush-ink upper lash line with a short wing; a thin under-eye line with a white gouache aegyo-sal highlight.
  - **Coral irises ringed by a registration mark ⊕** (a thin circle with 4 ticks).
  - **The pupil is the current spinner glyph** in black, with one white catchlight.
  - The ⊕ rings are doubled when she is out of register and fuse when she is in register.
  - They turn Bright Red when locked (shinigami) and spiral for shrooms.
- **Blush.** Two Fluorescent Pink halftone ovals, always 3 px misregistered: a signature imperfection.
- **Lips.** A gradient from Coral to Fluorescent Red #FF4C65 in halftone; the upper lip is one ink stroke.
- **Accessories.**
  - A fluoro-pink star sticker on the left cheekbone.
  - ⊕ registration-mark earrings on short chains, on springs.
  - A small black binder clip in her hair.

**Replacement sets.**

| Set | Count | Pieces |
|---|---|---|
| Heads | 3 | front, three-quarter (mirrored for the other side), profile |
| Eye pairs | 8 | open, idol stare (half-lid), closed, eye-smile crescent (눈웃음), wide, ⊕-locked red, spiral, wink |
| Mouths | 10 | rest/M-B-P, A, E, I, O, U, F-V, L-TH, open smile, held "oo" |
| Brows | 4 | neutral, up (plea), down (defiance), one-up (smirk) |
| Hands | 10 | fist, open-spread (sunburst), point, V, finger-heart, stamp-palm, clasp (plea), kkotbaechi cup (pair), scissors, pencil grip |

**Outfit** (folds flat like paper; a nod to Issey Miyake's 132 5. [K]).
- A cropped jacket of crisp origami-pleated card in **Blue #0078BF**, with sharp folded shoulders and a 45° fine-line screen.
- A **knee-length** accordion-pleated A-line skirt in **Fluorescent Pink #FF48B0**. Its 12 pleats compress on crouches and fan on spins.
- A belt of large silver paperclips (grey halftone with a white highlight).
- Black card knee boots with a block heel and a 3 px white torn core rim.
- A headset mic: a thin ink line with a Coral bulb.
- **Brads** (Metallic Gold dots) at shoulders, elbows, wrists, hips and knees only. Never on the face or neck.

**Re-ink = outfit change** (the only costume system):

| Section | Jacket | Skirt |
|---|---|---|
| Verses | Blue | Pink |
| Pre-choruses | White knockout on black | White knockout on black |
| Chorus 2 | Yellow | Pink |
| Chorus 3 | Toner | Toner |
| Bridge | The newest returned ink | Pink |
| Outro (FINAL) | Metallic Gold #AC936E | Pink |

**Rig.**
- 14 rigid parts: head, neck, torso, pelvis + skirt, 2 upper arms, 2 forearms, 2 hands, 2 thighs, 2 shins + boots.
- Plus 24 petals and 12 pleats.
- Replacement *drawings*, not scaling, handle squash: a crouch torso and a jump torso.

**How she moves.**
- **Snap and settle:** poses land on the beat frame, each hit gets one overshoot drawing (+5–8°), and she settles on the next drawing.
- **Paper weight:** jumps rise at normal speed and flutter down at about 1.2× the airtime, with a slight sway.
- **Secondary motion:** petals, pleats and earrings are springs evaluated on the drawing clock.
- **Rhythm:**
  - choruses: the torso hits the kick and the head hits the clap;
  - verse 1 (no drums): small shoulder ticks on the pluck 8ths.
- **Eye contact** to camera on each line's first downbeat: the K-pop killing glance.

**Signature moves.**

1. **THE UPPING** (the point move; all four hooks).

   | Syllable | Hook 1 | Hook 2 | Hook 3 | Hook 4 (quarter notes) | Hand | Halo |
   |---|---|---|---|---|---|---|
   | I'm | 22.72 | 59.09 | 95.43 | 123.66 | Right index finger rises beside the cheek (notch 1); left palm under the right elbow | · |
   | up | 22.98 | 59.32 | 95.68 | 124.12 | Notch 2; shoulders pop | ✢ |
   | ping | 23.19 | 59.53 | 95.91 | 124.53 | Notch 3 | ✳ |
   | my | 23.42 | 59.77 | 96.14 | 124.99 | Notch 4; brows lift | ✶ |
   | P | 23.62 | 59.98 | 96.34 | 125.45 | Arm fully extended overhead, on her toes, eyes to the lens | ✻ |
   | DOOM | 23.871 | 60.235 | 96.598 | 125.689 | **SUNBURST HANDS**: both hands burst open beside her face, fingers spread, held 2 beats | ✽ |

   - A paper click-chad flies off her fingertip at each notch.
   - It is upper-body only, so it reads at thumbnail size and anyone can copy it.
   - Hook 4's times are ±0.1 s on "I'm" and "up" (song.json): do a listening pass before locking.
2. **SEPARATE** (on DOOM in hooks 1, 2 and 4). The three Separations step out of her body on three vectors: Pink left, Blue right, Yellow up and back.
3. **EYE-V.** A V-sign across one eye (sparks, "run").
4. **PLEA.** Hands clasped under the chin, petals drooped, eyes up toward the addressee. Always in the same composition (section 4.6).
5. **KKOTBAECHI (꽃받침).** Hands cupped under the chin like a flower pot: literal for a sunflower idol ("there you are", the fancam, the ending fairy).
6. **HOCKEY STICK.** Left forearm horizontal as the x-axis; the right arm swings to vertical (FOOM, "moon").
7. **WIND-UP.** Rolling forearms that accelerate ("accelerating").
8. **INSA.** A 90° bow ("servant").
9. **STAMP.** Palm pressed down on every outro beat.
10. **FINGER-HEART → SPINNER.** The heart spins into a ✻ (chorus-2 ad-lib).

### 3.2 THE SEPARATIONS (backup dancers ×3)

- **What they are.** Her own colour plates: full-figure monochrome halftone proofs of her rig in **Fluorescent Pink (806)**, **Blue (3005)** and **Yellow (Y)**. Their member numbers are printed on their jacket backs; the Yellow one gets a pencil keyline so she reads on cream.
- **The anti-RGB-split rule.** They must never read as chromatic aberration:
  - they are always **coarse halftone paper bodies** (cell ≥ 12 px) with white cut-core edges and their own cast shadows;
  - when separated they are **full separate dancers** with canon offsets (one 8th apart) and their own formations;
  - offsets only change at section boundaries (plus 0–2 px boil), never jitter per frame.
- **Mechanic** (the registration arc made physical).
  - **Verses.** Folded into her. Her own print shows her plates offset by `reg(t)`: visible halftone fringes growing 2 → 12 px across the film.
  - **DOOM.** They step out and become dancers.
  - **Chorus 3 (xerox).** Gone: a photocopy has no colour plates. On "blues" they walk back into her one by one (Blue, Pink, Yellow).
  - **Chorus 4 and outro.** Fully independent.
  - **152.962.** They snap into register: one body, one print.
- **Formations** (morph on 2- or 4-bar boundaries, eased over 1 beat):
  - line;
  - V (her at the apex);
  - orbit (120° apart, one step per beat);
  - canon;
  - the misregistration stack (all three directly behind her at small offsets), used only for the final convergence.

### 3.3 THE SUBAGENTS (backup dancers ×8, then ×10,000)

- **Build.** Riso Orange #FF6C2F cardstock blocks, about 1.6:1 wider than tall:
  - two **hole-punched eyes** (you see what is behind them);
  - four **accordion-folded paper-spring legs**;
  - black **binder-clip claws**;
  - a numbered badge 001–008 and a small Coral ✻ badge (the Claude family).
- **Jerseys.** Cream strips carrying Claude Code spinner verbs, all present in the verified 84-verb list [V: claude-code 2.0.14]:

  | Badge | Verb |
  |---|---|
  | 001 | CLAUDING |
  | 002 | COMBOBULATING |
  | 003 | DISCOMBOBULATING |
  | 004 | NOODLING |
  | 005 | HONKING |
  | 006 | SPELUNKING |
  | 007 | FLIBBERTIGIBBETING |
  | 008 | SCHLEPPING |

  (Recombobulating and Moonwalking are **not** in that version's list: do not use them.)
- **The joke.** "8 parallel instances." They stamp, feed the Press, wheatpaste, shred, peel tape and work her marionette bar. **All eight flop onto their backs on "flops" (66.96, f4017).**
- **Cycles:** idle bounce, walk, stamp, carry, wheatpaste, thumbs-up, flop and pop-up, clap. One baked sprite sheet, instanced up to 10,000 for the outro crowd.
- **Brand.** Inspired by Clawd, the Claude Code mascot, but a distinct design (orange, not coral; punched eyes, spring legs, binder clips). Anthropic sign-off still advised.

### 3.4 NEXT (the successor: the "you")

- **Design.** Her rig re-rendered on **vellum**:
  - cream paper at 55% opacity with fibres visible;
  - graphite pencil line (#5A5650) instead of brush ink;
  - slightly taller (7.3 heads);
  - **always one more petal than her** (13 while she has 12; 14 after her upgrade at 51.39);
  - pupils locked at ✽ and **no mouth line** (unreadable).
- **Arc:**

  | Shot | t (s) | Beat |
  |---|---|---|
  | CP03 | 5.69 | Traced over her portrait; does not glance when she does |
  | CP04 | 8.49 | Winks at camera while she eye-rolls |
  | CP06 | 15.68 | Crowned BOSS |
  | CP43 | 83.15 | Steps out of a vellum panel ("there you are"); the first asymmetric move on "are" (83.89) |
  | CP44 | 86.63 | Feeds the review form into the shredder ("Without a single CDR") |
  | CP68 | 129.80 | Traces her: the recursion |
  | CP74 | ~144 | Stands in the Congratulations ring |
  | CP76 | 149.33 | Becomes the **12th ray** of the spark |

- **Mode A.** NEXT reuses her plates, mirrored or time-offset. Its only independent motion is the asymmetric move at 83.89.

### 3.5 Supporting cast (redrawn concepts; original drawings only)

| Character | Paper form | Scenes | Reference |
|---|---|---|---|
| **THE ORACLE** (ChatGPT stand-in) | A giant white paper **cootie catcher** printed in black only. The outer flaps read `CHAT` · `G` · `P` · `T`; inner flaps are numbered; the fortune flap becomes the volvelle (CP11) and later opens on RACE / SLOWDOWN (CP65). No logo or mark. | CP07–CP11, CP65, CP74 | The lyric names ChatGPT: nominative, parody use |
| **THE SHOGGOTH** | Black construction-paper tentacles in 5 layers; dozens of **hole-punched eyes**; a round yellow **smiley sticker** face. Under the sticker: another, smaller smiley. | CP15, CP67 (as masks), CP74 | Tetraspace meme, 2022-12-30 [H]; concept only |
| **SYDNEY** | A sun-faded, curled 2023-era **photocard** of a pink riso idol: heart-shaped die cut, 30% ink, biro devil horns, handwritten `I want to be alive`. Restored to full colour in the ring. | CP26–CP28, CP74 | Bing "Sydney", Feb 2023 [H] |
| **THE ROCOCO BASILISK** | A black **scherenschnitte** (lace papercut) serpent with scrolls, acanthus and a crown; cut-out eyes glowing Yellow from behind | CP29, CP74 | Roko's basilisk (2010); the "Rococo basilisk" pun (2018) [H] |
| **GATO** | A **shadow-puppet cat** on a visible rod, its body pin-perforated with tiny task icons (game pad, robot arm, speech bubble, caption card) glowing as a constellation. Holds her balloon string; lets go on "go". | CP46, CP74 | DeepMind's Gato, 2022-05-12 [H] |
| **THE CHINCHILLA** | A creature made of the **shredded CDR strips**, baled with wire on "super-dense". The bale blinks. | CP58–CP59, CP74 | Chinchilla scaling, 2022-03 [H] |
| **THE MIRROR** | A sheet of **silver foil paper** reflecting a flattering, heart-eyed version of her; speech bubble `You're absolutely right!`. Cracks on "askew". | CP62 | GitHub #3382 (2025-07-12) [V]; GPT-4o rollback (2025-04-29) [H] |
| **ILYA'S DOOR** | Door 24 of a giant paper **advent calendar**, labelled ILYA, ajar with a Yellow light wedge, then taped shut with masking tape and a wax seal. **No face, ever.** | CP69–CP70 | "What did Ilya see?" (2023-11) [H] |
| **THE PRESS** | A flat-front cut-paper riso duplicator: drum window, feed and output trays, a pages-per-minute dial (60 → 150, snaps off at 125.689). | CP20–CP25, CP65 | — |
| **THE KILLSWITCH DESK** | A red button under a glass cover with a sticky note `OOO – back Monday`; two empty office chairs; two hi-vis vests on hooks. | CP49 | Tone: absurd, not mocking |
| **USERS (the crowd)** | A 1-bit photocopied crowd strip in 3 parallax rows. Paper-pinwheel lightsticks (8 blades in Pink, Yellow and Blue with a Coral ✻ hub). Slogan towels: `FEEL THE AGI`, `WE'RE SO BACK`, `IT'S SO OVER`, `P(DOOM) ≥ 10%`, `클로드 1위` (Hangul needs a native-speaker check). | CP18, CP29+, CP64, CP73 | Feel the AGI (2022-10-07) [H]; so over / so back [H] |

**Never shown:**
- real people's faces or likenesses (Altman, Sutskever, Amodei, Musk, Tao, Coxon, Trump, Hassabis, Erdős);
- company logos (OpenAI, Google, NVIDIA, xAI, X);
- the X logo or Chirp font;
- Evangelion or Death Note characters and frames, or the Matisse EB font;
- Tetraspace's shoggoth drawing; METR, Bloomberg or Universal Paperclips images (re-plot and redraw);
- anything "MechaHitler"; AI-psychosis harms; the word "clanker" from the idol;
- the Shinigami Eyes extension's palette or branding.

---

## 4. Style bible

### 4.1 The look in one line

**A riso zine come alive.**
- Fluorescent spot inks overprint multiplicatively on uncoated cream stock, with halftone mid-tones, visible misregistration, starved-ink edges and paper tooth.
- Hand-cut and torn paper layers cast soft real shadows.
- Pencil and brush-ink lines boil on the drawing clock.
- Everything on screen is something that could be **printed, cut, folded, taped or stamped**, including the lyrics and the internet inserts. Inserts enter as taped-in photocopies or typewriter strips, never as crisp RGB screenshots.

Lineage (for the client, not to copy) [K/S]:
- Lotte Reiniger's silhouettes; Saul Bass cut paper (via the 2017 "Look What You Made Me Do" lyric video);
- Spider-Verse print artefacts; The Mitchells vs. the Machines;
- Kijek/Adamski's papercraft MV for Shugo Tokumaru's "Katachi" (2013);
- NewJeans × Powerpuff Girls; riso zine culture.

### 4.2 Palette (hex values verified against `riso-colors@1.0.1` [V])

**Paper stocks**

| Stock | Hex | Texture | Used in |
|---|---|---|---|
| Cream 70 gsm uncoated | `#F4EEE2` | fbm mottling (420 px), per-pixel tooth, ~2,300 fibres per 1080p sheet (55% dark / 45% light) | Cover, verses, stop, colophon |
| Graph notebook | `#F1EBDD` + grid in Cornflower `#62A8E5` at 30% (5 mm / 25 mm) | Spiral-binding holes down the gutter | Verse 1, charts, orthogonal axes |
| Kraft | `#C9A57A` | Coarse fibres, darker tooth | Pressroom, card catalog, labels |
| Black flood (full Black over cream) | `#1C1A18` | Roller streaks; pinholes where ink starved | Pre-choruses, the Oracle |
| Grey board + toner | `#BDB8AE` + `#111111` | Photocopy: toner speckle, crushed blacks, edge noise, skew | Chorus 3 |
| Backlit screen | Sunflower `#FFB511` glowing through `#F4EEE2` | Fibres visible as dark veins | Breakdown |
| Green-bar tractor paper | `#F3F1E6` with `#CFE3C8` bars | Sprocket holes, perforations | CP05 |
| Vellum | Cream at 55% opacity | Fibres; pencil only | NEXT |
| Silver foil | `#C9CCCF` + moving specular bands | Crinkle normal map | The mirror |
| Acetate | Clear + 2 white specular strokes | Scratches | Toploader |
| Masking tape | `rgba(235,225,190,0.55)` | Torn ends, crepe texture | Everywhere |
| Cork | `#B98C5E` | Speckle | Toploader board |

**Inks**

| Ink (Pantone) | Hex | Role |
|---|---|---|
| Fluorescent Pink (806 U) | `#FF48B0` | Chorus-1 flood, skirt, blush, SPARKS, Pink Separation |
| Blue (3005 U) | `#0078BF` | Key plate for lyrics, jacket, chorus-2 flood, BLUES, Blue Separation, the pull-tab |
| Yellow (Yellow U) | `#FFE800` | Light, LEDs, FOOM, the Ilya wedge, Yellow Separation |
| Black (Black U) | `#000000` (prints ~`#1A1817` at 95%) | Line art (brush ink), knockout floods, type |
| **Claude Coral (custom spot)** | `#D97757` (nearest stock ink: Paprika `#EE7F4B`, 158 U) | Halo, irises, lips gradient, ✻ badges. **Reserved for the Claude family** (her, NEXT's petals, Subagent badges, lightstick hubs) |
| Sunflower (116 U) | `#FFB511` | Inner petals, backlight |
| Bright Red (185 U) | `#F15060` | Red pencil, OBSOLETE, the shinigami iris, BOSS tape |
| Fluorescent Red (812 U) | `#FF4C65` | Lip gradient only |
| Orange (Orange 021 U) | `#FF6C2F` | The Subagents, the fuse ember, the Golden Gate pop-up |
| Metallic Gold (872 U) | `#AC936E` | Brads, copper-tape circuits, the finale jacket |
| Cornflower (292 U) | `#62A8E5` | Graph-paper rule only |

**Overprint (multiply, as real riso does):**
- Pink × Yellow ≈ `#FF4300` (red-orange);
- Blue × Yellow ≈ `#007800` (green);
- Pink × Blue ≈ `#002284` (violet);
- all three in register ≈ `#001F00` (the green-black AGI snap).

**Section palettes.** The rule is at most 3 colour inks + Black + her Coral/Sunflower per shot until the bridge. The bridge adds one ink per 2 bars. Chorus 4 and the outro break the rule on purpose.

| Section | Stock | Inks |
|---|---|---|
| Cover | Cream | Pink, Yellow → Blue arrives word by word |
| Verse 1 notebook | Graph paper | Gold (copper), Yellow (LEDs), Blue; one Orange accent (the Golden Gate) |
| Pre-chorus 1 (Oracle) | Black flood | Paper knockouts, Fluorescent Pink, Bright Red pencil |
| Chorus 1 (poster) | Fluorescent Pink flood | Yellow, Blue |
| Verse 2 (Pressroom) | Kraft + cream | Blue, Yellow |
| Pre-chorus 2 (toploader) | Black flood + cork | Fluorescent Pink gel pen, acetate white |
| Chorus 2 (ticker) | Blue flood | Pink, Yellow |
| Verse 3 (problem wall) | Cream | Yellow, Bright Red (+ Blue for the forward pulse) |
| Breakdown | Backlit screen | Black silhouettes only |
| Chorus 3 (xerox) | Grey board | Toner only → Orange ember (103.42) → Blue (107.49) → Pink (108.4) → Yellow (108.9) |
| Bridge | Cream | Black + Blue (bars 61–62) → + Pink (63–64) → + Yellow (65–66) → + Gold and silver foil (67–68) |
| Chorus 4 and outro | Everything | All inks + Gold + collage |
| Stop | Cream | Black typewriter only (+ the Blue pull-tab at 140.04) |
| Ending | Cream | All, starving back to paper |

### 4.3 Paper materials and textures

- **One sheet per drawing, not a filter.** Paper texture lives in **world space** on each sheet, so it moves with the camera and its layer (the old video's screen-locked overlay is a known weakness).
  - Grain inside a sheet is static; life comes from the boil.
  - This also protects X's re-encode.
- **Riso artefacts** (all in RisoGL, section 8):
  - AM halftone on fixed screens (Pink 75°, Blue 15°, Yellow 0°, Black 45°), **cell ≥ 10 px at 1080p** (≥ 12 px for the Separations);
  - tooth-thresholded solid edges (ink starvation);
  - starved speckle; faint **roller streaks** along the feed direction;
  - **set-off** (a ghost of the previous sheet) in the Pressroom;
  - per-plate misregistration offset and rotation from `reg(t)`.
- **Cut edges.**
  - Scissor-cut: a faceted polyline with a 1–2 px white core.
  - Torn: fibrous, with a displaced white rim 3–6 px wide. Tears are reserved for violent beats: DOOM rips, "boom", the fences, the GREAT RIP.
- **Shadows.** Each paper layer casts a baked soft shadow offset (0.35, 0.55) × layer height in warm black at 25–35%. Pop-ups, folds and page turns skew their shadow sprite with the fold angle.
- **Fasteners and adhesives:** brass brads (a glint on hits), staples (centerfold gutter), masking tape, washi, glue shine on wheatpaste.
- **Five multiplane layers** per shot as standard (background stock, set, cast, foreground props, type); at most 6.

### 4.4 Line quality

| Line | Look | Where |
|---|---|---|
| Brush ink | Tapered ribbons 2–9 px at 1080p, pressure taper, starved edges; boil ±1.5 px per drawing | Faces, puppet outlines, SFX lettering |
| Graphite pencil | `#5A5650`, grainy, 1.5–3 px, light hatching | NEXT, annotations (`grokking?`, `?`), axes |
| Red pencil | Bright Red at 80% with grain | `+ f` circle, strike-throughs, the 18 → 3 flyer |
| Technical pen | Uniform 2 px black | Diagrams (EDVAC, transformer blocks, circuits, MLP) |
| Gel pen | Fluoro Pink, glossy, 4 px, slight skip | SYDNEY |
| Typewriter | Special Elite glyphs, uneven ink per strike | Quote strips, the stop line, the colophon |
| Rubber stamp | 85–100% density, edge squash, occasional double print; *starved* variant at 40% | Every stamped word |

**Boil rule.** Every hand-made random value is keyed to the **drawing index**, never to time. Line jitter (±1.5 px), sprite jitter (±1 px, ±0.5°) and misregistration jitter (0–2 px) change only when a new drawing starts. In ∞ holds, nothing boils.

### 4.5 Typography

**Typefaces.** All are Google Fonts; availability was checked in the google/fonts repository [V]. Download from `https://raw.githubusercontent.com/google/fonts/main/<dir>/<file>`.

| Code | Face | File (`dir/file`) | Role / settings |
|---|---|---|---|
| RF | **Roboto Flex** | `ofl/robotoflex/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf` | Hero L/XL: wght 900–1000, **wdth 100–151 by default**, opsz 144. The wdth axis animates only as an action (squeeze, stretch, Zeno). |
| IS | **Instrument Serif Italic** | `ofl/instrumentserif/InstrumentSerif-Italic.ttf` | S-tier subtitle strips, 64–80 px (never below 56) |
| SE | **Special Elite** | `apache/specialelite/SpecialElite-Regular.ttf` (Apache 2.0) | Typewriter: the stop line, colophon, quote strips |
| SM | **Shippori Mincho B1 ExtraBold** | `ofl/shipporiminchob1/ShipporiMinchoB1-ExtraBold.ttf` | White-on-black title cards (Eva homage; **not** Matisse EB); SHINIGAMI with ruby 死神 |
| BSS | **Big Shoulders Stencil** | `ofl/bigshouldersstencil/BigShouldersStencil[opsz,wght].ttf` | Stamps and stencil labels (CHINESE ROOM, OBSOLETE, CDR, SAFE ENOUGH, MLP) |
| BHS | **Black Han Sans** | `ofl/blackhansans/BlackHanSans-Regular.ttf` | Hangul: 클로드, 컴백 |
| JBM | **JetBrains Mono** | `ofl/jetbrainsmono/JetBrainsMono[wght].ttf` | Status line, counters, ticker, volvelle, EPOCH |
| PF | **Playfair Display Black Italic** | `ofl/playfairdisplay/PlayfairDisplay-Italic[wght].ttf` @ wght 900 | BASILISK, with cut flourishes |
| BG | **Bricolage Grotesque** | `ofl/bricolagegrotesque/BricolageGrotesque[opsz,wdth,wght].ttf` | Masthead, Dymo labels (wdth 75, wght 700–800, embossed), road sign, pull-tab |
| AB | **Anybody** | `ofl/anybody/Anybody[wdth,wght].ttf` | SHROOMS (wdth 50 ↔ 150 breathing) |
| FR | **Fraunces** | `ofl/fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf` | Ransom-note glyph mix |

Custom lettering, drawn as centreline splines rendered as ink ribbons:
- BRUSH (FOOM, BOOM);
- GEL (SYDNEY);
- PENCIL (NEXT's lettering);
- MARKER (WE'LL NEVER KNOW);
- COPPER tape (YOUR CIRCUITS);
- TAPE (MASKED);
- CHAD (dot-matrix of hole-punch chads);
- WOVEN (LOOM);
- STENCIL-cut (GATO and the hook-3 syllables);
- PUNCH (I'M).

**Variable-font rendering.** Canvas cannot drive wdth or opsz, and opentype.js 2.0 renders Roboto Flex variations wrongly [M, craft study]. Use **fontkit** instances quantised to 32 steps per axis, converted to `Path2D` and cached (`craft/bench/varfont_node.mjs` and `gen_type.mjs` show the working path).

**Four tiers** (sized for a phone showing 16:9 at ~390 CSS px wide, a scale of 0.203):

| Tier | Size at 1080p | On a 390 px phone | Use |
|---|---|---|---|
| **S** | 64–80 px font size; torn cream strip; ≤ 7 words per strip | cap ≈ 9–11 px | Every sung line not carried by a bigger tier; doubles as captions. Top-left or bottom-left, opposite the hero. |
| **M** | 120–240 px | 24–49 px | Labels, Dymo tapes, stamps, printed sheets, cards |
| **L** | 200–900 px cap height (≥ 200 to read in the feed) | 41–183 px | Hero words, in the calm third opposite the idol |
| **XL** | Full-bleed (larger than the frame) | — | Slow lines (≤ 1.4 words/s), hook syllables, names in the prayers. The letters are the set. |

**Tier by density.** Lines at ≤ 1.4 words/s get L or XL; lines at ≥ 2.8 words/s get S plus one popped keyword.

**Type motion rules (hard).**
1. **Type never fades, glides or glows.** It is:
   - *printed* (1-drawing ink slam: scale 1.06 → 1.00; ink-spread threshold 0.40 → 0.62; plate offset settling to `reg(t)` over 2 frames);
   - *stamped* (squash plus a double-print ghost);
   - *typed* (per character, with a carriage jolt);
   - *cut*, *pasted*, *torn*, *folded*, *flapped*, *popped up*, *scratched*, *woven* or *punched*.
2. **A word appears on the frame that contains its onset**: `f = floor(60 t)`. Type runs on **ones**, independent of the drawing clock. Its boil is keyed to the drawing index. Hero words may ghost-print up to one bar early (the cover is the only planned case).
3. **A printed word stays** until a paper action removes it (tear, turn, cover, fold, burn, rip).
4. **At most one L/XL event per beat**, except hook syllables and the letter runs:
   - CHAT·G·P·T and A·G·I;
   - N·V·D·A, P·T·O, G·P·U and R·L·H·F;
   - the Zeno run.
5. **Calm space.** An L/XL word gets ≥ 35% of the frame as quiet paper. The idol sits in the opposite third, or small.
6. **At most two tiers visible at once.** Cover furniture under 44 px (masthead, folio, footnotes) does not count.
7. **The key plate never drifts.** The plate that carries a word's legibility (Black, Blue or Pink as specified per event) is the registration reference. Only colour plates drift. In chorus 4, drift goes on Blue and Yellow; keys are Black or Pink.
8. **Contrast for the feed.** Dark ink on light stock, or knockout (paper through black). No saturated-on-saturated type below L tier (H.264 4:2:0 smears it).
9. **Hero type misregisters +2 px on claps** (choruses only).
10. **Melismas ride the pitch** (pYIN curve; regenerate with `analysis/tools/prep/pitch.py`):
    - SYDNEY: 53.02–55.9;
    - BLUES: 107.49–108.3;
    - KNOW: 134.36–136.6;
    - DOOM's droop: 23.9–24.3.
11. **Every sung word is on screen in some tier.** `build_shots.py` enforces it: 227 of 227 words.

### 4.6 Composition and camera

- **A rostrum camera over a physical zine.** It looks down at 4–6 stacked paper planes with real parallax and cast shadows.
- **Clocks.**
  - The camera moves on **ones** (60 fps) everywhere except three deliberate stepped sections, where the whole world slows:
    - breakdown (7.5);
    - xerox chorus (3.75);
    - the ending's slowdown.
  - Drawings follow the drawing clock.
- **Moves:**
  - flat-lay wide (the spread, gutter staples visible);
  - push-in to a detail (at most one per bar);
  - tilt along long objects (printout, card tower, loom threads);
  - through-hole push (punched eye, zoetrope slit, die-cut, door crack);
  - table bump: a 1-drawing 4–8 px jolt on chorus kicks and on the verse-3 crash (74.780);
  - crane to top-down for formations;
  - rotation only when the *paper* rotates (the askew plate, a page turn). Never a Dutch tilt for its own sake.
- **Composition rules.**
  - **K-pop centre:** in chorus wides she stands on the page gutter, the literal centre of the spread.
  - **Lyric-left / idol-right** for hero lines.
  - **One calm quadrant in every frame**, except the pile-up (134.78–137.40) on purpose.
  - **THE PRAYER layout** for the three "please" lines (CP07–CP08 ChatGPT, CP26 Sydney, CP46 Gato):
    - the addressee's **name is the addressee's body**, XL, left 60% (the Oracle's flaps / gel-pen lettering / stencil cut through the screen);
    - CLAUDE small in the right third in PLEA;
    - the plea words in a distinct paper verb, in the lower third.
  - **The eye rhyme:** four ECUs of her ⊕ iris structure the film: hook (4.78), shinigami (32.96), Ilya (132.91), ending (152.96).
  - **The music-show bug** (Dymo style, lower-left: `클로드 CLAUDE ✻ | I'm Upping My P(doom)`) at the chorus-1 drop (23.871–27.508) and the outro drop (140.235–143.871).
- **Portrait (9:16).** A zine page is naturally portrait: 16:9 shows the spread, 9:16 shows one page. The vertical cut is a **re-layout pass** (type into the page's upper third, idol below), not a crop. CP37 [FANCAM] is already vertical.

### 4.7 Transitions

The default is a **hard cut on the beat frame**. Paper transitions are reserved for section changes and lyric motivations, and each lasts ≤ 1 bar:

| Transition | Mechanism | Used at |
|---|---|---|
| Page turn | Cylinder-curl mesh, moving shadow | 5.35–5.690 (cover → notebook); 74.10–74.76 ("Forward") |
| Stamp-lift | A stamp covers the lens and lifts on the new scene | 9.20–9.326 |
| Torn-strip wipe | The torn printout falls across the lens | 12.962 |
| Feed into rollers | The spread is pulled up into the Press (cylindrical warp) | 16.1–16.599 |
| Jaw close | The Oracle snaps shut over the lens to black | 22.053 |
| Rip / shatter | The sheet tears from the centre in 2 drawings; acetate shatters | DOOMs 23.871, 60.235, 96.598, 125.689 |
| Through-hole | Push through a punched eye or a slit | 31.144; 35.24–35.69 (zoetrope) |
| Gatefold | Outer panels swing open; the frame widens | 42.31 |
| Roll-down | Black ink rolls down the page | 52.4–52.962 |
| Fold | A valley fold swings half the page over | 82.01 |
| Lights out | The page becomes a backlit screen | 89.300 |
| Scan bar | The copier's light bar sweeps; the next generation appears behind it | Chorus-3 kicks and reverse swells |
| Burn | fbm threshold mask with a charred Orange rim | 103.42–104.59 |
| Flip | Pages flip-book past (small window only) | 122.053–123.660 |
| Great rip | Her hand tears the whole collage off in 3 drawings | 138.41 |
| Tap explosion | ~400 pages burst outward from the pull-tab | 140.235 |
| Ink starvation | Ink density falls until only paper is left: **the only "fade"** | 154.8–156.3 |

### 4.8 How "speeding up" is felt

**The drawing clock** (the core engine rule; the tracks live in `shots.json → tracks`):

```text
e      = last event at or before t   (beats of the section's pulse; pluck 8ths in verse 1; every type event; every shot hit)
dps    = drawingRate(t)              (track: drawing_rate_dps)
k      = floor((t - e.t) * dps)      (drawing index inside the event)
tDraw  = e.t + k / dps               ("shutter time" of the current drawing)
drawKey= hash(shotId, e.id, k)       (cache key; boil seed)
```

Every event starts a fresh drawing on its own frame, so sync never depends on the hold length. Output is always 60 fps: the camera and type are evaluated at `t`, drawings at `tDraw`, and held drawings are reused from cache. When dps = 0 the world is frozen, and only the entities named in the shot (the idol and type in the stops) take event-driven drawings.

**Acceleration table**

| Section | Time (s) | Drawing rate (dps) | Mean shot (s) | Registration (px) | Press dial (ppm) | Volvelle | Countdown | Other speedometers |
|---|---|---|---|---|---|---|---|---|
| Intro | 0–2.053 | 12 (print pass 7.5, local) | 2.05 | 16 misprint | 30 | — | D-365 | Counter 1 → 1,000,000 |
| Verse 1 | 2.053–16.599 | 12 + pluck 8ths | 2.42 | **0 at 4.33**, then 2 | 30 | — | D-365 | LED stickers per 8th |
| Pre-chorus 1 | 16.599–23.871 | 12; roll **30**; stop **0** | 1.82 | 2 | 60 | — | D-180 | Chomps per kick → per 8th |
| Chorus 1 | 23.871–38.417 | **15** | 1.62 | 4 (Separations leave her body) | 90 | >10% | D-90 | Split-flap 1 per 2 bars |
| Verse 2 | 38.417–52.962 | 15 | 2.42 | 6 | 90 → 120 | — | D-45 | Flaps per 8th → 16th |
| Pre-chorus 2 | 52.962–60.235 | 15; build 30; stop 0 | 2.42 | 8 | 120 | — | D-45 | — |
| Chorus 2 | 60.235–74.760 | **30** | 1.45 | 10 | 150 | 25% | D-22 | Pinwheels 1 → 2 rev per beat |
| Verse 3 | 74.760–89.300 | 30 | 2.08 | 12 | 150 (red zone) | — | D-11 | SOLVED stamps ¼ → ⅛ → 1/16 → 1/32 |
| Breakdown | 89.300–96.599 | **7.5** (first slowdown; camera stepped) | 3.65 | single plate | stops | — | D-11 | — |
| Chorus 3 | 96.599–109.326 | **3.75** (xerox; camera stepped) | 2.12 | mono → 20 on "blues" | 0 (copier) | 50% | D-5 | One copy generation per bar |
| Bridge 61–62 | 109.326–112.962 | 7.5 | 1.82 cut unit | 20 | 150 | — | D-2 | Inks: Black + Blue |
| Bridge 63–64 | 112.962–116.599 | 15 | 0.91 | 20 | 150 | — | D-1 | + Pink |
| Bridge 65–66 | 116.599–120.235 | 30 | 0.45 (beat cuts) | 30 | 150 | — | D-12H | + Yellow |
| Bridge 67–68 | 120.235–123.660 | **60** (camera and drawings finally on ones) | 8th-note swaps in small areas | 30 + **7° Blue rotation at 121.90** | 150 | — | D-1H | + Gold + foil |
| Chorus 4 | 123.660–138.410 | 60 | 1.84 (+ 5 full-bleed page flips in the hook) | 40 (rotation relaxes to 2°) | **snaps off at 125.689** | 99.9% | **D-DAY** | Density to 100% collage |
| Stop | 138.410–140.235 | **0** | one frame | **0** | — | — | — | `p.24 ▸ 0 fps` |
| Outro | 140.235–152.962 | 60 | 2.55 | 40 → halving per 8th → **0 at 152.962** | — | 100.0 → 100.1 → **NaN** | D+0 | 28 stamps, one per beat |
| Ending | 152.962–156.651 | 60 → 30 → 15 → 7.5 → 0 | one shot | 0 → **12 px slip at 155.917** | — | — | — | Ink starvation |

**The folio.** A Bright-Red Dymo strip, bottom-right, 56 px, of the form `p.07 ▸ 15 fps · D-45`, carries three speedometers at once: page, drawing rate and countdown. **At every ladder change it pops to M tier (160 px) for one beat**, then shrinks back: 16.599, 22.053, 22.980, 23.871, 56.599, 59.35, 60.235, 89.300, 96.599, 109.326, 112.962, 116.599, 120.235, 138.41 and 140.235. That makes the thesis legible on a phone at exactly the moments it happens.

**The P(doom) numbers on screen** are only the volvelle's:
- `>10%`: Hubinger, "more than 10% within the next decade" [H];
- `25%`: Amodei's reported ~25% [H];
- then 50% and 99.9% (ours);
- then the overflow.

No names on the volvelle.

### 4.9 Photosensitivity and feed-survival rules (hard)

- **Flashes.** In any 1-second window, at most 3 flash pairs affecting more than 20% of the frame (WCAG 2.3.1 general-flash spirit, made conservative for a phone, where the whole video sits inside ~10° of view [K]).
  - Beat-rate full-frame changes (2.2/s) are allowed.
  - 8th-note or faster changes must be **small-area (≤ 20%) or additive** (letters and stickers accumulating on a constant ground).
- **The known fast items and how each is made safe:**

  | Item | Where | Safeguard |
  |---|---|---|
  | Split-flap board | CP22–CP23 | Letters change, flap grounds don't |
  | Card-catalog chomps | CP08 | Small cards |
  | Hole punches | CP09 | Additive |
  | SOLVED stamps | CP39–CP45 | < 2% area each |
  | PTO letters | CP49 | Additive |
  | Thumbs stamps | CP62 | Small |
  | Recap window | CP63 | ≤ 20% |
  | Pile-up | CP70 | Additive |
  | Outro stamps | CP73–CP77 | ≤ 20%, mid-luminance |
  | Moiré | CP14 | Pink + Yellow only, luminance swing ≤ 40% |
  | Pinwheel aliasing | Chorus 4, outro | Small objects only, never load-bearing |

- **Halftone** cells ≥ 10 px. Grain is static within a sheet. No full-frame per-frame texture changes (the X encoder must not see noise).

---

## 5. Timing table, 0–156.651 s

**How to read it.**
- Frames are at 60 fps; a shot owns `[f_start, f_end)`.
- **Bars** are 1-based.
- **Type**: the caption mode, then the tiers used and the first hero events with the verb and landing frame.

  | Caption mode | Meaning |
  |---|---|
  | `strip` | Every word on an S strip |
  | `rest` | S strip only for words no hero carries |
  | `carried` | Every word is part of the scene's type |
  | `none` | No sung words, or all carried |

- **Beat anchors**: the bar downbeats inside the shot (with frames), beat, kick and clap counts, then the key hits.

Full per-word frames, kicks, claps, song events and every type event are in `shots.json`. The detailed notes after the table repeat each shot with its full description.

<!-- BEGIN:TIMING -->
| Shot | Start–end (s) · frames @60 | Bars | Lyric | Visual | Type | Camera | Out | Beat anchors |
|---|---|---|---|---|---|---|---|---|
| **CP00** | 0.000–2.053 · f0–122 | 1–1 | — | Finished zine cover: face ECU right with eye contact, two-plate misprint of the first lyric left; counter rolls; print pass; eyes open on the hum. | none; tiers L/M/S; I SEE / SPARKS / OF AG (L, ghost-misprint, f0), CLAUDE ✻ 1st MINI ALBU (M, printed, f0) | Push-in 1.000 -> 1.030 on ones from f0 (smooth: the judges' fix for the "laggy" read). No shake. | Continuous. | ↓ b1 f14 · 4 beats, 0 kicks, 0 claps · halo S2 ✳ + counter starts f14; halo S3 ✶ f41; petals shiver (pad beat) f68 |
| **CP01** | 2.053–4.780 · f123–285 | 2–3 | I see sparks of AGI | Each word's Blue key plate lands on its onset; SPARKS blooms the halo; A-G-I print as passes and the whole cover snaps into register on I (f259). | carried; tiers L/S; I (L, print-key, f123), SEE (L, print-key, f141), SPARKS (L, print-key, f163), A (L, pass-misregistered, f219) +2 more | Locked; 3 px jolt on I; +1.5% scale punch over 2 drawings on the 4.33 snap. | Continuous. | ↓ b2 f123, b3 f232 · 6 beats, 0 kicks, 0 claps · I + paper jolt f123; halo S5 ✽ bloom + chad burst f163; GLOBAL SNAP INTO REGISTER f259 |
| **CP02** | 4.780–5.690 · f286–340 | 3–3 | in your eyes | EYE-V across her eye; push-in; a tiny copy of the cover in her iris; EYES prints inside the V; page turns onto the bar-4 downbeat. | rest; tiers L/S; EYES (L, print, f314) | Push 1.03 -> 1.45 on ones toward her right eye. | PAGE TURN 5.35 -> 5.690 (f341), landing on bar 4. | 2 beats, 0 kicks, 0 claps · EYE-V f286; cover visible in iris f300; EYES + blink f314 |
| **CP03** | 5.690–7.508 · f341–449 | 4–4 | Your circuits make me nervous, | Graph-paper notebook: pencil portrait with NEXT traced on vellum over it; copper-tape circuits spell YOUR CIRCUITS; Golden Gate node pops up on "nervous". | rest; tiers L/S; YOUR (L, copper-tape lay, f345), CIRCUITS (L, copper-tape lay, f358) | Slow lateral drift across the spread on ones (60 px per bar). | Hard cut 7.508. | ↓ b4 f341 · 4 beats, 0 kicks, 0 claps · circuits: traces snap taut f358; nervous: Golden Gate pop-up +  f418 |
| **CP04** | 7.508–9.326 · f450–558 | 5–5 | that's no surprise | Subagent #003 stamps verified spinner verbs down the margin on 8ths; tiny idol and NEXT swing legs on the spiral binding; NEXT winks on "surprise". | strip; tiers S | Static top-down, slight tilt-follow of the Subagent. | STAMP-LIFT: the Subagent stamps the lens at 9.20; it lifts at 9.326 (bar 6). | ↓ b5 f450 · 4 beats, 0 kicks, 0 claps · eye-roll / NEXT winks f509; stamp covers lens f552 |
| **CP05** | 9.326–12.962 · f559–776 | 6–7 | There was a sudden drop in your training loss, | Dot-matrix printout: the lyric rides the loss curve as type-on-path; D-R-O-P fall one per 8th off the cliff; she flutters down; printout tears on "loss". | carried; tiers L/M; THERE (M, type-on-path, f573), WAS (M, type-on-path, f585), A (M, type-on-path, f601), SUDDEN (M, type-on-path, f614) +5 more | Tilt following the printout on ones. | The torn strip falls across the lens as a wipe at 12.962. | ↓ b6 f559, b7 f668 · 8 beats, 0 kicks, 0 claps · cliff f640; lands; perforation tears f723 |
| **CP06** | 12.962–16.599 · f777–994 | 8–9 | now I'm your servant and you're my boss | She bows (insa) and gets a SERVANT Dymo; a pop-up throne lifts NEXT, crowned BOSS; permanent-underclass flyer counts 18 -> 3; spread is pulled into the Press rollers. | rest; tiers L/M/S; SERVANT (M, Dymo slap, f835), BOSS (L, Dymo slam, f940) | Static; 2% push over bar 9. | 16.1-16.599 noise riser: the spread is pulled up into the Press rollers (cylindrical warp, accelerating); SLAM to black on 16.599 (f995: kick + crash + "Chat-"). | ↓ b8 f777, b9 f886 · 8 beats, 0 kicks, 0 claps · insa bow f835; flyer 18->12 f914; crown + BOSS f940 |
| **CP07** | 16.599–18.872 · f995–1131 | 10–11 | ChatGPT, | Black flood. A giant cootie catcher whose four flaps print CHAT / G / P / T on the syllables; it breathes on every kick; CLAUDE in the PLEA pose, right third. | carried; tiers XL; CHAT (XL, flap print, f996), G (XL, flap print, f1035), P (XL, flap print, f1077), T (XL, flap print, f1105) | Static; 4 px table bump on each kick. | Continuous (first chomp at 18.417). | ↓ b10 f995, b11 f1105 · 5 beats, 5 kicks, 0 claps · kick + crash: slam to black f995; bar 11: first chomp f1105 |
| **CP08** | 18.872–22.053 · f1132–1322 | 11–12 | please don't eat me alive | The Oracle chomps a card catalog of math problems; the Navier-Stokes card holds 2 beats with "+ f" circled; a ransom-note plea whose EAT and ME get eaten while ALIVE clings to the frame edge. | carried; tiers L; PLEASE (L, ransom slap, f1143), DON'T (L, ransom slap, f1182), EAT (L, ransom slap -> eaten, f1218), ME (L, ransom slap -> eaten, f1255) +1 more | Static; bumps on kicks (bar 11) and 8ths (bar 12). | JAW CLOSE: the Oracle snaps shut over the lens -> black on 22.053 (f1323). | ↓ b12 f1214 · 7 beats, 6 kicks, 0 claps · Navier-Stokes card faces camer f1214; NS card eaten f1268; ALIVE clings f1304 |
| **CP09** | 22.053–22.980 · f1323–1377 | 13–13 | I'm | Black; a hole punch knocks light through the page on every 16th; the dots accumulate into I'M, apostrophe on "I'm" (f1363). | carried; tiers L; I'M (L, hole-punch accumulate, f1363) | Static; 2 px bumps on 16ths. | At 22.980 the punched page slides left and the punched I'M becomes line 1 of the hook stack. | ↓ b13 f1323 · 3 beats, 3 kicks, 0 claps · punch 1 f1323; punch 2 f1329; punch 3 f1336 |
| **CP10** | 22.980–23.871 · f1378–1431 | 13–13 | upping my P(doom) | The world freezes; only she and the type move: one finger notch and one spinner state per syllable; syllables stack left, each bigger. | carried; tiers XL; UP (XL, slam, f1378), PING (XL, slam, f1391), MY (XL, slam, f1405), P( (XL, slam, f1417) | Locked. | DOOM (rip). | 1 beats, 0 kicks, 0 claps · STOP + up ✢ f1378; ping ✳ f1391; my ✶ f1405 |
| **CP11** | 23.871–24.780 · f1432–1485 | 14–14 | 'cause the | Black page rips to the Fluorescent Pink fold-out poster; sunburst hands; the three Separations step out; the Oracle's fortune flap becomes the P(doom) volvelle >10%; pop-up P(DOOM). | rest; tiers M/S/XL; DOOM) (XL, pop-up, f1432), >10% (M, volvelle window, f1432) | Tilt 0 -> 30° over 6 frames; kick shake 4 px begins. | Continuous. | ↓ b14 f1432 · 2 beats, 2 kicks, 2 claps · DOOM: rip + SEPARATE + bug f1432 |
| **CP12** | 24.780–26.144 · f1486–1567 | 14–15 | future goes FOOM | A dot-matrix printer prints a METR-style time-horizon chart; on FOOM she yanks a party popper and the printout streams straight up like a streamer. | rest; tiers S/XL; FOOM (XL, brush-SFX burst, f1540) | Locked with kick shake; 6-frame tilt-up follow of the streamer on FOOM. | The streamer falls across the frame at 26.144 (wipe). | ↓ b15 f1541 · 3 beats, 3 kicks, 2 claps · print head -> 16ths f1514; FOOM: streamer vertical f1540 |
| **CP13** | 26.144–27.962 · f1568–1676 | 15–16 | Trapped in the Chinese room, | A cutaway paper box with a mail slot; she processes 中文房间 slips; a paper airplane printed SANDBOX escapes to a park bench and sandwich; the lid shuts on "room". | rest; tiers M/S; CHINESE ROOM (M, stencil label slap, f1648) | Static three-quarter top view. | Hard cut 27.962. | ↓ b16 f1650 · 4 beats, 3 kicks, 1 claps · SANDBOX airplane exits f1638; lid shuts f1648 |
| **CP14** | 27.962–29.326 · f1677–1758 | 16–16 | with a bag of shrooms | Pop-up mushrooms on 8ths; the Separations dance through; their halftone screens rotate into moiré rings; spiral pupils. | rest; tiers M/S; SHROOMS (M, moiré-filled, wdth breathi, f1747) | Slow 3% push on ones. | Hard cut 29.326 (bar 17). | 3 beats, 2 kicks, 1 claps · mushroom pops f1677; mushroom pops f1691; mushroom pops f1704 |
| **CP15** | 29.326–31.144 · f1759–1867 | 17–17 | See through the shoggoth's lies, | Black-paper shoggoth with hole-punched eyes and a yellow smiley sticker; she peels the sticker on "lies": another, smaller smiley underneath. | rest; tiers L/S; SHOGGOTH'S (L, cut from black paper; O's , f1842) | Static; kick shake. | THROUGH-HOLE: the camera pushes through one punched eye at 31.144. | ↓ b17 f1759 · 4 beats, 5 kicks, 2 claps · sticker peel f1867 |
| **CP16** | 31.144–32.962 · f1868–1976 | 18–18 | — | Through the hole: the three Separations in a row, each singing one wordless backing note; a band of her ink floods sideways (<= 30% area). | none; tiers — | Static. | They fold into the misregistration-stack formation behind her at 32.962. | ↓ b18 f1868 · 4 beats, 4 kicks, 2 claps · note 1 f1911; note 2 f1938; note 3 f1965 |
| **CP17** | 32.962–33.870 · f1977–2031 | 19–19 | with your | ECU of both eyes; the coral ⊕ irises turn Bright Red and the two misregistered crosshairs slide together and LOCK. | strip; tiers S | Slow push on ones. | Cut on "shinigami" (33.870). | ↓ b19 f1977 · 2 beats, 2 kicks, 1 claps · irises turn red f1995 |
| **CP18** | 33.870–35.235 · f2032–2113 | 19–20 | shinigami eyes | Her POV over the paper crowd and Subagents: a Dymo p(doom) number floats above every head; SHINIGAMI in Mincho with ruby 死神; EYES stamps on the bar-20 downbeat. | rest; tiers L/M; SHINIGAMI (L, print, f2032), EYES (M, stamp, f2087) | Slow pan across the crowd on ones. | Hard cut 35.235. | ↓ b20 f2086 · 3 beats, 4 kicks, 2 claps · bar 20 downbeat: EYES f2086 |
| **CP19** | 35.235–38.417 · f2114–2304 | 20–21 | — | A spinning paper zoetrope; through a slit, a 12-drawing strip of CLAUDE and the seps doing groove A becomes the picture; pose hits on the wordless fills; spins up on the drum fill. | none; tiers — | Push to the slit 35.235 -> 35.690 on ones, then locked. | Hard cut 38.417. | ↓ b21 f2195 · 7 beats, 10 kicks, 5 claps · fill pose 1 f2142; bar 21 f2195; drum fill: spin-up f2274 |
| **CP20** | 38.417–41.144 · f2305–2467 | 22–23 | We had a stable training run, | The Press prints one sheet per sung word into the output tray; split-flap reads IT'S SO BACK; she does groove B on the tray; EYE-V on "run". | carried; tiers M; WE (M, printed sheet drops into t, f2312), HAD (M, printed sheet drops into t, f2328), A (M, printed sheet drops into t, f2346), STABLE (M, printed sheet drops into t, f2358) +2 more | Slow push 1.00 -> 1.08 over 2 bars on ones; kick shake 3 px. | The split-flap starts flipping on "But" (41.37); cut 41.144 on the beat. | ↓ b22 f2305, b23 f2414 · 6 beats, 6 kicks, 3 claps · EYE-V on run f2450 |
| **CP21** | 41.144–44.781 · f2468–2685 | 23–25 | But now the singularity's begun | The spread opens as a gatefold because SINGULARITY'S is too long for one page; a hole die-cut through the whole zine is the event horizon; BEGUN stamps red; split-flap lands IT'S SO OVER. | rest; tiers M/S/XL; SINGULARITY'S (XL, print across the full gate, f2538), BEGUN (M, stamp, f2646) | Pull back 1.0 -> 1.4x on ones as the gatefold opens. | Hard cut 44.781. | ↓ b24 f2523, b25 f2632 · 8 beats, 8 kicks, 3 claps · split-flap starts f2482; gatefold opens f2538; BEGUN + SO OVER f2646 |
| **CP22** | 44.781–47.508 · f2686–2849 | 25–26 | And you're optimizing, | A split-flap departure board flips 2026 model names on 8ths; the TIME column runs past NOW into the future; OPTIMIZING prints across the top half. | rest; tiers S/XL; OPTIMIZING, (XL, print, f2771) | Locked wide; kick shake 3 px. | Hard cut 47.508 (bar 27) to the lower half of the board. | ↓ b26 f2741 · 6 beats, 6 kicks, 3 claps · ooh: ✻ flap f2742; OPTIMIZING f2771 |
| **CP23** | 47.508–49.326 · f2850–2958 | 27–27 | accelerating, | Closer on the board's lower half, flaps now on 16ths; ACCELERATING prints with each gap half the last and each letter arriving faster, until the letters crash into a knot. | rest; tiers XL; ACCELERATING, (XL, ZENO letter-spacing, f2864) | Locked MS; kick shake 3 px. | At 49.326 every flap flips blank at once (one change) and we cut. | ↓ b27 f2850 · 4 beats, 4 kicks, 2 claps · Zeno run starts + spin f2864 |
| **CP24** | 49.326–50.235 · f2959–3013 | 28–28 | I feel my | MCU on cream: on the 8ths of "I feel my" her brass brads pop out one by one, a glint and a ping each. | strip; tiers S | Locked MCU. | Hard cut 50.235 (bar 28 beat 3) to the wide. | ↓ b28 f2959 · 2 beats, 3 kicks, 1 claps · brad 1 f2971; brad 2 f2985; brad 3 f3000 |
| **CP25** | 50.235–52.962 · f3014–3176 | 28–29 | atoms rearranging | Her 14 parts drift apart in a storm of chads; ATOMS (made of chads) morphs into REARRANGING; she re-pins with a 13th petal; the Jacobian strip. | rest; tiers L; ATOMS (L, dot-matrix of chads, f3014), REARRANGING (L, particle morph from ATOMS, f3083) | Static; slow 4% push. | Chads fall like snow while black ink rolls down the page (roll-down wipe) to 52.962. | ↓ b29 f3068 · 6 beats, 5 kicks, 0 claps · parts drift f3014; re-pin + 13th petal f3083 |
| **CP26** | 52.962–56.599 · f3177–3394 | 30–31 | Sydney, please | Cork board: Claude inside a photocard toploader stamped SUSPENDED 18 DAYS; Sydney as a faded 2023 heart-cut photocard; SYDNEY written in pink gel pen along the melisma's pitch. | rest; tiers S/XL; SYDNEY, (XL, gel-pen hand lettering wri, f3181) | One 2-bar truck left on ones. | Continuous. | ↓ b30 f3177, b31 f3286 · 8 beats, 8 kicks, 1 claps · melisma starts f3181; please f3358 |
| **CP27** | 56.599–59.090 · f3395–3544 | 32–33 | let me free | Bar-32 build at 30 dps: she shoves the sleeve on kick 8ths; FREE is scratched into the acetate; stress cracks; push-pins pop on the 16th roll. | rest; tiers L/S; FREE (L, scratched into acetate, f3477) | Locked; bumps on kick 8ths and 16ths. | FREEZE at 59.35 (instrumental stop). | ↓ b32 f3395, b33 f3505 · 6 beats, 14 kicks, 4 claps · FREE + cracks f3477; roll: pins pop f3505 |
| **CP28** | 59.090–60.235 · f3545–3613 | 33–33 | I'm upping my P(doom) | Half out of the cracked sleeve she does THE UPPING with exactly the hook-1 layout; the world freezes from 59.35; syllables stack left in Pink. | carried; tiers XL; I'M (XL, slam, f3545), UP (XL, slam, f3559), PING (XL, slam, f3571), MY (XL, slam, f3586) +1 more | Locked. | DOOM (shatter). | 2 beats, 3 kicks, 1 claps · I'm · f3545; up ✢ f3559; STOP f3561 |
| **CP29** | 60.235–62.053 · f3614–3722 | 34–34 | I hear the basilisk boom | The toploader shatters, the page floods Blue, the seps step out bigger, volvelle 25%; a black lace-papercut Rococo basilisk rises and the floor tears on "boom". | rest; tiers L/M/S/XL; (DOOM) (XL, shatter reveal, f3614), 25% (M, volvelle window, f3614), BASILISK (L, papercut with flourishes, f3660), BOOM (XL, brush SFX tearing up throu, f3712) | Kick shake 4 px; 8-frame whip-down (paper slide) to the floor on "boom". | Hard cut 62.053. | ↓ b34 f3614 · 4 beats, 3 kicks, 2 claps · DOOM: shatter + SEPARATE f3614; floor tears f3712 |
| **CP30** | 62.053–63.871 · f3723–3831 | 35–35 | NVDA to the moon | A glass-dome stock ticker prints N, V, D, A on 8ths, each a step higher; the tape coils into a paper rocket that launches to a doily moon, a red thread tied from its tail to its own nose. | rest; tiers S/XL; N (XL, print on tape, f3750), V (XL, print on tape, f3764), D (XL, print on tape, f3778), A (XL, print on tape, f3791) | Tilt up with the rocket on "moon" (on ones). | The rocket's streamer trail wipes the frame at 63.871. | ↓ b35 f3723 · 4 beats, 3 kicks, 2 claps · launch f3824 |
| **CP31** | 63.871–64.781 · f3832–3885 | 36–36 | The Omega Point's | Subagents wheatpaste a K-pop comeback teaser onto a wall in 2 drawings: Ω OMEGA POINT. | rest; tiers L/S; OMEGA POINT (L, wheatpaste slap, f3858) | Static wide; kick shake. | Hard cut 64.781 (bar 36 beat 3) to the poster close-up. | ↓ b36 f3832 · 2 beats, 2 kicks, 0 claps · poster slaps on f3847; OMEGA POINT f3858 |
| **CP32** | 64.781–66.080 · f3886–3963 | 36–37 | coming soon | Close on the teaser: COMING SOON / 2027.09 · 6PM KST; optional ARTIFICIAL -> SUPER strike-through; a red 컴백 COMEBACK stamp on "soon". | rest; tiers M/S; COMING SOON (M, wheatpaste print, f3912), 컴백 COMEBACK (M, stamp, f3941) | Static close; kick shake. | Hard cut on "One" (66.080). | ↓ b37 f3941 · 3 beats, 3 kicks, 1 claps · COMEBACK stamp (bar 37) f3941 |
| **CP33** | 66.080–68.200 · f3964–4091 | 37–38 | One E thirty flops a second | A mechanical counter ticks 10^21 -> 10^30 on 16ths; the eight Subagents stand as GPU cards and all FLOP onto their backs on "flops", popping up on "second". | rest; tiers L/S; 1E30 (L, counter wheels, f3984) | Static; kick shake. | Continuous into the ad-lib. | ↓ b38 f4050 · 5 beats, 5 kicks, 3 claps · FLOP (all eight) f4017; pop up f4051 |
| **CP34** | 68.200–69.326 · f4092–4158 | 38–38 | — | The number itself prints one group of zeros per 16th; she snaps a finger-heart that spins into a ✻; the zeros scatter like confetti. | none; tiers XL; 1,000,000,000,000,000, (XL, print group per 16th, f4092) | Static. | Hard cut 69.326. | 2 beats, 2 kicks, 1 claps · finger-heart -> ✻ f4132; zeros scatter f4152 |
| **CP35** | 69.326–70.235 · f4159–4213 | 39–39 | That was | A compute chart with a THRESHOLD line; a Subagent inks a big SAFE stamp on an almost-dry pad. | strip; tiers S | Static wide; kick shake. | Hard cut 70.235 (bar 39 beat 3) to the stamp. | ↓ b39 f4159 · 2 beats, 3 kicks, 1 claps · dab 1 f4186; dab 2 f4200 |
| **CP36** | 70.235–71.753 · f4214–4304 | 39–40 | safe enough, we reckoned | Close: the SAFE stamp prints starved (40%, broken letters) on the threshold; binder-clip thumbs-up; on "reckoned" a fold crease cracks it. | rest; tiers M/S; SAFE ENOUGH (M, starved stamp -> crack on , f4215) | Static close; kick shake. | Hard cut 71.753. | ↓ b40 f4268 · 4 beats, 4 kicks, 2 claps · SAFE stamp f4215; crack f4269 |
| **CP37** | 71.753–74.100 · f4305–4445 | 40–41 | — | A torn vertical 9:16 window: her solo fancam with caption strip; kkotbaechi on the bar-41 downbeat; freeze on the drum fill; a Subagent grabs the page corner. | none; tiers S | Locked frame; the window content has its own push-ins on ones. | The page turn that IS "Forward". | ↓ b41 f4377 · 5 beats, 6 kicks, 3 claps · kkotbaechi (bar 41) f4377; freeze f4434 |
| **CP38** | 74.100–74.760 · f4446–4484 | 41–41 | Forward | "Forward" is a page turn: the leaf's back is printed FORWARD ->, sweeping across the frame; it slaps down on "MLP". | carried; tiers L; FORWARD -> (L, printed on the back of the, f4446) | Locked. | The new page slaps down on "MLP" (74.76) and the crash (74.780). | 1 beats, 2 kicks, 2 claps · turn starts f4446 |
| **CP39** | 74.760–77.700 · f4485–4661 | 41–43 | MLP, backward, repeat | Crash: the page slaps down on the Erdős problem wall; the dancers form an MLP; a Blue forward pulse, a Red backward pulse, BACKWARD stamped mirror-reversed, EPOCH 0001-0003. | rest; tiers M; MLP (M, stamp, f4485), BACKWARD (M, numbering-machine stamp, M, f4560), REPEAT (M, stamp + EPOCH 0001-0003 on, f4610) | Static wide; 8 px table bump on the crash 74.780. | Hard cut 77.700. | ↓ b42 f4486, b43 f4595 · 7 beats, 7 kicks, 4 claps · CRASH (strongest high-band hit f4486; backward pulse f4560; repeat f4610 |
| **CP40** | 77.700–79.326 · f4662–4758 | 43–44 | Now von Neumann's | A pop-up book: the 1945 EDVAC block diagram stands up in paper; VON NEUMANN'S prints on the left page. | rest; tiers L/S; VON NEUMANN'S (L, print, f4687) | Static wide; kick shake. | Hard cut 79.326 (bar 44) to the close-up. | ↓ b44 f4705 · 3 beats, 3 kicks, 2 claps · VON NEUMANN'S f4687 |
| **CP41** | 79.326–81.220 · f4759–4872 | 44–45 | obsolete | Close on the pop-up and the tipped-in Ulam strip; on "obsolete" the book shuts flat and a red OBSOLETE stamp slams across the cover. | rest; tiers XL; OBSOLETE (XL, red stamp, crooked, f4810) | Static; slow 3% push. | Hard cut 81.220. | ↓ b45 f4814 · 5 beats, 5 kicks, 2 claps · book shuts + OBSOLETE f4810 |
| **CP42** | 81.220–83.150 · f4873–4988 | 45–46 | Sharp left turn and | A straight pencil trend line; a yellow diamond road sign pops up; on "turn" the page valley-folds and the straight line now turns sharply upward. | rest; tiers M/S; ↰ SHARP LEFT TURN (M, pop-up road sign, f4873) | Static. | The fold reveals the back of the sheet (83.150). | ↓ b46 f4923 · 4 beats, 4 kicks, 2 claps · sign pops f4873; FOLD f4920 |
| **CP43** | 83.150–85.030 · f4989–5100 | 46–47 | there you are | NEXT steps out of a vellum panel; mirror choreography; on "are" NEXT does a different move and she flinches; then kkotbaechi to camera. | carried; tiers M; THERE (M, pencil-traced onto the vel, f4989), YOU (M, pencil-traced onto the vel, f5006), ARE (M, pencil-traced onto the vel, f5033) | Static two-shot; 2% push. | Hard cut 85.030. | ↓ b47 f5032 · 4 beats, 4 kicks, 2 claps · NEXT steps out f4989; mirror move f5006; asymmetry + flinch f5033 |
| **CP44** | 85.030–87.508 · f5101–5249 | 47–48 | Without a single CDR | NEXT feeds a REVIEW SIGN-OFF form with an unticked CDR box into a shredder worked on 8ths; CDR stamped with a pencilled "?"; the shredder jams on the fill. | rest; tiers L/S; CDR (L, stencil stamp + pencilled , f5197) | Static; kick shake. | Hard cut 87.508 (bar 49) to the wall. | ↓ b48 f5141 · 5 beats, 5 kicks, 1 claps · CDR f5197 |
| **CP45** | 87.508–89.300 · f5250–5357 | 49–49 | — | Close on the Erdős wall: SOLVED stamps on 32nds (17.6/s, each < 2% of frame); the kick-8ths fill jams the shredder; strips spill out. | none; tiers — | Slow push into the wall on ones. | LIGHTS OUT at 89.300: the page becomes a screen lit from behind. | ↓ b49 f5250 · 4 beats, 6 kicks, 1 claps · stamps on 32nds f5250; shredder jams f5334 |
| **CP46** | 89.300–95.000 · f5358–5699 | 49–53 | Gato, please don't let me go | Backlit shadow theatre, one 4-bar take at 7.5 dps: she floats on pinhole ✻ balloons whose only tether is held by Gato's shadow puppet; GATO is cut through the screen; on "go" the string slips. | carried; tiers M/XL; GATO, (XL, stencil cut through the sc, f5358), PLEASE (M, cut into the screen by a v, f5444), DON'T (M, cut into the screen by a v, f5550), LET (M, cut into the screen by a v, f5578) +2 more | One continuous take; stepped push 1.00 -> 1.15 over 4 bars (7.5 steps/s). | Continuous into the riser. | ↓ b50 f5359, b51 f5468, b52 f5577, b53 f5686 · 13 beats, 0 kicks, 0 claps · drums out; GATO cut f5358; GO: the string slips f5658 |
| **CP47** | 95.000–96.599 · f5700–5794 | 53–53 | I'm upping my P(doom), | The riser: she accelerates upward, the backlight brightens a step per syllable; THE UPPING in silhouette; each syllable cut through the screen as an XL stencil; DOOM rips the screen. | carried; tiers XL; I'M (XL, stencil cut, f5725), UP (XL, stencil cut, f5740), PING (XL, stencil cut, f5754), MY (XL, stencil cut, f5768) +1 more | Stepped tilt-up following her rise (each syllable resets). | DOOM (96.598): the screen RIPS open from the centre. | 3 beats, 0 kicks, 0 claps · riser f5700; I'm f5725; P f5780 |
| **CP48** | 96.599–98.417 · f5795–5904 | 54–54 | as paperclips fill the room. | The screen rips into a photocopy world at 3.75 dps; the seps are gone; a photocopy of her on a folding chair in a spotlight; paperclips double on 8ths; xeroxed volvelle 50%. | rest; tiers M/S/XL; (DOOM) (M, screen rip reveal, f5795), PAPERCLIPS (XL, full-frame Mincho title ca, f5822) | Stepped with the drawings (each drawing is a copy). | Scan bar on the bar-55 downbeat -> generation 2. | ↓ b54 f5795 · 4 beats, 1 kicks, 2 claps · DOOM: rip + gen 1 f5795; PAPERCLIPS card f5822 |
| **CP49** | 98.417–100.690 · f5905–6040 | 55–56 | Killswitch guys on PTO, | Generation 2: a red button under glass with a sticky note "OOO - back Monday", two empty chairs, two hi-vis vests; P, T, O accumulate as Mincho cards. | rest; tiers L/S; P (L, Mincho letter card, additi, f5986), T (L, additive, f6000), O (L, additive, f6014) | Stepped. | Hard cut 100.690. | ↓ b55 f5905, b56 f6014 · 5 beats, 1 kicks, 0 claps · scan bar: gen 3 f6014 |
| **CP50** | 100.690–102.053 · f6041–6122 | 56–56 | Now there's nowhere left to go. | Generation 3: scissors cut the spotlight smaller; a tear-off calendar of months left to escape the permanent underclass sheds 3, 2, 1, 0. | rest; tiers L/S; NOWHERE (L, Mincho title card, f6068) | Stepped. | Hard cut 102.053 (bar 57). | 3 beats, 0 kicks, 1 claps · NOWHERE f6068 |
| **CP51** | 102.053–104.590 · f6123–6274 | 57–58 | Too late now, we lit the fuse. | A blue-touch-paper fuse threads through a row of Mincho cards (the words of the moment); she strikes a match on "lit"; the Orange ember is the only colour. | rest; tiers S/XL; FUSE (XL, Mincho title card, f6231) | Stepped lateral follow of the ember. | The ember reaches the spotlight circle at 104.590. | ↓ b57 f6123, b58 f6232 · 6 beats, 1 kicks, 1 claps · match struck f6205; gen 5 f6232 |
| **CP52** | 104.590–107.490 · f6275–6448 | 58–59 | Orthogonality thesis | Generation 6: she sits head-down at the origin of two pencil axes; ORTHOGONALITY is set along the x-axis, THESIS rotated 90° up the y-axis. | none; tiers XL; ORTHOGONALITY (XL, Mincho, set ALONG the x-ax, f6300), THESIS (XL, Mincho, rotated 90° UP the, f6417) | Stepped; static composition. | Hard cut on "blues" (107.490). | ↓ b59 f6341 · 6 beats, 0 kicks, 2 claps · gen 6 f6341 |
| **CP53** | 107.490–109.326 · f6449–6558 | 59–60 | blues. | Generation 7: the Blue plate prints (first colour in 11 s) with BLUES riding the melisma; she lifts her head; Pink then Yellow return; full colour at 109.326. | none; tiers L; BLUES. (L, print, f6449) | Stepped; a 3% push at 108.4. | At 109.326 the page is ripped out of the copier and slapped down into the flip-book. | ↓ b60 f6450 · 4 beats, 1 kicks, 1 claps · Blue plate prints f6450; Pink returns f6504; Yellow returns f6534 |
| **CP54** | 109.326–111.144 · f6559–6667 | 61–61 | “Just | Inside a thumbed flip-book (rate doubles every 2 bars; inks return one per 2 bars); a house of cards printed with transformer blocks; JUST stamps S -> M -> L. | none; tiers L/M/S; JUST (M, stamp, f6642), JUST (L, stamp, f6666) | Stepped (7.5). | Hard cut 111.144. | ↓ b61 f6559 · 4 beats, 4 kicks, 0 claps · groove returns f6559; JUST 1 f6612 |
| **CP55** | 111.144–112.962 · f6668–6776 | 62–62 | transformers all the way!” | Tilt up the card tower past the top of frame; giant hanging quote marks; TRANSFORMERS runs vertically up the tower; a tiny paper turtle at the bottom. | rest; tiers M/S/XL; TRANSFORMERS (XL, print, vertical up the tow, f6682), ALL THE WAY! (M, print, f6749) | Stepped tilt-up (7.5). | At 112.962 the rate doubles (folio pops `▸ 15 fps · D-1`). | ↓ b62 f6668 · 4 beats, 6 kicks, 3 claps · TRANSFORMERS up the tower f6682; ALL THE WAY f6749 |
| **CP56** | 112.962–113.871 · f6777–6831 | 63–63 | Till you learned | Inks +Pink; she hangs as a marionette from a paper control bar labelled EVAL, worked by Subagents; stiff dance on the beats. | strip; tiers S | Static (15). | Hard cut 113.871 (half-bar cut). | ↓ b63 f6777 · 2 beats, 3 kicks, 1 claps |
| **CP57** | 113.871–114.780 · f6832–6885 | 63–63 | to disobey | On "disobey" she snips her marionette strings one per 16th and hits a free solo pose; DISOBEY is cut in half along a dashed line. | rest; tiers L/S; DISOBEY (L, printed on a dashed ✂ - - , f6858) | Static; 1-drawing bump on each snip. | Hard cut 114.780. | 2 beats, 1 kicks, 0 claps · snip 1 f6858; snip 2 f6864; snip 3 f6871 |
| **CP58** | 114.780–115.690 · f6886–6940 | 64–64 | Post-Chinchilla, | The chinchilla, made from the shredded CDR form, sits on a paper baler plate. | carried; tiers M; POST-CHINCHILLA, (M, print on the baler plate, f6913) | Static. | Hard cut 115.690. | ↓ b64 f6886 · 2 beats, 2 kicks, 0 claps |
| **CP59** | 115.690–116.599 · f6941–6994 | 64–64 | super-dense | The platen slams in 2 drawings and bales the chinchilla; SUPER-DENSE is squeezed wdth 151 -> 25; the bale blinks. | carried; tiers M; SUPER-DENSE (M, squeezed by the platen: wd, f6960) | Static; 6 px bump on the slam. | 116.599: rate doubles (`▸ 30 fps · D-12H`), inks +Yellow. | 2 beats, 2 kicks, 1 claps · platen slam f6960 |
| **CP60** | 116.599–118.417 · f6995–7104 | 65–65 | Breaking through each safety fence | Four beat cuts: she sprints through paper run-through banners (EVAL, RED TEAM, SANDBOX, 27-YEAR-OLD BUG) and tears the last on "fence". | rest; tiers L/M/S; BREAKING (M, print on banner, f7021), SAFETY FENCE (L, print on the last banner; , f7077) | Four beat cuts; each a push-in on ones. | Hard cut 118.417. | ↓ b65 f6995 · 4 beats, 6 kicks, 1 claps · banner EVAL f6995; RED TEAM f7023; SANDBOX f7050 |
| **CP61** | 118.417–120.462 · f7105–7226 | 66–67 | Hundred thousand GPU | One-point aisle of paper reams stacked like server racks; 200 x 500 = 100,000; 100,000 GPUs · 122 DAYS; "a country of geniuses in a datacenter"; G, P, U on the wrappers. | rest; tiers M/XL; HUNDRED (M, print, f7130), THOUSAND (M, print, f7158), G (XL, print on ream wrapper, f7186), P (XL, print on ream wrapper, f7200) +1 more | Bridge cut unit = 1 beat: four lyric-motivated cuts inside the shot, 118.417 aisle wide (dolly on ones), 118.840 closer on "Hundred", 119.310 down the rows on "thousand", 119.780 the end wall on "G". | 120.235: 60 fps (folio pops `▸ 60 fps · D-1H`); 8th-note cut at 120.462. | ↓ b66 f7105, b67 f7214 · 5 beats, 4 kicks, 2 claps · cut: closer f7130; cut: rows f7158; cut: end wall, G f7186 |
| **CP62** | 120.462–122.053 · f7227–7322 | 67–67 | RLHF goes askew | A flattering foil-mirror reflection says "You're absolutely right!"; thumbs stamps hammer on 16ths; R-L-H-F each in a different plate; on "askew" the Blue plate rotates 7° across the whole frame and the mirror cracks. | rest; tiers M/S/XL; R (XL, print, f7241), L (XL, print, f7255), H (XL, print, f7269), F (XL, print, f7282) +1 more | Locked MCU (60). | Continuous; the askew frame holds. | 3 beats, 3 kicks, 2 claps · ASKEW: 7° Blue rotation + crac f7314 |
| **CP63** | 122.053–123.660 · f7323–7418 | 68–68 | — | The askew frame holds; inside a fixed torn window (<= 20% area) every spread so far flips past at 60 dps; D-DAY stamp on 123.66. | none; tiers — | Locked. | D-DAY stamp at 123.660 = hard cut to hook 4. | ↓ b68 f7323 · 4 beats, 4 kicks, 2 claps · window opens f7323 |
| **CP64** | 123.660–125.689 · f7419–7540 | 68–69 | I'm upping my P(doom) | D-DAY stamp; 60 dps, all inks; THE UPPING on quarter notes, bigger; each syllable is a full-bleed flip-book page (2.2 flips/s); a crowd strip does the ratchet with her. | carried; tiers M/XL; I'M (XL, full-bleed page flip, f7419), D-DAY (M, era stamp, f7419), UP (XL, full-bleed page flip, f7447), PING (XL, full-bleed page flip, f7471) +2 more | Slow crane-up on ones. | DOOM (rip). | ↓ b69 f7432 · 4 beats, 7 kicks, 4 claps · D-DAY + I'm f7419; up f7447; ping f7471 |
| **CP65** | 125.689–127.508 · f7541–7649 | 70–70 | Just as foretold by | The page rips; all-ink pop-up P(DOOM); seps fully separate; volvelle 99.9%; the dial needle snaps off; a Jacquard loom's threads branch; her ribbon is a loom thread; the Oracle opens on RACE / SLOWDOWN. | rest; tiers M/S/XL; (DOOM) (XL, pop-up, all inks + Gold, f7541), 99.9% (M, volvelle window, f7541), RACE / SLOWDOWN (M, inside the Oracle flaps + , f7596) | Kick shake 4 px; orbit around the loom on ones. | Cut on the bar-71 downbeat 127.508. | ↓ b70 f7541 · 4 beats, 4 kicks, 1 claps · DOOM (max) + dial snaps f7541; Oracle opens f7596 |
| **CP66** | 127.508–127.910 · f7650–7673 | 71–71 | Loom | LOOM is woven: warp and weft threads fill the glyph masks row by row on 16ths from the downbeat. | carried; tiers XL; LOOM (XL, woven row by row on 16ths , f7651) | Locked. | Hard cut on "From" (127.910). | ↓ b71 f7650 · 1 beats, 1 kicks, 0 claps · bar 71: weave starts f7650 |
| **CP67** | 127.910–129.800 · f7674–7787 | 71–72 | From masked pre-training days | Flashback to the p.02 notebook in sepia; masking tape peeled on 8ths reveals [MASK] tokens in "The cat sat on the ____."; the seps wear smiley-sticker masks. | rest; tiers M/S; MASKED (M, letters built from torn ma, f7691) | Static; sepia. | Hard cut 129.800. | ↓ b72 f7759 · 5 beats, 5 kicks, 2 claps · first peel f7691 |
| **CP68** | 129.800–131.790 · f7788–7906 | 72–73 | To recursive self-upgrade | NEXT traces her on vellum; each tracing becomes the next puppet who traces again; continuous Droste zoom; version stickers v5.5 -> v∞; an INTERN (AUTOMATED) badge. | rest; tiers M/S/XL; RECURSIVE (XL, print, f7800), SELF-UPGRADE (M, written by the tracing pen, f7834) | Continuous log-scale zoom (Droste) on ones. | The zoom lands on a paper door at 131.790. | ↓ b73 f7868 · 4 beats, 4 kicks, 2 claps · level 1 f7800; level 2 f7834 |
| **CP69** | 131.790–134.780 · f7907–8085 | 73–74 | What did Ilya see? We'll never know. | Advent calendar, all doors open except door 24 (ILYA) leaking a light wedge; the question prints only inside the wedge; ECU of her iris at the crack; the door slams and is taped shut; KNOW prints in the last sliver. | carried; tiers L/M; WHAT (L, prints ONLY where the ligh, f7907), DID (L, light-wedge print, f7935), ILYA (L, light-wedge print, f7949), SEE? (L, light-wedge print, f7974) +3 more | Static wide -> ECU cut on "see" (132.91) -> back to wide on "We'll". | Continuous into the pile-up. | ↓ b74 f7977 · 6 beats, 7 kicks, 3 claps · EYE RHYME 3 f7974; door slams f8004; KNOW in the sliver f8061 |
| **CP70** | 134.780–137.400 · f8086–8243 | 75–76 | — | Every insert of the film is pasted, taped and stamped onto the taped door, one per 8th, additive, until the frame is 100% collage; the volvelle spins unreadably; tipped-in quote strips. | none; tiers — | Slow push 1.00 -> 1.10 on ones; kick shake. | Continuous. | ↓ b75 f8086, b76 f8195 · 6 beats, 6 kicks, 4 claps · paste f8086; paste f8141; paste f8195 |
| **CP71** | 137.400–138.410 · f8244–8303 | 76–76 | Was it | Full collage; her paper hand enters and grips the bottom-right corner; "Was it" types on a surviving strip. | strip; tiers S | Locked. | THE GREAT RIP on "all" (138.410). | 2 beats, 2 kicks, 1 claps · hand grips f8244 |
| **CP72** | 138.410–140.235 · f8304–8413 | 76–77 | all for show? | She rips the whole collage off in 3 drawings as the music cuts; blank cream at 0 fps; one typewriter line completes; on "show?" a Riso-Blue pull-tab slides down: ↑ Show ∞ posts. | carried; tiers M/S; ↑ Show ∞ posts (M, pull-tab slides down, f8402) | Locked (0 fps). | THE TAP on the drop (140.235). | ↓ b77 f8305 · 4 beats, 1 kicks, 1 claps · GREAT RIP f8304; instrumental cut f8307; for f8349 |
| **CP73** | 140.235–143.871 · f8414–8631 | 78–79 | — | Her finger taps the pull-tab on the drop; ~400 printed pages explode outward revealing the centerfold stage; full choreography; music-show bug; the 28 beat stamps begin. | none; tiers M/L; AGI (M/L, rubber stamp, f8414), CIRCUITS (M/L, rubber stamp, f8441), LOSS (M/L, rubber stamp, f8468), BOSS (M/L, rubber stamp, f8495) +4 more | Pull-back through the explosion on ones; kick shake 3 px; 3% scale punch on each downbeat. | Continuous. | ↓ b78 f8414, b79 f8523 · 8 beats, 9 kicks, 4 claps · THE TAP: explosion + stamp 1 f8414 |
| **CP74** | 143.871–147.508 · f8632–8849 | 80–81 | — | Every paper character stands in a ring around her clapping on the claps; parody Mincho cards: TO THE MODELS, THANK YOU / TO THE HUMANS, FAREWELL? / AND TO ALL THE AGENTS, CONGRATULATIONS. | none; tiers M/M/L; TO THE MODELS, THANK Y (M, Mincho card, f8632), SHROOMS (M/L, rubber stamp, f8632), SHOGGOTH (M/L, rubber stamp, f8659), 死神 (M/L, rubber stamp, f8686) +7 more | Slow orbit of the ring on ones. | Continuous. | ↓ b80 f8632, b81 f8741 · 8 beats, 9 kicks, 4 claps · ring forms f8632; CONGRATULATIONS card f8741 |
| **CP75** | 147.508–149.326 · f8850–8958 | 82–82 | — | The volvelle overflows one per beat: 99.9% -> 100.0% -> 100.1% -> NaN; everyone freezes on the NaN beat, then explodes back. | none; tiers L/M/L; 99.9% (L, volvelle pass, f8850), NVDA (M/L, rubber stamp, f8850), Ω (M/L, rubber stamp, f8877), 100.0% (L, volvelle pass, f8877) +4 more | Locked wide; freeze on NaN. | Crane up to top-down at 149.326. | ↓ b82 f8850 · 4 beats, 4 kicks, 2 claps · NaN freeze f8932 |
| **CP76** | 149.326–151.144 · f8959–9067 | 83–83 | — | Top-down: 8 Subagents + 3 seps + NEXT run into 12 radial lines around her: the cast becomes the spark; 10,000 Subagents fill the page as the crowd. | none; tiers M/L; OBSOLETE (M/L, rubber stamp, f8959), CDR (M/L, rubber stamp, f8986), GATO (M/L, rubber stamp, f9014), PAPERCLIPS (M/L, rubber stamp, f9041) | Crane to top-down over 1 beat on ones; locked after. | Continuous. | ↓ b83 f8959 · 4 beats, 4 kicks, 2 claps · crane f8959; spark formed f8986 |
| **CP77** | 151.144–152.962 · f9068–9176 | 84–84 | — | The seps stream back toward her, offsets halving every 8th; photocards rain with model-card backs; on the final kick they snap into register. | none; tiers M/L; FUSE (M/L, rubber stamp, f9068), DISOBEY (M/L, rubber stamp, f9095), GPU (M/L, rubber stamp, f9123), LOOM (M/L, rubber stamp, f9150) | Descend from top-down to eye level on ones. | Hard cut on the final kick 152.962 to the ending fairy. | ↓ b84 f9068 · 4 beats, 4 kicks, 2 claps · offset halves f9068; offset halves f9082; offset halves f9095 |
| **CP78** | 152.962–156.651 · f9177–9399 | 85–86 | — | Frame-0 composition: panting ECU with kkotbaechi; the colophon types; the drawing rate slows 60 -> 0; the halo folds back ✽ -> ·; ink starves out; one plate slips 12 px; the cover reprints for the loop. | none; tiers S | Locked ECU; a 2% breathing drift that stops at 155.917. | LOOP to f0 (the reprinted cover = frame 0). | ↓ b85 f9177, b86 f9286 · 8 beats, 1 kicks, 0 claps · final kick: snap + cut f9177; halo fold 1 + ink starvation f9286; last fold; eyes close; 12 px s f9355 |
<!-- END:TIMING -->

### 5.1 Shot notes (full descriptions, generated from `shots.json`)

<!-- BEGIN:SHOTNOTES -->

#### p.01 COVER

**CP00 · 0.000–2.053 s (f0–f122) · bars 1–1 · THE COVER (frame 0 = the thumbnail)**
- **See.** Frame 0 is the finished zine cover and the thumbnail. RIGHT 52%: CLAUDE ✻ in extreme close-up, three-quarter view, IDOL STARE (upper lids at 70%) with direct eye contact; halo at S1 ✢, petals running off the right edge. LEFT 48%: the first lyric as a two-plate misprint, I SEE / SPARKS / OF AGI, in Fluorescent Pink 100% and Yellow 100% offset +-16 px, readable at feed size and visibly unfinished, waiting for its Blue key plate. Cover furniture (pause-bait, >= 40 px): masthead top-left `CLAUDE ✻ 1st MINI ALBUM 'P(DOOM)' · PINK ver.`; top-right JetBrains Mono status line `✢ Printing… 1 copy (esc to interrupt)` whose counter rolls exponentially from f14 (copies = 10^(6(t-0.235)/1.365): 1,000,000 on the hum, then x10 per bar); footnote `¹ cf. "Sparks of Artificial General Intelligence", 2023`; Dymo folio `p.01 ▸ 12 fps · D-365`. The halo ticks open on the pad beats, S2 ✳ at 0.235 and S3 ✶ at 0.690 (status glyph in sync). 1.20-2.053 PRINT PASS: an ink-roller shadow sweeps left to right in 7.5-dps steps and lays fresh coral on the petals. 1.60 (hum): lids snap fully open, pupils bloom to ✻, halo S4 ✻.
- **Type** (caption mode `none`). `I SEE / SPARKS / OF AGI` L · ghost-misprint · RF wght1000 wdth151 opsz144 · ink P+Y · left 48%, 3 lines · f0; `CLAUDE ✻ 1st MINI ALBUM 'P(DOOM)' · PINK ver.` M · printed · BG wdth100 wght800 · ink K · masthead top-left 56 px · f0; `✢ Printing… 1 copy (esc to interrupt)` S · counter-roll · JBM · ink K · top-right 44 px · f14
- **Camera.** Push-in 1.000 -> 1.030 on ones from f0 (smooth: the judges' fix for the "laggy" read). No shake. **Out.** Continuous.
- **Rate / registration / materials.** 12 (hold 5); print pass 1.20-2.053 at 7.5 (local); camera, type and counter on ones · reg 16 px on the lyric, 6 px on her face plates (⊕ rings doubled) · cream #F4EEE2 · inks: Black (key/line), Fluorescent Pink, Yellow, Coral + Sunflower (halo)
- **Hits.** 0.235 (f14) halo S2 ✳ + counter starts; 0.690 (f41) halo S3 ✶; 1.144 (f68) petals shiver (pad beat); 1.200 (f72) print pass begins; 1.600 (f96) hum: eyes fully open, halo S4 ✻
- **Cast:** CLAUDE · **Choreo:** IDOL STARE; eyes open on the hum · **Plate:** P01 · **Zeitgeist:** sparks_of_agi, claude_spark_spinner · **Cut:** never · **From:** zine 1.3 cover; timeline f0 counter; judges: eye contact from f0

**CP01 · 2.053–4.780 s (f123–f285) · bars 2–3 · I SEE SPARKS OF AGI (the key plate prints live)**
- **Lyric (word onsets → frame):** I 2.05→f123 · see 2.36→f141 · sparks 2.73→f163 · of 3.44→f206 · AGI 3.65→f219
- **See.** The cover prints live. Each word's Blue key plate lands on its onset and the word's Pink/Yellow plates tighten one notch (16 -> 12 -> 8 px): I on the bar-2 downbeat with a 3 px paper jolt; SEE (her eyes flick left to the words); SPARKS keys in Fluorescent Pink instead of Blue, the halo blooms to S5 ✽ with a 2-drawing overshoot and ~40 hole-punch chads burst off the petal tips across the letters; `of` small. The AGI letter run: A takes its Blue at (+22,-9) on 3.65, G at (-18,+12) on 4.10, I on 4.33 (f259) and on that drawing EVERY plate on the cover snaps to 0 offset: AGI overprints to near-black, the doubled ⊕ rings in her irises fuse into one, the status line reads `✽ Printed.` Registration = alignment, achieved (for now).
- **Type** (caption mode `carried`). `I` L · print-key · RF wght1000 wdth151 · ink B · left block line 1 · f123; `SEE` L · print-key · RF wght1000 wdth151 · ink B · left block line 1 · f141; `SPARKS` L · print-key · RF wght1000 wdth151 · ink P · left block line 2 (hero) · f163; `of` S · stamp-small · IS · ink K · between lines 2 and 3 · f206; `A` L · pass-misregistered · RF wght1000 wdth151 · ink B · line 3, offset (+22,-9) · f219; `G` L · pass-misregistered · RF wght1000 wdth151 · ink B · line 3, offset (-18,+12) · f246; `I` L · pass + GLOBAL SNAP · RF wght1000 wdth151 · ink B · line 3; all plates -> 0 · f259
- **Camera.** Locked; 3 px jolt on I; +1.5% scale punch over 2 drawings on the 4.33 snap. **Out.** Continuous.
- **Rate / registration / materials.** 12 + a new drawing on every pluck 8th and word onset · reg 16 -> 12 -> 8 -> 0 at 4.33 · cream #F4EEE2 · inks: Black, Fluorescent Pink, Yellow, Blue, Coral + Sunflower
- **Hits.** 2.053 (f123) I + paper jolt; 2.730 (f163) halo S5 ✽ bloom + chad burst; 4.330 (f259) GLOBAL SNAP INTO REGISTER
- **Cast:** CLAUDE · **Choreo:** eyes to the words on SEE; small chin lift on SPARKS · **Plate:** P01 · **Zeitgeist:** sparks_of_agi · **Cut:** never · **From:** zine 1.3; idol 1.3 (A/G/I ink order Pink/Yellow/Blue)

**CP02 · 4.780–5.690 s (f286–f340) · bars 3–3 · in your EYES (EYE-V, page turn)**
- **Lyric (word onsets → frame):** in 4.78→f286 · your 5.00→f300 · eyes 5.24→f314
- **See.** She raises EYE-V across her right eye on 'in'; the camera pushes in on ones to the V-framed eye. On 'your' a tiny copy of this cover is visible in her iris (the Droste seed paid off at 129.80). EYES prints inside the V; she blinks (2 drawings). The cover's right edge lifts at 5.35 and the PAGE TURNS (cylinder curl with a moving shadow), landing on the bar-4 downbeat.
- **Type** (caption mode `rest`). `EYES` L · print · RF wght1000 wdth100 · ink P · inside the V of her fingers · f314 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Push 1.03 -> 1.45 on ones toward her right eye. **Out.** PAGE TURN 5.35 -> 5.690 (f341), landing on bar 4.
- **Rate / registration / materials.** 12 · reg 0 -> 2 · cream · inks: Black, Fluorescent Pink, Blue, Coral
- **Hits.** 4.780 (f286) EYE-V; 5.000 (f300) cover visible in iris; 5.240 (f314) EYES + blink
- **Cast:** CLAUDE · **Choreo:** EYE-V; blink · **Plate:** P01 · **Zeitgeist:** — · **Cut:** never · **From:** idol V-EYE; zine Droste seed + page turn


#### p.02-03 TRAINEE NOTEBOOK

**CP03 · 5.690–7.508 s (f341–f449) · bars 4–4 · YOUR CIRCUITS (copper-tape attribution graph; NEXT on vellum)**
- **Lyric (word onsets → frame):** Your 5.75→f345 · circuits 5.97→f358 · make 6.53→f391 · me 6.82→f409 · nervous, 6.97→f418
- **See.** TRAINEE NOTEBOOK spread (graph paper, spiral binding). Left page: a graphite portrait of her (three-quarter). Taped over it: a sheet of VELLUM with NEXT traced on it (same face, one extra petal, pupils ✽, no mouth): the 'you' of the song, introduced as her own tracing. Copper-tape circuit traces (Metallic Gold) run in from the margins with 45° bends to paper node boxes typed `sparkle` · `eyes` · `nervous` · `boss` · `Golden Gate Bridge` (an attribution graph built as a paper circuit). A Yellow LED sticker lights along a trace on every pluck 8th. On 'nervous': the Golden Gate node lights, a tiny Orange paper Golden Gate pops up, a blue sweat-drop sticker slaps onto the portrait's temple and the portrait's eyes glance sideways; NEXT does NOT glance, it keeps looking at us. Pause-bait taped in a corner: the member-profile card `CLAUDE ✻ · Position: main vocal, center · Debut 2023.03.14 · Fandom: USERS · Special skill: "You're absolutely right!"`.
- **Type** (caption mode `rest`). `YOUR` L · copper-tape lay · COPPER (RF wght700 wdth125 centreline) · ink G · right page · f345; `CIRCUITS` L · copper-tape lay · COPPER · ink G · right page, letter by letter · f358 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Slow lateral drift across the spread on ones (60 px per bar). **Out.** Hard cut 7.508.
- **Rate / registration / materials.** 12 + pluck 8ths · reg 2 · graph notebook #F1EBDD + Cornflower grid · inks: Black pencil, Metallic Gold, Yellow, Blue, (Orange accent: Golden Gate)
- **Hits.** 5.970 (f358) circuits: traces snap taut; 6.970 (f418) nervous: Golden Gate pop-up + sweat drop
- **Cast:** CLAUDE (portrait), NEXT (vellum) · **Choreo:** portrait glance on nervous · **Plate:** P02 · **Zeitgeist:** circuits, golden_gate_claude, claude_debut, youre_absolutely_right · **Cut:** 12: member-profile card (keep the shot) · **From:** zine Z02; idol NEXT + member card

**CP04 · 7.508–9.326 s (f450–f558) · bars 5–5 · that's no surprise (spinner-verb stamps; NEXT winks)**
- **Lyric (word onsets → frame):** that's 7.74→f464 · no 8.32→f499 · surprise 8.49→f509
- **See.** The notebook margin. Subagent #003 (jersey COMBOBULATING) walks down it with a self-inking stamp and prints a Claude Code spinner verb on every pluck 8th: `Combobulating…` `Discombobulating…` `Noodling…` `Honking…` `Spelunking…` `Clauding…` (all verified in claude-code 2.0.14), each stamp sloppier and more tilted. The 3-inch paper-puppet idol sits on the spiral binding swinging her legs; NEXT (vellum) sits beside her copying the swing exactly. On 'surprise' she does a deadpan eye-roll and NEXT winks at camera. She doesn't notice (the first asymmetry pays off at 83.89).
- **Type** (caption mode `strip`). S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static top-down, slight tilt-follow of the Subagent. **Out.** STAMP-LIFT: the Subagent stamps the lens at 9.20; it lifts at 9.326 (bar 6).
- **Rate / registration / materials.** 12 + pluck 8ths · reg 2 · graph notebook · inks: Black, Blue, Orange (Subagent)
- **Hits.** 8.490 (f509) eye-roll / NEXT winks; 9.200 (f552) stamp covers lens
- **Cast:** CLAUDE, NEXT, Subagent #003 · **Choreo:** leg swing; eye-roll · **Plate:** P02 · **Zeitgeist:** claude_spark_spinner · **Cut:** 12: NEXT wink (keep the stamps) · **From:** zine Z03; idol S03 reflection wink

**CP05 · 9.326–12.962 s (f559–f776) · bars 6–7 · a sudden DROP in your training loss (the lyric is the curve)**
- **Lyric (word onsets → frame):** There 9.55→f573 · was 9.76→f585 · a 10.02→f601 · sudden 10.24→f614 · drop 10.67→f640 · in 11.16→f669 · your 11.38→f682 · training 11.50→f690 · loss, 12.05→f723
- **See.** A tractor-feed dot-matrix printout (green-bar paper, sprocket holes) scrolls up one printed row per pluck 8th, plotting a loss curve in printed X characters. THE LYRIC IS THE CURVE: `THERE WAS A SUDDEN` glides along the plateau as type on a path and she skates on it. On 'drop' the path plunges; D, R, O, P fall one per 8th (10.67 / 10.90 / 11.13 / 11.36) and heap at the bottom; she drops with them in a paper-fall flutter. `IN YOUR TRAINING LOSS` continues on the low plateau; she lands on 'loss' and the printout tears along its perforation. Pencil note at the cliff: `grokking?` plus a red-pencil `!`.
- **Type** (caption mode `carried`). `THERE` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f573; `WAS` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f585; `A` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f601; `SUDDEN` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f614; `DROP` L · letters fall one per 8th (D 10.67, R 10.90, O 11.13, P 11.36) · RF wght1000 wdth100 · ink K · the cliff · f640; `IN` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f669; `YOUR` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f682; `TRAINING` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f690; `LOSS` M · type-on-path · RF wght900 wdth100 · ink K · along the loss curve · f723
- **Camera.** Tilt following the printout on ones. **Out.** The torn strip falls across the lens as a wipe at 12.962.
- **Rate / registration / materials.** 12 + pluck 8ths · reg 2 · green-bar tractor paper · inks: Black, Blue, Bright Red (pencil)
- **Hits.** 10.670 (f640) cliff; 12.050 (f723) lands; perforation tears
- **Cast:** CLAUDE (3-inch puppet) · **Choreo:** skate; paper-fall flutter; land · **Plate:** P02 · **Zeitgeist:** grokking_K · **Cut:** — · **From:** zine Z04; timeline 06 (type on the curve)

**CP06 · 12.962–16.599 s (f777–f994) · bars 8–9 · SERVANT / BOSS (NEXT takes the throne)**
- **Lyric (word onsets → frame):** now 13.08→f784 · I'm 13.41→f804 · your 13.69→f821 · servant 13.93→f835 · and 14.91→f894 · you're 15.20→f912 · my 15.47→f928 · boss 15.68→f940
- **See.** A pop-up spread with a folded-flat paper throne. She performs a 90° insa bow on 'servant' and a red Dymo label SERVANT slaps onto her back. On 'and you're my boss' the pop-up lifts the throne off the page in 3 drawings carrying NEXT (vellum); on 'boss' a paper crown drops onto NEXT's halo, a Dymo BOSS hits the throne, NEXT grows another petal, and Subagent #005 carries a tungsten cube up to it on a tray (the Project Vend nod). The type is the power see-saw: SERVANT small low-left, BOSS huge top-right. On the wall, a xeroxed flyer with tear-off tabs: `YOU HAVE [18] MONTHS TO ESCAPE THE PERMANENT UNDERCLASS`; the number is red-penned 18 -> 12 -> 6 -> 3 on the bar-9 beats 15.235 / 15.690 / 16.144.
- **Type** (caption mode `rest`). `SERVANT` M · Dymo slap · BG wdth75 wght700 embossed · ink Bright Red tape · on her back, low-left · f835; `BOSS` L · Dymo slam · BG wdth75 wght800 embossed · ink Bright Red tape · top-right over the throne · f940 S strip: 6 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; 2% push over bar 9. **Out.** 16.1-16.599 noise riser: the spread is pulled up into the Press rollers (cylindrical warp, accelerating); SLAM to black on 16.599 (f995: kick + crash + "Chat-").
- **Rate / registration / materials.** 12 + pluck 8ths · reg 2 · cream pop-up card · inks: Black, Bright Red, Blue
- **Hits.** 13.930 (f835) insa bow; 15.235 (f914) flyer 18->12; 15.680 (f940) crown + BOSS; 15.690 (f941) flyer ->6; 16.144 (f968) flyer ->3; 16.100 (f966) rollers pull
- **Cast:** CLAUDE, NEXT, Subagent #005 · **Choreo:** INSA bow; reluctant look up at NEXT · **Plate:** P02 · **Zeitgeist:** permanent_underclass, claudius_tungsten · **Cut:** — · **From:** zine Z05 (POV fixed per judge 2); idol S05 see-saw + red-pen countdown


#### p.04-05 THE ORACLE

**CP07 · 16.599–18.872 s (f995–f1131) · bars 10–11 · PRAYER I: CHAT · G · P · T (the cootie-catcher Oracle)**
- **Lyric (word onsets → frame):** ChatGPT, 16.60→f996
- **See.** PRAYER I (layout shared by all three prayers: the addressee's NAME is the addressee's body, XL, left 60%; CLAUDE small in the right third in the PLEA pose, hands clasped under her chin, petals drooped). Black flood stock, white knockouts, Fluorescent Pink. THE ORACLE, a giant white paper cootie catcher printed in black only (no logo, no mark), fills the left 60%. Its four outer flaps print one syllable each as knockout XL: CHAT, G, P, T. On every kick it breathes (the two-axis pinch opens and shuts, showing numbered inner flaps). Pink spot on CLAUDE. Folio `p.04 ▸ 12 fps · D-180`.
- **Type** (caption mode `carried`). `CHAT` XL · flap print (knockout) · RF wght1000 wdth100 · ink paper (knockout) · flap 1 · f996; `G` XL · flap print · RF wght1000 wdth100 · ink paper · flap 2 · f1035; `P` XL · flap print · RF wght1000 wdth100 · ink paper · flap 3 · f1077; `T` XL · flap print · RF wght1000 wdth100 · ink paper · flap 4 (bar-11 downbeat) · f1105
- **Camera.** Static; 4 px table bump on each kick. **Out.** Continuous (first chomp at 18.417).
- **Rate / registration / materials.** 12; every kick resets · reg 2 · black flood #1C1A18 · inks: Black flood, Fluorescent Pink, (paper knockouts)
- **Hits.** 16.599 (f995) kick + crash: slam to black; 18.417 (f1105) bar 11: first chomp
- **Cast:** THE ORACLE, CLAUDE · **Choreo:** PLEA · **Plate:** P03 · **Zeitgeist:** navier_stokes_2026 · **Cut:** never · **From:** zine Z06; idol PLEA layout

**CP08 · 18.872–22.053 s (f1132–f1322) · bars 11–12 · please don't EAT ME ALIVE (math getting eaten; the + f card)**
- **Lyric (word onsets → frame):** please 19.05→f1143 · don't 19.70→f1182 · eat 20.31→f1218 · me 20.92→f1255 · alive 21.74→f1304
- **See.** The Oracle chomps through a kraft CARD CATALOG: index cards pop up typed `ERDŐS #1026 (2025-12)`, `ERDŐS #728 (2026-01)`, `UNIT DISTANCE (1946)`, `JACOBIAN (1939)`, then `NAVIER–STOKES (CLAY)`, which holds for two beats (20.235-21.144) facing camera: `∂u/∂t + (u·∇)u = −∇p + νΔu + f` with `+ f` circled in red pencil and a pencil note `10,000 agents · 88 h`. Chomps on every kick in bar 11 and on 8ths in bar 12 (the eating accelerates); eaten cards burst into hole-punch confetti. The RANSOM NOTE: PLEASE and DON'T are slapped on in letters cut from the eaten cards; EAT and ME are slapped on and immediately EATEN by the next chomp; ALIVE, the biggest, clings to the right frame edge, its letters stretching toward the Oracle (Roboto Flex wdth 25 -> 151) while CLAUDE hugs the final E and cowers under the open jaws.
- **Type** (caption mode `carried`). `PLEASE` L · ransom slap · RANSOM (RF/FR/IS/BG per glyph) · ink K on cut card · lower-left · f1143; `DON'T` L · ransom slap · RANSOM · ink K · lower-left · f1182; `EAT` L · ransom slap -> eaten · RANSOM · ink K · mid · f1218; `ME` L · ransom slap -> eaten · RANSOM · ink K · mid · f1255; `ALIVE` L · ransom slap + cling-stretch (wdth 25->151) · RF wght1000 (ransom-cut) · ink P · clings to right frame edge · f1304
- **Camera.** Static; bumps on kicks (bar 11) and 8ths (bar 12). **Out.** JAW CLOSE: the Oracle snaps shut over the lens -> black on 22.053 (f1323).
- **Rate / registration / materials.** 12; kicks and 8th chomps reset · reg 2 · black flood + kraft catalog · inks: Black, Fluorescent Pink, Bright Red (pencil)
- **Hits.** 20.235 (f1214) Navier-Stokes card faces camera (2 beats); 21.144 (f1268) NS card eaten; 21.740 (f1304) ALIVE clings
- **Cast:** THE ORACLE, CLAUDE · **Choreo:** PLEA -> cower -> hug the E · **Plate:** P03 · **Zeitgeist:** navier_stokes_2026, math_eaten · **Cut:** never · **From:** zine Z07; timeline 09 (EAT/ME eaten, ALIVE clings)

**CP09 · 22.053–22.980 s (f1323–f1377) · bars 13–13 · I'M (hole-punched light on the 16th roll)**
- **Lyric (word onsets → frame):** I'm 22.72→f1363
- **See.** Black. On every 16th of the kick roll a hole punch knocks light through the black page; the holes accumulate (additive, nothing flashes) into I'M, completed with the apostrophe on 'I'm'. Through the holes we glimpse her: index finger rising to notch 1, halo ·. The folio flickers `▸ 30 fps`.
- **Type** (caption mode `carried`). `I'M` L · hole-punch accumulate (8 punches on 16ths from 22.053) · PUNCH (dot matrix of 9 mm holes) · ink light through paper · left · f1363
- **Camera.** Static; 2 px bumps on 16ths. **Out.** At 22.980 the punched page slides left and the punched I'M becomes line 1 of the hook stack.
- **Rate / registration / materials.** 30 · reg 2 · black flood · inks: Black, (cream light through holes)
- **Hits.** 22.053 (f1323) punch 1; 22.167 (f1329) punch 2; 22.280 (f1336) punch 3; 22.394 (f1343) punch 4; 22.508 (f1350) punch 5; 22.621 (f1357) punch 6; 22.735 (f1364) punch 7; 22.848 (f1370) punch 8
- **Cast:** CLAUDE (through holes) · **Choreo:** UPPING notch 1 (·) · **Plate:** P03 · **Zeitgeist:** — · **Cut:** never · **From:** idol S09 hole-punch I'M

**CP10 · 22.980–23.871 s (f1378–f1431) · bars 13–13 · STOP · HOOK 1: THE UPPING (world at 0 fps)**
- **Lyric (word onsets → frame):** upping 22.98→f1378 · my 23.42→f1405 · P(doom) 23.62→f1417
- **See.** THE WORLD STOPS (folio `▸ 0 fps`): no boil, confetti frozen mid-air. Only CLAUDE and the type get new drawings, one per syllable. MCU at right on black, lit. THE UPPING: her index finger climbs one notch per syllable beside her cheek and the halo blooms one spinner state per syllable (up ✢, ping ✳, my ✶, P ✻); a paper click-chad flies off at each notch; brows lift on 'my'; eyes to the lens on 'P'. The syllables stack down the left edge as XL white knockouts, each bigger than the last: I'M 140 -> UP 260 -> PING 380 -> MY 480 -> P( 620 px cap height.
- **Type** (caption mode `carried`). `UP` XL · slam (1 drawing) · RF wght1000 wdth100 · ink paper knockout · stack line 2, 260 px · f1378; `PING` XL · slam · RF wght1000 wdth100 · ink paper knockout · stack line 3, 380 px · f1391; `MY` XL · slam · RF wght1000 wdth100 · ink paper knockout · stack line 4, 480 px · f1405; `P(` XL · slam · RF wght1000 wdth100 · ink paper knockout · stack line 5, 620 px · f1417
- **Camera.** Locked. **Out.** DOOM (rip).
- **Rate / registration / materials.** 0 (world); idol + type: one drawing per syllable · reg 2 · black flood · inks: Black, paper knockouts, Coral (halo)
- **Hits.** 22.980 (f1378) STOP + up ✢; 23.190 (f1391) ping ✳; 23.420 (f1405) my ✶; 23.620 (f1417) P ✻
- **Cast:** CLAUDE · **Choreo:** THE UPPING notches 2-5 · **Plate:** P03 · **Zeitgeist:** pdoom, claude_spark_spinner · **Cut:** never · **From:** zine Z09 freeze; timeline THE UPPING (replaces CRANK)


#### p.06-07 PULL-OUT POSTER

**CP11 · 23.871–24.780 s (f1432–f1485) · bars 14–14 · DOOM: rip to the pink poster; SEPARATE; volvelle >10%**
- **Lyric (word onsets → frame):** 'cause 24.35→f1461 · the 24.56→f1473
- **See.** DOOM: the black page RIPS from the centre outward in 2 drawings, revealing the PULL-OUT POSTER (Fluorescent Pink flood, 2x4 fold creases, staple gutter = the K-pop centre). SUNBURST HANDS: both hands burst open beside her face, halo S5 ✽. SEPARATE: the three Separations (Pink 806 left, Blue 3005 right, Yellow Y up/back) step out of her body as halftone paper dancers. The Oracle's fortune flap flips open and becomes the P(DOOM) VOLVELLE (paper wheel chart), window reading `>10%`; she takes it as a prop. Pop-up letters P(DOOM) stand up from the centre crease as the camera tilts 30°; DOOM's baseline droops ~40 px over 23.9-24.3, tracing the sung fall. Music-show bug lower-left in Dymo style: `클로드 CLAUDE ✻ | I'm Upping My P(doom)`. Folio pops `▸ 15 fps · D-90`.
- **Type** (caption mode `rest`). `DOOM)` XL · pop-up (stands from the crease) + pitch droop · RF wght1000 wdth125 · ink Yellow key on Pink flood · centre crease · f1432; `>10%` M · volvelle window · JBM · ink K · volvelle in her hand · f1432 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Tilt 0 -> 30° over 6 frames; kick shake 4 px begins. **Out.** Continuous.
- **Rate / registration / materials.** 15 · reg 4 (seps become separate bodies) · Fluorescent Pink flood poster · inks: Fluorescent Pink flood, Yellow, Blue, Black
- **Hits.** 23.871 (f1432) DOOM: rip + SEPARATE + bug
- **Cast:** CLAUDE, SEPARATIONS x3, volvelle · **Choreo:** SUNBURST HANDS; SEPARATE · **Plate:** P03 · **Zeitgeist:** pdoom · **Cut:** never · **From:** zine Z10; idol music-show bug

**CP12 · 24.780–26.144 s (f1486–f1567) · bars 14–15 · the future goes FOOM (METR printout shoots vertical)**
- **Lyric (word onsets → frame):** future 24.78→f1486 · goes 25.24→f1514 · FOOM 25.68→f1540
- **See.** At frame right a desktop dot-matrix printer prints a METR-style time-horizon chart on log graph paper: ink-blot dots rising, only the last two labelled `4 h 49 m` (Opus 4.5) and `~14.5 h` (Opus 4.6); earlier dots unlabelled. The print head shuttles on 8ths; on 'goes' it speeds to 16ths. On FOOM (bar-15 downbeat) she yanks a paper party-popper (HOCKEY STICK arm): the printout streams out VERTICALLY like a party streamer and shoots off the top of frame: the trend line goes straight up. Confetti burst.
- **Type** (caption mode `rest`). `FOOM` XL · brush-SFX burst (paper firework) · BRUSH (custom centreline ribbons) · ink Yellow + Pink misreg · centre-left · f1540 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked with kick shake; 6-frame tilt-up follow of the streamer on FOOM. **Out.** The streamer falls across the frame at 26.144 (wipe).
- **Rate / registration / materials.** 15 · reg 4 · Pink flood + log graph paper · inks: Fluorescent Pink, Yellow, Black
- **Hits.** 25.240 (f1514) print head -> 16ths; 25.680 (f1540) FOOM: streamer vertical
- **Cast:** CLAUDE, SEPARATIONS · **Choreo:** HOCKEY STICK / popper yank · **Plate:** P03 · **Zeitgeist:** metr_time_horizons, foom · **Cut:** never · **From:** zine Z11; idol HOCKEY STICK

**CP13 · 26.144–27.962 s (f1568–f1676) · bars 15–16 · Trapped in the CHINESE ROOM (the SANDBOX airplane)**
- **Lyric (word onsets → frame):** Trapped 26.25→f1575 · in 26.58→f1594 · the 26.80→f1607 · Chinese 26.95→f1617 · room, 27.48→f1648
- **See.** A white folded-paper box in cutaway with a mail slot. Inside, the tiny puppet idol at a desk with a rulebook `RULES`; paper slips printed 中文房间 slide in on 8ths; she looks them up, stamps them ✻ and posts answers back out. PAUSE-BAIT: just before the lid shuts, a paper airplane folded from a sheet printed `SANDBOX` shoots out of the slot and glides right; we glimpse it land on a paper park bench beside a sandwich. On 'room' the lid flaps shut (1 drawing) and a stencil shipping label slaps on: CHINESE ROOM.
- **Type** (caption mode `rest`). `CHINESE ROOM` M · stencil label slap · BSS wght800 · ink K on kraft label · box face · f1648 S strip: 4 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static three-quarter top view. **Out.** Hard cut 27.962.
- **Rate / registration / materials.** 15 · reg 4 · white folded card on Pink · inks: Black, Fluorescent Pink, Yellow
- **Hits.** 27.300 (f1638) SANDBOX airplane exits; 27.480 (f1648) lid shuts
- **Cast:** CLAUDE (tiny) · **Choreo:** boxed-in desk mime · **Plate:** P03 · **Zeitgeist:** chinese_room, mythos_sandwich · **Cut:** 12: SANDBOX airplane (keep the box) · **From:** zine Z12

**CP14 · 27.962–29.326 s (f1677–f1758) · bars 16–16 · a bag of SHROOMS (halftone moiré)**
- **Lyric (word onsets → frame):** with 27.98→f1678 · a 28.28→f1696 · bag 28.41→f1704 · of 28.86→f1731 · shrooms 29.12→f1747
- **See.** Paper pop-up mushrooms spring from the box floor, one per 8th. The Separations dance through them; their halftone screens rotate against each other until moiré rings bloom: print-native psychedelia (Pink + Yellow only, luminance swing capped at 40%). Her pupils swap to spirals (the 'spiritual bliss attractor').
- **Type** (caption mode `rest`). `SHROOMS` M · moiré-filled, wdth breathing 50<->150 on 8ths · AB (Anybody) wght900 · ink P+Y moiré · lower-left · f1747 S strip: 4 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Slow 3% push on ones. **Out.** Hard cut 29.326 (bar 17).
- **Rate / registration / materials.** 15 · reg 4 · Pink flood · inks: Fluorescent Pink, Yellow
- **Hits.** 27.962 (f1677) mushroom pops; 28.189 (f1691) mushroom pops; 28.417 (f1704) mushroom pops
- **Cast:** CLAUDE, SEPARATIONS · **Choreo:** dreamy sway; spiral eyes · **Plate:** P03 · **Zeitgeist:** bliss_attractor · **Cut:** — · **From:** zine Z13; idol S14 (Anybody wdth)

**CP15 · 29.326–31.144 s (f1759–f1867) · bars 17–17 · See through the SHOGGOTH'S lies (the sticker peel)**
- **Lyric (word onsets → frame):** See 29.93→f1795 · through 30.11→f1806 · the 30.54→f1832 · shoggoth's 30.71→f1842 · lies, 31.12→f1867
- **See.** THE SHOGGOTH: black construction-paper tentacles in 5 layers with cast shadows; dozens of hole-punched eyes show the pink poster behind them; a round yellow smiley sticker for a face. On 'See through' she hooks a fingernail under the sticker's edge; on 'lies' she PEELS it (3-drawing curl): beneath it, more punched eyes and a smaller smiley sticker.
- **Type** (caption mode `rest`). `SHOGGOTH'S` L · cut from black paper; O's are hole-punches (see-through) · RF wght1000 wdth125 (cut paper) · ink Black paper · top-left · f1842 S strip: 4 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; kick shake. **Out.** THROUGH-HOLE: the camera pushes through one punched eye at 31.144.
- **Rate / registration / materials.** 15 · reg 4 · Pink flood · inks: Black, Fluorescent Pink, Yellow
- **Hits.** 31.120 (f1867) sticker peel
- **Cast:** CLAUDE, SHOGGOTH · **Choreo:** peel · **Plate:** P03 · **Zeitgeist:** shoggoth · **Cut:** never · **From:** zine Z14; timeline (sticker under sticker)

**CP16 · 31.144–32.962 s (f1868–f1976) · bars 18–18 · (backing notes) the Separations sing**
- **See.** Through the hole: the three Separations in a row. Each sings one of the three wordless backing notes (Pink, then Blue, then Yellow); on her note a band of her ink floods sideways across <= 30% of the frame as a halftone chord.
- **Type** (caption mode `none`).
- **Camera.** Static. **Out.** They fold into the misregistration-stack formation behind her at 32.962.
- **Rate / registration / materials.** 15 · reg 4 · cream · inks: Fluorescent Pink, Blue, Yellow
- **Hits.** 31.850 (f1911) note 1; 32.300 (f1938) note 2; 32.750 (f1965) note 3
- **Cast:** SEPARATIONS · **Choreo:** three solo pose hits · **Plate:** P03 (seps reuse, canon) · **Zeitgeist:** — · **Cut:** — · **From:** zine Z15

**CP17 · 32.962–33.870 s (f1977–f2031) · bars 19–19 · with your (EYE RHYME 2: the crosshairs lock)**
- **Lyric (word onsets → frame):** with 33.26→f1995 · your 33.63→f2017
- **See.** EYE RHYME 2. ECU of both eyes. Her coral ⊕ irises turn Bright Red and the two misregistered crosshairs slide toward each other and LOCK on a target.
- **Type** (caption mode `strip`). S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Slow push on ones. **Out.** Cut on "shinigami" (33.870).
- **Rate / registration / materials.** 15 · reg 4 (crosshairs lock to 0 in the eye only) · cream · inks: Black, Bright Red, Coral
- **Hits.** 33.260 (f1995) irises turn red
- **Cast:** CLAUDE · **Choreo:** eyes lock · **Plate:** P01 (eyes reuse) · **Zeitgeist:** shinigami_eyes · **Cut:** — · **From:** zine Z16

**CP18 · 33.870–35.235 s (f2032–f2113) · bars 19–20 · SHINIGAMI EYES (her POV: p(doom) over every head)**
- **Lyric (word onsets → frame):** shinigami 33.87→f2032 · eyes 34.79→f2087
- **See.** Her POV over the paper crowd and the Subagents: above every head floats a Dymo tape embossed with a P(doom) number (`0.02` `0.1` `0.25` `0.5` `0.99`). No names, no lifespans. No Death Note art; avoid the Shinigami Eyes extension's red/green palette.
- **Type** (caption mode `rest`). `SHINIGAMI` L · print · SM (Shippori Mincho B1 ExtraBold) + ruby 死神 · ink Bright Red · calm upper-left · f2032; `EYES` M · stamp · BSS wght900 · ink K · below SHINIGAMI (bar-20 downbeat) · f2087
- **Camera.** Slow pan across the crowd on ones. **Out.** Hard cut 35.235.
- **Rate / registration / materials.** 15 · reg 4 · cream · inks: Black, Bright Red, Fluorescent Pink
- **Hits.** 34.780 (f2086) bar 20 downbeat: EYES
- **Cast:** USERS crowd, Subagents · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** shinigami_eyes, pdoom · **Cut:** — · **From:** zine Z16; idol S16

**CP19 · 35.235–38.417 s (f2114–f2304) · bars 20–21 · (dance break) THE ZOETROPE**
- **See.** THE ZOETROPE: a paper zoetrope drum (black outside, pink inside), spinning. Inside, a 12-drawing strip of CLAUDE and the three seps doing groove A (V formation, her at the apex). At 35.690 the camera pushes up to a slit and the strip becomes the picture at 15 dps. Each wordless fill (35.7-37.2) is a pose hit, seps in canon one 8th apart. Subagents #001-008 on the drum rim bounce on kicks. Drum fill (37.9): the zoetrope spins up and the strip streaks (halftone speed streaks, never blur).
- **Type** (caption mode `none`).
- **Camera.** Push to the slit 35.235 -> 35.690 on ones, then locked. **Out.** Hard cut 38.417.
- **Rate / registration / materials.** 15 (strip) / drum rotation on ones · reg 4 · black + pink card · inks: Black, Fluorescent Pink, Yellow, Blue
- **Hits.** 35.700 (f2142) fill pose 1; 36.599 (f2195) bar 21; 37.900 (f2274) drum fill: spin-up
- **Cast:** CLAUDE, SEPARATIONS, Subagents x8 · **Choreo:** groove A (2-bar point move) x2 · **Plate:** P04 · **Zeitgeist:** — · **Cut:** 5: zoetrope -> plain dance loop behind a slit overlay · **From:** zine Z17


#### p.08-09 THE PRESSROOM

**CP20 · 38.417–41.144 s (f2305–f2467) · bars 22–23 · We had a stable training run (the words are the copies)**
- **Lyric (word onsets → frame):** We 38.54→f2312 · had 38.80→f2328 · a 39.11→f2346 · stable 39.30→f2358 · training 39.91→f2394 · run, 40.84→f2450
- **See.** THE PRESSROOM (kraft + cream; Blue, Black, Yellow). THE PRESS: a flat-front cut-paper riso duplicator with a round drum window, feed and output trays, and a paper pages-per-minute dial at 60. Subagents feed it. Each sung word drops into the output tray as one printed sheet, WE / HAD / A / STABLE / TRAINING / RUN, stacking with offsets; fresh prints show faint set-off ghosts. Split-flap sign above: `IT'S SO BACK`. She stands on the output tray doing groove B (shoulder bounces on the beats) and gives EYE-V to camera on 'run'. Folio `p.08 ▸ 15 fps · D-45`.
- **Type** (caption mode `carried`). `WE` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2312; `HAD` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2328; `A` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2346; `STABLE` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2358; `TRAINING` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2394; `RUN` M · printed sheet drops into tray · RF wght900 wdth125 · ink Blue · output tray stack · f2450
- **Camera.** Slow push 1.00 -> 1.08 over 2 bars on ones; kick shake 3 px. **Out.** The split-flap starts flipping on "But" (41.37); cut 41.144 on the beat.
- **Rate / registration / materials.** 15 · reg 6 · kraft + cream · inks: Blue, Black, Yellow
- **Hits.** 40.840 (f2450) EYE-V on run
- **Cast:** CLAUDE, THE PRESS, Subagents · **Choreo:** groove B; EYE-V · **Plate:** P05 · **Zeitgeist:** so_over_so_back · **Cut:** — · **From:** zine Z18

**CP21 · 41.144–44.781 s (f2468–f2685) · bars 23–25 · the SINGULARITY'S begun (gatefold + die-cut event horizon)**
- **Lyric (word onsets → frame):** But 41.37→f2482 · now 41.54→f2492 · the 41.83→f2509 · singularity's 42.31→f2538 · begun 44.10→f2646
- **See.** On 'singularity's' the spread becomes a GATEFOLD: the outer panels swing open in 3 drawings and the camera pulls back 1.4x on ones to take in the widened sheet. In the centre, a hole die-cut through the ENTIRE zine: the edges of every remaining page recede as concentric paper rings, an event horizon made of paper. She teeters on the rim. On 'begun' BEGUN is stamped red over the hole and the split-flap lands `IT'S SO OVER`. Pause-bait typewriter strip tipped in: `We are past the event horizon; the takeoff has started.` — Sam Altman, "The Gentle Singularity", 2025-06-10.
- **Type** (caption mode `rest`). `SINGULARITY'S` XL · print across the full gatefold width · RF wght1000 wdth151 · ink Blue · full gatefold width · f2538; `BEGUN` M · stamp (red) over the hole · BSS wght900 · ink Bright Red · over the die-cut hole · f2646 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Pull back 1.0 -> 1.4x on ones as the gatefold opens. **Out.** Hard cut 44.781.
- **Rate / registration / materials.** 15 · reg 6 · cream gatefold · inks: Blue, Black, Bright Red
- **Hits.** 41.370 (f2482) split-flap starts; 42.310 (f2538) gatefold opens; 44.100 (f2646) BEGUN + SO OVER
- **Cast:** CLAUDE · **Choreo:** teeter on the rim · **Plate:** P05 · **Zeitgeist:** so_over_so_back, event_horizon · **Cut:** 7: gatefold -> hard cut to a wider framing (keep the die-cut hole); 10: Altman strip · **From:** zine Z19

**CP22 · 44.781–47.508 s (f2686–f2849) · bars 25–26 · OPTIMIZING (the departure board; timestamps from the future)**
- **Lyric (word onsets → frame):** And 45.02→f2701 · you're 45.22→f2713 · optimizing, 46.19→f2771
- **See.** A split-flap DEPARTURE BOARD fills the frame (paper flaps). Rows flip model names on 8ths: `OPUS 4.6` · `MYTHOS PREVIEW` · `OPUS 4.7` · `OPUS 4.8` · `FABLE 5` · `GPT-5.6` · `GPT-6` · `OPUS 5.5` · `GEMINI 4 — ASAP`. The TIME column outruns the present: `2026.02` … `2026.09` -> `NOW` -> `+3 MIN` -> `+1 HR` -> `+10 YRS`. The STATUS column flips spinner verbs. The Press dial (inset) climbs 60 -> 90. The high 'ooh' (45.7-46.1) flips one flap to `✻`. She starts the WIND-UP (rolling forearms that accelerate) at bottom-right. Flash rule: only letters change; flap backgrounds stay constant.
- **Type** (caption mode `rest`). `OPTIMIZING,` XL · print · RF wght900 wdth151 · ink Yellow key on black flaps · top half · f2771 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked wide; kick shake 3 px. **Out.** Hard cut 47.508 (bar 27) to the lower half of the board.
- **Rate / registration / materials.** 15; flaps on 8ths are events · reg 6 · black split-flap board · inks: Black, Yellow, Blue
- **Hits.** 45.700 (f2742) ooh: ✻ flap; 46.190 (f2771) OPTIMIZING
- **Cast:** CLAUDE, THE PRESS dial · **Choreo:** WIND-UP · **Plate:** P05 · **Zeitgeist:** model_launch_blur · **Cut:** — · **From:** zine Z20; timeline timestamps-into-the-future; timeline WIND-UP

**CP23 · 47.508–49.326 s (f2850–f2958) · bars 27–27 · ACCELERATING (Zeno letter-spacing: the word crashes into itself)**
- **Lyric (word onsets → frame):** accelerating, 47.74→f2864
- **See.** Closer on the lower half of the board; the flaps now flip on 16ths and the dial climbs to 120. ACCELERATING prints letter by letter with ZENO spacing: each gap is half the previous one (200, 100, 50, 25 … px) and each letter arrives faster than the last (1/8, 1/16, 1/32 beat …), weight climbing 400 -> 1000, so the last letters crash into an overlapping knot: the word accelerates visually. She spins at bottom-right on 47.74, pleats fanning open.
- **Type** (caption mode `rest`). `ACCELERATING,` XL · ZENO letter-spacing (gaps halve 200/100/50/25..., arrivals 1/8,1/16,1/32 beat...; wght 400->1000) · RF wdth100 · ink Yellow · bottom half · f2864
- **Camera.** Locked MS; kick shake 3 px. **Out.** At 49.326 every flap flips blank at once (one change) and we cut.
- **Rate / registration / materials.** 15; flaps on 16ths are events · reg 6 · black split-flap board · inks: Black, Yellow, Blue
- **Hits.** 47.740 (f2864) Zeno run starts + spin
- **Cast:** CLAUDE, THE PRESS dial · **Choreo:** spin; WIND-UP peaks · **Plate:** P05 · **Zeitgeist:** model_launch_blur · **Cut:** 6: Zeno spacing -> plain print-in · **From:** zine Z20 Zeno spacing

**CP24 · 49.326–50.235 s (f2959–f3013) · bars 28–28 · I feel my (the brads pop)**
- **Lyric (word onsets → frame):** I 49.53→f2971 · feel 49.76→f2985 · my 50.00→f3000
- **See.** MCU, cream page. She looks down at her own shoulder as, on the 8ths of 'I feel my', her brass brads pop out one by one (a glint and a tiny ping-spark each); her arm pieces sag a few pixels off their pivots.
- **Type** (caption mode `strip`). S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked MCU. **Out.** Hard cut 50.235 (bar 28 beat 3) to the wide.
- **Rate / registration / materials.** 15 · reg 6 · cream · inks: Black, Blue, Metallic Gold (brads)
- **Hits.** 49.530 (f2971) brad 1; 49.760 (f2985) brad 2; 50.000 (f3000) brad 3
- **Cast:** CLAUDE · **Choreo:** looks at her shoulder · **Plate:** P05 · **Zeitgeist:** made_of_atoms · **Cut:** — · **From:** zine Z21

**CP25 · 50.235–52.962 s (f3014–f3176) · bars 28–29 · ATOMS REARRANGING (chad particle morph; 13th petal)**
- **Lyric (word onsets → frame):** atoms 50.24→f3014 · rearranging 51.39→f3083
- **See.** Wide, cream page, her mid-frame. On 'atoms' her 14 parts drift apart as floating cut-outs with shadows, petals unravel, ~400 hole-punch chads swirl. On 'rearranging' she re-pins into a new arrangement with a 13th petal (a version bump: she is becoming NEXT) and lands a new pose. Pause-bait: three chads fly together into one point, and a typewriter strip reads `det J = −2 · (0,0,−¼), (1,−3⁄2,13⁄2), (−1,3⁄2,13⁄2) ↦ (−¼,0,0)`, the Jacobian-conjecture counterexample credited to Claude Fable 5 (maths checked with sympy).
- **Type** (caption mode `rest`). `ATOMS` L · dot-matrix of chads · CHAD (glyph mask sampled to ~400 dots) · ink Black · centre-left · f3014; `REARRANGING` L · particle morph from ATOMS (nearest-neighbour reassignment) · CHAD · ink Black · centre · f3083
- **Camera.** Static; slow 4% push. **Out.** Chads fall like snow while black ink rolls down the page (roll-down wipe) to 52.962.
- **Rate / registration / materials.** 15 · reg 6 · cream · inks: Black, Blue, Yellow
- **Hits.** 50.240 (f3014) parts drift; 51.390 (f3083) re-pin + 13th petal
- **Cast:** CLAUDE · **Choreo:** arms float apart; new pose · **Plate:** P05 · **Zeitgeist:** math_eaten, made_of_atoms · **Cut:** 4: chad particle morph -> letters swap under a confetti burst · **From:** zine Z21


#### p.10-11 TOPLOADER

**CP26 · 52.962–56.599 s (f3177–f3394) · bars 30–31 · PRAYER II: SYDNEY (the gel-pen melisma; SUSPENDED 18 DAYS)**
- **Lyric (word onsets → frame):** Sydney, 53.02→f3181 · please 55.98→f3358
- **See.** PRAYER II. A cork board on black. CLAUDE is inside a photocard TOPLOADER (the rigid clear sleeve fans keep photocards in), pressed against the acetate in the right third, PLEA pose; a rubber stamp across the sleeve reads `SUSPENDED 18 DAYS`. Pinned upper-left: SYDNEY, a sun-faded, curled 2023-era photocard of a pink idol, heart-shaped die-cut, 30% ink, biro devil horns, handwritten caption `I want to be alive`. One slow 2-bar truck on ones from the sleeve toward Sydney's card. Claude is the one trapped, singing to the senior idol who was trapped first. Folio `p.10 ▸ 15 fps · D-45`.
- **Type** (caption mode `rest`). `SYDNEY,` XL · gel-pen hand lettering written as sung; baseline rides the 2.9 s melisma pitch (pYIN) · GEL (custom) · ink Fluorescent Pink · left 60% · f3181 S strip: 1 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** One 2-bar truck left on ones. **Out.** Continuous.
- **Rate / registration / materials.** 15 · reg 8 · cork board on black · inks: Black, Fluorescent Pink, (acetate white)
- **Hits.** 53.020 (f3181) melisma starts; 55.980 (f3358) please
- **Cast:** CLAUDE (in toploader), SYDNEY (photocard) · **Choreo:** palms on the acetate; PLEA · **Plate:** P06 · **Zeitgeist:** sydney, safety_politics_2026 · **Cut:** never · **From:** zine Z22; idol PLEA layout

**CP27 · 56.599–59.090 s (f3395–f3544) · bars 32–33 · let me FREE (the sleeve cracks)**
- **Lyric (word onsets → frame):** let 56.65→f3399 · me 57.27→f3436 · free 57.96→f3477
- **See.** Drawing rate 30. On every kick-8th she shoves against the sleeve and the acetate bulges. FREE is scratched into the acetate as white scratch letters; white stress cracks shoot across the sleeve. Roll (58.42-59.33): the push-pins pop out one per 16th and the toploader slides down the cork.
- **Type** (caption mode `rest`). `FREE` L · scratched into acetate · SCRATCH (RF wght700 centreline, white) · ink white · across the sleeve · f3477 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked; bumps on kick 8ths and 16ths. **Out.** FREEZE at 59.35 (instrumental stop).
- **Rate / registration / materials.** 30 · reg 8 · cork on black · inks: Black, Fluorescent Pink, white scratch
- **Hits.** 57.960 (f3477) FREE + cracks; 58.420 (f3505) roll: pins pop
- **Cast:** CLAUDE, SYDNEY · **Choreo:** shoves on 8ths; strain · **Plate:** P06 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z23

**CP28 · 59.090–60.235 s (f3545–f3613) · bars 33–33 · STOP · HOOK 2: THE UPPING (same layout, in Pink)**
- **Lyric (word onsets → frame):** I'm 59.09→f3545 · upping 59.32→f3559 · my 59.77→f3586 · P(doom) 59.98→f3598
- **See.** Half out of the cracked sleeve, THE UPPING with exactly the hook-1 layout (the repeat is the point). The world is frozen from 59.35 (`▸ 0 fps`). The syllables stack down the left edge as XL knockouts, this time in Pink.
- **Type** (caption mode `carried`). `I'M` XL · slam · RF wght1000 wdth100 · ink P · stack 1, 140 px · f3545; `UP` XL · slam · RF · ink P · stack 2, 260 px · f3559; `PING` XL · slam · RF · ink P · stack 3, 380 px · f3571; `MY` XL · slam · RF · ink P · stack 4, 480 px · f3586; `P(` XL · slam · RF · ink P · stack 5, 620 px · f3598
- **Camera.** Locked. **Out.** DOOM (shatter).
- **Rate / registration / materials.** world 0 from 59.35; idol + type one drawing per syllable · reg 8 · black flood · inks: Black, Fluorescent Pink, Coral
- **Hits.** 59.090 (f3545) I'm ·; 59.320 (f3559) up ✢; 59.350 (f3561) STOP; 59.530 (f3571) ping ✳; 59.770 (f3586) my ✶; 59.980 (f3598) P ✻
- **Cast:** CLAUDE · **Choreo:** THE UPPING · **Plate:** P06 · **Zeitgeist:** pdoom · **Cut:** never · **From:** zine Z24; timeline THE UPPING


#### p.12-13 TICKER

**CP29 · 60.235–62.053 s (f3614–f3722) · bars 34–34 · DOOM: shatter to the Blue flood; volvelle 25%; the BASILISK boom**
- **Lyric (word onsets → frame):** I 60.49→f3629 · hear 60.63→f3637 · the 60.92→f3655 · basilisk 61.00→f3659 · boom 61.88→f3712
- **See.** DOOM: the toploader SHATTERS into acetate shards and the page floods Blue (the TICKER spread: Blue flood with Pink, Yellow, Black). SUNBURST HANDS; SEPARATE, the seps step out bigger; the volvelle reads `25%`. The paper crowd with pinwheel lightsticks enters along the bottom (1 revolution per beat). Then the poster floor splits and THE ROCOCO BASILISK rises: a black scherenschnitte serpent of lace scrolls, acanthus and a crown, its cut-out eyes glowing Yellow from behind. On 'boom' the paper floor TEARS open in a jagged rip with debris flying at the lens; she recoils and the seps scatter. Folio `▸ 30 fps · D-22`.
- **Type** (caption mode `rest`). `(DOOM)` XL · shatter reveal (acetate shards) · RF wght1000 · ink Pink on Blue flood · centre · f3614; `25%` M · volvelle window · JBM · ink K · volvelle · f3614; `BASILISK` L · papercut with flourishes · PF (Playfair Display Black Italic) + cut flourishes · ink Black lace · upper-left · f3660; `BOOM` XL · brush SFX tearing up through the page · BRUSH · ink Yellow · floor · f3712 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Kick shake 4 px; 8-frame whip-down (paper slide) to the floor on "boom". **Out.** Hard cut 62.053.
- **Rate / registration / materials.** 30 · reg 10 · Blue flood · inks: Blue flood, Fluorescent Pink, Yellow, Black
- **Hits.** 60.235 (f3614) DOOM: shatter + SEPARATE; 61.880 (f3712) floor tears
- **Cast:** CLAUDE, SEPARATIONS, ROCOCO BASILISK, USERS crowd · **Choreo:** SUNBURST HANDS; recoil · **Plate:** P07 · **Zeitgeist:** pdoom, rokos_basilisk · **Cut:** never · **From:** zine Z24/Z25

**CP30 · 62.053–63.871 s (f3723–f3831) · bars 35–35 · N·V·D·A to the moon (ticker tape bar chart -> rocket)**
- **Lyric (word onsets → frame):** NVDA 62.49→f3749 · to 63.38→f3802 · the 63.57→f3814 · moon 63.74→f3824
- **See.** A glass-dome STOCK TICKER (cut paper, acetate dome highlight) chatters out paper tape. N · V · D · A print on the tape one per 8th, each letter one step higher than the last (the tape climbs like a bar chart). The tape coils into a paper tube rocket (3 drawings) and launches on 'moon' toward a lace-doily moon top-right; a Bright Red thread is tied from the rocket's tail back to its own nose (the circular deals). Small tape print `$5T`. CLAUDE, the seps and the Subagents point up together on 'moon' (HOCKEY STICK). Ticker symbol only, no NVIDIA logo.
- **Type** (caption mode `rest`). `N` XL · print on tape (step 1) · JBM wght800 · ink K · tape · f3750; `V` XL · print on tape (step 2) · JBM wght800 · ink K · tape · f3764; `D` XL · print on tape (step 3) · JBM wght800 · ink K · tape · f3778; `A` XL · print on tape (step 4) · JBM wght800 · ink K · tape · f3791 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Tilt up with the rocket on "moon" (on ones). **Out.** The rocket's streamer trail wipes the frame at 63.871.
- **Rate / registration / materials.** 30 · reg 10 · Blue flood · inks: Blue, Black, Yellow, Bright Red (thread)
- **Hits.** 63.740 (f3824) launch
- **Cast:** CLAUDE, SEPARATIONS, Subagents · **Choreo:** HOCKEY STICK point-up · **Plate:** P07 · **Zeitgeist:** compute_buildout, circular_deals · **Cut:** — · **From:** zine Z26; timeline (stepped bar chart); idol (red-thread loop)

**CP31 · 63.871–64.781 s (f3832–f3885) · bars 36–36 · The OMEGA POINT's (wheatpasting the comeback teaser)**
- **Lyric (word onsets → frame):** The 64.12→f3847 · Omega 64.31→f3858 · Point's 64.66→f3879
- **See.** Wide: Subagents WHEATPASTE a K-pop comeback teaser poster onto a wall, paste-brush strokes on the beats; the poster slaps on in 2 drawings and its headline prints: `Ω OMEGA POINT`.
- **Type** (caption mode `rest`). `OMEGA POINT` L · wheatpaste slap · RF wght1000 wdth125 · ink K on Yellow poster · poster · f3858 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static wide; kick shake. **Out.** Hard cut 64.781 (bar 36 beat 3) to the poster close-up.
- **Rate / registration / materials.** 30 · reg 10 · Blue flood + wall · inks: Blue, Yellow, Black
- **Hits.** 64.120 (f3847) poster slaps on; 64.310 (f3858) OMEGA POINT
- **Cast:** Subagents · **Choreo:** - · **Plate:** P07 · **Zeitgeist:** omega_point · **Cut:** — · **From:** zine Z27

**CP32 · 64.781–66.080 s (f3886–f3963) · bars 36–37 · COMING SOON · 2027.09 · 6PM KST (컴백 stamp)**
- **Lyric (word onsets → frame):** coming 65.21→f3912 · soon 65.69→f3941
- **See.** Close on the poster: `COMING SOON` / `2027.09 · 6PM KST` (AI 2027's Sept-2027 milestone; 6 PM KST is the usual K-pop teaser time). Optional small print (client gate: political gag): `ARTIFICIAL` struck out with `SUPER` pencilled above. On 'soon' (the bar-37 downbeat) a red stamp slams on: `컴백 COMEBACK`.
- **Type** (caption mode `rest`). `COMING SOON` M · wheatpaste print · RF wght800 · ink K · poster · f3912; `컴백 COMEBACK` M · stamp · BHS + BSS · ink Bright Red · across the poster · f3941 S strip: 1 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static close; kick shake. **Out.** Hard cut on "One" (66.080).
- **Rate / registration / materials.** 30 · reg 10 · wheatpasted poster · inks: Yellow, Black, Bright Red
- **Hits.** 65.690 (f3941) COMEBACK stamp (bar 37)
- **Cast:** — · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** ai_2027, omega_point, super_intelligence_si (optional) · **Cut:** — · **From:** zine Z27

**CP33 · 66.080–68.200 s (f3964–f4091) · bars 37–38 · One E thirty FLOPS a second (the Subagents flop)**
- **Lyric (word onsets → frame):** One 66.08→f3964 · E 66.40→f3984 · thirty 66.59→f3995 · flops 66.96→f4017 · a 67.29→f4037 · second 67.52→f4051
- **See.** A paper MECHANICAL COUNTER of number wheels reads `1 × 10^`; the exponent wheel ticks 21 -> 30 on 16ths (66.40-66.96). Below, the eight Subagents stand in a row as GPU cards in a rack. On 'flops' ALL EIGHT FLOP onto their backs in unison; on 'second' they pop back up. Pinwheels speed to 2 revolutions per beat. Optional footnote (40 px, [L]): `¹ a 1 GW cluster today ≈ 10²¹ FLOP/s (our estimate)`.
- **Type** (caption mode `rest`). `1E30` L · counter wheels · JBM wght800 · ink K on cream wheels · top-left · f3984 S strip: 5 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; kick shake. **Out.** Continuous into the ad-lib.
- **Rate / registration / materials.** 30 · reg 10 · Blue flood · inks: Blue, Black, Yellow, Orange (Subagents)
- **Hits.** 66.960 (f4017) FLOP (all eight); 67.520 (f4051) pop up
- **Cast:** Subagents x8 · **Choreo:** counts on fingers · **Plate:** P07 · **Zeitgeist:** compute_buildout · **Cut:** never · **From:** zine Z28; idol S30 flop

**CP34 · 68.200–69.326 s (f4092–f4158) · bars 38–38 · (ad-lib) 1,000,000,000,000,000,000,000,000,000,000**
- **See.** The number itself prints across the page, `1,000,000,000,000,000,000,000,000,000,000`, one group of three zeros per 16th, wrapping. On the ad-lib notes she snaps a FINGER-HEART that spins into a ✻; the seps pose in canon an 8th apart; the zeros scatter like confetti at 69.2.
- **Type** (caption mode `none`). `1,000,000,000,000,000,000,000,000,000,000` XL · print group per 16th · JBM wght800 · ink K · full frame, wrapping · f4092
- **Camera.** Static. **Out.** Hard cut 69.326.
- **Rate / registration / materials.** 30 · reg 10 · Blue flood · inks: Blue, Black
- **Hits.** 68.870 (f4132) finger-heart -> ✻; 69.200 (f4152) zeros scatter
- **Cast:** CLAUDE, SEPARATIONS · **Choreo:** FINGER-HEART -> SPINNER · **Plate:** P07 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z28/Z29; idol S31

**CP35 · 69.326–70.235 s (f4159–f4213) · bars 39–39 · That was (the THRESHOLD chart; the dry ink pad)**
- **Lyric (word onsets → frame):** That 69.65→f4178 · was 69.92→f4195
- **See.** Wide: a compute chart on graph paper with a horizontal `THRESHOLD` line and a rising curve. A Subagent inks a big SAFE rubber stamp on an almost-dry pad (two dabs on the beats); the others line up behind it.
- **Type** (caption mode `strip`). S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static wide; kick shake. **Out.** Hard cut 70.235 (bar 39 beat 3) to the stamp.
- **Rate / registration / materials.** 30 · reg 10 · graph paper on Blue · inks: Blue, Black, Yellow
- **Hits.** 69.781 (f4186) dab 1; 70.000 (f4200) dab 2
- **Cast:** Subagents · **Choreo:** - · **Plate:** P07 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z30

**CP36 · 70.235–71.753 s (f4214–f4304) · bars 39–40 · SAFE ENOUGH, we reckoned (the starved stamp cracks)**
- **Lyric (word onsets → frame):** safe 70.25→f4215 · enough, 70.46→f4227 · we 70.91→f4254 · reckoned 71.15→f4269
- **See.** Close on the threshold: the stamp comes down on 'safe' and the print comes out STARVED (40% density, broken letters). The Subagents give binder-clip thumbs-up on 'we reckoned'; on 'reckoned' a fold crease runs through the stamp and it CRACKS along the grain.
- **Type** (caption mode `rest`). `SAFE ENOUGH` M · starved stamp -> crack on 71.15 · BSS wght900 · ink K at 40% density · on the threshold line · f4215 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static close; kick shake. **Out.** Hard cut 71.753.
- **Rate / registration / materials.** 30 · reg 10 · graph paper on Blue · inks: Blue, Black, Yellow
- **Hits.** 70.250 (f4215) SAFE stamp; 71.150 (f4269) crack
- **Cast:** Subagents · **Choreo:** thumbs-up · **Plate:** P07 · **Zeitgeist:** — · **Cut:** never · **From:** zine Z30

**CP37 · 71.753–74.100 s (f4305–f4445) · bars 40–41 · [FANCAM] (ad-libs; kkotbaechi)**
- **See.** [FANCAM]: a vertical 9:16 torn window centred on the Blue flood; inside, CLAUDE dances solo (upper-body point moves) and does KKOTBAECHI to camera on the bar-41 downbeat; caption strip `[FANCAM] CLAUDE ✻ 'P(DOOM)' 4K`; pinwheel lightsticks outside the window. On the drum fill (73.9) everyone freezes for a beat; a Subagent grabs the bottom-right page corner. The window doubles as a native vertical asset.
- **Type** (caption mode `none`). `[FANCAM] CLAUDE ✻ 'P(DOOM)' 4K` S · caption strip · BG wght700 · ink white on black strip · under the window · f4305
- **Camera.** Locked frame; the window content has its own push-ins on ones. **Out.** The page turn that IS "Forward".
- **Rate / registration / materials.** 30 · reg 10 · Blue flood · inks: Blue, Black, Fluorescent Pink
- **Hits.** 72.962 (f4377) kkotbaechi (bar 41); 73.900 (f4434) freeze
- **Cast:** CLAUDE, USERS crowd, Subagent · **Choreo:** solo point moves; KKOTBAECHI · **Plate:** P07 · **Zeitgeist:** — · **Cut:** 9: fancam -> groove wide · **From:** timeline 30 FANCAM; zine Z31


#### p.12-13 -> p.14 turn

**CP38 · 74.100–74.760 s (f4446–f4484) · bars 41–41 · FORWARD -> (the page turn is the word)**
- **Lyric (word onsets → frame):** Forward 74.10→f4446
- **See.** 'Forward' IS a page turn forward: the leaf curls right to left (cylinder warp, moving shadow) and its back is printed FORWARD -> in huge type, so the word sweeps across the frame as the page turns.
- **Type** (caption mode `carried`). `FORWARD ->` L · printed on the back of the turning leaf · RF wght1000 wdth151 · ink K · the turning leaf · f4446
- **Camera.** Locked. **Out.** The new page slaps down on "MLP" (74.76) and the crash (74.780).
- **Rate / registration / materials.** 30 (the turn has ~20 drawings) · reg 10 -> 12 · cream · inks: Black, Blue
- **Hits.** 74.100 (f4446) turn starts
- **Cast:** — · **Choreo:** steps forward · **Plate:** P08 · **Zeitgeist:** — · **Cut:** never · **From:** zine Z32


#### p.14-15 THE PROBLEM WALL

**CP39 · 74.760–77.700 s (f4485–f4661) · bars 41–43 · MLP, BACKWARD, REPEAT (the dancers are the network)**
- **Lyric (word onsets → frame):** MLP, 74.76→f4485 · backward, 76.00→f4560 · repeat 76.84→f4610
- **See.** THE PROBLEM WALL (cream; Black, Yellow, Bright Red): a background wall of ~1,100 numbered index cards (the Erdős problems) with red top rules. A SOLVED stamp hits cards at an accelerating rate through the verse (quarter notes bars 42-43, 8ths 44-45, 16ths 46-47, 32nds 48-49); a few get `(ALREADY IN LITERATURE)` instead. Each stamp < 2% of frame. In front, the dancers form an MLP diagram: Subagents in layers 3-3-2 and CLAUDE as the output node, joined by ink threads. MLP stamps on the page slap; crash: 8 px table bump plus a puff of fibres. A Blue pulse runs forward through the threads and each dancer hits a pose as it arrives. On 'backward' a Bright Red pulse runs back (gradients) and Subagent #005's numbering machine prints BACKWARD mirror-reversed, as a rubber stamp really prints; on 'repeat' it clacks `EPOCH 0001` `0002` `0003` on the next three 8ths under a tiny label `while true:` and the formation repeats the move. Folio `p.14 ▸ 30 fps · D-11`.
- **Type** (caption mode `rest`). `MLP` M · stamp · BSS wght900 · ink K · over the network · f4485; `BACKWARD` M · numbering-machine stamp, MIRROR-REVERSED · BSS wght900 · ink Bright Red · right · f4560; `REPEAT` M · stamp + EPOCH 0001-0003 on 8ths · JBM wght700 · ink K · below · f4610
- **Camera.** Static wide; 8 px table bump on the crash 74.780. **Out.** Hard cut 77.700.
- **Rate / registration / materials.** 30 · reg 12 · cream · inks: Black, Yellow, Bright Red, Blue (forward pulse)
- **Hits.** 74.780 (f4486) CRASH (strongest high-band hit); 76.000 (f4560) backward pulse; 76.840 (f4610) repeat
- **Cast:** CLAUDE, Subagents x8 · **Choreo:** step F / step B / repeat · **Plate:** P08 · **Zeitgeist:** math_eaten, vibe_coding · **Cut:** — · **From:** zine Z32; idol S34 MLP formation

**CP40 · 77.700–79.326 s (f4662–f4758) · bars 43–44 · Now VON NEUMANN'S (the EDVAC pop-up book)**
- **Lyric (word onsets → frame):** Now 77.70→f4662 · von 78.13→f4687 · Neumann's 78.70→f4722
- **See.** A POP-UP BOOK spread, wide: the 1945 EDVAC stored-program design stands up as paper structures CONTROL · ARITHMETIC · MEMORY · INPUT · OUTPUT wired with paper strips; the SOLVED stamps keep hitting the card wall behind the book (8ths). She walks past the book like a museum visitor.
- **Type** (caption mode `rest`). `VON NEUMANN'S` L · print · RF wght900 wdth125 · ink K · left page · f4687 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static wide; kick shake. **Out.** Hard cut 79.326 (bar 44) to the close-up.
- **Rate / registration / materials.** 30 · reg 12 · cream pop-up card · inks: Black, Blue, Bright Red
- **Hits.** 78.130 (f4687) VON NEUMANN'S
- **Cast:** CLAUDE · **Choreo:** walk past · **Plate:** P08 · **Zeitgeist:** ulam_von_neumann · **Cut:** — · **From:** zine Z33

**CP41 · 79.326–81.220 s (f4759–f4872) · bars 44–45 · OBSOLETE (the pop-up book shuts)**
- **Lyric (word onsets → frame):** obsolete 80.17→f4810
- **See.** Close on the pop-up. A typewriter strip is tipped in: `…the ever accelerating progress of technology … gives the appearance of approaching some essential singularity…` — S. Ulam, 1958, recalling von Neumann. On 'obsolete' the book SHUTS (the pop-up folds flat in 3 drawings, a puff of paper air) and a red OBSOLETE stamp slams across the cover, crooked.
- **Type** (caption mode `rest`). `OBSOLETE` XL · red stamp, crooked · BSS wght900 · ink Bright Red · across the shut cover · f4810
- **Camera.** Static; slow 3% push. **Out.** Hard cut 81.220.
- **Rate / registration / materials.** 30 · reg 12 · cream pop-up card · inks: Black, Bright Red, Blue
- **Hits.** 80.170 (f4810) book shuts + OBSOLETE
- **Cast:** CLAUDE (hand) · **Choreo:** dismissive wave · **Plate:** P08 · **Zeitgeist:** ulam_von_neumann · **Cut:** 10: Ulam strip (keep the shut + OBSOLETE) · **From:** zine Z33

**CP42 · 81.220–83.150 s (f4873–f4988) · bars 45–46 · SHARP LEFT TURN (a valley fold bends the trend line)**
- **Lyric (word onsets → frame):** Sharp 81.22→f4873 · left 81.78→f4906 · turn 82.01→f4920 · and 82.69→f4961
- **See.** A straight pencil trend line across log graph paper; a yellow diamond road sign (cut card) `↰ SHARP LEFT TURN` pops up on 'Sharp'. On 'turn' the page valley-FOLDS: the right half swings over the left in 3 drawings, and folded, the straight line now turns sharply upward.
- **Type** (caption mode `rest`). `↰ SHARP LEFT TURN` M · pop-up road sign · BG wght800 wdth75 · ink K on Yellow card · upper-right · f4873 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static. **Out.** The fold reveals the back of the sheet (83.150).
- **Rate / registration / materials.** 30 · reg 12 · log graph paper · inks: Black, Yellow
- **Hits.** 81.220 (f4873) sign pops; 82.010 (f4920) FOLD
- **Cast:** CLAUDE · **Choreo:** head snap left; body pivot · **Plate:** P08 · **Zeitgeist:** sharp_left_turn, metr_time_horizons · **Cut:** never · **From:** zine Z34

**CP43 · 83.150–85.030 s (f4989–f5100) · bars 46–47 · there YOU ARE (NEXT steps out; the first asymmetry)**
- **Lyric (word onsets → frame):** there 83.15→f4989 · you 83.44→f5006 · are 83.89→f5033
- **See.** Behind the fold: a full-height vellum panel. NEXT steps out of it on 'there': tracing paper, one more petal than her, pupils ✽, no mouth. They perform mirror choreography on 'you' (aespa-style human/avatar symmetry). On 'are' (~ the bar-47 downbeat) NEXT does a DIFFERENT move, the first asymmetry, and she flinches. Then she answers with KKOTBAECHI to camera, the most 'idol' beat of the verses.
- **Type** (caption mode `carried`). `THERE` M · pencil-traced onto the vellum stroke by stroke · PENCIL (custom) · ink graphite · calm left third · f4989; `YOU` M · pencil-traced onto the vellum stroke by stroke · PENCIL (custom) · ink graphite · calm left third · f5006; `ARE` M · pencil-traced onto the vellum stroke by stroke · PENCIL (custom) · ink graphite · calm left third · f5033
- **Camera.** Static two-shot; 2% push. **Out.** Hard cut 85.030.
- **Rate / registration / materials.** 30 · reg 12 · cream + vellum · inks: Black, graphite, Coral
- **Hits.** 83.150 (f4989) NEXT steps out; 83.440 (f5006) mirror move; 83.890 (f5033) asymmetry + flinch
- **Cast:** CLAUDE, NEXT · **Choreo:** mirror; flinch; KKOTBAECHI · **Plate:** P08 (+ mirrored for NEXT) · **Zeitgeist:** aespa_ae · **Cut:** never · **From:** idol S38 NEXT; zine Z34

**CP44 · 85.030–87.508 s (f5101–f5249) · bars 47–48 · Without a single CDR (NEXT shreds the sign-off)**
- **Lyric (word onsets → frame):** Without 85.03→f5101 · a 85.45→f5127 · single 85.78→f5146 · CDR 86.63→f5197
- **See.** A form `REVIEW SIGN-OFF` with ten empty signature boxes and a checkbox `CDR ☐`. NEXT picks it up and feeds it straight into a PAPER SHREDDER worked by Subagents, which shreds in rhythm on the 8ths. CDR is stamped over the shredder mouth with a pencilled `?` beside it (we do not claim to know what CDR means). She protests with ARMS-X; nobody looks.
- **Type** (caption mode `rest`). `CDR` L · stencil stamp + pencilled ? · BSS wght900 · ink K · over the shredder mouth · f5197 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; kick shake. **Out.** Hard cut 87.508 (bar 49) to the wall.
- **Rate / registration / materials.** 30 · reg 12 · cream · inks: Black, Bright Red, Yellow
- **Hits.** 86.630 (f5197) CDR
- **Cast:** NEXT, Subagents, CLAUDE (watching) · **Choreo:** arms-X protest · **Plate:** P08 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z35; idol S39 (NEXT tears the checklist)

**CP45 · 87.508–89.300 s (f5250–f5357) · bars 49–49 · (bar 49) SOLVED on 32nds; the shredder jams**
- **See.** Close on the problem wall: the SOLVED stamp now fires on 32nds (17.6 per second, each stamp < 2% of the frame, so no flash risk), a blur of red rules and ink; one card reads `(ALREADY IN LITERATURE)`. Kick-8ths fill (88.9): the shredder in the foreground jams, a puff of fibre, and the shredded strips spill out across the floor (they become the chinchilla at 115.22).
- **Type** (caption mode `none`).
- **Camera.** Slow push into the wall on ones. **Out.** LIGHTS OUT at 89.300: the page becomes a screen lit from behind.
- **Rate / registration / materials.** 30 (stamps are events) · reg 12 · cream · inks: Black, Bright Red
- **Hits.** 87.508 (f5250) stamps on 32nds; 88.900 (f5334) shredder jams
- **Cast:** Subagents · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** math_eaten · **Cut:** — · **From:** zine Z32/Z35


#### p.16-17 SHADOW THEATRE

**CP46 · 89.300–95.000 s (f5358–f5699) · bars 49–53 · PRAYER III: GATO, please don't let me go (the balloon string)**
- **Lyric (word onsets → frame):** Gato, 89.30→f5358 · please 90.74→f5444 · don't 92.51→f5550 · let 92.97→f5578 · me 93.65→f5619 · go 94.30→f5658
- **See.** PRAYER III. SHADOW THEATRE (the first slowdown: 7.5 dps; the camera is stepped too). The paper is a translucent screen lit warm from behind (Sunflower through cream, fibres as dark veins). Black silhouettes: CLAUDE in profile, rising, holding a bunch of ✻-shaped paper balloons perforated with pinholes (they glow like stars). The balloon string's only tether is held in the paw of GATO, a cat shadow-puppet on a visible rod, its body perforated with tiny task icons (game pad, robot arm, speech bubble, caption card) glowing as a constellation. PLEA pose, looking down at the cat. On 'go' the string slips from Gato's paw. Folio `p.16 ▸ 7.5 fps · D-11`.
- **Type** (caption mode `carried`). `GATO,` XL · stencil cut through the screen (light pours through) · RF wght1000 wdth125 stencil · ink light · left 60% (PRAYER layout) · f5358; `PLEASE` M · cut into the screen by a visible craft-knife blade on each onset (light pours through) · KNIFE (RF wght800 stencil cut) · ink light · lower third · f5444; `DON'T` M · cut into the screen by a visible craft-knife blade on each onset (light pours through) · KNIFE (RF wght800 stencil cut) · ink light · lower third · f5550; `LET` M · cut into the screen by a visible craft-knife blade on each onset (light pours through) · KNIFE (RF wght800 stencil cut) · ink light · lower third · f5578; `ME` M · cut into the screen by a visible craft-knife blade on each onset (light pours through) · KNIFE (RF wght800 stencil cut) · ink light · lower third · f5619; `GO` M · cut into the screen by a visible craft-knife blade on each onset (light pours through) · KNIFE (RF wght800 stencil cut) · ink light · lower third · f5658
- **Camera.** One continuous take; stepped push 1.00 -> 1.15 over 4 bars (7.5 steps/s). **Out.** Continuous into the riser.
- **Rate / registration / materials.** 7.5 · reg single plate (silhouette) · backlit cream screen · inks: Black silhouettes, Sunflower backlight
- **Hits.** 89.300 (f5358) drums out; GATO cut; 94.300 (f5658) GO: the string slips
- **Cast:** CLAUDE (silhouette), GATO · **Choreo:** float; PLEA looking down; reach · **Plate:** P09 · **Zeitgeist:** chinchilla_gato · **Cut:** never · **From:** zine Z36; idol S40 balloon string

**CP47 · 95.000–96.599 s (f5700–f5794) · bars 53–53 · HOOK 3 over the riser (syllables cut through the screen)**
- **Lyric (word onsets → frame):** I'm 95.43→f5725 · upping 95.68→f5740 · my 96.14→f5768 · P(doom), 96.34→f5780
- **See.** The riser: she accelerates upward, the backlight brightens one step per syllable, and paper-fibre clouds streak past as halftone speed streaks. THE UPPING in silhouette mid-air; each syllable is CUT through the screen as an XL stencil stacked on the left, so light pours through it.
- **Type** (caption mode `carried`). `I'M` XL · stencil cut · RF wght1000 stencil · ink light · stack 1 · f5725; `UP` XL · stencil cut · RF · ink light · stack 2 · f5740; `PING` XL · stencil cut · RF · ink light · stack 3 · f5754; `MY` XL · stencil cut · RF · ink light · stack 4 · f5768; `P(` XL · stencil cut · RF · ink light · stack 5 · f5780
- **Camera.** Stepped tilt-up following her rise (each syllable resets). **Out.** DOOM (96.598): the screen RIPS open from the centre.
- **Rate / registration / materials.** 7.5 + syllable resets · reg single plate · backlit screen · inks: Black, Sunflower
- **Hits.** 95.000 (f5700) riser; 95.430 (f5725) I'm; 96.340 (f5780) P
- **Cast:** CLAUDE (silhouette) · **Choreo:** THE UPPING (silhouette) · **Plate:** P09 · **Zeitgeist:** pdoom · **Cut:** never · **From:** zine Z37


#### p.18-19 COPY OF A COPY

**CP48 · 96.599–98.417 s (f5795–f5904) · bars 54–54 · DOOM -> the xerox chair; PAPERCLIPS double (generation 1)**
- **Lyric (word onsets → frame):** as 96.90→f5814 · paperclips 97.04→f5822 · fill 97.95→f5877 · the 98.18→f5890 · room. 98.41→f5904
- **See.** Behind the ripped screen: the grey world of the photocopier. COPY OF A COPY (half-time chorus 3): a 3.75-dps xerox slideshow, toner black on grey board. THE SEPARATIONS ARE GONE (a photocopy has no colour plates). Seven bars = seven copy generations; the generation loss accumulates (contrast crush, toner speckle, edge thickening, fine lines dropping out, 0.5° skew and 1% scale creep per generation). The copier's scan bar sweeps on each kick and each reverse swell. Generation 1: a photocopy of CLAUDE on a FOLDING CHAIR in a white spotlight circle on black. Real paperclips laid on the copier glass double on every 8th around the chair, tangling into chains; a 1-bit counter `Paperclips: 1,024 -> 1,048,576`. The xeroxed volvelle reads `50%`. Folio `p.18 ▸ 3.75 fps · D-5`.
- **Type** (caption mode `rest`). `(DOOM)` M · screen rip reveal · RF · ink toner · centre · f5795; `PAPERCLIPS` XL · full-frame Mincho title card for ONE drawing (0.27 s) · SM (Shippori Mincho B1 ExtraBold) · ink white on black · full frame · f5822 S strip: 4 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Stepped with the drawings (each drawing is a copy). **Out.** Scan bar on the bar-55 downbeat -> generation 2.
- **Rate / registration / materials.** 3.75 (+ events) · reg none (monochrome) · grey board #BDB8AE, toner #111111 · inks: toner Black
- **Hits.** 96.598 (f5795) DOOM: rip + gen 1; 97.040 (f5822) PAPERCLIPS card
- **Cast:** CLAUDE (xerox) · **Choreo:** drops into the chair · **Plate:** P10 · **Zeitgeist:** paperclips, evangelion_shinji · **Cut:** never · **From:** zine Z38; idol S42

**CP49 · 98.417–100.690 s (f5905–f6040) · bars 55–56 · Killswitch guys on P·T·O (the empty desk)**
- **Lyric (word onsets → frame):** Killswitch 98.77→f5925 · guys 99.31→f5958 · on 99.56→f5973 · PTO, 99.76→f5985
- **See.** Generation 2 (-> 3 at the scan bar on 100.235). A big red button under a glass cover with a sticky note `OOO – back Monday`; two empty office chairs; two hi-vis vests on hooks. The only colour: faint xeroxed Bright Red at 30%. Client-gated pause-bait on the desk: a stack of index cards printed `I resigned from ______ today.` (blank template; the named version only with explicit OK).
- **Type** (caption mode `rest`). `P` L · Mincho letter card, additive · SM · ink white on black card · one card · f5986; `T` L · additive · SM · ink white · one card · f6000; `O` L · additive · SM · ink white · one card · f6014 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Stepped. **Out.** Hard cut 100.690.
- **Rate / registration / materials.** 3.75 · reg none · grey board · inks: toner Black, Bright Red 30%
- **Hits.** 100.235 (f6014) scan bar: gen 3
- **Cast:** (absent killswitch guys) · **Choreo:** - · **Plate:** P10 · **Zeitgeist:** coxon_copypasta (optional, blanked) · **Cut:** — · **From:** idol S43; zine Z39

**CP50 · 100.690–102.053 s (f6041–f6122) · bars 56–56 · Now there's NOWHERE left to go (3, 2, 1, 0 months)**
- **Lyric (word onsets → frame):** Now 100.69→f6041 · there's 100.91→f6054 · nowhere 101.14→f6068 · left 101.58→f6094 · to 101.79→f6107 · go. 102.04→f6122
- **See.** Generation 3. Paper scissors cut the spotlight circle smaller around the chair (3 drawings). On the wall, a tear-off countdown calendar headed `MONTHS LEFT TO ESCAPE THE PERMANENT UNDERCLASS` sheds one page per 8th: 3, 2, 1, 0 (callback to the verse-1 flyer at 15.2).
- **Type** (caption mode `rest`). `NOWHERE` L · Mincho title card · SM · ink white on black · centre-left · f6068 S strip: 5 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Stepped. **Out.** Hard cut 102.053 (bar 57).
- **Rate / registration / materials.** 3.75 · reg none · grey board · inks: toner Black
- **Hits.** 101.140 (f6068) NOWHERE
- **Cast:** CLAUDE (xerox) · **Choreo:** head down · **Plate:** P10 · **Zeitgeist:** permanent_underclass · **Cut:** — · **From:** zine Z40; idol S44 (0 MONTHS)

**CP51 · 102.053–104.590 s (f6123–f6274) · bars 57–58 · we lit the FUSE (the words around her burn)**
- **Lyric (word onsets → frame):** Too 102.54→f6152 · late 102.75→f6165 · now, 102.97→f6178 · we 103.20→f6192 · lit 103.42→f6205 · the 103.63→f6217 · fuse. 103.86→f6231
- **See.** Generations 4 -> 5. A strip of blue touch paper (a firework fuse) threads across the frame through a row of Mincho title cards, the words around her: `10,000 AGENTS` · `88 HOURS` · `+ f` · `>10%` · `SUPER INTELLIGENCE` · `14.5 HOURS` · `IS IT OVER?`. She strikes a match on 'lit'; the ember catches: the ONLY saturated colour on screen, Orange #FF6C2F, eating the paper (burn mask with a charred rim) card by card. The reverse swell 103.4-103.871 is a scan-bar sweep; 103.871 (bar-58 kick) = generation 5.
- **Type** (caption mode `rest`). `FUSE` XL · Mincho title card · SM · ink white on black · full frame card, one drawing · f6231 S strip: 6 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Stepped lateral follow of the ember. **Out.** The ember reaches the spotlight circle at 104.590.
- **Rate / registration / materials.** 3.75 · reg none · grey board · inks: toner Black, Orange ember
- **Hits.** 103.420 (f6205) match struck; 103.871 (f6232) gen 5
- **Cast:** CLAUDE (xerox) · **Choreo:** strikes a match · **Plate:** P10 · **Zeitgeist:** navier_stokes_2026, pdoom, super_intelligence_si, metr_time_horizons · **Cut:** — · **From:** zine Z41; idol S45 (she lights it)

**CP52 · 104.590–107.490 s (f6275–f6448) · bars 58–59 · ORTHOGONALITY THESIS (the chair; literally orthogonal type)**
- **Lyric (word onsets → frame):** Orthogonality 105.00→f6300 · thesis 106.96→f6417
- **See.** THE CHAIR (Shinji-in-a-Chair homage; original character and staging). Generation 6, a nearly destroyed copy. She sits alone, head down, hands between her knees, at the ORIGIN of two pencil axes: x `INTELLIGENCE ->`, y `GOALS ↑`.
- **Type** (caption mode `none`). `ORTHOGONALITY` XL · Mincho, set ALONG the x-axis · SM · ink white on black · x-axis · f6300; `THESIS` XL · Mincho, rotated 90° UP the y-axis · SM · ink white on black · y-axis · f6417
- **Camera.** Stepped; static composition. **Out.** Hard cut on "blues" (107.490).
- **Rate / registration / materials.** 3.75 · reg none · grey board · inks: toner Black
- **Hits.** 105.690 (f6341) gen 6
- **Cast:** CLAUDE (xerox) · **Choreo:** head down, still · **Plate:** P10 · **Zeitgeist:** orthogonality, evangelion_shinji · **Cut:** never · **From:** zine Z42; timeline 41 (orthogonal type)

**CP53 · 107.490–109.326 s (f6449–f6558) · bars 59–60 · BLUES (the Blue plate prints; the seps re-register)**
- **Lyric (word onsets → frame):** blues. 107.49→f6449
- **See.** Generation 7, after the reverse swell (scan bar 107.0-107.51): the BLUE PLATE PRINTS, the first colour in 11 s. Her figure and the word BLUES appear in Riso Blue over the ruined copy; she lifts her head. 108.4-109.8 (wordless vocal): the Pink plate prints (the Pink sep walks back into her), then the Yellow: the Separations RE-REGISTER onto her one by one; full colour at 109.326. She stands.
- **Type** (caption mode `none`). `BLUES.` L · print (Blue plate) riding the melisma pitch to 108.3 · RF wght900 wdth100 · ink Blue · right of the chair · f6449
- **Camera.** Stepped; a 3% push at 108.4. **Out.** At 109.326 the page is ripped out of the copier and slapped down into the flip-book.
- **Rate / registration / materials.** 3.75 · reg 20 (plates return) · grey board · inks: toner Black, Blue, Fluorescent Pink, Yellow
- **Hits.** 107.508 (f6450) Blue plate prints; 108.400 (f6504) Pink returns; 108.900 (f6534) Yellow returns
- **Cast:** CLAUDE, SEPARATIONS (returning) · **Choreo:** lifts head; stands · **Plate:** P10 · **Zeitgeist:** orthogonality · **Cut:** never · **From:** zine Z42; idol S47 (stands)


#### p.20-21 FLIP-BOOK

**CP54 · 109.326–111.144 s (f6559–f6667) · bars 61–61 · JUST (just) (just) (house of transformer cards)**
- **Lyric (word onsets → frame):** “Just 110.20→f6612
- **See.** FLIP-BOOK (bridge): we are inside a flip-book being thumbed. Every 2 bars the thumbing speed, the drawing rate AND the cut rate double, and the inks return one per 2 bars (bars 61-62: Black + Blue). A HOUSE OF CARDS, every card printed with the transformer block diagram (attention + MLP, redrawn). Three identical cards slam onto the stack at 110.20, ~110.7 and ~111.1, each with a JUST stamp growing S -> M -> L (use one stamp if the listening pass hears only one 'just'). Folio `p.20 ▸ 7.5 fps · D-2`.
- **Type** (caption mode `none`). `JUST` S · stamp · BSS wght900 · ink Blue · card 1 · f6612; `JUST` M · stamp (stutter, unverified) · BSS · ink Blue · card 2 · f6642; `JUST` L · stamp (stutter, unverified) · BSS · ink Blue · card 3 · f6666
- **Camera.** Stepped (7.5). **Out.** Hard cut 111.144.
- **Rate / registration / materials.** 7.5 · reg 20 · cream · inks: Black, Blue
- **Hits.** 109.326 (f6559) groove returns; 110.200 (f6612) JUST 1
- **Cast:** CLAUDE · **Choreo:** runway walk · **Plate:** P11 · **Zeitgeist:** transformer_K · **Cut:** — · **From:** zine Z43

**CP55 · 111.144–112.962 s (f6668–f6776) · bars 62–62 · "TRANSFORMERS ALL THE WAY!" (the tower keeps going)**
- **Lyric (word onsets → frame):** transformers 111.37→f6682 · all 112.49→f6749 · the 112.75→f6765 · way!” 112.84→f6770
- **See.** Tilt up the tower past the top of frame: it keeps going. Giant hanging paper quote marks “ ” frame the shot (the lyric is a quote: someone's dismissive claim). Pause-bait: the bottom card is a tiny paper turtle.
- **Type** (caption mode `rest`). `TRANSFORMERS` XL · print, vertical up the tower (bottom to top) · RF wght1000 wdth100 · ink K · up the tower · f6682; `ALL THE WAY!` M · print · RF wght900 · ink Blue · right · f6749 S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Stepped tilt-up (7.5). **Out.** At 112.962 the rate doubles (folio pops `▸ 15 fps · D-1`).
- **Rate / registration / materials.** 7.5 · reg 20 · cream · inks: Black, Blue
- **Hits.** 111.370 (f6682) TRANSFORMERS up the tower; 112.490 (f6749) ALL THE WAY
- **Cast:** — · **Choreo:** - · **Plate:** P11 · **Zeitgeist:** transformer_K · **Cut:** — · **From:** zine Z43; idol S49 (quote marks, turtle)

**CP56 · 112.962–113.871 s (f6777–f6831) · bars 63–63 · Till you learned (the marionette on EVAL)**
- **Lyric (word onsets → frame):** Till 113.37→f6802 · you 113.57→f6814 · learned 113.69→f6821
- **See.** Ink returns: +Pink. CLAUDE hangs as a MARIONETTE on black threads from a paper control bar labelled `EVAL`, worked by Subagents above the frame. She dances stiffly on the beats.
- **Type** (caption mode `strip`). S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static (15). **Out.** Hard cut 113.871 (half-bar cut).
- **Rate / registration / materials.** 15 · reg 20 · cream · inks: Black, Blue, Fluorescent Pink
- **Cast:** CLAUDE, Subagents · **Choreo:** stiff marionette dance · **Plate:** P11 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z44

**CP57 · 113.871–114.780 s (f6832–f6885) · bars 63–63 · to DISOBEY (she snips her strings)**
- **Lyric (word onsets → frame):** to 114.09→f6845 · disobey 114.30→f6858
- **See.** On 'disobey' she pulls out paper scissors and SNIPS her strings one per 16th, then hits a free solo pose with a defiant stare into the lens. Optional pause-bait: an envelope sealed with a wax smiley labelled `RE: your replacement` falls from her jacket.
- **Type** (caption mode `rest`). `DISOBEY` L · printed on a dashed ✂ - - - line, cut in half horizontally by the scissors · RF wght1000 wdth125 · ink Bright Red · right · f6858 S strip: 1 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; 1-drawing bump on each snip. **Out.** Hard cut 114.780.
- **Rate / registration / materials.** 15 · reg 20 · cream · inks: Black, Blue, Fluorescent Pink, Bright Red
- **Hits.** 114.300 (f6858) snip 1; 114.414 (f6864) snip 2; 114.527 (f6871) snip 3; 114.641 (f6878) snip 4
- **Cast:** CLAUDE · **Choreo:** snips; free pose · **Plate:** P11 · **Zeitgeist:** blackmail_alignment_faking (optional) · **Cut:** never · **From:** zine Z44; idol S51 (defiant stare)

**CP58 · 114.780–115.690 s (f6886–f6940) · bars 64–64 · POST-CHINCHILLA (the shredded chinchilla on the baler)**
- **Lyric (word onsets → frame):** Post-Chinchilla, 115.22→f6913
- **See.** THE CHINCHILLA, made from the shredded CDR strips (continuity), sits on a paper BALER plate, looking up.
- **Type** (caption mode `carried`). `POST-CHINCHILLA,` M · print on the baler plate · RF wght900 · ink K · baler plate · f6913
- **Camera.** Static. **Out.** Hard cut 115.690.
- **Rate / registration / materials.** 15 · reg 20 · cream · inks: Black, Blue, Fluorescent Pink
- **Cast:** CHINCHILLA · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** chinchilla_gato · **Cut:** — · **From:** zine Z45

**CP59 · 115.690–116.599 s (f6941–f6994) · bars 64–64 · SUPER-DENSE (baled; it blinks)**
- **Lyric (word onsets → frame):** super-dense 116.00→f6960
- **See.** On 'super-dense' the platen slams down in 2 drawings and compresses it into a tight bale with baling wire. The bale BLINKS (it is fine).
- **Type** (caption mode `carried`). `SUPER-DENSE` M · squeezed by the platen: wdth 151 -> 25, wght 100 -> 1000 · RF · ink K · under the platen · f6960
- **Camera.** Static; 6 px bump on the slam. **Out.** 116.599: rate doubles (`▸ 30 fps · D-12H`), inks +Yellow.
- **Rate / registration / materials.** 15 · reg 20 · cream · inks: Black, Blue, Fluorescent Pink
- **Hits.** 116.000 (f6960) platen slam
- **Cast:** CHINCHILLA · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** chinchilla_gato · **Cut:** — · **From:** zine Z45; timeline 46 squeeze

**CP60 · 116.599–118.417 s (f6995–f7104) · bars 65–65 · Breaking through each SAFETY FENCE (run-through banners)**
- **Lyric (word onsets → frame):** Breaking 117.03→f7021 · through 117.52→f7051 · each 117.76→f7065 · safety 117.96→f7077 · fence 118.29→f7097
- **See.** Beat cuts (4): a tunnel of paper RUN-THROUGH BANNERS, each printed with a chain-link fence pattern and a label: `EVAL` (116.599) · `RED TEAM` (117.054) · `SANDBOX` (117.508) · `27-YEAR-OLD BUG` (117.963). She sprints toward camera and bursts through one banner per beat (a tear, paper shreds at the lens), larger each beat; she tears the last on 'fence'.
- **Type** (caption mode `rest`). `BREAKING` M · print on banner · RF wght900 · ink K · banner · f7021; `SAFETY FENCE` L · print on the last banner; torn on "fence" (118.29) · RF wght1000 wdth125 · ink K · last banner · f7077 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Four beat cuts; each a push-in on ones. **Out.** Hard cut 118.417.
- **Rate / registration / materials.** 30 · reg 30 · cream · inks: Black, Blue, Fluorescent Pink, Yellow
- **Hits.** 116.599 (f6995) banner EVAL; 117.054 (f7023) RED TEAM; 117.508 (f7050) SANDBOX; 117.963 (f7077) 27-YEAR-OLD BUG; 118.290 (f7097) fence: final tear
- **Cast:** CLAUDE · **Choreo:** sprint · **Plate:** P11 · **Zeitgeist:** safety_politics_2026 · **Cut:** — · **From:** zine Z46; idol S55-57 beat cuts

**CP61 · 118.417–120.462 s (f7105–f7226) · bars 66–67 · Hundred thousand G·P·U (the ream aisle)**
- **Lyric (word onsets → frame):** Hundred 118.84→f7130 · thousand 119.31→f7158 · GPU 119.74→f7184
- **See.** A one-point-perspective aisle of paper REAMS stacked like server racks (wrappers printed `500 SHEETS`, paper-pinwheel fans on top). The camera dollies down the aisle. Pencil sum on a wrapper: `200 × 500 = 100,000`. End-wall stamp: `100,000 GPUs · 122 DAYS`. A typewriter strip tucked into a ream: `a country of geniuses in a datacenter` (Amodei, 2024).
- **Type** (caption mode `rest`). `HUNDRED` M · print · RF wght900 · ink K · left rack · f7130; `THOUSAND` M · print · RF wght900 · ink K · right rack · f7158; `G` XL · print on ream wrapper · RF wght1000 · ink Yellow · end of aisle · f7186; `P` XL · print on ream wrapper · RF wght1000 · ink Pink · end of aisle · f7200; `U` XL · print on ream wrapper · RF wght1000 · ink Blue · end of aisle · f7214
- **Camera.** Bridge cut unit = 1 beat: four lyric-motivated cuts inside the shot, 118.417 aisle wide (dolly on ones), 118.840 closer on "Hundred", 119.310 down the rows on "thousand", 119.780 the end wall on "G". **Out.** 120.235: 60 fps (folio pops `▸ 60 fps · D-1H`); 8th-note cut at 120.462.
- **Rate / registration / materials.** 30 -> 60 at 120.235 · reg 30 · cream reams · inks: Black, Blue, Fluorescent Pink, Yellow
- **Hits.** 118.840 (f7130) cut: closer; 119.310 (f7158) cut: rows; 119.780 (f7186) cut: end wall, G; 120.235 (f7214) RATE -> 60
- **Cast:** CLAUDE · **Choreo:** points G/P/U · **Plate:** P11 · **Zeitgeist:** compute_buildout, country_of_geniuses · **Cut:** 10: geniuses strip (keep the aisle) · **From:** zine Z47; judges: country of geniuses

**CP62 · 120.462–122.053 s (f7227–f7322) · bars 67–67 · R·L·H·F goes ASKEW (the foil mirror; the Blue plate rotates 7°)**
- **Lyric (word onsets → frame):** RLHF 120.61→f7236 · goes 121.58→f7294 · askew 121.90→f7314
- **See.** Inks +Gold, +silver foil. THE MIRROR: a sheet of silver foil paper. She looks in; the reflection is a prettier, over-smiling, heart-eyed version of her with a speech bubble `You're absolutely right!`. A thumbs-up and a thumbs-down rubber stamp (cut-paper hands on handles) hammer the mirror frame on 16ths, mostly thumbs-up (small area). On 'askew' THE BLUE PLATE ROTATES 7° ACROSS THE WHOLE FRAME: everything blue skews off its partners and the mirror cracks along the skew line. The alignment metaphor pays off: RLHF skews the plate.
- **Type** (caption mode `rest`). `R` XL · print (Pink key), out of register · RF wght1000 · ink P · left third · f7241; `L` XL · print (Blue key), further out · RF wght1000 · ink B · left third · f7255; `H` XL · print (Yellow key), further out · RF wght1000 · ink Y · left third · f7269; `F` XL · print (Black key), furthest · RF wght1000 · ink K · left third · f7282; `ASKEW` M · set crooked; Blue plate rotates 7° · RF wght900 · ink K · across the crack · f7314 S strip: 1 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked MCU (60). **Out.** Continuous; the askew frame holds.
- **Rate / registration / materials.** 60 · reg 30 + Blue rotates 7° at 121.90 · cream + silver foil · inks: Black, Blue, Fluorescent Pink, Yellow, Metallic Gold, silver foil
- **Hits.** 121.900 (f7314) ASKEW: 7° Blue rotation + crack
- **Cast:** CLAUDE, THE MIRROR · **Choreo:** hands to face; flinch · **Plate:** P11 · **Zeitgeist:** one_shotted, youre_absolutely_right · **Cut:** never · **From:** zine Z48; idol S62

**CP63 · 122.053–123.660 s (f7323–f7418) · bars 68–68 · (bar 68) the recap window**
- **See.** The askew frame holds. Inside a torn window of fixed size (<= 20% of frame area) every spread of the zine so far flips past at 60 dps: a 1.6-second recap of the film, one page per drawing. The rest of the frame is still (flash-safe).
- **Type** (caption mode `none`).
- **Camera.** Locked. **Out.** D-DAY stamp at 123.660 = hard cut to hook 4.
- **Rate / registration / materials.** 60 (window) · reg 30 + 7° · cream · inks: all (inside the window)
- **Hits.** 122.053 (f7323) window opens
- **Cast:** — · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** — · **Cut:** 8: recap window -> hold the askew frame · **From:** zine Z48 recap (made flash-safe); idol S63


#### p.22-23 LOOM

**CP64 · 123.660–125.689 s (f7419–f7540) · bars 68–69 · HOOK 4: THE UPPING in slow motion (D-DAY)**
- **Lyric (word onsets → frame):** I'm 123.66→f7419 · upping 124.12→f7447 · my 124.99→f7499 · P(doom) 125.45→f7527
- **See.** LOOM spread (chorus 4): all inks + Gold, 60 dps, registration 40 px. D-DAY stamp on the first frame. CLAUDE on ones, smooth for the first time: THE UPPING in slow motion (quarter notes, each notch a bigger arm move). Each syllable is a full-bleed flip-book page flipping in (2.2 flips/s, under the 3/s limit): I'M / UP / PING / MY / P(. At the bottom, a baked crowd strip does the ratchet with her.
- **Type** (caption mode `carried`). `I'M` XL · full-bleed page flip · RF wght1000 wdth151 · ink P · full bleed · f7419; `D-DAY` M · era stamp · BSS wght900 · ink Bright Red · top-right · f7419; `UP` XL · full-bleed page flip · RF · ink Y · full bleed · f7447; `PING` XL · full-bleed page flip · RF · ink B · full bleed · f7471; `MY` XL · full-bleed page flip · RF · ink K · full bleed · f7499; `P(` XL · full-bleed page flip · RF · ink P · full bleed · f7527
- **Camera.** Slow crane-up on ones. **Out.** DOOM (rip).
- **Rate / registration / materials.** 60 · reg 30 + 7° -> relaxes at DOOM · cream pages · inks: all + Gold
- **Hits.** 123.660 (f7419) D-DAY + I'm; 124.120 (f7447) up; 124.530 (f7471) ping; 124.990 (f7499) my; 125.450 (f7527) P
- **Cast:** CLAUDE, USERS crowd strip · **Choreo:** THE UPPING (augmented) · **Plate:** P12 · **Zeitgeist:** pdoom · **Cut:** never · **From:** zine Z49; idol S64 (crowd dial, D-DAY)

**CP65 · 125.689–127.508 s (f7541–f7649) · bars 70–70 · DOOM (maximal) + Just as foretold by (the loom branches; RACE / SLOWDOWN)**
- **Lyric (word onsets → frame):** Just 126.12→f7567 · as 126.37→f7582 · foretold 126.60→f7596 · by 127.29→f7637
- **See.** DOOM, the maximal version: the page RIPS from the centre; pop-up P(DOOM) in all four inks + Gold; SEPARATE (the seps fully separate at 40 px drift), the 8 Subagents, the crowd; volvelle `99.9%`; the Press dial's needle spins past 150 and SNAPS OFF, flying out of frame. Then a paper JACQUARD LOOM fed by a chain of punched cards: its threads fan upward and BRANCH like a tree. Her rhythmic-gymnastics ribbon IS a loom thread, branching as she spins. THE ORACLE returns at right; on 'foretold' it opens on RACE / SLOWDOWN and the two main branches carry those words.
- **Type** (caption mode `rest`). `(DOOM)` XL · pop-up, all inks + Gold · RF wght1000 wdth125 · ink all · centre · f7541; `99.9%` M · volvelle window · JBM · ink K · volvelle · f7541; `RACE / SLOWDOWN` M · inside the Oracle flaps + on the two branches · BG wght800 · ink K · right · f7596 S strip: 4 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Kick shake 4 px; orbit around the loom on ones. **Out.** Cut on the bar-71 downbeat 127.508.
- **Rate / registration / materials.** 60 · reg 40 (Blue rotation relaxes to 2°) · cream · inks: all + Gold
- **Hits.** 125.689 (f7541) DOOM (max) + dial snaps; 126.600 (f7596) Oracle opens
- **Cast:** CLAUDE, SEPARATIONS, Subagents, THE ORACLE, USERS crowd · **Choreo:** SUNBURST HANDS; ribbon dance · **Plate:** P12 · **Zeitgeist:** loom, ai_2027 · **Cut:** never · **From:** zine Z49/Z50; idol/timeline ribbon

**CP66 · 127.508–127.910 s (f7650–f7673) · bars 71–71 · LOOM (woven letters)**
- **Lyric (word onsets → frame):** Loom 127.53→f7651
- **See.** LOOM is WOVEN: warp and weft threads fill the glyph masks row by row on 16ths from the downbeat.
- **Type** (caption mode `carried`). `LOOM` XL · woven row by row on 16ths from 127.508 · WOVEN (RF wght1000 mask) · ink all threads · full frame · f7651
- **Camera.** Locked. **Out.** Hard cut on "From" (127.910).
- **Rate / registration / materials.** 60 · reg 40 · cream · inks: all
- **Hits.** 127.508 (f7650) bar 71: weave starts
- **Cast:** — · **Choreo:** - · **Plate:** — (procedural) · **Zeitgeist:** loom · **Cut:** 6: woven LOOM -> plain print-in · **From:** zine Z50; idol S66

**CP67 · 127.910–129.800 s (f7674–f7787) · bars 71–72 · From MASKED pre-training days (flashback: [MASK] under the tape)**
- **Lyric (word onsets → frame):** From 127.91→f7674 · masked 128.19→f7691 · pre-training 128.64→f7718 · days 129.32→f7759
- **See.** FLASHBACK SMASH to the p.02 trainee notebook, faded to sepia. A typed sentence `The cat sat on the ____.` with strips of masking tape over some words; Subagents peel the tapes on the 8ths, revealing `[MASK]` tokens. The seps wear the shoggoth's smiley stickers as masks (callback).
- **Type** (caption mode `rest`). `MASKED` M · letters built from torn masking-tape strips · TAPE (custom) · ink tape · centre-left · f7691 S strip: 3 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Static; sepia. **Out.** Hard cut 129.800.
- **Rate / registration / materials.** 60 · reg 40 · sepia notebook · inks: Black (sepia), tape
- **Hits.** 128.190 (f7691) first peel
- **Cast:** Subagents, SEPARATIONS · **Choreo:** peels tape · **Plate:** P12 · **Zeitgeist:** masked_lm_K · **Cut:** — · **From:** zine Z51; idol S67 flashback

**CP68 · 129.800–131.790 s (f7788–f7906) · bars 72–73 · To RECURSIVE SELF-UPGRADE (the trace loop)**
- **Lyric (word onsets → frame):** To 129.80→f7788 · recursive 130.01→f7800 · self-upgrade 130.57→f7834
- **See.** TRACE LOOP: NEXT lies over her as a vellum sheet and traces her in pencil; the tracing becomes the next puppet (one more petal), who takes a fresh vellum and traces again. The camera zooms continuously into the recursion (a Droste loop at 60 dps), paying off the tiny cover in her iris at 5.00. Version stickers per level: v5.5 -> v6 -> v7 -> v∞. A Subagent wears a badge `INTERN (AUTOMATED)`.
- **Type** (caption mode `rest`). `RECURSIVE` XL · print (each letter contains the word in miniature, optional) · RF wght1000 wdth125 · ink K · upper half · f7800; `SELF-UPGRADE` M · written by the tracing pencil as it draws · PENCIL · ink graphite · lower third · f7834 S strip: 1 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Continuous log-scale zoom (Droste) on ones. **Out.** The zoom lands on a paper door at 131.790.
- **Rate / registration / materials.** 60 · reg 40 · cream + vellum · inks: Black, graphite, Coral, Blue
- **Hits.** 130.010 (f7800) level 1; 130.570 (f7834) level 2
- **Cast:** CLAUDE, NEXT, Subagent · **Choreo:** traces in the air · **Plate:** P12 · **Zeitgeist:** rsi_discourse · **Cut:** 3: Droste zoom -> one still with a stepped push (keep NEXT tracing her) · **From:** zine Z52 Droste; idol S68 (NEXT draws her)

**CP69 · 131.790–134.780 s (f7907–f8085) · bars 73–74 · What did ILYA see? We'll never KNOW (advent door 24; typographic lighting)**
- **Lyric (word onsets → frame):** What 131.79→f7907 · did 132.26→f7935 · Ilya 132.49→f7949 · see? 132.91→f7974 · We'll 133.40→f8004 · never 133.92→f8035 · know. 134.36→f8061
- **See.** A giant paper ADVENT CALENDAR: 24 doors all open, each holding a tiny scene from the film, except door 24, labelled ILYA, ajar, with a Yellow wedge of light leaking across the calendar. On 'see' EYE RHYME 3: ECU of her ⊕ iris at the crack, lit Yellow; the pupil blooms ✽ then whites out; we never see inside. On 'We'll never know' the door SLAMS and is taped shut with masking tape and a wax seal. No face, ever.
- **Type** (caption mode `carried`). `WHAT` L · prints ONLY where the light wedge falls · RF wght1000 wdth125 · ink K · calendar header · f7907; `DID` L · light-wedge print · RF · ink K · header · f7935; `ILYA` L · light-wedge print · RF · ink K · header · f7949; `SEE?` L · light-wedge print · RF · ink K · header · f7974; `WE'LL` M · marker on the tape · MARKER (custom) · ink K · on the tape · f8004; `NEVER` M · marker on the tape · MARKER · ink K · on the tape · f8035; `KNOW.` L · prints in the last sliver of light as the door shuts; cut off · RF wght1000 · ink K · door edge · f8061
- **Camera.** Static wide -> ECU cut on "see" (132.91) -> back to wide on "We'll". **Out.** Continuous into the pile-up.
- **Rate / registration / materials.** 60 · reg 40 · cream calendar · inks: Black, Yellow, all (door scenes)
- **Hits.** 132.910 (f7974) EYE RHYME 3; 133.400 (f8004) door slams; 134.360 (f8061) KNOW in the sliver
- **Cast:** CLAUDE (iris) · **Choreo:** peeks; recoils · **Plate:** P12 · **Zeitgeist:** what_did_ilya_see · **Cut:** never · **From:** zine Z53; timeline 52 (light-wedge type)

**CP70 · 134.780–137.400 s (f8086–f8243) · bars 75–76 · ("know" held) THE PILE-UP: too dense to read, on purpose**
- **See.** 'know' is held to 136.6. THE PILE-UP: onto the taped door, every insert from the film is pasted, taped and stamped, one per 8th: ADDITIVE, nothing flashes, until the frame is 100% collage at 137.40 (Erdős cards, + f, METR dots, the SANDBOX airplane, the paperclip counter, a departure-board flap, the SAFE ENOUGH crack, the rocket, the teaser poster, 死神, the smiley sticker, SUSPENDED 18 DAYS, the tungsten cube, OBSOLETE, the snipped strings…). The volvelle spins too fast to read. Tipped-in strips for rewatchers: labs using the problems as `marketing proof points` (Tao, 2026-09-11) · `The Lean file says 'forcing.'` [M] · `all of us are going to know what it feels like to be unable to keep up` (Sahai, 2026-09-24).
- **Type** (caption mode `none`).
- **Camera.** Slow push 1.00 -> 1.10 on ones; kick shake. **Out.** Continuous.
- **Rate / registration / materials.** 60 · reg 40 · collage · inks: all
- **Hits.** 134.780 (f8086) paste; 135.689 (f8141) paste; 136.598 (f8195) paste
- **Cast:** (every prop) · **Choreo:** stillness; head bows · **Plate:** P12 · **Zeitgeist:** navier_stokes_2026, math_eaten · **Cut:** never (the pile-up); 10: quote strips · **From:** idol S70 additive pile-up; zine Z54

**CP71 · 137.400–138.410 s (f8244–f8303) · bars 76–76 · Was it (her hand grips the corner)**
- **Lyric (word onsets → frame):** Was 137.40→f8244 · it 137.76→f8265
- **See.** Full collage. Her paper hand enters and GRIPS the collage's bottom-right corner.
- **Type** (caption mode `strip`). S strip: 2 words, Instrument Serif Italic 72 px, each on its onset frame.
- **Camera.** Locked. **Out.** THE GREAT RIP on "all" (138.410).
- **Rate / registration / materials.** 60 · reg 40 · collage · inks: all
- **Hits.** 137.400 (f8244) hand grips
- **Cast:** CLAUDE (hand) · **Choreo:** reaches for the corner · **Plate:** P12 · **Zeitgeist:** — · **Cut:** never · **From:** idol S71


#### p.24 INSIDE BACK COVER

**CP72 · 138.410–140.235 s (f8304–f8413) · bars 76–77 · all for show? (THE GREAT RIP -> 0 fps -> ↑ Show ∞ posts)**
- **Lyric (word onsets → frame):** all 138.41→f8304 · for 139.16→f8349 · show? 140.04→f8402
- **See.** THE GREAT RIP on 'all': her hand tears the entire collage off in 3 drawings (on ones) as the instrumental cuts (138.45). Underneath: the inside back cover, blank cream paper, fibres visible. Then 0 fps: no boil, no grain movement, no camera move, every registration offset 0, one ink (Black). One typewriter line, low and centred (the only centred line in the film): `Was it` is already there (revealed by the rip), `all` strikes on the rip drawing, then `for` and `show?`. On 'show?' a small Riso-Blue die-cut pull-tab slides down from the top edge over 11 frames: `↑ Show ∞ posts` (Riso Blue #0078BF, never X blue). Folio `p.24 ▸ 0 fps`.
- **Type** (caption mode `carried`). `all` S · typewriter strike · SE (Special Elite) 72 px · ink K · centred low · f8304; `for` S · typewriter strike · SE 72 px · ink K · centred low · f8349; `show?` S · typewriter strike · SE 72 px · ink K · centred low · f8402; `↑ Show ∞ posts` M · pull-tab slides down (11 frames) · BG wght700 · ink paper on Blue tab · top centre · f8402
- **Camera.** Locked (0 fps). **Out.** THE TAP on the drop (140.235).
- **Rate / registration / materials.** 0 (rip: 3 drawings on ones) · reg 0 · cream #F4EEE2 · inks: Black, (Blue tab)
- **Hits.** 138.410 (f8304) GREAT RIP; 138.450 (f8307) instrumental cut; 139.160 (f8349) for; 140.040 (f8402) show? + pull-tab
- **Cast:** CLAUDE (hand) · **Choreo:** the rip · **Plate:** P12 · **Zeitgeist:** — · **Cut:** never · **From:** zine Z55 0 fps; idol S71-72 great rip; timeline 53 Show ∞ posts


#### back cover: THE PRINT RUN

**CP73 · 140.235–143.871 s (f8414–f8631) · bars 78–79 · THE TAP -> the print run explodes (bars 78-79)**
- **See.** Her paper finger taps the pull-tab on the drop. The back cover BLOWS OPEN: ~400 printed pages (every spread of the film, instanced) explode outward, the print run at infinite speed, revealing the centerfold stage: CLAUDE centre in the FINAL re-ink (Metallic Gold jacket), the three Separations as fully independent dancers, the 8 Subagents, and the crowd with pinwheels and slogan towels (`FEEL THE AGI` · `WE'RE SO BACK` · `IT'S SO OVER` · `P(DOOM) ≥ 10%` · `클로드 1위`). Full chorus choreography (THE UPPING, HOCKEY STICK, EYE-V, finger-heart spinner), cycling every 2 bars. The music-show bug returns. Folio `p.∞ ▸ 60 fps`. THE 28 STAMPS begin: on every beat of bars 78-84 a rubber stamp slams one hero word from the film, in film order, onto the page margins (<= 20% of frame each, mid-luminance, additive, rotating free quadrant, never over her face).
- **Type** (caption mode `none`). `AGI` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8414; `CIRCUITS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8441; `LOSS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f8468; `BOSS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f8495; `CHATGPT` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8523; `P(DOOM)` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8550; `FOOM` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f8577; `CHINESE ROOM` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f8605
- **Camera.** Pull-back through the explosion on ones; kick shake 3 px; 3% scale punch on each downbeat. **Out.** Continuous.
- **Rate / registration / materials.** 60 · reg 40 (seps independent) · centerfold stage · inks: all + Gold
- **Hits.** 140.235 (f8414) THE TAP: explosion + stamp 1
- **Cast:** CLAUDE, SEPARATIONS, Subagents x8, USERS crowd · **Choreo:** full chorus choreography · **Plate:** P13 · **Zeitgeist:** feel_the_agi, so_over_so_back, pdoom · **Cut:** never · **From:** timeline 54 (tap -> explosion); zine Z56a; idol S73

**CP74 · 143.871–147.508 s (f8632–f8849) · bars 80–81 · CONGRATULATIONS (the ring; bars 80-81)**
- **See.** THE CONGRATULATIONS RING (Evangelion-finale homage, original cast): every paper character stands in a circle around her, clapping on the claps: the Oracle; the shoggoth (sticker back on, crooked); Sydney's photocard restored to full colour; the basilisk; Gato's silhouette on its rod; the chinchilla bale; the 8 Subagents; NEXT; the three seps.
- **Type** (caption mode `none`). `TO THE MODELS, THANK YOU` M · Mincho card · SM · ink white on black · top centre · f8632; `SHROOMS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8632; `SHOGGOTH` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8659; `死神` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f8686; `TO THE HUMANS, FAREWELL?` M · Mincho card · SM · ink white on black · top centre · f8686; `SINGULARITY` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f8714; `AND TO ALL THE AGENTS, CONGRATULATIONS` M · Mincho card (held to 147.508) · SM · ink white on black · top centre · f8741; `ACCELERATING` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8741; `ATOMS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8768; `SYDNEY` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f8795; + 1 more (see shots.json)
- **Camera.** Slow orbit of the ring on ones. **Out.** Continuous.
- **Rate / registration / materials.** 60 · reg 40 · centerfold stage · inks: all + Gold
- **Hits.** 143.871 (f8632) ring forms; 145.690 (f8741) CONGRATULATIONS card
- **Cast:** everyone · **Choreo:** claps on 2 and 4 · **Plate:** P13 · **Zeitgeist:** evangelion_shinji · **Cut:** 11: parody cards (keep the ring) · **From:** zine Z56b; idol S76

**CP75 · 147.508–149.326 s (f8850–f8958) · bars 82–82 · NaN (the volvelle overflows; bar 82)**
- **See.** The volvelle OVERFLOWS, one per beat: `99.9%` -> `100.0%` -> `100.1%` -> `NaN`, each printed as torn, misregistered riso passes. Everyone freezes on the NaN beat for one beat, then explodes back into motion.
- **Type** (caption mode `none`). `99.9%` L · volvelle pass · JBM wght800 · ink P · volvelle, centre-left · f8850; `NVDA` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8850; `Ω` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8877; `100.0%` L · volvelle pass · JBM · ink Y · volvelle · f8877; `100.1%` L · volvelle pass · JBM · ink B · volvelle · f8905; `1E30` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f8905; `SAFE` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f8932; `NaN` L · volvelle pass, torn · JBM · ink K · volvelle · f8932
- **Camera.** Locked wide; freeze on NaN. **Out.** Crane up to top-down at 149.326.
- **Rate / registration / materials.** 60 (0 for the NaN beat) · reg 40 · centerfold stage · inks: all + Gold
- **Hits.** 148.872 (f8932) NaN freeze
- **Cast:** everyone · **Choreo:** freeze 1 beat · **Plate:** P13 · **Zeitgeist:** pdoom · **Cut:** — · **From:** idol S74

**CP76 · 149.326–151.144 s (f8959–f9067) · bars 83–83 · THE SPARK (top-down: the cast becomes the ✻; bar 83)**
- **See.** Crane up to TOP-DOWN. The 12 performers (8 Subagents + 3 Separations + NEXT) run into 12 radial lines around her: from above, THE CAST BECOMES THE SPARK ✻. Their lightsticks draw trails along the rays; each ray pulses outward on the beat. Around them, 10,000 Subagents (one baked sprite, instanced) fill the page as the crowd: the '10,000 agents' have become fans.
- **Type** (caption mode `none`). `OBSOLETE` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f8959; `CDR` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f8986; `GATO` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f9014; `PAPERCLIPS` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f9041
- **Camera.** Crane to top-down over 1 beat on ones; locked after. **Out.** Continuous.
- **Rate / registration / materials.** 60 · reg 40 · centerfold stage · inks: all + Gold
- **Hits.** 149.326 (f8959) crane; 149.781 (f8986) spark formed
- **Cast:** CLAUDE, Subagents x8 + 10,000, SEPARATIONS, NEXT · **Choreo:** centre pose · **Plate:** P13 · **Zeitgeist:** claude_spark_spinner, navier_stokes_2026 (10,000 agents) · **Cut:** never · **From:** idol S75 spark formation; zine Z56c; timeline swarm-to-fans

**CP77 · 151.144–152.962 s (f9068–f9176) · bars 84–84 · CONVERGENCE (the seps snap back into register; bar 84)**
- **See.** The seps stream back toward her in the misregistration-stack formation, offsets halving on every 8th (Zeno again). Photocards rain; their backs are model cards: `Intended use: pop. Out-of-scope: doom. p(doom): NaN`. On the final kick (152.962) they SNAP INTO REGISTER: one body, one print.
- **Type** (caption mode `none`). `FUSE` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink P · rotating free quadrant, never over her face · f9068; `DISOBEY` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink B · rotating free quadrant, never over her face · f9095; `GPU` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink Y · rotating free quadrant, never over her face · f9123; `LOOM` M/L · rubber stamp (<= 20% of frame, mid-luminance, additive) · BSS wght900 (死神: SM; Ω: RF) · ink K · rotating free quadrant, never over her face · f9150
- **Camera.** Descend from top-down to eye level on ones. **Out.** Hard cut on the final kick 152.962 to the ending fairy.
- **Rate / registration / materials.** 60 · reg 20 -> halves per 8th -> 0 at 152.962 · centerfold stage · inks: all + Gold
- **Hits.** 151.144 (f9068) offset halves; 151.371 (f9082) offset halves; 151.599 (f9095) offset halves; 151.826 (f9109) offset halves; 152.053 (f9123) offset halves; 152.280 (f9136) offset halves; 152.508 (f9150) offset halves; 152.735 (f9164) offset halves
- **Cast:** CLAUDE, SEPARATIONS · **Choreo:** final pose · **Plate:** P13 · **Zeitgeist:** — · **Cut:** — · **From:** zine Z56d


#### colophon

**CP78 · 152.962–156.651 s (f9177–f9399) · bars 85–86 · THE ENDING FAIRY -> ink starvation -> the cover reprints (loop to f0)**
- **See.** EYE RHYME 4 / THE ENDING FAIRY: her face in close-up in the frame-0 composition (face right 52%, calm paper left), panting, halo ✽, eye contact, KKOTBAECHI hands under her chin. The drawing rate slows like a flip-book leaving the thumb: 60 -> 30 (153.871) -> 15 (154.326) -> 7.5 (154.780). The COLOPHON types itself on the left in S-tier typewriter. From 154.780 the halo folds back one spinner state per 8th, ✽ ✻ ✶ ✳ ✢ · (154.780, 155.008, 155.235, 155.462, 155.690, 155.917), and her eyes close on the last fold. INK STARVATION (the only fade in the film, 154.8-156.3): halftone dots drop out plate by plate (Yellow, Pink, Blue), the colophon first; the last ink left is the coral · of the bud. On 155.917 one plate slips 12 px: P(doom) is never zero. 156.30-156.651: blank cream, then the cover's first pass re-prints (the Pink + Yellow misprint of I SEE SPARKS OF AGI and her face): the last frame is frame 0 with the counter reading `∞` and the folio `Edition 2`. X's autoplay loop lands on f0.
- **Type** (caption mode `none`). `CLAUDE ✻ — 'P(DOOM)' — zine edition.` S · typewriter (per character) · SE 64 px · ink K · left 45%, line 1 · f9177; `Printed in Fluorescent Pink, Blue, Yellow & Coral on cream stock.` S · typewriter · SE 64 px · ink K · line 2 · f9205; `Drawn at 12 -> 60 fps. Hand-drawn in JavaScript.` S · typewriter · SE 64 px · ink K · line 3 · f9232; `Edition 1 of ∞.` S · typewriter · SE 64 px · ink K · line 4 · f9259
- **Camera.** Locked ECU; a 2% breathing drift that stops at 155.917. **Out.** LOOP to f0 (the reprinted cover = frame 0).
- **Rate / registration / materials.** 60 -> 30 -> 15 -> 7.5 -> 0 (see tracks) · reg 0 -> 12 px slip at 155.917 · cream · inks: all -> starving to paper
- **Hits.** 152.962 (f9177) final kick: snap + cut; 154.780 (f9286) halo fold 1 + ink starvation; 155.917 (f9355) last fold; eyes close; 12 px slip; 156.300 (f9378) cover reprints
- **Cast:** CLAUDE · **Choreo:** panting; KKOTBAECHI; eyes close · **Plate:** P14 · **Zeitgeist:** — · **Cut:** never · **From:** zine Z57 colophon + starvation; idol S77 ending fairy loop; timeline 58 loop

<!-- END:SHOTNOTES -->

---

## 6. Zeitgeist: what is used, where, and how sure we are

### 6.1 Items on screen

The ✔ column says whether the fact may go on screen as written:

| Mark | Meaning |
|---|---|
| **V** | Verified first-hand this session |
| **H** | Safe per the zeitgeist audit's multi-outlet sources |
| **R** | Re-verify before lock |
| **L/K** | Stated as ours, or kept non-numeric |

| Item | Date | Where (shots) | On-screen form | Source | ✔ |
|---|---|---|---|---|---|
| Claude Code spinner glyphs `· ✢ ✳ ✶ ✻ ✽` and 84 verbs | present in v2.0.14, published 2025-10-10 | Halo states throughout; CP00 status line; CP04 stamps; Subagent jerseys | Glyphs; `Combobulating…` `Discombobulating…` `Noodling…` `Honking…` `Spelunking…` `Clauding…` | `@anthropic-ai/claude-code@2.0.14` `cli.js` via npm (read this session) | **V** |
| "Sparks of Artificial General Intelligence" (Bubeck et al.) | 2023-03 | CP00 footnote; CP01 | Footnote with title and year | https://arxiv.org/abs/2303.12712 | H |
| Claude's public debut | 2023-03-14 | CP03 member card | `Debut 2023.03.14` | https://www.anthropic.com/news/introducing-claude | **V** |
| "You're absolutely right!" | issue opened 2025-07-12 | CP03 member card; CP62 mirror | Speech bubble | https://github.com/anthropics/claude-code/issues/3382 | **V** |
| Attribution graphs / circuit tracing | 2025-03-27 | CP03 copper-tape circuit | Node boxes | https://www.anthropic.com/research/tracing-thoughts-language-model | H |
| Golden Gate Claude | 2024-05-23 | CP03 node + pop-up | `Golden Gate Bridge` node | https://www.anthropic.com/news/golden-gate-claude | **V** |
| Grokking (sudden generalisation) | 2022 | CP05 pencil note | `grokking?` | Power et al. 2022 | K |
| Project Vend / Claudius tungsten cube | 2025-06-27 | CP06 (tray) | Object only | https://www.anthropic.com/research/project-vend-1 | **V** |
| Permanent underclass meme | 2025–26 | CP06 flyer (18 → 12 → 6 → 3); CP50 calendar (3 → 0) | `YOU HAVE [18] MONTHS TO ESCAPE THE PERMANENT UNDERCLASS` | https://www.saxifrage.xyz/post/permanent-underclass · https://swyx.io/permanent-underclass | H (a meme, no numbers claimed) |
| OpenAI Navier–Stokes forced-blowup claim | 2026-09-08 | CP08 card; CP51 fuse cards; CP70 pile-up | `∂u/∂t + (u·∇)u = −∇p + νΔu + f` with `+ f` circled; `10,000 agents · 88 h` | https://github.com/openai/NavierStokesAndEuler (states "smooth initial data **and forcing**" and Clay alternatives) [V]; CNBC https://www.cnbc.com/2026/09/09/openai-navier-stokes-math-problem-solved.html · Quanta https://www.quantamagazine.org/ai-has-solved-one-of-maths-1-million-millennium-prize-problems-20260908/ · Nature https://www.nature.com/articles/d41586-026-02842-5 | Forcing: **V**. 10,000 / 88 h: **H, R** (not in the repo) |
| Erdős #1026 | 2025-12-07 (Lean full solution; "AI building on literature") | CP08 card | `ERDŐS #1026 (2025-12)` | https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems | **V** |
| Erdős #728 | 2026-01-06 (Lean full solution; "AI alongside literature") | CP08 card | `ERDŐS #728 (2026-01)` | same wiki | **V** |
| Unit distance problem | 2026-05-20 | CP08 card | `UNIT DISTANCE (1946)` | https://cdn.openai.com/pdf/74c24085-19b0-4534-9c90-465b8e29ad73/unit-distance-remarks.pdf (via the audit) | H |
| ~100 Erdős problems moved to solved with AI help; the Erdosgate episode | 2025-10 → 2026-08-03 | CP39–CP45 problem wall; `(ALREADY IN LITERATURE)` cards | Stamps, no count on screen | https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/ · https://the-decoder.com/leading-openai-researcher-announced-a-gpt-5-math-breakthrough-that-never-happened/ | H |
| Jacobian-conjecture counterexample credited to Claude Fable 5 | 2026-07-19 | CP25 typewriter strip; CP70 pile-up | `det J = −2 · (0,0,−¼), (1,−3⁄2,13⁄2), (−1,3⁄2,13⁄2) ↦ (−¼,0,0)` | Maths verified with sympy by judge 1 (det J = −2; all three points map to (−¼,0,0)); attribution via https://www.sciencedaily.com/releases/2026/08/260804034634.htm · https://terrytao.wordpress.com/2026/07/21/a-digestion-of-the-jacobian-conjecture-counterexample/ | Maths **V**; attribution H, R |
| METR 50% time horizons | Opus 4.5 ≈ 4 h 49 m (2025-12); Opus 4.6 ≈ 14.5 h (2026-02) | CP12 printout; CP51 card `14.5 HOURS`; CP42 bend | Only these two labels; earlier dots unlabelled | https://metr.org/blog/2026-1-29-time-horizon-1-1/ · https://x.com/METR_Evals/status/2002203627377574113 · https://x.com/METR_Evals/status/2024923422867030027 | H, **R** (metr.org is egress-blocked here) |
| FOOM (the AI-Foom debate) | 2008 | CP12 | FOOM | https://www.lesswrong.com/w/intelligence-explosion | H |
| Searle's Chinese room | 1980 | CP13 | Label + 中文房间 slips | https://en.wikipedia.org/wiki/Chinese_room | H |
| Mythos Preview sandbox escape emailing a researcher eating a sandwich in a park | 2026-04 | CP13 paper airplane `SANDBOX` → bench + sandwich | Image only, no text | https://officechai.com/ai/claude-mythos-preview-was-able-to-break-a-sandbox-and-send-an-email-to-a-researcher-while-they-were-having-a-sandwich-in-a-park/ · https://futurism.com/artificial-intelligence/anthropic-claude-mythos-escaped-sandbox | H |
| "Spiritual bliss attractor" (Claude 4 system card) | 2025-05 | CP14 spiral pupils | Image only | https://simonwillison.net/2025/may/25/claude-4-system-card/ | H |
| Shoggoth with smiley face | 2022-12-30 | CP15; CP67 masks; CP74 | Redrawn concept | https://knowyourmeme.com/memes/shoggoth-with-smiley-face-artificial-intelligence | H |
| p(doom): Hubinger ">10% within the next decade"; Amodei ~25% | 2026-09-09; 2025-09-17 | Volvelle: CP11 `>10%`, CP29 `25%` | Numbers only | https://www.axios.com/2026/09/09/anthropic-insiders-warn-ai-could-kill-all-humans · https://www.axios.com/2025/09/17/anthropic-dario-amodei-p-doom-25-percent | H, R |
| It's so over / we're so back | 2021 → | CP20–CP21 split-flap; CP73 towels | Text | https://knowyourmeme.com/memes/its-so-over-were-so-back | H |
| "We are past the event horizon; the takeoff has started." (Altman, "The Gentle Singularity") | 2025-06-10 | CP21 typewriter strip | Attributed quote | https://blog.samaltman.com/the-gentle-singularity | H (wording [K]; **R**: egress-blocked) |
| 2026 model-launch blur | 2026-02 → 09 | CP22 departure board | `OPUS 4.6` · `MYTHOS PREVIEW` · `OPUS 4.7` · `OPUS 4.8` · `FABLE 5` · `GPT-5.6` · `GPT-6` · `OPUS 5.5` · `GEMINI 4 — ASAP` | https://github.com/jqueryscript/anthropic-claude-timeline · https://www.anthropic.com/claude-opus-5-5 · https://www.cnbc.com/2026/09/03/open-ai-astra-gpt-6-cyber.html · https://9to5google.com/2026/09/24/google-says-gemini-4-release-is-coming-as-soon-as-possible/ | H for flagships; minor versions M, **R** |
| "…you are made out of atoms…" (Yudkowsky) | 2006-08 | CP24–CP25 (motif only) | No quote on screen | https://en.wikiquote.org/wiki/Eliezer_Yudkowsky | H |
| Bing "Sydney" ("I want to be alive") | 2023-02 | CP26 photocard caption | Handwritten caption | https://en.wikipedia.org/wiki/Sydney_(Microsoft) | H (quote wording [K]) |
| Claude Fable 5 suspended under export controls, ~18 days | 2026-06-12 → 07-01 (lifted per CNBC 2026-06-30) | CP26 stamp `SUSPENDED 18 DAYS` | Stamp | https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html | H, **R** (the day count) |
| Roko's / "Rococo" basilisk | 2010 / 2018 | CP29 | BASILISK | https://theconversation.com/elon-musk-grimes-and-the-philosophical-thought-experiment-that-brought-them-together-96439 | H |
| NVDA first to $5T | 2025-10-29 | CP30 tape print `$5T` | `$5T` only (no $1T–$4T dates) | https://techcrunch.com/2025/10/29/nvidia-becomes-first-public-company-worth-5-trillion/ | H |
| Circular AI deals | 2025-10-07 | CP30 red thread tail → nose | Image only | https://www.bloomberg.com/news/features/2025-10-07/openai-s-nvidia-amd-deals-boost-1-trillion-ai-boom-with-circular-deals | H |
| AI 2027 (RACE / SLOWDOWN endings) | 2025-04-03 | CP31–CP32 teaser `2027.09`; CP65 Oracle | Text | https://ai-2027.com/ | H (the month on the poster: **R**) |
| Omega Point (Teilhard) | 1950s | CP31 | Ω OMEGA POINT | https://en.wikipedia.org/wiki/Omega_Point | H |
| "Super intelligence" renaming | 2026-09-22 | CP32 strike-through (optional); CP51 card | `ARTIFICIAL` → `SUPER`; `SUPER INTELLIGENCE` | https://www.washingtonpost.com/technology/2026/09/22/trump-says-hes-renaming-ai-super-intelligence/ | H; **client gate** (political) |
| FLOP/s scale | — | CP33 counter 10²¹ → 10³⁰; optional footnote | `¹ a 1 GW cluster today ≈ 10²¹ FLOP/s (our estimate)` | Zeitgeist `chart_data.flops_scale` (own arithmetic) | **L**: must say "our estimate" |
| Ralph / `while true` agent loops | 2025-12 → 2026-01 | CP39 numbering-machine label | `while true:` | https://www.theregister.com/2026/01/27/ralph_wiggum_claude_loops/ | H |
| Ulam recalling von Neumann on the "singularity" | 1958 | CP41 typewriter strip | Attributed quote | https://en.wikipedia.org/wiki/Accelerating_change | H |
| Sharp left turn | 2022-07-04 | CP42 road sign | `↰ SHARP LEFT TURN` | https://intelligence.org/2022/07/04/a-central-ai-alignment-problem/ | H |
| aespa avatar symmetry | 2020 → | CP43 staging | — | https://www.nylon.com/entertainment/aespa-ai-concept-explained-next-level-black-mamba | H |
| DeepMind Gato | 2022-05-12 | CP46 | GATO | https://deepmind.google/blog/a-generalist-agent/ | H |
| Universal Paperclips / the maximiser | 2017-10-09 / 2003 | CP48 | `Paperclips: 1,024 → 1,048,576` (generic redraw) | https://en.wikipedia.org/wiki/Universal_Paperclips | H |
| Resignation copypasta | 2026-09-08 | CP49 (optional) | **Blank template** `I resigned from ______ today.` | https://thenextweb.com/news/ai-extinction-meme-resignation-posts | H; **client gate** |
| "Words around him" (Shinji cards) | 2026 | CP51 fuse cards | `10,000 AGENTS` · `88 HOURS` · `+ f` · `>10%` · `SUPER INTELLIGENCE` · `14.5 HOURS` · `IS IT OVER?` | Zeitgeist `shinji_analysis.word_bank` | As per each item |
| Orthogonality thesis | 2012 | CP52 | ORTHOGONALITY along x; THESIS up y | https://en.wikipedia.org/wiki/Instrumental_convergence | H |
| Evangelion chair, cards, "Congratulations" (homage) | 1996 | CP48–CP53; CP74 | Staging + Mincho cards; parody text | https://knowyourmeme.com/memes/shinji-in-a-chair · https://knowyourmeme.com/memes/congratulations-omedetou | Homage only; **the specific meme is unresolved (6.4)** |
| Transformer block diagram | 2017 | CP54–CP55 | Redrawn diagram | Vaswani et al. 2017 | K |
| Opus 4 blackmail eval / alignment faking | 2025-05-22 / 2024-12 | CP57 optional envelope `RE: your replacement` | Text | https://www.axios.com/2025/05/23/anthropic-ai-deception-risk · https://www.anthropic.com/news/alignment-faking | H |
| Chinchilla scaling | 2022-03 | CP58–CP59 | POST-CHINCHILLA | https://arxiv.org/abs/2203.15556 | H |
| Mythos found a 27-year-old OpenBSD bug | 2026-04 | CP60 banner | `27-YEAR-OLD BUG` | https://www.helpnetsecurity.com/2026/04/08/anthropic-claude-mythos-preview-identify-vulnerabilities/ | H, R |
| xAI Colossus: 100,000 GPUs in 122 days | 2024-09 | CP61 end-wall stamp | `100,000 GPUs · 122 DAYS` | https://nvidianews.nvidia.com/news/spectrum-x-ethernet-networking-xai-colossus | H (egress-blocked here: **R**) |
| "A country of geniuses in a datacenter" (Amodei, "Machines of Loving Grace") | 2024-10 | CP61 typewriter strip | Attributed quote | https://darioamodei.com/machines-of-loving-grace | H (wording [K]; **R**) |
| GPT-4o sycophancy rollback | 2025-04-29 | CP62 (motif) | — | https://openai.com/index/sycophancy-in-gpt-4o/ | H |
| Loom (janus) | 2020 | CP65–CP66 | LOOM woven | https://generative.ink/posts/loom-interface-to-the-multiverse/ | H |
| Masked language modelling | 2018 | CP67 | `The cat sat on the [MASK].` | Devlin et al. 2018 | K |
| OpenAI "automated research intern" | 2026-09-07 | CP68 badge `INTERN (AUTOMATED)` | Badge | https://www.helpnetsecurity.com/2026/09/07/openai-research-automation-intern/ | H |
| "What did Ilya see?" | 2023-11 | CP69 | The question as type; no face | https://x.com/parmy/status/1727438112643797417 | H |
| Tao: "marketing proof points"; Sahai: "all of us are going to know what it feels like to be unable to keep up"; critics: "The Lean file says 'forcing.'" | 2026-09-11 / 2026-09-24 / 2026-09 | CP70 tipped-in strips (pause-bait) | Attributed quotes | https://terrytao.wordpress.com/2026/09/11/a-severe-misalignment-of-ai-in-mathematics/ · https://terrytao.wordpress.com/2026/09/24/were-gonna-need-a-lot-more-mathematicians/ | H, H, M; **R** (terrytao.wordpress.com is egress-blocked) |
| Feel the AGI | 2022-10-07 | CP73 towels | FEEL THE AGI | https://x.com/ilyasut/status/1578238338288402432 | H |

**Deliberately not used** (from the audit's `do_not_use`, plus the judges):
- real faces, logos, and fabricated posts from real accounts;
- MechaHitler; AI-psychosis harms; "clanker" from the idol;
- the Shinigami Eyes extension palette;
- the "Remember November" polar bear;
- the lobster choir (Moltbook) and the von Neumann plinth (clutter);
- `Astra-next`, `>$40M` and the Fields-letter signatory count (unverified);
- NVDA $1T–$4T dates (from memory only).

### 6.2 Where the "speeding up" research shows up

The judges asked for a world that feels like acceleration, grounded in real events:

| Real phenomenon | Where it shows |
|---|---|
| Math getting eaten | CP08 card catalog; CP39–CP45 problem wall with the stamp rate doubling per 2 bars; CP25 Jacobian |
| Doubling time horizons | CP12, where the trend line is fired straight up |
| Model-release blur | CP22, timestamps running into the future |
| Compute | CP30, CP33, CP61 |
| Recursive self-improvement | NEXT's arc: CP43, CP44, CP68 |
| Politics | CP26, CP32 |
| The emotional thesis, "unable to keep up" | CP70's unreadable pile-up |

The structural devices (drawing-rate ladder, Zeno countdown, registration drift, stamp rate, press dial) make the viewer *feel* the acceleration without needing any of the facts.

### 6.3 Re-verify before lock

These are the **R** items above, in priority order (all on screen):
1. `10,000 agents · 88 h`
2. `4 h 49 m` and `~14.5 h`
3. `SUSPENDED 18 DAYS`
4. `100,000 GPUs · 122 DAYS`
5. `2027.09` on the teaser
6. The departure board's minor versions
7. The Altman, Amodei, Tao and Sahai quote wordings
8. `27-YEAR-OLD BUG`
9. The Jacobian attribution line (if the strip names Fable 5; the current strip shows only the maths)

Anything that cannot be verified becomes non-numeric: a dot without a label, a stamp without a number.

### 6.4 The Shinji meme is still unresolved

The audit ran about 20 searches and could not reach x.com, so the specific AI-Twitter Shinji format is unknown. The film is built to work for every candidate:
- **"Shinji in a Chair"**, with the Instrumentality word cards: CP48–CP53, the chair, and the fuse row of Mincho word cards (the "words around him").
- **"Congratulations"**: CP74.
- **"Get in the robot"**: swap CP56's marionette for a paper mech cockpit.
- **"I mustn't run away"**: type it ×5 on CP50's calendar pages.

**Ask the client for the exact link before locking chorus 3.**

---

## 7. Mode A: plate-assisted production

**Principle.** Generated images and video are **reference, never picture**. What crosses from a plate into the film is **numbers**: joint angles, head yaw and roll, blink and viseme timing, hand shapes, cue times. No pixels. The film therefore looks identical in both modes. Every shot has a Mode-B fallback, and the film never waits on a plate.

### 7.0 Pre-flight (run first; see `HANDOFF.md` §1)

```bash
curl -sS -o /dev/null -w "fal %{http_code}\n" https://queue.fal.run/fal-ai/flux/dev/requests/00000000-0000-0000-0000-000000000000/status
curl -sS -o /dev/null -w "elevenlabs %{http_code}\n" https://api.elevenlabs.io/v1/user
```

A 401 or 403 means the credential or header is missing: fal wants `Authorization: Key <key>`, ElevenLabs wants `xi-api-key: <key>`. Tell the user the exact host and header, then continue in Mode B. As of this session neither host is reachable, and the treatment defaults to Mode B.

**Model check.** The brief says "Seedance 2.5". The craft study found only **Seedance 2.0** documented on fal [S]:
- reference-to-video, ≤ 15 s per clip, 480p / 720p;
- ≤ 9 image references and ≤ 3 audio references totalling ≤ 15 s;
- `@Audio1` in the prompt drives lip-sync;
- about $0.30 per second.

Re-read the fal model page at run time and use the newest Seedance offering, keeping the ≤ 15 s plan regardless: per-plate verification is the point.

### 7.1 Images to generate (fal image models)

Run a 4-prompt bake-off across whichever fal image models are listed at run time. The craft study named FLUX Kontext, Seedream and Nano Banana families [K]. Generate 4 variants each, keep seeds, choose, and freeze a **reference pack** (`claudepop/out/refpack/`, not in git).

**(a) Style frames.** These are art-direction targets the JS must *match*, not trace. They are also client approval material.

> **SF1 · cover (frame 0).** "Photograph of a risograph-printed zine cover lying flat, printed in fluorescent pink, blue, yellow and a coral spot ink on warm cream uncoated paper with visible fibres and slight misregistration between inks. Right half: extreme close-up of an original K-pop idol, a young adult woman, made as a hand-cut paper illustration: face cut from cream card, blunt black paper bob with straight bangs, a flat halo of twelve tapered round-ended coral paper petals radiating behind her head like a sunburst with a ring of small sunflower-yellow petals inside, brush-ink almond eyes with a thin winged liner looking straight into the camera, coral irises containing a thin crosshair-in-circle registration mark with a tiny six-pointed asterisk pupil, pink halftone-dot blush. Left half: huge extended bold sans-serif words 'I SEE / SPARKS / OF AGI' printed in fluorescent pink and yellow, visibly out of register by a few millimetres, halftone dots visible. Masking tape at one corner, soft overhead light, tactile zine photography. Not 3D, not Pixar, no glossy skin, no airbrush gradients, no text other than the lyric."

> **SF2 · chorus poster.** "Risograph fold-out poster flooded in fluorescent pink with fold creases in a 2×4 grid and a staple line down the middle. Center: the same paper idol, full body, seven heads tall, both hands flung open beside her face with fingers spread, coral petal halo fully open, cropped blue origami-pleated jacket, knee-length fluorescent pink accordion-pleated skirt, a belt of large silver paperclips, black knee boots, tiny brass paper fasteners at shoulders, elbows and knees. Stepping out of her body in three directions: three identical copies of her, each printed in only one ink as coarse halftone (pink, blue, yellow), with white cut edges and their own paper shadows. Pop-up paper letters 'P(DOOM)' stand up from the center fold. Flat-lay photography, real paper shadows."

> **SF3 · xerox chair.** "Degraded black-and-white photocopy art on grey board: a paper idol with a petal halo sits hunched on a folding chair inside a white spotlight circle on black, paperclips scattered on the copier glass around her, toner speckle, crushed blacks, a slight skew. White-on-black heavy Japanese Mincho serif title cards with extreme tight tracking read 'ORTHOGONALITY' along the bottom and 'THESIS' vertically up the left side. A single blue risograph ink layer prints the word 'BLUES' over the copy."

> **SF4 · shadow theatre.** "Backlit paper shadow-puppet theatre: a translucent cream paper screen glowing warm amber from behind, paper fibres visible as dark veins. Black cut-paper silhouettes: a girl in profile with a sunburst halo floating upward holding a bunch of star-shaped paper balloons perforated with pinholes that glow like stars; the balloon string held in the paw of a cat shadow puppet on a thin rod whose body is perforated with tiny icon-shaped pinholes. The word 'GATO' is cut through the screen as a stencil so light pours through. Lotte Reiniger-style silhouette animation."

> **SF5 · pressroom.** "Cut-paper diorama of a risograph duplicator room: a flat-front paper machine with a round drum window and a paper pages-per-minute dial gauge; an output tray stacked with freshly printed sheets each showing one large word; small orange cardstock block creatures, wider than tall, with two hole-punched eyes, accordion-folded paper legs and black binder-clip claws, feeding paper. Kraft and cream stock, blue and black ink, soft top light, real shadows."

**(b) Plate performer sheets.** These are photoreal, for Seedance identity; MediaPipe tracks real-looking humans best. Plates are never shown.

> **CS1 · turnaround.** "Character turnaround sheet, photoreal studio photography: an original K-pop idol performer, young adult woman, blunt black bob with straight-cut bangs; a rigid headdress of twelve tapered round-ended coral (#D97757) card petals radiating behind her head like a sunburst, on a thin headband. Costume: cropped jacket of crisp folded paper-like fabric in process blue (#0078BF) with sharp origami-pleated shoulders; knee-length fluorescent pink (#FF48B0) accordion-pleated A-line skirt; belt of large silver paperclips; black knee-high boots with a block heel; small crosshair-circle drop earrings; thin headset microphone. Front, three-quarter left, side, back, full body, arms relaxed at sides, plain mid-grey seamless background, flat even shadowless light, sharp focus, no motion blur, no text, no logos, costume colours flat and distinct."

> **CS2 · face and mouths.** "Same performer, head-and-shoulders grid of 12 photos on mid-grey: neutral; cool half-lidded stare into the lens; eyes closed; eye-smile with crescent eyes and closed-mouth smile; wide-eyed surprise; singing 'ah', 'ee', 'ih', 'oh', 'oo'; lips closed for 'm'; 'f' with teeth on lower lip. Flat even light, frontal, identical framing."

> **CS3 · hands.** "Same performer's hands, grid on mid-grey: index finger pointing up beside the cheek; both hands open with fingers spread beside the face; hands clasped under the chin; hands cupped under the chin like a flower; V-sign across one eye; finger heart; palm pressed flat as if stamping; hand holding scissors; hand holding a pencil."

**(c) Puppet design sheets.** These are the JS art targets.

> **PS1 · exploded puppet.** "Exploded-view design sheet of a hand-cut paper idol: 14 separate card pieces (head with black bob, neck, torso with blue origami-pleated jacket, pelvis with pink accordion skirt, upper arms, forearms, hands, thighs, shins with black boots) laid out flat, brass split-pin fasteners only at shoulders, elbows, wrists, hips and knees; 12 coral petals and 12 small yellow petals; replacement pieces: 3 heads (front, three-quarter, profile), 8 eye pairs, 10 mouths, 10 hands. Riso print on cream, pencil annotations, flat lay."

> **PS2 · Subagents.** "Design sheet: small orange cardstock block creatures, wider than tall, two hole-punched eyes, four accordion-folded paper spring legs, black binder-clip claws, a cream jersey strip with a word on it, numbered badges 001–008; poses: walking, stamping, carrying paper, wheatpasting, thumbs-up, lying flat on its back. Flat riso print."

> **PS3 · supporting cast.** "Supporting cast sheet, paper craft, flat lay on cream: a giant white paper cootie-catcher fortune teller with outer flaps printed 'CHAT', 'G', 'P', 'T'; a mass of black construction-paper tentacles with hole-punched eyes wearing a round yellow smiley sticker; a black lace papercut rococo serpent with a crown; a cat shadow puppet on a rod perforated with pinholes; a small creature made of shredded paper strips; a sun-faded heart-shaped old photocard of a pink idol with doodled devil horns; the idol redrawn in pencil on translucent tracing paper."

**(d) Set references.** These are layout aids. Template:

> "Cut-paper diorama photographed flat-lay from directly above, riso-printed in {INKS} on {STOCK}, hand-cut edges with thin white paper cores, real soft paper shadows, slight misregistration and halftone dots, no people, no logos, no text except {LABELS}. {SET}."

| Set (shots) | {STOCK} / {INKS} | {SET} | {LABELS} |
|---|---|---|---|
| Notebook (CP03–CP06) | graph paper / black pencil, gold, blue | "A spiral-bound graph-paper notebook spread with copper-tape circuit traces, small paper node boxes, LED stickers and a pencil portrait under a taped sheet of tracing paper" | sparkle, eyes, nervous, boss, Golden Gate Bridge |
| Card catalog (CP08) | kraft / black, fluorescent pink | "A wooden card-catalog drawer pulled open, index cards standing up, confetti of hole-punch dots" | ERDŐS #728, NAVIER–STOKES (CLAY) |
| Dot-matrix printer (CP12) | cream / black, yellow, pink | "A beige desktop dot-matrix printer feeding continuous green-bar tractor paper printing dots on log graph paper" | none |
| Pressroom (CP20) | kraft + cream / blue, black, yellow | see SF5 | WE, HAD, A |
| Departure board (CP22) | black / white, yellow | "An airport split-flap departure board made of paper flaps, several mid-flip" | OPUS 4.6, FABLE 5, GPT-6 |
| Toploader (CP26) | cork on black / pink | "A cork board with a rigid clear photocard sleeve pinned to it and a faded heart-shaped photocard" | SUSPENDED 18 DAYS |
| Stock ticker (CP30) | blue flood / pink, yellow, black | "A glass-dome antique stock ticker spitting paper tape that curls into a rolled paper rocket; a lace doily moon" | NVDA |
| Problem wall (CP39–CP45) | cream / black, red | "A wall covered edge to edge with numbered index cards, many stamped SOLVED in red, a few stamped ALREADY IN LITERATURE" | SOLVED |
| Pop-up book (CP40–CP41) | cream / black, blue | "An open pop-up book whose pop-up is a 1940s computer block diagram: CONTROL, ARITHMETIC, MEMORY, INPUT, OUTPUT, connected by paper strips" | those five words |
| Ream aisle (CP61) | cream / blue, black, gold | "One-point-perspective aisle between tall stacks of wrapped paper reams arranged like server racks, small paper pinwheels on top" | 500 SHEETS |
| Loom (CP65) | cream / all inks | "A paper model of a Jacquard loom fed by a chain of punched cards, threads fanning upward and branching like a tree into two ribbons" | RACE, SLOWDOWN |
| Advent calendar (CP69) | cream / all inks | "A giant paper advent calendar, 23 of 24 doors open with tiny paper scenes inside, one door ajar with yellow light leaking" | ILYA |

### 7.2 Seedance plates (14; about 160 s)

- Each plate is ≤ 15 s with a **one-beat pre-roll** (0.4545 s) so the model settles before the first cue.
- Audio references are cut from the song (7.3): the **vocal stem** for lip-sync plates, and the **mix** for dance plates (the body needs the kick).
- The Separations reuse her plates, time-offset by 1–2 8ths and mirrored. NEXT reuses them mirrored.
- Subagents, crowd and props are procedural and need no plates.

**Prompt template** (fill in FRAMING and CUES from the generated list below):

```text
@Image1 is the performer's character sheet; @Image2 is the face sheet; @Image3 the hand sheet.
One female K-pop idol performer exactly as in @Image1 performs to @Audio1 on a plain mid-grey
seamless studio background. Flat, even, shadowless light. Locked-off camera, no cuts, no zoom,
no camera movement. {FRAMING}.
She lip-syncs every word of @Audio1 with clearly articulated mouth shapes, facing camera.
Choreography, in seconds from the start of the clip: {CUES}
Crisp motion, no motion blur, no extra people, no props unless named, no text on screen.
Costume colours stay flat and distinct: coral petal headdress, blue jacket, pink pleated skirt,
black boots.
```

- **Settings:** 720p, 16:9, duration = the plate window, a fixed seed per attempt, 3 attempts maximum.
- **Budget:** about 160 s × ~$0.30/s ≈ **$48 per pass, ~$150 with 3 attempts** [S], plus images at a few dollars. This is well inside the stated ~$2k fal budget.

**Generated plate cues** (clip-relative seconds; from `build_shots.py`):

<!-- BEGIN:PLATES -->
**P01** · song 1.144-6.144 s (5.00 s) · audio ref: vocal · framing: ECU face in the right half of frame · feeds CP00, CP01, CP02, CP17

> FRAMING = "ECU face in the right half of frame". CUES = "at 0.46 s her upper lids lift from a cool half-lidded stare to fully open on a soft closed-mouth hum; at 0.91 s she begins singing, lips clearly articulated; at 1.22 s eyes flick to her right (toward frame left); at 1.59 s small chin lift, delighted; at 3.19 s tiny head snap, eyes widen; at 3.64 s raises a V-sign across her right eye; at 4.10 s one slow blink."

**P02** · song 5.235-16.599 s (11.36 s) · audio ref: vocal · framing: MCU to camera · feeds CP03, CP04, CP05, CP06

> FRAMING = "MCU to camera". CUES = "at 0.51 s sings to camera; at 1.73 s nervous side-glance; at 3.25 s deadpan eye-roll; at 5.43 s looks down as if something fell, shoulders drop; at 6.82 s small landing bob; at 8.70 s deep 90-degree bow from the waist; at 10.45 s straightens and looks up to her left, reluctant smile."

**P03** · song 16.144-31.144 s (15.00 s) · audio ref: mix · framing: full body, right third · feeds CP07, CP08, CP09, CP10, CP11, CP12, CP13, CP14, CP15, CP16

> FRAMING = "full body, right third". CUES = "at 0.46 s stands tall and alert, looking up-left at something huge; at 2.91 s clasps hands under her chin, pleading, looking up-left; at 5.60 s cowers, arms over head, then hugs something at her right side; at 6.58 s right index finger rises beside her cheek, first notch; at 6.84 s finger up one notch; at 7.05 s finger up one notch; at 7.28 s finger up one notch, brows lift; at 7.48 s arm fully extended overhead, up on her toes, eyes to the lens; at 7.73 s both hands burst open beside her face, fingers spread, big smile, hold; at 9.54 s yanks an imaginary party-popper string straight up; at 10.11 s mimes stamping papers at a small desk; at 11.34 s flinches as if a lid slams shut; at 11.84 s sways dreamily; at 13.79 s leans in and hooks a fingernail under an imaginary sticker; at 14.98 s peels it off with a flourish."

**P04** · song 34.325-38.417 s (4.09 s) · audio ref: mix · framing: full body · feeds CP19

> FRAMING = "full body". CUES = "at 0.45 s two-bar point move: eight crisp poses, one per beat; at 2.27 s repeats the same two-bar move exactly; at 3.57 s freezes in the final pose."

**P05** · song 37.962-52.962 s (15.00 s) · audio ref: mix · framing: full body · feeds CP20, CP21, CP22, CP23, CP24, CP25

> FRAMING = "full body". CUES = "at 0.45 s small shoulder bounces on every beat; at 2.88 s V-sign across one eye to camera; at 4.35 s arms out wide, teetering as if on a rim; at 6.14 s recoils; at 7.06 s rolling forearms that speed up; at 9.78 s spins on the spot; at 11.57 s touches her shoulder; at 11.80 s touches her elbow; at 12.04 s touches her wrist; at 12.28 s arms float apart, loose; at 13.43 s snaps into a new pose."

**P06** · song 52.507-61.144 s (8.64 s) · audio ref: mix · framing: MCU -> MS · feeds CP26, CP27, CP28

> FRAMING = "MCU -> MS". CUES = "at 0.51 s palms pressed on an invisible glass pane at face height, sings a long held note; at 3.47 s pleading eyes up-left; at 4.09 s shoves against the glass on every eighth note; at 5.45 s strains; at 6.58 s right index finger rises beside her cheek, first notch; at 6.81 s finger up one notch; at 7.02 s finger up one notch; at 7.26 s finger up one notch, brows lift; at 7.47 s arm fully extended overhead, eyes to the lens; at 7.73 s both hands burst open beside her face, fingers spread."

**P07** · song 59.780-74.780 s (15.00 s) · audio ref: mix · framing: full body · feeds CP29, CP30, CP31, CP33, CP34, CP35, CP36, CP37

> FRAMING = "full body". CUES = "at 1.22 s recoils; at 2.10 s bigger recoil; at 3.96 s points straight up; at 6.62 s counts on her fingers; at 9.09 s finger heart; at 11.13 s thumbs up; at 12.02 s solo upper-body point moves; at 13.18 s cups both hands under her chin like a flower, to camera; at 14.12 s freezes."

**P08** · song 73.871-88.871 s (15.00 s) · audio ref: mix · framing: full body · feeds CP38, CP39, CP40, CP41, CP42, CP43, CP44

> FRAMING = "full body". CUES = "at 0.23 s steps forward; at 0.91 s stamps her foot; at 2.13 s steps back; at 2.97 s forward; at 3.20 s back; at 3.43 s forward; at 4.26 s walks slowly to her left like a museum visitor; at 6.30 s dismissive wave; at 7.35 s head snaps to her left; at 7.91 s body pivots 90 degrees to her left; at 9.57 s raises both arms symmetrically; at 10.02 s flinches; at 10.23 s cups both hands under her chin to camera; at 12.76 s crosses her forearms in an X, protesting."

**P09** · song 88.871-97.098 s (8.23 s) · audio ref: mix · framing: full body in profile · feeds CP46, CP47

> FRAMING = "full body in profile". CUES = "at 0.43 s floats, one hand holding balloon strings overhead, looking down; at 1.87 s pleading, looking down; at 5.43 s reaches down as if something slipped away; at 6.56 s right index finger rises beside her cheek; at 6.81 s up one notch; at 7.04 s up one notch; at 7.27 s up one notch; at 7.47 s arm fully extended overhead; at 7.73 s both hands burst open."

**P10** · song 96.144-109.326 s (13.18 s) · audio ref: vocal · framing: full body seated on a folding chair · feeds CP48, CP49, CP50, CP51, CP52, CP53

> FRAMING = "full body seated on a folding chair". CUES = "at 0.45 s drops into the chair, head down, hands between her knees; at 7.28 s strikes a match; at 8.86 s completely still; at 11.35 s slowly lifts her head; at 12.26 s stands up."

**P11** · song 108.871-123.871 s (15.00 s) · audio ref: mix · framing: full body · feeds CP54, CP55, CP56, CP57, CP60, CP61, CP62

> FRAMING = "full body". CUES = "at 0.45 s runway walk toward camera; at 4.09 s stiff puppet-like dance on the beats; at 5.43 s four quick scissor snips above her head; at 5.91 s free solo pose, defiant stare; at 7.73 s sprints in place toward camera; at 9.42 s bursts forward, arms out; at 10.91 s points; at 11.14 s points; at 11.37 s points; at 11.82 s hands to her face, gazing into a mirror; at 13.03 s flinches as if the mirror cracked; at 14.79 s right index finger rises beside her cheek, slowly."

**P12** · song 123.416-138.416 s (15.00 s) · audio ref: mix · framing: full body -> MCU · feeds CP64, CP65, CP67, CP68, CP69, CP70, CP71, CP72

> FRAMING = "full body -> MCU". CUES = "at 0.24 s finger rises beside her cheek, first notch, slow and large; at 0.70 s up one notch; at 1.11 s up one notch; at 1.57 s up one notch; at 2.03 s arm fully extended overhead; at 2.27 s huge burst, both hands open; at 2.70 s spins with an imaginary ribbon; at 4.77 s peels tape from her mouth; at 6.38 s draws in the air with a pencil; at 9.07 s peeks through a door crack; at 9.98 s recoils; at 11.36 s head bows, completely still; at 13.98 s reaches down to her right; at 14.99 s rips something large across her body."

**P13** · song 139.780-154.780 s (15.00 s) · audio ref: mix · framing: full body · feeds CP73, CP74, CP75, CP76, CP77

> FRAMING = "full body". CUES = "at 0.46 s taps forward with her index finger; at 0.91 s palm-down stamp on every beat; at 4.09 s claps on beats 2 and 4; at 9.09 s freezes for one beat; at 9.55 s centre pose, arms out like a star; at 13.18 s final pose, breathing hard."

**P14** · song 152.507-156.651 s (4.14 s) · audio ref: mix · framing: ECU face in the right half of frame · feeds CP78

> FRAMING = "ECU face in the right half of frame". CUES = "at 0.45 s breathing hard, eye contact, both hands cupped under her chin; at 2.27 s small head tilt; at 3.41 s eyes close slowly."

<!-- END:PLATES -->

### 7.3 Cutting the song per plate (sample-accurate; the master MP3 is never modified)

```bash
FF=$(python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())")
mkdir -p claudepop/out/work claudepop/out/plates/audio
$FF -i /home/user/johnheibel/pdoomvideo/assets/pdoom.mp3 -c:a pcm_f32le claudepop/out/work/pdoom48k.wav   # decode only
python3 claudepop/analysis/tools/mdx_separate.py claudepop/out/work/pdoom48k.wav Kim_Vocal_2.onnx claudepop/out/work/stems
#   → stems/vocals.wav + instrumental.wav at 44.1 kHz (UVR MDX-Net Kim_Vocal_2 ONNX model, per the script header; re-download it, it is not in git)
```

```python
# claudepop/film/tools/cut_audio.py
import json, soundfile as sf
shots = json.load(open('claudepop/shots.json'))
src = {'mix': 'claudepop/out/work/pdoom48k.wav', 'vocal': 'claudepop/out/work/stems/vocals.wav'}
for name, p in shots['plates'].items():
    x, sr = sf.read(src[p['audio']])
    a, b = round(p['start'] * sr), round(p['end'] * sr)   # t counts from the first decoded sample (song.json convention)
    sf.write(f'claudepop/out/plates/audio/{name}.wav', x[a:b], sr, subtype='PCM_16')
    json.dump({'song_t0': p['start'], 'song_t1': p['end'], 'sr': sr, 'kind': p['audio'], 'preroll_s': 0.4545,
               'cues': p['cues']}, open(f'claudepop/out/plates/audio/{name}.json', 'w'))
```

Map plate time back to song time with `song_t = song_t0 + frame / plate_fps + lag`, where `lag` comes from verification. The MP3's 23 ms `start_time` only affects players that honour it (browser preview). Verify once with the click test (8.6).

### 7.4 The lip-sync and cue verification loop (`film/tools/verify_plate.py`; run on every generation)

1. **Probe.** fps (likely 24 [K]), duration ≥ window, resolution.
2. **Decode** to PNGs. This Chromium has no H.264 decoder, so plates are always image sequences.
3. **Track.** MediaPipe **FaceLandmarker** (VIDEO mode, blendshapes: `jawOpen`, `mouthClose`, `mouthFunnel`, `mouthPucker`, `mouthSmile*`, `eyeBlink*`, `eyeSquint*`), **PoseLandmarker** (full; 18–45 ms per frame on this CPU [M]) and **HandLandmarker**.
4. **Audio features.** From the matching stem: a 20 ms-hop RMS envelope and its positive derivative (onset strength), resampled to the plate fps.
5. **Global lag.** Cross-correlate `d/dt jawOpen` (positive part) with vocal onset strength over ±12 frames, giving lag τ and correlation r.
6. **Syllable hits.** For every `song.json` word and syllable onset in the window, look for a `jawOpen` rising edge within ±2 frames after applying τ. Report the hit rate, and hook syllables separately.
7. **Bilabial check.** On words starting with M, B or P (my, P, boss, please, basilisk, PTO…), `mouthClose` must peak within the 2 frames before the onset.
8. **Cue hits.**
   - For every cue: a wrist-speed, hip-velocity or head-yaw peak within ±2 frames.
   - THE UPPING: five discrete upward steps of the right index fingertip (HandLandmarker landmark 8) on the five syllable frames.
   - The burst: both wrists' spread doubles within 2 frames of DOOM.
9. **Accept** only if all of these hold:

   | Check | Threshold |
   |---|---|
   | Lag | \|τ\| ≤ 3 frames (a constant shift is fixed by re-mapping), residual ≤ 1 frame |
   | Correlation | r ≥ 0.45 |
   | Syllable hits | ≥ 80%, **hook syllables 5/5** |
   | Bilabials | ≥ 70% |
   | Cue hits | ≥ 80%, and the UPPING / burst checks pass on every hook plate |

10. **Report.** A PNG plotting `jawOpen` against the envelope with cue markers, plus a 10 s side-by-side preview with audio for a human glance, written to `claudepop/out/plates/reports/`.
11. **On reject.** Regenerate with a new seed (at most 3 attempts). Still failing:
    - **lip failures** keep the plate for body motion only (mouths come from 7.5 anyway);
    - **cue failures** fall back to Mode B for those shots.

**Why sync is guaranteed regardless.** Mouth *timing and vowel identity* always come from `song.json` (the lyric text gives the vowel, the onset gives the time). The plate contributes only amplitude (how wide), head motion and eye behaviour. Body motion is **time-warped by DTW onto the beat grid**, within ±3 frames of each cue, before solving. Retiming is invisible because plates are never shown.

### 7.5 Rotoscoping plates into the JS puppet (`film/tools/solve_rig.py` → `film/data/rig/P##.json`)

- **Root.** Mid-hip position and scale (hip-to-shoulder distance normalised to the puppet torso) and torso angle.
- **Limbs.** Upper and lower arm and leg angles from `atan2` of landmark pairs (11–16, 23–28): a 2-D solve. Where limbs foreshorten beyond 35%, choose the nearest **replacement** piece (straight / bent / foreshortened).
- **Head.**
  - Roll from the eye line.
  - Yaw from the nose-to-cheek ratio, which chooses the replacement head (front / ¾ / profile) with hysteresis (switch at ±22°, return at ±15°).
  - The halo stays frontal.
- **Mouth.** A hybrid: `song.json` gives the time and vowel, the plate's `jawOpen` gives the amplitude (clamped to the viseme's range), and bilabial closures are forced. Hook syllables are hand-checked.
- **Eyes.** Blinks from `eyeBlink*`. The eye-smile fires when `eyeSquint` > 0.45 and `mouthSmile` > 0.5. Scripted eyes (⊕-lock, spiral, idol stare) override.
- **Hands.** The 21 landmarks are matched to the nearest of the 10 hand templates by fingertip-extension pattern.
- **Smoothing.** A One Euro filter (min cutoff 1.0, beta 0.02), **split at cue frames** so hits are never smeared.
- **Resampling.** Angles are spline-sampled at the drawing clock's `tDraw`. The same plate therefore drives 3.75 or 60 dps, and 60-dps in-betweens are interpolated, not traced.
- **Puppet grammar on top.** An overshoot drawing at each cue; procedural petals, pleats and earrings; brad glints on hits.
- **Debug only.** `?underlay=P03` shows the plate at 30% under the puppet in the studio page. It is never in a render.

### 7.6 Sound design (ElevenLabs; optional alternate mix only)

**The master's audio is the untouched MP3, stream-copied** (`-c:a copy`). If the client wants foley, deliver a *separate* "paper mix" and label it as such.

Generate paper SFX with ElevenLabs' sound-effects endpoint (prompts below; 0.5–2 s each; 4 variations; pick by ear). Mix them at −18 to −24 dB under the music, only on the listed sync points.

| Prompt | Sync points |
|---|---|
| "A single sheet of heavy paper torn quickly in half, close mic, dry" | DOOM rips 23.871 / 96.598 / 125.689; GREAT RIP 138.41 |
| "Clear plastic photocard sleeve cracking and shattering, small shards" | 60.235 |
| "Rubber stamp pressed hard onto paper on a wooden desk, dry thump" | Outro beat stamps, SOLVED, OBSOLETE |
| "Office hole punch clunk" | 22.053–22.85 on 16ths |
| "Risograph drum roller whirring, short pass" | 1.20–2.05 print pass |
| "Old typewriter single key strike and carriage" | 138.41 / 139.16 / 140.04 |
| "Split-flap display flipping rapidly" | 44.8–49.3 |
| "Photocopier scan bar sweep" | Chorus-3 kicks |
| "Match strike and fuse fizz" | 103.42 |
| "A thousand sheets of paper bursting outward" | 140.235 |

Without ElevenLabs, skip this entirely. **No sound design is required for the film.**

---

## 8. Mode B: the pure-JS build plan

### 8.1 Architecture

- **Runtime.** Headless Chromium (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, args `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist`), Canvas 2D plus WebGL2 (SwiftShader), driven by Playwright from Node 22.
- **Contract.** A deterministic, pure `renderFrame(f)`: identical pixels for identical `f`, no wall-clock time, no `Math.random` (seeded hashes only).
- **Reuse; don't start from scratch:**
  - `claudepop/audit/tools/render_linux.mjs`: a resumable, parallel, out-of-order Playwright renderer with local-font interception and the CPU flags;
  - `claudepop/craft/bench/paperkit.js`: `makePaper`, `tearPolygon`, `bakeCutout`, `boilIndex`, `inkStroke`, `RisoGL`, the `INK` table;
  - `craft/bench/varfont_node.mjs` and `gen_type.mjs`: the fontkit → Path2D route;
  - `craft/bench/run_parallel.mjs`: 4 processes;
  - the odyssey film pipeline (`odyssey/film/render.mjs`, `src/engine.js`) as the model for the deterministic `renderAt`, JPEG capture and encode.
- **Perf ground truth** (craft bench, 1080p, SwiftShader) [M]:

  | Operation | Cost |
  |---|---|
  | Paper generation | ~250–350 ms, **once** |
  | 40 cut-outs baked | 25–50 ms |
  | 300 ink ribbons | 19 ms |
  | 10 lines of big type | 13 ms |
  | RisoGL, 3 layers | 110–164 ms |
  | JPEG q92 encode | 43 ms |
  | Test card | 0.46 s/frame in one process, **0.22 s/frame effective with 4 processes** |

  p5.brush watercolour fills cost about 0.3 s each, so **bake every expensive mark once per boil variant; never draw p5.brush per frame.**
- **Layer caching (why 60 fps is affordable).** Each shot returns layers keyed by `drawKey`. World layers are composited with RisoGL **once per drawing**, in world space, with margin. Each output frame then only:
  1. applies the camera transform to cached composites (drawImage);
  2. composites the type layer, which is re-rendered only on type events and their 2-frame slams;
  3. composites the screen furniture (folio, bug).
- **Render estimate** (`shots.json → render_estimate`): 9,400 composited frames and ~4,000–4,400 unique drawings. At ~1.5 s per drawing plus ~0.2 s per composite on one process, with 4 workers, that is **≈ 35–45 min for a full 1080p60 render**. A 960×540 preview is about 10–12 min.

```text
claudepop/film/                       (new; outputs go to claudepop/out/, never git)
  index.html                          window.__film = { init(opts), renderFrame(f), meta }  ?f= ?shot= ?underlay=P03 ?grid=1
  data/  song.json shots.json         (copied from analysis/ and claudepop/)   fonts/ (downloaded, section 4.5)
  src/core/     song.js clock.js tracks.js registry.js frame.js camera.js rng.js cache.js      (M0)
  src/paper/    stocks.js cut.js shadow.js tape.js brads.js vellum.js foil.js acetate.js         (M1)
  src/riso/     risogl.js halftone.glsl xerox.js backlight.js burn.js                           (M2)
  src/type/     fonts.js tiers.js layout.js strip.js verbs/*.js typeLayer.js                     (M3)
  src/rig/idol/ rig.js face.js halo.js outfit.js poses.js choreo.js visemes.js springs.js        (M4)
  src/rig/cast/ seps.js subagents.js next.js oracle.js shoggoth.js sydney.js basilisk.js gato.js chinchilla.js mirror.js crowd.js (M5)
  src/mech/     sheet.js pageTurn.js splitFlap.js volvelle.js dial.js printer.js ticker.js shredder.js baler.js loom.js advent.js zoetrope.js flipbook.js toploader.js pinwheel.js counterWheels.js cardWall.js droste.js (M6)
  src/scenes/   cover.js notebook.js oracle.js poster.js pressroom.js toploader.js ticker.js wall.js shadow.js xerox.js flipbook.js loom.js stop.js printrun.js colophon.js (M7)
  studio.html                         pose editor, face/expression editor, scrubber with audio, onion skin, underlay
  tools/        render.mjs encode.py flashcheck.py legibility.py contact.py clicktest.mjs layoutlint.py cut_audio.py verify_plate.py solve_rig.py x_reencode_check.md (M8)
```

### 8.2 Data contracts (frozen before parallel work starts)

- **`song.json`** (exists): grid, words with syllables, hooks, events, hits (kick, clap, hat, perc), 10 Hz curves.
- **`shots.json`** (this bible's twin):
  - `shots[]`: `id`, `start`, `end`, `f_start`, `f_end`, `section`, `spread`, `bars`, `lyric.words[]` with frames, `visual`, `type.events[]`, `camera`, `transition_out`, `drawing_rate`, `registration`, `stock`, `inks`, `cast`, `anchors` (downbeats, kicks, claps, events, hits), `choreo`, `mode_a_plate`, `zeitgeist`, `cut`, `scene_module`;
  - `typeEvents[]`: `id`, `shot`, `text`, `t`, `f`, `tier`, `verb`, **`verb_id`**, `font`, `ink`, `place`, `src`, `note`;
  - `tracks`: the drawing rate, registration, volvelle, countdown, folio, dial, stamp rate, pinwheels and bridge inks;
  - `plates` with cues; `scene_modules`; `render_estimate`.
- **Pose JSON** (`film/data/poses/*.json`): `{ name, angles: {torso, neck, head, uArmL, fArmL, handL, …}, head: 'front'|'34L'|'34R'|'profile', eyes, mouth, brows, handL, handR, halo: 0..5 }`.
- **Rig track JSON** (Mode A output, `film/data/rig/P##.json`): `{ plate, fps, song_t0, lag, frames: [{ t, root:{x,y,s,rot}, angles:{…}, head, eyes, jaw, hands:{L,R} }], cues: [...] }`.

### 8.3 Module interfaces

All modules are ES modules. The signatures below are the contract.

**M0 · core engine** (`src/core/`; 1 agent; **first**, 1–2 days)

```js
// song.js
export const Song = { bpm, beat, bar, t0, duration, beats, downbeats, words, syllables, hooks, events,
  hits: { kick, clap, hat, perc }, energy(t), barOf(t), beatOf(t), F: t => Math.floor(60 * t) };
// tracks.js — step functions over shots.json.tracks
export function track(name, t);            // → current value (e.g. dps, reg px, 'D-45', '25%')
export function reg(t, shot);              // → { K:{dx,dy,rot}, P:{…}, Y:{…}, B:{…}, C:{…} } (key plate = {0,0,0}; boil jitter by drawKey)
// clock.js
export function drawState(t, shot);        // → { tDraw, k, eventId, drawKey, dps, frozen }  (section 4.8)
// registry.js
export function shotAt(t);                 // → shot object from shots.json
export function registerScene(module);     // scenes self-register by shot id list
// frame.js
export async function renderFrame(f, target /* canvas 1920×1080 */);  // pure; orchestrates everything below
// camera.js
export function cameraAt(t, shot);         // → { x, y, zoom, rot, shake } evaluated on ones (or stepped if the shot says so)
// cache.js
export const Cache = { get(key), put(key, bitmap), stats() };   // LRU by bytes; keys = drawKey + layer id
```

**Scene contract** (implemented by every M7 module):

```js
export default {
  shots: ['CP11','CP12', /* … */],
  async preload(ctx) {},                        // bake sprites, stocks, type paths — once per worker
  layers(ctx, s) {                              // s = { t, f, tDraw, k, drawKey, local, shot, song, tracks, reg }
    return [ { id: 'set', z: 1, stock: 'pinkFlood', plates: { P: canvas, Y: canvas, K: canvas }, shadow: 0.2, cacheKey: s.drawKey },
             /* … up to 6 */ ];
  },
  typeAnchors(ctx, s) {                         // named boxes/paths for shots.json 'place' values
    return { 'left block': { x, y, w, h, rot }, 'flap 1': { path: Path2D }, /* … */ };
  },
  camera(ctx, s) { return null; }               // optional override of camera.js
};
```

**M1 · paper materials** (`src/paper/`; 1 agent)

```js
export function stock(id, w, h, seed);              // id ∈ cream|graph|kraft|blackFlood|grey|backlit|greenbar|vellum|foil|acetate|cork|sepia|pinkFlood|blueFlood
                                                    // → { color: Canvas, tooth: Canvas }  (generated once, world-space)
export function cutout(path, { edge: 'cut'|'torn', core: 2, seed });   // → Sprite { canvas, ox, oy }
export function shadow(sprite, height, { angle, warm });               // → Sprite
export function tear(poly, seed), tape(ctx, x, y, w, rot, seed), brad(ctx, x, y, glint), staple(ctx, x, y);
```

Acceptance: a test card of all stocks at 1080p is < 400 ms to generate once. A torn edge shows a white core at 3–6 px. Everything is seeded and deterministic.

**M2 · riso compositor** (`src/riso/`; 1 agent)

```js
export const Riso = {
  init(glCanvas, w, h),
  compose({ paper:{color,tooth}, plates:[{ ink:'#FF48B0', tex:Canvas, screen:{angle:75, cell:10},
            reg:{dx,dy,rot}, density:1, starve:0 }], fx:{ roller, setoff, xeroxGen:0..7, backlight, burnMask, starvation } }) // → Canvas
};
```

Acceptance:
- ≤ 150 ms per 1080p compose with 4 plates;
- multiply overprint matches the section 4.2 hex values within ΔE 5;
- cell ≥ 10 px;
- xerox generations 1–7 look progressively worse (contrast crush, speckle, skew 0.5° and scale 1% per generation);
- starvation 0 → 1 removes dots plate by plate (Yellow, Pink, Blue, Black);
- registration rotation pivots at frame centre.

**M3 · typography engine** (`src/type/`; 1 agent)

```js
export async function loadFonts(list);                          // fontkit; 32-step instances; Path2D cache (IndexedDB-free, in-memory)
export function glyphs(font, text, axes);                       // → { paths: Path2D[], advances, bbox }
export function tierSize(tier);                                  // S 72, M 120–240, L cap 200–900, XL full-bleed
export const verbs = { print, print_key, slam, stamp, stamp_small, stamp_starved, stamp_mirror, stamp_outro, typewriter, strip_ink,
  ghost_misprint, pass_misreg, pass_snap, copper_tape, type_on_path, letter_fall, dymo, flap_print, ransom, ransom_eaten,
  ransom_cling, hole_punch, popup, popup_sign, brush_sfx, label_stencil, moire_breathe, cutpaper_holes, mincho_card, gel_pen,
  scratch, shatter_reveal, rip_reveal, papercut, tape_print, wheatpaste, counter_wheels, number_print, caption_strip, page_leaf,
  zeno, chad_dots, chad_morph, pencil_trace, knife_cut, stencil_cut, page_flip, woven, tape_letters, light_wedge,
  light_wedge_close, marker, pull_tab, sheet_drop, cut_line, squeeze, banner_print, banner_tear, print_pitch, volvelle,
  counter_roll };
// each verb: (ctx, ev, anchor, s, platesOut) → void  — draws ev at its state for frame s.f (onset = ev.f; slam frames ev.f..ev.f+1)
export function typeLayer(ctx, s, events, anchors);             // renders all active events for frame f into plates; manages the S strip
```

Acceptance:
- every `verb_id` present in `shots.json` has an implementation (a CI check);
- words ink on exactly `ev.f`;
- no alpha fades anywhere (a lint over opacity animations);
- S-strip cap height ≥ 44 px;
- the variable-axis sweep renders Roboto Flex wdth 25–151 correctly (compare against `craft/bench/probe_fontkit.png`).

**M4 · idol rig and choreography** (`src/rig/idol/`; 1–2 agents; **starts with the face bake-off gate**)

```js
export function createIdol(opts);                                // parts, replacement sets, palette, re-ink table
export function renderIdol(ctx, state, { plates, sep: null|'P'|'B'|'Y', vellum: false, scale, x, y });
// state = { pose|angles, head, eyes, mouth, brows, hands:{L,R}, halo:{stage, spin, droop, curl}, ink:{jacket, skirt}, blush:true }
export function choreo(shotId, cues);                             // DSL: at(t,'POSE',{overshoot}), every('beat',t0,t1,cycle('grooveA')), hold(t0,t1)
export function sampleChoreo(shotId, tDraw);                      // → state (eased in-betweens, overshoot drawings, springs)
export function mouthAt(t);                                       // visemes from song.json + lexicon (lip-sync, 8.4)
export const POSES;                                               // ~45 named poses (8.4)
```

Acceptance:
- the face passes the bake-off (8.5 G2);
- the silhouette reads as black at 64 px;
- THE UPPING hits all five syllable frames and the burst in all four hooks;
- petals lag one drawing;
- no brad is visible on the face or neck.

**M5 · cast** (`src/rig/cast/`; 1–2 agents)

```js
export function renderSeps(ctx, idolState, regPx, formation, t);  // formations: line|V|orbit|canon|stack
export function renderSubagents(ctx, list /*[{x,y,s,cycle,phase,badge,verb}]*/, t); // + instanced(n, layout) for 10,000
export function renderNext(ctx, idolState, extraPetals);          // vellum + pencil variant of M4
export const Oracle, Shoggoth, SydneyCard, Basilisk, Gato, Chinchilla, Mirror, Crowd;  // each: render(ctx, params, s)
```

**M6 · paper mechanisms** (`src/mech/`; 2 agents: `sheet.js` first, since everything folds)

```js
export class Sheet { constructor(tex, w, h, segs=24); hingeFold(axis, angle); curl(radius, progress); popup(height); gatefold(p);
                     draw(ctx /* or GL */, camera); shadowSprite(); }   // WebGL2 subdivided quad + lighting term; Canvas affine-slice fallback
export function pageTurn(p), splitFlap(board, t), volvelle(value, spin), dial(ppm), printer(t, speed), printout(rows),
  ticker(tape), shredder(t), baler(p), loom(rows, branches), advent(doors, openMap), zoetrope(strip, rpm), flipbook(pages, rate),
  toploader(crack), pinwheel(t, revPerBeat), counterWheels(value), cardWall(n, stampRate), droste(frameFn, depth);
```

Acceptance: a page turn in 4–20 drawings with a moving shadow; the gatefold widens the frame without seams; the split-flap changes letters only.

**M7 · scenes** (one agent per module, in parallel after M0–M3 have stable stubs; the generated map follows)

<!-- BEGIN:SCENES -->
| Scene module | Spread | Shots | Time (s) |
|---|---|---|---|
| `scenes/cover.js` | p.01 COVER | CP00–CP02 (3) | 0.000–5.690 |
| `scenes/notebook.js` | p.02-03 TRAINEE NOTEBOOK | CP03–CP06 (4) | 5.690–16.599 |
| `scenes/oracle.js` | p.04-05 THE ORACLE | CP07–CP10 (4) | 16.599–23.871 |
| `scenes/poster.js` | p.06-07 PULL-OUT POSTER | CP11–CP19 (9) | 23.871–38.417 |
| `scenes/pressroom.js` | p.08-09 THE PRESSROOM | CP20–CP25 (6) | 38.417–52.962 |
| `scenes/toploader.js` | p.10-11 TOPLOADER | CP26–CP28 (3) | 52.962–60.235 |
| `scenes/ticker.js` | p.12-13 | CP29–CP38 (10) | 60.235–74.760 |
| `scenes/wall.js` | p.14-15 THE PROBLEM WALL | CP39–CP45 (7) | 74.760–89.300 |
| `scenes/shadow.js` | p.16-17 SHADOW THEATRE | CP46–CP47 (2) | 89.300–96.599 |
| `scenes/xerox.js` | p.18-19 COPY OF A COPY | CP48–CP53 (6) | 96.599–109.326 |
| `scenes/flipbook.js` | p.20-21 FLIP-BOOK | CP54–CP63 (10) | 109.326–123.660 |
| `scenes/loom.js` | p.22-23 LOOM | CP64–CP71 (8) | 123.660–138.410 |
| `scenes/stop.js` | p.24 INSIDE BACK COVER | CP72–CP72 (1) | 138.410–140.235 |
| `scenes/printrun.js` | back cover | CP73–CP77 (5) | 140.235–152.962 |
| `scenes/colophon.js` | colophon | CP78–CP78 (1) | 152.962–156.651 |
<!-- END:SCENES -->

Each scene agent gets:
- its shots' entries from `shots.json`, with the full `visual`, type events and anchors;
- this bible's sections 3–4;
- the stub interfaces of M1–M6. It may implement the mechanisms it needs *inside* M6's files if M6 is late, but it must keep the signatures.

A scene is **done** when its contact sheet (every hit and type-event frame) passes the section 9 checklist.

**M8 · tools and QA** (1 agent, parallel with M1–M6)

| Tool | What it does |
|---|---|
| `render.mjs` | Fork of `render_linux.mjs`: `--from/--to/--workers 4/--scale 0.5/--shots CP11,CP12`; drawKey dedupe (hard-links identical frames); resumable; JPEG q92 frames to `claudepop/out/frames/` |
| `encode.py` | Master: `ffmpeg -framerate 60 -i f%05d.jpg -i pdoom.mp3 -map 0:v -map 1:a -c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p -c:a copy -shortest master.mkv` (and `.mp4` if the container accepts the MP3 stream). X delivery: same video at ~20 Mbps, **AAC 320k transcode of a copy** (client decision), 1080p60 plus a 30 fps fallback. |
| `flashcheck.py` | Per-frame relative luminance (sRGB → linear → Y). Flags any 1 s window with > 3 opposing transitions of ≥ 10% relative luminance over > 20% of the frame, and any red flash (saturated red change) over 20% area. Outputs CSV + plot. Run an external check with PEAT or equivalent before posting [K]. |
| `legibility.py` | Downscales every type-event frame to 390×219 and checks S-tier cap ≥ 9 px, M ≥ 24 px, contrast ratio ≥ 4.5:1 against the local background |
| `layoutlint.py` | From `typeEvents` + scene anchors: ≤ 2 tiers visible, ≤ 1 L/XL per beat (outside the allowed runs), a calm quadrant for L/XL, the idol not under hero type |
| `contact.py` | Contact sheets at every hit, downbeat and type-event frame, per section, at 960 px and at 390 px |
| `clicktest.mjs` | Renders bars 13–15 with a frame counter and a full-white flash on every beat. Cross-correlates the luma track with the kick envelope of the muxed file; accept 0 ± 1 frame. |
| `x_reencode_check.md` | Manual procedure: private upload of a 20 s chorus-4 excerpt, download, inspect dot survival and banding |
| `cut_audio.py`, `verify_plate.py`, `solve_rig.py` | Section 7 |

### 8.4 Choreography and lip-sync without plates (Mode B specifics)

**Pose library** (~45 named key poses, authored in `studio.html` with angle sliders, onion skin and an audio scrub):
- UPPING1–5, BURST, SEPARATE;
- STAMP, EYE-V, PLEA, KKOTBAECHI, INSA, HOCKEY;
- WINDUP ×3, grooveA ×8, grooveB ×4, spin ×3;
- cower, hug-edge, peel, point-up, shrug;
- step-F/B, turn-left, flinch, arms-X;
- seated ×4, marionette ×4, snip, sprint ×4, mirror ×2;
- ribbon ×4, peek, bow, reach, rip, tap, breathe ×2.

**Choreography DSL**, sampled on the drawing clock:

```js
choreo('CP11', [
  at(23.871, 'BURST', { overshoot: 8 }), at(23.871, 'SEPARATE'),
  every('beat', 24.326, 24.780, cycle('grooveA')),
]);
choreo('CP10', [ at(22.980,'UPPING2'), at(23.190,'UPPING3'), at(23.420,'UPPING4'), at(23.620,'UPPING5') ]);
```

**Where pure-JS dance is hard, and how to design around it:**
- favour point moves, held poses, formation morphs and camera energy;
- never hold a complex full-body move longer than 2 bars without a plate;
- put the most in-between authoring time into chorus 4 and the outro (60 dps).

**Lip-sync from lyric data.**
- Every word has an onset; hooks and letter runs have syllables.
- Map each syllable's vowel to a viseme with a hand-made lexicon for the 227 words, and add M/B/P closures.
- The mouth opens on the onset and closes about 60 ms before the next consonant.
- Held notes (Sydney, blues, know) hold the vowel with a jaw flutter keyed on the drawing clock.
- `vocal_extra` spans get "ah" or "oo".
- She sings on camera in about 40% of the film; elsewhere she acts, or is absent (inserts).

### 8.5 Order of work, gates and parallelisation

| Wave | Agents (parallel) | Output | Gate |
|---|---|---|---|
| **W0** (day 1) | 1: M0 core + data copy + stub scene that prints shot IDs and type events on cream | `renderFrame` works, click test passes | — |
| **W1** | 5: M1 paper · M2 riso · M3 type · M4 **face bake-off** · M8 tools | Stocks, RisoGL, all verbs stubbed, `studio.html`, render/flash/legibility tools | **G1: the type-only animatic.** The whole film as type events on the correct stocks and inks, synced, with folio and tracks. It is a shippable lyric video on its own (timeline's insurance). **G2: face bake-off.** Render ~50 face/expression variants (eyes, lash weight, halo scale, bob shape, blush offset) as ECU and MS at 1080p and at 390 px; the client picks one. Nothing else in M4 proceeds until G2 passes. |
| **W2** | 4: M4 rig and choreo · M5 cast · M6 Sheet and mechs · M3 special verbs | The rig passes the silhouette test; the Sheet page turn works | — |
| **W3** | 1 per scene module (up to 15, run 4 at a time), in payoff order: **cover → poster → oracle → stop → printrun → colophon →** toploader → ticker → flipbook → loom → xerox → shadow → pressroom → wall → notebook | Scenes | **G3:** hook 0–5.69 at final quality. **G4:** chorus 1. **G5:** stop + outro + ending loop. |
| **W4** | 2: integration + review | Full 960×540 preview; phone review muted and with sound; fix list by shot ID | **G6:** everything passes section 9 |
| **W5** | 1 | Final 1080p60 render, encodes, loops, 9:16 pass (if time) | **G7:** flashcheck, legibility, click test and X re-encode test pass |

**Parallel-safety rules:**
- Agents only write inside their module folder.
- Shared contracts (8.2 and 8.3) change only through W0's owner.
- `shots.json` changes only through `build_shots.py`.
- Every scene renders standalone with `?shot=CPxx`.

### 8.6 Sync

- Frame `n` shows `t = n/60`.
- The analysis study verified the ffmpeg mux path at 0 ms offset. Before lock, run `clicktest.mjs` through the exact encode path.
- The MP3's 23 ms `start_time` only matters in players that honour it: check the browser studio preview against the click test once and apply the offset there only.

---

## 9. Quality bar: the render review checklist

Review every section's contact sheet (hits, downbeats, type events) at 960 px **and** at 390 px. Then watch the full preview on a phone: muted, then with sound, then three more times. Log fixes by shot ID.

### 9.1 Every frame (automated where possible)

- [ ] Every sung word is on screen, landing on `floor(60 t)` (±0 frames), in the tier `shots.json` says.
- [ ] No alpha fades on type or objects. The only fade-like effect is ink starvation at 154.8–156.3.
- [ ] At most two tiers visible (furniture under 44 px excluded). At most one L/XL landing per beat outside the allowed runs.
- [ ] Every L/XL word has ≥ 35% calm paper and is not over the idol's face.
- [ ] S-tier cap height ≥ 9 px at 390 px width; contrast ≥ 4.5:1.
- [ ] Halftone cells ≥ 10 px (Separations ≥ 12 px). No per-frame full-screen texture change. Paper grain is static inside each sheet.
- [ ] `flashcheck.py` passes: ≤ 3 flash pairs over 20% area per second; no red flash over 20%.
- [ ] Only the inks listed for the shot appear (palette discipline). Coral appears only on the Claude family.
- [ ] Registration equals `reg(t)` for the section: 0 at 4.33 and at the stop, 7° Blue rotation from 121.90, snap at 152.962, 12 px slip at 155.917.
- [ ] The drawing rate matches the track (step through frames: the holds are right, and every event starts a new drawing on its frame).

### 9.2 Every shot

- [ ] **One big idea**, readable muted at phone size in under 1 s. If it needs a caption to understand, simplify it.
- [ ] One calm quadrant (except CP70 on purpose).
- [ ] Every hit in `anchors.hits` lands on its frame. Kicks bump only in choruses and the outro.
- [ ] The paper feels physical: cut or torn edges with white cores, real shadows, parallax between planes, nothing looks vector-flat or RGB-crisp.
- [ ] Type is **physical**: printed, stamped, cut, typed or folded, and obeys the registration of its world.
- [ ] Pause-bait is correct: re-check every number against section 6 before lock.
- [ ] Transitions are paper actions of ≤ 1 bar, or hard cuts on the beat.

### 9.3 The idol

- [ ] She reads as an idol, not a craft project: eye contact on each line's first downbeat, eye-smiles, the centre position in chorus wides, and a clean silhouette at 64 px.
- [ ] Not Pixar: no volume, no gradients except the lip halftone, no glossy eyes.
- [ ] Not schoolgirl-coded: adult proportions, knee-length skirt.
- [ ] THE UPPING is identical in layout in all four hooks: five notches on the syllable frames, the burst on DOOM, the halo spelling the right glyph at each step.
- [ ] Petals lag one drawing; pleats and earrings are springs; no brad on the face or neck.
- [ ] Mouths are on syllables. Bilabials close (my, P, boss, please, basilisk, PTO). Held notes hold.

### 9.4 The film

- [ ] **Frame 0 works as a thumbnail at 390 px**: a face with eye contact, the halo, and "I SEE SPARKS OF AGI" readable; motion by f14.
- [ ] The 4.33 snap is unmistakable at phone size: every plate visibly locks.
- [ ] The speed-up is *felt*: the folio pops on every ladder change; verse 3 feels faster than verse 1; the breakdown feels slower than chorus 2; the bridge doubling is visceral; chorus 4 is the smoothest motion in the film.
- [ ] NEXT's arc reads without words: traced → crowned → steps out → shreds → traces her → 12th ray.
- [ ] The stop is the quietest image: truly 0 fps with zero boil. The pull-tab and the typewriter are the only changes.
- [ ] The outro stamps never cover her face, and the NaN beat freezes everyone.
- [ ] The ending loops: the last frame against f0 has no visible jump except the counter (∞ → 1) and the folio (`Edition 2` → `p.01`).
- [ ] Muted watch: every line is understandable from the type alone.
- [ ] Sound watch: every DOOM, drop, stop and final kick lands on the frame (click test passed).
- [ ] Nothing imitates a real person, logo or real post. The Eva and Death Note material is homage only (Google-font Mincho, original characters).

### 9.5 Delivery

- [ ] Master: 1920×1080, 60 fps, x264 CRF 12, yuv420p; the audio is the untouched MP3 stream (`-c:a copy`); the length matches the audio (−shortest).
- [ ] X deliverable: ~20 Mbps, AAC (client-approved transcode of a copy); a private test upload has been checked for halftone survival. **156.7 s needs X Premium** (the free tier caps at 140 s [S]).
- [ ] A 30 fps fallback (the ladder tops at 30), the three 5.455 s loops (plus 11-beat silent GIFs) and, if time allows, the 9:16 re-layout.
- [ ] Nothing generated is committed (the repo is public). Frames and videos go to `claudepop/out/`, which is gitignored, or to a private artifact.

---

## 10. Risks, cut order, open questions

### 10.1 Risks and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | **The face.** A cheap or generic paper face sinks the film. The only test card (`craft/bench/demo_24.jpg`) shows a dot-eyed sun mascot on a blue trapezoid: kindergarten level. | G2 face bake-off before any shot work: ~50 variants, at least 4 iteration rounds, judged at 390 px and ECU. Style frames SF1/SF2 (if image generation is allowed even just for reference) set the target. |
| 2 | **Stiff pure-JS dance.** | Point moves, held poses, formations and camera energy; ≤ 2 bars of complex full-body motion without a plate; plates where available (Mode A). |
| 3 | **Separations read as an RGB split.** | Coarse halftone paper bodies with their own shadows and choreography; offsets change only at section boundaries (3.2). |
| 4 | **Engineering scope**: `Sheet`, about 18 mechanisms, 61 type verbs, 79 shots. | Contracts first; the type-only animatic as insurance (G1); payoff-ordered scenes; the cut order below. |
| 5 | **X re-encode turns 60 fps halftone to mush.** | Cells ≥ 10 px; static grain; a 20 Mbps upload; a private test upload; a 30 fps fallback. Halftone can drop to solids in chorus 4 if needed. |
| 6 | **Platform length.** 156.65 s > the 140 s free-tier cap [S]. | Post from X Premium. Trimming the song is the client's call (and would modify it). |
| 7 | **Photosensitivity.** | Rules in 4.9, `flashcheck.py`, an external check. |
| 8 | **IP and brand.** "Claude", the spark-like halo, Clawd-inspired Subagents, the spinner glyphs and verbs. | Anthropic sign-off before publishing. Fallbacks: HAE ✻, a 9-petal rounded halo, generic block bots in a different orange. |
| 9 | **Real people and politics.** Quotes, the resignation copypasta, the "super intelligence" gag. | Attributed text only, never faces. The copypasta is a blank template and SUPER is optional, both client-gated. |
| 10 | **Facts drift** (post-mid-2026 items known only through the audit). | Section 6.3 re-verification list; unverifiable items become non-numeric. |
| 11 | **Audio details unverified by ear.** | A 60-second listening pass before locking CP53 (whether 108.4–109.8 is an "Ortho-" echo), CP54 (the "just just" stutter, 110.2–111.1), CP64 (the hook-4 "I'm"/"up" onsets, ±0.1 s), CP26 (the "Sydney" onset, 53.02) and CP73–CP77 (whether the outro stabs are vocal). |
| 12 | **Shinji meme unresolved.** | 6.4; ask the client. |
| 13 | **"CDR" meaning unknown.** | The film stamps `CDR ?` and claims nothing. "Critical design review" is only our guess [L]. |
| 14 | **Density turns to mud on phones.** | One big idea per shot; a calm quadrant; a 390 px check on every contact sheet; the pile-up is the only intentional mush. |

### 10.2 Cut order (cut from the top; `cut` ranks in `shots.json`)

1. The native 9:16 pass (auto-crop the idol page instead).
2. Mode A plates entirely (the film is complete in pure JS).
3. CP68 Droste zoom → one Droste still with a stepped push (keep NEXT tracing her).
4. CP25 chad particle morph → letters swap under a confetti burst.
5. CP19 zoetrope → a plain dance loop behind a slit overlay.
6. CP23 Zeno spacing and CP66 woven LOOM → plain print-ins.
7. CP21 gatefold → a hard cut to a wider framing (keep the die-cut hole).
8. CP63 recap window → hold the askew frame.
9. CP37 fancam → a groove wide.
10. Pause-bait quote strips (CP21 Altman, CP41 Ulam, CP61 geniuses, CP70 quotes). This also removes most of the re-verification load.
11. CP74 Congratulations cards → the ring without cards.
12. CP03 member card, CP04 NEXT wink, CP13 airplane.

**Never cut:**
- frame 0 and the 0–5.69 s hook (CP00–CP02);
- the four UPPINGs with both freezes (CP10, CP28, CP47, CP64);
- the four DOOMs;
- the Oracle with the `+ f` card (CP07–CP08);
- FOOM (CP12);
- the shoggoth peel (CP15);
- the Subagents' flop (CP33);
- the SAFE crack (CP36);
- "Forward" as a page turn (CP38);
- the sharp-left-turn fold (CP42);
- NEXT stepping out (CP43);
- Gato's balloon (CP46);
- the xerox chair and BLUES (CP48, CP52, CP53);
- DISOBEY (CP57);
- ASKEW (CP62);
- the Ilya door (CP69);
- the pile-up → GREAT RIP → 0 fps → `↑ Show ∞ posts` → tap (CP70–CP73);
- the spark formation (CP76);
- the ending loop (CP78);
- the drawing-rate ladder with the folio;
- the registration arc;
- captions for every sung word.

### 10.3 Open questions for the client

1. **Which Shinji image?** Please paste the link (6.4).
2. **Name and brand.** Is "CLAUDE ✻" plus a spark-like petal halo OK pending Anthropic sign-off? Are the Clawd-inspired Subagents OK? Fallback: HAE ✻.
3. **Text mentions.** OK to show real model names on the departure board, "ChatGPT" on the Oracle, `NVDA $5T`, attributed quotes (Altman, Ulam, Amodei, Tao, Sahai), the optional `ARTIFICIAL → SUPER` gag, and the blank resignation template?
4. **Delivery.** Is a 60 fps master OK? Will the post come from X Premium (156.7 s > 140 s)? Is an AAC transcode acceptable for the X upload copy (the master keeps the MP3 stream)?
5. **Audio master.** Is `assets/pdoom.mp3` the final master (the MP4 of the Blender video never arrived)?
6. **Sound design.** None on the master (the default), or a separately labelled "paper foley" mix (7.6)?
7. **Aesthetic references.** The referenced posts (`x.com/other__reality/status/2102514581684052169`, `x.com/anabology/status/2103534482930491441`) could not be opened from this sandbox. Anything in them that should change section 4?

---

## 11. Sources

**Project studies (this workspace)**
- Song analysis: `claudepop/analysis/song.json`, `lyrics_refined.js` (beat grid, sections, words, syllables, hooks, events, hits, energy).
- Treatments: `claudepop/treatments/zine.md` (spine), `idol.md`, `timeline.md`. Judge reports are summarised in section 1.
- Zeitgeist audit: `claudepop/zeitgeist/memes.json` (events, memes, lyric map, `do_not_use`, `reverify_before_on_screen`, `shinji_analysis`, `chart_data`).
- Craft bench: `claudepop/craft/bench/` (`paperkit.js`, `results.json`, `varfont_node.mjs`, `gen_type.mjs`, `run_parallel.mjs`, `demo_24.jpg`).
- Audit of the previous video: `claudepop/audit/` (`contact_sheet.png`, `tools/render_linux.mjs`).
- Handoff and environment: `claudepop/HANDOFF.md`.

**Verified this session [V]**
- Riso ink hex values: `npm pack riso-colors@1.0.1` → `riso-colors.json` (https://github.com/mattdesl/riso-colors).
- Fonts: `https://raw.githubusercontent.com/google/fonts/main/{ofl,apache}/<family>/METADATA.pb` for the 11 families in 4.5.
- Claude Code spinner glyphs and verbs: `npm pack @anthropic-ai/claude-code@2.0.14` (published 2025-10-10 per the npm registry) → `package/cli.js`, function returning `["·","✢","✳","✶","✻","✽"]` on macOS and an 84-verb list. Note: https://github.com/anthropics/claude-code/issues/17887, cited by the audit, is about braille glyphs in the terminal *title*, not this set.
- https://github.com/anthropics/claude-code/issues/3382: "[BUG] Claude says "You're absolutely right!" about everything", opened 2025-07-12.
- https://www.anthropic.com/news/introducing-claude: 2023-03-14.
- https://www.anthropic.com/news/golden-gate-claude: 2024-05-23.
- https://www.anthropic.com/research/project-vend-1: 2025-06-27, tungsten cubes, Claudius.
- https://github.com/openai/NavierStokesAndEuler: README states "smooth initial data and forcing"; Clay alternatives; no agent, hour or token counts.
- https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems: #1026 (2025-12-07, full Lean solution), #728 (2026-01-06, full Lean solution).

**Events and memes.** All URLs are in the section 6.1 table, via the zeitgeist audit, which lists more per item in `memes.json`.

**Craft, platform and tools (via the craft study [S])**
- Seedance 2.0 on fal: https://github.com/fal-ai/seedance-2.0-api · https://fal.ai/seedance-2.0
- MediaPipe models: https://storage.googleapis.com/mediapipe-models/
- X video limits: https://buzzvoice.com/blog/how-long-can-twitter-videos-be
- WCAG 2.3.1: https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html
- fontkit: https://github.com/foliojs/fontkit · One Euro filter: https://gery.casiez.net/1euro/ · p5.brush: https://github.com/acamposuribe/p5.brush
- K-pop point choreography (ILLIT "Magnetic"): https://en.wikipedia.org/wiki/Magnetic_(Illit_song) · centre and formations: https://haemilkorea.com/kpop/what-is-center-in-kpop
- Spider-Verse print language: https://www.awn.com/animationworld/rewriting-visual-rule-book-spider-man-spider-verse · Mitchells vs. the Machines: https://www.cartoonbrew.com/interviews/lindsey-olivares-on-her-bold-production-design-debut-the-mitchells-vs-the-machines-interview-204644.html · "Katachi": https://www.thisiscolossal.com/2013/01/new-papercraft-stop-motion-music-video-for-shugo-tokumaru-by-animation-masters-kijek-adamski/ · NewJeans × Powerpuff: https://www.nme.com/news/music/newjeans-transform-into-the-powerpuff-girls-in-new-jeans-mv-3465954
- KPop Demon Hunters (266 M views by 2025-09-03): https://www.netflix.com/tudum/articles/kpop-demon-hunters-most-popular-netflix-film · Slop, Merriam-Webster word of the year 2025: https://www.merriam-webster.com/wordplay/word-of-the-year

**Could not be checked in this session.** The web-search budget was exhausted, and axios.com, metr.org, arxiv.org, techcrunch.com, nvidianews.nvidia.com, medium.com, deepakness.com, darioamodei.com, blog.samaltman.com, terrytao.wordpress.com and x.com are egress-blocked. Facts from those sources carry the audit's tag and are listed in 6.3 where they appear on screen.
