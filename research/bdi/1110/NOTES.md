# BDI 2026-11-10 (Tuesday): V-day with a tech-out rotation, then a midday flip-up — Move Hunt day 9 (capture 16 %), all-account swing autopsy, MFX1 flip exit pre-registered and tested (fails), latch-counting check (no bug)

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in). R = journal
`pnl_adj / $ risk`; $ = Alpaca `day_pl` on the data branches. Two-year tests use the lab cache (bt_lab1104 lists + burst1
5-minute marks, to 11-04). **Locked block 2024-11-01..2025-02-28 never read (asserted).** **1 configuration tried tonight
(MFX1), pre-registered and committed before its two-year read (MFX1_PLAN.md, commit c25f74282), reported in full; 0 pass.**
No config, setup, exit, ledger or docs/live file changed.*

Built on, not redone: nightly1110 (close / coverage / hand-over, autopsy, latch-open-lot and midday-flip patterns → backlog
`nightly-1110-latch-closes-open-lots` / `nightly-1110-midday-flip-open-book-exit`, latch / BRAKE-1 / REG2 / LEASH shadows,
DECISION RW3S-GY) and the Team final (−12.31R / +$352, de7a134b6). Their numbers are quoted, not recomputed. The 18:33 ET
Primary decision (TEAM-6 vs PV) is not pre-empted; the Primary block below is factual input only.

**Day type: UP (barely), above at 10:00.** SPY open-to-close **+0.27 %** (SIP; +0.32 % on the coverage bars), at 10:00
**+0.37 %**; high +0.61 % 10:07, low −0.33 % 12:45. QQQ +1.21 % 10:01 → −0.60 % 12:45 → +0.52 %. Live compass: W60
UP-confirmed 10:00–10:30, leaning down 10:45, **DOWN-confirmed 11:30–14:00**, mixed 14:15–14:45, leaning up 15:00,
UP-confirmed 15:30 (compass/2026-11-10.csv). **Sector tape 10:55→12:45: XLK −1.12 %, SMH −0.84 % while XLP +0.71 %,
XLU +0.73 %, XLV +0.47 %, XLF +0.52 %, IWM +0.29 %** (a tech-out rotation that pulled SPY down while most stocks rose);
12:45→15:51 XLK +1.68 %, SPY +0.81 %.

**Rule changes inside the windows quoted** (research/ledger.jsonl): **EXPO1109 temporary moves in effect 11-09 / 11-10**
(GEN-261021-02 / GEN-261019-03 / GEN-261026-02 Gen → Testing 1, GEN-261022-07 / GEN-261026-03 Gen → Testing 2; reverted from
11-11, PR #173), so Testing totals include GEN results today (T1 GEN-261021-02 33 longs −11.8R). No Primary rule change
11-10. Earlier in the live day-type / record windows: 11-05 ROLL1, 11-04 UNI1 + DM-N3, 11-03 RW3S → T2 / MF3-FD, MF5-FD →
GY, 10-30 Testing cost filter + L3 pair, 10-29 Primary −2R latch + BAR90, 10-28 Primary ~$4k lot, 10-26 ST7-FD, 10-22 ST-A
(latch off in T1 / T2 / Gen), 10-20 MF2-FD / MF4-FD promoted. Two-year results are rule-fixed.

## Today's win
**Graveyard +67.90R / +$1,716 (Alpaca)** — the failed-opening-range-low-break longs `CWT14-failbrk-orl-*-long` (+69.4R on
233; p05-lowvol +30.9R, p05 +23.1R, p10-lowvol +15.4R) bought the 10:10-10:57 and 11:17-close dips and caught 5 of the
day's 8 captured big moves (DE, SNDQ, NVD, JKHY + CMCSA / SM by CWT14-pdl). In Primary, Gap-Down Recovery Fade
`L3-gap-slope-fromopen-FD` +6.26R / +$852.78 (the whole +9.1R morning leg). Live Lab +2.46R, Explore 1 +2.16R.
Research win: tonight's swing lead (MFX1, the open-book exit at the midday flip) went from idea to pre-registered two-year
answer in one session — it **fails on VALID** for a clear, measurable reason (false flips cost −794R vs +714R earned on
true flips), which names the next version (MFX2, magnitude-conditioned) — and the Team-flagged latch question is
answered (below: no bug; the "−3R by 11:30" read was not realized R).
**One-big-day caveat:** every GY CWT14-orl winner is **negative without today** (p05-lowvol 581 trades −0.050R, −0.121R
w/o today; p05 −0.079 / −0.130; p10-lowvol −0.040 / −0.087); L3-fromopen-FD (Primary) 63 trades −0.020R, −0.168R w/o today.

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-10; research/bdi/moves/moves_1110_out.txt, precursors_1110_out.txt)
Inputs rebuilt: priors + SIP 1-min bars for 1,694 universe names, 5-min bars 09-22..11-10, 11-10 lab frames; 1,291 liquid
names, 85,018 decision rows, 1,294 live trades (608 symbols), 7 accounts.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 5 / 50 (10 %) | +4.33 | 4, −4.35R | earnings blackout 29 (15 on the event day) |
| **tradable (blackout removed)** | **8 / 50 (16 %)**: long 6 / 25, short 2 / 25 | **+6.51** | 17, −7.14R | traded outside the move 17, no setup 10, wrong side only 8, skipped 7 |

