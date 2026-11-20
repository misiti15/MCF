# Outside exit methods: results

*Educational only. Not financial advice.* 2026-11-20. The plan was pre-registered in `PLAN.md`, written before the
walk was run. Nothing was committed and no live setting was touched.
**Verdict: FAIL. None of the four outside exit classes passes. Three adopt no family on fit; the fourth (O3, SPY turn)
adopts 2 short families and adds +4.4R on check (t 0.03, bar 4.10).**

## Sources opened (only these are cited)
1. Robot Wealth, K. Longmore, "Stop Losses: Rethinking Conventional Wisdom" (2025-05-30). A P&L-based exit helps only
   when the trade's own P&L predicts what comes next (trend). Otherwise it cuts the edge, and a backtest that improves
   with stops is more often fitted to noise.
2. Quantpedia, "Trend-following Effect in Stocks". A 10-period ATR trailing stop (volatility-scaled) as the exit.
   Multiples 8-12 made no material difference.
3. Quantpedia, C. Dujava, "Lunch Effect in the U.S. Stock Market Indices" (2024-08-21). SPY is weak into lunch and
   turns up after it (a clock-time reversal).
4. arXiv 1701.03960, Leung and Zhang, "Optimal Trading with a Trailing Stop" (abstract). A sell limit (take profit)
   used with the trailing stop is optimal, which supports scale-out plus a trail.
5. arXiv 1005.3535, Heston, Korajczyk and Sadka, "Intraday Patterns in the Cross-section of Stock Returns"
   (abstract). Half-hour continuation at daily multiples, and reversal from liquidity imbalances that last under an
   hour. Clock time matters more than elapsed time.

Not reachable, so not cited as read: dspace.mit.edu (Kaminski and Lo), nd.edu (Gao et al. intraday momentum),
alphaarchitect.com (403), papers.ssrn.com (403). WebFetch had no DNS for arxiv, quantpedia or robotwealth, so pages
were read with curl through the proxy.

## What was tested (WB2, paired on the parent's own signals)
- The giveback map's lab sample: first signal per (setup, symbol, day) of bt_lab1104. That is 1,106,391 trades,
  95 setups and 36 family-sides. The walk was redone on cache_hist 1-minute bars with BEREPLAY geometry and bt_all
  costs. The base reproduces the map exactly: avg −0.0742, correlation with the 5-minute list R 0.997. The locked
  block 2024-11-01..2025-02-28 was filtered at read and asserted absent twice.
- Fit = 170 sessions to 2025-09-30 (370,276 trades). Check = 276 sessions (736,115 trades), scored once.
- Every exit caused by a new rule pays the bt_all exit cost **plus 0.01/share extra**. Trail exits also pay the
  0.02 stop slippage.
- **O1 Chandelier / ATR trail:** arms at +a·D, then trails the best close by k x 14-bar 1-minute ATR.
  a ∈ {0.5, 1.0}, k ∈ {3, 6, 10}.
- **O2 Scale-out + runner:** bank half at +x·D. The runner keeps the target, with its stop at the original level or
  at breakeven. x ∈ {0.5, 1.0}. This differs from the live T2 scale-out (+0.25/0.35R with the runner at breakeven).
- **O3 Index turn:** exit when SPY retraces z% from its best level since entry in the trade's direction (optionally
  only if the trade's mark is ≥ +0.5D). z ∈ {0.25, 0.5}. This is new beside spy_exit_pct, which measures SPY since
  entry and runs on RW3/RW5 only.
- **O4 Clock exit:** exit open trades at 12:00, 13:00, 14:00 or 15:00, either all of them or only those marked
  ≥ +0.5D.
- MAE early cuts were not re-run, because they duplicate time_in_trade class A (FAIL).
- **Configs:** 22 per family-side x 36 = 792, plus 22 book-wide = **814**. Lineage N = 916 (map) + 2,664
  (time_in_trade) + 16 (day_lock) + 814 = **4,410**. Bar = max(1.5, sqrt(2 ln N)) = **4.10** (4.63 at 10x N).

## Fit half
Every one of the 22 configs loses R book-wide on fit except clock exits for winners only at 14:00 and 15:00
(+48R / +137R, t 0.28 / 0.74). See `book_fit_all_configs.csv`.

| config (book-wide, fit) | ΔR | t | family-sides better / worse |
|---|---|---|---|
| O1 a0.5 k3 (tight chandelier) | −3,493 | −4.9 | 2 / 25 |
| O1 a1.0 k10 (loosest) | −146 | −2.7 | 3 / 5 |
| O2 scale half at +0.5, runner at BE | −1,629 | −4.0 | 1 / 14 |
| O2 scale half at +1.0, runner original | −115 | −2.0 | 1 / 3 |
| O3 SPY retrace 0.25%, no arm | −5,999 | −3.4 | 15 / 21 |
| O3 SPY retrace 0.5%, no arm | −1,418 | −1.3 | 23 / 13 |
| O4 flatten all at 12:00 | −8,753 | −5.1 | 18 / 18 |
| O4 winners at 15:00 | +137 | +0.7 | 17 / 10 |

