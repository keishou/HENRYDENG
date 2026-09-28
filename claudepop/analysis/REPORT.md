# Song analysis: the timing backbone

"I'm Upping My P(doom)" (`pdoomvideo/assets/pdoom.mp3`, 48 kHz stereo MP3, untouched). Analysis run 2026-09-28. Every shot, cut, lyric card and HUD tick in the film is timed from `claudepop/analysis/song.json`. This report says how each number in it was made, what was checked, and what is still uncertain.

## 1. Files
| Path | What |
|---|---|
| `analysis/song.json` | grid, sections, events, lines with word timings, extra vocals, phrases, hits, per-beat energy, verification stats |
| `analysis/tools/run_all.sh` | regenerates everything in order (about 15 min on 4 CPU cores) |
| `grid.py` | beat grid, t0, bar phase, kick/snare/hat hits, crashes, per-beat stem levels |
| `beats_bt.py` | Beat This! (CPJKU, ISMIR 2024) beats + downbeats, an independent check (reproduces the cached output exactly) |
| `vocal_feats.py` | vocal-stem onsets (SuperFlux, energy, pYIN pitch/voicing), f0, RMS |
| `emissions.py` | CTC frame posteriors of torchaudio MMS_FA and WAV2VEC2_ASR_LARGE_LV60K_960H on the vocal stem, 4 sub-frame shifts each |
| `align_fa.py` | whole-song Viterbi forced alignment with a garbage state for unscripted singing |
| `asr_whisper.py` | Whisper large-v3 (faster-whisper, own venv `out/venv-asr`) transcript: sung material missing from lyrics.js |
| `build_song.py` | combines everything with the hand-verified `word_overrides.json` (75 word starts, each with its evidence) and `structure.json` (sections, events, extra vocals, couplets); writes song.json + click tracks |
| `zoom_post.py`, `zoom_plot.py`, `review_plots.py` | review plots (vocal + synth spectrograms, onsets, CTC posteriors, 16th grid) |
| `out/audio/click_words.wav`, `click_beats.wav` | auditions: vocal stem + clicks at word starts (high click = line start); mix + beat clicks (high = downbeat) |
| `out/audio/pdoom_44k/48k.wav`, `stems/htdemucs/pdoom_44k/` | analysis decodes and Demucs stems (never for delivery) |

Legacy scripts from the interrupted run (`rhythm.py`, `vocal_timing.py`, `align_ctc.py`, `align_ps.py`, `mdx_separate.py`) read a scratch folder that no longer exists and are superseded; `lyrics_lex.py` is still used.

## 2. Time zero
Seconds from the first sample of ffmpeg's decode of the MP3. ffmpeg honours the LAME gapless header and drops 1105 priming samples (23.0 ms), so t = 0 is the first programme sample. Duration 156.6507 s; first sound (pad, above -40 dBFS) 0.230 s. Checked: an MP4 muxed with `ffmpeg -c:a copy` and decoded back matches `pdoom_48k.wav` at exactly 0 samples lag. A player that ignored the MP4 edit list would play everything 23 ms late, so check once in Chromium at final review.

## 3. Beat grid and t0
- 132.000 BPM, 4/4, machine-quantised. The free fit of 106 clap-free on-beat kick attacks gives 132.0027 BPM, residual std 2.5 ms (p95 5.4 ms). Phase by thirds: 0.2368 / 0.2350 / 0.2348, so there is no drift.
- **t0 = 0.2356 s.** Beat n = t0 + n·60/132; bar b starts at t0 + (b−1)·240/132. 345 beats, 87 bars.

Phase estimates on the 132 grid:
| Estimate | Phase (s) | Note |
|---|---|---|
| kick attack start (10 % rise, unfiltered drum stem), clap-free beats | **0.2356** | chosen, R = 0.9993 |
| free fit intercept | 0.2371 | |
| Beat This! | 0.2407 | median +4.4 ms, MAD 6.2 ms from the grid |
| mix spectral-flux comb | 0.249 | peaks on the attack's energy build, not its start |
| kick max slope | 0.2598 | the kick's low end peaks ~23 ms after it starts |

Why the attack start: a cut or flash should land when the ear hears the hit begin. The older 0.219-0.244 spread measured different points of the kick (one ignored the gapless header). The first draft of `grid.py` used a zero-phase filter whose ringing moved attacks about 70 ms early (phase 0.166); it now uses causal filters with the delay removed plus an unfiltered-stem attack. At 24 fps, anything from 0.235 to 0.241 puts each beat in the same or the next frame. Claps are flammed (median -1.9 ms, p10 -19 ms from the grid).

**Bar phase (beat index mod 4)**:
| Evidence | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| snare/clap within 30 ms of a beat | 14 | **61** | 22 | **60** |
| harmonic change (chroma of bass + other stems) | **0.155** | 0.036 | 0.021 | 0.023 |
| Beat This! downbeats | **86** | 0 | 0 | 0 |
| crashes | 6 | 3 | 4 | 4 |

