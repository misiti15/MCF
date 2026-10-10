"""W1-NS3-vwapreclaim-sma100-vol2-short - W1 variant sweep candidate (swarm 2026-10-10, research/swarm1010/w1_variants/NOTES.md).
NS3 (failed VWAP reclaim on a stock down > 2% from the open) with the 5-min SMA50 layer swapped for SMA100 and
a volume layer volumeRatio >= 2 (two one-step variants of the coordinate search, a stage-2 pair).
Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Full day: YAML window [950, 1500], min_adv 95000000.
Open two-year lab history (426 sessions, locked block excluded, production costs): n 212 (0.50/day), exp +0.139R, day-clustered t 2.53; up +0.133 / down +0.174; walk-forward + share 0.857; plateau mean +0.065; ex-best-day +0.125; busiest day 3.8%.
LIVE-PROBATION candidate only: t is below the try-count bar t_required = 4.221 (lineage N 7,374 + 32). NOT scored on the
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
    "close crosses ABOVE session VWAP on this bar",
    "close above its 5-min SMA100",
    "stock down > 2% from the open",
    "volumeRatio >= 2.0",
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
    v, fo, s100, vr = col("vwapDistPct"), col("fromOpen"), col("sma100_dist_pct"), col("volumeRatio")
    with np.errstate(invalid="ignore"):
        return (v > 0) & (prev(v) <= 0) & (s100 > 0) & (fo < -2) & (vr >= 2.0)
