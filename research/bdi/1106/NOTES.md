# BDI 2026-11-06 (Friday): quiet-day whipsaw — Move Hunt day 7 (capture 26%), all-account swing autopsy, SQZ1 / MH1106-P1 / GATE2 tested, merged "burst-chase" swing type

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in). **$ = Alpaca**
(`day_pl` = equity − last equity on the data branch, final state); journal `pnl_adj` $ where it differs. **Primary $ is
shown with and without MTUM** (owner rule 11-06: the MTUM −183 position is a broker / fill anomaly under investigation —
an Alpaca paper bogus 1:4 split; not in R). R = journal `pnl_adj / $ risk`. Two-year tests use the lab cache of
research/bdi/1104/DATA.md (frames to 11-04, trade lists `bt_lab1104`, BURST1 enrichment). **Locked block
2024-11-01..2025-02-28 never read (asserted in every script).** **5 configurations tried tonight, all reported; 0 pass**
(full bar max(1.5, √(2 ln 5)) = 1.79, BAR90 1.61; SQZ1 is also counted in the BURST lineage, 30 configs, bar 2.61).
No config, setup, exit, ledger or docs/live file changed.*

Built on, not redone: nightly1106 (close, coverage, Gen buying-power rejects, autopsy, latch / halt / BRAKE-1 / REG2 /
FLOW1 / L1-L6 shadows, Team final, DM-MF2 / DM-MF4), BURST2 (13 configs on the short burst, QQQ-flush gate kept as a
shadow). Their numbers are quoted, not recomputed.

**Day type: QUIET (QDAY).** SPY open-to-close **+0.07 %** (daily table; −0.04 % on 1-min 09:30 open → 15:59 close), SPY vs
its open at 10:00 **+0.78 % (above)**. SPY high +0.86 % 09:53, faded to +0.29 % at 10:41 (QQQ +0.93 % 09:53 → −0.21 % 10:30,
semis led), **squeezed +0.29 → +0.75 % 10:41-10:51**, chopped +0.3..+0.7 % to 12:30, flat close. IWM up all day (+0.78 %).
GATE1 states UP 11:00-12:30 / 14:00, MIXED otherwise; W60 compass confirmed UP from 10:00 with no flip — **an UP compass on a
flat close** (the held-side reading failed late).

**Rule changes inside the windows quoted** (research/ledger.jsonl): **none effective 11-06.** In the live day-type windows:
11-05 ROLL1 (Explore 1 / Live Lab low-rep homes), 11-04 UNI1 (T2 top-500) + DM-N3, 11-03 RW3S → T2 / MF3-FD, MF5-FD → GY,
10-30 Testing cost filter, 10-29 Primary −2R latch + BAR90, 10-28 Primary ~$4k lot, 10-20 MF2-FD / MF4-FD promoted.
Two-year results are rule-fixed.

## Today's win
**The Move Hunt caught 13 of the day's 50 biggest tradable moves (26 %, +10.88R captured) vs 1 / 50 (2 %, +0.24R) on
11-05 — the most R captured since the hunt started (10-29).** Short side 6 / 25 (+8.81R: STX +8.33R, five accounts' fade /
VWAP-reclaim shorts at 09:55), long side 7 / 25 (+2.07R: the 09:40-09:50 defensive rotation via Gen GEN-261021-02 and
CWT14 failed-PDL longs). **Research win:** the FB1 flush-chase tag replicated in its first forward session — shorts sold
within 0.15 ATR of the session low **−0.495R (n 88) vs +0.195R for the rest** (MF2-FD 37 at −0.75R), which is exactly
Primary's loss mechanism. Account wins: Graveyard +21.75R / +$536, Testing 1 +3.64R, Explore 1 +2.40R; Claude's Team
(shadow) +10.84R vs Primary −24.18R (nightly).

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-06; research/bdi/moves/moves_1106_out.txt)
Inputs rebuilt tonight: priors + SIP 1-min bars for 1,664 universe names, 5-min bars 09-22..11-06, 11-06 lab frames; 1,255
liquid names, 82,724 decision rows, 1,331 live trades (538 symbols), 7 accounts.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 3 / 50 (6 %) | +0.90 | 5, −4.51R | **earnings blackout 37** (29 reported today / last night) |
| **tradable (blackout removed)** | **13 / 50 (26 %)**: long 7 / 25, short 6 / 25 | **+10.88** | 17, −17.76R | skipped 15, traded outside 10, no setup 7, wrong side 5 |

