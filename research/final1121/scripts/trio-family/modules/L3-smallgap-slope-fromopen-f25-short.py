"""L3-smallgap-slope-fromopen-f25-short - trio-family sibling (overnight 2026-11-21, research only, NOT live).
Derived from L3-gap-slope-fromopen-FD (parent untouched; this is a separate setup, not a gap widening of L3):
smaller gap-downs -2.657 < gap <= -1.5 that L3 never takes, sma20 slope > 0.3724, fromOpen > 2.5. 1.4% symbol-day overlap
with the trio. Short, t1s1, window [950, 1500], refire cooldown 1. Near-miss: FIT -0.138, CHECK -0.049, T2 -0.024.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["-2.657 < gap <= -1.5", "sma20_slope_pct > 0.3724", "fromOpen > 2.5", "full day: bar close 09:50-15:00 ET"]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        g = c("gap")
        return (g > -2.6573517322540283) & (g <= -1.5) & (c("sma20_slope_pct") > 0.37244729995727527) & (c("fromOpen") > 2.5)
