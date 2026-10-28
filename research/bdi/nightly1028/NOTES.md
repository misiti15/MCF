# Nightly learning loop, 2026-10-28 (Wednesday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **8 configurations were replayed tonight**
(ST-P: none / latch 1.5 / 2 / 3R on Primary's live trades; 15:45 vs 15:55 flatten on all live trades; 3 low-age buckets
for the CWT14 pdl longs), the same 8 as 10-27 with one more session. No backtest, no locked block, no holdout. No config,
setup or exit was changed. About 45 descriptive splits were looked at (setup, side, hour, exit, poll, lot, twin, cluster,
latency, $-risk quartile per account, inverse-ETF longs, QQQ-low age, QQQ vs VWAP for the MF shorts, early shorts,
re-entry after a stop, 15:45 flatten, NS3-family repeat / theme), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`; the journal's `r_multiple` is "R(j)". The Day 4
message-board post and the job-log review show P/L **before** costs (Primary +$246.76); after costs it is +$245.88.

**Scripts** = nightly1027's with the date set to 10-28, plus `decmin.py` (decision-minute coverage + handover gap from the
poll logs) and `ns3fam.py` (NS3-family shorts: repeat entries on a symbol, theme). `<scratch>` holds each account's
journal.db / status.json / reports / intraday (from the data branches), `bars/` (SIP 1-min, `fetch.py`, 580 symbols) and
`QQQ_hist.parquet` / `SPY_hist.parquet` (10-27 file + today's bars). Run as in nightly1023 (`python <script> <scratch>`;
`close.py` / `polls.py` also take the repo path; `tables.py > tables_out.md`, `riskq.py > riskq_out.txt`).

**Market: flat-to-up, quiet.** SPY +0.11% (low −0.28% 09:48, high +0.25% 14:37); QQQ +0.19% (low −0.53% 09:49, high +0.28%
15:59); IWM +0.33% (low −0.46% 14:33). A slow grind up from the 09:49 low: shorts lost everywhere except Primary again.

**Moves effective today:** ROT1 night 1 (CWT14-failbrk-pdl-p10-lowvol-long, NS4-pm-vwap-reclaim-oversold-short,
MF2-open-rsimidhi-flowsell Primary → Testing 2); 10 new GEN setups. ST-P (Primary −2R latched per-setup stop) starts
**10-29**, so today is the last Primary session without it.

## Failures first

1. **Closed clean in all 5 accounts.** Phase `closed`, 0 positions, `flatten_failed` [], no partial lots, no data outages;
   journal trades = submitted signals = EOD report rows = `status.today.trades` = job-log "Trades" in every account
   (14 / 162 / 213 / 298 / 82; job-log P/L matches the journal's before-cost P/L, e.g. Primary 246.76, Graveyard −979.61);
   "flatten complete: no MCF positions open" in the Testing 2 standby log; EOD report + scorecard pushed 19:57 UTC
   (scorecard as of 15:57 ET). Broker positions / open orders not reachable from here (no broker keys); journal = report =
   status = job log is the proxy.
2. **Handover #159 → standby #165 left a > 5 min gap in Testing 2 and Gen.** #159's jobs (started 08:55-08:57 ET) wrote
   "handover" status at 14:36-14:40 ET and "job 08:5x done" at 14:36-14:40 ET; #165's jobs (queued since 13:57 ET) started
   14:36:36-14:40:48 ET, and their Trade steps began 14:37:17 (T1), 14:38:03 (GY), 14:39:10 (P), **14:41:57 (T2)** and
   **14:42:08 (Gen)** — T2's checkout took 78 s, Gen's 42 s. Poll gaps at the handover (`decmin_out.txt`): Primary 3.0 min
   (14:36:14 → 14:39:12), Testing 1 2.1 (14:35:14 → 14:37:19), Graveyard 2.9 (14:35:14 → 14:38:05), **Testing 2 5.7
   (14:36:19 → 14:42:00), Gen 5.8 (14:36:20 → 14:42:11)**. T2 and Gen missed the **14:40 decision minute** (76 / 77); the
   14:35 bucket's lab decisions were not taken there (no T2 / Gen signal 14:37-14:45; T1 had 5 and Graveyard 15 at 14:41).
   Housekeeping (new row OPS-HANDOVER): start the standby's checkout / install before the old job hands over.
3. **HK-RECON closed:** Testing 2's two 10-27 entries (Z CWT14-failbrk-pdl-p05-lowvol-long −$0.56, SLN CWT12-coil-k4-long
   +$0.46, both flattened 15:55) were journaled under 10-27 by today's reconcile: T2 10-27 now 240 trades, −$261.14.
4. **Poll coverage fell again in the slower accounts** (of 384 expected 1-min polls 09:30-15:54): Testing 2 **268 (70%)**
   vs 316 on 10-27, Gen **227 (59%)** vs 248, Graveyard 315 (82%) vs 277; Primary 383, Testing 1 382. Apart from the
   handover every decision minute was polled; the slow accounts skip bucket minutes 1-2 (T2 polled exp%5 = 1 / 2 only
   17 / 24 times), which only non-lab setups use (OPS-POLL).
5. **Broker rejects 4, crosscheck skip 1, "missed: triggered" 0.** Graveyard: 2 "insufficient buying power", 1
   take-profit already through the base price (H-1 / HK-1); Gen: 1 stop_loss price on the wrong side of the base price;
   Graveyard 1 crosscheck (quote too old); Gen 1 "no quote (ConnectionError)". Primary: none (9 skips = borrow / spread).

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`, `decmin_out.txt`)

