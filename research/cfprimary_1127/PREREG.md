Educational only — not financial advice.

# CF-PRIMARY pre-registration (written 2026-11-27 ~04:20 UTC, before any CF configuration below was built or scored)

Source: inspector 1127 idea #1 (research/inspector_1127/ideas.json "CF-PRIMARY"). Research only: no config, ledger,
decisions.json or live change. The cost filter (CF) runs in the testing accounts since 2026-10-30 (ledger
2026-10-29-testing-cost-filter-cf: skip an entry whose stop-exit round trip costs > 0.15R; review was due 2026-11-12,
overdue). Owner 2026-10-29: "I do not want it affecting primary" - this study only measures what it would do there.

## Part A - score the overdue CF forward test (not a new config; not counted)
- Data: journals `git show origin/mcf-data-testing:journal.db` (Testing 1, renamed On Deck from 11-12) and
  `origin/mcf-data-testing2:journal.db` (Testing 2 / Testing A), copied to the scratchpad and deleted after.
  Rows: run-1 signals `status='skipped'` with reason starting `cost filter:`, days 2026-10-30..2026-11-25; their
  outcome = the run-2 what-if trade (`meta` = `status=skipped;why=cost filter:...`, the runner's own bar replay).
  C3-SCORE rule: first signal per (symbol, date, setup) only (repeat signals of one name dropped).
- Costs: what-if rows carry backtest costs (1 bp + $0.01 per side, +$0.02 on stops, targets at the limit). They are
  stripped back to a gross R on the raw signal price and re-costed with **LIVE-L** (primshorts_1126 cells_live.json,
  by price bucket and exit kind; eod/time = market). The as-recorded backtest-cost R is shown alongside.
- Measure: per-day sum of skipped-trade R (LIVE-L); the filter "saved" R if that sum is < 0. Day-clustered t.
  **Part A confirms CF** if the pooled skipped total is < 0 with day-clustered t <= -2.0 and the sign is the same in
  both accounts. Reported: per account, per setup (how many setups the skip helped / hurt and by how much), avg R
  w/o best day and best-day share, and the kept (taken) trades' live LR8 R per trade for context (different basis).
- Descriptive, no score: the same skip rows in the other accounts that carry the filter (explore1, livelab, testingd,
  testinge, testingf) if their journals are readable; and CF-15 applied to Primary's own live trades 10-23..11-25
  (which taken trades it would have skipped and their LR8 R; no re-simulation).

## Part B - CF on the Primary book (configs N = 2)
- **CF-15**: skip a candidate lot when the live runner's formula, cost_r = (2 x ($0.01 + 1 bp x entry) + $0.02) /
  risk_per_share, is > 0.15 (exactly mcf/execution/runner.py `_realism`).
- **CF-LL15**: skip a candidate lot when its LIVE-L predicted stop-exit cost, predict_R(cells_live, entry, risk,
  "stop"), is > 0.15R.
- Both are known at the signal (entry, stop). Counted: cumulative N ≈ 8,891 (regsteer_1126 addendum) + REGSTEER 7 +
  COMPASSIDX 2 + TAPE 7 + STOPX 3 ≈ 8,910 → **≈ 8,912**; family bar sqrt(2 ln 8,912) ≈ 4.27 shown descriptively; the
  pre-registered bar uses paired t >= 2.8 as written in ideas.json (global 3.93 / 4.27 shown alongside).
- Engine E4 (rule 31): the squeeze_1125 / hedgeb_1126 minute book engine (Primary rules: P4 lineup, >= $5, shorts ETB
  >= 0.9, 30 lots per setup, <= 3 per symbol per setup, 77 slots, burst brake 30 / 10 min, -2R latch, -20R closed+open
  halt), ported line by line to numba for speed; parity with the Python engine on REF is checked (|dR| < 0.01R/day per
  context) before any CF run. Lots = bench10 regenerated (squeeze_1125/gen.py + hedgeb_1126/build.py, unchanged),
  RAW book, LIVE-L costs on shorts, LR8 research on NM-ETF (as primshorts / hedgeb).
- Contexts: **BASE** (P4, realised -2R latch = live today), **LO** (P4 + LATCH-OPEN, pending), **LO+L3-OUT**.
  REF = the context without CF. The filter removes candidates before the engine, so freed slots / caps are refilled
  as live would.
- Controls (CHECK and T2 days): **500 random removals** per config x context, same number of candidates removed in
  each (setup, period) stratum as the CF removes, seed 1127; **constant cut** = every lot's R and open marks scaled by
  (1 - s), s = the CF's share of REF lots removed (per period), re-simulated (descriptive reference).
- Splits: FIT 2024-10 + 2025-03..09 (confirmation only, nothing tuned); CHECK 2025-10-01..2026-11-04; T2
  2023-01-03..2024-09-13. The locked block 2024-11-01..2025-02-28 is filtered at load and asserted absent in every
  script.

## Metrics (per context x config x period)
Avg R/day and dR/day vs REF, paired t (day-paired), random 95th percentile of dR/day and CF's percentile, red days per
month (x 21), worst-5 days (mean), days <= -10R, rolling 20-session floor, best-day share of the improvement (largest
single-day delta / total delta), avg dR/day without the best day, per-setup dR per month (21 sessions), lots taken.

## Pass bar (ideas.json, copied; every item on CHECK and on T2 separately)
1. dR/day > 0. 2. dR/day above the random-removal 95th percentile and paired t >= 2.8. 3. Red days per month down
by >= 0.5. 4. Worst-5 no more than 5% worse (cfg worst-5 mean >= 1.05 x REF's). 5. Best-day share < 25%.
6. Every Primary setup no worse than -2R per month vs REF.
A config **passes** if all six hold on CHECK and T2 in BASE and in LO; LO+L3-OUT is scored with the same bar and must
at least keep dR/day > 0 on both splits, else the verdict is INCONCLUSIVE (context-dependent). If Part A shows the
skipped Testing trades made money (pooled LIVE-L total > 0 with t >= +2.0), a Part B pass is reported as INCONCLUSIVE.
If a config passes: DECISION draft text in REPORT.md (owner decides; Primary shadow-first); decisions.json not edited.
Caveat fixed now: on a losing book, trading less "wins"; that is why the random-removal and constant-cut controls carry
the verdict, not dR alone.
Educational only — not financial advice.
