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

## 2. Results (104 new configurations; failures first)

*Educational only - not financial advice. Backtests on daily bars, costs in, locked block 2024-11..2025-02 in no
figure. A/B in bps per trade net of costs; C in %/yr active vs the EW universe.*

| lineage | new configs | lineage N / t bar | fail | near (failed a gate) | candidate (all gates) |
|---|---|---|---|---|---|
| A Connors dip buy | 51 | 115 / 3.08 | 0 | 38 | 13 |
| B weekly reversal basket | 35 | 47 / 2.78 | 0 | 26 | 9 |
| C momentum crash guards | 18 | 123 / 3.10 | 0 | 18 | 0 |
| **total** | **104** | | **0** | **82** | **22** |

**Read this first.** A and B are re-filters of parents that had *already passed* every one of these train/valid
gates and then failed the locked block. A filter that keeps a large subset of a passing parent will usually pass the
same gates too, so "candidate" here mostly means "still passes, and the filter did not break it". It is not evidence
that the filter fixes what went wrong in the locked block. The useful question is what the filter changes against
the parent on the same sample (2.3).

### 2.1 Failures and near misses
- **C momentum crash guards: 18 of 18 fail A2 (try-count t), and none beats its parent.**
  - Parents: S6_mom12_1rev_N20_M t 2.98, S1_mom12_1_N50_W t 2.91.
  - Every guard *lowers* the train+valid active t. Best: G6 bear-state 2.88/2.70, G7 vol-scaling 2.85/2.84,
    G5c 2.79/2.41. Worst: G2 to-BIL 1.18/1.12, G4 VIX-pct 1.63/1.35. Train+valid maxDD barely moves (-38..-41 % vs
    -41 %); only the to-BIL guard cuts it, to -30/-31 %.
  - Walk-forward share < 0.6 for 6 of the 9 S6M guards.
  - No Tier-B pass (DSR 0.41-0.77 < 0.95).
  - Diagnostic: the own-bar momentum proxy correlates 0.90 with FF `Mom` (2,328 days). FF `Mom` averaged -0.8 %/month
    in the months when G5b was on and +0.9 % when it was off, so the guard does find weak momentum-factor months.
    Even so, the top-20/50 long-only portfolio's *active* return in those months was not negative enough for
    skipping them to pay. The worst FF `Mom` months (2023-01 -13.7 %, 2020-04, 2020-11, 2026-07) are rebounds the
    guards mostly do not flag in time.
  - **Verdict: the crash-guard idea is retired for these two parents.** The parent S6_mom12_1rev_N20_W
    (passed look 1) stays as it is.
- **A, near (38):**
  - RSI(3)<10 and RSI(2)<5 bases with any filter: t 0.7-2.6 < 3.08. The filters do not lift the looser bases over
    the bar.
  - TR>=1.00/1.05 on b35: per trade +155..+400 bps, but valid1 n 51/23 < 100. Backwardation is rare in 2023-24.
  - Y1 (curve not inverted): valid1 n 82 < 100, because the curve was inverted for almost all of valid1.
  - Pairs with E2 fail valid1 t (1.2) and excess (<= 0).
  - noSMA200: t 2.28. noSMA200+TR95: t 1.48.
- **A, earnings exclusion (2019+ sample):** it *lowers* the per-trade result.
  - b35: E1 +77.9 / +49.3 / +68.3 and E2 +77.1 / +45.8 / +72.6 (train19 / valid1 / valid2), against the parent on
    the same sample at +85.7 / +65.1 / +78.3.
  - Excess falls from +28 to +16 (E1) and +8 (E2) in valid1.
  - So dips with earnings in or just before the hold are *better* than average, not worse. The exclusion is dropped.
- **B, near (26):**
  - The k10 base and its filters all fail the down-month gate (-13..-78 bps).
  - The earnings filters fail the down-month gate and lower excess (+1..+2 bps in valid1 vs +22 for the parent).
  - SPY200 fails the down-month gate.
  - TR95 alone fails valid1 t (1.35). TR100/105 have too few trades, or negative excess, in valid1.

### 2.2 Candidates (all gates pass)
Full table: `gates_ab.csv`. Sorted by the train+valid t that 1.8 ranks on (train19+valid1 for the 2019+ filters).

