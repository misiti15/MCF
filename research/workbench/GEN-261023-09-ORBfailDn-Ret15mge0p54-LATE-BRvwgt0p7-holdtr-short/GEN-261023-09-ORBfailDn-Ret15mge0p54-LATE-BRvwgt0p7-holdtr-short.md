# Workbench blueprint: Generated: Late Failed-Breakdown Pop Short

`GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short` - short - built 2026-11-16

> Short on the first 5-minute bar closing 14:00-15:00 ET where the share of stocks above their VWAP is above 0.7; closed below the OR low earlier today, now back above = 1; 3-bar (15 min) return % >= 0.54 (stocks with 20-day average dollar volume >= $150M). Exit stop 1R, no target, 1R trailing stop once +1R, flat 15:55, R = 0.25 x daily ATR. Machine-generated for exploration; not a tested edge.

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
| Entry window (5-min bar close) | `14:00-15:00 ET` | window: [1400, 1500] |
| Module's own window | `14:00-15:00 ET` | WINDOW constant |
| No entries before | `09:50 ET` | live.no_entry_before |
| Flat by | `15:55 ET` | half days: close - 5 min |
| Refire | `first qualifying bar per symbol-day` | refire: false |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `SHORT` | SIDE |
| share of stocks above their VWAP | `breadth > 0.7` | cond.breadth |
| closed below the OR low earlier today, now back above | `orb_fail_dn == 1` | cond.orb_fail_dn |
| 3-bar (15 min) return % | `ret3 >= 0.54` | cond.ret3 |
| Market context columns | `breadth` | context |
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
| Runs in | `Testing E` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | 200 slots x 2.0 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `10 / 1` | 2026-11-09 to 2026-11-09 |
| Avg R after costs | `+0.393R` | total +3.9R, win 60% |
| Avg R w/o best day | `n/a` | best day 2026-11-09 = 100% of R (1 day) |

## NAME CODE (Setup Generator id)

| Token | Meaning |
|---|---|
| `261023-09` | generated 2026-10-23, spec #09 of that run |
| `ORBfailDn` | closed below the OR low earlier today, now back above = 1 |
| `Ret15mge0p54` | 3-bar (15 min) return % >= 0.54 |
| `LATE` | time window 14:00-15:00 ET |
| `BRvwgt0p7` | the share of stocks above their VWAP is above 0.7 |
| `holdtr` | stop 1R, no target, 1R trailing stop once +1R, flat 15:55 |
| `short` | side short |

## MODULE