| account | polls | % of 384 | decision minutes | longest gap | handover gap | trades (journal = report = status = log) |
|---|---|---|---|---|---|---|
| Primary | 383 | 99.7% | 77 / 77 | 3.0 min (handover) | 3.0 min | 14 |
| Testing 1 | 382 | 99.5% | 77 / 77 | 2.1 min (handover) | 2.1 min | 162 |
| Testing 2 | 268 | **70%** | **76 / 77** (14:40) | **5.7 min** (handover) | **5.7 min** | 213 |
| Graveyard | 315 | **82%** | 77 / 77 | 3.1 min (14:41) | 2.9 min | 298 |
| Gen | 227 | **59%** | **76 / 77** (14:40) | **5.8 min** (handover) | **5.8 min** | 82 |

Moved setups traded only in their new accounts: CWT14-failbrk-pdl-p10-lowvol-long Testing 2 only (7 trades), NS4 window
and MF2 window 0 trades in Testing 2 (no signal).

## 1. Headline per account (real trades)

| account | trades | win% | avgR (costs) | **P/L after costs** (before) | stop / target / flatten | marked peak → close |
|---|---|---|---|---|---|---|
| Primary | 14 | 86% | +0.399 | **+$245.88** (+$246.76) | 2 / 11 / 1 | trough −$15 (09:51) → peak +$260 (15:18) → +$246 |
| Testing 1 | 162 | 46% | −0.214 | **−$702.27** (−$655.43) | 63 / 69 / 28 | +$83 (10:52) → −$704 (15:54) |
| Testing 2 | 213 | 51% | −0.194 | **−$925.79** (−$881.83) | 84 / 104 / 23 | never above 0; −$926 at the close |
| Graveyard | 298 | 49% | −0.229 | **−$1,079.05** (−$979.61) | 137 / 134 / 27 | never above 0; trough −$1,290 (14:44) |
| Gen | 82 | 49% | −0.091 | **−$121.63** (−$65.47) | 39 / 26 / 17 | +$261 (12:55) → −$122 |

Total after costs −$2,582.86. **Shorts lost everywhere but Primary:** T1 −$773, T2 −$806, Graveyard −$1,079, Gen −$416;
longs T1 +$71, T2 −$120, Graveyard +$0, Gen +$295. Primary shorts +$95.73 (RW5-FD +$61.51), longs +$150.15
(NS5-sma50-flush-oversold-long 2 trades +$145.10 at 09:50).

**Primary live-funds hold:** +$245.88 after costs (+$246.76 before) → positive-day streak **3** (10-26 +$33.67, 10-27
+$87.73, 10-28 +$245.88): **M1 (3 green days in a row) reached, also after costs.** Since Day 1 (10-23): 3 of 4 sessions
positive, **+$275.22** after costs (+$305.36 before). Since start: 6 of 17, −$746.14. M2 (8 of the last 10 green) 3 / 4 so
far. Lifting the hold is the owner's call; nothing changes here.

### 1a. Intraday peak vs close (`giveback_out.txt`)
- **Primary:** +$145 by 10:31 (NS5 base, 2 trades at the 09:50 poll), then the gap-down shorts carried it to +$260 at
  15:18; one open RW5-FD short gave back $13.81 into the flatten. 14 trades only (3 setups moved out, ROT1).
- **Testing 1:** +$83 at 10:52 → −$704. The NS3 family (RW4-ns3-adv150-short-FD 0 / 16 −$362.68, NS3 base 0 / 5
  −$119.54) and exhaustion_short (1 / 7, −$114.53) did the damage; 103 trades after the peak −$461.50, 15 open winners at
  the peak later stopped (−$380.30). orb20_a +$96.74.
