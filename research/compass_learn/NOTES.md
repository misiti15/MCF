Educational only — not financial advice.

# COMPASS-LEARN round 1 — how accurate is today's compass, and is there a better one? (2026-11-10)

Research only: no config, live compass, dashboard or trading change. Pre-registered in `PLAN.md` (commit 2975e118f,
before any score; no amendments). Locked block 2024-11-01..2025-02-28 never read (filtered inside the parquet read).
Market-only study (SPY / QQQ / IWM / XL* / 200 Hunch names; no setup R), so no `research/ledger.jsonl` rule change
bears on these numbers; the live compass itself started 11-09 (11-05 recomputed from the same code, 11-06 / 11-09
recorded rows). Periods (GATE1 split): TRAIN 234 days (2024-10 + 2025-03..12), VALID 190 (2026-01-01..10-05), FWD 22
(10-06..11-04, cache backtest), LIVE 3 (11-05 / 11-06 / 11-09 — real compass readings, outcome bars from a read-only
market-data GET). **Configurations: 205 (48 VOTE + 36 CHK + 16 ADD-ONE + 72 LOGIT + 33 FLIP) → bar t ≥ 3.26. 0 compass
variant passes. No DECISION (FYI only).**

Backfill check: the vectorised 2-year backfill reproduces `mcf.report.compass_live.compute` exactly — W60, 30-min and
checkpoint readings match 100% on 12 random history days + the 3 live days (375 marks) and on the 48 recorded live rows
(`backfill_check.csv`).

Primary score S (PLAN): on the 15-min grid 10:00..15:30, per day mean of +1 for a confirmed reading on the side SPY
closes on (vs its open), **−3** for a confirmed reading on the wrong side, 0 when unconfirmed (break-even precision 75%).

## Failures first
- **No variant beats today's W60 at the bar.** Best paired t on VALID = 2.94 (bar 3.26). 22 of 36 CHK and 54 of 72
  LOGIT configs score above W60 on VALID, but none clear the bar; VOTE tweaks (interval / window / move floor) max t
  1.47 (11 of 48 above), ADD-ONE filters max 1.84.
- **Most extra inputs make the compass worse** (as a must-agree filter on W60, VALID ΔS): Hunch lean −0.224 (t −7.1),
  breadth up/down share (last 15 min) −0.127, prior-day trend −0.125, sector-ETF breadth −0.087, gap −0.039, OR30
  −0.008; only OR15 (+0.007) and ATR regime (+0.010) are ≈ neutral. They cut coverage more than they add precision.
- **"Heading" is still a coin flip on every config:** next 30 / 60 / 120 min in the confirmed direction 51.8 / 51.1 /
  50.0% on VALID (mean of all configs; best 53.8 / 53.8 / 55.0%). What the compass reads well is *which side of the
  open the day closes on*, not where SPY goes next.
- Interval alone changes little: on the 15-min grid 5- and 15-min updates give the same readings; 5-min reads 5–10 min
  earlier with more flips. Shorter persistence (W30) is worse (VALID ΔS −0.016, flips 0.46/day vs 0.26).

## Today's compass — accuracy (`summary.csv`)
| reading | period | S | stays on its side (confirmed) | coverage | first conf. median / by 10:30 | first-conf. precision | flips/day (false) |
|---|---|---|---|---|---|---|---|
| **W60 (15-min, headline)** | TRAIN | 0.361 | 88.5% | 65% | 10:00 / 62% | 75.9% | 0.34 (0.11) |
| | VALID | 0.335 | 89.1% | 60% | 10:00 / 65% | 74.3% | 0.26 (0.07) |
| | FWD | 0.435 | 92.6% | 62% | 10:15 / 55% | 68.2% | 0.36 (0.09) |
| | LIVE (3 d) | 0.855 | 100% | 86% | 10:00 / 100% | 3/3 | 0 |
| 30-min GATE1 | VALID | 0.319 | 89.9% | 54% | 11:00 / 44% | 79.9% | 0.12 (0.02) |
| checkpoint ≥ 0.30% | VALID | 0.340 | 93.2% | 47% | 11:00 / 37% | 84.7% | 0.07 (0.01) |
Heading for W60 (VALID): next 30 / 60 / 120 min 51.8 / 51.1 / 50.6%. LIVE days: 11-05 SPY −4.2% (DOWN-confirmed
10:00, held), 11-06 +0.07% (UP, held — a flat day it happened to get right), 11-09 +1.4% (UP-confirmed 10:00, held).
Three trend-ish days, too few to judge.

