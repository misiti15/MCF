# Workbench blueprint: Gap-Down Bounce Short, Heavy Selling (all day)

`RW1-gapdn-bounce-flowsell-short-FD` - short - built 2026-11-16

> 09:50-15:00: stock gapped down, bearish heat <= -20, heavy net selling, and RSI(14) bounces to 55-65; short the bounce.

## WHICH STOCKS

| Part | Exact value | Source / note |
|---|---|---|
| Liquidity floor (20-day avg $ volume) | `>= $95M` | setup min_adv |
| Account universe | `ADV >= $5M core, ATR >= 1.0%` | extended tier $1M with rvol >= 3.0x |
| Price floor | `>= $5.0` | costs.min_price |
| Earnings blackout | `4 trading days either side` | universe |
| Partnerships (PTP) | `excluded` | 10% withholding on sales |
| Short borrow | `shortable + easy to borrow only` | broker flags |

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
| Side | `SHORT` | SIDE |
| Module rule (as described) | `MarcoFlow heat <= -20 (bearish)` | LAYERS |
| Module rule (as described) | `buyPressure < -0.35 (heavy net selling, 19 bars)` | LAYERS |
| Module rule (as described) | `55 <= RSI(14) <= 65` | LAYERS |
| Module rule (as described) | `gapped down at the open` | LAYERS |
| Module rule (as described) | `full day: bar close 09:50-15:00 ET (YAML window [950, 1500])` | LAYERS |
| Order | `enter at the close of the signal bar` | lab outcome model |

## RISK & EXIT

| Part | Exact value | Source / note |
|---|---|---|
| 1R (risk unit) | `0.25 x daily ATR` | r_atr_frac |
| Exit geometry | `t1s1: target +1R / stop 1R` | GEOM |
| Stop | `1.0R above entry` | bracket stop |
| Target | `+1.0R` | bracket target |
| Scale-out | `none` | scale_out_r: null |
| Time exit | `flat at 15:55 ET` | session.flatten_by |

## LIMITS

| Part | Exact value | Source / note |
|---|---|---|
| Open lots per setup | `150` | max_positions_per_strategy |
| Per-setup daily latch | `off` | max_setup_daily_loss_r |
| Account daily stop | `-300R` | max_daily_loss_r |
| Lots per symbol | `3 (same side)` | same_setup_reentry: True |
| Cost filter | `skip if stop costs > 0.15R` | max_stop_cost_r |
| Spread / size checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | live |

## ACCOUNT & SIZING

| Part | Exact value | Source / note |
|---|---|---|
| Runs in | `On Deck` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$950)` | 400 slots x 3.8 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `143 / 25` | 2026-10-12 to 2026-11-16 |
| Avg R after costs | `+0.023R` | total +3.3R, win 52% |
| Avg R w/o best day | `-0.016R` | best day 2026-10-22 = 163% of R (1 day) |
| By account | `On Deck 63 tr -0.13R, Testing A 80 tr +0.14R` |  |
| Rule changes in window | `8 (listed in the markdown)` | latest: 2026-11-12: On Deck build (ONDECK): OD-IN / OD-OUT rules; 14; 2026-11-16: On Deck -> Testing F: RW7-gapdn-bounce-early-sho |

## MODULE

- file: `research/bdi/fullday/RW1-gapdn-bounce-flowsell-short-FD.py` (parsed as: mask)
- module's own layer notes: MarcoFlow heat <= -20 (bearish); buyPressure < -0.35 (heavy net selling, 19 bars); 55 <= RSI(14) <= 65; gapped down at the open; full day: bar close 09:50-15:00 ET (YAML window [950, 1500])

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-20: Risk: no lot on a symbol held by the setup's twin (X / X-FD, 'twin held'); per-setup daily loss limit -2R net ('setup daily loss limit') in Testing 1/2 and gen, account backstop 60 -> 120R there
- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-23: Owner replies: withdraw G1 (R1 yes: the 6 -g1 up-tape gated short variants are never added); no new daily stop for Primary (R2 yes: keep the -20R account stop and the -2R per-setup stop in the testing accounts; B1b not adopted)
- 2026-10-30: Owner CF: Testing 1/2 skip entries whose stop-exit round-trip cost > 0.15R (forward test of p3_1029 A3)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
- 2026-11-12: On Deck build (ONDECK): OD-IN / OD-OUT rules; 14 setups in On Deck (11 qualifiers - MF4 base + OD-FILL CWT05-m05-v5 + OD-P20 MF2-FD / MF4-FD / L3-rsi5hi-FD); 7 out to Testing E / F; MF5 and exhaustion_short-FD single home Testing A (move)
- 2026-11-16: On Deck -> Testing F: RW7-gapdn-bounce-early-short-FD (owner demote; Graveyard review after 3 sessions) (move)

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `min_adv` = `95000000`
- `window` = `[950, 1500]`
- `scale_out_r` = `None`
- `refire` = `False`
- `refire_cooldown` = `1`
- `geom` = `t1s1`
- `r_atr_frac` = `0.25`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $95M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/271 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 25/271 signals (9%) |
| P6 | TIMER | Entry window (5-min bar close) | `09:50-15:00 ET` | - |
| P7 | TIMER | No entries before | `09:50 ET` | - |
| P8 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P9 | SENSORS | Module rule (as described) | `MarcoFlow heat <= -20 (bearish)` | - |
| P10 | SENSORS | Module rule (as described) | `buyPressure < -0.35 (heavy net selling, 19 bars)` | - |
| P11 | SENSORS | Module rule (as described) | `55 <= RSI(14) <= 65` | - |
| P12 | SENSORS | Module rule (as described) | `gapped down at the open` | - |
| P13 | SENSORS | Module rule (as described) | `full day: bar close 09:50-15:00 ET (YAML window [950, 1500])` | - |
| P14 | GATES | Open lots per setup | `150` | blocked 0/271 signals (0%) |
| P15 | GATES | Lots per symbol | `3 (same side)` | blocked 16/271 signals (6%) |
| P16 | GATES | Per-setup daily latch | `off` | blocked 10/271 signals (4%) |
| P17 | GATES | Account daily stop / halt | `-300R` | blocked 0/271 signals (0%) |
| P18 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/271 signals (0%) |
| P19 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 41/271 signals (15%) |
| P20 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P21 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P22 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$950)` | - |
| P23 | ENTRY | Max position | `10% of equity` | - |
| P24 | EXHAUST | Stop | `1.0R above entry` | ended 44/143 live trades (31%) |
| P25 | EXHAUST | Target | `+1.0R` | ended 53/143 live trades (37%) |
| P26 | EXHAUST | Scale-out | `none` | ended 0/143 live trades (0%) |
| P27 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 46/143 live trades (32%) |

