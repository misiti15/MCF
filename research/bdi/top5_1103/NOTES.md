# Top-20 conditions + top-5 execution tune, 2026-11-03 (fourteenth run): FAILED the Testing bar, 0 of 85; 20 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7). They are a diagnosis, not evidence. **History** numbers are
  **backtests** on the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN
  (<= 2025-12) and VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**, and
  no holdout was scored because nothing reached the Testing bar.
- **Configurations scored tonight: 90.** That is 85 execution variants (Part B, 17 per setup x 5, pre-declared in
  `PLAN.md` before any row was scored) plus 5 half-size checks (Part A, `research/bdi/top20/sizing_check.py`). Part A's
  bucket reads are descriptive and tune nothing: 10 dimensions x 20 setups live, and 11 setups on two years.
- **Result: 0 variants meet the Testing bar. There is no DECISION, no Testing proposal and no Primary change.**
  - 20 variants beat their parent, and every one of them still loses in TRAIN or VALID or in SPY-up sessions.
  - 0 of the 5 sizing checks clears max(1.5, sqrt(2 ln 5)) = 1.79 in both TRAIN and VALID.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00006R, 100% within 0.01R).
- config/, mcf/, docs/live/ and the workflows are untouched.
  - 26 lines were appended to research/backlog.jsonl: 5 grid lines (parked), 20 beat-parent lines (rework, tag
    `top5-tune`) and 1 Part A sizing idea (tag `top20-conditions`).
  - research/BACKLOG.md was not re-rendered, because it is outside this run's commit scope.

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-03:*
  - per-lot stacking (10-13)
  - refire option B and same-setup re-entry (10-14)
  - RW5-FD / RW3-FD promoted (10-15)
  - MF2-FD / MF4-FD promoted (10-20)
  - twin cap and -2R setup stop (10-20)
  - promotion = move (10-21)
  - Testing setup stop off (10-23)
  - GX1 5-minute clock gate (10-27)
  - Primary size ~$4k (10-28)
  - Primary -2R setup stop (10-29)
  - CF cost filter in Testing 1/2 (10-30)
  - L3-fromopen-FD Primary -> T1 (10-22) -> Primary (10-30); L3-rsi5hi-FD -> Primary (10-30)
  - NS4 / MF2 window-version rotations (10-28)
- *Part B live window, 10-28..11-03:* see PLAN.md section 1 (size 10-28, -2R 10-29, CF 10-30, Graveyard moves
  10-30 / 11-02 / 11-03, RW3S added 11-03).
- Live figures mix these regimes. In particular, every Primary record before 10-28 ran at the old size and without the
  -2R stop.

## Failures first
| setup (acct) | beat parent | parent TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|
| `exhaustion_short-FD` (T1+T2) | 7 | -0.110 / -0.028 (-3.92) | G16 CF stop-cost <= 0.15R: +0.034 (7.36) | -0.078 / -0.014 |
| `RW3S-gapdn-flowsell-short-FD` (T2, first tune) | 5 | -0.075 / -0.027 (-2.74) | G16 CF: +0.031 (7.23) | -0.047 / -0.005 |
| `RW1-gapdn-bounce-flowsell-short-FD` (T2) | 4 | -0.073 / -0.011 (-2.25) | G16 CF: +0.031 (4.92) | -0.045 / **+0.012** |
| `L3-gap-slope-lowdist-FD` (T1) | 4 | -0.149 / -0.093 (-1.80) | G16 CF: +0.073 (4.32) | -0.085 / -0.046 |
| `ST7-rsi50dn-long-pm-t1s1-FD` (Primary, first tune) | **0** | -0.062 / +0.100 (0.32) | G16 CF: +0.031 (1.64) | -0.018 / +0.136 |

- **The CF cost filter is the best knob on all 5 setups again.** It is already live in Testing 1/2 since 10-30, and it
  keeps 79-83% of trades. Every setup still loses with it, except ST7-FD in VALID.
  - ST7-FD has no CF in Primary. The +0.031R it gains there does not reach the 2.38 setup bar (t 1.64).
