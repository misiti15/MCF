# GAPSWITCH pre-registration: SPY gap-up day switch for the post-11-30 Primary roster

Educational only — not financial advice.

Written 2026-11-28 ~01:20 ET, **before any bench score of these configs was computed**. Committed and pushed before scoring.

## Why
- Live (in-sample, few days): Primary shorts lose on SPY gap-up days (shorts_autopsy finding 3: the current trio lost −44.9R on 6 gap ≥ +0.5% sessions; loss_anatomy: "no shorts on SPY gap-up > 0.3%" +85.1R in-sample, but 0th percentile in the arena). The running GAP-U regime shadow shows +42.7R over 11 live sessions.
- Prior bench result already known (stated so it is not re-discovered): shorts_autopsy R1 (skip the gap-down *family* on SPY gap ≥ +0.5%, candidate level, no book) FAILED the matched-random control (26th / 12th percentile on CHECK / T2). This test differs in three ways: (1) the exact likely Monday roster only, (2) scored as a **Primary book** (cap, per-setup −2R latch, −20R halt), (3) a second threshold (+0.25%) and a half-size variant. The prior failure is the base rate; expectation is optimistic but sober.

## Engine and data (no new data built)
- Candidate lots: `scratchpad/rsw/cand.parquet` from research/regsteer_1126/rs_cand.py = bench10 candidate lots (research/ultimate_1119/top10/bench10.py, unchanged), entry ≥ $5, shorts ETB ≥ 0.9, **costs: LIVE-L (primshorts_1126 cells_live.json) on shorts, LR8 research on NM-ETF longs** (primshorts convention).
- SPY gap: `rsw/st/gap.parquet` (research/regsteer_1126/rs_states.py): first RTH 1-min open / prior session's last RTH close − 1. **Known at 09:30; no lookahead.** 2025-03-03 gap is NaN (prior day is in the locked block) — treated as "switch off".
- Book: research/primshorts_1126/booksim.py `sim_day` with Primary rules (setup cap 30, ≤ 3 lots per symbol, per-setup −2R latch on closed R, −20R halt on realised R; LATCH-OPEN off, open marks not modelled — same as the regsteer base book).
- Splits: FIT 2024-10 + 2025-03..09; CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13. **Locked block 2024-11-01..2025-02-28 never read** (asserted on every load).
- Known gap: NM-ETF bench lots use the old stop (AV50 / stop50 starts 11-30, ledger 2026-11-30-etf-stop50-av50); the switch never touches NM-ETF entries, only through book interaction.

## Rosters
- **A (L3 out):** RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, NM-ETF-late-dip-di-long.
- **B (L3 in):** A + L3-gap-slope-fromopen-FD.
- Baselines: each roster with no switch.

## Configs (5, counted; nothing else will be scored as a candidate)
| id | roster | rule (decided at 09:30 from SPY open gap) |
|---|---|---|
| A-G25 | A | no short entries all day when SPY gap ≥ +0.25% |
| A-G50 | A | no short entries all day when SPY gap ≥ +0.50% |
| B-G25 | B | same as A-G25, roster B |
| B-G50 | B | same as A-G50, roster B |
| A-H25 | A | short setups at **half size** all day when SPY gap ≥ +0.25% (the latch still counts each lot's full-size R, as primshorts' half-size option) |

## Reported per config and split (FIT, CHECK, T2)
R/day (book) before and after, gain/day, day-clustered t of the daily gain, red-day count before/after, worst-5 days before/after, avg R/day without the best day (book), best-day share of the gain, per-setup better/worse counts and R, days the switch fires, and a **size-matched random day-skip control**: 1,000 draws of the same number of random sessions from the same split, same action applied; p = (draws with gain ≥ observed + 1) / 1,001.

## Pass bar (fixed now)
**Proposal-worthy** only if on **both CHECK and T2**: gain/day > 0; day-clustered t ≥ 2.0; random-control p ≤ 0.05; best-day share of the gain < 50%; red days not increased; worst-5 not worse; short setups improved ≥ worsened. FIT must not be negative (descriptive otherwise). With 5 configs, p ≤ 0.01 on both splits is read as "strong", 0.01-0.05 as "passes, multiplicity-discounted".
**Forward shadow only** if it passes on one scored split, or p ≤ 0.20 on both with positive gain.
**Fail** otherwise; the live gap-up loss would then be read as a size effect / in-sample noise.

## Live readout (descriptive only, in-sample)
Primary lots of the roster setups from `rsw/live_states.parquet` (10-06..11-25, LR8 costs) split by the same gap thresholds; not part of the pass bar.

Educational only — not financial advice.
