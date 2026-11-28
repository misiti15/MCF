# Track 3: long edge. Which conditions carry positive R for long trades?

Educational only — not financial advice.

**Data.** Live: all 10 journals, run 1, closed lots from 10-23 to 11-27, with LR8 R after costs. Identical signals are counted once.
- **Universe A:** Primary plus the 8 arena accounts, Graveyard excluded. 8,695 long lots, 25 sessions.
- **Universe B:** Graveyard longs, 6,459 lots. Different setups, used as a replication set.

Stock gap, prior-day and 5-day returns, and ATR% come from Alpaca daily bars (GET only). SPY context at the entry minute comes from SPY minute bars.

**History.** 1.93M generic long entries built from the minute caches:
- entries at 10:30, 12:00 and 13:30 at the bar's open;
- GEN geometry: stop at 0.25 daily ATR, trail of 1R once the trade is up 1R, flat at 15:55;
- adv20 ≥ $20M, price ≥ $5;
- LIVE-L costs (primshorts_1126 cells_live.json).

The splits are FIT (report only), CHECK 2025-10-01..2026-11-04 and T2 2023-01-03..2024-09-13. The locked block 2024-11-01..2025-02-28 was filtered at load and asserted absent, using the upday_1127 loader.

**Configs tried in this track: about 102.**
- The live condition scan has 16 dimensions and about 90 cells. It is descriptive, but it is counted.
- There are 6 pre-declared live filters.
- There are 6 history tests: 3 features × 2 subsets.

Cumulative N goes from about 9,363 to about 9,465 for this track alone; other tracks tonight add their own counts. Bars: lineage t ≥ about 4.3; study bar paired t ≥ 2.5 on both CHECK and T2.

Scripts and outputs are in `exploration/sandbox/long_edge/`:
- `daily_fetch.py`, `feat.py`
- `cells.py` → cells_out.txt
- `setups.py` → setups_out.txt
- `combos.py` → combos_out.txt
- `f1_detail.py` → f1_detail_out.txt
- `hist_build.py`, `hist_score.py` → hist_out.txt

**Rule changes inside the 10-23..11-27 window (ledger). Every number below spans them.**
- **10-23:** ST-A, no per-setup daily stop in Testing / Gen. The arena had no latch all window.
- **10-28:** Primary size about $4k.
- **10-29:** Primary −2R latch, counting closed R.
- **10-30:** testing cost filter.
- **11-11:** TEAM-6 lineup.
- **11-12:** LR8 costs and account restructure; half-day flatten 12:55.
- **11-17:** TSZ1, half lots with 2x slots in testing. R per lot is comparable across the date; lots per day are not.
- **11-19:** Epoch 1, C3-EXIT100, U9-TGT.
- **11-20:** stop rounding, FOOTRACE-EXIT.
- **11-21:** cost-basis fix.
- **11-23:** ST7 out of Primary, BRAKE-BURST, PSHADOW.
- **11-27:** GYH V1+V3, ROT-B3, GEN seed.
- **Next, 11-30:** AV50 / ETF-STOP50 for NM-ETF in Primary, and the Friday-review moves.

---

## 1. Headline numbers

| | Lots | R (LR8) | Avg R / lot | Gross / lot | Note |
|---|---|---|---|---|---|
| Live longs, A (no Graveyard) | 8,695 | **−1,408R** | **−0.162** | −0.118 | 25 sessions |
| Live longs, B (Graveyard) | 6,459 | −1,022R | −0.158 | −0.106 | |
| A on **SPY down days** (open→close ≤ −0.3%, 9 days) | 3,653 | **−1,090R** | −0.298 | −0.253 | **77% of all long loss** |
| A on SPY flat days (8) | 2,708 | −242R | −0.089 | −0.044 | |
| A on **SPY up days** (8) | 2,334 | −76R | **−0.033** | **+0.007** | Without 11-25: −0.115 |
| History, generic longs, CHECK | 928,806 | | −0.156 | −0.018 | cost 0.137 |
| History, generic longs, T2 | 520,139 | | −0.124 | +0.031 | cost 0.156 |

