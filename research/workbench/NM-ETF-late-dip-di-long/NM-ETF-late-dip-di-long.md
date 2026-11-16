# Workbench blueprint: Late-Day ETF Dip Buy (near-miss)

`NM-ETF-late-dip-di-long` - long - built 2026-11-16

> 14:00-15:00: buy a late-day dip in volatile ETFs with directional strength. Observation only.

## WHICH STOCKS

| Part | Exact value | Source / note |
|---|---|---|
| Liquidity floor (20-day avg $ volume) | `>= $95M` | setup min_adv |
| Account universe | `ADV >= $5M core, ATR >= 1.0%` | extended tier $1M with rvol >= 3.0x |
| Price floor | `>= $5.0` | costs.min_price |
| Earnings blackout | `4 trading days either side` | universe |
| Partnerships (PTP) | `excluded` | 10% withholding on sales |
| Allowed symbols | `module` | allow-list |

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
| Side | `LONG` | SIDE |
| 3-bar (15 min) return % | `ret3 <= -0.7977` | cond.ret3 |
| +DI(7) - -DI(7), in-day | `di_diff7 >= 0` | cond.di_diff7 |
| daily ATR % of price | `atr_d_pct >= 3.5968` | cond.atr_d_pct |
| Order | `enter at the close of the signal bar` | lab outcome model |

## RISK & EXIT

| Part | Exact value | Source / note |
|---|---|---|
| 1R (risk unit) | `0.25 x daily ATR` | r_atr_frac |
| Exit geometry | `t05s1: target +0.5R / stop 1R` | GEOM |
| Stop | `1.0R below entry` | bracket stop |
| Target | `+0.5R` | bracket target |
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
| Trades / sessions | `21 / 11` | 2026-10-19 to 2026-11-13 |
| Avg R after costs | `+0.311R` | total +6.5R, win 76% |
| Avg R w/o best day | `+0.281R` | best day 2026-11-05 = 22% of R |
| By account | `Primary 3 tr +0.22R, Testing A 10 tr +0.26R, Testing C 8 tr +0.41R` |  |
| Rule changes in window | `11 (listed in the markdown)` | latest: 2026-11-12: LR5: broker position vs journal lot check every ; 2026-11-12: LR7: closing flatten retries every 20 s until cl |

## MODULE

