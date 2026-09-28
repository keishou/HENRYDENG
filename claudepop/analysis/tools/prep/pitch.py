import numpy as np, soundfile as sf, librosa
v,sr=sf.read('stems/vocals.wav'); v=v.mean(1)
y=librosa.resample(v,orig_sr=sr,target_sr=22050)
f0,vflag,vprob=librosa.pyin(y,fmin=110,fmax=1100,sr=22050,frame_length=2048,hop_length=256)
rms=librosa.feature.rms(y=y,frame_length=1024,hop_length=256)[0]
np.savez('vocal_pitch.npz',f0=f0,vflag=vflag,vprob=vprob,rms=rms,hop=256,sr=22050)
print('done', np.nanmedian(f0), np.mean(vflag))
