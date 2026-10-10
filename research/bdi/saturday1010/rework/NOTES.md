# BD&I Saturday 2026-10-10: rule-18 rework of failed longer-hold ideas with new public data

*Educational only - not financial advice. Lab backtests on daily bars; nothing here is a live or paper result.*

**Section 1 (the pre-declaration) was written before any configuration was scored.** Before writing it I only read
the parent studies (`research/swarm1010/w3_daily`, `research/longhold`) and checked the new files' schemas, date
ranges, and that none of them holds a row dated 2024-11-01..2025-02-28 (all 0 locked rows; the `*_lockedblock`
files were never fetched or read). No return was computed by condition before this section existed. Section 1 may only
change by dated amendments in 1.9. Results are in section 2.

## 0. New information (not available to the parent studies)
Fetched from git branch `research-data` (`git show origin/research-data:<file>`, published 2026-10-10 05:25 UTC) into
`data/` (git-ignored):
- `cboe_vol_indices.parquet`: VIX (1990+), VIX3M (2009-09+), VIX9D, VVIX, daily OHLC.
- `finra_shvol_2019..2026.parquet`: FINRA daily short-sale **volume** per symbol (not short interest), 2019+.
- `earnings_cal.parquet`: earnings dates per symbol 2019+ (time of day is "not supplied" for 99 %).
- `treasury_yields.parquet`: daily curve 2000+, `t10y2y`.
- `ff_factors3_daily.parquet`, `ff_mom_daily.parquet`: Fama-French daily factors incl. momentum, to 2026-08-31.
- Not fetched: every `*_lockedblock.parquet`, FF industry files (not used).

## 1. Pre-declaration

### 1.1 Lineages reworked and their try counts
| lineage | parent (failed) | parent N | new configs (this round) | lineage N | t bar `max(1.5, sqrt(2 ln N))` |
|---|---|---|---|---|---|
| **A Connors RSI dip buy** | W3 `F2_rsi3_5_O_SMA5_L`, failed locked look 1 (-106 bps, t -1.64) | 64 (W3 F2 family) | 51 | 115 | 3.08 |
| **B weekly reversal basket** | W3 `F3_rev5_bot_k20_L`, failed locked look 1 (-85 bps, t -1.08) | 12 (W3 F3 family) | 35 | 47 | 2.78 |
| **C momentum near-misses** | longhold `S6_mom12_1rev_N20_M` (active t 2.98 < 3.05) and `S1_mom12_1_N50_W` (t 2.91) | 105 (longhold study) | 18 | 123 | 3.10 |

Total new configurations this round: **104**. Re-runs of the unchanged parents on the same samples are controls, not
new configurations (they were counted by the parent studies). Both A and B parents already used one locked look, so
any A/B finalist would be **look 2** (bar t >= 1.5 on the locked block, rule 18/19) and would go to paper as
probation if it passed. The C parents never went to the locked block, but the lineage (longhold study) had one look
(S6_mom12_1rev_N20_W passed), so a C finalist is also scored as **look 2** (t >= 1.5) to be conservative.

### 1.2 Data, splits, costs, engine (unchanged from the parents)
- A and B: the W3 engine (`research/swarm1010/w3_daily/study.py`, executed as a module prefix with its two file
  writes disabled; nothing in that folder is modified). Same eligibility ($5, $20M ADV20, not ETF, 200+ bars), same
  costs (1c/share + 1 bps per side), same fills, same locked-block blanking of every outcome array, same splits
  train 2016-2022 / valid1 2023-01..2024-10 / valid2 2025-03+, same clustered t, same excess vs the eligible
  universe, same month classes.
- C: the longhold simulator (`research/longhold/study.py` prefix up to the grid, executed with no writes; parent
  series read from its `sim_cache.npz`, read-only). Same costs, MOO execution, locked returns zeroed, splits
  train 2017-2020 / valid 2021-01..2024-10 / valid2 2025-03+, benchmark EW universe.
- The locked block 2024-11-01..2025-02-28 is used nowhere; no new feature file contains it. `MCF_HIST_ALLOW_LOCKED`
  is never set.

### 1.3 New features (all point in time)
- **TR** = VIX close / VIX3M close at day t. TR >= 1 is backwardation (stress).
- **VIXP** = percentile rank of the VIX close at t among the previous 252 available VIX closes (incl. t).
- **SVR20** = mean over the last 20 available sessions of FINRA shortvolume / totalvolume for the symbol (min 10
  obs). Cross-sectional rank among the day's eligible names. NaN (no FINRA row) -> the filter does not remove the
  name.
- **Earnings** dates mapped to the first trading session on or after the listed date. Time of day is unknown, so a
  trade "contains earnings" if an earnings session falls in [entry session, exit session] (E1), or in
  [signal session - 3, exit session] (E2, also excludes dips caused by a just-reported quarter). Look-ahead note: a
  historical calendar holds confirmed dates; live, dates are usually confirmed 2-4 weeks ahead, longer than any hold
  here.
- **Curve** = `t10y2y` at t (Y1: > 0, curve not inverted).
- **SPY200** = SPY close > its SMA200 at t.
- **Timing rule for MOC entries (lineage B):** VIX/VIX3M and FINRA are published after the 16:00 stock close, so
  for MOC entries they are lagged one session (t-1). Lineage A enters MOO (next open) and lineage C fills at the next
  open, so they use day t.
- **Momentum-factor proxy (C):** daily close-to-close return of the top-decile minus bottom-decile 12-1 momentum
  portfolio among eligible stocks (equal weight, re-formed at each month end), computed from our own bars so it is
  available live. **MOMVOL** = its sd over the last 126 non-locked sessions; **MOMVOLP** = percentile of MOMVOL among
  all its own previous values (expanding, point in time). FF `Mom` is used only as a diagnostic (correlation with the
  proxy, and which months the guard switched off), because it ends 2026-08-31 and is published with a lag.

