# Top-20 conditions + top-5 execution tune, 2026-11-05 (sixteenth run): FAILED the Testing bar, 0 of 90; 15 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. **History** numbers are **backtests** on
  the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN (<= 2025-12) and VALID
  (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored,
  because nothing reached the Testing bar.
- **Data:** the 2-year cache per `research/bdi/1104/DATA.md`, read from /home/user/MCF (frames to 2026-11-04; the
  worktree linked `research/history2y/data` to it, uncommitted). Part A's two-year reads for setups outside the gates1021
  harness use the BDI 1104 trade lists (`bt_lab1104`, all 22 open months).
- **Configurations scored tonight: 90.** That is 18 execution variants per setup x 5, all pre-declared in `PLAN.md`
  before any row was scored. Part A's bucket reads are descriptive and tune nothing: 10 dimensions x 20 setups live,
  plus 3 setups on two years. No sizing checks were run tonight.
- **Result: 0 variants meet the Testing bar. There is no DECISION, no Testing proposal and no Primary change.**
  - 15 variants beat their parent.
  - 17 variants are positive in both TRAIN and VALID. 15 of them are NS3V1 rows, and NS3V1's parent is already positive
    (+0.069R). The other 2 are L3-rsi5hi-FD G16 / G18.
  - The best TRAIN+VALID t of any non-NS3V1 variant is 0.79 (NS5 G14), against a BAR90 of 4.72.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00005R, 100% within 0.01R). For NS3V1 parity
  was checked on its cache geometry (row P0, not counted).
