# Nightly learning loop, 2026-11-02 (Monday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **Configurations tried tonight: 4** —
all in `levetf.py` (leveraged / inverse ETF skip rules on the 2-year lab trade lists; locked block 2024-11-01..2025-02-28
is not in the file and was not read). About 25 descriptive splits were looked at as well (setup, side, hour, exit,
poll, lot, twin, cluster, latency, peak-to-close attribution, re-entry after a stop, $ risk per lot, ETF class,
borrow skips, -2R latch timing), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`. The job-log review shows P/L **before** costs
(Primary −$614.39); after costs it is **−$627.19**.

**Rule changes inside the windows quoted below** (research/ledger.jsonl effective dates): Primary — ST7-FD promoted
10-26, CWT13-z05-long in/out 10-26/10-27, rotation out of CWT14 pdl lowvol / NS4 window / MF2 window and **position size
~$4,000 (77 slots) from 10-28**, **−2R per-setup stop from 10-29**, **L3 pair promoted 10-30**. All accounts — lab
5-minute clock (GX1) 10-27. Testing — per-setup stop off from 10-23, BAR90 10-29, cost filter (CF) from 10-30;
NS3-FD / RW4-FD moved to the Graveyard from 11-02; PDL-1a R2A legs in Testing 2 from 11-02 (SO-1A exemption from 11-03;
MF3-FD / MF5-FD to the Graveyard from 11-03).

**Scripts** = nightly1030's with the date set to 11-02 (`fetch.py`, `build.py`, `close.py`, `polls.py`, `decmin.py`
[handover window moved to 14:26-14:36], `autopsy.py`, `giveback.py`, `combined.py`, `burst.py`), plus `detail.py`
(per-setup cards: w/o best day, 3 busiest sessions, since-mark records, Primary per session, ETF class, re-entry after a
stop) and `levetf.py` (swarm). Scratch (journals, status, reports, intraday, polls, job logs, SIP 1-min bars for 584
symbols) was deleted after the run.

**Market: up early, then a steady slide.** SPY −0.78% (high +0.58% 10:28, low −0.84% 14:50), QQQ −1.75% (high +0.59%,
low −1.85% 14:50), IWM −0.65%. Semis led down — which matters below (SOXS, 3x inverse semis, rose all afternoon).

## Failures first

1. **No broken session.** All 5 accounts closed clean: phase `closed`, 0 positions, `flatten_failed` [], no partial
   lots, no data outages; journal trades = EOD report rows = `status.today.trades` = job-log "Trades" (12 / 37 / 129 /
   395 / 226); job-log P/L = journal before-cost P/L (P −614.39, T1 −178.95, T2 −382.24, GY −1,509.80, Gen −1,563.94);
   EOD reports + scorecards 15:56-15:59 ET; final state pushes 15:56-15:57 ET ("job 14:3x done"). Broker positions are
   not reachable from here (no broker keys); journal = report = status = job log is the proxy.
2. **Hand-overs lost no trades.** Run 190 (08:44 ET) handed over at its 14:30 slot end ("slot ends 14:30: handing over",
   14:29-14:33 ET); standby runs 191-194 were cancelled by their successors; run 195 (14:10 ET) took over; 196 cancelled,
   197 (15:55) clean. Gaps 2.0-4.7 min, **no gap > 5 min** (OPS-HANDOVER fine again after 10-30's 11-14 min). Graveyard
   missed the 14:30 decision minute (76/77); the other 4 polled 77/77.
3. **Gen: 39 submitted entries have no trade row (HK-RECON-GEN again).** 265 submitted vs 226 trades, all 39 still
   `submitted` in the orders table (other accounts: submitted = trades). 10:25-12:35 ET, mostly GEN-261021-07 ×13,
   GEN-261021-06 ×9, GEN-261022-08 ×6, GEN-261022-07 ×4. **10-30's 31 were booked by today's reconcile** (Gen 10-30 now
   276 trades, −$2,392.53 after costs, was −$2,744.98 on 245), so these should land on Tuesday's run. Gen's −$1,723.62
   is missing 39 trades.
4. **The Primary −2R per-setup latch was one lot late.** L3-gap-slope-fromopen-FD's 2nd and 3rd SOXS stops filled
   12:45:12-14 ET, but they were booked only by the 12:46:44 reconcile, so a 4th SOXS short entered at 12:45:39 with
   the setup really at −3.07R (−1.02R, −$87). Housekeeping row HK-LATCH (count broker stop fills before the entry check).
5. **Coverage under 90% in 2 accounts** (of 384 1-min polls): Primary 384, T1 384, T2 297 (77%), GY 348 (91%), Gen 253
   (66%); misses are bucket minutes 1-2 (OPS-POLL residual). Broker rejects: Graveyard 38 "insufficient buying power"
   (what-if +0.9R). Crosscheck 0, "missed: triggered" 0. One Testing 2 intraday push failed at 11:27 ET (GitHub
   `commit_refs` error); later pushes and the final push landed.

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`, `decmin_out.txt`)

