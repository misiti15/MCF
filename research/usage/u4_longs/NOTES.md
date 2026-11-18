Educational only — not financial advice

# U4 long-side program — working notes (2026-11-18)

- Order of work: PLAN.md written and pushed (commit 9f7b8e106) before the engine ran on any session. No spec, threshold,
  window or exit was changed after the first score; the only engine edits were before the first full run (one-day
  smoke test on 11-17 to check the code ran).
- Data: release packs bars-2026-10 / bars-2026-11 (31 live sessions, ~5,100 names; universe after the $5 / $20M ADV
  filter ~2,600 names a day) and bars2y-2024-09/10, 2025-05..2026-01 (223 sessions). Downloaded one session at a time,
  scored, deleted (code/engine.py). 2025-03/04 packs skipped because their 56-day daily priors reach into the locked
  block (store.check_dates rule); 1day rows inside the block are dropped and asserted absent.
- Journals: journal.db from the ten mcf-data* branches as of 2026-11-18 ~17:42 UTC, run_id 1, dates <= 11-17.
  R = pnl_adj / (|entry - stop| x shares), r_multiple where pnl_adj is missing (code/jload.py).
- Random controls: per trade, 5 random liquid names entered at the same bar ("same-time") and 5 random bars for the
  same name inside the spec window ("random bar"; U4-PMT uses 10:30-15:00 since its window is one bar). Same exits.
- U4-VWR fires on few days (19 of 31 live sessions; SPY-up gate) but many names per day, capped at 15.
- t is the day-clustered t of the per-trade mean (cluster = session).
- Files: u4_specs.csv (one row per config, every number in RESULTS), u4_daytype.csv (R by day type, per trade and per
  session), u4_days.csv (SPY day table), u4_trades.csv.gz (every simulated trade with its random-control values),
  u4_live_longs_all.csv (Part A, every live long setup), u4_live_longs_daytype.csv (Part A day types / correlation).
- Re-run: python -I code/engine.py <days...> then python -I code/analyze.py <out_dir> (paths point at the scratch dir;
  edit S in engine.py / jload.py).
- Scratch data (packs, per-day pickles, journal copies) deleted at the end.
