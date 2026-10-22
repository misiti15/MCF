# regime1022: which setups are good in which market, who gets a gate, and do we need a daily stop (owner 2026-10-21 night)

*Educational only - not financial advice. Unless a line says "live" or "paper", numbers are backtests on the open
two-year history (lab frames 2024-10..2026-10-07; the locked block 2024-11-01..2025-02-28 was never read; no holdout
was scored). Costs are always in: production cost, time-of-day entry cost, x3 on the extended tier. "As-run" = the
account's refire chain + at most 3 lots per symbol, exits on the 5-minute path. TRAIN = sessions to 2025-12-31,
VALID = 2026-01-01..10-07. Live = paper journals (run 1) of the five accounts through 2026-10-21. `PLAN.md` was
written before anything was scored and was not changed. No config, setup or exit was changed.*

**Configurations scored: 384** (44 protection rules + 336 setup-gate pairs + 4 exploratory), plus descriptive splits
(160 regime-detection measurements, 56 setups x 4 conditions x 3 periods, Part A). Bars: gate lineage N 1,254
(gates1021 718 + bdi1021 196 + 340 here) -> **3.78**; protection lineage N 92 (ll1020 16 + gates1021 32 + 44) -> 3.01.

## The answers, short
1. **(i) Does a specialist's good regime outweigh its bad days? For the two setups you named, no.** Over two years
   Gap-Down Recovery Fade (all day) earned +272R on Bear days and lost -1,020R on the rest (net -767R, -0.031R/trade;
   negative in 2025 and in 2026). Big Loser VWAP Reclaim Fade (all day) earned +375R on Bear days and lost -621R on
   the rest (net -250R). Bear days are only 19% of sessions. Of 24 "regime specialists", 9 are net positive.
2. **(ii) Can we tell the regime at entry? Not well enough to gate on it.** The best at-entry calls (SPY >= +0.5% from
   the open at 11:00) are right 70-82% of the time when they fire but catch only 26-38% of Bull days; the prior day's
   SPY return has almost no information (lift 1.1-1.2). Trading these two shorts *only* when the tape already looks
   bearish makes them worse (L3 -0.073R, NS3 -0.042R per trade): shorting a market that is already down catches the
   rebound.
3. **(iii) Selection rule: a setup gets a gate only if all six tests pass (below). Applied to all 56 scored setups x 6
   gates: 0 qualify.** Best near-miss: Prior-day RSI Dip Long (all day) with "skip while SPY is below VWAP and <= -0.25%"
   (t 3.69 vs bar 3.78).
4. **The 10-20/10-21 losses were not an anomaly in size**: a day as bad as 10-21 happens on 12% (NS3-FD) and 26%
   (L3-FD) of the days each setup trades. Bad days do not cluster into streaks. **No daily stop is recommended**:
   on two years every protection rule only "helps" by trading less in books that lose, and none beats random thinning.
5. **Correction to last night's G1 decision: withdraw it.** The gates1021 "prior-day SPY" gate used *today's* SPY
   close-to-close by mistake (lookahead). Scored correctly, all six G1 finalists fail (t 0.04-2.17 vs 4.80-3.95).

## Failures first
- **gates1021 had a lookahead bug, and its six G1 finalists are invalid.** Its `scan.py` stored
  `close(d) / close(d-1)` under date d as "prior session SPY". That number is only known at day d's close. Re-scored
  with the real prior session (`close(d-1) / close(d-2)`) on identical trades (`gates_c.csv`; rows `U7h` reproduce
  gates1021 to the digit):

  | G1 finalist | gate t as published (lookahead) | gate t corrected | passes? |
  |---|---|---|---|
  | MF4-h40-open-flowsell-FD | 4.80 | 2.17 | no (valid avg R worse) |
  | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 4.78 | 0.65 | no |
  | MF3-open-flowsell-rsi5hi-FD | 4.62 | 1.79 | no |
  | RW7-gapdn-bounce-early-short-FD | 4.12 | 0.87 | no |
  | RW3-gapdn-rsi5pop-flowsell-short-FD | 4.09 | 1.00 | no |
  | RW1-gapdn-bounce-flowsell-short-FD | 3.95 | 0.04 | no |
  | NS3-failed-vwap-reclaim-short-FD (near-miss) | 2.94 | 0.61 | no |

  The "stable up-prior-day" finding in gates1021 (and its L3 prior-day idea) came from the same bug: the real prior
  day predicts a Bull session with lift only 1.14 / 1.21 (train / valid). Only gates1021 used the file
  (`grep spy_prev`). The modules' live code (if built) would read the true prior day, so they would not have
  behaved as the backtest promised.
- **0 of 336 setup-gate pairs pass the selection rule** (6 gates x 56 scored setups). 17 pass tests S1-S5; none reaches
  the bar 3.78 (S6). `gates_c.csv`.
- **0 of 44 protection rules qualify** (`part_b.csv`). Details in B.
- **Trading the named shorts only in a bearish-looking tape is worse** (exploratory, added after PLAN, counted 4):
  `explore.csv`. Even with perfect hindsight, Big Loser VWAP Reclaim Fade lost on Bear days in 2026 (-0.051R/trade,
  -142R); its "great when the market falls" record is a 2025 record (+0.185R/trade on Bear days).
- **50 of 106 live setup slots are not scored**: CWT / opening-range setups, IDX / classic setups, heat setups (the
  Graveyard), structural-exit and hold-to-close setups, the RW6G1 VWAP-band guard, ETF allow-lists
  (`setups_used.csv`). This includes two Primary setups: Failed Prior-Day-Low Break Long (CWT14-failbrk-pdl-p10-lowvol-long;
  top5_1021 found -0.095R/trade, up sessions +0.023 / down -0.203) and RW6G1-ns2-up3-vwap2sd-short (2-year +0.264R on
  424 trades, 226 of them on 2025-04-07).
- **Survivorship**: the lab universe is today's list. Setups named NM-* were mined on this same history, so their
  regime profiles are in-sample.
- **The book simulation is simplified**: no slots/buying power beyond position counts, no ETB/spread skips, no fill
  slippage beyond the cost model, no twin cap except in the Graveyard.

## A. Primary setups with a big live loss (`part_a.csv`, `part_a_days.csv`, `part_a_out.md`)
Selected by the pre-declared rule (live P/L since start <= -$100, or 10-20 + 10-21 <= -$100): 3 of 14.

