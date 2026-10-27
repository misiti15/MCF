# Nightly learning loop, 2026-10-27 (Tuesday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **8 configurations were replayed tonight**
(ST-P: none / latch 1.5 / 2 / 3R on Primary's live trades; 15:45 vs 15:55 flatten on all live trades; 3 low-age buckets
for the CWT14 pdl longs). No backtest, no locked block, no holdout. No config, setup or exit was changed. About 50
descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster, latency, $-risk quartile per account,
inverse-ETF longs, QQQ-low age, QQQ vs VWAP for the MF shorts, early shorts, re-entry after a stop, 15:45 flatten), so
some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is "R(j)".

**Start / handover (known, not a new fault):** GitHub missed the 08:35 ET schedule again; the session guard dispatched
trade.yml run #149 at 08:43 ET; all 5 jobs ran pre-market prep and traded from the 09:30 warm-up poll. #149's Trade steps
ended 14:27:45-14:28:58 ET ("job 08:47 done") and standby run #155 took over (its Trade steps started 14:28:29-14:29:45 ET,
"job 14:28/14:29 done" at 15:56). Handover gap in the poll logs: Primary 1.8 min (14:27:18 → 14:29:06), Testing 1 2.1,
Testing 2 3.3 (14:25:15 → 14:28:32), Graveyard 3.5, Gen 4.5 (14:25:18 → 14:29:48); no 5-minute decision minute was missed.

**Moves effective today:** CWT13-vwapstretch-z05-long Primary → Testing 2; CWT12-coil-k6-long Testing 1 → Graveyard;
10 new GEN setups; **GX1** (5-minute clock gate for lab setups) live.

**Scripts** = nightly1026's with the date set to 10-27, plus four new descriptive checks: `patterns.py` (inverse-ETF longs,
CWT14 pdl longs by QQQ-low age, early shorts), `qqqvwap.py` (MF shorts by QQQ vs VWAP), `cooldown.py` (re-entry after a
stop), `flat1545.py` (15:45 vs 15:55 flatten replay; fetches SIP bars 15:44-15:46). Run as in nightly1023 with
`<scratch>` holding each account's journal.db / status.json / reports / intraday and `QQQ_hist.parquet` (SIP 10-06..10-27).

**Market: up day after an early dip.** SPY +0.30% (low −0.28% 10:21, high +0.50% 15:45); QQQ +0.86% (low −0.21% 10:17,
high +1.09% 15:46); IWM +0.80% (low −0.38% 10:02).

## Failures first

1. **Closed clean in all 5 accounts.** Phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages;
   "flatten complete: no MCF positions open" (Testing 2 job log; the others' status = 0 positions); journal trades =
   EOD report rows = `status.today.trades` in every account (58 / 189 / 238 / 392 / 89); EOD report + scorecard pushed
   19:57-19:58 UTC (scorecard as of 15:57-15:58 ET).
2. **Testing 2: 2 submitted entries never reconciled** — Z (CWT14-failbrk-pdl-p05-lowvol-long, 10:10) and SLN
   (CWT12-coil-k4-long, 10:20) are still `submitted` in the journal's `orders` table (240 submitted signals vs 238 trade
   rows). The account ended flat, so if they filled they were flattened; reconcile looks back up to 7 days for open
   journal orders, so the next session will either journal them (dated 10-27) or mark them expired. Housekeeping watch
   (row HK-RECON), no owner action. Until then they hold a lot slot on Z / SLN in Testing 2.
3. **Poll counts below 90% in Testing 2 (82%), Graveyard (72%) and Gen (65%)** of Primary's 384 (1/min 09:30-15:54),
   but **every 5-minute decision minute (77 of 77) was polled in every account**: the slower accounts skip the 1st/2nd
   minute of a bucket (exp % 5 = 1/2), which GX1 lab setups never use. Non-lab setups (orb20_a, exhaustion_short,
   heat_fade_*) in those accounts are checked less often. No gap > 5 min (longest = the handover, 4.5 min Gen).
   OPS-POLL: the GX1 load (more lab evaluations per poll) now shows in three accounts instead of one; housekeeping.
