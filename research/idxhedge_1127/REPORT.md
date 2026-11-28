Educational only — not financial advice

# IDXHEDGE-1127: one-shot SPY/QQQ long hedge sleeve on Primary's book. Research only. **FAIL (0 of 12)**

## In plain words

- **The hedge is cheap but does almost nothing to the tail.** Primary loses most on days when the stocks it is short get
  squeezed. We tested buying SPY or QQQ once a day at a "squeeze moment" that can be seen in real time, sized at 0.25x or
  0.5x Primary's net short exposure. It costs very little: 1 to 20 R a year, at most about 0.05 R/day (0.11 R/day under the
  stress test). That is well under the 0.2 R/day budget. But it cuts Primary's worst-5 days by only 0-3% on CHECK and T2.
  The bar was 10%. Days at or below -10R do not fall in a consistent way.
- **Why:** an index can only offset the market part of a squeeze. Primary's worst days are squeezes in single stocks.
  On CHECK's worst day (2025-11-07, -33.5R) SPY rose only 0.48% and no trigger fired. When the hedge does fire on a bad day,
  it helps: B6-QQQ-k0.5 added +14.4R on 2026-03-09 and +8.7R on 2026-05-12, and +34R in total across CHECK's worst 10
  days. Other days then become the worst five, so worst-5 hardly moves. The VWAP-loss exit also cuts many trades early
  (hit rate 5-50%).
- **Trigger A** (heavy gap-down morning, then SPY reclaims VWAP after 10:30) is the weakest. It loses on every split,
  including FIT, and makes every setup slightly worse. **Trigger B** (Primary's open book at -6R or -10R while SPY is
  above VWAP) is about break-even after costs (CHECK +0.00 to +0.05 R/day, T2 -0.02 to +0.01). That is the "one-shot hedge"
  idea from HEDGE-B, and it no longer costs 60-120 R a year. Its benefit is too small to count as a remedy, though.
- **Verdict: FAIL as a remedy.** Bar 1 (cost) passes everywhere. Bar 2 (worst-5 at least 10% better, days <= -10R not
  higher) fails in all 12 configs on both splits. Nothing changes; no DECISION draft.

**Configs: 12** (pre-registered: trigger {A, B6, B10} x {SPY, QQQ} x k {0.25, 0.5}). **Cumulative N ≈ 9,350 → ≈ 9,362**
(family bar ≈ 4.28 for reference; per-study bar t >= 2.23). No sleeve reaches t 1 on CHECK and T2 together.

## Setup (PREREG.md, sha256 in PREREG.sha256, committed d4751fa1f6 before any score)
- Engine **E4** (research/cfprimary_1127/e4nb.py) extended to record each minute's closed + open book R and net beta
  exposure (ih_e4.py). Daily R by setup matches the original engine exactly on all 861 days, in both contexts
  (max |diff| 0.0). bench10 was rebuilt tonight with 52,544 lots, matching cfprimary/rwout. REF CHECK is -2.05 R/day
  (LO) and -3.03 R/day (BASE), as in earlier studies.
- Costs: **LIVE-L** on Primary's shorts and LR8 on NM-ETF. Index legs use **IDX-L**: 1 bp per side plus SEC, TAF and CAT
  fees. **LR8-IDX** (about 2.7 bp round trip) and a **stress** case (+1 minute on fill and exit, +2 bp per side) are shown
  alongside.
- Fill is one minute after the trigger. Exit is at the first SPY close below VWAP, or else flat at calendar close
  - 5 min (12:55 on half days). VWAP is computed from regular-session bars, with bars after a half-day close dropped.
- Splits: FIT (used only to set the q67 gap-down threshold = 0.102, plus confirmation), **CHECK** 2025-10-01..2026-11-04
  (276 sessions), **T2** 2023-01-03..2024-09-13 (415). There is no EARLY split: the Primary bench does not exist before
  2023. The locked block 2024-11-01..2025-02-28 was filtered and asserted absent in every script.
