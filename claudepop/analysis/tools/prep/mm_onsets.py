import sys; sys.path.insert(0,'madmom_src')
import numpy as np
from madmom.features.onsets import CNNOnsetProcessor, RNNOnsetProcessor, OnsetPeakPickingProcessor
for s in ['instrumental','vocals']:
    act=CNNOnsetProcessor()(f'stems/{s}_s16.wav'); np.save(f'mm_onsetact_{s}.npy',act)
    on=OnsetPeakPickingProcessor(threshold=0.35, smooth=0.0, pre_max=0.02, post_max=0.02, combine=0.03, fps=100)(act)
    np.save(f'mm_onsets_{s}.npy',on); print(s, len(on))
    ract=RNNOnsetProcessor()(f'stems/{s}_s16.wav'); np.save(f'mm_rnnonsetact_{s}.npy',ract)