| account | polls | % of 384 | decision minutes | hand-over gap | trades (journal = report = status = log) |
|---|---|---|---|---|---|
| Primary | 384 | 100% | 77 / 77 | 2.3 min | 12 |
| Testing 1 | 384 | 100% | 77 / 77 | 2.5 min | 37 |
| Testing 2 | 297 | **77%** | 77 / 77 | 3.8 min | 129 |
| Graveyard | 348 | 91% | 76 / 77 (14:30) | 2.0 min | 395 |
| Gen | 253 | **66%** | 77 / 77 | 4.7 min | 226 (+39 submitted, not booked) |

## 1. Headline per account (real trades, `autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | avg R (costs) | **P/L after costs** (before) | marked peak → close |
|---|---|---|---|---|---|
| Primary | 12 | 25% | −0.515 | **−$627.19** (−$614.39) | +$67 (12:07) → −$627 |
| Testing 1 | 37 | 30% | −0.455 | **−$184.55** (−$178.95) | +$12 (09:58) → −$185 |
| Testing 2 | 129 | 47% | −0.256 | **−$389.38** (−$382.24) | +$95 (12:38) → −$389 |
| Graveyard | 395 | 49% | −0.212 | **−$1,626.84** (−$1,509.80) | +$67 (10:09) → −$1,627 |
| Gen | 226 (+39) | 32% | −0.365 | **−$1,723.62** (−$1,563.94) | +$153 (10:59) → −$1,724 |

By side: longs lost everywhere (T2 −34.5R / −$520, GY −67.8R / −$1,709, Gen −76.6R / −$1,836); shorts were about flat
to positive in T2 / GY / Gen ($+130 / +82 / +112). Primary was the exception: **its shorts lost** (−5.1R / −$500).

**Primary live-funds hold: RED, third red day in a row.** −$627.19 after costs (−$614.39 before; 12 trades, −0.515R)
→ streak **0**. Since Day 1 (10-23): 3 of 7 sessions positive, **−$854.48** after costs (−$773.72 before). Since start:
6 of 20 positive, −$1,875.84; last 10 sessions 4 green. Nothing changes; lifting the hold is the owner's call.
Rule changes in that window: ~$4,000 position size from 10-28, −2R per-setup stop from 10-29, L3 pair from 10-30.

**Why Primary lost (ask WHY): one symbol.** 6 SOXS shorts by the two promoted L3 setups (fromopen ×4 11:35-12:45,
rsi5hi ×2 13:35 / 14:10) all stopped: **−6.1R, −$641 — more than the whole day (−$627).** Without SOXS Primary was
+$14. SOXS is the 3x *inverse* semiconductor ETF: its "gap-down recovery" was semis gapping up and then fading, so
shorting it was a long on semis on a day QQQ fell 1.75%. Three things made it big:
- **$ risk per lot**: the L3 SOXS lots carried $87-124 risk each (stop ~2.8% on a ~$3,900 slot) vs a Primary median of
  $12-48 per lot on 10-20..10-30. Primary's $ per R today was ~$101. Since the 10-28 sizing change (~$4,000 slots),
  wide-stop names dominate the dollars; big-risk lots are *not* worse in R (all accounts: > 2x day median −0.13R vs
  −0.14R below it), so this is a size effect, not a signal effect.
- **Stacking before any stop**: lots 1-3 were all open before the first stop (12:35), so the −2R latch could not stop
  them (known LL-OPEN gap, closed 10-24 without a change).
- **Latch lag**: lot 4 entered 25 s after the 2nd and 3rd stops filled (failure 4 above).
The −2R stop then blocked 30 entries (L3-fromopen 26, rsi5hi 3, MF4-FD 1; what-if −16.8R, saved). L3's borrow skip
also saved R today: 251 not-shortable signals, L3-fromopen's 173 at −0.87R avg (what-if), mostly single-stock 2x
inverse ETFs (SMCZ, RAMZ, AAOZ, ASTN, SKDD).

