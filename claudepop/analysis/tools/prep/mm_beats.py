import sys; sys.path.insert(0,'madmom_src')
import numpy as np
from madmom.features.downbeats import RNNDownBeatProcessor, DBNDownBeatTrackingProcessor
from madmom.features.beats import RNNBeatProcessor, DBNBeatTrackingProcessor
import madmom
act = RNNDownBeatProcessor()('pdoom44k.wav')
np.save('mm_dbact.npy', act)
for bpb in ([3,4],[4],[3]):
    p = DBNDownBeatTrackingProcessor(beats_per_bar=bpb, fps=100, min_bpm=55, max_bpm=215)
    r = p(act); np.save(f'mm_db_{"".join(map(str,bpb))}.npy', r)
    b=r[:,0]; d=np.diff(b); print(bpb, len(b), 'median ibi', np.median(d), 60/np.median(d), 'beat nums', np.bincount(r[:,1].astype(int)))
bact = RNNBeatProcessor()('pdoom44k.wav'); np.save('mm_bact.npy', bact)
b = DBNBeatTrackingProcessor(fps=100, min_bpm=55, max_bpm=215)(bact); np.save('mm_beats.npy', b)
d=np.diff(b); print('beats', len(b), np.median(d), 60/np.median(d), b[:8])
