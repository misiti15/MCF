# BDI daily 2026-11-19 (Thursday), REFOCUSED (CAPTURE / COVERAGE)

*Educational only — not financial advice. The live figures are **paper** results from one session. The two lab tests
cover 2 years each. Nothing here shows that anything works live. **Configurations tried tonight: 2** (swing1119-L16
NTBE, 1; GUD1, 1). The locked block 2024-11-01..2025-02-28 was not read.*

**Rule changes in the window (ledger).** 11-19 is **day 1 of C3 Epoch 1**: NS5 out of Primary, BASE1 twin, C3-EXIT100,
ROT / ROT2, BAR2, WB / WB5, SCORE / UNIT1, DQ-P3 / P4, U9-TGT, U9-ETB and TAGS1. It follows GY-BENCH and SRCV1 (11-18)
and TSZ1, the WB copies and the promotion hold (11-17). Primary days before and after 11-19 are different books, and
Testing $ is under TSZ1 sizing. **From 11-20:** the broker stop/target rounding fix (housekeeping), 9 new testing
setups, and the ULT admissions (ledger 2026-11-20-ult1119-testing-admissions). The day-type averages below (10-06..11-18)
span the 10-23 Testing stop change, the 10-28 Primary sizing change, the 10-29 latch, ROT1 (11-16) and TSZ1 (11-17).

**Market: a gap-up-and-reverse day.**

| | Gap | Open → close | Low |
|---|---|---|---|
| SPY | **+0.98%** | **−3.01%** | −3.01% at 15:05 |
| QQQ | +1.74% | −3.87% | −4.02% at 15:11 |
| IWM | +0.35% | −2.54% | |

- SPY was −0.21% from the open at 10:00.
- The 11:49–12:05 leg took SPY from −1.14% to −2.45%.
- Day type: DOWN by the ±0.25% open→close rule, and an SPY **gap-up open** (≥ +0.30%).

## 0a Move Hunt (research/bdi/moves/moves_1119_out.txt; moves.csv +100 rows)
Inputs were rebuilt in scratch with research/ops/coverage1029/fetch.py, fetch5.py and frames_today.py. The logic is
unchanged. Live trades come from all 10 accounts: 1,066 trades on 577 symbols. There were 1,286 liquid names, and the
top 25 per side is kept.

| Set | 11-19 | 11-18 |
|---|---|---|
| All movers | **1/50 = 2%, +0.19R** | 4/50 = 8%, +0.84R |
| Tradable (blackout removed) | **1/50 = 2%, +0.19R** | 5/50 = 10%, +2.00R |

- **The only catch:** SPY long 15:00 → 15:50, Testing F `intraday_momentum`, +0.19R.
- **Wrong side:** CI and UNH longs while both fell 1.5 ATR, −2.23R.
- **Miss reasons (all set):**

  | Reason | Misses |
  |---|---|
  | No setup signalled | 23 |
  | Traded outside the move | 15 |
  | Earnings blackout | 7 (6 on the event day: PDD, BBWI, WSM, ESTC, NTES, GAP, ZM) |
  | Wrong side only | 2 |
  | Skipped for spread | 2 (HNGE 64 bps, FCNCA 42 bps) |

- **42 of 50 movers decided by 09:50, and 32 by 09:45.** That is the opening leg 09:35 → 10:39, the first leg of the
  index fall from the gap-up.
- **16 of the 25 top longs are inverse or vol ETPs**, a market-short bet bought at 09:35–09:50:
  - SPXU, SPXS, SDS, SH, SPDN, SDOW, SQQQ, QID, PSQ, UVIX, UVXY, VIXY, VXX, PLTD and MSTZ, plus AMDL on the short side.
  - Most show "no setup signalled". No live setup buys inverse or vol ETPs on a falling open.
  - The only live inverse trades were L3's SPXS / SQQQ **shorts** at 11:16–11:46, the wrong direction and outside the
    move (rootcause_1119 R1; DECISION INV is already with the owner).