Checks: (a) re-entering a symbol + side already stopped that day is not worse over the record (all accounts −0.06R on
427 vs −0.14R first entries; 11-02 −0.41R on 38 is the bad day); (b) shorts on inverse ETFs, live since 10-06: −0.322R
(105) vs −0.121R other shorts — but on two years they are *better* (swarm below), so no family rule.

### 1a. Promoted L3 setups on Primary (since 10-30, 2 sessions)
- **Gap-Down Recovery Fade (all day)** (`L3-gap-slope-fromopen-FD`): 4 trades, 0% win, −1.022R, −$423.76 (all today).
  All-account record 249 trades +0.155R, +0.029R w/o best day (10-20, 87% share, `1 day`), 3 busiest sessions +0.367R.
- **Gap-Down Rebound Overbought Short (all day)** (`L3-gap-slope-rsi5hi-FD`): 3 trades −0.566R, −$212.68. Record 79
  trades +0.145R, +0.056R w/o best day (10-26, 70%, `1 day`), 3 busiest +0.247R.
- Review stays 2026-11-12 (PROMO-L3 / PROMO-L3F). Live L3-on-leveraged / inverse-ETF trades: fromopen 14 −0.025R vs
  +0.165R on the rest; rsi5hi 5 −0.120R vs +0.163R (small n) → backlog `nightly-1102-l3-inverse-etf-skip`.

## 2. Winner / loser autopsy (`autopsy_out.txt`; SIP 1-min MFE / MAE for all 799 trades)

- **Losers "never worked" again**: Primary's 9 losers peaked at a median +0.18R; the SOXS lots reached +0.06 to +0.92R
  before stopping. Winners (MF2-FD CBRS target +2.16R, RW3-FD RNG +0.55R, RW5-FD BAH +0.69R) peaked late (86-259 min).
- **Testing 2**: R2A long leg day 1 (below), `NM-HL-T75-pm-long` 24 trades −9.9R / −$158, `CWT13-vwapstretch-z05-long`
  21 −7.4R, `CWT14-failbrk-pdl-p10-long` 24 −8.4R; 22 late flattens (≥ 15:50) gave back −$269 from the 12:38 peak.
- **Graveyard**: `heat_fade_long` 20 trades −18.6R / −$699 and `heat_fade_long-FD` 22 −12.0R / −$282 on the slide;
  `RW2-exhaustion-noon-adv150-short-FD` +9.8R and `heat_fade_short-FD` +7.2R the other way.
- **Gen**: `GEN-261021-06` (ORBfailUp MID long) 46 trades −47.3R / −$1,085, incl. a 27-entry burst at the 11:00 poll
  (−28.6R); `GEN-261022-07` short +15.1R / +$454 (best burst of the day, 14 entries +10.2R). Bursts ≥ 10 entries since
  10-06: 123, −420.5R (−0.219R avg). Added to `nightly-1029-burst20-one-bet`'s notes (failed on two years; no change).
- **Cost filter (CF, Testing only, day 2)**: T1 skipped 24 (what-if −6.2R before costs, saved), T2 skipped 30 (+3.0R,
  cost). Review 11-12.
- **Checked, no new pattern**: twins, latency terciles, lot number, cluster size, $ risk per lot (above), re-entry
  after a stop (above).

## 3. Backlog (2 new, 1 updated)
- `nightly-1102-skip-inverse-etf-shorts` (risk) — **failed**, 4 configs (`levetf.py`, bar t 1.665). Two-year lab lists
  (21 setups): shorts on inverse ETFs train +0.030R (n 521) vs −0.055R kept, valid +0.024R (748) vs −0.002R — they are
  better, not worse; all lev + inverse shorts +0.001 / +0.026R; longs on inverse ETFs −0.056 / −0.072R (t 0.45 / 0.96);
  lev-long longs +0.029 / −0.046R. Coverage gap: L3 is not in the lab lists.
- `nightly-1102-l3-inverse-etf-skip` (setup, idea) — L3 only: needs the l3_1022 two-year scan rebuilt with an ETF-class
  column (not run tonight, disk).