- Contexts: **LO** (LATCH-OPEN, main, as pre-registered) and **BASE** (realised -2R latch) alongside.

## Results, LO (main): Primary alone -> Primary + sleeve
| Config | CHECK dR/day (stress) | T2 dR/day (stress) | Cost R/yr C / T2 | Worst-5 CHECK (ref -25.7) | Worst-5 T2 (ref -14.5) | Days <= -10R C (39) / T2 (22) | Red/mo C (12.7) / T2 (12.8) | Hedge days C / T2 |
|---|---|---|---|---|---|---|---|---|
| A-SPY-k0.25 | -0.017 (-0.050) | -0.013 (-0.026) | 4.8 / 2.4 | -25.3 | -14.5 | 40 / 22 | 12.8 / 12.8 | 119 / 107 |
| A-SPY-k0.5 | -0.034 (-0.099) | -0.025 (-0.052) | 9.7 / 4.8 | -24.9 | -14.5 | 40 / 22 | 12.9 / 12.9 | 119 / 107 |
| A-QQQ-k0.25 | -0.006 (-0.029) | -0.006 (-0.017) | 3.4 / 1.9 | -25.2 | -14.5 | 39 / 22 | 12.8 / 12.8 | 119 / 107 |
| A-QQQ-k0.5 | -0.011 (-0.058) | -0.013 (-0.034) | 6.7 / 3.8 | -24.8 | -14.4 | 40 / 22 | 12.9 / 12.8 | 119 / 107 |
| B6-SPY-k0.25 | +0.010 (-0.056) | -0.010 (-0.044) | 10.1 / 4.1 | -25.2 | -14.2 | 40 / 18 | 12.8 / 13.0 | 129 / 88 |
| B6-SPY-k0.5 | +0.020 (-0.112) | -0.021 (-0.088) | 20.1 / 8.2 | -25.3 | -15.2 | 36 / 14 | 12.9 / 13.0 | 129 / 88 |
| B6-QQQ-k0.25 | +0.024 (-0.021) | -0.006 (-0.032) | 7.3 / 3.2 | -25.0 | -14.1 | 37 / 19 | 12.8 / 13.0 | 129 / 88 |
| B6-QQQ-k0.5 | +0.047 (-0.041) | -0.012 (-0.065) | 14.5 / 6.4 | -24.9 | -15.0 | 34 / 17 | 12.9 / 13.0 | 129 / 88 |
| B10-SPY-k0.25 | +0.001 (-0.038) | +0.002 (-0.004) | 5.5 / 1.0 | -25.1 | -14.0 | 40 / 22 | 12.8 / 12.9 | 53 / 26 |
| B10-SPY-k0.5 | +0.003 (-0.076) | +0.004 (-0.008) | 11.1 / 2.1 | -25.2 | -14.9 | 41 / 19 | 12.8 / 12.9 | 53 / 26 |
| B10-QQQ-k0.25 | -0.001 (-0.032) | +0.005 (+0.000) | 4.0 / 0.8 | -25.0 | -14.1 | 41 / 22 | 12.8 / 12.9 | 53 / 26 |
| B10-QQQ-k0.5 | -0.002 (-0.064) | +0.010 (+0.000) | 8.1 / 1.6 | -25.0 | -14.9 | 39 / 19 | 12.8 / 12.9 | 53 / 26 |

- **Controls (LO).** Random-time hedges (500 draws, same number of hedge days, same sizing and exit) give a median dR of
  about -0.01 R/day. The configs' worst-5 gains sit between the 0th and 98th percentile of those draws. Only the B10
  k0.25 configs beat the 90th percentile on both splits, and their gain is under 1R on worst-5. The size-matched
  constant hedge (10:30 -> 15:55, same notional-minutes) is about flat (-0.05 to +0.01 R/day) and moves worst-5 by
  < 1R. The always-on version at the same sizing rule costs up to -0.13 R/day.