Exit mix: {'stop': 44, 'target': 53, 'time': 46} of 143 live trades; blocked signals: {'cap_symbol': 16, 'borrow': 25, 'quote': 41, 'other': 24, 'latch': 10} of 271 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### APH 2026-11-05 (testing2 #8883): +2.68R, target

![](RW1-gapdn-bounce-flowsell-short-FD_trade1_APH_2026-11-05.png)

- **A** live signal at the 11:35 bar close inside the P6 window: sensors all met
- **B** P20 short at market 11:35:29 @ 73.98 (12 sh, slip -61.9 bps); P21 1R = 0.54
- **C** best point (MFE) +2.87R at 12:00
- **D** worst point (MAE) -0.24R at 11:35
- **E** P25 target hit 12:00:10 @ 72.53: +2.68R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### PURR 2026-10-16 (testing #3498): +1.51R, target

![](RW1-gapdn-bounce-flowsell-short-FD_trade2_PURR_2026-10-16.png)

- **A** live signal at the 14:30 bar close inside the P6 window: sensors all met
- **B** P20 short at market 14:32:11 @ 9.22 (100 sh, slip -43.6 bps); P21 1R = 0.15
- **C** best point (MFE) +1.58R at 15:45
- **D** worst point (MAE) -0.16R at 14:32
- **E** P25 target hit 15:45:12 @ 8.99: +1.51R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### MAGS 2026-10-22 (testing2 #6009): +1.42R, target

![](RW1-gapdn-bounce-flowsell-short-FD_trade3_MAGS_2026-10-22.png)

- **A** live signal at the 11:55 bar close inside the P6 window: sensors all met
- **B** P20 short at market 11:57:41 @ 71.14 (12 sh, slip -7.0 bps); P21 1R = 0.25
- **C** best point (MFE) +1.42R at 12:39
- **D** worst point (MAE) -0.20R at 12:00
- **E** P25 target hit 12:39:48 @ 70.79: +1.42R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### LEVI 2026-10-28 (testing2 #7145): +1.39R, target

![](RW1-gapdn-bounce-flowsell-short-FD_trade4_LEVI_2026-10-28.png)

- **A** live signal at the 13:30 bar close inside the P6 window: sensors all met
- **B** P20 short at market 13:31:28 @ 21.56 (42 sh, slip -11.6 bps); P21 1R = 0.13
- **C** best point (MFE) +1.54R at 14:51
- **D** worst point (MAE) -0.50R at 14:00
- **E** P25 target hit 14:51:47 @ 21.38: +1.39R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### BAI 2026-11-05 (testing2 #9033): +1.21R, target

![](RW1-gapdn-bounce-flowsell-short-FD_trade5_BAI_2026-11-05.png)

- **A** live signal at the 12:10 bar close inside the P6 window: sensors all met
- **B** P20 short at market 12:10:34 @ 33.20 (27 sh, slip -12.1 bps); P21 1R = 0.41
- **C** best point (MFE) +1.28R at 15:55
- **D** worst point (MAE) -0.81R at 14:48
- **E** P25 target hit 15:55:12 @ 32.71: +1.21R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|


Observation only: the original setup is never edited. Educational only — not financial advice.
