# Nightly learning loop, 2026-10-30 (Friday): Primary, Testing 1, Testing 2, Graveyard, Setup Generator

*Educational only — not financial advice. These are live **paper** results from one session plus the since-start live
record. They describe what happened and are not evidence that anything works. **Configurations tried tonight: 14** —
12 in the swarm `lateext.py` (late shorts with SPY extended down, plus a long mirror), 1 descriptive (`pmrev.py`), 1
live replay (`flat1545.py`, 15:45 vs 15:55 flatten, the same replay as 10-27..10-29). Two-year data =
research/history2y lab trade lists + SPY context; the locked block 2024-11-01..2025-02-28 is not in those files and
was not read. About 30 descriptive splits were looked at as well (setup, side, hour, exit, poll, lot, twin, cluster,
latency, peak-to-close attribution, borrow skips, $ risk per lot, same-symbol stacking), so some will look strong by chance.*

**Costs are in.** P/L = journal `pnl_adj`; avgR = `pnl_adj / $ risk`. The job-log review and the Day 6 post show P/L
**before** costs (Primary −$79.55); after costs it is **−$91.43**.

**Scripts** = nightly1029's with the date set to 10-30 (`fetch.py`, `build.py`, `close.py`, `polls.py`, `decmin.py`,
`autopsy.py`, `tables.py`, `giveback.py`, `combined.py`, `rearm.py`, `burst.py`, `onebig.py`, `flat1545.py`,
`ns3fam.py`), plus `l3etb.py` (L3 family: taken vs not-shortable what-if), `lateext.py` (swarm) and `pmrev.py`. Scratch
(journals / status / reports / intraday / polls / SIP 1-min bars for 683 symbols) was deleted after the run.

**Market: steady trend down, then a late bounce.** SPY −0.75% (low −1.45% at 14:52), QQQ −0.96% (low −1.97% 14:52),
IWM −0.95% (low −1.81% 14:35). From the low to the close SPY gained +0.7% and QQQ +1.0%.

## Failures first

1. **No broken session.** All 5 accounts closed clean: phase `closed`, 0 positions, `flatten_failed` [], no partial
   lots, no data outages; journal trades = EOD report rows = `status.today.trades` = job-log "Trades" (15 / 43 / 118 /
   361 / 245); job-log P/L = journal before-cost P/L (P −79.55, T1 60.80, T2 63.56, GY −543.96, Gen −2,546.06);
   "flatten complete: no MCF positions open" in the Primary and Gen standby logs; EOD reports + scorecards
   15:57-15:59 ET. Broker positions are not reachable from here (no broker keys); journal = report = status = job log
   is the proxy.
2. **Gen: 31 submitted entries have no trade row (HK-RECON-GEN again, 4x bigger).** 276 submitted vs 245 trades; the 31
   orders are still `submitted` in the orders table (all other accounts: submitted = trades). They are 10:50-12:31 ET
   entries, 27 of 31 "hold" / "holdtr" geometries (GEN-261027-08 ORBfailDn LUNCH short ×14, GEN-261028-08 LUNCH long
   ×7, GEN-261022-01 ×4 incl. UVIX / GDXD / LABD, GEN-261028-07 ×2, 4 others), closed by the 15:55 flatten whose stop legs
   answered "order pending cancel". **10-29's 8 missing trades were booked by today's reconcile** (Gen 10-29 now 225
   trades, −$3,871.86 after costs), so these should land on Monday's run. **Gen's −$2,744.98 is missing 31 trades.**
   Gen also had **12 "insufficient buying power" rejects** (what-if +8.5R), plausibly because those unbooked lots held
   buying power. Housekeeping row HK-RECON-GEN stays open: the reconcile should pair flatten closes on the same day.
3. **Handover gap 11-14 min in every account (OPS-HANDOVER regressed).** Run 41058369921 (manual dispatch, 08:50 ET)
   hit the 6-hour limit; its Trade steps ended 14:36:52-14:38:23 ET. Standby run 41102194532's jobs started
   14:36:57-14:38:28, but **`actions/setup-python` took ~10 min** (Graveyard job 14:38:10 → 14:48:13; the cache could
   not be reserved), so Trade steps began 14:47:32 (T1), 14:47:58 (P), 14:48:37 (GY), 14:48:43 (T2), 14:49:01 (Gen).
   Poll gaps: Primary 11.2 min (14:36:51 → 14:48:00), T1 12.3, T2 13.5, GY 13.4, Gen 13.8. **The 14:40 and 14:45
   decision minutes were missed in all 5 accounts (75 / 77)** — the index low (14:35-14:52) fell inside the gap.
   Open lots kept their broker brackets; **no trade was lost** (journal = log in all 5). Fix idea (housekeeping): install
   Python in the standby before the old job hands over, or pin a pip cache key per run.
