# Workbench blueprint: RSI Collapse Dip Buy (all day)

`ST7-rsi50dn-long-pm-t1s1-FD` - long - built 2026-11-16

> 09:50-15:00: RSI(14) on 5-minute bars collapses from 50+ to 30 or less in one bar while the stock is more than 1% below its open and buyers still lead the last 19 bars. Buy; target 1R, stop 1R (R = 0.25 x daily ATR), flat 15:55.

## WHICH STOCKS

| Part | Exact value | Source / note |
|---|---|---|
| Liquidity floor (20-day avg $ volume) | `>= $95M` | setup min_adv |
| Account universe | `ADV >= $5M core, ATR >= 1.0%` | extended tier $1M with rvol >= 3.0x |
| Price floor | `>= $5.0` | costs.min_price |
| Earnings blackout | `4 trading days either side` | universe |
| Partnerships (PTP) | `excluded` | 10% withholding on sales |

## WHEN

| Part | Exact value | Source / note |
|---|---|---|
| Entry window (5-min bar close) | `09:50-15:00 ET` | window: [950, 1500] |
| No entries before | `09:50 ET` | live.no_entry_before |
| Flat by | `15:55 ET` | half days: close - 5 min |
| Refire | `first qualifying bar per symbol-day` | refire: false |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `LONG` | SIDE |
| RSI(14) crosses below 50 | `rsi50 dn` | cond.trigger |
| RSI(14) <= 30 | `rsi_ext 70` | cond.rsi_ext |
| stock down > 1.0% from the open | `fo_against 1` | cond.fo_against |
| 19-bar buy pressure > 0 | `bp_with on` | cond.bp_with |
| Order | `enter at the close of the signal bar` | lab outcome model |

## RISK & EXIT

| Part | Exact value | Source / note |
|---|---|---|
| 1R (risk unit) | `0.25 x daily ATR` | r_atr_frac |
| Exit geometry | `t1s1: target +1R / stop 1R` | GEOM |
| Stop | `1.0R below entry` | bracket stop |
| Target | `+1.0R` | bracket target |
| Scale-out | `none` | scale_out_r: null |
| Time exit | `flat at 15:55 ET` | session.flatten_by |

## LIMITS

| Part | Exact value | Source / note |
|---|---|---|
| Open lots per setup | `30` | max_positions_per_strategy |
| Per-setup daily latch | `stops at -2R net` | max_setup_daily_loss_r |
| Account daily stop | `-20R` | max_daily_loss_r |
| Lots per symbol | `3 (same side)` | same_setup_reentry: True |
| Spread / size checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | live |

## ACCOUNT & SIZING