- file: `research/generator/modules/GEN-261023-09-orbfaildn-late-short.py` (parsed as: conds)
- module's own layer notes: breadth > 0.7; orb_fail_dn == 1; ret3 >= 0.54; window 1400-1500

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `context` = `['breadth']`
- `min_adv` = `150000000`
- `window` = `[1400, 1500]`
- `refire` = `False`
- `scale_out_r` = `None`
- `refire_cooldown` = `1`
- `geom` = `holdtr`
- `r_atr_frac` = `0.25`
- `cond.breadth` = `0.7`
- `cond.orb_fail_dn` = `1.0`
- `cond.ret3` = `0.54`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $150M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/28 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 4/28 signals (14%) |
| P6 | TIMER | Entry window (5-min bar close) | `14:00-15:00 ET` | - |
| P7 | TIMER | Module's own window | `14:00-15:00 ET` | - |
| P8 | TIMER | No entries before | `09:50 ET` | - |
| P9 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P10 | SENSORS | closed below the OR low earlier today, now back above | `orb_fail_dn == 1` | - |
| P11 | SENSORS | 3-bar (15 min) return % | `ret3 >= 0.54` | - |
| P12 | GATES | share of stocks above their VWAP | `breadth > 0.7` | - |
| P13 | GATES | Market context columns | `breadth` | - |
| P14 | GATES | Open lots per setup | `50` | blocked 0/28 signals (0%) |
| P15 | GATES | Lots per symbol | `3 (same side)` | blocked 4/28 signals (14%) |
| P16 | GATES | Per-setup daily latch | `off` | blocked 0/28 signals (0%) |
| P17 | GATES | Account daily stop / halt | `-300R` | blocked 0/28 signals (0%) |
| P18 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/28 signals (0%) |
| P19 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 0/28 signals (0%) |
| P20 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P21 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P22 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$1,000)` | - |
| P23 | ENTRY | Max position | `10% of equity` | - |
| P24 | EXHAUST | Stop | `1.0R above entry` | ended 3/10 live trades (30%) |
| P25 | EXHAUST | Target | `none (stop / trail / flat)` | ended 0/10 live trades (0%) |
| P26 | EXHAUST | Scale-out | `none` | ended 0/10 live trades (0%) |
| P27 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 7/10 live trades (70%) |

Exit mix: {'stop': 3, 'time': 7} of 10 live trades; blocked signals: {'borrow': 4, 'cap_symbol': 4} of 28 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### IAU 2026-11-09 (gen #5680): -1.15R, stop

![](GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_trade1_IAU_2026-11-09.png)

- **A** live signal at the 14:40 bar close inside the P6 window: P12-P11 all met
- **B** P20 short at market 14:42:28 @ 77.72 (22 sh, slip -19.5 bps); P21 1R = 0.19
- **C** best point (MFE) +1.11R at 14:47
- **D** worst point (MAE) -1.05R at 15:22
- **E** P24 stop hit 15:22:37 @ 77.92: -1.15R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P12 | `breadth > 0.7` | n/a | n/a | n/a |
| P10 | `orb_fail_dn == 1` | n/a | n/a | n/a |
| P11 | `ret3 >= 0.54` | n/a | n/a | n/a |

### GLDM 2026-11-09 (gen #5679): -1.14R, stop

![](GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_trade2_GLDM_2026-11-09.png)

- **A** live signal at the 14:40 bar close inside the P6 window: P12-P11 all met
- **B** P20 short at market 14:42:15 @ 81.79 (21 sh, slip -15.9 bps); P21 1R = 0.23
- **C** best point (MFE) +0.88R at 14:54
- **D** worst point (MAE) -1.01R at 15:15
- **E** P24 stop hit 15:22:48 @ 82.03: -1.14R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P12 | `breadth > 0.7` | n/a | n/a | n/a |
| P10 | `orb_fail_dn == 1` | n/a | n/a | n/a |
| P11 | `ret3 >= 0.54` | n/a | n/a | n/a |

### GLD 2026-11-09 (gen #5678): -1.05R, stop

![](GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_trade3_GLD_2026-11-09.png)

- **A** live signal at the 14:40 bar close inside the P6 window: P12-P11 all met
- **B** P20 short at market 14:42:17 @ 379.00 (4 sh, slip -17.3 bps); P21 1R = 1.02
- **C** best point (MFE) +0.97R at 14:54
- **D** worst point (MAE) -1.05R at 15:22
- **E** P24 stop hit 15:22:41 @ 380.05: -1.05R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P12 | `breadth > 0.7` | n/a | n/a | n/a |
| P10 | `orb_fail_dn == 1` | n/a | n/a | n/a |
| P11 | `ret3 >= 0.54` | n/a | n/a | n/a |

### PATH 2026-11-09 (gen #5836): -0.17R, flatten

![](GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_trade4_PATH_2026-11-09.png)

- **A** live signal at the 14:40 bar close inside the P6 window: P12-P11 all met
- **B** P20 short at market 14:43:19 @ 12.96 (133 sh, slip 31.6 bps); P21 1R = 0.17
- **C** best point (MFE) +0.12R at 14:50
- **D** worst point (MAE) -0.81R at 15:15
- **E** P27 15:55 time exit 15:57:36 @ 12.99: -0.17R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P12 | `breadth > 0.7` | n/a | n/a | n/a |
| P10 | `orb_fail_dn == 1` | n/a | n/a | n/a |
| P11 | `ret3 >= 0.54` | n/a | n/a | n/a |

### UNG 2026-11-09 (gen #5818): +0.11R, flatten

![](GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short_trade5_UNG_2026-11-09.png)

- **A** live signal at the 14:25 bar close inside the P6 window: P12-P11 all met
- **B** P20 short at market 14:27:59 @ 10.10 (171 sh, slip 14.8 bps); P21 1R = 0.09
- **C** best point (MFE) +0.52R at 14:39
- **D** worst point (MAE) -0.43R at 14:28
- **E** P27 15:55 time exit 15:57:54 @ 10.09: +0.11R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P12 | `breadth > 0.7` | n/a | n/a | n/a |
| P10 | `orb_fail_dn == 1` | n/a | n/a | n/a |
| P11 | `ret3 >= 0.54` | n/a | n/a | n/a |


Observation only: the original setup is never edited. Educational only — not financial advice.
