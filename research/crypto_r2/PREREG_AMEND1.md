Educational only — not financial advice.

# Crypto round 2: amendment 1 (written 2026-11-26, after the v1 run, before any v2 scoring)

PREREG.md (sha256 cdf610e3...c2f5) stays in force except for the points below.

## Why
The v1 run (FIT 480 configs, 0 eligible; the 10 frozen near-misses scored once on CHECK) is kept unchanged in
`research/crypto_r2/v1_badprints/`. Its best near-miss (draw 742, 4h pullback, all 13 pairs) was +0.031R on FIT and
+0.035R on CHECK (t 3.03), but **all of it came from SHIB** (+0.83R FIT, +0.51R CHECK; the other 12 pairs together
about −0.02R on both). Its SHIB trades hit targets on **bad prints**: 1-min highs of 0.0040 while SHIB traded at
0.000011 (2023-03), many on zero-volume bars. A scan of the 13 pairs found such prints in every alt (SHIB about
1,000 highs > 1.5x the local median; UNI, BCH, AAVE, SOL, DOGE dozens to hundreds). It also found that since 2023
Alpaca's history includes **zero-volume minutes** (BTC: 49% of minutes in 2023, 88% in 2024), which are not trades.
v1 is therefore void as evidence. It is reported only as a data-quality finding.

## Changes (engine and data only; grammar, seeds, grid, eligibility, ranking and CHECK rules unchanged)
1. **Bad-print filter** (`mcf/crypto/exec1m.clean_prints`, applied to raw 1-min bars before resampling and
   before the fill simulation; trailing only): ref = median close of the previous 60 bars. A bar whose close is
   more than 25% from ref is dropped. A high above ref x 1.25 is cut to the bar's body; a low below ref / 1.25 is
   raised to the body. Known cost: real one-minute wicks beyond 20-25% (e.g. alts on 2025-10-10, inside CHECK) are
   removed, which is slightly optimistic for stops on such minutes.
2. **Maker fills need a real trade:** a maker entry or a maker target fills only on a minute with volume > 0.
   Zero-volume minutes can still trigger stops and time exits (conservative).

## Counting
The same 480 configs (ids 500..979) are re-scored on the corrected data. They are counted again:
**N_cum = 500 + 480 (v1) + 480 (v2) = 1,460; noise bar sqrt(2 ln 1460) = 3.82.**
The 10 v1 finalists (ids 742, 515, 891, 797, 743, 582, 588, 881, 754, 555) have already been seen once on CHECK. If
any is frozen again, its CHECK look is look 2 and needs day t >= 1.5 to survive. All other rules as in PREREG.md.
