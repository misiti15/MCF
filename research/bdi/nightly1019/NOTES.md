# Nightly learning loop, analysis part: 2026-10-19 (Primary, Testing 1, Testing 2, Setup Generator)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They describe what happened; they are not evidence that anything works. **No backtest was run tonight (0 configurations)**, and neither the locked block (2024-11-01..2025-02-28) nor any holdout was touched. I looked at about 55 descriptive splits of today's trades: setup, side, hour, exit, poll, lot, twin, refire, cluster and latency per account, 11 index-context cuts and 3 slippage cuts. None of them is gated, so with that many cuts a few will look strong by chance.*

**Costs are in.** P/L is the journal `pnl_adj`. Avg R is `pnl_adj / $ risk` (labelled "avgR"); the journal's own `r_multiple` is quoted as "R(j)". The open lots on the intraday curves are marked at the 1-min SIP close less 1 bps + $0.01/sh.

**Inputs.** `journal.db`, `status.json`, `reports/scorecard.json`, `setups/2026-10-19.json` and `intraday/2026-10-19.jsonl` come from `origin/mcf-data` (Primary), `mcf-data-testing` (T1), `mcf-data-testing2` (T2) and `mcf-data-gen` (GEN). I also used SIP 1-minute bars for 326 symbols, SPY/QQQ/IWM included (Alpaca market data, read-only, kept in scratch). I called no trading endpoint and did not read broker activities.

**Scripts** (run each as `python <script> <scratch>`):
- `fetch.py`: downloads the bars.
- `build.py`: writes `trades.csv`.
- `t1_missing.py`: writes `t1_missing.csv` and `t1_missing_out.txt`.
- `autopsy.py`: writes `autopsy_out.txt`.
- `giveback.py`: writes `giveback_out.txt`, `daily_peak.csv` and `giveback_attr.csv`, using the giveback1019 method.
- `patterns.py`: writes `patterns_1019.csv` and `patterns_out.txt`.
- `indexctx.py`: writes `indexctx_out.txt`.
- `tables.py`: prints the markdown tables below.

**Market: a two-way day that ended flat.**

| index | 10:04 low | 11:37 high | close (from open) |
|---|---|---|---|
| SPY | −0.18% | +0.42% | −0.09% |
| QQQ | −0.42% | +0.69% | −0.18% |
| IWM | −0.41% | +0.31% | −0.19% |

The shape: a dip into 10:04, a rally to 11:37, then a fade back to flat by 13:00 that held into the close. The day punished both sides in turn. Shorts entered into the 10:04 low were stopped on the rally, and longs entered on the way up to the 11:37 high were stopped on the fade.

## Failures first

1. **Testing 1's journal is incomplete.** The final state push failed, so `mcf-data-testing` holds **325 of 457 trades**. The job log has the full day: **457 trades, P/L −$482.70, win 48.1%, exp −0.07R**. The 132 missing trades are submitted signals with no trade row. Almost all were lots still open at the last push (`status.json` at 15:54 shows phase `trading`, 91 open symbols, unrealized −$267.71).
   - `t1_missing.py` replays them on SIP bars from the signal reference price; this is an estimate. It finds 131 flattened at 15:55, 62 wins (the job log implies 60), and **−$181.68 gross / −$220.30 after costs**.
   - The job log implies −$341.80 for these trades. The gap is mostly entry fills: the actual average fills were $63 worse than the reference prices, compared on the open positions. Breakeven and trailing management are not modelled either.
   - **Use the job-log totals for T1.** Per-setup T1 figures below come from the 325 journaled trades, with the replay estimate in a separate column.
   - The T1 scorecard (`reports/scorecard.json`) was built from the incomplete journal as well.
2. **Testing 2 live scale-out did not complete once.** Seven T2 setups carry `live_scale_out: true`: CWT14 orl/pdl longs, CWT12-coil-k4 and CWT14-pdh-p05-lowvol-short.
   - `health.scale_outs` is empty and `health.scale_out_failed` lists **14 lots**: "scale-out not completed after 5 tries (error)".
   - Those lots kept their full-size bracket. 134 of the 212 trades on these setups reached ≥ +0.25R, and 17 of those were later stopped (−$66.46).
   - The error text is not in the snapshot. **This is housekeeping:** the scale-out code path errors at the broker call (`broker.scale_out_lot`). In practice T2 ran without scale-outs today.