- **Testing 2 never above zero:** NS3V1-am-widestop-short 0 / 13 −$531.87 (12 never reached +0.2R; its first trades ever),
  NS3-FD 1 / 11 −$161.35, exhaustion_short-FD 0 / 7 −$88.38, CWT12-coil-k4-long 77 trades −$77.71.
- **Graveyard −$1,290 at 14:44:** heat_fade_short-FD −$369.27 (29 trades, 17% win), CWT14-failbrk-pdh-p10-short −$329.15
  (31, 25 entries in one poll), RW2-exhaustion-noon −$191.81; the −2R latched stop blocked 253 signals worth −5.3R.
- **Gen +$261 at 12:55 → −$122:** GEN-261019-10 (FlowShift PM short) 13 trades −$380.60 after 13:00;
  GEN-261028-09 (new today) 24 trades −$107.36 (19 in one poll). GEN-261022-01 (ORB-fail-up long) +$331.00.

## 2. Winner / loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE/MAE for all 769 trades)

- **Losers "never worked" again:** 178 losers never reached +0.2R (P 1 / T1 34 / T2 58 / GY 69 / Gen 16, −$3,050 together);
  only 60 losers had been ≥ +0.5R. Losers' median MFE 0.17-0.30R; winners reach MFE late (median 43-110 min), losers peak
  early (8-22 min). Winners give back little (median 0.06-0.12R).
- **NS3 family = one bet, again** (`ns3fam_out.txt`): 48 shorts in Testing 1 + 2 today, 2 winners, −$1,204; CORZ / WULF /
  IREN / CLSK / HUT / APLD each shorted 2-4 times by 2-3 family setups 10:00-14:20 as QQQ climbed off its 09:49 low. Same
  shape on 10-21 (nightly1021: −25.1R, mostly miners). Since 10-06: 273 family shorts, 34% win, −0.243R, −$1,919
  (w/o 10-28 −0.085R); 1st / 2nd / 3rd+ entry on a symbol −0.247 / −0.260 / −0.187R (repeat entries are not worse per
  trade — it is concentration, not edge). The miner list (73 trades −0.507R) was picked after seeing today: descriptive
  only. → backlog `nightly-1028-ns3-family-one-bet` (risk).
