"""L3-gap-slope-atrrec-k09-short - trio-family sibling (overnight 2026-11-21, research only, NOT live).
Derived from L3-gap-slope-fromopen-FD (PROT-06/07/09 parent untouched): same gap (<= -2.657) and sma20-slope (> 0.3724)
layers, but the recovery is measured in daily-ATR units on the stock-days L3 cannot take: fromOpen <= 3.46% AND
(close - open) >= 0.9 x daily ATR (low-volatility / higher-priced names whose recovery is large in ATR terms).
Short, t1s1, window [950, 1500], min_adv 0, refire cooldown 1, prefilter gap_le:-2.6573517322540283.
Tier B (debatable / derived from L3-fromopen): FIT +0.220 (n 382, one-day), CHECK -0.017 (n 224), T2 +0.087 (n 220).
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["gap <= -2.657", "sma20_slope_pct > 0.3724", "fromOpen <= 3.46", "(close - open) / atr_d >= 0.9",
          "full day: bar close 09:50-15:00 ET"]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        fo = c("fromOpen")
        op = c("close") / (1 + fo / 100)
        return ((c("gap") <= -2.6573517322540283) & (c("sma20_slope_pct") > 0.37244729995727527)
                & (fo <= 3.460294628143309) & ((c("close") - op) / c("atr_d") >= 0.9))
