# Top-20 conditions + top-5 execution tune, 2026-11-09 (eighteenth run): FAILED the Testing bar, 0 of 95; 22 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. **History** numbers are **backtests** on
  the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN (<= 2025-12) and VALID
  (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored,
  because nothing reached the Testing bar.
- **Data:** the 2-year cache per `research/bdi/1104/DATA.md` (frames to 2026-11-04). Part A's two-year reads use the
  BDI 1104 trade lists (`bt_lab1104`, 22 open months).
- **Configurations scored tonight: 95.** That is 19 one-knob execution variants per setup x 5, all pre-declared in
  `PLAN.md` before any row was scored. Part A's bucket reads are descriptive and tune nothing: 11 dimensions x 20 setups
  live, plus 6 setups on two years.
- **Result: 0 variants meet the Testing bar. There is no DECISION, no Testing proposal and no Primary change.**
  - 22 variants beat their parent (RW3S 6, exhaustion_short-FD 7, L3-lowdist 5, RW1 4, NM-AR-AM 0).
  - Only 1 of the 22 is positive after costs (L3-lowdist G16 SPY-side, +0.037R), and it loses in VALID (-0.004R).
  - **CF (G13) is the best knob on all 4 shorts** (t 4.32-7.36). CF already runs in Testing 1/2 since 10-30, so this is
    what the live copies already do. With CF all 4 still lose: RW3S -0.030R, exhaustion_short-FD -0.051R, RW1 -0.023R,
    L3-lowdist -0.071R.
  - The one positive parent is **NM-AR-AM-gapdown-capitulation-long**: +0.278R, TRAIN +0.328 / VALID +0.210, t 2.23 vs
    BAR90 4.16. It has a one-day concentration (best day = 54% of R). No knob beats it.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00006R, 100% within 0.01R).
- config/, mcf/, docs/live/ and the workflows are untouched. 28 lines were appended to research/backlog.jsonl:
  - 27 with tag `top5-tune`: 5 grid lines (parked) and 22 beat-parent lines (rework).
  - 1 Part A sizing idea (CU1, status idea).

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-09:*
  - per-lot stacking (10-13), refire B (10-14)
  - twin cap and -2R setup stop (10-20)
  - Testing setup stop off (10-23)
  - GX1 5-minute clock (10-27)
  - Primary ~$4k (10-28), Primary -2R latch (10-29)
  - CF + BAR90 in Testing (10-30)
  - moves 10-30..11-04, UNI1 top-500 pool in Testing 2 (11-04), ROLL1 low-rep homes (11-05)
  - **EXPO1109 temporary GEN moves into Testing 1/2 (11-09 + 11-10)**
  - compass live from 11-09 (display only, no trading effect)
- *Part B live window, 11-03..11-09:* see PLAN.md section 1. EXPO1109's five GEN setups shared Testing 1/2 capacity on
  11-09. No setup or exit change touched the 5 setups below.

## Failures first
| setup (acct) | beat parent | parent TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID; up / down |
|---|---|---|---|---|
| `RW3S-gapdn-flowsell-short-FD` (T2) | 6 | -0.075 / -0.027 (-2.74) | G13 CF: +0.031 (7.23) | -0.047 / -0.005; -0.21 / +0.10 |
| `exhaustion_short-FD` (T1) | 7 | -0.110 / -0.028 (-3.92) | G13 CF: +0.034 (7.36) | -0.078 / -0.014; -0.15 / +0.09 |
| `RW1-gapdn-bounce-flowsell-short-FD` (T2) | 4 | -0.073 / -0.011 (-2.25) | G13 CF: +0.031 (4.92) | -0.045 / +0.012; -0.22 / +0.13 |
| `NM-AR-AM-gapdown-capitulation-long` (T2) | **0** | **+0.328 / +0.210 (2.23)** | G04 target x1.5: +0.039 (1.69, below 2.43) | +0.511 / +0.237; +0.39 / +0.40 |
| `L3-gap-slope-lowdist-FD` (T1) | 5 | -0.149 / -0.093 (-1.80) | G13 CF: +0.073 (4.32) | -0.085 / -0.046; -0.24 / +0.19 |

- **The same picture as top5_1103 for the four shorts.**
  - CF, price >= $20 and the wider stop (G01, x1.5 at the same $) each beat the parent.
  - The tighter stop (G02) is the worst knob on every setup, as in 1106.
  - All four shorts lose in up sessions (-0.18..-0.30R) and earn in down sessions (+0.06..+0.13R). They are bets on a
    down tape, not stock edges.