**What this means.**
- **Longs have no gross edge either.** Even on SPY up days the average live long is about zero before costs (+0.007R).
- Generic history longs are −0.02 to +0.03R gross, against 0.14-0.16R of cost.
- The long problem mirrors the short problem. Shorts give it back on up and squeeze days; longs give it back on down days (−0.298R per lot). Neither side earns on its "good" days.

## 2. Conditions: is any cell positive after costs? (Universe A; full table in cells_out.txt)

Fifteen pre-trade dimensions were scanned: time, SPY gap, SPY at entry, stock gap, stock move from the open in ATR, relative strength versus SPY, ETF/stock, price, ATR%, prior-day return, 5-day return, stop bp, stop in spreads, family and exit style. Hold length and SPY day type were also looked at, but they are known only after the fact.

**No pre-trade cell with ≥ 300 lots is positive after costs.** The only positive cells are:
- stocks already up more than 1 ATR from the open at entry: n 141, +0.025R, w/o best day −1.2R;
- lots held more than 180 minutes: +0.055R. This is an outcome, not a condition.

The "within-day control" column below compares each cell with random long lots drawn from the same days in the same counts. It separates "a better kind of long" from "it happened to trade on good days".

| Condition (A) | Lots | Avg R | Without 11-25 | Within-day control pct | Setups (≥ 10 lots) positive | Graveyard (B) avg R |
|---|---|---|---|---|---|---|
| All longs (base) | 8,695 | −0.162 | −0.190 | — | — | −0.158 |
| Stop ≥ 200 bp | 2,698 | −0.085 | −0.110 | **100** | 17/52 | −0.103 |
| Stop ≥ 12 spreads (12-25 / > 25) | 2,717 / 2,763 | −0.111 / −0.109 | −0.134 / −0.140 | **100 / 100** | 13/54, 11/56 | −0.180 / −0.109 |
| Stop < 6 spreads | 781 | **−0.319** | −0.337 | **0** | 2/22 | −0.201 |
| Prior day +1..+3% / > +3% | 1,070 / 1,345 | −0.063 / −0.094 | −0.081 / −0.070 | **100 / 99.6** | 12/30, 18/44 | −0.077 / −0.074 |
| Prior day −3..−1% | 1,956 | −0.242 | −0.274 | 0 | 6/44 | −0.221 |
| 5-day > +8% | 904 | −0.034 | −0.005 | 99.4 | 8/26 | −0.054 |
| ATR > 6% | 3,127 | −0.126 | −0.151 | 99.3 | 15/64 | −0.137 |
| Inverse / volatility ETFs (long = short the market) | 554 | −0.024 | **+0.132** | 84 | 10/16 | −0.089 |
| Long-bias ETFs vs stocks | 2,000 / 6,141 | −0.169 / −0.172 | −0.214 / −0.203 | 95 / 2 | | −0.166 / −0.160 |
| Entry 09:30-10:00 / 12:30-14:00 | 705 / 1,405 | −0.102 / −0.153 | −0.124 / −0.174 | 90 / 12 | | −0.350 / −0.026 |
| Entry 11:30-12:30 | 1,417 | **−0.240** | −0.332 | 3 | 2/28 | −0.222 |
| Stock gap < −3% / +1..+3% | 1,247 / 1,112 | −0.062 / −0.130 | −0.168 / −0.129 | 100 / 99.95 | 17/31, 14/36 | +0.100 (11-25 carried) / −0.126 |
| Price band (any) | | −0.128 to −0.174 | | 21-80 | | −0.13 to −0.17 |

Two features beat the within-day control in **both** live universes:
1. **Wide stops in spreads or bp.** This is the cost effect already known from SPREADFLOOR and STOPFLOOR. History confirms it is cost, not edge. In all 3 splits gross R is flat across stop widths, while cost falls from 0.20R (< 50 bp) to 0.08R (> 200 bp). Net: CHECK −0.228 → −0.105, T2 −0.159 → −0.069.
2. **Prior-day or 5-day strength** (the stock was up yesterday or over the last week). Live lift is about +0.08 to +0.10R per lot. **History does not confirm it** (section 4).

**Price band, ETF vs stock and time of day** show no long edge anywhere. No window is positive. 11:30-12:30 is the worst (−0.240), and 12:30-14:00 is the least bad in the Graveyard.

