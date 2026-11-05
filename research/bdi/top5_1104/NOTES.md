# Top-20 conditions + top-5 execution tune, 2026-11-04 (fifteenth run): FAILED the Testing bar, 0 of 90; 21 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. **History** numbers are **backtests** on
  the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN (<= 2025-12) and VALID
  (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**; no holdout was scored
  because nothing reached the Testing bar.
- **Data:** the 2-year lab frames were missing at the start of the night. The BDI daily agent rebuilt them
  (`research/bdi/1104/DATA.md`, frames now to 2026-11-04); this run used them through `research/history2y/lib.py`.
  The extra ~19 sessions are all HOLD and were dropped, so TRAIN / VALID are the same windows as earlier runs.
- **Configurations scored tonight: 95.** That is 90 execution variants (Part B, 18 per setup x 5, pre-declared in
  `PLAN.md` before any row was scored) plus 5 half-size checks (Part A, `research/bdi/top20/sizing_check.py`). Part A's
  bucket reads are descriptive and tune nothing: 10 dimensions x 20 setups live, 10 setups on two years in full and 2
  more on a partial two-year list.
- **Result: 0 variants meet the Testing bar. There is no DECISION, no Testing proposal and no Primary change.**
  - 21 variants beat their parent; every one still loses in TRAIN or VALID, or in SPY-up sessions, or is far below
    BAR90.
  - 0 of 5 sizing checks clears max(1.5, sqrt(2 ln 5)) = 1.79 in both TRAIN and VALID; 4 of 5 hurt in VALID.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00007R, 100% within 0.01R).
  - MF2-FD (t1s05) needed a units fix. The gates1021 cache stores R in 0.25-ATR units, and MF2-FD's stop is 0.5 unit,
    so its cache R is half of R per unit of risk. Tonight's report divides cache R and the random control by the stop
    multiple.
  - Consequence: **MF2-FD's two-year parent is -0.117R, not the -0.058R in 11-03's CONDITIONS row.** The sign was right
    and the size was understated by half. NS4-pm (also t1s05) is fixed the same way in `conditions_2y.py`.
- config/, mcf/, docs/live/ and the workflows are untouched.
  - 27 lines were appended to research/backlog.jsonl: 5 grid lines (parked), 21 beat-parent lines (rework, tag
    `top5-tune`) and 1 Part A sizing line (parked, tag `top20-conditions`).
  - research/BACKLOG.md was not re-rendered, because it is outside this run's commit scope.

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-04:* the 11-03 list applies, plus these:
  - RW3S-FD added to Testing 2 (11-03)
  - MF3-FD / MF5-FD -> Graveyard (11-03)
  - NS5-FD / ST4-FD / RW6G1-FD -> Graveyard (11-04)
  - UNI1 top-500 pool in Testing 2 (11-04)
  - Earlier in the window: per-lot stacking (10-13), refire B (10-14), RW5/RW3-FD promoted (10-15), MF2/MF4-FD
    promoted (10-20), twin cap and -2R setup stop (10-20), Testing setup stop off (10-23), GX1 5-minute clock (10-27),
    Primary ~$4k (10-28), Primary -2R per setup (10-29), CF in Testing 1/2 (10-30), L3 pair -> Primary (10-30).
- *Part B live window, 10-29..11-04:* see PLAN.md section 1.
  - Every Primary trade in it ran at ~$4k with the -2R setup stop.
  - Testing 1 / 2 ran with CF throughout.
  - Testing 2 ran with the UNI1 pool on 11-04 only.
- *After the windows:* ROLL1 Explore 1 / Live Lab low-rep homes start 11-05.
- Live figures mix these regimes.

## Failures first
| setup (acct) | beat parent | parent TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|
| `RW7-gapdn-bounce-early-short-FD` (T1) | 7 | -0.083 / -0.035 (-3.09) | G16 CF: +0.040 (7.09) | -0.051 / -0.005 |
| `L3-gap-slope-fromopen-FD` (P+T1) | 1 | -0.023 / -0.006 (-0.29) | G16 CF: +0.061 (4.00) | **+0.080 / +0.015** |
| `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` (P) | 5 | -0.054 / -0.078 (-2.42) | G16 CF: +0.047 (4.16) | -0.010 / -0.040 |
| `RW3-gapdn-rsi5pop-flowsell-short-FD` (P) | 6 | -0.095 / -0.041 (-3.32) | G16 CF: +0.045 (5.45) | -0.061 / -0.005 |
| `MF2-open-rsimidhi-flowsell-FD` (P) | 2 | -0.055 / -0.194 (-2.55) | G16 CF: +0.106 (4.82) | +0.082 / -0.131 |