- **Managed care short, day 2 in a row:** CI, UNH, MCK, DVA (+ VHT), 09:35 → ~10:50. On 11-18 it was UNH, HUM, ELV, MOH,
  CNC, CVS and DVA. 0 caught today, and CI / UNH were traded long. A recurring sector move is evidence for
  `mh-1102-group-laggard-hedged` and the queued `mech-0935-harness`. No new card.
- **Precursors** (research/bdi/moves/precursors_1119_out.txt; non-blackout rows 09:50–15:00, K = 1 ATR):
  - Base rate 0.08% long and 0.06% short: almost nothing moved 1 ATR after 09:50.
  - On a day like this the 09:50+ scan has no power; the decision was before the lab window.
  - No precursor test was run. MH1105-P1, MH1106-P1 and MH1109-P1 already failed on 2 years.
  - The opening-bar window stays the open C3-MECH item (`mech-0935-harness`). `bdi-tod-open-0935-simple` (30 configs)
    and `reddit-1102-open-candle-expansion` (12) failed as simple 09:35–09:45 entries.

## 0b Swing autopsy — Primary (root cause reused from research/rootcause_1119/FINDINGS.md)
**Method and code:** research/bdi/1106/swings.py, inputs only changed (research/bdi/1119/swings.py → swings_out.txt,
timeline_p.csv).
- **Curve:** a 1-minute mark-to-market of every lot. Realised R is after costs.
- **Close:** −16.21R / −$825 after costs (Alpaca −$760.48).
- **MTM peak:** **+8.69R at 11:40**. The nightly figure, +8.12R at 11:42, comes from polls.
- **Trough:** **−19.60R at 13:39**.

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific (incl. exits, costs) |
|---|---|---|---|---|---|
| 09:50 → 10:49 | −1.16 | −1.18 | +0.61 | −0.58 | +0.00 |
| 10:49 → 11:40 (to peak) | +9.85 | +10.30 | +0.29 | +0.22 | −0.96 |
| **11:40 → 13:39 (peak → trough)** | **−28.29** | **−17.86** | **−4.80** | **−0.60** | **−5.02** |
| 13:39 → close | +3.39 | +1.35 | +3.37 | −0.19 | −1.14 |

- **Top 5 names of the peak → trough leg** (−17.70R together): SPXS L3 −6.30, SQQQ L3 −4.71, SMH ST7 −2.36, TECL ST7
  −2.17, FTEC ST7 −2.16. By setup: ST7-FD −14.77, L3-fromopen −11.01, RW5 −3.71.
- **Timeline (5-min steps, timeline_p.csv):**

  | Time | Book R | SPY from open | Book beta (R per +1% SPY) | Lots |
  |---|---|---|---|---|
  | 11:39 | +6.54 | −0.99% | +21.1 | 7 long / 7 short (the shorts are SPXS / SQQQ, i.e. long the market) |
  | 11:49 | +3.37 | −1.14% | +22.4 | |
  | 11:54 | −7.80 | −1.56% | | |
  | 11:59 | −11.22 | −1.93% | | |
  | 12:04 | −13.25 | −2.45% | −0.6 (book now short) | all 14 ST7 / L3 lots stopped 11:50–12:05 (FINDINGS) |
  | 12:34 | −15.27 | −1.62% (bounce) | | 5 RW shorts |
  | 13:14 | −13.23 | | | |
  | 13:39 | −19.60 | −2.12% (second bounce) | −3.3 | 9 RW3 / RW5 shorts |
  | close | −16.21 | | | 13:39 → close +3.39R as SPY fell to −3.0% |

- **What turned it:**
  - A long-index book (+21R per +1% SPY) met the 1.3% drop at 11:49–12:05: market −17.9R.
  - After the flush the book turned short. Its RW3 / RW5 shorts, entered after the low, gave back −6.4R in the two SPY
    bounces at 12:19–12:34 and 13:14–13:39. That is the −4.80R mismatch and part of the stock-specific part.
  - The long-index exposure was itself the two setup defects from the root-cause file: the ST7 RSI warm-up burst, and
    L3 shorting inverse ETFs. Both are owner decisions ST7 and INV, and are not repeated here.
  - Swing type: `swing-midday-flip`-like. The book was one-sided with the index, then flipped side after the move.

