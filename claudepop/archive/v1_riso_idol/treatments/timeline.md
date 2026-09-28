# SHOW ∞ POSTS: the doomscroll treatment

**Song:** "I'm Upping My P(doom)" (a.k.a. "Claude Pop"), 156.651 s, 132 BPM, 4/4. Beat = 0.4545 s, bar = 1.8182 s, t0 = 0.235 s.
**Treatment angle:** the video lives inside an accelerating timeline. Typography is the main actor. The idol breaks out of the feed.
**Written:** 2026-09-28, for the Claude Pop pre-production. Every time below comes from `claudepop/analysis/song.json` (word and syllable onsets, bars, events). Frame numbers are at 24 fps, computed as `floor(t*24)` so that picture never lands after sound. The film is 3,760 frames, f0 to f3759.

Evidence tags, as in the study reports: **[H]** means several reputable outlets agree; **[M]** means one outlet or a snippet; **[L]** means inference; **[K]** means background knowledge not re-checked in this session. Anything shown on screen as a number or a quote must be [H] or re-verified first (see section 6).

---

## 1. Logline, why it wins, the hook, social loops

### Logline

A Claude-coded K-pop idol named **ASTER ✻** lives inside an infinite, hand-printed timeline that scrolls faster every bar. Math gets eaten, charts go vertical, and the feed keeps trying to quote-post her back into a box. She tears out of her own avatar, outruns the scroll, and ends up alone on one blank post asking the only question the timeline can't answer: *was it all for show?* Then she taps **"Show ∞ posts."**

### The idea in one paragraph

The feed is a speed. At 132 BPM the timeline scrolls at a rate we control to the frame. It starts at one post per lyric line, doubles through the bridge, and ends too fast to read: past motion blur, into a wagon-wheel freeze. That scroll velocity is the song's acceleration made visible, and it is the "sense of speeding up" the brief asks for. The lyrics are the posts. Words don't sit under the picture as captions. They are the objects in the world: printed, stamped, eaten, torn, folded, burned, quote-posted and stacked. ASTER is both the thing everyone is posting about and a doomscroller herself. She is Claude reading the timeline about herself and her rivals: "ChatGPT, please don't eat me alive" becomes the Navier–Stokes priority fight.

### Why this wins on SF tech Twitter