3. **The Setup Generator account started late.** It started at 12:10 ET (init) and restarted at 12:51 ET; the job ran "job 12:51". Of its 10 GEN setups, 4 have morning windows and could not trade:
   - 01, 05 and 08 (09:50–11:00) had no coverage.
   - 04 (11:00–13:00) had only about 12:10–13:00.
   - Only setups 03 and 10 signalled, with 7 signals, 6 trades and 1 skip (spread 39 bps).
   - **This is day 1, but not a full day.**
4. **Primary closed negative after costs.** The streak is in section 6.
5. **A cleanup check: no withholding shows on Testing 1's EPD short** (10-16). Equity changed from the 10-16 close to 15:54 by −$404.40, against the runner's −$408.61, so there is no ~$90 drop. Broker activities were not read.
   - Overnight gaps are small: Primary −$1.40, T2 −$6.96, GEN 0.00.

## 1. Headline per account (real trades, run 1)

| account | trades | win% | avgR (costs) | R(j) | P/L journal | P/L after costs | broker day | stop / target / flatten | intraday peak → trough → close (marked, costs in) |
|---|---|---|---|---|---|---|---|---|---|
| Primary (12 setups) | 37 | 48.6% | −0.175 | −0.127 | −$49.30 | **−$63.92** | −$50.70 | 16 / 16 / 5 | +$64 at 10:05 → −$142 at 15:40 → −$64 |
| Testing 1, journal | 325 | 49.2% | −0.075 | −0.059 | −$140.90 | −$184.06 | n/a (no final snapshot) | 165 / 160 / 0 | |
| **Testing 1, job log** | **457** | **48.1%** | | **−0.07** | **−$482.70** | ≈ −$404 marked + flatten costs | | | +$671 at 10:05 → −$837 at 14:35 → −$404 (with the 132 replayed) |
| Testing 2 | 310 | 60.3% | −0.148 | −0.106 | −$28.53 | **−$79.27** | −$35.49 | 102 / 180 / 28 | +$60 at 10:19 → −$226 at 14:29 → −$79 |
| Setup Generator (day 1, from 12:51) | 6 | 66.7% | −0.029 | +0.022 | +$39.28 | **+$21.24** | +$39.28 | 2 / 3 / 1 | −$65 at 14:22 → +$42 at 15:51 → +$21 |

The runner's own snapshots agree with these curves:

| account | runner peak | runner trough | runner last |
|---|---|---|---|
| Primary | +$78 at 10:39 | −$129 at 15:39 | |
| T1 | +$685 at 10:03 | −$777 at 14:27 | −$409 at 15:54 |
| T2 | +$67 at 10:20 | −$169 at 14:34 | |
| GEN | +$47 at 15:51 | | |

**Best and worst setups (after costs):**

| account | best | worst |
|---|---|---|
| Primary | MF4-h40-open-flowsell +$32.24 (3, 100%); RW5-FD +$17.40 (2) | MF3-open-flowsell-rsi5hi −$50.23 (5, 20%, −0.79R); MF3-FD −$37.91 (13, 54%); RW3-FD −$15.61 (5) |
| Testing 1 | heat_fade_short-FD +$241.74 (75, 61%); heat_fade_short +$134.25 (46); exhaustion_short-FD +$97.15 (12, 75%); NS3-FD +$89.92; RW2-FD +$89.28 | heat_fade_long −$216.48 (13, **0%**), est −$106 more in missing lots; heat_fade_long-FD −$192.38 (22), est −$123 more; LIQ-orl-sweep −$115.38 (6, 0%), est −$69 more; RW7-FD −$100.11; ST2-FD −$85.63; NS5-FD −$84.16 |
| Testing 2 | NM-RWN5-ns3-mon-weakrs-short +$35.50 (5, 80%); CWT14-orl-p05-long +$34.65 (58) | CWT14-pdl-p05-lowvol-long −$61.10 (29, 45%); CWT13-vwapstretch-z05-long −$47.65 (3, 0%); CWT14-pdl-p10-lowvol −$21.23 |

