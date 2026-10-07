# Layer-1 primitives: one metric at a time (key: `primitives`)

*Educational only - not financial advice. Backtest on the setup-lab frame. Nothing here has been tested live or scored on a locked holdout.*

## What was run
- **Data:** `research/setups2/data/{train,valid}.parquet` only. Train is 2026-06-30 to 08-25 (40 sessions, 3.08M bars). Valid is 08-26 to 09-15 (14 sessions, 1.08M bars). No locked data was read.
- **Metrics:** 29 continuous metrics, which include two derived ones that can still be deployed as masks:
  - `flowFlip` = flow3 - flow9prev
  - `dayRangePos` = position in the day's range from dist_hod/dist_lod
  
  Also 3 flags: vwapReclaim -1/0/1, bear_div, bull_div.
- **vol_climax:** it is identical to volumeRatio (max abs diff 0), so it was scanned once.
- **Bands:**
  - Train-quantile deciles D1-D10, plus the 5% tails V1/V20 and the 5-10% / 90-95% bands V2/V19.
  - The thresholds are fixed numbers, pooled over all windows, so they can be deployed.
  - Tied quantiles were merged.
- **Windows:** W1 09:50-10:30, W2 10:30-11:30, W3 11:30-13:00, W4 13:00-14:30, W5 14:30-15:00.
- **Sides, geometries and entries:** long and short, with exits t1s1, t05s1 and t1s05. Entry is the first qualifying bar per symbol-day in the window, the same as `setup_lab.evaluate`.
- **Configurations tried: 12,030.** At p = 0.05, roughly 600 would look "significant" by chance on any single test. The configurations are strongly correlated, so that count is only a rough guide.
- **Stats:**
  - Day-clustered t on exp_r.
  - Edge versus the same-side, same-window random baseline (mean R of every bar in the window).
  - Edge versus a time-of-day-matched baseline, its own t, ex-best-day, green-day share, and production-cost exp_r. Production cost is the lab cost plus 1 bps per side and +2c on stops. The extended-tier 3c slippage cannot be identified in the frame, so it is not included.
  - Plateau: the mean exp_r of the one-step neighbour bands. For flags it uses the adjacent windows instead. It must be above 0 on both train and valid.
- **Gate:** all of the following, as specified:
  - train exp_r > 0 and valid exp_r > 0
  - edge > 0 on train and on valid
  - valid n >= 30
  - valid day-clustered t >= 1.5
  - plateau > 0 on train and on valid
- **Survivor:** clears train and valid on exp_r and edge, with valid n >= 30. There are 131 survivors.

Files:
- `scan.py`: the scan.
- `report.py`: builds the map and the modules.
- `results.csv`: every configuration.
- `metric_map.json`: the full map plus bands and baselines.
- `METRIC_MAP.md`: the readable map, the finalists and all survivors.
- `verify_setup_lab.json`: every finalist module re-scored through `mcf.research.setup_lab.evaluate`. It reproduces n and exp_r exactly.
- Deployable modules: `research/primitives/P1-*.py`, each with SIDE, GEOM, LAYERS and mask(df).

## Failures first
- **No long primitive is a finalist.** Valid was a weak tape for longs, with a random long baseline of about -0.10R per trade in every window. Only 1 long survivor cleared both splits, and no long configuration reached train t >= 1.5.
- **Almost nothing is strong on train.** Only 0.2% of short configurations (and 0% of long) have train t >= 1.5. The only train t >= 1.5 cells are the gap-down shorts at 13:00-14:30.
- **The non-gap finalists are weak on train.**
  - `P1-dist_lod_atr_V20-short-W4-t1s1`: train +0.016R, t 0.35.
  - `P1-rsi_D7-short-W1-t1s1`: train +0.017R, t 0.49.
  - `P1-rsi_D8-short-W1-t1s1`: train +0.011R, t 0.27.
  - Their valid numbers ride the down-tape short drift. Their train halves show the decay: dist_lod is +0.109 / -0.083, and rsi_D7 is +0.045 / -0.009.
  - At production cost, the rsi finalists keep only +0.015R and +0.045R on valid. **These three should not be layered on their own merit.**
- **The gap family is not clean.**
  - Every gap finalist is **negative in the second half of train** (07-29 to 08-25), at -0.02 to -0.07R. All of the train edge comes from 06-30 to 07-28.
  - It only works in W4. The same gap-down short is negative on train in W3 (V1 -0.117R) and in W5 (V1 -0.026R).
  - Because gap is fixed per day, W4 always enters on the **13:00 bar**. This is in effect a fixed-time rule: "short every gap-down name at 13:00".
  - Valid has only 14 days, and green days are only 50-71%.

