# Workbench blueprint: Gap-Down Early Bounce Short (all day)

`RW7-gapdn-bounce-early-short-FD` - short - built 2026-11-16

> 09:50-15:00: stock gapped down, bearish heat <= -20, net selling (lighter than RW1), and RSI(14) bounces to 55-65; short the bounce.

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
| Module rule (as described) | `buyPressure < -0.15 (net selling)` | LAYERS |
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
| Open lots per setup | `30` | max_positions_per_strategy |
| Per-setup daily latch | `off` | max_setup_daily_loss_r |
| Account daily stop | `-300R` | max_daily_loss_r |
| Lots per symbol | `3 (same side)` | same_setup_reentry: True |
| Cost filter | `skip if stop costs > 0.15R` | max_stop_cost_r |
| Spread / size checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | live |

## ACCOUNT & SIZING

| Part | Exact value | Source / note |
|---|---|---|
| Runs in | `Testing F` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | 200 slots x 2.0 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `585 / 24` | 2026-10-12 to 2026-11-16 |
| Avg R after costs | `-0.003R` | total -1.7R, win 51% |
| Avg R w/o best day | `-0.030R` |  |
| By account | `On Deck 567 tr -0.02R, Testing F 18 tr +0.57R` |  |
| Rule changes in window | `6 (listed in the markdown)` | latest: 2026-11-12: LR5: broker position vs journal lot check every ; 2026-11-16: On Deck -> Testing F: RW7-gapdn-bounce-early-sho |

## MODULE

- file: `research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py` (parsed as: mask)
- module's own layer notes: MarcoFlow heat <= -20 (bearish); buyPressure < -0.15 (net selling); 55 <= RSI(14) <= 65; gapped down at the open; full day: bar close 09:50-15:00 ET (YAML window [950, 1500])

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-20: Risk: no lot on a symbol held by the setup's twin (X / X-FD, 'twin held'); per-setup daily loss limit -2R net ('setup daily loss limit') in Testing 1/2 and gen, account backstop 60 -> 120R there
- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-30: Owner CF: Testing 1/2 skip entries whose stop-exit round-trip cost > 0.15R (forward test of p3_1029 A3)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
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
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 1/1306 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 104/1306 signals (8%) |
| P6 | TIMER | Entry window (5-min bar close) | `09:50-15:00 ET` | - |
| P7 | TIMER | No entries before | `09:50 ET` | - |
| P8 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P9 | SENSORS | Module rule (as described) | `MarcoFlow heat <= -20 (bearish)` | - |
| P10 | SENSORS | Module rule (as described) | `buyPressure < -0.15 (net selling)` | - |
| P11 | SENSORS | Module rule (as described) | `55 <= RSI(14) <= 65` | - |
| P12 | SENSORS | Module rule (as described) | `gapped down at the open` | - |
| P13 | SENSORS | Module rule (as described) | `full day: bar close 09:50-15:00 ET (YAML window [950, 1500])` | - |
| P14 | GATES | Open lots per setup | `30` | blocked 45/1306 signals (3%) |
| P15 | GATES | Lots per symbol | `3 (same side)` | blocked 38/1306 signals (3%) |
| P16 | GATES | Per-setup daily latch | `off` | blocked 105/1306 signals (8%) |
| P17 | GATES | Account daily stop / halt | `-300R` | blocked 5/1306 signals (0%) |
| P18 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/1306 signals (0%) |
| P19 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 101/1306 signals (8%) |
| P20 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P21 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P22 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | - |
| P23 | ENTRY | Max position | `10% of equity` | - |
| P24 | EXHAUST | Stop | `1.0R above entry` | ended 152/585 live trades (26%) |
| P25 | EXHAUST | Target | `+1.0R` | ended 187/585 live trades (32%) |
| P26 | EXHAUST | Scale-out | `none` | ended 0/585 live trades (0%) |
| P27 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 246/585 live trades (42%) |

Exit mix: {'stop': 152, 'target': 187, 'time': 246} of 585 live trades; blocked signals: {'cap_symbol': 38, 'other': 97, 'borrow': 104, 'quote': 101, 'acct_stop': 5, 'split_gate': 195, 'latch': 105, 'cap_setup': 45, 'price': 1} of 1306 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### TTD 2026-10-14 (testing #1145): -1.40R, stop

![](RW7-gapdn-bounce-early-short-FD_trade1_TTD_2026-10-14.png)

- **A** live signal at the 12:25 bar close inside the P6 window: sensors all met
- **B** P20 short at market 12:26:47 @ 11.79 (79 sh, slip 8.5 bps); P21 1R = 0.11
- **C** best point (MFE) +0.00R at 12:26
- **D** worst point (MAE) -1.41R at 12:44
- **E** P24 stop hit 12:44:15 @ 11.92: -1.40R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### PFGC 2026-10-28 (testing #6663): -1.36R, stop

![](RW7-gapdn-bounce-early-short-FD_trade2_PFGC_2026-10-28.png)

- **A** live signal at the 10:45 bar close inside the P6 window: sensors all met
- **B** P20 short at market 10:45:45 @ 96.33 (9 sh, slip 14.5 bps); P21 1R = 0.71
- **C** best point (MFE) +0.07R at 10:47
- **D** worst point (MAE) -1.23R at 11:22
- **E** P24 stop hit 11:22:58 @ 97.28: -1.36R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### PDBC 2026-10-26 (testing #6007): -1.36R, stop

![](RW7-gapdn-bounce-early-short-FD_trade3_PDBC_2026-10-26.png)

- **A** live signal at the 11:20 bar close inside the P6 window: sensors all met
- **B** P20 short at market 11:20:50 @ 20.18 (45 sh, slip -7.4 bps); P21 1R = 0.05
- **C** best point (MFE) +0.19R at 11:21
- **D** worst point (MAE) -0.87R at 11:44
- **E** P24 stop hit 11:44:06 @ 20.23: -1.36R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### WDAY 2026-10-27 (testing #6372): -1.32R, stop

![](RW7-gapdn-bounce-early-short-FD_trade4_WDAY_2026-10-27.png)

- **A** live signal at the 10:55 bar close inside the P6 window: sensors all met
- **B** P20 short at market 10:55:54 @ 205.97 (4 sh, slip -14.3 bps); P21 1R = 1.40
- **C** best point (MFE) +0.11R at 10:55
- **D** worst point (MAE) -0.69R at 11:16
- **E** P24 stop hit 11:16:35 @ 207.80: -1.32R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### LHX 2026-11-05 (testing #8216): -1.32R, stop

![](RW7-gapdn-bounce-early-short-FD_trade5_LHX_2026-11-05.png)

- **A** live signal at the 13:55 bar close inside the P6 window: sensors all met
- **B** P20 short at market 13:55:40 @ 255.58 (3 sh, slip 5.7 bps); P21 1R = 2.14
- **C** best point (MFE) +0.30R at 14:05
- **D** worst point (MAE) -1.11R at 14:28
- **E** P24 stop hit 14:28:29 @ 258.38: -1.32R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|


Observation only: the original setup is never edited. Educational only — not financial advice.
