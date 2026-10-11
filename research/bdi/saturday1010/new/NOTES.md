# BD&I Saturday 2026-10-10, new ideas: post-earnings drift (PEAD) and FINRA short-volume ratio on daily bars

*Educational only - not financial advice. Lab backtests on daily bars; nothing here is a live or paper result.*

**Section 1 (the pre-declaration) was written before any configuration was scored.** Before writing it I only:
(a) read the schemas and date ranges of the new files, (b) checked that the earnings dates match announcement volume
(volume only, no returns, see 0.2), and (c) checked that `lib.py` reproduces longhold's `S6_mom12_1rev_N20_W` daily
returns exactly (max abs diff 6e-9, float32 storage). Section 1 changes only by dated amendments in 1.9.

## 0. Data
### 0.1 Sources
- Daily bars: `research/swarm1010/w3_daily/data/daily_2016.parquet` + longhold's `etf_extra.parquet`, loaded by
  `lib.py`, which copies the data block, eligibility, cost model, locked-block zeroing, calendars and simulator from
  `research/longhold/study.py` (study.py reruns and rewrites its outputs on import, so it is copied, not imported).
- From git branch `research-data` (published 2026-10-10 05:25 UTC), copied to `data/` (git-ignored):
  `earnings_cal.parquet` (118,203 rows, 2019-01-01..2026-11-09, 4,961 symbols; no rows in the locked block) and
  `finra_shvol_2019..2026.parquet` (FINRA Reg SHO daily short-sale volume; 2024 ends 2024-10-31, 2025 starts
  2025-03-03). **No `*_lockedblock.parquet` file is read.** `MCF_HIST_ALLOW_LOCKED` is never set.
- FINRA "totalvolume" is the volume reported to FINRA's facilities (TRFs/ADF/ORF), not consolidated volume, and
  "shortvolume" includes market-maker and hedging shorts. The ratio is a noisy flow proxy, **not short interest**.

### 0.2 Earnings dates and timing (data check, no returns)
- `time` is `time-not-supplied` for 116,709 of 118,203 rows (98.7 %); 748 after-hours, 746 pre-market. So bmo/amc
  can't set the reaction day for almost all events.
- For 27,176 events in our symbols (2019..2026-10), median volume vs the prior-20-day median is 1.27x on d-1, **1.85x
  on d, 1.90x on d+1**, 1.43x on d+2. The peak is on d in 48 % of events and on d+1 in 52 %. For the known rows the
  peak is on d for 90 % of pre-market events and on d+1 for 89 % of after-hours events. The dates are right, and the
  report falls either before the open of d or after the close of d.
- **Consequence (fixed):** the reaction is measured over close(d-1) -> close(d+1) for every event (covers bmo and
  amc), the signal is at the close of d+1 and the fill at the open of d+2. That uses no future information
  whatever the timing, at the cost of one day of drift for bmo events. Here d is the first trading day on or after
  the calendar date.

### 0.3 Survivorship and sample
- The symbol list is today's liquid universe applied backward (no delisted names at all). Long-only levels are
  inflated (longhold: the EW universe beat RSP by 6.3 %/yr). Active returns vs the same-universe EW benchmark are less
  affected but not immune: a PEAD long book holds names that rallied on earnings, and the names that later died
  are missing.
- Sample: 2019-01..2026-10 without the locked block, about 7.4 years, so roughly 89 months. One full cycle, one
  bear year (2022).

## 1. Pre-declaration

### 1.1 Splits
| split | dates | use |
|---|---|---|
| warm-up | before 2019-01-01 | features only |
| train | 2019-01-01 .. 2022-12-31 | in-sample |
| valid | 2023-01-01 .. 2024-10-31 | validation |
| LOCKED | 2024-11-01 .. 2025-02-28 | **not used**: every daily return is set to 0 before simulation (positions do not drift), its days are dropped before any statistic, no FINRA/earnings rows exist for it here. The lead scores finalists on it once |
| valid2 | 2025-03-01 .. 2026-10-09 | second validation |
Gates pool all three splits (2019-01..2026-10 without the locked block), as the task asks; there is no separate
fitting step (every configuration is a fixed rule), and the splits are reported separately for consistency.

