# Root cause 2026-11-19, execution: entries, stops and fills

*Educational only, not financial advice.* This is research only. Nothing in config/, the setups, the exits or the orders was changed (it is market hours).

## Answer
**Execution is not a root cause of today's loss.** Of the -15.14R that ST7-FD and L3 lost on their 14 trades today, execution accounts for about **-1.1R**. If every trade had filled exactly at the signal price and stopped exactly at its stop, the day would still have been about -14R. Entry slippage was -0.86R and stop-exit slippage was -0.50R, partly offset by favourable fills. The stops were not too tight. No stop gapped through. After each stop, price kept going the wrong way, so in every case the trade idea did not work. The loss comes from the *direction* of the trades: 13 of the 14 were in effect long the index-tech complex in the same 20-minute window, and the 11:51-12:05 leg (SPY 728.9 to 717.9, -1.5%; QQQ 660.1 to 647.4) stopped them all. That points to the setup and its conditions (other dimensions), not to how we enter or exit.

## Data and method
- **Journals (read only):** Primary `origin/mcf-data:journal.db` and Testing 1 `origin/mcf-data-testing:journal.db`, run_id=1 (live paper). The scope is all live ST7-rsi50dn-long-pm-t1s1-FD trades (58: Primary 42, Testing 1 16) and all live L3-gap-slope-fromopen-FD trades (403: Primary 181, Testing 1 222), plus today's 3 RW3 trades for contrast.
- **R = pnl_adj / (|entry - stop| x shares)**, with costs in (LR8).
- **Signal reference price** comes from the `signals` table, matched on the client order ID. 21 early Testing 1 rows have a broken reference price (19.68 for every symbol, 10-12/10-13) and are left out of the slippage figures.
- **1-minute bars:**
  - up to 11-04: `data/cache_hist` (the locked block 2024-11-01..2025-02-28 was not read);
  - 11-05..11-19: Alpaca SIP, 14 multi-symbol GET requests;
  - today's bars run only to **13:06 ET**, so "after the stop" for today means through 13:06, not 15:55.
- **ATR measures:** "1-minute ATR" is the mean true range of the 14 one-minute bars before the fill. "15-minute ATR" is the mean true range of up to 6 completed 15-minute bars of the same day.
- **Instrument type** comes from the `data/universe.csv` name: stock, ETF, leveraged ETF, or inverse ETF.
- **2-year lab:** `research/history2y/data/bt_lab1104/sig_*.parquet`, with production costs and refire as live, from 2024-10 to 2026-11-04 (locked months not present and not read).
- Scripts and outputs are under `rootcause_1119/exec_scripts/` and `rootcause_1119/exec_data/` (audit_trades.csv, anchor.csv, width.csv).
- **Configurations counted: 7.** Two bracket-anchoring variants, four stop widths (0.75 / 1.25 / 1.5 / 2.0), and one rounding rule (untested). The splits by instrument type are descriptive and add 10 cells (2 setups x 5 types).

## 1. Today's 17 Primary trades
Columns: `sig->fill` is seconds from signal to fill. `entry slip` and `exit slip` are in R: a negative entry slip means a better fill than the signal price, and a negative exit slip means a worse exit than the stop or target price. The `stop / ATR` columns divide the stop distance by the 1-minute and 15-minute ATR. `after stop` is the further move against the trade (R from entry) through 13:06 ET.

