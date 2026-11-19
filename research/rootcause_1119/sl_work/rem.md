Configurations tried in this dimension: **6 remedy variants** (A, A', A'', B, C1, C2 below), declared before scoring
except A'/A'' (narrowings of A made after seeing A's long/short split — counted). Family = all 118 enabled lab setups in
any account YAML that the lab frames can run (2 skipped: non-standard geometry); 2-year lab, first fire per
symbol-day, production costs; live = paper trades of every setup in Primary, Testing 1/2, Explore 1, Live Lab,
Graveyard, Gen (26,313 trades, 210 setups, 10-06..11-19). Per-setup tables: `sl_work/remedyA_per_setup.csv`,
`remedyB_per_setup.csv`, `burst_weight_per_setup.csv`, `fam_out.txt`, `fam_out2.txt`.

| # | remedy (where the failure occurs) | 11-19 effect | live family (paper) | 2-year lab family | verdict |
|---|---|---|---|---|---|
| A' | **SHORT setups do not trade market-inverse products** (inverse/levered-inverse ETFs and ETNs, long-VIX). Shorting one is a market-long bet the short thesis never meant. | L3: 0 lots instead of 6 → **+6.49R** | 48 short setups affected: **32 better (+74.4R), 16 worse (−19.8R; largest MF2-FD −3.9R)**, net **+54.6R**; 200 trades, win 39%, −0.27R; w/o the worst day still −38.3R | 60 short setups affected: 31 better (+747R), 29 worse (−219R), net +529R; unseen half 35/24 (+213R), later half 31/28 (+316R) | **Best-supported targeted fix.** Clear live, positive but mixed by count in the lab (the lab cannot apply ETB, and inverse products are always ETB live, so live is the more relevant read). Candidate for the backlog + forward shadow, not a market-hours change. |
| A'' | A' restricted to short setups whose rule reads the overnight gap (the L3/RW gap-fade family, where the gap sign flips) | same as A' for L3 | L3-FD −9.0R, L3-rsi5hi-FD −3.5R, L3-lowdist-FD −2.2R, L3-FD-WB4 −3.0R, L3-rsi5hi-FD-WB5 −2.1R: all 5 L3 variants improve | 14 affected: 7 better (+118R), 7 worse (−47R), net +70R; unseen half 11/3 (+71R); later half 6/8 (−0.6R) | Narrower but not stronger in the lab; A' is preferred (same mechanism in every short). |
| A | Remove inverse products from ALL setups (long and short) | as A' | 110 setups: 58 better / 52 worse, net +34R; long side on inverse is +0.04R live | 113: 70 better / 43 worse, net +3,110R (driven by LD2/CWT14 longs) | Too broad: longs on inverse products are not the failure mode live (+20.7R). Not recommended. |
| B | Skip the RSI gap-exit bar (RSI-14: 10:45; RSI-5: 10:00) for setups whose rule reads that RSI | ST7: −7.53R avoided | not tested live | 36 RSI setups affected: 27 better (+612R) / 9 worse (−137R); **but ST7 −35.6R and ST7Q −62.6R get worse** (their 10:45 fires average +0.05 / +0.19R) | Not a fix for ST7: the 10:45 burst is a correlated bet with a positive lab mean. (Interesting for the short families, where the bar is negative — separate backlog idea.) |
| C1 | Weight every same-setup same-bar burst of k fires at 1/√k ("cap the stacking" proxy) | ST7 −7.53 → −2.85R; L3 −6.49 → about −3.7R | not tested live | **115 setups: day-t falls for 102, rises for 13** (median −0.78) | Confirms the owner: blanket stack capping hurts almost every setup. Rejected. |
| C2 | 1/√k only for bursts on the RSI gap-exit bar (the artifact bursts) | ST7 −7.53 → −2.85R | not tested live | 36 affected: 17 t up / 15 down (median 0); **ST7 t 1.01 → 1.37, worst day −7.9 → −2.3 (per average day's risk)**; ST7Q t 2.80 → 2.53 | Neutral across the family, helps ST7 most. Weak candidate; the cleaner fix (untested) is to compute RSI without the overnight change. |

Untested (need a 1-minute rebuild of the frames, after hours): **RSI on intraday changes only** (drop the
prior-close→first-bar change from MCF's RSI windows, or start RSI at the open). That removes the 10:45 / 10:00 jump
at the source for every RSI setup instead of treating its symptoms, and would show whether ST7 has a genuine
"RSI collapse" edge before 13:35. Also untested: counting an inverse ETF's position as the opposite-sign index
exposure in the risk layer (other dimension).