Per family-side selection with gates (fit avg > 0, fit t ≥ 2, w/o best day > 0, ≥ 100 changed): O1 adopts 0 of 36,
O2 0, O4 0, and O3 adopts 2 (RW3S short and RW5 short, both SPY 0.5% retrace with no arm, fit t 2.27 / 2.34). In O3
and O4, 27-29 of 36 family-sides had a positive best config on fit, but only 1-2 cleared t 2. That pattern is
consistent with noise from picking the best of 4-8 configs.

## Check half (scored once)
| class | adopted | Δ total R | Δ avg R | paired t | avg R w/o best day (before → after) | families better / worse | setups better / worse | pass |
|---|---|---|---|---|---|---|---|---|
| O1 chandelier | 0 | 0 | 0 | n/a | −0.0736 → −0.0736 | 0 / 0 | 0 / 0 | **FAIL** |
| O2 scale-out | 0 | 0 | 0 | n/a | unchanged | 0 / 0 | 0 / 0 | **FAIL** |
| O3 SPY turn | 2 | **+4.4R** | +0.00001 | **0.03** | −0.0736 → −0.0736 | **1 / 1** (+27.4R RW3S; −23.0R RW5) | 1 / 1 | **FAIL** (t, ties, best-day share 984%) |
| O4 clock | 0 | 0 | 0 | n/a | unchanged | 0 / 0 | 0 / 0 | **FAIL** |

The check book before any change: −53,193R, avg −0.0723.

Secondary book-wide config per class (chosen on fit, scored on check):
- O1 a1.0 k10: −379R (t −4.9), 0 / 8 families better / worse.
- O2 x1.0 orig: −270R (t −3.5), 1 / 4.
- O3 0.5% with +0.5 arm: −238R (t −2.5), 9 / 18 families, 21 / 35 setups.
- O4 winners 15:00: −481R (t −2.3), 6 / 21 families, 17 / 40 setups.

Diagnostic, not part of the rule (each family's fit-best config applied on check regardless of gates):
- O1: 2 better (+42.6R) / 11 worse (−772.6R).
- O2: 1 (+0.8R) / 7 (−389.8R).
- O3: 9 (+184.4R) / 24 (−1,136.9R).
- O4: 7 (+43.2R) / 26 (−5,035.6R).

**Gap-down short fades (RW/MF/NS/exhaustion shorts), where SPY turning up looked like the obvious trigger:** SPY
0.5% retrace gave +330R on fit and −246R on check. Flatten at 14:00 gave +536R on fit and −3,138R on check. Both
flip sign out of sample.

**Far-target pocket (map pocket 1, check half, every config):**
- t1s05 trades (20,777): every O1, O2 and O4 config is negative (−37 to −1,792R).
- The four map pocket setups (CWT09 g5, MF1-945, MF2-open, CWT12-k6; 16,366 trades): all 22 configs are negative on
  check. The least bad is O3 0.5% with arm, at −17R.
- Scale-out at +1.0D, aimed at exactly this pocket: −92R (runner original) and −153R (runner at breakeven).
- `pocket_check.csv` has the full table.

## Reading
- This agrees with the map and source 1. A trade's own path (O1, O2, O4) and the index path (O3) carry no exit
  signal that survives costs out of sample.
- Banking early cuts the winners that pay for the far-target losers more than it rescues the giveback. Before the
  extra exit cost the rules are near zero; after it they are negative.
- The SPY-turn exit holds up only on the two short families where MCF already runs spy_exit_pct, and even there it
  is a coin flip on check.
- The remaining remedy directions are not per-trade exits: a book-level brake or hedge, and re-anchoring targets at
  entry for the far-target setups. Per the map they need their own WB2 tests.

## Notes
- Live: no class passed, so as pre-registered nothing was scored live. The live minute bars were deleted after the
  map, and the live parquet holds checkpoints only. Rule changes inside the live window (10-06..11-19) are therefore
  not in play here; the map's RESULTS.md lists them.
- Exits are filled at the minute close (O3, O4) or at the level (O1, O2 limit). That is slightly optimistic; the
  0.01/share extra is the allowance for it.
- Lab caveats from the map apply: no ETB, stacking, latch or GEN hold lists, and repeat signals are dropped.

## Files (this folder)
- PLAN.md, walk.py, score.py, score_out.txt, summary.json
- book_fit_all_configs.csv, fit_selection.csv, family_check.csv, setup_check.csv, pocket_check.csv
- The per-trade walk (26 MB) was deleted after scoring. It can be regenerated with
  `python walk.py OUT.parquet 4` in about 4 minutes.