**Capture rate 26 % vs 2 % on 11-05** (10-29 26 %, 10-30 6 %, 11-02 22 %, 11-03 12 %, 11-04 20 %). Primary caught none
(it only traded MF2 / MF4 semis shorts and energy fades; it halted at 10:55). Catches: Gen GEN-261021-02 (MDLZ, HDV, PM),
GEN-261029-08 (NVDA +0.90R), GEN-261023-03; Graveyard heat_fade_short / NS3 / RW4 / CWT14-pdl (STX, AVGO, HSY, PVAL); T2
CWT14-pdl (SNDQ, SOXS); Ex1 NM-RWN3 (STX).
What was known at the decision point:
- **09:35-09:50, defensive rotation on an up open:** 13 of the 25 top tradable long moves were low-beta staples / defensives
  that had NOT joined the rally (TSN, HSY, KO, SBUX, MDLZ, HDV, WMT, PM, XLP, DRI, QSR, VONV, PVAL; 1.0-1.6 ATR by
  10:30-11:10) while QQQ was rolling over. Misses: Gen GEN-261021-02 skipped 6 of them on "max positions for this setup"
  at 09:50 (SBUX, VONV, WMT, XLP, KO, TSN), spreads (DRI 44 bp, HSY in T2). → tested tonight as **MH1106-P1** (below).
- **Short side:** semis / tech names peaked 09:50-09:55 and fell to 10:31-10:37 (STX, AVGO, ADI, NVDA) — the fade shorts
  that sold at 09:55 caught them; MF2 / MF4 sold the same names 35-45 min later, at the bottom of that move (§0b).
- Inverse / vol ETPs (UVIX, UVXY, VXX, SDOW, DOG) short at 09:35: skipped not-shortable / opposite side held.
- **Precursor test MH1106-P1** (pre-registered in MH_PLAN.md, commit 79158e685; mh_p1_out.txt): long at the 09:50 bar names
  with 60-session beta ≤ 0.50 and fromOpen ≤ +0.10 % on days SPY ≥ +0.40 % from its open; t1s1, production costs.
  **20 qualifying days in two years, n 2,799, avg −0.023R (TRAIN −0.040 / VALID +0.004), win 54.1 % vs base 42.2 %,
  months positive 40 %, w/o best day −0.066R → fails.** Precision beats the base rate: **excess +0.170R over the same day's
  other 09:50 longs (day-t 1.51; VALID +0.357R)**. QDAY: **down-close (reversal) days +0.158R (n 938, 6 days), up-close days
  −0.114R (n 1,861, 14 days)**, no quiet day qualified in two years; SPY above its open at 10:00 by construction. 11-06
  in-sample (mh_p1_live_out.txt): 118 names +0.241R (66 % win) vs base −0.063R. Reading: a hedge-leg / relative edge on
  up opens that fade, not a stand-alone setup → forward shadow `mh1106-p1`, backlog `mh-1106-defensive-rotation-0950`.

## 0b. Swing autopsy, every account (swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = 1105 (1-min marked R per lot, zig-zag legs ≥ 25 % of the day's R range; each decomposed leg = market (beta × SPY)
+ setup-day mismatch (sector-ETF residual) + bad entries (fill + first 5 min) + stock-specific (rest, incl. exits and costs);
parts sum exactly, asserted). Betas 5-min 09-22..11-05.

**Primary** (52 lots, 48 short / 4 long; all entries 10:00-10:50, halted 10:55): R peak **+16.21R 10:41**, trough −31.66R
11:34, close **−24.18R**; journal $ +435 (10:36) → −1,091; **Alpaca −$1,238.60 with MTUM, ≈ −$1,054 without** (MTUM phantom
≈ −$184, broker / fill anomaly under investigation).

5-minute timeline (timeline_p.csv, excerpt):