| setup | sym | type | fill ET | sig->fill | entry slip | stop % | stop / ATR 1m | stop / ATR 15m | MFE before stop | stop touch | 1-min bar closed through | 5-min closed through | target after stop? | after stop | R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST7 | ASML | ETF* | 10:45:29 | 0.8s | -0.09 | 1.25 | 4.2 | 1.23 | 0.99 | 12:00 | no | yes | no | -2.16 | -1.09 |
| ST7 | ETHA | ETF | 10:45:40 | 1.5s | +0.03 | 1.48 | 6.6 | 1.61 | 0.43 | 12:18 | exact touch** | - | no (high 40.38 vs target 40.69) | - | -1.04 |
| ST7 | FTEC | ETF | 10:45:42 | 0.5s | -0.11 | 0.84 | 4.5 | 0.89 | 1.07 | 11:53 | no | no | no | -2.58 | -1.16 |
| ST7 | MUU | lev ETF 2x | 10:45:57 | 3.6s | -0.05 | 4.91 | 4.2 | 1.06 | 0.99 | 12:03 | yes | yes | no | -1.44 | -1.06 |
| ST7 | SMH | ETF | 10:46:08 | 2.4s | -0.22 | 1.28 | 3.2 | 0.95 | 1.32 | 12:01 | yes | yes | no | -2.17 | -1.14 |
| ST7 | TER | stock | 10:46:09 | 0.3s | 0.00 | 2.36 | 3.9 | 1.31 | 0.81 | 12:00 | no | yes | no | -1.93 | -1.02 |
| ST7 | TECL | lev ETF 3x | 10:46:12 | 3.7s | -0.24 | 2.82 | 4.5 | 1.01 | 1.19 | 12:00 | no | yes | no | -2.27 | -1.04 |
| L3 | SPXS | inv ETF 3x | 11:16:11 | 5.2s | -0.13 | 1.12 | 3.8 | 0.93 | 1.11 | 11:52 | yes | no | no | -4.02 | -1.22 |
| L3 | SQQQ | inv ETF 3x | 11:21:04 | 1.0s | +0.08 | 2.20 | 4.9 | 1.10 | 0.81 | 11:52 | yes | no | no | -2.99 | -0.92 |
| L3 | SPXS | inv ETF 3x | 11:26:07 | 3.3s | -0.29 | 0.97 | 4.3 | 0.80 | 1.34 | 11:52 | yes | no | no | -4.54 | -1.03 |
| L3 | SQQQ | inv ETF 3x | 11:31:09 | 5.7s | -0.28 | 1.58 | 3.4 | 0.88 | 1.04 | 11:51 | yes | yes | no | -4.26 | -1.13 |
| L3 | SPXS | inv ETF 3x | 11:36:06 | 1.8s | +0.12 | 1.44 | 5.5 | 1.25 | 0.67 | 11:52 | yes | no | no | -3.33 | -1.12 |
| L3 | SQQQ | inv ETF 3x | 11:46:05 | 1.0s | +0.01 | 2.04 | 4.5 | 1.20 | 0.27 | 11:51 | yes | yes | no | -3.54 | -1.07 |
| ST7 | IWN | ETF | 11:55:49 | 0.6s | +0.30 | 0.68 | 10.7 | 2.14 | -0.12 | 12:03 | yes | yes | no | -1.46 | -1.12 |
| RW3 | EWT | ETF | 11:15:43 | 4.1s | +0.11 | 1.60 | 8.1 | 1.53 | 0.82 | - | - | - | target | - | +0.77 |
| RW3 | IBRX | stock | 11:15:48 | 3.2s | +0.05 | 2.82 | 7.3 | 1.27 | 0.03 | 11:37 | yes | yes | no | -1.57 | -1.14 |
| RW3 | NUGT | lev ETF 2x | 11:30:54 | 1.3s | -0.04 | 2.96 | 10.8 | 1.86 | 1.12 | - | - | - | target | - | +1.08 |

\* The universe name for ASML is "New York Registry Shares", so the classifier labels it ETF. It is really a stock (ADR); this does not change any conclusion.

\*\* **ETHA:** the stop was 39.5366, and the broker stop was `round(stop, 2)` = 39.54 (`mcf/execution/alpaca_broker.py:91`). The SIP 1-minute low at 12:18 was exactly 39.540, so the stop filled at the day's low without ever trading through the raw stop. ETHA then went to 40.38 by 12:34, which is short of its 40.69 target, and was at 40.04 at 13:06. This is the only stop of 89 live stopped trades with bars that filled without the bar reaching the raw stop.

Reading today:
- **Timing.** The signal is the 5-minute bar close. The order goes in about 1.25 minutes later (bar_age 1.22-1.27 min, quote age 0.0-0.4 s) and fills in 0.3-5.7 s. No entry was late.
- **Entry price.** The sum of entry slippage over the 14 ST7/L3 trades was -0.86R, and most fills were *better* than the signal price. The largest adverse fill was IWN at +0.30R.
- **Stops.**
  - None gapped through.
  - The stop-exit slip ran from -0.14R to +0.10R, -0.50R in total.
  - The stops were 3.2-10.7x the 1-minute ATR and 0.8-2.1x the 15-minute ATR (median 4.4x / 1.08x).
  - The 3x inverse ETFs (SPXS/SQQQ) had the same stop/ATR ratios as the plain ETFs. The leveraged names (TECL, MUU) had wider stops in % terms (2.8% / 4.9%), because R = 0.25 x daily ATR already scales with leverage.
  - So the stops were not tight relative to the instruments' noise.
