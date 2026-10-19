# tf1019/t1-misc - results (Testing-1 NS*-FD, MF*-FD, heat_fade_* x 1/3/5/10/15-min decision bars)

Run 2026-10-19 (night of Sun 10-18), pre-declared in PLAN.md. Educational only - not financial advice.

**Verdict: 0 of 126 configurations pass. No candidate, no module written to modules/.** Configurations counted: 126
(70 as-is + 56 time-equivalent). Bars: t_required 4.76 (MF/NS lineages, N ~82k) / 4.78 (heat lineage, N 93,382);
this task's family alone (N=126) would need t >= 3.11 - the best configuration of all 126 reaches t 1.12.
The regime gate (up AND down sessions > 0, n >= 30) fails on every one of the 126 configurations: almost all are
one-regime (the shorts make money on down days and lose on up days; the longs the reverse) on every timeframe; the rest
have fewer than 30 trades in a regime (e.g. NS4-FD 15m, n=40).

Universe: 80 core symbols (all five timeframes), min_adv as in config (95M lab, 125M heat), costs in (production-cost R,
time-of-day entry costs), first qualifying bar per symbol-day (live refire not modelled), split open = train 2024-10 +
2025-03..12, valid 2026-01..10-07, forward 10-08..10-16 (reported in results.csv only, never used to choose). Locked
block 2024-11..2025-02 never loaded. Random same-minute baseline: most configurations beat the baseline (excess > 0),
but the baseline itself is negative after costs (about -0.03..-0.06 R), so beating it is not enough.

## Best timeframe per setup (highest t among configurations with n >= 30; first failed gate shown, regime fails on all)
| setup | best tf (variant) | n | exp train | exp valid | t (bar) | excess vs rnd | up / down | wf | fails |
|---|---|---|---|---|---|---|---|---|---|
| NS1-FD | 3m asis | 480 | +0.051 | +0.027 | 1.12 (4.76) | +0.056 | +0.098 / -0.051 | 0.562 | t 1.12 < 4.756 |
| NS2-FD | 15m te | 1152 | -0.024 | -0.044 | -0.86 (4.76) | +0.019 | -0.152 / +0.188 | 0.588 | exp<=0 |
| NS3-FD | 15m asis | 339 | +0.083 | +0.016 | 0.73 (4.76) | +0.035 | -0.108 / +0.201 | 0.636 | t 0.73 < 4.756 |
| NS4-FD | 15m asis | 40 | +0.181 | +0.199 | 1.02 (4.76) | +0.205 | +0.334 / +0.151 | nan | t 1.02 < 4.756 |
| NS5-FD | 3m asis | 644 | -0.044 | +0.030 | -0.14 (4.76) | +0.011 | +0.172 / -0.096 | 0.647 | exp<=0 |
| MF1-FD | 15m asis | 190 | -0.051 | +0.064 | 0.01 (4.76) | +0.067 | -0.258 / +0.151 | 0.429 | t 0.01 < 4.758 |
| MF2-FD | 15m asis | 158 | -0.040 | +0.046 | -0.00 (4.76) | +0.102 | -0.189 / +0.115 | 0.6 | exp<=0 |
| MF3-FD | 10m asis | 268 | -0.020 | -0.024 | -0.35 (4.76) | +0.002 | -0.040 / +0.202 | 0.615 | exp<=0 |
| MF4-FD | 1m te | 547 | -0.041 | +0.020 | -0.37 (4.76) | +0.016 | -0.159 / +0.034 | 0.5 | exp<=0 |
| MF5-FD | 15m asis | 97 | -0.053 | +0.224 | 0.34 (4.76) | +0.065 | -0.201 / +0.180 | 0.0 | t 0.34 < 4.758 |
| heat_fade_short | 1m te | 2617 | +0.043 | +0.017 | 0.82 (4.78) | +0.047 | -0.128 / +0.117 | 0.412 | t 0.82 < 4.784 |
| heat_fade_long | 1m te | 794 | -0.060 | +0.030 | -0.26 (4.78) | +0.075 | +0.057 / -0.041 | 0.562 | exp<=0 |
| heat_fade_short-FD | 10m asis | 6971 | -0.013 | -0.021 | -0.90 (4.78) | +0.025 | -0.153 / +0.096 | 0.353 | exp<=0 |
| heat_fade_long-FD | 1m asis | 4213 | -0.009 | -0.025 | -0.68 (4.78) | +0.032 | +0.115 / -0.121 | 0.471 | exp<=0 |

