# Nightly winner/loser autopsy: 2026-10-12 (primary, Testing 1, Testing 2)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They are a diagnosis, not evidence. No locked holdout was scored, and **0 configurations were tested on the history**. The tables below are descriptive splits of today's trades (about 20 one-session splits, none of them gated).*

Inputs: `journal.db`, `status.json`, `reports/2026-10-12.csv`, `reports/scorecard.json` and `intraday/2026-10-12.jsonl` from `origin/mcf-data`, `mcf-data-testing` and `mcf-data-testing2`. SIP 1-minute bars (Alpaca market data only, read-only; `fetch.py`, `fetch2.py`) for the 516 traded or ordered symbols plus SPY, QQQ and IWM. The EOD CSV has no MFE/MAE for real trades (`mae_r`/`mfe_r` are empty for run 1), so `build.py` recomputes MFE/MAE on the bars from entry to exit. Scripts and `trades.csv` (521 real trades) are in this folder.

## Failures first
- **The Testing 2 journal is missing trades.** 45 bracket orders (40 long, all submitted 09:51–10:52) and 20 in Testing 1 are still `submitted` in `orders`, with no trade row. Primary has none. The broker equity does not match the journal:
  - Testing 2 started at $100,000.00 (status 09:27) and ended at **$99,336.73**, which is **−$663.27**. The journal shows −$451.98, so **−$211.29 is not in the journal**.
  - Simulating the 45 orders on the bars (`ghost.py`: stop first, flat at 15:55, no costs) gives **−$172.20** (13 stops, 7 targets, 25 flat).
  - Journal open positions at 10:45 were 92. Adding the 42 ghost orders submitted by 10:45 gives about 134, which matches the lead's live count of 137.
  - Testing 1's equity is $30.19 below its journal (simulated ghosts: +$4.63).
  - Every reconciled early order (rank ≤ the last ghost) exited by a stop or target leg. None exited by the flatten.
  - **Likely cause** (not confirmed against the broker): `reconcile_day` only sees orders returned by `closed_orders_today()`, which is `get_orders(CLOSED, nested=True, limit=500)` with no pagination. Older parents drop out of that window on busy accounts.
  - This is housekeeping (rule 15), so it is not a backlog item. Until it is fixed, Testing 2 and Testing 1 per-setup P/L, the scorecards and the leaderboard **understate losses**: the 45 ghosts are mostly CWT14 ORL/PDL longs.
- **Testing 2 lost about 40R in one session** (journal −40.3R, −$451.98; broker −$663.27).
  - The loss is in line with the selection: 25 of the 28 setups whose comments could be parsed are negative after costs on the open history (config header: "NONE of these setups passed"). The busy CWT14 variants score −0.086 to −0.096R there, and today's realised rate was −0.128R per trade.
  - The account was green for only 5 minutes (10:07–10:12, peak +$18).
- **Longs lost in all three accounts on a down-drift day.**
  - SPY was −0.09% open to close (low −0.22% at 14:52). QQQ was −0.49% (−0.65% at 14:52). IWM was −0.22%. Among traded names, 33–38% were above their open from 10:00 to the close.
  - Primary had 1 long. Testing 1: shorts +$136.14, longs −$87.76. Testing 2: shorts +$107.25, longs −$559.23.
- **Testing 1 gave back $136 after 14:52.** The intraday peak was +$184.08 and the close +$48.38. RW7 lost −$85 and heat_fade_short-FD −$36 in the last hour on flatten-held shorts. 29 losers were flattened red, for −$145.
- **Testing 1's demoted setups were quiet.**
  - heat_fade_short: 3 trades, −$22.03.
  - heat_fade_long (windowed): 9 trades, +$5.07. heat_fade_long-FD: 9 trades, −$51.79, the worst setup in the account.
  - exhaustion_short: 0 trades (its only FD order, ALHC, is a ghost).
  - **orb20_a and intraday_momentum logged 0 signals.** The playing-time "silent" list is empty, so the wiring should be checked.