**Scorecard flags (fixed bar; paper results):**
- Primary: **MF3-open-flowsell-rsi5hi is now "below backtest – review"** (13 trades, −0.426R, −$79.21), next to NS2 (44 trades, now in T1).
- T1: heat_fade_long (64, −0.641R) and heat_fade_short (73, −0.206R) are both ex-primary.
- T2: 7 setups are flagged, among them CWT09-g5-lowerhalf (34, −0.691R) and CWT14-pdl-p10-long (111, −0.283R).
- Removal from Testing needs the owner prompt (rule 20). Nothing is proposed here.

### Intraday peak vs close: what gave it back (giveback1019 attribution, `giveback_out.txt`)

| account | giveback | (b) entered after peak | (a) open winners at peak | open losers at peak | side | late flatten ≥ 15:50 | worst contributors |
|---|---|---|---|---|---|---|---|
| Primary | $128 | **−$115 (25 trades, 90%)** | −$13: 5 stopped −$39, 6 targets +$27 | 0 | shorts −$126 | −$4 | MF3 −$56, MF3-FD −$51, RW3-FD −$23; entry hour 10h −$90 |
| Testing 1 (incl. est.) | $1,076 | **−$780 (343, 72%)** | −$284: 39 stopped −$438, 27 targets +$156 | −$12 | **longs −$1,091**, shorts +$16 | −$224 (131 lots, the missing ones) | heat_fade_long −$322, heat_fade_long-FD −$298, LIQ-orl −$185, heat_fade_short −$172, NS5-FD −$130; entry hour 12h −$593 |
| Testing 2 | $139 | −$35 (186) | **−$89: 7 stopped −$108** | −$15 | longs −$153 | +$5 | CWT14-pdl-p05-lowvol −$51, CWT13-z05-long −$48, CWT14 pdl/orl-p10-lowvol −$23 each |
| GEN | $21 | 0 | −$21 (DOCN flatten −$17) | 0 | | −$17 | |

**Testing 1, the main giveback, in plain words:**
- **09:50–10:05:** heat_fade_short and heat_fade_short-FD took the same semiconductor and tech shorts twice. They formed one 40-trade cluster per setup in the 09:50 poll, with 46 twin entries. The book was +$671 at the 10:04 index low.
- **10:05–11:37:** the rally stopped 39 of the open winners (−$438).
- **11:00–13:59:** T1 bought weakness right at and after the 11:37 index high: heat_fade_long, LIQ-orl-sweep, NS5-FD and ST2-FD. Longs entered in the 11h and 12h, by hour:

  | entry hour | trades | win% | avgR | P/L |
  |---|---|---|---|---|
  | 11h | 12 | 0% | −1.05 | −$205 |
  | 12h | 25 | 8% | −0.92 | −$360 |

  The index then faded flat, and those longs either stopped or sat underwater into the 15:55 flatten (the 131 replayed lots).

**Primary:** the morning peak is the 09:50 MF3/RW3/RW5 shorts at the 10:04 low. The give-back came from the next wave of shorts at 10:20–10:36 on VGT, VOOG and RGTI (8 trades, −$108.90). Those were entered after QQQ had already bounced, and the rally to 11:37 stopped them.

## 2. Winner/loser autopsy (`autopsy_out.txt`; SIP 1-min MFE/MAE for all 678 journaled trades)

| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winner give-back (MFE − R) | time to MFE, winners / losers | same-setup clusters per poll | twins (other setup, same symbol + side ≤ 3 min) | latency median / p90 | entry slip |
|---|---|---|---|---|---|---|---|---|---|
| Primary | 3 of 19, −$65.46 | **10 of 19, −$73.00** (loser median MFE **0.63R**) | 0.72 / 0.65 | 0.07R | 35 / 13 min | max 3; singles +0.06R, 2–4 **−0.61R** (13, −$45) | 17, −0.16R vs −0.19R | 1.6 / 3.5 s | 1.6 bps |
| Testing 1 | **83 of 165, −$1,178.41** | 43, −$393.62 | 0.94 / 0.31 | 0.06R | 83 / 8 min | max 40; singles −0.35R (106, −$444), ≥ 10 +0.09R (80, +$308) | 121, −0.06R vs −0.08R | 1.1 / 2.3 s | 4.5 bps |
| Testing 2 | **67 of 123, −$511.02** | 14, −$47.96 | 0.51 / 0.19 | 0.07R | 25 / 4 min | max 18; 2–4 −0.23R | 127, **−0.21R vs −0.10R** | 1.1 / 2.6 s | 5.5 bps |
| GEN | 0 of 2 | 0 | 0.68 / 0.25 | 0.15R | 62 / 7 min | max 2 | 0 | 1.1 / 2.5 s | **18.9 bps** |