| Part | Exact value | Source / note |
|---|---|---|
| Runs in | `Primary` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$4,156)` | 77 slots x 3.2 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `43 / 15` | 2026-10-12 to 2026-11-13 |
| Avg R after costs | `+0.150R` | total +6.4R, win 58% |
| Avg R w/o best day | `+0.061R` | best day 2026-10-12 = 63% of R (1 day) |
| By account | `Primary 27 tr +0.12R, On Deck 16 tr +0.20R` |  |
| Rule changes in window | `15 (listed in the markdown)` | latest: 2026-11-12: LR5: broker position vs journal lot check every ; 2026-11-12: LR7: closing flatten retries every 20 s until cl |

## MODULE

- file: `research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py` (parsed as: stack)
- module's own layer notes: RSI(14) crosses below 50; RSI(14) <= 30; stock down > 1.0% from the open; 19-bar buy pressure > 0; full day: bar close 09:50-15:00 ET (YAML window [950, 1500])

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-20: Risk: no lot on a symbol held by the setup's twin (X / X-FD, 'twin held'); per-setup daily loss limit -2R net ('setup daily loss limit') in Testing 1/2 and gen, account backstop 60 -> 120R there
- 2026-10-22: Testing 1: twin_group ST7-T1 for ST7Q (new) and its parent ST7-rsi50dn-long-pm-t1s1-FD (owner copy policy: the same signal is never traded twice)
- 2026-10-23: Owner S1: add ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD (RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day)) to Testing 1 as a NEW setup; parent ST7-rsi50dn-long-pm-t1s1-FD keeps running; new lab context column qqq_vwap
- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-23: Owner replies: withdraw G1 (R1 yes: the 6 -g1 up-tape gated short variants are never added); no new daily stop for Primary (R2 yes: keep the -20R account stop and the -2R per-setup stop in the testing accounts; B1b not adopted)
- 2026-10-26: Owner: promote ST7-rsi50dn-long-pm-t1s1-FD (RSI Collapse Dip Buy, all day) Testing 1 -> Primary (move)
- 2026-10-28: Owner: Primary position size ~$4,000 instead of ~$5,000 (slots 61 -> 77, max concurrent 61 -> 77; per-setup stays 30)
- 2026-10-28: Owner: Primary position size ~$5,000 (slots 160 -> 61, max concurrent 160 -> 61, per-setup 100 -> 30)
- 2026-10-29: Owner ST-P: per-setup daily stop at -2R (latched) in Primary only
- 2026-10-30: Owner CF: Testing 1/2 skip entries whose stop-exit round-trip cost > 0.15R (forward test of p3_1029 A3)
- 2026-10-30: Owner: promote L3-gap-slope-rsi5hi-FD (Gap-Down Rebound Overbought Short (all day)) Testing 2 -> Primary (move)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR3: Primary's -20R account halt and -2R per-setup latch count R after costs; the account halt also counts open lots' marks (less a market-exit cost)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
- 2026-11-12: LR7: closing flatten retries every 20 s until close - 1 min, then an extended-hours close, alerts on failure; watchdog in act for Primary until calendar close + 5 min (also acts on flatten_failed / exposure after the flatten)

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `min_adv` = `95000000`
- `window` = `[950, 1500]`
- `scale_out_r` = `None`
- `refire` = `False`
- `refire_cooldown` = `1`
- `geom` = `t1s1`
- `r_atr_frac` = `0.25`
- `cond.trigger` = `['rsi50', 'dn', None]`
- `cond.rsi_ext` = `70`
- `cond.fo_against` = `1.0`
- `cond.bp_with` = `None`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $95M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/73 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | TIMER | Entry window (5-min bar close) | `09:50-15:00 ET` | - |
| P6 | TIMER | No entries before | `09:50 ET` | - |
| P7 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P8 | SENSORS | Trigger: RSI(14) crosses below 50 | `rsi crosses below 50` | - |
| P9 | SENSORS | RSI(14) <= 30 | `rsi <= 30` | - |
| P10 | SENSORS | stock down > 1.0% from the open | `fromOpen < -1` | - |
| P11 | SENSORS | 19-bar buy pressure > 0 | `buyPressure > 0` | - |
| P12 | GATES | Open lots per setup | `30` | blocked 0/73 signals (0%) |
| P13 | GATES | Lots per symbol | `3 (same side)` | blocked 1/73 signals (1%) |
| P14 | GATES | Per-setup daily latch | `stops at -2R net` | blocked 0/73 signals (0%) |
| P15 | GATES | Account daily stop / halt | `-20R` | blocked 3/73 signals (4%) |
| P16 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 24/73 signals (33%) |
| P17 | ENTRY | Side + order | `LONG at market, signal-bar close` | - |
| P18 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P19 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$4,156)` | - |
| P20 | ENTRY | Max position | `10% of equity` | - |
| P21 | EXHAUST | Stop | `1.0R below entry` | ended 12/43 live trades (28%) |
| P22 | EXHAUST | Target | `+1.0R` | ended 18/43 live trades (42%) |
| P23 | EXHAUST | Scale-out | `none` | ended 0/43 live trades (0%) |
| P24 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 13/43 live trades (30%) |

Exit mix: {'target': 18, 'stop': 12, 'time': 13} of 43 live trades; blocked signals: {'quote': 24, 'acct_stop': 3, 'cap_symbol': 1} of 73 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### FNB 2026-11-04 (primary #1796): -1.33R, stop

![](ST7-rsi50dn-long-pm-t1s1-FD_trade1_FNB_2026-11-04.png)

- **A** live signal at the 10:45 bar close inside the P5 window: P8-P11 all met; last to turn true: P8 rsi crosses below 50, P9 rsi <= 30
- **B** P17 long at market 10:45:31 @ 18.50 (213 sh, slip 0.1 bps); P18 1R = 0.10
- **C** best point (MFE) +0.61R at 11:04
- **D** worst point (MAE) -0.82R at 11:31
- **E** P21 stop hit 11:31:41 @ 18.39: -1.33R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P8 | `rsi crosses below 50` | 58.755 | 20.872 | yes (flipped) |
| P9 | `rsi <= 30` | 58.755 | 20.872 | yes (flipped) |
| P10 | `fromOpen < -1` | -1.467 | -1.334 | yes |
| P11 | `buyPressure > 0` | 0.113 | 0.178 | yes |

