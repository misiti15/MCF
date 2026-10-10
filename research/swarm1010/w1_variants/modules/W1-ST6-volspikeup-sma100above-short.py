"""W1-ST6-volspikeup-sma100above-short - W1 variant sweep candidate (swarm 2026-10-10, research/swarm1010/w1_variants/NOTES.md).
ST6 (volume spike above 2x on a bar above VWAP, stock down > 3% from the open after a gap up > 1%) plus the
layer 'close above its 5-min SMA100' (SMA trend layer 'against', one-step variant of the coordinate search).
Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Full day: YAML window [950, 1500], min_adv 95000000.
Open two-year lab history (426 sessions, locked block excluded, production costs): n 237 (0.56/day), exp +0.171R, day-clustered t 3.23; up +0.150 / down +0.175; walk-forward + share 0.75; plateau mean +0.118; ex-best-day +0.150; busiest day 7.6%.
LIVE-PROBATION candidate only: t is below the try-count bar t_required = 4.837 (lineage N 120,500 + 33). NOT scored on the
rule-19 locked block (the lead scores it once).
LIVE NEEDS the column 'sma100_dist_pct' = (close / SMA100(close) - 1) * 100 on 5-min closes, computed on the same
history as the other indicators (PRIOR5_BARS = 60 prior bars + today's bars; NaN until today's 40th bar, ~12:50 ET).
The live frame does not carry it yet (mcf.research.setup_lab.extra_features); without it this mask is all False
(fail-safe). Verified against the scan on live-shaped frames: research/swarm1010/w1_variants/verify.json.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "volumeRatio crosses above 2.0 on a bar above VWAP",
    "stock down > 3% from the open",
    "gap up > 1%",
    "close above its 5-min SMA100",
    "full day: bar close 09:50-15:00 ET (SMA100 exists from ~12:50)",
]


def mask(df) -> np.ndarray:
    n = len(df)
    if "sma100_dist_pct" not in df:
        return np.zeros(n, dtype=bool)    # fail safe: the SMA100 layer cannot be computed
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        new = np.r_[True, key[1:] != key[:-1]]
    else:
        new = np.r_[True, np.zeros(max(0, n - 1), bool)]

    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        p[new] = np.nan
        return p
    c, atr = col("close"), col("atr_d")
    z = (c - c / (1 + col("vwapDistPct") / 100)) / atr
    vr = col("volumeRatio")
    with np.errstate(invalid="ignore"):
        return ((vr > 2.0) & (prev(vr) <= 2.0) & (z > 0) & (col("fromOpen") < -3.0) & (col("gap") > 1.0)
                & (col("sma100_dist_pct") > 0))
