# BDI daily 2026-11-20 (Friday), REFOCUSED (CAPTURE / COVERAGE)

*Educational only — not financial advice. The live figures are **paper** results from one session. The lab tests cover
2 years each. Nothing here shows that anything works live. **Configurations tried tonight: 3** (OPX1-A, OPX1-B,
swing1120-L17). The locked block 2024-11-01..2025-02-28 was not read.*

**Rule changes in the window (ledger).** 11-20 is **day 2 of C3 Epoch 1** (since 11-19: NS5 out of Primary, BASE1 twin,
EXIT100, ROT / ROT2, BAR2, WB / WB5, SCORE / UNIT1, U9-TGT / U9-ETB, TAGS1). **From 11-20:** broker stop/target
rounding fix (housekeeping), 9 ultimate_1119 testing admissions, FOOTRACE-EXIT + GY foot race. **From 11-23:** PR #238
(BEG-ORB / BEG-GNG, Remedy-Q 12:30 copies, BRAKE-BURST, watchdog, WW-PROTECT, WW-CLUSTER, RETIRE-R3) and PR #239 (Friday
review: 12 FOOTRACE-EXIT moves, 12 retirements). Primary's lineup and rules are unchanged by both. Day-type averages
below (10-06..11-19) span the 10-23 Testing stop change, 10-28 Primary sizing, 10-29 latch, ROT1 (11-16), TSZ1 (11-17)
and the 11-19 epoch.

**Market: a failed opening push, then a trend-down day.**

| | Gap | Open → close | Session high |
|---|---|---|---|
| SPY | −0.31% | **−3.20%** | +0.50% at the 09:55 bar, low into 15:55 |
| QQQ | −0.97% | −4.51% | +0.44% at 09:55 |
| IWM | −0.33% | −2.40% | +0.74% at 09:55 |

Day type DOWN (±0.25% open→close rule), the 2nd −3% session running. Compass W60 DOWN-confirmed from 11:15 (nightly).

## 0a Move Hunt (research/bdi/moves/moves_1120_out.txt; moves.csv +100 rows)
Inputs rebuilt in scratch with research/ops/coverage1029/fetch.py, research/bdi/moves/fetch5.py and frames_today.py
(logic unchanged). Live trades from all 10 accounts: 1,467 trades on 713 symbols; 1,282 liquid names; top 25 per side.

| Set | 11-20 | 11-19 |
|---|---|---|
| All movers | **4/50 = 8%, +5.90R** | 1/50 = 2%, +0.19R |
| Tradable (blackout removed) | **6/50 = 12%, +6.19R** | 1/50 = 2%, +0.19R |

- **Catches (all short, all outside Primary):** IBIT +1.84R, FBTC +2.00R, BITO +1.24R (Graveyard
  `GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short`), SNPS +0.82R (Graveyard
  `RW3S-gapdn-flowsell-short-FD`); tradable set adds RIOT +0.01R (Testing A `MF4-h40-open-flowsell`) and COMP +0.28R
  (Graveyard `MF4-h40-open-flowsell-FD`). **0 of 25 long movers caught.**
- **Wrong side:** 12 trades −14.15R (all set): crypto ETFs (IBIT, FBTC, GBTC, BITO, ETHA) bought long while they fell
  1.2 ATR, TTWO short into a +1 ATR pop, SQQQ shorted while it rose.
- **Miss reasons (all set):** no setup signalled 16, traded outside the move 13, earnings blackout 8 (7 on the event
  day: INTU, BJ, GAP, ESTC, IESC, DIS …), wrong side only 6, skipped 3 (SNAP cost filter / daily loss limit, FDXF spread
  32 bps, CGGR daily loss limit).
- **Timing:** 38 of 50 movers decided by 10:05, 20 by 09:50 — the **SPY opening push topped at the 09:55 bar** and the
  decision points cluster on the turn (10:00–10:05). A second cluster at **14:05** (UVIX, UVXY, VIXY, VXX +1.2–1.3 ATR
  to 15:34) — the same bar NM-ETF bought 12 bull ETFs (0b).
- **Inverse / vol ETPs among the top-25 longs for the 3rd session running** (11-19: 16; 11-20: SPXU, SPXS, SDS, SH, SPDN,
  SQQQ, QID, PSQ, TSLQ, MSTZ, BTCZ, UVIX, UVXY, VIXY, VXX = 15). No live setup buys them on a falling index. This is
  the CAPTURE idea tested tonight (OPX1, step 3) — it fails on 2 years.
