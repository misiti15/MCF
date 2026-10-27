# Top-5 setup execution tune, 2026-10-27 (tenth run): FAILED the Testing bar, 0 of 81; 14 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-21..10-27 (rule 7). They are a diagnosis, not evidence.
  10-26 started ~10:39 ET; GX1 (5-minute clock gate) went live 10-27, so 10-27 counts run higher (485 trades in the
  three accounts vs 294-377 on the other days).
- History numbers are **backtests** on the open two-year history, production + time-of-day costs and x3 on the
  extended tier in, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was
  **never loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 81** (coil-k4 13, pdl-p10-lowvol 14, NM-AR-AM 18, exhaustion_short 18, L3-lowdist-FD 18),
  plus 5 parent reference runs. Study bar max(1.5, sqrt(2 ln 81)) = **2.96**; setup bars 2.26 / 2.30 / 2.40.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 14 variants beat
  their parent, and every one still fails the Testing bar: 13 still lose after costs in TRAIN and VALID, and the
  14th (L3-lowdist-FD E14, skip when SPY is up) is +0.048R in TRAIN but -0.004R in VALID (t -0.04), and -0.41R in up
  sessions.
- **Parity:** the two CWT parents reproduce top5_1021 exactly (coil-k4 -0.0599R, pdl-p10-lowvol -0.0947R without the x3
  tier). The three cached parents equal the cached production R on every row (mean |d| <= 0.00005R, 100% within 0.01R).