- `nightly-1029-burst20-one-bet` — notes updated (above).
- Housekeeping (OPEN_ITEMS, not backlog): HK-LATCH (latch counts unbooked stop fills), HK-RECON-GEN (39 today).

Swarm: 2 new items (< 3) and no setup at a gate; the 4-config check ran because the Primary loss needed a WHY.

## 4. Suggestions (`combined_out.txt`, `detail_out.txt`; all accounts merged, 20 sessions 10-06..11-02, costs in)

- **DECISION DM-N3** (refresh of N3, open since 10-20; numbers moved): move **Big Loser Flush Buy (all day)**
  (`NS5-sma50-flush-oversold-long-FD`, T1 + T2), **ST4 EMA-down dip buy (all day)** (`ST4-emadn-long-am-t1s05-FD`, T1)
  and **Big Gainer Fade with VWAP Band Guard (all day)** (`RW6G1-ns2-up3-vwap2sd-short-FD`, T1) to the Graveyard.
  NS5-FD 44 trades / 15 sessions, 36.4% win, −0.384R, w/o best day −0.469R (total negative, no carry day), 3 busiest
  −0.699R, −$339, 2-yr base −0.039R; ST4-FD 15 / 8, −0.578R, w/o best −0.737R, 3 busiest −0.764R; RW6G1-FD 28 / 12,
  −0.237R, w/o best −0.277R, 3 busiest −0.290R, 2-yr parent +0.057R (t 0.68). Recommendation **yes**.
  Reply "DM-N3 yes" / "DM-N3 no".
- **No promotion is ready.** Best non-Primary records with 20+ trades are one-day records (`NS4-pm-...-short-FD` +0.187R
  / +0.011R w/o best day, 95%; `NM-MF3-qqqdn-gapdn-FD` +0.236R / −1.009R w/o best day).
- **No Primary demotion yet.** Watch: `ST7-rsi50dn-long-pm-t1s1-FD` (RSI Collapse Dip Buy (all day)) on Primary since
  10-26: 10 trades −0.245R, −$166 (record 26 +0.028R, w/o best day −0.151R); review 11-06. `MF4-h40-open-flowsell-FD`
  (Early Sellers, Strong Heat (all day)) 72 trades +0.050R, w/o best day −0.020R, last 4 −0.428R — drift watch Friday.
- MF1-945-flowsell-vwapup in Testing 1 since its 10-26 demotion: 5 trades −1.21R (FYI).

### 4a. Monitoring (docs/live/monitor.json)
- `NS4-pm-vwap-reclaim-oversold-short-FD` (up → Primary, since 10-27): no trade today; since the mark 9 trades 22% win
  −0.442R, −$2.34; record 26 +0.187R, +0.011R w/o best day (95%, `1 day`) — lean drop.
- `GEN-261026-03-NewLOD-...-holdtr-short` (up → Testing 1, since 10-27): 3 trades +0.19R today; since the mark 11 trades
  +0.475R, −0.231R w/o best day (118%, `1 day`); record 15 +0.420R, +0.018R w/o best day (98%) — lean wait.

### 4b. Watches
- **CWT14-failbrk-pdl-p10-lowvol-long** (T2 since the 10-28 move): today 15 trades −5.16R, −$39.44; since the move 63
  trades / 4 sessions, 54% win, −0.214R, −$106.95, −0.403R w/o best day (10-29); record 235 −0.036R.
- **PDL-1a R2A legs (T2, day 1)**: long leg 19 trades, 47% win, −0.157R, −$169.97; **2 got the half-off** (DELL, VEEV),
  **11 ran plain** because the 2/day cap was spent (12 cap messages; VLO twice), 6 never reached the scale-out trigger.
  Short leg: 0 signals. The exemption starts 11-03.

### 4c. Primary −2R per-setup stop (FYI)
Latched: MF4-FD (~10:21, 2 stops −2.35R), L3-fromopen-FD (12:46 reconcile, −3.07R at the latch), L3-rsi5hi-FD (14:38,
−2.04R). 30 entries blocked, what-if −16.8R (saved); one lot slipped through the reconcile lag (−1.02R, −$87).

### 4d. BRAKE-1 shadow line (FYI; never switched on)
Family stops today (RW3-FD / RW5-FD / MF2-FD / MF4 / MF4-FD): 2 (MF4-FD IWB, IWV) → the brake would not have
triggered. Primary R actual −6.18R = with brake −6.18R. Running total since 2026-11-02: **0.00R** (1 session).
