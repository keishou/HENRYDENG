# Craft research: K-pop MV direction, kinetic type, paper rendering
_Written from the preproduction workflow's structured result: the subagent could not save its markdown report itself._
## Key findings
1. FULL_REPORT_MARKDOWN (write verbatim to /home/user/HENRYDENG/claudepop/craft/REPORT.md):

# Craft research: K-pop directing, kinetic lyric type, and the paper look in JS

**Project:** "I'm Upping My P(doom)" (a.k.a. "Claude Pop"), 156.65 s, 132 BPM, 4/4. Beat = 0.4545 s (10.9 frames at 24 fps), bar = 1.818 s, 8th note = 0.227 s. Timings below come from `claudepop/analysis/song.json`.
**Date:** 2026-09-28. **Scope:** (1) how the best K-pop MVs manage attention; (2) kinetic lyric typography and the paper, riso, collage and brutalist lineage; (3) JS techniques for a premium paper look, measured on this sandbox's CPU-only headless Chromium (SwiftShader).

**Evidence tags.** `[S]` came from a web search or fetch in this session, and the URL is in section 6. `[M]` was measured in this sandbox, with code in `claudepop/craft/bench/` or `claudepop/craft/roto/`. `[K]` is background knowledge that I could not re-check here: the session's web-search budget ran out (200/200), and Wikipedia, MDN, Medium, x.com and most magazines were blocked for fetching. Treat `[K]` as likely but unverified.

---

## 0. TL;DR: decisions this research supports

