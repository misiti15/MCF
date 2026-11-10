# MFFRESHLOW — skip an MF flow-sell short at a fresh low (Builder, frozen 2026-11-10 ~03:00 ET, before any score)

*Educational only — not financial advice.* The rule, configs, controls and pass bar are Observer's backlog entry
(research/obs-extension/BACKLOG_ENTRY_mf_freshlow.md) unchanged; Lead lead-20261110-0100-2 narrowed the pool.

- **Pool (Lead):** MF2 and MF4 only, i.e. the 2-year lab lists of MF2-open-rsimidhi-flowsell-FD, MF4-h40-open-flowsell-FD
  and MF4-h40-open-flowsell (MF1/MF3/MF5 reported for information only, not scored; RW dropped).
- **Rule:** skip when, from 1-min bars that START before the entry bar close (lab `tod`), the session low was set within
  the last 15 minutes AND (entry price - session low) <= X x ATR10 (prior 10 sessions' mean true range, >= 5 required,
  first row after the locked-block gap set to NaN). Entry price = the lab entry (signal bar close). **X 0.10 / 0.20.**
- **N 4** (Observer's 2 live looks + 2) -> BAR90 1.67 (Observer's count; Lead may impose a wider one).
- **Scoring:** GROSS first (lab cost inverted as compassbf/retag.py); excess vs a same-variant same-day random skip block of
  equal size (200 draws), day-clustered t; TRAIN / VALID; w/o best day; SPY up/down/quiet; per variant n, skipped n,
  skipped / kept avg gross, excess, retention (>= 80% trades, >= 90% top-decile winners per variant).