**Lead (merged, not new): swing1119-L16 = backlog `nightly-1119-near-target-breakeven`** (hypotheses.jsonl; pre-registered
before the run; configs 1, lineage N 31, BAR90 2.36).
- **Rule:** once a lot reaches ≥ 80% of its target distance on 1-minute bars, its stop moves to entry. This fits the
  case: 6 of 7 ST7 burst lots reached 80–92% of target, then took a full stop.
- **2-year result (E4 on the BEREPLAY 1-minute engine; research/bdi/1119/ntbe_bt.py → ntbe_bt_out.txt; costs in):
  FAIL.**
  - 1,165,576 trades, 95 setups. **Delta −0.0070R per trade** (−8,154R, day-t −8.58).
  - TRAIN −0.0098, VALID −0.0056, LATE −0.0044.
  - Every SPY day type is worse: up −4,292R, quiet −2,793R, down −1,069R.
  - **1 of 35 family-sides better** (NS4 short +0.006R). Worst: ST4 long −0.021R per trade.
  - Setups: 6 better (+17.2R), 85 worse (−8,163.9R).
  - The break-even exit lost **68,701 target hits** and saved only 37,363 full stops.
  - Primary: ST7-FD −7.7R (w/o best day −9.7R), L3-fromopen −581R, RW3-FD −12.2R, RW5-FD −9.7R.
- **Today, in-sample (does not count):** all accounts +17.7R on 115 changed lots, of which Primary +9.25R
  (fwd_ntbe_out.txt). That is the reversal-day tail; on 2 years the exit costs R on the other days.
- This agrees with BEREPLAY BE50 / BE75 (0 and 2 of 27 family-sides better). Making the trigger target-relative does
  not change the sign.
- **Card parked.** There is no forward shadow beyond the day-0 check. The `stopL-be1r` forward shadow already logs live
  break-even effects.

**Forward tallies:**
- **swing1118-L15** EOD-loser short cover (research/bdi/1118/fwd_l15.py → research/bdi/1119/fwd_l15_out.txt): first
  out-of-sample session **+10.11R on 114 lots**, 9 of 10 accounts better, Primary 2 lots +0.14R. 1 of the 10 sessions
  the bar needs.
- **fwd_swings L1 / L2 / L3 / L6** (research/bdi/1112/fwd_swings.py → fwd_swings_out.txt):
  - L1: no class A.
  - L2: no trigger.
  - L3: not qualifying.
  - L6: counter-index entries 371 at −0.474R vs others 695 at −0.001R (−0.473). The counter entries were longs on a
    falling day.

**Lead count:** 27 hypotheses (L16 added and closed) and 2 swing-type rows. Backtest passes: only swing1111-L13
LATCH-CLOSE. Best positive forward figure: gate1-checkpoint-gate, +13.81R over 3 sessions (last tallied 11-10). Newest:
L15, +10.11R over 1 session.

## 0 Per-account lines (11-19; SPY gap +0.98%, open→close −3.01% = DOWN, gap-up open)
- **$** is the Alpaca day P/L (nightly).
- **R** is journal R **after costs** (pnl_adj / $ risk). Outside Primary it is lower than the nightly's R, which is
  before costs (r_multiple): for example On Deck −13.00 vs −11.70, Testing A −5.30 vs −1.75 and Graveyard −79.49 vs
  −61.83.
- **Peak** is the realised (exit-ordered) running peak; Primary's MTM peak is in 0b.
- **Day-type columns:** average R per session the account traded, 10-06..11-18 (10 up / 12 quiet / 10 down sessions).
  Testing B–F have 1–5 sessions per type.
- **Script:** research/bdi/1119/acct.py → acct_out.txt.

