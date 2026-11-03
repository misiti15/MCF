# Top-5 setup execution tune, 2026-11-02 (thirteenth run): FAILED the Testing bar, 0 of 80; 17 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-27..10-30 + 11-02 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history: production + time-of-day costs, x3 on the extended
  tier, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never
  loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 80** (16 per setup x 5), plus 5 parent rows. Setup bar sqrt(2 ln 16) = 2.35; study bar
  sqrt(2 ln 80) = 2.96; **Testing bar = rule 22 BAR90** on lineage N: CWT13 4.35, NM-HL-T75 4.11, exhaustion_short
  4.70, MF4-FD 4.72 (MarcoFlow discovery N unrecorded: largest backlog lineage used), NM-AR-AM 4.16; plus WF >= 54%.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 17 variants beat
  their parent (8 CWT13, 9 MF4-FD); all 17 still lose in TRAIN and VALID. No variant beats its parent on NM-HL-T75,
  exhaustion_short or NM-AR-AM.
- **New: CWT13-vwapstretch-z05-long now has a history kernel** (`cwt_live_lib.b2(z=0.5, long)` on the lab frame plus
  the 09:35-09:45 head rows, window 11:00-15:00, ADV >= 95M, first signal per symbol-day). Parity: 18,135 trades,
  -0.0796R over all open months = `research/bdi/cwt/live/verify.json` exactly; sim R = production R (mean |d| 0.00003R).
- **Parity:** every parent equals the production R (mean |d| <= 0.00005R, 100% within 0.01R).
- config/, mcf/ and workflows are untouched. 22 `top5-tune` lines in research/backlog.jsonl (5 grids, status failed;
  17 beats-parent, status rework); BACKLOG.md re-rendered.

**Rule changes inside the live window (research/ledger.jsonl):** GX1 5-minute clock gate (10-27); Primary per-setup
-2R daily stop (10-28, affects MF4-FD); **Testing 1/2 CF cost filter, skip if stop-exit cost > 0.15R (from 10-30;
affects CWT13, NM-HL, NM-AR-AM, exhaustion_short)**; moves on 10-30 (pdl p05 pair to Graveyard, L3 pair to Primary,
R2A legs into T2), 11-01 (NS3-FD, RW4-FD to Graveyard) and 11-02 (MF3-FD, MF5-FD to Graveyard). So CWT13's 76 trades
on 10-30 / 11-02 (vs 9 on 10-27..10-29) were all taken under CF, and the earlier 9 were not; live figures below mix
the two regimes.

## Failures first

| setup (acct) | beat parent | parent exp TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|
| Stretched Below VWAP Bounce, `CWT13-vwapstretch-z05-long` (T2) | 8 | -0.068 / -0.079 (-4.53) | G16 CF stop-cost <= 0.15R: +0.034 (6.08) | -0.041 / -0.064 |
| `NM-HL-T75-pm-long` (T2) | **0** | +0.052 / -0.003 (1.08) | G06 clock exit 14:30: +0.012 (1.06) | +0.068 / +0.003 |
| Afternoon Blow-off Short, `exhaustion_short` (T1) | **0** | -0.053 / +0.105 (0.09) | G16 CF: +0.018 (1.81) | -0.030 / +0.109 |
| Early Sellers, Strong Heat (all day), `MF4-h40-open-flowsell-FD` (Primary) | 9 | -0.119 / -0.071 (-5.04) | G16 CF: +0.052 (8.03) | -0.074 / -0.041 |
| Gap-Down Capitulation Buy, `NM-AR-AM-gapdown-capitulation-long` (T2) | **0** | **+0.328 / +0.210 (2.23)**, in-sample | G04 target x1.5: +0.117 (1.69) | +0.511 / +0.237 |

- **CWT13 (first history check):** the backtest parent loses -0.072R on 15,090 TRAIN+VALID trades (win 64.3% vs
  break-even 69.2%, WF 6% of months positive, -0.007R vs random). It is a market-direction bet like the others: TRAIN
  SPY up sessions +0.019R, down sessions -0.093R. **The CF filter already live in Testing 2 is the best knob**
  (+0.038R TRAIN / +0.031R VALID vs parent, t 6.08, keeps 73% of trades) but the setup still loses -0.049R. Second-best:
  window after 13:00 (G12, -0.037R, t 4.01) and stop x2.0 at the same $ (G02, -0.033R, t 4.00). Live -0.179R on 85
  trades agrees with the backtest sign.
