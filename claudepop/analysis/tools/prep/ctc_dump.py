import sys, numpy as np
sys.argv0=sys.argv; sys.argv=['x','/tmp/claude-0/-home-user-HENRYDENG/7f8d1921-66d2-537c-b24c-b53f151ed290/scratchpad/stems/vocals.wav','/home/user/johnheibel/pdoomvideo/src/lyrics.js',sys.argv0[1],'/dev/null','1']; a,b=float(sys.argv0[2]),float(sys.argv0[3])

src=open('/home/user/HENRYDENG/claudepop/analysis/tools/align_ctc.py').read().split('lines = load_lines(ly_path)')[0]
exec(src)
lp=logprobs(a,b)
for t in range(lp.shape[0]):
    top=np.argsort(-lp[t])[:3]
    s=' '.join(f'{vocab[i]}:{np.exp(lp[t,i]):.2f}' for i in top)
    print(f'{a+t*0.08:7.2f} {s}')
