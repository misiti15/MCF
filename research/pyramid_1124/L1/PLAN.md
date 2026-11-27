# PYRAMID L1 (longs, "catch the movers we miss") — pre-registration
Educational only — not financial advice. Written 2026-11-24 before any candidate was scored.

## Prior failures this plan must not repeat (cited)
- ULT-05 with-gap continuation (two-sided; check -0.003, long leg live 326 tr -0.049R) -> gap-up continuation NOT re-tested.
- ULT-26 trend-tape with-gap VWAP pullback (check -0.045, vs random -0.114) -> C2 differs: no gap condition; the
  name must belong to the day's *leading sector ETF* (rotation), the new data angle is the sector-ETF ranking.
- ULT-17 sector-lag catch-up (laggards in strong sectors, check -0.010) -> C2 buys sector *leaders' pullbacks*, not laggards.
- ULT-06 late morning-turn long, ULT-02/03/07 dip/washout longs -> no mean-reversion longs here; all three candidates
  are with-trend / relative-strength longs.
- ULT-28 earnings continuation failed -> no earnings angle.

## Common rules
Long only. Lab frames (5-min bars, tod = bar close). Entry = decision-bar close, tod in window (all >= 10:00),
first signal per symbol-day per config, price >= $5, ADV20 >= $20M. R = 0.25 x daily ATR (atr_d), stop 1R.
Geometry G1 = target 1R (t1s1), G2 = target 2R (t2s1). Exits walked on 1-minute bars (bench10.walk_trades:
stop first, gap-through at worse, target needs +$0.01 through, flat 15:55). LR8 costs (bench10.add_r).
Book = Testing rules (cap 100 open, <= 3 lots/symbol, stop-cost filter 0.15).

## Candidates and grid (12 configs)
- C1 RS-RED (relative strength on a red index): tod 10:00-11:30; qqq_fo <= -0.30%; stock fromOpen > 0;
  vwapDistPct > 0; fromOpen - qqq_fo >= D. D in {1.0, 2.0} x {G1, G2}.
- C2 SECTOR-LEAD-PB (rotation follower): tod 10:05-13:00; stock's mapped SPDR (11 sector ETFs; map = highest daily
  return correlation >= 0.30 on fit dates only) is the strongest sector ETF from the open at that bar and
  sector_fo - spy_fo >= S; stock fromOpen > 0; bar low <= VWAP x 1.001 and close > VWAP (VWAP test held).
  S in {0.3, 0.6} x {G1, G2}.
- C3 OR20-RECLAIM (opening-drive continuation): tod 10:00-12:00; OR20H = high 09:30-09:50; bar close > OR20H and
  previous bar close <= OR20H (cross-up); volumeRatio >= V; fromOpen > 0; vwapDistPct > 0. V in {1.5, 2.5} x {G1, G2}.

## Split and selection
FIT = 2024-10 + 2025-03..09 (bench10 T1 fit). CHECK = 2025-10-01..2026-11-04 (scored once). 2023-24 = bench10 T2
(2023-01-03..2024-09-13, cache_fresh 469 symbols) scored once for the selected config. Locked block never read.
Selection per candidate: highest fit avg R after costs among its 4 configs with >= 150 booked fit trades (else the
one with most trades). fitsel.json frozen before any check row is built.

## Bars
- TIER A: fit avg R > 0; check avg R > 0; check w/o best day > 0; check day-clustered t >= 1.5; both check halves > 0;
  2023-24 avg R > -0.02; check >= 0.5 trades/session; beats its random-entry control on check.
  (ultimate_1119's 2.0/session floor relaxed to 0.5 because this lane is a day-type complement; stated up front.)
- TIER B: fit avg R > 0 and check avg R > -0.02.  Otherwise FAIL.
Reported for every finalist: card per BRIEF; correlation of daily R with the Primary book (RW3-FD, RW5-FD,
L3-fromopen-FD, NM-ETF re-built with bench10 Primary rules) and R on the book's 10 worst days; live overlap
2026-10-06..11-04 vs the live Primary journal.
Random control: per signal, one random bar of the same symbol-day inside the config window, same geometry/costs/book.
Configs counted: 12 (+ controls, not counted).