- **Exits on winners are not the leak.** Give-back on winners is 0.06–0.07R in all three accounts again.
- **T1 and T2 losses are entry quality.** Half of the losers never worked, and they peaked within 4–8 minutes.
- **Primary is the exception today:** 10 of 19 losers had reached ≥ 0.5R first, e.g. DBMF at 1.1R/2.5R and MCHP at 0.77R. On 10-16 it was 9 of 19.
  - This is the "open winners revert" pattern, but the exit fixes for it have already failed on history: breakeven at 0.5R (BE050) gave valid −0.021R/trade, t −3.1, and scale-out at 0.5R with breakeven (SO05BE) gave valid −0.018R, t −2.1 (giveback1019).
  - So no exit hypothesis is proposed.
- **Latency and slippage do not separate winners from losers.**
  - Latency points different ways by account: the slowest tercile did best in Primary and T1 (T1 +0.045R vs −0.161R fastest) but worst in T2 (−0.305R vs −0.08R).
  - Trades where slippage took more than 25% of the target distance did better, not worse (−0.009 to +0.024R vs −0.167R for zero or negative slip).
  - GEN's 18.9 bps comes from two names: SNDQ +86 bps filled almost at the 0.5R target and banked +0.06R; ZS +41 bps halved a 1R target to +0.49R.
- **Stacking in Primary:** seven symbols carried three lots (CNQ, DBMF, RYAAY, VGT, VOOG, EMXC, BTI). Unlike 10-16, lot 3 made money today (7 trades, +0.145R, +$24.63). Lots 1 and 2 were −0.22R and −0.30R.

### Per-setup autopsy

Column key:
- `never`: never-worked losers / all losers.
- `lost05`: losers that reached ≥ 0.5R first.
- `gb_w`: winner give-back.
- `tmfe`: median minutes to MFE, winners/losers.
- `clus`: largest same-setup cluster in one poll.
- `twin`: twin entries.
- `lat`: median latency in seconds.
- `missing est`: the T1 replay estimate, as n / $.

**Primary**

| setup | n | win | avgR | P/L | mfe_w | mae_l | never | lost05 | gb_w | tmfe | clus | twin | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MF3-open-fs-rsi5hi | 5 | 20% | −0.79 | −50.23 | 0.72 | 1.02 | 0/4 | 2 | 0.07 | 193/12 | 2 | 5 | 2.5 |
| MF3-open-fs-rsi5hi-FD | 13 | 54% | −0.21 | −37.91 | 0.72 | 1.02 | 1/6 | 3 | 0.07 | 35/12 | 3 | 4 | 1.5 |
| RW3-gapdn-rsi5pop-fs-short-FD | 5 | 40% | −0.17 | −15.61 | 0.84 | 1.01 | 2/3 | 0 | 0.03 | 82/11 | 1 | 1 | 1.4 |
| MF1-945-fs-vwapup | 4 | 25% | −0.52 | −4.72 | 1.77 | 1.09 | 0/3 | 3 | 0.02 | 166/13 | 3 | 2 | 2.1 |
| MF5-fs-vwapup-rsi5hi | 3 | 67% | +0.13 | −2.13 | 0.81 | 1.06 | 0/1 | 1 | 0.09 | 114/8 | 1 | 2 | 1.1 |
| NS5-sma50-flush-oversold-long | 1 | 0% | −0.06 | −1.61 | - | 0.39 | 0/1 | 1 | - | - | 1 | 0 | 0.9 |
| NS4-pm-vwap-reclaim-oversold-short | 1 | 0% | −0.16 | −1.35 | - | 0.97 | 0/1 | 0 | - | - | 1 | 0 | 2.2 |
| RW5-heat30-fs-rsi5pop-gapdn-short-FD | 2 | 100% | +0.81 | +17.40 | 0.92 | - | 0/0 | 0 | 0.11 | - | 1 | 2 | 1.6 |
| MF4-h40-open-fs | 3 | 100% | +0.45 | +32.24 | 0.43 | - | 0/0 | 0 | 0.03 | - | 1 | 1 | 3.0 |

