Educational only — not financial advice

# REGSTEER-1 pre-registration (2026-11-26, written before any score; sha256 in PREREG.sha256)

Protocol: research/consultants_1126/C_STATISTICIAN.md §3 and §5, run as written except where noted (each note says why).
Research only: no config, ledger, decisions or live change.

## Owner override of rule 26
Rule 26 (C3 "Stop doing") lists day-type on/off switches as "ask the owner first". On 2026-11-26 the owner explicitly asked
for regime-steering research (Market Compass switching setups on/off by condition). That request lifts the rule-26 guard for
this research. Prior record flagged (C §0): REGSW 0 of 74 switches pass, REGX label repeat 31% vs 32% chance, GATE1 0 of 112,
HC1/COMP15 0 of 68, BREADTH-1125 0 of 12, day-type 0 of 67.

## Data, engine, costs
- Engine: bench10 (research/ultimate_1119/top10/bench10.py) unchanged, wrapped by rs_bench.py. Primary book rules via
  research/primshorts_1126/booksim.py (<= 77 lots, 30 per setup, 3 per symbol, burst brake, -2R realised latch, -20R halt;
  LATCH-OPEN off = live rules). Costs LIVE-L (primshorts_1126 cells_live.json) on shorts, LR8 research on NM-ETF (primshorts
  convention). Live = mcf.report.footrace.live_trades() (LR8 cost-R on real fills), parity asserted in rs_live_load.py.
- The 4 GEN contenders use geoms "hold"/"holdtr" that bench10 lacks; rs_bench.py adds them without editing bench10 (stop 1R
  at 0.25 x ATR, no target, holdtr trails 1R behind the best price once +1R, as runner.py). Used only in Step 1.
- Splits: FIT 2024-10 + 2025-03..09, CHECK 2025-10-01..2026-11-04, T2 2023-01-03..2024-09-13. The locked block
  2024-11-01..2025-02-28 is never read: every loader filters it and asserts no row; scoring asserts again. It is not scored.
- Setups: Primary's 4 (L3-gap-slope-fromopen-FD, RW3, RW5, NM-ETF-late-dip-di-long) + the top 4 live contenders by live total
  R with >= 30 live trades outside Primary (GEN-261022-05, GEN-261026-07, GEN-261020-09, GEN-261023-07; full names in
  rs_bench.py). Note: C allowed "at most 4 named long candidates"; the top 4 by live R are 2 shorts + 2 longs (rule is
  mechanical, fixed here). Contenders enter Step 1 only; the scored book in Step 2 is Primary's 4 (the owner's scoreboard).

## States (both known at decision time; rs_states.py)
- S1 = SPY open gap (first RTH 1-min open / prior session close - 1), terciles -> -1 / 0 / +1. Cut-offs: Step 1 from all
  T2 + FIT days; Step 2 from the training fold's days only (expanding).
- S2 = W60 compass confirmed side at entry: +1 UP-confirmed, -1 DOWN-confirmed, else 0 (C: "confirmed side -1/0/+1"). Mark
  used = latest 15-min mark T with T <= entry minute - 1 (compute() needs mark + 1 min; 09:45 mark counts).
  Bench: compute() rules re-implemented on cached 1-min bars, parity checked against compute() on sample days. Point-in-time
  proxy (allowed by C): breadth uses the 177 Hunch-200 names present in both caches (same names in every split); live uses
  200. Live W60 = compute() on Alpaca bars for 10-06..11-25 (compass_rd_1126 backfill, copied and frozen).
- Exposure alignment (direction fixed a priori, never fitted): a = side x state (side +1 long, -1 short; all 8 setups have
  beta sign = side). a = +1 state with the exposure, -1 against.

## Step 1: rank agreement (1 config)
Cells = setup x (S1 tercile x S2 side) (<= 9 per setup). Bench = candidate lots (price >= $5, ETB shorts) of all non-locked
splits pooled (per split for information); live = all accounts 10-06..11-25 (deduped). Cells need >= 30 bench and >= 8 live
trades. Gate statistic: Spearman rho of setup-demeaned cell means (cell mean minus the setup's own mean on that source = the
state effect steering uses); raw cell means reported too. 90% CI by day-block bootstrap (1,000 draws, live and bench days
resampled). Also the sign agreement of the pooled aligned-state effects gamma_k (bench vs live).
Rule: if gate rho <= 0.2 or its 90% CI includes 0 -> stop at a side-level rule: Step 2 scores only the 6 pooled configs.

## Step 2: REGSTEER-1 walk-forward
- Base book: Primary 4 under the book rules above; the lots it takes form the base set. Steering weights w in {0, 0.5, 1}
  scale each taken lot (linear: day R = sum w x lot R; freed-slot and latch-path effects ignored, same for every arm).