| ET | open R | realized R | total R | SPY | QQQ | longs / shorts | net beta (R per +1 % SPY) |
|---|---|---|---|---|---|---|---|
| 10:09 | +0.07 | 0.00 | +0.07 | +0.48 % | +0.24 % | 1 / 1 | −0.8 |
| 10:29 | +4.37 | +0.61 | +4.98 | +0.45 % | +0.02 % | 0 / 8 | −16.8 |
| 10:39 | +3.53 | +5.04 | +8.57 | +0.34 % | −0.14 % | 2 / 15 | −28.5 |
| 10:49 | −10.44 | −16.15 | −26.59 | +0.61 % | +0.30 % | 2 / 21 | −32.7 |
| 10:59 | −0.75 | −25.08 | −25.84 | +0.59 % | +0.26 % | 2 / 16 | −17.7 |
| 11:29 | −4.48 | −25.15 | −29.63 | +0.57 % | +0.35 % | 1 / 12 | −10.6 |
| 12:49 | +4.88 | −26.58 | −21.70 | +0.09 % | −0.45 % | 0 / 9 | −6.8 |

| leg (ET) | R | $ | SPY | market | mismatch | bad entries | stock | top 5 names (display name, code) | what turned it |
|---|---|---|---|---|---|---|---|---|---|
| 10:25→10:41 | +16.89 | +511 | +0.72→+0.29 % | +12.64 | +2.89 | +0.82 | +0.54 | MU, TER, VRT, CRDO, AVGO — Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` (+8.65R) | semis sold off with QQQ (−0.9 % in 30 min); 41 entries inside the leg, 38 short |
| **10:41→10:51** | **−46.59** | **−1,823** | **+0.29→+0.75 %** | **−24.21** | **−12.60** | +0.57 | −10.35 | ASX, AVGO, CRDO, IYW, TER — `MF2-open-rsimidhi-flowsell-FD` (−10.59R); by setup MF2-FD −35.10, Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD` −8.79, Big Gainer Dip-and-Pop `NS1-rsidip-rsi5pop-long` −1.63 (SOXS long = the same semis bet) | **the index squeeze against 37 open shorts (net beta −28.5R / +1 %)**, semis bouncing harder than SPY (mismatch); 20 stops 10:44-10:52 |
| 10:51→11:13 | +13.68 | +781 | +0.75→+0.35 % | +6.76 | +2.81 | +0.05 | +4.06 | TER, PANW, CIEN (MF2-FD), WDC, SNDK (MF4-FD) (+7.90R) | the surviving shorts as SPY faded again; no new entries (halt 10:55) |
| 11:13→close | −7.47 | −517 | +0.35→−0.04 % | | | | | | drift; halted, nothing new could recover it |

**Split of the −46.59R swing: market −24.21 + setup-day mismatch −12.60 + bad entries +0.57 + top-5 / stock-specific
−10.35 (sum −46.59).** Bad entries are not the problem (+0.57R): it is *where* in the swing the book sold — 34 of 40 open
lots at 10:41 were one theme (semis / tech names, the ETPs SOXX, SOXQ ×2, QTEC, IYW, MTUM, and a SOXS long). The recovery
leg was driven by the same MF2 / MF4 survivors; the day's only other Primary R came from energy fades entered 10:45-10:50
(Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` CVX +1.0R / XOP +0.8R, Gap-Down Pop
Fade (all day) `RW5-…-FD` XOM +0.5R, Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` HSY +1.2R). Peak → close
−40.4R (give-back = the squeeze; nightly: entered after the $ peak 28 trades −$764).

