"""W1-ST1-ordn-sma100below-long - W1 variant sweep candidate (swarm 2026-10-10, research/swarm1010/w1_variants/NOTES.md).
ST1 (close breaks below the 09:30-10:00 opening-range low, stock down > 3% from the open, volumeRatio >= 1.5,
inside the prior-day range) plus the layer 'close below its 5-min SMA100' (one-step variant).
Side long, exit t05s1 (R = 0.25 x daily ATR, exit by 15:55). Full day: YAML window [950, 1500], min_adv 95000000.
Open two-year lab history (426 sessions, locked block excluded, production costs): scan n 567 (1.33/day), exp +0.075R, day-clustered t 2.29; up +0.111 / down +0.094; walk-forward + share 0.688;
plateau mean +0.028; ex-best-day +0.070; busiest day 4.4%. This module's own list (frame-column opening range):
n 561, +0.073R, t 2.20, up +0.114 / down +0.089, WF 0.688 (verify.json). Time-only control (no SMA100 side, same bars): +0.061R t 1.55 - most of the gain is the afternoon restriction the SMA100 layer implies.
LIVE-PROBATION candidate only: t is below the try-count bar t_required = 4.837 (lineage N 120,500 + 32). NOT scored on the
rule-19 locked block (the lead scores it once).
LIVE NEEDS the column 'sma100_dist_pct' = (close / SMA100(close) - 1) * 100 on 5-min closes, computed on the same
history as the other indicators (PRIOR5_BARS = 60 prior bars + today's bars; NaN until today's 40th bar, ~12:50 ET).
The live frame does not carry it yet (mcf.research.setup_lab.extra_features); without it this mask is all False
(fail-safe). Verified against the scan on live-shaped frames: research/swarm1010/w1_variants/verify.json.
Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "t05s1"
LAYERS = [
    "close crosses below the 09:30-10:00 opening-range low (after 10:00)",
    "stock down > 3% from the open",
    "volumeRatio >= 1.5",
    "close inside the prior-day range",
    "close below its 5-min SMA100",
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

    def ffill(x):  # forward fill within the symbol-day
        idx = np.where(np.isfinite(x), np.arange(n), -1)
        idx = np.maximum.accumulate(idx)
        out = np.where(idx >= 0, x[np.maximum(idx, 0)], np.nan)
        start = np.maximum.accumulate(np.where(new, np.arange(n), 0))
        out[idx < start] = np.nan
        return out
    c, atr, tod = col("close"), col("atr_d"), col("tod")
    lod = c - col("dist_lod_atr") * atr
    pdh = c + col("dist_pdh_atr") * atr
    pdl = c - col("dist_pdl_atr") * atr
    orl = ffill(np.where(tod == 1000, lod, np.nan))      # opening range 09:30-10:00
    x = c - orl
    with np.errstate(invalid="ignore"):
        return ((x < 0) & (prev(x) >= 0) & (tod > 1000) & (col("fromOpen") < -3.0) & (col("volumeRatio") >= 1.5)
                & (c >= pdl) & (c <= pdh) & (col("sma100_dist_pct") < 0))
