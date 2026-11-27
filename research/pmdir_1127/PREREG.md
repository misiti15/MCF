# PMDIR-1127 — can SPY's afternoon direction be called at 12:00? (pre-registration, written before any scoring)

*Educational only — not financial advice.* Research only: no change to config/, setups, exits, assignments, decisions or the ledger.

## Question
Many live setups' results ride on SPY's 12:00-15:55 direction (ARENASTARS-1127: G05/G07/G37 are afternoon SPY bets).
Using only information available at 12:00, can a simple frozen model call the sign of SPY's 12:00 -> 15:55 move better
than chance out of sample, and does an actual SPY trade on it survive costs? Prior: COMPASS-5M / COMPASS-LEARN found
"heading" (where SPY goes next) a coin flip on every clock (48-53%); this asks the broader multi-feature question.

## Data
SIP 1-minute RTH bars for SPY, QQQ, IWM and the 11 SPDR sector ETFs (XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY;
XLC from 2018-06-19, a sector counts only on days it has bars). 2016-01-04..2022-09-30 from the wave-3 GET-only Alpaca
fetch (scratch, not in git); 2022-10-03..2024-09-13 `data/cache_fresh/1Min`; 2024-09-16..2026-11-04 `data/cache_hist/1Min`.
**Locked block 2024-11-01..2025-02-28 is dropped at load, before any feature is computed, and asserted absent.**
Prior-day / 20-day features that would need a day across the locked gap (or any gap > 5 calendar days) are NaN and the day
is excluded (early March 2025 in FIT only).

## Splits
FIT 2024-10 + 2025-03..2025-09 (fit only) · CHECK 2025-10-01..2026-11-04 · T2 2023-01..2024-09 · EARLY 2016-01..2022-12
(extra out-of-sample). Models are fit on FIT only, frozen, then scored once on CHECK, T2, EARLY.
FIT is small (~165 days); this is a deliberate choice by the task (fit on FIT only). As a pre-registered *secondary*
robustness view (not a pass route), the same model specs are also fit on EARLY and scored on T2 + CHECK (FIT unused).

## Decision clock and target
Decision at 12:00 ET using bars through the 11:59 bar's close. Target y = 1 if SPY's 15:55 bar open > SPY's 12:00 bar
open, else 0. Half days: exit at last bar - 4 min (LR1 rule); days with no 12:00 bar are dropped.

## Features (12:00-known only)
1. mret: SPY 11:59 close / 09:30 open - 1. 2. mrange: (SPY high - low 09:30-11:59) / open. 3. vwap: SPY 11:59 close vs
session VWAP (bp). 4. breadth: share of sector ETFs above their own open at 11:59, minus 0.5 (sector breadth, rebuilt from
bars, no look-ahead; the stock-universe breadth of ARENASTARS has no EARLY coverage, so the sector version is used on all
splits for consistency). 5. rvm: SPY morning realized vol (1-min log returns 09:31-11:59, annualized). 6. rv20: SPY prior
20-day close-to-close realized vol (VIX proxy). 7. qi: QQQ morning return - IWM morning return. 8. dow (Mon..Fri,
as 4 dummies in logistic; integer in trees). 9. prev: prior day close-to-close return. 10. gap: 09:30 open / prior close - 1.
11. lmom: SPY 11:00-11:59 return (last-hour momentum). 12. w60: W60-proxy compass state at 12:00 = votes {sign of SPY from
open, VWAP side, sector-breadth side, SPY/QQQ/IWM-from-open agreement} with persistence (SPY-from-open sign the same at
11:00/11:15/11:30/11:45/11:59 marks); +1/-1 when |votes| >= 3 of 4 and persistent, else 0. (Sector breadth replaces the
200-name Hunch breadth, which has no history; so this is a proxy, not the live W60.)

## Models (fit on FIT, frozen) — configurations counted
* M1 logistic, all features standardized (FIT mean/sd), L2 C=1.0.
* M2 logistic on mret only (afternoon momentum vs reversal).
* M3 decision tree depth 2, min_samples_leaf 25, all features.
* M4 decision stump depth 1, min_samples_leaf 25, all features.
* M5 W60-proxy rule (no fit): trade the sign of w60 when nonzero; no trade when 0.
* M6 always-long (drift control, no fit).
* M1c / M3c: M1 / M3 traded only when |p - 0.5| >= 0.05 (confident subset).
**8 configurations** (M1..M6, M1c, M3c). The secondary EARLY-fit view adds 4 (M1, M2, M3, M4) = **12 total**.
Cumulative program N ~9,176 -> ~9,188. Lineage claim bar (program-wide) t >= ~4.3 is noted; this study's own bar below.

## Trade (actual SPY trade, costs in)
Side = model sign. Enter at SPY's 12:00 bar open (market, next bar after the decision bar); stop 0.50% from entry (R =
0.50%), stop-first inside a bar, gap through -> bar open; exit at the 15:55 bar open. Costs: **LIVE-L** main
(primshorts_1126/cells_live.json, price bucket x exit kind: a / width_bp + b), **LR8** alongside (1c + 1bp per side, +2c on
stops, x tod multiplier, borrow 1.2bp on shorts). Note: LIVE-L at a 50 bp stop charges ~0.166R (~8 bp) per SPY trade, far
above SPY's real ~0.2 bp spread; it is kept as the main model per the research rules and LR8 is shown alongside.
Stress: entry +1 minute (12:01 open, stop re-anchored) and +2 bp extra cost per trade.
Controls: random direction on the same days (500 draws; the model must sit >= 95th pct on R), and M6 always-long.

## Pass bars (this study, 8 primary configs; sqrt(2 ln 8) = 2.04)
**PASS (trade)** requires all: mean R after LIVE-L > 0 on CHECK, T2 and EARLY separately; pooled OOS (CHECK+T2+EARLY)
t >= 2.04 (one trade per day, so day-clustered = per-trade t); hit rate > 50% in each split; >= 95th pct vs random
direction on pooled OOS; positive under both stresses; best-day share < 50% and avg R w/o best day > 0 per split.
**LEAD (gating information)**: hit rate >= 53% on pooled OOS with binomial z >= 2.04, hit rate > 50% and AUC > 0.5 in
every OOS split (stable sign) — even if the SPY trade fails after costs. That would justify a shadow test of the model as
a gate for index-like setups (backlog idea, never a live change from this study).
Otherwise **FAIL**. Every finalist (all 8 + 4 secondary) is reported.
Rule changes: this is a market-only study (no setup R), so no research/ledger.jsonl effective date bears on its numbers.
