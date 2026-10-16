# Nightly winner/loser autopsy: 2026-10-16 (primary, Testing 1, Testing 2)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They are a diagnosis, not evidence. No locked holdout was scored and **no backtest was run tonight** (only 2 new hypotheses, none near a gate; 0 configurations). Everything below is a descriptive split of today's trades (about 30 one-session splits, none of them gated).*

Inputs: `journal.db`, `status.json` (every commit since the 10-15 open, via `git log`), `reports/scorecard.json`, `setups/2026-10-16.json` and `intraday/2026-10-16.jsonl` from `origin/mcf-data`, `mcf-data-testing` and `mcf-data-testing2`; `longhold/status.json` and `marks.csv` from `mcf-data-longhold` (S6). SIP 1-minute bars for the 333 traded symbols plus SPY, QQQ and IWM, and SIP daily bars for the 20 S6 holdings (Alpaca market data only). No trading endpoint was called; broker orders and fills were **not** read.

Scripts in this folder (copied from nightly1015 and re-dated): `fetch.py`, `build.py` (`trades.csv`, 747 real trades), `summ.py` (`summ_out.txt`), `attr.py` (`attr_out.txt`, with the SPY/QQQ/IWM open path), `autopsy.py` (`autopsy_out.txt`), `sc3.py` (`sc3_out.txt`), `statusscan.py`, `add_backlog.py`. Not needed tonight (all gaps 0.00): `gapcurve.py`, `brokermtm.py`, `gapstep.py`. New: `s6close.py` (S6 equity at the official close from SIP daily closes, plus index gap / close-to-close).

**Market: a one-way down day.** SPY opened +0.19% above the 10-15 close (773.24), QQQ −0.34%, IWM +0.16%. None of them ever traded back to the open after 09:30–09:43. Open to close: **SPY −1.29%, QQQ −2.16%, IWM −1.84%**, lows at 15:07 (SPY −1.61%, QQQ −2.50%, IWM −2.01%). Close to close: SPY −1.11%, QQQ −2.50%, IWM −1.69%. Steady selling from 11:00 (SPY −0.27% at 11:00, −0.79% at 12:00, −1.30% at 14:15).

**The open path (for the index dip-bounce setups, first session today).**
- SPY: −0.12% at 09:35, low by 09:44 **−0.28%**, by 09:54 **−0.29%**, open-path low −0.36% at 10:11; never back to the open.
- QQQ: low by 09:44 **−0.57%**, by 09:54 **−0.74%**, open-path low −0.79% at 10:11; never back to the open.
- IWM: high +0.14% at 09:43, then down; −0.47% at 10:53.
- So no index dip reached the IDX thresholds (SPY ≥ 0.50/0.75%, QQQ ≥ 1.0%), and there was no bounce to trade either.

## Failures first

### 1. Day P/L, clean close, broker vs journal
| account | equity 09:29 (pre-open) | equity 15:55 (closed) | broker day P/L | journal day P/L | gap | orders `submitted` | overnight (10-15 close → 10-16 pre-open, flat book) |
|---|---|---|---|---|---|---|---|
| Primary | 94,906.62 | 94,913.79 | **+7.17** | +7.17 | **0.00** | 0 | −2.81 |
| Testing 1 | 97,710.52 | 97,691.12 | **−19.40** | −19.40 | **0.00** | 0 | −4.15 |
| Testing 2 | 96,758.29 | 95,775.80 | **−982.49** | −982.49 | **0.00** | 0 | −9.75 |
| S6 long-hold (separate, not ranked) | 95,818.61 (official 10-15 mark) | **90,388.22** (cash + held qty × SIP official close, `s6close.py`) | **−5,430.39 (−5.67%)** | — | — | — | — |