- **exhaustion_short-FD after 13:00 (G12)** is the closest short to break-even: -0.009R, TRAIN -0.056 / VALID +0.075,
  t 4.21 vs the parent. That repeats top5_1103's "late window" read. It is still negative in TRAIN.
- **Compass knobs (new; per-setup effect, as the remedies rule asks):**
  - **G17 (skip entries against a W60-confirmed compass)** helps 3 setups in both splits: L3-lowdist +0.036R per parent
    signal, RW1 +0.015R, RW3S +0.007R. It is mixed on exhaustion_short-FD (TRAIN +0.040 / VALID -0.005). It hurts
    NM-AR-AM badly (-0.236R).
    - None reaches the setup bar (best t 1.83).
    - G17 keeps 49-80% of trades, so on exhaustion_short-FD (65%), L3-lowdist (61%) and NM-AR-AM (49%) it would also
      fail the no-strangle screen.
  - **G18 (half size against the compass)** has the same sign pattern at half the effect: +0.018 / +0.007 / +0.003R,
    mixed on exhaustion_short-FD, -0.118R on NM-AR-AM.
  - So 3 setups get better, 1 is mixed and 1 gets worse, by about 4x the best gain. "Against the compass" is the wrong
    remedy for a capitulation long, whose home is the confirmed-down tape: NM-AR-AM DOWN-confirmed is TRAIN +0.507 /
    VALID +0.337R, UP-confirmed -0.207 / +0.086R.
  - It is not proposed. The 11-09 failure (MF4-FD shorts into an UP-confirmed tape) needs a remedy aimed at the
    failure mode, and the compass-side split is not a uniform per-setup edge in history (as MF1109 found for the MF
    shorts).
- **NM-AR-AM (first top-5 tune)** has the strongest two-year parent of any setup tuned in the last month:
  - +0.278R on 1,280 trades, win 65.9% vs break-even 51.8%.
  - WF 65% of months positive. Up sessions +0.27R, down sessions +0.28R. +0.173R vs random entries.
  - Without its best day it drops to +0.127R (best day = 54% of total R; April 2025, as swarm1017 noted).
  - t 2.23 against a BAR90 of 4.16 (lineage N 43,359 from the swarm1017 arena).
  - Live: 14 trades at -0.713R, 12 stops (11-05 8 trades -3.9R; 11-06 2, -2.0R; 11-09 4, -4.1R), all at 10:50-10:55.
    Live median MAE is 1.01R against 0.52R on two years. That is 3 sessions, not evidence, but live sits far below its
    backtest win rate (14% vs 66%).
  - Keep it running in Testing 2 for reps. No change.
  - A DOWN-compass-only version is an in-sample idea (from the parent split above). It is not a scored config, and it
    would keep about 51% of trades.
- **Live losers cluster as follows:**
  - RW3S: 10:30-11:30 (96 trades, -0.345R) and 11-05 (60 trades, -30.3R). Across the window, compass DOWN entries
    are -0.52R (n 59): shorts entered after the crash and squeezed. History has no 10:30-11:30 hole (-0.046R vs -0.056R parent).
  - exhaustion_short-FD: 10:30-11:30 (9, -0.69R).
  - NM-AR-AM: the 10:50 bar on 11-05 and 11-09.
  - L3-lowdist and RW1 are positive live (13 and 24 trades).
  - The **never-worked losers** (RW3S: 43 of 86 never > +0.2R) get no help from the 30/60-min time stops (G06 / G07,
    t -0.62..+0.08).

## Part A - top-20 conditions deep dive (`research/bdi/top20/`, table `CONDITIONS.md`)
- **Top 20** = the leaderboard order (shrunk avg R, >= 20 trades, all accounts incl. Primary, Graveyard, Live Lab and
  Explore 1; GEN out).
  - All 20 were read live (10-06..11-09, 14,800 trades loaded).
  - **Out:** MF4-h40-open-flowsell-FD, after 11-09's 17 shorts at -17.1R. **New:** RW6G1-ns2-up3-vwap2sd-short-FD
    (Graveyard, rank 20), after 11-09's 18 trades at +4.05R.