| id | train (or train19) | valid1 (n, t) | valid2 (n) | t tr+v1 / bar | excess v1 | down months | down years | WF |
|---|---|---|---|---|---|---|---|---|
| A_b35_VP30 | +83.7 | +85.1 (681, 3.04) | +75.8 (693) | 4.84 / 3.08 | +38.7 | +62.5 | +5.4 | 0.73 |
| A_b35_TR90 | +96.3 | +68.2 (731, 2.41) | +120.0 (415) | 4.71 | +23.0 | +73.7 | +17.3 | 0.75 |
| A_b35_TR95 | +106.1 | +62.2 (476, 1.88) | +116.0 (267) | 4.48 | +28.0 | +88.7 | +53.0 | 0.89 |
| A_b35_SV20 (2019+) | +90.9 | +63.3 (940, 2.88) | +89.3 (746) | 4.33 | +25.8 | +59.9 | -57.1 | 0.81 |
| A_b35_VP50 | +85.6 | +79.6 (486, 2.76) | +96.8 (514) | 4.22 | +24.7 | +61.4 | +5.1 | 0.77 |
| A_b35_SV10 / SV33 (2019+) | +85.5 / +87.2 | +62.4 / +64.4 | +79.4 / +103.3 | 4.22 / 4.21 | +25 | +51 / +62 | -58 / -65 | 0.77 / 0.82 |
| A_b35_VP50+SV20 (2019+) | +109.4 | +81.8 (416, 2.72) | +109.2 (427) | 3.76 | +25.3 | +76.6 | -55.0 | 0.82 |
| A_b35_SPY200 | +62.1 | +68.2 (1030, 3.59) | +54.7 (806) | 3.74 | +38.0 | +24.2 | -6.5 | 0.73 |
| A_b35_VP70 | +82.0 | +68.7 (365, 1.97) | +100.0 (365) | 3.64 | +19.8 | +73.8 | +12.1 | 0.60 |
| A_b35_TR95+SV20 (2019+) | +120.3 | +63.2 (406, 1.80) | +122.0 (219) | 3.58 | +26.1 | +97.8 | +9.3 | 0.86 |
| A_b35_E1 / E2 (2019+) | +77.9 / +77.1 | +49.3 / +45.8 | +68.3 / +72.6 | 3.52 / 3.35 | +16.0 / +7.5 | +41 / +36 | -83 / -90 | 0.75 |
| *parent A_b35 (control)* | *+74.0* | *+65.1 (1113, 3.19)* | *+78.3 (898)* | *5.07* | *+28.3* | *+50.7* | *-0.5* | *0.74* |
| **B_k20_TR95+SV20 (2019+)** | +387.8 | +256.0 (1374, 1.51) | +317.5 (2062) | 4.01 / 2.78 | +114.3 | +170.7 | +165.4 | 0.75 |
| B_k20_TR90 | +258.2 | +211.8 (4244, 2.34) | +294.5 (4032) | 3.87 | +52.8 | +118.1 | +82.3 | 0.79 |
| B_k20_VP70 | +250.0 | +426.1 (1769, 3.20) | +285.1 (3766) | 3.63 | +66.8 | +169.1 | +56.4 | 0.67 |
| B_k20_VP50 | +201.4 | +319.2 (2771, 3.59) | +297.2 (5162) | 3.44 | +67.1 | +100.2 | -0.6 | 0.70 |
| B_k20_VP50+SV20 (2019+) | +250.2 | +332.6 (2309, 3.83) | +308.4 (4388) | 3.24 | +83.7 | +102.1 | -38.8 | 0.69 |
| B_k20_SV33 / SV10 / SV20 (2019+) | +191 / +194 / +192 | +187 / +186 / +184 | +262 / +253 / +253 | 3.18 / 3.15 / 3.14 | +18..+23 | +61..+65 | ~0 | 0.65-0.69 |
| B_k20_VP30 | +178.6 | +259.3 (4000, 2.60) | +294.0 (6930) | 3.15 | +47.1 | +81.5 | +5.5 | 0.69 |
| *parent B_k20 (control)* | *+164.3* | *+188.7 (8391, 2.19)* | *+245.1 (8196)* | *3.56* | *+21.7* | *+67.5* | *+11.6* | *0.67* |

### 2.3 What the new data adds over the parent (same trades, `checks_ab.py` -> `checks_ab.csv`; nothing new tried)
- **A (Connors) + VIX filters: market timing, not stock selection.**
  - The VIX filters raise net bps (VP30 +82.5 vs parent +72.0; TR90 +93.0).
  - They do not raise the excess over the universe. Trades kept by VP30 have excess +20.9, trades removed +27.6. For
    TR90, kept +18.1 and removed +23.5.
  - Buying dips when the VIX is elevated earns more because the *market* rebounds afterwards (beta), not because the
    dip names do better than other stocks.
  - **valid2 excess of A_b35_VP30 is -4.6 bps** (the gate only checks train and valid1).
  - 2022 is still negative (VP30 -47.7, TR90 -24.7 bps/trade), and 2026 YTD is weak (+19.7 / +15.0).
- **B (reversal basket) + VIX term structure: stock-level improvement.**
  - TR90 keeps 22,109 of 41,778 trades. Excess of kept trades is **+67.0 bps** against **+15.7** for the removed
    ones. Net is +255.9 against +128.4.
  - TR95+SV20 (2019+): kept excess +56.1 against removed +28.8.
  - This fits the liquidity-provision story: short-term losers rebound more, relative to other stocks, when the VIX
    curve is flat or inverted.
  - The SVR filter alone changes almost nothing (excess +18..+23 vs parent +22).