4. **Poll coverage under 90% in the 3 slow accounts** (of 384 1-min polls): Primary 373 (97%), T1 374 (97%), **T2 303
   (79%), GY 309 (80%), Gen 292 (76%)**; all slow-account misses are bucket minutes 1-2 (OPS-POLL residual) plus the
   handover gap. Broker rejects 12 (Gen, buying power), crosscheck 0, "missed: triggered" 0.

## 0. Session close and coverage (`close_out.txt`, `polls_out.txt`, `decmin_out.txt`)

| account | polls | % of 384 | decision minutes | longest gap (handover) | trades (journal = report = status = log) |
|---|---|---|---|---|---|
| Primary | 373 | 97% | 75 / 77 | 11.2 min | 15 |
| Testing 1 | 374 | 97% | 75 / 77 | 12.3 min | 43 |
| Testing 2 | 303 | **79%** | 75 / 77 | 13.5 min | 118 |
| Graveyard | 309 | **80%** | 75 / 77 | 13.4 min | 361 |
| Gen | 292 | **76%** | 75 / 77 | 13.8 min | 245 (+31 submitted, not booked) |

## 1. Headline per account (real trades, `autopsy_out.txt`, `giveback_out.txt`)

| account | trades | win% | avgR (costs) | **P/L after costs** (before) | marked peak → close |
|---|---|---|---|---|---|
| Primary | 15 | 47% | −0.168 | **−$91.43** (−$79.55) | +$144 (14:21) → −$91 |
| Testing 1 | 43 | 58% | +0.068 (journal) | **+$57.88** (+$60.80) | −$42 (12:00) → +$129 (14:21) → +$58 |
| Testing 2 | 118 | 56% | −0.111 (journal) | **+$55.10** (+$63.56) | −$112 (10:49) → +$216 (14:08) → +$55 |
| Graveyard | 361 | 56% | −0.114 (journal) | **−$703.08** (−$543.96) | +$47 (10:01) → −$1,098 (11:10) → −$703 |
| Gen | 245 (+31) | 38% | −0.329 (journal) | **−$2,744.98** (−$2,546.06) | +$323 (10:42) → −$3,579 (14:53) → −$2,745 |

By side (R / $ after costs): Primary shorts −4.6R / −$184, longs +2.1R / +$93; T1 shorts +3.0R / +$51; T2 shorts
+2.0R / +$107, longs −16.1R / −$52; **GY longs −56.3R / −$918**, shorts +4.7R / +$215; **Gen longs −61.0R / −$1,981**,
shorts −28.5R / −$764. On a trend-down day the long dip / failed-break books lost and the short books made a little.

**Primary live-funds hold: closed RED again.** −$91.43 after costs (−$79.55 before; −0.168R avg, 15 trades) → streak
**0** (second red day). Since Day 1 (10-23): 3 of 6 sessions positive, **−$227.29** after costs (−$159.33 before).
Since start: 6 of 19 positive, −$1,248.65. Last 10 sessions: 4 green. Nothing changes; lifting the hold is the owner's call.

**Why Primary lost (ask WHY):** it was +$144 at 14:21 on its ST7 / NS5 longs and MF4 / L3 shorts. Then 5 shorts entered
13:55-15:00 — RW3-FD ×3 (TOL, ZETA, ASML), RW5-FD and MF2-FD (both ZETA) — and all 5 stopped (−5.4R, −$220) when the
index bounced +0.7% from 14:52. ZETA alone took 3 short lots (−$154). Checks: (a) stacked short lots are *not* worse
on Primary's record (2nd lot +0.029R n 84, 3rd+ +0.274R n 45, vs first lots −0.075R), so no stacking cap; (b) on two
years, when SPY is ≤ −1% at 14:30 it closes lower 75% of the time (`pmrev_out.txt`), so the late bounce was the
exception, and the "skip late shorts when the index is extended" swarm found nothing (0 of 12, below). Verdict: a
variance day, no rule change.

### 1a. Promoted L3 setups, Primary day 1 (`l3etb_out.txt`)
- **Gap-Down Rebound Overbought Short (all day)** (`L3-gap-slope-rsi5hi-FD`): 1 trade (CRNC) +0.34R, +$4.76. 17
  signals: 15 not shortable / ETB, 1 spread; what-if of the 14 skipped +6.8R (before costs).