- **Did the idea work later?** No. In 0 of 13 stopped trades did price reach the target after the stop (through 13:06). Price went a further 1.4-4.5R against the trades, and at 13:06 they were still -0.4 to -3.1R from entry. Holding through the stop would have lost more.
- **The setup worked first, then the market turned.**
  - 10 of 14 trades reached a favourable move of at least 0.8R before the reversal.
  - ST7 bought at 10:45, close to SPY's then-low (727.6). The market bounced to 728.9 by 11:30, then dropped 1.5% from 11:51 to 12:05.
  - L3's six shorts of SPXS/SQQQ are long-index positions in effect: L3 shorts a gapped-down name that has recovered more than 3.5% from the open. On an inverse ETF, that means "the index gapped up and has since fallen more than about 1.2%".
  - All six lots had stops in one narrow band (SPXS 28.545-28.575, SQQQ 46.63-46.98) and were stopped at 11:51-11:52.
  - This is a direction and correlation problem, not a fill problem.

## 2. All live ST7-FD and L3 trades
### Slippage
L3 rows are 388 trades after removing bad reference prices; ST7 rows are 52.

| setup | acct | n | entry slip mean (R) | entry slip median (bps) | entry slip 90th pct (R) | exit slip mean (R) |
|---|---|---|---|---|---|---|
| L3 | Primary | 181 | +0.020 | 7.8 | 0.128 | -0.018 |
| L3 | Testing 1 | 207 | +0.017 | 6.9 | 0.158 | -0.007 |
| ST7 | Primary | 42 | +0.013 | 0.3 | 0.158 | -0.023 |
| ST7 | Testing 1 | 10 | +0.053 | 9.2 | 0.100 | -0.024 |

- **Stop exits** slip -0.048R on average for L3 (91 stops) and -0.050R for ST7 (21 stops).
- **Target exits** gain +0.009 to +0.010R on average.
- **Total execution drag:**
  - L3: about 10R over 388 trades (+7.1R entry, -2.8R exit), against a live total of +81.3R.
  - ST7: about 1.9R over 52 trades, against -3.4R.
  - That is about -0.025 to -0.04R per trade. It is small and not the reason either setup wins or loses.

