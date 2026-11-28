# regime_filters pre-registration (written 2026-11-28 00:16 ET, before any rule below was scored)

Educational only — not financial advice. Research only; nothing live changes.

Data: run-1 closed lots of all 10 journals, LR8 net R (`cost_r_lr8`). Graveyard excluded from "arena" (as Track 1);
arena identical signals counted once. Books: **Primary**; **arena** = each of testing, testing2, gen, livelab, explore1,
testingd, testinge, testingf treated as its own book (a book rule acts per account).
Periods: **DISC** = 2026-10-23..11-27 (25 sessions). **HOLD** = every earlier session in the journals (10-06..10-22;
Primary, testing, testing2, gen only). HOLD is scored once, after DISC, with the same configs. The locked holdout
2024-11-01..2025-02-28 is not touched (no backtest data is used at all).

Point in time: L = the account's median lots/day over its previous (up to) 5 sessions; first session of an account has
no rule. "Closed R by time t" = sum of R of lots with exit minute <= t (same day). A rule BLOCKS new entries (entry minute
> trigger minute) for the rest of that day in that account; lots already open run as they did (no flatten modelled —
open marks are not in the journal).

## Q1 (3 descriptive configs): does a bad start predict a worse rest of day?
T in {10:00, 10:30, 11:00}. X = closed R by T / L; Y = avg R of lots entered after T. Spearman rho(X, Y) over
account-days; and avg Y on days with X in the bottom quintile vs the rest (day-clustered).

## Q2 (8 rule configs): book risk budget
- BR10 / BR20 / BR30: block when closed R <= -0.10 / -0.20 / -0.30 x L
- BS15 / BS30: block when stop exits >= 0.15 / 0.30 x L
- FH05 / FH10: at 10:30, if closed R <= -0.05 / -0.10 x L, block entries after 10:30
- SIDE20: per side, block that side when that side's closed R <= -0.20 x L_side
Controls: U = same number of lots skipped at random in the same account (300 draws); TT = time-matched: each trigger
(day d, minute tau) is moved to a random non-trigger day of the same account and lots after tau are blocked there
(300 draws). Neutral: saving after re-pricing each account to zero mean R/lot.
Pass bar (all, DISC Primary AND arena, then HOLD same sign): saved > 0, >= 90th pct vs U and vs TT, day-clustered t >= 2,
best-day share < 50%, green-day cost < 50% of saving.

## Q3 (3 regime variables x families): regime by setup family
SPY 20-day realized vol at prior close (terciles fixed on 2026-08-03..10-22), SPY gap at open (< -0.3%, mid, > +0.3%),
SPY open->10:00 move for lots entered after 10:00 (< -0.2%, mid, > +0.2%). Family x side cells with >= 150 lots in
DISC. Persistence: does the best-minus-worst regime cell keep its sign from 10-23..11-09 to 11-10..11-27? Compared
with 50% (coin flip).

Configs counted: 3 + 8 + 3 = 14 (cell counts reported separately).