### 1.4 Grid A: Connors dip buy (51)
Bases (signal at close t, MOO entry at open t+1, exit at the first close > SMA5, cap 10 sessions; ELIG200):
`b35` = close > SMA200 and RSI(3) < 5 (the failed finalist); `b310` = RSI(3) < 10; `b25` = RSI(2) < 5.
Single filters, each applied to each base (14 x 3 = **42**):
- TR >= 0.90 / 0.95 / 1.00 / 1.05 (4)
- VIXP >= 0.3 / 0.5 / 0.7 (3)
- SVR20 not in the top 10 % / 20 % / 33 % of the day's eligible names (3)
- E1, E2 earnings exclusion (2)
- SPY200 (1), Y1 curve not inverted (1)
Pairs and triple on `b35` only (**7**): TR>=0.95 & E2; TR>=0.95 & SVR20-not-top20; TR>=0.95 & SPY200;
VIXP>=0.5 & E2; VIXP>=0.5 & SVR20-not-top20; VIXP>=0.5 & SPY200; TR>=0.95 & E2 & SVR20-not-top20.
Condition removed (**2**): `b35` without the SMA200 condition; the same with TR >= 0.95.

### 1.5 Grid B: weekly reversal basket (35)
Bases (bottom decile of the 5-day return among ELIG200, MOC entry at close t, exit at close t+k): `k20` (the failed
finalist) and `k10`. The same 14 single filters on each (**28**; VIX/FINRA lagged one session). Pairs and triple on
`k20` only, the same 7 combinations as A (**7**).

### 1.6 Grid C: momentum crash guards (18)
Bases: `S6M` = S6_mom12_1rev_N20_M (monthly), `S1W` = S1_mom12_1_N50_W (weekly). The guard is checked at every week
end (both bases); when its state changes mid-month the monthly base re-targets at that week's next open (guard on:
the guard portfolio; guard off: the last month-end momentum targets). Guards (9 x 2 bases = **18**):
- G1 SPY200 false -> hold the EW universe; G2 SPY200 false -> hold BIL
- G3 TR > 1.0 -> EW; G4 VIXP > 0.8 -> EW
- G5a/b/c MOMVOLP > 0.7 / 0.8 / 0.9 -> EW
- G6 bear state (SPY 504-session return < 0, Daniel-Moskowitz) -> EW
- G7 scaling: weight = s x momentum + (1 - s) x EW, s = min(1, median(MOMVOL history to t) / MOMVOL_t), set at the
  base's rebalance
"-> EW" means the guard holds the benchmark, so the active return is ~0 (minus switching costs) while it is on: the
guard tests whether skipping the momentum tilt in crash states helps, without betting on cash.

### 1.7 Gates (same as the parents, plus the round's extra bars; all must pass for "candidate")
**A and B** (W3 `evaluate.py` gates, with the lineage N from 1.1):
1. exp > 0 in train, valid1, valid2, n >= 100 in each.
2. clustered t on train+valid1 >= t_req(lineage N) (A 3.08, B 2.78).
3. valid1 clustered t >= 1.5.
4. excess vs the eligible universe > 0 in train and valid1.
5. exp > 0 in up months and down months (pooled open splits), each n >= 30.
6. plateau: mean train+valid1 exp of the grid neighbours > 0. Neighbours: one threshold step in the same filter
   (TR 0.90-0.95-1.00-1.05, VIXP 0.3-0.5-0.7, SVR 10-20-33, E1-E2), the same filter on the adjacent base
   (A: b35<->b310, b35<->b25; B: k20<->k10); for a pair/triple, its component single filters on the same base;
   for the no-SMA200 rows, the base and its b35 counterpart.
7. walk-forward (gates.walk_forward, 3m/1m, locked months excluded, folds with n >= 10): share positive >= 0.6.
- **2019+ filters (SVR, E1, E2 and any pair containing them):** their data start 2019, so gate 1/2/4 use
  **train19 = 2019-01..2022-12** in place of train, and the parent base is reported on the same train19 sample with
  and without the filter. n >= 100 still applies.
**C** (longhold Tier A, lineage N 123): A1 active > 0 in train, valid, valid2; A2 monthly active t on train+valid
>= 3.10; A3 plateau: neighbours' mean train+valid active > 0 (same guard on the other base; G1<->G2; G5 a-b-c;
G3<->G4); A4 active > 0 in SPY-up and SPY-down months; plus walk-forward share of monthly active returns > 0 >= 0.6
(3m/1m folds, locked months excluded, min_n 1). Tier B (risk improver) is also reported with the longhold B1-B4
definitions and DSR at N = 123.

### 1.8 Recommendation rule (fixed now)
At most one candidate per lineage goes to the lead for the one-time locked score (look 2, bar t >= 1.5 for A/B;
active > 0 with weekly active t >= 1.5 for C), ranked by train+valid only (A/B: train+valid1 t; C: trval active t).
valid2 is a gate, never a ranking input. If nothing passes, nothing is recommended.

### 1.9 Amendments (dated)
- **2026-10-10, before any scoring (no number seen).** The SMA5 exit date is not known at entry, so the earnings
  windows are defined ex ante on the maximum hold: A (MOO entry at t+1, cap 10): E1 = earnings session in
  [t+1, t+10], E2 = in [t-3, t+10]. B (MOC entry at t, exit t+k): E1 = in [t, t+k], E2 = in [t-3, t+k]. Configs
  that use FINRA or earnings data only take signals dated 2019-01-02 or later (all splits), and are compared with
  the parent on the same 2019+ sample.
