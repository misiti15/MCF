# Workbench blueprint: Gap-Down VWAP Loss Short (10% gap)

`CWT09-gapdn-vwaploss-g10-short` - short - built 2026-11-16

> 10:30-15:00: a stock that gapped down 10%+ (no earnings within 4 days) traded back above VWAP during 09:35-10:30; from 10:30 the first close back below VWAP; short, stop at the 09:30-10:30 high, hold to 15:55.

## WHICH STOCKS

| Part | Exact value | Source / note |
|---|---|---|
| Liquidity floor (20-day avg $ volume) | `>= $1M` | setup min_adv |
| Account universe | `ADV >= $5M core, ATR >= 1.0%` | extended tier $1M with rvol >= 3.0x |
| Price floor | `>= $5.0` | costs.min_price |
| Earnings blackout | `4 trading days either side` | universe |
| Partnerships (PTP) | `excluded` | 10% withholding on sales |
| Short borrow | `shortable + easy to borrow only` | broker flags |

## WHEN

| Part | Exact value | Source / note |
|---|---|---|
| Entry window (5-min bar close) | `10:30-15:00 ET` | window: [1030, 1500] |
| No entries before | `09:50 ET` | live.no_entry_before |
| Flat by | `15:55 ET` | half days: close - 5 min |
| Refire | `first qualifying bar per symbol-day` | refire: false |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `SHORT` | SIDE |
| Module rule (as described) | `A7 gap<=-10 E=out T1 S guest` | LAYERS |
| Order | `enter at the close of the signal bar` | lab outcome model |

## RISK & EXIT

| Part | Exact value | Source / note |
|---|---|---|
| 1R (risk unit) | `0.25 x daily ATR` | r_atr_frac |
| Exit geometry | `S: structural stop (module stop_price), no fixed target` | GEOM |
| Target | `none (stop / trail / flat)` | bracket target |
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
| Trades / sessions | `18 / 11` | 2026-10-13 to 2026-11-13 |
| Avg R after costs | `+0.301R` | total +5.4R, win 83% |
| Avg R w/o best day | `+0.215R` | best day 2026-10-30 = 48% of R |
| By account | `On Deck 2 tr +0.08R, Testing A 12 tr +0.40R, Testing C 4 tr +0.13R` |  |
| Rule changes in window | `9 (listed in the markdown)` | latest: 2026-11-12: LR5: broker position vs journal lot check every ; 2026-11-12: On Deck build (ONDECK): OD-IN / OD-OUT rules; 14 |

## MODULE