- **Concentration:**
  - ex-best-session: A_b35_VP30 +72.0, B_k20_TR95+SV20 +338.6.
  - Busiest session: 2.5 % (A, 2021-01-27) and 1.1 % (B, 2026-07-30).
  - At 2x costs: +76.2 / +342.1 bps.
  - But B_k20_TR95+SV20 enters on only **364 sessions** (2019+), in clusters, and its 20-day holds overlap. The
    block-clustered t (blocks of 40 sessions) in valid2 is **1.07**, against a day-clustered 2.80
    (`locked_dryrun.json`). Its effective sample is a few dozen stress episodes.
- **Survivorship (unchanged from W3):** both are long dip/loser trades on today's survivors, the trade that
  survivorship flatters most.

## 3. Recommendation (rule 1.8, fixed before scoring)
One per lineage, ranked by train+valid t among candidates. Both A and B are **look 2** for their lineage (bar: exp > 0
and day-clustered t >= 1.5 on the block). A pass goes to paper as probation (rule 18).
1. **A: `A_b35_VP30`** (t 4.84). Close > SMA200 and Wilder RSI(3) < 5 at the close of t, and the VIX close at t at or
   above its 30th percentile of the last 252 VIX closes. Buy at the next open (MOO), sell at the first close > SMA5,
   with a 10-session cap.
   - Rule caveat: what it adds over the failed parent is mainly market timing, and its valid2 excess is negative
     (2.3). I expect it to behave like the parent on the block.
2. **B: `B_k20_TR95+SV20`** (t 4.01 on 2019-01..2024-10).
   - Rule: bottom decile of the 5-day return among ELIG200 at the close of t. The previous session's VIX/VIX3M must
     be >= 0.95. Skip names whose previous-session 20-day FINRA short-volume ratio is in the day's top 20 %. Signals
     from 2019 on. Buy MOC at t, sell MOC at t+20.
   - Under the rule it outranks the full-sample `B_k20_TR90` (t 3.87, valid1 t 2.34, n 22k, WF 0.79). TR95+SV20 has
     the higher t on a shorter sample, but a valid1 t of only 1.51 and few independent episodes. TR90 is the more
     robust profile, and it is *not* recommended under the fixed rule. If the lead prefers it, that is a deviation
     from 1.8 and should be recorded as one.
3. **C: nothing.** No guard passes, and none beats its parent.

Command (lead, once):
```
for f in cboe_vol_indices_lockedblock finra_shvol_2024_lockedblock finra_shvol_2025_lockedblock; do
  git show origin/research-data:$f.parquet > research/bdi/saturday1010/rework/data/$f.parquet; done
MCF_HIST_ALLOW_LOCKED=1 python research/bdi/saturday1010/rework/score_locked.py   # -> locked.json
```
The dry run (`--dry-run`, open data, valid2 window) reproduces gates_ab.csv exactly: A n 693, +75.8 bps; B n 2,062,
+317.5 bps.

## 4. What a live version would need (on top of W3 NOTES section 3)
- Everything in W3 section 3: a daily job outside market hours, MOO/MOC orders, positions tagged and kept out of
  the intraday flatten, multi-day journaling. The intraday runner cannot hold overnight.
- **A_b35_VP30:** an evening VIX fetch (CBOE daily close, after 16:15 ET) and its 252-day history. The signal is
  computed after the close, and the MOO order goes in before 09:28.
- **B_k20_TR95+SV20:**
  - The MOC entry uses the *previous* session's VIX/VIX3M and FINRA files (both published in the evening), so no
    intraday data is needed. The stock signal still uses day t's close, so it needs a 15:50 snapshot plus CLS
    orders, as in W3.
  - A FINRA daily short-volume download (CNMS file, about 18:00 ET).
  - In stress weeks it opens hundreds of concurrent positions. A capped top-N or a small equal-weight basket would be
    a new configuration and needs its own run.

## 5. Files
- `study_ab.py`: grid A/B, writes `results_ab.csv` and `gates_ab.csv`.
- `study_c.py`: grid C, writes `results_c.csv`, `gates_c.csv` and `diag_c.json`.
- `checks_ab.py`: writes `checks_ab.csv`.
- `score_locked.py`: the lead's one-time scorer. Its dry run writes `locked_dryrun.json`.
- `data/` (git-ignored, about 82 MB): the research-data files. No `*_lockedblock` file was fetched.

## Lead: one-time locked-block score (2026-10-10, look 2 for both lineages; bar exp > 0 and t >= 1.5)
| id | n | net bps | t (day) | t (block) | excess bps | sessions | verdict |
|---|---|---|---|---|---|---|---|
| A_b35_VP30 | 329 | -103.4 | -1.58 | -1.25 | -37.0 | 53 | FAIL |
| B_k20_TR95+SV20 | 341 | +271.6 | 0.94 | 0.61 | +203.3 | 11 | FAIL (positive, but 11 entry sessions) |
Next look on either lineage needs t >= 2.0. Source: locked.json.
