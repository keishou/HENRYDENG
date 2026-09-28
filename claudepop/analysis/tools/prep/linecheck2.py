import sys, json, numpy as np, soundfile as sf, librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
VT=json.load(open(sys.argv[1])); tag=sys.argv[2]
v,sr=sf.read('stems/vocals.wav'); v=v.mean(1)
P=np.load('vocal_pitch.npz'); f0=P['f0']; tp=np.arange(len(f0))*256/22050
on=np.array(VT['onsets']); pc=np.array(VT['pitch_onsets'])
T=60/132; T0=0.235
wins=[(0,12),(11,23.5),(22.5,35),(34,47),(46,59),(58,70),(69,81),(80,92),(91,103),(102,114),(113,125),(124,136),(135,147),(146,157)]
if len(sys.argv)>3: wins=[wins[int(i)] for i in sys.argv[3].split(',')]
Sref=np.abs(librosa.stft(v[int(20*sr):int(40*sr)],n_fft=2048,hop_length=256)).max()
for (a,b) in wins:
    seg=v[int(a*sr):int(b*sr)]; hop=256
    S=librosa.amplitude_to_db(np.abs(librosa.stft(seg,n_fft=2048,hop_length=hop)),ref=Sref)
    fq=librosa.fft_frequencies(sr=sr,n_fft=2048)
    fig,(ax,ax2)=plt.subplots(2,1,figsize=(28,12),gridspec_kw={'height_ratios':[3,1.3]},sharex=True)
    tt=a+np.arange(S.shape[1])*hop/sr; sel=(fq>80)&(fq<6000)
    ax.pcolormesh(tt,fq[sel],S[sel],cmap='magma',vmin=-70,vmax=0,shading='auto'); ax.set_yscale('log'); ax.set_ylim(80,6000)
    m=(tp>=a)&(tp<=b); ax.plot(tp[m],f0[m],color='cyan',lw=1.5)
    for t in on[(on>=a)&(on<=b)]: ax.axvline(t,ymin=0,ymax=0.1,color='lime',lw=2.5)
    for t in pc[(pc>=a)&(pc<=b)]: ax.axvline(t,ymin=0.1,ymax=0.16,color='deepskyblue',lw=2)
    k=int(np.ceil((a-T0)/(T/2)))
    while T0+k*T/2<b:
        t=T0+k*T/2; ax.axvline(t,color='w',lw=2 if k%8==0 else (.8 if k%2==0 else .3),alpha=.6)
        if k%8==0: ax.text(t+.02,5200,f'bar{k//8+1}',color='w',fontsize=11)
        k+=1
    for L in VT['lines']:
        if L['sub_end']<a or L['sub_start']>b: continue
        ax2.plot([L['sub_start'],L['sub_end']],[1.3,1.3],color='red',lw=5); ax2.text(max(a,L['sub_start']),1.38,f"{L['i']}: {L['text']}  (subtitle)",color='red',fontsize=11)
        ax2.plot([L['start'],L['end']],[1.1,1.1],color='green',lw=5)
        for j,w in enumerate(L['words']):
            ax2.axvline(w['t'],ymin=0,ymax=0.72,color='green',lw=1.8); ax.axvline(w['t'],ymin=0.9,ymax=1,color='yellow',lw=2)
            ax2.text(w['t']+.01,0.15+0.2*(j%3),w['w'],color='darkgreen',fontsize=12,fontweight='bold')
            for mname,col,y in [('PS','blue',0.05),('PK','orange',0.1),('FC','purple',0.15)]:
                if mname in w['est']: ax2.plot([w['est'][mname]],[y],marker='v',color=col,ms=7)
    r=librosa.feature.rms(y=seg,frame_length=1024,hop_length=hop)[0]; ax2.plot(a+np.arange(len(r))*hop/sr, 0.9*(20*np.log10(r+1e-5)+60)/60, color='k', lw=1)
    ax2.set_ylim(0,1.5); ax2.set_xlim(a,b); ax2.set_xticks(np.arange(np.ceil(a*4)/4,b,0.25),minor=True); ax2.grid(which='both',axis='x',alpha=.3)
    ax.set_title(f'{tag} {a}-{b}s  lime=madmom vocal onsets, blue=pitch onsets, yellow/green=final word starts, markers: PS blue, PK orange, FC purple (lag-corrected)')
    plt.tight_layout(); plt.savefig(f'linecheck/{tag}_{a:05.1f}.png',dpi=52); plt.close()
print('ok')
