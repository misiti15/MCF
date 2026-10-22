# ns3var1022: can Big Loser VWAP Reclaim Fade (all day) be made to work in more market weather? (owner 2026-10-22)

*Educational only - not financial advice. All numbers are backtests on the open two-year history (lab frames
2024-10, 2025-03..2026-10-07; the 15:05-15:55 bars come from the 1-minute SIP cache). The locked block
2024-11-01..2025-02-28 was never read (loader refusal + asserts; the 1-minute read filter excludes it). No holdout was
scored. Costs are always in: production cost (1c + 1 bps per side, target exits free, +2c on stops), time-of-day entry
cost, x3 on the extended tier. "As run" = refire chain cooldown 1 + at most 3 open lots per symbol, each lot exiting on
its own 5-minute path, as NS3-FD runs live. TRAIN = sessions to 2025-12-31, VALID = 2026-01-01..10-07. Regimes are the
regime1022 labels (SPY, hindsight; Bull >= +0.5% open-to-close, Bear <= -0.5%, Choppy/Quiet in between with a wide/narrow
range). `PLAN.md` was committed before anything was scored and was not changed. No config, setup or exit was changed.*

**Configurations counted: 95** = 73 pre-declared (PLAN.md) + 3 exploratory + 19 plateau rows, the last two groups added
after the grid was scored and labelled as such. Study bar max(1.5, sqrt(2 ln 95)) = **3.02**; NS3 lineage N 167,113
(swarm1017 rework-ns 165,764 + regime1022 gate lineage 1,254 incl. gates1021 718 / bdi1021 196 / regime1022 340, + 95)
-> **4.90**. Reference rows P0 / P1 are not counted.

## Verdict in plain English
1. **No version of the all-day setup is good in more weather.** 0 of 73 pre-declared variants pass the Testing bar or
   your near-miss merit rule, and none passes all five "better NS3-FD edit" tests. The all-day setup loses because 88%
   of its trades come after 11:30, and shorting a big loser's VWAP reclaim after 11:30 loses on Bull and Choppy days and,
   in 2026, on Bear days too (after 11:30: train -0.011R / valid -0.027R per trade). Filters, exits and re-fire rules
   only move it around zero; most flip sign between 2025 and 2026.
2. **Two changes help in every kind of market, and they work together:**
   - **the parent's morning window (09:50-11:30)** - the morning trades are the profitable part
     (+0.049 / +0.039R per trade with refire);
   - **a stop twice as wide at the same dollar risk, with the target at the same price** (half the shares; target =
     0.5R). This cuts the stop-outs on up-drift days. On the all-day setup alone it lowers the Bull + Choppy loss by
     a third and raises Bear-day R (1.5x stop: Bull -0.103 / Bear +0.084 / Choppy -0.042 / Quiet +0.004, against
     -0.154 / +0.067 / -0.067 / -0.008). That passes four of the five edit tests, but its significance is t 2.67,
     below both bars, and the all-day version is still about break-even in 2026 (-0.002R). Rework idea, not a proposal.
3. **Morning window + 2x stop = V1 "Big Loser VWAP Reclaim Fade, Morning, Wide Stop" (NS3V1-am-widestop-short).**
   - Backtest: train +0.044R (868 trades) / valid +0.058R (1,402); +120R over 2 years; win rate 63%.
   - By regime: Bull -0.037 / Bear +0.200 / Choppy +0.092 / Quiet -0.014. NS3-FD: -0.154 / +0.067 / -0.067 / -0.008.
     In 2026 it is positive in 3 of 4 conditions (Bull -0.043 / Bear +0.132 / Choppy +0.139 / Quiet +0.036).
   - Beats random same-minute shorts by +0.018 / +0.061R. Best day 18% of total R. Worst day -21.9R (NS3-FD -105R).
   - It meets your near-miss merit rule. It is **far below the multiple-testing bars** (t 2.15 vs 3.02 / 4.90), and it
     was found **after** the pre-declared grid had been scored, so VALID is not out of sample for it.
   - All 20 neighbouring settings are positive in both periods: stop 1.25-2x, target fixed or scaled, last entry
     11:00 / 11:30 / 12:00, refire on/off.
   - Proposed as **DECISION V1** in the 10-22 inbox, for Testing 2 as a new observation setup. Nothing is changed.
4. **The long "inverse" fails in every form.** E1-E4 lose -0.08 to -0.18R per trade. On Bull days the mirror long is
   only +0.03R. The failure is not systematic enough to flip.