- **MF4-FD (Primary):** same story as top5_1026 - wider stops (G01 / G02 t 5.80 / 6.51) and CF (t 8.03) beat the parent,
  every row negative in TRAIN. Losses sit in SPY up sessions (TRAIN -0.225R vs -0.005R down). Not a candidate. CF is a
  Testing-only rule today; this run does not propose it for Primary (would need the owner and the full bar; still < 0R).
- **NM-HL-T75:** parent +0.030R (TRAIN +0.052 / VALID -0.003, t 1.08, WF 65%); no knob beats it. CF (G16) is a no-op
  (ADV >= 125M names), G13 keeps 32 trades (nearly all signals are down > 2% from open). The 11-02 live loss (24 trades
  -9.8R, 1 session) is a one-bet day; G15 (first 5 per session) lowers avg R in history (t -1.79).
- **exhaustion_short:** parent flat (+0.004R; TRAIN -0.053 / VALID +0.105). Wider stops and CF are positive pooled
  (+0.027 / +0.022 / +0.021R) but lose in VALID vs the parent. 0 beat parent.
- **NM-AR-AM:** the only clearly positive parent (+0.278R, 1,280 trades; +0.127R without its best day, +0.173R vs random)
  but it was **mined on this history** (swarm1017, in-sample) and every signal fires 10:50-10:55. No knob beats it.
  Live 15 trades -0.025R (10-30: 5 of 5 stopped); 15 trades is not evidence.
- No-op / empty rows (counted in N): NM-AR-AM G11 (before 10:30) 0 trades, G12 = parent; NM-HL G16 = parent.

**Recurring live loser patterns tested:**
- **One-bet days** (CWT13 55 trades on 10-30 and 21 on 11-02; NM-HL 24 trades -9.8R on 11-02): G15 first 5 per session
  beats the parent only on CWT13 / MF4-FD (t 3.92 / 4.19) and keeps the rows negative; it lowers NM-HL, NM-AR-AM and
  exhaustion_short. Capping counts does not pick the better trades.
- **Never-worked losers** (live: CWT13 23 of 39 losers never > +0.2R, NM-HL 10 of 18, exhaustion_short 7 of 14): G07
  60-min time stop is flat or worse on all 5 (t -1.91..0.47).
- **Late-afternoon longs** (live CWT13 14:00-16:00 52 trades -0.093R; NM-HL 26 trades -0.217R): in history CWT13's best
  slice is 13:00-14:00 (+0.020R) and 14:00+ is -0.101R; G12 (after 13:00) beats the parent but stays negative.
  NM-HL G12 (after 14:00) is lower than the parent (t -0.99).
- **Give-back** (live losers gave back 1.0-1.4R from their best): G05 half at 0.5 x target + BE raises win rates 7-12
  points; beats the parent on CWT13 / MF4-FD (still negative), lowers NM-AR-AM (t -4.32).
- **Longs into a falling index** (11-02: 110 T2 longs into the slide): G10 (skip SPY down > 0.5%) and G14 (skip SPY
  below open) lower avg R on CWT13, NM-HL and NM-AR-AM; G14 only "beats" CWT13's parent by cutting 77% of trades.

## Selection
Live paper trades 10-27..10-30, 11-02 (run_id 1; S6 and GEN-* out; `live_rank.csv`).

- **Rotated out:** the four CWT14 pdl longs (233 / 160 / 156 / 97) and the R2A long leg (19) - pdl lineage
  exhaustively tuned (pdl1030/b/c, 245 configs, 0 pass); Graveyard: CWT12-coil-k4 (150), MF3-FD (43), MF5-FD (31),
  RW4-FD (25), NS3-FD (19); tuned in the last 3 runs with no change since: RW7-FD (94), exhaustion_short-FD (62),
  L3-fromopen-FD (52), L3-rsi5hi-FD (23), NS3V1 (19), RW5-FD (18), RW1-FD (18), NS1-FD (14); MF5 (non-FD, 17; same
  signal as MF5-FD tuned 10-30); intraday_momentum (14; classic, no lab kernel).
