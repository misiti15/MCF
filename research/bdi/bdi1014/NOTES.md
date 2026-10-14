# BDI 2026-10-14: every-trade analysis and CWT14 stop-and-reverse (new setup plus a rework). Both FAILED

*Educational only - not financial advice.*

- Section 1 is one live **paper** session (rule 7), so it is a diagnosis, not evidence.
- Sections 3 and 4 are backtests on the open two-year history (2024-10..2026-10-07 minus the locked block), with
  production costs in.
- The rule-19 locked block (2024-11-01..2025-02-28) was never loaded, and no holdout was scored.
- `PLAN.md` was written before any history configuration was scored. Part B2 was appended after Part B's results
  and before B2 was scored, as the plan states.
- The top-5 small-variation tuning was **not** done here; the 18:07 ET run owns it.

**Configurations scored tonight: 480** (Part B 240, Part B2 240). **Passes: 0.** The Testing bar was met 0 times and
the research bar 0 times. 0 of the 240 SAR legs has positive expectancy.

## vs yesterday (2026-10-13)

| | 10-13 | 10-14 | why |
|---|---|---|---|
| Primary (paper, journal) | -$95.39 | **+$63.53** (11 trades, 10 shorts) | Down tape: QQQ -1.24%, peak at 09:49. Primary is almost all shorts |
| Testing 1 | -$629.03 | **+$71.27** (broker +$65.21) | Shorts +$590, longs -$518. The split tape of 10-13 reversed |
| Testing 2 | -$103.27 | **-$785.74** (broker -$1,160.46, gap unexplained, nightly H-2) | CWT14 PDL/ORL longs against a falling index. The -60R halt came at 10:30 |
| BDI output | 1,327 configs, 0 Primary, 1 Testing-bar finalist (G7 split-tape gate, now live in T1) | 480 configs, 0 pass | Tonight's idea came from today's biggest what-if (+57R from SAR on T2) and history refuted it |

- Better on Primary and T1, and the reason is the direction of the day, not a change in the system.
- Worse on T2, whose whole book is negative-expectancy CWT (history -0.09R).
- Worse for BDI: nothing passed. Next: a parent setup other than CWT14 (see Queued).

## 1. Every trade (681: Primary 11, T1 317, T2 353). Rule values, path, what-ifs, opposite side, loss type
`analyse_1014.py` re-uses the nightly's `trades.csv` and its 1-minute bars. Per-trade output is in
`trades_analysis_1014.csv`, and the per-setup what-ifs are in `per_setup_1014.csv`.

**How the what-ifs were scored.** Each what-if is the mean R per trade, on the 1-minute path from entry to 15:55,
stop-first, costs in. "base" is the re-simulation of the trade's own bracket. It matches the journal with a
correlation of 0.999 for Primary, 0.964 for T1 and 0.955 for T2. It runs about 0.03-0.12R below the journal because
costs are charged.

| acct | journal R | base | BE@0.5R | trail 0.5R | t 0.5R | t 1R | hold 15:55 | **SAR** | re-entry | opposite 1R/1R |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | +0.293 | +0.234 | +0.234 | +0.234 | -0.058 | +0.260 | -0.166 | +0.076 | +0.382 | -0.480 |
| T1 | +0.025 | -0.008 | -0.055 | -0.078 | -0.113 | -0.049 | -0.124 | -0.003 | -0.008 | -0.102 |
| T2 | -0.322 | -0.440 | -0.426 | -0.416 | -0.334 | -0.404 | -0.533 | **-0.278** | -0.488 | +0.020 |

**Exits**
- No management overlay helps T1 today: breakeven and trail both cut its winners.
- Primary's winners kept almost all of their MFE (median MFE 0.73R to exit, 1.55R to 15:55).
- T1 trades took a median 32 minutes to reach their best price. T2 took 8 minutes, then reversed (median MAE to
  15:55 is 1.87R).

**Stop-and-reverse**
- On T2, SAR adds +0.318R per stop (180 stops, +57R).
- On T1 it adds +0.016R (101 stops). On Primary it adds -0.58R (3 stops; two of them were stopped and then reversed
  back to the target).
- Section 3 tests this on history.

**Re-entry** after a stop, same side, within 60 minutes:
- T2: -0.56R per re-entry (30).
- T1: 0.00R (15).
- Primary: +0.82R (2).
- Nothing is learned for Primary from 2 trades.

**Refire** (T1 only): 8 trades, base +1.15R against -0.04R for the rest. One session, and UVXY carries it.

**Opposite side, with a hindsight check.**
- The opposite trade would have won on T2's longs (+0.06R) and T1's longs (+0.34R). It would have lost on every
  short book.
- The **pointer** is the only rule known at entry that I tested: QQQ fromOpen >= 0.25% against the trade, with the
  stock on the far side of its VWAP.
  - On all 681 trades, the opposite R is -0.062 when the pointer is set (103 trades) and -0.042 when it is not (578).
  - The pointer helps T1 (+0.237 against -0.149) and hurts T2 (-0.221 against +0.073).
- No rule known at entry pointed to the opposite side consistently, so the "opposite side worked" reading is
  hindsight from the day's direction.

**Loss types** (341 losers, merged into `patterns.csv`; the merge can be re-run without duplicates):

| account | never_worked | small MFE then failed | gave_back | late_hold | stopped_then_reversed | wrong_side_big_swing |
|---|---|---|---|---|---|---|
| Primary (4) | 1 | 0 | 0 | 1 | 2 | 0 |
| T1 (152) | 36 | 29 | 21 | 26 | 10 | 30 |
| T2 (185) | 53 | 61 | 33 | 0 | 28 | 10 |

