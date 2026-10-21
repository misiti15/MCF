# Top-5 setup execution tune, 2026-10-21 (sixth run): FAILED the Testing bar, 0 of 66; 14 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-15..10-21 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history, production + time-of-day costs in, TRAIN (<= 2025-12)
  + VALID (2026-01..03, 07..09-15). The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout
  was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 66** (3 setups x 16 + coil-k6 x 18), plus 4 parent reference runs. Study bar
  max(1.5, sqrt(2 ln 66)) = **2.89**; setup bar 2.35 / 2.40; lineage bars: CWT14 b3 (N 121,396) 4.84, CWT12 coil
  (N 230) 3.30.
- **Results:** 0 variants meet the Testing bar. **0 of 66 have exp > 0** - every parent and every variant loses after
  costs. 14 beat their parent at the setup bar (all still negative). No DECISION line.
- **Only 4 of the top 5 were scored.** Three of the live top 5 (L3-fromopen-FD, MF3-FD, NS3-FD) were cited from tonight's
  other work instead of re-tuned, and two CWT setups were rotated in (see Selection).
- config/, mcf/ and workflows are untouched. 18 `top5-tune` lines were appended to research/backlog.jsonl
  (BACKLOG.md re-rendered).

## Failures first

| setup (acct) | variants | exp > 0 | beat parent | parent exp TRAIN+VALID (t) | best (d R; t_improve) | best variant exp (VALID t) |
|---|---|---|---|---|---|---|
| CWT12-coil-k4-long (T2) | 16 | 0 | 2 | -0.060 (-5.0) | E05 stop x1.5: +0.022 (6.0) | -0.038 (-3.03) |
| CWT14-failbrk-pdh-p10-lowvol-short (T2, **N6 Graveyard proposal**) | 16 | 0 | 5 | -0.086 (-8.0) | E05: +0.032 (8.2) | -0.054 (-2.89) |
| CWT14-failbrk-pdl-p10-lowvol-long (**Primary since 10-21**) | 16 | 0 | 5 | **-0.095 (-7.7)** | E05: +0.033 (7.7) | -0.061 (-3.92) |
| CWT12-coil-k6-long (T1+T2) | 18 | 0 | 2 | -0.068 (-3.8) | E05: +0.017 (3.7) | -0.052 (-2.52) |

**Every parent is a regime bet** (backtest up / down sessions): coil-k4 +0.050 / -0.178, coil-k6 +0.060 / -0.248,
pdl-p10-lowvol long +0.023 / -0.203, pdh-p10-lowvol short -0.212 / +0.010. No execution knob changes the sign.

**Flag for the owner (not a decision from this routine):** CWT14-failbrk-pdl-p10-lowvol-long was promoted to Primary on
10-21 on its live record (51 trades, 74.5% win, +0.106R). Its two-year as-run backtest is **-0.095R/trade
(16,031 trades, t -7.7)**, the worst of the four here, and its module header says it "did NOT pass the gates". Live is
5 sessions of mostly up/flat tape for longs.

**Recurring-loser pattern tested and refuted:** bdi1021 queued "coil-k6 breakeven at +0.5R" (13 of 30 live losers reached
+0.5R first). On two years it is worse: E14 breakeven after live +0.5R d -0.014R (t -1.58), E15 after +1.0R d -0.014R
(t -2.84). Moving the stop up cuts the 2R winners that dip first. `bdi1021-cwt12k6-breakeven` can be closed with this.

## Selection
Live paper trades 10-15, 16, 19, 20, 21 (run_id 1; S6 and GEN-* out; `live_rank.csv`).

- **Out (tuned in top5_1016 / 1019 / 1020, no change since):** CWT14 pdl-p05 (177), pdh-p05-lowvol-short (147),
  pdh-p10-short (131), pdl-p05-lowvol (106), pdl-p10 (106), RW7-FD (59).
- **Out (now in the Graveyard, not in P / T1 / T2):** the 4 CWT14 ORL longs, heat_fade_short(-FD) (166), heat_fade_long(-FD),
  RW2-FD, LIQ-orl, NS2(-FD) and the rest of the Graveyard list.
- **Top 5 eligible:** coil-k4 (112, scored; its 10-16 tune led to the live 0.35R scale-out, so it is not a no-change
  repeat), L3-gap-slope-fromopen-FD (112), MF3-open-flowsell-rsi5hi-FD (74), NS3-failed-vwap-reclaim-short-FD (62,
  **N5 demotion proposal**), CWT14-failbrk-pdh-p10-lowvol-short (60, scored, **N6 Graveyard proposal**).
- **Cited, not redone:** L3-fromopen-FD and NS3-FD - gates1021 scored 30 tweaks on them tonight, none pass, both lose
  slightly over two years as run live (-0.031 / -0.015R). MF3-FD - MF3 family swarmed 10-20 (mf3swarm1020) plus
  gates1021's G1 up-tape gate tonight; there is no MF3 execution harness here, so an MF3-FD execution grid is **queued**.
- **Rotated in:** CWT14-failbrk-pdl-p10-lowvol-long (51) and CWT12-coil-k6-long (49), the next eligible by count.

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | bt win / BE win / exp | live losers never > +0.2R |
|---|---|---|---|---|---|---|
| coil-k4 | 112 | 67.0 / 69.3% | +0.46 / -1.03 | -0.034 | 69.9 / 74.5% / -0.060 | 28 of 37 |
| pdh-p10-lowvol-s | 60 | 50.0 / 70.1% | +0.41 / -0.97 | -0.278 | 64.5 / 70.2% / -0.086 | 18 of 30 |
| pdl-p10-lowvol-l | 51 | 74.5 / 67.6% | +0.50 / -1.05 | +0.106 | 64.1 / 70.4% / -0.095 | 11 of 13 |
| coil-k6 (t1s05) | 49 | 38.8 / 38.7% | +1.69 / -1.06 | +0.003 | 35.7 / 40.4% / -0.068 | 6 of 30 |

