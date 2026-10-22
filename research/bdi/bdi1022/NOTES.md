# BDI 2026-10-22: every trade of the 5 accounts, and one small swarm (midday window / weak-Nasdaq longs)

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7), one session: a diagnosis, not
evidence. History numbers are **backtests** on the open two-year history with production + tier costs in. The locked
block (2024-11-01..2025-02-28) was never read and no holdout was scored. No config, setup, exit or assignment was
changed and nothing was routed tonight.*

Already done today and **cited, not redone**: `nightly1022/` (P/L, autopsy, give-back, −2R stop re-arm bug →
DECISION LL-LATCH, D1), `l3_1022/` (L3-1 demote), `ns3var1022/` (V1), `st7_1022/` (S1), `pdh1022/`, `regime1022/`
(R1-R3), `swing1022/`. With this run: **8 studies shipped today, 837 configurations** (regime1022 384, swing1022 192, ns3var1022 95,
st7_1022 60, pdh1022 47, bdi1022 36, l3_1022 22, nightly1022 LL-LATCH 1; counts from each NOTES). 0 pass a bar; the
near-misses S1 and V1 are owner decisions in tonight's inbox.

## Failures first
1. **The swarm failed: 0 of 36 configurations pass** (`PLAN.md` written before scoring, `results.csv`,
   `counts.json`, `swarm_out.txt`; gate lineage N 1,290 → bar t 3.78).
   - **A. "Midday" is not a window for the gap-down short family (0 of 20).** RW3/RW5/MF2/MF4 -FD restricted to one
     entry window (09:50-11, 11-12, 12-13, 13-15, 11:30-12:30): every window-only variant still loses after costs in
     at least one period (best MF4 11-12: train −0.111 / valid +0.011R; MF2 11-12: −0.016 / +0.006R). Four MF4
     rows clear t 3.78 on the delta, but only by trading less on up days: in all 20 rows the delta is positive in up
     sessions (+0.06..+0.24) and negative in down sessions. Pooled, 12:00-12:59 is the family's **worst** window in
     valid (−0.079R, n 2,567). Primary's 12:10-12:20 burst on 10-22 was the Nasdaq leg, not the clock.
   - **B. Blocking longs when QQQ is already ≤ −0.5% / −0.75% at entry does not help (0 of 16).** 6 of 8 long
     setups get worse in valid: on weak-Nasdaq days the blocked longs were *better* than average (dip-buys).
     Best NS1-FD Q50: delta +0.013 / +0.018, t 2.40, gated still −0.07 / −0.06R. NM-AR-AM capitulation long would
     lose its edge (train delta −0.31R).
   - Descriptive: the whole family is a market-direction bet on two years — avg R down sessions +0.03..+0.10,
     up sessions −0.19..−0.28, all four negative in train and valid (−0.03..−0.12 / −0.045..−0.066R). By QQQ
     from-open at entry it is flat-to-negative in every bucket (no "Nasdaq already weak" edge either).
2. **No exit or management lever helps on all three days** (SIP 1-min, costs in, Δ vs the simulated bracket;
   `out_1022.txt`, bdi1021 for 10-20/10-21):

   | lever (all accounts, ΔR vs sim bracket) | 10-20 | 10-21 | 10-22 |
   |---|---|---|---|
   | breakeven at +0.5R | −9.4 | +7.9 | −12.8 |
   | +0.5R target | −7.4 | +11.4 | −48.2 |
   | +1R target | +16.3 | −41.7 | −18.2 |
   | 0.5R trail after +0.5R | +30.9 | −2.8 | +1.6 |
   | hold to 15:55 | +3.5 | −132.1 | −4.5 |
   | stop-and-reverse 1R/1R | −13.0 | −27.8 | **+29.3** |
   | one re-entry after a stop | +20.9 | −14.2 | −19.6 |
   | opposite side 1R/1R (instead of the trade) | −165.8 | +179.0 | −11.4 |

   Stop-and-reverse was positive today for the first time (−11.5R over the 3 days; `bdi1014-cwt14-sar` failed on
   history). Every lever flips sign with the day's direction.
3. **The opposite side has no rule known at entry.** Today the stock's own move sorted shorts the right way (shorts
   on names ≥ +1% from the open −0.414R, the rest +0.386R); on 10-20 it sorted them the wrong way (+0.176 vs
   −0.206R) and on 10-21 not at all. SPY's move sorted longs the wrong way today (longs with SPY ≤ −0.25% −0.180R vs
   −0.371R). No opposite-side proposal.