## Headline per account (real trades, run 1)
| account | trades | win% | avg R | P/L | cost-adj | stop / target / flatten | green intraday |
|---|---|---|---|---|---|---|---|
| primary (11 setups) | 22 | 73% | +0.370 | **+$117.93** | +$115.77 | 4 / 15 / 3 | from 10:22 to the close (peak +$136.35 at 14:49) |
| Testing 1 (37) | 184 | 57% | +0.074 | **+$48.38** | +$33.94 | 41 / 64 / 79 | from 12:40 (min −$114.69 at 12:05, peak +$184.08 at 14:52) |
| Testing 2 (30) | 315 | 56% | −0.128 | **−$451.98** (broker −$663.27) | −$525.68 | 116 / 165 / 34 | only 10:07–10:12 (min −$723.10 at 14:50) |

Latency (signal to fill) has a median of 1.3–2.3 s in every account, with no winner/loser difference. Entry slip: losers have a median of 1.1–3.2 bps and winners 1.8–3.4 bps. No account entered before 09:50, and every exit was at or before 15:56:50.

## Primary
| setup | n | win% | avg R | P/L | stops | MFE | MAE | time to MFE (median, min) |
|---|---|---|---|---|---|---|---|---|
| NS5-sma50-flush-oversold-long | 1 | 100 | +1.16 | +43.03 | 0 | 1.20 | 0.06 | 119 |
| MF3-open-flowsell-rsi5hi | 7 | 71 | +0.41 | +30.46 | 2 | 0.85 | 0.51 | 115 |
| MF5-flowsell-vwapup-rsi5hi | 5 | 60 | +0.41 | +20.46 | 0 | 0.69 | 0.39 | 110 |
| MF4-h40-open-flowsell | 6 | 83 | +0.25 | +13.34 | 1 | 0.55 | 0.47 | 11 |
| MF1-945-flowsell-vwapup | 1 | 100 | +1.53 | +11.26 | 0 | 1.50 | 0.16 | 29 |
| NS2-sma50break-overbought-short | 1 | 100 | +0.28 | +6.52 | 0 (flatten) | 0.76 | 0.24 | 276 |
| MF2-open-rsimidhi-flowsell | 1 | 0 | −1.19 | −7.14 | 1 | 0.68 | 1.06 | 4 |

- **Winners vs losers.**
  - Winners (16): MFE 0.94R, MAE 0.30R, time to MFE 117 min.
  - Losers (5): MFE 0.28R, MAE 0.97R, time to MFE 4 min.
  - The losers went against the trade almost at once. Four of the five would have won on the opposite side with a 1R/1R exit (0 of 16 winners).
- 13 of 22 entries came at 10:30–10:59 (+$47.56). The MF3/MF4/MF5 shorts into the 10:30–10:55 flow-sell cluster carried the day. 20 signals were skipped as "already in symbol"; their simulated what-if is +0.084R and 1.7R in total.

## Testing 1 (37 setups)
- **Best:** heat_fade_short-FD 40 trades, +$74.26, +0.26R. RW5 10 trades, +$40.65, +0.59R. RW3 5 trades, +$30.66. RW2 10 trades, +$19.75.
- **Worst:** heat_fade_long-FD 9 trades, −$51.79, −0.52R, 6 stops. RW4-ns3-adv150 6 trades, −$30.96. ST2 18 trades, −$30.45. RW7 32 trades, −$27.91 (20 flattens).
- **Time of day:**
  - 09:50–09:59: 9 trades, −0.49R, −$44.62.
  - 11:00–11:59: 50 trades, +0.33R, +$140.02.
  - 13:30–14:59: 41 trades, −$107.08.
- **Loss types (79 losers):** late hold 29 (−$145), wrong side after a big swing 11 (−$143), small MFE then failed 10, gave back gains 15, never worked 11, stopped then reversed 3.
- Peak open positions: 99 (journal) / 101 (scorecard), at about 14:20.