| setup | live Primary (paper) | live all accounts (paper) | 2-year as-run | Bull / Bear / Choppy / Quiet avg R | day as bad as live worst |
|---|---|---|---|---|---|
| Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD) | 32 trades, 2 sessions, win 15.6% vs break-even 55.9%, -0.374R, t -4.2, -$484.71; 10-21 -11.7R | 84 trades, 7 sessions, win 39.3% vs 43.6%, -0.058R, t -0.35, -$358.95; last-4 -0.036R | 16,955 trades, -0.015R (t -0.63); train -0.004 / valid -0.021 | -0.154 / +0.067 / -0.067 / -0.008 | 51 of 425 traded days (12%), all regimes (Choppy 14, Bull 13, Quiet 13, Bear 11) |
| Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) | 5 trades, 1 session, 0 wins, -1.149R, -$176.93; 10-21 -5.7R | 133 trades, 7 sessions, win 61.7% vs 52.3%, +0.147R, t 0.7, +$350.18; last-4 +0.332R | 25,124 trades, -0.031R (t -0.62); train -0.032 / valid -0.029 | -0.051 / +0.078 / -0.066 / -0.027 | 101 of 395 traded days (26%): Bull 40, Quiet 36, Choppy 16, Bear 8 |
| RW6G1-ns2-up3-vwap2sd-short | 3 trades (10-15, Bull), 0 wins, -1.069R, -$102.18 | same | not scored (needs the 1-minute VWAP-band guard) | – | – |

- **By the session labels below, 10-20 (SPY +0.41% open-to-close) and 10-21 (+0.25%) were Choppy days, not Bull days**:
  wide ranges (1.05% and 0.78%, above the 20-day median 0.75-0.77%) with a slow up-drift. On two years both setups
  lose on Choppy days (-0.067R/trade each) and lose most on Bull days.
- **Not rare.** NS3-FD has a day at or below -11.7R on 12% of its traded days (12 per 100 sessions); L3-FD has a day at
  or below -5.7R on 26% of its traded days. Those days come in every regime, mostly Bull and Quiet.
- **No streaks.** After a bottom-decile day, the next traded day is bottom-decile 14% (NS3-FD) and 5% (L3) of the time,
  against a 10% base rate; the longest run is 2 days for both.
- **Concentration by regime** (setup-days): NS3-FD averages +4.6R on Bear days, -4.3R on Bull days, -2.6R on Choppy;
  L3-FD +3.8R / -7.1R / -3.8R. That is a short-side market bet that loses on balance.
- **Live Primary lost in every regime** (paper, 12 sessions): Bear 47 trades -0.068R, Bull 48 -0.607R (10-15, -$927),
  Choppy 164 -0.161R, Quiet 207 -0.124R. The live losses are not a two-day event.