- config/, mcf/, docs/live/ and the workflows are untouched. 20 lines were appended to research/backlog.jsonl, tag
  `top5-tune`: 5 grid lines (parked) and 15 beat-parent lines (rework). research/BACKLOG.md was not re-rendered (outside
  this run's commit scope).
- **Gen 11-05 is incomplete** (69 lots are not booked until PR #154). GEN-* is outside both parts, so no number here
  uses it.

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-05:*
  - Everything listed in top5_1104 applies.
  - Plus **ROLL1 (11-05)**: Explore 1 / Live Lab became the low-rep homes, and 42 setups moved there from Testing 1 / 2.
    Tonight's live read includes the 36 + 19 trades of those two accounts on 11-05.
  - Within the window: per-lot stacking (10-13), refire B (10-14), twin cap and -2R setup stop (10-20), Testing setup
    stop off (10-23), GX1 5-minute clock (10-27), Primary ~$4k (10-28), Primary -2R per setup (10-29), CF + BAR90 in
    Testing (10-30), moves 10-30..11-04, UNI1 top-500 pool in Testing 2 (11-04).
- *Part B live window, 10-30..11-05:* see PLAN.md section 1.
  - All of it ran with CF in Testing 1/2, and Primary ran at ~$4k with the -2R latch.
  - UNI1 covers 11-04..11-05 for NS3V1 / MF5's Testing 2 copy. ROLL1 covers 11-05.
- 11-05 was a SPY -4.2% session. It dominates several live records below.

## Failures first
| setup (acct) | beat parent | parent TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID; up / down |
|---|---|---|---|---|
| `MF5-flowsell-vwapup-rsi5hi` (T1+T2) | 6 | -0.096 / -0.001 (-2.78) | G16 CF: +0.057 (5.23) | -0.040 / +0.042; -0.16 / +0.18 |
| `L3-gap-slope-rsi5hi-FD` (P) | 3 | -0.084 / +0.011 (-1.06) | G16 CF: +0.058 (4.57) | **+0.001 / +0.030**; -0.02 / +0.06 |
| `NS1-rsidip-rsi5pop-long-FD` (T1) | 6 | -0.075 / -0.064 (-3.25) | G16 CF: +0.036 (4.09) | -0.035 / -0.049 |
| `NS5-sma50-flush-oversold-long` (P) | **0** | -0.174 / +0.163 (-0.51) | G14 SPY side: +0.064 (0.70) | -0.037 / +0.160 |
| `NS3V1-am-widestop-short` (T2) | **0** | **+0.040 / +0.106 (2.39)** | G16 CF: +0.008 (1.86) | +0.059 / +0.104 |

- **CF (G16) is again the best knob on 4 of 5** (all but NS5, where G14 is best). It keeps 66-98% of trades. On 11-03
  and 11-04 it was the best knob on all 5.
  - **L3-rsi5hi-FD + CF is the closest call tonight.** It is positive in TRAIN (+0.001) and VALID (+0.030), and +0.070R
    vs random. It fails the Testing bar for four reasons: t 0.30 vs BAR90 4.50, WF 35%, up sessions -0.019R, and avg R
    without its best day -0.013R.
  - CF already runs on the Testing copies. The Primary copy has none. Whether to add it there is an owner call on
    Primary, and it is not proposed here. It is the same picture as L3-fromopen-FD on 11-04.
- **Skip price < $20 (G18, new tonight from Part A)** beats the parent on L3-rsi5hi-FD (3.40), MF5 (3.63) and NS1-FD
  (2.58). It overlaps CF (cheap stocks = high stop cost). Per-setup effect, as the remedies rule asks:
  - 3 improve: L3-rsi5hi-FD +0.056R, MF5 +0.008R, NS1-FD +0.019R per parent signal.
  - 1 flat: NS3V1 +0.003R.
  - 1 worse: NS5 -0.011R.
  - CF, for comparison: 4 improve (+0.058 / +0.057 / +0.036 / +0.008R) and NS5 is flat (-0.002R).
  - CF is the more targeted remedy for the same failure mode, and it is already live in Testing.
- **NS1-FD G11 (window end 11:30)** is the largest gain again (+0.074R per parent signal, t 3.73, as on 10-30). It keeps
  17% of trades (319), is -0.014R in TRAIN and -0.005R in down sessions, and its t is 0.52.
- **NS3V1 is the only positive parent** (+0.069R on 1,560 trades, WF 71%, +0.055R without its best day, +0.106R vs
  random t1s1 shorts). No knob beats it.
  - Its morning slice is better (G11 <= 10:30: +0.109R, TRAIN +0.112 / VALID +0.103, t 2.72), but it does not beat the
    parent per signal (t -1.42).
  - It is already in Testing 2. Live it has 10 trades in the window at -0.093R (11-05: 4 trades -2.19R).
- **NS5 (Primary) is a coin flip on two years**: TRAIN -0.174 / VALID +0.163R, up sessions +0.175 / down -0.133R. That
  makes it a market-direction long. No knob beats it.
  - G14 (skip SPY below its open) is +0.055R but keeps 26% of trades (276), at t 0.70.
  - G13 (skip stock down > 2%) keeps 0 trades on NS5 and NS3V1, because every signal is already down > 2%. It is a
    no-op on NS1-FD. All three are counted.
- **MF5** is the same down-tape bet as MF5-FD on 10-30: up / down sessions -0.200 / +0.109R. Wider stops at the same $
  beat the parent (G01 / G02, t 2.92 / 2.93) and still lose in TRAIN.

**Recurring live loser patterns tested (Part B):**
- **Never-worked losers** (live: L3-rsi5hi-FD 7 of 9 never > +0.2R, NS1-FD 5 of 8): G07 (60-min time stop) beats
  nothing. It is -0.007R on L3-rsi5hi-FD and +0.012R on NS1-FD (t 1.85). In history 54% of L3-rsi5hi-FD losers never
  reach +0.2R, against 78% live in this window: a 14-trade window.
- **Give-back** (live losers gave back 0.8-1.2R from their best on all 5): G05 (half off + BE) raises the win rate
  10-14 points and beats no parent (best t 0.32).
- **Late-day L3-rsi5hi-FD losers** (live 13:00+ 8 trades, -0.83R avg): G12 (>= 11:30) is the better half on two years
  (+0.012R vs parent, t 2.00). The live loss is not a time-of-day effect in history.

## Part A - top-20 conditions deep dive (`research/bdi/top20/`, table `CONDITIONS.md`)
- **Top 20** = the leaderboard order (shrunk avg R, >= 20 trades, all accounts incl. Primary, Graveyard, Live Lab and
  Explore 1; GEN out).
  - All 20 were read live (10-06..11-05, 13,182 trades loaded). Counts match the dashboard within 0-10 per setup.
  - 11-05 reshuffled the top: RW3-FD rose to rank 1 (+16.7R on 13 trades that day).
  - New to the top 20: CWT09-gapdn-vwaploss-g5-short, CWT09-gapdn-bounce-g5-lowerhalf-short (both Graveyard, both
    lifted by 11-05) and NM-HL-T75-pm-long.
  - Out of the top 20: MF4-FD, RW3S-FD, CWT14-p10-lowvol.
- **Deep set:** the 17 others were all read in depth on 11-03 or 11-04, so tonight's deep set is **only the 3
  newcomers, plus CWT13-z075-short's two-year read** (now 22 of 22 months). That is 4 deep reads, under the usual 5-8:
  the rotation has run out of unread setups.
- **One-day records** (avg R without best day, and best-day share):
  - CWT09-vwaploss: 11-05 = 662% of total R; without it -0.31R.
  - NM-MF3: 143%. ST7-FD: 109%. L3-rsi5hi-FD: 117%. MF3: 523%. L3-lowdist: 170%. NS4-pm: 184%. MF4: 129%.
  - The top 3 Primary shorts are no longer one-day records: RW3-FD's best day (10-22) is 49%, and it is +0.29R without
    it. RW5-FD: 41%, +0.29R. MF2-FD is still 73%, +0.15R.
  - All three lose on two years (-0.076 / -0.063 / -0.117R).
- **"Thrives / struggles" for tonight's deep 4 (point-in-time only; REGX reliability noted):**
  - **CWT09-gapdn-vwaploss-g5-short (Graveyard):**
    - Thrives with SPY below its open at entry (live +0.33R, n 53).
    - Struggles with SPY flat at 10:00 (live -0.43R, n 43, 49% of losing R).
    - On two years it is -0.169R (up sessions -0.71 / down +0.14R), and **price < $20 is -0.85R in both splits** (n
      745).
    - REGX: only its hindsight Bear / Bull label holds; every point-in-time rating is weak or false.
    - Skipping price < $20 keeps 80% of trades and 99% of the top decile on two years, but only 64% of the live top
      decile. That makes it **on deck, not a filter**. It is a cost proxy, and the Graveyard has no CF.
  - **CWT09-gapdn-bounce-g5-lowerhalf-short (Graveyard):**
    - Thrives with SPY below its open at entry (+0.35R, n 60).
    - Struggles with SPY above its open at entry (-0.27R, n 59, 61% of losing R) and at ADV $300M-1B (-0.50R, n 23).
    - Its total is 0R. There is no two-year list (geom "S"), and every REGX rating is weak.
  - **NM-HL-T75-pm-long (T2):**
    - Thrives on gap < -3% (live +0.56R, n 15). On two years gap > +3% is the best bucket (+0.116R, both splits).
    - Struggles with SPY above its open at 10:00 (live -0.28R, n 26, 82% of losing R), but **on two years that is its
      best bucket** (+0.091R, both splits).
    - Two years +0.030R (TRAIN +0.052 / VALID -0.003). The live skip of gap +1..+3 is not supported (2y +0.067R there).
  - **CWT13-vwapstretch-z075-short (T2):** the full two-year read is -0.079R (TRAIN -0.090 / VALID -0.056).
    - Leveraged ETFs are its only positive bucket (+0.20R, n 127). ATR% < 2 and price $20-50 lose in both splits.
    - No skip rescues it: skipping ATR% < 2 still leaves -0.056R.
- **Filters:** none passes the strangling rule and also holds on two years and live.
  - Price < $20 is again the most consistent two-year loser. Part B tested it as a remedy (G18), and CF does the same
    job more evenly.
  - The SPY-side splits on shorts restate the market tilt that REGX found trustworthy only in hindsight.

## Selection (Part B)
Live paper trades 10-30..11-05 (run_id 1; S6 and GEN-* out; `live_rank.csv`). The exclusions are in PLAN.md section 1.
- MF5 base: 23 trades (first top-5 tune; its -FD copy was tuned 10-30)
- L3-rsi5hi-FD: 14 (last tuned top5_1030)
- NS1-FD: 11 (top5_1030)
- NS5: 11 (first top-5 tune)
- NS3V1: 10 (top5_1030)

CWT05 (28) and intraday_momentum (19) cannot be run in the harness.

## 1. Live (paper) vs backtest
| setup | live n | live win / BE win | live avg win / loss | live avg R | live losers never > +0.2R | bt win / BE win / exp | bt avg win / loss | bt med MFE / MAE | bt w/o best day | bt vs random |
|---|---|---|---|---|---|---|---|---|---|---|
| MF5 | 23 | 69.6 / 48.7% | +0.83 / -0.78 | +0.336 (11-03 16 trades +7.1R = 91% of R) | 2 of 7 | 49.2 / 53.1% / -0.067 | +0.81 / -0.91 | 0.72 / 0.65 | -0.070 | +0.012 |
| L3-rsi5hi-FD | 14 | 35.7 / 72.1% | +0.40 / -1.02 | -0.515 | 7 of 9 | 66.5 / 69.6% / -0.047 | +0.45 / -1.04 | 0.54 / 0.43 | -0.065 | +0.012 |
| NS1-FD | 11 | 27.3 / 61.8% | +0.37 / -0.59 | -0.331 | 5 of 8 | 60.2 / 65.6% / -0.070 | +0.44 / -0.84 | 0.51 / 0.48 | -0.077 | +0.001 |
| NS5 | 11 | 45.5 / 49.9% | +0.76 / -0.76 | -0.067 | 3 of 6 | 49.8 / 52.4% / -0.050 | +0.89 / -0.98 | 0.81 / 0.77 | -0.077 | +0.110 |
| NS3V1 | 10 | 50.0 / 58.5% | +0.45 / -0.64 | -0.093 | 0 of 5 | 65.8 / 59.4% / **+0.069** | +0.44 / -0.64 | 0.51 / 0.32 | +0.055 | +0.106 |

- Live and backtest agree on the shape (win and loss sizes match within ~0.1R) and on the sign for 4 of 5. MF5's live
  +0.34R is one day (11-03).
- Only NS3V1 sits above its break-even win rate on two years. It is the one setup tonight whose backtest supports what
  it does; its 10 live trades are not evidence either way.
- **Time of day (backtest):**
  - L3-rsi5hi-FD earns only 10:30-11:30 (+0.019R) and 14:00+ (+0.031R).
  - NS1-FD earns only 10:30-11:30 (+0.063R).
  - NS3V1 is best first: 09:50-10:00 +0.172R, 10:00-10:30 +0.092R.
  - NS5 loses 09:50-10:00 (-0.36R) and wins 10:00-10:30 (+0.14R).
  - MF5 loses across the day, least at 13:00-14:00.
- **Side / market (backtest):** the three shorts lose in SPY-up sessions (MF5 -0.20, L3-rsi5hi-FD -0.08, NS3V1 -0.02R).
  The two longs lose in SPY-down sessions (NS1-FD -0.17, NS5 -0.13R).

## 2. Grid readout (all 90 rows in `results.csv`, full print in `report_out.txt`)
Beat the parent (paired day-clustered t >= 2.40, d > 0 in TRAIN and VALID):
- MF5: G16 5.23, G18 3.63, G02 2.93, G01 2.92, G14 2.76, G11 2.52
- L3-rsi5hi-FD: G16 4.57, G18 3.40, G01 2.65
- NS1-FD: G16 4.09, G11 3.73, G02 3.00, G18 2.58, G01 2.57, G14 2.51
- NS5: none
- NS3V1: none

Variants with exp > 0 in TRAIN and VALID:
- NS3V1: 15 rows (its parent is positive)
- L3-rsi5hi-FD: 2 rows (G16, G18)
- MF5 / NS1-FD / NS5: none in both splits

None reaches BAR90 (4.41-4.72). The best TRAIN+VALID t is NS3V1 G18 3.25, which does not beat its parent (t 0.27).

## 3. What would change the picture
- The forward record of CF in Testing (since 10-30) is the live test of the one knob that keeps winning on two years.
  L3-rsi5hi-FD and L3-fromopen-FD now both show CF as their best two-year row, and both of their Primary copies run
  without CF. That is an owner question, not a proposal, because neither variant clears the Testing bar.
- No setup or exit change is proposed. Next top-5 run: rotate these 5 out unless a setup or exit changes. The eligible
  pool is thin, because CWT05 and intraday_momentum cannot be run in the harness.

## Files
- `PLAN.md` (pre-declaration)
- `live_rank.py` / `live_rank.csv` / `live_top5.csv` / `live_top5_detail.txt`
- `build_cache.py`, `scan_1105.py`, `report_1105.py` (scratch in /dev/shm/t5_1105, deleted after the run)
- `results.csv`, `summary.json`, `report_out.txt`, `hist_parent_detail.txt`
- `make_proposals.py` / `backlog_proposals.jsonl`
- Part A: `research/bdi/top20/`
  - `fetch_live.py` (Live Lab / Explore 1 added), `conditions_live.py`
  - new `conditions_2y_bt.py` -> `hist_bt_*`
  - `CONDITIONS.md` rows dated 2026-11-05
