# BDI daily 2026-11-25 (Wednesday): CAPTURE / COVERAGE

*Educational only — not financial advice. Live figures are **paper** results; the lab covers 2 years (22 open months
2024-10..2026-11). **Configurations tried tonight: 3** (swing1125-L19 arm A K 10 = 1; VRL-1125 A / B = 2). The locked
block 2024-11-01..2025-02-28 was not read. Scratch under scratchpad/s1125 (deleted after). Thu 11-26 closed; next
session Fri 11-27, half day to 13:00 ET.*

**Rule changes in the window (ledger).** Nothing effective 11-24 or 11-25; next 11-27 GYH V1+V3 (Graveyard only). Earlier
in the 10-06..11-24 day-type window: 10-28 Primary sizing, 10-29 −2R latch, 11-12 LR8 costs, 11-16 ROT1, 11-17 TSZ1,
11-19 C3 Epoch 1, 11-20 stop rounding / FOOTRACE-EXIT, 11-21 cost-basis fix, 11-23 ST7 out of Primary, BRAKE-BURST,
PSHADOW. Account per-day averages below mix these.

**Market: a V-day.** SPY low −0.90% from the open at 09:44, back near flat at 10:00, −0.6% at 11:40, then +0.7% by
12:20 and **+2.0% at the close** (high +2.24% 14:31); QQQ +2.87%, IWM +2.04%. An **up** day by the ±0.25% rule.

## 0a Move Hunt (research/bdi/moves/moves_1125_out.txt; moves.csv +100 rows; precursors_1125_out.txt)
moves.py unchanged, all 10 accounts (2,778 trades on 876 symbols), 1,283 liquid names, top 25 per side.

| Set | 11-25 | 11-24 |
|---|---|---|
| All movers | **2/50 = 4%, +0.07R** | 2/50 = 4%, +0.62R |
| Tradable (blackout removed) | **2/50 = 4%, +0.07R** | 3/50 = 6%, +1.10R |

- **Catches (both long):** FCFS and STRC, both by Testing F's `CWT14-failbrk-pdl-p10-lowvol-long-WB3` (+0.06R, +0.01R).
  Short side 0 of 25.
- **The moves were small** (top long 1.66 ATR, WDAY, blackout): a broad index day, few stock-specific moves.
- **What was known at the decision point:** **12 of the 25 short movers were inverse / long-vol ETPs decided at 11:50**
  (UVIX, VXX, UVXY, VIXY, SPXS, TZA, SDS, SH, SDOW, SPXU, DOG, RWM; SPY −0.60% from its open then): the squeeze. The book
  was on the wrong side of 9 of them (16 longs, −16.88R). Long movers were gap-down names below their open / VWAP decided
  09:35–09:55 (sector: CRH, VMC, AWI building materials; GD, CHDN) or 11:35–11:55 just before the squeeze (CWB, CG, H, ZBRA,
  MMM, SPY −0.45..−0.66%). Precursor scan (K 1.0 ATR): long movers came from fromOpen q1 (lift 2.5×), far from the HOD
  (q5 3.1×), near the prior-day low (2.5×), below VWAP — the gap-down short family's names. That is the lead (0b).
- **Miss reasons (all set):** wrong side only 12, traded outside the move 10, no setup signalled 10, blackout 9, skipped 7
  (spread 5, burst brake 2 incl. META/ZBRA/BAM in tradable, missed trigger 1). Wrong-direction trades 19, **−20.41R**.

## 0b Swing autopsy: Primary (research/bdi/1125/swings.py → swings_out.txt, timeline_p.csv; method unchanged)
- **Close:** **−42.30R after costs**, Alpaca −$2,853.75, 41 shorts (2 wins). Realised peak +0.76R (11:10).
  **Mark (1-min, no costs while open): peak +6.06R at 11:38, trough −42.43R at 13:20.**

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific |
|---|---|---|---|---|---|
| 09:50 → 11:38 (build-up) | +6.06 | +3.89 | +1.04 | −1.75 | +2.88 |
| **11:38 → 13:20 (the swing)** | **−48.49** | **−34.91** | −2.08 | +0.18 | −11.67 |
| 13:20 → close | +0.13 | −0.19 | 0.00 | 0.00 | +0.32 |

- **Timeline (5-min, timeline_p.csv):** 11:39 open +4.32R, 30 shorts / 0 longs, net beta **−19.6R per +1% SPY**, SPY
  −0.53%; 11:59 −10.62R (SPY −0.14%); 12:09 −27.11R (SPY +0.55%, 25 shorts); 12:19 −33.03R (SPY +0.95%); 12:59 −40.72R
  (SPY +1.18%, 3 shorts). L3 latch 12:02, −20R halt 12:07; flat from 13:20.