## B. Daily stop / protection (`part_b.csv`, `part_b_days.csv`, `part_b_out.md`, `part_b_live_primary.csv`)
Four books on two years: Primary (12 covered setups), Testing 1, Testing 2, Graveyard. Each book is simulated in time
order with its own as-run rules (account-wide 3 lots per symbol, per-setup and concurrent caps, Primary's -20R realized
account stop, the testing accounts' -2R per-setup realized stop and -120R account stop, the Graveyard twin cap). 11
variants per book. "vs random thinning" = the variant's total R minus (the as-run total x the share of trades kept):
positive means the rule removed worse-than-average trades, not just fewer trades.

**Primary book** (train / valid; worst-5% = mean R of the book's worst 5% of days; the next column is the same rule's
result on the as-run book's own worst 5% of days):

| variant | kept % | total R | avg R | vs random thinning | worst day | worst-5% days | on as-run's worst-5% days | days <= -10R |
|---|---|---|---|---|---|---|---|---|
| P0 as-run | 100.0 / 100.0 | -2633 / -1052 | -0.1029 / -0.0355 | +0 / +0 | -150.6 | -88.2 | -88.2 | 203 |
| B1a per-setup 1 open lot per symbol | 83.9 / 84.6 | -2229 / -954 | -0.1038 / -0.0381 | -20 / -64 | -96.5 | -68.2 | -64.1 | 190 |
| B1b per-setup 2 open lots per symbol | 95.5 / 95.2 | -2569 / -1020 | -0.1051 / -0.0362 | -54 / -19 | -118.1 | -82.1 | -80.5 | 201 |
| B1c per-setup max 5 open lots | 60.6 / 54.3 | -1475 / -541 | -0.0951 / -0.0336 | +121 / +30 | -39.1 | -31.8 | -19.3 | 147 |
| B1d per-setup max 10 open lots | 78.3 / 72.5 | -1856 / -659 | -0.0926 / -0.0307 | +206 / +104 | -58.8 | -43.2 | -31.1 | 186 |
| B2a per-setup realized+open stop -3R | 43.5 / 38.2 | -959 / -359 | -0.0861 / -0.0317 | +187 / +44 | -28.5 | -21.8 | -12.0 | 120 |
| B2b per-setup realized+open stop -4R | 50.9 / 45.7 | -1215 / -469 | -0.0933 / -0.0346 | +125 / +12 | -31.8 | -26.2 | -15.0 | 152 |
| B3a account realized+open stop -10R | 31.5 / 26.0 | -718 / -287 | -0.0892 / -0.0372 | +110 / -13 | -23.4 | -13.0 | -9.7 | 61 |
| B3b account realized+open stop -15R | 43.4 / 36.4 | -983 / -314 | -0.0885 / -0.0290 | +160 / +70 | -35.2 | -18.4 | -13.7 | 141 |
| B3c account realized+open stop -20R | 53.1 / 44.9 | -1210 / -403 | -0.0891 / -0.0302 | +187 / +70 | -49.8 | -23.5 | -17.8 | 170 |
| B4a cluster cap 3 (20d corr > 0.7) | 82.9 / 83.7 | -2107 / -962 | -0.0993 / -0.0388 | +77 / -81 | -96.8 | -61.1 | -52.3 | 185 |
| B4b cluster cap 5 (20d corr > 0.7) | 87.8 / 90.0 | -2233 / -987 | -0.0994 / -0.0370 | +79 / -40 | -94.4 | -66.5 | -58.9 | 194 |

- **The as-run Primary book loses on two years** (-0.103R per trade in train, -0.036R in valid). In a losing book
  every cap "improves" total R just by trading less, so the test that matters is "vs random thinning".
- **Pre-declared recommendation test** (total R >= as-run in both periods, beats random thinning in both, keeps >= 80%,
  worst-5% days >= 20% better): **no variant passes.**
  - The ones that beat random thinning in both periods (B1c, B1d, B2a, B2b, B3b, B3c) keep only 26-78% of trades.
  - The ones that keep >= 80% (B1a, B1b, B4a, B4b) lose to random thinning in at least one period, i.e. they remove
    better-than-average lots.
  - The plan's fallback ("insurance": largest tail gain with total R no more than 3% worse and >= 90% kept) selects
    **B1b, at most 2 open lots per symbol per setup**: total R slightly better than as-run, but the worst-5% days only
    7% better (-82 vs -88R) and it removes better-than-average lots (-54R / -19R vs random). It is offered, not
    recommended.
- **The other books disagree with each other.** The per-setup -3R realized+open stop beats random thinning on
  Testing 1 (+115R / +143R) but loses to it on Testing 2 (-111R / -38R) and is neutral on the Graveyard. The cluster
  cap beats random in train and loses in valid in every book. The account-level realized+open stop loses to random
  on Testing 1 and Testing 2.
- **Live Primary replay** (paper, 12 sessions, 466 trades, diagnosis only): every rule "saves" money because the book
  lost (-84.3R). The -3R realized+open per-setup stop gives -17.3R (keeps 54%); random thinning to 54% would give about
  -45R. On 10-21 it would have cut -14.8R to -2.5R. Twelve sessions are not evidence; two years say this does not
  hold up across books.

**Recommendation: none. Do not add a daily stop.** The 10-20/10-21 losses were ordinary bad days for two
short-side setups that lose on two years; a stop cannot turn a losing setup into a winner, and on two years no rule
removes bad trades better than random. The fix is setup selection: demote NS3-FD (N5) and judge L3-FD at its
10-27 review. The existing rules stay (Primary -20R realized account stop; testing accounts -2R per setup).

## C. Market conditions and "who gets a gate"
### Labels (`scripts/regime.py`; one per session, SPY regular session, hindsight)
| label | definition | share of sessions (2 years) |
|---|---|---|
| **Bull** | SPY closed >= +0.5% above its open | 21.6% |
| **Bear** | SPY closed >= 0.5% below its open | 19.2% |
| **Choppy** | SPY within +-0.5% of its open, high-low range at or above its 20-day median | 17.1% |
| **Quiet** | SPY within +-0.5% of its open, range below its 20-day median | 42.0% |

Cut-offs kept as pre-declared. At +-0.3% the split is 144 Bull / 120 Bear / 38 Choppy / 130 Quiet; at +-0.75% Bull and
Bear shrink to about 11% each. Live sessions 10-06..10-21: 6 Quiet, 3 Choppy (10-08, 10-20, 10-21), 2 Bear (10-14,
10-16), 1 Bull (10-15).

### Classes (pre-declared; `classes.csv`, `regime_by_setup.csv`, `years.csv`, `live_by_regime.csv`)
- **all-weather**: avg R >= -0.02 in every condition (>= 30 trades each) and >= 0 overall. **6 setups**: five
  NM-* observation setups mined on this same history, plus ST8-volspikedn-long-pm-t1s1-FD (528 trades).
- **regime specialist**: best condition avg R >= +0.03, t >= 2, positive in train and valid. **24 setups**: 14 shorts whose best
  condition is Bear, 7 longs whose best is Bull, 3 shorts best in Choppy or Quiet. **9 of the 24 are net positive** over the real mix; the other 15 lose
  more in their bad conditions than they earn in their good one.
- **loser**: no condition where it reliably earns. **26 setups**, including both setups you named: their Bear edge is
  real in sign but not strong or stable enough (L3-FD Bear t 1.36; NS3-FD Bear +0.185R in 2025, -0.051R in 2026).

### (i) Does success in one condition outweigh the losses elsewhere? (net over the real mix, `years.csv`)
| setup | Bear R | Bull R | Choppy R | Quiet R | net 2 years | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) | +272 | -622 | -252 | -146 | **-767** | -430 | -310 |
| Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD) | +375 | -386 | -188 | -47 | **-250** | -54 | -220 |

- Bear sessions are one in five. A setup that earns +0.07R on those and -0.03..-0.15R on the other four in five loses.
- With **perfect hindsight** (trade only on Bear sessions) L3-FD would be +0.078R/trade (+272R) and NS3-FD +0.067R
  (+375R, but -142R in 2026). That is the ceiling for any gate, and no rule known at entry gets near it.

### (ii) Can the condition be identified at entry? (`detect.csv`; one row per session; precision = how often the call is right, recall = share of such days it catches)
| at-entry call (train / valid) | Bull: precision | Bull: recall | Bear: precision | Bear: recall |
|---|---|---|---|---|
| prior session SPY >= +0.5% / <= -0.5% (true prior day) | 0.27 / 0.23 | 0.33 / 0.38 | 0.16 / 0.18 | 0.14 / 0.22 |
| SPY from open >= +0.25% / <= -0.25% at 10:30 | 0.53 / 0.58 | 0.54 / 0.70 | 0.55 / 0.42 | 0.53 / 0.50 |
| SPY from open >= +0.5% / <= -0.5% at 11:00 | 0.70 / 0.82 | 0.26 / 0.38 | 0.83 / 0.56 | 0.49 / 0.31 |
| SPY >= +0.25% and above its VWAP / mirror at 11:00 | 0.56 / 0.46 | 0.57 / 0.62 | 0.63 / 0.50 | 0.69 / 0.59 |
| QQQ from open >= +0.25% / <= -0.25% at 11:00 | 0.44 / 0.36 | 0.59 / 0.76 | 0.50 / 0.41 | 0.76 / 0.75 |
| breadth >= 0.6 / <= 0.4 at 11:00 | 0.44 / 0.42 | 0.61 / 0.60 | 0.47 / 0.33 | 0.71 / 0.50 |
| breadth rising / falling >= 0.1 in 30 min at 11:00 | 0.40 / 0.19 | 0.32 / 0.22 | 0.38 / 0.23 | 0.39 / 0.31 |
| *hindsight, the gates1021 bug: today's SPY close-to-close* | *0.59 / 0.50* | *0.72 / 0.81* | *0.73 / 0.54* | *0.67 / 0.62* |
Base rates: Bull 0.24 / 0.19, Bear 0.21 / 0.17.

