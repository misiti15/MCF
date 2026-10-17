"""RWR1-exh150-gapdn-spyup-pm-short-t05s1 - rework of RW2-exhaustion-noon-adv150-short(-FD) (swarm1017/rework-rw, 2026-10-17).
RW2's exhaustion short (RSI5 > 90, > 1% above the 5-min SMA20, bearish RSI divergence, ADV >= 150M) restricted to names
that GAPPED DOWN more than 1% while SPY is more than 0.5% above its open, 13:00-15:00 bar close, target 0.5R / stop 1R.
Open history, production cost (prod_r, tod entry costs), first signal per symbol-day, min_adv 150M:
  train 2024-10..2025-12 (locked 2024-11..2025-02 excluded): n 326, exp +0.122R, day-t 2.46
  valid 2026-01..2026-10-07: n 328, exp +0.182R, day-t 2.97; all n 654 (78 sessions), exp +0.152R, day-t 3.83
  regime up/flat/down +0.149/+0.134/+0.197R (n up 534, down 64: pass), walk-forward share 0.80,
  ex-best-day +0.120R, excess vs same-minute random +0.131R (t 4.20), win rate 74%.
STATUS: FAILS the try-count bar (t 3.83 < 5.25; exhaustion lineage N ~967,000). Clustered: 654 trades on 78 sessions
(~8 per session, nearly all on up-tape afternoons). Not for live funds. Research record / backlog only.
Live note: needs `spy_fo` (SPY % from today's open at this bar) in the lab frame - LabStrategy does not provide it
(code needed: read ctx.peers['SPY']). Without the column the mask is all False (fail-safe).
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "RSI(5) > 90",
    "close > 1% above the 5-min SMA20",
    "bearish RSI divergence (bear_div)",
    "gapped down more than 1% at the open",
    "SPY > 0.5% above its open at this bar [live code needed: spy_fo]",
    "ADV >= 150M (set min_adv in the YAML)",
    "window: bar close 13:00-15:00 ET (YAML window [1300, 1500])",
]


def mask(df) -> np.ndarray:
    if "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
    c = {k: df[k].to_numpy(dtype=float) for k in ("rsi5", "sma20_dist_pct", "bear_div", "gap", "spy_fo", "tod")}
    with np.errstate(invalid="ignore"):
        return ((c["rsi5"] > 90) & (c["sma20_dist_pct"] > 1.0) & (c["bear_div"] > 0) & (c["gap"] < -1)
                & (c["spy_fo"] > 0.5) & (c["tod"] >= 1300) & (c["tod"] <= 1500))
