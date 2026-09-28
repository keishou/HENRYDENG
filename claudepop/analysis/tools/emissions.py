"""CTC emissions (frame log-probabilities) of the separated vocal stem for two independent acoustic models.

  mms  torchaudio.pipelines.MMS_FA: wav2vec2 trained by Meta for multilingual forced alignment (uroman characters)
  w2v  torchaudio.pipelines.WAV2VEC2_ASR_LARGE_LV60K_960H: English character CTC (LibriLight 60k pre-training,
       LibriSpeech 960 h fine-tuning)

Both output one frame per 20 ms. To get finer than 20 ms resolution the input is also run with the audio delayed by
k * 20/NSHIFT ms (k = 0..NSHIFT-1); the aligner takes the median over shifts.
The song is processed in 30 s chunks with 4 s of context on each side (no seams inside the kept part).

Input : out/audio/stems/htdemucs/pdoom_44k/vocals.wav (Demucs v4 htdemucs vocal stem)
Output: out/work/analysis/emis_<model>_s<k>.npy  float16 [frames, labels], plus emis_<model>_labels.json

usage: python3 emissions.py <claudepop_dir> [nshift=4] [models=mms,w2v]
"""
import sys, os, json, time
import numpy as np
import soundfile as sf
import librosa
import torch
import torchaudio

ROOT = sys.argv[1]
NSHIFT = int(sys.argv[2]) if len(sys.argv) > 2 else 4
MODELS = (sys.argv[3] if len(sys.argv) > 3 else "mms,w2v").split(",")
W = f"{ROOT}/out/work/analysis"
torch.set_num_threads(3)

v, sr = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav", always_2d=True)
x = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000, res_type="soxr_hq").astype(np.float32)
SR = 16000
FR = 320  # samples per output frame (20 ms)

for name in MODELS:
    bundle = {"mms": torchaudio.pipelines.MMS_FA, "w2v": torchaudio.pipelines.WAV2VEC2_ASR_LARGE_LV60K_960H}[name]
    model = bundle.get_model(with_star=False) if name == "mms" else bundle.get_model()
    model.eval()
    labels = bundle.get_labels(star=None) if name == "mms" else bundle.get_labels()
    json.dump(list(labels), open(f"{W}/emis_{name}_labels.json", "w"))
    for k in range(NSHIFT):
        out_path = f"{W}/emis_{name}_s{k}.npy"
        if os.path.exists(out_path):
            print("exists", out_path)
            continue
        lead = int(round(k * FR / NSHIFT))  # prepend `lead` zeros: output frame j then starts at song time (j*FR - lead)/SR
        xs = np.concatenate([np.zeros(lead, np.float32), x])
        n_frames = int(np.ceil(len(xs) / FR))
        E = None
        CH, CTX = 30 * SR, 4 * SR
        t_start = time.time()
        for a in range(0, len(xs), CH):
            lo, hi = max(0, a - CTX), min(len(xs), a + CH + CTX)
            with torch.inference_mode():
                em, _ = model(torch.from_numpy(xs[lo:hi])[None])
            em = torch.log_softmax(em[0], dim=-1).numpy()  # MMS already outputs log-probs; idempotent
            if E is None:
                E = np.zeros((n_frames, em.shape[1]), np.float32)
            f_lo = (a - lo) // FR
            f_a, f_b = a // FR, min(n_frames, (a + CH) // FR)
            n = min(f_b - f_a, em.shape[0] - f_lo)
            E[f_a:f_a + n] = em[f_lo:f_lo + n]
        np.save(out_path, E.astype(np.float16))
        json.dump({"lead_samples": lead, "frame_s": FR / SR, "first_frame_start_s": -lead / SR},
                  open(f"{W}/emis_{name}_s{k}.json", "w"))
        print(f"{name} shift {k} ({-lead / SR * 1000:.1f} ms) frames {E.shape} {time.time() - t_start:.0f}s", flush=True)