- **Top 5 names in the swing (−18.91R), all `L3-gap-slope-fromopen-FD`:** AADX −4.26R, LBRT −3.78R, AXON −3.77R, INIO
  −3.76R, RUN −3.35R. By setup: L3 −41.58R, RW3 −5.63R, RW5 −1.27R. Entries inside the swing: 7 shorts, final avg −1.09R.
- **Cause:** **market direction** — 72% of the swing (−34.9R of −48.5R) is index beta on a 30-short, zero-long book
  built 11:15–11:40 while SPY sat ~0.6% below its open; the stock-specific part (−11.7R) is the squeeze in the most-shorted
  names on top. Swing type **swing-midday-flip** (2nd instance; 11-10 first).
- **What turned it:** nothing in Primary (no long setup); the latch + halt stopped new entries and the book ran out of
  lots by 13:20. Across accounts the recovery came from longs that bought the V (A GEN-261023-07 +90.8R, GY GEN-261022-01
  +81.0R, D GEN-261027-10 +57.7R; nightly).
- **Lead swing1125-L19 (pre-registered, merges backlog nightly-1125-squeeze-stopcluster-flip-long arm A, 1 config):**
  family stop cluster (≥ 10 distinct symbols stopped in 10 min, 10:30–14:30) → buy each name stopped from then to 14:30
  at its stop minute's close, 1R = the short's stop distance, hold to 15:55. **Lab FAIL** (l19_lab.py → l19_lab_out.txt;
  bench10 family replay, 82,809 lots / 446 sessions, LR8): 85 trigger days, 4,410 longs, **−0.120R after costs** (gross
  −0.065R), day t −1.11, w/o best day −0.190R, fit −0.083 / check −0.147; up sessions +0.215R, down −0.531R; worse than
  the day-matched control (not-stopped family names bought at T, +0.049R) by −0.187R per trigger day (t −2.82). The stopped
  names do not keep running on average; it is a bet on the rest of the day's index direction. **Live 11-25 (in-sample):**
  T 12:02, 281 shadow longs **+0.644R** after costs (+181R; 12:xx +1.41R, 13:xx +0.29R, 14:xx −0.25R) — an up day.
  Forward shadow logged for the record (l19_live.py; forward.csv L19), no pass expected.