## 2. Recurring patterns turned into rules (patterns.csv: 54 setup x loss-type pairs now on 3+ days)

| pattern (days) | testable rule (information known at entry or stop) | status |
|---|---|---|
| CWT14 never_worked / small-MFE / stopped_then_reversed (3 of 3 T2 sessions, all 11 variants) | reverse at the stop (SAR) | **tested tonight, failed** (sections 3-4) |
| RW7-FD late_hold, gave_back (3) | exit or move to breakeven at 15:00-15:30 | already queued (`nightly-1014-fd-short-late-giveback`). The book-wide versions failed (`sw-w4-book-exits` 22, `cutoff-1515` 76), so a per-setup rework comes next |
| RW2-FD never_worked (4) | deeper extension floor: fromOpen >= 2.5% or RSI5 >= 90 | **new idea** `bdi1014-rw2-extension-floor` (today: winners +3.2% / RSI5 94, losers +1.4% / 80, 9 trades) |
| ST2-FD wrong_side_after_big_swing, late_hold (3) | skip when the stock is <= -3% from the open | **new idea** `bdi1014-st2-wrong-side` (today's data does not separate winners from losers, so it is queued on recurrence only) |
| heat_fade, exhaustion, MF1/MF2/MF5 pairs | - | already in the backlog or under review (bdi1013) |

## 3. NEW setup: CWT14 stop-and-reverse ("failed fail-break continuation"). FAILED, 0 of 240
`sar1014.py`.

**Data and method**
- 512,798 CWT14 first signals (live semantics), 31.7% of them stopped.
- The base re-simulation matches the nightly scan: correlation 0.998, -0.092 against -0.090R.
- Leg = the opposite side after the base stop, R = 0.25 x ATR.
  - E1 is a resting stop-entry at the stop price.
  - E2 is a market order at the stop bar's close.
- Geometries: t05s1, t1s1, t2s1, t1s05, eod-s1.
- Books: 11 setups plus a pooled book.

**Failures first**
- **0 of 120 legs has exp > 0.**
- Best leg: pdl-p10-lowvol E2 t05s1, -0.054R (n 6,515, t -4.30).
- Pooled: E2 t05s1 -0.074R (n 79,748), E1 t05s1 -0.165R (n 80,702).
- **E2 legs equal the same-time random control.** Excess is -0.04 to +0.024R with |t| < 2.1 in every book. Once the
  level fails, the continuation has no edge of its own.
- **E1 is 0.07-0.18R worse than the control.** The stop-entry pays stop slippage and fills on the bar that already
  ran.
- **The regime decides the sign.** Short legs lose in up sessions (-0.18 to -0.49R) and are about 0 in down
  sessions. Long legs win in up sessions and lose in down sessions (eod: +0.15 / -0.42).
- Today's +57R was the down session. Day-clustered WF share is 0.00-0.29, against a bar of 0.6.
- **Managed trade (base + SAR):** worse than the base alone in every one of the 12 books.
- Bars:
  - Testing bar (t >= 2.0 plus gates): 0 met.
  - Research bar (lineage N 120,849, t >= 4.84): 0 met.
  - The study-only bar would be 3.31.

## 4. Rework (rule 18): index-aligned SAR. FAILED, 0 of 240
`sar_ix1014.py`. The leg is taken only when SPY's fromOpen at the stop bar is on the leg's side by more than k,
with k in {0, 0.25%}. Entry is E2, with 5 geometries and 12 books.

- **0 of 120 legs has exp > 0.**
- Best leg: pdh-p10-lowvol-short t2s1 k0, -0.040R (n 3,687, t -1.25).
- Pooled: k0 t05s1 -0.070R (n 48,339); k0.25 t05s1 -0.071R.
- The gate does not repair the regime split: short legs in up sessions are still -0.23 to -0.89R.
- Lineage N 121,089, bar 4.84; study-only bar 3.51.
- **Verdict:** the CWT14 SAR lineage is closed. Both versions are in the backlog as failed, with their numbers.

## Proposed changes for tomorrow
- **None.** Nothing met the Primary or the Testing bar, so there is no config diff.
- The G7 split-tape gate (bdi1013) is already live on Testing 1. It blocked 0 shorts today (nightly), which is
  correct on a large-cap-led down day.

## Backlog (`add_backlog.py`; `research/BACKLOG.md` regenerated, 391 entries)

| id | status | configs |
|---|---|---|
| `bdi1014-cwt14-sar` | failed | 240 |
| `bdi1014-cwt14-sar-ixalign` (parent: the above) | failed | 240 |
| `bdi1014-rw2-extension-floor` | idea | 0 |
| `bdi1014-st2-wrong-side` | idea | 0 |

## Queued for the next session
1. Per-setup late exit for the T1 FD shorts (`nightly-1014-fd-short-late-giveback`). It must beat `cutoff-1515` and
   `sw-w4-book-exits`.
2. The RW2 extension floor and the ST2 wrong-side filter, scored on history with their neighbourhoods.
3. Stop-and-reverse on a parent whose stops are **not** regime-driven, such as the Primary short book's
   stopped_then_reversed MF/NS trades. Only after a check that the parent has at least 60 stops on history.
4. Disk: the scratch trade file (25 MB) is deleted. The nightly's `bt_hits.parquet` is the nightly's to keep or
   delete.

## Files
- `PLAN.md`: the pre-declaration.
- `analyse_1014.py` writes `trades_analysis_1014.csv` and `per_setup_1014.csv`, and merges the losers into
  `patterns.csv`.
- `sar1014.py` writes `sar_results.csv` and `sar_summary.json`.
- `sar_ix1014.py` writes `sar_ix_results.csv` and `sar_ix_summary.json`.
- `add_backlog.py`: the backlog entries.