**Capture rate 16 % vs 22 % on 11-09 (R +6.51 vs +9.69)**; hunt so far 10-29 26 %, 10-30 6 %, 11-02 22 %, 11-03 12 %,
11-04 20 %, 11-05 2 %, 11-06 26 %, 11-09 22 %, 11-10 16 %. Catches: GY CWT14-orl / pdl longs (DE, SNDQ, NVD, JKHY, SM,
CMCSA; +5.96R with T1 / T2 / LL / Gen co-catches), shorts P MF4-FD (UPST +0.46R) and Gen GEN-261026-01 (ALV +0.09R).
What was known at the decision point:
- **Longs = energy at the open.** 13 of the 25 tradable long moves were energy / gas names decided at 09:35 (FANG, CRGY,
  DTM, OVV, AR, NUE, KMI, EXE, XOP, EQT, SM, STLD + UNG 11:00) and ran ~35 min (to ~10:10) with almost no heat; XLE was
  +1.22 % by 10:55. Misses: "traded outside the move" (setups started at 09:50+, after the run) and "no setup".
- **Shorts = crypto ETFs 10:10→11:37** (GBTC, IBIT, BITO, FBTC, ETHA: 5 of 25) — the book was **long** them (wrong side
  only, 4 names) — and MSFT / MSFU 12:20→12:46 (the tech leg of the rotation). OMH +153 % / −55 % is a data or corporate
  event, not a tradable move (skipped: price through stop / not shortable).
- **Precursor scan** (K 0.5 ATR): vol_exp (5-min ATR / daily ATR, "in play") is again the top feature (short q5 3.6× the
  base rate) — the 4th day running; MH1109-P1 already showed it predicts size, not direction (parked). Time of day (first
  hour) is the other recurring one: the big moves of 11-09 and 11-10 both started before 09:50.
- No new precursor test tonight (the day's lead went to the swing exit). Next Move Hunt step stays the *open-window*
  catalogue (09:30-09:50 decisions) — 2 days running the long side was decided at 09:35.

## 0b. Swing autopsy, every account (swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = 1109 (1-min marked R per lot; each leg = market (beta × SPY) + setup-day mismatch (sector-ETF residual) + bad
entries (fill + first 5 min) + stock-specific (rest, incl. exits and costs); parts sum exactly, asserted; top 5 names =
cross-cut of the same leg). Betas 5-min 09-22..11-09. Primary decomposed at its R peak, SPY's low, its R trough and the close.

**Primary** (99 lots, 93 short / 6 long): R peak **+9.14R 10:55**, trough −34.45R 15:51, close **−31.25R**; journal $
+1,089 (10:56) → −163; Alpaca −$109.40.

| ET | open R | realized R | total R | SPY | QQQ | longs / shorts | net beta (R per +1 % SPY) |
|---|---|---|---|---|---|---|---|
| 10:04 | +0.19 | 0.00 | +0.19 | +0.56 % | +1.29 % | 0 / 1 | −1.4 |
| 10:49 | +3.83 | +3.59 | +7.42 | −0.03 % | +0.31 % | 1 / 8 | −10.4 |
| 11:49 | −2.99 | +6.56 | +3.57 | −0.14 % | −0.09 % | 5 / 22 | −12.8 |
| 12:34 | −14.29 | +5.83 | −8.46 | −0.09 % | −0.19 % | 2 / 40 | −27.8 |
| 12:49 | −14.83 | +5.83 | −9.00 | −0.23 % | −0.41 % | 2 / 46 | −31.2 |
| 13:34 | −16.60 | +0.29 | −16.30 | −0.06 % | −0.13 % | 2 / 50 | −43.5 |
| 14:34 | −17.96 | −8.32 | −26.28 | +0.19 % | +0.17 % | 2 / 48 | −42.1 |
| 15:19 | −13.51 | −12.30 | −25.80 | +0.21 % | +0.26 % | 2 / 48 | −38.6 |
| 15:49 | −11.54 | −19.22 | −30.75 | +0.36 % | +0.49 % | 2 / 40 | −32.1 |