- By 10:30-11:00 the tape tells you something (precision 2-3x the base rate), but a call that is right half the time
  and misses a third or more of the days is not enough for these setups: their losses come from Choppy and Quiet days
  as well, and their wins come from Bear days that often *look* calm at 11:00.
- The prior day tells you almost nothing once it is computed correctly. That retires the "prior-day up" idea.
- Acting on the call the other way (trade the shorts only when it already looks bearish) loses more (failures
  above), consistent with direction1020: weak opens tend to rebound.

### (iii) The selection rule (pre-declared): a setup gets a market-condition gate only if ALL hold
1. **S1 real split**: its worst condition is below its other conditions with t >= 2 in train and >= 1 in valid.
2. **S2 detectable**: a pre-declared at-entry gate improves its R per parent trade in train and in valid.
3. **S3 light touch**: the gated setup keeps >= 80% of its trades in both periods and blocks <= 20% of its winners.
4. **S4 better, not just smaller**: gated avg R beats the parent in both periods and total R does not fall.
5. **S5 never gate an all-weather setup.**
6. **S6 survives the search**: pooled gate t >= max(1.5, sqrt(2 ln N)) over the whole gate lineage (3.78 tonight).
Gates tested (shorts; longs mirrored): R1 prior SPY >= +0.5%; R2 prior SPY >= +0.5% and SPY >= 0; R3 SPY above VWAP
and >= +0.25%; R4 from 10:30, SPY's first hour >= +0.25%; R5 breadth >= 0.60 and rising; U7 (gates1021, corrected).

**Result: 0 of 56 setups qualify.** 21 setups pass S1 (a real, stable split), 17 setup-gate pairs pass S1-S5, none
passes S6. Near-misses (rework, not candidates; `backlog_proposals.jsonl`): Prior-day RSI Dip Long (all day)
(NS1-rsidip-rsi5pop-long-FD) R3 t 3.69; RW7-FD R4 2.69; RW1-FD R4 2.40; RW3-FD R4 2.15. All four gated versions still
lose after costs. **No module was written** because no gated variant passed.

### Verdicts for the two setups you named
- **Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD): keep as-is, no gate; decide at its 10-27 Primary review.**
  No gate helps (best: U7 t 1.49; S1 fails, its worst condition flips between periods: Choppy -0.227 in train, +0.110
  in valid). It loses -0.031R/trade on two years in both periods. Live it is +0.147R on 133 paper trades across
  accounts (5 in Primary, all lost on 10-21). If its Primary record at the 10-27 review is below break-even, move it
  back to Testing.
- **Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD): demote (N5 yes).** Its split is real
  (Bull -0.154R, t -3.95; S1 t 3.16 / 1.89) but no at-entry gate captures it (best R4 t 1.83; corrected U7 0.61), its
  Bear-day edge vanished in 2026 (-0.051R/trade even with hindsight), and live it is -0.058R on 84 paper trades.

### Per-setup table (every live setup; `selection.csv`)
Class, best / worst condition and avg R per condition are the 2-year as-run backtest after costs; "best gate" is the
gate that passed the most tests (t = pooled gate-delta t; fails = tests not met).

