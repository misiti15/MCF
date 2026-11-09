# BDI 2026-11-09 (Monday): trend-up day — Move Hunt day 8 (capture 22 %), all-account swing autopsy, ECG1 early compass gate + MH1109-P1 tested (0 pass), counter-tape variant merged into "burst-chase"

*Educational only — not financial advice. Live numbers are **paper** results from one session (costs in). R = journal
`pnl_adj / $ risk`; $ = Alpaca `day_pl` on the data branches (nightly close-to-close where quoted). Two-year tests use the
lab cache (bt_lab1104 lists / lab frames to 11-04). **Locked block 2024-11-01..2025-02-28 never read (asserted in every
script).** **2 configurations tried tonight, both pre-registered and committed before their two-year read
(ECG1_PLAN.md commit 58c58843e, MH_PLAN.md commit 15184a08a), both reported; 0 pass.** No config, setup, exit, ledger or
docs/live file changed.*

Built on, not redone: nightly1109 (close, coverage, EOD chain fix, T1X, autopsy, MF1109 4-config screen, latch / BRAKE-1 /
REG2 / burst1 / gate1 / comp15 shadows, Team final +2.54R, PV out-of-sample day 1) and Exposure Lab 11-09. Their numbers are
quoted, not recomputed. Guild board (mcf-guild) read: its 11-09 threads (GATE2, OD0950 09:50 continuation — closed, NH1 near-HOD
continuation, SC1/SC2, C3FR, CWT14SKIP, BE-replay, STOPW) are not repeated here; no guild thread covers an early-compass
short gate.

**Day type: UP (trend day).** SPY open-to-close **+1.44 %** (QQQ +2.43 %, IWM +1.81 %); SPY vs its open at 10:00 **+0.78 %
(above)**. W60 compass UP-confirmed from 10:00, 30-min compass from 10:30, GATE1 UP at every checkpoint, 0 flips (live
compass/2026-11-09.csv). SPY high +1.82 % 15:15.

**Rule changes inside the windows quoted** (research/ledger.jsonl): **11-09 EXPO1109 temporary moves** — GEN-261021-02 /
GEN-261019-03 / GEN-261026-02 Gen → Testing 1, GEN-261022-07 / GEN-261026-03 Gen → Testing 2 (revert after the 11-10 close;
Testing totals include GEN results 11-09 / 11-10); live compass recording started 11-09 (display only). Earlier in the live
day-type windows: 11-05 ROLL1, 11-04 UNI1 + DM-N3, 11-03 RW3S → T2 / MF3-FD, MF5-FD → GY, 10-30 Testing cost filter, 10-29
Primary −2R latch + BAR90, 10-28 Primary ~$4k lot, 10-20 MF2-FD / MF4-FD promoted. No Primary rule change 11-09. Two-year
results are rule-fixed.

## Today's win
**Graveyard's coil longs and Gen's morning RSI longs caught the up-trend: Coil Under the High (4 bars) `CWT12-coil-k4-long`
+10.4R and (6 bars) `CWT12-coil-k6-long` +16.6R (15 longs 10:35-10:42, +15.3R), Generated Morning RSI Surge Buy
`GEN-261020-07-…-hold-long` +9.2R / +$398 (19 longs 09:55-09:58, +10.2R).** Move Hunt: 11 of the day's 50 biggest tradable
moves caught (+9.69R) — second-best R day of the hunt after 11-06. Claude's Team (shadow) +2.54R vs Primary −18.10R
(nightly). Research win: the live W60 compass read the day right at 10:00 (first confirmation 30 min before the 30-min
compass) and its gate idea, ECG1, would have removed +40.3R of today's momentum-short losses (in-sample) — the two-year test
says why it cannot go live as is (below), and points at the next version.

