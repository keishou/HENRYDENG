"""Vocal separation with a UVR MDX-Net ONNX model (Kim_Vocal_2), CPU onnxruntime.

Reads a stereo 44.1k/48k wav, writes vocals + instrumental wavs at 44.1 kHz.
Analysis-only copies: the song itself is never modified.

usage: python3 mdx_separate.py in.wav model.onnx out_dir
"""
import sys, os, time
import numpy as np
import soundfile as sf
import librosa
import onnxruntime as ort

src, model_path, out_dir = sys.argv[1:4]
os.makedirs(out_dir, exist_ok=True)

# Kim_Vocal_2 parameters from TRvlvr/application_data mdx_model_data.json
N_FFT, HOP, DIM_F, DIM_T, COMP = 7680, 1024, 3072, 2 ** 8, 1.009
SR = 44100

x, sr = sf.read(src, always_2d=True)
x = x.T.astype(np.float32)  # [2, n]
if sr != SR:
    x = librosa.resample(x, orig_sr=sr, target_sr=SR, res_type="soxr_hq")
n_sample = x.shape[1]
peak = np.abs(x).max()
x = x / max(peak, 1e-9)

chunk = HOP * (DIM_T - 1)
trim = N_FFT // 2
gen = chunk - 2 * trim
pad = gen - n_sample % gen
mix_p = np.concatenate([np.zeros((2, trim), np.float32), x, np.zeros((2, pad), np.float32), np.zeros((2, trim), np.float32)], 1)

win = np.hanning(N_FFT + 1)[:-1].astype(np.float32)  # periodic hann == torch.hann_window


def stft(w):  # w [2, chunk] -> [1, 4, DIM_F, DIM_T]
    S = librosa.stft(w, n_fft=N_FFT, hop_length=HOP, window=win, center=True, pad_mode="reflect")  # [2, 3841, 256]
    S = S[:, :DIM_F, :]
    out = np.stack([S[0].real, S[0].imag, S[1].real, S[1].imag], 0)[None].astype(np.float32)
    return out


def istft(o):  # [1, 4, DIM_F, DIM_T] -> [2, chunk]
    nb = N_FFT // 2 + 1
    o = o[0]
    L = o[0] + 1j * o[1]
    R = o[2] + 1j * o[3]
    S = np.zeros((2, nb, o.shape[-1]), np.complex64)
    S[0, :DIM_F] = L
    S[1, :DIM_F] = R
    return librosa.istft(S, n_fft=N_FFT, hop_length=HOP, window=win, center=True, length=chunk)


so = ort.SessionOptions()
so.intra_op_num_threads = 4
sess = ort.InferenceSession(model_path, so, providers=["CPUExecutionProvider"])
iname = sess.get_inputs()[0].name
print("model input", sess.get_inputs()[0].shape, "output", sess.get_outputs()[0].shape)

res = []
t0 = time.time()
for i in range(0, n_sample + pad, gen):
    w = mix_p[:, i:i + chunk]
    spec = stft(w)
    out = sess.run(None, {iname: spec})[0]
    wav = istft(out)
    res.append(wav[:, trim:-trim])
    print(f"chunk {i / SR:7.1f}s  {time.time() - t0:5.1f}s", flush=True)
voc = np.concatenate(res, 1)[:, :n_sample] * COMP * peak
inst = x * peak - voc
sf.write(os.path.join(out_dir, "vocals.wav"), voc.T, SR, subtype="FLOAT")
sf.write(os.path.join(out_dir, "instrumental.wav"), inst.T, SR, subtype="FLOAT")
print("done", voc.shape, time.time() - t0)
