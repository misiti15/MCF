# Workbench blueprint: Monday Weak-RS NS3 Short (near-miss)

`NM-RWN5-ns3-mon-weakrs-short` - short - built 2026-11-16

> Mondays 09:50-11:30: failed VWAP reclaim on a stock weaker than SPY. Observation only.

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
| Entry window (5-min bar close) | `09:50-11:30 ET` | window: [950, 1130] |
| No entries before | `09:50 ET` | live.no_entry_before |
| Flat by | `15:55 ET` | half days: close - 5 min |
| Refire | `first qualifying bar per symbol-day` | refire: false |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `SHORT` | SIDE |
| Module rule (as described) | `close crosses above VWAP on this bar` | LAYERS |
| Module rule (as described) | `close above the 5-min SMA50` | LAYERS |
| Module rule (as described) | `stock down > 2% from the open` | LAYERS |
| Module rule (as described) | `Monday` | LAYERS |
| Module rule (as described) | `stock fromOpen below SPY fromOpen [live code needed]` | LAYERS |
| Module rule (as described) | `09:50-11:30 ET` | LAYERS |
| Market context columns | `spy_fo` | context |
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
| Trades / sessions | `8 / 3` | 2026-10-19 to 2026-11-16 |
| Avg R after costs | `+0.543R` | total +4.3R, win 88% |
| Avg R w/o best day | `+0.884R` | best day 2026-10-19 = 39% of R |
| By account | `Testing A 7 tr +0.48R, Testing D 1 tr +0.99R` |  |
| Rule changes in window | `6 (listed in the markdown)` | latest: 2026-11-12: LR5: broker position vs journal lot check every ; 2026-11-12: Testing D / E / F filled (10 setups each) and th |

## MODULE

- file: `research/swarm1017/rework-ns/modules/RWN5-ns3-mon-weakrs-short.py` (parsed as: mask)
- module's own layer notes: close crosses above VWAP on this bar; close above the 5-min SMA50; stock down > 2% from the open; Monday; stock fromOpen below SPY fromOpen [live code needed]; 09:50-11:30 ET

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-23: Owner replies: withdraw G1 (R1 yes: the 6 -g1 up-tape gated short variants are never added); no new daily stop for Primary (R2 yes: keep the -20R account stop and the -2R per-setup stop in the testing accounts; B1b not adopted)
- 2026-11-05: Owner ROLL1: Explore 1 + Live Lab go live 2026-11-05 as low-rep homes; 42 setups with < 20 live trades move there (21 each) from Testing 1 (12) and Testing 2 (30) (move)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
- 2026-11-12: Testing D / E / F filled (10 setups each) and the testing areas rebalanced: A 11 / B 11 / C 11 / D 10 / E 10 / F 10, by side and family, twins apart (move)

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `context` = `['spy_fo']`
- `min_adv` = `95000000`
- `window` = `[950, 1130]`
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
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/21 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 7/21 signals (33%) |
| P6 | TIMER | Entry window (5-min bar close) | `09:50-11:30 ET` | - |
| P7 | TIMER | No entries before | `09:50 ET` | - |
| P8 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P9 | SENSORS | Module rule (as described) | `close crosses above VWAP on this bar` | - |
| P10 | SENSORS | Module rule (as described) | `close above the 5-min SMA50` | - |
| P11 | SENSORS | Module rule (as described) | `stock down > 2% from the open` | - |
| P12 | SENSORS | Module rule (as described) | `Monday` | - |
| P13 | SENSORS | Module rule (as described) | `stock fromOpen below SPY fromOpen [live code needed]` | - |
| P14 | SENSORS | Module rule (as described) | `09:50-11:30 ET` | - |
| P15 | GATES | Market context columns | `spy_fo` | - |
| P16 | GATES | Open lots per setup | `50` | blocked 0/21 signals (0%) |
| P17 | GATES | Lots per symbol | `3 (same side)` | blocked 0/21 signals (0%) |
| P18 | GATES | Per-setup daily latch | `off` | blocked 0/21 signals (0%) |
| P19 | GATES | Account daily stop / halt | `-300R` | blocked 0/21 signals (0%) |
| P20 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/21 signals (0%) |
| P21 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 5/21 signals (24%) |
| P22 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P23 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P24 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | - |
| P25 | ENTRY | Max position | `10% of equity` | - |
| P26 | EXHAUST | Stop | `1.0R above entry` | ended 1/8 live trades (12%) |
| P27 | EXHAUST | Target | `+1.0R` | ended 5/8 live trades (62%) |
| P28 | EXHAUST | Scale-out | `none` | ended 0/8 live trades (0%) |
| P29 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 2/8 live trades (25%) |

Exit mix: {'stop': 1, 'target': 5, 'time': 2} of 8 live trades; blocked signals: {'quote': 5, 'borrow': 7, 'other': 1} of 21 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### LITE 2026-10-19 (testing2 #5241): -1.11R, stop

![](NM-RWN5-ns3-mon-weakrs-short_trade1_LITE_2026-10-19.png)

- **A** live signal at the 10:20 bar close inside the P6 window: sensors all met
- **B** P22 short at market 10:24:41 @ 852.47 (1 sh, slip -8.7 bps); P23 1R = 18.06
- **C** best point (MFE) +0.19R at 10:39
- **D** worst point (MAE) -1.08R at 11:31
- **E** P26 stop hit 11:31:00 @ 872.45: -1.11R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### ARM 2026-10-19 (testing2 #5357): +0.53R, flatten

![](NM-RWN5-ns3-mon-weakrs-short_trade2_ARM_2026-10-19.png)

- **A** live signal at the 11:05 bar close inside the P6 window: sensors all met
- **B** P22 short at market 11:06:01 @ 232.59 (3 sh, slip -9.7 bps); P23 1R = 3.73
- **C** best point (MFE) +0.84R at 14:35
- **D** worst point (MAE) -0.54R at 11:37
- **E** P29 15:55 time exit 15:55:34 @ 230.62: +0.53R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### CIFR 2026-10-19 (testing2 #5310): +0.72R, target

![](NM-RWN5-ns3-mon-weakrs-short_trade3_CIFR_2026-10-19.png)

- **A** live signal at the 10:00 bar close inside the P6 window: sensors all met
- **B** P22 short at market 10:01:47 @ 9.19 (98 sh, slip 52.2 bps); P23 1R = 0.34
- **C** best point (MFE) +0.72R at 14:08
- **D** worst point (MAE) -0.62R at 10:45
- **E** P27 target hit 14:08:13 @ 8.95: +0.72R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### CRCL 2026-10-19 (testing2 #5319): +0.77R, target

![](NM-RWN5-ns3-mon-weakrs-short_trade4_CRCL_2026-10-19.png)

- **A** live signal at the 11:05 bar close inside the P6 window: sensors all met
- **B** P22 short at market 11:06:44 @ 82.67 (10 sh, slip 22.8 bps); P23 1R = 1.54
- **C** best point (MFE) +0.67R at 14:27
- **D** worst point (MAE) -0.45R at 11:29
- **E** P27 target hit 14:27:55 @ 81.48: +0.77R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|


Observation only: the original setup is never edited. Educational only — not financial advice.