- **Scored:** CWT13-z05-long (85, first kernel), NM-HL-T75 (35, first tune), exhaustion_short (18; last top5_1027),
  MF4-FD (15; last top5_1026), NM-AR-AM (15; last top5_1027).

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day | bt win / BE win / exp | bt w/o best day | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|
| CWT13-z05-long | 85 | 54.1 / 67.0% | +0.46 / -0.93 | -0.179 | -0.198 (total < 0) | 64.3 / 69.2% / -0.072 | -0.075 | 23 of 39 |
| NM-HL-T75 | 35 | 48.6 / 65.8% | +0.40 / -0.77 | -0.201 | -0.357 (total < 0) | 66.4 / 64.0% / +0.030 | +0.019 | 10 of 18 |
| exhaustion_short | 18 | 22.2 / 52.9% | +0.77 / -0.87 | -0.502 | -0.807 (total < 0) | 52.6 / 52.3% / +0.004 | -0.022 | 7 of 14 |
| MF4-FD | 15 | 46.7 / 69.0% | +0.48 / -1.08 | -0.348 | -0.472 (total < 0) | 61.0 / 68.3% / -0.101 | -0.105 | 3 of 8 |
| NM-AR-AM | 15 | 60.0 / 61.5% | +0.66 / -1.05 | -0.025 | -0.517 (10-29 = 3.25R of a -0.37R total) | 65.9 / 51.8% / +0.278 | +0.127 | 4 of 6 |

- No live record here is carried by a big day; all five are negative in total over the window.
- **Conversion:** CWT13 and MF4-FD sit 5-7 points under break-even in the backtest (0.5R target vs 1R stop needs ~69%);
  NM-HL is 2.4 points above it; exhaustion_short is at it; NM-AR-AM well above it (in-sample).
- **Time of day (backtest):** CWT13 earns only 13:00-14:00 (+0.020R); MF4-FD loses in every slice; exhaustion_short
  13:00-14:00 -0.007 / 14:00+ +0.022R; NM-HL slightly positive in every slice.
- **Random control** (same minute, parent geometry): NM-AR-AM +0.173R, NM-HL +0.092R, exhaustion_short +0.057R beat
  random; CWT13 -0.007R and MF4-FD -0.017R do not.

## 2. Grid readout (all 85 rows in `results.csv`)

| knob | beats parent | note |
|---|---|---|
| stop x1.5 / x2.0 at same $ (G01 G02) | 4 of 10 (CWT13, MF4-FD) | lowers NM-AR-AM and NM-HL; exhaustion_short positive pooled, loses in VALID vs parent |
| target x0.75 / x1.5 (G03 G04) | 0 | NM-AR-AM G04 +0.396R (t 1.69 vs parent) |
| half at 0.5 x target + BE (G05) | 2 (CWT13, MF4-FD) | win rate +7-12 points; NM-AR-AM t -4.32 |
| clock exit / 60-min time stop (G06 G07) | 0 | |
| limit 0.1R / next-bar entry (G08 G09) | 0 | limit skips 28-43% of trades |
| SPY 0.5% veto (G10) | 0 | |
| window halves (G11 G12) | 3 (CWT13 G12, MF4 G11 G12) | all still negative in TRAIN |
| stock down > 2% skip (G13) | 2 (CWT13, MF4-FD) | NM-HL keeps 32 trades |
| SPY-side filter / one per symbol-day (G14) | 2 (CWT13, MF4-FD) | cuts 51-77% of trades |
| first 5 per session (G15) | 2 (CWT13, MF4-FD) | |
| CF stop-cost <= 0.15R (G16) | 2 (CWT13 t 6.08, MF4-FD t 8.03) | no-op on NM-HL; slight help on exhaustion_short (t 1.81) |

## 3. Bars
- **Beats parent (17):** CWT13 G01 G02 G05 G12 G13 G14 G15 G16; MF4-FD G01 G02 G05 G11 G12 G13 G14 G15 G16. All negative
  in TRAIN and VALID.
- **Testing bar (BAR90):** 0 met it. 23 of 80 variants have exp > 0 in TRAIN and VALID (14 NM-AR-AM rows incl. G12 = parent, in-sample,
  none beating the parent; 8 NM-HL rows and 1 exhaustion_short row, none beating the parent at the bar). Best TRAIN+VALID t of
  any row is 2.48 (NM-AR-AM G02), under 4.16.

## Queued (not scored tonight)
- CWT13's other live legs (z05-short, z075-long / short) can now reuse this kernel (`scan_1102.cwt13_rows`, change z / side).
- CF's effect on CWT13 is now measured in history (+0.034R, still < 0); the live CF window (2 sessions) is too short to read.

## Files
- `live_rank.py` -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py`: rebuilds gates1021's live-shaped signal cache (scratch, ~5 min) for the 4 cached setups.
- `scan_1102.py`: cached entries + the CWT13 kernel, exits from the top5_1028 simulator (~6 min; scratch trades file
  deleted after the report). `report_1102.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`, `report_out.txt`.
  `make_proposals.py` -> `backlog_proposals.jsonl`.

Educational only - not financial advice.