**Testing 1** (journal, 325 trades; setups with ≥ 3 trades or ≥ $25 either way; the full table is printed by `tables.py`)

| setup | n | win | avgR | P/L | mfe_w | mae_l | never | lost05 | gb_w | tmfe | clus | twin | lat | missing est |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| heat_fade_long | 13 | 0% | −1.04 | −216.48 | - | 1.04 | 12/13 | 1 | - | - | 2 | 6 | 1.4 | 13 / −106 |
| heat_fade_long-FD | 22 | 27% | −0.52 | −192.38 | 0.84 | 1.04 | 12/16 | 1 | 0.12 | 42/3 | 3 | 6 | 0.7 | 23 / −123 |
| LIQ-orl-sweep-open15-s25-long | 6 | 0% | −1.03 | −115.38 | - | 1.02 | 0/6 | 3 | - | - | 4 | 0 | 1.0 | 18 / −69 |
| RW7-gapdn-bounce-early-short-FD | 19 | 26% | −0.54 | −100.11 | 0.93 | 1.03 | 10/14 | 1 | 0.05 | 86/10 | 3 | 1 | 1.3 | 5 / −0 |
| ST2-slope20up-long-am-t05s1-FD | 8 | 25% | −0.64 | −85.63 | 0.62 | 1.00 | 4/6 | 0 | 0.07 | 14/2 | 3 | 0 | 1.1 | 4 / −24 |
| NS5-sma50-flush-oversold-long-FD | 4 | 0% | −1.06 | −84.16 | - | 1.06 | 4/4 | 0 | - | - | 1 | 0 | 0.8 | 10 / −46 |
| RW6-ns2-up3-short-FD | 2 | 0% | −1.08 | −32.45 | - | 1.06 | 2/2 | 0 | - | - | 1 | 2 | 1.6 | |
| NS2-sma50break-overbought-short-FD | 2 | 0% | −1.05 | −31.88 | - | 1.06 | 2/2 | 0 | - | - | 1 | 2 | 1.9 | |
| RW6G1-ns2-up3-vwap2sd-short-FD | 2 | 0% | −1.05 | −31.84 | - | 1.06 | 2/2 | 0 | - | - | 1 | 0 | 0.6 | |
| ST4-emadn-long-am-t1s05-FD | 3 | 0% | −1.14 | −29.92 | - | 1.08 | 2/3 | 0 | - | - | 2 | 0 | 0.8 | |
| RW1-gapdn-bounce-fs-short-FD | 3 | 0% | −1.05 | −24.80 | - | 1.03 | 3/3 | 0 | - | - | 1 | 2 | 1.9 | 1 / +0 |
| MF3-open-fs-rsi5hi-FD | 5 | 20% | −0.73 | −24.06 | 1.02 | 1.02 | 1/4 | 2 | 0.09 | 192/11 | 2 | 2 | 1.6 | 1 / +1 |
| RW3-gapdn-rsi5pop-fs-short-FD | 4 | 50% | −0.15 | −6.21 | 0.84 | 1.04 | 2/2 | 0 | 0.10 | 82/5 | 1 | 2 | 1.6 | 1 / −3 |
| MF1-945-fs-vwapup-FD | 6 | 50% | +0.10 | +3.88 | 1.66 | 1.13 | 0/3 | 3 | 0.02 | 36/12 | 3 | 3 | 0.8 | |
| MF5-fs-vwapup-rsi5hi-FD | 7 | 57% | −0.03 | +6.41 | 0.99 | 1.01 | 0/3 | 3 | 0.10 | 89/12 | 2 | 4 | 1.1 | |
| MF4-h40-open-fs-FD | 4 | 100% | +0.48 | +13.78 | 0.58 | - | 0/0 | 0 | 0.10 | - | 2 | 2 | 1.5 | |
| L3-gap-slope-lowdist-FD | 3 | 100% | +0.90 | +26.69 | 0.96 | - | 0/0 | 0 | 0.05 | - | 2 | 0 | 1.9 | |
| RW4-ns3-adv150-short-FD | 14 | 57% | +0.18 | +30.65 | 0.89 | 1.09 | 3/6 | 2 | 0.05 | 154/8 | 3 | 12 | 1.2 | 7 / +23 |
| L3-gap-slope-fromopen-FD | 7 | 71% | +0.42 | +33.60 | 1.20 | 1.03 | 1/2 | 0 | 0.19 | 72/1 | 1 | 1 | 1.1 | |
| NS3-failed-vwap-reclaim-short | 15 | 60% | +0.26 | +44.99 | 0.93 | 1.06 | 3/6 | 2 | 0.06 | 154/8 | 3 | 7 | 1.2 | 2 / +11 |
| RW2-exhaustion-noon-adv150-short-FD | 16 | 69% | +0.40 | +89.28 | 1.13 | 1.02 | 3/5 | 1 | 0.06 | 82/2 | 4 | 7 | 0.9 | 1 / −3 |
| NS3-failed-vwap-reclaim-short-FD | 18 | 61% | +0.32 | +89.92 | 0.94 | 1.09 | 3/7 | 2 | 0.04 | 154/13 | 4 | 10 | 1.4 | 7 / +27 |
| exhaustion_short-FD | 12 | 75% | +0.60 | +97.15 | 1.13 | 1.01 | 3/3 | 0 | 0.05 | 93/2 | 4 | 5 | 1.1 | 2 / +13 |
| heat_fade_short | 46 | 57% | +0.02 | +134.25 | 0.78 | 1.05 | 2/20 | 10 | 0.06 | 12/12 | 40 | 22 | 1.0 | 4 / +12 |
| heat_fade_short-FD | 75 | 61% | +0.13 | +241.74 | 0.95 | 1.05 | 8/29 | 11 | 0.05 | 83/12 | 40 | 24 | 1.3 | 25 / +44 |

