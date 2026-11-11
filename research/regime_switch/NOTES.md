# REGSW Phase 1: switching setups on and off by the compass or other market factors (2026-11-11)

*Educational only — not financial advice.* This is research only. No config, setup, exit, ledger or workflow was
changed.

The owner asked on 11-10 at about 21:40 ET for "hard and thorough research into switching setups on/off based on either
the market compass or other factors."
- The study was pre-registered in `PLAN.md`, commit d15326333, before any score was computed.
- Costs are in.
- The locked block 2024-11-01..2025-02-28 was never read. It is filtered at load and asserted.
- **Configurations: 74 main + 25 finalist sensitivities = 99. The bar uses N = 100, so t ≥ 3.03.**

## Plain-English summary
- **Verdict: 0 of 74 switches pass, and none is a near-miss under the pre-registered bar. Nothing should be switched
  live.** Three candidates go to a journal-only forward shadow (below).
- **Why "it improves R" is not enough here.**
  - The two-year lab lists of the 52 target setups lose money as a whole:
    - TRAIN −19,920R
    - VALID −12,133R
    - FWD −1,806R
    - live run-1 trades of the same setups over 26 sessions: −1,413R
  - So switching almost anything off "helps": **62 of 74 configs raise VALID R**.
  - The honest test is the **random-switch baseline**: the same fraction of setup-sessions, the same timing, on random
    days.
    - Only **13 of 74** beat the random *average* in VALID.
    - Only **4** beat its 95th percentile in VALID, and 3 in FWD.
    - Only **GAP-U** (OFF and HALF) beats it in both VALID and FWD.
  - Most of the "gain" in this study is *trading less of a losing list*, not market-regime information.
- **The setups that work live get hurt by switching.** For the five TEAM-6 setups that have a lab list (RW3-FD,
  RW5-FD, L3-fromopen-FD, ST7-FD, NS5), summed over the 37 OFF configs:

  | split | better | worse | net |
  |---|---|---|---|
  | VALID | 63 | 58 | +1,130R |
  | FWD | 42 | 77 | −532R |
  | live | 36 | 80 | −671R |

  The VALID gains come from VALID periods in which these setups' lab lists lost money.
  - The owner's example rule, "shorts off when the compass is UP-confirmed" (CMP-U-OFF), costs L3-fromopen −35R in
    FWD and −32.5R live. This agrees with L3LEASH K01.
- **Best result: GAP-U.**
  - Rule: shorts off when SPY opens more than 0.25% above yesterday's close; longs off when it opens more than 0.25%
    below.
  - VALID +4,617R, t 3.93 (above the bar). That is +1,215R above the random average, and above the random 95th
    percentile.
  - FWD +939R, which is +285R above random.
  - Live +521R, only +58R above random, **below** the live random 95th percentile (611R).
  - Setups better / worse: VALID 46 / 6, FWD 32 / 19, live 34 / 17.
  - Red-day losses cut 31% / green-day R given up 26% (VALID). FWD 39% / 26%, live 33% / 30%.
  - Not carried by one day: VALID best-day share 5%, live 24%.
  - **It fails two criteria:**
    - Criterion 3: 5 setups are worse by more than X in VALID: NM-AR −61R, NS1 −13R, RW1-FD −12R, NS3V1 −8R, ST7-FD −7.5R.
    - Criterion 4: the setup-weighted FWD gain (+26.8) is below its random 95th percentile (+46.7).
  - Its gains come from the CWT / RW2 / exhaustion lists that lose anyway. On the TEAM-6 shorts it is negative in FWD
    (L3-fromopen −3.2R, RW3-FD −11.2R, RW5-FD −7.3R) and flat-to-negative live.
- **Per-setup fingerprints (rule P)** are the only family with consistent selectivity. In each of VALID, FWD and live,
  the switched trades average lower R than the kept trades in most setups:

  | config | VALID setups | FWD setups | live setups | VALID t | gain (VALID / FWD / live) | excess over random (VALID / FWD / live) |
  |---|---|---|---|---|---|---|
  | **IDX3-P** | 15 vs 6 | 11 vs 4 | 11 vs 4 | 2.58 | +1,005 / +158 / +146R | +187 / +75 / +93R |
  | **SPYO-P** | 13 vs 7 | 12 vs 7 | 9 vs 7 | 2.61 | +788 / +132 / +96R | small |

  - IDX3-P switches off a setup's worst "all three indices agree" state.
  - SPYO-P switches off a setup's worst SPY-from-open state. Its t is 2.61 in VALID, 2.44 in FWD and 2.87 live.
  - Both are below t 3.03 and below the VALID random 95th percentile, and both have setups worse by more than X. **No pass.**
  - They switch only 5-7% of trades, so their R impact is small.
