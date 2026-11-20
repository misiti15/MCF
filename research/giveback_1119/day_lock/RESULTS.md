# Day-level profit lock — results

*Educational only — not financial advice. Research only: nothing was committed by this stage, and no setup, exit or
config was changed.* Plan: [PLAN.md](PLAN.md). It was written before any score, and addendum A was added after the
first pooled totals but before any check-half, family or Primary score. Full tables: [tables.md](tables.md). Data:
[data/](data/). Code: sim_live.py, analyze.py, sim_lab.py, fetch_bars.py.

**Configs tried: 16** (X ∈ {+5R, +8R} × giveback Y ∈ {30%, 50%} × action ∈ {A1 block the dominant side, A2 tighten
stops to lock 50% of open profit, A3 scale out half, A4 flatten and stop trading}). N_class = 16 gives a bar of
2.35. At a conservative lineage N = 200 the bar is 3.26.
Costs: LR8 on every live row, plus an extra early-exit cost (half spread + $0.01/share + 1 bp) on every early exit.

## Answer first

**FAIL. 0 of 16 configs pass.** No form of account-level profit lock beats a matched control on live data.

- **Exits on open lots lose R on the check half.** A2 tighten loses -64 to -103R and A3 half loses -85 to -129R
  (t -0.6 to -1.7). Both were slightly positive on the fit half, so the sign flips between halves. This agrees with
  the map: from any state, holding is worth more than exiting once the exit cost is paid.
- **Block and flatten gains come from trading less, not from the lock signal.** The book loses money on average
  (-0.151R per trade), so any rule that stops entries looks good. To test that, I applied the same action at the same
  clock minute on the same account's days when the lock did not fire. That control did as well or better:

  | Config | Check-half gain | Same action on non-fired days (control) | Excess over control |
  |---|---|---|---|
  | A4 flatten, +5R / 30% | +287R | +575R | **-288R** |
  | A1 block, +5R / 50% | +408R | +269R | +139R (t 0.99) |
  | A1 block, +5R / 50%, fit half | | | -160R (t -1.70) |

- **Best candidate: A1 block (dominant side), +5R / 50%.** It passes every original item on the check half:
  - 49 days fired: 25 helped, 18 hurt. Total +408R, paired t 2.60.
  - Avg R per trade -0.139 → -0.132. Avg R per trade without the best day -0.158 → -0.146. Best day's share of the gain 28%.
  - Families: 27 better (+466R), 11 worse (-58R). Setups: 77 better, 38 worse.
  - It fails addendum A: excess t is 0.99, and the excess was negative on the fit half. The t of 2.60 also falls short
    of the conservative 3.26 bar.
  - The families that gain are mostly the large losing books: GEN +149R, CWT14 +91R, RW2 +35R, heat_fade_short +25R.
    The families hurt are RW7 -17R, L3 -13R, CWT09 -9R and RW6G1 -6R.
- **Cost on days that kept running up.** These are fired days where the MTM later went above the peak it had when the
  lock fired. Under flatten they cost -175 to -224R on the check half (25-28 such days). A1 cost about +10R on them.
  On Primary, flatten at +5R/30% cost -40.8R on 11-12 (that day closed +39.9R) and -24.0R on 11-16.

## Primary (descriptive; 33 sessions, 5-13 fired days, no t clears 1)

| config | fired | helped/hurt | Δ all days | excess | 11-19 Δ |
|---|---|---|---|---|---|
| A4 flatten +5R/30% | 13 | 8/5 | +49.8R | +32.4 | +19.9 (−16.2 → +3.7) |
| A4 flatten +8R/50% | 6 | 3/3 | +43.7R | +45.6 | +18.7 |
| A1 block +8R/30% | 7 | 2/4 | +34.6R | +33.2 | +2.8 |
| A2 tighten +5R/30% | 13 | 6/7 | +8.3R | +4.0 | +14.2 |
| A3 half +5R/30% | 13 | 7/6 | +7.5R | +4.7 | +7.5 |

- On Primary, the lock adds about +1 to +1.5R per session. The result rests on 11-06 (+25.4R), 11-10 (+40.0R) and
  11-19, and is offset by 11-12 and 11-16. With 6-13 days, Primary cannot carry a verdict.

## Per account, check half (Δ R, A1 block +5R / 50%)
| Account | Δ R |
|---|---|
| Graveyard | +228 |
| Gen | +120 |
| Testing 2 | +35 |
| Explore 1 | +21 |
| Primary | +13 |
| Testing D | +9 |
| Live Lab | +6 |
| Testing 1 | -9 |
| Testing E | -13 |
| Testing F | -3 |

Excess over the control is negative for Testing 1, Testing 2, Testing D and Testing E ([tables.md](tables.md)).

## 2-year book replay

research/replay2y is not calibrated (79.4% match against a 98% bar, weight 0, 7 sessions), so it was not scored.

As a reference only, I ran synthetic lab books: 3 draws of 40 trades per session, 1,338 books, with marks interpolated
between the 5-120 minute checkpoints. Locks show small positive deltas:
- A4 flatten +5R/30%: +46R over 828 check books, t 1.5.
- A2 tighten: t 2.4-3.0.

Interpolated marks are too smooth and miss moves inside the minute, which favours locks. Under the plan these numbers
carry screening weight only and never count toward a pass. Only 10.6% of books ever reached +5R.
[data/lab_scores.csv](data/lab_scores.csv).

## Rule changes inside the live window (research/ledger.jsonl)
- 10-16/17: Testing 2 scale-out.
- 10-23: per-setup loss latch.
- 10-28: Primary sizing changed twice.
- 10-29: Primary -2R per-setup latch. This already truncates late entries, which overlaps with A1.
- 10-30: Testing cost filter.
- 11-12: LR1 flatten at 15:55, LR3 latch in R, LR8 costs, Gen/Graveyard sizing.
- 11-17: TSZ1 sizing and SPYEXIT.
- 11-19: C3 Epoch 1.

The fit/check split (10-31) falls after the latch and sizing changes, so the two halves run under different regimes.

## Caveats
- Blocked lots score 0; capacity freed by a block is not re-used.
- Account MTM sums lots in R at equal weight.
- A1's dominant side is set by count of open lots.
- Each account-day fires at most once.

## What could come next (not tested)
- The live data favour entry restraint over exits. A block, given its control result, should be tested as a
  setup-level or time-of-day entry rule, not as a profit lock. This overlaps with the existing latches.
- The map's directional-book hedge (an SPY/QQQ hedge when ≥ 80% of the book is on one side) is a different mechanism
  and remains untested.