T1 by side: longs (journal) 58 trades, 16% wins, −$741.21, and the replay adds 73 long lots (est. −$367). Shorts (journal) 267 trades, 57% wins, +$557.15, and the replay adds 59 short lots (est. +$147).

**Testing 2**

| setup | n | win | avgR | P/L | mfe_w | mae_l | never | lost05 | gb_w | tmfe | clus | twin | lat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CWT14-pdl-p05-lowvol-long | 29 | 45% | −0.41 | −61.10 | 0.53 | 1.02 | 9/16 | 2 | 0.08 | 31/2 | 6 | 17 | 1.5 |
| CWT13-vwapstretch-z05-long | 3 | 0% | −1.06 | −47.65 | - | 1.03 | 2/3 | 0 | - | - | 1 | 0 | 2.9 |
| CWT14-pdl-p10-lowvol-long | 12 | 58% | −0.21 | −21.23 | 0.46 | 1.02 | 4/5 | 0 | 0.06 | 82/2 | 4 | 5 | 0.9 |
| CWT09-gapdn-bounce-g5-lowerhalf-short | 1 | 0% | −1.12 | −19.56 | - | 1.04 | 0/1 | 0 | - | - | 1 | 0 | 1.0 |
| CWT12-coil-k6-long | 1 | 0% | −0.37 | −17.50 | - | 0.60 | 1/1 | 0 | - | - | 1 | 0 | 1.2 |
| CWT14-orl-p10-lowvol-long | 19 | 58% | −0.25 | −14.55 | 0.56 | 1.06 | 4/8 | 0 | 0.06 | 7/14 | 6 | 13 | 1.7 |
| NM-HL-T75-pm-long | 6 | 50% | −0.08 | −8.09 | 0.55 | 0.90 | 0/3 | 1 | 0.06 | 104/38 | 3 | 0 | 0.8 |
| NM-RWN3 / NM-RWR3 ns3 early shorts (each) | 2 | 50% | −0.16 | −6.00 | 0.96 | 1.10 | 1/1 | 0 | 0.18 | 254/15 | 2 | 2 | 0.8 |
| CWT14-pdl-p05-long | 39 | 59% | −0.10 | −4.29 | 0.59 | 1.02 | 8/16 | 2 | 0.09 | 32/2 | 8 | 13 | 0.8 |
| CWT14-pdh-p05-lowvol-short | 9 | 56% | −0.13 | −2.48 | 0.54 | 1.04 | 4/4 | 0 | 0.12 | 30/9 | 2 | 0 | 1.0 |
| CWT13-vwapstretch-z05-short | 5 | 40% | −0.12 | −1.74 | 0.92 | 1.02 | 0/3 | 1 | 0.02 | 58/15 | 2 | 0 | 2.1 |
| CWT14-pdl-p10-long | 22 | 64% | −0.19 | +1.06 | 0.41 | 1.01 | 4/8 | 0 | 0.07 | 36/6 | 3 | 11 | 1.0 |
| CWT14-pdh-p10-short | 4 | 75% | +0.04 | +3.90 | 0.53 | 1.69 | 0/1 | 1 | 0.04 | 39/10 | 1 | 0 | 1.6 |
| CWT14-orl-p10-long | 27 | 59% | −0.25 | +5.41 | 0.47 | 1.06 | 4/11 | 2 | 0.04 | 4/19 | 9 | 16 | 1.1 |
| CWT14-orl-p05-lowvol-long | 53 | 64% | −0.10 | +9.12 | 0.49 | 1.04 | 12/19 | 1 | 0.07 | 9/3 | 18 | 31 | 1.4 |
| CWT05-flush-m05-v3-long | 2 | 100% | +0.41 | +10.34 | 0.55 | - | 0/0 | 0 | 0.13 | - | 1 | 1 | 1.7 |
| CWT12-coil-k4-long | 7 | 86% | +0.33 | +10.51 | 0.61 | 1.00 | 1/1 | 0 | 0.09 | 114/0 | 4 | 0 | 1.2 |
| CWT14-orl-p05-long | 58 | 67% | −0.06 | +34.65 | 0.36 | 1.02 | 11/19 | 3 | 0.06 | 9/3 | 18 | 15 | 0.9 |
| NM-RWN5-ns3-mon-weakrs-short | 5 | 80% | +0.34 | +35.50 | 0.82 | 1.10 | 1/1 | 0 | 0.11 | 228/15 | 2 | 0 | 0.7 |