## Testing 2 (30 CWT setups, first session)
| setup | n | win% | avg R | P/L | stops | MFE | open-history exp R (t) |
|---|---|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-lowvol-long | 48 | 33 | −0.470 | −217.82 | 27 | 0.28 | −0.090 (−9.4) |
| CWT14-failbrk-pdl-p05-lowvol-long | 26 | 50 | −0.253 | −94.44 | 11 | 0.31 | −0.096 (−10.0) |
| CWT14-failbrk-orl-p05-long | 38 | 53 | −0.124 | −76.60 | 14 | 0.42 | −0.094 (−10.1) |
| CWT14-failbrk-orl-p10-long | 16 | 56 | −0.109 | −55.09 | 7 | 0.40 | −0.091 (−7.1) |
| CWT14-failbrk-pdl-p05-long | 14 | 50 | −0.140 | −43.32 | 3 | 0.35 | −0.088 (−10.1) |
| CWT12-coil-k6-long | 10 | 10 | −0.762 | −37.27 | 9 | 0.58 | −0.070 (−4.7) |
| CWT13-vwapstretch-z05-long | 4 | 25 | −0.591 | −24.69 | 2 | 0.14 | −0.080 |
| CWT05-flush-m05-v3-long | 1 | 0 | −1.0 | −20.70 | 1 | 0.25 | −0.136 |
| CWT12-coil-k4-long | 39 | 67 | −0.032 | −16.86 | 11 | 0.43 | −0.075 |
| CWT14-failbrk-pdl-p10-long | 11 | 64 | +0.121 | −16.01 | 3 | 0.56 | −0.086 |
| CWT14-failbrk-pdh-p10-short | 21 | 62 | −0.092 | −2.72 | 8 | 0.45 | −0.096 |
| CWT14-failbrk-pdh-p10-lowvol-short | 17 | 59 | −0.081 | +1.35 | 7 | 0.51 | −0.089 |
| CWT04-backside-lh-a15-short | 1 | 100 | +0.637 | +4.48 | 0 | 0.86 | +0.142 |
| CWT13-vwapstretch-z05-short | 5 | 60 | +0.137 | +5.57 | 1 | 0.79 | −0.069 |
| CWT14-failbrk-pdl-p10-lowvol-long | 8 | 75 | +0.245 | +9.95 | 1 | 0.51 | −0.095 |
| CWT14-failbrk-orl-p10-lowvol-long | 32 | 75 | +0.130 | +33.62 | 7 | 0.46 | −0.089 |
| CWT14-failbrk-pdh-p05-lowvol-short | 23 | 78 | +0.162 | +37.78 | 4 | 0.50 | −0.095 |
| CWT09-gapdn-bounce-g10-lowerhalf-short (S) | 1 | 100 | +0.280 | +60.79 | 0 | 0.35 | — |

The other 12 setups made no trades; most of them are low-frequency, and CWT09 was blocked by borrow (below).

### Drivers of the −$452 (journal) / −$663 (broker)
1. **CWT14 failed-breakdown longs.** 193 trades, −0.156R, **−$459.7**, which is more than the whole loss. Shorts in the same family made +$36.4.
   - p05 variants (shallow 0.05-ATR penetration): 149 trades, −0.215R, −$394. p10 variants: 105 trades, +0.023R, −$29. The open history scores both about −0.09R, so this split is probably noise.
   - Losers: MFE 0.16R and time to MFE 2.2 min, meaning they never moved in the trade's favour. 55 of 116 stops had MFE < 0.1R. "Never worked" covers 54 trades and −$490 across the account.
   - The opposite 1R/1R side would have won on 114 of 139 losers (and on 23 of 176 winners).
2. **Exit mix.** Stops: 116 trades, −$1,056.24, −1.03R on average. Targets: 165 trades, +$616.91, +0.52R. Flatten: 34 trades, −$12.65. Most setups use t05s1, which needs more than 67% winners before costs; the account won 56% (longs 53%).
3. **Crowding.** Open positions (journal): 92 at 10:45 and a peak of 101 at 11:00. About 134–137 including the ghosts, and the scorecard peak is 107. 180 of the 315 entries (57%) came at 10:00–10:59, for −$226.47.
   - Longs entered while >20 longs were already open: 211 trades, about −0.22R. With ≤20 open: 36 trades, +0.067R. This is descriptive only.
   - The per-setup cap of 25 bound only CWT12-coil-k4-long: 37 skips at 10:40–11:30, what-if −0.023R.
4. **Skips.**
   - 350 signals were held by another setup (what-if −0.248R, −86.8R in total: the skips were worse than the takes).
   - 109 were realism skips: 53 for spread ≥ 25% of the stop (−0.227R) and 49 for spread over the bps cap.
   - 31 were not shortable (−0.491R) and 5 hit the size floor.
