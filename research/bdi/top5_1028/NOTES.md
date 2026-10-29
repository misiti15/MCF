# Top-5 setup execution tune, 2026-10-28 (eleventh run): FAILED the Testing bar, 0 of 70; 17 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-22..10-28 (rule 7). They are a diagnosis, not evidence.
  10-26 started ~10:39 ET; GX1 (5-minute clock gate) is live from 10-27, so 10-27 / 10-28 counts run higher.
- History numbers are **backtests** on the open two-year history, production + time-of-day costs and x3 on the
  extended tier in, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was
  **never loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 70** (14 per setup x 5), plus 5 parent reference runs. Study bar max(1.5, sqrt(2 ln 70)) =
  **2.91**; setup bar sqrt(2 ln 14) = 2.30.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 17 variants beat
  their parent; all 17 still lose after costs over TRAIN+VALID pooled. The closest two (RW1-FD F02 and
  exhaustion_short-FD F02, stop x2.5) are positive only in VALID (+0.0005R / +0.0011R, t 0.03 / 0.06) and lose in TRAIN
  and in up sessions.
- **Parity:** all five parents equal the cached production R (mean |d| <= 0.00008R, >= 99.99% within 0.01R).
- config/, mcf/ and workflows are untouched. 22 `top5-tune` lines appended to research/backlog.jsonl (5 grids, status
  failed; 17 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | variants | beat parent | parent exp TRAIN / VALID (t VALID) | best variant (d R; t) | best variant TRAIN / VALID |
|---|---|---|---|---|---|
| RW7-gapdn-bounce-early-short-FD (T1; no display name) | 14 | 4 | -0.083 / -0.035 (-1.01) | F02 stop x2.5: +0.045 (3.99) | -0.026 / -0.008 |
| exhaustion_short-FD (T1+T2; no display name) | 14 | 4 | -0.110 / -0.028 (-0.90) | F01 stop x2.0: +0.047 (5.00) | -0.047 / -0.003 |
| Early Sellers into a Pop (all day), MF3-open-flowsell-rsi5hi-FD (T1, ex-primary) | 14 | 6 | -0.099 / -0.055 (-1.83) | F01 stop x2.0: +0.044 (5.07) | -0.049 / -0.021 |
| RW1-gapdn-bounce-flowsell-short-FD (T2; no display name) | 14 | 3 | -0.073 / -0.011 (-0.30) | F02 stop x2.5: +0.038 (2.87) | -0.019 / +0.0005 |
| RW4-ns3-adv150-short-FD (T1+T2; no display name) | 14 | **0** | **+0.006 / -0.001** (-0.03) | F01 stop x2.0: +0.022 (1.34) | +0.024 / +0.024 |

- **Every parent is a market-direction bet** (backtest, SPY up / down sessions): RW7-FD -0.247 / +0.080; exhaustion-FD
  -0.180 / +0.064; MF3-FD -0.221 / +0.049; RW1-FD -0.230 / +0.097; RW4-FD -0.087 / +0.054. No execution knob turns the
  up-session number positive (best: RW4-FD F02 -0.026). Same finding as top5_1022 and the last ten runs.
- **RW4-FD is still the one flat parent** (+0.0025R/trade, 10,569 trades, +0.067R vs same-minute random shorts, -0.016R
  without its best day). Its wider stops are positive in TRAIN and VALID (F01 +0.024 / +0.024R, F02 +0.022 / +0.023R),
  but the improvement is t 1.34 / 1.06 (bar 2.30) and the VALID t is 1.11 / 1.18 (bar 2.91). This is the third near
  miss on the same knob (top5_1022 E04/E05 t 1.65 / 1.50). Live it is 31 trades -0.635R; 10-28 alone is -18.0R (16
  of 16 lost, bdi1028), which is the NS3-family one-bet pattern already in the backlog (nightly-1028).
- **RW4-FD F11 (until 11:30)** is +0.098R on 1,194 trades (TRAIN +0.014 / VALID +0.206, VALID t 2.82) but it does
  not beat the parent per signal (t 0.30) and loses in up sessions (-0.017). Not a candidate; noted only because it
  is the largest positive row.
- **RW4-FD F10 keeps 0 trades**: every RW4 signal is a stock already down > 2% from open. Counted in N.

**Recurring live loser patterns tested:**
- **Shorts into an index reversal / grind up** (bdi1028: shorts lost everywhere on a slow grind up). F08 skip when SPY
  up > 0.5% beats the parent only on MF3-FD (t 2.39) and still loses -0.078R; elsewhere t 1.01..2.24. The up-session
  loss is not confined to the > 0.5% days.
- **Morning short losers** (live: MF3-FD < 10:30 5 trades -1.05R, 10:30-11:30 11 trades -0.68R; exhaustion-FD
  10:30-11:30 20 trades -0.37R; RW4-FD < 11:30 12 trades -1.0R). In history the morning is not the problem for RW1 /
  RW4 / RW7 (window end 11:30 is their *best* row). exhaustion-FD's morning is its worst time (10:00-10:30 -0.133R);
  F12 window start 11:30 beats the parent (d +0.032 / +0.079R, t 3.84) but is -0.083R in TRAIN.
- **"Never worked" losers** (live: RW7-FD 19 of 48, exhaustion-FD 15 of 41, MF3-FD 11 of 24). A 120-minute time stop
  for trades under +0.25R (F14) is flat on all five (t -1.61..+0.04). Same as the 15/30/60-minute rows of top5_1022.
- **Give-back** (live losers gave back 1.1-1.4R from their best). Smaller target 0.5R (F03) raises the win rate 12-15
  points and loses R on 3 of 5 (t -1.48..+1.44). Target 2.0R (F04) is worse on all 5.

## Selection
Live paper trades 10-22, 23, 26, 27, 28 (run_id 1; S6 and GEN-* out; `live_rank.csv`). Account membership comes from
`docs/live/assignments.json` (last change 10-28 18:00 ET).

- **Out - Graveyard:** CWT12-coil-k4-long (236; owner K4-2, Graveyard from 10-29), pdh-p10-short (23), coil-k6 (17).
- **Rotated out: tuned in top5_1023 / 1026 / 1027, no setup or exit change since.** pdl-p05-long (309), pdl-p05-lowvol
  (183), pdl-p10 (140), pdl-p10-lowvol (79), L3-fromopen-FD (74), RW5-FD (50), RW3-FD (33), MF2-FD (33),
  exhaustion_short (32), L3-rsi5hi-FD (30), NS3-FD (25), MF4-FD (24), NM-AR-AM (22), L3-lowdist-FD (17).
- **Cannot be backtested: CWT13-vwapstretch-z05-long** (40, T2). No CWT13 kernel in the harness; fourth run skipped.
- **Not re-tested:** the high-frequency half-R cost-floor idea (research/bdi/hf1027); none of tonight's setups is half-R.
- **Scored (all last tuned top5_1022):** RW7-FD (90, T1), exhaustion_short-FD (64, T1+T2), MF3-FD (35, T1), RW1-FD
  (31, T2), RW4-FD (31, T1+T2). Tonight's grid uses only knobs top5_1022 did not score on them.

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day (share) | bt win / BE win / exp | bt w/o best day | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|
| RW7-FD | 90 | 46.7 / 52.6% | +0.65 / -0.72 | -0.081 | -0.113 (total < 0) | 48.7 / 52.7% / -0.065 | -0.070 | 19 of 48 |
| exhaustion_short-FD | 64 | 35.9 / 48.9% | +0.86 / -0.83 | -0.219 | -0.338 (total < 0) | 49.3 / 53.5% / -0.076 | -0.081 | 15 of 41 |
| MF3-FD | 35 | 31.4 / 60.2% | +0.59 / -0.89 | -0.424 | -0.567 (total < 0) | 48.1 / 53.1% / -0.084 | -0.087 | 11 of 24 |
| RW1-FD | 31 | 74.2 / 55.3% | +0.77 / -0.96 | +0.328 | +0.296 (10-22, 53%: **1 day**) | 49.2 / 52.3% / -0.050 | -0.054 | 3 of 8 |
| RW4-FD | 31 | 22.6 / 67.8% | +0.45 / -0.95 | -0.635 | -0.722 (total < 0; 10-28 -18.0R) | 51.2 / 51.0% / +0.003 | -0.016 | 5 of 24 |

- **Conversion problem.** Every parent is 3-5 points under its break-even win rate in the backtest except RW4-FD
  (51.2 vs 51.0%). Wider stops at the same $ add 4-9 win-rate points and narrow the gap, but break-even rises with them.
- **Stop curve (queued since top5_1022): still rising at x2.5 on four of five** (RW7 -0.065 -> x2.0 -0.028 -> x2.5
  -0.020; exhaustion -0.076 -> -0.029 -> -0.019; MF3 -0.084 -> -0.039 -> -0.031; RW1 -0.050 -> -0.018 -> -0.012). It
  approaches zero from below; it does not cross it in TRAIN on any setup.
- **RW1-FD live +0.33R on 31 is a 1-day record** (10-22 = 53% of its R) and its two-year backtest loses (-0.050R).
- **Random control** (same minute, t1s1 short): RW4-FD +0.067R, RW1-FD +0.030R, RW7-FD +0.016R, exhaustion-FD +0.006R
  beat random; MF3-FD -0.004R does not.

## 2. Grid readout (all 75 rows in `results.csv`)

| knob | d range (t) | note |
|---|---|---|
| **wider stop x2.0 / x2.5 at the same $ (F01 F02)** | +0.020..+0.057 (1.06-5.07) | beats the parent on 4 of 5; all still negative over TRAIN+VALID except RW4 (+0.023, below bar) |
| window end 11:30 (F11) | +0.009..+0.055 (0.30-3.62) | beats the parent on RW7 / MF3 / RW1 (t 2.62-3.62); still -0.020..-0.079R |
| window start 11:30 / skip 10:30-11:29 (F12 F13) | -0.011..+0.062 (-1.72..3.84) | beat the parent on exhaustion-FD (both) and MF3 (F12); still negative |
| SPY / stock filters (F08 F09 F10) | -0.003..+0.021 (-0.09..2.66) | MF3 F08/F09, RW7 F10 beat the parent; all still negative |
| clock exits 12:00 / 14:00 (F05 F06) | -0.014..+0.016 (-1.97..2.19) | flat; none beats the parent |
| targets 0.5 / 2.0 (F03 F04) | -0.021..+0.015 (-2.19..1.44) | flat to worse; 2.0R worse on all 5 |
| limit entry 0.1R better (F07) | +0.005..+0.017 per parent signal (0.45-1.66) | skips 35-48% of trades; R per trade worse except RW4 |
| time stop 120 min < +0.25R (F14) | -0.003..+0.000 (-1.61..0.04) | flat |

## 3. Bars
- **Beats parent (17):**
  - RW7-FD: F01 F02 F10 F11.
  - exhaustion_short-FD: F01 F02 F12 F13.
  - MF3-FD: F01 F02 F08 F09 F11 F12.
  - RW1-FD: F01 F02 F11.
  - RW4-FD: none.
- **Testing bar** (exp > 0 on TRAIN and VALID, VALID t >= 2.91, up and down sessions > 0, ex-best-day > 0, beats
  random): **0 met it.** No Testing proposal; no Primary change proposed. No holdout scored.
- 4 of 70 variants have exp > 0 in TRAIN and VALID separately (RW4-FD F01 F02 F07 F11); none beats its parent at the
  bar and all four lose in up sessions. 7 are positive pooled.

## Queued (not scored tonight)
- CWT13-vwapstretch-z05-long still needs a CWT13 kernel in the history harness (fourth run skipped).
- The short t1s1 stop curve is still rising at x2.5 on RW7 / exhaustion / MF3 / RW1 and still negative; together with
  the CWT14 pdl curve (top5_1027) a single "stop x3.0 at same $" round across all live t1s1 setups would close it.

## Files
- `live_rank.py` (top5_1027's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py`: rebuilds gates1021's live-shaped signal cache (scratch, ~2 min) for the 5 setups.
- `scan_1028.py`: entries from the rebuilt cache, exits from the top5_1027 simulator (~6 min; scratch trades file
  deleted after the report).
- `report_1028.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`, `report_out.txt` (with the parity gate).
  `make_proposals.py` -> `backlog_proposals.jsonl`.

Educational only - not financial advice.