## 0a. Move Hunt (v1 definition unchanged; moves.csv +100 rows for 11-09; research/bdi/moves/moves_1109_out.txt)
Inputs rebuilt: priors + SIP 1-min bars for 1,676 universe names, 5-min bars 09-22..11-09, 11-09 lab frames; 1,267 liquid
names, 83,520 decision rows, 966 live trades (513 symbols), 7 accounts.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | 5 / 50 (10 %) | +4.55 | 10, −9.69R | earnings blackout 31 (16 reported today / last night) |
| **tradable (blackout removed)** | **11 / 50 (22 %)**: long 6 / 25, short 5 / 25 | **+9.69** | 18, −14.37R | no setup 14, skipped 12, traded outside 8, wrong side 5 |

**Capture rate 22 % vs 26 % on 11-06 (R +9.69 vs +10.88)**; hunt so far 10-29 26 %, 10-30 6 %, 11-02 22 %, 11-03 12 %, 11-04
20 %, 11-05 2 %, 11-06 26 %, 11-09 22 %. Primary caught none (it was short all day). Catches: T1 GEN-261021-02 (COF, SYF;
EXPO1109 move), GY CWT12 coil (DAR, IWP +2.10R), CWT14 orl (SCO), T2 CWT14 pdl (GTLB); shorts Gen GEN-261023-03 + T2 RW3S
(SOXS +2.77R), Gen GEN-261023-03 (PSQ), GY CWT14 pdh (FOXA).
What was known at the decision point:
- **The moves started at the open.** 20 of the 25 top tradable long moves had their best decision at 09:35-09:40 and ran
  to ~11:00 with almost no heat (MAE ≤ 0.08 ATR: MPWR, PL, AVAV, FN, TSEM, BG, PLD, VO, IWP, IWR...). Most MCF setups start
  at 09:50, by which time the move was ~half done; misses were "no setup" (14) and buying-power rejects (VO, CRBG, IWR in
  Gen/GY — HK-GEN-BP).
- **Short side = inverse index ETPs** (SOXS, SQQQ, QID, PSQ, SPXS, SPXU, SDS, SPDN, SH, UVIX: 11 of 25): mostly not
  shortable / no setup; 5 "wrong side only" (the book was long some of them as dip-buys — L1 shadow: inverse/vol ETP longs A
  29 −0.877R).
- **Precursor scan** (precursors.py, K 0.5 ATR, 11-05 / 11-06 / 11-09): the only feature with lift on all three days, both
  sides, is **vol_exp** (5-min ATR / daily ATR, "in play"): top quintile 2.9-4.2× the base rate — MH1 (10-29) showed it
  predicts size, not direction. → tested tonight as **MH1109-P1** with the direction taken from the W60 compass
  (pre-registered, MH_PLAN.md; mh_p1_out.txt): 10:00 bar, W60 confirmed (UP → long, DOWN → short), vol_exp ≥ 0.12, already
  moving the compass's way, t1s1, production costs. **217 confirmed days, n 78,822: precision 47.2 % win vs base 45.2 %
  (+2.0 pts) but avg R −0.138 vs base −0.111 (excess −0.005, day-t −0.59); TRAIN −0.119 / VALID −0.154; long −0.134 / short
  −0.141; months positive 18 %; w/o best day −0.144 → fails the full bar (1.67), BAR90 (1.50) and the light lane.** QDAY:
  shorts on down-close days −0.005, longs on up-close days −0.022, everything on quiet days −0.22..−0.30. 11-09 in-sample
  +0.610 vs base +0.453 (excess +0.157). Reading: being in play and on the compass side does not choose a better direction
  than the average name; the big-move days are visible only as "everything goes up" days. Parked
  (`mh-1109-inplay-compass-side`). Next precursor step (not run): an *open-window* catalogue (09:30-09:50
  decisions) to measure how much of the hunt is structurally out of reach for 09:50-start setups.

## 0b. Swing autopsy, every account (swings.py → swings_out.txt, timeline_<acct>.csv, 5-min)
Method = 1106 (1-min marked R per lot; each leg = market (beta × SPY) + setup-day mismatch (sector-ETF residual) + bad
entries (fill + first 5 min) + stock-specific (rest, incl. exits and costs); parts sum exactly, asserted; top 5 names =
cross-cut of the same leg). Betas 5-min 09-22..11-06. Primary decomposed at its local extremes (the zig-zag merged its day
into one leg).