- **Wider stops at the same $ (G01 / G02)** beat the parent on 4 of 5 setups (every one except ST7-FD), which matches
  every top-5 run since 10-22. Every row stays below zero in TRAIN.
- **ST7-FD is the only parent that is positive overall** (+0.019R, 741 trades, WF 59%, +0.086R vs random), but it is
  negative in TRAIN.
  - 3 variants are positive in both TRAIN and VALID: G12 after 13:00 (+0.131R, t 1.86, 138 trades), G14 longs only
    with SPY at or above its open (+0.062R), and G17 skip SPY flat (+0.063R).
  - None beats the parent at the bar (paired t 0.09 / 0.10 / 0.64), and the best TRAIN+VALID t is 1.86, against a
    BAR90 of 4.35.
- **RW3S-FD (first tune, owner observation since 11-03):** 70 signals per session on two years at -0.056R (up sessions
  -0.24R / down +0.08R). It is a down-tape bet like its RW3 parent.
  - The one live session (24 trades, -0.04R) lost its early trades: 09:50-10:30 went -0.70R on 9 trades. Two years says
    the opposite: G11 (entries until 10:30) *beats* the parent (t 2.75), and the early slice is the least bad.
- **exhaustion_short-FD:** the best slice is after 13:00 (G12, -0.009R, t 4.21 vs parent), but it is still negative in
  TRAIN.
- No-op / empty rows: none.

**Recurring live loser patterns tested (Part B):**
- **SPY flat at entry** (new G17, from tonight's top-20 loser clusters: RW1-FD -0.40R, RW7-FD -0.14R, MF4-FD -0.31R
  live). It beats the parent only on exhaustion_short-FD (t 3.12, still -0.071R). It is flat on RW1-FD (t 0.40),
  RW3S-FD (1.21), L3-lowdist (0.09) and ST7-FD (0.64). The live cluster does not carry over to two years.
- **Never-worked losers** (live: ST7-FD 6 of 6 losers never above +0.2R, exhaustion_short-FD 10 of 22). G07 (60-min
  time stop) is flat on all 5 (t -0.68..0.60).
- **Give-back** (live losers gave back 1.0-1.3R from their best). G05 (half off + BE) raises win rates 12-14 points,
  but it beats no parent at the bar (best t 2.04 on exhaustion_short-FD).
- **Early-window losers** (RW3S 09:50-10:30; exhaustion_short-FD 10-28 12 trades -8.1R). Two years favours the early
  window for RW3S and the late window for exhaustion_short-FD.
- **L3-lowdist 11:30-13:00** (live 72% of losing R): G12 (from 11:30) does not beat the parent (t 1.39).

## Part A - top-20 conditions deep dive (`research/bdi/top20/`, table `CONDITIONS.md`)
- **Top 20** = the leaderboard order (shrunk avg R, >= 20 trades, all accounts incl. Primary and Graveyard, GEN out).
  - All 20 were read live (10-06..11-03, 11,640 trades loaded; trade counts match the dashboard within 0-10 per setup).
  - 8 were read deep on two years (ranks 1-8), plus 3 more through Part B's cache (ranks 10, 11 and 14).
- **Shared caveat on the top 3:** their live R is mostly market.
  - MF2-FD +0.70R falls to +0.29R ex-market; RW5-FD +0.38 falls to +0.12; RW3-FD +0.37 falls to +0.14.
  - The best day, 10-22, carries 63% / 43% / 71% of their total R.
  - On two years all three lose (-0.058 / -0.063 / -0.076R), and they lose most in SPY-up sessions (-0.19 / -0.30 /
    -0.28R).
  - The live records are down-tape records.