## Best variants (finalists, all reported; `configs.csv` has every config)
| config | what it is | VALID S (ΔS, t) | TRAIN ΔS | stays | coverage | first conf. / prec. | flips (false) | FWD S | LIVE S |
|---|---|---|---|---|---|---|---|---|---|
| **CHK-I15-t0.2** | SPY ≥ 0.20% from its open, read every 15 min from 09:45 | 0.410 (+0.075, **2.94**) | +0.046 | 90.9% | 65% | 10:00 / 75.0% | 0.26 (0.06) | 0.484 | 1.000 |
| CHK-I5-t0.2-P30 | same, 5-min, same side for 30 min | 0.409 (+0.074, 2.94) | +0.051 | 91.4% | 63% | 10:00 / 77.0% | 0.23 (0.04) | 0.468 | 1.000 |
| LOGIT-all-p75-I5 | logistic P(close > open), all inputs, ≥ 75% | 0.414 (+0.079, 2.16) | +0.078 | 90.3% | 68% | 10:30 / 79.8% | 0.18 (0.03) | 0.389 | 1.000 |
| LOGIT-qqq_iwm-p80-I5 | logistic on SPY/QQQ/IWM z-moves, ≥ 80% | 0.408 (+0.074, 2.78) | +0.064 | **93.1%** | 56% | 11:15 / **86.9%** | **0.08 (0.02)** | 0.429 | 1.000 |
| VOTE-I15-W60-t0.2 | today's W60 + needs ≥ 0.20% move | 0.352 (+0.017, 0.94) | +0.023 | 92.0% | 52% | 10:30 / 79.9% | 0.13 (0.02) | 0.429 | 0.855 |
- **Reading:** the simplest compass is as good or better than today's 5-vote W60 on every target — "SPY is 0.20%+ from
  its open" (15-min marks) confirms at the same time (median 10:00), is right 90.9 vs 89.1% of the time, covers 65 vs
  60% of the grid, has the same flips (0.26/day) and fewer false flips (0.06 vs 0.07); +0.075 S on VALID, +0.046 on
  TRAIN, +0.049 on FWD. Plateau: every grid neighbour also beats W60 on VALID. But t 2.94 < 3.26 → **near-miss, not a
  pass**. The VWAP / breadth / agreement votes add nothing beyond the move from the open.
- **Trade-off:** earlier vs more accurate is one dial. The logistic at 80% is the most accurate and stable (93% stays,
  87% first-confirmation precision, 0.08 flips/day) but confirms ~75 min later (11:15). The 0.20% rule is as early as
  W60. The checkpoint at 0.30% sits between (93% stays, 11:00).
- FWD (22 days): CHK-0.2 +0.049 vs W60, LOGIT-all −0.045, LOGIT-qqq_iwm −0.006 — only the simple rule keeps its sign.

## Midday FLIP detector (`flip.csv`; morning side = SPY's side at 12:00 when ≥ 0.20% from its open)
Reversal (R1) = SPY closes on the other side of its open: **17 of 129 VALID days (13%)**, 17 of 153 TRAIN.
| detector (from 12:00) | VALID recall | false flags (no-reversal days) | Youden J | precision | median flag | SPY move left after a right flag |
|---|---|---|---|---|---|---|
| **D1 SPY back across its open 15 min (k3)** | 94% | **6.2%** | **0.88** | 70% | 13:32 | +13 bps |
| D1 k1 (first 5-min mark across) | 100% | 16.1% | 0.84 | 49% | 13:35 | +16 bps |
| D5 logistic P(morning side) < 40% | 82% | 5.4% | 0.77 | 70% | 13:52 | +11 bps |
| D2 below VWAP + 75% give-back | 100% | 27.7% | 0.72 | 35% | 12:55 | +27 bps |
| D3 W60 confirmed against | 35% | 3.6% | 0.32 | 60% | 14:00 | −12 bps |
TRAIN for k3: recall 88%, false 6.6%, J 0.82, precision 63%. Neighbours k2 (J 0.84 / 0.82) and k1 hold → plateau.
Passes the pre-registered "useful" rule (VALID J ≥ 0.30, precision ≥ 60%, TRAIN J ≥ 0.25); t vs k1 2.97.
- **Honest limits:** (1) R1 recall is near-mechanical — a day cannot close on the other side without crossing the open,
  so the value is in the *false flags* (6% of days) and the *timing* (median 13:32, i.e. the afternoon is half gone).
  (2) Against the stricter truth R2 (SPY falls ≥ 0.25% against the morning side from 12:00 to the close) k3 catches 56%
  with 78% precision. (3) Averaged over all flags the move left is −5 bps: a flag says "the morning side is no longer
  safe" (standby for morning-side afternoon setups), **not** "trade the other side". (4) Today's W60 is a poor flip
  detector (recall 35%, flags at 14:00, move already spent). (5) FWD: 1 reversal day of 13, caught by k1 at 13:10;
  LIVE: no reversal on 11-05 / 11-06 / 11-09 and no flag.

## Verdict and next step
- Today's compass (W60) is right ~89% of the time when confirmed (TRAIN 88.5 / VALID 89.1 / FWD 92.6 / LIVE 100%,
  3 days), confirms by 10:00 on median, ~0.26 flips/day — and **a plain "SPY ≥ 0.20% from its open" reading matches or
  beats it on every measure**, short of the 3.26 bar (t 2.94). No DECISION: FYI + forward shadow.
- Forward shadow (nightly, from 11-10): log `CHK-I15-t0.2` and the flip detector `D1-k3 from 12:00` beside the live W60
  in the nightly COMPASS-LEARN line; re-score at 20 forward sessions (pass = paired t ≥ 1.5 on forward days with the
  same sign as VALID). The flip detector is the piece COMPASS-ROLL needs: test "afternoon morning-side setups to
  standby on a D1-k3 flag" per setup there (Remedies rule).
- Next round ideas (count new configs): close-side probability shown as a number (calibration of the logistic),
  thresholds scaled by ATR, a 13:00-start flip detector with a minimum distance from the open.

## Files
`panel.py` (5-min panel from the cache + live bars), `fetch_live.py`, `engine.py`, `check.py` → `backfill_check.csv`,
`study.py` → `configs.csv` (all 175 compass configs + 3 baselines, every period and target), `summary.csv`
(baselines + finalists), `logit_coefs.csv`, `flip.py` → `flip.csv` (33 detector configs × 4 periods × 2 truths),
`flip_days_live.csv`. Hunch lean = `research/bdi/hc1/hunch_probs.py` replay (to 11-04; not on the live days).
Scratch panel deleted. Caveats: breadth = the 200 Hunch names (live list) over the whole history (survivorship);
ATR20 just after the locked block uses pre-block days; half days dropped.