5. **Where the up-day losses sit.** 78% of the Bull + Choppy loss (-448R of -574R) comes from entries after 13:00. On
   Bull + Choppy days the setup still beats random shorts (+0.13R / +0.03R per trade). The stock pick is fine; the short
   side of an up-drifting afternoon market is what loses.

## Failures first
- **0 of 73 pre-declared variants pass** (`variants.csv`). None reaches the study bar or the lineage bar on its own
  t: the best 2-year t is +1.08 (F ret20<0 + 1.5x stop), then +1.01 (D4). The per-day difference vs NS3-FD reaches
  its best at 3.13 (A6, daily ATR >= 3%), which is below the lineage bar. 18 rows pass W1-W2 (better avg R in both
  periods and better than random thinning), but every one fails W5 (significance) and most fail W3 or W4. Among them:
  - B7 at 1.25x and 1.5x, in both target modes;
  - A6 ATR% >= 3, A8 SPY above VWAP, A1 relative strength, A10 20-day return < 0;
  - D4 09:50-11:30 and seven F pairs.

  Four rows pass W1-W4 and fail only W5: B7 1.5x stop (same / scaled target) and "20-day return <= +10%" + the
  1.5x stop (same / scaled). The two pairs are negative in VALID (-0.002 / -0.006).
- **Every exit idea except the wider stop is worse than the parent's 1R / 1R in train.** Losers:
  - stop 0.5R: -0.12 / -0.08;
  - time stops at 30 / 60 / 120 minutes;
  - trailing 1R, and 0.5R trail after +0.5R;
  - breakeven after +0.5R;
  - flat by 14:00 / 15:00.

  Target 0.5R (-0.033 / -0.014) and scale-out at 0.35R (-0.015 / -0.016) help in VALID only.
- **Re-fire limits make it worse.** First signal only, cooldown 3 / 6, and 1 / 2 lots per symbol are all lower in train
  and valid. The 2nd and 3rd entries on a symbol are better than the first (+0.017 / +0.034 vs -0.033R); only the
  4th+ is bad (-0.14R, 2% of trades).
- **Market-tape entry filters do not fix the weather problem.**
  - SPY or QQQ below its VWAP at entry makes it worse (-0.043 / -0.042; QQQ -0.052 / -0.070). Shorting into a weak
    tape catches the rebound, as regime1022 found.
  - SPY above VWAP helps a little (+0.022 / -0.006), but it fails W3: its Bull-day loss is not smaller.
  - "SPY up from the open" flips between periods (-0.090 / +0.026).
  - Breadth falling: -0.017 / -0.012.
- **Stock-state filters flip between periods.** Most look good in 2025 and lose in 2026:
  - 20-day return < 0: +0.071 / -0.020;
  - gapped down: +0.066 / -0.040;
  - down > 4% from the open: +0.092 / -0.028;
  - peers down: +0.013 / -0.042;
  - was >= 1% below VWAP before: +0.063 / -0.035.

  The only filter positive in both periods is the pre-declared window cut D4 (09:50-11:30). D4 misses your merit rule
  only because its best day (2025-04-14) is 39% of its total R.
- **The train-selected pairs (F) do not hold up in VALID.**
  - Best: 20-day return < 0 + 1.5x stop, +0.078 / +0.008. That is positive in both periods, but its best day is 79% of
    total R, so it fails.
  - "ret20<0 + ret20<=10" equals "ret20<0", a redundant pair the pre-declared selection produced. It is counted anyway.
- **V1 was not pre-declared.** It came from looking at the grid: D4 positive + B7 the best exit. The 3 exploratory rows
  and 19 plateau rows that found and checked it are counted. Treat its VALID numbers as in-sample.
- **Not modelled:**
  - the live 5-bar gate. The lab evaluates every bar, which is the "every bar" variant;
    research/replay/VALIDATION.md found the dropped signals are not worse;
  - ETB / spread skips and slot limits;
  - survivorship: the universe is today's list.

  The live replay of V1 (`mcf.replay --alone`) was **not run**: the replay bar store (`data/replay`) is empty in this
  container, and the disk has 1.8 GB free. Construct check only: LabStrategy builds the module with
  `r_atr_frac: 0.5` -> GEOM t05s1, stop 1.0 x 0.5 ATR, target 0.5 x 0.5 ATR, window [950, 1130], refire on.

## Part 1 - diagnosis of NS3-FD as run (P0: 16,955 trades, train -0.0045 / valid -0.0214R; reproduces regime1022 / gates1021 exactly)
Full tables: `diag.csv`, `diag_regime_cross.csv`, `diag_worst_days.csv`, `tables_out.md`. 2-year avg R per trade,
with the random same-minute short (same exit) for comparison.

