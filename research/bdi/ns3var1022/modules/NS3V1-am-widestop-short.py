"""NS3V1-am-widestop-short - Big Loser VWAP Reclaim Fade, Morning, Wide Stop (research/bdi/ns3var1022, 2026-10-22).
A variant of NS3-failed-vwap-reclaim-short-FD for "more market weather": the same entry, back in the parent's morning
window (bar close 09:50-11:30 ET), refire cooldown 1, and a stop twice as wide at the same $ risk with the target at
the SAME price as NS3's 1R target. Live shape: GEOM t05s1 with YAML `r_atr_frac: 0.5` (R = 0.5 x daily ATR: stop
1R = 0.5 ATR above entry, target 0.5R = 0.25 ATR below entry, exit by 15:55), window [950, 1130], min_adv 95000000,
refire: true, refire_cooldown: 1. Found AFTER the pre-declared grid (post-hoc plateau rows); a near-miss under the
owner's merit rule, below the multiple-testing bars (t 2.15 vs study 3.02 / lineage 4.90). Not in any config.
Check: research/bdi/ns3var1022/verify_module.json (this mask AND the window == the scan's rows).
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"          # with r_atr_frac 0.5 in the YAML: stop 0.5 ATR, target 0.25 ATR (= NS3's 1R target price)
R_ATR_FRAC = 0.5        # documentation only: LabStrategy reads r_atr_frac from the YAML
LAYERS = [
    "price reclaims VWAP on this bar",
    "price above the 5-min 50-bar average",
    "stock down > 2% from the open",
    "09:50-11:30 ET (YAML window [950, 1130])",
    "wide stop: R = 0.5 x daily ATR, target 0.5R (YAML r_atr_frac 0.5, GEOM t05s1)",
]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(k):
        x = col(k)
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    fromOpen, sma50, vwap, tod = col("fromOpen"), col("sma50_dist_pct"), col("vwapDistPct"), col("tod")
    with np.errstate(invalid="ignore"):
        return (vwap > 0) & (prev("vwapDistPct") <= 0) & (sma50 > 0) & (fromOpen < -2) & (tod >= 950) & (tod <= 1130)