- **Forward tallies:** L15 EOD-loser cover: no short lots in −2% losers at 15:30 (up day), 0 lots. fwd_swings: L1 no NS5
  longs; L2 no trigger; L3 not qualifying (SPY +0.05%, IWM −0.16% at 10:00); **L6** counter-index entries n 1,591 −0.551R
  vs others n 1,187 −0.295R (−0.256, with L6's sign; running 13 sessions −0.300, t −1.93). L13 LATCH-CLOSE not re-tallied.
- **Lead count:** 33 rows in hypotheses.jsonl (17 swing L-leads), 1 added (L19, failed). Best forward lead still **L13**
  (LATCH-CLOSE; +302.7R over 7 sessions to 11-20, `1 day` 69%).

## 0 Per-account lines (11-25; research/bdi/1125/acct.py → acct_out.txt)
R = journal R after costs; $ = Alpaca day P/L (nightly). Peak = realised running peak (exit order). Day-type columns = avg
R per traded session 10-06..11-24 by SPY open→close (up / quiet / down; sessions). Today is an **up** day (all R below is
up-day R).

| Account | $ | Trades | Avg R | Total R (L / S) | Peak (time) | Best setup | Worst setup | Up / Quiet / Down per day |
|---|---|---|---|---|---|---|---|---|
| Primary | −$2,854 | 41 | −1.032 | −42.30 (0 / −42.30) | +0.76 (11:10) | RW5-…-gapdn-short-FD −1.17 (1) | L3-gap-slope-fromopen-FD −34.97 (35) | −9.18 (11) / −4.70 (12) / +4.74 (13) |
| On Deck | −$6,183 | 545 | −0.717 | −390.81 (+3.08 / −393.89) | +1.08 (11:14) | NM-HL-T75-pm-long +2.12 (4) | L3-gap-slope-rsi5hi-FD −219.08 (311) | −20.84 / −15.74 / −10.58 |
| Testing A | −$1,299 | 272 | −0.495 | −134.77 (+58.33 / −193.10) | −1.21 (10:05) | GEN-261023-07 long +90.84 (48) | L3-fromopen-FD-WB4 −149.57 (140) | −21.02 / −15.21 / −31.77 |
| Testing B | −$1,895 | 258 | −0.713 | −184.05 (−16.99 / −167.06) | −1.14 (10:06) | IDX1-qqq100-0955-TQQQ-hold +8.40 (1) | L3-rsi5hi-FD-WB4 −135.96 (193) | +2.75 / +2.40 / +3.19 |
| Testing C | −$1,900 | 237 | −0.789 | −186.92 (+3.07 / −189.98) | +3.24 (11:43) | IDX1-qqq100-0955-TQQQ-trail +1.40 (1) | L3-rsi5hi-FD-WB5 −170.92 (182) | +1.56 / −1.17 / −19.38 |
| Testing D | +$272 | 235 | +0.059 | +13.90 (+46.49 / −32.59) | +14.85 (15:57) | GEN-261027-10 long +57.70 (98) | NM-RWR1-exh150-gapdn-spyup-pm-short −31.52 (60) | −8.13 / — / −3.37 |
| Testing E | −$650 | 180 | −0.257 | −46.30 (−22.98 / −23.32) | +1.90 (10:10) | IDX5-spy050-0945-3x-trail +1.68 (1) | ULT-05-withgap-cont-short −21.39 (46) | −28.02 / — / −1.64 |
| Testing F | −$2,475 | 404 | −0.647 | −261.38 (+14.13 / −275.51) | +5.67 (10:52) | CWT14-failbrk-pdl-p10-lowvol-long-WB3 +12.43 (63) | L3-lowdist-FD-WB4 −123.85 (194) | −27.86 / — / +1.25 |
| Gen | +$764 | 106 | +0.285 | +30.23 (+47.22 / −16.99) | +30.51 (15:55) | GEN-261019-04 long +29.07 (30) | GEN-261021-04 short −16.26 (19) | −31.38 / −24.40 / −28.85 |
| Graveyard | +$514 | 500 | −0.049 | −24.37 (+124.08 / −148.44) | −1.18 (09:59) | GEN-261022-01 long +80.97 (35) | exhaustion_short-FD −38.82 (41) | −43.09 / −25.12 / −84.03 |

- **COVERAGE gap, again:** Primary now averages −9.18R per up day (11 sessions, 10-06..11-24) and added its worst day.
- **Today's win:** the protections and the V-buyers. Primary's L3 latch + −20R halt blocked what-if −364.7R, the GY latch
  −431.8R (nightly 6c); longs made +256.4R across accounts (850 trades) while shorts lost −1,483R; the V-buyers led (A GEN-261023-07 +90.8R, GY GEN-261022-01
  +81.0R, D GEN-261027-10 +57.7R — all `1 day` records). The L19 shadow +181R is in-sample on an up day only.

## 1 Patterns (research/bdi/patterns.csv +1,694 loser rows; research/bdi/1125/patterns.py → patterns_out.txt)
Accounts Primary, On Deck, Testing A–F (2,172 trades). Classifier unchanged.
- **Wrong side after a big swing −560.0R (650)** leads (On Deck −153.9, F −120.9, A −105.3, Primary −20.0): the
  squeeze. Never worked −412.9R (406); small MFE then failed −282.9R (283); late hold −124.8R (191).
- Primary: wrong side after big swing −20.0R, never worked −11.1R, small-MFE −6.9R, near-target-then-stopped −4.6R.
- **Stacking hurt today:** lot 2+ 308 trades −0.706R vs lot 1 −0.545R (11-24: −0.140 vs −0.154). Primary 17 re-entry
  lots (LBRT 5; nightly).
- Inverse / long-vol ETP longs (VIX, SPY, IWM, GDX inverse) lost in every account (−1 to −5R each) — the 11:50 short movers.

## 2 Recurring patterns → rules
- Midday-flip on a crowded short book (11-10, 11-25): the live remedies are LATCH-OPEN / HS-SCALE (with the owner) and
  the IDX3-P / compass shadows (nightly); not re-tested here (guarded: day-type switch / hedge category). The long-side
  flip (L19) and the laggard version (VRL) both fail in the lab: after a V signal the edge is the index direction, not
  the names.

## 3–4 Tested idea: VRL-1125 V-Reclaim Laggard Long (COVERAGE) — FAIL (configs 2; research/bdi/1125/vrl_lab.py)
Pre-declared: SPY dips ≥ 0.5% from its open, first 5-min bar 10:30–13:30 back at/above the open → buy liquid names
(ADV20 ≥ $95M) ≤ −0.5 ATR (A) / ≤ −1.0 ATR (B) below their own open and below VWAP; stop 0.5 daily ATR, hold to 15:55;
LR8 costs; control = every liquid name at the same bar. History2y 5-min frames (5-min exits).
- 21 trigger sessions. **A** n 1,316 **+0.036R**, day t 0.30, w/o best day −0.042R (best day 205% of total), fit +0.018 /
  check +0.051, up +0.283 / down −0.288R, 5/11 positive months, minus control −0.005R per day. **B** n 311 −0.113R.
  Control +0.088R (t 1.30). **0 of 2 pass** (BAR90 t ≥ 1.35): the laggards do no better than the index after the reclaim.
  Same lesson as bdi1027-index-reclaim-leaders-long (leaders) and L19 (stopped names). Backlog `bdi1125-vrl-v-reclaim-laggard-long`, parked.
- research/queue.jsonl: the open items (LEASH-SHADOW, compass, ROTA1, RISK1 …) are run by the nightly / consultant
  routines; none taken here.

## 5 Decision
None. Nothing passed; no Testing suggestion.

Educational only — not financial advice.