## 3. The best live longs: real edge or one big day?

44 long setups in A have ≥ 50 live lots:
- **5** are positive in total;
- **2** are positive without their best day;
- **2** are positive without 11-25.

| Setup (account) | Lots / days | R | Avg R | R w/o best day | Best day (share) | 11-25 R | Green days / weeks | Avg R 1st / 2nd half |
|---|---|---|---|---|---|---|---|---|
| **GEN-261020-09 … MID-QQQltm0p3-holdtr-long** (Gen) | 259 / 12 | +76.0 | +0.293 | **+3.4** | 11-13 (96%) `1 day` | +6.1 | 6/12, 3/5 | −0.006 / +0.411 |
| GEN-261023-07 … LUNCH-hold-long (Gen, Testing 2) | 139 / 11 | +63.9 | +0.460 | **−27.0** | 11-25 (142%) `1 day` | +90.8 | 5/11, 2/6 | −0.094 / +0.553 |
| GEN-261027-10 … LUNCH-holdtr-long (Gen, Testing D) | 176 / 6 | +25.8 | +0.146 | **−31.9** | 11-25 (224%) `1 day` | +57.7 | 3/6, 2/4 | −0.597 / +0.293 |
| **CWT14-failbrk-orl-p10-long-WB5** (Testing D) | 148 / 7 | +11.2 | +0.076 | **+2.7** | 11-18 (76%) `1 day` | +3.3 | 4/7, 2/2 | — / +0.076 |
| NM-AR-AM-gapdown-capitulation-long (Testing 2) | 92 / 18 | +2.1 | +0.023 | −8.6 | 11-24 (502%) | +2.7 | 8/18, 1/5 | −0.385 / +0.263 |
| ULT-05-withgap-cont-long (Testing E) | 467 / 5 | −11.7 | −0.025 | −19.5 | — | −3.3 | 3/5, 1/2 | — / −0.025 |
| NM-ETF-late-dip-di-long (Primary) | 35 / 9 | −8.1 | −0.230 | −13.4 | — | | | (AV50 from 11-30) |

- **The "big" GEN long records are one-day records.** GEN-261023-07 and GEN-261027-10 are negative without 11-25. That one V-day reversal gave +148.5R between them.
- **The two survivors are GEN-261020-09 and CWT14-WB5.** Without the best day they are worth about +0.01 to +0.02R per lot, which is break-even. Day t is 0.96 and 1.15.
- **GEN-261020-09** makes its money buying mid-morning dips while SPY is weak:
  - entries 10:30-11:30: +0.49R per lot (194 lots);
  - later entries: −0.28;
  - SPY below −0.5% from the open at entry: +0.35 (191 lots);
  - held more than 180 minutes: +0.64 (168 lots).
- **CWT14-WB5** is flat across conditions (+0.10 on down days, +0.11 on up days). It is the only long that looks "even", but it has only 7 sessions.
- **ULT-05** is the largest-sample long (467 lots). It sits at −0.025R, −0.015R gross: no edge, no damage.
- **Exit style (A, descriptive):** holdtr −0.111, hold −0.167, fixed target −0.250 R/lot. In the Graveyard, holdtr has only 35 lots. Long trades that are left to run lose least. This is consistent with "holding beats cutting" in prior research.

## 4. Pre-declared combination filters, and the history check

Live filters (combos.py; written after the cell scan, before these were scored). A random within-day control and a per-setup count are included.

| Filter | A lots (share) | A avg R | Halves | w/o 11-25 | Control pct (p95) | Setups up / down (median Δ) | B avg R | B setups up / down |
|---|---|---|---|---|---|---|---|---|
| **F1 prior day > +1% & stop ≥ 12 spreads** | 1,526 (18%) | **+0.003** | +0.007 / −0.001 | +0.023 | 100 (−0.105) | **40/17** (+0.103) | −0.061 | 14/6 |
| F2 5-day > +3% & ≥ 12 spreads | 1,245 (14%) | −0.032 | −0.117 / +0.070 | −0.006 | 100 | 39/19 | −0.057 | 12/7 |
| F3 prior day > +1% & stop ≥ 200 bp | 824 (9%) | −0.009 | | +0.015 | 100 | 29/13 | −0.004 | 11/6 |
| F4 (prior > +1% or 5-day > +3%) & ≥ 12 spreads | 2,176 (25%) | −0.016 | | −0.002 | 100 | 49/16 | −0.068 | 15/5 |
| F5 ≥ 12 spreads only | 5,486 (63%) | −0.110 | | | 100 | 52/18 | −0.150 | 19/9 |
| F6 prior day > +1% only | 2,415 (28%) | −0.080 | | | 100 | 47/20 | −0.076 | 14/8 |