- **Gap-Down Recovery Fade (all day)** (`L3-gap-slope-fromopen-FD`): **0 trades.** 46 signals: 41 not shortable /
  ETB, 5 spread > max; what-if of the 45 skipped **+42.1R** (before costs) on a down day that suited shorts.
- Is the borrow skip costing L3 over time? No: across all accounts since 10-12, L3-fromopen's 1,315 not-shortable
  what-if signals average **−0.053R** vs **+0.199R** for the 245 taken trades (NTSB above taken on 8 of 12 days with both;
  corr 0.30); rsi5hi-FD 296 NTSB −0.022R vs 77 taken +0.189R. Today is the big exception. FYI: L3 fires mostly on
  hard-to-borrow gap-down names, so its Primary trade count will stay well below the Testing signal counts.

## 2. Winner / loser autopsy (`autopsy_out.txt`, `tables_out.md`; SIP 1-min MFE / MAE for all 782 trades)

- **Losers "never worked" again:** Primary 7 of 8 losers never reached +0.2R (−$285); winners peaked late (median 75
  min), losers early (8.5 min); winners gave back 0.03R. Same shape in the other accounts.
- **Graveyard:** the four failed opening-range-low longs (`CWT14-failbrk-orl-*`) lost −$812 on 136 trades as the index
  slid all morning (10:00-11:10 entries −$773); the −2R latch and per-setup cap blocked 247 + 164 signals worth −75.6R /
  −15.7R (what-if). `CWT09-gapdn-vwaploss-g5-short` took a 25-entry burst at one poll (24% win, −$172) while its
  sibling `CWT09-gapdn-bounce-g5-lowerhalf-short` made +$269 (best burst in the 10-06..10-30 record, 15 entries +9.7R).
- **Gen:** −$2,745 on 245 booked trades. Worst: GEN-261019-04 (EMA-change RSI14 MID long) 12 trades −$769 (leveraged
  ETFs AXTX, MVLL, BEX, SNDU, SNXX with 6-7% stops carry $75-131 risk per lot at Gen's flat ~$1,840 notional);
  GEN-261020-03 30 trades 0% win −$635; GEN-261028-08 29 trades −$589. Gen's whole book since 10-19 is −0.28R per
  trade; neither breadth-gate token (`BRop*` / `BRvw*`) nor side separates winners. Big-risk lots (> 2x the day's median
  $ risk) are not worse in R (Gen −0.309 vs −0.282R), so no sizing item.
- **Testing 2:** `NM-AR-AM-gapdown-capitulation-long` 5 trades 0% win −$103 (record 38 / 4 sessions −0.405R);
  17 late flattens of open winners gave back −$224 from the 14:08 peak.
- **Bursts** (`burst_out.txt`): unchanged picture; 10-30 adds the best burst on record (above). The 10-29 item
  (`nightly-1029-burst20-one-bet`) stands.
- **15:45 flatten** (`flat1545_out.txt`, 2,041 lots since 10-06): +66.9R vs the 15:55 flatten (avg +0.026 → +0.059R),
  15 of 19 days better, t_day 2.02; **today +18.7R** — 10-29 + 10-30 = 58% of the gain; shorts +53.3R, longs +13.6R.
  Live-only evidence; added to `nightly-1027-flatten-1545`'s notes (still idea, the 2-year test on the setups' own lots
  is not done).
- **Cost filter day 1 (CF, Testing only):** T1 skipped 5 (what-if +2.8R), T2 skipped 32 (what-if −16.4R, saved). Review 11-12.
- **Checked, no new pattern:** twins, latency terciles, lot number, refires, re-arm after −2R in the Testing accounts.

## 3. Backlog (2 new, both tested and failed; 1 updated)
- `nightly-1030-late-short-extended-index` (risk) — **failed**, 12 configs (`lateext.py`): skip short entries at
  tod ≥ 13:00 / 13:30 / 14:00 when SPY from-open ≤ −0.75 / −1.0 / −1.25%. Skipped shorts lose in train and valid in 8 of
  9 cells (best: 13:30 / −0.75%: train −0.175R n 295 t 1.62; valid −0.102R n 572 t 0.79), but no valid t above 0.94
  vs the bar 2.23. The long mirror (3 configs) had no lab long trades after 14:00 (empty → counted as failures).
  Coverage gap: the lab lists hold base windows, not the -FD full-day versions Primary runs.