- file: `research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py` (parsed as: conds)
- module's own layer notes: ret3 <= -0.7977116525173187 (3-bar (15 min) return %); di_diff7 >= 0.0 (+DI(7) - -DI(7), in-day); atr_d_pct >= 3.5967583179473883 (daily ATR % of price); window: bar close 1400 <= tod < 1500 ET (hi >= 1500 includes 15:00) (YAML window [1400, 1500])

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-23: Owner replies: withdraw G1 (R1 yes: the 6 -g1 up-tape gated short variants are never added); no new daily stop for Primary (R2 yes: keep the -20R account stop and the -2R per-setup stop in the testing accounts; B1b not adopted)
- 2026-10-28: Owner: Primary position size ~$4,000 instead of ~$5,000 (slots 61 -> 77, max concurrent 61 -> 77; per-setup stays 30)
- 2026-10-28: Owner: Primary position size ~$5,000 (slots 160 -> 61, max concurrent 160 -> 61, per-setup 100 -> 30)
- 2026-10-29: Owner ST-P: per-setup daily stop at -2R (latched) in Primary only
- 2026-11-05: Owner ROLL1: Explore 1 + Live Lab go live 2026-11-05 as low-rep homes; 42 setups with < 20 live trades move there (21 each) from Testing 1 (12) and Testing 2 (30) (move)
- 2026-11-11: Owner TEAM yes: Primary runs TEAM-6 from 2026-11-11 to 2026-11-13, frozen (no rotation): NM-ETF-late-dip-di-long Live Lab -> Primary; MF2-FD, MF4-FD, L3-rsi5hi-FD Primary -> Testing 1; MF4 base, NS1 Primary -> Testing 2 (move)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR3: Primary's -20R account halt and -2R per-setup latch count R after costs; the account halt also counts open lots' marks (less a market-exit cost)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
- 2026-11-12: LR7: closing flatten retries every 20 s until close - 1 min, then an extended-hours close, alerts on failure; watchdog in act for Primary until calendar close + 5 min (also acts on flatten_failed / exposure after the flatten)

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `symbols` = `module`
- `min_adv` = `95000000`
- `window` = `[1400, 1500]`
- `scale_out_r` = `None`
- `refire` = `False`
- `refire_cooldown` = `1`
- `geom` = `t05s1`
- `r_atr_frac` = `0.25`
- `cond.ret3` = `-0.7977116525173187`
- `cond.di_diff7` = `0.0`
- `cond.atr_d_pct` = `3.5967583179473883`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $95M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/25 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Allowed symbols | `module` | - |
| P6 | TIMER | Entry window (5-min bar close) | `14:00-15:00 ET` | - |
| P7 | TIMER | Module's own window | `14:00-15:00 ET` | - |
| P8 | TIMER | No entries before | `09:50 ET` | - |
| P9 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P10 | SENSORS | 3-bar (15 min) return % | `ret3 <= -0.7977` | - |
| P11 | SENSORS | +DI(7) - -DI(7), in-day | `di_diff7 >= 0` | - |
| P12 | SENSORS | daily ATR % of price | `atr_d_pct >= 3.5968` | - |
| P13 | GATES | Open lots per setup | `30` | blocked 0/25 signals (0%) |
| P14 | GATES | Lots per symbol | `3 (same side)` | blocked 1/25 signals (4%) |
| P15 | GATES | Per-setup daily latch | `stops at -2R net` | blocked 0/25 signals (0%) |
| P16 | GATES | Account daily stop / halt | `-20R` | blocked 0/25 signals (0%) |
| P17 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 2/25 signals (8%) |
| P18 | ENTRY | Side + order | `LONG at market, signal-bar close` | - |
| P19 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P20 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$4,156)` | - |
| P21 | ENTRY | Max position | `10% of equity` | - |
| P22 | EXHAUST | Stop | `1.0R below entry` | ended 0/21 live trades (0%) |
| P23 | EXHAUST | Target | `+0.5R` | ended 15/21 live trades (71%) |
| P24 | EXHAUST | Scale-out | `none` | ended 0/21 live trades (0%) |
| P25 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 6/21 live trades (29%) |

Exit mix: {'time': 6, 'target': 15} of 21 live trades; blocked signals: {'quote': 2, 'other': 1, 'cap_symbol': 1} of 25 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### TECL 2026-11-04 (testing2 #8653): -0.56R, flatten

![](NM-ETF-late-dip-di-long_trade1_TECL_2026-11-04.png)

- **A** live signal at the 14:25 bar close inside the P6 window: P10-P12 all met
- **B** P18 long at market 14:25:59 @ 164.96 (5 sh, slip 8.5 bps); P19 1R = 4.03
- **C** best point (MFE) +0.12R at 15:21
- **D** worst point (MAE) -0.61R at 15:55
- **E** P25 15:55 time exit 15:55:51 @ 162.70: -0.56R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P10 | `ret3 <= -0.7977` | n/a | n/a | n/a |
| P11 | `di_diff7 >= 0` | n/a | n/a | n/a |
| P12 | `atr_d_pct >= 3.5968` | n/a | n/a | n/a |

### SOXL 2026-10-22 (testing2 #6096): -0.14R, flatten

![](NM-ETF-late-dip-di-long_trade2_SOXL_2026-10-22.png)

- **A** live signal at the 14:40 bar close inside the P6 window: P10-P12 all met
- **B** P18 long at market 14:43:31 @ 83.07 (10 sh, slip 13.3 bps); P19 1R = 3.30
- **C** best point (MFE) +0.17R at 15:30
- **D** worst point (MAE) -0.87R at 15:47
- **E** P25 15:55 time exit 15:55:53 @ 82.62: -0.14R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P10 | `ret3 <= -0.7977` | n/a | n/a | n/a |
| P11 | `di_diff7 >= 0` | n/a | n/a | n/a |
| P12 | `atr_d_pct >= 3.5968` | n/a | n/a | n/a |

### SOXL 2026-11-06 (livelab #94): -0.10R, flatten

![](NM-ETF-late-dip-di-long_trade3_SOXL_2026-11-06.png)

- **A** live signal at the 14:30 bar close inside the P6 window: P10-P12 all met
- **B** P18 long at market 14:31:57 @ 45.64 (21 sh, slip -32.1 bps); P19 1R = 3.29
- **C** best point (MFE) +0.30R at 15:13
- **D** worst point (MAE) -0.12R at 15:50
- **E** P25 15:55 time exit 15:55:57 @ 45.31: -0.10R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P10 | `ret3 <= -0.7977` | n/a | n/a | n/a |
| P11 | `di_diff7 >= 0` | n/a | n/a | n/a |
| P12 | `atr_d_pct >= 3.5968` | n/a | n/a | n/a |

### LABD 2026-11-13 (primary #5053): -0.07R, flatten

![](NM-ETF-late-dip-di-long_trade4_LABD_2026-11-13.png)

- **A** live signal at the 14:20 bar close inside the P6 window: P10-P12 all met
- **B** P18 long at market 14:20:48 @ 7.40 (469 sh, slip 2.0 bps); P19 1R = 0.18
- **C** best point (MFE) +0.16R at 14:47
- **D** worst point (MAE) -0.47R at 15:23
- **E** P25 15:55 time exit 15:55:44 @ 7.40: -0.07R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P10 | `ret3 <= -0.7977` | n/a | n/a | n/a |
| P11 | `di_diff7 >= 0` | n/a | n/a | n/a |
| P12 | `atr_d_pct >= 3.5968` | n/a | n/a | n/a |

### SOXL 2026-11-04 (testing2 #8652): -0.05R, flatten

![](NM-ETF-late-dip-di-long_trade5_SOXL_2026-11-04.png)

- **A** live signal at the 14:25 bar close inside the P6 window: P10-P12 all met
- **B** P18 long at market 14:25:56 @ 65.53 (13 sh, slip 16.0 bps); P19 1R = 3.37
- **C** best point (MFE) +0.13R at 14:27
- **D** worst point (MAE) -0.42R at 15:39
- **E** P25 15:55 time exit 15:55:52 @ 65.36: -0.05R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|
| P10 | `ret3 <= -0.7977` | n/a | n/a | n/a |
| P11 | `di_diff7 >= 0` | n/a | n/a | n/a |
| P12 | `atr_d_pct >= 3.5968` | n/a | n/a | n/a |


Observation only: the original setup is never edited. Educational only — not financial advice.