| split | bucket: n, avg R (random) |
|---|---|
| regime | Bull 2,511 -0.154 (-0.289); Bear 5,584 +0.067 (+0.070); Choppy 2,806 -0.067 (-0.096); Quiet 6,013 -0.008 (-0.048) |
| time of day | 09:50-10:30 795 +0.032; 10:30-11:30 1,414 +0.045; 11:30-13:00 1,742 +0.001; **13:00-14:00 4,657 -0.063 (-291R)**; 14:00-15:00 8,347 -0.006 |
| entry #k per symbol-day | 1st 10,201 -0.033; 2nd 4,512 +0.017; 3rd 1,860 +0.034; 4th+ 382 -0.140 |
| gap | <= -5% 432 +0.212; -5..-2% 1,486 +0.124; -2..0% 4,374 -0.054; 0..+2% 5,193 -0.075; > +2% 5,470 +0.018 |
| daily ATR % | <= 3% 1,946 -0.11; 3-5% 4,898 -0.043; 5-8% 5,708 -0.002; > 8% 4,313 +0.042 |
| SPY / QQQ vs own VWAP at entry | SPY above +0.004, below -0.045; QQQ above +0.015, below -0.063 |
| RS vs SPY | no clear slope: -0.029 (> -2) to +0.021 (<= -5) |
| 20-day return | <= -10% +0.015; -10..0 +0.010; 0..+10% -0.057; +10..25% +0.002; > 25% -0.028 |
| 60-day beta | <= 0.75 -0.060; 0.75-1 -0.020; 1-1.5 +0.016; 1.5-2 -0.038; > 2 +0.005 |
| reclaim size / bars below VWAP / reclaim volume | no monotone pattern (all within -0.06..+0.04) |
| day of week | Mon -0.050, Tue -0.071, Wed -0.039, Thu +0.071, Fri +0.005 (noise-sized, t <= 1.6) |
| exit | held to 15:55 48% (-0.039), stop 24%, target 28% |

- **The setup beats random shorts by +0.04R per trade** (train +0.066, valid +0.022). Random same-minute shorts with
  the same exit lose -0.05R, because shorting loses on most days after costs.
  - On Bull days NS3-FD is +0.135R better than random (t 3.9) and still loses -0.154R.
  - The entry picks the right stocks to short. The losses come from being short at all on up-drifting days.
- **Up-day losses by time** (Bull + Choppy days, -574R in total):
  - before 11:30: -39R;
  - 11:30-13:00: -87R;
  - 13:00-14:00: -171R;
  - 14:00-15:00: -277R.
- **The worst days are big stacking days, and recently Bear days**: 2026-07-27 Bear -105R (156 trades), 2026-06-09 Bear
  -99R (260 trades), 2026-05-12 Choppy -82R, 2026-05-13 Bull -73R.

## Part 2/3 - the variants (key rows; every row in `variants.csv`, `explore.csv`, `plateau.csv`, `tables_out.md`)
Edit tests:
- **W1** avg R above P0 in train and in valid.
- **W2** beats random thinning in both periods.
- **W3** 2-year Bull + Choppy loss at least 25% smaller, with Bear-day total R at least 75% of P0's.
- **W4** keeps at least 50% of the trades.
- **W5** per-day difference t at least the lineage bar.

Merit:
- **Testing bar**: positive in both periods, beats random, t at least 4.90.
- **near-miss**: your rule.