| Account | $ | Trades | Avg R | Total R | L / S | Realised peak | Best setup | Worst setup | Up / Quiet / Down avg per day |
|---|---|---|---|---|---|---|---|---|---|
| Primary | −$760 | 32 | −0.507 | −16.21 | −9.55 / −6.66 | −1.14 (11:37) | RW3-FD +2.03 (8) | ST7-FD −8.66 (8) | −8.92 / −4.70 / +7.43 |
| On Deck | −$300 | 41 | −0.317 | −13.00 | −9.16 / −3.84 | +2.75 (11:41) | RW1-FD +0.75 (10) | NS5 −6.52 (16) | −22.40 / −15.74 / −13.17 |
| Testing A | +$107 | 197 | −0.027 | −5.30 | −3.17 / −2.13 | +6.42 (12:23) | CWT14-pdl-p05-R2A-short +5.90 (129) | MF2-WB3 −5.82 (5) | −23.15 / −15.21 / −50.20 |
| Testing B | −$184 | 104 | −0.302 | −31.38 | −34.85 / +3.47 | +0.95 | GEN-261022-05 short +8.87 (34) | GEN-261023-04 long −11.39 (20) | +2.58 / +2.40 / −5.42 |
| Testing C | −$47 | 62 | −0.190 | −11.79 | −17.73 / +5.94 | +6.13 | GEN-261027-09 short +3.36 (8) | GEN-261027-06 long −7.84 (11) | +1.93 / −1.17 / −5.58 |
| Testing D | +$41 | 49 | +0.033 | +1.62 | −3.17 / +4.79 | +2.74 | GEN-261029-06 short +3.78 (23) | GEN-261019-03 long −4.25 (12) | +7.28 / — / −5.72 |
| Testing E | +$37 | 30 | −0.008 | −0.25 | −0.69 / +0.44 | +3.58 | NS3-failed-vwap-reclaim-short +2.27 (3) | GEN-261027-07 −1.05 (1) | −20.37 / — / −10.73 |
| Testing F | −$32 | 114 | −0.035 | −3.95 | −10.17 / +6.23 | +2.50 | RW7-gapdn-bounce-early-short-FD +9.73 (50) | CWT14-pdl-p10-lowvol-long-WB3 −5.74 (18) | −17.52 / — / −0.61 |
| Gen | −$143 | 69 | −0.237 | −16.38 | −19.92 / +3.54 | −1.06 | GEN-261020-10 short +3.50 (40) | GEN-261020-09 long −10.38 (16) | −33.74 / −24.40 / −29.49 |
| Graveyard | −$439 | 368 | −0.216 | −79.49 | −100.33 / +20.84 | +0.64 | NS3-failed-vwap-reclaim-short-FD +12.88 (25) | GEN-261022-01 long −20.31 (24) | −39.21 / −25.12 / −84.03 |

- **A −3% day where the shorts paid and the longs did not:**
  - Across Primary, On Deck and Testing A–F, trades with **long market exposure** (inverse-ETF shorts counted as long)
    lost **−110.3R on 238 trades (−0.464R)**.
  - Trades with short market exposure made **+30.1R on 391 trades (+0.077R)** (patterns_out.txt).
  - Every account's short side was positive or near flat, and every long side was negative.
- **Primary lost on a down day** for the second session running. It averages +7.43R on down days. Today the cause was
  long exposure built by setup defects (0b), not its short book: RW3 +2.03R.
- **COVERAGE gap stands:** Primary −8.92R per up day and −4.70R per quiet day. No account with enough sessions is
  positive on both.

## 1 Patterns (research/bdi/patterns.csv +290 loser rows; research/bdi/1119/patterns.py → patterns_out.txt)
Accounts: Primary, On Deck and Testing A–F (629 trades). The classifier is the 1106 one, plus a new first label
`near_target_then_stopped`.

| Loss type | Losers | R |
|---|---|---|
| Wrong side after a big swing | 69 | −55.1 |
| Small MFE then failed | 41 | −43.9 |
| Never worked | 43 | −39.1 |
| Near target then stopped | 30 | −32.5 (Primary −10.8, On Deck −6.3) |
| Late hold | 67 | −25.7 |
| Gave back gains | 31 | −13.4 |
| Stopped then reversed | 9 | −10.2 |

- **Same-symbol stacking:** lot 1 is 612 trades at −0.117R; lot 2+ is 17 trades at −0.522R. That is mostly L3's 3
  SPXS + 3 SQQQ. STOP2 (1) rules out structural caps; the inverse guard (INV) removes these lots.
