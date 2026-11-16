# Workbench blueprint: Generated: Lunch New-Low Short (selling)

`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` - short - built 2026-11-16

> Short on the first 5-minute bar closing 11:30-14:00 ET where the share of stocks above their open is above 0.5; bar made a new low of day = 1; signed volume share, 3 bars (frame column) <= -0.37; close - open in daily ATRs <= -0.78 (stocks with 20-day average dollar volume >= $150M). Exit stop 1R, no target, 1R trailing stop once +1R, flat 15:55, R = 0.25 x daily ATR. Machine-generated for exploration; not a tested edge.

## WHICH STOCKS

| Part | Exact value | Source / note |
|---|---|---|
| Liquidity floor (20-day avg $ volume) | `>= $150M` | setup min_adv |
| Account universe | `ADV >= $5M core, ATR >= 1.0%` | extended tier $1M with rvol >= 3.0x |
| Price floor | `>= $5.0` | costs.min_price |
| Earnings blackout | `4 trading days either side` | universe |
| Partnerships (PTP) | `excluded` | 10% withholding on sales |
| Short borrow | `shortable + easy to borrow only` | broker flags |

## WHEN

| Part | Exact value | Source / note |
|---|---|---|
| Entry window (5-min bar close) | `11:30-14:00 ET` | window: [1130, 1400] |
| Module's own window | `11:30-14:00 ET` | WINDOW constant |
| No entries before | `09:50 ET` | live.no_entry_before |
| Flat by | `15:55 ET` | half days: close - 5 min |
| Refire | `first qualifying bar per symbol-day` | refire: false |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `SHORT` | SIDE |
| share of stocks above their open | `breadth_open > 0.5` | cond.breadth_open |
| signed volume share, 3 bars | `flow3 <= -0.37` | cond.flow3 |
| close - open in daily ATRs | `fromOpen_atr <= -0.78` | cond.fromOpen_atr |
| bar made a new low of day | `new_lod == 1` | cond.new_lod |
| Market context columns | `breadth_open` | context |
| Order | `enter at the close of the signal bar` | lab outcome model |

## RISK & EXIT

| Part | Exact value | Source / note |
|---|---|---|
| 1R (risk unit) | `0.25 x daily ATR` | r_atr_frac |
| Exit geometry | `holdtr: stop 1R, no target, 1R trailing stop once +1R` | GEOM |
| Stop | `1.0R above entry` | bracket stop |
| Target | `none (stop / trail / flat)` | bracket target |
| Scale-out | `none` | scale_out_r: null |
| Time exit | `flat at 15:55 ET` | session.flatten_by |

## LIMITS

| Part | Exact value | Source / note |
|---|---|---|
| Open lots per setup | `50` | max_positions_per_strategy |
| Per-setup daily latch | `off` | max_setup_daily_loss_r |
| Account daily stop | `-300R` | max_daily_loss_r |
| Lots per symbol | `3 (same side)` | same_setup_reentry: True |
| Cost filter | `skip if stop costs > 0.15R` | max_stop_cost_r |
| Spread / size checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | live |

## ACCOUNT & SIZING

| Part | Exact value | Source / note |
|---|---|---|
| Runs in | `Testing D` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | 200 slots x 2.0 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `21 / 5` | 2026-10-26 to 2026-11-03 |
| Avg R after costs | `+0.379R` | total +8.0R, win 67% |
| Avg R w/o best day | `+0.129R` | best day 2026-10-27 = 77% of R (1 day) |
| Rule changes in window | `1 (listed in the markdown)` | latest: 2026-10-26: Owner GX2: Setup Generator account caps 80 -> 20 |

## NAME CODE (Setup Generator id)

| Token | Meaning |
|---|---|
| `261026-03` | generated 2026-10-26, spec #03 of that run |
| `NewLOD` | bar made a new low of day = 1 |
| `Flow3lem0p37` | signed volume share, 3 bars (frame column) <= -0.37 |
| `FromOpenATRlem0p78` | close - open in daily ATRs <= -0.78 |
| `LUNCH` | time window 11:30-14:00 ET |
| `BRopgt0p5` | the share of stocks above their open is above 0.5 |
| `holdtr` | stop 1R, no target, 1R trailing stop once +1R, flat 15:55 |
| `short` | side short |

## MODULE

- file: `research/generator/modules/GEN-261026-03-newlod-lunch-short.py` (parsed as: conds)
- module's own layer notes: breadth_open > 0.5; flow3 <= -0.37; fromOpen_atr <= -0.78; new_lod == 1; window 1130-1400

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-26: Owner GX2: Setup Generator account caps 80 -> 200 slots / concurrent positions, 16 -> 48 per setup

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `context` = `['breadth_open']`
- `min_adv` = `150000000`
- `window` = `[1130, 1400]`
- `refire` = `False`
- `scale_out_r` = `None`
- `refire_cooldown` = `1`
- `geom` = `holdtr`
- `r_atr_frac` = `0.25`
- `cond.breadth_open` = `0.5`
- `cond.flow3` = `-0.37`
- `cond.fromOpen_atr` = `-0.78`
- `cond.new_lod` = `1.0`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $150M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/41 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 7/41 signals (17%) |
| P6 | TIMER | Entry window (5-min bar close) | `11:30-14:00 ET` | - |
| P7 | TIMER | Module's own window | `11:30-14:00 ET` | - |
| P8 | TIMER | No entries before | `09:50 ET` | - |
| P9 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P10 | SENSORS | signed volume share, 3 bars | `flow3 <= -0.37` | - |
| P11 | SENSORS | close - open in daily ATRs | `fromOpen_atr <= -0.78` | - |
| P12 | SENSORS | bar made a new low of day | `new_lod == 1` | - |
| P13 | GATES | share of stocks above their open | `breadth_open > 0.5` | - |
| P14 | GATES | Market context columns | `breadth_open` | - |
| P15 | GATES | Open lots per setup | `50` | blocked 0/41 signals (0%) |
| P16 | GATES | Lots per symbol | `3 (same side)` | blocked 0/41 signals (0%) |
| P17 | GATES | Per-setup daily latch | `off` | blocked 0/41 signals (0%) |
| P18 | GATES | Account daily stop / halt | `-300R` | blocked 8/41 signals (20%) |
| P19 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/41 signals (0%) |
| P20 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 4/41 signals (10%) |
| P21 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P22 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P23 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | - |
| P24 | ENTRY | Max position | `10% of equity` | - |
| P25 | EXHAUST | Stop | `1.0R above entry` | ended 6/21 live trades (29%) |
| P26 | EXHAUST | Target | `none (stop / trail / flat)` | ended 0/21 live trades (0%) |
| P27 | EXHAUST | Scale-out | `none` | ended 0/21 live trades (0%) |
| P28 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 15/21 live trades (71%) |