- **REGX (the owner's worry about per-setup condition labels): the labels flip. They are not stable.**
  - Across 12 signals, a setup's best state in TRAIN is also its best state in VALID **31%** of the time. Its worst
    state matches **31%** of the time. Chance is **32%**.
  - The mean rank correlation of state means between TRAIN and VALID is **−0.08**.
  - Against live: 38% / 37% vs chance 36%, rank correlation +0.04.
  - **On the whole, a label learned on one year is no better than a coin toss on the next.**
  - The exception is the SPY-from-open label on a few TEAM-6 setups, which is consistent in TRAIN, VALID and live:
    - L3-fromopen: worst when SPY < open.
    - RW3-FD, ST7-FD and NS5: best when SPY < open.
  - This matches top20/CONDITIONS, but it covers 4 setups, not a system. The owner's hesitation on REGX is supported.
- **Other signals, plainly:**
  - **Compass (CMP / CMPL):** fails the random baseline in VALID and FWD, in all three matching rules. It is strong
    on rest-of-day side, but that does not translate into which setups to switch.
  - **Breadth (BRDO / BRDV), VXX, prior-day type, weekday, FOMC days:** nothing beats random.
  - **Sector rotation (SECT-U):** VALID +908R over random, but FWD −256R under random. It flips sign.
  - **Realised volatility (RVOL-U, "quiet days off"):** at random level, about −77R excess.
  - **Self-latch (SELF-U, −1R per setup):** selects worse trades in VALID (switched −0.08 vs kept −0.05R/trade), but is
    below random in R. Live +276R vs random 95th percentile 279R.
  - **Family brake (FSTOP-U, ≥ 3 family stops):** t 5.62, but it switches 63% of trades. It is exactly at random:
    VALID −274R, FWD +4R excess. This is a BRAKE-1 generalisation, and it is *not* supported as a cross-family rule.
- **Not available:**
  - the VIX index and its term structure (VXX, the ETN, was used instead)
  - a CPI calendar (skipped)
  - c30, gate1 and checkpoint on two years (GATE1 already failed its two-year test)
  - at 09:50, breadth uses no bar (the first context bar closes at 09:55), so BRDO/BRDV start at 10:00

## Shadow candidates (journal-only, no trading change)

`research/regime_switch/shadow.py` applies the three frozen rules to every account's run-1 trades of the target setups
and writes `shadow_scoreboard.csv`. Each row is date × config × account with ΔR(OFF), ΔR(HALF) and avg R of switched
vs kept trades.

The backfill rows (in-sample, 10-06..11-10, 26 sessions) reproduce the study's live numbers exactly:

| config | live ΔR (backfill) |
|---|---|
| GAP-U | +520.57R |
| IDX3-P | +145.52R |
| SPYO-P | +96.29R |

Forward rows start at **2026-11-11**.

**Nightly (after 16:05 ET):** `python research/regime_switch/shadow.py --date YYYY-MM-DD`

This uses a read-only 1-min bar GET and `git show` of the journals. **Re-score after 20 forward sessions:**
- Pass rule: ΔR > 0 in total and on TEAM-6.
- The switched trades average lower R than the kept trades in ≥ 60% of affected setups.
- It beats a permutation baseline on the forward days.

Then it is a DECISION only if all three hold.

| candidate | rule | why it is shadowed |
|---|---|---|
| GAP-U | shorts off/half if SPY gap > +0.25%, longs if < −0.25% | best lab result; beats random in VALID and FWD; t 3.93 |
| IDX3-P | per setup: off/half in its worst IDX3 state (fits_P.csv) | consistent selectivity VALID / FWD / live |
| SPYO-P | per setup: off/half in its worst SPY-from-open state | t > 2.4 in VALID, FWD and live; stable label on core setups |

## Rule changes inside the windows (CLAUDE.md 11-02)
- **Lab lists (bt_lab1104):** one fixed rule version per setup (current code), so there is no rule change inside
  TRAIN, VALID or FWD.
- **Live 10-06..11-10:** many changes per research/ledger.jsonl. The switch scales each live trade's own R, so moves
  between accounts do not bias it, but the trade *set* changed with:
  - per-lot stacking: 3 lots/symbol from 10-13, same-setup re-entry from 10-14
  - promotions, demotions and Graveyard moves: 10-15, 10-20..10-22, 10-25..10-27; Graveyard account from 10-21
  - the per-setup loss stop:
    - latching from 10-23
    - **turned off in Testing 1, Testing 2 and Gen from 10-23** (Graveyard keeps −2R)
  - the GX1 5-minute clock gate from 10-27 (lab-gate bug before)
  - Primary position size from 10-28
  - low-rep rotation (Explore 1 / Live Lab) from 11-05
- Live R before and after 10-27 is not like-for-like.
- **TEAM-6 starts 11-11, after the window.**

## Method (as pre-registered)
- **Unit:** setup × session.
- **Switch mechanics:**
  - Decision times are 09:50, 10:00, 10:30, 11:00, 12:00 and 13:00.
  - A trade gets the weight set at the last decision time ≤ its entry (re-evaluated mode).
  - Lab trades start at 09:50.
- **Lab base (B0):**
  - per-setup −2R latch, ≤ 3 lots/symbol, ≤ 30 open
  - ETB E90 proxy on shorts (L3LEASH-2): 74-97% of short trades kept
  - 531,285 base trades: TRAIN 249,672 / VALID 253,142 / FWD 28,471
- **Live:** run-1 trades of the target setups in all 7 journals: 13,224 trades.
  - Primary 860, Testing 1 2,619, Testing 2 4,619, Graveyard 4,943, Gen 183.
  - Live Lab and Explore 1 had no target trades.
- **Targets:** 52 lab-covered setups.
  - TEAM-6 minus NM-ETF, which has no lab list.
  - Plus the 11-10 top-20.
  - Plus every Primary / Testing setup with ≥ 20 live trades (`targets.csv`).
- **Matching rules:**
  - U = fixed direction (don't fight the tape).
  - F = the family's worst state, fit on TRAIN.
  - P = the per-setup worst state, fit on TRAIN with shrinkage k = 100.
  - Fits are in `fits_F.csv`, `fits_P.csv` and `fingerprints_train.csv`.
- **Random baseline:** each setup's day schedules permuted across its own days within the split, 200 draws.
- **"Excess"** = ΔR − the random mean.
- **Setup-weighted R:** each setup's ΔR divided by its TRAIN base trades per day.
- **HALF configs:** exactly half the OFF ΔR, with the same t and the same counts. Only the OFF rows are listed below.
  HALF rows are in `configs.csv`.

Note: in `configs.csv` the `*_red_cut` column is signed so that a negative value means losses were removed (−30.6 = 30.6% of red-day losses cut); `*_green_given` is positive when green-day R is given up.

## All 37 OFF configs (HALF = ½ ΔR, same t / counts)

Fail codes:
- 1: VALID or FWD ≤ 0
- 2: t < 3.03
- 3: < 60% of setups better, or a setup worse by > max(5R, 10% of |base|)
- 4: not above the random 95th percentile in VALID and FWD
- 5: VALID ΔR ≤ 0 without its best day
- 7: live ΔR < 0

Criterion 6 (thresholds ×0.8 / ×1.2) was run only on the 5 finalists; all of them held.

"Switched-trades-worse" = number of setups where the switched trades average below the kept trades, vs above (each side
needs ≥ 10 trades).

| config | sw % VALID | VALID dR (excess vs random, rand95) | t | FWD dR (excess, rand95) | LIVE dR (excess, rand95) | setups better/worse V · F · L (worse > X, V) | switched-trades-worse setups V · F · L | fails |
|---|---|---|---|---|---|---|---|---|
| CMP-U-OFF | 19% | +1421 (-1112, +3095) | 1.12 | +307 (-45, +510) | +504 (+187, +442) | 37/15 · 37/14 · 36/14 (8) | 18/34 · 25/23 · 24/23 | 2,3,4 |
| CMP-F-OFF | 1% | -90 (-112, +94) | -1.58 | +15 (+2, +36) | +20 (+4, +32) | 1/2 · 2/1 · 2/1 (2) | 0/3 · 2/1 · 1/2 | 1,2,3,4,5 |
| CMP-P-OFF | 6% | +277 (-322, +860) | 1.61 | +124 (+29, +184) | +111 (+32, +141) | 14/5 · 14/5 · 13/6 (4) | 7/12 · 10/7 · 8/6 | 2,3,4 |
| CMPL-U-OFF | 40% | +3667 (-1572, +5894) | 1.32 | +686 (-72, +1005) | +785 (+148, +788) | 37/15 · 36/15 · 40/11 (14) | 15/37 · 27/23 · 25/21 | 2,3,4 |
| CMPL-F-OFF | 1% | +28 (-8, +116) | 0.13 | -5 (-15, +44) | -19 (-15, +16) | 6/3 · 3/6 · 2/6 (2) | 3/6 · 3/4 · 0/4 | 1,2,3,4,5,7 |
| CMPL-P-OFF | 2% | +195 (+38, +307) | 0.83 | -16 (-56, +109) | -10 (-51, +80) | 10/9 · 7/12 · 7/12 (5) | 8/11 · 6/12 · 1/8 | 1,2,3,4,7 |
| SPYO-U-OFF | 35% | +3790 (-741, +5099) | 1.85 | +577 (+53, +698) | +682 (+200, +643) | 39/12 · 37/14 · 40/10 (9) | 27/24 · 27/22 · 28/19 | 2,3,4 |
| SPYO-F-OFF | 3% | +280 (-8, +472) | 0.74 | +123 (+47, +149) | +59 (-10, +115) | 6/7 · 10/3 · 10/3 (3) | 7/6 · 9/3 · 6/5 | 2,3,4 |
| SPYO-P-OFF | 5% | +788 (+164, +847) | 2.61 | +132 (+10, +208) | +96 (-18, +175) | 14/6 · 14/6 · 14/6 (4) | 13/7 · 12/7 · 9/7 | 2,3,4 |
| IDX3-U-OFF | 21% | +2708 (-42, +3273) | 1.77 | +259 (+31, +371) | +478 (+235, +377) | 43/8 · 35/16 · 35/14 (7) | 31/20 · 30/17 · 32/14 | 2,3,4 |
| IDX3-F-OFF | 0% | +0 (+0, +0) | nan | +0 (+0, +0) | +0 (+0, +0) | 0/0 · 0/0 · 0/0 (0) | 0/0 · 0/0 · 0/0 | 1,2,3,4,5 |
| IDX3-P-OFF | 6% | +1005 (+187, +1090) | 2.58 | +158 (+75, +160) | +146 (+93, +126) | 17/4 · 16/5 · 14/6 (2) | 15/6 · 11/4 · 11/4 | 2,3,4 |
| GAP-U-OFF | 28% | +4616 (+1215, +3904) | 3.93 | +939 (+285, +853) | +521 (+58, +611) | 46/6 · 32/19 · 34/17 (5) | 38/14 · 28/22 · 21/22 | 3,4 |
| GAP-F-OFF | 2% | +128 (-69, +344) | 0.57 | +84 (-6, +150) | +55 (+6, +91) | 8/2 · 6/4 · 7/3 (2) | 3/7 · 6/3 · 3/4 | 2,3,4 |
| GAP-P-OFF | 4% | +288 (-174, +731) | 0.71 | +196 (+48, +248) | +82 (+35, +140) | 14/7 · 14/7 · 11/10 (6) | 8/13 · 14/6 · 7/8 | 2,3,4 |
| BRDO-U-OFF | 19% | +832 (-1585, +2933) | 0.52 | +208 (-81, +442) | +236 (-50, +411) | 36/16 · 30/21 · 34/17 (10) | 19/33 · 25/23 · 20/26 | 2,3,4 |
| BRDO-F-OFF | 1% | -8 (-107, +197) | -0.13 | +18 (+3, +52) | -7 (-10, +15) | 0/1 · 1/0 · 0/1 (0) | 0/1 · 1/0 · 0/1 | 1,2,3,4,5,7 |
| BRDO-P-OFF | 4% | +433 (+38, +619) | 1.24 | +120 (+28, +179) | +83 (+14, +127) | 10/7 · 10/7 · 9/7 (5) | 6/11 · 11/5 · 5/9 | 2,3,4 |
| BRDV-U-OFF | 20% | +1301 (-1397, +3206) | 0.80 | +171 (-189, +513) | +474 (+94, +524) | 39/13 · 30/21 · 36/14 (10) | 20/32 · 21/28 · 26/20 | 2,3,4 |
| BRDV-F-OFF | 2% | +215 (-9, +380) | 1.47 | +82 (-7, +155) | +69 (+27, +82) | 9/1 · 8/2 · 5/5 (1) | 8/2 · 8/2 · 5/5 | 2,3,4 |
| BRDV-P-OFF | 6% | +401 (-282, +979) | 1.00 | +91 (-53, +259) | +125 (+16, +192) | 19/6 · 15/10 · 14/11 (3) | 12/13 · 14/11 · 10/12 | 2,3,4 |
| VXX-U-OFF | 15% | +1686 (-285, +2390) | 1.26 | +369 (+73, +456) | +410 (+84, +452) | 38/14 · 34/17 · 32/19 (11) | 24/28 · 24/23 · 24/20 | 2,3,4 |
| VXX-F-OFF | 5% | +288 (-28, +571) | 0.82 | +4 (-57, +148) | +73 (+5, +139) | 11/9 · 10/10 · 14/6 (7) | 11/9 · 6/12 · 7/7 | 1,2,3,4 |
| VXX-P-OFF | 7% | +765 (-119, +1255) | 1.61 | +132 (-26, +275) | +151 (-23, +267) | 20/12 · 20/12 · 27/5 (8) | 20/12 · 13/17 · 13/11 | 2,3,4 |
| SECT-U-OFF | 36% | +5473 (+908, +5230) | 2.81 | +392 (-256, +843) | +621 (+150, +618) | 39/12 · 34/18 · 39/12 (10) | 33/18 · 20/31 · 22/26 | 2,3,4 |
| SECT-F-OFF | 2% | +96 (-79, +330) | 0.77 | +17 (-41, +115) | +51 (-9, +97) | 4/6 · 6/4 · 7/3 (5) | 5/5 · 6/4 · 3/5 | 2,3,4 |
| SECT-P-OFF | 5% | +403 (-113, +748) | 0.66 | +13 (-65, +181) | -3 (-64, +123) | 9/10 · 11/8 · 11/8 (9) | 9/10 · 10/9 · 5/10 | 2,3,4,7 |
| RVOL-U-OFF | 24% | +2974 (-77, +3576) | 1.88 | +213 (+12, +323) | +115 (-6, +231) | 35/17 · 34/17 · 32/16 (13) | 24/28 · 24/18 · 13/20 | 2,3,4 |
| RVOL-F-OFF | 0% | -50 (-14, +24) | -1.59 | +9 (+12, +15) | +2 (+3, +13) | 0/3 · 3/0 · 2/0 (2) | 0/3 · 1/1 · 0/0 | 1,2,3,4,5 |
| RVOL-P-OFF | 7% | +356 (-342, +957) | 1.51 | +19 (-77, +196) | +158 (+40, +199) | 12/7 · 11/8 · 13/5 (6) | 10/9 · 8/11 · 10/5 | 2,3,4 |
| PDT-F-OFF | 7% | +583 (-128, +1019) | 1.25 | +92 (+56, +131) | +84 (+7, +161) | 13/4 · 10/7 · 13/4 (3) | 6/11 · 10/7 · 9/8 | 2,3,4 |
| PDT-P-OFF | 6% | +655 (-58, +1081) | 1.46 | +107 (+85, +113) | +113 (+13, +210) | 15/9 · 14/10 · 17/7 (8) | 10/14 · 13/9 · 10/10 | 2,3,4 |
| DOW-F-OFF | 4% | -85 (-468, +639) | -1.78 | -46 (-127, +174) | +12 (-44, +114) | 8/15 · 8/15 · 11/12 (15) | 6/17 · 4/14 · 6/8 | 1,2,3,4,5 |
| DOW-P-OFF | 7% | +515 (-224, +1059) | 0.65 | +21 (-59, +197) | +78 (-1, +187) | 24/12 · 17/18 · 22/12 (11) | 17/19 · 13/17 · 13/13 | 2,3,4 |
| SELF-U-OFF | 6% | +1329 (-1728, +3457) | 2.93 | +90 (-409, +639) | +276 (+94, +279) | 40/10 · 27/21 · 37/9 (2) | 29/21 · 19/19 · 19/16 | 2,3,4 |
| FSTOP-U-OFF | 63% | +7807 (-274, +8468) | 5.62 | +1057 (+4, +1181) | +420 (+87, +429) | 46/4 · 36/13 · 33/11 (1) | 29/13 · 19/19 · 16/20 | 3,4 |
| FOMC-U-OFF | 1% | -6 (-59, +141) | -0.80 | +4 (-10, +41) | +13 (+2, +34) | 20/16 · 11/11 · 13/9 (8) | 18/16 · 0/1 · 1/2 | 1,2,3,4,5 |

## Finalist sensitivities (25 configs, `sensitivity.csv`)

**GAP-U-OFF:**

| variant | VALID | FWD | live |
|---|---|---|---|
| thresholds ×0.8 | +4,947 | +1,047 | +613 |
| thresholds ×1.2 | +4,473 | +782 | +367 |
| sticky | +4,617 | +939 | +521 (same as main) |
| one decision at 10:00 | +3,899 | +736 | +377 |
| one decision at 12:00 | +1,236 | −14 | +10 |

So the gap rule works only when it is applied from the open.

**FSTOP-U:** thresholds 2 or 4 stops give the same picture (VALID t 5.1-5.7), still at random level.

**BRDV-F-HALF:** VALID +88..+223R, FWD +4..+49R, below random.

## REGX label stability (`regx_summary.csv`, `regx_stability.csv`)

Each cell is the share of setups whose TRAIN best (or worst) state is also best (or worst) in VALID or live. A state
needs ≥ 30 VALID / 10 live trades.

| signal | VALID best | VALID worst | chance | ρ VALID | live best | live worst | ρ live |
|---|---|---|---|---|---|---|---|
| CMP | 0.23 | 0.33 | 0.34 | −0.16 | 0.42 | 0.52 | +0.19 |
| CMPL | 0.29 | 0.29 | 0.33 | −0.08 | 0.27 | 0.27 | −0.19 |
| SPYO | 0.39 | 0.39 | 0.33 | +0.02 | 0.50 | 0.35 | −0.03 |
| IDX3 | 0.28 | 0.47 | 0.34 | −0.04 | 0.43 | 0.55 | +0.34 |
| GAP | 0.42 | 0.29 | 0.33 | −0.04 | 0.40 | 0.31 | 0.00 |
| BRDO | 0.29 | 0.21 | 0.34 | −0.21 | 0.38 | 0.31 | 0.00 |
| BRDV | 0.31 | 0.23 | 0.34 | −0.24 | 0.26 | 0.40 | +0.02 |
| VXX | 0.23 | 0.37 | 0.33 | −0.10 | 0.39 | 0.41 | +0.07 |
| SECT | 0.48 | 0.33 | 0.34 | +0.10 | 0.44 | 0.22 | −0.11 |
| RVOL | 0.29 | 0.33 | 0.34 | −0.10 | 0.54 | 0.48 | +0.16 |
| PDT | 0.31 | 0.21 | 0.33 | −0.12 | 0.31 | 0.29 | −0.04 |
| DOW | 0.21 | 0.21 | 0.20 | −0.01 | 0.18 | 0.27 | +0.05 |
| **mean** | **0.31** | **0.31** | **0.32** | **−0.08** | **0.38** | **0.37** | **+0.04** |

IDX3 "worst" (0.47 VALID / 0.55 live vs 0.34) is the one label that beats chance in both. That is why IDX3-P is
shadowed.

## Next steps (optimistic, honest)
1. **Run the shadow** for 20 forward sessions.
2. **The finding that matters most for the north star:** the lab lists of the live-positive setups lose in TRAIN /
   VALID (L3-fromopen, RW3-FD, RW5-FD), so any switch fitted on them learns "trade less".
   - A switch study on *winners* needs a base that wins: the live journals, or lab lists that agree with live.
   - A REGSW-2 on the live record alone (26+ sessions, setup × day, permutation baseline) becomes meaningful at about
     40-60 sessions (XA-EPROC power).
3. **GAP-U as a targeted remedy (Remedies rule):** restrict it to the families where it helped in all of VALID, FWD
   and live (CWT14 / RW2 / exhaustion: the losing lists). This is a "who is switched" question; it needs a new
   pre-registration and is counted in this lineage.

## Files
| file | contents |
|---|---|
| `PLAN.md` | pre-registration |
| `fetch_live.py` | live bars after the cache |
| `base.py` | targets, ETB base, live trades, features |
| `score.py` | all scoring |
| `configs.csv` | every metric per config × split |
| `sensitivity.csv` | finalist sensitivities |
| `per_setup.csv.gz` | ΔR per setup × config × split |
| `fits_F.csv`, `fits_P.csv`, `fingerprints_train.csv` | TRAIN fits |
| `regx_*.csv` | label stability |
| `score_out.txt` | full output |
| `shadow.py`, `shadow_scoreboard.csv` | forward shadow |
| `targets.csv` | target setups |

Educational only — not financial advice.
