#!/usr/bin/env bash
# Fetch the film's fonts (BIBLE 6.1; all SIL OFL, github.com/google/fonts `main`) into claudepop/fonts/ (gitignored by
# claudepop/**/fonts/), plus the legacy look-dev faces used by src/hud.js loadFonts(). Idempotent: existing files are kept.
# The two CJK families are large (Noto Serif SC 25 MB, Noto Sans SC 18 MB); if fontTools is available (claudepop/out/venv)
# they are also subset to GB2312 level 1 + every character in shots.json / lyric_concepts.json + punctuation, vertical
# presentation forms and Latin (*-sub.ttf, ~3 MB each, variable axes kept). src/type/type.js loads the subsets when
# present, else the full files.
#   bash claudepop/film/fetch_fonts.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CP="$(cd "$HERE/.." && pwd)"
OUT="$CP/fonts"; mkdir -p "$OUT"
F=https://raw.githubusercontent.com/google/fonts/main/ofl
get() { [ -s "$OUT/$2" ] || { echo "fetch $2"; curl -sSfL --retry 3 -o "$OUT/$2.part" "$F/$1" && mv "$OUT/$2.part" "$OUT/$2"; }; }

# BIBLE 6.1
get "notoserifdisplay/NotoSerifDisplay%5Bwdth,wght%5D.ttf" NotoSerifDisplay-VF.ttf        # CARD (wdth 62.5, wght 900)
get "newsreader/Newsreader-Italic%5Bopsz,wght%5D.ttf"      Newsreader-Italic-VF.ttf       # THOUGHT (opsz 72, wght 400)
get "newsreader/Newsreader%5Bopsz,wght%5D.ttf"             Newsreader-VF.ttf              # QUESTION
get "intertight/InterTight%5Bwght%5D.ttf"                  InterTight-VF.ttf              # SUBTITLE (500)
get "ibmplexmono/IBMPlexMono-Regular.ttf"                  IBMPlexMono-Regular.ttf        # HUD, premise
get "ibmplexmono/IBMPlexMono-Medium.ttf"                   IBMPlexMono-Medium.ttf
get "notoserifsc/NotoSerifSC%5Bwght%5D.ttf"                NotoSerifSC-VF.ttf             # ZH card / thought / vertical
get "notosanssc/NotoSansSC%5Bwght%5D.ttf"                  NotoSansSC-VF.ttf              # ZH subtitle / HUD
# legacy look-dev faces (src/hud.js loadFonts; film/lookdev)
get "intertight/InterTight%5Bwght%5D.ttf"                  InterTight.ttf
get "barlowcondensed/BarlowCondensed-Medium.ttf"           BarlowCondensed-Medium.ttf
get "barlowcondensed/BarlowCondensed-SemiBold.ttf"         BarlowCondensed-SemiBold.ttf
get "instrumentserif/InstrumentSerif-Regular.ttf"          InstrumentSerif-Regular.ttf
get "instrumentserif/InstrumentSerif-Italic.ttf"           InstrumentSerif-Italic.ttf
for f in notoserifdisplay newsreader intertight ibmplexmono notoserifsc notosanssc barlowcondensed instrumentserif; do
  get "$f/OFL.txt" "OFL-$f.txt"
done

# CJK subsets (optional; needs fontTools)
PY=""
for p in "$CP/out/venv/bin/python" "$CP/out/venv-avatar/bin/python" python3; do
  if "$p" -c 'import fontTools' 2>/dev/null; then PY="$p"; break; fi
done
if [ -n "$PY" ]; then
  CHARS="$OUT/.charset.txt"
  "$PY" - "$CP" "$CHARS" <<'PYEOF'
import json, sys, os
cp, out = sys.argv[1], sys.argv[2]
chars = set()
def walk(x):
    if isinstance(x, str): chars.update(x)
    elif isinstance(x, dict): [walk(v) for v in x.values()]
    elif isinstance(x, list): [walk(v) for v in x]
for f in ('shots.json', 'research/lyric_concepts.json'):
    p = os.path.join(cp, f)
    if os.path.exists(p): walk(json.load(open(p, encoding='utf-8')))
for hi in range(0xB0, 0xD8):                       # GB2312 level 1 (3755 most common hanzi)
    for lo in range(0xA1, 0xFF):
        try: chars.add(bytes([hi, lo]).decode('gb2312'))
        except UnicodeDecodeError: pass
chars.update(chr(c) for c in range(0x20, 0x7F))    # ASCII
chars.update(chr(c) for c in range(0xA0, 0x180))   # Latin-1 + Latin Extended-A
chars.update(chr(c) for c in range(0x3000, 0x3040))  # CJK symbols and punctuation
chars.update(chr(c) for c in range(0xFE10, 0xFE20))  # vertical forms
chars.update(chr(c) for c in range(0xFE30, 0xFE50))  # CJK compatibility forms (vertical brackets)
chars.update(chr(c) for c in range(0xFF00, 0xFF5F))  # fullwidth forms
chars.update('·—–‘’“”…→←↑↓×≈ΩΦ')
open(out, 'w', encoding='utf-8').write(''.join(sorted(c for c in chars if c.isprintable() or c == ' ')))
print(f'charset: {len(chars)} characters')
PYEOF
  sub() {   # sub <in> <out>
    if [ ! -s "$OUT/$2" ] || [ "$CHARS" -nt "$OUT/$2" ]; then
      echo "subset $2"
      "$PY" -m fontTools.subset "$OUT/$1" --text-file="$CHARS" --output-file="$OUT/$2.part" \
        --layout-features='*' --no-hinting --notdef-outline --name-IDs='*' && mv "$OUT/$2.part" "$OUT/$2"
    fi
  }
  sub NotoSerifSC-VF.ttf NotoSerifSC-sub.ttf
  sub NotoSansSC-VF.ttf NotoSansSC-sub.ttf
fi
ls -la "$OUT"