## Finalists (all 16; valid t ordered; R per trade; prod = valid at production costs)
| tag | rule | train exp_r (t) | valid n | valid exp_r | valid prod | valid t | ex-best-day | green days | plateau tr / va |
|---|---|---|---|---|---|---|---|---|---|
| P1-gap_V1-short-W4-t1s1 | gap <= -2.657%, 13:00-14:30 | +0.115 (1.98) | 751 | +0.247 | +0.223 | 2.86 | +0.191 | 57% | +0.056 / +0.170 |
| P1-gap_D2-short-W4-t1s1 | -1.657 < gap <= -0.881 | +0.049 (0.88) | 2130 | +0.158 | +0.121 | 2.59 | +0.134 | 71% | +0.065 / +0.168 |
| P1-gap_V1-short-W4-t1s05 | gap <= -2.657 | +0.064 (1.34) | 751 | +0.169 | +0.134 | 2.42 | +0.106 | 57% | +0.037 / +0.129 |
| P1-gap_D1-short-W4-t1s1 | gap <= -1.657 | +0.089 (1.56) | 1634 | +0.212 | +0.186 | 2.41 | +0.163 | 50% | +0.049 / +0.158 |
| P1-gap_V1-short-W4-t05s1 | gap <= -2.657 | +0.096 (1.80) | 751 | +0.129 | +0.106 | 2.34 | +0.115 | 57% | +0.030 / +0.092 |
| P1-dist_lod_atr_V20-short-W4-t1s1 | dist_lod_atr > 0.976 | +0.016 (0.35) | 1601 | +0.078 | +0.032 | 2.33 | +0.060 | 71% | +0.004 / +0.062 |
| P1-gap_D1-short-W4-t1s05 | gap <= -1.657 | +0.047 (1.09) | 1634 | +0.155 | +0.117 | 2.12 | +0.109 | 50% | +0.043 / +0.115 |
| P1-gap_D2-short-W4-t1s05 | -1.657 < gap <= -0.881 | +0.043 (1.05) | 2130 | +0.115 | +0.067 | 2.08 | +0.089 | 50% | +0.042 / +0.118 |
| P1-gap_V2-short-W4-t1s1 | -2.657 < gap <= -1.657 | +0.063 (1.07) | 883 | +0.183 | +0.154 | 1.97 | +0.119 | 50% | +0.082 / +0.202 |
| P1-rsi_D8-short-W1-t1s1 | 59.6 < rsi <= 65.3, 09:50-10:30 | +0.011 (0.27) | 4379 | +0.099 | +0.045 | 1.94 | +0.075 | 64% | +0.008 / +0.045 |
| P1-gap_D1-short-W4-t05s1 | gap <= -1.657 | +0.070 (1.43) | 1634 | +0.114 | +0.088 | 1.94 | +0.082 | 50% | +0.017 / +0.085 |
| P1-rsi_D7-short-W1-t1s1 | 54.7 < rsi <= 59.6, 09:50-10:30 | +0.017 (0.49) | 4645 | +0.068 | +0.016 | 1.82 | +0.052 | 71% | +0.008 / +0.055 |
| P1-gap_D2-short-W4-t05s1 | -1.657 < gap <= -0.881 | +0.017 (0.38) | 2130 | +0.085 | +0.049 | 1.79 | +0.063 | 64% | +0.036 / +0.083 |
| P1-gap_D3-short-W4-t1s1 | -0.881 < gap <= -0.445 | +0.041 (1.01) | 2340 | +0.123 | +0.079 | 1.77 | +0.091 | 64% | +0.027 / +0.083 |
| P1-gap_V2-short-W4-t1s05 | -2.657 < gap <= -1.657 | +0.031 (0.71) | 883 | +0.143 | +0.102 | 1.69 | +0.087 | 43% | +0.054 / +0.142 |
| P1-gap_V2-short-W4-t05s1 | -2.657 < gap <= -1.657 | +0.044 (0.94) | 883 | +0.100 | +0.072 | 1.61 | +0.063 | 57% | +0.038 / +0.107 |

All are in W4 (13:00-14:30), except the two rsi rows, which are in W1 (09:50-10:30).

**Mirror check (supports gap-down continuation):** the long side of the same gap bands is strongly negative on both splits. For example, gap V1 long in W4 is t -3.16 on train and -3.94 on valid. This matches the MarcoFlow lesson "short the drop, don't fade the rip". Gap-up names (D10/V20) show no short edge.

## What to layer (for the layering stage)
- **Base primitive:**
  - `P1-gap_V1-short-W4-t1s1`, or the broader `P1-gap_D1-short-W4-t1s1` for more trades.
  - The gap bands D1-D3 / V1-V2 form one family, not 9 independent finds. Pick one gap cut-off and do not stack them.
- **Second layers to try on top of gap-down at 13:00:**
  - short-side survivors that are also in W4: `dist_lod_atr` V20/D10 (well off the low of day, i.e. bounced), `vwapDistPct` V20/D10 (stretched above VWAP), `sma20_slope_pct` V20, `fromOpen` D9, `dist_pdl_atr` V1/D1 (below the prior-day low).
  - The aim is to filter out the train-half-2 losing days. A plausible reading: gap-downs that bounced into the afternoon fail.
- **W1 and W5 short survivors are weak on train, so use them as filters only, not bases:** rsi D7/D8, sma20_dist_pct D7-D9, dist_pdh_atr D2, pricePosition D6 (W1); emaDiff V19/V20/D10, vwapDistPct V20, sma50_dist_pct D10, macdPct V20 (W5).
- Any layered winner must still be scored once on the locked holdouts by the lead before it goes to paper, and it goes through `research/backlog.jsonl` (RESEARCH_RULES 2, 16).