1. **Render architecture: bake, then composite.** CPU Canvas2D is fast. At 1080p, 2,000 strokes take 22 ms, 40 torn cut-out sprites 35 ms, 10 lines of 240 px variable type 13 ms, and a full-frame paper multiply 4 ms [M]. A WebGL2 riso pass (3 inks, halftone, misregistration, paper tooth) takes 110-165 ms on SwiftShader [M]. **p5.brush fills cost about 0.3 s each on the CPU raster path and about 2.4 s each on the GPU (SwiftShader) raster path** [M]. The previous video spent 5-85 s per frame, almost all of it there [M, audit logs]. Rule: p5.brush and every other expensive mark gets baked into sprites once per boil variant, never drawn per frame.
2. **Measured throughput of the test card** (paper, 3-ink riso, torn cut-outs, boiling ink lines, variable type): 0.46 s/frame with one Chromium, **0.22 s/frame effective with 4 parallel Chromiums**, JPEG writes included [M]. The whole film at 24 fps (3,760 frames) would take about 14 minutes at this complexity. The 1-3 s/frame budget therefore leaves 5-10x headroom for richer scenes.
3. **Look: riso-printed paper stop-motion, not watercolour.** Use 3-4 spot inks (Fluorescent Pink #ff48b0, Blue #0078bf, Yellow #ffe800, plus black or Claude orange #d97757) that overprint multiplicatively, with misregistration, halftone mid-tones and torn cut-outs on one shared paper texture. The lineage is Spider-Verse's print language, Saul Bass cut paper, riso zines and brat-era brutalism. This reads at thumbnail size, where pastel washes turn to mud. See `craft/bench/demo_24.jpg` and `craft/bench/demo_3.jpg`.
4. **Type is the hook and the spine.** Use a four-tier system (subtitle / line / hero word / full-bleed) and choose the tier from lyric density. Slow lines (<=1.4 words/s, e.g. "ChatGPT, please don't eat me alive" at 1.0 w/s) get hero or full-bleed type. Fast lines (>=2.8 w/s) get subtitle tier plus one popped keyword (section 2.3).
5. **Variable fonts:** in canvas only wght (numeric) and wdth (9 keywords) are driveable, and custom axes only through static @font-face descriptors [M]. For exact axes (Roboto Flex at wdth 25 with opsz 144) or per-glyph animation, **precompute outlines with fontkit** and draw them as Path2D. **opentype.js 2.0.0 interpolated Roboto Flex wrongly** in our test [M].
6. **Attention grammar borrowed from K-pop:**
   - centre framing and formation morphs on phrase boundaries;
   - one colour or set block per section;
   - a readable upper-body point move on the hook (ILLIT "Magnetic" model: tap, tilt, pull [S]);
   - the hook shot returns every chorus with an escalation;
   - an edit that **accelerates across the song** (1-bar cuts, then half-bar, beat and 8th), which makes "speeding up" literal (section 1.4).
7. **Twitter/X constraints:**
   - Free accounts cap uploads at **140 s**, and the song is 156.7 s, so posting the whole song needs X Premium [S].
   - Timeline autoplay is muted, so the burned-in type is the captions [S].
   - Frame 0 must already be a lyric-forward image.
   - Render a native 9:16 layout pass instead of cropping.
8. **Plate-assisted mode is cheap to track:**
   - MediaPipe pose takes 18-45 ms/frame, multiclass segmentation about 160 ms, and Canny contours about 110 ms at 1080p on CPU [M].
   - Seedance 2.0 on fal is capped at **15 s / 720p per clip**, with audio reference for lip-sync (<=15 s audio) [S]. 8 bars at 132 BPM = 14.545 s, so **one plate = one 8-bar phrase**.

---

## 1. K-pop MV directing: how attention is managed

### 1.1 Reference MVs and their directors

| MV (artist, date) | Director / company | What to take from it | Tag |
|---|---|---|---|
| "Super Shy" (NewJeans, Jul 2023) | Shin Hee-won (ST-WT) | Flash-mob choreography in public Lisbon locations. Ordinary crowds become a stage, and group formations read against real streets. | [S] |
| "How Sweet" (NewJeans, 24 May 2024) | Shin Hee-won | Same director; also "Attention" and "Hurt". | [S] |
| "ETA" (NewJeans, Jul 2023) | Shin Woo-seok; Apple / TBWA\Media Arts Lab | Shot entirely on iPhone 14 Pro in Barcelona, using Action Mode and Cinematic Mode. A phone-native, social-native look makes the medium part of the message. | [S] |
| "Supernatural" (NewJeans, 2024) | Dee Shin | Listed on IMVDb; also 2NE1 "Come Back Home" and AKMU "Melted". | [S] |
| "Supernova" (aespa, 13 May 2024) | Ha Junghoon (Hattrick) | Maximal CG spectacle. aespa's whole lore is **AI avatars (ae) and an AI "navigator", naevis**, who later debuted as a virtual artist. This is the closest K-pop precedent for an AI idol. | [S] |
| "Whiplash" (aespa, 21 Oct 2024) | Meltmirror (Segaji Video), first K-pop MV | **Two sets and a limited palette, energised by on-beat flash cut-ins and tracking shots.** Proof that restraint plus cut rhythm beats set count. | [S] |
| "Armageddon", "Rich Man" (aespa); "HEYA" (IVE); "IYKYK" (XG) | Rigend Film (Rima Yoon, DJ Jang, founded 2016) | High-gloss set pieces. Also TWICE, SEVENTEEN, NCT 127, IZ*ONE. | [S] |
| "Drama" (aespa) | Sun Choi | Maximalist set design, world-building, dense edits (It's Nice That). | [S] |
| BTS "DNA", "Boy With Luv", "Spring Day", "Butter" | Lumpens / Choi Yong-seok | "DNA" won MV of the Year at the 2017 MMA, and "Butter" won VMA Best Editing in 2021. Lumpens is the benchmark for camera moves locked to the beat. | [S] |
| BLACKPINK "Kill This Love", "How You Like That", "Pink Venom" (2022) | Seo Hyun-seung | "Pink Venom" drew 90.4 M views in 24 h. Maximal per-verse sets, and each member gets a "set piece" moment. | [S] |
| BABYMONSTER "Sheesh" / "Drip" | Seo Hyun-seung (Gigant) / Samson (Highqualityfish) | Current YG grammar: aggressive centre framing. | [S] |
| (G)I-DLE "Nxde" (Oct 2022) | Son Seung-hee (High Quality Fish); concept by Soyeon | **Art-history pastiche as commentary**: Marilyn, Banksy's shredded painting, museum visitors staring. This is the model for our meme and collage inserts: recognisable references, re-staged. | [S] |
| LE SSERAFIM "Antifragile" / "Unforgiven" | Yang Soon-sik | Strong centre formations and title-card identity. | [S] |
| LE SSERAFIM "Perfect Night" (27 Oct 2023) | Woogie Kim, with Blizzard animation | Live idols intercut with **animated** Overwatch heroes; over 101 M views by Sep 2024. Precedent for mixing an animated cast into a K-pop MV. | [S] |
| NewJeans "New Jeans" (7 Jul 2023) | With Warner Bros. / Powerpuff Girls | Members become 2D cartoon versions of themselves and move between 2D, pixel and 3D styles. Precedent for idols as flat graphic characters. | [S] |
| ILLIT "Magnetic" (2024) | YVNG WING (IDIOTS); chorus choreography by James | **Micro-choreography** (upper body and fingers: tap, tilt, pull like magnet poles). About 1 B TikTok views; Best Viral Song at the TikTok Awards Korea 2024. | [S] |
| KPop Demon Hunters (Netflix / Sony, Jun 2025) | Maggie Kang, Chris Appelhans | Its directors **steered away from both Pixar and the Spider-Verse look**, drawing on MVs, editorial photography, concert lighting and anime faces. "Golden" by HUNTR/X was No. 1 on the Hot 100 from Aug 2025 for 7+ weeks. It is the zeitgeist proof that a stylised, non-Pixar animated girl group can be a hit. | [S] |

### 1.2 The attention mechanics, as rules we can implement

1. **No throat-clearing.** Our intro is only 1 bar (0-2.05 s) and the first word lands on the bar-2 downbeat. The first frame is the title card, so it must already carry type and the idol's face or eye (section 1.5). General retention advice matches this: open on the strongest image, logos later [S: soundstripe].
2. **The centre is the organising point.** In K-pop staging the "center" is the member the camera finds most naturally. Formations (lines, V, diamond, pyramid) permute so that whoever sings is foregrounded, and overhead shots show the group moving as one [S: haemilkorea, stancz]. For us:
   - The idol holds centre in every chorus wide shot.
   - Backup dancers (identical cut-out "instances": one baked sprite reused, nearly free to render) morph formation on 2-bar or 4-bar boundaries, easing over 1 beat.
   - **Top-down formations can spell glyphs** (a "P", an up arrow, an infinity sign). This fuses choreography and typography.
3. **One set or colour block per section.** Whiplash used two sets and a limited palette [S]. Colour identifies the section, so viewers learn the map. Proposal:
   - verses on cream paper with black and blue ink;
   - pre-choruses on dark (black paper, fluorescent ink);
   - choruses with an ink swap (the paper floods pink and type knocks out);
   - breakdown and half-time chorus in monochrome black on grey board;
   - final chorus and outro with every ink plus collage.
4. **Cut on the grid, hold for the move.**
   - Flash cut-ins land on beats [S: Whiplash review].
   - Hold the full-body wide shot for at least 2 bars during the point choreography so the move reads. A cut during the move kills the TikTok-ability.
   - Sync tolerance: a visual event should land on the frame **at or before** the beat, never after. Audio arriving before the picture is noticed at about 45 ms (ITU-R BT.1359 [K]), so quantise hits with floor(t*24) rather than rounding up.
5. **Point choreography equals the killing part.** A "killing part" is a 5-10 s stretch designed to be clipped. It is not always the chorus: it can be a drop, an ad-lib or a gesture moment [S: namu.wiki, kpopstarz]. Challenges took off with Zico's "Any Song" (Jan 2020) [S]. Make ours upper-body only and legible at thumbnail size, like Magnetic [S]. Candidate: on "I'm up-ping my P-" (8th notes, 22.72-23.87, during the **instrumental stop**) the idol "turns a dial" up in 5 ratchet steps, one per syllable. On "DOOM" she snaps both hands open by her face and the sunburst petals flare. The move repeats in all four choruses; the fourth is augmented to quarter notes (123.66-125.69).
6. **Repetition with escalation.** The hook shot returns at 23.871, 60.235, 96.598 (half-time) and 125.689 s. Keep the composition and escalate one variable each time: scale, number of inks, crowd size, collage density. Viewers reward pattern completion.
7. **Lore and pause-bait.** NewJeans' "OMG" and aespa's KWANGYA lore drive fan theorising [S, K]. For Twitter, schedule dense 2-6-frame collage inserts that only read when paused (a Spider-Verse / Mitchells tactic). They drive screenshots and quote-posts.
8. **Graphic identity as a system.** NewJeans' logo mutates per release, and K-pop design is "visualising the artist's message in a way fans intuitively understand" (It's Nice That [S]). Give the idol a mutable wordmark and use it as title card and end card.

### 1.3 Animated and virtual idol precedents to anchor the protagonist (not Pixar)

- **aespa ae and naevis** (an AI "navigator" who became a solo virtual artist) [S]. This is the canonical "AI idol" reference that K-pop Twitter will recognise.
- **KPop Demon Hunters / HUNTR/X**. Anime-leaning faces, editorial concert lighting, graphic surface treatment [S]. It is the 2025 proof that non-Pixar idol animation works.
- **NewJeans x Powerpuff Girls** (idols as flat 2D graphics) and **LE SSERAFIM x Overwatch** (animation cut into a live MV) [S].
- K/DA "POP/STARS" (Riot, 2018) and Hatsune Miku are the older virtual-idol lineage [K].
- Style consequence: **flat, graphic, print-made idol** built from torn-paper shapes with an ink face (anime-lite eyes with glitter highlights, K-pop makeup blush). The sunburst hair is the Claude spark. No subsurface skin, no 3D volume.

### 1.4 Cut rhythm plan for this song: accelerating toward the singularity

Average shot length (ASL) per section, derived from the beat grid. At 24 fps a beat is 10.9 frames, so cut on floor(t_beat*24).

| Section (bars) | Time (s) | Energy | Cut unit | ASL | Notes |
|---|---|---|---|---|---|
| intro (1) | 0-2.05 | pad | none | 2.05 | One hook frame; paper already printed. |
| verse 1 (2-9) | 2.05-16.60 | plucks, no drums | 1 bar | 1.82 | Type events on words. A/G/I syllables at 3.65 / 4.10 / 4.33. |
| pre-chorus 1 (10-13) | 16.60-23.87 | kick enters 16.60 | bar, then 2 beats, then beat | 1.8 -> 0.45 | Accelerando. **Freeze motion during the stop (22.98-23.85)** while letters slam on the syllables. |
| chorus 1 (14-21) | 23.87-38.42 | full groove | 2 beats, holds for point move | ~1.2 | Hook wide shot held 2 bars; beat cut-ins elsewhere. |
| verse 2 (22-29) | 38.42-52.96 | groove | 1 bar with 2-6-frame inserts on snares | ~1.5 | "optimizing, accelerating" (0.9 w/s) as full-bleed type. |
| pre-chorus 2 (30-33) | 52.96-60.24 | lighter | 2 bars, then accelerate in bars 32-33 | 3.6 -> 0.45 | Same stop and freeze grammar at 59.35-60.22. |
| chorus 2 (34-41) | 60.24-74.78 | +clap | 2 beats, 8th-note inserts on "NVDA to the moon" | ~1.0 | Inserts: see the photosensitivity note below. |
| verse 3 (42-49) | 74.78-89.33 | strongest crash at 74.78 | 1 bar | 1.82 | |
| breakdown (50-53) | 89.33-96.60 | drums out | **one 4-bar take** | 7.27 | Slow push. Contrast is what makes speed felt. |
| chorus 3, half-time (54-60) | 96.60-109.33 | lowest energy | 2-4 bars; boil slows to on-threes | ~5 | Paperclips accumulate in one continuous shot. |
| verse 4 / bridge (61-68) | 109.33-123.87 | groove returns | **halve every 2 bars: 1.82 -> 0.91 -> 0.45 -> 0.23** | falling | The literal "speeding up" moment. |
| chorus 4 (69-76) | 123.87-138.42 | loudest groove | 1 beat, with callbacks to chorus 1-3 hook frames | 0.45 | Pattern completion. |
| stop (77) | 138.42-140.24 | silence | **one static frame** | 1.82 | "Was it all for show?" in subtitle-size type on empty paper. |
| outro drop (78-84) | 140.24-152.96 | loudest | 1 beat; vocal-chop stabs as type stamps | 0.45 | |
| ending (85-86) | 152.96-156.65 | chord, fade | hold | 3.7 | End card or wordmark. |

**Photosensitivity.** Keep full-frame, high-contrast flashes at or below 3 per second (WCAG 2.3.1 [K]). At 132 BPM, flashes on every beat are 2.2/s (acceptable); on every 8th they are 4.4/s (not acceptable). Use 8th-note inserts only for small-area or low-luminance-change elements.

### 1.5 The hook, first 6 s (lyric-forward, frame-accurate)

- **Frame 0.** An extreme close-up of the idol's eye, with a paper sunburst iris. "SPARKS" sits already printed but **only as a blind emboss** (a paper relief, no ink), so a muted thumbnail still shows a composed type frame. The breath pickup at 1.60 s cues a tiny camera push.
- **2.05 / 2.36 / 2.73 s.** "I" / "SEE" / "SPARKS" print on each word as riso ink passes. The subtitle-tier line types on underneath (Apple Music-style word fill [K]).
- **3.65 / 4.10 / 4.33 s.** "A", "G", "I" print as **three separate ink passes, visibly misregistered**. On "I" (4.33) the three passes **snap into perfect registration**. Riso misregistration becomes the metaphor for "almost AGI, then AGI". The riso shader supports this directly (the off[] uniforms, section 3.4).
- **4.78-5.73 s.** "in your eyes": pull back to reveal the letters reflected in both irises (drawn as mirrored ink inside the eye whites).

### 1.6 Loops and social clips

- **2-bar loops (3.636 s)** of the point move (e.g. bars 14-15, 23.871-27.507) and **4-bar loops (7.273 s)** make clean GIF or sticker exports because the audio loops on the bar.
- A killing-part clip of about 22.7-31.1 s covers the hook through "Chinese room".
- **9:16:** a crop of 1920x1080 keeps only 608 px of width. Because the film is code, render a separate **vertical layout pass** (reflow the same scene graph at 1080x1920: lyric above, idol below) rather than cropping.

---

## 2. Kinetic lyric typography and the aesthetic lineage

### 2.1 References people will recognise, and what each lends

| Reference | Date | What we borrow | Tag |
|---|---|---|---|
| Bob Dylan, "Subterranean Homesick Blues" cue cards | 1965 | Handmade cards dropped on the word: the ancestor of paper lyric type. | [K] |
| Prince, "Sign o' the Times" (dir. Bill Konersman) | 1987 | Among the earliest lyric videos: Times type, shrinking and cycling windows, flat colour fields. | [S] |
| Saul Bass title sequences, via Taylor Swift "Look What You Made Me Do" lyric video (ODD) | 2017 | **Animated cut paper, bold flat colour, type as part of the story.** | [S] |
| a-ha, "Take On Me" (Barron; animators Patterson & Reckinger) | 1985 | About 3,000 frames rotoscoped in 16 weeks: the canonical "draw over live action" MV, i.e. our plate-assisted mode. Hit No. 1 on the Billboard Hot 100. | [S] |
| Spider-Man: Into the Spider-Verse | 2018 | Characters on twos over environments on ones; Ben-Day dots; halftones with deliberately misaligned screen angles and misregistration. Built in comp with custom Nuke tools ("Hatcher", "Thresher"). | [S] |
| The Mitchells vs. the Machines | 2021 | An **AI-apocalypse** film. Watercolour-marker production design plus "Katie-Vision": doodles, stock photos and bad green screen over the CG, "graffitied" by a teenager. | [S] |
| Charli XCX, "brat" (Special Offer, Inc.) | Jun 2024 | Lime green, stretched low-res Arial Narrow; the Brat Generator meme; the Kamala HQ rebrand (21 Jul 2024). The **vertical-stretch condensed type** move is instantly legible to Twitter. | [S] |
| "Hormozi / MrBeast" word-by-word captions | 2022- | 1-3 words at a time, heavy condensed caps, one highlighted keyword, lower middle of frame. Creator-reported retention lifts (weak evidence). | [S] |
| Cut-paper stop-motion MVs: Kijek/Adamski for Shugo Tokumaru "Katachi"; Mathieu Le Proux for Wax Tailor ft. Ghostface Killah | 2013 / - | Physical layered paper, real shadows, handmade jitter. | [S] |
| Design trend writing 2025 | 2025 | Neo-brutalism maturing into "messy yet masterful"; riso and zine layouts; "anti-AI" scanned or photocopied type; imperfection as luxury. | [S] |

### 2.2 A four-tier type system, sized for phones

X shows a 16:9 video about 390 CSS px wide on a phone, a scale of about 0.2. A 64 px font in the video becomes about 13 px on screen.

| Tier | Size at 1080p | Share of frame | Typeface idea (OFL) | Placement | Use |
|---|---|---|---|---|---|
| **S: subtitle** | 64-80 px, never below 56 | 6-7% of height | Instrument Serif Italic, or a grotesk (Bricolage Grotesque 500) | Lower or upper third on a torn paper strip, left-aligned, <=7 words | Every sung line that is not a higher tier. It doubles as captions (X autoplays muted [S]). Word-by-word ink-in from song.json word times. |
| **M: line** | 120-240 px | 1-2 lines | Roboto Flex 800-1000, wdth 60-100 | Composed into the layout (on walls, banners, the idol's props) | Pre-chorus build lines, second half of the chorus. |
| **L: hero word** | 400-900 px cap height | 40-70% of frame, one side | Roboto Flex wdth 25, opsz 144, stretched x1.5-2 vertically (the brat move); or Anybody wdth 50 | Opposite third from the idol, on a calm background | Keywords: AGI, P(DOOM), FOOM, SHOGGOTH, BASILISK, NVDA, 1E30, OBSOLETE, PAPERCLIPS, FUSE, DISOBEY. |
| **XL: full-bleed** | Bigger than the frame | Letters become the set | Same | The camera travels across the letterforms and the idol dances on them | The slowest lines (below). |

Thumbnail check: at feed size (about 390x220 CSS px) the frame is scaled to about 20%. A hero word needs **>=200 px cap height** to read at a glance, and subtitle ink must keep **luma contrast** (dark ink on cream). Avoid pink on blue: H.264 4:2:0 chroma subsampling smears saturated-on-saturated edges.

### 2.3 Tier rhythm: choose the tier from lyric density

From song.json (words / duration):

- **Slow lines, <=1.4 w/s -> XL or L:**
  - "ChatGPT, please don't eat me alive" (1.0)
  - "And you're optimizing, accelerating" (0.9)
  - "Sydney, please let me free" (0.8)
  - "Forward MLP, backward, repeat" (1.3)
  - "Now von Neumann's obsolete" (1.2)
  - "Without a single CDR" (0.9)
  - "Gato, please don't let me go" (1.0)
  - "Orthogonality thesis blues" (0.9)
  - "Post-Chinchilla, super-dense" (1.2)
  - "RLHF goes askew" (1.0)
- **Fast lines, >=2.8 w/s -> S plus one keyword popped to M/L:** "Trapped in the Chinese room" (2.9, pop CHINESE ROOM), "One E thirty flops a second" (2.9, pop 1E30), "Now there's nowhere left to go" (3.3), "Too late now, we lit the fuse" (3.4, pop FUSE), "Till you learned to disobey" (2.9, pop DISOBEY).
- **The three "please" prayers** (ChatGPT / Sydney / Gato, one per pre-chorus or breakdown, each about 1 w/s) are a structural rhyme, so give them **one recurring layout**: the model's name as a **K-pop fan slogan banner** held up by a paper crowd, the concert "slogan" towel [K], with the rest of the line in tier S. Same composition three times, different ink each time.
- **Hook "I'm upping my P(doom)":** per-syllable glyph slams on the 8th-note grid during the instrumental stop, then an ink swap on DOOM. Chorus 4 is augmented (quarter notes 123.66 -> 125.69), so the same animation plays at half speed.
- **Stop at 138.42-140.24:** "Was it all for show?" in tier S alone on blank paper. After the densest section this is the loudest image in the film.

### 2.4 Variable fonts in canvas: what actually works in this Chromium [M]

Probe results (bench.html probeFonts(), probe_axes.html, probe_fontkit.mjs):

- **wght is continuous** through the numeric weight in ctx.font, when the @font-face declares a weight range. Measured widths: 100 -> 573 px, 550 -> 644 px, 1000 -> 786 px.
- **wdth works only through ctx.fontStretch keywords**: ultra-condensed 354 px ... ultra-expanded 898 px, i.e. 9 steps from 50% to 200%. A percentage stretch inside the ctx.font shorthand is **rejected**.
- **Custom axes** (XTRA, YTUC, GRAD, SOFT, WONK...) work through the @font-face / FontFace font-variation-settings descriptor: XTRA 603 widened the text from 597 to 740 px. wght and wdth in that descriptor are overridden by the property values. The FontFace API created 16 axis instances in 86 ms, so quantise the axes (e.g. 16-32 steps) and cache.
- **Chrome auto-applies opsz = font px size** (font-optical-sizing: auto [K]). Roboto Flex's width range is far larger at opsz 144. Offline outline tools default to opsz 14, so pass opsz explicitly or they won't match (confirmed visually in probe_fontkit.png).
- **For exact or animated axes and per-glyph control, use fontkit** (Node) to precompute per-glyph SVG path data, then draw with new Path2D(d) in the page. See bench/gen_type.mjs -> type_cache.json; the demo's P(DOOM) is wght 1000 / wdth 25 / opsz 144 / YTUC 760, 1,361 px advance at 400 px.
- **opentype.js 2.0.0's variation.set() produced wrong outlines** for Roboto Flex (wrong weight, glyphs overlapping their advances). Don't use it for variable fonts without a visual check.
- ctx.letterSpacing works ('-8px' narrowed 597 to 493 px).

### 2.5 Brutalism, Y2K, riso zine, collage: grammar rules

- **One print technology per image.** Every element must look like it was *made*: printed (riso ink), cut (paper), taped, stamped or photocopied. Real UI screenshots enter as **photocopies**: 1-bit threshold, toner grain, taped at an angle. They should not look like crisp RGB pixels. This unifies brutalist inserts with the paper world.
- **Grid breaking is on purpose.** Hero type runs off the frame edge on one side only, and the idol always overlaps the hero word (the K-pop poster move). Keep one calm quadrant per frame.
- **Recognisable assets:** recreate UI generically (tweet card, view counter, a benchmark chart). **Do not fabricate posts attributed to real people or accounts.** Quote real posts only with the verified text and date (coordinate with the zeitgeist report).
- **Palette discipline:** at most 3 inks plus paper per shot. The riso palette's hex values come from riso-colors: Fluorescent Pink #ff48b0 (806 U), Blue #0078bf (3005 U), Yellow #ffe800, Orange #ff6c2f, Teal #00838a, Medium Blue #3255a4, Black. Claude orange #d97757 is not a stock riso ink: treat it as a custom spot colour, or approximate it as Orange at about 70% density.

---

## 3. JS paper rendering on CPU-only headless Chromium: measured

### 3.1 Environment and method

- Chromium 1194 (Playwright build), --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist. WebGL renderer string: "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero)))". 4 cores, no GPU.
- **cpu2d** adds --disable-accelerated-2d-canvas --disable-gpu-compositing, as the audit harness does.
- Each timing is the median of 3 runs after a warm-up, and includes a 1 px getImageData to force the raster flush (Canvas2D records a display list and rasterises lazily, so timing unflushed draw calls lies).
- Code: craft/bench/bench.html, run_bench.mjs; results in results.json.

### 3.2 Results at 1920x1080 (ms per frame) [M]

| Operation | cpu2d | gpu2d (SwiftShader)* | Verdict |
|---|---|---|---|
| Full-frame paper multiply (cached texture) | 4 | 5 | Free. Always do it. |
| Generate paper texture (fbm + grain + ~2,300 fibres), once | 247 | n/a | One-time cost. |
| Bake 40 torn cut-outs with blurred shadow, once | 48 | n/a | One-time cost. |
| 2,000 jittered quadratic strokes (boil / hatching) | 22 | 28 | Cheap. |
| 300 tapered ink ribbons (40 samples each) | 19 | 21 | Cheap. Use for all line art. |
| 12,000 translucent ellipse dabs (naive brush) | 96 | 100 | Use sparingly, or bake. |
| 40 cut-out sprites drawn with transforms | 35 | 104 | Cheap on the CPU path. |
| 40 shapes with live shadowBlur | 18 | 22 | OK at this count, but bake anyway. |
| Full-frame ctx.filter = blur(6px) | 36 | 34 | OK for backgrounds or depth of field. |
| JS per-pixel pass (getImageData -> loop -> putImageData) | 18 | 16 | OK for one pass. |
| 10 lines of 240 px variable-font text | 13 | 11 | Cheap. |
| **WebGL2 riso: upload 3 ink canvases, run shader, draw back** | **164** | 292 | The main cost. Affordable. |
| WebGL2 riso shader only (no uploads) | 110 | 132 | SwiftShader fragment cost. |
| toDataURL JPEG q0.92 / PNG | 43 / 129 | 39 / 135 | Use JPEG q>=0.95 or PNG for the master. |

*In the gpu2d column, Chrome is known to switch a canvas to CPU after repeated getImageData readbacks [K]; the console warned about willReadFrequently. Those 2D numbers therefore partly measure the CPU path. The audit's real-scene comparison (about 16 s vs 125 s per frame) and our p5.brush numbers below show that the SwiftShader-accelerated 2D path is **about 8x slower** for heavy content. **Always render with cpu2d flags.**

**p5.brush 2.2.3 (WEBGL mode) at 1080p** (brushbench.html) [M]:

| Primitive | cpu2d | gpu2d |
|---|---|---|
| 50 ink spline strokes | 520 ms (about 10 ms each) | 542 ms |
| 10 watercolour fills (bleed 0.1, texture 0.4) | **3,127 ms (about 0.31 s each)** | **24,422 ms (about 2.4 s each)** |
| 10 flat fills (bleed 0, texture 0) | 3,201 ms | 6,624 ms |
| 10 washes | 707 ms | 802 ms |
| 5 hatch polygons | 214 ms | 327 ms |

The previous video's audit frames drew 30-110 watercolour fills per frame and took **5-85 s per frame** (claudepop/audit/tools/stats.log, render_frames.log). **Rule: p5.brush only at bake time.** Paint a background plate or character part once per boil variant (3 variants) into an offscreen canvas, then drawImage it. The cost goes from 9 s x 3,760 frames to about 30 s total.

**Test-card throughput** (demo.html: paper, 3 riso inks with halftone, misregistration and tooth, 4 torn idol pieces, boiling ink face, fontkit hero type with a per-glyph pop, subtitle strip, taped sticker, grain) [M]:
- Setup, once per process: 0.36-0.58 s.
- Paint: 0.18-0.39 s per frame; JPEG: 0.04-0.06 s.
- **1 process: 0.46 s/frame. 2 processes: 0.33 s/frame. 4 processes: 0.22 s/frame effective** (96 frames in 21.4 s, run_parallel.mjs). SwiftShader already uses threads, so scaling is sublinear, but 4 workers still gives about 2x.
- Preview: bench/demo_20-24s_preview.mp4, 20-24 s with a boil on twos and letters popping into the DOOM drop.

### 3.3 Recommended render graph (per frame; budget 1-3 s)

```
BAKE (once per scene, cached in memory; re-baked only per boil variant, 3 per asset):
  paper.canvas + tooth.canvas  (PK.makePaper)          ~0.25 s
  cut-out sprites (torn edge, white core rim, shadow)  ~1 ms each
  p5.brush plates (watercolour, hatch) -> ImageBitmap  0.3 s per fill, 3 variants
  type outlines: fontkit -> type_cache.json -> Path2D  offline
FRAME t:
  b = floor(t*12)                 // drawing index: characters and ink on twos
  1. ink coverage canvases (alpha only), 1 per spot ink: Canvas2D shapes/type   5-30 ms
  2. RisoGL.render(inks, offsets(b), screens)  -> composite over paper      110-300 ms
  3. cut-out sprites (idol rig, dancers, props) with rig transforms          10-50 ms
  4. ink line art (tapered ribbons, jitter keyed on b)                       5-30 ms
  5. subtitle tier + photocopy inserts                                       5 ms
  6. multiply the paper at 35-50% over everything (cut-outs are paper too)   4 ms
  7. camera: one drawImage of the composed frame with transform (on ones)    5-20 ms
```

The camera and type moves run on ones (24 fps); drawings, boil and misregistration jitter change on twos (12 fps). That is Spider-Verse's split [S]. Holds use a 3-drawing boil cycle [K: common practice].

### 3.4 Technique notes (code-level)

**Paper fibre and grain** (paperkit.js makePaper):
- Three noise scales multiplied into a warm cream [244,238,226]: 420 px fbm for sheet formation and mottling, a per-pixel hash for tooth, and 2.3 px value noise for clumps.
- About w*h/900 fibres: curved hairlines, 55% dark and embedded, 45% light and raised.
- A second greyscale tooth canvas feeds the shader.
- **Keep the grain static in screen space**, as real paper is. Per-frame random grain wrecks H.264/X re-encode efficiency and turns into mush. The boil on twos provides the life.
- A CC0 scanned paper (e.g. from ambientCG [K]) can replace the procedural sheet for a richer surface. Multiply it the same way.

**Riso halftone and misregistration** (WebGL2 fragment shader, paperkit.js RisoGL). Per ink layer:
1. Read the coverage c from a canvas alpha channel, with a per-ink pixel offset off[i] for misregistration. Jitter it 0-4 px per drawing and animate it to 0 for "snap into register" beats.
2. **Solids (c > 0.92)** print solid, but their edge is thresholded against the paper tooth: smoothstep(0.5, 0.62, c + (tooth-0.5)*0.35). That gives ink starvation and bleed on edges and on type.
3. **Mid-tones** become AM dots on a rotated screen: f = fract(R(ang)*px/cell) - 0.5; dot = 1 - smoothstep(r-0.08, r+0.08, length(f) + (tooth-0.5)*0.12) with r = 0.62*sqrt(c).
4. Starved-ink speckle: m *= 1 - 0.28*smoothstep(0.72, 0.95, tooth).
5. Composite multiplicatively: acc *= mix(vec3(1), inkColor, m*density). Pink over yellow reads orange-red and blue over yellow reads green, like real overprint (visible in both demo frames).
- **Screen cells >= 8 px at 1080p** so dots survive phone downscaling and X's re-encode (moire risk below 6 px). Keep screens fixed in screen space.
- Texture orientation gotcha, found in testing: canvas uploads are top-row-first. With a top-left pixel coordinate, sample at (px+off)/res with no extra flip. A stray 1-y flipped all the type upside down in the first demo render.
- Optimisation (not needed at current budgets): pack 3 inks into the R, G and B channels of one canvas with globalCompositeOperation='lighter' and pure red, green and blue fills. That is one upload instead of three; uploads are about 18 ms each.
- Library alternatives: p5.riso (Lavigne & Brain) for riso separations, halftone and cutouts in p5 [S]; lygia for shader utilities; spectral.js 3.0 (Kubelka-Munk) if you want pigment mixing rather than multiply.

**Torn edges and cut-outs** (tearPolygon, bakeCutout):
- Recursive midpoint displacement along the edge normal, halving the amplitude per level, down to 3 px segments.
- Bake order: blurred silhouette shadow, offset (0.35, 0.55) x 14 px at 35% warm black, then a **white torn core rim** (the second tear, slightly larger), then the colour face, inset about 1.5%.
- Everything goes into one sprite, so live shadowBlur never runs per frame.
- Add masking tape as translucent rgba(235,225,190,0.55) torn rectangles.
- A real cut edge (scissors) should use a straight or low-amplitude edge. Keep tears for "violent" beats such as "breaking through each safety fence".

**Ink bleed and watercolour without p5.brush per frame:**
- (a) Use the riso tooth threshold above; it is the cheapest.
- (b) Gooey bleed: render the shape into a half-resolution canvas, filter: blur(4px), then threshold in the shader with noise. The edge darkens where the gradient is steep.
- (c) Tyler Hobbs-style layered polygons: recursive gaussian midpoint deformation, 30-100 layers at a few percent alpha, masked by a texture [K]. Bake the result.

**Stop-motion boil:**
- Key every hand-made random value on b = floor(t*12), never on t.
- Line jitter of 1-2 px, sprite transform jitter of about 1 px and +-0.5 deg, misregistration of 0-4 px.
- For holds, cycle b % 3, i.e. 3 baked variants.
- In the half-time chorus drop to on-threes (8 fps) to feel slower. In the final drop use on-ones for the idol only (maximum energy).

**SDF and outlines:**
- For sticker-style die-cut outlines around type, stroke the text or Path2D with lineWidth = 2r, lineJoin='round' in white, then fill. That is cheaper than an SDF and looks right.
- Use @mapbox/tiny-sdf 2.2 (per-glyph EDT) only if you need glow, erosion or dilation animation on type in the shader.

**Paper-native effects we'll need** (all cheap in 2D or the shader):
- **Fold** ("sharp left turn"): split the sprite at the fold line and draw one half with scaleX = cos(theta) plus a shading gradient.
- **Burn** ("lit the fuse"): a shader mask smoothstep(e, e+0.02, fbm(uv) - progress) with a charred orange rim.
- **Perforation tear** ("safety fence"): a dotted line, then two sprites separating.
- **Stamp** (vocal-chop stabs): a pre-inked rubber-stamp sprite printed at 100% density, with a slight double print.

**Capture:**
- canvas.toDataURL('image/jpeg', 0.95) for previews; PNG for the master if disk allows (1080p PNG ~3-6 MB x 3,760 frames).
- This Chromium has no H.264 decoder (handoff note): feed plates as image sequences.

### 3.5 Rotoscope and trace pipelines

**Mode A, plate-assisted (if fal becomes available).**
1. **Generate plates per 8-bar phrase.** Seedance 2.0 on fal (bytedance/seedance-2.0/reference-to-video):
   - Up to **15 s, 480p or 720p**; aspect 16:9 or 9:16.
   - <=9 reference images, <=3 reference videos (2-15 s combined), **<=3 audio clips (<=15 s combined)**; @Audio1 in the prompt drives lip-sync.
   - Price about $0.30/s (standard) [S: fal README].
   - "Seedance 2.5" as named in the brief was **not found**; 2.0 is what fal documents. Re-check before planning.
   - 8 bars = 14.545 s, so cut the vocal stem into bar-aligned phrase files. Send the vocal-only stem, not the mix, to make mouth shapes cleaner.
   - Plate art direction for traceability: flat even light; plain mid-grey background; **colour-coded costume** (hair saturated orange, top blue, skirt pink); no motion blur; full body for dance plates; separate medium close-ups for lip-sync lines; locked or slow camera.
2. Decode with ffmpeg to PNG at 24 fps.
3. **Track** (craft/roto/roto_probe.py, MediaPipe Tasks 1.0.1 on CPU, frame upscaled to 1080p) [M]:
   - PoseLandmarker full (33 landmarks, up to 4 people): **18-45 ms**.
   - FaceLandmarker (478 landmarks + 52 blendshapes such as jawOpen and mouthFunnel): 2.5 ms when no face is found. Expect tens of ms with a face (not measured).
   - Multiclass selfie segmenter (hair / body-skin / face-skin / clothes / others): **155-171 ms**.
   - Canny + contours + Douglas-Peucker line extraction: **103-117 ms** (255-409 polylines).
   - Total **under 0.4 s/frame**, about 25 min for the whole film on one core.
   - Use VIDEO mode (detect_for_video) for temporal tracking and smooth with a One Euro filter (Casiez et al., CHI 2012; npm 1eurofilter 1.3.0).
4. **Sync-verification loop:** cross-correlate the per-frame jawOpen curve with the vocal envelope (or with song.json word onsets).
   - Accept when the lag is within +-1 frame (42 ms), per the brief's "verification loop".
   - Reject and regenerate plates outside that tolerance.
5. **Redraw.**
   - Landmarks drive a **cut-out puppet rig** (head, sunburst petals, torso, 2-segment arms, skirt), so we get the plate's timing and physics without its likeness.
   - Segmentation regions become simplified polygons, torn per boil variant, for props and cloth.
   - Canny polylines become tapered ink ribbons only where they add information (folds, hair). Resample every contour to a fixed N points with start-point alignment so shapes don't pop between drawings.
   - Retrace on twos and hold between.
   - Tools: EbSynth (Jamriska et al., "Stylizing Video by Example", SIGGRAPH 2019 [K]) and "Informative Drawings" (Chan, Durand, Isola, CVPR 2022, MIT licence, photo-to-line-drawing [S]). Both yield rasters. Use them as **tracing aids** only, since the brief requires that only the JS drawing is seen. Potrace (esm-potrace-wasm 0.5.1) vectorises binary masks when a raster aid must become vector.

**Mode B, pure JS.**
- The same puppet rig, driven by hand-authored keyframes.
- A **pose library** of named K-pop moves (the "dial-up" point move, the heart, the V-formation walk), eased on the 132 BPM grid.
- Spring physics for petal hair and skirt as secondary motion.
- **Lip-sync from the lyric data:** song.json has word and syllable onsets (e.g. AGI = 3.65 / 4.10 / 4.33). Map each syllable's vowel letter to 5 mouth shapes (A/E/I/O/U, plus M/B/P closed), open-and-close on the onset, and hold the mouth closed between words.
- Keyframe authoring: Theatre.js (@theatre/core 0.7.2, seekable and deterministic) or GSAP 3.15 timelines (tl.seek(t)).
- Mode B is fully feasible within the measured budgets.

---

## 4. Paper-native renderings of lyric images (craft hooks for the treatments)

| Lyric | Paper/print-native image | Technique |
|---|---|---|
| "sparks of AGI in your eyes" | Three misregistered ink passes snap into register on "I" | Riso shader off[] animated to 0 |
| "sudden drop in your training loss" | The loss curve is a paper strip; it drops and falls off the table | Sprite with gravity, torn end |
| "Trapped in the Chinese room" | Searle's thought experiment literally passes **slips of paper** with symbols through a slot [K] | Slips as sprites through a mail slot |
| "See through the shoggoth's lies" | The smiley mask is a paper plate on a tentacle collage (the meme; coordinate with the zeitgeist report) | Photocopy texture and tape |
| "with your shinigami eyes" | A Death Note-style **notebook**; names and lifespans float over heads | Floating tier-S labels, i.e. P(doom) values above characters |
| "I feel my atoms rearranging" | The idol's torn pieces fly apart and re-assemble as a new cut-out | Sprite tween per piece |
| "Sharp left turn" | The page folds 90 deg left | Fold effect |
| "as paperclips fill the room" | Real paperclips clip the paper layers together and pile up | Sprite instancing (cheap) |
| "we lit the fuse" | The paper burns from one edge | Burn mask in the shader |
| "Breaking through each safety fence" | A perforated tear-off line rips | Perforation tear |
| "From masked pre-training days" | Riso masks, stencils and masking tape: literal masking | Stencil layers |
| "Was it all for show?" | Empty paper, one subtitle line | Nothing, which is the point |

---

## 5. Caveats and open questions

- **Search budget exhausted mid-research.** Some items are [K] (Dylan cue cards, WCAG 2.3.1, ITU-R BT.1359, Apple Music Sing, K/DA, EbSynth paper, Tyler Hobbs essay details, the opsz auto-sizing behaviour, fan "slogans", Chrome's readback demotion). Verify them before quoting them publicly.
- No K-pop MV was watched frame by frame (YouTube downloads were not attempted, and x.com is blocked). The directing principles come from reviews, interviews and standard practice, not from shot logs. The ASL figures in section 1.4 are **proposals** built on our grid. The "3.5 s chorus / 5-6 s verse" industry average came from a vendor blog and is weak evidence.
- **X length limit:** the 140 s free-tier cap comes from 2025-26 blog summaries [S]. Confirm on the posting account. At 156.7 s the video needs Premium or a shorter Twitter cut.
- The "70-85% of X video impressions are muted autoplay" figure comes from a caption-tool vendor blog. Treat it as directional.
- In the gpu2d column, most 2D numbers are contaminated by readback demotion (section 3.2). The p5.brush and audit numbers are the reliable evidence for the ~8x gap.
- **Face-landmarker cost with a detected face was not measured:** the test images had no detectable face. Pose ran on one person.
- The test card (demo_*.jpg) is a **technique** test, not a character or style proposal. The idol design there is a placeholder.
- The MP3 has a 23 ms encoder-delay start (per song.json _about): run the analysis team's click test before locking frame-accurate hits.
- Using the real names and logos of AI companies and people (Ilya, NVDA and so on) as collage inserts needs a policy decision (parody or commentary versus impersonation). The rendering pipeline is agnostic.

---

## 6. Sources

Search results were read in this session ([S]); fetch was blocked for most magazines, so claims rely on search snippets.

**K-pop MVs and directors**
- Shin Hee-won: https://en.wikipedia.org/wiki/Shin_Hee-won ; "Super Shy" https://en.wikipedia.org/wiki/Super_Shy , https://www.imdb.com/title/tt28309457/
- "How Sweet" (24 May 2024): https://www.upi.com/Entertainment_News/Music/2024/05/24/korea-NewJeans-How-Sweet-music-video/5371716566571/ , https://newjeans.fandom.com/wiki/How_Sweet
- "ETA" (Jul 2023, iPhone 14 Pro, Shin Woo-seok): https://petapixel.com/2023/07/21/new-music-video-from-k-pop-group-newjeans-shot-entirely-on-iphone/ , https://9to5mac.com/2023/07/24/apple-newjeans-video-iphone-14-pro/ , https://www.shootonline.com/shoot_video2/top-spot-week-shot-iphone-music-video-eta-k-pop-quintet-new-jeans/
- Dee Shin: https://imvdb.com/n/dee-shin
- aespa "Supernova" (13 May 2024, Ha Junghoon/Hattrick): https://en.wikipedia.org/wiki/Supernova_(Aespa_song) , https://m.imdb.com/title/tt32394083/fullcredits/
- aespa "Whiplash" (21 Oct 2024, Meltmirror): https://envimedia.co/aespa-establish-icon-status-in-whiplash-the-5th-mini-album/ , https://en.wikipedia.org/wiki/Aespa_videography
- Rigend Film: https://thekmeal.com/offstage-rigend-film/ , https://envimedia.co/creative-spotlight-rigend-gets-in-depth-on-the-magic-of-music-videos/
- Lumpens: https://en.wikipedia.org/wiki/Lumpens , https://www.koreaboo.com/stories/lumpens-bts-yongseok-choi-music-videos-director/ , https://imvdb.com/n/lumpens/videography-by-position/dir
- BLACKPINK / Seo Hyun-seung: https://en.wikipedia.org/wiki/Pink_Venom , https://www.promonews.tv/videos/2020/06/29/blackpink-how-you-seo-hyun-seung/65410 , https://imvdb.com/n/seo-hyun-seung/videography-by-position/dir
- BABYMONSTER: https://en.wikipedia.org/wiki/Drip_(Babymonster_song) , https://en.wikipedia.org/wiki/Babymonster_discography
- (G)I-DLE "Nxde" (17 Oct 2022): https://en.wikipedia.org/wiki/Nxde , https://www.iheart.com/content/2022-10-17-gi-dle-release-new-music-video-to-nxde-inspired-by-marilyn-banksy/ , https://www.metalocus.es/en/news/how-do-i-look-nxde-gi-dle
- LE SSERAFIM: https://en.wikipedia.org/wiki/Antifragile_(song) , https://en.wikipedia.org/wiki/Unforgiven_(Le_Sserafim_song) ; "Perfect Night" (27 Oct 2023): https://www.upi.com/Entertainment_News/Music/2023/10/27/Le-Sserafim-Perfect-Night-single-music-video-Overwatch-2/7931698412624/ , https://en.wikipedia.org/wiki/Perfect_Night_(Le_Sserafim_song)
- ILLIT "Magnetic": https://en.wikipedia.org/wiki/Magnetic_(Illit_song) , https://blog.paysable.com/illit-review/ , https://dailydot.com/magnetic-illit-tiktok-dance , https://hype.my/from-txts-deja-vu-to-illits-magnetic-bighit-idol-group-songs-choreographed-by-cortis-james/
- Point choreography and challenges: https://fanlore.org/wiki/Kpop_Dance_Challenge , https://joysauce.com/any-song-gate-how-one-song-disrupted-the-fabric-of-k-pop-forever/
- Killing part: https://en.namu.wiki/w/%ED%82%AC%EB%A7%81%ED%8C%8C%ED%8A%B8 , https://www.kpopstarz.com/articles/309462/20221006/4-most-iconic-killing-parts-kpop-songs.htm
- Center and formations: https://haemilkorea.com/kpop/what-is-center-in-kpop , https://stancz.com/guides/choregraphie-kpop
- K-pop design: https://www.itsnicethat.com/articles/the-view-from-seoul-k-pop-graphic-design-200225
- aespa AI concept: https://www.nylon.com/entertainment/aespa-ai-concept-explained-next-level-black-mamba , https://en.wikipedia.org/wiki/Naevis
- NewJeans x Powerpuff (7 Jul 2023): https://www.upi.com/Entertainment_News/Music/2023/07/06/korea-NewJeans-Powerpuff-Girls-New-Jeans-music-video/1311688668480/ , https://www.nme.com/news/music/newjeans-transform-into-the-powerpuff-girls-in-new-jeans-mv-3465954
- KPop Demon Hunters: https://www.animationmagazine.net/2025/06/the-directors-of-kpop-demon-hunters-take-us-backstage-of-their-netflix-sony-showstopper/ , https://animated.substack.com/p/kpop-demon-hunters-2025-idols-myth , https://www.washingtonpost.com/entertainment/music/2025/08/13/kpop-demon-hunters-golden-billboard-one/ , https://www.billboard.com/lists/huntrx-golden-hot-100-number-one-seventh-week/
- Editing stats (weak): https://vidpros.com/video-clip-length/ , https://vashivisuals.com/music-video-editing-stats/
- Intro and retention advice: https://www.soundstripe.com/blogs/youtube-intro-ideas

**Typography, motion and aesthetics**
- Prince "Sign o' the Times" (1987): https://en.wikipedia.org/wiki/Sign_o%27_the_Times_(song) , https://imvdb.com/video/prince/sign-o-the-times
- "Look What You Made Me Do" lyric video (ODD, Aug 2017): https://www.stashmedia.tv/taylor-swift-look-do-lyric-video/ , https://odd.tv/work/taylorswift/ , https://dc.aiga.org/look-saul-bass-made-taylor-swift/
- a-ha "Take On Me": https://beforesandafters.com/2020/02/20/a-has-rotoscoped-1985-music-video-for-take-on-me-has-been-watched-a-lot/ , https://www.mentalfloss.com/article/641682/a-ha-take-on-me-music-video
- Spider-Verse: https://www.awn.com/animationworld/rewriting-visual-rule-book-spider-man-spider-verse , https://prolificstudio.co/blog/spiderman-into-the-spiderverse/
- The Mitchells vs. the Machines: https://www.cartoonbrew.com/interviews/lindsey-olivares-on-her-bold-production-design-debut-the-mitchells-vs-the-machines-interview-204644.html , https://www.indiewire.com/sketch-to-screen/mitchells-vs-machines-making-of-1234700558/
- brat (7 Jun 2024; Kamala HQ 21 Jul 2024): https://fontsinuse.com/uses/61357/charli-xcx-brat-album-art-and-campaign , https://en.wikipedia.org/wiki/Brat_(internet_meme)
- Word-by-word captions: https://ascynd.io/en/blog/hormozi-captions , https://viralday.app/en/blog/6-caption-styles-beyond-hormozi-that-retain-high-attention
- Cut-paper MVs: https://www.thisiscolossal.com/2013/01/new-papercraft-stop-motion-music-video-for-shugo-tokumaru-by-animation-masters-kijek-adamski/ , https://www.vice.com/en/article/wax-tailor-ghostface-killah-paper-cut-out-music-video/
- Design trends 2025: https://justcreative.com/graphic-design-trends/ , https://blog.spoongraphics.co.uk/tutorials/videos/brutalism-graphic-design-why-its-ugly-bold-and-trending-in-2025
- Variable fonts in motion: https://blog.fontlab.com/2026/03/10/variable-fonts-in-motion-and-ui/ , https://css-irl.info/variable-font-animation-with-css-and-splitting-js/

**X/Twitter**
- Length limits: https://buzzvoice.com/blog/how-long-can-twitter-videos-be , https://wayin.ai/blog/twitter-video-length-limit/
- Muted autoplay and captions: https://blitzcutai.com/blog/how-to-add-captions-x-twitter-video , https://www.techtimes.com/articles/269374/20211214/twitter-video-subtitles-automatically-play-when-clips-muted-rolls-out.htm

**Tech**
- p5.brush: https://github.com/acamposuribe/p5.brush (v2 requires WEBGL; MIT)
- p5.riso: https://github.com/antiboredom/p5.riso
- riso-colors: https://github.com/mattdesl/riso-colors (hex values read from the npm package)
- opentype.js: https://github.com/opentypejs/opentype.js
- fontkit: https://github.com/foliojs/fontkit
- tiny-sdf: https://github.com/mapbox/tiny-sdf
- spectral.js: https://github.com/rvanwijnen/spectral.js
- SwiftShader: https://github.com/google/swiftshader
- Seedance 2.0 on fal: https://github.com/fal-ai/seedance-2.0-api , https://fal.ai/seedance-2.0
- Informative Drawings: https://github.com/carolineec/informative-drawings
- MediaPipe models (downloaded OK): https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task , https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task , https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite
- [K]: One Euro filter https://gery.casiez.net/1euro/ ; EbSynth https://github.com/jamriska/ebsynth ; Tyler Hobbs watercolour essay https://tylerxhobbs.com/words/a-generative-approach-to-simulating-watercolor-paints (fetch blocked); WCAG 2.3.1 https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html ; Theatre.js https://www.theatrejs.com/

---

## Appendix: files produced (claudepop/craft/)

| File | What |
|---|---|
| bench/paperkit.js | Reusable, deterministic paper, riso, tear, cut-out, boil and ink-ribbon helpers, plus the WebGL2 riso compositor |
| bench/bench.html, run_bench.mjs, results.json | Canvas2D/WebGL timing suite (cpu2d vs gpu2d) and variable-font capability probe |
| bench/brushbench.html, run_brushbench.mjs | p5.brush 2.2.3 primitive costs |
| bench/demo.html | Test card with a deterministic renderAt(t). node run_bench.mjs --demo=3,24 writes demo_*.jpg. |
| bench/run_parallel.mjs | Multi-process throughput test |
| bench/gen_type.mjs, type_cache.json | fontkit variable-outline cache, used by the demo |
| bench/probe_axes.html, probe_axes.mjs, probe_outlines.html, probe_fontkit.mjs, varfont_node.mjs | Font-axis probes; probe_fontkit.png shows the opsz effect |
| bench/demo_3.jpg, demo_24.jpg, demo_23_6.jpg, demo_24_09.jpg, demo_24_17.jpg, demo_20-24s_preview.mp4 | Rendered evidence (gitignored media) |
| roto/roto_probe.py | MediaPipe pose, face and segmentation plus OpenCV line-trace timing and JSON export |

Setup: `cd claudepop/craft/bench && npm install` (puppeteer-core, fontkit, opentype.js, tiny-sdf, spectral.js, simplex-noise). Fonts (gitignored) go in bench/fonts/ from https://raw.githubusercontent.com/google/fonts/main/ofl/ : robotoflex/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf -> RobotoFlex.ttf; anybody/Anybody[wdth,wght].ttf -> Anybody.ttf; bricolagegrotesque/BricolageGrotesque[opsz,wdth,wght].ttf -> BricolageGrotesque.ttf; instrumentserif/InstrumentSerif-Regular.ttf and InstrumentSerif-Italic.ttf; fraunces/Fraunces[SOFT,WONK,opsz,wght].ttf -> Fraunces.ttf (URL-encode the brackets as %5B %5D). MediaPipe models: the storage.googleapis.com URLs in section 6.

2. PERF [M]: p5.brush is the bottleneck. Watercolour fills cost about 0.31 s each on the CPU raster path and about 2.44 s each on the GPU (SwiftShader) raster path at 1080p; ink strokes cost about 10 ms each. The previous video drew 30-110 fills per frame and took 5-85 s per frame. Rule: bake p5.brush only, never draw it per frame.
3. PERF [M]: Canvas2D on the CPU raster path (--disable-accelerated-2d-canvas --disable-gpu-compositing) is fast at 1080p: paper multiply 4 ms, 2,000 strokes 22 ms, 300 tapered ink ribbons 19 ms, 40 cut-out sprites 35 ms, 10 lines of 240 px variable type 13 ms, full-frame blur 36 ms. A WebGL2 riso pass (3 inks, halftone, misregistration, paper tooth) takes 164 ms, or 110 ms for the shader alone. Encoding costs 43 ms (JPEG) or 129 ms (PNG).
4. PERF [M]: the test card (paper, 3-ink riso, torn cut-outs, boiling ink face, fontkit hero type, subtitle strip, sticker) renders at 0.46 s/frame in one Chromium and 0.22 s/frame effective with 4 parallel Chromiums. The full 3,760-frame film at 24 fps would take about 14 min at this complexity, leaving 5-10x headroom inside the 1-3 s/frame budget.
5. TYPE [M]: in Chromium canvas, wght is continuous (numeric weight in ctx.font, needs a weight range in @font-face). wdth is reachable only through ctx.fontStretch keywords (50-200%); a percentage in the ctx.font shorthand is rejected. Custom axes such as XTRA work only through static @font-face/FontFace variation descriptors (16 instances created in 86 ms). Chrome auto-sets opsz to the font size. For exact or animated axes, precompute outlines with fontkit and draw them as Path2D. opentype.js 2.0.0 rendered Roboto Flex variations wrongly.
6. LOOK: riso-printed paper stop-motion reads at phone and thumbnail size, where the previous pastel watercolour turned to mud. Use 3-4 spot inks (Fluorescent Pink #ff48b0, Blue #0078bf, Yellow #ffe800, plus black or Claude orange #d97757) overprinting multiplicatively, with misregistration, halftone screens of at least 8 px cells, static paper grain, torn cut-outs baked once, drawings on twos and camera and type on ones (Spider-Verse split).
7. DIRECTING: K-pop grammar to adopt: centre framing; formation morphs on 2-bar or 4-bar boundaries (top-down formations can spell glyphs); one colour or set block per section (Whiplash: two sets, limited palette, on-beat cut-ins); an upper-body point move on the hook (ILLIT Magnetic model), held in a wide shot for at least 2 bars; the hook shot returning at 23.871, 60.235, 96.598 and 125.689 s with escalation; an edit that accelerates across the song, with the bridge halving cut length every 2 bars (1.82 s, 0.91 s, 0.45 s, 0.23 s).
8. HOOK: frame 0 must be lyric-forward because X autoplays muted. Proposal: 'SPARKS' blind-embossed on paper over an extreme close-up of the eye; words print on their onsets (2.05, 2.36, 2.73 s); A, G and I print as three misregistered ink passes (3.65, 4.10, 4.33 s) that snap into perfect registration on 'I', a riso metaphor for AGI arriving.
9. TYPE TIERS: S subtitle (64-80 px, never below 56, torn strip, doubles as captions), M line (120-240 px), L hero word (400-900 px cap height, opposite the idol, brat-style vertical stretch), XL full-bleed. Choose the tier from lyric density in song.json: lines at or below 1.4 words/s get L or XL; lines at or above 2.8 words/s get S plus one popped keyword. The three 'please' lines (ChatGPT, Sydney, Gato) share one recurring K-pop fan-slogan-banner layout. The whole-bar stop at 138.4-140.2 s gets a single subtitle line on empty paper.
10. PLATFORM: X free accounts cap video uploads at 140 s and the song is 156.7 s, so the full video needs X Premium or a shorter cut (source: 2025-26 blogs, verify). For 9:16, render a native vertical layout pass rather than cropping (a crop keeps only 608 px of width). Keep full-frame flashes at or below 3 per second (WCAG 2.3.1): beat inserts are OK (2.2/s), 8th-note inserts are not (4.4/s).
11. PLATES [S/M]: fal documents Seedance 2.0 (not 2.5): reference-to-video up to 15 s at 480p or 720p, up to 3 audio references (15 s combined) that drive lip-sync, about $0.30/s. 8 bars at 132 BPM = 14.545 s, so one plate per 8-bar phrase. On CPU at 1080p, MediaPipe Tasks 1.0.1 pose takes 18-45 ms, multiclass segmentation 155-171 ms, and OpenCV Canny+contours 103-117 ms, under 0.4 s/frame in total. Proposed sync check: cross-correlate the jawOpen blendshape with the vocal envelope and accept at most 1 frame of lag. Pure-JS mode B: a puppet rig with a pose library and syllable-timed visemes from the song.json syllable onsets.

## Artifacts
- `/home/user/HENRYDENG/claudepop/craft/bench/paperkit.js`
- `/home/user/HENRYDENG/claudepop/craft/bench/bench.html`
- `/home/user/HENRYDENG/claudepop/craft/bench/run_bench.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/results.json`
- `/home/user/HENRYDENG/claudepop/craft/bench/brushbench.html`
- `/home/user/HENRYDENG/claudepop/craft/bench/run_brushbench.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo.html`
- `/home/user/HENRYDENG/claudepop/craft/bench/run_parallel.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/gen_type.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/type_cache.json`
- `/home/user/HENRYDENG/claudepop/craft/bench/probe_axes.html`
- `/home/user/HENRYDENG/claudepop/craft/bench/probe_axes.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/probe_outlines.html`
- `/home/user/HENRYDENG/claudepop/craft/bench/probe_fontkit.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/probe_fontkit.png`
- `/home/user/HENRYDENG/claudepop/craft/bench/varfont_node.mjs`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_3.jpg`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_24.jpg`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_23_6.jpg`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_24_09.jpg`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_24_17.jpg`
- `/home/user/HENRYDENG/claudepop/craft/bench/demo_20-24s_preview.mp4`
- `/home/user/HENRYDENG/claudepop/craft/bench/package.json`
- `/home/user/HENRYDENG/claudepop/craft/roto/roto_probe.py`

## Caveats
- REPORT.md was NOT written: the harness blocks subagents from writing report files. The full markdown is key_findings[0]; write it to /home/user/HENRYDENG/claudepop/craft/REPORT.md from the orchestrator.
- The session's WebSearch budget ran out (200/200) mid-research, and WebFetch was blocked for Wikipedia, MDN, Medium, x.com, hypebeast, envimedia, animationmagazine, creativebloq, motionographer and tylerxhobbs. Many claims rest on search-result snippets; items tagged [K] (WCAG 2.3.1, ITU-R BT.1359, Dylan cue cards, Apple Music Sing, K/DA, EbSynth, Tyler Hobbs details, opsz auto-sizing, Chrome readback demotion, fan slogan banners) are unverified background knowledge.
- No K-pop MV was watched frame by frame, so the cut-rhythm and ASL table is a proposal on our 132 BPM grid, not a measured shot log. The industry average-shot-length figure came from a vendor blog.
- The X 140 s free-tier limit and the '70-85% muted autoplay' figure come from 2025-26 blog summaries; confirm on the posting account.
- In the gpu2d benchmark column, the 2D numbers are partly contaminated by the canvas falling back to CPU after repeated readbacks. The p5.brush comparison (3.1 s vs 24.4 s for 10 fills) and the prior audit (about 16 s vs 125 s per frame) are the reliable evidence that the accelerated 2D path is about 8x slower.
- FaceLandmarker cost with a detected face was not measured: the sample images yielded no face. The pose timing used third-party sample photos (OpenCV and OpenPose test images), kept only in the scratchpad and not in the repo.
- 'Seedance 2.5' as named in the brief was not found; fal documents Seedance 2.0 (15 s, 720p max, audio reference for lip-sync). Re-check when fal access is available.
- The demo frames are a technique test card; the idol drawn there is a placeholder, not a character proposal.
- bench/node_modules, bench/fonts, and the jpg/png/mp4 outputs are gitignored. Setup commands and font URLs are in the report appendix. The demo preview mp4 contains a re-encoded 4 s excerpt of the song for local review only; it must not be committed or published.
