# BDI 2026-10-28: per-account session review, every trade of the 5 accounts, and a two-year test of a market-neutral leader / laggard spread

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7) from one full session (handover
#159 → #165 at 14:36-14:42 ET; T2 / Gen missed the 14:40 decision minute, see nightly1028). One session is a
diagnosis, not evidence. History numbers are **backtests** on the open two-year history (train ≤ 2025-12-31, valid
2026-01-01..10-07) with production + time-of-day costs in. The locked block (2024-11-01..2025-02-28) was never read
and no holdout was scored. No config, setup, exit or assignment was changed. No new DECISION tonight (K4-2 from the
nightly loop stays the only open owner question).*

Already done tonight and **cited, not redone**: `nightly1028/` (close and coverage, P/L, give-back curves, autopsy,
NS3-family "one bet", ST-P baseline, DECISION K4-2). **Configurations tonight: 8** (LLS 8), **0 pass, 0 near-misses**
(`counts.json`). Lineage counted with the relative-strength family: N 761, bar 3.64.

## Failures first
1. **New strategy "Leader / Laggard Spread" (BDI1028-LLS) fails: 0 of 8** (`PLAN.md` written before scoring;
   `scan_1028.py`, `eval_1028.py`, `eval_out.txt`, `results.csv`). Rule: at a fixed bar T, buy the N strongest names vs
   QQQ from the open that are above VWAP and short the N weakest below VWAP (ADV ≥ $95M), R = 0.25 ATR, equal R per leg,
   one basket per day. 8 configs (T 10:30 / 12:00 × N 5 / 10 × hold / t1s1), 426 sessions each.
   - Every basket is negative: −0.025..−0.112R per leg. Best row T 12:00 / N 5 / hold: −0.025R, t −0.90, train +0.007 /
     valid −0.064, up −0.063 / down −0.024, w/o best day −0.036R.
   - **What it learned:** the neutral pair did cut the direction bet (up and down sessions now lose about the same), and
     the **12:00 long leaders beat the same-minute random long in train and valid in all 4 rows** (+0.01..+0.10R). The
     laggard shorts beat random in train but not in valid. But the random trade itself is about −0.08R after costs on
     these geometries, so the selection edge is smaller than paying costs on two legs. Backlog
     `bdi1028-leader-laggard-spread` → **failed** (8 configs).
2. **Live fills were 47R worse than the simulated bracket today** (live −146.3R vs the same brackets on SIP 1-min −99.0R,
   all 769 trades). Part is the handover / slow-poll entries (T2, Gen, Graveyard), part is fill slippage; no new item —
   OPS-POLL / OPS-HANDOVER (nightly) cover the cause.
3. **The two skip replays disagree in the Graveyard.** A plain bracket replay of the 255 "setup daily loss limit" skips
   (`skipped.py`, setup's median cost, no extra spread) gives **+35.2R** (CWT14 ORL longs +42R); the broker what-if run
   (nightly1028 `caps.py`, run 2) gives −5.35R gross / −24.6R net. The run-2 number is the one to use; the gap is noted on
   `bdi1027-graveyard-cap-replay`. Nothing in this file argues for loosening the latch.
4. **The opposite side has no rule known at entry again.** Opposite side 1R/1R +77.0R vs live −146.3R (all of it shorts:
   opposite of shorts +0.36R, of longs −0.07R). SPY never got ≥ +0.25% at a short's entry (`flag_spy` never set), and
   shorts on names already ≥ +1% from the open did *better* (−0.16R) than the rest (−0.56R). It was the slow grind from
   the 09:49 low; nothing at entry showed it.

## 0. Per-account session review (`accounts.py` → `accounts_out.txt`; `skipped.py` → `skipped_out.txt`)
R = after costs (journal `pnl_adj` / $ risk). Break-even win% = avg loss R / (avg win R + avg loss R). Blocked signals
replayed as their own bracket on SIP 1-min bars at the setup's median cost (no extra spread; see failure 3).

### Primary (mcf-data): +$245.88, first day at ~$4,000 / position, 3rd green day in a row
- **Day:** 14 trades, **85.7% win vs 62.1% break-even**, +0.399R (+5.6R). Shorts 10 +0.437R (+$95.73), longs 4
  +0.302R (+$150.15).
- **Peak vs close:** trough −$15 (09:51) → peak +$260 (15:18) → +$246. Give-back $14: one open RW5-FD short into the
  flatten. Nothing to fix.
- **Best:** Big Loser Flush Buy `NS5-sma50-flush-oversold-long` 2 trades (CORZ, WULF at 09:50) +$145.10 — **59% of the
  day's P/L**, so the day rests on one poll. Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`
  7 trades 6 wins +$61.51.
- **Worst:** RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` XHB 14:05 −$24.80 (never worked); RW5-FD COST
  −$16.84 (+0.52R then stopped).
- **Blocked:** 3 not-shortable +3.0R, 3 spread-% +1.0R, 3 spread-bps +0.1R. Small.
- **Edits:**
  1. *No change (tested by replay):* hold-to-close would have made +13.0R vs +5.6R, but the hold lever flips with the
     day's direction (−109R over 10-20..10-26, bdi1026; −50R all accounts today). Don't over-correct.
  2. *Queued:* `bdi1028-primary-stp-sizing-audit` — ST-P (−2R latch) starts 10-29 on the new ~$4,000 sizing; compare the
     journal's latch events with the stp.py replay for the first 5 sessions ($ at the trip, entries in the trip poll,
     value of the blocked signals).
  3. *Watch:* the NS5 flush buy's share of the green streak (10-28: 59% of P/L in 2 trades). Show it with the Day-5 post.

### Testing 1 (mcf-data-testing): −$702.27
- **Day:** 162 trades, **46.3% win vs 60.7% break-even**, −0.214R (−34.6R). Shorts 75 −0.514R (−$773.37), longs 87
  +0.045R (+$71.10). Every hour from 10:00 to 14:00 negative.
- **Peak vs close:** +$83 (10:52) → −$704 (15:54). Give-back $785: 103 entries after the peak −$461.50 and 15 open
  winners at the peak later stopped −$380.30, all against the index's climb (nightly1028 `giveback_out.txt`).
- **Best:** 20-Minute Opening Range Breakout `orb20_a` 2 trades +$96.74. Big Loser Flush Buy (all day)
  `NS5-sma50-flush-oversold-long-FD` 2/2 +$33.26.
- **Worst:** `RW4-ns3-adv150-short-FD` (no display name) **0 / 16 −$362.68**; Big Loser VWAP Reclaim Fade
  `NS3-failed-vwap-reclaim-short` 0/5 −$119.54; Afternoon Blow-off Short `exhaustion_short` 1/7 −$114.53.
- **Losses:** small MFE then failed −$403 (26), wrong side after a big swing −$298 (17), never worked −$157 (13).
- **Blocked:** not-shortable 126 signals −39.0R if taken (the guard saved it); lot cap 9 −7.7R; spread-bps 48 −3.4R.
- **Edits:**
  1. *Queued (nightly, cited):* `nightly-1028-ns3-family-one-bet` — one NS3-family short per symbol per day + theme cap;
     RW4-FD and NS3 base were 21 of T1's 75 shorts and −$482. Test as written there (2-year, costs in, random-skip control).
  2. *Watch:* RW4-ns3-adv150-short-FD (T1 + T2) 101 trades −0.268R, but today is 70% of its loss → Friday review (10-30).
  3. *No change:* the 15 open winners stopped after the peak are the "cluster profit lock" idea already queued
     (`bdi1022-short-cluster-profit-lock`); the book-wide trail lost −19.5R today.

### Testing 2 (mcf-data-testing2): −$925.79, never above zero
- **Day:** 213 trades, **51.2% win vs 64.1% break-even**, −0.194R (−41.4R). Shorts 45 −0.665R (−$805.84), longs 168
  −0.068R (−$119.95). The 10:00 hour −$576.56.
- **Peak vs close:** never above $0; −$926 at the close. All of it was new entries (213 after the 09:31 "peak").
- **Best:** Big Loser Flush Buy (all day) 1/1 +$18.60; `RW1-gapdn-bounce-flowsell-short-FD` 4/5 +$13.13.
- **Worst:** Big Loser VWAP Reclaim Fade, Morning `NS3V1-am-widestop-short` **0 / 13 −$531.87 on its first day** (7
  never worked); NS3-FD 1/11 −$161.35; Afternoon Blow-off Short (all day) 0/7 −$88.38; Coil Under the High (4 bars)
  `CWT12-coil-k4-long` 77 trades −12.0R −$77.71 (→ K4-2).
- **Day 1 of the 3 moved setups:** CWT14-failbrk-pdl-p10-lowvol-long 7 trades −0.58R (−$21.98); NS4 and MF2 windows 0 trades.
- **Blocked:** twin-held 19 −17.1R (NS3-FD 17 −17.7R: the twin rule saved it), spread-% 39 −5.5R, not-shortable 34 −8.1R.
- **Edits:**
  1. *Queued:* `bdi1028-t2-pdl-trio-twin-group` — one twin group for the three failed-PDL longs (14 symbols bought by 2+
     versions, 5 by all three; every p10-lowvol trade overlapped a sibling). Test: first vs duplicate entries live, and
     the overlap / keep-first rule on the 2-year CWT14 kernels.
  2. *Owner item (nightly):* K4-2 coil-k4 → Graveyard.
  3. *Watch:* NS3V1 (13 trades, all losers) — a one-day record; it falls under the NS3-family item above.

### Graveyard (mcf-data-graveyard): −$1,079.05, the worst book
- **Day:** 298 trades, **49.3% win vs 63.4% break-even**, −0.229R (−68.3R). Shorts 148 −0.427R (−$1,079.09), longs 150
  −0.035R (+$0.04). 09:xx entries −0.592R (41).
- **Peak vs close:** never above $0; trough −$1,290 (14:44) → −$1,079. Entries, not give-back.
- **Best:** Midday Gap-Up Dip Buy (all day) `heat_fade_long-FD` 6/8 +$133.81; Failed Prior-Day-High Break Short (0.1 ATR,
  low volume) `CWT14-failbrk-pdh-p10-lowvol-short` +$59.09.
- **Worst:** Morning Bounce Fade (all day) `heat_fade_short-FD` 29 trades 17% win −$369.27; Failed Prior-Day-High Break
  Short `CWT14-failbrk-pdh-p10-short` 31 trades 16% win −$329.15 (25 entries in one poll, 11 never worked);
  `RW2-exhaustion-noon-adv150-short-FD` −$191.81.
- **Losses:** small MFE −$742 (42), never worked −$654 (38), stopped then reversed −$541 (30).
- **Blocked:** setup daily loss limit 255 (see failure 3: run 2 says the latch saved −24.6R net); not-shortable 43
  −14.6R; spread-bps 66 −13.0R; opposite side held 11 +8.0R.
- **Edits:**
  1. *Queued (updated):* `bdi1027-graveyard-cap-replay` — now also reconcile the bracket replay (+35R) with the run-2
     what-if (−24.6R) before reading either.
  2. *No change:* a burst cap on the 09:55 pdh shorts failed on two years (nightly-1015); the Graveyard exists to keep
     scoring dead setups, not to be optimised.

### Setup Generator (mcf-data-gen): −$121.63
- **Day:** 82 trades, **48.8% win vs 53.7% break-even**, −0.091R (−7.5R). Longs 60 +0.022R (+$294.63), shorts 22
  −0.399R (−$416.26).
- **Peak vs close:** +$261 (12:55) → −$122. Give-back $383: 27 entries after the peak −$271.90 (GEN-261019-10 PM short
  13 trades −$380.60) and 12 open losers −$137.20; open winners at the peak added +$26.
- **Best:** Generated ORB-fail-up AM long `GEN-261022-01-…-SPYdn-hold-long` 12 trades +5.1R +$331.00.
- **Worst:** `GEN-261019-10-FlowShift…-PM-…-t1s1-short` 2/13 −$380.60; new `GEN-261028-09-…-AM-…-t05s1-long` 24 trades
  −6.8R −$107.36 (**19 entries in one poll on day 1**).
- **Blocked:** spread-bps 29 +8.8R (the bps cap clipped winners again → `bdi1027-spread-bps-skip-replay`).
- **For the pause question (data only, no change):** since 10-19 the Gen account has 275 trades, +0.043R, +$1,066.73,
  4 of 8 days green; **w/o its best session (10-27, 128% of total R, 1 day) −0.018R**. The book's record rests on one day.
- **Edits:**
  1. *Queued:* `bdi1028-gen-new-setup-first-poll-cap` — cap a new GEN setup at 5 entries per poll in its first 5
     sessions (sample quality, not edge). Test: first-5-session records of every GEN setup since 10-19, burst vs single.
     Waits on the owner's pause decision.
  2. *Queued (cited):* `bdi1027-spread-bps-skip-replay` — Gen's bps skips were +8.8R today.

## 1. Every trade (769 of 769 with bars; `trades_bdi.py` = bdi1027's, unchanged → `per_trade_1028.csv`, `by_setup_1028.csv`, `out_1028.txt`)
- R after costs: Primary +5.6R, Testing 1 −34.6R, Testing 2 −41.4R, Graveyard −68.3R, Gen −7.5R. **Total −146.3R**
  (10-27 −124.6R). **Longs −10.3R (469), shorts −136.0R (300).** Per trade: rule values at entry (from-open, VWAP
  deviation, 15-min return, SPY from-open), MFE / MAE, time to MFE, loss type and the what-ifs are in `per_trade_1028.csv`.
- **Exit levers** (Δ R vs the simulated bracket, all accounts):

  | lever | 6 days to 10-27 | **10-28** | 7-day |
  |---|---|---|---|
  | breakeven at +0.5R | −9.8 | −11.7 | −21.5 |
  | +0.5R target | −20.2 | −10.5 | −30.7 |
  | +1R target | +27.5 | −14.3 | +13.2 |
  | 0.5R trail after +0.5R | +77.8 | −19.5 | +58.3 |
  | hold to 15:55 | +21.8 | −50.0 | −28.2 |
  | stop-and-reverse 1R/1R | −82.9 | −38.0 | **−120.9** |
  | one re-entry after a stop | −29.0 | −12.7 | **−41.7** |
  | opposite side 1R/1R | +64.5 | +176.0 | +240.5 |

  Every exit lever lost today. Stop-and-reverse and re-entry are negative on 7 days (−120.9R / −41.7R): don't. The trail
  is ahead on 5 of 7 days but failed on history (`t6-exit-overlay`, `sw-w4-book-exits`). Opposite side is the day's
  direction with hindsight (failure 4).
- **patterns.csv:** +386 loser rows for 10-28 (4,036 → 4,422; `merge_patterns.py`, idempotent by date). Loss mix: small
  MFE 27.2%, never worked 23.8%, wrong side after a big swing 13.7%, gave back 13.5%, stopped then reversed 12.2%, late
  hold 9.6% — entries again, as on 10-26 / 10-27.
- **Intraday give-back** (curves from nightly1028, attribution here): T1 ($785) and Gen ($383) gave back; both were
  mostly **new entries after the peak** (T1 59%, Gen 71%) against the index's move, plus T1's 15 stopped open winners.
  Same answer as `giveback1019/` (65-98% from after-peak entries). Primary's $14 is noise. Nothing new for giveback1019.

## 2. Recurring patterns (≥ 3 of the last 10 sessions) → testable rules
- Shorts into a slow index grind (10-12, 10-14, 10-20, 10-27, 10-28): index vetoes already failed on two years
  (`bdi1015-short-index-up-veto`, `nightly-1019-index-chase-veto`). Tonight's market-neutral pairing (LLS) was the
  structural answer to "the book is one direction bet"; it fails on costs (above).
- Same-signal concentration (NS3 family 10-21 / 10-28; three pdl longs in T2 10-28): → `nightly-1028-ns3-family-one-bet`,
  `bdi1028-t2-pdl-trio-twin-group` (both idea, tests written).
- Day-1 bursts of new GEN setups (10-27, 10-28): → `bdi1028-gen-new-setup-first-poll-cap`.

## 3. Backlog (`research/backlog.jsonl`, `research/BACKLOG.md` regenerated; `add_backlog.py`)
- New, failed: `bdi1028-leader-laggard-spread` (8 configs).
- New, idea: `bdi1028-t2-pdl-trio-twin-group`, `bdi1028-gen-new-setup-first-poll-cap`, `bdi1028-primary-stp-sizing-audit`.
- Updated: `bdi1027-graveyard-cap-replay` (note on the two replays).

## vs yesterday (10-27)
10-27: 25 configurations, 0 pass, −124.6R live. 10-28: 8 configurations, 0 pass, −146.3R live (shorts −136R on the grind
up). **Not improved.** Why: the selection kernel keeps beating random (now on both sides at 12:00 in train, longs in
valid too), but random trades lose ~0.08R after costs, and two legs double that. **Next:** test leader selection only
where costs are small relative to R (wider R, e.g. 0.5 ATR, or a cost floor like hf1027's idea), long leg only at 12:00
against a same-minute random-long baseline, before anything else in this family.

## Suggestions
None pass, so there is no new DECISION and no near-miss for Testing. K4-2 (nightly) stays the only open owner question.

Files: `PLAN.md`, `trades_bdi.py`, `merge_patterns.py`, `per_trade_1028.csv`, `patterns_1028.csv`, `by_setup_1028.csv`,
`out_1028.txt`, `accounts.py`, `accounts_out.txt`, `skipped.py`, `skipped_out.txt`, `skipped_1028.csv`, `scan_1028.py`,
`scan_out.txt`, `eval_1028.py`, `eval_out.txt`, `results.csv`, `counts.json`, `add_backlog.py`, `backlog_lls.json`.
Scan trades are in the scratchpad (not in git).

Educational only — not financial advice.
