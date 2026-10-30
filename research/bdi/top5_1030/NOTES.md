# Top-5 setup execution tune, 2026-10-30 (twelfth run): FAILED the Testing bar, 0 of 75; 7 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-26..10-30 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history: production + time-of-day costs, x3 on the extended
  tier, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never
  loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 75** (15 per setup x 5), plus 5 parent rows and 1 NS3V1 parity row (P0, not counted).
  Setup bar sqrt(2 ln 15) = 2.33; study bar sqrt(2 ln 75) = 2.94; **Testing bar = rule 22 BAR90** on lineage N:
  L3-rsi5hi-FD 4.50, NS3-FD / NS3V1 4.41, MF5-FD / NS1-FD 4.72 (conservative: MarcoFlow discovery N unrecorded, the
  backlog's largest lineage was used), plus walk-forward months positive >= 54%.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 7 variants beat
  their parent; all 7 still lose in TRAIN. Best TRAIN+VALID t of any row is 2.98 (NS3V1 G03), far under 4.41.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00004R, 100% within 0.01R).
- config/, mcf/ and workflows are untouched. 12 `top5-tune` lines in research/backlog.jsonl (5 grids, status failed;
  7 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | beat parent | parent exp TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|
| Gap-Down Rebound Overbought Short (all day), `L3-gap-slope-rsi5hi-FD` (Primary from 10-30) | 1 | -0.084 / +0.011 (-1.06) | G01 stop x1.5: +0.030 (2.65) | -0.038 / +0.018 |
| `MF5-flowsell-vwapup-rsi5hi-FD` (T2) | 3 | -0.096 / -0.001 (-2.78) | G02 stop x2.0: +0.033 (2.93) | -0.053 / +0.010 |
| `NS3-failed-vwap-reclaim-short-FD` (T2) | **0** | -0.004 / -0.018 (-0.38) | G01 stop x1.5: +0.022 (2.26) | +0.019 / +0.003 |
| `NS3V1-am-widestop-short` (T2) | **0** | **+0.040 / +0.106 (2.39)** | G04 target x1.5: +0.014 (1.05) | +0.068 / +0.103 |
| `NS1-rsidip-rsi5pop-long-FD` (T1) | 3 | -0.075 / -0.064 (-3.25) | G11 until 11:30: +0.074 per parent signal (3.73) | -0.014 / +0.058 |

- **NS3V1 is the only positive parent** (backtest +0.069R on 1,560 trades, WF 71%, +0.055R without its best day,
  +0.106R vs random t1s1 shorts). It is a near-miss already in Testing 2 as an owner observation, and **no execution knob
  beats it**: wider stops, a 60-min time stop, a 12:00 clock exit, a session cap and the window cuts all lower it.
  Its weak spot is the same market tilt as every short: TRAIN up sessions -0.117R. Live it is 16 trades -0.747R, 13 of
  them on 10-28 (13 of 13 lost, the NS3-family one-bet day already in the backlog). 16 trades is not evidence.
- **NS3-FD is flat** (-0.011R); its 09:50-11:30 slice (G11, +0.086R, TRAIN +0.043 / VALID +0.142) is NS3V1's own window
  and does not beat the parent per signal (t 0.75). G02 stop x2.0 is positive in TRAIN and VALID (+0.021 / +0.014) but
  t 1.0 overall and 1.92 vs the parent (bar 2.33).
- **NS1-FD G11 (window end 11:30)** is the largest improvement (+0.074R per parent signal, t 3.73) but keeps 17% of the
  trades (319), is -0.014R in TRAIN and -0.005R in down sessions. Not a candidate.
- **L3-rsi5hi-FD** (promoted to Primary today): the backtest parent loses (-0.047R; -0.084R TRAIN); its live +0.28R on
  39 trades is **a 1-day record** (10-26 = 74% of R; w/o best day +0.074R). Stop x1.5 / x2.0 at the same $ narrow the
  loss to -0.016 / -0.006R; still negative in TRAIN. No change proposed to the Primary setup.
- **MF5-FD** is a market-direction bet (backtest SPY up / down sessions -0.200 / +0.109); wider stops beat the parent
  (t 2.92 / 2.93) and stay negative in TRAIN.
- No-op / empty rows (counted in N): G13 (skip stock down > 2%) keeps 0 trades on NS3-FD and NS3V1 (every NS3 signal is
  already down > 2%) and is identical to the parent on NS1-FD; G14 (one per symbol-day) is identical on MF5-FD (no refire).

**Recurring live loser patterns tested:**
- **One-bet days** (MF5-FD 14 trades -12.1R on 10-27; NS3-FD 11 trades -10.4R and NS3V1 13 trades -12.0R on 10-28):
  G15 first 5 signals per session lowers avg R on 4 of 5 setups (NS3V1 -0.059 / -0.071R vs parent in TRAIN / VALID,
  t -3.23; NS1-FD slightly up, t 1.97). G14 one entry per symbol-day lowers avg R on L3 / NS3-FD / NS1-FD; on NS3V1 it
  raises R per trade (+0.077R) but loses total R vs the parent (t -1.44). Capping counts does not pick the better trades.
- **Shorts into a rising index** (G10 skip SPY up > 0.5%): beats nothing at the bar (t -1.76..1.82); L3-rsi5hi-FD falls
  to -0.091R. The up-session loss is not confined to the > 0.5% days (same as top5_1028 F08).
- **"Never worked" losers** (live: NS3V1 12 of 14 losers never > +0.2R, MF5-FD 8 of 18): G07 60-min time stop is worse
  on L3 / NS3-FD / NS3V1, flat on MF5-FD and better but under the bar on NS1-FD (t 1.85).
- **Morning losers** (live: MF5-FD 10:00-10:30 5 of 5 lost; NS3V1 09:50-10:30 6 of 6 lost): in history the morning is
  NS3V1's *best* slice (09:50-10:00 +0.172R, 10:00-10:30 +0.092R) and G11 (start 10:30) lowers it (t -2.12); MF5-FD
  G12 (start 11:30) beats nothing (t 2.06 < 2.33).
- **Give-back** (live losers gave back 1.0-1.2R from their best): earlier half exit at BE (G05) raises the win rate 7-13
  points; avg R falls on 3 of 5 and the two that rise (MF5-FD, NS1-FD) stay far below the bar (t 0.30 / 0.32).

## Selection
Live paper trades 10-26..10-30 (run_id 1; S6 and GEN-* out; `live_rank.csv`).

- **Rotated out:** the four CWT14 pdl longs (257 / 172 / 147 / 88; 245 configs today in pdl1030/b/c, 0 pass),
  CWT12-coil-k4 (202, Graveyard), RW7-FD (106), L3-fromopen-FD (90), exhaustion_short-FD (65), MF3-FD (40),
  exhaustion_short (33), RW4-FD (26), L3-lowdist-FD (21), RW1-FD (19), RW5-FD (18) - all tuned in top5_1027 / 1028 /
  swarm15_1029 / p1_1029 with no setup or exit change since.
- **Cannot be backtested:** CWT13-vwapstretch-z05-long (75, T2; -7.8R on 10-30). No CWT13 kernel in the history
  harness; fifth run skipped. It is the largest live setup with no history check.
- **Scored:** L3-rsi5hi-FD (39), MF5-FD (24), NS3-FD (20), NS3V1 (16, first tune), NS1-FD (14, first top-5 tune).

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day (share) | bt win / BE win / exp | bt w/o best day | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|
| L3-rsi5hi-FD | 39 | 84.6 / 64.7% | +0.50 / -0.91 | +0.281 | +0.074 (10-26, 74%: **1 day**) | 66.5 / 69.6% / -0.047 | -0.066 | 3 of 6 |
| MF5-FD | 24 | 25.0 / 56.8% | +0.72 / -0.95 | -0.531 | -0.607 (total < 0) | 49.2 / 53.1% / -0.067 | -0.070 | 8 of 18 |
| NS3-FD | 20 | 30.0 / 67.7% | +0.48 / -1.01 | -0.561 | -0.604 (total < 0) | 50.7 / 51.5% / -0.011 | -0.029 | 5 of 14 |
| NS3V1 | 16 | 12.5 / 64.5% | +0.51 / -0.93 | -0.747 | -0.798 (total < 0) | 65.8 / 59.4% / **+0.069** | +0.055 | 12 of 14 |
| NS1-FD | 14 | 64.3 / 55.7% | +0.39 / -0.49 | +0.076 | +0.034 (10-27, 59%: **1 day**) | 60.2 / 65.6% / -0.070 | -0.077 | 2 of 5 |

- **Conversion:** four of five parents sit 1-5 points under break-even in the backtest; only NS3V1 is above it
  (65.8 vs 59.4%). Wider stops at the same $ add 2-7 win-rate points, break-even rises with them.
- **Time of day (backtest):** L3-rsi5hi-FD loses before 10:30 (-0.245R at 10:00-10:30) and 11:30-13:00; NS3-FD earns
  only before 11:30 and loses 13:00-14:00 (-0.073R, 4,004 trades); NS1-FD earns only 10:30-11:30; MF5-FD loses in every
  slice. Live NS3-FD traded only after 11:30 (twin group: NS3V1 holds the morning symbols).
- **Random control** (same minute, parent geometry): NS3V1 +0.106R, NS3-FD +0.054R, L3-rsi5hi-FD +0.012R, MF5-FD
  +0.012R, NS1-FD +0.001R beat random.

## 2. Grid readout (all 80 rows in `results.csv`)

| knob | beats parent | note |
|---|---|---|
| stop x1.5 / x2.0 at same $ (G01 G02) | 5 of 10 (L3, MF5, NS1) | positive on NS3-FD both periods (below bar); lowers NS3V1 |
| target x0.75 / x1.5 (G03 G04) | 0 | NS3V1 G04 +0.084R (t 1.05 vs parent) |
| half at 0.5 x target + BE (G05) | 0 | win rate +7-13 points, R lower on 3 of 5 |
| clock exit 12:00 / 60-min time stop (G06 G07) | 0 | worse on NS3V1 (t -1.94 / -2.47) |
| limit 0.1R / next-bar entry (G08 G09) | 0 | limit skips 40-55% of trades |
| SPY 0.5% veto (G10) | 0 | t -1.76..2.08 |
| window cuts (G11 G12) | 2 (MF5 G11, NS1 G11) | both still negative in TRAIN |
| stock > 2% skip (G13) | 0 | 0 trades on NS3-FD / NS3V1, no-op on NS1 |
| one per symbol-day / first 5 per session (G14 G15) | 0 | lower total R on every setup where they bind |

## 3. Bars
- **Beats parent (7):** L3-rsi5hi-FD G01; MF5-FD G01 G02 G11; NS1-FD G01 G02 G11. All negative in TRAIN.
- **Testing bar (BAR90):** 0 met it. 16 of 75 variants have exp > 0 in TRAIN and VALID (13 NS3V1 rows, all below
  their parent; NS3-FD G01 G02 G11, none beating the parent at the bar). The best TRAIN+VALID t is 2.98 (NS3V1 G03) vs 4.41.

## Queued (not scored tonight)
- CWT13-vwapstretch-z05-long still needs a CWT13 kernel in the history harness (fifth run skipped; now 75 live trades).
- NS3V1's own record: watch its up-session TRAIN loss; nothing here changes it.

## Files
- `live_rank.py` -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py`: rebuilds gates1021's live-shaped signal cache (scratch, ~4 min) for the 5 setups.
- `scan_1030.py`: entries from that cache, exits from the top5_1028 simulator (~5 min; scratch trades file deleted
  after the report). `report_1030.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`, `report_out.txt`.
  `make_proposals.py` -> `backlog_proposals.jsonl`.

Educational only - not financial advice.
