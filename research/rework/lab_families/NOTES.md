# Rule-18 rework of the failed layered-setup families (key: lab_families)

*Educational only — not financial advice.*

## Pre-declared grid (written before any run, 2026-10-06)

Data: `research/setups2/data/{train,valid}.parquet` only (train to 2026-08-25, valid 2026-08-26..2026-09-15).
No test split, no `data/cache` dates >= 2026-09-16, no `data/cache_q2`, no unlock env vars.
Scoring: `setup_lab` semantics (first qualifying bar per symbol-day, entry at bar close, costs in, R = 0.25 x daily ATR,
exit by 15:55), plus day-clustered t (same formula as `research/reddit_bt/common.metrics`).

### Seed families (side; conditions; one-step grids, base value in brackets)
| family | side | conditions |
|---|---|---|
| OL1 (obos_levels_1) | short | rsi < 20/22.5/[25]/27.5/30; low <= PDL; dist_pdl > 0; dist_pdl <= .1/.15/[.2]/.3/.4; lower_wick >= .3/.4/[.5]/.6/.7; tod <= 1030/1100/[1130]/1200/1230 |
| TP (trend_pullback_1/2/3) | short | fromOpen < -1/-.75/[-.5]/-.25/0; vwapDistPct < -.4/-.2/[0]/.2/.4; sma50_dist < -.4/-.2/[0]/.2/.4; sma20_dist > -.2/-.1/[0]/.1/.2; tod <= 1000/1015/[1030]/1100/1130 |
| WG1 (win_geometry_1) | short | gap < -1/-.7/[-.445]/-.2/0; sma50_dist > 1.5/1.85/[2.19]/2.5/3; tod >= 1200/1230/[1300]/1330/1400 |
| WG2 (win_geometry_2) | short | macdPct > .2/.3/[.399]/.5/.6; dist_pdh > .6/.75/[.95]/1.15/1.35; flow3 > .2/.3/[.376]/.45/.55 |
| WG3 (win_geometry_3) | long | macdPct < -1.5/-1.25/[-1.06]/-.85/-.65; rsiSlope > 17/20/[23.7]/27/30; momentum > .3/.45/[.569]/.7/.85 |
| VF (volume_flip_2 mask) | short | rsi5 > 80/85/[90]/93/95; sma20_dist > .5/.75/[1]/1.25/1.5; bear_div = 1; tod >= 1200/1230/[1300]/1330/1400 (and <= 1500) |
| OVM_L (obos-vwap-ma train favourite) | long | rsi5 > 80/85/[90]/93/95; vwap_atr < .25/.1/[0]/-.1/-.25; sma50_atr < -.25/-.375/[-.5]/-.625/-.75 |
| OVM_S (obos-vwap-ma short fade) | short | rsi5 > 90/93/[95]/97/98; vwap_atr > .4/.5/[.6]/.7/.8; sma20_atr > .3/.4/[.5]/.6/.7 |

(vwap_atr / sma20_atr / sma50_atr = pct distance x close / 100 / atr_d, as in the obos_vwap_ma notes.)

### Tweaks per family (every mask scored in all three geometries t1s1, t05s1, t1s05 = 3 configs per mask)
1. base
2. neighbourhood: each threshold moved +-1 and +-2 grid steps, one at a time
3. drop each condition in turn
4. indicator-length swaps (per family): rsi<->rsi5, sma20<->sma50, macdPct->emaDiff, flow3->flow3-flow9prev,
   and "swap_all": every swap of that family applied at once. Across-all-setups swap (rsi<->rsi5 and sma20<->sma50
   in every family at the same time) is reported as the aggregate of the per-family swap_all rows.
5. add one layer from the library (37 conditions; a library item on the same column+direction as a seed condition is skipped): vwapDistPct >0/<0/>1/<-1; sma20_dist >0/<0; sma50_dist >0/<0;
   sma20_slope >0/<0; dist_pdh_atr <.25/>1; dist_pdl_atr <.25/>1; dist_hod_atr <.1/>.5; dist_lod_atr <.1/>.5;
   dist_round_atr <.1; flow3 >.3/<-.3; flow3-flow9prev >.5/<-.5; vol_climax >2/<1; bear_div; bull_div;
   upper_wick >=.4; lower_wick >=.4; volumeRatio >1.5/<.8; buyPressure >.3/<-.3; tod <=1130 / >=1100 / >=1300 / 1000-1400.
6. pairs: per family, the 8 best single tweaks from 2-5 (ranked by best-geometry TRAIN day-clustered t, n_train >= 100)
   combined pairwise (28 pairs, pairs that set the same parameter twice are skipped).