**Primary** (36 lots, 35 short / 1 long): R peak **+0.25R 10:05**, trough −21.61R 14:41, close **−18.10R**; journal $
+16 (10:06) → −197; Alpaca −$175.87 close-to-close (nightly).

| ET | open R | realized R | total R | SPY | QQQ | longs / shorts | net beta (R per +1 % SPY) |
|---|---|---|---|---|---|---|---|
| 10:04 | 0.00 | 0.00 | 0.00 | +0.96 % | +1.55 % | 0 / 0 | 0 |
| 10:19 | −0.87 | 0.00 | −0.87 | +1.05 % | +1.85 % | 0 / 3 | −4.2 |
| 10:29 | −1.31 | 0.00 | −1.31 | +1.05 % | +1.82 % | 0 / 11 | −20.0 |
| 10:39 | −6.66 | 0.00 | −6.66 | +1.09 % | +1.81 % | 0 / 21 | −37.4 |
| 10:49 | −9.44 | −1.02 | −10.46 | +1.20 % | +2.03 % | 0 / 25 | −44.2 |
| 10:59 | −12.30 | −6.56 | −18.86 | +1.40 % | +2.39 % | 1 / 23 | −35.6 |
| 11:09 | −6.16 | −12.39 | −18.55 | +1.24 % | +2.18 % | 1 / 18 | −26.7 |
| 11:39 | −0.02 | −13.51 | −13.53 | +1.13 % | +1.91 % | 1 / 11 | −10.3 |
| 12:49 | +0.81 | −18.03 | −17.22 | +1.51 % | +2.30 % | 1 / 10 | −7.3 |
| 14:44 | −0.51 | −19.91 | −20.42 | +1.70 % | +2.60 % | 0 / 8 | −7.1 |
| 15:59 | 0.00 | −18.10 | −18.10 | +1.53 % | +2.46 % | 0 / 0 | 0 |

| leg (ET) | R | $ | SPY | market | mismatch | bad entries | stock | top 5 names (display name, code) | what turned it |
|---|---|---|---|---|---|---|---|---|---|
| **10:05→10:58** | **−19.20** | **−654** | +0.94→+1.40 % | **−13.75** | −2.37 | −2.64 | −0.44 | USD, COIN (Gap-Down Slope From Open `L3-gap-slope-fromopen-FD`), AVLV, QUAL, JEPI (Early Sellers, Strong Heat (all day) `MF4-h40-open-flowsell-FD`) −8.73R; by setup MF4-FD −12.12, L3-fromopen −6.35 | **29 new shorts into a tape the W60 compass had confirmed UP at 10:00**; net beta built to −44R per +1 % by 10:49 while SPY climbed another 0.5 %; 12 of 17 MF4-FD lots were broad / factor ETFs = one index short |
| 10:58→11:39 | +5.42 | +460 | +1.40→+1.13 % | +7.31 | −4.42 | −0.22 | +2.76 | COIN, BMNR, USD (L3-fromopen), MAGS, SPYM (MF4-FD) +8.24R | the 11:00-11:40 index dip; L3 crypto-linked shorts paid (COIN / BMNR), MF4 already mostly stopped |
| 11:39→close | −4.58 | −20 | +1.13→+1.53 % | −4.13 | −1.64 | +0.22 | +0.98 | FNDE (MF4-FD), TCOM, ACGL (Gap-Down Pop Fade, Heat (all day) `RW5-…-FD`), USD, SPYM −5.83R | the afternoon grind higher stopped the survivors |

**Split of the −19.20R swing: market −13.75 + setup-day mismatch −2.37 + bad entries −2.64 + stock-specific −0.44 (sum
−19.20); top-5 names −8.73R of it.** Unlike 11-05 / 11-06 there was no flush to chase and no squeeze: the book simply shorted
the index on a day the compass had already called UP, 20-50 minutes after it did. **What turned it:** nothing turned it —
the −2R latch fired 10:52, after MF4-FD's last entry (nightly: 0 entries saved), and the 11:00 GATE1 gate would have dropped
none of these entries (nightly).