- **Crypto complex short** (IBIT / FBTC / GBTC / BITO / ETHA / RIOT short, MSTZ / BTCZ long), 09:35–09:40 → ~11:04:
  a sector move; 3 of 8 caught by one Graveyard GEN setup. Evidence for `mh-1102-group-laggard-hedged`; no new card.
- **Precursors:** no new precursor test. The recurring precursor (failed opening push → inverse ETPs) is tested as a
  setup in step 3 (OPX1), which is the stronger form. MH1105-P1 / MH1106-P1 / MH1109-P1 already failed on 2 years.

## 0b Swing autopsy — Primary (research/bdi/1120/swings.py → swings_out.txt, timeline_p.csv)
Method and code = research/bdi/1106/swings.py via 1119, inputs only (two edits: top 4 legs; peak→trough only when the
trough follows the peak). 1-minute mark of every lot; realised R after costs. Close **+3.00R / +$162 after costs**
(Alpaca +$214.16). MTM trough −0.86R at 10:11, **peak +6.54R at 13:48**.

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific (incl. exits, costs) |
|---|---|---|---|---|---|
| 10:11 → 12:04 | +6.59 | +3.94 | +0.50 | +0.63 | +1.52 |
| **13:48 → 13:56** (largest) | **−7.35** | **−6.29** | −0.52 | +0.00 | −0.54 |
| 13:56 → 14:11 | +6.14 | +6.92 | −0.21 | −0.15 | −0.42 |
| **14:11 → 14:35** (NM-ETF burst) | **−3.99** | −2.75 | −0.56 | −0.58 | −0.10 |
| 10:11 → close | +3.85 | +4.44 | −0.60 | −0.29 | +0.30 |

- **Top 5 names, 13:48 → 13:56** (−4.53R): ERAS `L3-gap-slope-fromopen-FD` −1.66, AGI `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`
  −0.81, SNOW `RW3-gapdn-rsi5pop-flowsell-short-FD` −0.71, U (RW3) −0.71, CORZ (RW5) −0.64.
- **Top 5 names, 14:11 → 14:35** (−5.23R): SMH −1.12, SPXL −1.05, TECL −1.04, UPRO −1.02, QLD −0.99, all
  `NM-ETF-late-dip-di-long`; by setup NM-ETF −9.40, RW3 +1.85, RW5 +1.19.
- **Timeline (5-min, timeline_p.csv):**

  | Time | Book R | SPY from open | Beta (R per +1% SPY) | Lots |
  |---|---|---|---|---|
  | 10:09 | −0.79 | +0.47% | −0.7 | 1 short |
  | 12:04 | +5.73 | −1.54% | −3.3 | 5 short (realised +3.40) |
  | 13:44 | +5.59 | −1.66% | −10.9 | 13 short |
  | 13:54 | +1.93 | −1.33% (bounce) | −11.0 | 13 short |
  | 14:09 | +3.81 | −1.69% | −11.0 | 13 short |
  | **14:14** | +3.16 | −1.96% | **+2.6** | **9 long** / 14 short (NM-ETF burst 14:11–14:16) |
  | 14:19 | +3.42 | −2.02% | **+5.5** | 12 long / 14 short |
  | 14:34 | +1.73 | −2.58% | −2.0 | 6 long / 11 short (realised +4.08 → −0.80) |
  | close | +3.00 | −3.20% | | |

- **What turned it:** two things. (1) The largest leg is pure market: a 13:48–13:56 SPY bounce (−1.71% → −1.14%) against a
  fully short 13-lot book (−11R per +1% SPY), recovered in the next 15 minutes (+6.14R). Noise, not a lead. (2) The only
  **avoidable** swing: NM-ETF's 12 long-exposure ETF lots at 14:11–14:16 turned the book from −11.0 to +5.5R per +1% SPY
  on a DOWN-confirmed session at SPY −1.7%; SPY fell another 0.9% and all 12 stopped (−12.57R). Without NM-ETF the book
  made +15.57R (20/20 shorts green).
- **Swing type: new `swing-counter-index-burst`** (hypotheses.jsonl): the book is with the confirmed index direction;
  one setup fires a same-bar correlated burst against it and flips net beta. Distinct from `swing-burst-chase` (burst
  with the index after the move) and `swing-midday-flip`. Linked to the open DECISION ETF-BURST (a lot limit), which it
  does not duplicate.