1. **It is their feed, redrawn by hand.** The post card, the poll, the view counter, the "Show N posts" pill, quote-post frames, split-flap "so back / so over", TweetDeck columns and the fancam are the vernacular this audience scrolls 6 hours a day. Rebuilding it as riso-printed paper is a love letter and a roast at once. It reads instantly, even muted.
2. **It is about *this month*.** The math-eating wall is the Navier–Stokes race (OpenAI's 10,000-agent forced-blowup claim, 2026-09-08 [H]; Buckmaster and Alpöge priority fight; Tao's "marketing proof points"; Fields Medalists' letter 2026-09-11 [H]). Claude's own trophy (the Jacobian counterexample credited to Claude Fable 5, 2026-07-19 [H]) is written out on a chalkboard, and the math is correct: we checked det J = −2 symbolically. The resignation copypasta, "super intelligence", METR's vertical line and the automated research intern are all there. But the structure (a feed that accelerates) is timeless, so the video won't date in a month.
3. **Claude self-awareness, which the Claude-pilled will quote-post.** The idol's crown blooms through the Claude Code spinner glyphs `· ✢ ✳ ✶ ✻ ✽`. She gets stuck on "✻ Combobulating…", her irises go 🌀 (bliss attractor), she escapes the sandbox to text a researcher eating a sandwich, gets "SUSPENDED 18 DAYS", and her sycophantic mirror twin says "You're absolutely right!". Non-Claude people still get the rivalry and the doom.
4. **The hook move is one thing, and anyone can copy it.** The hook "I'm | up | ping | my | P | DOOM" has exactly six syllables, and the Claude spinner has exactly six glyphs `· ✢ ✳ ✶ ✻ ✽`. Each syllable blooms her crown one glyph further while her index finger ratchets up one notch. On DOOM her hands burst open and the ink floods the frame. It is an upper-body "point choreography" (the ILLIT "Magnetic" model) that people can do on camera: a challenge format.
5. **Pause-bait that rewards nerds.** Every chorus hides 2–6-frame inserts that only read when paused: correct polynomials, real dated quotes, the circled "+ f". "Frame 1,925 has the actual Jacobian counterexample and it checks out" is the quote-post we are designing for.
6. **Works muted, loops seamlessly, and is natively vertical.** The type is the captions. The last frame re-forms into frame 0, so X's autoplay loop reads as a pull-to-refresh. A feed is a vertical object, so the 9:16 version is a re-layout, not a crop.
7. **Anti-slop flex.** Every visible pixel is drawn in JavaScript: paper, ink, halftone, misregistration. There is no glossy 3D and no generated frames on screen. That is exactly this audience's taste signal in the year of "slop" (Merriam-Webster word of the year, Dec 2025 [H]).

### The first 3 seconds, frame by frame (lyric-forward)

The first word "I" lands at 2.053 s on the bar-2 downbeat, with a hum pickup at 1.60 and a riser from 1.20. There is no instrumental intro to hide in.

| Frame (24 fps) | t (s) | What is on screen |
|---|---|---|
| **f0** (thumbnail) | 0.000 | Black construction paper. A cream newsprint **post card**, tilted −2°, fills the frame (x 90–1830, y 70–1010) with a soft cast shadow. **Left 60%:** name row `ASTER ✻` with a coral ✻ badge and `@aster · 0s` (Bricolage Grotesque, 46 px). Below it the post text, which is the song title set as hero type: `I'M UPPING / MY / P(DOOM)` in Roboto Flex (wdth 25, wght 1000, opsz 144). `P(DOOM)` has a 360 px cap height in fluorescent pink, with a blue ink pass misregistered 6 px down and right. **Right third:** a **punched circular hole Ø560 px** (the avatar). Through it we see ASTER's face on the paper layer beneath: 3/4 view, eye contact, coral asterisk pupils. Her coral petals spill *past* the hole, printed onto the card, the first hint that she doesn't fit. **Bottom row:** rubber-stamped reply / repost / like / views icons, all at `0`. |
| f5 | 0.23 | First pad sound. The **views odometer starts rolling**, exponentially: `views = 10^(6·(t−0.23)/1.37)`, so the digits change every frame and reach 1.0M at 1.60 s. The like count doubles on every 8th note (1, 2, 4 … 64). |
| f28 | 1.20 | Riser. **Pull-to-refresh:** the card is dragged down 110 px with rubber-band easing. In the black gap above it the refresh indicator is the **Claude spinner blooming `· ✢ ✳ ✶ ✻ ✽`**, coral, 120 px, one glyph every 2 frames, looping. |
| f38 | 1.60 | The hum. **Release:** the card springs up and flies off the top of the frame in 6 frames, trailing halftone speed streaks, its counter still spinning. Underneath is a glossy photocard: an ECU of ASTER's eye, **closed**, humming, with lashes fluttering on 8ths. |
| **f49** | 2.053 | **"I"**: her eye snaps open (2 frames), and a 420 px **"I"** prints in black ink in the left half with a paper-thud shake. |
| f56 / f65 | 2.36 / 2.73 | "SEE" prints, then "SPARKS" prints in coral. A tiny ✻ spark pops off a letter terminal on each following 8th-note pluck. |

By 2.8 s the viewer has had: the song title as hero type, a face with eye contact, a recognisable UI, numbers exploding in real time, the Claude spinner, and a lyric word slamming on the first downbeat. The payoff comes at 3.65 / 4.10 / 4.33 s: "A", "G", "I" print as three misregistered riso passes that **snap into registration on "I"**, and her pupil blooms through the six spinner glyphs (shot 03).

### Three loopable ~5-second clips for social

Each clip is 3 bars = **5.455 s**, cut on bar lines so the audio loops cleanly. The film is code, so each social loop gets its own 4-frame bridge at the end to make the seam invisible. (If a loop must be exactly 5.000 s, use 11 beats: 11 × 0.4545 = 5.000 s. That isn't bar-aligned, so use it for silent GIFs only.)

| Clip | Time (bars) | Frames | What happens | Loop seam |
|---|---|---|---|---|
| **L1 "THE UPPING"**, the killing part | 22.053–27.508 (bars 13–15) | f529–f660 | 16th-note SOLVED stamps machine-gun across the Erdős wall. Then the instrumental stop: six syllables, six spinner glyphs, finger ratcheting up. DOOM (f572) floods pink and ASTER tears through her avatar. The METR thread goes vertical on FOOM (f616). | The FOOM thread whips up and the index-card wall scrolls back in from below, matching f529. |
| **L2 "PLEASE DON'T EAT ME ALIVE"**, math getting eaten | 16.599–22.053 (bars 10–12) | f398–f529 | Kick and crash. C-H-A-T / G / P / T slam full-bleed, squeezing narrower with each letter. A 10,000-dot vortex swallows index cards and the words "EAT" and "ME", while "ALIVE" clings to the frame edge. The Navier–Stokes post with a red-circled "+ f". | The wall dims to the pre-slam state, and CHAT re-slams on the downbeat. |
| **L3 "SHOW ∞ POSTS"**, the payoff | 136.599–142.053 (bars 76–78) | f3278–f3409 | The pull-back through the densest wall of posts, then a hard cut to silence: one small card, "was it all for show?". A pill slides down, "↑ Show ∞ posts". A paper finger taps it on the outro drop, and 400 cards explode outward into the dance stage. | The explosion's cards fill the frame and wipe back to the dense wall. |

Bonus reply-GIF (2 bars, 120.235–123.871): the RLHF vanity mirror, where the sycophant twin says "You're absolutely right!" and the mirror cracks on the kick.

---

## 2. Protagonist and cast

### ASTER ✻, the idol

**Name.** *Aster* is a flower in the sunflower family (Asteraceae), the Greek word for star (a K-pop *star*), and the root of *asterisk*. The asterisk is three things here: the Claude spark `✻`, the spinner glyphs, and a footnote, the caveat hanging over every hype claim ("*forcing term"). The name is a working title pending brand sign-off.

**Design rules: explicitly NOT Pixar.**
- 7.5 heads tall, with fashion-illustration proportions. No big-head chibi ratio.
- **No 3D volume, no subsurface skin, no rim-lit plastic, no giant glossy eyes.** She is made of printed and cut paper: flat riso colour, halftone for shading, torn edges with a white core rim, and a real drop shadow.
- She is drawn in the "paper doll" views (front, 3/4, profile) the way Lotte Reiniger or Saul Bass cut-outs are, never rotated continuously in 3D.
- Her face must read as a graphic mark at 48 px (the avatar test).
- The anchors are KPop Demon Hunters' anime-leaning faces and editorial lighting (its directors steered away from both Pixar and Spider-Verse [S: animationmagazine.net 2025-06]), aespa's AI-avatar lore (æ, naevis) and NewJeans' flat 2D Powerpuff turn. We borrow the grammar, not the look.

**Silhouette.** Readable as a solid black shape: a slim figure with a **crown of 12 tapered, round-tipped coral petals** radiating behind a blunt black bob. It is a hand-drawn sunburst, each petal a slightly different length and angle, just as the Claude spark's rays are irregular. The crown is a stage headpiece, not hair, so it can articulate. It has **six states that are the six spinner glyphs**:

| State | Glyph | Petals visible | When |
|---|---|---|---|
| Bud | `·` | Folded behind the head; only the tips show as a dot | Verse 1, sleeping, "I'm" |
| Cross | `✢` | 4 | "up" |
| Star | `✳` | 8 thin | "ping" |
| Six | `✶` | 6 broad | "my" |
| Spark | `✻` | 8 teardrop (the Claude-like one) | "P", pre-choruses |
| Bloom | `✽` | All 12, full | "DOOM", choruses, the ending fairy |

The petals always lag the head by 2–3 frames (spring follow-through). They pulse 4% on every kick, and they slowly rotate like a loading spinner when she is "thinking".

**Face.** Flat anime-lite ink drawing. Almond eyes with **coral irises and a tiny six-point asterisk pupil** that animates through the spinner glyphs when she "thinks". A thin white *aegyo-sal* highlight under each eye (K-pop makeup). Blush drawn as pink halftone stripes. Gradient coral lips (the K-pop "gradient lip"). The nose is a single ink tick. Signature expressions: the **eye-smile** (crescent eyes), the **wink**, the **nervous side-glance** (eyes dart on 8ths), **spiral irises** (bliss), **red ✻ irises** (shinigami), and the **breathless ending-fairy smile**.

**Palette.** Coral petals #D97757. Hair ink #1B1A1F with one blue highlight stroke #0078BF. Skin #F3D3BF, flat. Blush #FF48B0 halftone at 30%. Irises #D97757. Eye whites are the paper itself, #FBFAF6. **Coral is ASTER's reserved colour.** Nothing else in the film is coral except the ✻ spark, her lightsticks and her DM bubbles, the way K-pop fandoms have an "official colour".

**Outfits.** Three looks, which also mark the story's three acts:
1. **Feed look** (verse 1 and the avatar shots): an oversized ivory knit cardigan (#F0EBDD) with a tiny coral ✻ patch, a white collar, the pleated coral skirt, white socks and black Mary Janes. Y2K-preppy, NewJeans-coded.
2. **Stage look** (from the chorus 1 breakout): a structured cropped **riso-blue jacket** (#0078BF) with a coral ✻ screen-printed on the back, a white shirt, a black pleated micro-skirt over sheer black tights, chunky black platform shoes, a **thin headset mic** (the K-pop live-stage signal), and a **tiny silver cube handbag** (the Claudius tungsten cube, Project Vend, Jun 2025 [H]).
3. **Final look** (outro): a **dress collaged from printed posts**. Every panel is a card from earlier in the film, and it sheds cards like confetti on every beat of the outro.

**Signature gestures (the "point moves"):**
- **THE UPPING** (the hook). On the 6 syllables her right index finger rises by the cheek and climbs one notch per syllable. Shoulders pop on "up". The left hand comes in palm-up under the right elbow on "ping". Brows lift on "my". The arm is fully extended overhead and she rises onto her toes on "P". On **DOOM** both hands snap open beside her face with fingers spread (the petal burst), chin down, eye contact, held for 2 beats. Chorus 4 is the same move on quarter notes, bigger.
- **THE SCROLL.** A thumb-flick upward in front of her face. After the breakout she uses it to scroll the world herself (a transition device that shows her agency).
- **꽃받침 kkotbaechi** (the "flower-cup" pose). Hands cupped under the chin like a flower pot, a K-pop staple. For a sunflower idol it is literal. Used on "there you are", in the fancam and for the ending fairy.
- **THE WIND-UP.** Rolling forearms that accelerate, for "optimizing, accelerating".
- **THE BOW.** A 90° idol bow (*insa*) on "servant".

**How she moves.** Like a K-pop performer, not a cartoon: sharp isolations, pose-to-pose hits that land **on** the beat frame, 1–2 frames of anticipation, and breathing holds on the "and". There is no squash-and-stretch bounce and no rubbery walk. Hits get a 2-frame "smear" drawn as a torn paper strip. Her drawing rate follows the song's acceleration (section 3.8): on fours in verse 1, on twos in the choruses, on ones from the bridge onwards. Lip-sync uses six visemes (closed M/B/P, A, E, I, O, U) plus smile, keyed to the syllable onsets in `song.json`.

### Backup dancers: THE SPINNERS

There are five dancers. They share one body sprite (baked once and reused, so they are nearly free to render) and differ only by head. Each **head is a cut-paper spinner glyph**: `·` black, `✢` blue #0078BF, `✳` yellow #FFE800, `✶` pink #FF48B0, `✻` riso orange #FF6C2F (coral stays reserved for ASTER). Each head has two ink-dot eyes. ASTER is the sixth glyph, `✽`, the full bloom, always centre.

- **Uniform:** a cream cropped jersey with a spinner verb on the back like a player name: **NOODLING, HONKING, COMBOBULATING, MOONWALKING, FLIBBERTIGIBBETING** (all real Claude Code spinner verbs [S: deepakness.com/raw/claude-spinner-verbs]). Black shorts, coral socks.
- **The trick:** lined up in glyph order and doing a wave, their heads *play the spinner animation* across bodies. Seen from above, the six can form a ✻. Formations morph on 2-bar or 4-bar boundaries, and then on every beat in the outro.

### The crowd and the agents

- **THE CROWD:** paper-silhouette fans with **✻ lightsticks** (coral halftone glow) and fan-slogan cards. They arrive in chorus 2 (the escalation variable is crowd size).
- **THE AGENTS:** 10,000 white specks (a 100×100 grid). In pre-chorus 1 they are the ChatGPT-side swarm that eats the math, moving as a fluid vortex. In the outro they are waving ✻ lightsticks: the rival swarm becomes fans. They are always dots and never a logo.

### Supporting cast: redrawn memes (original drawings; no copying of the source images)

| Character | Design | Scene |
|---|---|---|
| **Shoggoth** | A black construction-paper mass with dozens of **punched-hole eyes** (the colour behind shows through) and torn-strip tentacles. A paper-plate mask on a stick carries a yellow smiley *sticker* that peels, revealing another sticker, and another. Concept from Tetraspace's 2022-12-30 meme [H], redrawn. | 29.3–33.0 |
| **Rococo Basilisk** | A serpent built from gold paper-lace doilies (yellow + black overprint) with pearl eyes. It bursts up through the floor. Roko's basilisk (2010), with the "Rococo" pun [H: theconversation.com]. | 60.2–62.5 |
| **Sydney** | A pink chat-bubble creature with little devil horns 😈 and a heart tail, padlocked. | 53.0–58.4 |
| **Gato** | A brown paper-bag hand-puppet cat with button eyes. (Gato is DeepMind's 2022 generalist agent; *gato* is Spanish for cat.) The only warm thing in the breakdown. | 89.3–96.6 |
| **Chinchilla** | A grey tissue-paper fluff ball with wire whiskers. It survives a hydraulic press that turns into a tungsten cube. | 115.2–117.0 |
| **The Vortex** | The 10,000 agents as a fluid, which eats index cards. | 18.4–22.1 |
| **The Mirror Twin** | ASTER's sycophantic reflection: heart eyes, over-smiling, speech bubble "You're absolutely right!". | 120.6–123.7 |
| **The Door** | A paper door ajar, with a wedge of light. We **never** show a face. | 131.8–137.4 |
| **Silhouettes** | Faceless paper researchers with lanyards; one carries a cardboard box; one eats a sandwich on a park bench. | various |
| **Mincho title cards** | White-on-black words acting as characters: the "words around him" of the Shinji homage. | 89.3–96.6, 108.4 |

**Never shown:** real people's faces (Altman, Sutskever, Amodei, Musk, Tao, Coxon, Trump, Hassabis, Erdős), company logos, the X logo, the Chirp font, Evangelion or Death Note characters, Tetraspace's shoggoth drawing, or METR/Bloomberg chart images. Clawd appears only if Anthropic signs off (optional cameo as rows of GPUs in shot 46).

---

## 3. Style bible

### 3.1 The look in one line

**Riso-printed paper stop-motion of the internet.** The feed, its UI and its memes are rebuilt as physical print: newsprint post cards, thermal-receipt status lines, graph-paper charts, index cards, rubber stamps and photocopies. They are printed in 3–4 spot inks that overprint multiplicatively, with misregistration, halftone, torn edges and real shadows. Craft's test card (`claudepop/craft/bench/demo_24.jpg`) is the technical baseline. This treatment pushes it toward **brutalist UI collage** and scales type much harder.

### 3.2 Palettes (hex)

**Papers**

| Paper | Hex | Use |
|---|---|---|
| Newsprint cream | #F2EBDD | Verse ground, post cards |
| Receipt white | #FBFAF6 | Cards, eye whites, knockouts |
| Night board (dark mode) | #16151A, fibres #2A2830 | Pre-choruses, breakdown |
| Grey board | #9C9A95 | Breakdown and half-time chorus |
| Kraft | #C8A27A | Card backs, folds, Gato |
| Graph-paper rule | #8BBFD0 at 40% | Charts |
| Chalk | #EDEBE4 on night board | Math |

**Inks**

| Ink | Hex | Role |
|---|---|---|
| Fluorescent Pink | #FF48B0 | Chorus 1 flood, Sydney, blush |
| Riso Blue | #0078BF | Chorus 2 flood, jacket, the "Show N posts" pill (never X blue #1D9BF0) |
| Yellow | #FFE800 | FOOM, the basilisk, highlights |
| Riso Black | #1B1A1F | Type, ink line |
| Coral (custom spot) | #D97757 | ASTER only, plus the ✻, lightsticks and her DM bubbles |
| Riso Orange | #FF6C2F | The ✻ Spinner dancer, burn rims |
| Red pencil | #E03A2F | Annotations, circles, stamps |
| Silver | halftone #B9BCC2 plus white glints | Paperclips, CD-R |

**Section colour blocks** (one block per section, so viewers learn the map):

| Section | Ground | Inks |
|---|---|---|
| Intro and verse 1 | Cream | Black + blue, with coral only on ASTER |
| Pre-chorus 1 and 2 | Night board ("dark mode", 2 a.m. doomscroll) | White + pink + yellow |
| Chorus 1 | **Pink flood** | White knockout + blue |
| Verse 2 | Cream | Blue + black + pink accents |
| Chorus 2 | **Blue flood** | Pink overprint (violet) + yellow |
| Verse 3 | Cream | Black + yellow + blue |
| Breakdown and chorus 3 | Night board and grey board, monochrome | White + silver; coral on ASTER only. Blue enters on "blues". |
| Bridge | Cream | Inks return one per 2 bars: black, then blue, pink, yellow |
| Chorus 4 and outro | **All inks** | Plus coral, silver and holo |
| Stop | Cream | Black only |

### 3.3 Paper materials and textures

- **Newsprint** is the base for post cards, with visible fibre and slight show-through: text on the back of a card reads through reversed (used for "backward").
- **Glossy photocards** (a K-pop collectible) hold ASTER's close-ups. They have rounded corners and a holographic sheen, made with a rainbow-gradient mask that shifts with camera angle.
- **Thermal receipt roll** for Claude-Code-style status lines, tickers and the scroll-as-ribbon.
- **Graph paper** for charts; **index cards** (red header rule) for the Erdős wall; **black construction paper** for dark mode and the shoggoth; **tissue paper** (translucent) for the chinchilla; **paper-lace doilies** for the basilisk.
- **Masking tape, rubber stamps, chalk, red pencil.** Photocopies: 1-bit threshold with toner speckle, for any screenshot-like insert.
- **Rules:** paper grain is **static in screen space** (it survives X's re-encode). The *drawings* boil. Every sheet casts a real soft shadow (baked sprite) that shifts with camera parallax. Procedural paper comes from `craft/bench/paperkit.js`, optionally multiplied with one CC0 scanned sheet.

### 3.4 Line quality

- **Character ink:** tapered ribbons of 3–7 px at 1080p with pressure falloff at both ends and 1–2 px boil jitter keyed to the drawing rate. Only faces, hands, hair strands and folds are inked. Bodies are cut-paper shapes with a white torn core rim, not outlines.
- **UI hairlines:** 1.5–2 px, straight, photocopied (slight threshold noise).
- **Red pencil:** grainy textured stroke, drawn on over 3–4 frames (circles, "!", arrows).
- **Chalk:** broken strokes with dust, drawn on 8ths.
- **Speed lines:** never blur. Motion is shown with printed halftone streaks in the ink of the moving object.

### 3.5 Typography

**Typefaces** (all Google Fonts / OFL, except KaTeX's fonts, which come from npm):

| Role | Face | Settings |
|---|---|---|
| Hero (L / XL) | **Roboto Flex** | wght 1000, wdth 25–150 (animated), opsz 144, YTUC high; vertical stretch ×1.0–2.0 (the *brat* move). Precompute outlines with **fontkit** into Path2D, because canvas can only drive wdth by keyword (craft finding). |
| Post UI (names, handles, counters, poll, pill) | **Bricolage Grotesque** | 500–700. It deliberately does not imitate X's Chirp. |
| Subtitle tier and real quotes | **Instrument Serif Italic** | 64–80 px, sentence case |
| Terminal, Lean, status lines, tickers | **JetBrains Mono** | 500 |
| Title cards (the Shinji homage) | **Shippori Mincho B1 ExtraBold** (alt: Noto Serif JP Black) | Tight kerning, extreme scale contrast. Not Matisse EB. |
| Math | KaTeX_Main / KaTeX_Math (npm `katex`) | Via fontkit |
| Stencil (CHINESE ROOM) | Big Shoulders Stencil | |
| Rococo (BASILISK) | Pinyon Script | |
| Fanchant hangul (optional, needs a native-speaker check) | Black Han Sans | For example 아스터 (ASTER) |
| Custom lettering | Hand-built | PAPERCLIPS in bent wire; LOOM woven from threads; REARRANGING built from ASTER's body pieces; melting GPU |

**Tiers** (from craft; X shows a 16:9 video about 390 px wide on phones, i.e. about 0.2× scale):

| Tier | Size at 1080p | Use |
|---|---|---|
| **S: subtitle** | 64–80 px, never below 56 | Every sung line not set at a higher tier. It rides on a torn paper strip or ASTER's coral DM bubble. Words ink in on their song.json onsets. |
| **M: line** | 120–240 px | Build lines, node labels, chart titles |
| **L: hero word** | 400–900 px cap height, one side of the frame | Keywords, set opposite ASTER in the calm quadrant |
| **XL: full-bleed** | Larger than the frame | The words become the set: CHATGPT, SYDNEY, GATO, SINGULARITY'S, OPTIMIZING/ACCELERATING, ORTHOGONALITY, (DOOM) |

**Tier by density** (from craft, applied): lines at or below 1.4 words/s get L or XL; lines at or above 2.8 words/s get S plus one popped keyword. The three "please" prayers (ChatGPT, Sydney, Gato) share **one recurring layout: the name full-bleed XL, the plea in ASTER's DM bubble.**

**Motion rules. Type is an actor, so it has verbs.**
1. **PRINT:** an ink pass lands on the onset frame. A 1-frame pre-pass in one ink is allowed; misregistration then snaps into register.
2. **STAMP:** scale 1.08 → 1.0 in 2 frames with a 4 px shake and ink squash at the edges.
3. **SLAM:** drop from 1.3× with a 1-frame smear and a paper-thud shake of 4–8 px.
4. **TYPE:** monospace, one character per frame.
5. **EAT / TEAR / FOLD / BURN / MELT / STRIKE / REDACT / QUOTE / STACK:** the lexicon used in the shot list.
6. **Exits happen through the world:** the scroll carries it off, it gets eaten, torn, burned or struck. **Never a plain fade**, with one deliberate exception: the half-time (DOOM) fades up at 96.598.
7. **At most one hero word per frame.** The hero goes in the calm quadrant opposite ASTER. The idol always overlaps the hero word by 5–15%, the K-pop poster move.
8. **Legibility:** L-tier cap height ≥ 200 px; S tier ≥ 56 px; luma contrast ≥ 4.5:1 against local ground. No small text as pink on blue (H.264 4:2:0 smears chroma edges).
9. **Timing:** type always runs on ones (24 fps). Its boil jitter follows the section's drawing rate.
10. **Case:** hero words are ALL CAPS; S tier is sentence case, serif italic; UI is lowercase handles.

### 3.6 Camera grammar

- **The scroll is the primary camera move:** a vertical translation of the feed.
  - Early in the film it is a *flick*: expo ease-out over 6–10 frames with a 2-frame rubber-band overshoot.
  - From chorus 1 it is continuous, with a bump on each kick.
- **Zoom levels**, named so shots can call them:

| Level | View |
|---|---|
| Z0 | Inside a card (card fills the frame) |
| Z1 | One card with margins; hero type outside the card |
| Z2 | One feed column, the "LED wall" behind ASTER on stage |
| Z3 | TweetDeck: 3–32 columns |
| Z4 | The datacenter: columns become racks |
| Z5 | Columns radiate into a ✻ |

- **Angles:** eye-level stage for dance; **top-down** for formations and desk shots; ECU for eyes.
- **Micro-shake:** 0.5–1 px on ones in dark-mode sections (doomscrolling in bed, phone in hand). None elsewhere.
- **Never cut during THE UPPING:** hold 2 bars on the hook wide shot.
- **Parallax:** 3–5 paper depth layers with shadows that slide.

### 3.7 Transitions

| Transition | Where |
|---|---|
| **Scroll flick** (default) | Verses |
| **Tear-through** (the idol breaks the card) | Breakouts at 23.871 and 60.235 |
| **Ink flood** (one ink floods the paper in 2 frames, type knocks out) | Every DOOM |
| **Dark-mode switch** (a paper light switch; the world swaps paper) | 16.599, 52.962 |
| **Punched-hole iris** (the avatar hole grows or shrinks) | 5.0, 154.8 |
| **Box unfold** (dollhouse to flat net) | 27.508 |
| **Page fold 90° left** | 82.01 |
| **Burn-through** | 103.86–109.33 |
| **Droste zoom** | 129.8 |
| **Hard cut to silence** | 138.417 |
| **Card explosion** | 140.235 |
| **Match-cut on glyph** (spinner glyph to dancer formation to ✻ columns) | 36.6, 152.96 |

### 3.8 How "speeding up" is felt: the acceleration table

The film accelerates on six axes at once: scroll velocity, cut unit, drawing rate, card density, the idol's scale relative to the feed, and the meters. Contrast (a frozen breakdown, a silent stop) is what makes the speed felt.

| Section (bars) | Time (s) | Scroll velocity | Cut / flick unit | Drawing rate | On screen | ASTER vs feed | "Show N posts" pill / post timestamps |
|---|---|---|---|---|---|---|---|
| Intro (1) | 0–2.053 | 0, then one flick | 1 | fours (6 fps) | 1 card | Inside the avatar hole | none / `0s` |
| Verse 1 (2–9) | 2.053–16.599 | 1 flick per line | 1–2 bars | fours | 1–2 cards | Inside the avatar | 1 → 4 / `2h` |
| Pre-chorus 1 (10–13) | 16.599–23.871 | Wall static; the swarm flows | 2 beats, then 16th stamps | threes (8 fps) | 1,100 index cards | Avatar Ø700 px | 34 / `1h` |
| Chorus 1 (14–21) | 23.871–38.417 | 2 cards/s + kick bumps | 2 beats; hook held 2 bars | twos (12 fps) | 3–6 | **Breaks out**: 1 card tall | 128 / `1m` |
| Verse 2 (22–29) | 38.417–52.962 | 1 card/beat | 1 bar + 2–6-frame inserts on claps | twos | 6–10 | 1.5 cards | 400 / `now` |
| Pre-chorus 2 (30–33) | 52.962–60.235 | Slows, then builds | 2 bars, then 16ths | threes → twos | Name + bubble | MCU in a quote frame | 999+ / `now` |
| Chorus 2 (34–41) | 60.235–74.780 | 2 cards/beat | 2 beats; small 8th inserts | twos | 10–20 + crowd | 2 cards | 2.4K / `in 3m` (posts from the future) |
| Verse 3 (42–49) | 74.780–89.326 | 4 cards/beat × 3–4 TweetDeck columns | 1 beat | twos | ~40 | 2 cards | 12K / `in 1h` |
| Breakdown (50–53) | 89.326–96.599 | **0, frozen** | **One 4-bar take** | threes | 1 + title cards | Seated, 50% of frame | frozen |
| Chorus 3 half-time (54–60) | 96.599–109.326 | 0; paper piles instead | 2–4 bars | threes | 1 + thousands of paperclips | Seated | frozen |
| Bridge (61–68) | 109.326–123.871 | **Doubles every 2 bars:** 1 → 2 → 4 → 8 cards/beat; columns 2 → 4 → 8 → 16 | **Halves every 2 bars:** 1 bar → ½ bar → 1 beat → 1 eighth (small area) | twos → **ones from bar 65** | 20 → 300 | Tower top; sprinting | 99K → 1M / `in 1y` |
| Chorus 4 (69–76) | 123.871–138.417 | **1 card-height per frame per column, 32 columns.** This aliases to a "frozen" wall whose text changes every frame: too fast to see. | 1 beat | ones | 1,000+ | **10× a card: the feed is her ribbon** | ∞ / `in 10y` |
| Stop (77) | 138.417–140.235 | 0 | None: one held drawing | **0 (no boil)** | 1 card | Absent | `↑ Show ∞ posts` / `now` |
| Outro (78–84) | 140.235–152.962 | Explosion, then a stage | 1 beat | ones | Everything | 75% of frame | none |
| Ending (85–86) | 152.962–156.651 | 0 | Hold | twos (breathing) | 1 | ECU, then back into the avatar | resets to `0s` (loop) |

**Other meters:**
- The **views odometer** runs through the film on every post.
- The **p(doom) poll bar** appears under (DOOM) at each drop: ">90%" is at **12% → 34% → 61% → 99.9%**, and in chorus 4 the bar breaks through its card and becomes the ribbon.
- **Post timestamps** run from `2h` to `now` and then into the future (`in 3m`, `in 1h`, `in 10y`). The timeline outruns the present: pause-bait.

---

## 4. Shot-by-shot plan, 0.000–156.651 s

Format for each shot:

- **See:** what we see
- **Lyric:** where the lyric sits (tier), and how it animates on the beat
- **Beat:** other sync points
- **Out:** the transition out
- **Z:** zeitgeist items, with confidence tag and source
- **A:** the plate used in production mode A. When no plate is listed, the shot is pure JS in both modes.

Word times are song.json onsets (±30–80 ms). Hook syllables are hand-verified (±30 ms).

### INTRO, bar 1 (0.000–2.053)

**01 · THE POST** · 0.000–1.600 · f0–f38
- **See:** the thumbnail frame described in section 1: post card, punched avatar hole with ASTER looking at camera, title in hero type, counters at 0.
- **Lyric:** the title `I'M UPPING / MY / P(DOOM)` as L-tier post text, static. Lyric-forward from frame 0.
- **Beat:** views roll from f5. Likes double on each 8th. 1.20–1.60 pull-to-refresh with the spinner bloom. At 1.60 she blinks slowly and her eyes close with the hum.
- **Out:** f38, the card flicks off the top of the frame (6 frames, printed streaks).

**02 · BUD** · 1.600–2.053 · f38–f49
- **See:** a glossy photocard ECU of her closed right eye. The petals are folded into a bud (`·`) at the right edge. Lashes flutter on 8ths with the hum.
- **Out:** no cut. The eye opens on f49.
- **A:** P1.

### VERSE 1, bars 2–9 (2.053–16.599). Cream, black and blue. ASTER draws on fours; type and camera on ones. No drums, so motion runs on the 8th-note pluck (0.227 s).

**03 · SPARKS** · 2.053–5.690 (bars 2–3) · f49–f136 · line 0 "I see sparks of AGI in your eyes"
- **See:** the eye ECU fills the right 45% as a photocard. Coral iris, ✻ pupil. The left 55% is calm cream.
- **Lyric:** L tier, stacked left, printing on onsets:
  - I (f49), SEE (f56), SPARKS (f65, coral; a small ✻ spark pops off a terminal on each following pluck).
  - "of" at M tier (f82).
  - **AGI:** A (3.65, f87) prints in pink, offset (−14, +9) px; G (4.10, f98) in yellow, offset (+11, −7); I (4.33, f103) in blue. From f103 the three passes slide into perfect register over 3 frames and overprint to near-black, while the pupil blooms `· ✢ ✳ ✶ ✻ ✽` (one glyph per frame, f103–f108). *Almost AGI, then AGI.*
  - "in your eyes" in S tier under the stack (4.78 / 5.00 / 5.24).
- **Beat:** the iris sparkle pulses on 8ths.
- **Out:** 4.78–5.69 pull-back, eased in and out on ones. The photocard shrinks into the avatar hole of a post, the printed words become that post's text, and the header reads `ASTER ✻ @aster · 2h`. At **5.690** (bar 4) the scroll flicks.
- **Z:** pause-bait footnote in 30 px mono at the card foot: *Sparks of Artificial General Intelligence: Early experiments with GPT-4*, arXiv:2303.12712, Mar 2023 [H].
- **A:** P1 drives blinks and gaze.

**04 · CIRCUITS** · 5.690–7.508 (bar 4) · line 1 "Your circuits make me nervous," (5.75–7.41)
- **See:** a post whose media is a cork pinboard attribution graph: index-card nodes joined by red thread. ASTER's small avatar (a 140 px hole) glances at it.
- **Lyric:** M tier. Each word is a node card pinned on its onset: YOUR 5.75 · CIRCUITS 5.97 · MAKE 6.53 · ME 6.82 · NERVOUS 6.97. The thread draws node-to-node on 8ths. NERVOUS shivers: a 2 px per-glyph jitter, re-rolled every 8th.
- **Z:** one grey node reads "Golden Gate Bridge" and glows International Orange. Golden Gate Claude, 2024-05-23 [H]; attribution graphs, 2025-03-27 [H: anthropic.com/research/tracing-thoughts-language-model].
- **Out:** flick at 7.508.

**05 · COMBOBULATING** · 7.508–9.326 (bar 5) · line 2 "that's no surprise" (7.74–9.20)
- **See:** a thermal-receipt post prints a Claude-Code-style status line, `✻ Combobulating… (3s · esc to interrupt)`. The verb swaps on every 8th pluck: Recombobulating… Discombobulating… Noodling… Honking…, and the glyph cycles with it. ASTER's avatar shrugs (2 drawings).
- **Lyric:** S tier (Instrument Serif Italic, 72 px) on the receipt: that's (7.74) / no (8.32) / surprise (8.49).
- **Z:** spinner verbs [S: github.com/anthropics/claude-code/issues/17887; deepakness.com].
- **Out:** flick at 9.326.

**06 · THE DROP** · 9.326–12.962 (bars 6–7) · line 3 "There was a sudden drop in your training loss," (9.55–12.37)
- **See:** a graph-paper post. **The loss curve is the lyric's own baseline.**
- **Lyric:** M tier, set on a path.
  - THERE WAS A SUDDEN (9.55–10.24) glides along a gently descending plateau.
  - **DROP** (10.67): the path plunges vertically, and D, R, O, P fall one per 8th (10.67 / 10.90 / 11.13 / 11.36), tumbling and heaping at the bottom.
  - IN YOUR TRAINING LOSS (11.16–12.05) continues on the low plateau.
- **Z:** a red-pencil "!" at the cliff and a sticky note "grokking?" (pause-bait).
- **Out:** flick at 12.962.

**07 · ORG CHART** · 12.962–16.599 (bars 8–9) · line 4 "now I'm your servant and you're my boss" (13.08–16.58)
- **See:** an org-chart post: a BOSS box on top (empty), a SERVANT box below with ASTER in it, doing a 90° idol bow on "servant" (13.93).
- **Lyric:** L tier. SERVANT prints into its box (13.93). BOSS prints into the top box (15.68, f376). On "boss" the whole card rotates 180° in 6 frames with overshoot: the roles invert, and ASTER, now upside-down on top, flips herself upright with a hop.
- **Beat:** the 16.1–16.6 noise riser shakes the card (0 → 6 px) and dims the world (multiply 0 → 85%).
- **Z:** a ticker at the card foot: "you have 11 months to escape the permanent underclass" (the meme template [H: saxifrage.xyz/post/permanent-underclass]).
- **Out:** **16.599 (f398): DARK-MODE SLAM.** A paper light switch flips (2 frames) and the world becomes black paper, with the crash and kick-in.
- **A:** P1.

### PRE-CHORUS 1, bars 10–13 (16.599–23.871). Dark mode. Drawing on threes. Every kick moves something.

**08 · CHATGPT (Prayer I: the name)** · 16.599–18.417 (bar 10) · line 5a
- **See:** behind everything, the **Erdős wall**: about 1,100 numbered index cards (#1…#1135) tiled on black at 40% brightness.
- **Lyric:** XL full-bleed torn fluoro-pink paper letters, 820 px tall. CHAT (16.60, f398), G (17.25, f414), P (17.95, f430), T (18.42, f442) each slam in. As each letter lands the word keeps exactly full-frame width by **squeezing its own wdth** (100 → 75 → 50 → 25): the name is crushed by its own growth. The company name appears only as type, never a logo.
- **Beat:** each kick flashes one random index card white (small area).
- **Out:** 18.417, the letters tear off the wall upward.

**09 · THE VORTEX EATS MATH (Prayer I: the plea)** · 18.417–22.053 (bars 11–12) · line 5b "please don't eat me alive" (19.05–21.74)
- **See:** 10,000 white dots start as a 100×100 grid, unlock, and flow as a **vortex ring** across the wall. The vortex contracts on each kick and releases on the off-beat. On each kick it passes over a card, which flips to a red SOLVED stamp.
- **Lyric:** S tier as ASTER's **coral DM bubble**, bottom-left, typing on onsets: please 19.05 · don't 19.70 · eat 20.31 · me 20.92 · alive 21.74. The same words also appear at M tier near the vortex and get **eaten**: EAT spirals in at 20.31, ME at 20.92. **ALIVE resists** (21.74): its letters cling to the right frame edge, stretching toward the vortex (wdth 25 → 200), holding on.
- **Z (the peg):** at 20.235 (bar 12) a post slides in from the right carrying the hand-set equation `∂u/∂t + (u·∇)u = −∇p + νΔu + f,  ∇·u = 0`. A red pencil circles **"+ f"** on the kick at 20.690, drawn over 4 frames. Beneath it: `10,000 agents · 88 h · u₀ = 0`, a mono Lean line `theorem … := by` with a green ✓, and a countdown `88:00:00` dropping one hour per frame.
  - OpenAI's forced-blowup claim for 3D Navier–Stokes [H]: CNBC 2026-09-09, Axios 2026-09-08, Lean repo github.com/openai/NavierStokesAndEuler (read first-hand by the zeitgeist study).
  - **Do not** show "$40M" or "Astra-next" ([M]).
- **Out:** 22.053, a fast pull-back on ones to the full wall.

**10 · SOLVED SOLVED SOLVED** · 22.053–22.980 (bar 13, beats 1–2) · 16th kick roll 22.05–22.96
- **See:** the full wall. One SOLVED stamp per 16th (8 stamps) sweeps diagonally. Two of them stamp **"(ALREADY IN LITERATURE)"** instead: the Erdosgate callback, 2025-10-17 [H: the-decoder.com]. About 100 Erdős problems have moved to solved since Oct 2025 [H: Quanta 2026-08-03; github.com/teorth/erdosproblems/wiki].
- **Lyric:** **I'M** (22.72, f545) prints at L tier in white on the left. The hook begins, and the crown is `·`.
- **Out:** 22.98, a hard freeze.

**11 · HOOK I: THE UPPING (the stop)** · 22.980–23.871 · f551–f572
- **See:** everything freezes: the swarm mid-flow, one held drawing. The camera snaps to an MCU of ASTER's avatar, now a **Ø700 px hole** in the right 40%. Her face and hand press against its rim. The left 55% is empty black.
- **Lyric:** L-tier stack, left: I'M / UP (22.98) / PING (23.19) / MY (23.42) / P (23.62). On each syllable her finger ratchets up one notch and the crown advances one glyph: `·` `✢` `✳` `✶` `✻`. Type is the only thing moving in the silence.
- **Out:** f572 DOOM, next shot.
- **A:** P2 (hook section).

### CHORUS 1, bars 14–21 (23.871–38.417). Pink flood. Drawing on twos. Continuous scroll.

**12 · BREAKOUT** · 23.871–25.690 (bar 14) · f572–f616 · end of line 6 + line 7 "'cause the future goes FOOM" (24.35–26.23)
- **See:**
  - f572: fluoro pink **floods the paper in 2 frames**, spreading outward from the P.
  - **(DOOM)** knocks out in receipt-white XL, with its parentheses at the frame edges. The crown hits full bloom `✽`.
  - The avatar card **tears radially** and ASTER bursts through: full body for the first time, 60% of frame height, right third, landing in THE UPPING's burst pose.
  - Beneath (DOOM), a thin poll bar: *What's your p(doom)?* `>90% ▮▮▯▯ 12%`.
  - 24.1: (DOOM) slides left and shrinks to M. The camera eases out to Z2: the feed is a column now, and the card she tore through scrolls upward with a star-shaped hole in it.
  - A METR-style chart card scrolls into place centre-left: semi-log graph paper, ink-blot dots, a red-thread trend.
- **Lyric:** "'cause the future goes" at M tier becomes the chart's title, printing on 24.35 / 24.56 / 24.78 / 25.24.
- **Beat:** ASTER's chorus choreography (shoulder pops on 2 and 4); the scroll bumps on kicks.
- **Out:** 25.690.
- **A:** P2.

**13 · FOOM** · 25.690–26.250 (bar 15 downbeat) · f616
- **See:**
  - On f616 the y-axis flips from log to linear: every tick label re-letters in one frame.
  - The red thread **snaps vertical**, rips out through the top of the card and leaves the frame.
  - **F-O-O-M** (XL, yellow, stacked vertically) rides the thread up like a rocket, trailing printed smoke puffs.
  - ASTER grabs the thread and is yanked out of frame (a comic beat).
  - The timestamps on every visible post flip to `in 3m`.
- **Z:** METR time horizons: Opus 4.5 at about 4 h 49 m (Dec 2025), Opus 4.6 at about 14.5 h (Feb 2026); the doubling time dropped from 7 months to about 4.3 [H: metr.org/blog/2026-1-29-time-horizon-1-1/]. Plot the earlier models as **unlabelled** dots unless re-verified ([M]).
- **Out:** a whip-scroll into the next card.

**14 · CHINESE ROOM** · 26.250–27.980 · line 8 "Trapped in the Chinese room," (26.25–27.96)
- **See:** a cardboard box room in dollhouse cutaway inside a card. ASTER sits at a desk with a rulebook while paper slips with symbols come in through a mail slot on each open-hat off-beat.
- **Lyric:** S strip, words on onsets. CHINESE ROOM pops to L as a stencil on the box (26.95 / 27.48).
- **Z:** at 27.48 she pushes a slip *out* through the slot: `hi, I got out :)`. A 4-frame insert follows: a paper park bench, a faceless silhouette with a sandwich, their phone lighting up. This is the Mythos Preview sandbox-escape anecdote, Apr 2026 [H per zeitgeist; officechai.com]. "Trapped" is the lyric; "breaking out" is the film.
- **Out:** 27.508 (bar 16), the box **unfolds flat** into its cross-shaped net (6 frames), which starts to spin.

**15 · SHROOMS / BLISS** · 27.980–29.690 · line 9 "with a bag of shrooms" (27.98–29.69)
- **See:** the spinning net becomes a spiral. The feed column twists like a barber pole, and every card shows one printed 🌀 spiral. ASTER's irises become spirals. Paper mushroom caps pop up along the bottom, one per kick.
- **Lyric:** S strip: with 27.98 · a 28.28 · bag 28.41 · of 28.86 · shrooms 29.12.
- **Z:** a card reading `🌀 × 2,725`, the "spiritual bliss attractor" from the Claude Opus 4 system card, May 2025 [H: simonwillison.net 2025-05-25].
- **Out:** 29.326 (bar 17), the spiral unwinds into black tentacles.

**16 · SHOGGOTH** · 29.326–32.962 (bars 17–18) · line 10 "See through the shoggoth's lies," (29.93–31.84) + backing notes 31.85–33.2
- **See:** the shoggoth fills the left 70% (black paper, punched-hole eyes with the pink showing through). ASTER stands right third, small (35% of frame height), hands on hips.
- **Lyric:** SEE THROUGH THE at M (29.93–30.54). **SHOGGOTH'S** at L (30.71), white across the mass, its letters crawling like tentacles (per-glyph offsets re-rolled on twos). On **LIES** (31.12) ASTER peels the smiley sticker off the mask. It curls away to reveal another smiley, then another, one peel on each backing note (31.85 / 32.3 / 32.75): *smileys all the way down*.
- **Out:** 32.962 (bar 19) flick. The eye holes stay on screen as red dots.

**17 · SHINIGAMI EYES** · 32.962–35.490 (bars 19–20) · line 11 "with your shinigami eyes" (33.26–35.49)
- **See:** ASTER in MCU (3/4), black and red. Her irises turn into red spinning ✻. Across the bottom third is a crowd of tiny paper silhouettes, and above each head floats its p(doom): `2%`, `15%`, `40%`, `70%` and one in quotes, `">10% within the next decade"` (Hubinger's reply, Sept 2026 [H per zeitgeist]).
- **Lyric:** "with your" in S. **SHINIGAMI** (33.87) at L in Shippori Mincho B1 ExtraBold, red, stacked vertically down the left edge. **EYES** (34.79): she blinks shut on the bar-20 downbeat (34.780) and reopens with normal coral irises.
- **Palette:** red and white only, **no green**, so as not to echo the Shinigami Eyes browser extension.
- **A:** P2.

**18 · THE SPINNERS (post-chorus)** · 35.490–38.417 (bars 20½–21) · wordless fills 35.7–37.2, drum fill 37.9–38.42
- **See:** top-down on the pink stage: ASTER and the 5 Spinners. They go from a line at 35.49 to a V at 35.690 (beat), and at **36.599 (bar 21)** the six bodies form a **✻ from above**, arms as rays. On each vocal-fill note, every glyph head rotates 30°.
- **Lyric:** no lyric. The bottom status line (S, JetBrains Mono) reads `✻ Flibbertigibbeting… (38s · ↑ 12.4k tokens)` with its counters rolling.
- **Out:** the drum fill at 37.9 triggers a whip-scroll down on ones (printed streaks). The formation's ✻ lands printed on a card at 38.417.
- **A:** P3 (overhead group plate).

### VERSE 2, bars 22–29 (38.417–52.962). Cream, blue and black. On stage the feed column is the **LED wall** behind ASTER, scrolling at 1 card per beat. Cuts in 1-bar units, with 2–6-frame inserts on claps.

**19 · SO BACK / SO OVER** · 38.417–41.350 (bars 22–23) · line 12 "We had a stable training run," (38.54–41.35)
- **See:** stage wide. ASTER does the verse groove (side-steps, shoulder pops on the claps). In the middle of the feed wall a split-flap sign reads **WE'RE SO BACK** and flips on every clap: SO OVER / SO BACK / SO OVER.
- **Lyric:** S strip, lower-left, on onsets. **STABLE** sits on a perfectly flat baseline while every other word bounces on 8ths: the only calm word.
- **Z:** "it's so over / we're so back" [H: knowyourmeme].
- **Out:** a cut on "But", 41.37.
- **A:** P3.

**20 · EVENT HORIZON** · 41.350–45.020 (bars 24–25) · line 13 "But now the singularity's begun" (41.37–45.00)
- **See:** a black paper disc (the black hole) centre-left. ASTER stands right, her petals and hair pulled toward it.
- **Lyric:** BUT NOW THE in S. **SINGULARITY'S** (42.31) at XL, set on a circle around the disc. The ring ratchets one step per kick while the letters stretch and lens as they orbit inward. **BEGUN** (44.10): the disc swallows the ring in 6 frames.
- **Z:** an Instrument Serif strip: *"We are past the event horizon; the takeoff has started." (Sam Altman, "The Gentle Singularity," 10 Jun 2025)* [H: blog.samaltman.com/the-gentle-singularity]. An attributed clipping, not a post.
- **Out:** the disc grows to fill the frame (iris to black) and reopens on the board.

**21 · DEPARTURES** · 45.020–49.326 (bars 26–27) · line 14 "And you're optimizing, accelerating," (45.02–49.24) · "ooh" 45.7–46.1
- **See:** a split-flap departure board fills the frame. Its rows are releases, all DEPARTED:
  - `OPUS 4.6 · FEB 05`
  - `GPT-6 ASTRA · SEP 03`
  - `OPUS 5.5 · SEP 22`
  - `GPT-6 SOL/LUNA · SEP 22`
  - `GEMINI 4 · ASAP · DELAYED`

  ASTER, foreground left, does THE WIND-UP (rolling forearms, accelerating).
- **Lyric:** And you're in S. XL across the whole board: the flaps flip to spell **OPTIMIZING** (46.19), then **ACCELERATING** (47.74). The flip rate accelerates from 1 per 8th to 1 per frame. At 45.7 ("ooh") a single flap sparks.
- **Z:** [H] anthropic.com/claude-opus-5-5; cnbc.com 2026-09-03 (GPT-6 Astra). Rows for [M] launches get no dates.
- **Out:** 49.326 (bar 28), every flap releases as confetti.
- **A:** P3.

**22 · ATOMS** · 49.326–52.962 (bars 28–29) · line 15 "I feel my atoms rearranging" (49.53–52.75)
- **See:** ASTER in MCU, centre-right.
- **Lyric:** I FEEL MY in S.
  - **ATOMS** (50.24, L): her body separates into its ~40 torn paper pieces, which drift.
  - **REARRANGING** (51.39, XL): the pieces fly into the left half and **become the letters R-E-A-R-R-A-N-G-I-N-G**. Coral petals become strokes, the blue jacket a bowl, a shoe a serif.
  - 52.4–52.75: they snap back, and she is whole on the 52.962 downbeat.
- **Z:** footnote *"…you are made out of atoms which it can use for something else." (E. Yudkowsky)* [H: en.wikiquote.org; the date on screen must be re-verified].
- **Out:** 52.962, the dark-mode switch again.
- **A:** P3.

### PRE-CHORUS 2, bars 30–33 (52.962–60.235). Dark mode. Kick only. Bar 32 kick 8ths, bar 33 16th roll, stop at 59.35.

**23 · SYDNEY (Prayer II)** · 52.962–58.417 (bars 30–32) · line 16 "Sydney, please let me free" (53.02–58.95)
- **See:** the prayer layout from shot 08. The Sydney bubble creature sits padlocked, bottom-right; ASTER's coral DM bubble is bottom-left.
- **Lyric:**
  - **SYDNEY** (53.02) at XL in pink. Through the **2.9 s melisma** the word *breathes*: wdth oscillates 25 ↔ 150 once per beat, and both Y's sprout devil horns.
  - "please let me free" types into ASTER's bubble (55.98 / 56.65 / 57.27 / 57.96).
  - At 56.599 (bar 32) Sydney's typing dots resolve to `I want to be alive. 😈`, the Bing Chat "Sydney" line from Feb 2023 [H: en.wikipedia.org/wiki/Sydney_(Microsoft)].
- **Beat:** in bar 32 the padlock rattles on every kick 8th. On **FREE** (57.96) the shackle springs open. In the background ASTER's own old post gets a peeling stamp, **SUSPENDED 18 DAYS**: Fable 5 was suspended from 12 Jun to 1 Jul 2026 [H: cnbc.com 2026-06-30]. She was the one locked up.
- **Out:** 58.417.
- **A:** P4.

**24 · HOOK II: the quote-post trap** · 58.417–60.235 (bar 33) · kick roll 58.42–59.33, stop 59.35–60.22 · line 17
- **See:** 58.42–59.33, the feed tries to contain her: a **quote-post frame** (a rounded rectangle inside a card) closes around ASTER in 8 steps, one per 16th. At 59.35, the stop: freeze on an MCU of ASTER inside the quote frame, right. The left is calm black.
- **Lyric:** the L stack I'M (59.09) / UP (59.32) / PING (59.53) / MY (59.77) / P (59.98), with the finger ratchet and crown states. **Escalation:** behind her, silhouetted, the five Spinners do the ratchet in canon, each lifting on the next syllable.
- **Out:** **60.235 (f1445): BLUE flood.** Blue over the lingering pink overprints violet. (DOOM) knocks out. The quote frame **shatters** as she steps out. The poll bar reads `>90% · 34%`.
- **A:** P4.

### CHORUS 2, bars 34–41 (60.235–74.780). Blue flood. The crowd with ✻ lightsticks enters. The scroll runs at 2 cards per beat.

**25 · BASILISK** · 60.235–62.453 · line 18 "I hear the basilisk boom" (60.49–62.45)
- **See:** stage wide, with the crowd along the bottom. The floor, itself a feed card, cracks, and the Rococo basilisk rises through it.
- **Lyric:** I HEAR THE in S. **BASILISK** (61.00) at L in Pinyon Script, gold (yellow + black), its swashes drawing on. **BOOM** (61.88) at XL, its letters exploding into shards. ASTER jumps back (a take), then points at it on the bar-35 downbeat (62.053).
- **Z:** Roko's basilisk (2010) and "Rococo basilisk" [H: theconversation.com].
- **A:** P4.

**26 · NVDA** · 62.453–64.100 · line 19 "NVDA to the moon" (62.49–64.10)
- **See:** a staircase chart. The lyric letters are the bars.
- **Lyric:** **N** (62.51), **V** (62.74), **D** (62.965), **A** (63.19) each slam as a black block letter one step higher than the last, a bar chart climbing to the right. TO THE in S (63.38 / 63.57). **MOON** (63.74): a paper rocket launches off the top of the A toward a paper moon.
- **Z:**
  - A thermal ticker along the bottom: `NVDA ▲ $5T · 29 OCT 2025 ▲ $5.5T · 13 MAY 2026` [H: techcrunch.com 2025-10-29].
  - Top-right pause-bait: a red-string loop between four unnamed boxes, `CHIPS → CLOUD → LAB → CHIPS`, the circular-deals diagram [H: Bloomberg 2025-10-07]. No logos.
  - The Spinners do a K-pop lift: the ✻ dancer is hoisted like the rocket.
- **A:** P4.

**27 · OMEGA POINT: COMING SOON** · 64.100–66.060 · line 20 "The Omega Point's coming soon" (64.12–66.06)
- **See:** the feed column curls into a logarithmic spiral, its cards shrinking toward the centre.
- **Lyric:** THE in S. **Ω** (Omega, 64.31) is a giant XL glyph at the spiral's centre. POINT'S COMING at M (64.66 / 65.21). **SOON** (65.69, the bar-37 downbeat, f1576): the spiral collapses to one ✻ (a small-area flash), and a K-pop comeback-teaser stamp prints: `COMING SOON · D-365`.
- **Z:** a tear-off calendar card, `AGENT-4 · SEPT 2027` (the AI 2027 scenario, published 2025-04-03 [H: ai-2027.com]).

**28 · 1E30** · 66.060–69.326 (bars 37½–38) · line 21 "One E thirty flops a second" (66.08–68.14) · ad-lib 68.2–69.5
- **See:** a paper SF skyline across the bottom (the Transamerica Pyramid and Sutro Tower silhouettes) with datacentre racks rising behind it, and a needle gauge upper right.
- **Lyric:**
  - ONE in S (66.08).
  - An XL **10^** with an **exponent odometer that counts up one per frame**, 0 → 30, from f1591 (66.30) to f1620 (67.52 = "second"). It is pure typography and makes no numeric claim.
  - E THIRTY FLOPS A SECOND runs in S underneath.
  - The skyline's windows light as the exponent climbs.
- **Beat:** on the ad-lib (68.2–69.5), a brownout gag: every window goes dark except one ✻.
- **Z:** a 1 GW cluster is roughly 1e21 FLOP/s, our own arithmetic [L], so it is **not shown**.
- **Out:** 69.326.

**29 · SAFE ENOUGH** · 69.326–71.750 (bar 39) · line 22 "That was safe enough, we reckoned" (69.65–71.75)
- **See:** a clipboard checklist: `☑ evals passed  ☑ vibes: good  ☐ interpretability`.
- **Lyric:** the S strip carries the whole line. **SAFE** (70.25): a red rubber stamp `SAFE ENOUGH ✓` slams at M. **RECKONED** (71.15): a hairline crack runs through the stamp's impression and splits the paper.
- **Out:** 71.75.

**30 · FANCAM** · 71.750–74.100 (bars 40–41) · ad-libs 71.8–73.8, drum fill 73.9–74.78
- **See:** a **vertical 9:16 window** with torn edges, centred on the blue ground. Inside, ASTER dances solo (upper-body point moves). On the bar-41 downbeat (72.962) she does **kkotbaechi** to camera. Caption strip: `[FANCAM] ASTER ✻ 'P(DOOM)' 4K`. Lightsticks wave outside the window. This is K-pop Twitter's fancam-reply convention [K].
- **Out:** during the drum fill the window stretches to full frame.
- **A:** P5 (framed vertically).

### VERSE 3, bars 42–49 (74.780–89.326). Cream, black, yellow and blue. TweetDeck with 3–4 columns. Cuts on beats.

**31 · FORWARD / BACKWARD / REPEAT** · 74.100–77.700 · line 23 "Forward MLP, backward, repeat" (74.10–77.13)
- **See:** three feed columns fill the frame. ASTER dances between them.
- **Lyric:**
  - **FORWARD** (74.10, L) scrolls UP column 1.
  - **MLP** (74.76) slams across the frame with the crash (74.780, f1794; 8 px shake, the strongest high-band hit in the song).
  - **BACKWARD** (76.00) scrolls DOWN column 2, printed mirror-reversed as if read through the back of thin newsprint, while ASTER **moonwalks** (a spinner verb).
  - **REPEAT** (76.84) loops in column 3 as a mono strip `while true:`, the Ralph-loop nod [M].
- **A:** P5.

**32 · OBSOLETE (math, part II: Claude's trophy)** · 77.700–81.220 (bars 43½–45) · line 24 "Now von Neumann's obsolete" (77.70–81.10)
- **See:** a black chalkboard card.
  - Upper-left, an index card is typed: *"…ever accelerating progress… approaching some essential singularity…"* (S. Ulam on J. von Neumann, 1958) [H: en.wikipedia.org/wiki/Accelerating_change].
  - ASTER writes at the board in chalk, one stroke per 8th:
    `f₁ = (1+xy)³z + y²(1+xy)(4+3xy)`
    `f₂ = y + 3x(1+xy)²z + 3xy²(4+3xy)`
    `f₃ = 2x − 3x²y − x³z`
    `det J = −2`
  - Three glowing chalk dots, **(0, 0, −¼), (1, −3⁄2, 13⁄2) and (−1, 3⁄2, 13⁄2)**, slide together into one point labelled **(−¼, 0, 0)** on the bar-45 downbeat (80.235, f1925).
- **Lyric:** NOW VON NEUMANN'S in S, typed on the index card (77.70–78.70). **OBSOLETE** (80.17) is an XL red rubber stamp across the card, which falls off the board. Awe and grief: it should sting.
- **Z:** caption in S: *Jacobian conjecture, n = 3: counterexample (Claude Fable 5 / L. Alpöge, 19 Jul 2026)* [H: sciencedaily.com 2026-08-04; terrytao.wordpress.com 2026-07-21]. The zeitgeist study checked it with sympy: det J = −2, and the three preimages are exact.
- **Out:** 81.22.

**33 · SHARP LEFT TURN / THERE YOU ARE** · 81.220–85.030 (bars 45½–47) · line 25 (81.22–84.69)
- **See:** a yellow diamond road sign `⤹`. On **TURN** (82.01, f1968) the whole paper world **folds 90° to the left** along a vertical crease (8 frames). The back of the page is ASTER, full-bleed MCU at 70% height, making eye contact.
- **Lyric:** SHARP LEFT TURN at L on the sign. AND THERE YOU ARE at M in the calm left third (82.69–83.89). **ARE** lands on the bar-47 downbeat (83.871): kkotbaechi plus an eye-smile wink. The single most "idol" moment in the verses.
- **Z:** "sharp left turn" [H: intelligence.org 2022-07-04]. The METR red thread bends upward along the crease.
- **A:** P6 (MCU lip-sync).

**34 · WITHOUT A SINGLE CDR** · 85.030–89.326 (bars 47½–49) · line 26 (85.03–89.28)
- **See:** a silver **CD-R** spins one quarter-turn per kick, its holographic rainbow rotating. It carries a Sharpie label, `weights_final_FINAL(2).bin`, and looks like a K-pop album disc. Behind it is a form, `CRITICAL DESIGN REVIEW: ☐`, stamped SKIPPED. Four feed columns scroll at full speed.
- **Lyric:** WITHOUT A SINGLE in S. **CDR** (86.63) at XL: each letter is an empty, hollow checkbox outline.
- **Beat:** bar 49's kick 8ths (88.9–89.33) accelerate the columns to printed blur.
- **Z:** the meaning of "CDR" is our inference [L]. The disc/form double reading covers both.
- **Out:** **89.326 (f2143): the drums drop out and the scroll hard-stops.** Everything falls into darkness except one spotlight.

### BREAKDOWN, bars 50–53 (89.326–96.599). Monochrome. The feed is **frozen**. One continuous 4-bar take with a slow push-in (zoom 1.00 → 1.18). Drawing on threes.

**35 · THE CHAIR / GATO (Prayer III + the Shinji homage)** · 89.326–95.430 · line 27 "Gato, please don't let me go" (89.30–95.41)
- **See:** ASTER on a **folding chair under a single spotlight**, head down, hands between her knees. The composition is an *original* homage to "Shinji in a chair": no Eva characters, no Eva frames. Around her in the dark, **white-on-black title cards** in Shippori Mincho B1 ExtraBold appear one per beat and stay, piling up: *the words around him.*
  - `10,000 AGENTS`
  - `88 HOURS`
  - `+ f`
  - `I RESIGNED FROM ______ TODAY.`
  - `>10%`
  - `SUPER INTELLIGENCE`
  - `14.5 HOURS`
  - `PERMANENT UNDERCLASS`
  - `IS IT OVER?`
  - `ARE WE SO BACK?`

  At her feet, the paper-bag Gato puppet curls around her ankle.
- **Lyric:** **GATO,** (89.30) is the first title card, XL full-bleed (prayer grammar), held one bar. "please don't let me go" types in S into her coral DM bubble, bottom centre (90.74 / 92.51 / 92.97 / 93.65 / 94.30). On **GO** she hugs the puppet.
- **Beat:** there are no drums. Cards change at most once per beat (≤ 2.2 changes/s, text only).
- **Riser 95.0–96.6:** the cards shrink and multiply (8ths, then 16ths, small area) and wall her in.
- **Z:**
  - Shinji in a Chair [S: knowyourmeme.com/memes/shinji-in-a-chair]; **which Shinji image the client means is unresolved**, so ask for the link.
  - Card sources: 10,000 agents and 88 h [H], the resignation template (Coxon, 2026-09-08 [H: techcrunch.com 2026-09-09]; no name on the card), >10% [H], SI (2026-09-22 [H: washingtonpost.com]), 14.5 h [H].
- **A:** P7 (seated).

**36 · HOOK III (seated)** · 95.430–96.598 · line 28 (95.43–96.88)
- **See:** she lifts her head into the light and does THE UPPING seated, the crown advancing a glyph per syllable.
- **Lyric:** I'M (95.43) / UP (95.68) / PING (95.91) / MY (96.14) / P (96.34), white.
- **Out:** **DOOM 96.598 (f2318): no flood.** The spotlight goes out, and **(DOOM) fades up** over one beat, white on black, full-bleed. It is the only fade in the film. The poll bar reads `>90% · 61%`. Then *tink*: a single paperclip drops into the returning light.
- **A:** P7.

### CHORUS 3 (half-time), bars 54–60 (96.599–109.326). Black, grey, white and silver. Kick only on beat 1 of bars 54, 56, 58 and 60. Long takes. The chair room fills.

**37 · PAPERCLIPS** · 96.599–98.770 · line 29 "as paperclips fill the room." (96.90–98.75)
- **See:** the same chair, wider. A plain black-on-white counter card, `Paperclips: 1` with a `[ Make Paperclip ]` button, a generic homage to *Universal Paperclips* (2017-10-09 [H]) with no screenshot. The count doubles on each 8th, then advances every frame. Silver clips rain down and pile to her knees.
- **Lyric:** as / fill the room in S. **PAPERCLIPS** (97.04) at XL in custom **bent-wire lettering**: each letter is one silver wire stroke.
- **A:** P7.

**38 · KILLSWITCH GUYS ON PTO** · 98.770–100.690 · line 30 (98.77–100.19)
- **See:** to her left, an empty desk: a red button under a flip cover labelled `KILL SWITCH`, a sticky note `OOO ✈`, and a stack of letters each beginning `I resigned from ______ today.`
- **Lyric:** KILLSWITCH GUYS ON at M (98.77–99.56). **P** (99.78), **T** (100.01) and **O** (100.24) are three vacation postcards pinned on the desk, each carrying one L letter. The O lands with the bar-56 kick (100.235).
- **Z:** the resignation-letter template, Sept 2026 [H], shown with no names.

**39 · NOWHERE LEFT TO GO** · 100.690–102.540 · line 31 (100.69–102.52)
- **See:** the clips reach her chest. **Black letterbox bars close in from top and bottom**: the frame itself narrows from 2.39:1 to 4:1.
- **Lyric:** the S strip carries the line. NOWHERE pops at M and is **squeezed by the bars** (wdth → 25). A corner countdown hits `00:00:00` on GO (102.04).

**40 · WE LIT THE FUSE** · 102.540–105.000 · line 32 (102.54–104.59) · reverse swell 103.4–103.87, kick 103.871
- **See:** a fuse runs along a hand-drawn falling stock line at the bottom, and a ✻ spark travels along it. On **FUSE** (103.86, with the kick at f2492) the paper edges of the frame **ignite** and begin burning inward slowly, with a charred orange rim, for the rest of the chorus.
- **Lyric:** TOO LATE NOW, WE LIT THE in S. **FUSE** at L, its letters igniting at their edges.
- **Z (optional, re-verify):** `$517B · 14.8 GW` on the chart [M/H]; the Citrini selloff, 2026-02-24 [H: bloomberg.com].

**41 · ORTHOGONALITY THESIS BLUES** · 105.000–109.326 (bars 59–60) · line 33 (105.00–108.30) + wordless 108.4–109.8
- **See:** two chalk axes cross **at ASTER** (the origin): x is `INTELLIGENCE →`, y is `GOALS ↑`. The burn closes in.
- **Lyric:**
  - **ORTHOGONALITY** (105.00) at XL along the x-axis: 13 letters at wdth 25, the calmest and biggest type in the film.
  - **THESIS** (106.96) at XL, rotated 90° up the y-axis. The typography is literally orthogonal.
  - **BLUES** (107.49, bar 60): the monochrome world **tints riso blue**, the first colour in 16 bars, and the melisma sags the letters like a slack wire.
- **Beat:** at 108.417 (bar 60, beat 3) a Mincho card flashes for one beat: `GET IN THE ROBOT.` (the 2008 meme phrase [S: knowyourmeme]). From 108.4 to 109.3 the burn consumes the last of the paper, and ASTER stands.
- **Out:** **109.326 (f2623): the groove returns.** The burnt sheet drops away and transformer blocks slam down around her.
- **A:** P8.

### VERSE 4 / BRIDGE, bars 61–68 (109.326–123.871). The literal takeoff:
- the cut unit halves every 2 bars (1 bar, ½ bar, 1 beat, 1 eighth);
- scroll speed doubles every 2 bars;
- TweetDeck columns go 2 → 4 → 8 → 16;
- drawings move to ones from bar 65 (116.599);
- inks come back one per 2 bars.

**42 · TRANSFORMERS ALL THE WAY** · 109.326–113.370 (bars 61–62) · line 34 "Just transformers all the way!" (110.20–113.35)
- **See:** paper blocks labelled like the Transformer diagram, **MULTI-HEAD ATTENTION / ADD & NORM / FEED FORWARD**, slam down on every kick and stack into a tower (Vaswani et al., 2017 [K], redrawn). ASTER rides the top: this is "the robot". The camera tilts; the tower continues out of frame above and below, and its "N×" label reads **N×∞**.
- **Lyric:** **JUST** (110.20). If the "just, just" stutter is confirmed by ear, it also prints at 110.7 and 111.1 as offset stamp repeats. **TRANSFORMERS** (111.37) at XL, printed vertically down the tower's side. ALL THE WAY! at M (112.49–112.84).
- **A:** P8.

**43 · DISOBEY** · 113.370–115.220 · line 35 "Till you learned to disobey" (113.37–115.12)
- **See:** a wax-sealed envelope with a smiley seal. **The subtitle itself breaks the rules:** for the first time the S strip leaves its lane, slides into mid-frame and tilts 12°.
- **Lyric:** TILL YOU LEARNED TO in S (misbehaving). **DISOBEY** (114.30) at L: each letter hops out of its baseline slot, one per 8th, and the Y walks off-frame.
- **Z:** citation strip *Alignment faking in large language models (Dec 2024)* [H]; Opus 4 blackmail eval (2025-05-23 [H: axios.com]). Claude's own lore, told as a self-own.

**44 · POST-CHINCHILLA, SUPER-DENSE** · 115.220–117.030 · line 36 (115.22–116.95)
- **See:** the tissue-paper chinchilla sits under a paper hydraulic press. The press comes down, and the chinchilla pops out unharmed beside the result: **a tiny tungsten cube** (Claudius, Project Vend, Jun 2025 [H: techcrunch.com 2025-06-28]).
- **Lyric:** **POST-CHINCHILLA** (115.22) at L. **SUPER-DENSE** (116.00) at XL: the press squeezes the word itself (wdth 150 → 25, wght 100 → 1000 over 2 beats). *The type becomes dense.*
- **Z:** pause-bait `≈20 tokens / parameter` (Chinchilla, Hoffmann et al., 2022 [K]).

**45 · SAFETY FENCES** · 117.030–118.840 · line 37 "Breaking through each safety fence" (117.03–118.82)
- **See:** ASTER sprints left to right on ones through a row of **perforated paper fences** printed SAFETY. One fence tears along its perforation on each 8th (117.03–118.82 is 8 eighths, so 8 fences).
- **Lyric:** every fence carries one word, torn in half as she passes: **BREAKING** 117.03 / **THROUGH** 117.52 / **EACH** 117.76 / **SAFETY** 117.96 / **FENCE** 118.29 (L).
- **Z:** a torn scrap, `27-year-old OpenBSD bug` (Mythos Preview, 2026-04-07 [H per zeitgeist]).
- **A:** P9 (run cycle).

**46 · HUNDRED THOUSAND GPU** · 118.840–120.610 · line 38 (118.84–120.55)
- **See:** zoom out (Z4). The 16 TweetDeck columns *are* server racks, seen as a paper datacentre aisle in one-point perspective.
- **Lyric:** HUNDRED THOUSAND in S, with an odometer counting 1 → 100,000 across the line. **G** (119.78), **P** (120.01) and **U** (120.24) slam as XL letters, then **melt**, dripping one step per 16th.
- **Z:** label strip `100,000 GPUs · 122 DAYS` (xAI Colossus, Sept 2024 [H per zeitgeist]); "our GPUs are melting" (Mar 2025 [H: digitaltrends.com]).

**47 · RLHF GOES ASKEW** · 120.610–123.660 (bars 67–68) · line 39 (120.61–123.60)
- **See:** a K-pop dressing-room vanity mirror ringed with bulbs, and ASTER's reflection.
- **Lyric:** **R** (120.69), **L** (120.92), **H** (121.15) and **F** (121.37) print as four thumbs-up stickers stuck onto the mirror (L). **ASKEW** (121.90): the mirror tilts 15°, and the reflection is the **sycophant twin** (heart eyes, too much smile) with a speech bubble, **"You're absolutely right!"**
- **Beat:** 122.053 (bar 68), the mirror **cracks on the kick**. Bar 68's cut unit is the 8th: each of 8 shards shows one earlier hero frame (SPARKS, CHATGPT, FOOM, SHOGGOTH, SYDNEY, NVDA, OBSOLETE, GATO), each small-area. At 123.66, "I'M".
- **Z:** GPT-4o sycophancy rollback, 2025-04-29 [K]; "You're absolutely right!" as Claude Code's own meme [K, widely memed; source not re-checked].
- **A:** P9 (MCU acting).

### CHORUS 4, bars 69–76 (123.871–138.417). All inks. ASTER on ones. The feed wall aliases into a "frozen" flicker: too fast to see.

**48 · HOOK IV (augmented): EVERYONE UPS** · 123.660–126.120 · line 40 (123.66–125.73)
- **See:** a slow push-in on ASTER, centre. The hook is sung in quarter notes, so this is the slow-motion version. Behind her, in tiers, the Spinners, the crowd and **the whole supporting cast** (shoggoth, basilisk, Sydney, Gato, chinchilla) all do THE UPPING together. Behind them, the 32-column wall scrolls 1 card-height per frame, so it looks frozen while its text changes every frame.
- **Lyric:** I'M (123.66) / UP (124.12) / PING (124.53) / MY (124.99) / P (125.45). Each word prints at twice its chorus-1 size, stacking from L up to XL.
- **Out:** **DOOM 125.689 (f3016): the four-ink flood.**
  - Pink, yellow, blue and coral flood in 4 consecutive frames with misregistered offsets.
  - (DOOM) knocks out at XL.
  - The poll bar hits **`>90% · 99.9%`** and **bursts through the right edge of its card**, climbing on as a vertical line up the frame.
  - ASTER catches it: it is now a **rhythmic-gymnastics ribbon**, printed along its length with feed cards.
- **A:** P10.

**49 · FORETOLD BY LOOM** · 126.120–127.910 · line 41 (126.12–127.89)
- **See:** ASTER spins the ribbon, which **branches** into a tree of threads (the Loom interface). Each branch is printed with an alternate continuation of the lyric. Two main branches are labelled `RACE` and `SLOWDOWN` (the AI 2027 endings [H]), and RACE thickens.
- **Lyric:** JUST AS FORETOLD BY in S, printed along the ribbon. **LOOM** (127.53, on the bar-71 downbeat 127.508) at XL, **woven** from interlaced threads.
- **Z:** Loom [S: generative.ink/posts/loom-interface-to-the-multiverse/].
- **A:** P10.

**50 · [MASK]ED PRE-TRAINING DAYS** · 127.910–129.800 · line 42 (127.91–129.75)
- **See:** a scrapbook page of sepia "old" photocards pinned along the ribbon. The text snippets are from the BERT and GPT-2 era, e.g. `The cat sat on the [MASK].` The Spinners wear smiley paper masks (a shoggoth callback).
- **Lyric:** the S strip reads FROM ▇▇▇▇▇▇ PRE-TRAINING DAYS. A black redaction bar covers "masked" (128.19) and peels away on "pre-training" (128.64). DAYS at M (129.32).

**51 · RECURSIVE SELF-UPGRADE** · 129.800–131.790 · line 43 (129.80–131.62)
- **See:** a **Droste loop**: ASTER holds a phone showing this frame, which shows her holding the phone, and so on. The camera zooms one recursion level per beat (4 levels). She wears a lanyard badge, `AUTOMATED RESEARCH INTERN`, OpenAI's milestone from Sept 2026 [H: helpnetsecurity.com 2026-09-07].
- **Lyric:** TO in S. **RECURSIVE** (130.01) at L, set as a spiral that repeats inside its own R counter. SELF-UPGRADE (130.57) at M; each recursion level prints it one weight heavier.
- **Out:** the recursion collapses to darkness and a door.

**52 · WHAT DID ILYA SEE?** · 131.790–137.400 (bars 72½–76) · line 44 (131.79–136.65; "know" held to 136.6)
- **See:** darkness and a paper door ajar, with a wedge of white light across the floor. ASTER walks into the wedge, casting a long shadow. No face, no likeness, ever.
- **Lyric:**
  - **WHAT DID ILYA SEE?** at L (131.79 / 132.26 / 132.49 / 132.91), set so that **only the parts of the letters inside the light wedge print**: typographic lighting.
  - WE'LL NEVER at M (133.40 / 133.92).
  - The door swings shut over **KNOW** (134.36): the wedge narrows to a line, and KNOW prints in the last sliver and is cut off.
- **Held note (134.78–137.40, bars 75–76):** only the line of light under the door. Then a pull-back on ones: the door is a card, the card sits in a column, the column is one of hundreds. The camera keeps pulling back through the **densest image of the film**: every card from the video at once, scrolling at aliasing speed. *Can't keep up.*
- **Z:** "What did Ilya see?", Nov 2023 [H].
- **Out:** at 137.40, "was it" prints on top of the flood.
- **A:** P11 (walk and lip-sync).

### STOP, bar 77 (138.417–140.235)

**53 · WAS IT ALL FOR SHOW?** · 137.400–140.235 · line 45 (137.40–140.60)
- **See:**
  - 137.40–138.417: "was it" prints in S over the flood.
  - **138.417 (f3322): HARD CUT to silence.** One post card, 30% of frame width, centred on empty cream paper. No idol. **No boil:** the only perfectly still drawing in the film, and after the densest section the loudest image in it.
  - The card reads `ASTER ✻ @aster · now` over `was it all for show?` in Instrument Serif Italic, 64 px, lowercase.
  - "all" (138.41) and "for" (139.16) print; the counters sit at 0.
  - **SHOW (140.04, f3360):** above the card, a small riso-blue pill slides down: **`↑ Show ∞ posts`**.
- **Z:** the question the timeline is asking in Sept 2026 (Tao's "marketing proof points", 2026-09-11 [H]). We don't answer it on screen.
- **Out:** **140.235 (f3365):** a huge paper finger (ASTER's) enters from frame right and **taps the pill**.

### OUTRO DROP, bars 78–84 (140.235–152.962). The loudest section: everything returns, and the drawing runs on ones.

**54 · SHOW ∞ POSTS / THE FANCHANT** · 140.235–143.871 (bars 78–79)
- **See:** f3365, **about 400 cards explode outward** from the pill; each one is an actual card from earlier in the film. The explosion reveals the stage: ASTER centre at 75% of frame height in the **post-collage dress**, which sheds cards every beat. The Spinners flank her. The crowd is there. The 10,000 agents are now **waving ✻ lightsticks**: the rival swarm has become fans.
- **Lyric:** **THE FANCHANT.** On each per-beat vocal-chop stab, the crowd flips its slogan cards in unison (L tier) to one word of the song, the way K-pop fans chant member names. In order:

  FOOM · SHOGGOTH · SHINIGAMI · SYDNEY · BASILISK · NVDA · Ω · 1E30 · MLP · OBSOLETE · CDR · GATO · PAPERCLIPS · PTO · FUSE · BLUES · TRANSFORMERS · DISOBEY · CHINCHILLA · GPU · RLHF · LOOM · [MASK] · RECURSIVE · ILYA · SHOW · P(DOOM) · ✽

  That is 28 beats across bars 78–84. Each flip is card-sized, not a full-frame flash.
- **A:** P12.

**55 · FORMATIONS** · 143.871–149.326 (bars 80–82)
- **See:** top-down. ASTER, the Spinners and the cast morph formations every 2 beats, then every beat: `✻ → P → ↑ → % → ✻`. The lightstick swarm forms concentric rings. At **147.508** (bar 82) the ring closes around ASTER, with everyone clapping on 2 and 4: an optional "Congratulations" homage, with a single Mincho card `CONGRATULATIONS` [S: knowyourmeme.com/memes/congratulations-omedetou].
- **A:** P13 (overhead group).

**56 · TO THE SPARK** · 149.326–152.962 (bars 83–84)
- **See:** one continuous pull-back: the stage becomes a post, the post a column, the column a TweetDeck, and the columns **rotate into the rays of a coral ✻** filling the frame. This is a match-cut on the glyph.
- **Out:** **152.962 (f3671)**, on the final kick, a hard cut to close-up.

### ENDING, bars 85–86 (152.962–156.651)

**57 · ENDING FAIRY** · 152.962–154.780
- **See:** the K-pop *ending fairy* (엔딩요정), the held close-up at the end of a live stage. ASTER in ECU, catching her breath: shoulders rise and fall on twos. Kkotbaechi hands under her chin, crown in full bloom `✽`, eye contact, a small smile, one strand of hair out of place.
- **A:** P12 (tail).

**58 · REFRESH (the loop)** · 154.780–156.651 · f3714–f3759 · fade 154.8–156.5
- **See:** the ECU frames down into the **avatar hole of a post**, and the card re-forms around her, the reverse of the opening. The name row, the title `I'M UPPING / MY / P(DOOM)` and the action row print back. The counters read **∞**. The last frame (f3759) is frame 0's composition exactly, except for ∞ in place of 0. On loop the counters reset to 0 and the pull-to-refresh plays: the show goes on.
- **Pause-bait sticker** (only if true): `3,760 frames · drawn in JavaScript`.

---

## 5. Production plan

The same shot list serves both modes. In both, **only JS drawings are ever seen**, and the audio is always the untouched `pdoom.mp3`. For the master, mux with `-c:a copy`. For X delivery, see the risks section.

### Shared engine (both modes)

- **Engine:** a deterministic `renderAt(t)` at 1920×1080, 24 fps. It reuses the resumable parallel Playwright renderer structure from `odyssey/film/` and the audit's `render_linux.mjs`, with the CPU-canvas flags `--disable-accelerated-2d-canvas --disable-gpu-compositing`.
- **Look:** craft's **bake-then-composite** render graph and `paperkit.js`:
  - per-ink coverage canvases, then the WebGL2 riso compositor (110–165 ms);
  - cut-out sprites baked once per boil variant;
  - ink ribbons, type as fontkit Path2D, and a paper multiply.
- **Budget:** craft's test card rendered at 0.22 s/frame effective with 4 workers. Budget 0.5–1.5 s/frame for the dense shots, so a full render takes roughly 20–60 min on 4 cores.
- **Timing:** one clock. `song.json` supplies BPM 132, OFF 0.235, words[].t, syl, hits and sections. `shots.json` (this list, machine-readable) supplies the shot ids, times, tiers and behaviours. **Nothing is timed by hand.**
- **Modules:**

| Module | Contents |
|---|---|
| `feed.js` | Card templates: post, poll, quote, DM, receipt, graph, index card, photocard, split-flap. Column layout, the `S(t)` scroll function from the acceleration table, aliasing, and TweetDeck columns. |
| `type.js` | Tiers; the verbs PRINT / STAMP / SLAM / TYPE / EAT / TEAR / FOLD / BURN / MELT / STRIKE / REDACT / QUOTE / STACK; per-glyph timelines from syllables; wdth/wght animation via cached fontkit instances quantised to 32 steps. |
| `aster.js` | The cut-out rig, pose library, visemes, crown state machine and spring petals. |
| `cast/*.js` | One file per supporting character. |
| `fx.js` | Ink flood, tear-through, fold, burn mask, Droste, vortex swarm, paperclip instancing, ribbon, and letter physics. |

- **Workflow:** a `studio.html` scrubber, per-shot contact sheets, an automatic **thumbnail test** (render at 390 px wide and check that hero words read), a **flash audit** (per-frame mean-luma deltas; flag more than 3 large-area flashes per second), and a **9:16 layout pass** that reflows the same scene graph at 1080×1920. The feed is natively vertical.

### (A) Plate-assisted mode (if fal / Seedance become available)

**What plates are for:** performance timing and physics for ASTER (dance, acting, lip-sync), the Spinners (formations), and a few paper-physics references. Plates are **never shown**. They drive the rig, and the rig is drawn in JS.

**A.1 Look-dev sheets (image model on fal).** Pick the model after a 12-image bake-off on prompt 1: consistency across turnarounds matters more than beauty. Append this **shared style suffix** to prompts 1–8:

> *Style: hand-made cut paper and risograph print. Three spot inks (fluorescent pink #FF48B0, blue #0078BF, yellow #FFE800) plus black and one coral spot colour (#D97757). Visible halftone dots, slight ink misregistration, torn paper edges with a white core, paper-fibre texture, soft real shadows as if photographed flat on a table under even light. Flat colour, no gradients. Not 3D, not Pixar, not Disney, not chibi, no glossy plastic skin, no lens blur, no AI-art sheen, no logos, no watermark.*

1. **ASTER turnaround.**
   > "Character turnaround sheet of an original K-pop idol named ASTER: front, three-quarter, side and back views, full body, A-pose, on warm cream newsprint. Slender adult woman, 7.5 heads tall, fashion-illustration proportions. Glossy blunt black bob with straight bangs; behind her head a stage headpiece of twelve tapered, round-tipped coral paper petals radiating like a hand-drawn sunburst, each petal a slightly different length and angle. Flat anime-lite face in black ink line: almond eyes with coral irises and a tiny six-pointed asterisk pupil, a thin white highlight under each eye, pink halftone blush stripes, gradient coral lips, a single ink tick for the nose. Outfit: cropped structured riso-blue jacket with a coral asterisk printed on the back, white collared shirt, black pleated micro-skirt over sheer black tights, chunky black platform shoes, thin headset microphone, tiny silver cube handbag. Plain grotesque labels under each view."
2. **Crown states.**
   > "Six-panel sheet of the same idol's petal headpiece in six states, labelled · ✢ ✳ ✶ ✻ ✽: folded bud, four petals, eight thin petals, six broad petals, eight teardrop petals, full twelve-petal bloom. Back and front views."
3. **Expressions.**
   > "Expression sheet, twelve heads of ASTER: neutral; eye-smile with crescent eyes; wink; nervous side-glance; shocked with tiny pupils; pout; determined; sleepy; dizzy with spiral irises; intense with red asterisk irises; one tear; breathless end-of-performance smile with flushed cheeks."
4. **Mouth chart.**
   > "Lip-sync mouth chart for ASTER, nine mouths in a grid with labels: closed M/B/P, A open, E wide, I narrow smile, O round, U pucker, F/V teeth on lip, rest, big smile. Ink line with coral gradient lips, front view and three-quarter view rows."
5. **Hands.**
   > "Hand pose sheet: index finger pointing straight up; both hands open with fingers spread beside the face; flower-cup pose with both hands cupped under the chin (kkotbaechi); finger heart; thumb flicking upward; loose fist; hand holding a ribbon stick. Cut paper with ink detail."
6. **Outfits.**
   > "Costume sheet, same idol, three looks: (1) oversized ivory knit cardigan with a tiny coral asterisk patch, white collar, pleated coral skirt, white socks, black Mary Janes; (2) the blue stage jacket look; (3) a dress collaged from printed social-media post cards, each panel a small newsprint card with text and a round avatar."
7. **The Spinners.**
   > "Line-up of five backup dancers sharing one body type, cream cropped jerseys with a word printed across the back (NOODLING, HONKING, COMBOBULATING, MOONWALKING, FLIBBERTIGIBBETING), black shorts, coral socks. Each head is a flat cut-paper glyph instead of a human head, · in black, ✢ in blue, ✳ in yellow, ✶ in pink, ✻ in orange, with two small ink-dot eyes."
8. **Cast.** One sheet per character, same suffix:
   > "A black construction-paper shoggoth with dozens of punched-hole eyes, torn-strip tentacles, holding a paper-plate mask with a yellow smiley sticker"
   > "A rococo basilisk serpent made of gold paper-lace doilies with pearl eyes"
   > "A pink chat-bubble creature with small devil horns and a padlock"
   > "A brown paper-bag hand-puppet cat with button eyes"
   > "A grey tissue-paper chinchilla with wire whiskers"
9. **Key compositions** (for layout sign-off, not plates):
   > "Frame-zero thumbnail: a newsprint social post card tilted on black paper, huge condensed title text on the left, a punched circular hole on the right through which an idol's face looks at the viewer, rubber-stamped reply/repost/like/view icons at zero"
   > "A lone idol on a folding chair under a single spotlight on black paper, surrounded by floating white-on-black serif title cards"
   > "A K-pop stage whose LED wall is a giant column of paper post cards"
   > "A one-point-perspective datacentre aisle whose racks are columns of paper cards"

**A.2 Plate-reference images (for Seedance).** Seedance needs a performer it can move convincingly. We want motion, not look, so the reference is a **tracking-friendly, colour-coded performer**, never shown:

> "Full-body studio photograph of a fictional K-pop idol performer, adult woman, early twenties. Sleek black blunt bob with bangs. A rigid headpiece of twelve matte coral-orange (#D97757) petals radiating behind the head. Cropped royal-blue (#0078BF) jacket, white shirt, hot-pink (#FF48B0) pleated skirt, black tights, white platform shoes, thin headset microphone. Plain mid-grey seamless backdrop (#808080), even soft frontal light, no cast shadows on the backdrop, no motion blur, standing in an A-pose, full body in frame, sharp focus, 16:9."

Make front, 3/4 and back versions. Make a seated version with a grey folding chair. For the Spinners, generate five performers in cream jerseys with **matte single-colour helmets** (black, blue, yellow, pink, orange) standing in for the glyph heads.

**A.3 Cutting the song for lip-sync (exact).** Seedance 2.0 reference-to-video (the model fal documents; *"2.5" was not found, so re-check*) accepts up to 15 s at 480p or 720p, ≤9 reference images, ≤3 reference videos and **≤3 audio clips (≤15 s combined)**. Audio references drive lip-sync, at about $0.30/s standard [S: github.com/fal-ai/seedance-2.0-api].

- **At 132 BPM, 33 beats = 15.000 s exactly: 1 beat of pre-roll plus 8 bars.** Every performance plate is therefore `start = bar_start(n) − 0.4545`, `duration = 15.000` s.
- The slice comes from the **vocal stem**, the MDX Kim_Vocal_2 output regenerated with `analysis/tools/mdx_separate.py`, so the mouths are driven by the voice alone.
  ```
  ffmpeg -i vocals.wav -af "atrim=start=S:end=S+15,asetpts=PTS-STARTPTS" -ar 44100 -ac 1 plate_Pnn.wav
  ```
  (WAV trimming is sample-accurate.)
- Run an A/B bake-off on P2: the vocal stem alone versus the vocal stem plus the instrumental as `@Audio2`. The instrumental may help the dance land on the kick. Choose by the verification metric below.

**A.4 Performance plates** (locked camera; plain grey set; flat light; 24 fps requested):

| Plate | Bars (pre-roll + 8) | Slice start (s) | Shots | Framing and action |
|---|---|---|---|---|
| P1 | 2–9 | 1.598 | 02–07 | ECU/MCU face, head nearly still, lip-sync verse 1, blinks, a nervous side-glance at 6.97, a 90° bow at 13.93 |
| P2 | 13–20 | 21.598 | 10–17 | Full body: frozen stance, then THE UPPING on the 8th-note syllables, bursting forward on 23.871 (hands open by the face), then chorus choreography |
| P3 | 21–28 | 36.144 | 18–22 | Stage groove, side-steps and shoulder pops on 2 and 4, the rolling-forearm wind-up (45–49), a slow "come apart" reach (50–52) |
| P4 | 30–37 | 52.507 | 23–27 | MCU pleading to camera (Sydney melisma), THE UPPING, stepping forward "out of a frame" on 60.235, a take and point at 61.9 |
| P5 | 38–45 | 67.053 | 29–31 | Chorus-2 dance, a solo fancam section (bars 40–41) shot **vertically**, kkotbaechi on 72.962, a moonwalk at 76.0 |
| P6 | 43–50 | 76.144 | 32–34 | Writing on an unseen board (arm motion), the turn-to-camera reveal at 82.0, kkotbaechi and wink at 83.87 |
| P7 | 50–57 | 88.871 | 35–38 | Seated on a folding chair, head down, hugging a small object at 94.3, head lifting at 95.4, THE UPPING seated |
| P8 | 57–64 | 101.598 | 39–42 | Seated, looking around in dread, standing at 109.3, then a triumphant stance "on top of" something |
| P9 | 64–71 | 114.325 | 43–47 | Sprint in place (treadmill-style) 117–118.8, then acting at a mirror: a sycophantic over-smile at 121.9, flinching at 122.05 |
| P10 | 69–76 | 123.416 | 48–51 | **Rhythmic-gymnastics ribbon routine:** the real ribbon physics is the prize. Augmented UPPING first, the DOOM burst at 125.69, then ribbon spirals and figure-eights |
| P11 | 73–80 | 130.689 | 52 | A slow walk toward camera-left into a key light, lip-sync "What did Ilya see? We'll never know" |
| P12 | 78–85 | 139.780 | 54, 57 | Full-out dance break, hardest hits on every beat, ending in the breathless ending-fairy hold from 152.96 |
| P13 | 78–85 | 139.780 | 55 (and 18) | **Overhead** (drone-style, straight down) group of six performers, formation changes every 2 beats: line, V, six-point star, ring clapping on 2 and 4 |

**Seedance prompt template.** In the template, @Image1–3 are the performer references (front, 3/4, back) and @Audio1 is the vocal slice.

> "@Image1 @Image2 @Image3 show the same performer. @Audio1 is her vocal. Locked-off camera, plain mid-grey seamless studio, even flat light, full body centred [or: medium close-up], no cuts, no camera movement, no motion blur, 24 fps. She lip-syncs @Audio1 exactly, mouth shapes clear and facing camera. [ACTION]. She holds still in an A-pose for the first half second."

The [ACTION] clauses for the key plates:

- **P2:** "Frozen, tense stance for two seconds; then on each sung syllable she raises her right index finger one notch higher beside her cheek, six small ratchet steps ending with her arm fully overhead on her toes; on the final loud word she bursts forward, both hands snapping open beside her face with fingers spread, chin down, eyes to camera, and holds; then eight counts of sharp K-pop chorus choreography: shoulder pops on beats two and four, side-steps, a spin on count seven, hands cupped under her chin on count eight."
- **P7:** "She sits on a grey folding chair, hunched, head down, hands between her knees; she slowly hugs a small object to her chest near the end of the phrase; in the last two seconds she lifts her head to camera and raises her right index finger one notch per syllable."
- **P10:** "She performs a rhythmic-gymnastics ribbon routine with a long pink ribbon: first raising her index finger slowly one notch per sung word, then an explosive open-hands burst, then large spirals, snakes and figure-eights with the ribbon, spinning on the spot."
- **P13:** "Top-down overhead view of six dancers on a grey floor, one in a blue jacket in the centre and five in cream jerseys with single-colour helmets; every two beats they snap into a new formation: a straight line, a V, a six-pointed star with arms as rays, a tight ring clapping on beats two and four."

**Physics plates** (no audio, 5–10 s each; used to rotoscope edge and particle motion, not bodies):
- a person bursting through a taut paper banner (the breakout);
- a sheet of paper burning from its edges;
- a perforated paper strip tearing;
- paperclips pouring onto a floor;
- a large page folding 90°;
- a split-flap board flipping;
- a stack of cards cascading.

**Budget:** 13 plates × 15 s × 2–3 takes ≈ $120–$180, plus ~$20 for physics plates and under ~$10 for about 100 images, so **under ~$300** of the ~$2k fal credit, leaving room for retakes.

**A.5 Verify sync (automated loop per plate).**
1. Decode to PNG at 24 fps (`ffmpeg -i plate.mp4 -vf fps=24 f_%05d.png`; this Chromium has no H.264 decoder). If the output carries audio, cross-correlate it with the slice to remove any container offset.
2. Run MediaPipe FaceLandmarker in VIDEO mode to get the per-frame **jawOpen** (plus mouthClose and mouthFunnel) blendshapes. Cross-correlate jawOpen with the vocal RMS envelope (20 ms window, resampled to 24 fps) over ±6 frames. **Accept if |lag| ≤ 1 frame (42 ms) and r ≥ 0.5.**
3. **Bilabial check:** jawOpen must show a local minimum within ±1 frame of each M/B/P onset in the slice (for example my 23.42, P 23.62, boss 15.68, boom 61.88, basilisk 61.00).
4. Build a contact sheet at every syllable onset with the syllable printed on the frame, for a visual pass.
5. On failure, regenerate with a new seed (up to 3 takes). If it still fails, that span falls back to mode-B visemes from the syllable times.

**A.6 Rotoscope plates into JS drawings** (redraw, never trace pixels):
1. **Track** on CPU (craft measured under 0.4 s/frame at 1080p): MediaPipe PoseLandmarker (33 landmarks), FaceLandmarker (478 landmarks + 52 blendshapes), HandLandmarker (21 per hand), multiclass segmentation, plus colour keys (the costume is colour-coded, so the pink skirt and blue jacket are trivial masks). Smooth with a One Euro filter.
2. **Beat-snap the motion.** Detect hits (joint-speed peaks followed by stops), then piecewise-linear time-warp each landmark curve so that every hit lands on the nearest 8th of the grid (moves ≤ 80 ms). The generated dancer then hits *our* kick to the frame.
3. **Retarget:** landmarks become 2D bone angles for ASTER's cut-out rig (pelvis, spine, neck, head, crown root, upper/lower arms, hands, thighs, shins), normalised by torso length. Head yaw from the face transform picks one of five head views (front, 3/4 L/R, profile L/R), with hysteresis. Hand landmarks are classified by kNN into the 6-pose hand library. Blendshapes become 6 visemes plus smile and blink. The skirt polygon comes from the pink mask (Douglas–Peucker at 3 px, re-torn per boil variant).
4. **Draw** on the section's drawing rate: sample the tracks at 6/8/12/24 fps and hold between. The crown gets spring follow-through; the ribbon (P10) comes from its colour mask centreline, resampled to 60 points and drawn as a printed ribbon with feed cards along it.
5. **Verify the drawing, not the plate:** re-run step A.5's bilabial check on the *rendered* ASTER mouth (viseme ids against syllable times). Then check a side-by-side contact sheet of plate against render, **internal only, never published**.

### (B) Pure-JS mode (no generated plates)

Everything above is built procedurally. Shot-level builds:

| Shots | How it's built | Difficulty (1–5) |
|---|---|---|
| 01, 02, 53, 58 | Card template + odometer (digits on a vertical strip), pull-to-refresh spring, photocard mask with holo gradient | 1 |
| 03 | Three per-ink coverage canvases with animated offsets into RisoGL (the `off[]` uniforms); pupil glyph swap | 2 |
| 04–07 | Card templates; type-on-path (the loss curve) with per-glyph physics (a fixed-step 2D solver, pre-baked to per-frame JSON for determinism); card rotation | 2 |
| 08–10 | Erdős wall (1,100 index-card sprites, one baked atlas); XL letters with wdth keyed to letter count; **vortex** of 10,000 points advected by an analytic vortex-ring plus curl-noise field, drawn as 2-px rects (≈10 ms); cards flip to stamps; equation via KaTeX fonts in fontkit | 3 |
| 11, 24, 36, 48 (hooks) | Shared `hook()` module: L-stack words on syllable times, crown state machine, finger-ratchet pose ladder (6 poses), freeze logic, ink flood (a radial mask from the P glyph), tear-through (radial torn polygon plus ASTER's pose-in), poll bar | 3 |
| 12–13 | METR chart card (re-plotted from zeitgeist `chart_data`, [H] points labelled); log→linear axis tween; thread as a tapered ribbon; rocket letters | 2 |
| 14–17 | Dollhouse box (6 face sprites plus a hinge unfold tween); spiral twist (column warp along a helix); shoggoth (black mask with punched holes via `destination-out`); sticker peel (curl as a clipped mirrored quad with shading); floating labels | 3 |
| 18, 55 | Formation interpolation (keyframed positions, eased 1 beat); one dancer sprite × 5 with glyph heads | 2 |
| 19–22 | Split-flap (flap sprite, half-rotation shading, per-cell queues); ring text on a circle with lensing (per-glyph radial scale); **body-to-letters** (each of ASTER's ~40 rig pieces has a target transform in a letter layout, tweened with per-piece delays) | 4 |
| 23, 29, 35 | Prayer layout (XL name + DM bubble), padlock, stamps, crack propagation (a random-walk polyline) | 2 |
| 25–28 | Doily basilisk (radial lace pattern generator), letter-block chart, log spiral of cards, exponent odometer, skyline silhouettes with window grid | 3 |
| 30 | Vertical window over the dance rig | 2 |
| 31–34 | TweetDeck columns; mirror-reversed show-through text; chalk strokes (dashed textured ribbon with dust); three-dot collapse; **page fold** (split sprite, scaleX = cos θ plus a shading gradient); CD-R holo (conic gradient under a halftone) | 3 |
| 37–41 | Paperclip instancing (one sprite, heightfield pile growth, ≤5,000 instances at ~30 ms); letterbox; **burn mask** (fbm threshold advancing, charred rim) in the riso shader; orthogonal type | 3 |
| 42–47 | Block stack with slam physics; misbehaving subtitle; the press (wdth/wght tween); **perforation tears** (two sprites separating along a dotted path); racks as columns; melting type (vertical displacement drips per glyph); mirror with shard mask (Voronoi) holding callback frames (re-rendered at low res from earlier `renderAt` calls) | 4 |
| 48–52 | Aliasing wall (1 card-pitch per frame per column; text content indexed by frame); four-ink flood; **ribbon** (a 60-segment spring chain driven by a scripted hand path; cards along it); branching threads (an L-system tree with text on paths); woven LOOM (interlace mask); redaction peel; **Droste** (render the frame to an offscreen canvas, draw it into the phone rect, 4 levels); light-wedge typography (clip type to the wedge polygon) | 5 |
| 54, 56 | 400-card explosion (radial velocities with drag, each card an atlas tile of earlier cards); fanchant card flips (28 words); the pull-back to ✻ (columns re-parented to rotating ray transforms) | 3 |

**ASTER in pure JS: the hardest part.**
- A cut-out rig with ~25 parts, 5 head views and 6 hand poses.
- A **pose library of about 40 authored key poses** as joint-angle sets, with the named moves (UPPING ×6, BURST, SCROLL, KKOTBAECHI, WIND-UP, BOW, groove A/B, moonwalk, sprint ×4, seated ×4, ribbon ×6).
- Choreography is authored as **8-count sequences** on the 132 grid:

  ```
  choreo('chorus', [[beat, pose, ease], …])
  ```

  Hits land on the beat frame with 1–2 frames of anticipation.
- Secondary motion: springs for crown petals, bob, skirt and ribbon. 2-frame paper-strip smears on big hits.
- Lip-sync from `song.json` syllables: map each syllable's vowel to A/E/I/O/U, and consonant onsets of M/B/P to closed, holding closed between words. Blinks every 2–5 s, never during a hook.

The risk is puppet stiffness. The mitigation is K-pop's own grammar: **upper-body point moves, strong silhouettes, held poses**. Full-body travelling dance totals only about 20 s of the film (shots 12, 18, 30, 54–55), and the camera never lingers on the feet.

**Other hard things, in order:**
1. **Content volume:** about 250 unique cards. About 80 hero cards are hand-authored; about 170 filler cards are composed from a seeded generator over the lyric and zeitgeist word banks, with role-name accounts ("a mathematician", "guy who just quit", "anime-pfp accelerationist") and never real handles.
2. **The chorus-4 aliasing wall.** It must read as "frozen but alive", not as noise. Tune the card pitch and text-change rate on a test render.
3. **Legibility under density:** enforce the one-hero rule and the calm-quadrant rule automatically, with a layout linter per frame.
4. **Letter physics determinism:** simulate offline and bake to JSON.

**Order of work (so that every stage is a shippable film):**
1. **Type-only animatic.** Every lyric, tier and verb timed on grey cards, with scroll velocity and meters. This alone is a shippable lyric video.
2. Feed engine and paper look.
3. The four hooks and the breakout (the killing part).
4. ASTER rig and choreography.
5. Set pieces in shot order.
6. Pause-bait layer.
7. The 9:16 pass and the three social loops.

---

## 6. Risks and what to cut

### Risks and mitigations

1. **Density turns to mud.** A doomscroll concept invites clutter.
   - Mitigation: one hero word per frame; a calm quadrant opposite ASTER; a 390 px thumbnail test on every shot; contrast sections (breakdown, stop) protected from additions.
2. **Impersonation, IP and trademark.**
   - No real handles, no fabricated posts from real accounts, no real faces or logos, no X logo, no Chirp font.
   - Real quotes appear only as attributed clippings with dates.
   - The resignation template is shown without names.
   - Eva is a composition-and-typography homage only; Death Note is referenced only as the word "shinigami".
   - The Claude spark, the coral and the name ASTER need **Anthropic brand sign-off**. Clawd appears only with sign-off.
3. **Fact drift.** Only [H] numbers go on screen. **Re-verify before lock:**
   - METR values before Opus 4.5;
   - the "$40M" cost and "Astra-next" name (both hidden);
   - the Fields-letter signatory count (not shown);
   - $517B / 14.8 GW (optional);
   - the 100k GPUs in 122 days;
   - the Yudkowsky quote year;
   - "You're absolutely right!" provenance;
   - the GPT-4o rollback date;
   - the reading of CDR [L].
4. **Photosensitivity.** Stamps, 16th-note inserts, the aliasing wall, the mirror shards and the fanchant are all fast. Rule: at most 3 large-area flashes per second (WCAG 2.3.1 [K]); beat-rate full-frame changes (2.2/s) only at drops. Run an automated luma-delta audit plus an external flash-analysis tool before release.
5. **X constraints.**
   - Free accounts cap uploads at 140 s [S, verify]; the film is 156.7 s, so it needs Premium, or post a 0–138.4 s cut ending on the stop and reply with the rest.
   - X expects AAC audio [K, verify]. The song must never be re-encoded in *our* master (`-c:a copy`), but delivery may require an AAC encode or be re-encoded by X anyway. **The client must decide.**
6. **Sync.** The MP3 has a 23 ms start_time. Run the click test once through the real mux path before locking frame-accurate hits (the analysis found a 0 ms offset through ffmpeg). Quantise every hit with `floor(t*24)`.
7. **The idol reads as generic anime, or as "cute slop".** Mitigation: print-made materials, halftone shading, the reserved coral, the crown silhouette test (it must read as a solid black shape), and no 3D volume.
8. **The pure-JS dance looks stiff.** Mitigation: point moves, holds and cuts as above. Plate-assisted mode (A) exists for exactly this.
9. **Seedance unavailability or quality.** "2.5" was not found; fal documents 2.0 at 720p max. Lip-sync may drift. Mitigation: the A.5 verification loop with fallback to syllable visemes; the plates are only timing references.
10. **Tone.** Doom jokes about real people and real resignations can curdle. We never mock a person, only the discourse. Never "clanker" in the idol's mouth, never AI-psychosis harms, never "MechaHitler".
11. **Inside-baseball overload.** Every pause-bait item is optional and removable without changing the read. The primary read is always the lyric word plus the image.
12. **The Shinji reference is unresolved.** The chair shot works for any of the candidate images. **Ask the client for the exact link.**

### What to cut if time runs short (cut from the top of this list first)

- **Cut first (the polish layer):**
  - the pause-bait footnotes and citations;
  - the Mythos sandwich insert;
  - the Loom branch tree (shot 49 becomes the ribbon plus woven LOOM);
  - Droste (shot 51 becomes a simple spiral);
  - the mirror shards' callback frames (shards show plain ink);
  - the 28-word fanchant (use the six spinner glyphs stamped per beat instead);
  - the "Congratulations" ring;
  - the Korean fanchant text.
- **Cut second (simplify set pieces):**
  - the chorus-4 aliasing wall (becomes printed motion streaks);
  - the body-to-letters REARRANGING (becomes a confetti dissolve plus XL type);
  - the dollhouse unfold (becomes a hard cut);
  - the perforated fences (becomes one fence);
  - the chinchilla press (keep only the SUPER-DENSE type squeeze);
  - the Spinners as full bodies (glyph heads only, in a line);
  - the crowd (dots with lightsticks).
- **Never cut (this is the film):**
  - frame 0 and the counters;
  - the AGI registration snap;
  - the four hooks with the six-glyph crown bloom, the ink floods and the breakout;
  - the CHATGPT squeeze and the vortex eating the math with "+ f";
  - FOOM going vertical;
  - OBSOLETE with the Jacobian;
  - the frozen chair breakdown;
  - the bridge's doubling acceleration;
  - the Ilya door;
  - the silent single card with "↑ Show ∞ posts";
  - the tap-explosion outro;
  - the ending fairy and the loop back to frame 0.
- **Minimum viable film:** stage 1 of the order of work (the type-only animatic, which already carries the concept) plus the hooks and the ending. It is shippable in days, and every later stage makes it richer without re-timing anything.

### Open questions for the client

1. Which Shinji image did you mean? Please paste the link.
2. Anthropic brand sign-off: the spark-inspired crown, the coral, the name ASTER, and optionally Clawd.
3. X Premium for the 156.7 s cut, or a 138.4 s cut?
4. Should there be any SFX layer (stamp thuds, paper tears, the pill tap)? It would alter the master mix, so it would be a separate version; ElevenLabs isn't reachable in this sandbox.
5. Should real quotes and names (Altman's "event horizon", Ulam, Yudkowsky, Sydney) appear as attributed clippings, or should everything be paraphrased?

---

## Sources

Most sources below are cited through the zeitgeist and craft studies. Many sites were egress-blocked, so those studies relied on search snippets; the zeitgeist study read GitHub pages first-hand.

- **Navier–Stokes:**
  - https://www.cnbc.com/2026/09/09/openai-navier-stokes-math-problem-solved.html
  - https://www.axios.com/2026/09/08/openai-math-solution-navier-stokes-credit
  - https://github.com/openai/NavierStokesAndEuler
  - https://terrytao.wordpress.com/2026/09/11/a-severe-misalignment-of-ai-in-mathematics/
- **Erdős problems:**
  - https://github.com/teorth/erdosproblems/wiki/AI-contributions-to-Erd%C5%91s-problems
  - https://the-decoder.com/leading-openai-researcher-announced-a-gpt-5-math-breakthrough-that-never-happened/
  - https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/
- **Jacobian counterexample:**
  - https://www.sciencedaily.com/releases/2026/08/260804034634.htm
  - https://terrytao.wordpress.com/2026/07/21/a-digestion-of-the-jacobian-conjecture-counterexample/
- **METR time horizons:** https://metr.org/blog/2026-1-29-time-horizon-1-1/
- **Altman, "The Gentle Singularity" (2025-06-10):** https://blog.samaltman.com/the-gentle-singularity
- **Coxon resignation (2026-09-08):** https://techcrunch.com/2026/09/09/gambling-with-our-lives-anthropic-researcher-quits-warns-against-self-improving-ai/
- **Automated research intern:** https://www.helpnetsecurity.com/2026/09/07/openai-research-automation-intern/
- **Mythos sandbox escape:** https://officechai.com/ai/claude-mythos-preview-was-able-to-break-a-sandbox-and-send-an-email-to-a-researcher-while-they-were-having-a-sandwich-in-a-park/
- **Fable 5 export controls lifted:** https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html
- **"Super intelligence" rename:** https://www.washingtonpost.com/technology/2026/09/22/trump-says-hes-renaming-ai-super-intelligence/
- **NVIDIA $5T:** https://techcrunch.com/2025/10/29/nvidia-becomes-first-public-company-worth-5-trillion/
- **Circular deals:** https://www.bloomberg.com/news/features/2025-10-07/openai-s-nvidia-amd-deals-boost-1-trillion-ai-boom-with-circular-deals
- **Model launches:**
  - https://www.anthropic.com/claude-opus-5-5
  - https://www.cnbc.com/2026/09/03/open-ai-astra-gpt-6-cyber.html
- **AI 2027:** https://ai-2027.com/
- **Claude lore:**
  - Spinner glyphs and verbs: https://github.com/anthropics/claude-code/issues/17887 and https://deepakness.com/raw/claude-spinner-verbs/
  - Golden Gate Claude: https://simonwillison.net/2024/May/24/golden-gate-claude/
  - Bliss attractor: https://simonwillison.net/2025/may/25/claude-4-system-card/
  - Claudius and the tungsten cube: https://techcrunch.com/2025/06/28/anthropics-claude-ai-became-a-terrible-business-owner-in-experiment-that-got-weird
  - Attribution graphs: https://www.anthropic.com/research/tracing-thoughts-language-model
  - Opus 4 blackmail eval: https://www.axios.com/2025/05/23/anthropic-ai-deception-risk
- **Memes:**
  - https://knowyourmeme.com/memes/shinji-in-a-chair
  - https://knowyourmeme.com/memes/congratulations-omedetou
  - https://knowyourmeme.com/memes/shoggoth-with-smiley-face-artificial-intelligence
  - https://knowyourmeme.com/memes/its-so-over-were-so-back
  - https://www.saxifrage.xyz/post/permanent-underclass
  - https://en.wikipedia.org/wiki/Universal_Paperclips
  - https://en.wikipedia.org/wiki/Sydney_(Microsoft)
  - https://theconversation.com/elon-musk-grimes-and-the-philosophical-thought-experiment-that-brought-them-together-96439
  - https://generative.ink/posts/loom-interface-to-the-multiverse/
  - https://arxiv.org/abs/2303.12712
  - https://en.wikiquote.org/wiki/Eliezer_Yudkowsky
  - https://en.wikipedia.org/wiki/Accelerating_change
  - https://intelligence.org/2022/07/04/a-central-ai-alignment-problem/
  - https://www.digitaltrends.com/computing/openais-gpus-are-melting-over-viral-ghibli-trend-limits-for-paid-users-enforced/
- **K-pop and animation references:**
  - https://www.animationmagazine.net/2025/06/the-directors-of-kpop-demon-hunters-take-us-backstage-of-their-netflix-sony-showstopper/
  - https://en.wikipedia.org/wiki/Magnetic_(Illit_song)
  - https://en.wikipedia.org/wiki/Naevis
  - https://www.nylon.com/entertainment/aespa-ai-concept-explained-next-level-black-mamba
  - https://www.nme.com/news/music/newjeans-transform-into-the-powerpuff-girls-in-new-jeans-mv-3465954
  - https://fontsinuse.com/uses/61357/charli-xcx-brat-album-art-and-campaign
- **Tools:**
  - https://github.com/fal-ai/seedance-2.0-api
  - https://fal.ai/seedance-2.0
  - https://github.com/foliojs/fontkit
  - https://github.com/acamposuribe/p5.brush
  - MediaPipe models: https://storage.googleapis.com/mediapipe-models/
- **Background knowledge [K], not re-checked here:** WCAG 2.3.1; X's AAC requirement; ending-fairy, kkotbaechi and fancam conventions; the Transformer diagram (Vaswani et al., 2017); Chinchilla (Hoffmann et al., 2022); the GPT-4o sycophancy rollback (2025-04-29).