Four single trades are not in the table: CWT04 −$1.50, CWT05-m075 +$0.84, NM-ETF-late-dip +$9.40 and CWT13-z075-long +$11.70 (+$20.44 together). Several CWT14 setups show a positive P/L with a negative avg R; the reason is differences in risk size.

## 3. Losers vs. recurring patterns (`patterns_1019.csv`, `patterns_out.txt`; not merged into `research/bdi/patterns.csv`)

| loss type | earlier days (10-06..10-16) | today | where today |
|---|---|---|---|
| never_worked (MFE < 0.15R) | 23.7% | 27.0% | T1 44 (−$642), T2 37 (−$298); heat_fade_long(-FD) 16, CWT14-orl-p05-lowvol 7 |
| small MFE then failed | 20.4% | 22.5% | T1 38, T2 30 |
| gave_back_gains (MFE ≥ 0.5R) | 15.9% | 17.9% | heat_fade_short(-FD) 19, MF3-FD 4; Primary 9 of 19 losers |
| stopped_then_reversed | 11.8% | 15.6% | T1 22, T2 23 (CWT14 longs) |
| wrong_side_after_big_swing | 15.5% | 12.1% | ST2-FD 6, heat_fade_long-FD 3, ST4-FD 3; GEN-03 OCUL |
| late_hold | 11.8% | 4.9% (the T1 lots flattened at 15:55 are not in the journal) | T2 13 |

**Same loss mix as before; no new loss type.** Ties to existing work:

| existing item | how today's data bears on it |
|---|---|
| `gb-1019-twin-setup-exposure` (idea) | Supported in T2: twin entries −0.21R vs −0.10R. Not in T1: −0.06R vs −0.08R, where the 40-trade heat_fade_short pair made money. The 7 triple-lot names in Primary are the same mechanism. |
| `nightly-1016-primary-one-lot-per-symbol` (idea) | Mixed: today lot 3 was positive. |
| `gb-1019-post-peak-index-guard` and `gb-1019-cut-1100-fd` (ideas) | Consistent: 72–90% of the Primary/T1 give-back came from entries after the 10:05 peak. Primary's after-peak entries −$115. |
| `nightly-1016-trend-day-long-reversal-veto` (idea) | Today is not a trend day (SPY was back above its open by 10:30). The T1 long losses came from the opposite situation: longs bought after a rally. |
| giveback1019 BE050 / SO05BE | Primary's 10 losers that had reached ≥ 0.5R. Those exits are already failed on history, so they are not re-proposed. |