## Full grid: n: exp_r train / valid, day-clustered t (core symbols, costs in)
| setup | 1m asis | 1m te | 3m asis | 3m te | 5m asis | 10m asis | 10m te | 15m asis | 15m te |
|---|---|---|---|---|---|---|---|---|---|
| NS1-FD | 1260: -0.03/-0.03, t -1.1 | 1 (n<30) | 480: +0.05/+0.03, t 1.1 | 88: -0.01/+0.07, t 0.2 | 232: +0.03/+0.00, t 0.3 | 116: -0.11/-0.04, t -1.1 | 757: +0.02/+0.01, t 0.5 | 55: -0.11/+0.01, t -0.5 | 635: -0.01/-0.01, t -0.4 |
| NS2-FD | 4486: -0.10/-0.04, t -2.9 | 249: -0.05/-0.16, t -1.1 | 1789: -0.04/-0.05, t -1.5 | 722: -0.10/-0.08, t -1.3 | 888: -0.04/-0.09, t -1.4 | 754: -0.18/-0.05, t -1.6 | 1156: -0.14/-0.07, t -2.3 | 795: -0.23/+0.06, t -1.2 | 1152: -0.02/-0.04, t -0.9 |
| NS3-FD | 2020: -0.10/+0.01, t -0.9 | 1186: -0.02/+0.00, t -0.2 | 1482: -0.04/-0.01, t -0.6 | 1116: +0.01/-0.02, t -0.2 | 1067: +0.02/-0.02, t -0.1 | 362: +0.02/+0.01, t 0.2 | 1002: +0.04/-0.02, t 0.1 | 339: +0.08/+0.02, t 0.7 | 938: +0.07/-0.05, t 0.0 |
| NS4-FD | 549: -0.08/-0.04, t -1.6 | 4 (n<30) | 250: +0.06/-0.03, t 0.1 | 83: -0.09/+0.01, t -0.5 | 154: -0.14/+0.15, t -0.1 | 70: -0.03/+0.04, t -0.3 | 253: -0.12/+0.04, t -1.1 | 40: +0.18/+0.20, t 1.0 | 246: -0.04/+0.05, t 0.1 |
| NS5-FD | 2005: -0.04/-0.00, t -0.7 | 6 (n<30) | 644: -0.04/+0.03, t -0.1 | 181: -0.08/-0.06, t -0.6 | 360: -0.02/-0.01, t -0.3 | 372: -0.27/-0.01, t -1.8 | 731: -0.10/+0.02, t -0.7 | 406: -0.01/-0.13, t -1.1 | 832: -0.10/-0.11, t -1.8 |
| MF1-FD | 1745: -0.09/-0.04, t -3.8 | 26 (n<30) | 693: -0.15/+0.02, t -2.5 | 176: -0.09/-0.06, t -1.2 | 443: -0.04/-0.08, t -1.4 | 259: -0.11/+0.06, t -0.8 | 1530: -0.09/-0.05, t -3.6 | 190: -0.05/+0.06, t 0.0 | 1164: -0.05/-0.06, t -2.2 |
| MF2-FD | 2644: -0.08/-0.04, t -3.4 | 89: -0.10/+0.03, t -0.8 | 717: -0.07/-0.05, t -1.6 | 358: -0.06/-0.04, t -1.3 | 425: -0.01/-0.04, t -0.4 | 241: -0.10/-0.06, t -1.6 | 546: -0.02/-0.02, t -0.3 | 158: -0.04/+0.05, t -0.0 | 256: -0.08/-0.09, t -1.6 |
| MF3-FD | 4721: -0.10/-0.07, t -4.6 | 23 (n<30) | 1178: -0.08/-0.05, t -2.2 | 298: -0.19/-0.06, t -2.9 | 579: -0.14/+0.01, t -1.9 | 268: -0.02/-0.02, t -0.3 | 1815: -0.09/-0.08, t -3.2 | 180: -0.07/-0.10, t -1.1 | 1248: -0.05/-0.05, t -1.6 |
| MF4-FD | 2029: -0.12/-0.01, t -4.1 | 547: -0.04/+0.02, t -0.4 | 685: -0.14/-0.05, t -3.5 | 464: -0.07/+0.01, t -0.7 | 488: -0.07/-0.05, t -1.9 | 466: -0.11/+0.03, t -1.0 | 1233: -0.07/-0.07, t -2.6 | 455: -0.10/-0.03, t -1.3 | 838: -0.04/-0.02, t -1.4 |
| MF5-FD | 1333: -0.13/-0.03, t -3.4 | 1 (n<30) | 472: -0.13/+0.03, t -1.3 | 94: -0.13/-0.03, t -1.0 | 269: -0.02/-0.08, t -0.8 | 135: -0.17/+0.06, t -0.9 | 1104: -0.09/-0.06, t -2.5 | 97: -0.05/+0.22, t 0.3 | 840: -0.04/-0.01, t -1.0 |
| heat_fade_short | 8108: -0.02/-0.01, t -0.4 | 2617: +0.04/+0.02, t 0.8 | 2724: +0.00/+0.00, t 0.1 | 2490: +0.05/-0.01, t 0.5 | 2554: +0.01/+0.04, t 0.7 | 2593: +0.03/-0.00, t 0.2 | 2809: -0.03/+0.02, t -0.1 | 2083: -0.02/-0.11, t -1.5 | 2430: -0.02/-0.07, t -1.3 |
| heat_fade_long | 2563: -0.02/-0.00, t -0.4 | 794: -0.06/+0.03, t -0.3 | 2215: -0.05/-0.00, t -0.7 | 1486: -0.07/-0.01, t -0.8 | 2128: +0.02/-0.04, t -0.4 | 1725: -0.11/-0.03, t -1.2 | 2586: -0.04/-0.06, t -1.1 | 1390: -0.06/-0.09, t -1.7 | 2684: -0.05/-0.08, t -1.6 |
| heat_fade_short-FD | 16700: -0.03/-0.03, t -1.5 | 9128: -0.04/-0.01, t -1.1 | 12891: -0.04/-0.04, t -2.0 | 10089: -0.04/-0.01, t -1.1 | 10520: -0.05/-0.01, t -1.4 | 6971: -0.01/-0.02, t -0.9 | 11264: -0.06/-0.03, t -2.4 | 4727: -0.01/-0.04, t -1.0 | 11089: -0.06/-0.04, t -2.8 |
| heat_fade_long-FD | 4213: -0.01/-0.03, t -0.7 | 1616: -0.04/-0.04, t -1.1 | 3778: -0.05/+0.01, t -0.7 | 2607: -0.03/-0.04, t -1.2 | 3355: -0.02/-0.03, t -0.9 | 2781: -0.07/-0.01, t -1.1 | 3883: -0.02/-0.04, t -1.2 | 2347: -0.03/-0.06, t -1.6 | 3933: -0.04/-0.02, t -1.1 |

