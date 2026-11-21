"""P1 neighbourhood wrapper: L3-gap-slope-lowdist-FD mask with env-free parameters set by the loader (research only)."""
import numpy as np
SIDE = "short"; GEOM = "t1s1"
P = dict(slope=0.37244729995727527, dlo=0.7816761255264282, dhi=0.9764953255653381)
def mask(df):
    c = lambda k: df[k].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (c('sma20_slope_pct') > P['slope']) & (c('dist_lod_atr') > P['dlo']) & (c('dist_lod_atr') <= P['dhi'])