- **Top 3 "thrives when" (point-in-time):**
  1. MF2-FD: gap-down names while SPY is below its open at entry (live +0.99R, n 38).
  2. RW5-FD: 10:30-13:00 with SPY below its open at entry (live +0.56R, n 54; two years agrees on direction: -0.004R
     vs -0.117R when SPY is above its open).
  3. RW3-FD: SPY below its open at entry (live +0.61R, n 51; SPY above its open holds 54% of its losing R).
- **L3 pair (fromopen / rsi5hi):** they struggle when SPY is below its open at 10:00. This holds live (-0.33R n 35 /
  -0.47R n 11) and on two years (-0.126R / -0.100R vs parent -0.017 / -0.047).
  - Skipping that condition fails the strangling rule (two years keeps 76% of trades but only 75% of top-decile winners
    for L3-fromopen), so it is only a sizing idea.
- **No filter passes the strangling rule and also holds on two years.**
  - Two years' most consistent loser bucket is **price < $20**. Every short family loses there in TRAIN and VALID, and
    for L3-fromopen skipping it would turn -0.017R into +0.068R while keeping 72% / 98%.
  - But live L3-fromopen is +0.30R on 125 sub-$20 trades. The bucket is mostly a cost proxy (2c stop slippage, x3 tier)
    and overlaps CF and UNI1.
  - It is not proposed.
- **Sizing (on deck, 5 checks: half size in the struggle condition).** Every check improves R per unit of risk in both
  TRAIN and VALID (+0.002..+0.028R), but none clears 1.79 in both splits:
  - RW5-FD SPY above its open at entry: TRAIN t 1.19, VALID 2.27, live 1.46
  - RW3-FD SPY above its open at entry: 0.22 / 1.57 / 2.46
  - L3-fromopen SPY below at 10:00: 1.39 / 0.32 / 1.30
  - L3-rsi5hi SPY below at 10:00: 0.90 / 0.40 / 1.47
  - ST7-FD SPY above at 10:00: 0.90 / 1.46 / -0.01
  - One backlog idea line records them (`top20-1103-half-size-against-tape`).
- Live vs two-year disagreements are listed in CONDITIONS.md, so they are not taken as fact:
  - L3-fromopen after 13:00
  - L3-lowdist 10:30-11:30
  - RW3S before 10:30
  - RW1-FD SPY flat at entry

## Selection (Part B)
Live paper trades 10-28..11-03 (run_id 1; S6 and GEN-* out; `live_rank.csv`). The exclusions are in PLAN.md section 1.
Scored:
- exhaustion_short-FD: 44 trades (last tuned top5_1028)
- RW3S-FD: 24 trades (first tune)
- RW1-FD: 17 trades (last tuned top5_1028)
- L3-lowdist-FD: 11 trades (last tuned top5_1027)
- ST7-FD: 10 trades (first top-5 tune)

## 1. Live (paper) vs backtest
| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day | bt win / BE win / exp | bt w/o best day | bt vs random | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|---|
| exhaustion_short-FD | 44 | 50.0 / 53.3% | +0.75 / -0.85 | -0.052 | -0.583 (total < 0) | 49.3 / 53.5% / -0.076 | -0.081 | +0.006 | 10 of 22 |
| RW3S-FD | 24 | 54.2 / 56.6% | +0.68 / -0.89 | -0.038 | n/a (1 session) | 49.4 / 52.5% / -0.056 | -0.061 | +0.023 | 4 of 11 |
| RW1-FD | 17 | 52.9 / 50.0% | +0.87 / -0.87 | +0.052 | -0.177 (10-28 = 342% of total) | 49.2 / 52.3% / -0.050 | -0.054 | +0.030 | 1 of 8 |
| L3-lowdist-FD | 11 | 36.4 / 45.0% | +0.85 / -0.70 | -0.135 | -0.135 (total < 0) | 48.2 / 54.9% / -0.129 | -0.153 | -0.011 | 2 of 7 |
| ST7-FD | 10 | 40.0 / 50.3% | +1.06 / -1.07 | -0.219 | -0.620 (total < 0) | 52.5 / 51.4% / +0.019 | +0.006 | +0.086 | 6 of 6 |