### 1.2 Mechanics (all configurations, as longhold)
Signal at the close of t, MOO fill at the open of t+1. Costs per side `0.01/open + 0.0001` on every traded dollar.
Long-only. Universe at t = longhold eligibility: not ETF, close >= $5, 20-day median dollar volume >= $20M, >= 253 bars.
Missing price: return 0. Name with no open on the execution day: not traded that day.

### 1.3 Family P: post-earnings announcement drift (PEAD)
Events: every earnings_cal row whose symbol is in the bar file; d = first trading day on or after its date. Duplicates
of the same symbol within 10 sessions keep the first. The event needs closes at d-1 and d+1, the signal row is
s = d+1 (<= 2026-10-08 so a fill exists), and the stock must be eligible at d-1 (pre-event).
Scores (all known at the close of s):
- **RAW** = (C[d+1]/C[d-1] - 1) - (SPY C[d+1]/C[d-1] - 1) (market-adjusted 2-day reaction).
- **Z** = RAW / (sd of daily stock-minus-SPY returns over the 60 sessions ending d-2 (min 40) x sqrt(2)).
- **ZV** = Z, keeping only events with abnormal volume: max(V[d], V[d+1]) / median V over the 20 sessions ending d-2
  >= 2 (others are not candidates).
- **OC** = sum over d and d+1 of the open-to-close return minus SPY's (the intraday part of the reaction).
Bucket: an event's score percentile among all scored events of the same score with signal rows in [s-252, s-1]
(min 500 events, else no candidates that day; trailing, so no look-ahead). **Top 10 % or top 20 %** = long
candidates. **Bottom 10 %** = short-side diagnostic (evaluated as a long-only book of the weakest reactions; the
live book is long-only, so it's a diagnostic and never a candidate).
Book (`lib.simulate_slots`): K equal slots; at the open of s+1, positions whose holding period is over are sold first,
then candidates fill free slots in score order (strongest first), each with 1/K of current equity (capped by cash, no
leverage); a name already held isn't added again. Held H sessions (sold at the open H sessions after the fill).
Names that stay aren't re-weighted. Idle cash earns 0.
Grid: score {RAW, Z, ZV, OC} x bucket {top10, top20} x H {20, 40, 60} x K {20, 50} = **48**;
diagnostics bottom10 x score {4} x H {3} x K 50 = **12**. Family P total **60**.
Benchmark: **exposure-matched EW universe**, b[d] = exposure[d-1] x EW[d] (the book is often partly in cash; this
compares the invested part to the same universe). EW universe and SPY are also reported.
Control (rule 6, not counted, not a candidate): **ALL** = every eligible event regardless of reaction, filled in a
fixed random order (seed 20261010), same H and K (6 rows). This separates the drift from the earnings-season premium
and from the slot mechanics.

### 1.4 Family V: FINRA short-volume ratio
SVR[t] = shortvolume / totalvolume (totalvolume > 0), on the trading-day grid, NaN where FINRA has no row. Features at
the close of t use FINRA data through t (published ~18:00 ET; the runner's evening run is 18:20 ET and OPG orders open
19:00 ET); a one-day-lag variant is a diagnostic for finalists only (1.8).
- **L5** = mean SVR over the last 5 sessions (min 4); **L20** = over 20 (min 15).
- **D5** = L5 - mean SVR over the 60 sessions before those 5 (min 40); **D20** = L20 - mean over the 60 sessions
  before those 20 (min 40). (Level and change; literature: heavy short flow -> lower future returns, so LOW = long.)
V1 standalone sorts (long-only, equal weight; vs EW universe):
- lowest-N: feature {L5, L20, D5, D20} x N {20, 50} x rebalance {W, M} = **16**
- lowest quintile (all eligible names in the bottom 20 % of the feature): 4 x {W, M} = **8**
- highest-N diagnostic (long the HIGHEST, N 50): 4 x {W, M} = **8** (diagnostic, never a candidate)
V2 filter on S6 (longhold `S6_mom12_1rev`: drop the top decile of 21-day return, hold the top N by 12-1 momentum):
before ranking, drop names whose feature is in the top q of eligible names with the feature. A name with no feature
keeps its place; at a rebalance where fewer than half the eligible names have the feature (FINRA gap) no filter is
applied.
- N 20: feature {4} x q {10 %, 20 %, 30 %} x rebalance {W, M} = **24**
- N {10, 50}, W, q 20 %: 4 x 2 = **8**
Family V total **64**. V2 benchmark = **the unfiltered S6 with the same N and rebalance** (the question is whether the
filter adds value); vs EW universe also reported and required (1.6).

**Total N = 60 + 64 = 124.** Try-count bar `t_required(124) = sqrt(2 ln 124) = 3.10` for every configuration (the bar
uses the scan's total, not the family's: 60 -> 2.86, 64 -> 2.88 are reported for information).

### 1.5 Statistics (per split and pooled "all")
CAGR, vol, Sharpe (rf 0), maxDD, turnover (one-way/yr), cost drag (%/yr), mean exposure (P), active = annualised
arithmetic mean of daily strategy minus benchmark, monthly active t (mean/sd x sqrt(months), months clustered = the
day-clustering of rule 4 at monthly resolution), monthly active t without the best month (rule 5), share of months
beating the benchmark, active in SPY-up / SPY-down months, per calendar year return and active, number of trades
(P: entries).

### 1.6 Gates (fixed now)
**A "edge candidate"** (all; diagnostics and controls are never candidates):
- G1 active > 0 in train, valid and valid2. For V2 also active vs EW universe > 0 in all three.
- G2 pooled monthly active t >= 3.10.
- G3 walk-forward share >= 0.6: rule-19 folds (3 months train, next month test, step 1). A frozen rule has nothing to
  fit, so the share is the fraction of test months (every month from the 4th open month on) with active > 0.
- G4 active > 0 in SPY-up months and in SPY-down months (pooled).
- G5 plateau: mean pooled active of the neighbours (one parameter one step: P: score RAW<->Z, Z<->ZV, RAW<->OC;
  bucket 10<->20; H 20-40-60; K 20<->50. V1: L5<->L20, D5<->D20, L5<->D5, L20<->D20; N 20<->50; W<->M. V2: same
  feature steps; q 10-20-30; W<->M; N 10-20-50) > 0.
**near:** pooled active > 0 and active > 0 in at least 2 of the 3 splits. **fail:** the rest.
Turnover and cost drag are reported for every row.

### 1.7 Recommendation rule (fixed now)
At most 2 finalists for the lead's one-time locked-block score, Tier A only, at most one per family, ranked by pooled
monthly active t. They must also keep pooled active > 0 under each 1.8 diagnostic. If nothing passes, nothing is
recommended for a locked look and the best near-misses are listed as backlog ideas.

### 1.8 Diagnostics (not counted; can only remove a candidate)
For A-passes and the best near-miss per family: 2x costs; one-day execution delay (fill at the open of t+2); top-300
universe by ADV (P and V1); for V, features lagged one day (FINRA through t-1).

### 1.9 Amendments (dated)
(none yet)

## 2. Results (124 configurations; failures first)

*Educational only - not financial advice. Backtest only (daily bars, MOO fills at the next open, costs 1c + 1 bps per
side in). The locked block 2024-11..2025-02 is in no figure. Window: 2019-01-02..2026-10-09 without the locked block
(1,874 sessions, 89 months). "active" = annualised arithmetic mean of daily (strategy - benchmark); t = monthly active
t over the 89 months; WF = share of test months (month 4 on) with active > 0.*

**Counts.** 124 pre-declared configurations scored (P 60 incl. 12 short-side diagnostics, V 64 incl. 8 high-side
diagnostics). Not counted: 6 random-event controls, 2 benchmarks, 4 unfiltered S6 baselines, 14 diagnostic reruns
(1.8). Try-count bar t >= 3.10. **No configuration passes Tier A, so nothing is recommended for a locked-block look
(rule 1.7).**

| family (N) | A_edge | near | fail | diagnostic |
|---|---|---|---|---|
| P PEAD long books (48) | 0 | 22 | 26 | - |
| P bottom-10 % short-side diagnostic (12) | - | - | - | 12 |
| V1 lowest-N short-volume ratio (16) | 0 | 1 | 15 | - |
| V1q lowest-quintile short-volume ratio (8) | 0 | 2 | 6 | - |
| V1h highest-N diagnostic (8) | - | - | - | 8 |
| V2 short-volume filter on S6 momentum (32) | 0 | 3 | 29 | - |
| **total (124)** | **0** | **28** | **76** | **20** |

### 2.0 Benchmarks on this window (reference)
| series | CAGR | Sharpe | maxDD | active vs EW | t |
|---|---|---|---|---|---|
| EW universe (today's list) | 21.0 % | 0.99 | -40 % | - | - |
| SPY | 17.8 % | 0.95 | -34 % | -3.2 %/yr | -1.36 |
| S6 N20 W (unfiltered, the longhold finalist) | 62.5 % | 1.37 | -44 % | +36.0 %/yr | 3.21 |
| S6 N20 M / N10 W / N50 W | 65.1 / 76.8 / 44.3 % | | | +37.5 / +46.8 / +21.4 %/yr | 3.18 / 3.38 / 2.76 |
| PEAD control: random events, H20 K50 | 13.7 % | 0.75 | -36 % | -0.3 %/yr vs expo-matched EW | -0.13 |
| PEAD controls, all 6 (H x K) | 11.5-17.4 % | | | -5.2..+0.2 %/yr | -1.79..+0.01 |

### 2.1 Failures
- **Short-volume ratio as a filter on S6 momentum (V2, 32): 29 fail, 3 near, none helps.** Dropping the names with
  the highest short-volume ratio (level or change, top 10/20/30 %) cuts S6's return in 28 of 32 configurations:
  active vs the unfiltered S6 is -6.9..+0.8 %/yr pooled (t -2.4..+0.4). The 3 "near" rows (`dropD5_q10` W,
  `dropL20_q10` M, `dropD20_q10` M) gain +0.1..+0.8 %/yr at t 0.2-0.4, and none survives 2x costs, a one-day delay or
  a one-day FINRA lag (diag.csv; all go negative). The filtered books still beat the EW universe by +18..+45 %/yr,
  but only because S6 does.
- **Long the lowest short-volume ratio (V1 + V1q, 24): 21 fail, 3 near.** The change features (D5, D20) are
  negative in every configuration (-3.3..-7.2 %/yr, t down to -2.8): names whose short ratio *fell* lagged the
  universe. The level features are about flat: best `V1_L5_low_N20_W` +2.2 %/yr (t 0.56; train +6.1, valid +0.6,
  valid2 -5.8 %/yr) at 36x turnover and a 2.5 %/yr cost drag. `V1_L20_lowQ5_W` +1.2 %/yr (t 0.51), with all of
  it in valid2. Neither holds under 2x costs, top-300 or a one-day lag.
- **PEAD long books (P, 48): 26 fail, 22 near, best t 2.01.** Long the strongest 2-day market-adjusted reaction:
  - RAW top 10 % is positive in all 6 (H, K) cells, +1.8..+5.4 %/yr vs the exposure-matched EW universe, t
    0.4-2.0.
  - Volatility scaling (Z) and abnormal-volume conditioning (ZV) do *worse* than RAW (Z: -5.4..+1.5 %/yr; ZV
    -4.5..+3.1 %/yr). The intraday part of the reaction (OC) is -2.7..+3.6 %/yr.
  - Longer holds decay: H40/H60 are negative in 20 of 32 cells, and H20 is the only hold with every top-10 % cell
    positive.
  - No PEAD cell reaches WF 0.6 (best 0.575), and none clears t 3.10.
  - **Absolute level:** the books hold 30-93 % stock (idle cash earns 0). Against the plain EW universe they are
    -16..+2 %/yr (46 of 48 negative). Only invested dollar for invested dollar do they beat it.
- **Best PEAD near-miss `P_RAW_top10_H20_K50`** (long the top 10 % 2-day reactions, 50 slots of 2 %, 20-session hold):
  - Active +3.5 %/yr (train +2.1, valid +6.2, valid2 +3.9 %/yr), t 2.01, ex-best-month t 1.77, WF 0.575.
  - SPY-up months +5.3 %/yr, SPY-down months **-0.6 %/yr** (fails G4).
  - Positive in 7 of 8 calendar years (2020 -0.8 %).
  - Exposure 42 %, turnover 5.3x/yr, cost drag 0.3 %/yr, CAGR 9.7 %, maxDD -27 %.
  - It survives 2x costs (+3.2 %/yr, t 1.82) and a one-day delay (+3.1 %/yr, t 1.69). **It does not survive the
    top-300 universe** (+0.9 %/yr, t 0.60, train negative), so most of it comes from smaller, less liquid names,
    where both survivorship and real fill costs are worst.
  - The random-event control with the same H20 K50 is -0.3 %/yr, so the reaction sort adds about 4 %/yr. That spread
    is not significant after 124 tries.
- **Short-side PEAD diagnostic (bottom 10 %, 12):**
  - For Z and ZV the weakest reactions do lag (Z bottom -1.3..-3.4 %/yr, t down to -1.9). That is the drift seen
    from the short side, which a long-only book can't harvest.
  - For RAW and OC the weakest reactions *beat* the exposure-matched EW (+0.5..+2.7 %/yr): there is no clean
    asymmetry. RAW top-minus-bottom at H20 K50 is +3.0 %/yr.
- **High short-volume diagnostic (V1h, 8):** long the 50 highest-ratio names lags EW in 8 of 8 rows,
  -2.8..-5.9 %/yr. Level L5 is the strongest (W: -5.7 %/yr, t -2.31; M: -5.9 %/yr, t -2.16; W negative in 6 of 8
  years). That matches the literature that heavy short flow predicts lower returns. The effect sits on the
  **short** side only (the low side does not outperform), and removing these names from S6 does not help (V2). So it
  can't be used in the long-only live book as tested. At 124 tries a t of -2.3 is also below the bar.

### 2.2 Passes
None. No configuration meets G1-G5. The closest on the gates is `P_RAW_top10_H20_K50`: it fails G2 (t 2.01 < 3.10),
G3 (0.575 < 0.6) and G4 (down months -0.6 %/yr), and passes G1 and G5.

### 2.3 Honest caveats
- **Survivorship:** today's symbol list. It biases long PEAD books up: a positive reaction in a name that later failed
  is missing. The top-300 rerun, which carries less survivorship bias, removes most of the PEAD near-miss.
- **Short sample:** 89 months, a single regime cycle. The monthly t has about 88 degrees of freedom, and a 3.10 bar
  needs a large, steady effect.
- **Earnings timing:** 98.7 % of events have no bmo/amc flag. The uniform 2-day window gives up the first day of
  drift on bmo events (about half). A cleaner timing source could add a little to PEAD, but the 4 known-timing
  checks suggest the window is right.
- FINRA ratios include market-maker shorting and only FINRA-reported volume. They are not short interest, and short
  interest (bi-monthly) was not available.

## 3. Recommendation
- **No locked-block look** (rule 1.7: no Tier-A pass). Burning a look on a t 2.0 near-miss would leak the block for
  nothing.
- Backlog (prefix `sat1010-new-`): four failed ideas with their numbers, plus two rework ideas for rule 18:
  - PEAD as a fully invested sleeve: idle slots go to the EW universe or S6 instead of cash, H 10/15/20, RAW top
    5/10 %, large-cap only.
  - A "high short-volume ratio" avoid-list for any EW-style long book.
- **Live needs, if a rework ever passes:**
  - PEAD: a daily refresh of the earnings calendar (the `research-data` workflow publishes it; it must be fetched
    before the 18:20 ET run). The signal is the close of the day after the report, from the daily bar already
    pulled, and MOO the next morning. The book is event-driven, so the runner needs a daily (not weekly) job with
    per-position exit dates.
  - Short volume: the FINRA daily file for day t is posted around 18:00 ET, so the evening run would have to start
    after it lands, or use t-1 (the lag1 diagnostic was tested and was no better).

## 4. Files
`NOTES.md` (this), `lib.py` (loader/simulator copied from longhold, parity-checked), `study.py` (grid, gates,
diagnostics), `results.csv` (config x split x calendar year, plus controls and benchmarks), `gates.csv` (one row per
config with its verdict, gates, neighbours), `diag.csv` (1.8 diagnostics). `data/` is git-ignored and holds the
copies of the research-data files (~80 MB).
Reproduce: `python research/bdi/saturday1010/new/study.py` (~15 min, one process, ~0.9 GB RAM).
