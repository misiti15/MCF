# Workbench blueprint: Big Gainer Fade, VWAP Band Guard (all day)

`RW6G1-ns2-up3-vwap2sd-short-FD` - short - built 2026-11-16

> 09:50-15:00: like Big Gainer Average Reclaim Fade on stocks up over 3%, but never while price holds above the +2 SD VWAP band. Full-day version of RW6G1-ns2-up3-vwap2sd-short.

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
| Refire | `every qualifying bar, cooldown 1 bar(s)` | refire: true |

## ENTRY TRIGGER

| Part | Exact value | Source / note |
|---|---|---|
| Side | `SHORT` | SIDE |
| Module rule (as described) | `close crosses above the 5-min SMA50 on this bar` | LAYERS |
| Module rule (as described) | `stock up > 3% from the open` | LAYERS |
| Module rule (as described) | `RSI(14) >= 60` | LAYERS |
| Module rule (as described) | `no unresolved close above VWAP + 2 SD (owner VWAP band guard)` | LAYERS |
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
| Open lots per setup | `75` | max_positions_per_strategy |
| Per-setup daily latch | `stops at -2R net` | max_setup_daily_loss_r |
| Account daily stop | `-120R` | max_daily_loss_r |
| Lots per symbol | `3 (same side)` | same_setup_reentry: True |
| Spread / size checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | live |

## ACCOUNT & SIZING

| Part | Exact value | Source / note |
|---|---|---|
| Runs in | `Graveyard` | configs now |
| Size per trade | `min(0.25% equity at risk, slot ~$533)` | 300 slots x 1.6 BP |
| Max position | `10% of equity` | max_position_notional_pct |

## RECORD

| Part | Exact value | Source / note |
|---|---|---|
| Trades / sessions | `63 / 19` | 2026-10-13 to 2026-11-13 |
| Avg R after costs | `-0.003R` | total -0.2R, win 49% |
| Avg R w/o best day | `-0.093R` |  |
| By account | `On Deck 30 tr -0.17R, Graveyard 33 tr +0.15R` |  |
| Rule changes in window | `7 (listed in the markdown)` | latest: 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 mi; 2026-11-12: LR5: broker position vs journal lot check every  |

## MODULE

- file: `research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD.py` (parsed as: mask)
- module's own layer notes: close crosses above the 5-min SMA50 on this bar; stock up > 3% from the open; RSI(14) >= 60; no unresolved close above VWAP + 2 SD (owner VWAP band guard); full day: bar close 09:50-15:00 ET (YAML window [950, 1500])

## RULE CHANGES INSIDE THE RECORD WINDOW

- 2026-10-20: Risk: no lot on a symbol held by the setup's twin (X / X-FD, 'twin held'); per-setup daily loss limit -2R net ('setup daily loss limit') in Testing 1/2 and gen, account backstop 60 -> 120R there
- 2026-10-23: Owner ST-A: per-setup daily loss stop off in Testing 1, Testing 2 and the Setup Generator (Graveyard keeps -2R; Primary unchanged, never had one)
- 2026-10-30: Owner CF: Testing 1/2 skip entries whose stop-exit round-trip cost > 0.15R (forward test of p3_1029 A3)
- 2026-11-04: Owner DM-N3: NS5-sma50-flush-oversold-long-FD (T1+T2 split), ST4-emadn-long-am-t1s05-FD (T1), RW6G1-ns2-up3-vwap2sd-short-FD (T1) -> Graveyard (move)
- 2026-11-12: Graveyard: buying_power_multiple 3.8 -> 1.6, slots 200 -> 300 (REPV-11); per-setup cap 25 -> 75 (REPV-12); -2R latch kept (config)
- 2026-11-12: LR1: flatten at min(15:55, calendar close - 5 min) on every account (half days 11-27 / 12-24 flatten 12:55)
- 2026-11-12: LR5: broker position vs journal lot check every poll on all accounts; a persistent mismatch is flagged (health.position_mismatch), blocks new entries in that symbol and alerts; never auto-closed

## WORKBENCH PARAMETERS (for `python -m mcf.research.workbench spawn`)

- `refire` = `True`
- `refire_cooldown` = `1`
- `min_adv` = `95000000`
- `window` = `[950, 1500]`
- `scale_out_r` = `None`
- `live_scale_out` = `False`
- `geom` = `t1s1`
- `r_atr_frac` = `0.25`

## ENGINE VIEW (numbered parts)