4. **The simulation is optimistic by 33R today** (sim bracket −5.1R vs live −38.2R; Graveyard 15.6R of it), against
   12-18R on 10-20/10-21. Fills and stop overshoot on the 273 post-peak Graveyard entries (nightly1022) are the likely
   cause; what-ifs above are compared with the sim bracket, not with live, for that reason.
5. **OWNER_CHART_READS: nothing new to test.** Both reads (10-15 week, 10-20: the ~09:45 SPY dip buy) are covered:
   IDX1/2/3/5, longs1020 (0 of 200), bdi1021 (0 of 196, both sides of "morning dip then rally"). 10-22 showed no
   09:45 dip (SPY high +0.17% at 10:03, then down).

## What was done
1. **Every trade, 662 of 662 with bars** (`trades_bdi.py`, a copy of bdi1021's, unchanged logic, on
   `nightly1022/trades.csv` + SIP 1-min bars): context at entry, MFE/MAE/time to MFE, the what-ifs above, opposite side
   with hindsight flags, loss type → `per_trade_1022.csv`, `by_setup_1022.csv`, `out_1022.txt`.
   - Per account (R after costs, live): Primary +65.8R (126 trades, +$1,369), Testing 1 −21.4R (113), Testing 2 −1.0R
     (138), Graveyard −77.3R (281), Generated −4.2R (4).
   - **Long vs short:** shorts +36.1R / +$1,648 (369), longs −74.4R / −$2,256 (293). 10-20 was the mirror image
     (longs +43.0R, shorts +5.9R). Primary's gap-down family: 87 trades +73.9R / +$1,581 today, 35 trades +7.6R on
     10-20, 8 trades −0.8R on 10-21.
   - Worst setups: RW2-FD −21.4R (the re-arm, LL-LATCH), CWT14-orl-p05-long −17.4R (65), LIQ-orl −10.4R,
     NM-AR-AM −10.4R, CWT14-pdl-p05-long −10.0R. Best: MF2-FD +29.2R, RW3-FD +24.3R, RW5-FD +19.7R.
2. **patterns.csv:** +297 loser rows for 10-22 (2,829 → 3,126; `merge_patterns.py`, idempotent by date). Loss mix vs
   10-12..10-21: wrong side after a big swing 22.6% (was 15.7%), stopped then reversed 20.9% (12.0%), never worked
   22.9% (23.5%), small MFE 19.2% (21.1%), gave back 10.8% (16.4%), late hold 3.7% (11.4%). A trend day shows up as
   more wrong-side and stop-then-reverse losses.
3. **Give-back (nightly1022, not recomputed):** Primary $184 (12 open shorts flattened at 15:55 as QQQ bounced off
   −1.64%), Testing 1 $95, Testing 2 $104, Graveyard $1,350 (273 entries after a 09:54 peak).
4. **Recurring patterns (≥ 5 of the last 9 sessions)** — CWT14 ORL/PDL longs never-worked / stopped-then-reversed
   (9 days), RW2-FD small-MFE (9), heat_fade_short-FD never-worked / gave-back (8-9), L3-FD and ST2-FD wrong side (7)
   — are all already in the backlog (top5 execution tunes incl. 1.25x/1.5x stops, gates1021/regime1022, N6,
   LL-LATCH). Not re-added.
5. **Backlog (tag `bdi-1022`, no duplicates):** `bdi1022-gapdn-family-time-window` (failed, 20),
   `bdi1022-longs-qqq-weak-block` (failed, 16), `bdi1022-short-cluster-profit-lock` (idea: when ≥ 5 correlated
   sibling shorts are together ≥ +X R open, lock them at breakeven / trail; per-lot breakeven flips sign by day, a
   cluster-level lock might not). `research/BACKLOG.md` regenerated.

## Queued
- `bdi1022-short-cluster-profit-lock` on the two-year history (pre-declare X 3/5/8R × breakeven / 0.5R trail).
- The beta-hedged scoring of the gap-down family (`bdi-rg-beta-hedged`, idea): its two-year split is pure market
  direction, which is exactly what that idea removes.

Files: `PLAN.md`, `swarm.py`, `swarm_out.txt`, `results.csv`, `counts.json`, `trades_bdi.py`, `per_trade_1022.csv`,
`patterns_1022.csv`, `by_setup_1022.csv`, `out_1022.txt`.