- config/, mcf/ and workflows are untouched. 19 `top5-tune` lines appended to research/backlog.jsonl (5 grids, status
  failed; 14 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | variants | beat parent | parent exp TRAIN / VALID (t VALID) | best variant (d R; t) | best variant TRAIN / VALID |
|---|---|---|---|---|---|
| Coil Under the High (4 bars), CWT12-coil-k4-long (T2; K4 Graveyard decision open) | 13 | 4 | -0.059 / -0.064 (-3.76) | K01 stop x2.0: +0.033 (5.85) | -0.027 / -0.029 |
| Failed Prior-Day-Low Break Long (0.1 ATR, low volume), CWT14-failbrk-pdl-p10-lowvol-long (Primary to 10-27, T2 from 10-28) | 14 | 7 | -0.097 / -0.097 (-5.09) | K02 stop x2.5: +0.060 (8.55) | -0.036 / -0.037 |
| Gap-Down Capitulation Buy (near-miss), NM-AR-AM-gapdown-capitulation-long (T2) | 18 | 0 | **+0.328 / +0.210 (2.08)**, in-sample | E09 target 1.5: +0.117 (1.69) | +0.511 / +0.237 |
| Afternoon Blow-off Short, exhaustion_short (T1) | 18 | 0 | -0.053 / +0.105 (1.35) | E04 stop x1.25: +0.012 (1.17) | -0.024 / +0.085 |
| L3-gap-slope-lowdist-FD (T1; no display name in setup_names.yaml) | 18 | 3 | -0.149 / -0.093 (-1.42) | E05 stop x1.5: +0.054 (3.06) | -0.098 / -0.036 |

- **NM-AR-AM is the only positive parent, and that is not new evidence.** Its +0.278R on 1,280 TRAIN+VALID trades
  (up +0.27 / down +0.28, +0.17R vs random, +0.127R without its best day) is the same sample swarm1017 fitted it on
  (plateau picked on VALID; half of TRAIN in Apr 2025). Its forward follow-up failed (swarm1017/followup: 88 trades
  -0.254R), and live it is 25 trades -0.50R on 2 days. No execution knob beats it. Its signals all fall 10:30-11:00
  (60-minute return), so window rows E11 / E13 equal the parent and E12 (until 10:30) is empty. All three are counted.
- **The other four parents are market-direction bets** (backtest, SPY up / down sessions): coil-k4 +0.015 / -0.167;
  pdl-p10-lowvol -0.021 / -0.160; exhaustion_short -0.062 / +0.092; L3-lowdist-FD -0.297 / +0.127. No execution knob
  turns the losing side positive. This is the same finding as the last nine runs.

**Recurring live loser patterns tested:**
- **coil-k4 "+1R target would have made +21.9R today" (bdi1027).** On two years it is worse: K03 target 1.0 with the
  scale-out kept is d -0.024R (t -11.5), and K13 target 1.0 with no scale-out is d -0.023 / -0.037R (t -2.24). It fails
  in down sessions (-0.30R).
- **coil-k4 late entries** (live: 10:30-11:30 137 trades -0.095R, 11:30+ -0.30R). K12 window end 10:30 beats the parent
  (d +0.045 / +0.051R, t 4.68), but it keeps 24% of trades and still loses -0.059R.
- **"Never worked" losers** (live: coil-k4 44 of 62, pdl-p10-lowvol 14 of 26, NM-AR-AM 11 of 18, L3-lowdist 7 of 10).
  The 15-minute time stop is flat everywhere: K04 / K05 / E15 t -1.84..+0.69. In history, cutting the losers also cuts
  the slow winners. This is the same answer as top5_1026 C05.
- **pdl-p10-lowvol 10:10-poll burst before the 10:17 index low** (10-27). K13 skip 10:00-10:29 beats the parent (d +0.036
  / +0.032R, t 5.59), but it is -0.090R. Burst skips themselves already failed (bdi1027-pdl-long-burst-skip).
- **Shorts into an index reversal** (exhaustion_short 0 of 6 on 10-27). E18 skip when SPY up > 0.5% is worse on
  exhaustion_short (d -0.0013 / -0.044R, t -0.90). On L3-lowdist-FD it is t 1.51, which is under the bar.

## Selection
Live paper trades 10-21, 22, 23, 26, 27 (run_id 1; S6 and GEN-* out; `live_rank.csv`). Account membership comes from
`docs/live/assignments.json` (last change 10-27 16:42 ET). Graveyard setups are out (pdh-p10-short 65, coil-k6 48,
pdh-p05-lowvol-short 44).

- **Rotated out: tuned in top5_1022 / 1023 / 1026, no setup or exit change since.** pdl-p05-long (272), pdl-p05-lowvol
  (159), pdl-p10 (110), L3-fromopen-FD (72), RW7-FD (71), exhaustion_short-FD (61), RW5-FD (47), NS3-FD (40), MF2-FD
  (34), MF3-FD (34), RW3-FD (34), RW4-FD (33), L3-rsi5hi-FD (29), RW1-FD (28), MF5-FD (24), MF4-FD (23).
- **Cannot be backtested: CWT13-vwapstretch-z05-long** (40, Stretched Below VWAP Bounce, Testing 2 since 10-27). It is
  not in the two-year signal cache (it needs 09:35-09:45 head rows) and the harness has no CWT13 kernel. This is the third
  run in a row that skips it.
- **Scored:** coil-k4 (176, T2; last tuned top5_1021), pdl-p10-lowvol (78, Primary through 10-27; last tuned top5_1021),
  NM-AR-AM (25, T2; first tune), exhaustion_short (25, T1; the 13:00-15:00 original, first tune), L3-lowdist-FD (18,
  T1; first tune).

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day (share) | bt win / BE win / exp | bt w/o best day | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|
| coil-k4 | 176 | 64.8 / 69.4% | +0.39 / -0.88 | -0.059 | -0.123 (total < 0) | 69.9 / 74.5% / -0.061 | -0.063 | 44 of 62 |
| pdl-p10-lowvol | 78 | 66.7 / 65.4% | +0.49 / -0.93 | +0.017 | -0.034 (10-23, 264%: **1 day**) | 64.0 / 70.4% / -0.097 | -0.099 | 14 of 26 |
| NM-AR-AM | 25 | 28.0 / 55.1% | +0.82 / -1.01 | -0.496 | -0.433 (total < 0; 2 days) | 65.9 / 51.8% / +0.278 | +0.127 | 11 of 18 |
| exhaustion_short | 25 | 68.0 / 54.7% | +0.68 / -0.82 | +0.198 | -0.602 (10-26, 197%: **1 day**) | 52.6 / 52.3% / +0.004 | -0.022 | 4 of 8 |
| L3-lowdist-FD | 18 | 44.4 / 55.5% | +0.83 / -1.03 | -0.204 | -0.855 (total < 0) | 48.2 / 54.9% / -0.129 | -0.153 | 7 of 10 |

- **Conversion problem.** coil-k4 with its 0.35R scale-out needs 74.5% wins in the backtest and gets 70%.
  pdl-p10-lowvol needs 70% and gets 64%. L3-lowdist-FD needs 55% and gets 48%. exhaustion_short is at break-even
  (52.6 vs 52.3%).
- **Time of day (backtest):** L3-lowdist-FD loses most before 11:30 (10:00-10:30 -0.37R, 10:30-11:30 -0.26R), and it is
  positive only 14:00-15:00 (+0.10R, n 400). Its "from 10:30" row (E11) is t 2.19, under the bar. pdl-p10-lowvol is
  negative in every hour. coil-k4 is flat across its two buckets.
- **Random control** (same minute, same mechanics): coil-k4 +0.006R and exhaustion_short +0.057R beat random.
  pdl-p10-lowvol -0.019R and L3-lowdist -0.011R are worse than random.

## 2. Grid readout (all 86 rows in `results.csv`)

| knob | d range (t) | note |
|---|---|---|
| **wider stop at the same $ (K01 K02 E04 E05)** | +0.012..+0.060 (1.04-8.55) | beats the parent on coil-k4, pdl-p10-lowvol and L3-lowdist. Win rate +5-9 pts, all still negative. Worse on NM-AR-AM (t -2.1..-2.3). Same finding as every run since 10-19. pdl-p10-lowvol curve: x1.5 (1021) -0.061, x2.0 -0.044, x2.5 -0.037R, still rising and still negative |
| windows / skips (K07 K08 K12-K14, E11-E13) | -0.064..+0.047 | beat the parent on coil-k4 and pdl-p10-lowvol; all still -0.06..-0.10R |
| SPY / stock filters (K08-K11, E14, E18) | -0.33..+0.17 | pdl K09 / K10 beat the parent (t 2.62 / 3.08), still -0.098R; L3-lowdist E14 +0.037R pooled, VALID -0.004R |
| time stops (K04 K05, E01 E02 E15) | -0.045..+0.013 (-1.93..0.84) | flat to worse |
| targets (K02 K03 K13, K03 K04 pdl, E08 E09) | -0.024..+0.18 | coil-k4 bigger targets clearly worse (t -11..-14); NM-AR-AM target 1.5 t 1.69 (< bar) |
| scale-out / breakeven (E06 E07) | -0.097..+0.004 (-4.32..-0.51) | worse on all three cached setups |
| limit entry 0.1 better (K11 K12 E17) | per parent trade | coil-k4 K11 beats the parent per signal (t 2.40) because it skips 44% of trades, -0.084R; worse R per trade elsewhere |
| tighter stop x0.85 (E03), wait one bar (E10), clock exits (K06 K07 E16) | -0.032..+0.046 | flat to worse |

## 3. Bars
- **Beats parent (14):**
  - coil-k4: K01 K07 K11 K12.
  - pdl-p10-lowvol: K01 K02 K08 K09 K10 K13 K14.
  - L3-lowdist-FD: E04 E05 E14.
  - NM-AR-AM and exhaustion_short: none.
- **Testing bar** (exp > 0 on TRAIN and VALID, VALID t >= 2.96, up and down sessions > 0, ex-best-day > 0, beats
  random): **0 met it.** No Testing proposal; no Primary change proposed. No holdout scored.
- 16 of 81 variants have exp > 0 in TRAIN and VALID separately, and all 16 are NM-AR-AM rows (in-sample; none beats its
  parent). 23 are positive pooled: those 16 plus NM-AR-AM E14, L3-lowdist E14 (VALID < 0) and five exhaustion_short
  rows (TRAIN < 0).

## Queued (not scored tonight)
- CWT13-vwapstretch-z05-long needs a CWT13 kernel in the history harness (09:35-09:45 head rows) before it can be tuned.
  It has been skipped three runs running.
- The CWT14 pdl stop curve is still rising at x2.5 on pdl-p10-lowvol (-0.037R). One paired x2.5-x3.0 round covers all
  CWT14 pdl longs (queued since top5_1023).

## Files
- `live_rank.py` (top5_1026's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py`: rebuilds gates1021's live-shaped signal cache (scratch) for NM-AR-AM, exhaustion_short and
  L3-lowdist-FD (gates1021 `scan.month_job` unchanged, ~10 min).
- `scan_1027.py`: CWT entries come from the top5_1021 kernels, and cached entries come from the rebuilt cache. Exits use
  the top5_1026 simulator. The scan takes ~8 min, and the scratch trades file is deleted.
- `report_1027.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt` (with the parity gates).
  `make_proposals.py` -> `backlog_proposals.jsonl`.

Educational only - not financial advice.
