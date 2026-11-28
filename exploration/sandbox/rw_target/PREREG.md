# RW-TGT125 re-check: pre-registration (written 2026-11-28 ~01:12 ET, before any bench score of this track was read)

Educational only — not financial advice.

Already seen before writing this: the WAVE2 Y1 result (+0.044 R/trade, t 2.58, live 10-12..11-17), tonight's
shorts_autopsy T1 re-check (CHECK +0.007 t 1.78, FIT −0.007, no rounding, T2 not walked), and the live what-if of this
track (live_score_out.txt: 10-23..11-27 +0.029 R/trade, t 2.06; 11-18..11-27 only +0.001).

Config (1, a re-check of the already-counted WAVE2 Y1 config; counted once more): RW3-FD and RW5-FD target at 1.25x the
parent's target distance from the signal price, stop unchanged, 15:55 flatten unchanged. Current rules on both arms:
LIVE-L costs (research/primshorts_1126 cells_live.json), 11-20 rounding (stop to the cent away from price, take-profit
toward entry). Engine: bench10 signals + 1-minute walk unchanged (exploration/sandbox/rw_target/bench_rwtgt.py).
Filters as shorts_autopsy: entry ≥ $5, ETB rate ≥ 0.9. Locked block 2024-11-01..2025-02-28 never read.

Splits: CHECK 2025-10-01..2026-11 and T2 2023-01-03..2024-09-13 are scored; FIT (2024-10, 2025-03..09) descriptive.

PASS (all, on BOTH CHECK and T2, RW3 + RW5 pooled, candidate level):
1. mean paired Δ > 0 and day-clustered t ≥ 2.0;
2. sign-flip p < 0.05 on daily Δ sums (10,000 flips);
3. best day's share of the total gain < 50%;
4. neither setup's Δ < −0.02 R/trade;
5. variant avg R without its best day ≥ parent's.
Also reported (not part of the verdict): Primary book view (cap 30, −2R latch on realized R), LR8-bench cost basis and
unrounded arms (parity with shorts_autopsy), exit crosstab, SPY up/flat/down day split, weeks up.
If it fails on either scored split the verdict is "does not hold"; no draft config is written.