- **New dimension: compass at entry.**
  - The W60 state comes from the latest 15-min mark at or before the entry minute.
  - Recorded `mcf-data-compass` rows cover 11-06 and 11-09. The other 23 sessions were backfilled with
    `mcf.report.compass_live.compute()` from the 1-minute cache plus market-data GETs (`compass_backfill.py`). The
    backfill matches the recorded rows 100% (W60 and checkpoint) on both recorded days.
  - Two-year compass: `compass_2y.py`, the same W60 rule with lab-context breadth (the hc1 approximation).
  - Live mix: UP 4,035 / DOWN 3,204 / unconfirmed 7,561 trades.
- **Deep set (8):** the least recently deep (11-03 / 11-04) and the newcomer: RW3-FD, RW5-FD, L3-fromopen-FD, RW7-FD,
  L3-rsi5hi-FD, NS5, MF3 (no 2-year list) and RW6G1-FD (no 2-year list).
  - With 11-05 / 11-06, **all 20 have been read in depth within 3 nights**. MF4-h40 base (11-04) is next.
- **One-day records** (avg R without best day; best-day share):
  - MF2-FD 159%, w/o it -0.11R. NM-MF3-FD 142%, -0.44R. L3-lowdist 144%, -0.05R. MF3 523%, -0.08R.
  - CWT09-vwaploss: its total is about 0, w/o its best day -0.34R.
  - **Not one-day records:** RW3-FD (46%, +0.30R w/o best day), RW5-FD (41%, +0.28R), RW7-FD (48%, +0.04R) and RW1-FD
    (50%, +0.06R).
- **Compass by setup** (live; 2y in brackets where read):
  - **Shorts that like a confirmed DOWN tape:** RW3-FD (DOWN +0.64R / UP +0.08R; 2y all three negative, UP least bad),
    RW7-FD (DOWN +0.22R / unconfirmed -0.15R; 2y all negative), RW1-FD, MF4 base.
  - **Shorts that like a confirmed UP tape:**
    - L3-fromopen-FD: UP +0.26R. 2y UP +0.080R vs unconfirmed -0.158R, both splits the same sign.
    - RW6G1-FD: UP +0.20R, 83% of top-decile winners.
    - MF3, CWT09-lowerhalf, CWT13-z075.
  - **Unconfirmed is the worst state** for 5 live setups (RW7, RW1, the two CWT09s, RW6G1) and for 5 of the 6 two-year
    reads (L3-fromopen, L3-rsi5hi, NS5, RW3, RW5). The exceptions run the other way: live RW3 / RW5 / MF2 / NM-MF3 do
    best when unconfirmed.
    - Unconfirmed holds 33-57% of trades, so a skip fails the 70% screen.
    - It is logged as sizing idea CU1 (half size when unconfirmed, per-setup effects to report). 0 configs are scored
      on it so far.
- **Top 3 "thrives when" (live and 2y agree):**
  1. **L3-fromopen-FD with the compass UP-confirmed** (live +0.26R n 121; 2y +0.080R, TRAIN +0.126 / VALID +0.002,
     n 19,091).
  2. **NS5 with the compass DOWN-confirmed** (2y +0.182R, TRAIN +0.050 / VALID +0.432, n 335; live n 4). It struggles
     with SPY above its open at 10:00 (live -0.30R; 2y -0.234R).
  3. **L3-rsi5hi-FD unless SPY is below its open at 10:00** (live -0.47R n 16; 2y -0.100R).
     - The live skip keeps 82% / 100% (+0.082 -> +0.200R).
     - On two years that bucket is 37% of trades, so it is sizing / on deck.
- **Disagreements:**
  - RW3-FD's live compass-UP skip passes the live screen (74% / 92%), but on two years UP is its least-bad state.
  - RW5-FD's live ETF edge is -0.128R on two years.
  - RW7-FD's live DOWN preference is not in history.
  - The L3 pair's live 14:00+ losses sit against two-year 14:00+ gains.
- **Filters:** none is proposed. Price < $20 is again a two-year loser in both splits for 4 of the 6 deep setups. Every
  skip of it fails the live top-decile screen for the L3s, and CF already does that job in Testing.

## Selection (Part B)
Live paper trades 11-03..11-09 (run_id 1; S6 and GEN-* out, so the EXPO1109 GEN setups are out; `live_rank.csv`).
The exclusions are in PLAN.md section 1.

