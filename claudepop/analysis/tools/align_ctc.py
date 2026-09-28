"""CTC forced alignment of the lyrics on the separated vocal stem with a NeMo (Fast)Conformer CTC model
exported to ONNX by sherpa-onnx (downloaded from the k2-fsa/sherpa-onnx GitHub release "asr-models").

Features re-implement NeMo's AudioToMelSpectrogramPreprocessor (16 kHz, 25 ms hann / 10 ms hop, n_fft 512,
80 slaney mels, preemph 0.97, log(x + 2^-24), per-feature normalisation). Output frames are 80 ms (subsampling 8).
Lyrics are tokenised by greedy longest match over the model's SentencePiece vocabulary.

usage: python3 align_ctc.py vocals.wav lyrics.js model_dir out.json
"""
import sys, json
import numpy as np
import soundfile as sf
import librosa
import onnxruntime as ort
from lyrics_lex import load_lines

voc_path, ly_path, model_dir, out_path = sys.argv[1:5]
NSHIFT = int(sys.argv[5]) if len(sys.argv) > 5 else 1
SR = 16000
v, sr = sf.read(voc_path, always_2d=True)
x = librosa.resample(v.mean(1), orig_sr=sr, target_sr=SR).astype(np.float32)
x = x / (np.abs(x).max() + 1e-9) * 0.9

onnx = [f for f in ("model.onnx", "model.int8.onnx") if __import__("os").path.exists(f"{model_dir}/{f}")][0]
sess = ort.InferenceSession(f"{model_dir}/{onnx}", providers=["CPUExecutionProvider"])
vocab = [l.rsplit(" ", 1)[0] for l in open(f"{model_dir}/tokens.txt", encoding="utf8").read().splitlines()]
BLANK = len(vocab) - 1
tok2id = {t: i for i, t in enumerate(vocab)}
MEL = librosa.filters.mel(sr=SR, n_fft=512, n_mels=80, fmin=0, fmax=SR / 2, norm="slaney", htk=False)
WIN = np.hanning(400).astype(np.float32)  # torch.hann_window(400, periodic=False)


def features(seg):
    seg = np.append(seg[0], seg[1:] - 0.97 * seg[:-1])
    S = librosa.stft(seg, n_fft=512, hop_length=160, win_length=400, window=WIN, center=True, pad_mode="constant")
    m = np.log(MEL @ (np.abs(S) ** 2) + 2 ** -24)
    m = (m - m.mean(1, keepdims=True)) / (m.std(1, keepdims=True) + 1e-5)
    return m.astype(np.float32)


def logprobs(a, b):
    seg = x[int(a * SR):int(b * SR)]
    f = features(seg)
    lp = sess.run(None, {"audio_signal": f[None], "length": np.array([f.shape[1]], np.int64)})[0][0]
    return lp  # [T, V]


def tokenize(text):
    """greedy longest-match SentencePiece-style tokenisation; returns list of (token_id, word_index)."""
    out = []
    for wi, w in enumerate(text.split()):
        s = "▁" + w
        i = 0
        while i < len(s):
            for j in range(len(s), i, -1):
                if s[i:j] in tok2id:
                    out.append((tok2id[s[i:j]], wi))
                    i = j
                    break
            else:
                if s[i] == "▁":
                    i += 1
                    continue
                out.append((tok2id.get(s[i], 0), wi))
                i += 1
    return out


def ctc_align(lp, ids):
    """Viterbi forced alignment; returns per-token (first_frame, last_frame)."""
    T = lp.shape[0]
    L = len(ids)
    S = 2 * L + 1
    lab = np.full(S, BLANK)
    lab[1::2] = ids
    NEG = -1e30
    dp = np.full((T, S), NEG)
    bp = np.zeros((T, S), np.int32)
    dp[0, 0] = lp[0, BLANK]
    if S > 1:
        dp[0, 1] = lp[0, lab[1]]
    for t in range(1, T):
        prev = dp[t - 1]
        c0 = prev
        c1 = np.concatenate([[NEG], prev[:-1]])
        c2 = np.concatenate([[NEG, NEG], prev[:-2]])
        allow2 = np.zeros(S, bool)
        allow2[3::2] = lab[3::2] != lab[1:-2:2]
        c2 = np.where(allow2, c2, NEG)
        stack = np.stack([c0, c1, c2])
        k = stack.argmax(0)
        dp[t] = stack.max(0) + lp[t, lab]
        bp[t] = k
    s = S - 1 if dp[T - 1, S - 1] >= dp[T - 1, S - 2] else S - 2
    path = np.zeros(T, np.int32)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= bp[t, s]
    spans = {}
    for t, s in enumerate(path):
        if s % 2 == 1:
            j = s // 2
            a, b = spans.get(j, (t, t))
            spans[j] = (min(a, t), max(b, t))
    score = float(dp[T - 1, path[-1]])
    return [spans.get(j, (None, None)) for j in range(L)], score


lines = load_lines(ly_path)
GAP, PAD = 0.9, 0.8
groups, cur = [], [0]
for i in range(1, len(lines)):
    if lines[i]["start"] - lines[i - 1]["end"] >= GAP:
        groups.append(cur)
        cur = []
    cur.append(i)
groups.append(cur)

FR = 0.08
res = []
for gi, g in enumerate(groups):
    a = lines[g[0]]["start"] - PAD
    b = lines[g[-1]]["end"] + PAD
    if gi > 0:
        a = max(a, lines[groups[gi - 1][-1]]["end"] + 0.05)
    if gi + 1 < len(groups):
        b = min(b, lines[groups[gi + 1][0]]["start"] - 0.05)
    a = max(0.0, a)
    ids, owners = [], []
    for li in g:
        text = lines[li]["text"].replace("“", "").replace("”", "").replace("’", "'")
        for tid, wi in tokenize(text):
            ids.append(tid)
            owners.append((li, wi))
    runs = []
    for k in range(NSHIFT):
        a_k = a + k * FR / NSHIFT
        lp = logprobs(a_k, b)
        spans, score = ctc_align(lp, ids)
        runs.append([(None if f0 is None else a_k + f0 * FR, None if f1 is None else a_k + (f1 + 1) * FR) for f0, f1 in spans])
        if k == 0:
            hyp = "".join(vocab[i] for i in lp.argmax(1) if i != BLANK).replace("▁", " ")
            score0 = score
    toks = []
    for j, (tid, (li, wi)) in enumerate(zip(ids, owners)):
        ts = [r[j][0] for r in runs if r[j][0] is not None]
        es = [r[j][1] for r in runs if r[j][1] is not None]
        toks.append({"tok": vocab[tid], "line": li, "word": wi, "t": float(np.median(ts)) if ts else None,
                     "e": float(np.median(es)) if es else None, "t_all": ts})
    res.append({"group": gi, "lines": g, "win": [a, b], "score": score0, "tokens": toks, "greedy": hyp})
    print(f"group {gi} lines {g[0]}-{g[-1]} win {a:.2f}-{b:.2f} score {score0:.1f}", flush=True)
json.dump(res, open(out_path, "w"))