- Model per training fold (empirical-Bayes approximation of C's REML model; day clustering through day-clustered SEs):
  setup mean mu_s; deviations d_sk = cell mean - mu_s on aligned cells k; pooled gamma_k = precision-weighted mean of d_sk
  over setups; hierarchical: b_sk = d_sk - gamma_k shrunk by B = tau2/(tau2 + v_sk), tau2 by DerSimonian-Laird (estimated,
  not chosen). Cell mean m = mu_s + gamma_k (+ B b_sk); var = v_mu + v_gamma (+ B v_sk); P = Phi(-m/sd).
  w = 0 if m < -0.02R and P >= 0.9; (OFF/HALF only) w = 0.5 if P >= 0.75; else 1. Monotone projection: w(a) = max over
  cells a' <= a (componentwise) of w(a') (a more-aligned cell is never weighted below a less-aligned one). Cells with < 10
  training trades use the pooled value.
- Grid (12 configs): {S1, S2, S1+S2} x {pooled gamma only (= side-level rule), hierarchical} x {OFF-only, OFF/HALF}.
- Walk-forward: monthly, expanding window, months 2023-01..2026-11 minus the locked months; first 3 months training only,
  OOS = 2023-04..2026-11 (40 months). The concatenated OOS daily series is the only scored series.
- Nulls on the same OOS days: (a) unsteered; (b) constant weight = the config's overall OOS mean weight; (c) random switches
  = the day's weights permuted across that day's lots (500 draws, seed 1126; its mean = w_bar_day x base day R, used for
  the paired excess); (d) side-only = the matching pooled config.
- Scored statistic: excess_d = steered day R - null (c) mean; paired day t. CSCV: 16 contiguous blocks, all 12,870 splits,
  IS-best by mean excess, PBO = P(OOS logit <= 0). Hansen SPA (and White RC) over the scored configs, stationary bootstrap,
  mean block 5 days, 2,000 draws. Deflated Sharpe of the best config's excess at N = 2,271 and at the corrected N (info).
- Try count (C §3.8 asks the lead to verify ~400): the regime / market-context gate lineage on file is far larger:
  bdi1016 PLAN lists 2,450 market-context gates by 10-16 (regime1009 1,052 + ix-gate 912 + splitgate 370 + nightly/bdi1015
  32 + day-class 84); since then gates1021 718, bdi1021 196, regime1022 384, REGSW 99, regsw2 4, GATE1 112, HC1/COMP15 68,
  day-type 67, L3LEASH 12, BREADTH 14, squeeze_1125 5 = 1,679 -> N_lineage ~ 4,129 (overlaps possible; order of magnitude
  4,000, not 400). Bar = max(3.46, sqrt(2 ln 4,141)) = **4.08** (4,129 + this study's 12). C's 3.46 is reported too.
  Configs tried here: 1 (Step 1) + 12 or 6 (Step 2). Cumulative N ~ 2,271 -> 2,284 (or 2,278).

## Pass bar (all must hold, for the best config by OOS mean excess; SPA/PBO cover the selection)
1. Step 1 gate rho >= 0.3 with 90% CI > 0 (C's build-it bar; else the result can only be a side-level rule).
2. OOS mean excess vs null (c) >= +0.5R/day with paired day t >= 4.08 (C: 3.46; both reported).
3. Beats null (b): mean (steered - constant) > 0 with t >= 2; total above null (c)'s 95th percentile.
4. PBO <= 0.20 and SPA p <= 0.05.
5. Excess positive in both halves (2023-04..2024-10 and 2025-03..2026-11) and in >= 60% of OOS months; best-day share of
   the total excess < 10%.
6. Worst-5-day sum (OOS) improves >= 20% vs unsteered (vs constant cut reported).
7. No Primary setup worse by > 2R/month (per-setup monthly delta vs null (b) constant cut; vs unsteered reported).
Goal metrics (unsteered / constant / steered): red days per 21 sessions, worst-5 sum, worst trailing-60 worst-5, 20-session
rolling R floor, avg R/day without best day.
If (and only if) all pass: the locked block is scored once at the very end (look 1, bar t >= 1.0), then a DECISION draft
(journal-only shadow first) in REPORT.md. Otherwise the locked block stays unread.

## Addendum A (2026-11-26, before any score; coordinator note on compass_rd_1126)
- COMPASS-RD-1126 counted N = 4,762 condition cells (none clears ~t 4.3). Added to the lineage: N_lineage = 4,129 + 4,762 =
  8,891 -> bar = sqrt(2 ln 8,903) = **4.26** (replaces 4.08; 3.46 still reported). Cumulative program N unchanged in kind.
- Information only (not configs, not used for selection): bench W60 first-confirmed side vs the day's close side (SPY close vs
  open) by month and by confirmation time, with the base rate; share of base-book entries made at/after the day's first
  W60 confirmation and with a confirmed side at the entry mark.