F1 looks good on paper: break-even, better than random within the day, 40 setups up against 17 down, and replicated in the Graveyard. **But the detail weakens it** (f1_detail_out.txt):
- **Most of F1's lift is on SPY down days:** −0.338 → +0.024, 400 lots. On up days F1 is *worse* than the rest (−0.046 vs −0.028).
- **In the latest week (11-23..11-27), F1 lost** (−0.077 vs +0.118 for the rest).
- **+41.8R of F1's R comes from inverse / volatility ETFs** (249 lots, +0.168). Long SQQQ, SOXS or UVXY that were up yesterday is a short-market bet. **Single stocks under F1 average −0.035R.**

**The history check does not support the strength feature** (hist_out.txt). This compares generic longs, same day and same entry time, strong-prior names against the rest, with paired lift and day-clustered t.

| Test | FIT lift (t) | CHECK lift (t) | T2 lift (t) |
|---|---|---|---|
| H1 prior day > +1% | −0.025 (−1.35) | +0.022 (+1.57) | −0.015 (−1.03) |
| H2 5-day > +3% | −0.026 (−1.41) | +0.034 (+2.55) | +0.017 (+1.31) |
| H3 either | −0.029 (−1.88) | +0.029 (+2.32) | +0.002 (+0.15) |
| H1 within stop ≥ 100 bp | −0.043 (−2.01) | +0.001 (+0.09) | −0.022 (−1.10) |

- No test reaches t 2.5 on both CHECK and T2. FIT goes the wrong way in all four.
- H1 by year: 2025 +0.047, 2026 +0.014, 2023 −0.026, 2024 +0.001.
- The opposite bucket, prior day below −3% (the bounce), is the least bad in history in all 3 splits (FIT +0.038, CHECK −0.095, T2 −0.082, versus about −0.12 to −0.19 for the rest). Live, it is among the worst (−0.209 / −0.229). So the prior-day sign itself flips between regimes.
- **Verdict on F1:** the stop-width part is real but known (it is a cost effect). The strength part is a 5-week regime effect, mixed with inverse-ETF down-day exposure. It is **not a durable long edge**.

## 5. Answer to the question, and a challenge to "longs need focus"

1. **No condition makes intraday single-stock longs positive after costs.** That holds live (all 15 pre-trade dimensions, both universes) and in history (generic longs −0.12 to −0.16R net, gross about 0). Longs lose about as much per lot as shorts (−0.162 vs −0.191 outside the Graveyard). "Longs need focus" is right as a diagnosis, but "find the long edge" has the same answer as for shorts: **the gross edge is about 0 and costs are 0.10-0.15R**.
2. **Where long R actually goes:**
   - **77% of long loss is on SPY down days** (−1,090R).
   - **Long R lives in V-day reversals.** GEN-261023-07 and GEN-261027-10 made +148.5R on 11-25 and are negative on every other day combined.
   - The gentlest longs are wide-stop, left-to-run lots (holdtr, more than 12 spreads).
3. **The real, non-one-day part is small:** about +6R in total across two setups (GEN-261020-09 +3.4R and CWT14-WB5 +2.7R without their best day), or about +0.01-0.02R per lot.
4. **Amplifying it:**
   - More size does not help. TSZ1 already makes R per lot size-invariant, and SZ-PROOF failed.
   - Adding a long to Primary is settled as a fail (LONGBOOK 0/8).
   - The honest move is **more forward sessions on the two survivors**, scored with the one-big-day rule, plus **logging only** for the stop-width/strength tag. Both already trade in Gen / Testing D, so no assignment move is needed.

## Confidence