| Part | Stage | Component | Exact value | Binding share |
|---|---|---|---|---|
| P1 | INTAKE | Account universe | `ADV >= $5M core, ATR >= 1.0%` | - |
| P2 | INTAKE | Setup liquidity floor (20d avg $ vol) | `>= $95M` | - |
| P3 | INTAKE | Price floor | `>= $5.0` | blocked 0/110 signals (0%) |
| P4 | INTAKE | Earnings blackout | `4 trading days either side` | - |
| P5 | INTAKE | Short borrow | `shortable + easy to borrow` | blocked 24/110 signals (22%) |
| P6 | TIMER | Entry window (5-min bar close) | `09:50-15:00 ET` | - |
| P7 | TIMER | No entries before | `09:50 ET` | - |
| P8 | TIMER | Refire | `every qualifying bar, cooldown 1 bar(s)` | - |
| P9 | SENSORS | Module rule (as described) | `close crosses above the 5-min SMA50 on this bar` | - |
| P10 | SENSORS | Module rule (as described) | `stock up > 3% from the open` | - |
| P11 | SENSORS | Module rule (as described) | `RSI(14) >= 60` | - |
| P12 | SENSORS | Module rule (as described) | `no unresolved close above VWAP + 2 SD (owner VWAP band guard)` | - |
| P13 | SENSORS | Module rule (as described) | `full day: bar close 09:50-15:00 ET (YAML window [950, 1500])` | - |
| P14 | GATES | Open lots per setup | `75` | blocked 0/110 signals (0%) |
| P15 | GATES | Lots per symbol | `3 (same side)` | blocked 6/110 signals (5%) |
| P16 | GATES | Per-setup daily latch | `stops at -2R net` | blocked 0/110 signals (0%) |
| P17 | GATES | Account daily stop / halt | `-120R` | blocked 1/110 signals (1%) |
| P18 | GATES | Quote & spread checks | `spread <= 30 bps and <= 0.25 of stop; <= 10% of 1-min volume` | blocked 4/110 signals (4%) |
| P19 | ENTRY | Side + order | `SHORT at market, signal-bar close` | - |
| P20 | ENTRY | 1R (risk unit) | `0.25 x daily ATR` | - |
| P21 | ENTRY | Size per trade | `min(0.25% equity at risk, slot ~$533)` | - |
| P22 | ENTRY | Max position | `10% of equity` | - |
| P23 | EXHAUST | Stop | `1.0R above entry` | ended 13/63 live trades (21%) |
| P24 | EXHAUST | Target | `+1.0R` | ended 13/63 live trades (21%) |
| P25 | EXHAUST | Scale-out | `none` | ended 0/63 live trades (0%) |
| P26 | EXHAUST | Time exit | `flat at 15:55 ET` | ended 37/63 live trades (59%) |

Exit mix: {'target': 13, 'stop': 13, 'time': 37} of 63 live trades; blocked signals: {'other': 3, 'borrow': 24, 'quote': 4, 'cap_symbol': 6, 'acct_stop': 1, 'split_gate': 3, 'twin': 1} of 110 live signals (refire setups re-signal every bar while held).

## TRADE TEARDOWNS

### MDGL 2026-10-20 (testing #4382): -1.27R, stop

![](RW6G1-ns2-up3-vwap2sd-short-FD_trade1_MDGL_2026-10-20.png)

- **A** live signal at the 14:50 bar close inside the P6 window: sensors all met; none newly true on this bar (all held already: P8 refire)
- **B** P19 short at market 14:51:31 @ 465.20 (1 sh, slip 9.4 bps); P20 1R = 4.56
- **C** best point (MFE) -0.06R at 14:54
- **D** worst point (MAE) -1.12R at 15:42
- **E** P23 stop hit 15:42:23 @ 470.99: -1.27R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### LUNR 2026-10-15 (testing #1632): -1.14R, stop

![](RW6G1-ns2-up3-vwap2sd-short-FD_trade2_LUNR_2026-10-15.png)

- **A** live signal at the 10:55 bar close inside the P6 window: sensors all met; none newly true on this bar (all held already: P8 refire)
- **B** P19 short at market 10:56:51 @ 11.02 (86 sh, slip -41.0 bps); P20 1R = 0.18
- **C** best point (MFE) +0.19R at 10:56
- **D** worst point (MAE) -1.00R at 11:06
- **E** P23 stop hit 11:06:35 @ 11.21: -1.14R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### DKNG 2026-10-19 (testing #4105): -1.08R, stop

![](RW6G1-ns2-up3-vwap2sd-short-FD_trade3_DKNG_2026-10-19.png)

- **A** live signal at the 14:25 bar close inside the P6 window: sensors all met; none newly true on this bar (all held already: P8 refire)
- **B** P19 short at market 14:26:07 @ 19.56 (47 sh, slip -5.1 bps); P20 1R = 0.24
- **C** best point (MFE) +0.00R at 14:28
- **D** worst point (MAE) -1.08R at 15:42
- **E** P23 stop hit 15:42:11 @ 19.80: -1.08R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### TEM 2026-11-09 (graveyard #14367): -1.07R, stop

![](RW6G1-ns2-up3-vwap2sd-short-FD_trade4_TEM_2026-11-09.png)

- **A** live signal at the 14:30 bar close inside the P6 window: sensors all met; none newly true on this bar (all held already: P8 refire)
- **B** P19 short at market 14:32:20 @ 84.23 (21 sh, slip -36.3 bps); P20 1R = 1.36
- **C** best point (MFE) -0.00R at 14:32
- **D** worst point (MAE) -0.97R at 15:31
- **E** P23 stop hit 15:31:12 @ 85.67: -1.07R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|

### NTSK 2026-10-29 (testing #7145): -1.06R, stop

![](RW6G1-ns2-up3-vwap2sd-short-FD_trade5_NTSK_2026-10-29.png)

- **A** live signal at the 13:40 bar close inside the P6 window: sensors all met; none newly true on this bar (all held already: P8 refire)
- **B** P19 short at market 13:40:32 @ 25.83 (35 sh, slip 23.2 bps); P20 1R = 0.41
- **C** best point (MFE) +0.21R at 13:47
- **D** worst point (MAE) -0.99R at 14:33
- **E** P23 stop hit 14:33:43 @ 26.25: -1.06R after costs

| Part | Test | Bar before | Signal bar | Met |
|---|---|---|---|---|


Observation only: the original setup is never edited. Educational only — not financial advice.
