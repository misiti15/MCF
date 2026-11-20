# GB-GENTRAIL: trails and targets for GEN "hold" setups — results

*Educational only — not financial advice.* Research only. No setup, exit or config change was made. Owner reply
11-19: "Research gentrail". GB-NOEXIT and GB-NOLOCK (no new exit rule, no day-level lock) still stand. The plan was
pre-registered in PLAN.md before any scoring.

## Verdict: FAIL. Keep the hold exits as they are.
- **Hold setups (25 specs, stop 1R, no target, flat at 15:55).** Every trail, target, partial and chandelier rule lost
  R on both halves.
  - The rule picked on the fit half was TR50 (stop at 50% of the best gain once the trade is up 1R). On the check half
    it lost **-0.049R per trade (t -2.61), -1,879R in total. 4 setups got better (+134R) and 21 got worse (-2,013R).
    0 of 10 families got better.**
- **Holdtr setups (22 specs, which already trail 1R behind the best price after +1R).** The fit half picked
  *removing* the trail, which is plain hold.
  - On the check half that scored +0.004R per trade (t 0.49): 13 setups better (+427R), 9 worse (-298R), with the best
    day providing 75% of the gain.
  - The whole fit-half gain came from one day, 2025-04-09. Without it the fit half is -0.016R.
  - Verdict: neutral, so no change.
  - Every other rule on holdtr setups lost on the check half (t -2.1 to -4.5).
- **Live replay (descriptive).** 3,074 trades, 10-06..11-19, LR8 costs.
  - Hold setups: +0.004 to +0.022R per trade (t at most 0.78). Holdtr setups: -0.007 to -0.033R.
  - This is too little data to set against the lab, and live replays have favoured holding to the close before (see
    giveback_1119 FYI).
- This matches every earlier trail and breakeven test: Wave 2 trail, L16, giveback O1/O2 and the target caps.
  Cutting winners at 1R gives up the far runners that pay for the 1R stops.

## Data and method
- **Lab.** 47 GEN hold/holdtr specs from config/account_gen.yaml, with signal lists rebuilt on the generator's own
  2-year panel. That is the first signal per symbol-day, using the same windows, context and earnings blackout as the
  generator.
  - Rebuilt trade counts and baseline R match each spec's `gen.screen` record, e.g. GEN-261029-01 has 9,063 trades vs
    8,921 screened, at +0.229R vs +0.244R.
  - **107,892 trades** in total. Fit: up to 2025-09-30 (170 sessions, 40,436 trades). Check: after that date up to
    2026-10-30 (273 sessions, 67,456 trades).
  - The locked block 2024-11-01..2025-02-28 was never read (the loader refuses it, and the code asserts it is absent).
- **Costs.** The generator's production costs, plus an extra 1c + 1 bp on every exit caused by a rule that is not the
  setup's own exit.
  - Shorts are intraday only, so there is no overnight borrow. Hard-to-borrow fees are not modelled.
  - Live: LR8 costs, plus half spread + 1c + 1 bp on rule-driven exits. The baseline replay correlates 0.978 with the
    journal R.
- **Configs.** 7 rules × 2 groups = 14 cells (12 of them alternatives to the setup's own exit). One rule was picked per
  group on the fit half and scored once on the check half.
  - Across the giveback lineage the multiple-testing bar is t ≥ 4.14. No cell came close to it in a positive direction.

## Check half (lab), paired against each setup's own exit
| Group | Config | Δ R/trade | t | Setups better / worse (R) | Families better / worse |
|---|---|---|---|---|---|
| hold | C2 1R trail after +1R | -0.046 | -2.62 | 3 (+116) / 22 (-1,875) | 0 / 10 |
| hold | **C3 TR50 (fit pick)** | **-0.049** | **-2.61** | 4 (+134) / 21 (-2,013) | 0 / 10 |
| hold | C4 fixed 1R target | -0.059 | -1.99 | 5 (+131) / 20 (-2,380) | 2 / 8 |
| hold | C5 half at 1R + trail | -0.052 | -2.27 | 5 (+107) / 20 (-2,111) | 1 / 9 |
| hold | C6 chandelier 2×ATR5 | -0.079 | -2.30 | 4 (+176) / 21 (-3,217) | 1 / 9 |
| hold | C7 chandelier 3×ATR5 | -0.047 | -2.45 | 4 (+181) / 21 (-1,994) | 1 / 9 |
| holdtr | **C1 no trail (fit pick)** | **+0.004** | **0.49** | 13 (+427) / 9 (-298) | 7 / 3 |
| holdtr | C3 TR50 | -0.012 | -3.40 | 7 / 15 | 1 / 9 |
| holdtr | C4 fixed 1R target | -0.025 | -2.14 | 4 / 18 | 1 / 9 |
| holdtr | C5 half at 1R + trail | -0.012 | -2.14 | 4 / 18 | 1 / 9 |
| holdtr | C6 chandelier 2×ATR5 | -0.047 | -4.49 | 3 / 19 | 1 / 9 |
| holdtr | C7 chandelier 3×ATR5 | -0.020 | -2.83 | 6 / 16 | 5 / 5 |

**Baselines.** The check-half baseline is +0.016R for hold and +0.006R for holdtr.
- **One-big-day check.** On the fit half the hold baseline is +0.228R, but only +0.039R without its best day. That day
  is 2025-04-09, the tariff-pause rally, when the hold longs ran up to 13R.
- Leaving out the single largest day of each cell does not change any sign. For example, hold TR50 on the check half
  goes to -0.037R, with 4 setups better and 21 worse.
- Full grid, both halves and live: data/grid.csv. Robustness: data/robust_out.txt.

**Effect per setup.** The rules hurt most on GEN-261021-06 (-335R), GEN-261029-01 (-324R), GEN-261023-07 (-301R) and
GEN-261020-07 (-227R). The largest gain is GEN-261029-08 (+73R).
- The per-setup tables are in data/setup_hold_C3.csv and data/setup_holdtr_C1.csv.
- GEN-POD seeds and -WB copies are scored live only. WB copies count under their parent spec.

## FYI for the inverse item (no decision here)
GEN hold setups sometimes trade inverse ETFs (data/inverse_out.txt). In the lab, **longs in inverse ETFs averaged
-0.105R (1,838 trades)** against +0.07R for the book. Live there were 101 such longs at +0.114R.

## Rule changes inside the live window (research/ledger.jsonl)
The live figures mix several rule regimes:
- **10-23:** per-setup latch.
- **10-26:** Gen caps (GX2).
- **10-30:** Testing cost filter.
- **11-12:** LR1/LR3/LR8, plus Gen/Graveyard sizing (REPV).
- **11-17:** TSZ1 sizing, SPYEXIT and WB4 copies, and KILL-FLAT adopted lots.
- **11-19:** C3 Epoch 1.
- **11-20, after the window:** broker stop rounding, FOOTRACE-EXIT and PKT-FX.

## Backlog
gb-1119-gen-hold-trail is now `parked`, with configs_tried 14 and the evidence line. The parent
nightly-1020-gen-hold-mfe-giveback is unchanged.

## Files
- PLAN.md, lab_walk.py, live_walk.py, score.py.
- data/ (grid.csv, summary.json, setup_*.csv, score_out.txt, robust_out.txt, inverse_out.txt).
- The per-trade lab and live files (not in git) are in the scratchpad: gt_lab.parquet and gt_live.parquet.
