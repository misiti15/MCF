# giveback1019: pre-declared counterfactual replays (written before any replay was run)

Declared 2026-10-19 ~12:30 ET, after the descriptive steps 1-3 (`curves.py`, `diag.py`) and before `replay.py` was
written or run. Educational only - not financial advice.

## Sample (in-sample, live paper trades; hypothesis generation only)
Real trades (run 1) of every complete session: Primary 2026-10-06..10-16 (9 sessions, 313 trades), Testing 1
10-09..10-16 (6, 1,495), Testing 2 10-12..10-16 (5, 2,281). 2026-10-19 is mid-session and is excluded from replays
(described separately from the runner's intraday snapshots). No locked block or holdout is touched.

## Replay mechanics (same for every configuration)
- SIP 1-min bars from the bar after the entry minute. Entry = the actual live fill (already includes the real
  slippage). Stop-first inside a bar; a gap through a stop fills at the open; targets fill at the limit price;
  stop/breakeven/trail moves take effect on the next bar.
- Costs (config/default.yaml): market exits 1 bps + $0.01/sh; stop exits additionally $0.02/sh; targets no slippage.
  The actual baseline is the journal `pnl_adj` (actual fills less the $0.02/sh stop haircut).
- Deadline: the actual exit time when the live exit was a flatten (time/EOD/halt), else 15:55.
- **Delta method:** for per-trade exit rules, counterfactual P/L = `pnl_adj` + (sim_variant - sim_baseline) on the
  same simulator, so simulator error cancels where the rule never triggers. Simulator fidelity (exit-reason match,
  sum of sim_baseline vs pnl_adj) is reported.
- Account-level rules act on the marked curve (realized `pnl_adj` + open lots at the 1-min close less a market exit
  cost) evaluated each minute; a halt drops every later entry; a flatten exits all open lots at the next minute's open
  with market costs. Dropped trades cannot be replaced by other signals (lot caps and the T2 daily-loss halt are not
  re-simulated) - stated limitation.
- Account R unit U = median $ risk per trade over all sessions: P $19.81, T1 $9.50, T2 $6.79.

## Configurations (21 per account x 3 accounts = 63)
| # | id | rule |
|---|---|---|
| 1-3 | BE050 / BE075 / BE100 | stop to breakeven once MFE >= +0.5R / +0.75R / +1.0R |
| 4-5 | TR1-05 / TR1-10 | after MFE >= +1R, trail the stop at (best - 0.5R) / (best - 1.0R) |
| 6-7 | LKG30-H / LKG50-H | once the marked day P/L has reached >= 5U, halt new entries when it gives back 30% / 50% of its peak |
| 8-9 | LKG30-F / LKG50-F | as 6-7, and also flatten every open lot at that moment |
| 10-11 | LKZ5-H / LKZ10-H | halt new entries once the marked day P/L reaches >= 5U / 10U (daily profit target) |
| 12-14 | CUT1100 / CUT1200 / CUT1330 | no new entries at or after 11:00 / 12:00 / 13:30 ET |
| 15-16 | TS30 / TS60 | time stop: at 30 / 60 min after entry, exit at the bar close if the trade is not >= +0.3R |
| 17-18 | WIDE125 / WIDE150 | stop 1.25x / 1.5x farther, size / 1.25 / 1.5 (same $ risk), target price unchanged |
| 19 | SO05 | scale half out at +0.5R (limit), rest unchanged |
| 20 | SO05BE | scale half out at +0.5R, rest's stop to breakeven |
| 21 | NOISE4 | skip entries whose stop distance is < 4 x the 1-min ATR(14) before entry. **Post-hoc:** added after `diag.py` showed the tightest stop/ATR quartile was the worst in all three accounts; it is therefore partly fitted to this sample. |

## Statistics and bar
- Per account per config: trades taken, win rate, avg R (cf P/L / original $ risk), total $, change vs actual $,
  sessions better / worse / equal, and the **day-clustered t** of the daily $ change (mean / (sd / sqrt(days))),
  plus the change without the best day.
- Secondary: pooled over the 20 account-days (accounts share market days, so not independent - indicative only).
- **Bar:** N = 63 -> max(1.5, sqrt(2 ln 63)) = **2.88** (per-account family N = 21 would be 2.47). With 5-9 sessions
  per account, no result here can be more than a hypothesis; anything that clears the bar still needs the long-history
  check (step 5) and the backlog gates before it can be proposed.

## Step 5 (only if a rule looks good)
For the rule(s) that look best, check on the lab frames (`mcf/research`, open history only: train <= 2025-12 excluding
2024-11-01..2025-02-28, valid 2026-01+) for the setups that traded live in Primary, if it fits in ~2 hours of compute.
Each long-history configuration is counted and added to N.

## Step 5 addendum (declared after the live replays, before any long-history run)
Live replays showed no rule clearing the bar in Primary; the pooled view ranked NOISE4, WIDE125, WIDE150, CUT1100,
TS30, TS60 highest, and BE050 / SO05BE were Primary's best per-account rows. These **8** are re-checked on the long
history; N becomes 63 + 8 = **71**, bar **2.92**.
- Entries: every setup enabled in config/default.yaml (the 12 Primary lab setups; each traded live in Primary), mask on
  the history2y 5-min lab frames via `research/history2y/lib.load_month` (open months only - the locked block
  2024-11..2025-02 lives in a separate directory and is refused), window and min_adv from config, first qualifying
  bar per symbol-day (gates.lab_trades convention), side and geometry from the module, R = 0.25 x daily ATR.
- Exits: replayed on `data/cache_hist/1Min` SIP bars from the minute after the signal bar's close, with the same
  simulator and costs as the live replays (entry side 1c + 1 bps x the time-of-day multiplier of gates.TOD_COST),
  exits by 15:55. Baseline fidelity vs the frame's production R is reported.
- Splits: train 2024-10 + 2025-03..2025-12, valid 2026-01-01..2026-10-07, forward 10-08..10-16 reported only.
- Statistic: paired delta (variant - baseline) in original R per trade, summed per day; day-clustered t of the daily
  delta; months with a positive delta; delta in up and down sessions (lib.regimes).
- **Supports** (pre-declared): delta > 0 in train AND valid, valid day-clustered t >= 2.92, and delta > 0 in both up and
  down sessions. Anything else: "not supported". Supported rules still go to the backlog gates, not to live.
