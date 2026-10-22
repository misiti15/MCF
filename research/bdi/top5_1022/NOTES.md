# Top-5 setup execution tune, 2026-10-22 (seventh run): FAILED the Testing bar, 0 of 90; 18 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-16..10-22 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history, production + time-of-day costs in, TRAIN (<= 2025-12)
  + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was
  scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 90** (6 setups x 15), plus 6 parent reference runs. Study bar max(1.5, sqrt(2 ln 90)) =
  **3.00**; setup bar 2.33.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 18 variants beat
  their parent (all still lose after costs in at least one period). Only 6 of 90 variants have exp > 0 over both periods pooled (4 in TRAIN and VALID separately), all on RW4-FD, and none of those beat their parent at the bar.
- config/, mcf/ and workflows are untouched. 24 `top5-tune` lines appended to research/backlog.jsonl (6 grids, status
  failed; 18 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | variants | beat parent | parent exp TRAIN / VALID (all, t VALID) | best variant (d R; t) | best variant TRAIN / VALID |
|---|---|---|---|---|---|
| MF3-open-flowsell-rsi5hi-FD (T1) | 15 | 4 | -0.097 / -0.053 (-1.78) | E04 stop x1.25: +0.021 (4.96) | -0.075 / -0.032 |
| RW7-gapdn-bounce-early-short-FD (T1) | 15 | 4 | -0.079 / -0.033 (-0.96) | E04 stop x1.25: +0.027 (3.92) | -0.059 / -0.026 |
| RW4-ns3-adv150-short-FD (T1+T2) | 15 | **0** | **+0.009 / +0.002** (0.05) | E04 stop x1.25: +0.011 (1.65) | +0.018 / +0.015 |
| exhaustion_short-FD (T1+T2) | 15 | 5 | -0.102 / -0.026 (-0.83) | E05 stop x1.5: +0.040 (4.63) | -0.063 / -0.012 |
| MF5-flowsell-vwapup-rsi5hi-FD (T2) | 15 | 3 | -0.096 / -0.001 (-0.03) | E04 stop x1.25: +0.025 (3.28) | -0.075 / +0.014 |
| RW1-gapdn-bounce-flowsell-short-FD (T2) | 15 | 2 | -0.071 / -0.010 (-0.29) | E14 skip SPY up: +0.033 (2.65) | -0.019 / -0.013 |

**Every parent is a market-direction bet** (backtest, SPY up / down sessions): MF3-FD -0.220 / +0.051, RW7-FD -0.244 /
+0.082, RW4-FD -0.083 / +0.056, exhaustion-FD -0.174 / +0.069, MF5-FD -0.200 / +0.109, RW1-FD -0.230 / +0.100. No
execution knob turns the up-session number positive. The "skip while SPY is up" filter (E14) only helps by trading
the down sessions (keeps 32-60% of trades) and still fails VALID or TRAIN.

**RW4-FD is the one setup that does not lose over two years** (+0.005R/trade, 10,569 trades, t ~0; beats same-minute
random shorts by +0.07R). None of its 15 knobs improve it at the bar; its wider stops (E04/E05 +0.016/+0.021R, positive
in both periods) are the nearest miss (t 1.65 / 1.50 < 2.33). Live it is -0.092R on 54 paper trades (10-21: 21 trades
-7.5R).

**Recurring live loser patterns tested and refuted:**
- MF3-FD and MF5-FD live losers cluster at 10:00-10:29 entries (MF3 20 trades -0.78R, MF5 10 trades -0.84R). On two
  years that half-hour is not special (MF3 -0.072R, MF5 -0.080R, both about the parent average); skipping it (E13)
  gives d -0.002 (MF3) / +0.018 (MF5), t 1.40 / 1.67 - not significant.
- RW7-FD: 17 of 31 live losers never reached +0.2R ("never worked"). A 15-minute time stop for those (E15) is d +0.002R
  (t 0.31); 30 / 60-minute versions are the same. In history 39% of losers never work, and cutting them early also
  cuts the slow winners.
- Breakeven after +0.5R (E07) is worse or flat on all 6 (win rate falls 11-13 points). Tighter stop x0.85 (E03) is
  clearly worse on all 6 (t -1.6..-5.9).

## Selection
Live paper trades 10-16, 19, 20, 21, 22 (run_id 1; S6 and GEN-* out; `live_rank.csv`), account membership from
`docs/live/assignments.json` (Graveyard out).

- **Rotated out - tuned in top5_1019 / 1020 / 1021, no change since:** CWT14 pdl-p05-long (169), pdl-p10-long (81),
  pdl-p05-lowvol-long (76), coil-k4 (50), pdl-p10-lowvol-long (49), coil-k6 (39).
- **Cited, not redone (studied today):** L3-gap-slope-fromopen-FD (118; `l3_1022`, 0 of 22, now Testing 1);
  NS3-failed-vwap-reclaim-short-FD (68; `ns3var1022`, V1 decision open); RW5-FD / RW3-FD / MF2-FD / MF4-FD
  (`bdi1022`, gap-down family windows, 0 of 20); CWT14 pdh-p10 family (`pdh1022`, Graveyard).
- **Scored:** MF3-FD (74; queued by top5_1021, this run adds the harness), RW7-FD (62), RW4-FD (54), exhaustion_short-FD
  (39), and the tie for fifth MF5-FD / RW1-FD (29 each) - both scored.

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | bt win / BE win / exp | live losers never > +0.2R |
|---|---|---|---|---|---|---|
| MF3-FD | 74 | 45.9 / 59.3% | +0.64 / -0.94 | -0.211 | 48.1 / 53.1% / -0.082 | 7 of 40 |
| RW7-FD | 62 | 50.0 / 54.0% | +0.74 / -0.87 | -0.064 | 48.7 / 52.5% / -0.062 | 17 of 31 |
| RW4-FD | 54 | 35.2 / 41.8% | +0.81 / -0.58 | -0.092 | 51.3 / 50.9% / +0.005 | 10 of 35 |
| exhaustion-FD | 39 | 51.3 / 45.6% | +0.97 / -0.81 | +0.101 | 49.3 / 53.2% / -0.071 | 6 of 19 |
| MF5-FD | 29 | 41.4 / 53.5% | +0.82 / -0.95 | -0.215 | 49.2 / 53.1% / -0.067 | 3 of 17 |
| RW1-FD | 29 | 62.1 / 50.0% | +0.78 / -0.78 | +0.188 | 49.2 / 52.2% / -0.048 | 6 of 11 |

- **Conversion problem:** all six are t1s1 (1R target / 1R stop), so after costs they need ~51-53% wins; the backtests
  win 48-51%. Live winners average only +0.64..+0.97R because many end at the 15:55 flatten below target (live
  "flatten" exits: MF3 19, RW7 17, RW4 29 of 54).
- **Where live losers cluster:** MF3-FD lost on 10-19 / 10-20 (-14.3R of -15.6R) and at 10:00-10:30; RW7-FD on 10-19
  (-9.5R) and 10:30-11:30 entries (19 trades -0.34R); RW4-FD on 10-21 (21 trades -7.5R) and late flattens; MF5-FD at
  10:00-10:30. History does not confirm any time-of-day cluster (`hist_parent_detail.txt`); the session direction
  dominates.
- MFE/MAE (history, R): median MFE +0.55..+0.76, median MAE -0.51..-0.76; 35-40% of losers never reach +0.2R and
  23-30% reach +0.5R first (give-back).

## 2. Grid readout (all 96 rows in `results.csv`)

| knob | d range (t) | note |
|---|---|---|
| **E04 / E05 wider stop x1.25 / x1.5 (same $)** | +0.009..+0.051 (1.5-5.0) | beats parent on 5 of 6 (not RW4); win +3-6 pts; the same generic stop-width gain as in the last five runs; still negative except RW4 |
| E14 skip shorts while SPY up | -0.001..+0.033 (0.1-3.8) | beats parent on 4; trades only down sessions, up-session R gets worse |
| E12 window end 13:00 | -0.010..+0.033 (0.1-3.1) | beats parent on MF3, RW7 |
| E11 from 10:30 / E13 skip 10:00-10:29 | -0.006..+0.024 (-2.1..3.0) | beats parent on exhaustion-FD only (E11 2.95, E13 2.69) |
| E06 scale half at +0.5R, stop to BE | -0.029..+0.027 (-1.5..2.0) | win +11-14 pts, no better R |
| E08 / E09 target 0.75R / 1.5R | -0.017..+0.018 (-2.1..1.3) | flat |
| E01 / E02 / E15 time stops | -0.018..+0.012 (-3.1..0.6) | flat to worse |
| E10 wait one bar | -0.014..+0.009 (-2.2..0.4) | flat to worse |
| E07 breakeven after +0.5R | -0.041..+0.002 | worse |
| E03 stop x0.85 | -0.032..-0.011 (-1.6..-5.9) | worse on all 6 |

Random control (same-minute random shorts, parent geometry): RW4-FD +0.070R, RW1-FD +0.031, RW7-FD +0.019,
exhaustion-FD +0.012, MF5-FD +0.012, MF3-FD -0.002. The stock pick adds a little; the loss is the short-side market
bet plus costs.

## 3. Bars
- **Beats parent (18):** MF3-FD E04 E05 E12 E14; RW7-FD E04 E05 E12 E14; exhaustion-FD E04 E05 E11 E13 E14; MF5-FD E04
  E05 E14; RW1-FD E05 E14 (RW1 E04 has the higher t 3.06 but VALID d -0.0004, so it fails "d > 0 on both").
- **Testing bar** (exp > 0 on TRAIN and VALID, VALID t >= 3.00, up and down sessions > 0, ...): **0 met it.** No
  Testing proposal; no Primary change proposed. No holdout scored.

## Queued (not scored tonight)
- Thresholds +-20% for these six (the cached signals have no threshold hook; each lab module must be re-run).
- RW4-FD wide stop x1.5-x2.0 at same $ as a paired round (rule 18) with its morning window - it is the only parent at
  break-even and the stop-width curve still rises.

## Files
- `live_rank.py` (top5_1021's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `scan_1022.py`: entries from gates1021's cached live-shaped signals (`gates1021/scripts/scan.py`), exits with the
  top5_1019 simulator on 5-minute paths. Parity on 2025-06: 2,855 trades, 0 unmatched, mean |d| 0.004R vs the cached
  production R, 99.5% within 0.05R (per-setup means equal to 3 decimals except exhaustion-FD -0.110 vs -0.121: the
  cache's extended-tier x3 costs). Scan ~2 min; scratch trades file not committed.
- `report_1022.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`; `make_proposals.py` ->
  `backlog_proposals.jsonl`.

Educational only — not financial advice.
