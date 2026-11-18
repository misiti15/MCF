# L3 bespoke review 2026-11-17: notes

*Educational only — not financial advice.* Built 18:10-18:45 ET on 11-17, after the close. Research files only.

## Method details
- **Engine** (`code/sim4.py`): the Workbench L3 engine (research/workbench/L3-gap-slope-fromopen-FD/code/sim.py and
  sim2.py) with optional exit, filter and book layers, all off for the parent. With the old book it reproduces the
  Workbench parent to the trade: replay 10-12..11-12 gives 350 trades / +0.0587R, and the 2-year gives 4,885 /
  −0.0476R (`code/chk.py`).
- **Latch semantics changed on purpose.** The Workbench `sim.book` blocked entries only while the *current* realized R
  was ≤ −2. That is the pre-10-23 re-arming rule. Here the latch uses the day's running low of realized R after costs,
  in exit order, so once it trips the setup is stopped for the day, as the runner does since LL-LATCH (10-23). The
  parent baseline therefore differs from the Workbench files: replay 10-12..11-17 is 354 / +0.136R (to 11-12: 301 /
  +0.091R), and the 2-year is 4,242 / −0.052R. Every config in this folder uses the same book, so the comparisons hold.
- **Replay extension.** The 11-13..11-17 symbol-days are the Primary journal's L3 signals not rejected as
  not-shortable/ETB (11-13: none; 11-16: 19; 11-17: 4). They were fetched read-only from SIP with the same
  `lab_frame`/`apply_daily` pipeline (`code/fetch_ext.py`). SPY 1-min was extended to 11-17 the same way.
- **Live latch replay** (`code/live.py`) reuses research/latch_review_1117/analysis.py: its loader, the 3-lot cap on
  what-ifs, and the what-if cost haircut (the setup's measured live gap). Only this setup's own latch is replayed (no
  account halt; Primary's −20R halt never bound L3 alone), on R after costs for every day (LR3 basis; before 11-12
  Primary's real latch counted raw R). Exit → journal lag 2 min, as in the latch review. Above −2 in Primary from 10-29
  and in On Deck on 10-20..10-22, the post-latch trades are **simulated what-ifs** (42 after the cap). Below −2 they
  are real fills dropped.
- **SPY day states.** `spy10` = SPY's 09:59 bar close vs its 09:30 open (known at 10:00). Rules that use it apply −2
  to entries before 10:00. `dtype_oc` (open → close ±0.25%) is for reporting only.
- **Test C thresholds** came from the TRAIN parent signal distribution (C_quantiles.json): fromOpen p80 9.75,
  vwapDistPct p80 4.00, volumeRatio p80 1.235, rsi5 p20 38.8.
- **Top-decile guard**: the parent's 2-year trades with R ≥ their 90th percentile. A variant keeps one when it takes
  the same (symbol, date, entry minute). The R captured on those trades is reported too (C_workbench.csv
  `top_decile_R_captured`).
- **Random entries**: each taken trade's entry is moved to a random 5-min bar close between 09:50 and 15:00 on the same
  symbol-day (5 seeds), with the same exit rules and costs and no book. A random short on a gap-down name is a
  headwind trade, because these names tend to drift up. The baseline is negative for that reason, and the gap to it
  is the timing value.

## Deviations from PLAN.md
- The Workbench RULES.md "meet-or-exceed" check is reported as a column (`workbench_rules_meets` in C_verdicts.csv).
  Under that looser rule, C01, C02, C03, C06, C07, C08, C15, C16, C19, C20 and C21 "meet" the parent. None is a clear
  overall improvement under the supervisor standard (MECHANIC.md), and none passes the pre-registered validation, so
  none is sent to a testing account from this run. If the owner prefers the meets rule, C02 (target 1.5R) and C07
  (breakeven at +0.75R) are the two that fit the loss:gain ask.
- The plateau table compares total R without the best day (one-big-day rule). The best day differs by level (e.g.
  11-12 vs 11-16 in the replay), and the table notes it where it matters.

## Caveats
- The 2-year test loses after costs for the parent (−0.052R). A config that trades less can look better there almost
  automatically, which is why tighter latches lean positive over 2 years. The live and replay columns are the counter
  check.
- The live sample is small: 23 sessions with trades, 12 in Primary. Two days (10-20 On Deck, 11-12 Primary) are a large
  share of live R.
- Engine vs live on 11-12: the replay latched at −2 early in the day, while live did not (+31R). Live fills, slippage
  and the exact stop fills differ. The engine is a comparison tool, not a forecast.