| leg (ET) | R | $ | SPY | market | mismatch | bad entries | stock | top 5 names (display name, code) | what turned it |
|---|---|---|---|---|---|---|---|---|---|
| 09:50→10:55 | **+9.14** | +1,103 | +0.06→−0.14 % | +4.56 | +2.32 | +1.29 | +0.97 | SOXL, ALAB, PTEN, MRVL (Gap-Down Recovery Fade `L3-gap-slope-fromopen-FD`), SMCI (Early Sellers, Mid-High RSI `MF2-open-rsimidhi-flowsell-FD`) +7.57R | L3 shorts of gap-down semis / AI names as QQQ gave back +1.2 % |
| **10:55→12:45** | **−16.68** | −431 | −0.14→−0.33 % | **+6.59** | **−12.96** | −4.07 | −6.25 | ERY (Big-Dip SMA50 Flush Buy `NS5-sma50-flush-oversold-long`), S (MF2-FD), BMNR, MRSH (Early Sellers, Strong Heat `MF4-h40-open-flowsell-FD`), BG (Gap-Down Pop Fade, Heat `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`) −6.62R; by setup RW5-FD −6.24, Gap-Down Heavy Selling `RW3-gapdn-rsi5pop-flowsell-short-FD` −4.65, MF4-FD −2.32 | **sector rotation, not the index:** SPY fell, but the money left tech for staples / utilities / health / financials, and 52 new shorts (RW3 / RW5 burst 12:00-12:35 in YUM, PFE, NVS, UL, EQIX, AEP, CNP, DG, LLY…) were in the sectors that rose |
| **12:45→15:51** | **−26.91** | −959 | −0.33→+0.36 % | **−30.21** | +10.22 | −0.93 | −5.99 | COPX (MF2-FD), NDAQ (MF4-FD, RW5-FD, RW3-FD: one name, three setups), ARVN (Gap-Down Recovery Fade, RSI5-high `L3-gap-slope-rsi5hi-FD`) −7.38R; by setup RW5-FD −7.45, MF2-FD −7.36, MF4-FD −4.54, RW3-FD −4.20 | **SPY back over its open (flip confirmed 14:31; XLK +1.68 %)** with 45-50 shorts open, net beta −30..−45R per +1 %; 11 straight stop-outs 13:24-13:58 |
| 15:51→close | +3.20 | +124 | | +2.76 | −0.22 | 0.00 | +0.67 | flatten at 15:55 | the last-minute SPY dip |

**Split of the −43.60R peak-to-trough swing: market −23.62 + setup-day mismatch −2.74 + bad entries −5.00 + stock-specific
−12.24 (sum −43.60)** — and inside it two different causes: the 10:55→12:45 leg was **rotation** (market +6.6R *for* the
short book, mismatch −13.0R against it), the 12:45→15:51 leg was **the flip** (market −30.2R). New shorts kept coming in
both legs (80 shorts after 10:55, final avg −0.490R). **What turned it:** the up-turn in SPY at 12:45 (QQQ low −0.60 %),
SPY back above its open from ~13:55 and for good from 14:16 (flip 14:31); per-setup −2R latches fired 13:04 (RW3), 13:31
(RW5), 13:57 (MF2), 15:28 (MF4) — they stopped new lots, but 43 open lots lost another −22.46R (nightly). Nothing drove a
recovery (2 longs open).