| variant | trades train / valid | kept % | avg R train / valid | t 2y | Bull / Bear / Choppy / Quiet avg R | vs random entries tr / va | diff-t vs P0 | worst day | edit tests failed | merit |
|---|---|---|---|---|---|---|---|---|---|---|
| P0 NS3-FD as run | 6,660 / 10,295 | 100 | -0.004 / -0.021 | -0.63 | -0.154 / +0.067 / -0.067 / -0.008 | +0.066 / +0.022 | – | -105.3 | (parent) | no |
| P1 parent NS3 (Testing 1: 09:50-11:30, no refire) *ref* | 573 / 937 | 9 | +0.063 / +0.036 | 1.04 | -0.127 / +0.289 / +0.067 / -0.030 | +0.068 / +0.109 | – | – | – | best day 34% |
| B7 stop 1.5x, same target | 6,644 / 10,280 | 100 | +0.020 / -0.002 | 0.37 | -0.103 / +0.084 / -0.042 / +0.004 | +0.048 / +0.018 | 2.67 | -73.2 | W5 | no (valid < 0) |
| B7 stop 1.25x, same target | 6,648 / 10,284 | 100 | +0.013 / -0.010 | -0.04 | -0.126 / +0.081 / -0.049 / -0.001 | +0.057 / +0.020 | 2.87 | -87.8 | W3, W5 | no |
| A6 daily ATR >= 3% | 5,604 / 9,315 | 84 / 90 | +0.016 / -0.014 | -0.12 | -0.148 / +0.068 / -0.049 / +0.010 | +0.079 / +0.021 | 3.13 | -104.3 | W3, W5 | no |
| A8 SPY above its VWAP | 4,002 / 6,706 | 60 / 65 | +0.022 / -0.006 | 0.14 | -0.167 / +0.150 / -0.052 / +0.033 | +0.069 / +0.032 | 1.71 | -81.8 | W3, W5 | no |
| D4 09:50-11:30 (with refire) | 869 / 1,403 | 13 | +0.049 / +0.039 | 1.01 | -0.154 / +0.293 / +0.114 / -0.051 | +0.026 / +0.103 | 0.92 | -41.1 | W3, W4, W5 | no (best day 39%) |
| D5 after 11:30 only | 5,866 / 9,073 | 88 | -0.011 / -0.027 | -0.81 | -0.155 / +0.043 / -0.084 / +0.002 | +0.072 / +0.010 | -0.67 | – | W1-W3, W5 | no |
| D2 no entries after 14:00 | 3,679 / 5,538 | 55 / 54 | -0.047 / -0.003 | -0.94 | -0.191 / +0.051 / -0.020 / -0.000 | +0.056 / +0.047 | 0.19 | – | W1-W3, W5 | no |
| B1 target 0.5R | 6,804 / 10,555 | 102 | -0.033 / -0.014 | -1.38 | -0.126 / +0.016 / -0.046 / +0.000 | +0.053 / +0.028 | -0.67 | -75.8 | W1-W3, W5 | no |
| B5 half off at +0.35R | 6,660 / 10,295 | 100 | -0.015 / -0.016 | -0.90 | -0.122 / +0.038 / -0.044 / -0.007 | +0.059 / +0.028 | -0.11 | -83.6 | W1-W3, W5 | no |
| C1 first signal only | 4,009 / 6,192 | 60 | -0.028 / -0.036 | -1.63 | -0.174 / +0.034 / -0.082 / -0.014 | +0.075 / +0.018 | -0.38 | – | W1-W3, W5 | no |
| E1 LONG mirror | 6,660 / 10,295 | 100 | -0.131 / -0.081 | -4.31 | +0.032 / -0.169 / -0.058 / -0.113 | -0.027 / +0.024 | – | – | – | no |
| F ret20<0 + 1.5x stop (best train pair) | 2,661 / 4,800 | 40 / 47 | +0.078 / +0.008 | 1.08 | -0.101 / +0.113 / +0.001 / +0.004 | +0.045 / +0.017 | 2.01 | – | W4, W5 | no (best day 79%) |
| X1 stop 2.0x, same target (post-hoc) | 6,639 / 10,277 | 100 | +0.023 / +0.008 | 0.92 | -0.066 / +0.083 / -0.029 / +0.004 | +0.035 / +0.017 | 2.31 | -57.4 | W5 | no (best day 75%) |
| **V1 = 09:50-11:30 + stop 2.0x, same target (post-hoc)** | 868 / 1,402 | 13 | **+0.044 / +0.058** | **2.15** | **-0.037 / +0.200 / +0.092 / -0.014** | +0.018 / +0.061 | 0.97 | **-21.9** | W3, W4, W5 | **near-miss** (best day 18%) |

V1 by period and regime (avg R, trades):

| period | Bull | Bear | Choppy | Quiet |
|---|---|---|---|---|
| train | -0.024 (138) | +0.290 (267) | -0.014 (93) | -0.086 (361) |
| valid | -0.043 (313) | +0.132 (355) | +0.139 (210) | +0.036 (524) |
| NS3-FD train | -0.211 (1,013) | +0.185 (2,791) | -0.177 (771) | -0.094 (2,044) |
| NS3-FD valid | -0.115 (1,498) | -0.051 (2,793) | -0.025 (2,035) | +0.037 (3,969) |

**V1 plateau** (`plateau.csv`, post-hoc, counted). Train / valid avg R:

| last entry | stop 1.25x | stop 1.5x | stop 2.0x |
|---|---|---|---|
| 11:00 | +0.087 / +0.018 | +0.088 / +0.023 | +0.071 / +0.039 |
| 11:30 | +0.044 / +0.050 | +0.049 / +0.052 | +0.044 / +0.058 |
| 12:00 | +0.028 / +0.051 | +0.034 / +0.052 | +0.033 / +0.056 |

