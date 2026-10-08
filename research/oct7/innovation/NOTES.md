# BD innovation scan, 2026-10-08 (key: innovation)

*Educational only — not financial advice. Backtest (lab frame) results only; nothing here is live or paper evidence.*

**Data.** Train is 2026-07-15..08-25 (30 sessions). The lab train split starts 06-30, so the rows before 07-15 were dropped. Valid is 08-26..09-15 (14 sessions). The locked data (09-16..10-05 and cache_q2) was never read.

**Costs.** Lab costs are a flat 1c per side. `exp_r_prod` adds 1 bps per side and +2c on stop-outs.

**Entries.** Every configuration takes the first qualifying 5-minute bar per symbol-day, which is the production rule of LabStrategy. R = 0.25 × daily ATR, with a time exit at 15:55.

**Gate (declared before the scan).** All of the following, on train and valid:
- exp_r_prod > 0
- edge > 0 against the same-side, same-window all-bar baseline
- edge > 0 against the same-time control (all symbols' bars at the same date, time and side)
- day-clustered t ≥ 1.0
- valid ex-best-day > 0
- n ≥ 40 on train and n ≥ 30 on valid

## Configurations tried: 2,208
| stage | configs | gate passes |
|---|---|---|
| stage 1 scan (`scan.py`): families A–E | 1,821 (+6 parent/reference rows) | **0** |
| orb20_a "skip the extended opening swing" filter (`orb_swing_filter.py`, engine trades) | 8 | 0 |
| stage 2, add one condition (`stage2.py`): 7 families × top-3 train cores × 16 conditions | 336 | 3 |
| plateau and ablation (`plateau.py`) plus 2 hfl-PDL variants | 37 | (checks) |

At p = 0.05, about 110 false positives are expected from 2,208 configurations. The 3 stage-2 passes are within what chance alone would produce.

## Failures first
- **(a) Short-horizon RSI(2/3/4).**
  - **As a layer on the live setups: 45 configs, 0 pass.**
    - heat_fade_short with RSI(N) ≥ x: all 15 versions turn valid exp_r negative (parent +0.075R).
    - heat_fade_long with RSI(N) ≤ x: about no change.
    - exhaustion_short: a no-op, because RSI5 > 90 already implies a high RSI(3).
  - **As a primitive** (≥ 80/90/95 or ≤ 20/10/5, 5 windows, both sides, 3 geometries): **0 of 540 positive on both splits.**
  - The owner's ALAB "4-period RSI" idea is not supported. The autopsy also found RSI4 = 65 on ALAB, which would not have flagged it.
- **(b) Fading the extended opening swing (PENG/BKV read): 864 configs, 0 pass.**
  - The grid was T0 09:50/10:00/10:10, run ≥ 0.5–1.5 ATR, six stall rules, fade and follow, up and down.
  - **The direction of the owner's read holds.** Shorts after a big opening rip beat the same-time controls: median edge +0.027R on train and +0.067R on valid (t1s1). Longs that follow that rip, which is what orb20_a did, sit below the controls (−0.02/−0.06R).
  - Raw R is still negative on both splits, because the 10:00–11:30 short baseline is −0.03/−0.05R. So the read is right relative to the controls but is not tradeable after costs.
  - **As an orb20_a filter** ("skip an ORB trade in the direction of a ≥ k ATR opening run"): **all 8 versions fail.** Train loses $224–$1,056, because extended ORB longs made money on train. Valid gains +$73..+$146 on the long-only versions. This matches the autopsy's width and fromOpen filter results.
- **(c) Web ideas wi-*: 264 configs, 0 pass.**
  - Williams vol-breakout: 0/48 positive on both splits.
  - red-to-green: 0/36.
  - lunch reversal: 0/36.
  - overreaction fade: 3/72 positive on both, all with t < 1.
  - VWAP first pullback: 0/36.
  - EOD reversal (14:30–15:00 proxy; the frame ends at 15:00): 3/18 positive on both. The best is fo ≤ −5% long, valid ex-best +0.0006R with 99% from one day.
  - narrow-IB extension: 0/18.
  - Not tested: wi-same-halfhour, wi-vwap-trend-etf (needs ETF bars), wi-intraday-vcp, wi-ema-cross.
- **The owner's RIOT read** (short the bounce on a down day, 10:30–14:00, RSI3 ≥ 70–90, below VWAP): **0 of 81 pass**, and 1 is positive on both splits.

## Finalists (gate passes after plateau and ablation; none is proven)
**1. BD-gapdn-reclaim** (`BD-gapdn-reclaim.py`).
- **Rule:** short at 13:00–14:30 when gap ≤ −0.88% and the price is back above today's open. Geometry t1s1.
- **Results:**

  | split | n | exp_r_prod | day-clustered t | ex-best-day | same-time t |
  |---|---|---|---|---|---|
  | train | 4,512 | +0.066R | 1.26 | +0.027R | 3.18 |
  | valid | 2,365 | +0.196R | 1.20 | +0.157R | 1.86 |

- **Plateau:** all four gap and RSI neighbours pass, and 3 of the 4 window shifts pass. The t05s1 and t1s05 geometries do not pass.
- **Weaknesses:**
  - 90% of entries land on the 13:00 bar, so this is a state bet across the cross-section: about 120–140 names a day, all correlated.
  - The best train day is 64% of the train total.
  - With a realistic 20-per-day cap, t falls to 0.59 (train) and 1.16 (valid).
  - **Lineage:** P1-gap_* afternoon gap-down shorts failed both holdouts on look 1. This is look 2, so it needs t ≥ 1.5 on both holdouts.

**2. BD-gapdn-reclaim-rsi3** (`BD-gapdn-reclaim-rsi3.py`).
- **Rule:** the exact stage-2 winner, which is finalist 1 plus RSI(3) ≥ 70.

  | split | n | exp_r_prod | day-clustered t | ex-best-day |
  |---|---|---|---|---|
  | train | 4,152 | +0.072R | 1.57 | +0.013R |
  | valid | 2,104 | +0.159R | 1.13 | +0.125R |

- The best train day is 84% of the train total.
- The ablation shows the RSI layer adds nothing on valid. **Score only one of finalists 1 and 2.** A second one would be look 3, which needs t ≥ 2.0.

**3. BD-hfl-nearPDL** (`BD-hfl-nearPDL.py`).
- **Rule:** heat_fade_long, taken only when the close is below the prior-day low or within 0.25 ATR above it.

  | split | n | exp_r_prod | day-clustered t | ex-best-day |
  |---|---|---|---|---|
  | train | 1,128 | +0.109R | 1.14 | +0.078R |
  | valid | 365 | +0.075R | 2.05 | +0.049R |

- **Parent:** train +0.069R with t 0.57; valid +0.060R with t 1.83.
- **Neighbours:** PDL < 0 passes but is concentrated, with valid best day 92% of the total. PDL < 0.5 is positive with train t 0.82.
- **Lineage:** this is a rework of a live setup, the same lineage as the autopsy's hfl_deep4. The two overlap: 475 of these 1,128 train trades are also deep4 trades. **Only one of them should take the heat_fade_long look 2** (t ≥ 1.5 on both holdouts).
- The stage-2 version with RSI3 ≤ 50 is the same trade set; the RSI layer is a no-op.

**Deploy (only after the lead's holdout score, after hours, with a ledger entry).** Under `strategies:`:
- `type: lab`
- `module: research/oct7/innovation/<file>.py`
- `min_adv: 95000000`, or `125000000` for hfl
- `window: [1300, 1430]`, or `[1105, 1330]`
- `prefilter: "gap_le:-0.88"` for the gap modules

The modules work on the single-symbol production frame. `_bd_features.rsi` restarts each session; the lab starts at 09:50 and production at 09:35, which makes no difference by 13:00.