| setup | live n | live win / BE win | avg win / loss | avg R | losers never > +0.2R | live med MFE / MAE | give-back (losers) |
|---|---|---|---|---|---|---|---|
| RW3S-FD (T2) | 143 | 39.9 / 54.5% | +0.83 / -0.99 | -0.266 (11-05: 60 trades -30.3R) | 43 of 86 | 0.39 / 0.94 | 1.26R |
| exhaustion_short-FD (T1+T2) | 31 | 41.9 / 52.7% | +0.52 / -0.58 | -0.118 (11-04 5 trades -4.0R) | 7 of 18 | 0.49 / 0.59 | 0.92R |
| RW1-FD (T2) | 24 | 66.7 / 47.7% | +0.78 / -0.71 | +0.281 | 3 of 8 | 0.64 / 0.71 | 0.97R |
| NM-AR-AM (T2) | 14 | 14.3 / 44.5% | +1.31 / -1.05 | -0.713 (12 stops) | 3 of 12 | 0.34 / 1.01 | 1.42R |
| L3-lowdist-FD (T1) | 13 | 69.2 / 54.4% | +0.87 / -1.03 | +0.282 | 0 of 4 | 0.81 / 0.46 | 1.67R |

**Backtest parents** (TRAIN + VALID; `hist_parent_detail.txt`):
| setup | bt win / BE | exp | w/o best day | vs random | best / worst time | up / down sessions |
|---|---|---|---|---|---|---|
| RW3S-FD | 49.4 / 52.5% | -0.056 | -0.061 | +0.023 | 10:00-10:30 -0.024 / 13:00-14:00 -0.086 | -0.236 / +0.077 |
| exhaustion_short-FD | 49.3 / 53.5% | -0.076 | -0.081 | +0.006 | 14:00+ +0.011 / 10:00-10:30 -0.133 | -0.180 / +0.064 |
| RW1-FD | 49.2 / 52.3% | -0.050 | -0.054 | +0.030 | 09:50-10:00 +0.044 / 13:00-14:00 -0.097 | -0.230 / +0.097 |
| NM-AR-AM | 65.9 / 51.8% | **+0.278** | +0.127 | +0.173 | 10:50 bar +0.318 / 10:55 bar +0.105 | +0.275 / +0.280 |
| L3-lowdist-FD | 48.2 / 54.9% | -0.129 | -0.153 | -0.011 | 14:00+ +0.104 / 10:00-10:30 -0.374 | -0.297 / +0.127 |

- Live and backtest agree on the win and loss sizes within about 0.4R. Win rates do not agree:
  - RW3S, exhaustion_short-FD and NM-AR-AM sit 11-52 points below break-even live.
  - RW1 and L3-lowdist sit 15-19 points above it, on 13-24 trades.
- **By W60 compass on two years:** RW3S and RW1 are worst when unconfirmed in TRAIN (-0.107 / -0.108R) but positive
  there in VALID (+0.016 / +0.043R). L3-lowdist is worst unconfirmed in both splits (-0.229 / -0.122R). exhaustion_short-FD
  is only positive UP-confirmed in VALID (+0.014R). The state split is not stable across periods for most of them.

## What would change the picture
- NM-AR-AM is the only setup tonight whose two-year record supports what it does. Its forward record in Testing 2 is
  the test, and so far it is poor (3 sessions).
- CU1 (half size when the compass is unconfirmed) is the Part A lead. It needs a pre-declared multi-setup test with
  per-setup better / worse counts.
- Next top-5 run: rotate these 5 out. The next eligible by live count: CWT05 (not coverable), intraday_momentum (not
  coverable), ST7-FD (11), then the 1104 group (RW7-FD, MF2-FD, RW3-FD, RW5-FD, L3-fromopen-FD) after its 3-run gap.

## Files
- `PLAN.md` (pre-declaration)
- `live_rank.py` / `live_rank.csv` / `live_top5.csv` / `live_top5_detail.txt`
- `build_cache.py`, `scan_1109.py`, `report_1109.py` (scratch in /dev/shm/t5_1109, deleted after the run)
- `results.csv`, `summary.json`, `report_out.txt`, `hist_parent_detail.txt`
- `make_proposals.py` / `backlog_proposals.jsonl`
- Part A: `research/bdi/top20/`
  - `fetch_live.py`, `conditions_live.py` and `conditions_2y_bt.py`, re-dated to 11-09, with the compass dimension added
  - new: `compass_backfill.py` and `compass_2y.py`
  - `live_*` and `hist_bt_*` outputs
  - `CONDITIONS.md` rows dated 2026-11-09