- **Clean close in all three:** phase `closed` 15:55, `positions: []`, `health.flatten_failed: []`, no `data_stale` and `data_outages: []`, `partial_lots: []`. All orders `closed` (P 313, T1 1,495, T2 2,281; 0 `submitted`, any day). EOD reports and scorecards committed 15:56–15:57 ET.
- **Testing 2 gap is 0.00 today.** The earlier T2 gaps (10-14 −374.72, 10-15 −178.63) were §1446(f) PTP withholding, resolved. T2 traded no PTP today (no ET/EPD/MPLX/PAA/WES), so there is no residual to attribute. The overnight −9.75 (flat book) is not trading P/L; the overnight moves are small in all three accounts (P −2.81, T1 −4.15) and look like fee postings (not verified; activities were not read).
- **PTP exclusion was not live yet today:** #64 (universe excludes PTPs) merged at 16:15 ET, after the session. **Testing 1 shorted EPD** (25 sh @ 36.07, stopped 36.14, −$1.75, 10:41–11:11 ET). T1's broker-vs-journal gap is 0.00 at the close; if a 10% withholding on that sale (~$90) posts later, it will show as an overnight drop in T1 on Monday. Watch it.
- **Testing 2 hit its daily loss limit at 11:20 ET** (−60R); 385 later signals skipped (`halted` 384, `daily loss limit` 1). Its last entry was 11:13.
- **Testing 1 job restarted at 11:52 ET** (unplanned: polls reset 116 → 1 between the 11:49 and 11:52 snapshots, no `handover` phase, and the 09:22 job never committed "done"; only "job 11:52 done" at the close). 51 open lots carried over; no gap in snapshots longer than ~4 min and the journal still equals the broker. Primary and T2 did the planned 15:02–15:04 handover. Housekeeping H-1.

### 2. Testing 2 CWT14 `scale_out_r 0.25` did not happen: the live runner does not implement scale-outs
- `CWT14-failbrk-pdl-p05-long` (the only setup with `scale_out_r: 0.25`, `a19bac2`): 16 trades, **0 partial exits**. Every trade closed its full quantity at the stop or the full target; on the 8 symbols it shared with `CWT14-failbrk-pdl-p05-lowvol-long` (no scale-out) the exits are the same price and size (AZN, CSCO, DBX, DT, FIS, HUBS, SNOW, SNPS).
- Code: `scale_out_r` is read in `mcf/strategies/base.py` (put on the signal) and used only in `mcf/backtest/engine.py`. `mcf/execution/runner.py` manages time stops, breakeven and trailing stops only, and the brackets are placed for the full quantity. **The owner's 10-16 change is a no-op live.** Housekeeping H-2 (implementation, not a strategy change).
- What it would have changed today (estimate, not simulated with the breakeven path): 13 of 16 reached ≥ +0.25R; 4 of them were then stopped (AZN, CIBR, COHR, DBX, **−$32.17**). With half off at +0.25R and the rest at breakeven those 4 would have made about +$3.8, so roughly **+$36** on the stopped trades, less what the halved winners give up (8 targets, median target 0.48R).

### 3. Testing 2: −$982.49, the reversal longs on a trend-down day
- Longs **274 trades, 47% wins, −0.365R, −$1,114.75**; shorts 114, 73%, +0.034R, +$132.26.
- CWT14 orl/pdl failed-breakdown longs: orl-p05-lowvol −$255.06 (64), orl-p05 −$195.79 (60), orl-p10 −$111.92 (39), orl-p10-lowvol −$108.55 (31), pdl family −$175.01 (51). CWT12-coil-k4-long −$238.50 (22, 27% wins, MFE of losers 0.22R).
- **111 of 177 losers never worked (MFE < 0.2R, −$1,114.66)**. Winners took only 0.50R median MFE (t05s1 geometry, target ≈ 0.5R), losers −1.07R MAE. 341 of 388 trades were entered in the 10:00 hour; 206 were in same-setup clusters of ≥ 5 per poll.
- Positive: CWT14 pdh shorts (p10 +$52.34, p05-lowvol +$31.84), CWT09-g5-lowerhalf 1 trade +$50.40.