### CSX 2026-10-29 (primary #1140): -1.25R, stop

![](ST7-rsi50dn-long-pm-t1s1-FD_trade2_CSX_2026-10-29.png)

- **A** live signal at the 10:45 bar close inside the P5 window: P8-P11 all met; last to turn true: P8 rsi crosses below 50, P9 rsi <= 30
- **B** P17 long at market 10:45:32 @ 52.05 (76 sh, slip 1.0 bps); P18 1R = 0.26
- **C** best point (MFE) +0.15R at 10:47
- **D** worst point (MAE) -1.36R at 11:08
- **E** P21 stop hit 11:08:22 @ 51.74: -1.25R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P8 | `rsi crosses below 50` | 50.529 | 21.739 | yes (flipped) |
| P9 | `rsi <= 30` | 50.529 | 21.739 | yes (flipped) |
| P10 | `fromOpen < -1` | -1.253 | -1.206 | yes |
| P11 | `buyPressure > 0` | 0.485 | 0.497 | yes |

### KEY 2026-11-04 (primary #1794): -1.20R, stop

![](ST7-rsi50dn-long-pm-t1s1-FD_trade3_KEY_2026-11-04.png)

- **A** live signal at the 10:45 bar close inside the P5 window: P8-P11 all met; last to turn true: P8 rsi crosses below 50, P9 rsi <= 30
- **B** P17 long at market 10:45:35 @ 21.45 (184 sh, slip -2.3 bps); P18 1R = 0.10
- **C** best point (MFE) +1.00R at 11:04
- **D** worst point (MAE) -1.05R at 11:24
- **E** P21 stop hit 11:24:40 @ 21.35: -1.20R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P8 | `rsi crosses below 50` | 56.329 | 23.333 | yes (flipped) |
| P9 | `rsi <= 30` | 56.329 | 23.333 | yes (flipped) |
| P10 | `fromOpen < -1` | -1.448 | -1.356 | yes |
| P11 | `buyPressure > 0` | 0.009 | 0.111 | yes |

### SMR 2026-10-21 (testing #5235): -1.19R, stop

![](ST7-rsi50dn-long-pm-t1s1-FD_trade4_SMR_2026-10-21.png)

- **A** live signal at the 13:50 bar close inside the P5 window: P8-P11 all met; last to turn true: P8 rsi crosses below 50, P9 rsi <= 30, P10 fromOpen < -1
- **B** P17 long at market 13:51:11 @ 5.61 (165 sh, slip 8.9 bps); P18 1R = 0.13
- **C** best point (MFE) +0.16R at 13:57
- **D** worst point (MAE) -1.11R at 15:09
- **E** P21 stop hit 15:09:16 @ 5.48: -1.19R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P8 | `rsi crosses below 50` | 60.904 | 30 | yes (flipped) |
| P9 | `rsi <= 30` | 60.904 | 30 | yes (flipped) |
| P10 | `fromOpen < -1` | -0.882 | -1.146 | yes (flipped) |
| P11 | `buyPressure > 0` | 0.099 | 0.107 | yes |

### Z 2026-10-21 (testing #5232): -1.12R, stop

![](ST7-rsi50dn-long-pm-t1s1-FD_trade5_Z_2026-10-21.png)

- **A** live signal at the 13:50 bar close inside the P5 window: P8-P11 all met; last to turn true: P8 rsi crosses below 50, P9 rsi <= 30
- **B** P17 long at market 13:51:18 @ 31.52 (29 sh, slip 9.5 bps); P18 1R = 0.36
- **C** best point (MFE) +0.21R at 14:34
- **D** worst point (MAE) -0.95R at 15:06
- **E** P21 stop hit 15:06:06 @ 31.14: -1.12R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P8 | `rsi crosses below 50` | 53.75 | 28.571 | yes (flipped) |
| P9 | `rsi <= 30` | 53.75 | 28.571 | yes (flipped) |
| P10 | `fromOpen < -1` | -2.173 | -2.266 | yes |
| P11 | `buyPressure > 0` | 0.427 | 0.378 | yes |


Observation only: the original setup is never edited. Educational only — not financial advice.
