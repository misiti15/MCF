Educational only — not financial advice.

# st7_fix — pre-registration (written 2026-11-19, before any scoring)

Item: root-cause remedy R2 (owner code ST7, decision pending). Research copies only; no live code path touched.

## Configurations (counted: 4)
- **A-SR** (session-reset RSI): RSI(14) and RSI(5) use only changes inside the current session (the prior-close -> first-bar
  change and every prior-session change are dropped; partial window = all intraday changes available until the full n
  are there, so RSI14 is identical to today's from the 10:45 bar on and RSI5 from 10:00). Derived columns recomputed:
  rsiSlope (rsi - rsi 3 bars back), bear_div/bull_div (rolling-20 RSI max/min), rsiHeat, heat (components + bonus).
- **A-GA** (gap-adjusted RSI): continuous RSI as today (prior-session bars stay in the window) but the session's first
  change (prior close -> first 5-min close) is replaced by the first bar's own move (close - open). Same derived columns.
- **B-WIN**: ST7-rsi50dn-long-pm-t1s1-FD with the source window 13:35-15:00 restored (= source rule ST7-rsi50dn-long-pm-t1s1).
- **C-SKIP**: ST7-FD skipping only its 10:45 bar (re-chained: a later same-day bar may fire).
(A-SR is the primary (a) form; A-GA is reported as the alternative. Nothing else will be tuned after seeing results.)

## Data / rules
- 2-year lab frames (research/history2y, open months only; locked block 2024-11-01..2025-02-28 never read: 1-min bars
  are filtered to open dates on load, before anything is computed). RSI rebuilt from data/cache_hist 1-min bars with the
  frame pipeline (resample 5min, mcf.research.heat._rsi_simple semantics). Sanity: rebuilt "as-is" RSI must match the frame
  `rsi` column.
- Family for (a): every enabled `type: lab` setup in config/*.yaml (as family.py in rootcause_1119), first fire per
  symbol-day, production costs (gates.lab_trades, tod costs = LR8). Affected = trade list changes.
- Report per affected setup: n, total R and avg R base vs variant, delta R; counts better/worse and sizes; halves
  (< 2026-03-10 / >= 2026-03-10); avg R w/o best day + best-day share for ST7-FD under each config.
- Live: paper trades (run 1, all accounts, live_all.pkl from rootcause_1119) of affected setups, matched to lab fires
  (setup, symbol, date, signal bar) where bars exist (cache ends 2026-11-04): a live trade whose signal no longer fires
  under the variant is "removed" (its live R is the delta). Live trades after 11-04 (incl. the 11-19 burst) cannot be
  re-evaluated from bars; reported as such, with the lab rate of 10:45 fires that survive the fix.
- Pass bar for proposing (a) as shared-code change: net family delta >= 0 in both halves, >= 60% of affected setups not
  worse, no setup worse by more than 10R in the lab or 3R live. For ST7-FD configs: avg R > 0 in both halves and
  avg R w/o best day > 0.
