# saturday1024 PLAN (written 2026-10-24 before any configuration was scored)

*Educational only — not financial advice.*

Data: gates1021 cached signal tables (history2y 5-min lab frames of the cached live setups, production + tier costs in,
R per trade after costs, entry `tod`, `exit_tod`), train <= 2025-12-31, valid 2026-01-01..2026-10-07. The locked block
2024-11-01..2025-02-28 is never read (`no_locked` asserts it; `MCF_HIST_ALLOW_LOCKED` unset). No holdout is scored.

Books = today's `docs/live/assignments.json` ∩ the cache: Primary 10 of 11 setups (CWT14-failbrk-pdl-p10-lowvol-long
missing), Testing 1 19 of 33, Testing 2 24 of 47 (Graveyard / Gen: 0 cached, not scored). Testing 1 and Testing 2 are
scored the same way (equal weight).

Baseline B0 per book (book simulator, 1R per trade, by entry minute then symbol): live risk checks that can be
replayed without slots — max 3 lots per symbol, no lot against an opposite-side lot, twin block (setup vs its -FD twin /
twin_group on the same symbol), per-setup open-lot cap (P 100 / T1 150 / T2 50), book daily stop at realized
-20R (P) / -120R (T1, T2). Primary has no per-setup stop (live); Testing 1/2 have none since ST-A (2026-10-23).

## Configurations (23)
- **S (per-setup daily stop, latched, realized R at exit time):** Primary S1.5 / S2 / S3 (ST-P 2-year part);
  Testing 1 S2, Testing 2 S2 (ST-A retrospective); **SO** = S2 plus an open-risk bound (stop new entries of a setup once
  realized + open lots x -1R <= -3R; LL-OPEN) on P / T1 / T2. 8 configs.
- **G1 (one lot per symbol across setups,** max_lots_per_symbol 1; gb-1019-twin-setup-exposure /
  nightly-1016-primary-one-lot-per-symbol): P / T1 / T2. 3 configs.
- **G2 (same-bar cluster cap:** a setup takes at most k new entries per decision bar, k = 3 / 5, first by symbol
  order; rule-18 rework of failed loop-1008-exhaustion-cluster-t1 / idea window-open-cluster): 6 configs.
- **G3 (post-peak same-side brake:** once the book's realized R today has peaked at >= X (P 3R, T1/T2 10R) and fallen
  to <= (1-f) x peak, f = 0.5 / 0.33, the side with the larger realized loss since the peak takes no new entries for
  the rest of the day; rule-18 rework of failed gb-1019-post-peak-index-guard): 6 configs.

Lineage N = 1,311 (gate lineage, bdi1023) + 23 = 1,334 → bar max(1.5, sqrt(2 ln N)) = 3.79 for every row.

## Metrics per config, per split (train / valid)
trades kept %, avg R, delta vs B0 per B0 trade (day-clustered t), sum R, up / down regime deltas, mean daily give-back
(realized-R curve by exit time: day peak (>= 0) minus close), p90 give-back, "swing days" (peak >= +X then close <= 0),
worst day.

## Verdicts (fixed now)
- **pass** (could be proposed as a change): kept >= 85% in both splits; delta > 0 in train and valid; delta >= -0.005R
  in up and in down sessions; mean give-back lower in train and valid; all-data delta t >= 3.79.
- **no-harm** (give-back cut that does not cost avg R, below the bar): all of the above except the t bar, with delta
  >= 0 in both splits. Reported as such, never as a pass.
- otherwise **fail**.
- S rows are judged on avg R first ("avg R decides"); a stop that lowers give-back but costs avg R fails.

Live cross-check (description only, not a gate): the same rules on the live paper trades 10-12..10-23
(`research/bdi/nightly*/trades.csv`), per account, net R and give-back vs actual.

## Addendum (written after S / G1-G3 were scored, before L was scored)
S / G1-G3 cut give-back mostly by cutting trades. The live week's other give-back source is open winners handed back
into the 15:55 flatten (T1 10-20 -$221, P 10-22 -$135, T2 10-21 -$84 / 10-23 -$63). Added, 6 configs (N 1,340, bar 3.80):
- **L (late profit lock, no exit before the lock is hit and no change to targets):** from the bar closing at T, a trade
  still open with open profit >= +0.5R at a bar close gets its stop raised to entry + 0.25R. **L1500** T = 15:00,
  **L1430** T = 14:30; P / T1 / T2. Same verdict rules; give-back metric = the per-trade give-back of the locked trades
  as well as the book curve. Costs: the locked exit pays stop costs (entry + exit slippage + the extra stop slippage).
