"""RWR3-ns3-adv150-qqqup-early-short-refire - rework of RW4-ns3-adv150-short(-FD) (swarm1017/rework-rw, 2026-10-17).
RW4 (close crosses above VWAP on a stock down > 2% from the open, above its 5-min SMA50, ADV >= 150M) only while QQQ is
above its open, bar close 09:50-10:30, refire cooldown 1 (as RW4-FD live), target 1R / stop 1R.
Open history, production cost (prod_r, tod entry costs), refire chain (LabStrategy.refire_select, cooldown 1):
  train 2024-10..2025-12 (locked excluded): n 157, exp +0.251R, day-t 2.44
  valid 2026-01..2026-10-07: n 198, exp +0.171R, day-t 1.89; all n 355 (127 sessions), exp +0.206R, day-t 2.97
  regime up/flat/down +0.091/+0.239/+0.290R (n up 117, down 113: pass), walk-forward 0.77, ex-best-day +0.170R,
  excess vs same-minute random +0.266R (t 4.16).
STATUS: FAILS the try-count bar (t 2.97 < 4.83; NS lineage N ~114,000). Best-spread of this family (127 sessions,
both regimes positive), but well short of the bar. Not for live funds. Backlog / Testing-observation candidate only.
Live note: needs `qqq_fo` (QQQ % from today's open at this bar) in the lab frame - LabStrategy does not provide it
(code needed: read ctx.peers['QQQ']). Without the column the mask is all False (fail-safe). YAML: min_adv 150000000,
window [950, 1030], refire: true, refire_cooldown: 1.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "close crosses above VWAP on this bar",
    "stock down > 2% from the open",
    "close above the 5-min SMA50",
    "QQQ above its open at this bar [live code needed: qqq_fo]",
    "ADV >= 150M (set min_adv in the YAML)",
    "window: bar close 09:50-10:30 ET (YAML window [950, 1030]), refire cooldown 1",
]


def mask(df) -> np.ndarray:
    if "qqq_fo" not in df:
        return np.zeros(len(df), dtype=bool)

    def col(k):
        return df[k].to_numpy(dtype=float)

    vwap = col("vwapDistPct")
    p = np.r_[np.nan, vwap[:-1]]
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    tod = col("tod")
    with np.errstate(invalid="ignore"):
        return ((vwap > 0) & (p <= 0) & (col("fromOpen") < -2) & (col("sma50_dist_pct") > 0) & (col("qqq_fo") > 0)
                & (tod >= 950) & (tod <= 1030))
