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
