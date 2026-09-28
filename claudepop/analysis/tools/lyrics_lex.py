"""Lyric lines with display words -> spoken tokens, and a custom pronunciation lexicon (ARPAbet).

Each LINE: (display_text, [(display_word, [spoken tokens...]), ...]).
Spoken tokens either exist in CMUdict (pocketsphinx en-us) or are defined in LEX below.
"""
import re

LEX = {
    # letter names
    "ey_": "EY", "jee_": "JH IY", "eye_": "AY", "pee_": "P IY", "tee_": "T IY", "en_": "EH N", "vee_": "V IY",
    "dee_": "D IY", "ee_": "IY", "em_": "EH M", "el_": "EH L", "see_": "S IY", "ar_": "AA R", "oh_": "OW",
    "you_": "Y UW", "aych_": "EY CH", "ef_": "EH F",
    # out-of-vocabulary words
    "foom": "F UW M", "shrooms": "SH R UW M Z", "shoggoth's": "SH AA G AH TH S", "shinigami": "SH IH N IH G AA M IY",
    "basilisk": "B AE S AH L IH S K", "neumann's": "N OY M AH N Z", "gato": "G AA T OW",
    "paperclips": "P EY P ER K L IH P S", "killswitch": "K IH L S W IH CH",
    "orthogonality": "AO R TH AA G AH N AE L AH T IY", "singularity's": "S IH NG G Y AH L EH R AH T IY Z",
    "chat": "CH AE T",
}

# display word -> spoken tokens (only where it differs from lower-cased, punctuation-stripped display word)
SPECIAL = {
    "AGI": ["ey_", "jee_", "eye_"], "ChatGPT,": ["chat", "jee_", "pee_", "tee_"], "P(doom)": ["pee_", "doom"],
    "P(doom),": ["pee_", "doom"], "FOOM": ["foom"], "NVDA": ["en_", "vee_", "dee_", "ey_"], "E": ["ee_"],
    "MLP,": ["em_", "el_", "pee_"], "CDR": ["see_", "dee_", "ar_"], "PTO,": ["pee_", "tee_", "oh_"],
    "GPU": ["jee_", "pee_", "you_"], "RLHF": ["ar_", "el_", "aych_", "ef_"], "Post-Chinchilla,": ["post", "chinchilla"],
    "super-dense": ["super", "dense"], "pre-training": ["pre", "training"], "self-upgrade": ["self", "upgrade"],
    "'cause": ["cause"],
}


def spoken(word):
    if word in SPECIAL:
        return SPECIAL[word]
    w = word.strip("“”\"!?,.;:").lower()
    w = w.replace("’", "'")
    return [w]


def load_lines(path):
    txt = open(path).read()
    out = []
    for a, b, c in re.findall(r'\[([\d.]+),\s*([\d.]+),\s*"((?:[^"\\]|\\.)*)"\]', txt):
        words = c.split()
        out.append({"start": float(a), "end": float(b), "text": c, "words": [(w, spoken(w)) for w in words]})
    return out


def syllables(arpa):
    return sum(1 for p in arpa.split() if p[:2] in ("AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"))