4. **No broker rejects, no price-crosscheck skips, no "missed: triggered" skips.** Testing 1's pre-submit guard skipped
   2 "price already through target" signals (H-1 guard, as intended).

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`)

| account | polls | % of 384 | decision minutes polled | longest gap | handover gap |
|---|---|---|---|---|---|
| Primary | 384 | 100% | 77 / 77 | 1.8 min (14:27) | 1.8 min |
| Testing 1 | 383 | 99.7% | 77 / 77 | 2.1 min (14:27) | 2.1 min |
| Testing 2 | 316 | **82%** | 77 / 77 | 3.3 min (14:25) | 3.3 min |
| Graveyard | 277 | **72%** | 77 / 77 | 3.5 min (14:25) | 3.5 min |
| Gen | 248 | **65%** | 77 / 77 | 4.5 min (14:25) | 4.5 min |

(`polls_out.txt`'s "symbol_decisions_missed" still uses the old bar-count rule for lagging symbols; under GX1 a symbol
that missed a minute is evaluated when its bucket completes, so that column overstates misses.)

Moved setups traded only in their new accounts: CWT13-z05-long Testing 2 only (3 trades −0.82R); CWT12-coil-k6-long
Graveyard only (11 trades, +0.27R, +$72.93).

## 1. Headline per account (real trades)

| account | trades | win% | avgR (costs) | **P/L after costs** (before) | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|
| Primary | 58 | 66% | +0.110 | **+$87.73** (+$99.57) | 14 / 30 / 14 | trough −$76 (10:24) → peak +$97 (15:36) → +$88 |
| Testing 1 | 189 | 43% | −0.321 | **−$406.88** | 82 / 63 / 42 | never above 0; trough −$421 (15:50) |
| Testing 2 | 238 | 58% | −0.162 | **−$261.04** | 85 / 118 / 32 | +$17 (11:45) → −$298 (15:36) |
| Graveyard | 392 | 58% | −0.120 | **−$949.76** | 125 / 209 / 58 | +$100 (10:02) → −$1,149 (15:46) |
| Gen | 89 | 63% | +0.168 | **+$564.80** | 17 / 15 / 57 | −$74 (11:12) → +$863 (15:46) → +$565 |

Total after costs −$965.15. **Shorts lost everywhere but Primary** on the rally from the 10:17 low: T1 −$375, T2 −$254,
Graveyard −$1,224; longs T1 −$32, T2 −$7, Graveyard +$275, Gen +$535. Primary's shorts made +$90.73
(MF2-FD +$47.05, RW3-FD +$35.82, RW5-FD +$24.63).

**Primary live-funds hold:** +$87.73 after costs (+$99.57 before) → positive-day streak **2** (10-26 +$33.67, 10-27 +$87.73;
2 of the 3 needed for M1). Since Day 1 (10-23): 2 of 3 sessions positive, **+$29.34**. Since start: 5 of 16, −$992.02.

**GX1 effect on trade counts:** 966 trades vs 665/day on 10-21..10-23 (full sessions): Primary 58 vs 68 (setup mix changed:
3 fewer setups), Testing 1 189 vs 148 (+28%), Testing 2 238 vs 125 (+90%), Graveyard 392 vs 301 (+30%), Gen 89 vs 23
(new GEN setups every night). Replay expected +57 / +39 / +51 / +20 / +26%; the setup mix and today's CWT14 / coil bursts
confound the comparison, so this is a first read, not a measurement.

### 1a. Intraday peak vs close (`giveback_out.txt`)
- **Primary:** CWT14-failbrk-pdl-p10-lowvol-long bought 12 names in the 10:10 poll before the 10:17 index low (trough
  −$76 at 10:24; 34 trades on the day −0.035R, −$14.26). The shorts carried it to +$97 at 15:36; no give-back.
- **Testing 1** never got above zero: MF3-open-flowsell-rsi5hi-FD tripped −2R at 10:33 and kept shorting (14 more trades,
  −8.5R after the trip), CWT14-failbrk-pdl-p05-long tripped 10:48 then 26 more trades (−8.8R), exhaustion_short 0 of 6.
- **Testing 2:** exhaustion_short-FD −$119.70 (6 never worked), MF5-FD −$59.37 (1 of 14 won, −8.7R after its 10:33 trip),
  L3-rsi5hi-FD MRNA shorted 3 times (−$74). CWT12-coil-k4-long +$106.98 (73 trades, 75% win) held it up.
- **Graveyard −$1,050 from 10:02:** CWT14 pdh shorts took 25 entries in the 09:55 poll (pdh-p10 34 trades −$270.92,
  p05-lowvol −$256.64), RW2-exhaustion-noon-adv150-short-FD −$375.14, heat_fade_short 0 of 9 (−$223.39). The ORL longs
  made +$208.59.
- **Gen +$863 at 15:46 → +$565:** GEN-261021-06 (ORB-fail-up, hold to close) 25 trades +13.1R, +$440.99; 44 open winners
  gave back $279 in the last 9 minutes as the index dipped into the 15:55 flatten (→ backlog nightly-1027-flatten-1545).

## 2. Winner / loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 966 trades)

- **Losers "never worked" again:** losers' median MFE 0.20-0.31R; 202 losers never reached +0.2R (P 8 / T1 48 / T2 50 /
  GY 82 / Gen 14, −$2,509 together); only 62 losers had been ≥ +0.5R. Winners reach MFE late (median 25-153 min), losers
  peak early (4-31 min). Winners give back little (median 0.06-0.08R, Gen 0.27R).
- **Clusters:** Primary same-setup clusters > 9 (CWT14 pdl, 10:10) −0.34R vs singles +0.43R; T2 > 9 −0.30R; Graveyard
  no clean order (twins +0.06R vs −0.20R non-twin). The burst-skip ideas already failed on two years (nightly-1015 shorts,
  nightly-1026 coil); no new item.
- **CWT14 pdl longs and the index low** (`patterns_out.txt` B, all live trades since 10-06): entries within 15 min of
  QQQ's low of day 472 trades −0.214R vs +0.00R later (all four versions same order), but 10-14 is −77R of it and today
  is the opposite (< 15 min +8.2R, later −45.7R) → backlog `nightly-1027-pdl-long-index-low-age` (rework of the failed
  nightly-1012 index-confirm lineage).
- **15:45 flatten** (`flat1545_out.txt`, 1,669 lots flattened at 15:55 since 10-06): closing at 15:45 +27.8R (12 of 16
  days better, t 1.24, best day 38% of the gain; longs +35.4R, shorts −7.5R) → backlog `nightly-1027-flatten-1545`.
- **Checked, no pattern:** inverse-ETF longs (94 trades −0.11R vs −0.13R other longs); MF1/3/5 "sellers into strength"
  shorts by QQQ above / below VWAP (both lose; ix-gate already failed on two years); shorts before 10:00 (−0.17R vs
  −0.10R; the gap is day direction, i.e. lookahead); re-entry after a stop on the same symbol (−0.07R vs −0.12R, no worse).
- **Latency:** medians 1.1-1.4 s; no consistent tercile order across accounts.
- **Testing accounts after the −2R mark** (`rearm_out.txt`; per-setup stop is off there since 10-23, ST-A): today 7
  setup-days kept trading after −2R and lost another −37.8R (T1 CWT14-pdl-p05 −8.8R, T2 MF5-FD −8.7R, T1 MF3-FD −8.5R,
  T2 CWT14-pdl-p05-lowvol −5.1R); since 10-23 −29.9R over 3 sessions (10-23 +8.4R). Same question as ST-P; no new item.

## 3. Backlog (2 new, status idea)
- `nightly-1027-flatten-1545` (exit)
- `nightly-1027-pdl-long-index-low-age` (setup; parent nightly-1012-cwt14-long-index-confirm, failed lineage)
No swarm tonight: 2 new ideas (< 3) and no setup is near a gate.

## 4. Suggestions (`combined_out.txt`; all accounts merged, 16 sessions, costs in; yardstick research/ops/primary_bar.md)

- **DECISION K4 (due: K4-WATCH, owner 10-26 "wait 20-30 more trades")** — Coil Under the High (4 bars)
  (CWT12-coil-k4-long, Testing 2) → Graveyard: 73 more trades since then (+0.086R, +$107 today), record now 349 trades /
  12 sessions, 64.5% win vs 68.9% needed, −0.078R, w/o best day (10-23) −0.109R (total negative, no best-day share),
  t_day −0.75, last 4 sessions 159 trades −0.099R, −$84.45; 2-year −0.075R (BDI 10-26: both sides of the coil signal
  lose after costs). Its 6-bar sibling made +$72.93 on its first Graveyard day, which does not change the record.
- **Demotion watch, not raised (one bad day):** Sellers into Strength (all day) (MF5-flowsell-vwapup-rsi5hi-FD, Testing 2)
  65 trades, 37% win vs 51% needed, −0.293R, −0.383R w/o best day, last 4 −0.554R, −$66.57, 2-year −0.010R; but today
  (−13.3R) is 70% of its loss (before today −0.11R on 51). Its base (MF5-flowsell-vwapup-rsi5hi, T1+T2) 56 trades −0.206R,
  last 4 −0.807R. Early Sellers into a Pop (all day) (MF3-open-flowsell-rsi5hi-FD, Testing 1) 124 trades −0.195R, last 4
  −0.467R, today −13.0R. Re-check after Friday's review.
- **N3 (waiting on owner) update:** NS5-sma50-flush-oversold-long-FD 32 trades, 34% win vs 70% needed, −0.454R, −$271.11.
- **No promotion is ready:** L3-gap-slope-rsi5hi-FD (Testing 2) 60 trades +0.123R but −0.015R w/o best day (10-26 = 108%,
  **1 day**); GEN-261021-06 (Gen) 37 trades +0.336R, −0.058R w/o best day (today 106%, **1 day**).
- **Primary's three remaining shorts all carry the 1-day tag (best day 10-22):** Early Sellers, Mid-High RSI (all day)
  (MF2-open-rsimidhi-flowsell-FD) 59 trades +0.775R, +0.458R w/o best day (64%); RW3-gapdn-rsi5pop-flowsell-short-FD 83,
  +0.444R / +0.217R (66%); RW5-heat30-flowsell-rsi5pop-gapdn-short-FD 92, +0.381R / +0.244R (56%) — all still positive
  without it. Early Sellers, Strong Heat (all day) (MF4-h40-open-flowsell-FD) 63, +0.118R / +0.048R (65%), last 4
  −0.125R, 2-year −0.017R: drift watch for Friday's ROT review.
- **CWT14 watch closed:** CWT14-failbrk-pdl-p10-lowvol-long moves Primary → Testing 2 from 10-28 (owner rotation, PR #126).

## 5. ST-P live replay (`stp_out.txt`; 4 configs, counted)

Primary 16 sessions (10-06..10-27), latched per-setup stop vs none: 1.5R +17.96R (6/5 days, t 0.76), **2R +21.10R**
(6/4, t 0.90), 3R +10.03R (5/4, t 0.75); best day (10-22) give-up 0.8-1.7R. Today 2R / 3R no change, 1.5R −1.69R. Not materially changed (10-26: 2R +21.10R); ST-P stays "revisit later".

Educational only — not financial advice.