- **The CF cost filter is the best knob on all 5 setups**, as it was on all 5 on 11-03. It keeps 61-81% of trades.
  - **L3-fromopen-FD + CF is the closest call of the series.** It is positive in TRAIN (+0.080), VALID (+0.015), up
    sessions (+0.025) and down sessions (+0.121), with WF 65% and +0.075R vs random.
  - It still fails, because its TRAIN+VALID t is 0.95 against a BAR90 of 4.50, and its avg R without its best day is
    only +0.004R.
  - CF already runs on L3-fromopen's Testing 1 copy (since 10-30). The Primary copy has no CF. That would be an owner
    call on Primary and is not proposed here (backlog line `top5-1104-L3-gap-slope-fromopen-FD-G16-cf_stopcost_le0.15`).
- **Wider stops at the same $ (G01 / G02)** beat the parent on RW7-FD, RW5-FD and RW3-FD (t 2.68-4.05). This matches
  every top-5 run since 10-22, and every one of these rows still loses in TRAIN.
  - On L3-fromopen they are positive in both splits (G02 +0.017R), but they do not beat the parent at the bar (t 1.34 /
    2.05).
- **SPY-side filter (G14, shorts skip SPY above its open)** beats the parent on RW7-FD (3.50), RW3-FD (3.11) and RW5-FD
  (2.85).
  - That is the live loser cluster read the right way round. RW3-FD with SPY above its open at entry holds 65% of
    losing R in the window; MF2-FD holds 73%.
  - All three stay below zero in both splits, so this is a sizing / on-deck idea at most (11-03's sizing line already
    holds it).
- **L3-fromopen after 13:00 (G12)** is +0.092R (TRAIN +0.063 / VALID +0.152, t 0.76), but it beats the parent only at
  t 1.58. Two years agrees with itself: 14:00+ is +0.130R.
  - Live in this window it lost after 13:00 (-1.03 / -0.33R on 9 trades). This is the same disagreement as 11-03.
