# PROJECT PYRAMID — common brief (owner 2026-11-24 "national project")
Educational only — not financial advice. Research only: never change config, setups, accounts, orders or the ledger.

Owner goal: build the "ultimate 5" setups that beat every current setup on numbers, efficiency and operation —
about 3 LONGS + 2 SHORTS — so MCF stops depending on shorting the same gap-down names in the same conditions.
Owner: "use all forms of usage necessary." Owner research mindset: optimistic search, honest reporting.

## Read first (do not repeat failed work)
- research/ultimate_1119/RESULTS.md, ROUNDS.md, PLAN.md, BENCHMARK (benchmark/BENCHMARK.md): 35 candidates over 4 rounds,
  NONE passed on the check half after costs. Cite which families failed and do NOT re-test them unless you have a
  genuinely new mechanism or a new data angle; say so explicitly.
- docs/RESEARCH_RULES.md (costs always in, locked block 2024-11-01..2025-02-28 NEVER read, configs counted, report every
  finalist and failures first, vs random entries, avg R w/o best day + best-day share, one-big-day check).
- CLAUDE.md "Stop doing"/guarded categories, Remedies rule; docs/BDI_CHARTER.md (Move Hunt, capture rate).
- research/owner_inbox/2026-11-24.md (today: rotation day; we missed 21 of 25 long movers = 09:35-09:40 rotation bid into
  health care / utilities / REITs; Testing A's NM-AR-AM-gapdown-capitulation-long +10.76R).
- research/observer_1123/profitable_setups_1123.csv (7 clearly profitable live setups, mostly gap-down shorts).

## What is DIFFERENT this time (use it)
1. LIVE evidence first: ~31k live trades across 10 accounts since 10-06 (mcf.report.footrace.live_trades(); journals on
   data branches mcf-data, mcf-data-testing, -testing2, -explore1, -livelab, -testingd, -testinge, -testingf, -gen,
   -graveyard; trades table run_id=1). Setups that already pass LIVE (or near) are seeds, not just backtest ideas.
2. TEAM value: a setup earns its place partly by winning on the day types where the current book (≈80% short, gap-down)
   loses: up days, squeeze/rotation days (11-10, 11-11, 11-24), quiet days. Report each candidate's correlation of daily R
   with the current Primary book and its R on the book's 10 worst days.
3. Both halves: report 2023-24 vs 2025-26 separately (long mean-reversion worked 2025-26, failed 2023-24; see
   research/ultimate_1119/round5/round6 if present). A regime gate is allowed only if pre-registered and simple.

## Hard rules for every team
- Pre-register in your report BEFORE scoring: candidates, exact rules, grid, total configs (max ~12 per team), fit/check
  split (use the repo's standard bench10 FIT/T2/CHECK or ultimate_1119 fit/check halves), selection rule.
- Entries >= 09:50 ET, flat by 15:55. Shorts only in easy-to-borrow names. LR8 costs (mcf.costs). Reuse existing pipelines:
  research/ultimate_1119/benchmark/bench10.py, live10.py, bench_var.py; research/bdi/... scripts. Data under
  /home/user/MCF/data (cache, cache_hist, cache_fresh) — read only.
- WORKSPACE: disk is ~0.7 GB free. Do NOT create git worktrees. Read code from
  /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox (read-only: never checkout/commit/modify
  there; run python with cwd there or PYTHONPATH). Write ONLY in your own dir
  /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/<team>/ and keep it under ~60 MB
  (delete journal copies / big intermediates at the end; keep scripts + small csv). Alpaca reads GET only; never write secrets.
- Return your full report as your final text (report files may be blocked for subagents). No owner messages.

## Required finalist card (every finalist, pass or fail)
name / side / exact rule; configs tried; trades, sessions, trades/session; avg R after costs (fit, check, live if any);
win% vs break-even win%; day-clustered t; avg R w/o best day + best-day share; 2023-24 vs 2025-26; vs random-entry
control; R on the current book's 10 worst days and correlation with the book; median hold minutes; verdict TIER A
(deploy-worthy to Testing), TIER B (promising, forward-test), or FAIL. Be honest; no inflation.