(Live R = stop distance; coil-k6's backtest is in 0.25-ATR units, its stop is 0.5 of that, so its avg win/loss is half
the live numbers.)

- **Conversion problem:** the t05s1 setups need ~70% wins (75% with a scale-out); the backtests win 64-70%. Live
  pdl-p10-lowvol beat its break-even only on a 5-session sample (+6.0R on 10-20 / 10-21 alone).
- **Where losers cluster (live):** coil-k4 lost on one day, 10-16 (-14.0R on 22 trades; the other 4 days +10.2R);
  pdh-p10-lowvol-short lost on 10-15 (-9.3R) and on 10:30-11:30 entries; most live losers of the t05s1 setups never
  reached +0.2R (stop-outs straight away), while coil-k6's losers mostly went green first (13 of 30 reached +0.5R).
- **History:** time of day is flat for all four (no bucket is positive); "against SPY after 10:30" is only mildly worse
  for coil-k4 / coil-k6 (-0.078 / -0.094 vs -0.052 / -0.058) and not worse for pdl. The session regime dominates.

## 2. Grid readout (all 66 rows in `results.csv`)

| knob | d range (best t_improve) | note |
|---|---|---|
| **E04 / E05 wider stop x1.25 / x1.5 (same $)** | **+0.009..+0.033 (2.9-8.2)** | beats parent on all 4; win +4-8 pts, avg loss smaller per $; still negative; monotone, x1.5 is the grid edge |
| R0 / E06 / E07 scale-out on the no-scale CWT14 p10 pair (0.25 / 0.35 / 0.15) | +0.019..+0.029 (3.5-5.5) | beats parent on both; same story as the 10-16 scale-out change on the p05 siblings |
| R0 removing coil-k4's live 0.35 scale-out | -0.013 (t -3.5) | confirms the 10-17 live change |
| E06 / E07 coil-k4 scale 0.25 / 0.45 | -0.003 | 0.35 is on a plateau |
| E01 / E02 time stop 30 / 60 min | -0.003..+0.003 (0.9) | smaller avg loss, lower win; a wash |
| E03 tighter stop x0.85 | -0.013..-0.024 (t -5.6..-8.4) | clearly worse on all 4 |
| E08 wait one bar | -0.003..+0.009 (1.4) | not significant |
| E09-E11 window | -0.014..+0.005 (0.6) | flat |
| E12 skip against SPY after 10:30 | -0.004..+0.009 (1.1) | not significant |
| E13 re-entry 30-min cooldown | -0.001..0 | +2-5% trades at the same quality |
| T1 / T2 threshold -20 / +20% | -0.017..-0.000 | parent is not improved by thresholds |
| E14 / E15 coil-k6 breakeven | -0.014 (t -1.6 / -2.8) | refutes the bdi1021 loser pattern |

**Excess over the same-minute random control:** coil-k4 / coil-k6 parents are slightly above random (+0.006 / +0.025R),
the CWT14 p10 pair below (-0.004 / -0.019R). The wide-stop gains do not raise the excess (coil-k4 E05 +0.003, pdh E05
-0.005): as in the last four runs, the stop-width gain is generic exit geometry - random entries gain about as much.

## 3. Bars
- **Beats parent (14):** E04 + E05 on all 4; R0 (scale 0.25), E06 (0.35), E07 (0.15) on pdh-p10-lowvol-short and
  pdl-p10-lowvol-long. 7 of the 10 CWT14 rows also clear the lineage bar 4.84 (not E07 pdh 3.53, E07 pdl 4.03, R0 pdh
  4.17); coil-k4 E04/E05 clear the coil lineage bar 3.30, coil-k6 E05 (3.72) does, E04 (2.91) does not.
- **Testing bar** (VALID t >= 2.89 with exp > 0, both regimes > 0, excess > 0): **0 met it.** Every variant is negative
  on TRAIN and VALID. No Testing proposal; no Primary change proposed.
- Live support: E04/E05 = module with GEOM "S" at the same $ (see top5_1020); scale-out rows = config only
  (`scale_out_r` + `live_scale_out`).

## Backlog (appended to research/backlog.jsonl, tag top5-tune)
4 `top5-1021-<setup>-exec` lines (status failed) + 14 beats-parent lines (status rework, with live_support).

## Queued (not scored tonight)
- MF3-open-flowsell-rsi5hi-FD execution grid (needs an MF3 harness with parity).
- Stop x1.75 / x2.0 extension across the CWT families (the wide-stop curve still rises at x1.5; it has done so in all
  five runs - it narrows the loss, never flips it).
- The two CWT14 p10 lowvol setups would gain ~0.02-0.03R from a 0.25-0.35R scale-out (as their p05 siblings did on
  10-16) but stay negative; with pdh-p10-lowvol in N6 and pdl-p10-lowvol in Primary, that is the owner's call, not a
  proposal here.

## Files
- `live_rank.py` (top5_1020's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`.
- `scan_1021.py` (top5_1019 / 1020 harness + coil kernel). Parity on 2025-06: 4 kernels equal `cwt_live_lib`;
  parents equal `gates.lab_trades` trade for trade (2,159 / 825 / 789 / 866 matched, mean |d| 2-4e-5R, 100% within
  0.01R). Scan ~8 min; scratch trades file deleted.
- `report_1021.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`; `make_proposals.py` ->
  `backlog_proposals.jsonl`.

Educational only — not financial advice.