- **G18 (new: skip price >= $150, from tonight's L3-fromopen live bucket)** beats no parent (t -1.39..1.01) and lowers
  avg R per trade on all 5 on two years (L3-fromopen -0.017 -> -0.044R). The live bucket does not carry over.
- No-op / empty rows: G13 is a no-op on L3-fromopen-FD (its signals never fire with the stock down > 2% from the
  open). It is counted.

**Recurring live loser patterns tested (Part B):**
- **SPY above its open at entry** (RW3-FD 65% of losing R, MF2-FD 73%, RW5-FD 43% in the window): G14 beats the parent
  on 3 of 5. MF2-FD is the exception (t 1.42) and L3-fromopen is worse (-0.22). Nothing turns positive.
- **Midday index turn** (11-04: MF2-FD 8 trades -5.96R; nightly1104's cluster-brake idea): none of tonight's one-knob
  rows addresses it. The backlog line `nightly-1104-midday-index-turn-short-cluster` stays as filed.
- **Give-back** (live losers gave back 1.1-1.4R from their best on all 5). G05 (half off + BE) raises the win rate
  11-14 points and beats no parent (best t 1.01 on RW3-FD).
- **Never-worked losers** (live: RW3-FD 6 of 13, L3-fromopen 7 of 16). G07 (60-min time stop) is flat on all 5 (t
  -0.97..1.48).

## Part A - top-20 conditions deep dive (`research/bdi/top20/`, table `CONDITIONS.md`)
- **Top 20** = the leaderboard order (shrunk avg R, >= 20 trades, all accounts incl. Primary and Graveyard, GEN out).
  - All 20 were read live (10-06..11-04, 12,360 trades loaded; counts match the dashboard within 0-10 per setup).
  - Tonight's deep set **skips the 12 done on 11-03**. It is ranks 12-18 and 20: MF4, RW7-FD, MF4-FD, NS4-pm, MF3,
    CWT13-z075-short (new to the top 20), exhaustion_short and CWT14-p10-lowvol.
  - The 4 top-5 setups (ranks 1-4) were re-read on two years through Part B's cache.
  - CWT13-z075-short and CWT14-p10-lowvol are not in the gates1021 harness. Their two-year read comes from the BDI 1104
    lab trade lists, which had 11 of 22 months built at read time, so it is partial.
- **Shared caveat on the top 3 (unchanged):** their live R is mostly market and mostly 10-22.
  - MF2-FD +0.55R falls to +0.19R ex-market; 72% of its R is on 10-22.
  - RW5-FD +0.36R falls to +0.11R; 44% on 10-22.
  - RW3-FD +0.34R falls to +0.12R; 73% on 10-22.
  - On two years all three lose (-0.117 / -0.063 / -0.076R), and they lose most in SPY-up sessions (-0.37 / -0.30 /
    -0.28R).
  - In the last 5 sessions RW3-FD (-0.29R, n 20) and MF2-FD (-0.42R, n 16) were negative; RW5-FD was +0.21R, but -0.55R
    without 11-03.
- **"Thrives / struggles" for tonight's deep 8 (point-in-time only):**
  - MF4 (base, P): thrives with SPY below its open at entry (+0.33R, n 9). Struggles at ATR% 2-3.5 (-0.22R, n 8). 2y
    -0.119R and positive in no bucket: a down-tape bet.
  - RW7-FD (T1): thrives on ETFs (+0.20R, n 63) and ADV >= $1B (+0.21R). Struggles with SPY flat at 10:00 (-0.10R, n
    149, 54% of losing R). On 2y the worst is SPY above its open at entry (-0.114R, both splits), and SPY flat is the
    least bad, so live and 2y disagree.
  - MF4-FD (P): thrives with SPY below its open at entry (+0.33R). Struggles with SPY flat at entry (-0.31R, n 16); 2y
    worst is ATR% < 2 (-0.145R, both splits).
  - NS4-pm (T2): thrives at ATR% 3.5-5 (+0.87R, n 6). Struggles at ATR% 2-3.5 (-1.10R, n 7, 61% of losing R); 2y gap
    +1..+3% is -0.31R.
  - MF3 (base): thrives with SPY above its open at 10:00 (+0.36R, n 12). Struggles 09:50-10:30 (-0.36R, n 17); 2y ETFs
    -0.15R.
  - CWT13-z075-short (T2): thrives on gap +1..+3% (+0.79R, n 9). Struggles on gap -1..+1% (-0.73R) and 14:00+. Partial 2y
    -0.087R, best 11:30-13:00.
  - exhaustion_short (T1): thrives with SPY flat at 10:00 (+0.14R, n 48). Struggles with SPY below its open at 10:00
    (-0.31R, n 24). 2y is +0.004R (TRAIN -0.053 / VALID +0.105), and leveraged ETFs are the best 2y bucket.
  - CWT14-p10-lowvol (T2): thrives at price $20-50 (+0.11R, n 75). Struggles at ATR% 3.5-5 (-0.23R); partial 2y -0.088R
    with no rescuing bucket.
- **Filters:** none passes the strangling rule and also holds on two years.
  - The most consistent two-year loser bucket is again **price < $20** (8 of 10 setups lose there in TRAIN and VALID).
  - L3-fromopen skip < $20 is +0.068R on 2y, keeping 72% / 98%, but live it is the opposite. It is a cost proxy that
    overlaps CF, and it is not proposed (as on 11-03).
- **Sizing (on deck, 5 checks, half size in the live struggle condition):** none clears 1.79 in both splits.
  - MF4-FD, SPY flat at entry: TRAIN t +0.39 / VALID -1.72 / live +1.69
  - RW7-FD, SPY flat at 10:00: +0.41 / -1.77 / +1.77
  - NS4-pm, ATR% 2-3.5: +1.30 / +0.28 / +2.59 (the only direction-consistent one)
  - MF3, 09:50-10:30: +0.89 / -1.08 / +2.30
  - exhaustion_short, SPY below at 10:00: +1.09 / -1.23 / +0.90
  - Takeaway: live loser clusters on 20-90 trades do not survive two years; the SPY-side reads (G14) do better.

## Selection (Part B)
Live paper trades 10-29..11-04 (run_id 1; S6 and GEN-* out; `live_rank.csv`). The exclusions are in PLAN.md section 1.
Tonight's 5 were last tuned 10-26..10-29:
- RW7-FD: 63 trades (last tuned swarm15_1029)
- L3-fromopen-FD: 49 (swarm15_1029)
- RW5-FD: 26 (p1_1029)
- RW3-FD: 20 (p1_1029)
- MF2-FD: 16 (p1_1029)

CWT05-flush-m05-v3-long (16) tied with MF2-FD but is not covered by the harness.

## 1. Live (paper) vs backtest
| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day | bt win / BE win / exp | bt w/o best day | bt vs random | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|---|
| RW7-FD | 63 | 66.7 / 49.5% | +0.82 / -0.81 | +0.279 | +0.195 (10-30 = 60%) | 48.7 / 52.7% / -0.065 | -0.070 | +0.016 | 6 of 21 |
| L3-fromopen-FD | 49 | 67.3 / 50.8% | +0.90 / -0.93 | +0.303 | -0.028 (10-29 = 102%) | 54.1 / 55.0% / -0.017 | -0.053 | +0.009 | 7 of 16 |
| RW5-FD | 26 | 65.4 / 52.2% | +0.76 / -0.83 | +0.208 | -0.547 (11-03 = 181%) | 48.6 / 52.6% / -0.063 | -0.069 | +0.018 | 4 of 9 |
| RW3-FD | 20 | 35.0 / 51.0% | +0.90 / -0.94 | -0.294 | -0.338 (total < 0) | 48.0 / 52.6% / -0.076 | -0.082 | +0.011 | 6 of 13 |
| MF2-FD | 16 | 18.8 / 34.8% | +1.69 / -0.90 | -0.417 | -0.588 (total < 0) | 37.1 / 41.5% / -0.117 | -0.138 | +0.060 | 3 of 13 |

- Three of the five are positive live in the window, and two of those rest on one day:
  - L3-fromopen-FD: 10-29 is 102% of its R. Its Primary copy was -0.03R on 11 trades; the Testing 1 copy (with CF) was
    +0.40R on 38.
  - RW5-FD: 11-03 is 181% of its R.
- RW7-FD is the steadiest, at +0.195R without its best day, but its two-year record is -0.065R.
- All five sit 1-5 points under break-even on two years. They are positive only in SPY-down sessions:
  - RW7-FD: up -0.25R / down +0.08R
  - L3-fromopen-FD: up -0.05R / down +0.06R
  - RW5-FD: up -0.22R / down +0.10R
  - RW3-FD: up -0.22R / down +0.05R
  - MF2-FD: up -0.36R / down +0.00R
- **Time of day (backtest):**
  - L3-fromopen earns after 13:00: 13:00-14:00 +0.054R, 14:00+ +0.130R.
  - RW3-FD's best slice is 09:50-10:00, at +0.002R.
  - RW7-FD / RW5-FD lose least before 11:30.
  - MF2-FD loses across the day.
- **Time of day (live, window):**
  - RW7-FD wins 10:30-13:00 (+0.58 / +0.30R) and loses 13:00-14:00 (-0.32R, n 11). G11 (<= 13:00) beats the parent on
    2y (t 3.15) and still loses.
  - RW5-FD wins 10:30-11:30 (+0.77R, n 12). G11 (< 11:30) has t 2.32, just under the 2.40 bar.

## 2. Grid readout (all 90 rows in `results.csv`, full print in `report_out.txt`)
Beat the parent (paired day-clustered t >= 2.40, d > 0 in TRAIN and VALID):
- RW7-FD: G16 7.09, G01 4.05, G02 3.96, G14 3.50, G11 3.15, G15 2.87, G13 2.46
- L3-fromopen-FD: G16 4.00
- RW5-FD: G16 4.16, G14 2.85, G01 2.80, G02 2.68, G15 2.54
- RW3-FD: G16 5.45, G02 3.80, G01 3.76, G15 3.14, G14 3.11, G12 2.98
- MF2-FD: G16 4.82, G10 2.52

Variants with exp > 0 in TRAIN and VALID: 4, all on L3-fromopen-FD:
- G16: +0.054R
- G12: +0.092R
- G02: +0.017R
- G01: +0.016R

None reaches its BAR90 (best TRAIN+VALID t is 0.95).

## 3. What would change the picture
- A CF copy of L3-fromopen-FD with forward evidence. The Testing 1 copy already runs CF, so its forward record from
  10-30 is the test. It needs more sessions and needs no new setup.
- No setup or exit change is proposed. Next top-5 run: rotate these 5 out unless a setup or exit changes.

## Files
- `PLAN.md` (pre-declaration)
- `live_rank.py` / `live_rank.csv` / `live_top5.csv` / `live_top5_detail.txt`
- `build_cache.py`, `scan_1104.py`, `report_1104.py` (scratch in /dev/shm/t5_1104, deleted after the run)
- `results.csv`, `summary.json`, `report_out.txt`, `hist_parent_detail.txt`
- `make_proposals.py` / `backlog_proposals.jsonl`
- Part A: `research/bdi/top20/` (`fetch_live.py`, `conditions_live.py`, `conditions_2y.py`, `sizing_check.py` and their
  outputs; `CONDITIONS.md` rows dated 2026-11-04)