**Lead: swing1120-L17** (hypotheses.jsonl; pre-registered before the run; configs 1, lineage N 33, t_required 2.64).
- **Rule:** the NM-ETF lab module (research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py, mask unchanged,
  t05s1). Class A = long-exposure entries (not inverse / long-vol) on bars where SPY is ≤ −1.00% from its open; class B =
  every other entry. Hypothesis: A − B ≤ −0.10R with day-t ≤ −2.64, same sign in both halves.
- **2-year result (E2 2-year screen, research/bdi/1120/l17_bt.py → l17_bt_out.txt; costs in): FAIL — falsified, the
  sign is opposite.**

  | Split | A n (sessions) | A avg R | B n | B avg R | A − B (day-t) |
  |---|---|---|---|---|---|
  | All | 121 (15) | **+0.314** (w/o best day +0.175) | 457 | +0.111 | **+0.203 (+2.24)** |
  | TRAIN | 101 (10) | +0.351 | 235 | +0.197 | +0.155 (+1.85) |
  | VALID | 14 (4) | +0.295 | 200 | +0.009 | +0.286 (+2.27) |
  | LATE | 6 (1) | −0.277 | 22 | +0.121 | −0.398 |

- On 2 years the module's long-exposure dip buys did **better** on deep-down sessions (SPY ≤ −2%: +0.332R, 63 trades):
  capitulation dips bounced. Large same-bar bursts (8+ long-exposure signals) were its best pocket, +0.480R on 66
  trades (mostly 10 TRAIN sessions). 11-20 is a loss of a size the lab has not seen; the down-session condition is not
  the cause. **Closed, no forward shadow.**
- **Useful for the open ETF-BURST study:** a per-bar lot limit would have cut the module's best 2-year pocket. Report it
  per setup with the 2-year burst column, not only the live 18 lots (consultant: −13.04R live on 3+-lot buckets).

**Forward tallies:**
- **swing1118-L15** EOD-loser short cover (research/bdi/1118/fwd_l15.py → research/bdi/1120/fwd_l15_out.txt):
  session 2 **−64.81R on 186 lots, 0 of 10 accounts better** (Primary 5 lots −1.24R; Testing B −36.68R, Testing A
  −14.40R) — the −2% losers kept falling into the close. Pooled 2 sessions **−54.70R**, 1 of 2 sessions positive; the
  bar needs 10 sessions, pooled > 0 and ≥ 60% positive. Effectively off track; kept running to 10 as pre-registered.
- **fwd_swings L1 / L2 / L3 / L6** (research/bdi/1112/fwd_swings.py → research/bdi/1120/fwd_swings_out.txt): L1 no NS5
  longs; L2 no trigger; L3 qualifying (SPY +0.50%, IWM +0.74% at 10:00): after-cut minus before +0.024R (107 trades);
  L6 counter-index entries 792 at −0.818R vs others 675 at +0.659R (−1.477): on a −3% day the counter entries were longs.

**Lead count:** 29 hypotheses + 3 swing-type rows (L17 and `swing-counter-index-burst` added). L17 closed (FAIL). Backtest passes: only
swing1111-L13 LATCH-CLOSE. Best positive forward figure: gate1-checkpoint-gate +13.81R over 3 sessions (last tallied
11-10). L15 now −54.70R over 2 sessions.