**Theme "shorting into a confirmed-UP compass before 11:00" → merged into the accumulating swing type `swing-burst-chase`
as its counter-tape variant** (3 sessions in 25: 11-05, 11-06, 11-09), and **the EARLY compass gate was pre-registered and
tested (ECG1, below)**.

**Testing 1** (65 lots, 58 long): −1.69R / journal −$6.99, Alpaca −$136.93 close-to-close (incl. the T1X short MCF did not
place — DECISION T1X, nightly). Range 9.5R in 14 small legs that track SPY's wiggles (net beta +14..+18R per 1 %): 14:29→14:40
+7.08R (market +5.34; Big-Dip RSI Pop Buy (all day) `NS1-rsidip-rsi5pop-long-FD` +9.70), 14:53→15:30 +6.85R (market +2.51,
mismatch +2.00; NS1-FD +4.55). The moved GEN-261021-02 (EXPO1109) 29 longs −3.64R, 22 entered at 09:50.

**Testing 2** (53 lots, 28 short): −5.07R / Alpaca −$66.96. 11:53→13:34 −9.09R (stock −5.92: Gap-Down Capitulation Buy
`NM-AR-…-long` −2.48, CWT14 pdl longs −1.65) and 14:28→15:28 −10.35R (market −4.92 with net beta −20.9R / 1 %: PM VWAP-Reclaim
Oversold Short `NS4-pm-vwap-reclaim-oversold-short` −5.53R, `exhaustion_short-FD` −3.53R — shorts into the 15:15 high).

**Graveyard** (512 lots): −76.41R / Alpaca −$549.75; peak +9.82R 09:59 → trough −101.65R 15:15. 09:59→close **−86.24R**
(market −31.59 with net beta −57R / 1 % at 10:00, **bad entries −24.16**, mismatch −12.95, stock −17.54; trough leg 09:59→15:15 ≈ −111.5R,
by setup MF3-FD −20.4, `heat_fade_short-FD` −19.8, MF5-FD −18.4, `heat_fade_short` −16.8): **the short book
(256 shorts −136R) sold the trend all day**, while CWT12 coil longs (+27R) and CWT14 pdl / orl longs (+19R) made money.
15:15 trough → close ≈ +25R (the late SPY dip; RW6 / NS2 shorts).

**Gen** (293 lots): −57.36R / Alpaca −$1,050.14; peak +3.85R 10:30. 10:30→14:28 −45.0R (stock −27.5, bad entries −11.3:
Generated Overbought Flow-Drop Short `GEN-261029-08-…-SPYgt0p5-hold-short` −35.7R — 50 shorts −38.9R on the day, two 18-lot
bursts 10:05-10:25 −28.4R, 28 stops), 14:41→close −41.6R (long book bought the 14:40 high, net beta +62.6R / 1 %: `GEN-261021-06`
−15.7, `GEN-261021-07` −15.5). 437 buying-power rejects (HK-GEN-BP).

**Explore 1** (4 lots, +0.60R / −$12.46) and **Live Lab** (3 lots, +1.40R / +$47.11): no swing worth decomposing (ranges
1.1R / 1.5R); LL's Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` SOXL / TECL +0.90R, Bull Flag `CWT12-flag-s1-long` VKTX +0.62R.

**Cross-account cause (one line):** a confirmed trend-up day from 10:00 that every short book sold anyway — Primary MF4-FD /
L3, GY MF3 / MF5 / MF1 / heat_fade, Gen GEN-261029-08 / GEN-261022-08 — while the longs that bought strength early (GY coil,
Gen GEN-261020-07, T1 NS1) made the day's money; shorts across 7 accounts −221.8R vs longs +65.2R.

