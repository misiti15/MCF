# mf3swarm1020 - PLAN (pre-declared 2026-10-20, written after the live autopsy and BEFORE any history scoring)

*Educational only - not financial advice. Research only: no config/, mcf/strategies, workflow, ledger, backlog or
owner-inbox edits; candidates are lab modules + proposed YAML in this folder. The locked block 2024-11-01..2025-02-28 is
never loaded (lib.months() lists only open months; headtail rows are read per open month with a date filter).*

## Owner request (2026-10-20)
MF3-open-flowsell ("Early Sellers into a Pop") fires a lot and has bouts of success by variant: find a tweak that makes it
more profitable; propose up to 3 new variants for the Testing account with the most room (placed later by the owner with
mcf/research/allocate.py).

## Parents
Core mask `heat <= -30 & buyPressure < -0.25 & rsi5 > 70`, short, R = 0.25 x daily ATR, min_adv 95M, first qualifying
bar per symbol-day (no refire), flat 15:55.
- **P-W**  MF3-open-flowsell-rsi5hi, window 950-1100, t1s1 (Testing 1 now).
- **P-FD** MF3-open-flowsell-rsi5hi-FD, window 950-1500, t1s1 (Primary).
swarm1017/rework-mf already scored 47,820 MF-family configs (heat/bp/RSI5 neighbourhood, 33 one-filter and 528 pair
filters incl. SPY>0/<0, breadth, gap, fromOpen, VWAP, ATR terciles, day-of-week, windows 950-1030/950-1100/1100-1300/
1300-1500/950-1500, t1s1/t05s1/t1s05, refire). Not repeated here. New in this study: finer window slices from the autopsy
(950-1015, 1015-1100, 1015-1500, 1100-1500), QQQ from-open and breadth_open context (lab_context columns, deployable),
buyPressure *band* (drop the extreme flow), liquidity floors, the live-supported exits swarm1017 could not score
(t05s05, hold, holdtr, time stop, wider/narrower stop at the same $ risk via r_atr_frac) and two-knob pairs of those.

## Live autopsy findings that motivate the knobs (paper, 125 trades / 9 sessions, in-sample - autopsy_out.txt)
early 09:50-10:15 entries -0.43R vs 11:00-15:00 +0.25R; QQQ < 0 at entry +0.02R vs QQQ >= 0 -0.38R; gap <= 0 +0.31R vs
gap > 0 -0.31R; below VWAP +0.09R vs above -0.24R; top adv20 tercile (>= ~$340M) +0.09R vs bottom -0.35R; extreme
flow (bp <= -0.5) -0.56R (n 12); median MFE +0.64R and 21 of 60 losers reached +0.5R (give-back) -> t05 targets / trail.

## Data, split, costs
- research/history2y frames (open months only) + lab context (spy_fo, qqq_fo, breadth, breadth_open) + the 15:05-15:55
  tail rows (research/bdi/cwt/test_b/data/headtail.parquet) for exits that hold into the close.
- **train** = open months <= 2025-12 (2024-10, 2025-03..2025-12); **valid** = 2026-01..2026-10-07.
- Universe rows adv20 >= 95M (the parent's min_adv), decision bar close 09:50..15:00.
- Every geometry is scored with ONE 5-minute path simulator (entry at the decision bar's close, stop checked first in a
  bar, then target; trailing / time-stop updates from the next bar; flat at 15:55): costs 1c + 1 bps per side, entry
  side x time-of-day multiplier (mcf.research.gates.tod_cost_mult), +2c on stop fills, target fills free, x3 on the
  extended tier (|gap| >= 20% or price < $5). Sanity check: simulator t1s1 vs frame outcome + gates.prod_r on the parent
  (reported).
- Random baseline: for each trade, the mean simulated R of every min_adv row at the same date and decision bar, same side
  and geometry ("same-minute random entry"); excess = trade R - baseline.

## Grid (every configuration counted, including empty ones). Base = P-FD unless stated.
| block | configurations | count |
|---|---|---|
| P | parents P-W, P-FD | 2 |
| A windows (t1s1) | 950-1015, 1015-1100, 1100-1300, 1300-1500, 1100-1500, 1015-1500 | 6 |
| B context | FD x {qqq_fo<0, qqq_fo<-0.25, spy_fo<0, breadth<0.5, breadth_open<0.5, qqq_fo<0&spy_fo<0}; W x {qqq_fo<0, spy_fo<0, breadth_open<0.5} | 9 |
| C thresholds | rsi5>60, rsi5>80, bp<-0.35, bp<-0.15, band -0.5<bp<-0.25, heat<=-40 | 6 |
| D stock state | gap<=0, gap<1, vwapDistPct<0, fromOpen<0 | 4 |
| E liquidity | adv20 >= 200M, 350M, 1B | 3 |
| F exits | FD x {t05s1, t1s05, t05s05, hold, holdtr, rfrac 0.1875 t1s1, rfrac 0.375 t1s1, rfrac 0.5 t1s1, TS30 (t1s1 + time_stop_min 30 / min_r 0.3), TS60}; W x {t05s1, t05s05, holdtr} | 13 |
| G refire | FD with refire cooldown 1 (the parents are already one entry per symbol per day) | 1 |
| H pairs | pairs of K = {win 1100-1500, win 1015-1500, qqq_fo<0, spy_fo<0, gap<=0, vwap<0, adv>=350M, bp band} (28 minus the window-window pair = 27) + each K x {t05s1, holdtr} (16) | 43 |
| **total N_study** | | **87** |

- **Bars.** Study bar: day-clustered t >= max(1.5, sqrt(2 ln 87)) = **2.99**. Lineage (MF family ~133,904 through
  swarm1017 + 87): sqrt(2 ln 133,991) = **4.86**. The Testing bar asked for is valid t >= 1.5.
- **Candidate rule (fixed now):** exp_train > 0 and exp_valid > 0 (after costs); beats BOTH parents' expectancy on train
  AND on valid; valid day-clustered t >= 1.5; n_valid >= 100; plateau: at least half of its declared neighbours (below)
  positive on train and valid. Reported for every candidate (not gates for Testing, gates for Primary): regime split
  (up/flat/down sessions, lib.regimes), walk-forward share (gates.walk_forward), ex-best-day, excess vs same-minute random
  (day-t), QQQ up/down day split, trades/day. Ranking: valid expectancy; ties by valid t.
- Up to 3 candidates, de-duplicated (pairwise trade overlap > 60% -> keep the higher valid exp).
- **Neighbours:** windows -> the windows sharing an edge; thresholds -> one step either side; context qqq<0 <-> {qqq<-0.25,
  spy<0, qqq&spy}; liquidity -> adjacent floors; exits -> the other exits of the same family (targets t05s1<->t05s05;
  rfrac 0.375 <-> 0.5 / 0.1875; TS30<->TS60; holdtr<->hold); a pair -> its two one-knob parts.
- Holdouts: none is scored here (the lead scores finalists once on the locked block; this study never loads it).
- Live paper data (2026-10-08..20) is reported only as the autopsy (rule 7); it is not used to rank.
