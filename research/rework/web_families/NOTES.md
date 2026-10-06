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
Stage A (singles, one knob from base; 47 configs incl. base):
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


## Results (train 2026-07-15..08-25, valid 08-26..09-15; costs in; holdouts untouched)

**419 configurations tried in this rework** (t4 188 incl. 132 plateau neighbours, t2 54, t3 60, t5 54, t7 43, global
ATR/EMA swaps 12, finalist ATR-swap checks 8). Lineage total with the original 160: **579**. At p = 0.05, ~21 false
positives are expected from 419 tries, so a single gate pass means little; read the plateau and train columns.
Reproduction: t4 base and t2 or15/c5 reproduce the original numbers exactly; the standalone finalist module
`f_t4_rs.py` reproduces the grid numbers exactly through `common.run`.

### Failures first
| family | configs | valid > 0 | train > 0 | best on valid (n >= 30) | verdict |
|---|---|---|---|---|---|
| T2 ORB | 54 | 0 | 13 | or30 5-min-close+vol t0.5: train -0.010R, valid n 1494 -0.044R t -2.07 | dead. OR 20/30, 1-min close and volume confirmation all lose on valid. Drop. |
| T3 RVOL consolidation | 60 | 1 (n 1) | 26 | N6 k0.2 am short: train -0.023R, valid n 59 -0.026R | dead. Train-positive configs have n < 60 and fail on valid. VWAP-side drop changes nothing. Drop. |
| T5 inside bar | 54 | 3 | 5 | mother >= 0.35 ATR, stop floor 0.25 ATR, 2R: train -0.046R, valid n 59 +0.097R t 0.45 | larger mothers and ATR-floored stops lift it from -0.24R to about 0, but no config is positive on both. Drop. |
| T7 noise band (SPY+QQQ+IWM) | 43 | 1 | 36 | i60 n20 check: train +0.076R, valid n 31 +0.064R t 0.12 | fails t, plateau (neighbours -0.05 / -0.50R) and baseline (+0.23R). Train-positive, valid-negative across the board. Drop. |
| Global swap ATR10 / ATR20 / EMA 5-13 / 20-50 | 12 | 2 | 8 | t4 w0=644,cap=5,long ATR20: train +0.316R, valid n 28 +0.090R (n < 30) | only the t4 config (already positive) stays positive on both; no failed family is revived by a length swap. |

### T4 relative strength: gate passers (4), forwarded 3 (cap; pre-declared order = valid t)
| variant (f_t4_rs.py) | train n / expR / t | valid n / expR / t | valid ex-best-day | plateau valid mean (frac > 0) | neighbours' train mean (frac > 0) | random baseline valid |
|---|---|---|---|---|---|---|
| long_nomf (long only, no market filter) | 244 / +0.050 / 0.57 | 108 / +0.308 / 2.54 | +0.262 | +0.244 (14/14) | +0.000 (6/14) | +0.049 (n 540) |
| long_vwapmf (long, SPY > VWAP) | 178 / +0.009 / 0.09 | 85 / +0.228 / 1.62 | +0.166 | +0.180 (14/14) | -0.036 (3/14) | +0.006 |
| both_sectormf (both sides, sector ETF filter) | 256 / +0.016 / 0.21 | 120 / +0.141 / 1.61 | +0.089 | +0.100 (14/14) | -0.013 (5/14) | -0.034 |
| long_emamf (long, SPY EMA9>21) - not forwarded | 167 / +0.077 / 0.80 | 51 / +0.226 / 1.52 | +0.111 | +0.181 (14/14) | +0.058 (13/14) | +0.042 |

Honest reading:
- The valid window is unusually kind to this family: 177 of 188 t4 configs are positive on valid, but only 88 are on
  train. The edge over the random baseline is the meaningful number (+0.26R for long_nomf), not the raw valid expR.
- Train support is thin. Train t is 0.09 to 0.80, and the train result of long_vwapmf (best-day share 4.5) and
  both_sectormf (1.5) comes from one day; their ex-best-day train expR is negative.
- Only long_emamf has a train plateau, with 13 of 14 neighbours positive on train. It has just 6 valid days, so it
  ranked 4th on valid t and was not forwarded.
- ATR(10)/ATR(20) swap (finalist_checks.json): long_nomf stays positive on both splits (valid +0.27R, t 2.2 / 2.0).
  both_sectormf goes train-negative with ATR20. long_vwapmf weakens to valid t 1.0-1.2.
- What changed vs the original: dropping the SPY market filter and the shorts. Shorts were the losing side on train.
  The sector-ETF RS benchmark did not help (valid +0.138R, train -0.079R); the sector-ETF *market filter* did.
- The sector map is data-driven: the residual correlation after removing SPY, over the warm-up month 06-15..07-14.
  It includes some odd assignments, e.g. AAPL -> XLP. For the Apr-Jun holdout it is a mild look-ahead, but only
  for both_sectormf.
- The three forwarded variants overlap heavily (same entry engine, all long-biased). Treat them as one lineage on
  the holdouts: the look counter applies to the t4 lineage.

Files: `t4_rs.py` (grid engine), `f_t4_rs.py` (finalist module: VARIANTS, NEIGHBORS, FINALISTS, signals(day, v)),
`t2_orb.py`, `t3_rvol.py`, `t5_ib.py`, `t7_nb.py`, `run_t4.py`, `run_fam.py`, `run_swaps.py`, `check_finalists.py`,
`*_results.json` (every config), `results.json` (summary + all counts), `safe.py` / `lib.py` (locked-data guard, runner).