### ECG1 — early compass gate (pre-registered ECG1_PLAN.md, ONE config; ecg1.py → ecg1_out.txt, ecg1_setups.csv)
Rule: block a new momentum short (`^(NM-)?MF\d`, `flowsell`, `^L3-`: 14 lab setups) entered ≥ 10:00 while the W60 compass
at the latest 15-min mark reads UP-confirmed (state, not latch). 2 years, bt_lab1104, 158,472 family shorts, costs in, locked
block excluded; lineage N 34 (BURST1 16 + BURST2 13 + MF1109 4 + 1): bar 2.66, BAR90 2.39.

| split | blocked | blocked avg R | kept avg R | delta (gate − none) | day-t | best day share |
|---|---|---|---|---|---|---|
| TRAIN (2024-10, 2025-03..12) | 27,614 of 76,468 | +0.017 | −0.132 | **−463.9R** | −0.18 | — (negative) |
| VALID (2026-01..10-05) | 24,657 of 73,707 | −0.025 | −0.042 | +605.7R | 0.67 | 66 % (w/o best +206R) |
| LATE lab rows (10-06..11-04) | 3,050 of 8,297 | −0.105 | +0.012 | +319.4R | 0.41 | 229 % (w/o best −411R) |

**FAIL** (VALID t 0.67 < 2.66 / 2.39; TRAIN negative; 2 setups worse by > 5 %: L3-fromopen −110R, L3-rsi5hi −7.5R; 12 better:
MF1-FD +236, RW3S-FD +108, RW5-FD +106, MF3-FD +64, L3-lowdist +52, RW3-FD +40, MF4-FD +39 ...). **QDAY: the gate gains on
up-close days (TRAIN +879R, VALID +2,472R, LATE +549R) and loses on W60-UP mornings that close quiet (VALID −1,360R) or down
(−507R); by SPY vs its open at 10:00 above +394R / below +212R (VALID).** So the early UP reading is right often enough to
confirm the side, but the 11 % that fail are where the blocked momentum shorts make their money. **Live 11-09 (in-sample):**
86 family shorts, 70 shadow-blocked, live −40.32R → gate gain **+40.32R** (Primary 35 +18.58R incl. MF4-FD 17 +17.09R, GY 29
+25.47R, T2 6 −3.72R). Remedies rule: per-setup table above; the harm is concentrated in L3 (which is not a momentum-flow
short in mechanism — its gap-down slope trades lost when blocked). → forward shadow **swing1109-L11** (from 11-10), and the
salvage idea **ECG2** (same gate only when SPY ≥ +0.75 % from its open at the mark — the "strong move" fact that holds its side
89-97 %) parked as an idea for a pre-registered run (`ecg2-1109-strong-up-gate`; it would be config 35 of the lineage).

### Leads (research/bdi/swings/hypotheses.jsonl; 19 leads + 1 accumulating swing type)
- **New lead `swing1109-L11` — TESTABLE, pre-registered (ECG1), two years failed → forward shadow** with bar: 15 sessions with
  ≥ 1 blocked entry, gain > 0 on ≥ 60 % and in total, then the ECG2 re-test before any DECISION.
- **`swing-burst-chase`** gains its 11-09 instance (counter-tape variant) and the ECG1 / MF1109 remedies: **35 configs, 0 pass**.
- **Forward tallies 11-09** (forward.csv, forward_1109_out.txt, fb1_live_out.txt, mh_p1_live_out.txt; L1/L2/L3/L6/burst1 from
  nightly1109): L1 A 29 −0.877 vs B +0.147 (right sign); L2 no trigger; L3 qualifying, family shorts 27 −0.612 (right sign);
  L6 counter 430 −0.516 vs +0.122 (right sign, opposite of 11-06); L7 class A 430 −0.516 (no class B); L8 no class A; L9 not
  qualifying; **burst1-openloss-latch3** P +0.89R / GY +10.56R; **burst2-openloss-latch4 day 1: +16.59R vs live** (10
  setup-days, P MF4-FD latched 10:40); burst2-flush-gate-short 3 blocked +0.96R; **swing1106-L10 day 1: 89 class A, scalp −
  live +3.42R**; fb1 A 59 −0.508 vs rest −0.500 (no separation), Bn 168 −0.384 vs −0.578 (right sign); mh1106-p1 day 1 excess
  −0.286 (wrong sign; up-close day, as its 2-year split predicted); gate1 day 3 +15.88R (3-day +18.05R, nightly); comp15 W60
  10:00 UP correct (nightly).
  **Best forward lead tonight: burst2-openloss-latch4 (+16.6R on its first forward day, 7 accounts) with gate1-checkpoint-gate
  (+18.05R over 3 sessions) next.**