### Selection (fixed in advance)
- Train eligibility: n >= 100, exp_r > 0, day-clustered t >= 1.5. Only eligible configs are looked at on valid for choosing.
- Finalist gate (backlog.py + task): valid n >= 30, valid exp_r > 0, valid day-clustered t >= 1.5;
  plateau = every +-1-step neighbour of every threshold of the config scored on valid: mean exp_r > 0 and >= 2/3 positive;
  beats both the same-side same-window baseline (all bars in the window, first per symbol-day) and the same-time control
  (mean r of all bars at the same date and bar time as each trade).
- Up to 3 finalists, at most one per family, ranked by valid day-clustered t. Ex-best-day valid exp_r reported.
- Budget about 3,000 configs; exact count in results.json.

## Results (run 2026-10-06; `python research/rework/lab_families/run.py`, ~65 s)

**Configurations: 4,416 evaluated** = 1,986 in the pre-declared search (8 families x ~83 masks x 3 geometries) +
2,430 one-step neighbours scored only for the plateau check of the 173 valid-gate candidates (all 3 geometries each).
This is over the ~3,000 budget: the plateau stage scored every geometry of each neighbour, not only the candidate's.
Lineage totals: parent swarm ~855,600 configs (obos_levels 31,212; obos_vwap_ma 19,196; trend_pullback ~268k;
volume_flip 176,256; win_geometry ~361,200) + 4,416 here. 1,052 configs met train eligibility and were looked at on valid.

### Failures first
- **OVM_L** (obos-vwap-ma long): base valid -0.13/-0.08/-0.10R (n 307). 0 configs pass valid. Dropped again.
- **OVM_S** (obos-vwap-ma short fade): only 23 train-eligible; best valid -0.018R. 0 pass.
- **WG3** (win_geometry_3 long t05s1): base valid ~0R; 3 tweaks pass the gate (best +round<.1, valid +0.10R n 64), weak; not chosen.
- **OL1**: base valid +0.06R t 0.53. 8 tweaks pass (best lwick>=.6 + volumeRatio<.8, valid +0.19R n 94 t 2.99); not chosen (one per family cap, lower t than the three below).
- **WG2**: base valid n 76; swap_all (macd->emaDiff, flow3->flow flip) valid +0.22R n 109 t 2.79 passes; not in top 3.
- Global swaps (swap_all) hurt TP and VF on train (+0.02 / +0.05R); OVM_L swap_all has zero trades.

### Finalists (chosen by valid day-clustered t among gate-passers, max one per family)
| module | side/geom | train n / exp_r / t_dc | valid n / days / exp_r / t_dc | valid ex-best-day | plateau (valid) | window base / same-time ctrl |
|---|---|---|---|---|---|---|
| vf_lowvol_div (VF + vol_climax<1) | short t1s1 | 368 / +0.251 / 1.92 | 51 / 13 / +0.354 / 5.63 | +0.310 | 8 nb, mean +0.262, 100% + | +0.032 / +0.094 |
| tp_slope_rip (TP + sma20_slope<0) | short t05s1 | 268 / +0.087 / 1.54 | 89 / 12 / +0.299 / 5.56 | +0.256 | 12 nb, mean +0.239, 100% + | -0.002 / +0.013 |
| wg1_pdl_fade (WG1 + dist_pdl<0.25 ATR) | short t1s05 | 328 / +0.155 / 1.83 | 33 / 11 / +0.356 / 4.62 | +0.288 | 8 nb, mean +0.361, 100% + | +0.003 / +0.000 |

### Caveats (read before trusting any of this)
- **Valid did not discriminate for these families last time**: TP base already had valid t 3.6 (t05s1) and then made
  +0.015R on the test; WG1/OL1 also passed train+valid and failed the test. 173 of 1,052 eligible configs cleared the
  valid gate, mostly afternoon/morning shorts: the 14-session valid window favoured shorts. Valid t values of 4-6 on
  11-13 days are selection-inflated (best of ~1,000 looks).
- Small samples: wg1_pdl_fade valid n 33 (gate is 30); vf_lowvol_div n 51.
- Train weaknesses: tp_slope_rip train t 1.54 (just eligible), train half1 +0.023; wg1_pdl_fade train half2 -0.013.
- tp_slope_rip is a t05s1 high-win geometry (valid win 87.6%); margin is sensitive to slippage.
- These are reworks of lineages that already used holdout look 1 (Sep16-Oct5): a holdout re-look is look 2 -> t >= 1.5 on both holdouts.
- Locked holdouts were not read. The lead scores the finalists once.