## Lookbacks in clock time (as-is = bars x m; TE = same span as 5-min bars)
RSI14 as-is: 14 / 42 / 70 / 140 / 210 min on 1/3/5/10/15-min bars; SMA50: 50 / 150 / 250 / 500 / 750 min; buyPressure
19 bars; heat inner lookbacks (RSI14, momentum 4/9, EMA 9/21/12/26, volume 20, pricePosition 20) likewise. TE keeps the
5-min spans (RSI 70 min, SMA50 250 min, ...) via n -> max(2, round(n*5/m)); rsi5 becomes RSI(2) on 10/15-min bars.
On 1-min TE the long smooth indicators rarely reach the thresholds (NS1/NS5/MF5/MF3/MF1 fire 1-26 times in 2 years).

## Not tested (noted)
LIQ-orl-sweep-open15-s25-long, LIQ-pdl-sweep-open15-vwap-long: GEOM "S" price-level exits (+ BE/time stop), not in
the harness geometries, and defined on 15-min bars of the 09:30-10:00 range. orb20_a: class orb20, not a lab module.

## Caveats
- heat_fade_* are heat-type setups scored through a lab adapter (score past threshold; t1s1 = HeatStrategy's
  1R stop / 1R target, R = 0.25 ATR). 5-min numbers on the 80 core names, not the study's ~1,000-name population.
- TE indicators are computed with the locked block removed, so their warm-up spans the Oct-2024 -> Mar-2025 gap.
- Files: PLAN.md, run.py, te_build.py, results.csv (all 126 rows with every gate). Trades and TE columns were in the
  scratchpad and are deleted.
