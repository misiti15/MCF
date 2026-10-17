# swarm1017 follow-up (owner decisions Q9=B, Q10=A, Q11=A, 2026-10-17) - PRE-DECLARATION

*Educational only - not financial advice. History backtests only (rule 7): nothing here is paper or live.*

Written 2026-10-17 before any of the scoring below was run. Changes only by dated amendments at the end.

## Q9 - locked-block look 1 for three near-miss lineages (lead's delegate)
Versions, scored exactly as frozen (no edits, no tuning, each scored ONCE):
| id | module (frozen 2026-10-17) | side/geom | window | universe / selection |
|---|---|---|---|---|
| RST1 | rework-st/modules/RST1-l3fromopen-spyup-pm-t05s1-short.py | short t05s1 | 1335-1500 | min_adv 0, gap <= -2.6574 prefilter, first bar per symbol-day (rework-st/verify_modules.py procedure, SPY fromOpen merged as spy_fo) |
| ETF-ADX | arena-index-etf/near_miss/AR-ETF-late-dip-adx-long.py | long t05s1 | 1400-1500 (15:00 incl.) | arena universe adv20 >= 95M, module SYMBOLS (ETF list), first bar per symbol-day (combine.trades) |
| AM-GAPDN | final/modules/AR-AM-gapdown-capitulation.py (= arena-am-long/near_miss) | long t1s1 | 950-1100 | arena universe adv20 >= 95M, first bar per symbol-day |

- Data: research/history2y/data/locked (2024-11-01..2025-02-28), loaded through history2y/lib.load_month with
  MCF_HIST_ALLOW_LOCKED=1 set only in the one scoring process (followup/locked_score.py), on the lead's behalf.
- Costs: RST1 - its frozen scorer (gates.prod_r with tod entry costs) AND the stricter arena cost (x3 on the extended
  tier, |gap| >= 20% or price < $5); both are reported and both must pass. Arena modules - arena.data.outcomes (x3 tier).
- Regimes: lib.regimes(include_locked=True) - tercile cut points from the open history only.
- **Look-1 pass (rules 18/19), all required:** n >= 30; exp > 0; day-clustered t >= 1.0; exp > 0 in up AND down
  sessions with n >= 30 each (gates.regime_split; a regime with n < 30 = not passed); excess over the same-minute
  random control > 0. Reported too: flat sessions, ex-best-day, top-3-day share, per month.
- Whatever the result, look 1 is spent for these three lineages (RST1 lineage = L3/ST rework; ETF-ADX = arena-index-etf;
  AM-GAPDN = arena-am-long). A look-1 pass does NOT clear their history try-count bars (5.03 / 5.00 / 4.62).

## Q10 - decision-time "skip trades against the index" filter (open history only, never the locked block)
- Setups: the lab setups in config/default.yaml, account_testing.yaml, account_testing2.yaml that belong to the
  swarm1017 rework parent families, each at its configured window / min_adv / prefilter / refire and module GEOM:
  MF (MF1-5 + FD), NS (NS1-5, RW6G1 + FD), RW (RW1-7 FD), ST (ST1-8 FD), L3 (3 FD), CWT (all Testing-2 CWT modules),
  MISC (exhaustion_short + FD, LIQ x2). heat_fade (type heat, not a lab module) is not included.
- Trades: first bar per symbol-day (or refire_select cooldown 1 where refire is set), arena outcomes (prod_r + tod
  entry cost + x3 extended tier). Split: train <= 2025-12, valid 2026-01..2026-10-07.
- Context at the decision bar (same date, same bar close): SPY fromOpen, QQQ fromOpen, the stock's sector ETF fromOpen
  (static map research/bdi/indexlink/linkage.csv `sector_etf`, fallback SPY; caveat: the map was estimated on the open
  history, a mild look-ahead), breadth = share of adv20 >= 95M names with fromOpen > 0.
- Filters (skip = drop the trade): longs skipped when I < -X, shorts when I > +X.
  I in {SPY, QQQ, ANY (SPY or QQQ against), SEC}; X in {0.25, 0.50, 0.75, 1.00}% -> 16.
  Breadth: longs skipped when breadth < b, shorts when breadth > 1 - b, b in {0.25, 0.35, 0.45} -> 3.
  19 filters x 7 families = 133 family configurations (the gate); per-setup rows are diagnostics, also counted.
- N = 133 + 19 x (number of setups) + the sibling lineages ix-gate 912 + regime1009 1,052. Bar max(1.5, sqrt(2 ln N)).
- Per family x filter: base vs kept (n, exp, day-clustered t), blocked trades' exp and t, train / valid, up / flat /
  down (end-of-day class, lib.regimes), walk-forward share, random baseline = 1,000 random skips of the same number of
  trades (seed 20261017; percentile of the kept exp), excess over same-minute control.
- **"Helps"** = kept exp > base exp in train AND valid, and above the 95th percentile of random skips.
- **"Passes"** = helps, and the filtered family list itself clears the history gates: exp > 0, day-clustered t >= bar,
  up AND down exp > 0 (n >= 30), walk-forward >= 0.6. A filter that only "helps" goes to the backlog, not live.

## Q11 - exits on 1-minute paths (open history only)
- Same trades as Q10. Path: data/cache_hist/1Min, from the minute after the decision bar close to 15:55; entry = the
  decision bar close (lab convention); R = 0.25 x daily ATR. Stop first inside a bar; a gap through the stop fills at
  the minute open; target is a limit (fills at the target); otherwise flat at the 15:55 close. Stop moves (breakeven /
  trail) take effect from the next minute (as mcf/backtest/engine.py and runner.manage). Costs as prod_r: entry 1c+1bps
  x tod multiplier, exit 1c+1bps except on targets, +2c on stop / breakeven / trail fills, x3 extended tier.
- Baseline = the module geometry on the same 1-minute paths (parity vs the frames' 5-minute r reported).
- (a) breakeven: be_at_r in {0.5 (asked), 0.25, 0.75 (plateau)} for MF1-5 parent + FD (10 setups) -> 30.
- (b) trailing for CWT12 / CWT14 longs: target kept + trail 1R after +1R (b0, a no-op if target <= 1R), and target
  removed with trail_r x trail_after in {0.5, 1.0} x {0.5, 1.0} (b1-b4) -> 5 per setup.
- (c) 0.5R stop by decision-time day class (SPY fromOpen at the decision bar vs the trade side: with > +0.25%,
  against < -0.25%, flat between), applied in class k in {with, against, flat, all}; target kept; families MF, NS, RW,
  ST, L3, CWT -> 24.
- Pass: variant minus baseline > 0 in train AND valid, paired day-clustered t of the difference >= bar
  max(1.5, sqrt(2 ln N)), N = all Q11 configurations; and up / down split reported. Live support checked against
  mcf/execution/runner.py and mcf/strategies (be_at_r / trail_r / trail_after_r keys).

## Amendments
(none yet)
