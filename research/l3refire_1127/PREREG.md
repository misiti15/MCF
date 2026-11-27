Educational only — not financial advice.

# L3REFIRE-1127 pre-registration (written 2026-11-27 ~22:20 UTC, before any configuration below was simulated or scored)

Source: consultant check-in 2026-11-27 (research/owner_inbox/2026-11-27.md, "## Consultant", one action) and backlog
`nightly-1015-l3-fromopen-refire-cap`. Question: does an **L3-only** limit on repeat lots in the same name improve
Primary's book? L3 = `L3-gap-slope-fromopen-FD` (Gap-Down Recovery Fade). Research only: no config, setup, exit,
assignment, decisions.json, backlog or ledger change.

## Prior results flagged first (RESEARCH_RULES 26, STOP2 item 1)
- Per-symbol stacking caps in Primary are on the STOP2 list: W7-NOCAP (research/crunch/w7_primaryday/RESULTS.md)
  STACK1 (one open Primary lot per symbol, all setups) cost L3 −15.0R on the current five (book −10.1R, t −0.60);
  SYM1 (no entry after a loss in the symbol, all setups) +1.0R for L3, ~0 for the book. sat1024 G1 (one lot per symbol,
  Primary-wide, 2-year) failed like every book-level gate: gains were up-session thinning, losses in down sessions
  (research/bdi/saturday1024/NOTES.md). This study is run because the owner's consultant asked for it with new
  evidence (131 live L3 repeat lots at −0.113R vs first lots −0.035R; 11-23 PLMR/UNH, 11-24 PTLO, 11-27 PANW).
  It is L3-only and within-setup, not a cross-setup cap.

## Configurations (N = 7; reference = keep = today's Primary rules, ≤ 3 open lots per symbol per setup)
All rules act on L3 candidates only; every other setup is untouched. "Prior L3 entry" = an L3 lot actually taken
in the simulated book that day (not a raw signal). A blocked candidate never opens, so it never blocks later ones.
| id | rule (L3 only, per symbol, per session) |
|---|---|
| OPEN1 | max 1 open L3 lot per name (variant 1) |
| OPEN2 | max 2 open L3 lots per name (variant 2) |
| GAP30 | no L3 entry within 30 min of the prior L3 entry in that name (variant 3) |
| GAP60 | same, 60 min (variant 3) |
| GAP120 | same, 120 min (variant 3) |
| NOSTOP | no L3 entry in a name after an L3 lot in that name exited at its stop today (variant 4) |
| FIRST1 | one L3 entry per name per day (the consultant's first-lot vs repeat-lot split; = GAP infinity) |
Counted: **7**. Cumulative N ≈ 9,176 + tonight's wave-4 configs so far (DAYTYPE 24, GAPNEWS 18, PAIRS 28 = 70) ≈
9,246 → **≈ 9,253**. Lineage bar sqrt(2 ln 9,253) ≈ 4.27 (reported). Per-study multiplicity-aware bar (7 configs × 2
contexts, Bonferroni one-sided 0.05/14 → z ≈ 2.9): **paired day t ≥ 3.0 on CHECK and ≥ 2.0 on T2**.

## Engine, lots, costs, contexts
- Engine E4 = research/cfprimary_1127/e4nb.py (numba port of the squeeze_1125 minute book; Primary rules: 77 slots,
  30 per setup, ≤ 3 per symbol per setup, burst brake 30 / 10 min, −2R realised latch, LATCH-OPEN option, −20R
  closed+open halt). The L3 rules are added in a copy `e4l3.py` (only the entry check changes; rule = off must
  reproduce e4nb exactly on all sessions, |diff| < 1e-9 R/day, asserted before any score). Exit kind (stop / target /
  market) comes from bench10 `kind`.
- Lots: bench10 P4 lots (L3, RW3, RW5, NM-ETF), hedgeb_1126/build.py unchanged: **LIVE-L costs on shorts**, LR8
  research cost on NM-ETF. Expected 52,544 candidates (as cfprimary / rwout); a different count is reported.
- Contexts: **BASE** (realised −2R latch, live today) and **LO** (LATCH-OPEN card). Freed caps refill as live would.
- Splits: FIT 2024-10 + 2025-03..09 (confirmation only); **CHECK** 2025-10-01..2026-11-04; **T2** 2023-01-03..
  2024-09-13. **Locked block 2024-11-01..2025-02-28 filtered at load and asserted absent in every script.**

## Controls
- **Size-matched random skip** (500 draws per config × context, seed 1127): per period, n = L3 lots taken in keep but
  not in the config; each draw removes n L3 lots uniformly from keep's taken L3 lots and re-simulates (refill on).
  Reported: random mean / 95th percentile of dR/day, the config's percentile, selection value = dR − random mean,
  and L3 lots taken under the config vs the random draws (exposure check, the RWOUT lesson).
- Constant cut (descriptive): L3 lots scaled by the config's L3 lot ratio vs keep, per period.
- **L3-OUT interaction:** L3 removed from the book (rwout); report how much of L3-OUT's dR the config captures.

## Live replay (descriptive, labelled Live replay)
Primary journal `origin/mcf-data:journal.db` (run 1, copied to scratch, deleted after), all Primary lots on the
sessions L3 traded in Primary (10-21..11-27), R after costs LR8 (`mcf.costs.cost_r_lr8`). Engine: primshorts_1126
booksim rules re-applied (current rules on every day: −2R latch, −20R halt; LO on/off), plus the config rule applied
in time order. The replay only drops lots (skipped signals cannot refill). Open marks from 1-min SIP bars (stored
primshorts grid, plus Alpaca GET for missing days; missing marks = 0, disclosed). Reported per config: dR/session,
paired t, L3 lots removed, removed lots' R, per-setup dR, 500 size-matched random L3 skips (percentile).
Also reproduced: the consultant's first-lot / repeat-lot split.

## Metrics (per config × context × period)
dR/day vs keep, paired day-clustered t, random p95 / percentile / selection value; L3 lots and all lots per session;
L3 lots lost (signals lost); per-setup dR per month (L3, RW3, RW5, NM-ETF); avg R w/o best day and best-day share of
the improvement; L3's avg R/lot keep vs config (and w/o best day); worst-5 days, red days per month.

## Pass bar (each on CHECK and on T2, in BASE and in LO)
1. dR/day > 0. 2. paired t ≥ 3.0 (CHECK) / ≥ 2.0 (T2) **and** dR above the random-skip 95th percentile.
3. Best-day share of the improvement < 25%. 4. No other Primary setup worse than −2R per month vs keep.
5. Worst-5 no more than 5% worse than keep.
PASS = ≥ 1 config meets 1-5 everywhere and its live replay (BASE) is not dR < 0 with t ≤ −2 (else INCONCLUSIVE).
LEAD = meets 1, 3, 4, 5 everywhere and bar 2 on at least CHECK or T2 in both contexts. FAIL otherwise.
Rule-30 checks reported for any passer (L3 keeps ≥ 70% of lots, ≥ 90% of top-decile winners, plateau among
GAP30/60/120 or OPEN1/2). If a config passes: decision-card proposal text in REPORT.md for the 12-04 epoch
(owner decides; decisions.json not edited). Every config is reported.
