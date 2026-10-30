Educational only — not financial advice.

# pdl1030 / merge-size: NOTES

**Result: nothing passes.** I scored 20 configurations: the 16 new rows pre-declared in PLAN.md plus 4 parent
re-scores. Nothing was added after scoring. Bar: N = 121512 + 3*20 = 121572, so t >= 4.355. No row has avg R > 0 on
TRAIN or on VALID. The best walk-forward is 11.8% of months positive. No module was written.

Data: TRAIN+VALID only (348 sessions). HOLD months and the locked block were never loaded (asserted at load).
Simulator: top5_1028 `sim` unchanged, costs in.

## Parity (passes, diff 0.0000)
| parent | TV avg R | swarm15 | n/session |
|---|---|---|---|
| p05 | -0.0677 (TRAIN -0.0677 / VALID -0.0675) | -0.0677 | 153.2 |
| p05-lowvol | -0.0950 | -0.0950 | 101.3 |
| p10 | -0.0880 | -0.0880 | 85.7 |
| p10-lowvol | -0.0968 | n/a | 46.1 |

## The merged setup
The bar-level union of the four masks, with one trade per symbol-day at the earliest firing bar, gives 158.9
trades/session. On 94.6% of trades that earliest bar is the p05 bar. Membership: 1 parent fires on 26% of trades,
2 on 57%, 3 on 2%, all 4 on 15% (March 2025 sample). So the merged book is p05 plus 5.7 extra symbol-days per
session. M0 (w = 1, p05 exit) scores -0.0670 / -0.0669, the same as p05.

## Rows (weighted R per unit of risk; every row keeps 158.9 trades/session because w > 0 on every trade)
| id | rule | TRAIN | VALID | t | WF% | risk units/sess | up-day | down-day | w/o best day |
|---|---|---|---|---|---|---|---|---|---|
| M0 | union, w=1 | -0.0670 | -0.0669 | -9.56 | 5.9 | 158.9 | -0.008 | -0.123 | -0.069 |
| W1 | half when SPY is below VWAP | -0.0602 | -0.0654 | -8.97 | 5.9 | 118.3 | -0.010 | -0.127 | -0.064 |
| W2 | half when breadth < 0.5 | -0.0603 | -0.0675 | -8.97 | 5.9 | 117.1 | -0.009 | -0.127 | -0.065 |
| W3 | tape score 0.25..1 | -0.0526 | -0.0647 | -7.54 | 5.9 | 85.0 | -0.005 | -0.131 | -0.059 |
| W4 | size by break depth | -0.0649 | -0.0602 | -8.74 | 5.9 | 141.6 | -0.008 | -0.123 | -0.065 |
| W5 | size down when cost > 5% of R | -0.0404 | -0.0472 | -6.21 | 11.8 | 116.0 | +0.016 | -0.100 | -0.045 |
| W6 | session budget min(1, 30/k) | -0.0637 | -0.0746 | -9.45 | 5.9 | 70.0 | -0.012 | -0.125 | -0.069 |
| W7 | size = number of parents firing | -0.0683 | -0.0637 | -9.12 | 5.9 | 332.1 | -0.010 | -0.122 | -0.068 |
| S1 | 3R stop at the same $ | -0.0205 | -0.0173 | -5.12 | 11.8 | 158.9 | +0.014 | -0.051 | -0.020 |
| C1 | S1 + W5 | -0.0167 | -0.0153 | -4.30 | 11.8 | 153.2 | +0.017 | -0.048 | -0.017 |
| C2 | S1 + W5 x W1 | -0.0147 | -0.0153 | -4.11 | 11.8 | 114.0 | +0.014 | -0.052 | -0.016 |
| C3 | S1 + W5 x W6 | -0.0167 | -0.0184 | -4.57 | 11.8 | 67.3 | +0.017 | -0.052 | -0.018 |
| C4 | S1 + W5 x W3 | **-0.0124** | **-0.0156** | -3.50 | 11.8 | 82.0 | +0.016 | -0.055 | -0.015 |
| C5 | S1 + W5 x W1 x W6 | -0.0139 | -0.0182 | -4.08 | 11.8 | 50.5 | +0.015 | -0.055 | -0.016 |
| H1 | M0 + SPY short hedge (b 0.76, fit on TRAIN) | -0.0949 | -0.0786 | -18.05 | 0.0 | 158.9 | -0.072 | -0.105 | -0.090 |
| H2 | C1 + SPY short hedge (b 0.30, fit on TRAIN) | -0.0284 | -0.0199 | -10.35 | 0.0 | 153.2 | -0.018 | -0.032 | -0.026 |

No row is carried by one big day: every row is negative, and its avg R without the best day is within 0.002R of its avg R.

## What this says
1. **Merging adds nothing on its own.** The four parents are nested versions of one event (63% overlap
   per pdl_eval1029), and the earliest union bar is the p05 bar 95% of the time. "Union, one per symbol-day" is p05.
   Sizing by how many parents agree (W7) has no gradient (-0.067), so agreement between the parents carries no information.
2. **Tape sizing helps on TRAIN, about half as much on VALID.** W3 moves TRAIN from -0.067 to -0.053 but VALID only to -0.065.
   Half-sizing on SPY below VWAP or on low breadth gains about 0.007 on TRAIN and nearly nothing on VALID. The down-day weighted R does
   not improve (it gets slightly worse), because the tape at entry does not predict the rest of the session.
3. **The session risk budget (W6) does not work.** Signal count does rise on down days, but the late signals in a
   crowded session are no worse than the early ones (VALID -0.075).
4. **The only real levers are the risk unit and cost per R.** Sizing by cost share (W5) is worth +0.025. The 3R stop
   at the same $ (S1) is worth +0.047, because it cuts cost/R by 3x and halves the down-day loss. Stacked (C1), they reach -0.016.
   Tape on top (C4) gets to -0.012 / -0.016. That is still negative, with t -3.5 and 2 of 17 months positive.
5. **The beta hedge loses.** The market-neutral intercept is negative after costs. The hedge removes the up-day gains
   as well as the down-day losses, and adds about 0.018R of SPY cost on the 1R unit. It cuts variance (|t| goes up) and avg R goes down.
6. **Sizing cannot fix this.** Sizing only re-weights buckets that are all at or below zero. The gross edge is +0.02R or
   less (pdl1030/why), and no bucket known at entry is positive after costs, so every weighted book stays negative.

## Best curve (fails)
C4: union of the four masks, 3R stop at the same $ risk (target and scale prices unchanged), weight =
clip(0.05/cost_R, 0.25, 1) x (0.25 + 0.25[SPY above VWAP] + 0.25[breadth >= 0.5] + 0.25[SPY gap <= -0.5%]).
TRAIN -0.0124, VALID -0.0156, t -3.50, WF 11.8%, 158.9 trades/session (82 risk units/session).

## When each input is known
Masks, depth, cost/R, SPY VWAP distance, breadth and the signal count k are known at the signal-bar close; the SPY gap is known at
the open. The hedge beta is fit on TRAIN only. spy_day (up/down session) is used only for the descriptive columns.

## Files
PLAN.md, NOTES.md, build.py, score.py, score_out.txt, results.csv, cache/ (u_*.parquet merged trades, par_*.parquet parents). About 6 MB in total.

## Not done
I did not promote L3-gap-slope-rsi5hi-FD to Primary. This step may not touch config/ or the repo. Per CLAUDE.md, a
setup move happens outside 09:30-16:00 ET and must, in the same commit, regenerate docs/live/assignments.json, switch the
setup off in its source account, show the one-big-day check and add the ledger entry. The parent session has to do it.

Educational only — not financial advice.