**Section starts on downbeats** (`verification.section_downbeat_check`):
- Choruses 1 and 2 and the final drop: kick, clap and crash within 3 ms, with drum steps of +34, +40 and +40 dB.
- Breakdown, stop and outro tail: drum cuts of -50, -56 and -47 dB.
- Pre-chorus 1, the breakdown chorus and the build: kick within 5 ms.
- Verse 2, pre-chorus 2, verse 3 and chorus 4: kick within 13 ms plus a vocal onset.
- The bridge has no kick on beat 1 (snare and bass return), which is correct for the song.

Half-time grid: t0 + n·2·60/132 (66 BPM, 0.909 s = beats 1 and 3). Units: beat 0.4545, bar 1.8182, 2 bars 3.6364, 8 bars 14.5455, 16th 0.1136 s.

## 4. Sections
| Section | t0 | t1 | Bars | Energy | Mix dB | Lines | What happens |
|---|---|---|---|---|---|---|---|
| intro | 0.000 | 2.054 | 1 | 0.36 | -30.5 | - | silence to 0.23, one bar of pad |
| verse1 | 2.054 | 16.599 | 2-9 | 0.68 | -22.7 | 0-4 | pad + voice, no drums; bass swells from 12.05, full from bar 8 |
| prechorus1 | 16.599 | 23.872 | 10-13 | 0.77 | -20.7 | 5-6 | first drums on "ChatGPT"; hat roll 22.05; a-cappella stop 22.96-23.87 |
| chorus1 | 23.872 | 38.417 | 14-21 | 0.87 | -18.3 | 6-11 | crash on "doom"; each line lands on a downbeat; fill in bar 21 |
| verse2 | 38.417 | 52.963 | 22-29 | 0.88 | -18.1 | 12-15 | full drums continue |
| prechorus2 | 52.963 | 60.236 | 30-33 | 0.79 | -20.1 | 16-17 | bass out on "Sydney"; 8th kicks bar 32; stop 59.33-60.24 |
| chorus2 | 60.236 | 74.781 | 34-41 | 0.90 | -17.5 | 17-23 | crash on "doom"; fill bar 41 |
| verse3 | 74.781 | 89.326 | 42-49 | 0.91 | -17.4 | 23-26 | densest stretch |
| breakdown_prechorus3 | 89.326 | 96.599 | 50-53 | 0.64 | -23.8 | 27-28 | drums + bass cut on "Gato"; hats back 94.78 |
| chorus3_breakdown | 96.599 | 109.326 | 54-60 | 0.67 | -23.1 | 28-34 | no bass; sub booms 96.60/100.24/103.87/107.51; reverbed claps |
| build | 109.326 | 111.145 | 61 | 0.83 | -19.3 | (34) | drums back, 8th snare roll, "just" stutter |
| bridge | 111.145 | 125.690 | 62-69 | 0.94 | -16.6 | 34-40 | bass back on "trans-"; melisma 122.73-124.5 |
| chorus4 | 125.690 | 138.417 | 70-76 | 0.93 | -16.9 | 40-45 | "What did Ilya see?" |
| was_it_all_for_show | 138.417 | 140.236 | 77 | 0.42 | -29.0 | 45 | full stop, voice alone |
| outro_climax | 140.236 | 152.963 | 78-84 | 0.98 | -15.6 | - | loudest, instrumental + vocal pad |
| outro_tail | 152.963 | 156.651 | 85-86 | 0.36 | -40.3 | - | drums stop; bass cut 154.78; synth fades; below -40 dBFS from 155.28 |

The song's dynamics come from cuts and stops: verse 2, verse 3 and the bridge are as loud as the choruses.

## 5. Events
There are 31 events in `song.json.events`:
- **Drops and big hits:** drop 16.60; big hits 23.87, 60.24 and 125.69; drums return 109.33; bass returns 111.15; final drop 140.24.
- **Stops:** 22.96-23.87 (the /p/ closures reach -60 dBFS), 59.33-60.24, 138.42-140.24.
- **Dropouts and cuts:** bass out 52.96; breakdown cut 89.33; drums stop 152.96; bass cut 154.78.
- **Risers:** 12.05-12.96, 22.05-22.96, 56.60-58.42, 58.42-59.33, 94.78-96.60, 109.33-111.15.
- **Fills:** 37.51, 73.87, 124.78.
- **Sub booms:** 96.60, 100.24, 103.87, 107.51.
- **Vocal melisma:** 122.73-124.5.
- **Silences:** 0-0.23 and 155.28-156.65.

Crashes are in `grid.json`.

## 6. Lyrics
**Method**:
1. Demucs htdemucs vocal stem.
2. Two CTC models, each run 4 times with 5 ms shifted inputs (5 ms effective resolution).
3. Whole-song Viterbi alignment with a garbage state for ad-libs and repeats; each line limited to ±1.5 s of its lyrics.js span; acronyms spelled as sung.
4. Lag calibration against vocal onsets (MMS -5.0 ms, wav2vec2 -3.7 ms).
5. Combination: mean when the models agree within 80 ms, else the model with an onset nearby; snap to a vocal onset within 50 ms; for words beginning with a vowel or sonorant, look back to the latest vocal onset.
6. Hand verification of every line on close-up plots: 75 overrides, 34 of them moved more than 30 ms.
7. Word ends from level dips; line ends at the end of the held note.

