# Spread calibration from Alpaca SIP NBBO (swarm1010 W5)

*Educational only - not financial advice.*

**Question (owner):** does the production cost model (mcf/research/gates.py `prod_r`, config/default.yaml `costs`:
1c + 1 bps per side, target exits free, +2c on stops) hold in the 09:30-09:50 open window, and anywhere else?

**Data:** Alpaca SIP historical quotes (`/v2/stocks/quotes`, our paid plan). Every symbol MCF filled on the paper
account 2026-10-06..09 (133 symbols, all universe tier `core`) on the 5 sessions 2026-10-05..09. Sample times:
every minute 09:30-10:30 ET and every 5 minutes 10:35-15:55, each the last valid quote (bid > 0, ask > bid) in the
3 s before hh:mm:05. Plus the NBBO at submit and at fill for all 306 paper fills. 630 sample-time requests + 612
fill requests, ~4 minutes. Scripts: `pull_orders.py`, `pull_nbbo.py`, `fill_quotes.py`, `spread_calibration.py`
(this file's tables are its output). Raw: `data/nbbo_sample.parquet` (67,144 rows), `data/fill_quotes.parquet`.
Configurations tried: none (measurement, no setup scored; nothing selected).

## Answer in one paragraph

In R units (what the gates use), **the model is right from 10:30 to the close** (median quoted round-trip spread
0.057 R vs model 0.061 R; means 0.074 vs 0.074). **It is too cheap in the open window**: quoted spread is
**3.8x the model in 09:30-09:34, 2.1x in 09:35-09:49 and 1.4x in 09:50-10:29**. Per symbol-day, the median
spread in 09:30-09:49 is **2.4x** that symbol's own 10:30-15:30 median (p75 3.2x, p90 4.2x; 09:30-09:34 alone 4.0x).
For a setup trading at 09:35-09:49 that is roughly **0.06 R per trade of cost the scans do not charge** (0.16 R in
09:30-09:34, 0.02 R in 09:50-10:29) - a large share of the edges being screened for (the trend-guard near miss is +0.26 R after costs on the 2-year history). Paper fills
confirm the simulator crosses the quoted spread: market orders paid +$0.073/sh vs mid on average against a mean
half-spread of $0.075 (model $0.025/sh: in dollars the model is ~3x low on our >$150 names, but those names have
proportionally larger ATR so in R it washes out after 10:30). Stop fills slipped a median $0.02 but mean $0.12/sh
past the stop (p90 $0.23) vs the model's 1c + 1 bps + 2c = $0.049 mean - a fat tail worth its own check.

## Proposed cost-model change (backlog `sw-w5-cost-tod-multiplier`, not applied)

Multiply the per-side slippage (1c + 1 bps) by a time-of-day factor at the fill time:
`m = 3.8 (09:30-09:34), 2.1 (09:35-09:49), 1.4 (09:50-10:29), 1.0 (10:30-close)` (from table 6, median spread/R
divided by model/R). This is a research-rules change (costs), so it goes through the backlog/ledger, and it should be
re-measured on a larger NBBO sample first (20+ sessions, the whole lab universe, not only names we traded) - the pull
is cheap (one multi-symbol request per sample time, ~1 s each). Effect to expect: open-window finalists lose
~0.06-0.16 R per trade; full-day (09:50+) setups barely move. Caveats: quoted, not effective spread (our 1-200 share
orders fit at the touch, so quoted is the right first-order cost); 5 sessions in one week (VIX ~15, calm); last-quote
snapshots at :05 s; paper fills are simulated by Alpaca against the NBBO and do not show real market impact.

## Tables (output of spread_calibration.py)

Sample: 133 symbols x 5 sessions (2026-10-05..2026-10-09), 67,144 symbol-time NBBO snapshots (last valid quote in the 3 s before each sample time).

### 1. Quoted spread by time of day (all symbols pooled)

| bucket | n | median spread bps | mean spread bps | median half-spread / model per-side | share half-spread > model | p90 half/model |
|---|---|---|---|---|---|---|
| 09:30 | 638 | 33.0 | 48.2 | 6.47 | 86% | 24.34 |
| 09:31-09:34 | 2016 | 19.8 | 29.0 | 3.87 | 78% | 16.05 |
| 09:35-09:39 | 2731 | 13.8 | 20.4 | 2.55 | 71% | 12.30 |
| 09:40-09:49 | 5620 | 11.5 | 16.9 | 2.09 | 69% | 10.10 |
| 09:50-09:59 | 5535 | 9.6 | 13.5 | 1.62 | 64% | 8.08 |
| 10:00-10:29 | 16594 | 8.1 | 11.4 | 1.29 | 58% | 7.07 |
| 10:30-11:59 | 9487 | 6.5 | 8.6 | 0.96 | 49% | 5.18 |
| 12:00-13:59 | 11940 | 5.8 | 7.6 | 0.81 | 44% | 4.38 |
| 14:00-15:29 | 9018 | 5.4 | 6.8 | 0.74 | 40% | 3.83 |
| 15:30-15:55 | 3565 | 5.4 | 7.0 | 0.71 | 39% | 4.11 |

### 2. Open-window spread multiplier (per symbol-day median spread in window / median 10:30-15:30)

| window | symbol-days | median multiplier | mean | p75 | p90 |
|---|---|---|---|---|---|
| 09:30-09:34 | 661 | 3.95 | 4.93 | 6.00 | 9.00 |
| 09:35-09:49 | 665 | 2.14 | 2.33 | 2.94 | 3.70 |
| 09:30-09:49 (open window) | 665 | 2.42 | 2.61 | 3.17 | 4.16 |
| 09:50-10:29 | 665 | 1.45 | 1.53 | 1.90 | 2.26 |
| 15:30-15:55 | 665 | 0.88 | 0.86 | 1.00 | 1.07 |

### 3. By price band: median half-spread / model per-side cost

| price band | symbols | 09:30-09:49 | 09:50-10:29 | 10:30-15:29 | open-window multiplier (median) |
|---|---|---|---|---|---|
| <$20 | 25 | 0.84 | 0.45 | 0.44 | 2.00 |
| $20-50 | 24 | 1.93 | 1.12 | 0.72 | 2.58 |
| $50-150 | 46 | 2.49 | 1.42 | 0.89 | 2.50 |
| $150-400 | 37 | 6.14 | 3.71 | 1.98 | 2.62 |
| >$400 | 11 | 7.33 | 4.89 | 2.95 | 2.12 |

### 4. Per-side cost implied by the quoted half-spread (mean over snapshots, $/share and bps)

| window | mean half-spread $ | median half-spread $ | mean half-spread bps | model mean per-side $ |
|---|---|---|---|---|
| 09:30-09:49 | 0.1887 | 0.0450 | 10.89 | 0.0272 |
| 09:50-10:29 | 0.1085 | 0.0250 | 5.95 | 0.0268 |
| 10:30-15:29 | 0.0674 | 0.0150 | 3.85 | 0.0265 |
| 15:30-15:55 | 0.0652 | 0.0150 | 3.52 | 0.0270 |

Widest names vs model mid-day (median half-spread / model): SITM 14.5, HUM 9.5, ONTO 7.9, ILMN 7.6, MXL 6.7, ALAB 6.7, MCK 6.6, SMTC 6.5, NET 6.0, FICO 5.9

### 5. Paper fills vs SIP NBBO (Alpaca paper account, 2026-10-06..09)

Paper fills are simulated by Alpaca against the NBBO, so this checks the simulator, not real market impact.

| order type | n | median $ vs mid at submit | mean $ vs mid at submit | mean half-spread at submit | mean model per-side | mean $ vs mid at fill |
|---|---|---|---|---|---|---|
| market | 179 | 0.0200 | 0.0726 | 0.0749 | 0.0248 | 0.0744 |
| stop | 61 | 0.0300 | 0.1216 | 0.1357 | 0.0285 | 0.1516 |
| limit (targets: vs mid at submit is meaningless, they rest away from the market) | 66 | -0.4266 | -1.0174 | 0.0955 | 0.0264 | 0.0879 |

Stop fills vs stop price: n 61, median 0.0200 $/sh, mean 0.1214, p90 0.2300 (model: 1c + 1 bps + 2c stop extra = mean 0.0485).
Market fills 09:50-16:00: n 179, mean $ vs mid at submit 0.0726, mean half-spread 0.0749, model 0.0248

### 6. In R units (R = 0.25 x 20-day daily ATR): round-trip cost of crossing the quoted spread twice vs model

Round trip = entry + exit, both marketable (the model's worst case: a non-target exit; stop extra not included).

| window | symbol-snapshots | median spread / R (= 2 half-spreads) | mean spread / R | median model 2-side / R | mean model 2-side / R |
|---|---|---|---|---|---|
| 09:30-09:34 | 2629 | 0.219 | 0.330 | 0.057 | 0.073 |
| 09:35-09:49 | 8276 | 0.120 | 0.170 | 0.057 | 0.073 |
| 09:50-10:29 | 21929 | 0.080 | 0.114 | 0.058 | 0.075 |
| 10:30-15:29 | 30145 | 0.057 | 0.074 | 0.061 | 0.074 |
| 15:30-15:55 | 3535 | 0.049 | 0.065 | 0.057 | 0.072 |