- `nightly-1030-afternoon-index-reversal-long` (setup, Move Hunt) — **failed** on the premise (`pmrev.py`, 1 config):
  20 sessions in 2 years with SPY ≤ −1% at 14:30; SPY's 14:30 → close move −0.19% avg, up on 25%.
- `nightly-1027-flatten-1545` — notes updated with tonight's live replay.

Swarm: 2 new items (< 3), no setup at a gate; the small swarm above ran because the Primary loss needed a WHY.

## 4. Suggestions (`combined_out.txt`, `onebig_out.txt`; all accounts merged, 19 sessions, costs in)

The Friday demotion watch (WATCH-NS3, with MF3-FD / MF5-FD) is due tonight. Both proposals are moves to the Graveyard,
where the setups keep trading (no setup is switched off, rule 20).

- **DECISION DM-NS3:** move **Big Loser VWAP Reclaim Fade (all day)** (`NS3-failed-vwap-reclaim-short-FD`, Testing 2)
  and its liquid-names twin `RW4-ns3-adv150-short-FD` (Testing 1 + Testing 2) to the Graveyard.
  NS3-FD: 112 trades / 13 sessions, 39.3% win vs 49.3% needed, −0.147R, w/o best day −0.270R, last 4 −0.629R, −$553;
  RW4-FD: 104 / 14, 32.7% vs 49.2%, −0.246R, w/o best day −0.354R, last 4 −0.673R, −$540. 2-year: NS3 +0.056R (t 1.26),
  RW4 +0.054R (t 1.13), both losing on up days. Recommendation: **yes**. Reply "DM-NS3 yes" / "DM-NS3 no".
- **DECISION DM-MF:** move **Early Sellers into a Pop (all day)** (`MF3-open-flowsell-rsi5hi-FD`, Testing 1) and
  `MF5-flowsell-vwapup-rsi5hi-FD` (Testing 2) to the Graveyard. MF3-FD: 141 / 15, 45.4% vs 57.5%, −0.225R, w/o best day
  −0.265R, last 4 −0.588R, −$44; MF5-FD: 74 / 14, 37.8% vs 51.7%, −0.284R, w/o best day −0.361R, last 4 −0.665R, −$75.
  2-year: base MF3 −0.074R (t −2.5), MF5 −0.052R (t −2.39). Recommendation: **yes**. Reply "DM-MF yes" / "DM-MF no".
- **No promotion is ready.** Best non-Primary records with 25+ trades are all carried by one day
  (`NS4-pm-vwap-reclaim-oversold-short-FD` +0.187R / w/o best day +0.011R, 95%).
- BRAKE-1 (open since 10-29): unchanged; today's 5 family stops (RW3-FD ×3, RW5-FD, MF2-FD) all came after the family's
  last entry (15:00), so the brake would have changed nothing. No new numbers that change it.

### 4a. Monitor marks (docs/live/monitor.json)
- **Afternoon VWAP Reclaim Fade (all day)** (`NS4-pm-vwap-reclaim-oversold-short-FD`, Testing 1 → Primary, mark
  10-27): today 1 trade −1.03R (−$9.64); since the mark 3 sessions, 8 trades, 25% win, −2.74R (−0.343R), +$6.24. Record
  26 / 10, 53.8% vs 43.1%, +0.187R, w/o best day +0.011R (10-22, 95%, **1 day**). **Lean: wait** (leaning drop).
- **Generated NewLOD, Flow3lem0p37 LUNCH short** (`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`,
  Gen → Testing 1, mark 10-27): no trade today; since the mark 1 trade −1.12R. Record 12 / 3, 58% vs 33%, +0.509R, w/o
  best day −0.009R (10-27, 101%, **1 day**). **Lean: wait.**

### 4b. Watch: CWT14-failbrk-pdl-p10-lowvol-long (Primary → Testing 2 from 10-28)
Since the move: 3 sessions, 48 trades, 56% win, −8.31R (−0.173R), −$67.51 (today 10 trades −3.68R, −$26.41). Record
220 / 15, 66.8% vs 66.5% needed, −0.015R, w/o best day −0.043R, 2-year −0.095R.

## 5. ST-P (Primary −2R latched per-setup stop), day 2
**Blocked 0 entries; no setup latched in time to matter.** RW3-FD reached −3.26R, but its three lots entered at 13:55,
14:06 and 15:00 and the first stop came at 15:22, so the latch never had a later signal to block. No decision item.

Educational only — not financial advice.