5. **Structural-exit "S" shorts.** Only one traded: CTNM, CWT09 g10, entry 11:31, stop 23% above. Its 1R was **$217, against a median of $7.25**, because the risk budget binds instead of the slot cap. It made +$60.79 at +0.28R: one trade equal to about 8R of the account's typical risk.
   - 26 of 29 CWT09 signals could not be traded: 25 were not shortable (mostly leveraged single-stock ETFs) and 2 failed the spread cap.

### Execution-bug check
- **Clean.**
  - No stop or target on the wrong side of entry, no trade with 0 shares, and no P/L whose sign disagrees with its R.
  - No target exit at negative R and no stop exit at positive R.
  - No overlapping positions in the same symbol in any account. 40 symbols in Testing 2 were traded 2–3 times one after another, which the design allows.
  - One trade lasted under 30 s (SSPC, target hit after 32 s, legitimate).
  - Stop slippage: worst −1.54R (LABD coil-k6, a 0.34% stop on a $7.70 3x ETF) and −1.34R (CPNG). The median stop exit is −1.02R.
- **Targets traded through without a fill:** 2 of 150 non-target exits (`touch.py`). On CCI (short), the 11:01 bar's low of 79.27 was 8c through the 79.35 limit; the trade was later stopped for −$8.69. On AXON, the high was 15c through and the trade was flattened. These are probably SIP prints the paper engine does not fill on. Watch only.
- **Unreconciled orders (above): a real defect in the journal/reporting path. It does not affect trading.**

## Recurring patterns (`research/bdi/patterns.csv` + today's 223 losers in `patterns_1012.csv`; the classifier is the 10-09 precedence without the news check)
- Book-wide, every loss type has now been seen on 4–5 sessions. Today added: never worked 67, late hold 51, small MFE then failed 41, gave back gains 25, wrong side after a big swing 22, stopped then reversed 17.
- **New setup × loss-type patterns that reached 3 sessions:**
  - heat_fade_long × wrong side after a big swing: 12 trades (10-06, 10-09, 10-12). New backlog item.
  - MF5 × never worked: 4 trades (10-08, 10-09, 10-12). New backlog item (analysis).
  - heat_fade_long × never worked, × gave back gains and × late hold. heat_fade_short × never worked, × gave back gains and × stopped then reversed. These are covered by the heat_fade_long holdout fail (−0.138R) and by `loop-1009-hfs-small-mfe-scratch`.
- **heat_fade_short × small MFE then failed** is now on 4 sessions (11 trades): `loop-1009-hfs-small-mfe-scratch` stays open.
- **The opposite side would have won on 4 of 5 primary losers, 39 of 79 in Testing 1 and 114 of 139 in Testing 2.** This is the same pattern as `loop-1009-opposite-side-family`. Today's day type was a down-drift, and the bdi-rg-* gates found no regime signal at entry, so there is no new rule.
- **Shorts beat longs in every account.** Same regime dependence as bdi-rg-* and `bdi-rg-beta-hedged` (open).

## 3-market-day scorecard (Oct 8, 9, 12; journal real trades; `scorecard3.csv`)
Primary by day: 10-08 48 trades / −$120.66 / −0.134R. 10-09 70 / −$238.87 / −0.168R. 10-12 22 / +$117.93 / +0.370R. **Total 140 trades, −$241.60.** Win% and avg R in the table are over the 3 days.