Exit mix: {'stop': 6, 'time': 15} of 21 live trades; blocked signals: {'borrow': 7, 'quote': 4, 'acct_stop': 8} of 41 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### JD 2026-11-03 (gen #1557): -1.14R, stop

![](GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short_trade1_JD_2026-11-03.png)

- **A** live signal at the 12:00 bar close inside the P6 window: P13-P12 all met
- **B** P21 short at market 12:00:56 @ 26.92 (66 sh, slip 1.9 bps); P22 1R = 0.14
- **C** best point (MFE) +0.04R at 12:00
- **D** worst point (MAE) -1.00R at 13:34
- **E** P25 stop hit 13:34:29 @ 27.06: -1.14R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P13 | `breadth_open > 0.5` | n/a | n/a | n/a |
| P10 | `flow3 <= -0.37` | -0.681 | -1 | yes |
| P11 | `fromOpen_atr <= -0.78` | n/a | n/a | n/a |
| P12 | `new_lod == 1` | n/a | n/a | n/a |

### FISV 2026-10-26 (gen #101): -1.13R, stop

![](GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short_trade2_FISV_2026-10-26.png)

- **A** live signal at the 13:45 bar close inside the P6 window: P13-P12 all met
- **B** P21 short at market 13:45:45 @ 47.95 (39 sh, slip 7.3 bps); P22 1R = 0.33
- **C** best point (MFE) +0.12R at 13:47
- **D** worst point (MAE) -1.16R at 14:14
- **E** P25 stop hit 14:14:27 @ 48.30: -1.13R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P13 | `breadth_open > 0.5` | n/a | n/a | n/a |
| P10 | `flow3 <= -0.37` | -1 | -1 | yes |
| P11 | `fromOpen_atr <= -0.78` | n/a | n/a | n/a |
| P12 | `new_lod == 1` | n/a | n/a | n/a |

### CCEP 2026-10-29 (gen #445): -1.12R, stop

![](GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short_trade3_CCEP_2026-10-29.png)

- **A** live signal at the 11:55 bar close inside the P6 window: P13-P12 all met
- **B** P21 short at market 11:55:45 @ 109.76 (17 sh, slip 2.7 bps); P22 1R = 0.59
- **C** best point (MFE) +0.19R at 11:57
- **D** worst point (MAE) -1.08R at 12:49
- **E** P25 stop hit 12:49:42 @ 110.40: -1.12R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P13 | `breadth_open > 0.5` | n/a | n/a | n/a |
| P10 | `flow3 <= -0.37` | -0.696 | -0.676 | yes |
| P11 | `fromOpen_atr <= -0.78` | n/a | n/a | n/a |
| P12 | `new_lod == 1` | n/a | n/a | n/a |

### TOST 2026-10-26 (gen #114): -0.86R, flatten

![](GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short_trade4_TOST_2026-10-26.png)

- **A** live signal at the 12:30 bar close inside the P6 window: P13-P12 all met
- **B** P21 short at market 12:30:53 @ 31.81 (60 sh, slip 0.0 bps); P22 1R = 0.28
- **C** best point (MFE) +0.25R at 12:52
- **D** worst point (MAE) -0.96R at 15:38
- **E** P28 15:55 time exit 15:55:31 @ 32.05: -0.86R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P13 | `breadth_open > 0.5` | n/a | n/a | n/a |
| P10 | `flow3 <= -0.37` | -0.377 | -0.463 | yes |
| P11 | `fromOpen_atr <= -0.78` | n/a | n/a | n/a |
| P12 | `new_lod == 1` | n/a | n/a | n/a |

### CAVA 2026-10-26 (gen #106): -0.27R, stop

![](GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short_trade5_CAVA_2026-10-26.png)

- **A** live signal at the 12:30 bar close inside the P6 window: P13-P12 all met; last to turn true: P10 flow3 <= -0.37
- **B** P21 short at market 12:30:31 @ 50.77 (37 sh, slip 27.5 bps); P22 1R = 0.72
- **C** best point (MFE) +0.61R at 14:28
- **D** worst point (MAE) -0.28R at 15:30
- **E** P25 stop hit 15:30:22 @ 50.94: -0.27R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P13 | `breadth_open > 0.5` | n/a | n/a | n/a |
| P10 | `flow3 <= -0.37` | -0.146 | -0.547 | yes (flipped) |
| P11 | `fromOpen_atr <= -0.78` | n/a | n/a | n/a |
| P12 | `new_lod == 1` | n/a | n/a | n/a |


Observation only: the original setup is never edited. Educational only — not financial advice.