**Results**: 46 lines and 227 words; `song.json.lines[].words` holds `{w, t, e, u, how, parts?, auto?}`. `lyrics.js` is off by more than 0.25 s at 18 line starts. The largest errors are line 5 (1.28 s late), line 23 (+1.09), line 40 (+1.02) and line 29 (-0.64).

**Flagged (u > 80 ms)**: automatic pipeline, 16 lines (5-11, 14, 15, 22, 25, 27, 34, 40, 41, 44). After hand verification, 0 lines. Word u: median 30 ms, p90 40 ms, max 72 ms ("as", line 41). Causes:
- MMS goes nearly silent in chorus 1;
- "I'm" pickups sung on the previous held vowel (22.73, 124.52);
- the "just" stutter;
- held notes ("are" 83.65, "never know" 133.87/134.38, "eyes" 34.77);
- ad-libs absorbed before lines 22 and 33.

**Not in lyrics.js** (`extra_vocals`, `sung_as`):
- melisma 35.6-37.05;
- ad-lib 68.18-69.58 ("get..et..eh", both CTC models hear it);
- ad-lib 72.27-73.92;
- uncertain "or-, or-?" at 104.98 and 105.43;
- "Just, just, just, just transformers" (109.07/109.56/110.18/110.65);
- "transformers, formers all the way" (112.05);
- wordless melisma 122.73-124.5;
- outro "oh/ooh" vocal pad 141.1-152.95, with a possible "oh my God" around 150 (Whisper, low confidence).

**Pronunciation:** P(doom) = "pee" on the 4&, "doom" on the downbeat; acronyms are spelled letter by letter with each letter in `parts` (e.g. NVDA 62.49/62.73/62.95/63.18).

**Phrases**:
- `level: "line"` (60): sung lines split at pauses or holds, with `breath_before` and `lands_on_downbeat`.
- `level: "couplet"` (25): the 2-line musical phrases.
- Chorus lines start on beat 2 and resolve onto the next downbeat, so cut on the landing to play a line out.
- Longest vocal gaps: 35.6-38.6, 45.6-47.6, 72.3-74.1, 90.6-92.5, 122.7-124.5, and inside the stop.

## 7. Hits and energy
- **Hits:** `kick` (246), `snare` (168, flammed clap), `hat` (405) as [t, strength], t = attack start. Checked against band plots of chorus 1, the breakdown and the outro.
- **Patterns:** four-on-the-floor from bar 10; claps on 2/4 from bar 14; 8th kicks bar 32; hat rolls bars 13, 33, 53; fills bars 21, 41, 61, 69; no drums in bars 1-9, 50-52, 77, 85-87.
- **Per-beat energy:** `per_beat` (345 rows) has stem dB, kick/snare counts and energy 0..1.

## 8. Verification
| Check | Result |
|---|---|
| tempo | 132.0027 BPM free fit, 2.5 ms residual, 2 ms phase stability |
| bar phase | backbeat, harmony and Beat This! agree |
| section starts | all on bar lines, with attacks within 13 ms or 47-56 dB cuts at every structural one |
| model disagreement | median 16 ms; 74 % ≤ 50 ms; 80 % ≤ 80 ms; 17 % > 200 ms (chorus 1, pickups, held notes) |
| onset coincidence (50 ms) | MMS 62 %, wav2vec2 63 %, final 78 % (any onset 80 %); chance 29 % |
| 8th-grid offset | median 17 ms (chance 57 ms); 82 % ≤ 40 ms |
| Whisper large-v3 | 189 words matched; constant offset -250 ms, MAD 90 ms; 18 outliers, 10 of them segment-initial (Whisper artifact); none contradicts a verified word |
| visual review | all windows with lyrics (1.6-146.8 s) inspected with posterior plots; 146.8-148.6 of the outro only through the CTC posterior listing |
| consistency | word starts increasing, e > t, no overlaps, parts inside their word, sections on downbeats |
| MP4 mux | 0-sample lag |

Listen to the click tracks, especially 22.7-24.4, 26.5-27.6, 33.3-35.0, 59.0-60.3, 109.0-113.0 and 124.4-125.8.

## 9. Still uncertain
- **Legato words with no onset of their own** ("upping" 22.96/59.31, "me" 20.83, "I" 60.50, "the" 26.84, "as" 126.36, "it" 137.80): u 50-72 ms. Fine for type reveals, not for frame-exact lip sync.
- **Word ends** are less reliable than starts; use them for how long a word stays on screen, not as cut points.
- **Guesses:** the 104.98/105.43 syllables and the outro "oh my God".
- **Backing vocals** are not listed separately.
- **Section label:** 109.33-111.14 could be counted as part of the bridge; the events are the same either way.