**Testing 1** (92 lots, 78 short): +3.64R / journal +$12.80, **Alpaca −$30.32** (≈ $43 gap vs the journal, small; for the
nightly reconcile). Range 14.4R; largest legs 11:20→11:56 −13.15R (market −7.31, mismatch −3.97, entries −0.04, stock −1.83;
Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD` −8.57R: 27 shorts riding SPY back to +0.66 %) and
15:10→15:59 +10.20R (market +10.00: the late SPY fade; RW7 +9.25R, Afternoon Blow-off Short `exhaustion_short` +4.39R).
T1 is an index-beta book (~−20..−31R per +1 % SPY): it whipsawed with SPY all day and closed near its R high (+4.12R 15:54).

**Testing 2** (165 lots, 101 long): −2.00R / Alpaca **+$51.95**. 10:22→10:53 −9.05R (market −0.38, mismatch −1.82, **bad
entries −4.28**, stock −2.56; Gap-Down Heavy-Selling Short, no RSI condition (all day) `RW3S-gapdn-flowsell-short-FD`
−8.03R) and 11:05→12:34 −13.60R (mismatch −6.94, stock −6.97; RW3S −9.59, Gap-Down Bounce Short `RW1-…-FD` −3.90). Net beta
near zero (+7.9..−4.0R per 1 %): T2's swings were stock-level, not market. RW3S verdict stands (nightly: fails).

**Graveyard** (623 lots): +21.75R / Alpaca **+$536.28**; peak +58.85R 11:33 → close (give-back 37.1R). 09:51→10:15 **+61.64R**
(market +7.57, **mismatch +30.49**, entries +3.78, stock +19.79): **Morning Bounce Fade `heat_fade_short` +22.83R** (27 shorts
09:50-09:56 at the semis peak: STX, WDC… with NS3 / RW4 sisters on the same names), Morning Bounce Fade (all day)
`heat_fade_short-FD` +7.72R. 11:53→12:53 **−69.53R** (market −47.31 with 120 longs open, net beta +85.6R / 1 %; Failed
Opening-Range-Low Break Long (low volume) `CWT14-failbrk-orl-p10-lowvol-long` −20.14R, `CWT14-failbrk-orl-p10-long` −17.70R,
Midday Gap-Up Dip Buy `heat_fade_long` −13.03R; ORCL, INIO, SOXL, VIG) — the long book through the 12:00-12:53 QQQ slide.
One-big-day check: heat_fade_short record 166 trades / 12 sessions −0.114R, **w/o today −0.319R** (today +23.3R; record sum
−18.9R) — a Graveyard-origin one-day burst, not a candidate.

**Gen** (356 lots): −12.90R / Alpaca **−$157.92** (journal −$272.82); peak +36.50R 10:35. 10:02→10:35 +42.20R (market +18.55,
mismatch +34.89; `GEN-261029-08-…-SPYgt0p5-hold-short` +30.10R on growth ETFs VUG / VOOG / IUSG / IWY / QQQM, `GEN-261021-02`
+25.49R) then **10:35→10:51 −48.95R** (market −35.58: the same squeeze took back GEN-261029-08's ETF shorts −46.06R).
GEN-261021-07 VWAPxUp long bought the squeeze top (37 longs 10:46-10:53, −19.2R, 21 stops). 348 buying-power rejects (HK-GEN-BP).

**Explore 1** (24 lots): +2.40R / Alpaca +$51.12; 09:50→10:35 +15.57R (Early Sellers, Mid-High RSI `MF2-open-rsimidhi-flowsell`
+9.95R, Early NS3 Short While SPY Up (near-miss) `NM-RWN3-ns3-spyup-early-short` +6.77R) → 10:35→10:51 −14.50R (market −9.46;
MF2 base −13.97R: the Primary wave in miniature). **Live Lab** (19 lots): −1.17R / Alpaca −$59.54; 10:07→15:09 −8.51R spread
across `ST6-volspikeup-short-mid-t1s1-FD` −5.51R and singles; late SPY fade +3.90R.

**Cross-account cause (one line):** the 09:50-10:35 semis / tech slide was sold *late* by momentum shorts (Primary MF2 / MF4,
Ex1 MF2, Gen GEN-261029-08) and the 10:41-10:51 SPY squeeze stopped them together, while long bursts (Gen GEN-261021-07,
GY CWT14 orl) then bought the squeeze top 10:46-10:53 — the burst-chase both ways; the early fades (GY heat_fade_short 09:50)
made the day's money.

### Leads (research/bdi/swings/hypotheses.jsonl; 18 leads + 1 accumulating swing type)
- **Merged accumulating swing type `swing-burst-chase`** (11-05 + 11-06, 2 of 24 sessions): a same-side burst *after* the index
  already moved ≥ 0.4 % that way in 30 min, stopped together in the snap-back. 11-05 Primary 10:42→11:22 −19.29R (MF4-FD 11
  shorts at the low); 11-06 Primary 10:41→10:51 −46.59R (MF2-FD / MF4-FD 30 shorts at 10:35-10:40) + Gen / GY long bursts
  at the squeeze top. Linked shadows: burst1-openloss-latch3, burst2-openloss-latch4, burst2-flush-gate-short,
  fb1-flush-chase-shadow, swing1106-L10. Remedies tested so far: BURST1 16 + BURST2 13 + SQZ1 1 = **30 configs, 0 pass**.
- **New lead `swing1106-L10` — TESTABLE, pre-registered in SQZ1_PLAN.md (commit d5855d6b3) before its 2-year read:**
  class A = ≥ 3rd same-side entry of a setup within 15 min AND QQQ 30-min return at entry ≤ −0.40 % (short) / ≥ +0.40 %
  (long); rule: class A takes a +0.5 × stop-distance target. **ONE 2-year backtest (sqz1_out.txt; 1.10M lab trades,
  5-min MFE, stop-first on the exit bar, costs in, locked block excluded; 1 config, BURST lineage 30, bar 2.61):**
  class A 7.6 % of trades (84,269); **TRAIN −268R (day-t −1.15), VALID −277R (t −1.38), VALID excess −84R (t −0.45);
  4 families harmed** (GEN −239R, exhaustion −62R, MF −38R, RW −10R); VALID setups 20 better / 29 worse → **fails.** QDAY:
  VALID down days −287R, quiet +52R, up −41R; SPY above its open at 10:00 −336R, below +59R. The +0.5R target is worse for
  these entries on two years than their own exits; 11-05 / 11-06 were the exception (in-sample +56.8R / +13.1R live).
  Forward shadow from 11-09 (bar: ≥ 5 sessions with class A, scalp − live > 0 on ≥ 60 % and beyond the same scalp on the
  same setups' other entries). Primary edit check (mf_t05_out.txt, 1 config): MF2-FD with a +0.5 stop-unit target is worse
  on its own record too (TRAIN −20.6R, VALID −59.6R, 10-06..11-04 −42.4R); MF4-FD is already t05s1. Supports DM-MF2 / DM-MF4.
- **Forward tallies, 11-06** (forward.csv, forward_1106_out.txt, fb1_live_out.txt; L1-L6 from nightly1106):
  L1 A 20 −0.276 vs B −0.154; L2 no trigger; L3 not qualifying; L6 counter 546 +0.082 vs −0.073 (setup-adjusted +0.003);
  **L7 class A 54 +0.876 vs B +0.022 (wrong sign: the 09:50 heat_fade_short burst at the QQQ high won)**; L8 no class A;
  **gate1-checkpoint-gate day 2 −11.64R** (dropped 38 winning GY / Gen longs; 2-day +2.17R, 18 to go); comp15 confirmed UP
  10:00, 0 flips, closed quiet; **burst1-openloss-latch3 forward day 1: 12 shadow-latched setup-days, all Graveyard
  (CWT14 orl / pdl longs 10:01-10:47), +39.51R vs live on taken entries**, Primary none (the MF2 wave entered in profit);
  L9 not qualifying; **fb1-flush-chase day 1: A (near-LOD shorts) 88 −0.495 vs rest 455 +0.195; Bn (bounce-sold) 89 −0.053
  vs +0.110 (wrong sign)**; burst2 shadows / L10 / mh1106-p1 in-sample (forward from 11-09); latch1103 day 3 (nightly) GY
  latch cost 30.6R. **Best forward lead tonight: fb1-flush-chase-shadow (A side −0.69R vs rest on day 1, n 88) with
  burst1-openloss-latch3 (+39.5R, Graveyard) close behind.**

## 0. Per-account session review (accounts.py → accounts_out.txt / accounts.csv; bursts_out.txt; daytype_out.txt)

| account | Alpaca $ | R | trades | win % vs break-even | avg R | peak → close (journal $) | best setup | worst setup | notable skips |
|---|---|---|---|---|---|---|---|---|---|
| Primary | **−1,238.60 with MTUM / ≈ −1,054 without** | **−24.18** | 52 | 33 % vs 58 % | −0.465 | +435 (10:36) → −1,091 | L3-fromopen-FD 1 +1.2R; RW3-FD 4 +1.5R | MF2-FD 28 −21.6R −$641 | 419 / 471 (ETB 279, halted 92: what-if +8.1R, nightly) |
| Testing 1 | −30.32 (journal +12.80) | +3.64 | 92 | 61 % vs 58 % | +0.040 | +61 (10:42) → +13 | RW7-FD 39 +6.7R | intraday_momentum 3 −2.5R | 120 / 212 (cost filter 33) |
| Testing 2 | +51.95 | −2.00 | 165 | 61 % vs 62 % | −0.012 | +165 (11:14) → +47 | CWT14-pdl-p10-lowvol-long 24 +2.5R | RW3S-FD 29 −6.5R | 113 / 278 (spread 60) |
| Graveyard | +536.28 | +21.75 | 623 | 64 % vs 62 % | +0.035 | +2,153 (11:34) → +397 | heat_fade_short 34 +23.3R +$786 | CWT14-orl-p10-lowvol-long 44 −17.0R | 1,170 / 1,793 (setup loss limit 412) |
| Gen | −157.92 (journal −272.82) | −12.90 | 356 | 52 % vs 54 % | −0.036 | +510 (10:36) → −273 | GEN-261021-02 long 85 +35.9R | GEN-261021-07 long 46 −26.6R | 863 / 1,219 (buying power 348) |
| Explore 1 | +51.12 | +2.40 | 24 | 54 % vs 49 % | +0.100 | +228 (10:36) → +48 | NM-RWN3 6 +6.1R | MF2 base 11 −1.9R | 54 / 78 (ETB 20) |
| Live Lab | −59.54 | −1.17 | 19 | 42 % vs 47 % | −0.061 | +64 (10:08) → −61 | NM-RWR3 3 +3.4R | ST6-volspikeup-FD 8 −3.1R | 32 / 51 (ETB 18) |

Give-back causes (peak → close): **Primary** −40.4R = the 10:41-10:51 squeeze against the semis short stack (market −24.2,
mismatch −12.6); **T1** ~0.5R (closed near its R high; $ give-back $48 = 11:20-11:56 index rebound); **T2** $118 = RW3S
stock-level losses; **GY** −37.1R from 11:33 = longs through the 12:00-12:53 QQQ slide (market −47.3R); **Gen** −49.4R from 10:35
= the squeeze on GEN-261029-08's ETF shorts; **Ex1** $180 = MF2 base in the same squeeze; **LL** $125 = ST6 shorts.
One-big-day checks (records): GEN-261021-02 183 trades / 3 sessions +0.066R, **w/o best −0.242R (today 296 % of R, `1 day`)**;
GEN-261029-08 114 / 3 −0.193R, w/o best −0.808R; heat_fade_short −0.114R, w/o best −0.319R; RW7-FD (T1) 436 / 19 +0.061R, w/o
best +0.032R (53 %, `1 day`); NM-RWN3 / NM-RWR3 1 session each (no verdict, ROLL1 rotation).

**R by day type** (all live sessions, daytype_out.txt; window now 12 quiet / 6 up / 6 down): Primary **quiet −0.145R (388)**,
up −0.165 (322), down +0.224 (261); by 10:00 side above +0.019 / below −0.135. T1 quiet −0.077 / up −0.214 / down −0.063;
T2 −0.061 / −0.139 / −0.266; GY −0.064 / −0.114 / −0.198; Gen −0.197 / −0.426 / −0.179; Ex1 / LL 1 quiet session each
(+0.100 / −0.061). **Primary MF2-FD on quiet days −0.729R (37 trades)** vs down +0.623 / up +0.274 — quiet days are where
MF2-FD loses. Live setups positive on both up and down days (≥ 10 each): 10 (RW5-FD also +0.294 on quiet days, RW1-FD T2 +0.069
quiet, L3-fromopen T1 +0.268 quiet) — RW5-FD is the one Primary setup positive on all three day types.

**Maximization edits (tested or queued; none live):**
- *Primary:* (1) +0.5R target for MF2-FD — **tested, fails** (mf_t05_out.txt); (2) chase-burst scalp (SQZ1) — **tested,
  fails**; (3) one theme = one bet (ETP + holdings + inverse ETP in 15 min: 34 of 40 lots at 10:41) — queued
  (`nightly-1106-etp-component-stack`); halt scope — queued (`nightly-1106-halt-scope-latched-only`). The decisions that
  matter are already on the inbox (DM-MF2 / DM-MF4).
- *Testing 1:* RW7-FD's R tracks the index (−20..−31R / 1 %); GATE2 held-side sizing — **tested, fails** (below); keep.
- *Testing 2:* RW3S verdict stands (nightly); no new edit.
- *Graveyard:* burst1-openloss-latch3 — forward (day 1 +39.5R on CWT14 longs); FB1-L near-HOD longs were +0.060 vs −0.126
  (no veto case).
- *Gen:* GEN-261021-02 capacity at 09:50 (6 top movers skipped on max positions) — queued as housekeeping
  (`bdi-1106-gen261021-02-capacity`; one-big-day record, check first); HK-GEN-BP (nightly).
- *Explore 1 / Live Lab:* day 2 of ROLL1; no verdict (re-evaluated after ~2 sessions per ROLL1).

## 1. Every-trade analysis (trades_bdi.py → per_trade_1106.csv, patterns_1106.csv → patterns.csv +551 rows; bursts.py)
- **Exit what-ifs** (1,331 trades, R after costs, 1-min SIP): live −0.009 / trade; orig sim +0.029 (**live is 0.04R worse than
  the bracket on bars — GY live +21.7R vs sim +43.5R, Gen −12.9 vs +4.4: fills / slippage**), be05 +0.005, **t05 +0.009**,
  trail +0.005, hold −0.053, sar −0.029, reent +0.013, opposite −0.027. Primary: t05 −2.6R vs live −24.2R, be05 −13.4R,
  trail −9.3R, opposite 1R/1R +15.8R (MF2-FD t05 −1.9R vs −21.6R). One session; the two-year checks of the same exits fail
  (SQZ1, mf_t05).
- **Opposite side, hindsight check:** entries with SPY ≥ |0.25 %| against them (shorts today) 547 trades **+0.081R** live
  (opposite −0.136): on a quiet day the counter-index shorts *won* (L6 +0.082). No rule known at entry picks the trades whose
  opposite won (flag_fo: opposite +0.015 vs −0.044).
- **Loss types** (losers): wrong_side_after_big_swing P 18 / −$952 (the squeeze), GY 44 / −$1,397; never_worked GY 66 / −$1,523,
  Gen 44 / −$810; stopped_then_reversed P 4, GY 27 / −$729.
- **Bursts** (≥ 4 same-setup same-side entries in 10 min): 104 bursts, 932 entries, +5.6R (avg +0.006R vs non-burst −0.045R);
  **9 bursts with ≥ 75 % stops = −52.4R.** Good bursts fired early on the 09:50 extreme (Gen GEN-261021-02 61 longs 09:50-09:57
  +33.8R, GY heat_fade_short 27 shorts 09:50-09:56 +19.2R, Gen GEN-261029-08 26 shorts 10:05-10:14 +24.2R); bad ones fired
  after the index already moved (P MF2-FD 13 shorts 10:40 −15.1R + 9 at 10:30-10:40 −9.8R, Gen GEN-261021-07 37 longs
  10:46-10:53 −19.2R, GY CWT14 orl 54 longs 10:46-10:52 −22.8R, Gen GEN-261029-01 20 longs 11:25-11:33 −14.6R).
- **Correlated stacking** (same symbol, same side, ≥ 2 setups, 30 min): Primary 16 lots −10.3R (MF2 / MF4 twins on AVGO, MRVL,
  SNDK, SOXQ, UMC, AMKR, KLAC, TER) plus **cross-instrument stacking: 5 semis / tech ETPs (SOXX, SOXQ ×2, QTEC, IYW) shorted
  with their holdings and a SOXS (3× inverse semis) long on NS1 — one bet ≈ 34 lots**; T2 87 lots −3.0R; GY 206 lots +8.8R
  (heat_fade / NS3 / RW4 on STX, WDC won); Gen 31 −0.2R.
- **Give-back** (journal $): GY $1,756, Primary $1,526, Gen $783, Ex1 $179, LL $125, T2 $118, T1 $48.

## 2-3. Patterns → testable rules; NEW tested ideas (all pre-registered and committed before their two-year read)
| idea (source) | configs | result | QDAY split | verdict |
|---|---|---|---|---|
| **SQZ1** chase-burst +0.5R scalp (swing autopsy 11-05 / 11-06) | 1 | VALID −277R, t −1.38, excess −84R; 4 families harmed | VALID down −287 / quiet +52 / up −41R; above-10:00 −336 / below +59R | fail → forward shadow L10 |
| **MH1106-P1** defensive rotation long (Move Hunt) | 1 | 20 days, avg −0.023R, excess +0.170R (t 1.51), 40 % months | down-close +0.158 / up-close −0.114; no quiet day; above 10:00 by construction | fail → forward shadow (relative edge) |
| **GATE2-A** held-side VWAP pullback (queue GATE2) | 1 | n 66,240 / 362 days, avg −0.066R (t −4.94), confirmed − unconfirmed +0.026 | long on up-close +0.053, short on down-close +0.018, **quiet −0.335 (long) / −0.400 (short)**; above −0.053 / below −0.083 | fail |
| **GATE2-B** held-side open-hold pullback (queue GATE2) | 1 | n 12,458, avg −0.081R (t −3.47), confirmed − unconfirmed +0.035 | up-close long +0.015, down-close short −0.018, **quiet −0.33 / −0.34**; above −0.060 / below −0.105 | fail |
| MF2-FD +0.5R target (Primary edit) | 1 | TRAIN −20.6R, VALID −59.6R, late −42.4R | — | fail |

**QDAY reading:** GATE2 shows the held-side reading pays only when the day keeps its direction (and then barely); **on the
days that end quiet the with-the-tape pullbacks lose 0.33-0.40R** — the 11 % of "confirmed" readings that fail are the quiet
days. So the QDAY problem is not finding a better with-trend entry but recognising a quiet day early; none of tonight's ideas
does that, and no light-lane (Live Lab) candidate came out of it (the light-lane gate is expectancy ≥ −0.02R on train and
valid; MH1106-P1 is −0.040 / +0.004, GATE2 −0.05..−0.11). Exhausted families (pdl1030*, rdt1030, saturday1031, night1102) not
repeated. Next QDAY step (queued in thought, not run): a quiet-day detector from the 10:30 compass + breadth dispersion, scored
on how often it labels the close correctly, before any setup is built on it.
Remedies rule: SQZ1 per family / setup above (GEN −239R, exhaustion −62R, MF −38R, RW −10R harmed; CWT +59R, NS +9R, L +3R
helped; VALID 20 setups better (+146R) / 29 worse (−423R)) — the remedy is not targeted enough on two years.

## 4. Swarm / configs counted
Configs tonight: SQZ1 ×1, MH1106-P1 ×1, GATE2 ×2, MF2-FD t05 ×1 = **5** (full bar 1.79, BAR90 1.61; plans were written for
N = 2 / 4 before the later configs were added, and all fail on any of these bars). 0 pass. Queue order: ROTA1 not started
(Saturday's), **GATE2 run (2 configs, fails; status left pending for the owner's broader GATE2 ask — the GATE1 near-miss
sizing part is not done)**, FLOW1-2Y / XA-* not run. Locked block never read. Backlog +3 parked (`sqz1-1106-chase-burst-scalp`,
`mh-1106-defensive-rotation-0950`, `bdi-1106-gen261021-02-capacity`; add_backlog.py; BACKLOG.md regenerated).

## 5. Decision
None new. Nothing passed; no setup moves. The pending DM-MF2 / DM-MF4 cards (nightly) gain two facts from tonight, for
Saturday: MF2-FD loses on quiet days (−0.729R, 37 trades) and neither a +0.5R target nor a chase-burst exit rescues it on two
years.

Files: accounts.py, swings.py, trades_bdi.py, bursts.py, daytype.py, forward_1106.py, fb1_live.py, sqz1.py (+ SQZ1_PLAN.md),
mh_p1.py / mh_p1_live.py (+ MH_PLAN.md), gate2.py (+ GATE2_PLAN.md), mf_t05.py, hyp_update.py, add_backlog.py (+ outputs).
Scratch inputs: priors / bars / frames under the session scratchpad `mh1106/` (rebuild: research/ops/coverage1029/fetch.py,
research/bdi/moves/fetch5.py, frames_today.py) and the BURST1 enrichment `burst2/enr`. Educational only — not financial advice.