**Testing 1** (127 lots, 76 short): −44.92R / Alpaca −$497.63; peak +0.79R 09:59 → trough −50.66R 15:51. 09:59→close
−45.71R = market −38.97 + mismatch +4.31 + bad entries −10.30 + stock −0.75: Gap-Down Bounce Early Short
`RW7-gapdn-bounce-early-short-FD` −28.66R (57 shorts; T1 has no latch, 45 entries after it would have hit −4R open+closed
at 12:35 = −25.4R) and the EXPO1109-moved `GEN-261021-02-…-OPEN-SPYgt0p5-t1s1-long` −11.80R (33 longs 10:05-10:10, 20 stops).
**Testing 2** (147 lots, 84 short): −27.11R / −$324.73; 10:22→12:40 **+18.73R** (market +12.44, mismatch +6.03:
Gap-Down Heavy-Selling Short, no RSI condition `RW3S-gapdn-flowsell-short-FD` +17.55R — shorts of TEM, DECK, RBRK, ORCL,
IGV, i.e. *tech*, the right side of the rotation), then 12:40→15:59 **−39.44R** (market −33.82, net beta −42.7R / 1 %:
RW3S-FD −35.38R in QLD, SPXL, TQQQ, COIN, AMD — the flip). Same cause as Primary's second leg, opposite sign in the first.
**Graveyard** (629 lots, 432 long): +67.90R / +$1,716.24; trough −15.29R 10:10 → +59.85R by 10:57 (mismatch +32.99,
stock +28.85: CWT14-orl longs + CWT14-pdh shorts), 10:57→11:17 −28.75R, 11:17→close +52.09R (mismatch +55.29, market
+13.77, net beta +72.7R / 1 % by 15:00: CWT14-orl longs +62.7R, CWT12 coil +9.6R) — long book on the rising sectors.
**Gen** (280 lots): −59.88R / −$957.84; 09:50→12:41 **−114.15R** (stock −41.14, mismatch −26.90, market −24.46, bad entries
−21.64: Generated BB-High ORB-Fail Short `GEN-261020-10-…-hold-short` −45.93R — 48 shorts 10:45-10:50, 41 stops; ORB-fail
Up long `GEN-261022-01-…-SPYdn-hold-long` −36.83R), then 12:41→close +54.26R (market +31.27, net beta +65.3R / 1 %: the
same GEN-261022-01 longs +26.0R, GEN-261027-06 +19.0R, GEN-261019-04 +17.2R) — the flip carried Gen's long book.
**Explore 1** (+2.16R / +$10.25) and **Live Lab** (+2.46R / +$53.18): ranges 3.4R / 2.7R, no swing worth decomposing; Ex1
Volume-Spike-Down PM long `ST8-volspikedn-long-pm-t1s1-FD` +2.0R 15:03→close; LL Flush Buy `CWT05-flush-m075-v3-long`
MSFT / MSFU +1.9R, Bull Flag `CWT12-flag-s1-long` CLX +1.1R, Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` SOXL +0.5R.

**Cross-account cause (one line):** a tech-out rotation (10:55-12:45) the short books sold into the wrong sectors, then a
midday flip-up (SPY back over its open 14:31) that took 45-85 open shorts per account with it; the long books (GY CWT14-orl,
Gen's afternoon longs) made the day's money.

### MFX1 — midday-flip open-book exit (pre-registered MFX1_PLAN.md, ONE config; mfx1.py → mfx1_out.txt)
Rule: morning side M = SPY's side of its open at 11:59; flip F = 15 consecutive 1-min SPY closes on the other side
(12:00-15:29); at F close every open trade on side M at the last 5-min close ≤ F, minus 1 bp + $0.01 / share. Entries after
F untouched. 2 years, every lab setup (86 with affected trades), costs in, locked block excluded; lineage N 34 (33 compass-learn
FLIP configs + 1): bar 2.66, BAR90 2.39. 107 flip days of 457 (23 %), median flip 13:10, **44 false** (SPY closed back on the
morning side).

| split | affected trades / flip days | actual → at flip (avg R) | delta | day-t | days better | w/o best day |
|---|---|---|---|---|---|---|
| TRAIN (2024-10, 2025-03..12) | 12,196 / 59 | −0.433 → −0.306 | **+1,555.9R** | 2.92 | 71 % | +1,242.5R |
| **VALID (2026-01..10-05)** | 10,162 / 36 | −0.248 → −0.256 | **−79.8R** | **−0.17** | 64 % | −209.7R |
| LATE (10-06..11-04) | 1,097 / 5 | −0.363 → −0.179 | +202.4R | 2.60 | 80 % | +111.8R |

**FAIL** (VALID t −0.17 < 2.66 / 2.39; w/o best day negative; families 4 better / 5 worse). **Why: VALID true flips
+713.7R, false flips −793.6R** (TRAIN false flips only −47.2R). Remedies rule, VALID families (≥ 30 affected): better MF
+31.1R, CWT +28.2R, ST +12.8R, NM +4.4R; worse NS −67.3R, GEN −42.2R, exhaustion −22.9R, L −15.8R, RW −8.2R; setups 22
better / 24 worse (worst RW4-ns3-adv150-short-FD −46.6R, NS3-failed-vwap-reclaim-short-FD −44.1R; best CWT14-pdl-p05-long
+42.8R, RW3S-FD +35.2R). **QDAY:** VALID down-close days −139.1R, quiet −17.6R, up +76.9R; SPY above its open at 10:00
−148.8R / below +69.0R; shorts −176.8R / longs +97.0R. **Live 11-10 (in-sample, flip 14:31):** P 50 lots −23.97R → −19.28R
(**+4.69R**, 5 setups better / 1 worse), T1 +16.15R, T2 +23.71R, GY +10.37R, Gen +1.36R (+56.3R total). Reading: on a real
reversal the exit pays (TRAIN, LATE, today); the detector's 41 % false flips give it all back on VALID. → forward shadow
**swing1110-L12**; salvage idea **MFX2** (flip only once SPY is ≥ 0.15 % across its open; `mfx2-1110-flip-magnitude`, config 35
of the lineage, pre-register before running).

### Latch counting (Team-reconciliation flag; latch_count.py → latch_count_out.txt)
Question: live and the Team replay took RW3 / RW5 entries at 11:50 / 11:55 although the setups "appeared past −2R" (RW3 ~−3R
by 11:30). **Finding: no bug — the latch counts realized R by exit time, as designed, and RW3 / RW5 were nowhere near −2R
realized at those entries.**
- **Realized vs marked:** RW3 at 11:30 realized −0.19R (YUM stop 10:31 −1.03, CP target 11:24 +0.86), open lots marked
  −0.67R, total −0.86R; at 11:55 −0.19 / −1.48 / −1.67R; it crossed −2R *with* open marks only ~12:15 (−2.94R) and realized
  at 13:04 (AR stop, −2.17R) → latch 13:04, last RW3 entry 12:35. RW5: realized 0.00R at 11:55 (−1.48R with marks), latch
  13:31 (OMC stop). The Team replay agrees (RW3 realized −0.11R at 11:24, latch 12:57, last entry 12:35; RW5 latch 12:33,
  last entry 12:30). The "~−3R by 11:30" was a mark-to-market or wrong-time read; the open-loss version is what
  burst1/burst2 shadow (burst2-openloss-latch4: +20.72R tonight).
- **Close-time vs entry:** trades are added in exit order (reconcile), never at entry. ✓
- **Partial fills:** 0 duplicate broker order ids (Primary 9 sessions, GY 14). ✓ **Shared lots:** each lot belongs to one
  setup (AVLV / NDAQ / OMC stopped in RW3, RW5 and MF4 at once = three lots, each counted once in its own setup). ✓
- **Two small gaps (not bugs, recorded for after-hours, no change proposed):** (1) the latch sums the journal's gross
  `r_multiple`, not after-cost R: Primary MF4-FD crossed −2R after costs at 13:55 (−2.07R) but only −1.90R gross, so it took 3
  more entries (ANET, EVR, RBRK −0.86R) before latching at 15:28; since 10-29 that gap let 11 Primary entries through
  (−1.68R; mixed sign: 11-04 MF4 −2.31R, NS5 +1.15R, RW3 +0.34R). (2) one-poll lag: an entry in the same poll as the
  latching stop fill (RW5 SGOL 6 s after OMC's stop, −0.58R); since 10-29 12 such Primary entries +4.54R (11-05 MF2 burst
  +6.13R). Neither is material or one-signed → FYI, not a DECISION.

### Leads (research/bdi/swings/hypotheses.jsonl; 20 leads + 2 accumulating swing types)
- **New lead `swing1110-L12` (MFX1) — TESTABLE, pre-registered, two years failed → forward shadow** from 11-11 with the fixed
  bar: 15 flip sessions, total delta > 0 and > 0 on ≥ 60 % of them (P + T1 + T2 + GY pooled; Primary alone reported); then
  the MFX2 re-test before any DECISION (Testing trial, never Primary first). 11-10 in-sample +56.3R.
- **New accumulating swing type `swing-midday-flip`** (first instance 11-10: rotation leg + flip leg, P / T2 / Gen). The
  nightly's `nightly-1110-latch-closes-open-lots` is its setup-level version (not run tonight).
- **Forward tallies 11-10** (forward.csv; forward_1110_out.txt, fb1_live_out.txt, mh_p1_live_out.txt, l11_live_out.txt;
  nightly1110 forward_out / forward_gate1_out / openloss_out): L1 A 35 −0.243 vs B +0.118 (right sign); L2 no trigger (the
  rotation had no QQQ new high); L3 qualifying, family shorts 129 −0.394 (right sign); L6 counter 100 +0.328 vs −0.103 (wrong
  sign); L7 A 69 +0.250 vs B −0.269 (wrong); L8 A 16 −0.079 vs B +0.194 (right); gate1 +6.67R (P +9.06); burst1-latch3 P
  +11.29R / GY −2.45R; **burst2-openloss-latch4 day 2 +20.72R** (2-day +37.3R); **burst2-flush-gate-short day 2 +56.68R**
  (122 shorts blocked; Gen +44.0R; 2-day +57.6R); swing1106-L10 day 2 scalp − live +28.02R (2-day +31.4R); fb1 A −0.503 vs
  rest −0.284 (right sign); mh1106-p1 not qualifying; L9 not qualifying; **swing1109-L11 (ECG1) day 1 −14.10R** (blocked 9
  winning L3-fromopen shorts −7.82R and T2 RW3S −5.81R — the same L3 harm as on two years); comp15 W60 10:00 UP right at the
  close, DOWN-confirmed 11:30-14:00 wrong.
  **Best forward lead tonight: burst2-flush-gate-short (+56.7R day 2, +57.6R over 2 sessions), then burst2-openloss-latch4
  (+37.3R over 2).** Both far from their 15-20 session bars.

## 0. Per-account session review (accounts.py → accounts_out.txt / accounts.csv; bursts_out.txt; daytype_out.txt; onebig_out.txt)

| account | Alpaca $ | R | trades | win % vs break-even | avg R | peak → close (journal $) | best setup | worst setup | notable skips |
|---|---|---|---|---|---|---|---|---|---|
| Primary | −109.40 | **−31.25** | 99 | 31 % vs 55 % | −0.316 | +1,089 (10:56) → −163 | L3-fromopen-FD 18 +6.3R +$853 | RW5-FD 22 −12.5R | 366 / 465 (ETB 274, spread 32, latch 28) |
| Testing 1 | −497.63 | −44.92 | 127 | 28 % vs 54 % | −0.354 | +8 (10:00) → −484 | orb20_a 3 +3.3R | RW7-FD 57 −28.7R | 147 / 274 (split-tape gate 60, cost 39) |
| Testing 2 | −324.73 | −27.11 | 147 | 46 % vs 61 % | −0.184 | +247 (12:41) → −333 | CWT13-vwapstretch-z05-long 3 +1.4R | RW3S-FD 61 −17.9R | 115 / 262 (spread 46, cost 23) |
| Graveyard | +1,716.24 | **+67.90** | 629 | 72 % vs 63 % | +0.108 | +1,874 (15:39) → +1,639 | CWT14-orl-p05-lowvol 84 +30.9R | heat_fade_short-FD 18 −12.3R | 895 / 1,524 (max pos 189, ETB 172) |
| Gen | −957.84 | −59.88 | 280 | 43 % vs 57 % | −0.214 | +85 (11:09) → −1,086 | GEN-261027-06 22 +10.8R | GEN-261020-10 48 −43.0R | 548 / 828 (BP 146, max pos 135) |
| Explore 1 | +10.25 | +2.16 | 7 | 71 % vs 47 % | +0.309 | +20 (15:53) → +10 | CWT05-flush-m05-v5 2 +1.4R | LD1-ns1 1 −1.0R | 27 / 34 (ETB 18) |
| Live Lab | +53.18 | +2.46 | 5 | 100 % | +0.493 | +53 → +53 | CWT05-flush-m075-v3 3 +1.1R | — | 11 / 16 (ETB 10) |

**Give-back (peak → close, journal $):** Primary $1,252 (rotation shorts + the flip), Gen $1,171, T2 $579, T1 $492, GY $234.
**Bursts:** 108 setup bursts, 860 entries, −53.3R (avg −0.062R vs non-burst −0.086R); 9 with ≥ 75 % stops −91.0R (Gen
GEN-261020-10 48 shorts 10:45-10:50 −43.0R, 41 stops; T1 GEN-261021-02 33 longs 10:05-10:10 −11.8R; Gen GEN-261022-01 48
longs 10:50-10:52 −10.8R); good: Gen GEN-261027-06 17 longs 12:00-12:02 +11.3R, GY CWT14-orl 21 + 18 + 12 longs 10:15-10:25
+17.3R. **Stacking:** P 28 lots −13.3R (NDAQ / AVLV / OMC in RW3 + RW5 + MF4), GY 355 +64.1R, T2 41 −5.0R.
**One-big-day checks (own-account records):** Primary RW5-FD 122 trades +0.186R, **+0.032R w/o 10-22 (87 %, `1 day`)**;
RW3-FD 102 +0.304R, **+0.088R w/o 10-22 (78 %, `1 day`)**; MF2-FD 111 −0.009R, −0.343R w/o 10-22; MF4-FD 126 −0.360R, −0.407R;
L3-fromopen-FD 63 −0.020R, −0.168R w/o today. T1 RW7-FD 493 −0.004R, −0.036R w/o 11-05. T2 RW3S-FD 204 −0.281R, −0.291R
(→ nightly DECISION RW3S-GY). GY CWT14-orl-p05-lowvol 581 −0.050R / −0.121R w/o today; Gen GEN-261028-02 58 +0.081R,
−0.147R w/o today (`1 day`); GEN-261020-10 58 −0.480R. LL NM-ETF late dip 8 +0.408R, +0.360R w/o best (45 %, low rep).

**R by day type** (all live sessions, daytype_out.txt; window 12 quiet / 8 up / 6 down; **today = up (+0.27 %) / above at
10:00 (+0.37 %)**, so every account's whole day falls in "up"): Primary quiet −0.145 (388), **up −0.224 (457)**, down +0.224
(261); above 10:00 −0.060 / below −0.135. T1 −0.077 / −0.220 / −0.063; T2 −0.061 / −0.142 / −0.266; GY −0.064 / −0.060 /
−0.198; Gen −0.197 / −0.293 / −0.179; Ex1 +0.100 / +0.251 / −0.426; LL −0.061 / +0.483 / −0.076. Live setups positive on
both up and down days (≥ 10 each): 6 (T1 L3-fromopen +0.204 up / +0.198 down / +0.268 quiet, T1 MF4-FD +0.100 / +0.356 /
+0.345, T2 RW1-FD +0.163 / +0.383 / +0.069, GY CWT09-gapdn-vwaploss-g5-short +0.528 / +0.358 / −0.436, Gen GEN-261022-07
+0.180 / +0.620 / −0.375, T1 exhaustion_short +0.020 / +0.037 / −0.117). Up days remain the worst type for Primary, T1, Gen.

**Maximization edits (tested or queued; none live):**
- *Primary:* (1) MFX1 flip exit — **tested, fails** on VALID (false flips); today +4.69R in-sample → forward L12 + MFX2 idea.
  (2) Latch closes open lots (nightly backlog, +13.1R today in-sample) — queued, needs the 2-year build (same enriched lists
  as MFX1; next run). (3) Latch on after-cost R — FYI only (−1.68R over 9 sessions, mixed sign). TEAM-6 / PV: 18:33 task.
- *Testing 1:* RW7-FD −28.7R with no latch: burst2-openloss-latch4 shadow would have blocked 45 of its entries after 12:35
  (−25.4R) — evidence for that shadow, not a change (T1 runs latch-off by ST-A). EXPO1109 GEN moves reverted from 11-11.
- *Testing 2:* RW3S-FD swung +17.6R → −35.4R in one day; DECISION RW3S-GY (nightly) stands; MFX1 in-sample +23.7R here.
- *Graveyard:* CWT14-orl longs +69.4R but every variant negative without today — no candidate; short book −24.2R.
- *Gen:* GEN-261020-10 one 48-short burst −43.0R: the flush-gate shadow (block 3rd+ short in 15 min when QQQ 30-min ≤
  −0.4 %) would have saved +44.0R in Gen alone — the strongest forward evidence tonight.
- *Explore 1 / Live Lab:* ROLL1 rotation; no verdict (low rep).

## 1. Every-trade analysis (trades_bdi.py → per_trade_1110.csv, patterns_1110.csv → patterns.csv +574 loser rows; bursts.py)
- **Exit what-ifs** (1,294 trades, R after costs, 1-min SIP): live −0.070 / trade; orig −0.054; be05 −0.043; t05 −0.019;
  **t1 +0.061, trail +0.085, hold +0.092** (GY: hold +246R vs live +68R, its long book); sar −0.084; reent −0.040; opposite −0.083.
  Primary: every variant −25..−41R (hold −41.0R worst; MFE median 0.14-0.31R in the losing setups: nothing to manage). One session.
- **Opposite side, hindsight:** flag_spy (SPY ≥ |0.25 %| against the entry) 88 trades live +0.356R (opposite −0.545) — the
  counter-index entries won today (L6 wrong sign; flip day); flag_fo 440 live +0.107R. No rule known at entry picked losers.
- **Loss types** (losers, $): wrong_side_after_big_swing P 11 / −$529, Gen 18 / −$746; never_worked Gen 41 / −$844, GY 51 /
  −$863, P 13 / −$344; late_hold P 27 / −$416; small-MFE-then-failed Gen 47 / −$1,099, P 12 / −$366.
- **Stacking incl. leveraged / inverse by underlying:** P NDAQ, AVLV and OMC each stopped in three setups at once (RW3 + RW5 + MF4, ≈ −3R per name); T2 QLD / SPXL / TQQQ
  (RW3S) = one Nasdaq / S&P short −5.4R in the flip; MSFT + MSFU (LL / Ex1 longs) = one MSFT long.

## 2-3. Patterns → testable rules; NEW tested idea (pre-registered and committed before its two-year read)
| idea (source) | configs | result | QDAY split | verdict |
|---|---|---|---|---|
| **MFX1** midday-flip open-book exit (swing autopsy 11-10 + nightly pattern 2) | 1 | TRAIN +1,556R (t 2.92), **VALID −80R (t −0.17)**, LATE +202R (t 2.60); families 4 better / 5 worse; true flips +714R, false −794R (VALID) | VALID down −139R / quiet −18R / up +77R; above 10:00 −149R / below +69R | fail → forward L12; MFX2 idea |

**QDAY reading:** an exit keyed to the index flip is a both-direction rule by construction (it works for long books on
down-flips and short books on up-flips: VALID longs +97R, shorts −177R), but it is still a market-state bet — it pays only
when the flip is real, and quiet days (where SPY wiggles across its open) are where the false flips live. Nothing passed
the light lane → **no Live Lab candidate tonight.** Exhausted families (pdl1030*, rdt1030, saturday1031, night1102) not
repeated.

## 4. Swarm / configs counted
Configs tonight: MFX1 ×1 (flip lineage N 34 → 2.66 / BAR90 2.39). 0 pass. Failures reported in full. Locked block never
read. Backlog +2 (`mfx1-1110-midday-flip-open-book-exit` parked, `mfx2-1110-flip-magnitude` idea; add_backlog.py; BACKLOG.md
regenerated). No research/queue.jsonl item run (the swing lead took the slot).

## 5. Decision
None new. Nothing passed; no setup moves. FYI: latch counting verified (no bug; two small definitional gaps, no change
proposed). Facts for the 18:33 Primary decision: RW3-FD / RW5-FD records are carried by 10-22 (78 % / 87 % of their R;
+0.088R / +0.032R without it), MF2-FD −0.343R and MF4-FD −0.407R without their best day, L3-fromopen-FD −0.168R without today.

Files: accounts.py, swings.py, trades_bdi.py, bursts.py, daytype.py, forward_1110.py, fb1_live.py, mh_p1_live.py,
l11_live.py, mfx1.py (+ MFX1_PLAN.md), latch_count.py, onebig.py, hyp_update.py, add_backlog.py (+ outputs);
research/bdi/moves/moves_1110_out.txt, precursors_1110_out.txt; nightly1110 forward_gate1_out.txt / openloss_out.txt (its own
scripts, run tonight). Scratch inputs under the session scratchpad `mh1110/` (rebuild: research/ops/coverage1029/fetch.py,
research/bdi/moves/fetch5.py, frames_today.py) and `burst2/enr` (burst1/enrich.py). Educational only — not financial advice.