- **HIGH** that there is no broad long condition that is positive after costs. There are 8,695 + 6,459 live lots, and 1.45M out-of-sample history lots point the same way. The sign agrees with LONGBOOK (0/8), UPDAY (0/16) and 10+ earlier long hunts.
- **MEDIUM** that the wide-stop lift is real. It is a cost effect, confirmed in 3/3 history splits, and it is already being logged by SPREADFLOOR from 11-30.
- **LOW** for the strength feature (F1). The history is mixed, and its live lift is down-day and inverse-ETF driven.
- **LOW** for the two surviving setups. Each has 7-12 sessions, with day t near 1.0 and a best-day share of 76-96%.

---

## PROPOSALS (subject to the owner's approval)

### P1: LONG-SURVIVORS forward scoreboard (score-only; can START Mon 11-30)
- **What:** pre-register now, then score GEN-261020-09 (Gen) and CWT14-failbrk-orl-p10-long-WB5 (Testing D) on their own live lots from 11-30 to 12-28 (20 sessions). There are no setup, exit, size or assignment changes. They already trade where they are.
- **Baseline:** each setup's own average R over the same sessions against (a) zero and (b) a within-day random draw of all non-Graveyard long lots, in the same per-day counts, 2,000 draws.
- **Success, per setup, all of these:**
  - avg R w/o best day > +0.05 R/lot (LR8);
  - best-day share < 35%;
  - day-clustered t ≥ 2.0;
  - above the random control's 95th percentile;
  - at least 11 of 20 sessions traded.
- **Fail:** avg R w/o best day ≤ 0. The setup then follows the normal low-rep rotation.
- **Expected effect on weekly R:** 0 on Primary (scoring only). In the arena, the current rate without the best day is about +1 to +2R a week for the pair, with a 95% band of about −8 to +10R. If a setup passes, it becomes the first long with a non-one-day record, and only then could a Primary card be written (Friday epoch, outside 09:30-16:00).
- **Risk:** none operationally (read-only scoring). The statistical risk is a false pass after about 9,465 tries. The success bar requires forward data only, so in-sample selection does not count toward the pass.
- **Starts Monday without touching Primary rules: YES.**

### P2: LONG-F1 tag in the forward log (score-only; can START Mon 11-30)
- **What:** compute, for every non-Graveyard long lot from 11-30, the F1 tag (prior-day close > +1% & stop ≥ 12 spreads). It uses the same daily bars and the spread_bps already in each lot's meta. It sits next to the SPREADFLOOR shadow, which logs from 11-30. There is no order impact.
- **Baseline:** untagged long lots on the same days, within-day random control, and a split by stock vs inverse/vol ETF.
- **Success at 20 sessions, all of these:**
  - F1 single-stock lots avg R > 0 after LR8;
  - above the control's p95;
  - setups up / down ≥ 2:1;
  - lift present on SPY up days and on non-down days (not only down days).
- **Expected effect on weekly R:** 0 now. If it passes, filtering arena longs to F1 would cut about 82% of long lots. On the live record that is about +56R per day across the 9 non-Graveyard accounts (−1,408R → about +5R over 25 days). **Most of that is plain exposure removal, and history says the strength part is unlikely to hold.** The prior chance of passing is about 20-25%.
- **Risk:** none (logging). It must not be read as a filter until it passes. Applying it early would be "trade less", which the research already shows is no better than a size cut.
- **Starts Monday: YES**, as a nightly score from journals. It needs no code in the trading path.

### P3: Redirect long research to "left-to-run" exits on the existing longs (backlog; NOT a Monday start)
- **What:** a pre-registered bench test (E4 / bench10, LIVE-L with a spread term) of holdtr-style exits on the existing non-GEN longs (CWT14, NS, ST, NM). Live: holdtr −0.111 vs fixed target −0.250 R/lot. Lots held more than 180 minutes are the only positive bucket.
- **Expected effect:** +0.03 to +0.08R per long lot if the live gap carries over. Uncertainty is high: hold length is an outcome, and "holding beats cutting" is already known for the stop side.
- **Duration:** one research night on the bench, then forward in one testing account for 20 sessions.
- **Risk:** it is an exit change, so it goes through the backlog gates and can be merged only outside 09:30-16:00. It does not touch Primary.
- **Starts Monday: NO** (research first).

Educational only — not financial advice.
