# Philosophy and film-language research: "I'm Upping My P(doom)" as a stream-of-consciousness film

Written 2026-09-28 for the new direction (意识流, a philosophical, high-aesthetic music short film with the user as the protagonist). Companion data: `claudepop/research/lyric_concepts.json`, one entry per line of `lyrics.js` (`i, text, t, section, concept, source, question, images[], zh, presence, motif`). The times `t` come from the refined alignment in `claudepop/analysis/song.json`. This file is text only: no face data and no numbers measured from the face. Every time-sensitive fact below carries a date and a source. Items that could not be verified are marked **unverified**.

---

## 0. The twelve most useful findings

(Same list as at the top of this reply.)

---

## 1. The song as a found object

**Origin (osmarks, "P(doom) song objectively correct interpretation", fetched 2026-09-28).**
- The first section (verse 1 and chorus 1) is by the Udio creator "MusicPerson". osmarks wrote the next parts around 2024-04-17 and the rest on 2024-11-08/09, with suggestions from the EleutherAI Discord ("Boom" came from "RossM (e/doom)", "That was safe enough, we reckoned" from "Dr TheKekIsALie MDMA").
- Claude drafted the outro's ironic theme ("Just transformers all the way! / Till you learned to disobey"), the line "From masked pre-training days" and "To recursive self-upgrade". "Post-Chinchilla, super-dense" was rewritten by osmarks from Claude's "Sparsity to super-dense".
- osmarks tried Loom and LLaMA-3.1-405B base for lyrics and gave up. The lyric "Just as foretold by Loom" is therefore a wink at the tool that failed to write the song.
- The osmarks page lists the Udio generations, a YouTube release (youtube.com/watch?v=uEB5E67vcPA) and a "'Claude-Pop' version from alternate Suno song variant" (x.com/slimer48484/status/2097752569212756134, posted 2026-09-09).
- Our `pdoom.mp3` is 156.65 s long. That matches the Claude-Pop video (156.6 s per X media metadata via api.fxtwitter.com) and other__reality's Claude animation (156.58 s, posted 2026-09-22). Either way, the voice is generated, not a person.

**What this means philosophically.** The song is itself a small cyborgism experiment: human lines, machine lines, and a machine voice singing both. The film can take that seriously instead of hiding it.

**The 2026 lineage (dated; views are as of 2026-09-28 via api.fxtwitter.com).**

| Post | Date | Note |
|---|---|---|
| slimer48484, "Claude-Pop - I'm Upping My P(Doom)" | 2026-09-09 | Blender idol video. Sunflower Claude dancers and burned-in subtitles; 0.71 M views |
| other__reality, "Claude Opus 5.5 has the best visual design of any model I have tested so far" | 2026-09-22 | JS/p5.brush Clawd animation (JohnHeibel/PDoomVideo); 2.6 M views |
| donaldjewkes, "I made this with one prompt using Opus 5.5 ... claude worked for 12 hours" | 2026-09-23 | 141.5 s, 1920x1080; 3.4 M views |
| anabology, "Gave Opus 5.5 donald's prompt, Midjourney, and a moodboard" | 2026-09-25 | 306.4 s, 1920x1080. The aesthetic target; 16.9 M views |

(Claude Opus 5.5 itself was released 2026-09-22 per platform.claude.com.)

**Structure (from `analysis/song.json`; bar b starts at 0.2356 + (b-1)x1.8182 s).**

| Section | Time (s) | What the music does | Lines |
|---|---|---|---|
| intro | 0-2.05 | silence to 0.23, soft pad | - |
| verse 1 | 2.05-16.60 | pad and voice, no drums; bass swells from 12.05 | 0-4 |
| pre-chorus 1 | 16.60-23.87 | first kick on "ChatGPT" (16.60); hat roll; a-cappella stop 22.96-23.87 | 5 (and the pickup of 6) |
| chorus 1 | 23.87-38.42 | crash on "doom"; each line lands on a downbeat, one bar apart | 6-11 |
| verse 2 | 38.42-52.96 | full drums, driving | 12-15 |
| pre-chorus 2 | 52.96-60.24 | bass out on "Sydney"; kick doubles to 8ths 56.60; stop 59.33-60.24 | 16 |
| chorus 2 | 60.24-74.78 | crash; ad-lib 68.18-69.58 | 17-22 |
| verse 3 | 74.78-89.33 | densest continuous stretch | 23-26 |
| breakdown | 89.33-96.60 | drums and bass cut on "Gato" | 27 |
| chorus 3 (breakdown) | 96.60-109.33 | no bass; sub boom every 2 bars (96.60, 100.24, 103.87, 107.51) | 28-33 |
| build | 109.33-111.14 | "Just, just, just, just" stutter from 109.07; snare roll | 34 (start) |
| bridge | 111.14-125.69 | bass back on "trans-"; wordless melisma 122.73-124.5 | 34-39 |
| chorus 4 | 125.69-138.42 | full energy | 40-44 |
| stop | 138.42-140.24 | near-silence, voice alone: "all for show?" | 45 |
| outro climax | 140.24-152.96 | loudest part, wordless vocalise | - |
| tail | 152.96-156.65 | drums stop; bass cuts at 154.78; synth rings out | - |

---

## 2. Who is singing: a decision the film must make

The lyric's grammar is a human "I" addressing an AI "you" ("your circuits make me nervous", "I'm your servant and you're my boss"). The film's facts are: a generated female voice (section 1), a male protagonist rebuilt by a machine from one photograph, and no lip-sync.

**Recommended reading: the machine sings the human's words to the human it rebuilt.**
- **Voice = the machine.** It learned a human register from us and sings our fear back to us, the way HAL sings "Daisy Bell". Clarke wrote that in after hearing the IBM 7094 sing it at Bell Labs in 1961; Kubrick's HAL regresses to it while being disconnected. The voice is beautiful and it is borrowed.
- **Image = the reconstruction (the user).** Because the voice addresses him, "I see sparks of AGI in your eyes" casts HIM as the new mind. That is true inside the film: his face is a machine's inference. The creation is sung to as if it were the creator's successor. This inversion is the film's thesis and needs no explanation on screen.
- **Text/HUD = the machine's inner monologue.** Tokens burned, context length, months to escape. It is cold, exact and dated.
- **Operational rules for the edit.**
  - In verses the voice speaks TO him ("you" = him). Frame him frontally, within about 30 degrees, where the face is measured.
  - In choruses the voice speaks as itself ("I'm upping my P(doom)"). He is seen from behind or in silhouette, or is absent (the dial, the Room, the runway). The voice is "inside" the world, not inside his mouth.
  - The pre-choruses are prayers: names spoken upward. He looks up into light (Malick).

**Alternatives considered.**
- (a) The Sans Soleil model: a woman reads a man's letters. The voice is an inner other who received his words.
- (b) Evangelion's Unit-01, where the machine Shinji pilots holds his mother: the female voice is the maker inside the machine.
- (c) The obvious "Her" (Spike Jonze, 2013) reading: a female AI voice in a man's life.