| primary setup | n | win% | avg R | 10-08 | 10-09 | 10-12 | total | exp R (backtest) | scorecard verdict | live |
|---|---|---|---|---|---|---|---|---|---|---|
| NS5-sma50-flush-oversold-long | 5 | 60 | +0.51 | – | +29.4 | +43.0 | +72.46 | +0.002 | too few | yes |
| NS2-sma50break-overbought-short | 3 | 100 | +0.61 | +33.3 | – | +6.5 | +39.83 | +0.021 | too few | yes |
| MF3-open-flowsell-rsi5hi | 15 | 67 | +0.19 | +2.5 | +3.5 | +30.5 | +36.37 | −0.034 | positive so far | yes |
| NS1-rsidip-rsi5pop-long | 3 | 100 | +0.48 | – | +25.7 | – | +25.72 | +0.056 | too few | yes |
| orb20_a | 2 | 100 | +0.77 | +4.3 | +5.4 | – | +9.68 | −0.040 | too few | demoted |
| NS4-pm-vwap-reclaim-oversold-short | 2 | 50 | +0.06 | +8.3 | – | – | +8.33 | −0.080 | too few | yes |
| exhaustion_short | 19 | 42 | −0.18 | −105.7 | +106.9 | – | +1.19 | −0.020 | below backtest | demoted |
| MF1-945-flowsell-vwapup | 7 | 43 | +0.32 | −6.2 | −7.0 | +11.3 | −1.95 | −0.050 | too few | yes |
| MF5-flowsell-vwapup-rsi5hi | 18 | 44 | −0.00 | −24.1 | −8.0 | +20.5 | −11.62 | −0.010 | negative so far | yes |
| MF2-open-rsimidhi-flowsell | 2 | 0 | −1.10 | −8.0 | – | −7.1 | −15.13 | +0.046 | too few | yes |
| MF4-h40-open-flowsell | 12 | 50 | −0.09 | −17.0 | −39.5 | +13.3 | −43.23 | −0.017 | negative so far | yes |
| heat_fade_long | 13 | 31 | −0.19 | −8.0 | −52.2 | – | −60.25 | −0.138 | negative so far | demoted |
| NS3-failed-vwap-reclaim-short | 8 | 38 | −0.23 | – | −76.3 | – | −76.25 | −0.136 | too few | yes |
| heat_fade_short | 31 | 32 | −0.37 | – | −226.7 | – | −226.75 | −0.015 | below backtest | demoted |

- **Testing 1 (10-09 + 10-12, 230 trades, +$23.35 journal):**
  - Over both days: RW2-exhaustion-noon +$44.0 (18 trades), RW5 +$49.5 (11), NS5 +$31.3 (6), NS1 +$14.2 (4).
  - 10-12 only (the FD variants started that day): heat_fade_short-FD +$74.3 (40). heat_fade_long-FD −$51.8 (9), ST2 −$30.4 (18), RW7 −$17.6 over both days (34).
  - No Testing 1 setup is flagged "below backtest" yet. Every one is "too few trades" or "positive/negative so far".
- **Testing 2 (1 session):** see the table above. The scorecard already flags 3 setups "below backtest – review": orl-p05-lowvol, pdl-p05-lowvol and coil-k6. Its P/L excludes the 45 ghost orders.
- 3 sessions is far below the forward gate (≥ 20 sessions, ≥ 60 trades). Nothing here is evidence for or against any setup (rules 7 and 13).

## Hypotheses added to `research/backlog.jsonl` (status "idea", source "nightly-2026-10-12")
| id | category | from |
|---|---|---|
| `nightly-1012-cwt14-long-index-confirm` | setup (parent cwt-b-b3) | CWT14 reclaim longs −$460 into a down-drift; 38 losers never worked |
| `nightly-1012-same-side-crowding-cap` | risk | Testing 2 long crowding buckets (descriptive) |
| `nightly-1012-structural-exit-risk-normalize` | risk | CTNM S trade with 1R = $217 vs a $7 median |
| `nightly-1012-hfl-big-swing-skip` | setup (parent live-heat_fade_long) | new 3-session pattern (12 trades) |
| `nightly-1012-mf5-never-worked` | analysis | new 3-session pattern (4 trades) |
| `nightly-1012-cwt09-etb-universe` | analysis | 26 of 29 CWT09 signals not tradable live |

The new entries have the same keys as the existing loop entries, plus `tags` (requested by the lead), and the ids are unique. `python -m mcf.research.backlog list` reads all 375 entries.

## Housekeeping for the lead (not backlog)
- **H-1.** Reconcile the 45 + 20 `submitted` orders, and paginate `closed_orders_today` (or fetch the missing parents by id) so that journal = broker. Then re-run the Testing 1/2 scorecards for 10-12.
- **H-2.** Check why orb20_a and intraday_momentum logged no signals in Testing 1, and why the playing-time "silent" list does not flag them.
- **H-3.** The EOD CSV `mfe_r`/`mae_r` columns are empty for real trades. Fill them from the bars, as `build.py` does here.
