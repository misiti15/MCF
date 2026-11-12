Educational only — not financial advice.

# UNRATED14 — 2-year lab rates of the 14 non-Gen unrated setups (Builder, 2026-11-11 22:20 ET; descriptive, 0 configs)

Lead lead-20261111-2100-2 / Observer research/obs-unrated. `rate.py` -> `rate_out.txt`, `unrated14.csv`. 449 open sessions.
Lab setups: research/bdi/1104/bt_all.py month_job (same signal rules, frames, windows, min_adv, refire chain), symbol allow-lists
applied; geometries the walker lacks (holdtr, S) are walked as t1s1 only to count signals (their R is blank).
Index setups: mcf.strategies.index_dip.find_trigger on the QQQ / SPY 1-min cache, per session.

## Results (setup-days/week: direct = 5 x lab p_day; fit = Scout's REPS2 5 x (1 - exp(-0.193 x lab trades/day)))
| setup | trades/day | lab p_day | direct /wk | fit /wk | use |
|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p05-R2A-short | parent ~54/session, short-regime days only | ~0.48 | ~2.4 | (saturates) | **~2.4 cap** (see note) |
| NM-RWR1-exh150-gapdn-spyup-pm-short | 1.50 | 0.183 | 0.91 | 1.26 | fit, capped at direct 0.91 |
| CWT04-backside-vwaptest-a25-short | 0.51 | 0.241 | 1.20 | 0.47 | fit 0.47 |
| LIQ-pdl-sweep-open15-vwap-long | 0.38 | 0.214 | 1.07 | 0.35 | fit 0.35 |
| CWT04-backside-lh-a25-short | 0.33 | 0.140 | 0.70 | 0.30 | fit 0.30 |
| LD7-ns1-idxturn-holdtr-long | 0.30 | 0.156 | 0.78 | 0.28 | fit 0.28 |
| LD6-spy-dip020atr-breadthturn-spxl-holdtr-long | 0.21 | 0.212 | 1.06 | 0.20 | **direct 1.06** (one symbol) |
| LD8-spy-dip030-breadthturn-spxl-holdtr-long | 0.15 | 0.149 | 0.75 | 0.14 | **direct 0.75** (one symbol) |
| LD5-st2-breadthup-t05s1-long | 0.08 | 0.062 | 0.31 | 0.07 | fit 0.07 |
| LD4-st4-breadthup-t1s05-long | 0.05 | 0.038 | 0.19 | 0.05 | fit 0.05 |
| IDX1-qqq100-0955-TQQQ-hold / -trail | 0.020 | 0.020 | 0.10 each | 0.02 | direct 0.10 each (one symbol) |
| IDX2-spy075-0945-3x-trail | 0.011 | 0.011 | 0.06 | 0.01 | direct 0.06 |
| IDX3-spy075-0955-3x-trail | 0.020 | 0.020 | 0.10 | 0.02 | direct 0.10 |

- **Total ~7.0 setup-days/week** with the 'use' column (fit for multi-name setups, direct for one-symbol setups, R2A capped); range 3.2 (fit only, R2A excluded) to 9.8 (direct ceiling).
  About 1.5% on REPS3's 482.8; Observer's 22 Gen setups (~39/wk) remain the only large block.
- Why two columns: the fit maps a lab rate to LIVE slot yield (about 1/5 of lab days at these rates: universe, filters, caps).
  One-symbol setups (SPXL / TQQQ / index) lose no names to a universe cut, so their lab p_day is the better guess
  (LD6: 0.21/session lab, 2 live trades in its first Testing C sessions, consistent).
- CWT14-R2A: the 2y context has no spy_prng, so the module's fail-safe gives 0 lab trades. Rated instead from SPY's prior-day
  range / ATR(14) (daily table, simple-mean ATR, an approximation of mcf F.atr) < the TRAIN-median cut 0.7956: 217 of 449
  sessions (48%; TRAIN 51%, as a median cut should give). The parent fires on ~every session, so p_day ~0.48 is the ceiling. The fit saturates
  at 5/wk and is not meaningful for a regime-gated setup.
- Index setups fire on a market state, at most once a day by design (Observer's expectation, confirmed: 0.06-0.10/wk each).