| setup (id) | acct | class | best / worst | 2-yr avg R (train / valid) | Bull / Bear / Choppy / Quiet avg R | best gate (t; fails) | verdict |
|---|---|---|---|---|---|---|---|
| Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (CWT14-failbrk-pdl-p10-lowvol-long) | P | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) | P | loser | Bear / Choppy | -0.030 (-0.032 / -0.028) | -0.051 / +0.078 / -0.066 / -0.027 | U7 (1.49; S1,S6) | no gate qualifies; loses net on 2 years in both periods |
| Early Sellers Above VWAP (MF1-945-flowsell-vwapup) | P | loser | Bear / Bull | -0.078 (-0.143 / +0.006) | -0.277 / +0.047 / -0.057 / -0.028 | R2 (1.94; S6) | no gate qualifies; mixed (one period positive) |
| Early Sellers, Mid-High RSI (MF2-open-rsimidhi-flowsell) | P | loser | Choppy / Bull | -0.034 (-0.091 / +0.001) | -0.142 / -0.052 / +0.100 / -0.049 | R2 (0.69; S1,S4,S6) | no gate qualifies; mixed (one period positive) |
| Early Sellers, Mid-High RSI (all day) (MF2-open-rsimidhi-flowsell-FD) | P | loser | Bear / Bull | -0.043 (-0.028 / -0.055) | -0.159 / +0.079 / -0.092 / -0.094 | R4 (0.85; S2,S4,S6) | no gate qualifies; loses net on 2 years in both periods |
| Early Sellers, Strong Heat (MF4-h40-open-flowsell) | P | loser | Bear / Bull | -0.099 (-0.146 / -0.051) | -0.344 / +0.033 / -0.020 / -0.066 | R5 (2.46; S4,S6) | no gate qualifies; loses net on 2 years in both periods |
| Early Sellers, Strong Heat (all day) (MF4-h40-open-flowsell-FD) | P | loser | Bear / Bull | -0.085 (-0.119 / -0.051) | -0.302 / +0.017 / -0.048 / -0.058 | R1 (3.91; S3,S4) | no gate qualifies; loses net on 2 years in both periods |
| Big Gainer Dip-and-Pop (NS1-rsidip-rsi5pop-long) | P | loser | Bull / Bear | +0.031 (-0.008 / +0.054) | +0.137 / -0.112 / -0.063 / +0.049 | U7 (0.79; S1,S6) | no gate qualifies; mixed (one period positive) |
| Big Loser VWAP Reclaim Fade (all day) (NS3-failed-vwap-reclaim-short-FD) | P | loser | Bear / Bull | -0.015 (-0.004 / -0.021) | -0.154 / +0.067 / -0.067 / -0.008 | R4 (1.83; S6) | no gate qualifies; loses net on 2 years in both periods |
| Afternoon VWAP Reclaim Fade (NS4-pm-vwap-reclaim-oversold-short) | P | loser | Bear / Bull | -0.069 (-0.128 / -0.024) | -0.174 / +0.068 / -0.006 / -0.057 | R4 (1.82; S1,S3,S6) | no gate qualifies; loses net on 2 years in both periods |
| Big Loser Flush Buy (NS5-sma50-flush-oversold-long) | P | regime specialist | Bull / Bear | -0.042 (-0.174 / +0.094) | +0.257 / -0.308 / -0.003 / +0.137 | R1 (-0.62; S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| Gap-Down Pop Fade, Heavy Selling (all day) (RW3-gapdn-rsi5pop-flowsell-short-FD) | P | regime specialist | Bear / Bull | -0.071 (-0.095 / -0.045) | -0.310 / +0.125 / -0.058 / -0.071 | R4 (2.15; S6) | no gate qualifies; loses net on 2 years in both periods |
| Gap-Down Pop Fade (all day) (RW5-heat30-flowsell-rsi5pop-gapdn-short-FD) | P | regime specialist | Bear / Bull | -0.060 (-0.054 / -0.066) | -0.323 / +0.178 / -0.044 / -0.041 | R5 (2.62; S3,S6) | no gate qualifies; loses net on 2 years in both periods |
| Big Gainer Fade with VWAP Band Guard (RW6G1-ns2-up3-vwap2sd-short) | P | not scored | – | – | – | – | needs the 1-minute VWAP-band guard |
| Panic Flush Reversal (3x volume) (CWT05-flush-m05-v3-long) | T1 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Coil Under the High (6 bars) (CWT12-coil-k6-long) | T1 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-High Break Short (0.05 ATR, low volume) [fill] (CWT14-failbrk-pdh-p05-lowvol-short) | T1 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-High Break Short (0.1 ATR) [fill] (CWT14-failbrk-pdh-p10-short) | T1 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-Low Break Long (shallow) (CWT14-failbrk-pdl-p05-long) | T1 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Index Dip Bounce 1 TQQQ (hold) (IDX1-qqq100-0955-TQQQ-hold) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| Index Dip Bounce 1 TQQQ (IDX1-qqq100-0955-TQQQ-trail) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| Index Dip Bounce 2 3x S&P (IDX2-spy075-0945-3x-trail) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| Index Dip Bounce 3 3x S&P (IDX3-spy075-0955-3x-trail) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| Index Dip Bounce 5 3x S&P (IDX5-spy050-0945-3x-trail) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| L3-gap-slope-lowdist-FD (L3-gap-slope-lowdist-FD) | T1 | loser | Bear / Bull | -0.129 (-0.149 / -0.107) | -0.327 / +0.195 / -0.134 / -0.027 | U7 (1.41; S4,S6) | no gate qualifies; loses net on 2 years in both periods |
| Prior-Day Low Sweep Reversal to VWAP (LIQ-pdl-sweep-open15-vwap-long) | T1 | not scored | – | – | – | – | geom S (no frame outcome) |
| Early Sellers into a Pop (MF3-open-flowsell-rsi5hi) | T1 | regime specialist | Bear / Bull | -0.086 (-0.124 / -0.034) | -0.383 / +0.164 / -0.004 / -0.046 | U7 (1.83; S6) | no gate qualifies; loses net on 2 years in both periods |
| Early Sellers into a Pop (all day) (MF3-open-flowsell-rsi5hi-FD) | T1 | regime specialist | Bear / Bull | -0.076 (-0.099 / -0.051) | -0.342 / +0.104 / -0.069 / -0.040 | U7 (1.79; S6) | no gate qualifies; loses net on 2 years in both periods |
| Sellers into Strength (all day) (MF5-flowsell-vwapup-rsi5hi) | T1+T2 | regime specialist | Bear / Bull | -0.057 (-0.096 / -0.006) | -0.345 / +0.171 / -0.003 / +0.005 | U7 (1.48; S6) | no gate qualifies; loses net on 2 years in both periods |
| NS1-rsidip-rsi5pop-long-FD (NS1-rsidip-rsi5pop-long-FD) | T1 | regime specialist | Bull / Bear | -0.070 (-0.075 / -0.066) | +0.090 / -0.282 / -0.161 / -0.090 | R3 (3.69; S6) | no gate qualifies; loses net on 2 years in both periods |
| Big Loser VWAP Reclaim Fade (NS3-failed-vwap-reclaim-short) | T1 | regime specialist | Bear / Bull | +0.046 (+0.063 / +0.036) | -0.127 / +0.289 / +0.067 / -0.030 | U7 (1.50; S1,S6) | keep as-is; profitable in both periods, no gate |
| NS4-pm-vwap-reclaim-oversold-short-FD (NS4-pm-vwap-reclaim-oversold-short-FD) | T1 | loser | Bear / Bull | -0.060 (-0.106 / -0.026) | -0.164 / +0.070 / -0.015 / -0.050 | R4 (1.85; S1,S3,S6) | no gate qualifies; loses net on 2 years in both periods |
| NS5-sma50-flush-oversold-long-FD (NS5-sma50-flush-oversold-long-FD) | T1+T2 | loser | Bull / Bear | -0.046 (-0.100 / +0.004) | +0.063 / -0.201 / +0.059 / +0.011 | R1 (-0.70; S1,S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| RW4-ns3-adv150-short-FD (RW4-ns3-adv150-short-FD) | T1+T2 | loser | Bear / Bull | -0.011 (+0.005 / -0.021) | -0.142 / +0.064 / -0.058 / -0.003 | R4 (1.28; S6) | no gate qualifies; mixed (one period positive) |
| RW6G1-ns2-up3-vwap2sd-short-FD (RW6G1-ns2-up3-vwap2sd-short-FD) | T1 | not scored | – | – | – | – | needs the 1-minute VWAP-band guard |
| RW7-gapdn-bounce-early-short-FD (RW7-gapdn-bounce-early-short-FD) | T1 | regime specialist | Bear / Bull | -0.061 (-0.083 / -0.040) | -0.335 / +0.194 / -0.139 / -0.051 | R4 (2.69; S6) | no gate qualifies; loses net on 2 years in both periods |
| ST3-rsi5up-short-pm-t1s1-FD (ST3-rsi5up-short-pm-t1s1-FD) | T1 | loser | Choppy / Bull | +0.007 (-0.026 / +0.022) | -0.154 / +0.068 / +0.076 / +0.031 | R3 (0.57; S1,S3,S4,S6) | no gate qualifies; mixed (one period positive) |
| ST4-emadn-long-am-t1s05-FD (ST4-emadn-long-am-t1s05-FD) | T1 | regime specialist | Bull / Bear | +0.017 (-0.043 / +0.056) | +0.149 / -0.042 / +0.020 / +0.033 | U7 (1.17; S1,S4,S6) | no gate qualifies; mixed (one period positive) |
| ST5-pdbrkup-short-mid-t05s1-FD (ST5-pdbrkup-short-mid-t05s1-FD) | T1 | loser | Quiet / Bear | -0.029 (-0.078 / +0.004) | -0.052 / -0.110 / -0.021 / +0.030 | R5 (1.02; S1,S3,S4,S6) | no gate qualifies; mixed (one period positive) |
| ST6-volspikeup-short-mid-t1s1-FD (ST6-volspikeup-short-mid-t1s1-FD) | T1 | loser | Bear / Bull | +0.015 (-0.094 / +0.057) | -0.038 / +0.054 / +0.004 / +0.018 | U7 (0.82; S1,S6) | no gate qualifies; mixed (one period positive) |
| ST7-rsi50dn-long-pm-t1s1-FD (ST7-rsi50dn-long-pm-t1s1-FD) | T1 | regime specialist | Bull / Bear | +0.024 (-0.062 / +0.071) | +0.226 / -0.177 / +0.126 / +0.021 | U7 (-1.21; S1,S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| ST8-volspikedn-long-pm-t1s1-FD (ST8-volspikedn-long-pm-t1s1-FD) | T1 | all-weather | Bear / Quiet | +0.034 (-0.004 / +0.051) | +0.049 / +0.066 / +0.040 / -0.010 | R5 (0.29; S1,S2,S4,S5,S6) | keep as-is; never gate (all-weather) |
| Afternoon Blow-off Short (exhaustion_short) | T1 | loser | Bear / Bull | -0.007 (-0.054 / +0.037) | -0.091 / +0.095 / -0.015 / +0.033 | R4 (1.03; S1,S3,S6) | no gate qualifies; mixed (one period positive) |
| exhaustion_short-FD (exhaustion_short-FD) | T1+T2 | regime specialist | Bear / Bull | -0.067 (-0.110 / -0.032) | -0.227 / +0.129 / +0.013 / -0.044 | R1 (2.37; S3,S6) | no gate qualifies; loses net on 2 years in both periods |
| Index Last-Half-Hour Momentum (intraday_momentum) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| 20-Minute Opening Range Breakout (orb20_a) | T1 | not scored | – | – | – | – | type classic (not a lab mask) |
| Backside Lower-High Short (CWT04-backside-lh-a15-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Backside Lower-High Short (big runner) (CWT04-backside-lh-a25-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Backside VWAP-Test Short (CWT04-backside-vwaptest-a15-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Backside VWAP-Test Short (big runner) (CWT04-backside-vwaptest-a25-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Panic Flush Reversal (5x volume) (CWT05-flush-m05-v5-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Panic Flush Reversal (deep, 3x volume) (CWT05-flush-m075-v3-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Panic Flush Reversal (deep, 5x volume) (CWT05-flush-m075-v5-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Gap-Down Bounce Rejection Short (10% gap) (CWT09-gapdn-bounce-g10-lowerhalf-short) | T2 | not scored | – | – | – | – | geom S (no frame outcome) |
| Gap-Down VWAP Loss Short (10% gap) (CWT09-gapdn-vwaploss-g10-short) | T2 | not scored | – | – | – | – | geom S (no frame outcome) |
| Gap-Down VWAP Loss Short (5% gap) (CWT09-gapdn-vwaploss-g5-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Coil Under the High (4 bars) (CWT12-coil-k4-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Spike-Pullback Flag Breakout (CWT12-flag-s1-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Stretched Below VWAP Bounce (CWT13-vwapstretch-z05-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Stretched Above VWAP Fade (CWT13-vwapstretch-z05-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Stretched Below VWAP Bounce (far) (CWT13-vwapstretch-z075-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Stretched Above VWAP Fade (far) (CWT13-vwapstretch-z075-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-High Break Short (low volume) (CWT14-failbrk-pdh-p10-lowvol-short) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-Low Break Long (0.05 ATR, low volume) [fill] (CWT14-failbrk-pdl-p05-lowvol-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Prior-Day-Low Break Long (CWT14-failbrk-pdl-p10-long) | T2 | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| L3-gap-slope-rsi5hi-FD (L3-gap-slope-rsi5hi-FD) | T2 | loser | Bear / Choppy | -0.041 (-0.084 / +0.005) | -0.076 / +0.077 / -0.143 / +0.025 | R2 (1.31; S1,S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| * Oversold Pop with Breadth Turning Up (near-miss) (LD1-ns1-breadthup-t05s1-long) | T2 | regime specialist | Bull / Quiet | +0.095 (+0.080 / +0.108) | +0.181 / -0.076 / +0.049 / +0.119 | R2 (0.51; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| * Shallow Nasdaq Dip, Breadth Turn (TQQQ) (near-miss) (LD2-qqq-dip015-breadthturn-tqqq-t05s1-long) | T2 | not scored | – | – | – | – | index/ETF allow-list setup |
| * Oversold Slope Turn after an SPY Dip-Turn (near-miss) (LD3-st2-idxturn-t05s1-long) | T2 | loser | nan / nan | +0.212 (+0.014 / +0.310) | +0.359 / +0.199 / -0.115 / +0.246 | R2 (0.59; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| * Oversold EMA Cross-Down with Breadth Turning Up (near-miss) (LD4-st4-breadthup-t1s05-long) | T2 | loser | nan / nan | +0.389 (+0.345 / +0.403) | +0.886 / +0.571 / +0.218 / -0.169 | R2 (0.99; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| * Oversold Slope Turn with Breadth Turning Up (near-miss) (LD5-st2-breadthup-t05s1-long) | T2 | loser | nan / nan | +0.154 (+0.072 / +0.194) | +0.048 / +0.136 / +0.469 / +0.166 | R2 (1.01; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| * SPY Dip of 0.2 ATR, Breadth Turn (SPXL, trailing) (near-miss) (LD6-spy-dip020atr-breadthturn-spxl-holdtr-long) | T2 | not scored | – | – | – | – | geom holdtr (no frame outcome) |
| * Oversold Pop after an SPY Dip-Turn (trailing) (near-miss) (LD7-ns1-idxturn-holdtr-long) | T2 | not scored | – | – | – | – | geom holdtr (no frame outcome) |
| * SPY Dip of 0.30%, Breadth Turn (SPXL, trailing) (near-miss) (LD8-spy-dip030-breadthturn-spxl-holdtr-long) | T2 | not scored | – | – | – | – | geom holdtr (no frame outcome) |
| MF5-flowsell-vwapup-rsi5hi-FD (MF5-flowsell-vwapup-rsi5hi-FD) | T2 | regime specialist | Bear / Bull | -0.057 (-0.096 / -0.006) | -0.345 / +0.171 / -0.003 / +0.005 | U7 (1.48; S6) | no gate qualifies; loses net on 2 years in both periods |
| Quiet Downtrend Bounce Short (near-miss) (NM-AMS-N1-quiet-morning-short) | T2 | all-weather | Bear / Bull | +0.131 (+0.184 / +0.082) | +0.065 / +0.239 / +0.134 / +0.078 | U7 (-0.25; S1,S2,S4,S5,S6) | keep as-is; never gate (all-weather) |
| Gap-Down Capitulation Buy (near-miss) (NM-AR-AM-gapdown-capitulation-long) | T2 | regime specialist | Bull / Choppy | +0.262 (+0.328 / +0.204) | +0.495 / +0.326 / -0.022 / +0.218 | R2 (-1.17; S1,S2,S3,S4,S6) | keep as-is; profitable in both periods, no gate |
| Late-Day ETF Dip Buy (near-miss) (NM-ETF-late-dip-di-long) | T2 | not scored | – | – | – | – | index/ETF allow-list setup |
| Afternoon Higher-Low Long (near-miss) (NM-HL-T75-pm-long) | T2 | all-weather | Choppy / Quiet | +0.044 (+0.052 / +0.038) | +0.072 / +0.009 / +0.139 / +0.007 | R4 (1.06; S1,S3,S5,S6) | keep as-is; never gate (all-weather) |
| Early Sellers into a Pop (index down, no gap up) (near-miss) (NM-MF3-qqqdn-gapdn-FD) | T2 | regime specialist | Bear / Bull | -0.010 (-0.010 / -0.010) | -0.499 / +0.134 / -0.126 / -0.028 | R5 (1.44; S6) | no gate qualifies; loses net on 2 years in both periods |
| Gap-Down Reclaim Fade, Afternoon (near-miss) (NM-PM-gapdn-above-pdh-rvol-short) | T2 | all-weather | Bull / Quiet | +0.239 (+0.320 / +0.112) | +0.318 / +0.271 / +0.110 / +0.042 | R2 (-1.02; S1,S2,S3,S4,S5,S6) | keep as-is; never gate (all-weather) |
| Early NS3 Short While SPY Up (near-miss) (NM-RWN3-ns3-spyup-early-short) | T2 | all-weather | Bear / Choppy | +0.159 (+0.195 / +0.130) | +0.179 / +0.566 / +0.051 / +0.065 | R4 (-1.24; S1,S2,S4,S5,S6) | keep as-is; never gate (all-weather) |
| NS2 Short, SPY Up 0.5%, Not Friday (near-miss) (NM-RWN4-ns2-spyup05-notfri-short) | T2 | regime specialist | Quiet / Bull | +0.113 (+0.098 / +0.143) | +0.085 / +0.404 / +0.417 / +0.219 | R1 (-0.72; S1,S2,S3,S4,S6) | keep as-is; profitable in both periods, no gate |
| Monday Weak-RS NS3 Short (near-miss) (NM-RWN5-ns3-mon-weakrs-short) | T2 | regime specialist | Bear / Quiet | +0.196 (+0.157 / +0.252) | +0.156 / +0.526 / +0.197 / -0.034 | U7 (0.10; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| Afternoon Exhaustion Short, Gap-Down, SPY Up (near-miss) (NM-RWR1-exh150-gapdn-spyup-pm-short) | T2 | regime specialist | Quiet / Bull | +0.151 (+0.121 / +0.182) | +0.084 / +nan / +0.234 / +0.421 | R1 (-0.85; S1,S2,S4,S6) | keep as-is; profitable in both periods, no gate |
| Early NS3 Short While QQQ Up (near-miss) (NM-RWR3-ns3-qqqup-early-short) | T2 | all-weather | Bear / Quiet | +0.205 (+0.251 / +0.169) | +0.242 / +0.650 / +0.198 / +0.055 | U7 (-0.49; S1,S2,S4,S5,S6) | keep as-is; never gate (all-weather) |
| NS2 Up-3 Short, QQQ Up, Slope Down (near-miss) (NM-RWR4-ns2-up3-qqqup-slopedn-short) | T2 | regime specialist | Choppy / Bull | +0.114 (+0.121 / +0.104) | +0.100 / -0.053 / +0.230 / +0.131 | R1 (-0.96; S1,S2,S3,S4,S6) | keep as-is; profitable in both periods, no gate |
| Gap-Down VWAP Loss Short, Slope Filter (near-miss) (NM1-cwt09-g10-vwaploss-short) | T2 | loser | Choppy / Bull | +0.051 (-0.028 / +0.137) | -0.081 / +0.127 / +0.169 / -0.023 | R2 (0.45; S1,S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| RW1-gapdn-bounce-flowsell-short-FD (RW1-gapdn-bounce-flowsell-short-FD) | T2 | regime specialist | Bear / Bull | -0.049 (-0.073 / -0.026) | -0.324 / +0.181 / -0.094 / -0.029 | R4 (2.40; S6) | no gate qualifies; loses net on 2 years in both periods |
| Gap-Down Bounce Rejection Short (5% gap) (CWT09-gapdn-bounce-g5-lowerhalf-short) | GY | not scored | – | – | – | – | geom S (no frame outcome) |
| Failed Opening-Range-Low Break Long (0.05 ATR) [fill] (CWT14-failbrk-orl-p05-long) | GY | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Opening-Range-Low Break Long (0.05 ATR, low volume) [fill] (CWT14-failbrk-orl-p05-lowvol-long) | GY | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (CWT14-failbrk-orl-p10-long) | GY | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Failed Opening-Range-Low Break Long (low volume) (CWT14-failbrk-orl-p10-lowvol-long) | GY | not scored | – | – | – | – | needs 09:35-09:45 head rows (opening-range logic) |
| Opening-Range Low Sweep Reversal (LIQ-orl-sweep-open15-s25-long) | GY | not scored | – | – | – | – | geom S (no frame outcome) |
| MF1-945-flowsell-vwapup-FD (MF1-945-flowsell-vwapup-FD) | GY | regime specialist | Bear / Bull | -0.079 (-0.100 / -0.052) | -0.248 / +0.087 / -0.048 / -0.049 | R5 (4.66; S3) | no gate qualifies; loses net on 2 years in both periods |
| Big Gainer Average Reclaim Fade (NS2-sma50break-overbought-short) | GY | loser | Bear / Bull | +0.001 (+0.031 / -0.026) | -0.037 / +0.067 / +0.067 / -0.001 | R1 (1.00; S1,S3,S4,S6) | no gate qualifies; mixed (one period positive) |
| NS2-sma50break-overbought-short-FD (NS2-sma50break-overbought-short-FD) | GY | loser | Bear / Bull | -0.059 (-0.046 / -0.069) | -0.154 / +0.075 / -0.028 / -0.035 | U7 (0.81; S1,S4,S6) | no gate qualifies; loses net on 2 years in both periods |
| RW2-exhaustion-noon-adv150-short-FD (RW2-exhaustion-noon-adv150-short-FD) | GY | regime specialist | Bear / Bull | -0.062 (-0.100 / -0.031) | -0.224 / +0.138 / +0.012 / -0.034 | U7 (1.41; S6) | no gate qualifies; loses net on 2 years in both periods |
| RW6-ns2-up3-short-FD (RW6-ns2-up3-short-FD) | GY | loser | Bear / Quiet | -0.016 (+0.024 / -0.048) | -0.029 / +0.096 / +0.021 / -0.065 | U7 (-0.04; S1,S2,S4,S6) | no gate qualifies; mixed (one period positive) |
| ST1-ordn-long-pm-t05s1-FD (ST1-ordn-long-pm-t05s1-FD) | GY | loser | Bull / Bear | -0.058 (-0.042 / -0.070) | +0.015 / -0.178 / +0.004 / -0.025 | R5 (2.02; S1,S3,S6) | no gate qualifies; loses net on 2 years in both periods |
| ST2-slope20up-long-am-t05s1-FD (ST2-slope20up-long-am-t05s1-FD) | GY | regime specialist | Bull / Bear | -0.019 (-0.057 / +0.005) | +0.074 / -0.060 / +0.019 / -0.030 | R2 (0.73; S1,S6) | no gate qualifies; mixed (one period positive) |
| Midday Gap-Up Dip Buy (heat_fade_long) | GY | not scored | – | – | – | – | type heat (not a lab mask) |
| heat_fade_long-FD (heat_fade_long-FD) | GY | not scored | – | – | – | – | type heat (not a lab mask) |
| Morning Bounce Fade (heat_fade_short) | GY | not scored | – | – | – | – | type heat (not a lab mask) |
| heat_fade_short-FD (heat_fade_short-FD) | GY | not scored | – | – | – | – | type heat (not a lab mask) |

## D. Dashboard: "Best conditions" column
- `docs/live/regimes.json` (`scripts/make_regimes_json.py`; validated by `python -m mcf.report.regimes` and
  `tests/test_regimes_json.py`): labels, definitions, and for 53 scored setup names best / worst condition (among
  conditions with >= 30 trades), trades and avg R per condition, class, source.
- `docs/live/index.html`: leaderboard column **Best conditions** (coloured chip: Bull green, Bear red, Choppy amber,
  Quiet grey; hover shows the worst condition, the class and every condition's trades and avg R; "—" when not scored),
  a **Market conditions — 2-year backtest** table in the setup drill-down (`#sd-reg`), and glossary entries for the
  column and the four labels. `tests/test_dashboard_inventory.py` gained the column, `sd-reg` and the data source;
  nothing was removed.
- Checked headless (Playwright, chromium from /opt/pw-browsers) at 1366 and 390 px with raw.githubusercontent routed to
  `git show origin/<branch>`: column present, 53 chips, drill-down table renders, no horizontal page scroll, no JS errors.

## Method notes
- Signals: every covered live lab setup of Primary / T1 / T2 / Graveyard (`scripts/scan.py`, reusing
  gates1021 `scan.py` functions; 52 unique signal definitions for 56 names), with the 5-minute exit bar for every
  setup (gates1021 had it for two). As-run (`scripts/asrun.py`) reproduces gates1021's trade counts exactly
  (NS3-FD 16,955; L3-FD 25,124).
- Regime labels: `scripts/regime.py`; live sessions from read-only SIP bars of SPY/QQQ/IWM
  (`scripts/fetch_live_idx.py`; keys from the environment, never written).
- Gate deltas and t: day-clustered, per parent trade (as gates1021). S1 t = (rest avg R - worst-condition avg R) /
  sqrt(se^2 + se^2) with day-clustered standard errors.
- Live record: `scripts/live.py` reads the journals (run 1) from origin/mcf-data* with `git show`; R = pnl_adj / risk.

**Files** (all under `research/bdi/regime1022/`): `PLAN.md`, `NOTES.md`, `scripts/` (rc, rsetups, scan, asrun,
regime, fetch_live_idx, live, part_a, book, detect, part_c, explore, selection, make_regimes_json), outputs
`setups_used.csv`, `setups_scored.csv`, `part_a*.csv/md`, `part_b*.csv/md`, `detect.csv`, `classes.csv`,
`regime_by_setup.csv`, `years.csv`, `live_by_regime.csv`, `gates_c.csv`, `explore.csv`, `selection.csv`,
`selection_table.md`, `counts.json`, `counts_c.json`, `backlog_proposals.jsonl` (8 entries; not appended to
research/backlog.jsonl). Scratch data (about 60 MB) stays in the session scratchpad.

Educational only - not financial advice.
