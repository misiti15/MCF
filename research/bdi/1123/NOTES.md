# BDI daily 2026-11-23 (Monday): CAPTURE / COVERAGE

*Educational only — not financial advice. Live figures are **paper** results from one session; the lab tests cover
2 years. **Configurations tried tonight: 9** (IGR1 8, swing1123-L18 1). The locked block 2024-11-01..2025-02-28 was not
read. Lean run: scratch under scratchpad/bdi1123 (deleted after).*

**Rule changes in the window (ledger).** **From 11-23:** ST7 out of Primary (lineup RW3-FD, RW5-FD, L3-fromopen,
NM-ETF), BRAKE-BURST, watchdog dispatch, PSHADOW, QA-EXIT2 moves, BEG-ORB / BEG-GNG, Remedy-Q 12:30 copies,
FOOTRACE-EXIT 12 moves and RETIRE-R3. Today is day 1 of that set. The day-type averages below (10-06..11-20) span the
10-23 Testing stop change, 10-28 Primary sizing, the 10-29 latch, ROT1 (11-16), TSZ1 (11-17) and C3 Epoch 1 (11-19).

**Market: an index gap-up that went nowhere after the open.** SPY gapped about +5% (QQQ +7%, NVDA +31%), dipped
−1.07% from the open by 09:40, and closed −0.28% from the open. Under the ±0.25% open→close rule that is a **DOWN** day,
even though it was a gap-up day. Burst brake fired in 4 testing accounts. Gap-up long setups lost −44.5R on 364 lots in
testing (nightly).

## 0a Move Hunt (research/bdi/moves/moves_1123_out.txt; moves.csv +100 rows)
Inputs were rebuilt with research/ops/coverage1029/fetch.py (no polls or journal), fetch5.py (5-min bars from 11-03 for
ADV ≥ $90M names, enough for the 14-day ATR) and frames_today.py. The logic is unchanged. Live trades come from all 10
accounts: 1,232 trades on 640 symbols, 1,286 liquid names, top 25 per side.

| Set | 11-23 | 11-20 (last run) |
|---|---|---|
| All movers | **5/50 = 10%, +0.40R** | 4/50 = 8%, +5.90R |
| Tradable (blackout removed) | **5/50 = 10%, +0.40R** | 6/50 = 12%, +6.19R |

- **Catches:**
  - CL long: NS1 / LD1 / LD7 in Graveyard, On Deck, Testing B and Testing C, +1.00R.
  - NVDQ long: Testing D CWT14-orl-WB5, +0.25R.
  - KYMR short: Graveyard GEN-261021-03, +0.36R.
  - ZS short: On Deck orb20_a, −0.12R.
  - SQQQ short: Testing E GEN-261027-07, −1.09R.
  - The long side caught **2 of 25** (11-20: 0 of 25).
- **What was known at the decision point:** 35 of 50 movers were decided at 09:35–09:40, inside the opening dip, when
  SPY was −1.07% from its open at 09:40.
  - **Shorts:** inverse / leveraged ETPs that spiked into the dip and then fell: NVDQ, NVD, SNDQ, SPXU, SPXS, SDS, SH,
    SDOW, SPDN, SQQQ, plus CORD. 6 were **skipped as not shortable / ETB**, which is correct: shorting an inverse fund is
    a long market bet. Big gappers also faded: ZS +22%, DELL +35% (blackout), KYMR.
  - **Longs:** defensives that had gapped **down** against the index climbed to about 11:00: CL, CHD, CLH (+0.9 to
    1.0 ATR). Also NVDA continuation (blackout) and KYMR.
- **Miss reasons (all set):**
  - No setup signalled: 21.
  - Traded outside the move: 11.
  - Skipped: 10 (6 ETB, KYMR / STRC on spread, MSTZ on the cost filter).
  - Wrong side only: 3.
  - Wrong-direction trades: 21, −9.42R. Primary shorted CHD 7 times (+0.33R net) and CL while both were long movers.
- **Idea from this:** the defensive counter-gap rebound became IGR1 (step 3). It **FAILS** on 2 years.

## 0b Swing autopsy: Primary
Sources: research/hardstop_1123/REPORT.md Part 2, plus research/bdi/1123/swings.py → swings_out.txt and
timeline_p.csv. The method is 1106/1120's, with one added leg: the pre-trough peak to the trough.

