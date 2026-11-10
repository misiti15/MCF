# COMPASS-LEARN round 1 — pre-registered plan (written 2026-11-10, before any score)

*Educational only — not financial advice.* Research only: no config, live compass, dashboard or trading change.
Owner 2026-11-09: "make sure we're learning from the compass — change the interval, a different indicator, or adjust
it to make it more accurate; it's crucial for switching setups on and off". Queue: COMPASS-LEARN (COMPASS-ROLL uses it).

## Data and periods
- 1-minute SIP bars from `data/cache_hist/1Min` (SPY, QQQ, IWM, the 11 XL* sector ETFs, the 200 Hunch names of
  `research/hunch/universe200.txt` = the live compass's breadth list), read with `mcf.hunch.data.load_1min`, which
  filters the **locked block 2024-11-01..2025-02-28 inside the parquet read (never loaded)**.
- Periods (GATE1's split): **TRAIN** = 2024-10 + 2025-03-01..2025-12-31; **VALID** = 2026-01-01..2026-10-05;
  **FWD** = 2026-10-06..11-04 (cache, backtest of recent days); **LIVE** = the live compass days since 11-05
  (11-05 recomputed with `mcf.report.compass_live.compute`, 11-06 / 11-09 from the `mcf-data-compass` branch; outcome
  bars from a read-only Alpaca market-data GET). Days whose last bar starts before 15:55 (half days) are dropped.
- Panel: every 5-min mark T = 09:35..15:55, point-in-time (bars that start before T, as `compass_live.snap`).
  The vectorised backfill of today's compass is checked against `compass_live.compute` on sampled days (must match
  ≥ 99% of W60 / 30-min / checkpoint readings) before anything is scored.

## Baselines (today's live card)
- **B-W60** (the 15-min reading, headline): `compass_live` W60 confirmed (UP/DOWN-confirmed) side.
- **B-C30** (30-min GATE1 compass, held between checkpoints) and **B-CHK** (checkpoint UP/DOWN, |fo| ≥ 0.30% at the
  latest 30-min checkpoint, from 10:30). All three are scored; **B-W60 is the reference for the paired tests.**

## Accuracy targets (all four reported for every config, TRAIN / VALID / FWD / LIVE)
- (a) **staying**: does SPY close on the confirmed side of its open; hit rate of confirmed readings and coverage.
- (b) **heading**: SPY at T+30 / T+60 / T+120 vs SPY at T, in the confirmed direction.
- (c) **first confirmation**: median time, share of days confirmed by 10:00 / 10:30, precision of the first confirmation.
- (d) **flips**: confirmed-side changes per day (UP→DOWN or DOWN→UP, through unconfirmed or not) and **false flips**
  per day (a flip to the side the day does not close on).
- **Primary score (selection):** on the common grid G = 15-min marks 10:00..15:30 (23 marks; each config's reading is
  held from its latest update ≤ T), per day S = mean over G of (+1 if confirmed and right, **−3 if confirmed and
  wrong**, 0 if unconfirmed) vs the close-vs-open side. A wrong confirmation costs 3 (break-even precision 75%),
  because switching a setup on the wrong side hurts more than waiting. Paired per day vs B-W60.

## Variants (each counts as one config)
1. **VOTE** (today's structure: 5 votes fo sign, VWAP side, breadth side, SPY/QQQ/IWM agreement, persistence;
   confirmed = |votes| ≥ 4 with persistence and ≥ 2 marks): update interval I ∈ {5, 10, 15, 30} min × persistence
   window W ∈ {30, 60, 90} × extra move floor θ ∈ {0, 0.2, 0.3, 0.4}% (confirmed also needs |fo| ≥ θ) = **48**
   (I15 W60 θ0 = B-W60 reproduced).
2. **CHK** (move-from-open only): confirmed side = sign(fo) when |fo| ≥ θ at the latest mark; I ∈ {5, 10, 15, 30} ×
   θ ∈ {0.2, 0.3, 0.4}% × persistence (none / same side at every mark of the last 30 / 60 min) = **36**.
3. **ADD-ONE filters on B-W60** (confirmed only if the input also agrees): opening-range break (15-min OR, 30-min OR:
   SPY beyond the OR high / low on that side), sector-ETF breadth (≥ 6 of 11 XL* on that side of their open),
   breadth up/down share (share of the 200 names up over the last 15 min on that side of 0.5), ATR regime (|fo| ≥ 0.25
   × the 20-day median daily range), gap size (no confirmation against a gap ≥ 0.5%), prior-day trend (prior day's
   open-to-close on that side), Hunch pooled lean (share_up of the Hunch replay on that side, where history exists)
   = **8**; and the same 8 on the best CHK of step 2 by TRAIN score = **8** (16 total).
4. **LOGIT** (a different indicator): P(SPY closes above its open | features at T), logistic, fit on TRAIN only.
   Base features: z = fo / ATR20, z × τ (τ = minutes since open / 390), VWAP side / ATR20, breadth − 0.5, index
   agreement. Models: base, base + one of {sector breadth, breadth up/down share, OR30 side, gap / ATR, prior-day sign,
   Hunch lean − 0.5, QQQ & IWM z}, all = 9 models × confirm threshold p* ∈ {0.75, 0.80, 0.85, 0.90} (stay confirmed
   until P < p* − 0.10, hysteresis) × I ∈ {5, 15} = **72**.
5. **FLIP detector (midday)**: morning side M = sign(SPY fo) at start S when |fo| ≥ 0.20%; truth R1 = SPY closes on the
   other side of its open (morning side reversed), R2 = close vs SPY at S ≥ 0.25% against M. Detectors from S on,
   5-min marks: D1 SPY back across its open for k ∈ {1, 2, 3} consecutive marks; D2 SPY across VWAP against M and
   ≥ ρ ∈ {0.5, 0.75} of the morning's max favourable move given back; D3 confirmed side of B-W60 / of the best compass
   variant leaves M; D4 breadth ≥ 0.05 past 0.5 against M and SPY across VWAP; D5 LOGIT(best model) P(close on M side)
   < q ∈ {0.5, 0.4, 0.3} = 11 detectors × S ∈ {11:00, 12:00, 13:00} = **33**. Scored per day: recall (reversal days
   flagged), false-flag rate (non-reversal days flagged), Youden J = recall − false-flag rate (selection, R1, S 12:00),
   precision, median flag time, and the SPY move left from the flag to the close in the new direction (bps).

**Total: 48 + 36 + 16 + 72 + 33 = 205 configs → bar max(1.5, sqrt(2 ln 205)) = 3.26.**

## Selection and pass rule (fixed now)
- Compass: rank by VALID primary score. **Clearly better** = VALID day-paired t (S_variant − S_B-W60) ≥ 3.26 AND TRAIN
  difference > 0 AND plateau (at least half of its grid neighbours — one step in each dimension — also > B-W60 on
  VALID) AND first-confirmation precision on VALID not below B-W60's minus 2 pts. FWD and LIVE are reported, not used
  to pick (too short). False flips/day reported beside it as the trade-off.
- Flip detector: best by VALID Youden J (R1, S 12:00); "useful" = VALID J ≥ 0.30 and precision ≥ 60% with TRAIN J ≥
  0.25; day-level two-proportion t vs the D1 k=1 detector reported. Neighbours reported.
- If a compass variant is clearly better → DECISION CL1 (display-only change to the live compass card). Otherwise FYI.
- All finalists reported, failures first, with the number of configs (205) and any extra looks added later.