- All 20 plateau rows are positive in both periods: the 9 window/stop rows with the target fixed at NS3's price, the 9
  with the target scaled with the stop, and both refire-off rows. The scaled-target rows have a best day of 28-46% of
  total R.
- Only the 2x stop (and 1.5x at 11:30 / 12:00) keeps the best day under 25%.
- Bull-day avg R improves steadily with the wider stop: at 11:30, -0.135 (1.25x) / -0.102 (1.5x) / -0.037 (2x).

V1 against the windowed parent P1:
- avg R +0.044 / +0.058 against +0.063 / +0.036; t 2.15 against 1.04; total R +120R against +70R.
- Bull days -0.037 against -0.127.
- Trades per session (431 sessions) 5.3 against 3.5; V1 trades on 317 of them.

## The proposal (DECISION V1; not in any config)
- **Big Loser VWAP Reclaim Fade, Morning, Wide Stop** (`NS3V1-am-widestop-short`). Module:
  `research/bdi/ns3var1022/modules/NS3V1-am-widestop-short.py`, the same NS3 mask with 09:50-11:30.
- Module-vs-scan parity: 2,297 of 2,297 signal rows equal on all 21 open months, 0 mismatches (`verify_module.json`).
- Live block, no code needed: `type: lab`, the module path, `r_atr_frac: 0.5` (the module's GEOM is t05s1),
  `window: [950, 1130]`, `min_adv: 95000000`, `refire: true`, `refire_cooldown: 1`.
- A 0.5-ATR stop at the same $ risk means half the shares of NS3. Fewer signals will hit the "spread is % of stop
  distance" skip.
- Where: Testing 2, next to NS3-FD. Testing 2 holds one position per symbol across setups, so V1 has to come before
  NS3-FD in `setup_order`; otherwise NS3-FD takes every morning signal first. The parent NS3 in Testing 1 overlaps it
  too, but it is a different account.
- Caveats:
  - found after the grid, so VALID is not out of sample for it;
  - t 2.15 is far below 3.02 / 4.90;
  - still loses on Bull days (-0.037R) and in Quiet train (-0.086R);
  - about 5 trades per session (7 on the days it trades).

## Method
- `scripts/scan.py`: per open month, every candidate bar. The superset is: reclaim of VWAP, fromOpen < -1.5,
  09:50-15:00, adv20 >= 95M. Each row keeps the entry features and the forward 5-minute path. It also keeps one random
  same-minute partner (another adv >= 95M symbol, seeded) with its path, for the random-entry baseline under every exit
  rule, and the peer median fromOpen (gates1021 peers, train correlations).
- `scripts/tail.py`: 15:05-15:55 bars from the 1-minute cache.
- `scripts/sim.py`: one exit simulator. Parity with the frames' lab outcome (production cost, extended tier) on 74,043
  candidate bars: t05s1 100%, t1s1 / t1s05 99.999% within 1e-4R (1 row differs, a float32 tie).
- `scripts/load.py`: daily features from prior days only (20-day return, 60-day beta to SPY, daily ATR %), regime
  labels (regime1022), refire chain (`mcf.strategies.setups.refire_select`) and lot cap.
- Scripts: `variants.py` (grid, tests W1-W5, merit), `diag.py` (Part 1), `explore.py` (3 post-hoc rows), `plateau.py`
  (19 rows), `ref_p1.py` (P1 / V1 reference numbers), `verify_module.py`, `report.py` (`tables_out.md`).
- The P0 reproduction matches regime1022 / gates1021 exactly (16,955 trades, -0.0045 / -0.0214). P1 matches the
  regime1022 parent (1,510, +0.063 / +0.036).
- "vs random thinning" = variant total R - P0 total x the share of trades kept. "diff-t" = the t of the per-day
  difference vs P0 (all P0 days). t values are day-clustered.

**Files** (`research/bdi/ns3var1022/`):
- `PLAN.md`, `NOTES.md`, `scripts/`, `modules/NS3V1-am-widestop-short.py`;
- `variants.csv`, `explore.csv`, `plateau.csv`, `reference_rows.json`, `diag*.csv`, `tables_out.md`, `counts.json`,
  `verify_module.json`;
- `backlog_proposals.jsonl`, not appended to research/backlog.jsonl.

Scratch data (about 200 MB) stays in the session scratchpad (`nv22/`).

Educational only - not financial advice.
