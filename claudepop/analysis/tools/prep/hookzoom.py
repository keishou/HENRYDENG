import sys, json, numpy as np, soundfile as sf, librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
VT=json.load(open(sys.argv[1])); tag=sys.argv[2]
wins=[tuple(map(float,w.split(':'))) for w in sys.argv[3].split(',')]
v,sr=sf.read('stems/vocals.wav'); v=v.mean(1)
m,_=sf.read('pdoom44k.wav'); m=m.mean(1)
P=np.load('vocal_pitch.npz'); f0=P['f0']; tp=np.arange(len(f0))*256/22050
on=np.array(VT['onsets']); T=60/132; T0=0.235
Sref=np.abs(librosa.stft(v[int(20*sr):int(40*sr)],n_fft=1024,hop_length=128)).max()
for (a,b) in wins:
    fig,axs=plt.subplots(3,1,figsize=(24,13),gridspec_kw={'height_ratios':[3,1,1]},sharex=True)
    ax=axs[0]
    seg=v[int(a*sr):int(b*sr)]
    S=librosa.amplitude_to_db(np.abs(librosa.stft(seg,n_fft=1024,hop_length=128)),ref=Sref)
    fq=librosa.fft_frequencies(sr=sr,n_fft=1024); tt=a+np.arange(S.shape[1])*128/sr; sel=(fq>80)&(fq<8000)
    ax.pcolormesh(tt,fq[sel],S[sel],cmap='magma',vmin=-70,vmax=0,shading='auto'); ax.set_yscale('log'); ax.set_ylim(80,8000)
    mm=(tp>=a)&(tp<=b); ax.plot(tp[mm],f0[mm],color='cyan',lw=2)
    for t in on[(on>=a)&(on<=b)]: ax.axvline(t,ymin=0,ymax=0.1,color='lime',lw=3)
    for ax_ in axs:
        k=int(np.ceil((a-T0)/(T/4)))
        while T0+k*T/4<b:
            t=T0+k*T/4; ax_.axvline(t,color='gray' if ax_!=ax else 'w',lw=2.5 if k%16==0 else (1.2 if k%4==0 else .4),alpha=.7)
            if k%4==0 and ax_==ax: ax.text(t+.01,6500,f'b{k//16+1}.{(k//4)%4+1}',color='w',fontsize=12)
            k+=1
    for L in VT['lines']:
        for j,w in enumerate(L['words']):
            if a<=w['t']<=b:
                ax.axvline(w['t'],ymin=0.85,ymax=1,color='yellow',lw=2.5)
                axs[1].axvline(w['t'],color='green',lw=2); axs[1].text(w['t']+.005,0.5+0.2*(j%2),w['w'],fontsize=14,color='darkgreen',fontweight='bold')
                for mname,col,y in [('PS','blue',0.1),('PK','orange',0.2),('FC','purple',0.3)]:
                    if mname in w['est'] and a<=w['est'][mname]<=b: axs[1].plot([w['est'][mname]],[y],marker='v',color=col,ms=9)
    r=librosa.feature.rms(y=seg,frame_length=512,hop_length=128)[0]; axs[1].plot(a+np.arange(len(r))*128/sr,(20*np.log10(r+1e-5)+60)/60,color='k')
    axs[1].set_ylim(0,1.1)
    sm=m[int(a*sr):int(b*sr)]; axs[2].plot(a+np.arange(len(sm))/sr,sm,lw=.3); axs[2].set_title('full mix waveform')
    axs[2].set_xticks(np.arange(np.ceil(a*10)/10,b,0.1),minor=True); axs[2].grid(which='both',axis='x',alpha=.3); axs[2].set_xlim(a,b)
    ax.set_title(f'{tag} zoom {a}-{b}: vocal stem; grid 16ths (b bar.beat); lime=vocal onsets; yellow=word starts')
    plt.tight_layout(); plt.savefig(f'linecheck/zoom_{tag}_{a:06.2f}.png',dpi=55); plt.close()