- Only RW1-FD is positive live, and that rests on one day (10-28).
- The four shorts sit 3-7 points under break-even on two years and are positive only in SPY-down sessions:
  - exhaustion_short-FD: up -0.18R / down +0.06R
  - RW3S-FD: up -0.24R / down +0.08R
  - RW1-FD: up -0.23R / down +0.10R
  - L3-lowdist: up -0.30R / down +0.13R
- ST7-FD (long) is the mirror image: up +0.19R / down -0.10R.
- **Time of day (backtest):**
  - L3-lowdist earns only 14:00+ (+0.104R)
  - exhaustion_short-FD is least bad late (14:00+ +0.011R)
  - RW1-FD is least bad 09:50-10:00 and 10:30-11:30

## 2. Grid readout (all 90 rows in `results.csv`)
| knob | beats parent | note |
|---|---|---|
| stop x1.5 / x2.0 at same $ (G01 G02) | 8 of 10 | not ST7-FD |
| target x0.75 / x1.5 (G03 G04) | 0 | |
| half at 0.5 x target + BE (G05) | 0 | |
| clock exit / 60-min time stop (G06 G07) | 0 | |
| limit 0.1R / next-bar entry (G08 G09) | 0 | the limit skips 33-48% of trades |
| SPY 0.5% veto (G10) | 0 | |
| window parts (G11 G12) | 2 (RW3S G11, exhaustion_short-FD G12) | |
| stock down > 2% skip (G13) | 0 | |
| SPY-side filter (G14) | 3 (L3-lowdist, RW1-FD, exhaustion_short-FD) | cuts 49-68% of trades |
| first 5 per session (G15) | 2 (RW3S, exhaustion_short-FD) | lowers avg R, "beats" only by cutting days |
| CF stop-cost <= 0.15R (G16) | 4 (t 4.32-7.36) | ST7-FD t 1.64 |
| skip SPY flat at the signal (G17, new) | 1 (exhaustion_short-FD) | |

## 3. Bars
- **Beats parent (20):**
  - exhaustion_short-FD: G01 G02 G12 G14 G15 G16 G17
  - RW3S-FD: G01 G02 G11 G15 G16
  - RW1-FD: G01 G02 G14 G16
  - L3-lowdist-FD: G01 G02 G14 G16
  - Each one is negative in TRAIN.
- **Testing bar (BAR90 4.28-4.70): 0.**
  - 3 of 85 variants have exp > 0 in both TRAIN and VALID: ST7-FD G12, G14 and G17. None of them beats the parent.
  - The best TRAIN+VALID t of any row is 1.86 (ST7-FD G12).

## Queued (not scored tonight)
- Rotation: the next deep set for CONDITIONS.md is ranks 9, 12, 13 and 15-20 (live-only tonight). Two-year kernels
  exist for MF4-FD, MF4, RW7-FD, NS4, MF3 and exhaustion_short; CWT14 pdl uses pdl1030.
- ST7-FD's "after 13:00" slice (+0.131R, 138 trades, t 1.86) and its sizing check are the only near-positive leads.
  Both are thin, so they need forward sessions, not more grids.

## Files
- `live_rank.py` -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py` rebuilds gates1021's live-shaped signal cache for the 13 setups. It wrote to /dev/shm/t5_1103/g,
  because the disk had 0.2 GB free; it took about 13 minutes and the cache is deleted afterwards.
- `scan_1103.py` -> `/dev/shm/t5_1103/trades.parquet` (deleted after the report).
- `report_1103.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`, `report_out.txt`.
- `make_proposals.py` -> `backlog_proposals.jsonl`.
- Part A: `research/bdi/top20/`.
  - `fetch_live.py` (Alpaca market-data GET only)
  - `conditions_live.py` -> live_summary.csv, live_buckets.csv, live_out.txt
  - `conditions_2y.py` -> hist_*
  - `sizing_check.py` -> sizing_check.csv
  - `CONDITIONS.md`

Educational only - not financial advice.
