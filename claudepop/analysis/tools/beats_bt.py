"""Beat and downbeat tracking with Beat This! (Foscarin, Schlueter, Widmer, ISMIR 2024; github.com/CPJKU/beat_this),
checkpoint final0, no DBN. Used only as an independent check of the fixed 132 BPM grid and of the bar phase.

usage: python3 beats_bt.py <claudepop_dir> [out_name=beat_this.json]
"""
import sys, json
from beat_this.inference import File2Beats

ROOT = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "beat_this.json"
f2b = File2Beats(checkpoint_path="final0", device="cpu", dbn=False)
beats, downbeats = f2b(f"{ROOT}/out/audio/pdoom_44k.wav")
json.dump({"beats": [round(float(b), 2) for b in beats], "downbeats": [round(float(d), 2) for d in downbeats]},
          open(f"{ROOT}/out/work/analysis/{OUT}", "w"))
print(len(beats), len(downbeats))
