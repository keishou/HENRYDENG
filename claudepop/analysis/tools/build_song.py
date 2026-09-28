"""Assemble analysis/song.json from the analysis intermediates.

inputs (in <work>): rhythm.json (rhythm.py), hits.json (hits.py), vt.json (vocal_timing.py)
usage: python3 build_song.py <work_dir> <out song.json>
"""
import sys, json
import numpy as np

W, OUT = sys.argv[1:3]
R = json.load(open(f"{W}/rhythm.json"))
HITS = json.load(open(f"{W}/hits.json"))
VT = json.load(open(f"{W}/vt.json"))

BPM, T, T0 = R["bpm"], R["beat_period"], R["t0"]
BAR = 4 * T
DUR = R["duration"]
AUDIBLE_END = 156.48  # mix below -70 dBFS after this (measured)


def bar_t(n):  # start time of bar n (1-based)
    return round(T0 + (n - 1) * BAR, 3)


def pos(t):
    q = (t - T0) / (T / 4)
    qi = int(round(q))
    return f"{qi // 16 + 1}.{(qi // 4) % 4 + 1}.{qi % 4 + 1}"


# ------------------------------------------------------------------ sections (bar numbers are 1-based, end exclusive)
SECTIONS = [
    ("intro", 0, 1, 2, "Soft synth pad/keys only (no drums). Vocal breath/hum pickup from 1.60 s; high-band swell 1.2-2.05 s into bar 2."),
    ("verse1", 1, 2, 10, "Vocals over 8th-note synth plucks, NO drums. 'I see sparks of AGI...' through '...you're my boss'."),
    ("prechorus1", 2, 10, 14, "Noise riser 16.1-16.6 then four-on-the-floor kick enters on bar 10 (16.60) with crash; 'ChatGPT, please don't eat me alive'. Bar 13 beats 1-2: 16th-note kick roll; beats 3-4 (22.98-23.85): full instrumental STOP while 'I'm upping my P-' is sung."),
    ("chorus1", 3, 14, 22, "DROP on 'DOOM' at 23.87 (bar 14 downbeat). Kick on every beat + clap on 2 & 4 + open hat on off-beat 8ths. Vocal lines end 35.5; wordless vocal fills 35.7-37.2; drum fill end of bar 21."),
    ("verse2", 4, 22, 30, "Full groove continues (kick/clap/hats), vocals 'We had a stable training run...' to '...atoms rearranging'."),
    ("prechorus2", 5, 30, 34, "Lighter: kick without clap, long notes 'Sydney, please let me free'. Bar 32 kick on 8ths + riser (build); bar 33 beats 1-2 kick roll; beats 3-4 (59.35-60.22) STOP with 'I'm upping my P-' pickup."),
    ("chorus2", 6, 34, 42, "DROP on 'DOOM' at 60.24 (bar 34). Basilisk / NVDA / Omega Point / 1e30 FLOPs / 'safe enough'. Wordless ad-libs 68.2-69.5 and 71.8-73.8. Drum fill end of bar 41; verse-3 pickup 'Forward' at 74.10."),
    ("verse3", 7, 42, 50, "Full groove. 'Forward MLP...' / von Neumann / sharp left turn / CDR. Bar 49 ends with kick 8ths fill."),
    ("breakdown", 8, 50, 54, "Drums OUT (instrumental ~-32 dB): pad + long vocal notes 'Gato, please don't let me go'. Big riser 95.0-96.6. Hook pickup 'I'm upping my P-' at 95.43."),
    ("chorus3_halftime", 9, 54, 61, "Half-time breakdown chorus (lowest energy of the song, instrumental -30..-41 dB): kick only on beat 1 of bars 54/56/58/60, noise-claps, reverse swells into bars 58 and 60. Paperclips / killswitch / fuse / orthogonality lines; 'blues' melisma + wordless vocal 108.4-109.8."),
    ("verse4_bridge", 10, 61, 69, "Full groove returns at 109.33. 'Just (just) transformers all the way' / disobey / Chinchilla / safety fence / 100k GPU / RLHF."),
    ("chorus4_final", 11, 69, 77, "No stop: the hook is sung in augmented quarter notes starting 123.66 and 'DOOM' lands on bar 70 (125.69). Loom / masked pre-training / recursive self-upgrade / 'What did Ilya see? We'll never know' (held to 136.6)."),
    ("stop", 12, 77, 78, "Whole-bar instrumental drop-out 138.45-140.24 (inst ~-60 dB): 'Was it all for show?' ('all' 138.41 on the cut, 'show' 140.04)."),
    ("outro_drop", 13, 78, 85, "Final DROP at 140.24: loudest section, full groove + pitched vocal-chop/lead stabs on every beat (non-lexical)."),
    ("ending", 14, 85, 87, "Final kick 152.96 then sustained chord (bar 85) and fade from 154.8; -50 dB at 155.85, silence by 156.5."),
]
PATTERN = {  # drum pattern per section, read off the transcription (hits.py) + spectrograms; use it to synthesise perfect pulses
    "intro": {"kick": None, "clap": None, "hat": None, "pulse": "none (pad)"},
    "verse1": {"kick": None, "clap": None, "hat": None, "pulse": "synth pluck on every 8th (0.227 s)"},
    "prechorus1": {"kick": "every beat from 16.60; 16th roll bar 13 beats 1-2; none during stop", "clap": None, "hat": None, "pulse": "plucks on off-beat 8ths"},
    "chorus1": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor"},
    "verse2": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths (lighter, pluck-like)", "pulse": "four-on-the-floor"},
    "prechorus2": {"kick": "every beat; 8ths in bar 32; 16th roll bar 33 beats 1-2; none during stop", "clap": None, "hat": None, "pulse": "kick only"},
    "chorus2": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor"},
    "verse3": {"kick": "every beat (8ths fill in bar 49)", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor"},
    "breakdown": {"kick": None, "clap": None, "hat": None, "pulse": "none (pad, long vocal notes)"},
    "chorus3_halftime": {"kick": "beat 1 of bars 54, 56, 58, 60 only", "clap": "sparse noise-claps (beat 2 / beat 4)", "hat": None, "pulse": "half-time, mostly empty"},
    "verse4_bridge": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor"},
    "chorus4_final": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor"},
    "stop": {"kick": None, "clap": None, "hat": None, "pulse": "silence (vocal only)"},
    "outro_drop": {"kick": "every beat", "clap": "beats 2 & 4", "hat": "off-beat 8ths", "pulse": "four-on-the-floor + vocal-chop stab per beat"},
    "ending": {"kick": "single hit 152.96", "clap": None, "hat": None, "pulse": "ring-out / fade"},
}
lufs = np.array(R["curves10hz"]["lufs"])
lufs_inst = np.array(R["curves10hz"]["lufs_inst"])
lufs_voc = np.array(R["curves10hz"]["lufs_vocal"])
sections = []
for name, idx, b0, b1, desc in SECTIONS:
    t0 = 0.0 if b0 == 1 and name == "intro" else bar_t(b0)
    t1 = DUR if b1 == 87 else bar_t(b1)
    if name == "intro":
        t0, t1 = 0.0, bar_t(2)
    i0, i1 = int(t0 * 10), int(t1 * 10)
    sections.append({"name": name, "start": round(t0, 3), "end": round(min(t1, DUR), 3), "bars": [b0 if name != "intro" else 1, b1 - 1],
                     "n_bars": (b1 - b0) if name != "intro" else 1,
                     "lufs_mean": round(float(np.mean(lufs[i0:i1])), 1), "lufs_inst_mean": round(float(np.mean(lufs_inst[i0:i1])), 1),
                     "drums": PATTERN[name], "desc": desc})

# ------------------------------------------------------------------ events
events = [
    {"t": 0.23, "type": "start", "note": "first sound (pad)"},
    {"t": 1.60, "type": "vocal_entry", "note": "breath/hum pickup; first word 'I' at 2.05 on the bar-2 downbeat"},
    {"t": 1.2, "end": 2.05, "type": "riser", "note": "intro swell into bar 2"},
    {"t": 16.1, "end": 16.6, "type": "riser", "note": "white-noise riser into bar 10; kick enters 16.60"},
    {"t": 16.60, "type": "impact", "note": "crash + kick-in (pre-chorus 1)"},
    {"t": 22.05, "end": 22.96, "type": "fill", "note": "16th-note kick roll (bar 13 beats 1-2)"},
    {"t": 22.98, "end": 23.85, "type": "stop", "note": "instrumental stop under 'I'm up-ping my P-'"},
    {"t": 23.87, "type": "drop", "note": "CHORUS 1 drop on 'DOOM' (bar 14)"},
    {"t": 37.9, "end": 38.42, "type": "fill", "note": "drum fill into verse 2"},
    {"t": 56.6, "end": 58.42, "type": "build", "note": "bar 32: kick on 8ths + rising high band"},
    {"t": 58.42, "end": 59.33, "type": "fill", "note": "16th-note kick roll (bar 33 beats 1-2)"},
    {"t": 59.35, "end": 60.22, "type": "stop", "note": "instrumental stop under 'I'm up-ping my P-'"},
    {"t": 60.235, "type": "drop", "note": "CHORUS 2 drop on 'DOOM' (bar 34)"},
    {"t": 73.9, "end": 74.78, "type": "fill", "note": "drum fill (end of bar 41) under 'Forward'"},
    {"t": 74.78, "type": "impact", "note": "crash at verse 3 downbeat (strongest high-band hit of the song)"},
    {"t": 88.9, "end": 89.33, "type": "fill", "note": "kick 8ths fill into breakdown"},
    {"t": 89.33, "type": "drop_out", "note": "drums out: breakdown"},
    {"t": 95.0, "end": 96.6, "type": "riser", "note": "big noise/reverse riser into the half-time chorus"},
    {"t": 96.60, "type": "drop", "note": "CHORUS 3 (half-time) on 'DOOM' (bar 54)"},
    {"t": 103.4, "end": 103.87, "type": "riser", "note": "reverse swell into bar 58"},
    {"t": 107.0, "end": 107.51, "type": "riser", "note": "reverse swell into bar 60"},
    {"t": 109.33, "type": "drop", "note": "full groove returns (verse 4 / bridge)"},
    {"t": 125.69, "type": "accent", "note": "CHORUS 4 'DOOM' (bar 70) - no stop, augmented hook"},
    {"t": 138.45, "end": 140.24, "type": "stop", "note": "whole-bar stop under 'Was it all for show?'"},
    {"t": 140.235, "type": "drop", "note": "OUTRO drop (bar 78) - loudest part of the song"},
    {"t": 152.96, "type": "final_hit", "note": "last kick (bar 85); chord rings"},
    {"t": 154.8, "end": 156.5, "type": "fade", "note": "fade to silence (-50 dB at 155.85)"},
]

# ------------------------------------------------------------------ hooks (hand-verified, see REPORT.md)
HOOKS = [
    {"chorus": 1, "drop": 23.871, "syl": [["I'm", 22.72], ["up", 22.98], ["ping", 23.19], ["my", 23.42], ["P", 23.62], ["DOOM", 23.871]],
     "rhythm": "8th notes; I'm = drop - 2.5 beats; last 5 syllables sung into the instrumental stop, DOOM on the drop downbeat"},
    {"chorus": 2, "drop": 60.235, "syl": [["I'm", 59.09], ["up", 59.32], ["ping", 59.53], ["my", 59.77], ["P", 59.98], ["DOOM", 60.235]],
     "rhythm": "identical to chorus 1 ('my' has no detectable onset: grid value)"},
    {"chorus": 3, "drop": 96.598, "syl": [["I'm", 95.43], ["up", 95.68], ["ping", 95.91], ["my", 96.14], ["P", 96.34], ["DOOM", 96.598]],
     "rhythm": "identical, over the breakdown riser (no stop); 'my' = grid value"},
    {"chorus": 4, "drop": 125.689, "syl": [["I'm", 123.66], ["up", 124.12], ["ping", 124.53], ["my", 124.99], ["P", 125.45], ["DOOM", 125.689]],
     "rhythm": "AUGMENTED: quarter notes (~0.46 s apart), no stop; 'P' -> 'DOOM' still a half beat. Lowest confidence of the four (+-0.1 s on I'm/up)"},
]

# sub-syllable timings for acronym / hook words (line index, word index) -> [[label, t], ...]
SYL = {
    (0, 4): [["A", 3.65], ["G", 4.10], ["I", 4.33]],
    (5, 0): [["Chat", 16.60], ["G", 17.25], ["P", 17.95], ["T", 18.42]],
    (19, 0): [["N", 62.51], ["V", 62.74], ["D", 62.965], ["A", 63.19]],
    (30, 3): [["P", 99.78], ["T", 100.01], ["O", 100.24]],
    (38, 2): [["G", 119.78], ["P", 120.01], ["U", 120.24]],
    (39, 0): [["R", 120.69], ["L", 120.92], ["H", 121.15], ["F", 121.37]],
}
for h in HOOKS:
    li = {1: 6, 2: 17, 3: 28, 4: 40}[h["chorus"]]
    s = dict(h["syl"])
    SYL[(li, 1)] = [["up", s["up"]], ["ping", s["ping"]]]
    SYL[(li, 3)] = [["P", s["P"]], ["(doom)", s["DOOM"]]]

NOTES = {
    0: "Vocal breath/hum from 1.60 s; first lexical word 'I' on the bar-2 downbeat (2.05). Show the line from ~1.6.",
    5: "Burned-in subtitle is 1.3 s late: 'Chat-' starts on the bar-10 downbeat together with the kick entry.",
    6: "Chorus hook. Sung into the 22.98-23.85 instrumental stop; DOOM = drop at 23.871.",
    10: "'lies' held to 31.8; unlabelled vocal notes 31.85-33.2 (backing 'ooh'/echo - subtitle keeps the line up to 33.4).",
    16: "'Syd-ney' is a 2.9 s melisma (53.02-55.9); subtitle starts 0.38 s late.",
    17: "Chorus hook; stop 59.35-60.22; DOOM = drop at 60.235.",
    19: "NVDA sung as letters N-V-D-A on 8th notes (ASR hears 'in the E-eight'); subtitle 0.5 s late.",
    22: "'reckoned' ends 71.75; wordless ad-libs 71.8-73.8 are not in the lyric sheet.",
    23: "Subtitle is 1.1 s early: 'Forward' starts at 74.10 (pickup into bar 42).",
    27: "Breakdown; long notes. 'Gato' on the bar-50 downbeat (89.33) as the drums drop out.",
    28: "Chorus hook over the riser; DOOM = bar 54 downbeat 96.598.",
    33: "'blues' held/melisma to ~108.3; more wordless vocal 108.4-109.8 (both ASR models hear 'who's a...', possibly an echo of 'Ortho-': unverified).",
    34: "Both CTC models hear the word 'just' repeated 2-3x (110.2, 110.7, ~111.1) before 'transformers' (111.2-111.4); subtitle 0.8 s early.",
    40: "Final chorus: hook in quarter notes, no stop; DOOM on bar 70 downbeat 125.689.",
    44: "'know' held to ~136.6.",
    45: "'Was' is a pickup (137.40); the instrumental cuts out at 138.45 on 'all'; 'show' at 140.04 rings into the outro drop at 140.235.",
}

lines = []
for L in VT["lines"]:
    words = []
    for j, w in enumerate(L["words"]):
        src = w["src"]
        conf = ("verified" if src == "manual" else "high" if src.startswith("ps+ctc>onset") else
                "med" if (">onset" in src or ">pitch" in src or src.startswith("ps+ctc")) else "low")
        d = {"t": w["t"], "e": w["e"], "w": w["w"], "conf": conf, "src": src}
        if (L["i"], j) in SYL:
            d["syl"] = [{"t": t, "s": s} for s, t in SYL[(L["i"], j)]]
        words.append(d)
    entry = {"i": L["i"], "start": L["start"], "end": L["end"], "text": L["text"], "words": words,
             "sub_start": L["sub_start"], "sub_end": L["sub_end"], "d_start": L["d_start"], "d_end": L["d_end"],
             "sub_off_gt150ms": L["flag_150ms"], "pos": pos(L["start"])}
    if L["i"] in NOTES:
        entry["note"] = NOTES[L["i"]]
    if L["i"] == 0:
        entry["vocal_entry"] = 1.60
    lines.append(entry)

VOCAL_EXTRA = [
    {"start": 1.60, "end": 2.02, "what": "breath/hum pickup before 'I see sparks'"},
    {"start": 31.85, "end": 33.20, "what": "3 wordless notes after 'lies' (backing/echo)"},
    {"start": 35.70, "end": 37.20, "what": "post-chorus wordless vocal fills"},
    {"start": 45.70, "end": 46.10, "what": "high 'ooh'/vocal chop (~900 Hz)"},
    {"start": 68.20, "end": 69.50, "what": "ad-lib after 'a second' (ASR: 'yeah... ah...')"},
    {"start": 71.80, "end": 73.80, "what": "wordless ad-libs after 'we reckoned'"},
    {"start": 108.40, "end": 109.80, "what": "wordless vocal / possible 'Ortho-' echo after 'blues'"},
    {"start": 140.24, "end": 154.0, "what": "outro: pitched vocal-chop (or lead) stabs on every beat, non-lexical"},
]

# ------------------------------------------------------------------ energy (10 Hz, 0..1)
lo, hi = -45.0, float(np.max(lufs))
energy = np.clip((lufs - lo) / (hi - lo), 0, 1)

song = {
    "_about": "I'm Upping My P(doom) - frame-accurate analysis. All times in seconds from the first decoded PCM sample of assets/pdoom.mp3 "
              "(ffmpeg/librosa/WebAudio decodeAudioData convention; the MP3 has a 23 ms encoder-delay start_time that some players/containers "
              "apply - verify once with a click test). See analysis/REPORT.md.",
    "duration": DUR,
    "bpm": BPM,
    "beat_period": T,
    "time_signature": "4/4",
    "grid": {"t0": T0, "t0_uncertainty_s": 0.008, "bar_period": BAR,
             "formula": "beat k (0-based) = t0 + k*beat_period; bar n (1-based) starts at t0 + (n-1)*bar_period",
             "madmom_free_fit": R["madmom_free_fit"]},
    "beats": [b for b in R["beats"] if b < AUDIBLE_END],
    "downbeats": [b for b in R["downbeats"] if b < AUDIBLE_END],
    "audible_end": AUDIBLE_END,
    "sections": sections,
    "lines": lines,
    "hooks": HOOKS,
    "vocal_extra": VOCAL_EXTRA,
    "hits": HITS,
    "events": events,
    "energy": [round(float(v), 3) for v in energy],
    "energy_info": {"rate_hz": 10, "t0": 0.0, "definition": "EBU R128 momentary loudness (400 ms, K-weighted) of the full mix mapped "
                    f"linearly from {lo} LUFS -> 0 to the song max {hi:.1f} LUFS -> 1", "integrated_lufs": R["integrated_lufs"]},
    "curves10hz": R["curves10hz"],
}
json.dump(song, open(OUT, "w"), separators=(",", ":"))
# drop-in replacement for pdoomvideo/src/lyrics.js format ([start, end, text])
import os
with open(os.path.join(os.path.dirname(OUT), "lyrics_refined.js"), "w") as f:
    f.write("// lyrics_refined.js: [start, end, text] refined against the audio (see analysis/REPORT.md). Word timings: song.json lines[].words.\n")
    f.write("const LY = [\n")
    f.write(",\n".join(f"  [{L['start']:.2f}, {L['end']:.2f}, {json.dumps(L['text'], ensure_ascii=False)}]" for L in lines))
    f.write("\n];\n")
print("sections", len(sections), "lines", len(lines), "hits", len(HITS), "beats", len(R["beats"]), "energy", len(energy))
for s in sections:
    print(f"{s['name']:18s} {s['start']:7.2f}-{s['end']:7.2f} bars {s['bars']} lufs {s['lufs_mean']} inst {s['lufs_inst_mean']}")