## 0. Per-account session review (accounts.py → accounts_out.txt / accounts.csv; bursts_out.txt; daytype_out.txt)

| account | Alpaca $ (close-to-close) | R | trades | win % vs break-even | avg R | peak → close (journal $) | best setup | worst setup | notable skips |
|---|---|---|---|---|---|---|---|---|---|
| Primary | −175.87 | **−18.10** | 36 | 31 % vs 59 % | −0.503 | +16 (10:06) → −197 | RW3-FD 2 +1.0R | MF4-FD 17 −17.1R −$203 | 227 / 263 (ETB 163, latch 28) |
| Testing 1 | −136.93 (T1X) | −1.69 | 65 | 57 % vs 59 % | −0.026 | +58 (10:08) → −7 | NS1-FD 22 +3.6R | GEN-261021-02 29 −3.6R | 161 / 226 (split-tape gate 113) |
| Testing 2 | −66.96 | −5.07 | 53 | 60 % vs 68 % | −0.096 | +83 (11:30) → −69 | CWT14-pdl-p10-long 13 +3.8R | NS4 6 −5.0R | 49 / 102 (ETB 22) |
| Graveyard | −549.75 | −76.41 | 512 | 54 % vs 65 % | −0.149 | +42 (10:00) → −653 | CWT12-coil-k6-long 17 +16.6R | heat_fade_short-FD 26 −19.3R | 997 / 1,509 (latch 282, BP 173) |
| Gen | −1,050.14 | −57.36 | 293 | 40 % vs 52 % | −0.196 | +173 (10:32) → −1,138 | GEN-261020-07 27 +9.2R | GEN-261029-08 50 −38.9R | 709 / 1,002 (BP 437) |
| Explore 1 | −12.46 | +0.60 | 4 | 75 % vs 65 % | +0.150 | +1 (14:57) → −13 | CWT05-flush-m05-v5 3 +1.6R | ST8-FD 1 −1.0R | 13 / 17 (ETB 11) |
| Live Lab | +47.11 | +1.40 | 3 | 100 % | +0.468 | +47 (15:32) → +47 | NM-ETF late dip 2 +0.9R | — | 10 / 13 (ETB 10) |

**The 5 GEN setups temporarily in Testing 1 / 2 (EXPO1109, 11-09 + 11-10, revert after the 11-10 close):** T1
GEN-261021-02 29 longs −3.64R (22 at 09:50; caught COF / SYF in the Move Hunt), GEN-261019-03 / GEN-261026-02 no trade; T2
GEN-261022-07 1 short −1.07R, GEN-261026-03 (M2) no trade. Their R is inside the T1 / T2 totals above.
Give-back (peak → close, journal $): Gen $1,311, GY $695, Primary $213, T2 $153, T1 $65, Ex1 $14, LL 0 — all the short books
grinding against the trend; bursts: 73 setup bursts −137.8R (avg −0.231R vs non-burst −0.051R), 20 with ≥ 75 % stops −144.2R.
**One-big-day checks (records, own account):** GEN-261020-07 126 trades / 6 sessions −0.309R, **w/o today −0.487R** (`1 day`);
CWT12-coil-k4-long 291 / 8 −0.054R, w/o today −0.107R; CWT12-coil-k6-long 116 / 9 −0.002R, w/o today −0.171R (Graveyard-origin);
NS1-FD (T1) 82 / 18 −0.059R, w/o today −0.140R; MF4-FD (P) 106 / 15 −0.378R, w/o best −0.436R; RW3-FD (P) 85 / 16 +0.469R, w/o
best +0.260R (61 %, `1 day`); RW5-FD (P) 100 / 17 +0.352R, w/o best +0.218R (56 %, `1 day`); NM-ETF late dip (LL) 7 / 3
+0.389R, w/o best +0.315R (54 %, `1 day`, low rep). None of today's top setups is a candidate.