### 4. Testing 1: −$19.40, longs −$813.51 against shorts +$794.11
- Worst: heat_fade_long-FD −$231.93 (49, 20% wins), ST1-ordn-long-pm-FD −$210.08 (19), heat_fade_long (ex-primary) −$195.47 (45, 22%), LIQ-orl-sweep-open15-s25-long −$102.57 (17).
- Best: heat_fade_short-FD **+$284.71** (35, 80% wins), RW7-gapdn-bounce-early-short-FD +$134.69 (22), RW2-FD +$80.64, heat_fade_short +$77.90 (7, 86%).
- 67 losers never worked (−$729.78); 47 losers had reached ≥ 0.5R first. 21 stops worse than −1.1R.
- Refire (#57): 12 refire trades, 58% wins, +0.397R, +$58.79. Same-setup re-entries 7, +$15.57 (L3-fromopen-FD 6, +$36.37).

### 5. Primary: +$7.17, the three promoted setups carried it
- Promoted today (first Primary session):

| setup | trades | win% | avg R | P/L | own signals skipped | skipped by lot cap / opposite side |
|---|---|---|---|---|---|---|
| MF3-open-flowsell-rsi5hi-FD | 12 | 50% | −0.103 | **+$51.16** | 2 (spread 30% of stop SHLD; spread 31 bps MPWR) | **0** |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 3 | 100% | +0.578 | **+$33.98** | 2 (BSP not shortable; TXG spread 44 bps) | **0** |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 2 | 50% | +0.369 | **+$6.48** | 1 (MPWR spread 31 bps) | **0** |
| together | 17 | 59% | +0.050 | **+$91.62** | 5 | 0 |

- **None of their signals were interrupted by the lot cap or the opposite-side rule.** The interruption ran the other way: the 6 Primary `lot cap` skips were MF5 (ENB, FER, HRL, RPRX) and MF4 (HRL, CUBE), all on symbols MF3-FD already held from 10:00–10:40. MF3 (windowed) and MF3-FD also both took ENB and RPRX.
- MF3-FD's avg R is negative while its P/L is positive: 5 stops of about −1.1R on small risk vs. 5 targets with larger risk (TEM +$41.82).
- Losers: NS5-sma50-flush-oversold-long −$67.32 (3), MF3 (windowed) −$17.30 (6), NS1 −$17.60 (1). Longs 4 trades −$84.92; shorts 32 trades +$92.09.
- Stacking: first lots on symbols that were never stacked 16 trades, +0.270R, +$64.73; every lot on a stacked symbol lost (lot 1 −0.534R, lot 2 −0.506R, lot 3 −0.164R; 20 trades, −$57.56).
- NS2 is no longer in Primary (Primary ran 12 setups). The scorecard still lists it as "below backtest – review" (51 trades, −0.515R, −$832.31) from its Primary days.

### 6. NS2 in Testing 1 (former primary, demoted 10-16)
`former_primary: {demoted: 2026-10-16, first_testing_session: 2026-10-16, review_after_sessions: 10}` is in the T1 snapshot. Today NS2-sma50break-overbought-short (windowed) produced **0 signals** (no overbought SMA50 breaks on a down day); NS2-FD 1 trade, +$6.30. Session 1 of 10.

### 7. Testing 1 index dip-bounce setups (IDX1 trail/hold, IDX2, IDX3, IDX5): none fired
All 5 are in the T1 setup snapshot and the runner's strategy list. **0 signals**: SPY was at most −0.28% from the open by 09:44 and −0.29% by 09:54 (needs ≥ 0.50% / 0.75%), QQQ −0.74% by 09:54 (needs ≥ 1.0%). No 3x ETF was picked (no setup armed). Correct non-fire: the day had no morning dip-and-bounce; it sold off later.

### 8. EOD email charts: landed
`reports/charts/2026-10-16/` exists on all three branches: Primary 8 PNGs (best 3 / worst 5), Testing 1 8, Testing 2 8, plus `reports/2026-10-16.{csv,html,png}`. Whether the email itself went out was not checked (no mail access).

## Headline per account (real trades, run 1)
| account | trades | win% | avg R | P/L (journal) | broker | cost-adj | stop / target / flatten | intraday (marked, 5-min) |
|---|---|---|---|---|---|---|---|---|
| Primary (12 setups) | 36 | 47% | −0.109 | **+$7.17** | +$7.17 | −$14.41 | 17 / 14 / 5 | min −$118 at 11:10; peak +$43 at 15:10; green from 10:10 at 18 marks |
| Testing 1 | 323 | 48% | −0.075 | **−$19.40** | −$19.40 | −$78.38 | 134 / 125 / 64 | min −$274 at 13:20; green only 15:45–15:50 (+$40) |
| Testing 2 | 388 | 54% | −0.248 | **−$982.49** | −$982.49 | −$1,084.81 | 176 / 211 / 1 | peak +$8 at 10:15; min −$983 at 15:15 |
| S6 long-hold (separate) | — | — | — | — | **−$5,430.39 (−5.67%)**, equity 90,388.22 at the official close | — | — | 15:59 snapshot 90,420.78 |

## Winner/loser autopsy (`autopsy_out.txt`)
| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winners give-back | time to MFE, winners | same-setup clusters |
|---|---|---|---|---|---|---|
| Primary | 3 of 19, −$35.47 | 9 | 0.99 / 0.28 R | 0.14 R | 76 min | max 3 per poll; singles −0.089R, 2–4 −0.130R |
| Testing 1 | 67 of 169, −$729.78 | 47 | 0.96 / 0.30 R | 0.08 R | 57 min | singles −0.042R, 2–4 +0.023R, 5–9 −0.391R, ≥ 10 −0.496R |
| Testing 2 | 111 of 177, −$1,114.66 | 21 | 0.50 / 0.19 R | 0.09 R | 12 min | singles −0.434R, 2–4 −0.230R, 5–9 −0.261R, ≥ 10 −0.124R |

- Primary's losses were not "never worked" today: 9 of 19 losers reached ≥ 0.5R first (median loser MFE 0.42R) and then stopped as the tape kept falling or bounced intraday. Exits are not the issue in T1/T2: winners kept their peak.
- The losses in T1 and T2 are entry direction again, now on the long side: reversal longs on a trend-down day (yesterday it was shorts on a reversal-up day).

## Intraday attribution (marked: realized plus open lots at the 1-minute close)
- **Primary:** low −$118 at 11:10 (NS5 −43.6, MF3-FD −29.9, MF3 −29.3) as the 10:00 flow-sell shorts were stopped on the 10:35–10:50 index bounce; green from 10:10 at times and from ~12:00 as the index fell; peak +$43 at 15:10 (MF3-FD +56.7, RW3-FD +46.6, RW5-FD +19.9, NS4 +18.7 vs NS5 −62.7).
- **Testing 1:** low −$274 at 13:20 (heat_fade_long-FD −250.6, heat_fade_long −234.1, ST1-FD −204.6, LIQ-orl −109.3 vs heat_fade_short-FD +272.8); the shorts caught up into the 15:07 low; +$40 at 15:45.
- **Testing 2:** +$8 at 10:15 (CWT14 pdh shorts), then the 10:05–10:45 polls (−$1,029.61 across 300 trades) took it to the halt; −$983 at 15:15 (orl-p05-lowvol −255.1, coil-k4 −238.5, orl-p05 −195.8 vs pdh-p10-short +52.3).

## Scorecard summary, all three accounts (last summary 10-15; window now 10-13..10-16) and this week's totals
Journal real trades; the verdict uses the fixed bar in `mcf/report/scorecard.py`. Paper results, not evidence.

| account | week 10-12..10-16 journal | week broker (10-12 pre-open → 10-16 close) | by day (journal) | scorecard window 10-13..10-16 | verdicts |
|---|---|---|---|---|---|
| Primary | 154 trades, **−$768.59** | **−$767.26** (95,681.05 → 94,913.79) | +117.93, −95.39, +63.53, −861.83, +7.17 | 113 trades, −$886.52 | 11 too few, **2 below backtest – review: NS2 (51, −0.515R vs +0.021; now in Testing 1), MF5 (10, −0.254R vs −0.010)**, 1 negative (MF3-FD, 12) |
| Testing 1 | 1,449 trades, **−$2,223.87** | **−$2,283.08** (99,974.20 → 97,691.12) | +32.37, −629.03, +65.21, −1,673.02, −19.40 | 1,245 trades, −$2,256.21 | 8 positive (RW7-FD +191.02, RW3-FD +114.14, MF3-FD +95.61, MF2-FD +77.72), 16 negative (NS2-FD −397.64, RW6-FD −294.78, heat_fade_long-FD −292.95, heat_fade_short-FD −254.41), 13 too few, 2 below backtest (heat_fade_long ex-primary 59, −0.417R vs −0.138; heat_fade_short ex-primary 28, −0.590 vs −0.015) |
| Testing 2 | 2,281 trades, **−$3,690.53** | **−$4,224.20** (100,000.00 → 95,775.80) | −721.32, −103.27, −785.74, −1,097.71, −982.49 | 1,921 trades, −$2,969.21 | 2 positive (coil-k6 +15.35, pdl-p10-lowvol −6.59 with +0.036R), 12 negative, **3 below backtest – review: CWT09-g5-lowerhalf (41, −0.572R vs +0.047), CWT09-vwaploss-g5 (29, −0.702 vs −0.031), CWT13-z05-short (36, −0.412 vs −0.069)**, 10 too few |

- Broker − journal for the week: Primary +1.33 (overnight postings), T1 −59.21 (the known 10-12 −13.41 and 10-13 −25.24 residuals plus overnight postings), T2 −533.67 (PTP withholding −553.35 on 10-14/10-15, the 10-12 +58.05 residual, overnight postings).
- S6 (separate): 4 official marks plus today's close, 100,000 → 90,388.22 (**−9.61% since 10-12**; drawdown from the 10-13 high 103,471.81 is −12.6%).
- Removal from Testing needs the owner prompt (rule 20); nothing is removed here.

## S6 long-hold: first weekly rebalance (Friday close → Monday)
- Day: **equity 90,388.22 at the official close, −$5,430.39 (−5.67%)** vs the official 10-15 mark 95,818.61 (SPY −1.11%, QQQ −2.50% close to close). 20 positions, cash 3,779.20. The 10-16 row in `marks.csv` is written by the 18:20 ET evening run; it was not there yet at 16:52 ET (the 10-15 row is: −$1,179.33, −1.22%).
- Status: `next_rebalance: 2026-10-16`, `halt_file: false`, no alerts. `plans/` holds only the 10-09 init plan (20 MOC orders, reconciled 10-13). **No 10-16 plan yet at the time of this note.**
- How Monday works (`mcf/longhold/runner.py` `run`, evening phase): today is a rebalance day, so the 18:20 ET run reconciles, writes the 10-16 mark, **builds the weekly plan (signal day 10-16, exec day 10-19, time in force `opg` = market-on-open, not the close)** and commits it; the orders are submitted from 19:00 ET (the 19:10 ET run) or, failing that, by the 08:50 ET Monday morning run before 09:28. The 09:45 ET Monday run reconciles fills against the official open and retries an unfilled OPG order once as a DAY order. A data-sanity failure skips the rebalance with a `data_sanity` warning event. Check on Monday: `plans/2026-10-16.json` exists with status `submitted`, its order count, and the 09:45 reconcile.

## Hypotheses added to `research/backlog.jsonl` (source "nightly-2026-10-16")
| id | category | status | from |
|---|---|---|---|
| `nightly-1016-trend-day-long-reversal-veto` | filter | idea | T2 longs −$1,114.75 (274), T1 longs −$813.51 (154) on a day SPY never reclaimed its open; related and failed: `ix-gate`, `bdi-tg-heat-fade-long` |
| `nightly-1016-primary-one-lot-per-symbol` | risk (parent `nightly-1013-stack-clone-skip`) | idea | Primary stacked-symbol lots 20 trades −$57.56 vs unstacked first lots +$64.73; MF3 + MF3-FD + MF4/MF5 overlap on the same names |

`add_backlog.py` writes them; `python -m mcf.research.backlog report` regenerated `research/BACKLOG.md` (419 ideas). No backtest: 2 new hypotheses and none near a gate (0 configurations). Nothing went into config/ or mcf/.

## Housekeeping for the lead (not backlog)
- **H-1 (T1 unplanned restart 11:52 ET).** The 09:22 job ended without a "done" commit; a new job started at 11:52 and ran to the close. No money or lot lost (journal = broker, 51 lots carried over). Find why the first job stopped (runner log / Actions run).
- **H-2 (scale-out not implemented live).** `scale_out_r` (CWT14-failbrk-pdl-p05-long in T2, owner 2026-10-16) is ignored by `mcf/execution/runner.py`; brackets are full size and there is no partial take-profit or breakeven move. Either implement it (a partial take-profit leg or a managed partial exit + stop to breakeven, mirroring `backtest/engine.py`) or flag the config so it is not silently a no-op. Until then T2's pdl-p05-long is still the old exit.
- **H-3 (EPD in T1).** T1 shorted EPD today, before #64 took PTPs out of the universe. Watch Monday's T1 pre-open equity for a §1446(f) withholding on that sale (~$90).
- **H-4 (S6).** Confirm Monday that `plans/2026-10-16.json` was built and submitted (OPG) and that the 10-16 mark row matches 90,388.22.
