# HC1 + COMP15 — pre-registration (written 2026-11-05 after the close, before any score)

*Educational only — not financial advice.* Research only: nothing in config/ or the trading path changes.

Queue items (owner 2026-11-05): **HC1** (does Hunch breadth add to the market compass?) and **COMP15** (compass every
15 min from 09:45 with rolling windows vs the 30-min GATE1 compass). Run together; one config count, one bar.

## Data and periods
- SPY / QQQ / IWM 1-min SIP cache (`data/cache_hist/1Min`, to 2026-11-04), lab context breadth (`breadth_open`,
  1,226 names, 5-min, 09:50..15:00, GATE1 time convention), Hunch 200-ticker panel built by `mcf.hunch.data.build_panel`
  (universe `research/hunch/universe200.txt`, M1 label). Locked block 2024-11-01..2025-02-28 is never read (both
  loaders filter it out before use).
- Periods = the Hunch replay's: **TRAIN** 2024-10-01..2026-02-28 (Hunch rows only after its 20 warm-up sessions),
  **VALID** 2026-03-01..2026-10-07, **FWD** 2026-10-08..2026-11-04 (reported, not used to pick), **LIVE** 2026-11-05
  (Hunch `guesses/2026-11-05.csv` on mcf-data-hunch + SPY/QQQ/IWM and 200-name 1-min bars for 11-05 from Alpaca
  market-data GET; breadth on 11-05 = the 200 Hunch names, not the lab 1,226 — flagged). Note: GATE1 used a different
  split (TRAIN < 2026-01-01); the 30-min compass is recomputed here on this split so the comparison is like for like.
- Outcomes (SPY): **staying** = sign(close − open) vs the reading's side; **heading** = rest of day sign(close − px_T),
  next 30 min sign(px_{T+30} − px_T), next 60 min sign(px_{T+60} − px_T). Close = 15:59 bar close.

## Hunch replay probabilities (HC1 input)
- Re-run of Hunch's pooled logistic learner (`pooled:logreg`, exactly `mcf.hunch.learners.LogReg` with the ticker
  intercept, online walk as `replay._walk`), recording `proba` per ticker per 3-min bar (live `p_pooled` is the same
  model continued). Aggregates per bar: n, **share_up** = share of tickers with p > 0.5, **mean_p**, **press** = mean
  of the `pressure` feature (buy/sell pressure proxy) across tickers.
- At checkpoint T the last Hunch bar closing ≤ T is used (bar closing at T is allowed: its data ends at T).

## HC1 — configurations (36)
- Rows: day × half-hour checkpoint 10:00..15:00 (11 per day; heading_60m to 15:00 only where px_{T+60} exists).
- Baseline model: logistic regression on one-hot(GATE1 compass reading) + one-hot(checkpoint) (fit on TRAIN).
- Augmented = baseline + Hunch block (z-scored on TRAIN). 8 Hunch blocks: (1) share_up, (2) mean_p, (3) Δshare_up 3 bars,
  (4) Δshare_up 6 bars, (5) Δmean_p 3 + 6 bars, (6) press (last bar), (7) press summed over last 3 and 6 bars,
  (8) all of the above. × 4 outcomes = **32**.
- Plus 4 split looks (one per outcome): within directional compass readings, hit when share_up's side (> / < 0.5)
  agrees with the reading vs disagrees. = **4**.
- Score on VALID: accuracy (up/down call) augmented − baseline, log-loss improvement, **day-clustered t** of the per-day
  mean log-loss improvement. **HC1 "yes"** only if, for some config: VALID accuracy +2 pts or more AND day-clustered
  t ≥ bar AND TRAIN improvement > 0 AND FWD not negative. Every config reported.

## COMP15 — configurations (32)
- Checkpoints every 15 min: 09:45, 10:00, …, 15:30 (09:45 uses only 09:30-09:45 → **low-confidence flag**; it can
  never be "confirmed"; its breadth vote is neutral as in GATE1). 15:15 / 15:30 breadth = the 15:00 value.
- Window W ∈ {30, 45, 60 min, whole day so far}. Marks = the 15-min checkpoints in (T − W, T] (≥ 09:45; day = all
  since 09:45). pW = sign(fo) if sign(fo) is the same non-zero sign at every mark, else 0.
- Votes v = sign(fo) + sign(VWAP distance) + breadth side (breadth_open vs 0.5) + index agreement (SPY, QQQ, IWM fo same
  sign) + pW. Reading: **confirmed** if |v| ≥ 4 and pW = sign(v) and ≥ 2 marks; **leaning** if |v| ≥ 2; else mixed.
  (Same thresholds as GATE1; GATE1's persist2/persist3 are replaced by pW.)
- Reference: the **30-min GATE1 compass** (persist2 / persist3 on the 30-min clock), held between its checkpoints.
- Looks per window: staying / rod / next-30 / next-60 hit × {confirmed only, all directional} = 8, × 4 windows = 32
  (earliness and flips are reported for each window as part of the same looks, not counted again).
- Earliness: per day, time of the first confirmed reading and whether its side = the close side; median first time,
  share of days confirmed by 10:15 / 10:30 / 11:00, precision of the first confirmed reading.
- Flips: per day, reversals of side between consecutive non-mixed readings (up ↔ down), and reversals of the
  confirmed side, 09:45..15:30.
- **COMP15 "yes"** only if one window on VALID (and TRAIN same direction): first confirmed reading ≥ 15 min earlier
  (median) with first-confirmed precision within 2 pts of the 30-min compass, AND confirmed staying hit within 2 pts,
  AND flips/day no more than +0.5 above the 30-min compass; heading hit differences reported with day-clustered t.

## Count and bar
N = 36 + 32 = **68** configurations → bar max(1.5, sqrt(2 ln 68)) = **2.90**. Nothing tuned on VALID; FWD and LIVE
are sanity checks only.