- **Testing 2's three failed-PDL longs** (first day with all three): 82 trades on 63 symbols, 14 symbols taken by 2+
  versions, 5 by all three; all 7 p10-lowvol trades were on symbols a sibling also took. No twin group spans them, so
  "twin held" = 0 for the trio (T2's 19 twin-held skips were NS3-FD 17 / MF5 base 2).
- **Clusters:** no clean order (T1 > 9 per poll −0.10R vs singles −0.26R; Graveyard > 9 −0.64R vs −0.13R; Gen 5-9 +0.26R).
  Burst skips already failed on two years; no new item.
- **Latency:** medians 1.1-1.5 s; today the slow tercile was worse in T1 (−0.41R vs −0.11R fast), T2 (−0.23 vs −0.12) and
  Gen, not in Graveyard; 10-27 showed no order. One day; watch only.
- **15:45 flatten** (`flat1545_out.txt`, 1,765 lots since 10-06): +28.0R vs the 15:55 flatten, 13 of 17 days better,
  t 1.25, best day 38% (longs +29.6R, shorts −1.6R); unchanged vs 10-27, already in the backlog (nightly-1027-flatten-1545).
- **Checked, no new pattern:** inverse-ETF longs (122, −0.08R vs −0.12R other longs); CWT14 pdl longs by QQQ-low age (the
  < 15 min bucket −0.19R vs ≥ 15 min −0.02R; its backlog item already failed on two years); MF1/3/5 shorts by QQQ vs VWAP
  (both lose); shorts before 10:00 (day direction = lookahead); re-entry after a stop (−0.08R vs −0.12R, no worse).
- **Testing accounts after −2R** (`rearm_out.txt`; per-setup stop off there since 10-23): 13 setup-days kept trading after
  −2R today, 61 entries −2.6R; since 10-20 46 events, 327 entries, −68.3R.

## 3. Backlog (1 new, status idea)
- `nightly-1028-ns3-family-one-bet` (risk; one NS3-family short per symbol per day per account + theme cap; related to
  nightly-1026-country-gap-basket-cap).
No swarm tonight: 1 new idea (< 3) and no setup is near a backtest gate (K4 is an owner move decision, not a gate).

## 4. Suggestions (`combined_out.txt`; all accounts merged, 17 sessions, costs in; yardstick research/ops/primary_bar.md)

- **DECISION K4-2** — Coil Under the High (4 bars) (`CWT12-coil-k4-long`, Testing 2) → Graveyard. The owner's extra day
  (K4 no, 10-27) is in: 77 trades −12.0R, −$77.71. Record 427 trades / 13 sessions, 63.0% win vs 68.4% needed, −0.092R,
  w/o best day (10-23) −0.118R (record negative, no best-day share), t_day −1.05, last 4 sessions 234 trades −0.121R,
  −$161.70; 2-year −0.075R; hf1027 (targets, cost floor) and htf1028 (trend filter) all fail on two years. Reply
  "K4-2 yes" / "K4-2 no".
- **Demotion watch, not raised (today is most of the loss):** `RW4-ns3-adv150-short-FD` (no display name yet; Testing 1 +
  Testing 2) 101 trades, 31.7% win vs 50.0% needed, −0.268R, −0.386R w/o best day, t_day −1.32, last 4 −0.786R,
  −$556.97, 8 of 12 days negative; but today (−18.9R) is 70% of its loss (w/o today −0.100R on 82). Big Loser VWAP
  Reclaim Fade (`NS3-failed-vwap-reclaim-short`, Testing 1) 50 trades −0.227R, last 4 −1.061R, 2-year −0.136R; (all day)
  (`NS3-failed-vwap-reclaim-short-FD`, Testing 2) 109 trades −0.144R, w/o today −0.049R. Re-check with MF3-FD / MF5-FD at
  Friday's review (10-30), together with the backlog item above.
- **MF watch (from 10-27):** Early Sellers into a Pop (all day) (`MF3-open-flowsell-rsi5hi-FD`, T1) 129 trades −0.205R,
  last 4 −0.427R; Sellers into Strength (all day) (`MF5-flowsell-vwapup-rsi5hi-FD`, T2) 68 trades −0.290R, last 4
  −0.566R. Friday.
- **No promotion is ready.** Every Testing setup with ≥ 30 trades and avg R > 0 fails "w/o best day > 0":
  L3-gap-slope-fromopen-FD (T1, 207, +0.134R / −0.045R, 121%), L3-gap-slope-rsi5hi-FD (T2, 61, +0.122R / −0.014R, 108%),
  RW1-gapdn-bounce-flowsell-short-FD (T2, 74, +0.070R / −0.003R), GEN-261021-06 (Gen, 37, +0.336R / −0.058R, 106%).
- **N3 (waiting on owner) update:** NS5-sma50-flush-oversold-long-FD 35 trades, 40% vs 65% needed, −0.350R, −$219.25.

### 4a. Monitor marks (docs/live/monitor.json, marked 10-27)
- Afternoon VWAP Reclaim Fade (all day) (`NS4-pm-vwap-reclaim-oversold-short-FD`, Testing 1 → Primary): 1 session since
  the mark, 1 trade −1.05R (−$2.84). Full record 19 trades / 8 sessions, 63% win vs 45% needed, +0.345R, w/o best day
  (10-22, 71% of R, **1 day**) +0.138R, last 4 3 trades −0.68R, t_day 1.21, base 2-year −0.080R. **Lean: wait** (needs
  ~30 trades; 1-day tag).
- Generated: NewLOD, Flow3lem0p37 LUNCH short
  (`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`, Gen → Testing 1): 1 session since
  the mark, 0 trades (no signal). Full record 11 trades / 2 sessions, 64% win vs 29% needed, +0.656R, w/o best day (10-27,
  85%, **1 day**) +0.267R, t_day 1.42, +$102.59. **Lean: wait** (2 sessions).

### 4b. Watch: CWT14-failbrk-pdl-p10-lowvol-long (Primary → Testing 2 from 10-28)
Day 1 in Testing 2: 7 trades, 2 wins, −0.58R, −$21.98 (all on symbols a sibling version also took). Record 179 trades /
13 sessions, 68.2% vs 66.3% needed, +0.006R, w/o best day (10-20, 591% of R, **1 day**) −0.029R, last 4 −0.041R,
−$116.74, 2-year −0.095R.

## 5. ST-P live replay, baseline before the rule (`stp_out.txt`; 4 configs, counted)

Primary 17 sessions (10-06..10-28), latched per-setup stop vs none: 1.5R +17.96R (6/5 days, t 0.76), **2R +21.10R**
(6/4, t 0.90), 3R +10.03R (5/4); none −12.05R, −$746.14. Today no Primary setup came near −2R (worst single trade −1.11R, ST7-FD XHB;
worst setup-day −0.27R), so all four rules give +5.58R. The owner approved ST-P on 10-28 (2R latched, Primary only, from 10-29): from
tomorrow the live Primary record includes the rule, and this replay is the pre-rule baseline. No decision item.

Educational only — not financial advice.