**R by day type** (all live sessions, daytype_out.txt; window now 12 quiet / 7 up / 6 down; today up / above):
Primary quiet −0.145 (388), **up −0.199 (358)**, down +0.224 (261); above +10:00 −0.015 / below −0.135. T1 −0.077 / −0.202 /
−0.063; T2 −0.061 / −0.137 / −0.266; GY −0.064 / −0.125 / −0.198; Gen −0.197 / −0.325 / −0.179; Ex1 +0.100 / +0.150 / −0.426
(1 session each); LL −0.061 / +0.468 / −0.076. **Up days are now the worst day type for Primary, T1 and Gen** — the short
books. Live setups positive on both up and down days (≥ 10 each): 10 (Primary MF2-FD +0.196 up / +0.623 down / −0.729 quiet;
RW3-FD +0.187 / +0.885 / −0.122; T1 L3-fromopen +0.204 / +0.198 / +0.268 and MF4-FD +0.100 / +0.356 / +0.345 — T1's MF4-FD
record is not Primary's; T2 RW1-FD +0.312 / +0.383 / +0.069). Both-direction / quiet-day leaders unchanged from 11-06.

**Maximization edits (tested or queued; none live):**
- *Primary:* ECG1 (early compass gate) — **tested, fails** two years (pays only on up-close days); forward shadow L11 + ECG2
  idea. MF1109 (nightly): ETF-skip / UP-confirmed proxy fail. The decisions that matter are on the inbox (DM-MF4 / DM-MF2,
  PV after 11-10).
- *Testing 1:* T1X (nightly DECISION); NS1-FD the day's best (+3.6R) but −0.140R w/o today.
- *Testing 2:* NS4 / exhaustion shorts into the 15:15 high; no new edit.
- *Graveyard:* short book −136R vs longs +59.5R; latch-by-category shadow +23.4R (nightly); burst2-latch4 +10.6R of its +16.6R.
- *Gen:* GEN-261029-08 (SPYgt0p5 overbought short) −38.9R in two bursts — shorting strength on an up day by design; HK-GEN-BP.
- *Explore 1 / Live Lab:* ROLL1 rotation (re-evaluated every ~2 sessions); no verdict.

## 1. Every-trade analysis (trades_bdi.py → per_trade_1109.csv, patterns_1109.csv → patterns.csv +484 loser rows; bursts.py)
- **Exit what-ifs** (966 trades, R after costs, 1-min SIP): live −0.162 / trade; orig −0.131 (live 0.03R worse than the
  bracket on bars: fills), be05 −0.100, t05 −0.075, **t1 −0.037, trail −0.042**, hold −0.123, sar −0.094, reent −0.128, opposite
  −0.004. Primary: sar −8.2R and opposite +12.4R vs live −18.1R; every exit variant ≈ −15..−18R (MF4-FD's MFE median 0.12R:
  nothing to manage). One session; the two-year exit tests of the same families fail (SQZ1, mf_t05; guild BE-replay running).
- **Opposite side, hindsight:** entries with SPY ≥ |0.25 %| against them 430 trades, live −0.516R (opposite +0.376); flag_spy
  picks them today (it is the L6 rule; 11-06 it was the other way round) — the day-type problem again.
- **Loss types** (losers, $): wrong_side_after_big_swing P 5 / −$382, Gen 33 / −$910, GY 31 / −$725, T1 15 / −$254, T2 14 /
  −$166; never_worked GY 65 / −$979, Gen 38 / −$738, P 14 / −$203; gave_back_gains Gen 47 / −$441, GY 36 / −$366.
- **Bursts:** 73 setup bursts, 597 entries, −137.8R; good: GY CWT12-coil-k6 15 longs 10:35-10:42 +15.3R, Gen GEN-261020-07 19
  longs 09:55-09:58 +10.2R; bad: Gen GEN-261029-08 18 + 18 shorts 10:05-10:25 −28.4R, GY MF3-FD / MF5-FD 11 + 11 shorts
  09:55-10:05 −24.3R (all stopped), GY MF1-FD 7 −8.4R, P MF4-FD 7 shorts 10:20-10:25 −8.0R.
- **Stacking** (same symbol / side, ≥ 2 setups, 30 min): P 3 lots +2.4R, GY 260 lots −30.5R, Gen 18 −4.7R, T2 10 +1.0R.

## 2-3. Patterns → testable rules; NEW tested ideas (both pre-registered and committed before their two-year read)
| idea (source) | configs | result | QDAY split | verdict |
|---|---|---|---|---|
| **ECG1** early compass gate on momentum shorts (swing autopsy 11-09) | 1 | TRAIN −464R (t −0.18), VALID +606R (t 0.67), LATE +319R; 12 setups better / 2 worse | up-close +2,472R / quiet −1,360R / down −507R (VALID); above 10:00 +394 / below +212R | fail → forward shadow L11; ECG2 idea |
| **MH1109-P1** in-play × compass side, both directions (Move Hunt) | 1 | n 78,822 / 217 days, avg −0.138R vs base −0.111, precision +2.0 pts, excess t −0.59, 18 % months | long up-close −0.022, short down-close −0.005, quiet −0.22..−0.30 | fail (full, BAR90, light lane) |

**QDAY reading:** both tests repeat 11-06's lesson from the other side — the early compass reading confirms the side most days,
but the money in both directions is decided by the days that *end* quiet or reverse, and neither the compass nor vol_exp knows
that at 10:00. Quiet-day setups: nothing new passed; the only live both-direction / quiet-positive setups remain T1
L3-fromopen, T1 MF4-FD, T2 RW1-FD (live records, not candidates by themselves). **No light-lane passer → no Live Lab
candidate tonight.** Exhausted families (pdl1030*, rdt1030, saturday1031, night1102) not repeated; ROTA1 not started.

## 4. Swarm / configs counted
Configs tonight: ECG1 ×1, MH1109-P1 ×1 = **2** (each scored against its lineage bar: MF short-gate N 34 → 2.66 / BAR90 2.39;
MH N 4 → 1.67 / 1.50). 0 pass. Failures reported above in full. Locked block never read. Backlog +3
(`ecg1-1109-early-compass-momentum-short-gate` parked, `ecg2-1109-strong-up-gate` idea, `mh-1109-inplay-compass-side` parked;
add_backlog.py; BACKLOG.md regenerated). `python -m mcf.research.ledger check` fails in this container before and after
tonight's changes (IndexError: no bar cache for its probe) — no ledger entry was added or changed.

## 5. Decision
None new. Nothing passed; no setup moves. Facts for the pending DM-MF4 / PV cards (after the 11-10 close): an early compass
gate does not rescue the MF short family on two years (it only helps on days that close up), so the case for PV1 (MF shorts out
of Primary) is unchanged by tonight.

Files: accounts.py, swings.py, trades_bdi.py, bursts.py, daytype.py, forward_1109.py, fb1_live.py, mh_p1_live.py, ecg1.py
(+ ECG1_PLAN.md), mh_p1.py (+ MH_PLAN.md), hyp_update.py, add_backlog.py (+ outputs); research/bdi/moves/moves_1109_out.txt,
precursors_1109_out.txt. Scratch inputs under the session scratchpad `mh1109/` (rebuild: research/ops/coverage1029/fetch.py,
research/bdi/moves/fetch5.py, frames_today.py). Educational only — not financial advice.