**One new concrete pattern: entries that chase the index's last hour** (`indexctx_out.txt`).
- Across Primary, T1 (including the 132 replayed trades) and T2, entries on the same side as QQQ's last-60-min move: **169 trades, 40% wins, −0.285R, −$660.78**.
- All other entries: 635 trades, 57%, −0.055R, +$113.23.
- At |move| ≥ 0.3%: 86 trades, −0.287R, −$333.
- It holds in 3 of 4 account-side cells (T1 longs, T2 longs, T1 shorts). Primary shorts go the other way (4 trades, +0.50R). It is one session and in-sample.
- Related ideas, all different from this one:
  - `bdi1016-dayclass-direction-gate` (failed): day-class at 10:00.
  - `gb-1019-post-peak-index-guard`: blocks entries *against* the index.
  - `nightly-1012-cwt14-long-index-confirm`: wants the index *with* the trade.
- Proposed as **`nightly-1019-index-chase-veto`** in `backlog_proposals.jsonl` (status idea, tag nightly-1019, 0 configs). Nothing was appended to `research/backlog.jsonl`.

## 4. Live-funds hold: Primary positive-day streak

- **Today Primary closed negative:** −$63.92 after costs, −$49.30 journal, −$50.70 broker.
- **Consecutive positive Primary sessions ending today: 0.**
- From `status.json` history, after costs, 10 sessions (10-06..10-19):

  | | 10-06 | 10-07 | 10-08 | 10-09 | 10-12 | 10-13 | 10-14 | 10-15 | 10-16 | 10-19 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | after costs | − | − | − | − | **+115.77** | − | **+60.35** | − | −14.41 (journal +7.17) | −63.92 |

- 2 of 10 sessions were positive after costs; the longest streak so far is 1. Since start: 350 trades, −0.161R, −$1,717.76 after costs.
- **The live-funds hold stays in place.**

## 5. Setup Generator account, day 1 (12:51 ET start; partial day)

| GEN setup | window | trades | win% | avgR (costs) | R(j) | P/L journal | P/L after costs | notes |
|---|---|---|---|---|---|---|---|---|
| 10 FlowShift ≥ 0.42, SMA50d ≥ 1.7, PM, BRop < 0.5, t1s1, **short** | 13:00–15:00 | 4 | 75% | +0.26 | +0.27 | +$97.24 | **+$94.06** | DOCN +$64.86 (flatten, 0.53R), RIG +1.14R, ZS +0.49R (41 bps slip), CELH stop −$47.83 |
| 03 Ret15m ≤ 0.12 ATR, FromOpen ≤ 0.34 ATR, SMA20 slope ≥ 0.29, PM, t05s1, **long** | 13:00–15:00 | 2 (1 skipped: SEDG spread 39 bps) | 50% | −0.60 | −0.49 | −$57.96 | **−$72.82** | OCUL stop −$81.73 (wrong_side_after_big_swing), SNDQ target +$8.91 (86 bps slip ate the 0.5R target) |
| 02, 06, 07, 09 (PM / late windows) | 13:00–15:00 / 14:00–15:00 | 0 | | | | | | no signals |
| 04 (MID 11:00–13:00) | partly covered | 0 | | | | | | only ~12:10–13:00 live |
| 01, 05, 08 (OPEN / AM 09:50–11:00) | not covered | 0 | | | | | | the account started at 12:10 / 12:51 |
| **total** | | **6** | **66.7%** | −0.03 | +0.02 | **+$39.28** | **+$21.24** | equity 100,039.28; scorecard "too few trades" for both |

Six trades on 2 of 10 setups are no evidence either way. Per the owner's rule (2026-10-19), no GEN setup is changed or removed. Proposals only.

## Housekeeping items (no strategy change)

| id | item |
|---|---|
| H-1 | Testing 1's final state push failed. The journal is missing 132 of 457 trades, so the EOD report and scorecard are built on 325. Retry or verify the final push. |
| H-2 | Testing 2 live scale-out: 0 completed and 14 failed after 5 tries ("error"), so the setups ran full-size. Log the broker error text in `health.scale_out_failed`. |
| H-3 | The Setup Generator job started at 12:10 / 12:51 ET. 4 of 10 GEN setups had no or partial window coverage on day 1. |

Educational only — not financial advice.
