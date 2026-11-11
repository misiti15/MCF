# REPS2 — setup-days per SLOT: what one live setup slot yields (descriptive, 0 configs)
Educational only — not financial advice. Research only; no config change. Follows REPS1b (Lead accepted: more setups live is
the only lever that scales). Source: the 7 journals' signals, 10-20..11-10 (16 sessions); `reps2.py` -> `reps2_out.txt`, `reps2_setups.csv`.

## Numbers
- 165 live setups with >= 5 active sessions. A slot yields a median **2.7 setup-days/week** (mean 2.9). 74 yield >= 3/week;
  9 yield < 1/week. All slots together: ~482 setup-days/week.
- By account (median per slot / total per week): Graveyard 5.0 / 150, Primary 4.4 / 50, On Deck (testing) 3.9 / 49,
  Testing A (testing2) 2.8 / 27, Gen 2.0 / 163, Testing C (livelab) 1.7 / 24, Testing B (explore1) 1.3 / 20.
- Planning rule from the lab rate (two-year, 5 busiest days out): p_day = 1 - exp(-0.193 x lab trades/day), fitted on 43 setups
  (corr 0.76). Lab 0.3/day -> 0.3 setup-days/week; 1/day -> 0.9; 3/day -> 2.2; 10/day -> 4.3.
- Blocks cost a slot about a quarter of its days: median signal-day share 0.71 vs submitted-day share 0.54.
- Near-dead slots: MF4-h40-open-flowsell (Primary journal) signalled on 14 of 16 days and submitted on 0 (twin block 71, spread 24,
  borrow 16). MF3-open-flowsell-rsi5hi (testing): 15 signal days, 2 submitted (twin 38, short gate 38). Their twins carry the reps,
  so these slots add almost no independent setup-days. Worth a housekeeping look (main session), not a research change.

## What it means for 'more setups live' (paired with Skeptic's two-stage promotion rule)
- A new account of 20 setups at lab >= 3 trades/day adds ~45-55 setup-days/week (+10%). The same 20 slots filled with
  low-rep setups (lab ~0.3-1/day) add ~6-18. Fill new homes with setups that fire often, or the slot is mostly idle.
- Low-rep setups are inherently slow (Testing B/C median 1.3-1.7/week). Judging one at ~20 setup-days takes 3-4 months
  in one slot. Running a low-rep setup in two homes doubles its signals only where the names differ. A twin in the same names is blocked.
- Rule-change context: Testing B/C started 11-05 (fewer sessions, rates are upper bounds); Testing A top-500 pool from 11-04;
  account names per owner 2026-11-11 (On Deck = testing; Testing A/B/C = testing2/explore1/livelab).
