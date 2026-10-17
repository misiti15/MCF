"""RWR4-ns2-up3-qqqup-slopedn-am-short-t05s1 - rework of RW6-ns2-up3-short(-FD) (swarm1017/rework-rw, 2026-10-17).
RW6 (close crosses above the 5-min SMA50 on a stock up > 3% from the open, RSI14 >= 60) only while QQQ is above its open
and the 5-min SMA20 slope is negative, bar close 09:50-11:00, first signal per symbol-day, target 0.5R / stop 1R.
Open history, production cost (prod_r, tod entry costs), min_adv 95M:
  train 2024-10..2025-12 (locked excluded): n 383, exp +0.125R, day-t 3.30
  valid 2026-01..2026-10-07: n 262, exp +0.108R, day-t 1.52; all n 645 (118 sessions), exp +0.118R, day-t 3.15
  regime up/flat/down +0.116/+0.045/+0.246R (n up 505, down 58: pass), walk-forward 0.78, ex-best-day +0.087R,
  excess vs same-minute random +0.101R (t 4.22), win rate 76%.
STATUS: FAILS the try-count bar (t 3.15 < 4.83). Not for live funds. Research record / backlog only.
Live note: needs `qqq_fo` in the lab frame (code needed: ctx.peers['QQQ']); without it the mask is all False.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "close crosses above the 5-min SMA50 on this bar",
    "stock up > 3% from the open",
    "RSI(14) >= 60",
    "5-min SMA20 slope < 0",
    "QQQ above its open at this bar [live code needed: qqq_fo]",
    "window: bar close 09:50-11:00 ET (YAML window [950, 1100])",
]


def mask(df) -> np.ndarray:
    if "qqq_fo" not in df:
        return np.zeros(len(df), dtype=bool)

    def col(k):
        return df[k].to_numpy(dtype=float)

    s50 = col("sma50_dist_pct")
    p = np.r_[np.nan, s50[:-1]]
    if "symbol" in df and "date" in df:
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    tod = col("tod")
    with np.errstate(invalid="ignore"):
        return ((s50 > 0) & (p <= 0) & (col("fromOpen") > 3) & (col("rsi") >= 60) & (col("sma20_slope_pct") < 0)
                & (col("qqq_fo") > 0) & (tod >= 950) & (tod <= 1100))