### Slippage and R by instrument type (live)
| setup | type | n | total R | avg R | avg R without best day (best day's share) | entry slip (bps) | stop / 15-min ATR (median) |
|---|---|---|---|---|---|---|---|
| L3 | stock | 296 | +71.9 | +0.243 | +0.185 (42%) | 6.9 | 1.34 |
| L3 | ETF | 51 | +13.6 | +0.267 | +0.215 (50%, **1-day tag**) | 8.6 | 1.24 |
| L3 | leveraged ETF | 35 | +9.1 | +0.261 | +0.271 (26%) | 5.8 | 1.44 |
| L3 | **inverse ETF** | 17 (4 days) | **-9.0** | **-0.530** | -0.669 | -2.3 | 1.24 |
| ST7 | stock | 48 | +3.5 | +0.073 | -0.013 (116%, **1-day tag**) | 4.8 | 1.26 |
| ST7 | ETF | 7 | -5.7 | -0.818 | -1.109 | -3.0 | 1.23 |
| ST7 | leveraged / inverse ETF | 3 | -1.2 | | | | |

- Slippage does not depend on instrument type: leveraged and inverse ETFs fill as well as stocks or better, because their spreads are 2-7 bps.
- The **inverse-ETF bucket** of L3 is the loser: -0.53R per trade, -0.23R excluding today (11 trades).
- In the 2-year lab (with costs and refire), L3 by type is:

  | type | n | avg R | avg R without best day |
  |---|---|---|---|
  | inverse ETF | 1,994 | -0.068 | -0.110 |
  | leveraged ETF | 7,901 | -0.093 | -0.110 |
  | stock | 29,203 | -0.019 | -0.062 |
  | ETF | 3,742 | +0.072 | -0.020 |

- L3 as a whole is -0.027R per trade in the lab (n 42,845) against +0.20R live. ST7 is +0.036R in the lab (n 1,114; +0.028R without its best day).
- These are **setup and condition findings** for the other dimensions. A stop or fill change cannot fix them.

### How stops are hit, and noise stops (87 live stops with bars)
| setup | stops | gap-through | 1-min bar closed through | 5-min bar closed through | later reached target (noise stop) | R at 15:55 if held through the stop | minutes to stop (median) |
|---|---|---|---|---|---|---|---|
| L3 | 68 | 2.9% | 68% | 53% | 10 (14.9%) | -1.36 | 40 |
| ST7 | 19 | 5.3% | 58% | 63% | 1 (5.3%) | -1.37 | 75 |

- Holding every stopped trade to 15:55 would have turned -95.7R into -117.2R.
- The stops save R. "Noise stops" (stopped, then target) are a small minority, and they are not more frequent on leveraged or inverse ETFs: inverse 2 of 12, stock 8 of 43, ETF 0 of 7, leveraged ETF 0 of 2.

## 3. Remedies tested
### Stop width k x own stop
The test uses a 1-minute walk on live fills, with the target unchanged and the same $ risk. It compares against the same trade sized at 1/k (a size-only control).

| setup | type | k=1 gross R | 0.75 | 1.25 | 1.5 | 2.0 | stop effect at 1.5 vs size control |
|---|---|---|---|---|---|---|---|
| L3 | stock (244) | +0.299 | +0.366 | +0.247 | +0.204 | +0.160 | +0.005 |
| L3 | ETF (43) | +0.445 | +0.556 | +0.371 | +0.291 | +0.200 | -0.005 |
| L3 | leveraged ETF (24) | +0.426 | +0.502 | +0.345 | +0.287 | +0.215 | +0.003 |
| L3 | inverse ETF (15) | -0.627 | -0.868 | -0.555 | -0.434 | -0.492 | -0.016 |
| ST7 | stock (46) | +0.129 | +0.107 | +0.085 | +0.046 | +0.034 | -0.040 |
| ST7 | ETF (7) | -0.610 | -0.689 | -0.631 | -0.537 | -0.418 | -0.131 |

A wider stop for leveraged or inverse ETFs has a stop effect of about 0 (+0.003 / -0.016R per trade). Any gain in R per trade is size, not the stop. This agrees with research/stoplab B: keep k = 1.0. **Rejected.**

### Bracket anchoring
The live bracket is anchored to the *signal close*, as in the lab. A favourable fill therefore puts the target 1.1-1.5R away in fill terms. Today, 5 of 7 ST7 trades peaked at 0.99-1.32R from the fill but missed their target. Two variants were tested on 370 live trades:
- **(a) target = fill + 1R of fill risk:** +10.3R in total, with 91 trades better and 61 worse. But today alone accounts for +12R (6 flips), so the other days are **-1.7R**. By setup:

  | setup | account | trades | change |
  |---|---|---|---|
  | ST7 | Primary | 41 | +5.9R |
  | ST7 | Testing 1 | 9 | -0.6R |
  | L3 | Primary | 166 | +5.4R |
  | L3 | Testing 1 | 151 | -0.6R |

  It is a one-big-day artifact. **Rejected.**
- **(b) whole bracket re-centred on the fill:** +2.1R in total (132 better / 96 worse). L3 +3.4R, ST7 -1.4R, best day 123% of the total. **Rejected.**

### Untested
- **Round broker stops away from entry** (floor for long stops, ceil for short stops; today `round(stop, 2)`). It is targeted and harmless, but it would have changed 1 of 89 stops (ETHA today, worth about +0.9R today: -1.04R to about -0.15R at 13:06). Its value elsewhere is not measured. It is backlog housekeeping, not a root-cause fix.

## Rule-change context (live window 10-12..11-19)
| date | change (research/ledger.jsonl) |
|---|---|
| 10-14 | refire option B (L3 refire, cooldown 1) |
| 10-20 / 10-22 / 10-30 | L3 promoted, demoted, re-promoted to Primary (Testing 1 before) |
| 10-26 | ST7-FD promoted to Primary (moved from Testing 1) |
| 10-27 | GX1 lab clock gate |
| 10-28 | Primary position size changes (5k / 4k) |
| 10-29 | Primary -2R per-setup daily stop (latch) |
| 10-30 | Testing cost filter CF |

There has been no Primary sizing, stop or fill change since 10-30, so today's figures are not mixed with a rule change.

## Hand-offs to other dimensions
These are evidence, not remedies of mine:
1. **The direction problem.** Today's 14 losses were one bet: long the index and tech dip, stopped by a single -1.5% leg. ST7 dip buys and L3 shorts of inverse ETFs (= index dip buys) fired into the same move. The Compass confirmed DOWN at 11:15, before every L3 entry and IWN.
2. **L3 on inverse ETFs is a different trade from the one L3 was built on**, which fades a gapped-down stock's recovery. Live it is -0.53R (17 trades) and in the 2-year lab -0.068R (n 1,994). Most inverse ETFs are already skipped as not shortable or ETB; SPXS and SQQQ were the ones that passed.
3. **L3's live edge** (+0.20R per trade) is not seen in the 2-year lab (-0.027R per trade, refire included).

Educational only, not financial advice.