- **Leveraged / inverse ETPs by underlying (exposure = the position's market sign):**
  - QQQ-long exposure: 27 trades, −15.4R (TQQQ / QLD longs and SQQQ / QID shorts).
  - SPY-long exposure: 15 trades, −8.8R (SPXS shorts, SPXL / UPRO longs).
  - XLK-long (TECL): 5 trades, −3.6R.
  - MU-long (MUU): 3 trades, −3.2R.
  - QQQ / SPY-short exposure: 8 trades, +2.0R.
  - Today the underlying, not the ticker, is what decided these trades. This is evidence for
    `bdi-1102-underlying-exposure-cap` (idea) and INV. No new card.

## 2 Recurring patterns → rules
- The near-target full stop recurs. It is tested tonight (L16) and fails on 2 years, so it is not a rule.
- Inverse / vol ETPs lead the opening leg on falling days, and live setups only ever short them. A long-side
  inverse-ETP setup on a falling open is the CAPTURE idea. Prior work bounds it:
  - `bdi1015-idxdip-gapdn-earlylow` (32 configs, best t 0.89).
  - GATE2 (held-side pullbacks, 0 of 11).
  - rootcause_1119: after DOWN-confirmed, the compass called SPY's next 60 minutes right only 48.9% of the time.
  - It is noted, not re-tested. It would need the 09:35 frames (`mech-0935-harness`).
- Managed care short two days running is a sector-move example for `mh-1102-group-laggard-hedged`.

## 3–4 New tested idea (COVERAGE, queue `mech-gapup-movehunt`, priority 1) — GUD1: FAIL
**Backlog** `mech-1119-gud1-gapup-gapdn-reclaim-long` (C3-MECH card with mechanism tag; pre-registered in the card
before the run; configs 1). **Script** research/bdi/1119/gud1_bt.py → gud1_bt_out.txt (E2 2-year screen: lab frames +
gates, production + TOD costs).
- **Rule:** on SPY gap-up opens (≥ +0.30%), go long a stock that gapped ≤ −1.5% at the first 5-minute bar 09:50–11:00
  with fromOpen ≥ +0.5% and above VWAP. t1s1, ADV ≥ $95M, close ≥ $5. It is long-only, so no borrow is needed.
- **Mechanism:** the market-wide bid absorbs idiosyncratic gap-down selling, and reclaiming names squeeze. This is the
  mirror of Primary's gap-down fades, which lose on gap-up days.
- **Result:**

  | Sessions | n | Avg R | t | TRAIN | VALID | LATE | w/o best day |
  |---|---|---|---|---|---|---|---|
  | SPY gap-up (124) | 2,887 (23.3 per session) | −0.042 | −0.70 | −0.120 (t −2.09) | +0.022 | −0.315 (6 sessions) | −0.083 |
  | Control (other sessions) | | −0.029 | | +0.055 | −0.084 | | |

  The gap-up condition **does not carry the effect**: the control is better in TRAIN, so the mechanism is falsified as
  stated.
- **What it shows:** the rule is market beta. In the control it makes +0.281R on SPY up closes and −0.448R on down
  closes, and on gap-up opens it is −0.041R even on up closes. Today proves the point: a +0.98% gap closed −3%. For
  COVERAGE the useful day type is the open→close direction, which is not known at entry. The card is parked.
- **Queue note:** `mech-gapup-movehunt` stays pending. The descriptive Move Hunt over gap-up sessions is still to do.

## 5 Decisions
None. Nothing passed. The ST7 and INV decisions already cover today's root causes, and the promotion hold and the
Friday C3-EPOCH window stand. No Testing suggestion: neither test is a near miss.

## Weekly KPI (BDI, week 11-16..11-19)

| Ideas tested | Passed research | Passed live |
|---|---|---|
| 5 (L14, L15, EODREV1, L16, GUD1; 5 configs) | 0 (L15 the only near miss, now forward) | 0 |

Scratch (deleted afterwards): `mh1119/`. Educational only — not financial advice.