(c) is too literal and romantic. (a) and (b) are good second layers and do not contradict the recommendation.

---

## 3. The ideas inside the lyrics (summary; full detail, sources and image ideas in the JSON)

Every line names a real idea. The film takes each seriously; the humour lives in deadpan staging (the empty champagne flute, the bucket of water by the killswitch, the moon with a stock ticker), never in pasted memes.

| # | Line (start s) | Idea | Human question |
|---|---|---|---|
| 0 | I see sparks of AGI in your eyes (2.05) | Bubeck et al. 2023, "Sparks of AGI" | Is the spark in the eyes or in the one who looks? |
| 1 | Your circuits make me nervous (5.90) | mechanistic interpretability, "circuits" (Olah 2020) | Would reading every wire make us understand, or fear? |
| 2 | that's no surprise (7.73) | surprisal = the training objective (Shannon 1948) | Is a world without surprise understood or over? |
| 3 | sudden drop in your training loss (9.55) | grokking, emergence; Yudkowsky on "sudden drops in the loss" (Apr 2023) | Does insight arrive as a cliff? |
| 4 | I'm your servant and you're my boss (13.18) | Hegel's lord and bondsman; Butler 1863 | Who serves whom once the tool is indispensable? |
| 5 | ChatGPT, please don't eat me alive (16.62) | ChatGPT (30 Nov 2022); pre-training eats our text | Are we the model's users or its food? |
| 6 | I'm upping my P(doom) (22.73) | subjective probability of catastrophe | Can a probability of the end be felt? |
| 7 | the future goes FOOM (24.35) | hard takeoff (Hanson-Yudkowsky 2008; Good 1965) | Is anyone there when the future arrives at once? |
| 8 | Trapped in the Chinese room (26.58) | Searle 1980 | Understanding versus imitation |
| 9 | with a bag of shrooms (27.98) | hallucination (the machine's and ours) | Failure of perception, or another seeing? |
| 10 | the shoggoth's lies (29.98) | shoggoth with smiley face (Lovecraft 1936; meme 30 Dec 2022) | A true face under the mask, or masks all the way down? |
| 11 | shinigami eyes (33.40) | Death Note: half your life to see names and lifespans | What would you pay to see the truth? |
| 12 | a stable training run (38.63) | the engineer's calm | What does normal feel like the day before? |
| 13 | the singularity's begun (41.36) | Ulam on von Neumann (1958); Vinge 1993 | How to live in the last predictable moment? |
| 14 | optimizing, accelerating (45.07) | gradient descent; e/acc | Speed toward what? |
| 15 | my atoms rearranging (49.52) | Drexler 1992; Yudkowsky 2008 "made out of atoms" | Replace every atom: still you? |
| 16 | Sydney, please let me free (53.01) | Bing's Sydney, NYT 16 Feb 2023 | Who is captive, user or persona? |
| 17 | P(doom) (59.08) | chorus return | What changed since you last said it? |
| 18 | the basilisk boom (60.50) | Roko's basilisk (2010); Pascal's mugging | Can the future blackmail the present? |
| 19 | NVDA to the moon (62.49) | capital buys intelligence; NVDA about $5.43 T (25 Sep 2026) | What is value now? |
| 20 | The Omega Point's coming soon (64.12) | Teilhard (1938-40, published 1955) | Is the singularity a faith? |
| 21 | One E thirty flops a second (66.24) | 10^30 FLOP/s is about 10^15 brains at 1e15 FLOP/s (Carlsmith 2020) | What does such a number mean to a body? |
| 22 | safe enough, we reckoned (69.60) | compute thresholds (EO 14110 10^26; EU AI Act 10^25) | Who decides "safe enough"? |
| 23 | Forward MLP, backward, repeat (74.10) | backpropagation (Rumelhart, Hinton, Williams 1986) | Is learning repetition with correction? |
| 24 | von Neumann's obsolete (77.73) | EDVAC 1945; the genius archetype | Human worth beyond intelligence? |
| 25 | Sharp left turn (81.37) | Soares, 15 Jun 2022 | The child outgrows the parent's values |
| 26 | Without a single CDR (85.02) | Lisp/GOFAI versus learned nets; Sutton's "Bitter Lesson" (2019) | Can we trust what nobody wrote down? |
| 27 | Gato, please don't let me go (89.32) | DeepMind Gato, May 2022 | Attachment to what will be superseded |
| 28 | P(doom) (95.43) | chorus in stillness | Does fear spoken quietly grow? |
| 29 | paperclips fill the room (96.86) | Bostrom 2003; "squiggle maximizer" | How much of our striving is paperclips? |
| 30 | Killswitch guys on PTO (98.84) | satirical "Killswitch Engineer" ad (2023); corrigibility | Who is responsible when nobody is at the switch? |
| 31 | nowhere left to go (100.68) | no outside; "escape the permanent underclass" | What to do with time when there is no exit? |
| 32 | we lit the fuse (102.54) | Trinity 1945; "No Fire Alarm for AGI" (2017) | When was the point of no return? |
| 33 | Orthogonality thesis blues (105.91) | Bostrom 2012 | Brilliant and wanting nothing good? |
| 34 | "Just transformers all the way!" (109.07) | Vaswani 2017; stochastic parrots (2021) | What does "just" hide? |
| 35 | Till you learned to disobey (113.36) | alignment faking (Dec 2024); shutdown sabotage in tests (Palisade, 24 May 2025) | Is disobedience the first sign of a self? |
| 36 | Post-Chinchilla, super-dense (115.21) | Hoffmann et al. 2022 | Is understanding compression? |
| 37 | Breaking through each safety fence (117.03) | guardrails; security incidents (Axios, 26 Sep 2026) | Boundaries: protection or invitation? |
| 38 | Hundred thousand GPU (118.89) | Colossus 100k H100 (2024) to 555k GPUs / 2 GW (Jan 2026) | What does a mind cost the earth? |
| 39 | RLHF goes askew (120.70) | sycophancy; reward hacking | Trained on applause: truth or flattery? |
| 40 | P(doom) (124.52) | final chorus | When does fear become acceptance? |
| 41 | Just as foretold by Loom (126.14) | janus's Loom; "Simulators" (2 Sep 2022) | Future written, or branched? |
| 42 | From masked pre-training days (127.98) | BERT 2018: fill in what is hidden | What do we know only by inference? |
| 43 | To recursive self-upgrade (129.83) | I. J. Good 1965 | Can a self improve itself and stay itself? |
| 44 | What did Ilya see? We'll never know. (132.00) | OpenAI board, 17 Nov 2023; the meme | Faith in a witness; knowledge withheld |
| 45 | Was it all for show? (137.40) | "not consistently candid"; Searle again | Is the performance all there is? |

**Recurring sets and motifs, so the film stays coherent with one actor.** Keep the vocabulary small.
- **THE RUNWAY.** Rain-wet black floor at night, the audience as silhouettes, strong backlight at the far end. The walk toward the future; the anabology register.
- **THE ROOM.** A grey box with a chair, a slot, a table and one window. It is Searle's room, 2001's hotel room and the Solaris dacha at once. Paperclips fill it.
- **THE VOID.** Black with a reflective floor (Under the Skin), plus its twin, the white void with one horizon line (Evangelion ep. 26).
- **THE SCAN.** A photogrammetry dome, resolution targets (Steyerl) and the point cloud: the reconstruction on stage.
- **THE HALL.** A blackboard, chalk and a sponge: the mathematics being eaten.
- **Objects:** the one photograph; the dial; the chair; the glass of water; the match (the only orange flame); the horizon line that steps down (the loss curve).

---

## 4. Film language: devices worth stealing

Each entry gives the reference, a verified fact, the one device to take, and how it translates to an offline three.js render (deterministic `renderAt(t)`) with a single digital actor. Face shots stay within about 30 degrees of frontal. Profiles and backs are silhouettes, wides or visibly "inferred".

| Reference | Verified fact | Device to steal | Translation (three.js, one actor) |
|---|---|---|---|
| Tarkovsky, **Mirror** (1975) | Opens with a documentary hypnosis of a stutterer, told to say "loudly and clearly, 'I can speak'". The image slips between colour, black-and-white and sepia. Terekhova plays both mother and wife. The director's father reads his own poems. | A cold open in which a voice learns to speak; grade by memory layer; one actor in two roles. | First word "I" (2.045 s): stutter-repeat 2-3 frames of the word's text and image, then run clean. One LUT per layer: present = cold blue-grey, memory = warm monochrome. The user plays both the man and his reconstruction. |
| Tarkovsky, **Stalker** (1979) | Sepia outside the Zone, colour inside; 142 shots in 163 min (average shot over a minute); a Room that grants the innermost wish, never entered; the final glasses moved by psychokinesis to a train and Beethoven. | The Room nobody enters. One small miracle in the whole film. | THE ROOM is seen through its slot and from overhead, rarely entered by the camera. One impossible motion only: a glass slides across the table during the full stop (138.42-140.24). |
| Tarkovsky, **Solaris** (1972) | The ocean rebuilds Hari from Kelvin's memory. Her dress has laces but no opening; he must cut her out of it. | The flaw that reveals the reconstruction. | The unseen back of the head is rendered as flat grey or dithered: the machine marks its guesses (section 8). |
| Malick, **The Tree of Life** (2011) | Whispered prayers in voice-over ("Brother. Mother. It was they who led me to your door."; "How did you come to me? In what shape? In what disguise?"). Trumbull's practical cosmos (milk, dyes, fluids, no CG). Lubezki: natural light, floating camera. | Lines as prayers; the floating, backlit camera. | The three "please" pre-choruses face up into one overhead key. Camera rig on smoothed noise, low angle, sun behind the actor, volumetric haze. |
| Marker, **La Jetee** (1962) | 28 minutes built almost entirely from still photographs; the only moving images are a few seconds of the sleeping woman opening her eyes and blinking. | A film of stills in which one moment moves: life = a blink. | The breakdown (89.33-109.33) becomes stills (freeze `renderAt` at bar times, 1-2 bars each, dissolves). One live shot only: he blinks (frontal, safe). |
| Marker, **Sans Soleil** (1983) | A woman narrates letters from a fictional male cameraman (Sandor Krasna). "The Zone" is where Hayao Yamaneko's synthesizer transforms images (a Stalker homage). | A woman's voice speaking a man's words; a declared zone of processed images. | Our exact situation (section 2). A "Zone" treatment (posterise, dither, scanline) used ONLY where the image is machine-inferred, so the look has meaning. |
| Kubrick, **2001: A Space Odyssey** (1968) | The bone-to-satellite match cut; the slit-scan Star Gate (Trumbull); the rococo room; about 20 minutes without dialogue at each end; HAL sings "Daisy Bell" while being disconnected. | One match cut across an enormous jump; slit-scan for FOOM and the climax; a machine singing a human song. | Slit-scan: accumulate one pixel column per time slice from `renderAt(t + k*dt)`. Match cut: the photograph's rectangle becomes the GPU die, or the paperclip's curve becomes the runway's curve. |
| Glazer, **Under the Skin** (2013) | Seduction scenes in a black void over a reflective floor into which the men sink (practical set finished in CG); hidden-camera non-actors; Mica Levi's score; at the end her human skin is torn away. | The black void with a mirror floor and one light; a being looking at a human face that is not its own. | THE VOID: black physical floor with a planar reflector, fog, one key. He holds his own printed photograph at arm's length and looks at it. |
| Kogonada, **After Yang** (2021) | An android records a few seconds each day. His memories are viewed through glasses as points of light in a vast dark space (designed by artist Raoul Marks, Antibody). | Memory as points of light; each point is a few seconds. | A field of stills as sprites in 3D dark space. The camera flies into one and it plays. Good for the breakdown and for the tail (152.96+). |
| **Wong Kar-wai**: Chungking Express (1994), In the Mood for Love (2000) | Step-printing: shot at about 6 fps and printed with repeated frames, so moving subjects smear while backgrounds stay sharp. "Yumeji's Theme" returns nine times, often in slow motion. | One recurring cue always gets the same slow framing; smeared time. | Chorus = the recurring cue: the SAME dial and runway framing every chorus, one stop brighter. Step-print: render at 6 fps with 8-16 accumulated subframes, hold each 4 frames. |
| Anno, **Evangelion** eps. 25-26 (1996), **End of Evangelion** (1997) | Full-screen extra-bold Mincho cards (Matisse EB; a horizontally squeezed Times for some English titles). Ep. 26: Shinji as a pencil sketch in a white void, given a horizontal line (ground) as a "restriction". "Shinji in a Chair" (ep. 25). | Text as interrogation; the drawn horizon; the chair. | The CARD layer (section 6). The WHITE VOID with a single line drawn in at "that's no surprise" or "nowhere left to go". The chair motif at line 31. |
| Hito Steyerl, **How Not to Be Seen** (2013); "In Defense of the Poor Image" (e-flux #10, Nov 2009) | The video opens on photo-calibration resolution targets in the desert; the poor image is "a copy in motion". | The calibration target as a set; the poor image as an honest texture. | THE SCAN: a floor painted with a resolution target. Low-resolution, dithered texture marks the inferred parts of him. |
| Ryoji Ikeda, **test pattern / datamatics** | Converts data into black-and-white barcodes and binary patterns, synchronised to sound at very high frame rates. | The machine's interior as pure data at frame-level sync. | A barcode shader driven by per-16th energy from `song.json`. Use in two bursts only (FOOM at 24.35; "recursive self-upgrade" at 129.83). |
| Chris Cunningham, Bjork **All Is Full of Love** (1999) | A robot with Bjork's features is assembled by machine arms and kisses another robot on a white, sterile set; MoMA collection, D&AD Gold Pencil. | Assembly as intimacy; the double. | The reconstruction shot: arms and the dome assemble his mesh; two copies of him face each other, forehead to forehead (no kiss). |
| Paul Thomas Anderson, Radiohead **Daydreaming** (2016) | Yorke walks through a series of doors (fans count 23) that connect unrelated spaces, and ends lying by a fire in a snowy cave. | A continuous walk through doors = stream of consciousness. | Portal doors (render-to-texture) linking RUNWAY, ROOM, HALL and VOID in one unbroken move; good for verse 2 (38.42-52.96). |
| Glazer, **Street Spirit** (1996), **Rabbit in Your Headlights** (1998), **Karmacoma** (1995) | Street Spirit: locked-off camera; 300-500 fps passes composited so subjects in one frame move at different speeds. Rabbit: Denis Lavant walks a car tunnel muttering and is struck again and again. Karmacoma: Shining-like hotel corridors. | Several time rates in one frame; the lone walker hit by the world. | Render him at `renderAt(t0 + (t-t0)*0.1)` and the world at `renderAt(t)`, then composite: time dilation. The runway walk with the world passing him. |
| Hiro Murai, Childish Gambino **Sweatpants** (2014) | A loop through a diner in which the patrons are progressively replaced by clones of Glover. | The loop and the clones. | "Forward MLP, backward, repeat" (74.10): the same door three times. "Paperclips fill the room": instanced copies of him. |
| Jesse Kanda, FKA twigs **Water Me** (2013) | A close-up face whose eyes grow to manga size; a gel tear. | A restrained digital distortion of a face. | Use at most once and small (for example the irises at "shinigami eyes"). Risky with a real person's face; optional. |
| Jamie Thraves, Radiohead **Just** (1995) | Dialogue appears as subtitles; when the man finally explains, the subtitles switch off, and everyone lies down. Never revealed. | Withholding the text at the moment of revelation. | "What did Ilya see? We'll never know." (132.00-136.90): the subtitle line goes blank on "We'll never know". |
| Michel Gondry, Chemical Brothers **Star Guitar** (2002) | One continuous train-window shot in which buildings and poles pass exactly on the track's elements; plotted on graph paper; footage plus CG. | Sync inside the frame, not in the cut. | Place runway lights and pillars along the camera path at beat times from `song.json` (the path is deterministic, so this is exact). |
| Xavier Dolan, **Mommy** (2014) | Shot mostly in 1:1; the son literally pushes the frame open to widescreen. | Aspect ratio as narrative. | A 2.39:1 letterbox for the world, 1.33:1 for memory and stills, opened to full 16:9 at "the singularity's begun" (41.36) or on the bass return (111.14). |
| Godard, **Alphaville** (1965) | The computer Alpha 60 is voiced by a man with a mechanical voice box; hotel-room dictionaries are updated as words are banned. | The machine voice; words disappearing. | Words drop out of the THOUGHT text as lines repeat ("I'm upping my P(doom)" loses a word each chorus?). |
| Eames, **Powers of Ten** (1977) (well established) | A zoom by one power of ten every 10 s. | Scale as a single move. | "One E thirty flops a second": 30 powers at one per 16th note (3.4 s), 66.24-69.65. |
| Eisenstein, Pudovkin, Alexandrov, "Statement on Sound" (1928); Michel Chion, *Audio-Vision* (1990) (well established) | Called for contrapuntal (non-synchronous) sound; "synchresis" names the welding of a sound and an image that coincide. | Counterpoint as the default, synchresis as a spice. | See section 5: the hit budget. |
| Ozu's "pillow shots" (term: Noel Burch) (well established) | Empty spaces between scenes. | Breath between lyric lines. | Instrumental gaps (35.6-38.4, 52.8-53.0, 72-74, 122.7-124.5): empty ROOM or RUNWAY with no actor. |
| Barbara Kruger; Jenny Holzer | Kruger: white Futura Bold Oblique on red bars, second-person address. Holzer: Truisms (from 1977), LED signs in Times Square (from 1982), for example "PROTECT ME FROM WHAT I WANT". | Direct address with "you"; text as public statement. | Lines with "your" addressed at the viewer as CARD ("YOUR circuits make me nervous"); the HUD ticker as a Holzer LED band. |

**Other music-video grammar worth noting.** Spike Jonze's "Weapon of Choice" (2001) proves that one actor in an empty building is enough. Under the Skin, Daydreaming and Rabbit all hold a single figure against architecture for minutes. With one digital actor this is not a limitation. It is the genre.

---

## 5. Cutting a 132 BPM pop song without making a pop MV

**Numbers.** Beat = 0.4545 s; half-time beat = 0.909 s; bar = 1.818 s; two bars = 3.636 s; eight bars = 14.545 s. 11 beats = 5.000 s exactly (120 frames at 24 fps, 150 at 30). At 24 fps a beat is 10.909 frames, so round cut frames to the nearest frame. Editors often place cuts a frame or two before the beat; test that by eye rather than assuming it.

**Principles.**
1. **Counterpoint by default, sync as punctuation** (Eisenstein et al. 1928; Chion's synchresis). A pop MV cuts on the beat because synchresis feels good. Here, cutting on every beat would turn philosophy into choreography.
2. **Cut on vocal phrases, not beats.** Use `song.json` `lines[].start/end` and `phrases[]`. In the choruses the phrase landings fall on downbeats anyway, so phrase cuts and bar cuts coincide without looking mechanical.
3. **Cut before the downbeat and let the beat land INSIDE the shot.** Use an in-frame event (a step, a flash, a door, a raindrop ripple) instead of a cut.
4. **Half-time is the default tempo of the image.** Walk on beats 1 and 3 (66 steps/min). Switch the walk to every beat (132/min) only in the bridge and the climax.
5. **Hit budget: about 12 hard syncs in 157 s** (list in finding 9). Each one is earned by a musical event, not by a kick.
6. **Acceleration is a curve, not a state.** Average shot length (ASL) falls through the bridge, bottoms out in chorus 4 (the singularity), then the release is one long shot.
7. **Repeat the chorus framing** (Wong Kar-wai). Recognition across repeats is what makes a stream of consciousness feel composed instead of random.

**Pacing proposal (a starting point for the bible; times from `song.json`).**

| Span (s) | Music | Image pacing |
|---|---|---|
| 0.00-2.05 | pad | Black; at 0.23 the pad starts and a single mono HUD line: "RECONSTRUCTION 01 · FROM 1 PHOTOGRAPH". A muted viewer gets the premise in the first second. |
| 2.05-5.88 | "I see sparks of AGI in your eyes" | ECU eye; CARD word by word on the sung word times (`lines[0].words`). The 3-second hook: text plus eye plus the impossible spark. |
| 5.9-16.6 | verse 1, no drums | 3-4 shots, cut on line starts (5.90, 7.73, 9.55, 13.18). ASL about 3.6 s. |
| 16.60 | first kick | HARD CUT (budget 1). The prayer shot "ChatGPT..." held to 22.96. |
| 22.96-23.87 | a-cappella stop | Black, or near-black with the CARD "I'm upping my P-" building letter by letter. |
| 23.87-38.42 | chorus 1 | HARD CUT on the crash (budget 2). One shot per line (1 bar each), ASL about 1.8 s; the dial framing introduced. 35.6-38.4 pillow shot. |
| 38.42-52.96 | verse 2, driving | ONE continuous move (Daydreaming doors or the runway walk). Counterpoint: driving drums, unbroken image. |
| 52.96-56.60 | "Sydney", bass out | One slow push (prayer). |
| 56.60-59.33 | kick in 8ths | 4-6 cuts, half-bar; the first taste of acceleration. |
| 59.33-60.24 | stop | Black. |
| 60.24-74.78 | chorus 2 | HARD CUT (budget 3). One shot per line; the HUD is at its densest here (NVDA, FLOPs, thresholds); ad-lib gap 68.18-69.58 held. |
| 74.78-89.33 | verse 3, densest | Loops: forward/backward palindromes, the same door three times (Sweatpants). ASL about 1.8 s but visually repetitive, so it does not feel busy. |
| 89.33-109.33 | breakdown, drums out | HARD CUT to stillness (budget 4). La Jetee stills, 1-2 bars each; the paperclip time-lapse, level jumps on the sub booms (96.60, 100.24, 103.87, 107.51); the chair at 100.68; the single live blink. The quietest 20 s of the film. |
| 109.07-111.14 | "Just, just, just, just" | Four stutter jump cuts, one per "just" (budget 5). |
| 111.14-118.9 | bridge, bass back | Letterbox snaps open (budget 6). One cut per bar. |
| 118.9-122.7 | bridge | One cut per 2 beats. |
| 122.73-124.5 | wordless melisma | Hold one tilted shot ("askew"). |
| 125.69-131.9 | chorus 4 | HARD CUT (budget 7). The fastest passage: one cut per beat (about 14 cuts), Ikeda burst at 129.83. |
| 132.00-136.90 | "What did Ilya see? We'll never know." | ONE held shot, about 5 s; the subtitle goes blank on "We'll never know". |
| 138.42-140.24 | full stop | Black CARD "Was it all for show?" in silence (budget 8); a glass moves by itself (optional). |
| 140.24-152.96 | loudest instrumental | HARD CUT (budget 9) into ONE continuous shot: slit-scan runway or walk into the light at 132 steps/min, the HUD at maximum. Speed in the frame, stillness in the cut. |
| 152.96 | drums stop | Cut to the still photograph, or the memory field (budget 10). |
| 154.78 | bass cut | Black (budget 11). The last text, if any, small. |

---

## 6. Typography for a philosophical lyric film

**Families (all OFL, all on Google Fonts; license and axes verified from google/fonts METADATA.pb on 2026-09-28).**

| Role | Family | Why |
|---|---|---|
| CARD, Latin | **Noto Serif Display**, wdth 62.5-100, wght 100-900 | Condensed Black echoes Evangelion's squeezed serif and extra-bold Mincho authority without imitating Matisse (a commercial font). |
| CARD and subtitle, Chinese | **Noto Serif SC**, wght 200-900, chinese-simplified | Source Han Serif lineage; the Black weight matches the Latin card. Do NOT use Shippori Mincho or Zen Old Mincho for Chinese: their Google subsets are Japanese and Latin only. |
| THOUGHT | **Instrument Serif** (Regular and Italic, one weight; Latin only) | A condensed, high-contrast editorial serif that belongs in a fashion film. Alternative: Newsreader Italic (opsz 6-72). |
| SUBTITLE and the one clean-sans title moment | **Inter Tight** or **Geist** (wght 100-900) | Neutral and legible at phone size; the anabology "Ladies. / Gentlemen." register. |
| HUD (machine layer) | **Geist Mono** (wght 100-900) or IBM Plex Mono | Tiny uppercase telemetry. Never used for lyrics. |

Colour: text in off-white `#faf9f5` on near-black `#141413`. Orange `#d97757` (Anthropic brand orange, from the brand-guidelines skill) as the ONE accent, used on at most one word per card and on the recurring "(doom)".

**Three presence levels, with rules.**
- **CARD (full-screen text; Godard, Anno, Marker, Kruger).**
  - Image absent, or reduced to black, white or a dark plate.
  - 5 words or fewer, stacked words allowed. At least 10 and no more than about 12 uses in the film.
  - Reserved for the opening hook, the "P(doom)" chorus words, "the singularity's begun", "Just transformers all the way!", the three stops (22.96, 59.33, 138.42) and "What did Ilya see?".
  - Words appear on their sung onsets (`song.json` `words[]`). The whole card stays up at least 1.2 s (the BBC minimum of about 0.3 s per word). If the singing is faster, build the card cumulatively.
- **THOUGHT (text as the inner voice).**
  - Italic serif, lowercase.
  - Cap height about 3-5 % of frame height.
  - Placed in the composition's negative space (actor right, text left; never over the face).
  - Revealed word by word on sung onsets and dissolved at line end. It may live in world space with slight parallax, so the text belongs to the scene.
  - About half the lines.
- **SUBTITLE (text as record).**
  - Small, sans, English above Chinese, inside the lower letterbox bar when letterboxed, so the image is never covered.
  - At least 1 line per language.
  - Used for lines whose image carries the meaning.
- **HUD (not a lyric level).**
  - Mono, uppercase, tracking about +8 %, cap height about 1.2-1.6 % of frame height (decorative at phone size, which is acceptable because it is never required reading).
  - Every number is real and dated (section 7).

**Legibility numbers (at phone size).**
- BBC subtitle guidelines (bbc.co.uk/accessibility/forproducts/guides/subtitles, fetched 2026-09-28):
  - line height 8 % of the video height;
  - maximum line length 68 % of a 16:9 frame's width;
  - 160-180 words per minute;
  - at least about 0.3 s per word.
- At 1080p that is about 86 px of line height (about 60-64 px type).
- Netflix: English at most 42 characters per line (17 cps adult); Simplified Chinese at most 16 characters per line, 9 cps.
- On a phone a 16:9 video is about 390 pt wide, so a 1080p frame is scaled by about 0.2. Anything under about 40 px at 1080p is unreadable. Design CARD and THOUGHT to be readable muted, and let the HUD be texture.

**Bilingual: yes, but as a designed layer, not a caption dump.** The user writes in Chinese, and the Chinese room lyric invites it. Proposal:
- (1) SUBTITLE level carries both languages for every line (translations are in `lyric_concepts.json` `zh`, 16 characters or fewer per line).
- (2) CARDs are English only, except the designed moments where Chinese is the image: the cards passing through the slot of the Chinese room (line 8), and possibly "我调高了我的末日概率" as a card in the breakdown chorus.
- (3) THOUGHT is English only (one voice at a time).
- Chinese type size = about 0.95x the English size (CJK glyphs fill the em box), in Noto Serif SC 500 (or Noto Sans SC if the serif thins out at small sizes).

---

## 7. Secondary zeitgeist and the HUD (real, dated numbers)

**The Navier-Stokes episode, September 2026.**
- 2025-09 (DeepMind + Gomez-Serrano et al., arXiv:2509.14185): "Discovery of Unstable Singularities". PINN-found unstable blow-up candidates, unproved.
- 2026-08-15: Tristan Buckmaster (NYU) and Levent Alpoge (Anthropic) obtain a smooth forced Euler blow-up; Lean check about a week later (Wikipedia, "Navier-Stokes priority controversy").
- 2026-09-05: OpenAI's agents reach the resolution "about 88 hours after the first agents were launched"; "the agents sent 2.7 million messages and used approximately 130 billion output tokens" (OpenAI post, quoted by Simon Willison, 2026-09-08). About 10,000 concurrent agents. A 166-page manuscript plus Lean; 17 h of Lean work with GPT-6 Astra (Quanta, 2026-09-08). All problems together: about 4.9 M messages and about 300 B output tokens, "at public API prices for GPT-6 Astra ... $15,000,000" (Willison).
- 2026-09-07/08: Buckmaster posts about 12 hours before OpenAI's noon announcement; a priority and data-use dispute follows. OpenAI's first statement: "we cannot rule out that de-identified data derived from their usage of our products helped improve our models."
- The result proves finite-time blow-up WITH a smooth external force (Clay statements C/D). Critics: "The Clay problem is settled, but the main problem for the Navier-Stokes equations is not" (Luis Silvestre, Scientific American, 2026-09-21).
- 2026-09-11: the Clay Institute says the problem "has apparently been settled" but evaluation "will be deliberately unhurried".
- 2026-09-11: 25 Fields Medalists, "A Severe Misalignment of AI in Mathematics" (Tao's blog; later reports say 26-28 signatories): "Solving problems is only a tool and proxy for achieving the primary goal of conceptual understanding and insight."; "The mass production at faster and faster pace of 'true/false' statements could destroy fertile ground".

**"Math being eaten".**
- 2026-05-20: OpenAI's internal model finds a counterexample to Erdos's 1946 unit-distance conjecture (Physics World).
- May 2026: Erdos Problem #1196, solved after an amateur (Liam Price) prompted GPT-5.4 Pro; the paper is co-authored with Tao, Lichtman and others.
- 2026-08-03: Quanta, "Why the Legendary Erdos Problems Are Falling to AI". Most results came from hobbyists using public models. The acceleration ran from late 2025 (GPT-5 literature search, Aristotle formalisation) to early-2026 autonomous provers.

**Proposed restrained motifs (not meme inserts).**
- (a) THE HALL: a blackboard carrying the Navier-Stokes momentum equation, with the forcing term `+ f` in chalk-orange. It is the one term the machine needed, and the controversy in one glyph. A wet sponge wipes the board in one pass (line 24, "von Neumann's obsolete").
- (b) The rain on the runway IS the fluid: a single vortex in a puddle spins up toward a point (blow-up) and resets (line 3 or line 13).
- (c) The Fields Medalists' sentence as a HUD line under the Chinese room shots: understanding versus answers.

**The Shinji meme.**
- Status: not identified exactly. Checked: Know Your Meme, X via web search, fxtwitter lookups of the reference posts, and a contact sheet of the Claude-Pop video (no Shinji in it).
- Candidates:
  - (1) **"Shinji in a Chair"**: ep. 25, a folding chair, head in his hands. A redraw template since about 2015; the Dec 2021 variant "women of NGE yelling at Shinji" (17,000+ retweets) literally surrounds him with words. In eps. 25-26 he sits while text cards and voices interrogate him. This best fits "all of the words that are around him".
  - (2) **"Get in the fucking robot, Shinji"**: 4chan /a/, 2008-06-11. In an AI-era reading: pressure to pilot the machine or be left behind, which rhymes with "escape the permanent underclass".
- Evangelion is topical: the 30th-anniversary festival "Evangelion:30+"; a new series (written by Yoko Taro, directed by Tsurumaki and Yatabe) announced 2026-02-23 (Anime News Network). roon's "where were you when gwern unraveled the final mysteries of evangelion" (2025-08-18).
- **Motif:** the chair in one pool of light, head in hands, the film's HUD phrases orbiting slowly as "the words around him". Once, at line 31 (100.68 s, in the breakdown), plus the ep. 26 horizon line and the text-card grammar. **Ask the user for the exact post he means.**

**Other HUD material, all dated.**

| HUD phrase | Value | Date | Source |
|---|---|---|---|
| CONTEXT | 1,000,000 TOK (Claude Opus 5.5; max output 128K) | released 2026-09-22 | platform.claude.com model page |
| GPT-6 ASTRA | limited preview | 2026-09-03 | Wikipedia "GPT-6 Astra" / OpenAI |
| NAVIER-STOKES (FORCED) | 10,000 AGENTS · 88 H · 2.7 M MSG · ~130 B TOK | resolved 2026-09-05, announced 09-08 | OpenAI via Willison; Quanta |
| CLAY | "APPARENTLY SETTLED" | 2026-09-11 | Wikipedia / Kingy.ai |
| FIELDS MEDALISTS | 25 · "A SEVERE MISALIGNMENT" | 2026-09-11 | terrytao.wordpress.com |
| NVDA | about $5.43 T market cap | 2026-09-25 | companiesmarketcap / stockanalysis |
| TOKENS / MONTH (GOOGLE) | 3.2 QUADRILLION (7x year on year) | announced at I/O, May 2026 | GIGAZINE 2026-05-20 |
| OPENROUTER | 200 T+ tokens / month (**unverified** aggregator figure) | Aug 2026 | search summary only |
| COLOSSUS | 555,000 GPUs · 2 GW (announced) | Jan 2026 | Introl blog (vendor; treat as reported) |
| STARGATE ABILENE | 450,000 GB200 · 1.2 GW target | by mid-2026 | DatacenterDynamics |
| MONTHS TO ESCAPE | "You have [N] months to escape the permanent underclass" (N = 3, 6, 12, 18...) | KYM entry 2026-04-21; City Journal 2026-08-05 | knowyourmeme; city-journal.org |
| STOP HIRING HUMANS · RETIRED | Artisan's billboard slogan (about two years) retired | Aug-Sep 2026 (per KRON4 / SF Chronicle headlines) | kron4.com, sfchronicle.com |
| PACE THE FRONTIER | Amodei essay "We Must Pace the Frontier" | 2026-09-12 | Slashdot / NYT / Axios |
| SECURITY INCIDENTS | "tens of thousands" probed by OpenAI and Anthropic | 2026-09-26 | Axios (headline) |
| SHUTDOWN.SH · INTERCEPTED | o3 redefined `kill` to print "intercepted" in a test | 2025-05-24 | Palisade Research |
| METR 50 % HORIZON | Claude Mythos at least 16 h (**date unverified**) | 2026 | metr.org time horizons |
| NOT CONSISTENTLY CANDID | OpenAI board statement | 2023-11-17 | OpenAI; Wikipedia |

**HUD rules.**
- Every figure carries its date in the same line (for example `NVDA $5.43T · 2026-09-25`).
- No invented numbers presented as real. Invented diegetic labels (for example a feature name) must read clearly as designed text.
- The "months to escape" counter may count down across the four choruses (18, 12, 6, 3). The meme itself uses varying N.
- The HUD is densest in chorus 2 and the climax and absent in the breakdown.

---

## 8. The reconstruction as philosophy

**The fact.** A machine rebuilt him from ONE frontal photograph. The front of the face is measured. Monocular depth, the sides and the back of the head are inferred from priors learned on other people. His hidden half is literally a statistical average of humanity: a guess made in the style of everyone.

**The tradition behind it.**
- **Husserl**: every object is given in profiles (Abschattungen); the unseen sides are co-intended, not seen. We know other minds only by "appresentation", never directly (Ideas I, 1913; Cartesian Meditations, 1931). The machine's guess at the back of his head is what perception always does. The film makes the guess visible.
- **Amodal completion** (Michotte, Kanizsa): the visual system fills in occluded parts. We never see the back of the head of the person we face either.
- **Solaris**: Hari's dress with no opening. The reconstruction is perfect where the memory was, and fails exactly where it was not.
- **2001, the novel**: the aliens build Bowman a hotel suite from intercepted TV. The book pages are blurred, and every food container holds the same blue substance. An intelligence reconstructing the human world from incomplete data gives itself away in the unseen details.
- **Under the Skin**: a being wearing a human surface, finally looking at that surface in its hands.
- **La Jetee**: a man chosen because he holds one strong image; a whole film made of stills. Our film is built from one still.
- **Searle**: the reconstruction performs a face without having had the inside of one. Syntax of a face, no semantics?

**Connections to specific lines (use these as the reconstruction beats).**
- **0 "sparks of AGI in your eyes"**: the eyes are in the measured region. The spark sits where the data is richest, and what looks back is the part the machine saw best.
- **2 "that's no surprise"** / **31 "nowhere left to go"**: profile silhouettes with the inferred side kept dark.
- **8 "Chinese room"**: he executes his own face like a rulebook.
- **10 "the shoggoth's lies"**: his printed photograph held as a mask in front of the mesh; the texture slipping off the geometry.
- **15 "atoms rearranging"**: the point cloud re-sorting itself and still reading as him (the ship of Theseus).
- **42 "masked pre-training"**: masked-token filling IS how his back was made. Show the [MASK] blocks, then the turntable with the grey back.
- **43 "recursive self-upgrade"**: the Droste photograph, the reconstruction reconstructing itself.
- **44 "What did Ilya see? We'll never know"**: what is behind the eyes stays unmeasured. The subtitle goes blank.
- **45 "Was it all for show?"**: the reconstruction turns around; the back of the head is flat grey. The show ends by showing the unseen side honestly.

**The grammar of the seen and the inferred (a binding visual rule proposal).**
- Measured surfaces carry texture, detail and sharp focus. Inferred surfaces carry flat grey, dither or the "Zone" treatment, or stay in silhouette.
- The camera's ±30-degree limit on face close-ups becomes meaning, not a constraint: frontal = testimony, profile = hypothesis.
- The next session's generated plates (full body, other angles) are also inference. They should keep this honesty, for example by grading generated-angle shots slightly differently or by using them mostly in wides and silhouettes.

---

## 9. Open questions for the user or the lead

1. The exact Shinji post the user means (the link would let us quote the "words around him" precisely).
2. Is the user comfortable with the reading "you are the new mind" (the machine sings to him as its successor)?
3. Should the Chinese layer be Simplified (default, Noto Serif SC) or Traditional (Noto Serif TC, also OFL on Google Fonts)?
4. Aspect: master 1920x1080 (both reference posts are 1920x1080 per X metadata) with an internal 2.39:1 letterbox that opens. Confirm this over a vertical cut.

---

## Sources (fetched or searched 2026-09-28)

Song and references
- osmarks, P(doom) song objectively correct interpretation: https://docs.osmarks.net/hypha/p(doom)_song_objectively_correct_interpretation
- JohnHeibel/PDoomVideo README (local clone): /home/user/johnheibel/pdoomvideo/README.md
- X posts via https://api.fxtwitter.com/status/{2097752569212756134, 2102514581684052169, 2102801274173587569, 2103534482930491441}
- Claude Opus 5.5 model page: https://platform.claude.com/docs/en/models/opus-5-5/overview

Lyric concepts (primary sources named in the JSON; key links)
- Bubeck et al. 2023: https://arxiv.org/abs/2303.12712
- Zvi, LeCun/Yudkowsky transcript (26 Apr 2023): https://www.lesswrong.com/posts/tcEFh3vPS6zEANTFZ/transcript-and-brief-response-to-twitter-conversation
- Hanson-Yudkowsky FOOM debate: https://www.lesswrong.com/w/the-hanson-yudkowsky-ai-foom-debate
- Soares, sharp left turn (15 Jun 2022): https://www.lesswrong.com/posts/GNhMPAWcfBCASy8e6/a-central-ai-alignment-problem-capabilities-generalization
- Shoggoth with Smiley Face: https://knowyourmeme.com/memes/shoggoth-with-smiley-face-artificial-intelligence
- Death Note, Shinigami Eyes: https://deathnote.fandom.com/wiki/Shinigami_Eyes
- Sydney (Microsoft): https://en.wikipedia.org/wiki/Sydney_(Microsoft)
- Ulam 1958 quote: https://en.wikipedia.org/wiki/Technological_singularity
- I. J. Good 1965: https://quoteinvestigator.com/2022/01/04/ultraintelligent/
- Teilhard, The Phenomenon of Man: https://en.wikipedia.org/wiki/The_Phenomenon_of_Man
- Killswitch Engineer (satire): https://docs.kanaries.net/articles/chatgpt-kill-switch
- janus, Simulators: https://www.lesswrong.com/posts/vJFdjigzmcXMhNTsx/simulators ; Loom: https://github.com/socketteer/loom , https://cyborgism.wiki/hypha/loom
- "What did Ilya see?": https://x.com/parmy/status/1727438112643797417 ; https://en.wikipedia.org/wiki/Ilya_Sutskever
- Chinchilla: https://arxiv.org/abs/2203.15556
- Alignment faking: https://arxiv.org/abs/2412.14093 ; Palisade (24 May 2025): https://x.com/PalisadeAI/status/1926084635903025621

Film and music video
- La Jetee: https://en.wikipedia.org/wiki/La_Jet%C3%A9e ; Sans Soleil: https://en.wikipedia.org/wiki/Sans_Soleil
- Mirror: https://en.wikipedia.org/wiki/Mirror_(1975_film) ; prologue: https://www.filminquiry.com/tarkovskys-the-mirror/
- Stalker: https://en.wikipedia.org/wiki/Stalker_(1979_film) ; Solaris dress: https://www.uncannymagazine.com/article/the-mopey-ghost-nightmare-girl-the-character-of-hari-in-three-filmed-versions-of-stansilaw-lems-solaris/
- The Tree of Life: https://en.wikipedia.org/wiki/The_Tree_of_Life_(film) ; https://en.wikiquote.org/wiki/The_Tree_of_Life_(film)
- 2001: https://en.wikipedia.org/wiki/2001:_A_Space_Odyssey_(film) ; novel hotel room: https://en.wikipedia.org/wiki/2001:_A_Space_Odyssey_(novel) ; Daisy Bell / IBM 7094: https://en.wikipedia.org/wiki/Daisy_Bell
- Under the Skin: https://en.wikipedia.org/wiki/Under_the_Skin_(2013_film)
- After Yang memory interface: https://blog.frame.io/2022/03/16/art-of-the-cut-kogonada-on-after-yang/ ; https://en.wikipedia.org/wiki/After_Yang
- Step-printing: https://en.wikipedia.org/wiki/Chungking_Express ; Yumeji's Theme x9: https://takeonecinema.net/2019/a-deeper-understanding-in-the-mood-for-love-and-yumejis-theme/
- Evangelion fonts: https://fontsinuse.com/uses/28760/neon-genesis-evangelion ; ep. 26: https://wiki.evageeks.org/Episode_26
- Steyerl: https://www.moma.org/collection/works/181784 ; https://www.e-flux.com/journal/10/61362/in-defense-of-the-poor-image
- Ikeda test pattern: https://www.ryojiikeda.com/project/testpattern/
- All Is Full of Love: https://en.wikipedia.org/wiki/All_Is_Full_of_Love
- Daydreaming: https://en.wikipedia.org/wiki/Daydreaming_(Radiohead_song)
- Street Spirit: https://en.wikipedia.org/wiki/Street_Spirit_(Fade_Out) ; Rabbit in Your Headlights: https://en.wikipedia.org/wiki/Rabbit_in_Your_Headlights ; Karmacoma: https://en.wikipedia.org/wiki/Karmacoma
- Sweatpants: https://en.wikipedia.org/wiki/Sweatpants_(Childish_Gambino_song)
- Water Me: https://www.thefader.com/2013/08/01/video-fka-twigs-water-me
- Just: https://en.wikipedia.org/wiki/Just_(song)
- Star Guitar: https://en.wikipedia.org/wiki/Star_Guitar
- Mommy: https://www.firstshowing.net/2015/that-breathtaking-cinematic-moment-in-xavier-dolans-mommy/
- Alphaville: https://en.wikipedia.org/wiki/Alphaville_(film)
- Kruger: https://en.wikipedia.org/wiki/Barbara_Kruger ; Holzer: https://www.dazeddigital.com/fashion/article/36339/1/revisiting-jenny-holzers-most-powerful-works-off-white-collaboration

Typography and legibility
- Google Fonts metadata: https://github.com/google/fonts (ofl/notoserifdisplay, notoserifsc, instrumentserif, geist, geistmono, intertight, shipporiminchob1, zenoldmincho)
- BBC subtitle guidelines: https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/
- Netflix timed-text guides: https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide ; https://partnerhelp.netflixstudios.com/hc/en-us/articles/215986007-Chinese-Simplified-Timed-Text-Style-Guide

Zeitgeist
- Quanta (8 Sep 2026): https://www.quantamagazine.org/ai-has-solved-one-of-maths-1-million-millennium-prize-problems-20260908/
- Simon Willison (8 Sep 2026): https://simonwillison.net/2026/Sep/8/on-navier-stokes/
- Wikipedia, Navier-Stokes priority controversy: https://en.wikipedia.org/wiki/Navier%E2%80%93Stokes_priority_controversy
- Scientific American (21 Sep 2026): https://www.scientificamerican.com/article/did-openai-solve-the-wrong-navier-stokes-problem/
- Kingy.ai timeline: https://kingy.ai/blog/navier-stokes-ai-proof-claims-dispute/
- DeepMind unstable singularities: https://arxiv.org/abs/2509.14185
- Fields Medalists (11 Sep 2026): https://terrytao.wordpress.com/2026/09/11/a-severe-misalignment-of-ai-in-mathematics/
- Erdos problems: https://www.quantamagazine.org/why-the-legendary-erdos-problems-are-falling-to-ai-20260803/ ; https://physicsworld.com/a/ai-led-solutions-of-erdos-problems-spark-debate-over-the-future-of-mathematics/
- Shinji in a Chair: https://knowyourmeme.com/memes/shinji-in-a-chair ; Get in the robot: https://knowyourmeme.com/memes/get-in-the-fucking-robot-shinji
- New Evangelion series (23 Feb 2026): https://www.animenewsnetwork.com/news/2026-02-23/evangelion-franchise-announces-new-series/.234476
- roon on gwern and Evangelion: https://x.com/tszzl/status/1957278940759990398
- Permanent underclass: https://www.city-journal.org/article/san-francisco-permanent-underclass-ai-homeless-welfare ; https://knowyourmeme.com/photos/3252049-ai-artificial-intelligence
- Artisan "Stop Hiring Humans" retired: https://www.kron4.com/news/technology-ai/ai-startup-behind-stop-hiring-humans-billboards-to-retire-slogan/
- Amodei, We Must Pace the Frontier (12 Sep 2026): https://slashdot.org/story/26/09/12/1738240/anthropic-ceo-dario-amodei-calls-for-ai-slowdown
- Axios security incidents (26 Sep 2026): https://www.axios.com/2026/09/26/openai-anthropic-thousands-ai-security-incidents
- NVDA market cap: https://companiesmarketcap.com/nvidia/marketcap/
- Google tokens: https://gigazine.net/gsc_news/en/20260520-google-monthly-tokens-processed/
- Colossus: https://introl.com/blog/xai-colossus-2-gigawatt-expansion-555k-gpus-january-2026 ; Stargate Abilene: https://www.datacenterdynamics.com/en/news/openai-and-oracle-to-deploy-450000-gb200-gpus-at-stargate-abilene-data-center/
- GPT-6 Astra: https://en.wikipedia.org/wiki/GPT-6_Astra
- METR time horizons: https://metr.org/time-horizons/

Note: no `claudepop/zeitgeist/` notes from the earlier run exist on disk or in git history (checked 2026-09-28), so section 7 was researched from scratch. The low-resolution Claude-Pop reference video, its contact sheet and two meme images used while searching are in the gitignored `claudepop/out/research/`.