- **Close:** **+0.49R after costs** (+$185 at Alpaca), 24 trades.
- **Part 2 mark:** peak **+5.4R at 12:49**, low **−3.8R at 14:26**.
- **This script's mark:** 1-minute, no costs while open, close mark at 15:59. Peak +5.28R at 12:49, trough −1.90R at
  14:25.

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific |
|---|---|---|---|---|---|
| 11:51 → 12:48 | +5.23 | −0.04 | +4.19 | −0.09 | +1.18 |
| **12:48 → 14:25** (the day's swing) | **−7.22** | **+0.81** | **−5.23** | −0.33 | −2.48 |
| 14:25 → close | +4.74 | +0.66 | +1.11 | +0.35 | +2.62 |

- **Top 5 names in 12:48 → 14:25 (−4.77R):**
  - SYY (RW5-FD) −1.03R
  - UL (RW5-FD) −1.01R
  - UNH (L3-fromopen) −0.99R
  - KMB (RW3-FD) −0.95R
  - TMUS (RW5-FD) −0.79R
- **By setup in the same leg:** RW5 −4.59, RW3 −2.07, L3 −1.58, NM-ETF +1.02.
- **What turned it:** not the index. SPY was flat from its open during the leg (−0.38% → +0.16%), and the book's net
  beta was about 0 (−0.6 to +0.3R per +1% SPY). The loss was **setup-day mismatch**. 14 of 18 shorts were defensives
  (staples / health / telecom) that had gapped down while SPY gapped up. That group rebounded midday against the
  shorts. Later shorts (entered 11:30–13:10) stayed open into it (Part 2: −4.84R). The 14:25 → close recovery came from
  the same names easing back, plus NM-ETF's inverse-ETF longs (LABD, SOXS).
- **Lead swing1123-L18** (hypotheses.jsonl; pre-registered before the run; configs 1, lineage N 34, t_required 2.66).
  - **Rule:** RW3-FD and RW5-FD masks, unchanged. Class A = entries on SPY gap ≥ +0.75% sessions; class B = all other
    sessions. Hypothesis: A − B ≤ −0.10R.
  - **Result: FAIL, falsified** (research/bdi/1123/igr_l18_bt.py → igr_l18_bt_out.txt; E2 2-year screen, costs in).
    - A: n 476 on 36 sessions, −0.029R.
    - B: n 11,709, −0.055R.
    - A − B = **+0.026 (t +0.31)**. TRAIN +0.006, VALID +0.065, LATE −0.123 (1 session).
    - Per setup: RW3 +0.041, RW5 +0.010.
    - Within A, the SPY open→close direction decided the result: down days +0.194, up days −0.257. That is not known at
      entry.
  - 11-23 was a loss specific to that day, not a condition. Closed with no forward shadow. A day-type switch on
    RW3/RW5 would also break rule 26.
- **Forward tallies:**
  - **swing1118-L15** EOD-loser short cover (research/bdi/1123/fwd_l15_out.txt): today **−25.54R on 147 lots, 0 of 10
    accounts better**; Primary has no qualifying lots. Pooled over 3 out-of-sample sessions: **−80.25R**, 1 of 3
    sessions positive. Kept to 10 sessions as pre-registered.
  - **fwd_swings** (research/bdi/1123/fwd_swings_out.txt):
    - L1: no NS5 class-A lots.
    - L2: no trigger.
    - L3: not qualifying (SPY −0.47% at 10:00).
    - L6: counter-index entries n 348 at +0.236R vs others +0.001R. The sign is opposite to L6's hypothesis. Running
      11 sessions: −0.261R, t −1.78.
- **Lead count:** 32 rows in hypotheses.jsonl (16 swing L-leads), L18 added and closed.
  - Only one backtest pass: swing1111-L13 LATCH-CLOSE. It is also the best forward lead: +302.7R over 7 sessions,
    w/o best +94.9R, `1 day` (69%), last tallied 11-20.
  - L15 is clearly off track.

## 0 Per-account lines (11-23; research/bdi/1123/acct.py → acct_out.txt)
$ = Alpaca day P/L (nightly). R = journal R after costs. Peak = realised running peak, exit-ordered. Day-type columns
= avg R per traded session 10-06..11-20 (up / quiet / down, sessions in brackets). Testing B–F have 1–7 sessions per type.

| Account | $ | Trades | Avg R | Total R | Peak (time) | Best setup | Worst setup | Up / Quiet / Down per day |
|---|---|---|---|---|---|---|---|---|
| Primary | +$185 | 24 | +0.021 | +0.49 | +5.25 (14:11) | RW3-gapdn-rsi5pop-flowsell-short-FD +3.61 (6) | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD −3.35 (7) | −8.92 (10) / −4.70 (12) / +5.09 (12) |
| On Deck | −$45 | 50 | −0.060 | −2.99 | +5.91 (12:45) | MF3-open-flowsell-rsi5hi +1.74 (27) | ST6-volspikeup-short-mid-t1s1-FD −4.64 (6) | −22.40 / −15.74 / −11.21 |
| Testing A | +$527 | 120 | +0.220 | +26.38 | +26.97 (15:56) | NS3V1-am-widestop-short +17.38 (86) | GEN-261026-04 short −1.25 (2) | −23.15 / −15.21 / −36.62 |
| Testing B | −$74 | 53 | −0.121 | −6.39 | +2.96 (11:38) | NM-RWN3-ns3-spyup-early-short +2.66 (10) | GEN-261023-04 long −4.93 (14) | +2.58 / +2.40 / +4.56 |
| Testing C | +$119 | 53 | +0.093 | +4.92 | +7.19 (15:55) | ULT-22-wb4-wide-etf-long +2.79 (6) | GEN-261023-03 short −1.21 (1) | +1.93 / −1.17 / −22.85 |
| Testing D | +$208 | 136 | +0.052 | +7.11 | +8.94 (15:56) | NM-RWN5-ns3-mon-weakrs-short +5.08 (44) | CWT14-failbrk-orl-p10-long-WB5 −2.21 (23) | +7.28 / — / −5.12 |
| Testing E | +$269 | 432 | +0.053 | +23.11 | +23.11 (15:56) | GEN-261026-05 short +19.55 (20) | ULT-05-withgap-cont-long −20.51 (310) | −20.37 / — / −5.76 |
| Testing F | +$70 | 75 | +0.029 | +2.14 | +2.63 (10:16) | GEN-261020-06 long +4.82 (7) | GEN-261022-03 short −3.02 (10) | −17.52 / — / +1.10 |
| Gen | +$94 | 22 | +0.471 | +10.37 | +10.37 (15:55) | GEN-261023-06 short +11.08 (17) | GEN-261019-04 long −1.17 (1) | −33.74 / −24.40 / −32.77 |
| Graveyard | +$138 | 267 | +0.069 | +18.36 | +18.95 (15:58) | GEN-261022-08 short +35.96 (24) | GEN-261021-06 Gapge1p2 long −22.03 (51) | −39.21 / −25.12 / −94.27 |

- **Every account except On Deck and Testing B finished up.**
  - Short side: **+103.1R** on 602 trades.
  - Long side: **−19.6R** on 630 trades (nightly).
  - The gap-up longs carried the long side's loss (ULT-05 −20.5R, GEN-261021-06 −22.0R).
- **Primary's peak and close:** the exit-ordered realised peak is +5.25R; it closed +0.49R. 11 lots flattened at 15:55
  for −2.45R.
- **COVERAGE gap unchanged:** Primary averages −8.92R per up day and −4.70R per quiet day.
- **Big testing days to call out:** GY GEN-261022-08 +35.96R and E GEN-261026-05 +19.55R (104% of its total,
  consultant). Both are one-day figures, not records.

## 1 Patterns (research/bdi/patterns.csv +460 loser rows; research/bdi/1123/patterns.py → patterns_out.txt)
Accounts: Primary, On Deck, Testing A–F (943 trades). The classifier is unchanged.

| Loss type | Losers | R |
|---|---|---|
| Never worked | 197 | −62.3 (Testing E −33.8 = ULT-05 time stops) |
| Small MFE then failed | 98 | −53.8 (Testing E −21.0) |
| Late hold | 98 | −35.2 (Testing D −8.9) |
| Gave back gains | 35 | −17.0 |
| Wrong side after a big swing | 19 | −8.4 (11-20: 130 / −119.0) |
| Stopped then reversed | 7 | −7.5 |
| Near target then stopped | 6 | −6.6 |

- **Never worked** is today's loss type. That points to entries with no follow-through (gap-up longs), not timing.
  Primary's share is small (−2.1R).
- **Stacking:** lot 2+ has 115 trades at +0.030R, close to lot 1 (+0.062R). Not today's problem.
- **Inverse-ETP shorts:** they were ETB-blocked, and the inverse longs that did fill mostly won. That is consistent
  with the inverse shadow (nightly: kept inverse longs +48.7R over 2 sessions).

## 2 Recurring patterns → rules
- **Gap-up long family on index-gap days (`never worked` time stops):** the recurring loss is already filed as
  nightly-1123-index-gap-residual-gap (family remedy, per-setup counts). Not re-filed.
- **Defensive counter-gap rebound** (11-06 MH, 11-23 MH and swing): tested twice tonight from both sides (IGR1 long,
  L18 short filter). Both fail. It is a beta bet on the SPY open→close direction, which is not known at entry.

## 3–4 New tested idea (CAPTURE + COVERAGE): IGR1 FAIL (0 of 8)
**Backlog card:** `mech-1123-igr1-index-gap-rotation-long`. C3-MECH, day type = index gap-up. Pre-registered in the
card before the run. Parent: nightly-1123-index-gap-residual-gap. Configs 8, lineage N 12, t_required 2.23.

**Script:** research/bdi/1123/igr_l18_bt.py → igr_l18_bt_out.txt. E2 2-year screen: lab frames + gates, production +
TOD costs, one trade per symbol-day, t1s1. Long-only, so no borrow is needed.

- **Rule:**
  - SPY gap ≥ G.
  - The stock gapped down: gap ≤ 0, and gap − SPY gap ≤ −K.
  - Liquid (ADV ≥ $95M), price ≥ $5, |gap| < 15%, leveraged / inverse / vol ETPs excluded.
  - Entry E1 = 09:50; E2 = first bar 09:55–10:30 that is +0.25% above the open.
  - Control = the same rule on normal-gap sessions (|SPY gap| < 0.25%).
- **Mechanism:** index gap-ups are executed as beta rotation at the auction. Names that gap down against the index
  carry a flow-driven dislocation that should revert.

| Config | Sessions | n | Avg R | Day-t | TRAIN | VALID | w/o best day | Control ALL | Down / up close |
|---|---|---|---|---|---|---|---|---|---|
| G0.75-K2.0-E1 | 37 | 2,137 | −0.160 | −1.57 | −0.114 | −0.117 | −0.218 | −0.126 | +0.029 / −0.467 |
| G0.75-K2.0-E2 | 37 | 1,297 | −0.124 | −1.39 | −0.203 | −0.020 | −0.185 | −0.098 | −0.040 / −0.320 |
| G0.75-K3.5-E1 | 37 | 754 | −0.158 | −1.12 | −0.183 | −0.018 | −0.270 | −0.163 | +0.052 / −0.492 |
| G0.75-K3.5-E2 | 37 | 451 | −0.074 | −0.52 | −0.285 | +0.184 | −0.179 | −0.108 | +0.069 / −0.351 |
| G1.0-K2.0-E1 | 19 | 1,278 | −0.114 | −0.85 | −0.121 | +0.087 | −0.209 | −0.126 | +0.040 / −0.423 |
| G1.0-K2.0-E2 | 19 | 813 | −0.062 | −0.52 | −0.214 | +0.187 | −0.154 | −0.098 | +0.002 / −0.274 |
| G1.0-K3.5-E1 | 19 | 520 | −0.020 | −0.11 | −0.087 | +0.327 | −0.164 | −0.163 | +0.220 / −0.416 |
| G1.0-K3.5-E2 | 19 | 332 | +0.050 | +0.30 | −0.182 | +0.415 | −0.068 | −0.108 | +0.272 / −0.272 |

- **What it shows:**
  - The trigger is common enough (37 sessions at +0.75%, 19 at +1%).
  - The counter-gap names do **not** revert reliably. 7 of 8 configs are positive on sessions where SPY then sold
    off from its open, and every config loses 0.27–0.49R on sessions that kept going up.
  - TRAIN is negative in all 8 configs. VALID is positive in 5 of 8.
  - No config is positive without its best day.
  - Best config: G1.0-K3.5-E2, +0.050R, t 0.30. It is a VALID-only pocket, so not a near miss.
  - 11-23 itself (CL / CHD / CLH) was a gap-up that faded from the open, the kind of session where this works. It is
    in-sample and not counted.
- **Parked**, configs_tried 8. The useful next step is the parent nightly-1123-index-gap-residual-gap (a family remedy
  for gap-up longs). It still needs the live setups' masks (bench10 conventions) and per-setup improve / worse counts.
  It is not run tonight (usage).

## 5 Decision
None. Nothing passed, so there is no Testing candidate tonight.

Educational only — not financial advice.