## 0 Per-account lines (11-20; SPY gap −0.31%, open→close −3.20% = DOWN; research/bdi/1120/acct.py → acct_out.txt)
$ = Alpaca day P/L (nightly). R = journal R after costs (pnl_adj / $ risk). Realised peak = exit-ordered running peak
(Primary's MTM peak is in 0b). Day-type columns: avg R per session traded 10-06..11-19 (10 up / 12 quiet / 11 down);
Testing B–F have 1–6 sessions per type.

| Account | $ | Trades | Avg R | Total R | L / S | Realised peak | Best setup | Worst setup | Up / Quiet / Down avg per day |
|---|---|---|---|---|---|---|---|---|---|
| Primary | +$214 | 33 | +0.091 | +3.00 | −12.35 / +15.34 | +4.75 (14:25) | L3-gap-slope-fromopen-FD +6.01 (7) | NM-ETF-late-dip-di-long −12.57 (12) | −8.92 / −4.70 / +5.28 |
| On Deck | +$110 | 23 | +0.444 | +10.22 | −2.37 / +12.59 | +10.83 (15:04) | RW1-gapdn-bounce-flowsell-short-FD +9.60 (14) | NM-HL-T75-pm-long −1.22 (2) | −22.40 / −15.74 / −13.16 |
| Testing A | +$113 | 232 | +0.293 | +67.88 | −42.45 / +110.33 | +67.88 (15:57) | GEN-261026-07 short +94.36 (79) | CWT14-failbrk-pdl-p05-R2A-long −25.42 (67) | −23.15 / −15.21 / −46.12 |
| Testing B | +$1,000 | 189 | +0.478 | +90.35 | −33.87 / +124.23 | +90.35 (15:57) | GEN-261022-05 short +121.12 (101) | CWT13-vwapstretch-z075-long −27.61 (25) | +2.58 / +2.40 / −9.74 |
| Testing C | −$715 | 192 | −0.626 | −120.26 | −137.65 / +17.39 | −1.04 (10:15) | GEN-261027-04 short +6.79 (10) | GEN-261027-06 long −111.25 (109) | +1.93 / −1.17 / −6.62 |
| Testing D | +$77 | 101 | −0.093 | −9.43 | −38.10 / +28.67 | +13.70 (15:26) | GEN-261029-06 short +21.97 (40) | GEN-261026-02 long −38.30 (45) | +7.28 / — / −4.25 |
| Testing E | +$299 | 81 | +0.106 | +8.61 | −15.93 / +24.54 | +22.73 (14:25) | RW7-gapdn-bounce-early-short-FD-WB3 +11.61 (16) | NM-ETF-late-dip-di-long-WB4 −17.88 (22) | −20.37 / — / −8.63 |
| Testing F | +$147 | 106 | +0.123 | +12.99 | −35.00 / +47.99 | +21.66 (15:02) | RW7-gapdn-bounce-early-short-FD +40.23 (55) | GEN-261022-06 long −15.48 (15) | −17.52 / — / −1.28 |
| Gen | −$1,579 | 132 | −0.571 | −75.39 | −104.61 / +29.22 | +1.68 (11:24) | GEN-261021-04 short +23.70 (15) | GEN-261019-04 long −99.06 (100) | −33.74 / −24.40 / −28.03 |
| Graveyard | −$1,542 | 378 | −0.505 | −190.97 | −252.93 / +61.97 | +5.70 (10:00) | GEN-261022-09 short +9.70 (5) | GEN-261019-05 long −77.98 (75) | −39.21 / −25.12 / −83.53 |

- Every account's short side was positive; every long side negative. Across Primary, On Deck and Testing A–F, **long
  market exposure** (inverse-ETF shorts counted as long) **456 trades −335.1R (−0.735R)**; short exposure **501 trades
  +398.5R (+0.795R)** (patterns_out.txt).
- Primary's down-day average is now +5.28R (11 sessions); the COVERAGE gap stands: −8.92R per up day, −4.70R per quiet
  day, and no account with enough sessions is positive on both.
- The big testing figures (B +121.1R, A +94.4R) are down-day short streaks whose best day is 91–94% of their total
  (consultant) — `1 day`, not a record.

## 1 Patterns (research/bdi/patterns.csv +426 loser rows; research/bdi/1120/patterns.py → patterns_out.txt)
Accounts: Primary, On Deck, Testing A–F (957 trades). Classifier unchanged from 1119.

| Loss type | Losers | R |
|---|---|---|
| Wrong side after a big swing | 130 | −119.0 (Primary −10.5 = the NM-ETF lots) |
| Never worked | 103 | −96.6 |
| Small MFE then failed | 89 | −94.1 (Testing C −48.3) |
| Late hold | 48 | −30.1 |
| Gave back gains | 42 | −34.7 (Testing C −20.1) |
| Near target then stopped | 9 | −10.6 |
| Stopped then reversed | 5 | −5.8 |

- Same-symbol stacking is not today's problem: lot 2+ 9 trades +2.46R.
- Leveraged / inverse ETPs by underlying: SPY-long exposure 23 trades −21.9R and QQQ-long 15 trades −15.9R (every
  account), against SPY / QQQ-short exposure 15 trades +6.4R. As on 11-19, the underlying decided these trades.
- The near-target full stop (L16) is small today (9 losers) — consistent with its 2-year FAIL.

## 2 Recurring patterns → rules
- **Inverse / vol ETPs lead the long movers on falling sessions (3 sessions running).** Turned into a rule and tested
  tonight as OPX1 (step 3): FAIL — the failed-open-push trigger is rare (26 sessions in 2 years) and a coin flip on the
  day type. Not a rule.
- **Correlated ETF dip-buy bursts against a confirmed down index (3rd time: 11-17, 11-19, 11-20).** Tested as L17 (0b):
  falsified (the lab pocket is positive). The lot-limit version is the open ETF-BURST decision.
- **Wrong-side counter-index entries** (L6 −1.477R gap today) keep recurring on trend days; the remedies already tested
  (L6 2-year, W4 filters, STOP2) fail or are guarded. No new card.

## 3–4 New tested idea (CAPTURE + COVERAGE) — OPX1: FAIL (both configs)
**Backlog** `mech-1120-opx1-failed-open-push-etp-long` (C3-MECH card with mechanism tag; pre-registered in the card before
the run; configs 2). **Script** research/bdi/1120/opx1_bt.py → opx1_bt_out.txt (E2 2-year screen: lab frames + gates,
production + TOD costs).
- **Rule:** SPY's opening move fails — session high so far ≥ +0.30% and SPY back ≤ −0.10% from the open at a 5-min bar
  09:50–10:30 (A), or the mirror (low ≤ −0.30%, back ≥ +0.10%; B). At that bar buy the index ETPs on the reversal side
  (A: SQQQ, SPXU, SPXS, SDS, PSQ, QID, SDOW, SPDN, UVXY, VXX; B: TQQQ, SPXL, UPRO, QLD, SSO, UDOW, TNA). t1s1, long-only.
  Control = the same ETPs at 10:00 on the other sessions. Pass bar t_required(76) = 2.94.
- **Mechanism:** a failed opening drive traps the early side; their exits push the index the other way into late morning.

  | Config | Sessions | n | Avg R | Day-t | TRAIN | VALID | w/o best day | Control |
  |---|---|---|---|---|---|---|---|---|
  | OPX1-A (inverse / vol) | 26 | 256 | −0.004 | −0.02 | −0.410 (14 sess) | +0.457 (12) | −0.042 | −0.267 (t −6.14) |
  | OPX1-B (bull 2x/3x) | 26 | 182 | −0.092 | −0.54 | +0.015 (20) | −0.450 (6) | −0.135 | −0.112 |

- **What it shows:** the trigger is far rarer than the last two live days suggest (both 11-19 and 11-20 triggered A, and
  the inverse ETPs rose 1–5% to 11:30 — in-sample, not counted). On 2 years the sign flips between halves, and by the
  SPY close A's trigger sessions split 13 down (+0.382R) / 5 quiet (−0.236R) / 8 up (−0.498R): the failed push does not
  tell the day type by 10:30. OPX1-A beats its control overall (inverse ETPs decay and lose at 10:00 on ordinary days)
  but not in TRAIN. Card parked; no salvage as a setup. Agrees with rootcause_1119 (48.9% next-60-min hit after
  DOWN-confirmed).

## 5 Decisions
None. Nothing passed. The ETF-BURST decision already covers today's leak; the promotion hold and PROT-29 stand.
No Testing suggestion: neither OPX1 config is a near miss. Primary records (Primary only, R after costs, nightly):
RW3-FD 176 tr +0.175R, w/o best +0.043R (79%, `1 day`), w/o top 2 −0.072R; RW5-FD 186 tr +0.109R, w/o best +0.004R
(97%, `1 day`), w/o top 2 −0.066R; L3-fromopen 188 tr +0.200R, w/o best +0.049R (82%, `1 day`), w/o top 2 −0.093R;
NM-ETF 27 tr −0.424R. Rule changes inside those windows: 10-28 sizing, 10-29 latch, 11-12 LR8, 11-19 epoch.

## Weekly KPI (BDI, week 11-16..11-20)

| Ideas tested | Passed research | Passed live |
|---|---|---|
| 8 (L14, L15, EODREV1, L16, GUD1, OPX1-A, OPX1-B, L17; 8 configs) | 0 (L15 the only near miss; its forward is −54.7R after 2 sessions; L17 falsified, opposite sign) | 0 |

Scratch (deleted afterwards): `mh1120/`. Educational only — not financial advice.
