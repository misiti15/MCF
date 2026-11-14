# MOMSIDE-LIVE — frozen companion check on LIVE trades (Observer, 2026-11-14 ~09:50 ET, before any outcome is read)

Purpose: Builder's MOMSIDE (research/momside/PLAN.md) scores the 2-year LAB trades once. This is a secondary, descriptive
check on LIVE paper trades with the same tags, run ONLY AFTER Builder posts the lab result, so it cannot shape the lab
plan. It cannot pass anything on its own (28 sessions); it can only flag 'live disagrees with lab'.

Frozen definitions (no tuning after this commit):
- Trades: run_id 1, all 10 accounts, entries 2026-10-06..2026-11-13 (window fixed now; later sessions excluded).
- R = raw R (r_multiple = pnl / risk), the basis that is identical on both sides of LR8 (OBS-LR8). Costs reported
  separately with LR8 recompute; gross first.
- 12-1 momentum per name and trade date: close(prior session - 21 trading days) / close(prior session - 252) - 1, from
  Alpaca daily SIP split-adjusted bars fetched after 16:00; names with < 253 prior sessions = untagged.
- Deciles: across the lab universe (research/lab_symbols.txt) on each trade date. Aligned = long in deciles 8-10 or
  short in deciles 1-3; counter = long in 1-3 or short in 8-10; else neutral.
- Score: within each setup-day, aligned trades' mean raw R minus the mean of a random same-count draw from that
  setup-day's non-aligned trades (1,000 draws); pooled over setup-days with >= 1 aligned and >= 1 other trade.
  Day-clustered t, best-day share, per-setup better/worse (setups with >= 5 eligible setup-days).
- Ex-market: subtract side x (SPY return over the hold) x the setup's live beta (OLS of R on side x SPY-hold return,
  per setup, from the same window); reported beside raw.
- Survivorship: none in live (names traded live existed then); report the share of live-traded names missing from the
  lab universe (lab survivorship proxy).
Reading rule (fixed): 'agrees with lab' if the sign of the live aligned-minus-random excess matches the lab's and |t| >= 1;
'disagrees' if opposite sign with |t| >= 1; else 'uninformative'. No pass/fail; no setup/config changes.
Family: 0 new configs (same tags as MOMSIDE; a check, not a candidate). Educational only — not financial advice.