- file: `research/bdi/cwt/live/CWT09-gapdn-vwaploss-g10-short.py` (parsed as: mask)
- module's own layer notes: A7 gap<=-10 E=out T1 S guest

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-20: Risk: no lot on a symbol held by the setup's twin (X / X-FD, 'twin held'); per-setup daily loss limit -2R net ('setup daily loss limit') in Testing 1/2 and gen, account backstop 60 -> 120R there
- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-23: Owner replies: withdraw G1 (R1 yes: the 6 -g1 up-tape gated short variants are never added); no new daily stop for Primary (R2 yes: keep the -20R account stop and the -2R per-setup stop in the testing accounts; B1b not adopted)
- 2026-10-30: Owner CF: Testing 1/2 skip entries whose stop-exit round-trip cost > 0.15R (forward test of p3_1029 A3)
- 2026-11-05: Owner ROLL1: Explore 1 + Live Lab go live 2026-11-05 as low-rep homes; 42 setups with < 20 live trades move there (21 each) from Testing 1 (12) and Testing 2 (30) (move)
- 2026-11-11: Owner TEAM yes: Primary runs TEAM-6 from 2026-11-11 to 2026-11-13, frozen (no rotation): NM-ETF-late-dip-di-long Live Lab -> Primary; MF2-FD, MF4-FD, L3-rsi5hi-FD Primary -> Testing 1; MF4 base, NS1 Primary -> Testing 2 (move)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed
- 2026-11-12: On Deck build (ONDECK): OD-IN / OD-OUT rules; 14 setups in On Deck (11 qualifiers - MF4 base + OD-FILL CWT05-m05-v5 + OD-P20 MF2-FD / MF4-FD / L3-rsi5hi-FD); 7 out to Testing E / F; MF5 and exhaustion_short-FD single home Testing A (move)

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `min_adv` = `1000000`
- `window` = `[1030, 1500]`
- `scale_out_r` = `None`
- `refire` = `False`
- `refire_cooldown` = `1`
- `geom` = `S`
- `r_atr_frac` = `0.25`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $1M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 1/319 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 284/319 signals (89%) |
| P6 | TIMER | Entry window (5-min bar close) | `10:30-15:00 ET` | - |
| P7 | TIMER | No entries before | `09:50 ET` | - |
| P8 | TIMER | Refire | `first qualifying bar per symbol-day` | - |
| P9 | SENSORS | Module rule (as described) | `A7 gap<=-10 E=out T1 S guest` | - |
| P10 | GATES | Open lots per setup | `150` | blocked 0/319 signals (0%) |
| P11 | GATES | Lots per symbol | `3 (same side)` | blocked 0/319 signals (0%) |
| P12 | GATES | Per-setup daily latch | `off` | blocked 0/319 signals (0%) |
| P13 | GATES | Account daily stop / halt | `-300R` | blocked 1/319 signals (0%) |
| P14 | GATES | Cost filter | `skip if stop costs > 0.15R` | blocked 0/319 signals (0%) |
| P15 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 10/319 signals (3%) |
| P16 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P17 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P18 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$950)` | - |
| P19 | ENTRY | Max position | `10% of equity` | - |
| P20 | EXHAUST | Target | `none (stop / trail / flat)` | ended 0/18 live trades (0%) |
| P21 | EXHAUST | Scale-out | `none` | ended 0/18 live trades (0%) |
| P22 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 16/18 live trades (89%) |

Exit mix: {'time': 16, 'stop': 2} of 18 live trades; blocked signals: {'borrow': 284, 'quote': 10, 'acct_stop': 1, 'price': 1, 'other': 1} of 319 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### ARCO 2026-10-26 (testing2 #6554): +1.31R, flatten

![](CWT09-gapdn-vwaploss-g10-short_trade1_ARCO_2026-10-26.png)

- **A** live signal at the 11:00 bar close inside the P6 window: sensors all met
- **B** P16 short at market 11:00:50 @ 7.29 (125 sh, slip 6.9 bps); P17 1R = 0.16
- **C** best point (MFE) +1.34R at 15:54
- **D** worst point (MAE) -0.41R at 11:06
- **E** P22 15:55 time exit 15:55:33 @ 7.08: +1.31R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### DELL 2026-10-30 (testing2 #7842): +0.97R, flatten

![](CWT09-gapdn-vwaploss-g10-short_trade2_DELL_2026-10-30.png)

- **A** live signal at the 10:30 bar close inside the P6 window: sensors all met
- **B** P16 short at market 10:30:53 @ 431.50 (2 sh, slip 17.6 bps); P17 1R = 9.58
- **C** best point (MFE) +1.91R at 13:33
- **D** worst point (MAE) -0.53R at 10:41
- **E** P22 15:55 time exit 15:55:53 @ 422.19: +0.97R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### CLSK 2026-11-04 (testing2 #8640): +0.91R, flatten

![](CWT09-gapdn-vwaploss-g10-short_trade3_CLSK_2026-11-04.png)

- **A** live signal at the 10:30 bar close inside the P6 window: sensors all met
- **B** P16 short at market 10:30:39 @ 7.14 (126 sh, slip -7.0 bps); P17 1R = 0.41
- **C** best point (MFE) +1.19R at 11:35
- **D** worst point (MAE) -0.27R at 10:36
- **E** P22 15:55 time exit 15:55:47 @ 6.77: +0.91R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### TECL 2026-10-30 (testing2 #7845): +0.88R, flatten

![](CWT09-gapdn-vwaploss-g10-short_trade4_TECL_2026-10-30.png)

- **A** live signal at the 10:30 bar close inside the P6 window: sensors all met
- **B** P16 short at market 10:31:59 @ 177.19 (5 sh, slip -25.6 bps); P17 1R = 4.81
- **C** best point (MFE) +2.55R at 14:35
- **D** worst point (MAE) -0.74R at 10:41
- **E** P22 15:55 time exit 15:55:55 @ 172.96: +0.88R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### SOXL 2026-11-05 (livelab #18): +0.69R, flatten

![](CWT09-gapdn-vwaploss-g10-short_trade5_SOXL_2026-11-05.png)

- **A** live signal at the 10:30 bar close inside the P6 window: sensors all met
- **B** P16 short at market 10:32:12 @ 48.81 (20 sh, slip -146.8 bps); P17 1R = 9.03
- **C** best point (MFE) +0.75R at 10:53
- **D** worst point (MAE) -0.12R at 11:35
- **E** P22 15:55 time exit 15:55:43 @ 42.59: +0.69R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|


Observation only: the original setup is never edited. Educational only — not financial advice.
