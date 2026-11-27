# PYRAMID L2 (longs, "buy the flush") - pre-registration. Written 2026-11-24 before any candidate was scored.
Educational only - not financial advice.

Pipeline: research/ultimate_1119/top10/bench10.py functions (signals, 1-min walk, add_r LR8 costs, book) unchanged.
Entry = decision-bar close, stop first, target needs +$0.01 trade-through, flat 15:55. R = 0.25 daily ATR (t1s1) unless the
module says otherwise. Testing book (cap 100, <=3 lots/symbol, price >= $5, cost filter 0.15R). Locked block never read.
Halves: FIT = 2024-10 + 2025-03..09 (170 sess); CHECK = 2025-10-01..2026-11-04 (276); T2 = 2023-01-03..2024-09-13 (427).

Single pre-registered regime gate G (used as a grid arm, not tuned): SPY at/above its open at the decision bar (spy_fo >= 0).
Mechanism: buy idiosyncratic flushes when the tape is not falling (ULT-02 bought tape flushes and failed).

Candidates / configs (12 counted):
- C1 SEED NM-AR-AM-gapdown-capitulation-long (live module unchanged: gap_atr <= -0.41, ret12 <= -1.61%, rvol_day <= 0.8,
  10:50-10:55, t1s1, ADV >= $95M, first hit/symbol-day): C1a as live; C1b + G; C1c window to 12:00 (10:50-11:55).
- C2 gap-down OR-high reclaim long: first 5-min close above the 09:30-09:50 high (prior close <= it), 10:00-12:00, above
  VWAP, ADV >= $95M, first hit/symbol-day, t1s1. C2a gap <= -1.5% & <= -0.5 ATR; C2b C2a+G; C2c gap <= -3% & <= -1.0 ATR; C2d C2c+G.
- C3 gap-down flush-spring long: gap <= -0.5 ATR, prior bar set the low of day on volumeRatio >= VR while >= 0.5 ATR below
  the open, current bar closes above that bar's high, 10:00-14:30, ADV >= $95M, first hit/symbol-day, t1s1.
  C3a VR 2.0; C3b C3a+G; C3c VR 3.0; C3d C3c+G.
- C4 NM-ETF-late-dip-di-long + G (live module unchanged otherwise; t05s1, 14:00-15:00, ETF list). Ungated NM-ETF = benchmark (0 configs).
Selection (per candidate, FIT only): highest FIT avg R without the best day among configs with >= 60 FIT trades. Frozen
in fitsel.json before CHECK / T2 numbers are printed. Then CHECK + T2 scored once. All other configs shown after, never re-picked.
Tiers: A = fit > 0, check > 0, check w/o best day > 0, T2 (2023-24) avg R > -0.02, check day t >= 1.5, check >= 1.0 trades/session.
B = fit > 0 and check > -0.02 (or A short only on volume/t/T2). FAIL otherwise. Live record (seed only) reported alongside.
Controls: random-entry (same symbol-day, random bar in the window, same exit) per config. Team: daily-R correlation with
the backtested Primary lineup (L3-fromopen, RW3-FD, RW5-FD, NM-ETF, home book) and R on its 10 worst days; live seed vs live Primary.
Prior failures not re-tested: ULT-02 tape-flush (SPY-falling washout), ULT-03 broad RSI collapse, ULT-07 PM volatile dip,
ULT-06 late morning turn, round-6 gates on BOOK-EM/ST7, round-5 fresh window.