- **Sleeve on its own:** day-clustered t from -2.2 to +0.5 on CHECK/T2 (bar 2.23); best positive t is B6-QQQ +0.52 on
  CHECK. The best-day share of the tail benefit is 49-111% where it is defined, so the tail help comes from 1-2 days
  (`1 day` tag). Bar 6 passes only for B10-SPY on T2.
- **FIT** is the only split where trigger B makes money: +0.06 to +0.24 R/day, with sleeve t <= 1.0. Trigger A
  loses there too (-0.04 to -0.09).
- Hedge days that fall in Primary's worst 20% of days: A about 30%, B6 40-67%, B10 81-92%. Trigger B does find the bad days.
  It just does not offset enough of them.

## BASE (realised -2R latch) alongside
Trigger B does a little better in BASE, but still fails bar 2. B6-QQQ-k0.5: CHECK +0.097 R/day (stress -0.016), worst-5
-35.6 -> -31.4 (-11.8%) but days <= -10R 62 -> 64. T2 -0.038 R/day, worst-5 -24.4 -> -22.8 (-6.5%), days <= -10R 31 -> 26.
B10 configs cut CHECK worst-5 by 10-12% but add 1-6 days <= -10R and cost -0.02 to -0.05 R/day (stress up to -0.21).
Trigger A is negative in every row. No config passes bars 1-2 on both splits in BASE either.

## Per-setup / book effect (remedy rule; sleeve P&L allocated by each setup's share of the exposure at the trigger)
Every effect is small: within +/-1.2 R/month per setup in every config.
- **A:** 0-1 setups better and 3-4 worse in every config and split (RW3 is worst hit, up to -0.56 R/month).
- **B6:** on CHECK, 3 setups better and 1 worse (RW3 -0.16 to -0.50 R/month; L3 +0.14 to +0.61, RW5 +0.31 to +1.20).
  On T2 it reverses: 1 better and 3 worse (up to -0.50 R/month).
- **B10:** 2 better and 2 worse in LO. In BASE CHECK, 1 better and 3 worse.
The sleeve does not fix any one setup's failure mode. Across the whole book it is a slightly positive or slightly
negative wash.

## Optimism / salvage (not tested, not counted)
- Trigger B finds the right days (81-92% of B10 hedge days are in Primary's worst 20%), and an index leg at this size is
  cheap (<= 20R/yr). The missing piece is size against single-stock squeezes. Two follow-ups are worth a prereg:
  (1) drop the VWAP-loss exit (hold to 15:55), since early exits cut the payoff on the days that matter;
  (2) size against the book's realised squeeze beta (open short R per 1% index move on the day) rather than daily beta.
  If a hedge on index ETFs only offsets about 0.5R per 1% of SPY, though, it cannot reach the idiosyncratic part. The
  stronger remedy direction is still exposure control (LATCH-OPEN, B8 block), not hedging.
- Not added to the backlog from a FAIL. The two ideas above are noted here for the next wave's synthesis.

## Rule changes inside the windows
The bench replays fixed Primary rules (P4 lineup, LIVE-L costs) over CHECK / T2 / FIT up to 2026-11-04. No ledger
effective date changes these figures. Any live Primary figures quoted for the same windows must list the ledger moves:
10-15 RW3/RW5 -> Primary, 10-20/10-22/10-30 L3 in/out/in, 10-28 sizing, 10-29 -2R latch, 11-11 NM-ETF in, 11-12 LR8,
11-17 TSZ1, 11-19 Epoch 1, 11-20 stop rounding, and 11-23 burst brake / PSHADOW.

Files: PREREG.md, ih_index.py (SPY/QQQ grids, VWAP, half days, QQQ beta, gap-down breadth), ih_e4.py (extended engine),
ih_run.py (sleeve, controls, scoring), results.csv (every config x context x period: metrics, controls, bars, per-setup
allocation), summary.json, idx_meta.csv, run_out.txt.

Educational only — not financial advice
