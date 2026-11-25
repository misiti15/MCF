Educational only — not financial advice

# Project Pyramid round 3 — Team N: new blood, honest fitness (2026-11-25)

Research only. Pre-registered (R3N/PREREG.md, sha256 eec603a6…32b6, 14:50 UTC). Generator grammar reused verbatim (ex30/gen2 prims; seeded draws like mcf/research/generator); 300 draws counted (240 longs behind the gate "SPY ≥ open at the decision bar", 60 easy-to-borrow shorts kept out of the gap-down family). Fitness on FIT only: F = min(avg R, avg R w/o best day, avg R on SPY-down days), eligibility ≥ 85 trades, ≤ 25/session, ≥ 20 down-day trades, best-day share < 0.5. Top 3 longs / 2 shorts frozen, then scored once on CHECK and 2023-24 (bench10, LR8 + borrow, testing book). Locked block never read. Noise bar within the search t ≈ 3.38; cumulative N ≈ 2,230 → ≈ 3.93.

## Verdict: 0 of 300 pass — no TIER A or B, no Testing suggestion
- No draw had F > 0 on FIT; only 3 longs were eligible (as F ≤ 0 fillers) and all 3 are negative on CHECK (−0.010 to −0.086) and 2023-24 (−0.054 to −0.064); 0 shorts eligible.
- Gated longs: 48 of 240 positive on FIT, but only 6 positive on SPY-down days and 4 with best-day share < 0.5; median gated long −0.38R on down days vs +0.06R on up days. "SPY ≥ open at entry" filters the moment, not the day's outcome.
- Best-looking longs were one-day records (2025-04-07/09 tariff crash/rebound) and were correctly rejected.
- Non-gap-down shorts: median −0.138R; best FIT t 0.34 — no edge in this grammar.
- The generator's 15% live front-runner rate (repsrot_1125) did not reproduce under honest fitness: it comes from cheap exposure in a short, favourable live window.
- Best hedge piece (filler 3, upper-wick flat-from-open long in high-volatility names): +54R on the book's 10 worst CHECK days, correlation −0.31, but negative carry.

## Next (backlog, untested)
A long gate that predicts the close, not the moment (e.g. TT1 + an intraday breadth-thrust leg — needs breadth data for 2023-24, a data gap to fill first); or run gen2's macdup-fade short family through this harness as one pre-registered family. Scripts/data: scratchpad pyramid/R3N/.
