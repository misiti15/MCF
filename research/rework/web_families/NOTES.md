# Rule-18 rework of the 5 failed Reddit/web families (key: web_families)

*Educational only — not financial advice.*

## Data and guard rails (fixed before any run, 2026-10-06)
- Harness: `research/reddit_bt/common.py` fills and production costs (1c + 1 bps per side, +2c on stops, 3c on
  extended-tier names; next-bar / stop entries, stop-first, gaps through stops at the open, flat 15:55, no fills before 09:50).
- `safe.py` patches the bar loader: `data/cache_q2` raises, parquet rows >= 2026-09-16 are filtered out by the reader
  and asserted absent; no unlock env var may be set. Only train (2026-07-15..08-25, 30 sessions) and valid
  (08-26..09-15, 14 sessions) are scored. Holdouts untouched (the lead scores finalists once).
- Search on TRAIN, choose on VALID. Every configuration run (including plateau neighbours added later) is counted
  in `results.json`.
- Finalist gate (mcf/research/backlog.py + task): train exp_r > 0 and valid exp_r > 0 after costs, valid n >= 30,
  valid day-clustered t >= 1.5, mean valid exp_r of the one-step neighbours > 0 (plateau, numeric knobs only),
  valid exp_r > same-side / same-session / same-minute random-symbol baseline from the same universe with the same
  stop/target ATR distance and trade management (5 reps). Max 3 finalists.
- Selection order among gate-passers: highest valid day-clustered t.

## T4 relative strength (priority) — `t4_rs.py`
Base = original `c0.5_late_1R` (reproduced exactly: train n 218 -0.0384R, valid n 104 +0.1874R t 1.82).
Stage A (singles, one knob from base; 46 configs incl. base):
- c 0.25 / 0.375 / 0.625 / 0.75 / 1.0
- market filter: vwap-only, ema-only, none, QQQ (vwap+ema), sector-ETF (vwap+ema)
- RS mode: open (drop RS30 check), r60, r30
- bench: sector ETF (RS vs sector ETF instead of SPY); bench sector + sector market filter
- beta 1.0; daily trend off; VWAP-side condition off
- rvol 0 (off) / 1.0 / 1.5 / 2.0
- window start 599 / 614 / 644 / 659; window end 659 / 674 / 719 / 749 / 779 (signal-bar minutes)
- stop 0.2 / 0.3 / 0.35 ATR; target 0.75 / 1.5 / 2.0 R
- cap 5 / 20; long only; short only
- add one library condition: gap in direction; close beyond the 30-min opening range; close beyond prior-day high/low
- EMA length swap in the market filter: 5/13, 20/50
Stage B (pairs): the 6 best stage-A singles by TRAIN exp_r (train n >= 60), all pairs on different knobs (<= 15).
Stage C (plateau): for any config with train > 0, valid > 0, valid n >= 30, its missing one-step numeric neighbours
(c, rvol, w0, w1, stop, tgt, cap) are run and counted.

## T2 ORB — `t2_orb.py` (48 + up to 6)
OR length {15, 20, 30} min x trigger {5-min close (orig), 1-min close, 1-min close + volume, 5-min close + volume}
x target {0.5, 1.0} x OR width x stop {opposite side, midpoint}. Volume confirmation: trigger bar volume >= 1.5 x
mean of the previous 10 bars of the same size. No trigger after 12:00, one trade per symbol per day, top300.
Then the 3 best by train exp_r get the OR-width filter (0.25..1.0 ATR) and a 60-min time stop (6).

## T3 RVOL consolidation — `t3_rvol.py` (54 + 6)
m = 2, 1R exit, side {long, short} x N {6, 9, 12} x k {0.2, 0.25, 0.35} x window {am 10:00-11:30, mid 11:30-13:30,
pm 13:00-15:00} = 54; then the 6 best by train exp_r (n >= 30) with the VWAP-side condition dropped (6).

## T5 inside bar — `t5_ib.py` (54)
Mother-bar range >= {0.15, 0.25, 0.35} x daily ATR x stop = max(inside-bar range, f x ATR) for f {0.10, 0.15,
0.25} x target {1, 1.5, 2} R x trend filter {on, off(OCO)}; top300, no time stop.

## T7 noise band — `t7_nb.py` (36 + 6)
Pooled SPY + QQQ + IWM. interval {30, 60} x lookback {10, 14, 20} x exit {check (band/VWAP stop intrabar + check
exit), trail1 (1R trail after 1R), trail05 (0.5R after 0.5R), faithful0.3 / faithful0.5 / faithful0.75 (band
evaluated only at checks, disaster stop at x ATR)} = 36; plus long-only for the 6 exits at i30 n14 (6).

## Global indicator-length swap (all families at once)
Each family's best-by-train config re-run with daily ATR(10) and ATR(20) instead of ATR(14) (every family at the
same time, 2 x 5 = 10), and EMA 5/13 and 20/50 in place of 9/21 in t5 (t4 covered in stage A) (2).

## Results
See bottom section (filled after the runs) and `results.json`.
