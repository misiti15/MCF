# bdi1026 PLAN (written before any history was scored)

*Educational only — not financial advice.*

**Idea tested:** backlog `nightly-1026-coil-breadth-burst-skip` (added by tonight's nightly loop, untested) — Coil Under
the High longs (CWT12-coil-k4-long, Testing 2; CWT12-coil-k6-long, Testing 1): when the setup fires on many symbols in
the same decision bar it is the index pausing at its high, not a stock-specific breakout.

**Data:** open two-year history (research/history2y frames, 5-min decision bars, SIP), train ≤ 2025-12-31, valid
2026-01-01..2026-10-07. The locked block 2024-11-01..2025-02-28 is never read (lib refuses it; asserts in the script).
No holdout is scored tonight (rule 2/19: only a finalist that passes train+valid gates is scored once, by the lead).

**Signals and costs:** the coil kernel and simulator of research/bdi/top5_1021/scan_1021.py unchanged (kernel parity
already checked there), parent variant "P" (live geometry, scale-out, window 09:50-11:30, first signal per symbol-day),
production + tier costs in, same-minute random control (5 draws). Burst count n_bar = number of the setup's entries in
the same (date, signal bar) across the universe — known at the poll, because live evaluates all symbols in one poll.
QQQ "at its high" = qqq_fo within 0.10 %-pt of its running max over the day's decision bars so far (5-min closes, an
approximation of the true high of day; stated limit).

**Configs (pre-declared, 6 per setup × 2 setups = 12):**
- A5 / A10 / A15: skip every entry of a bar with n_bar ≥ 5 / 10 / 15
- B3: keep at most 3 entries per bar (random order, seed 20261026)
- C: skip when QQQ is at its high so far (and qqq_fo ≥ +0.5%)
- D: skip when C and n_bar ≥ 5

**Gates (fixed now):** the gated setup must (1) be positive after costs in train AND valid, (2) improve on the parent
in train AND valid (delta per parent trade), (3) beat the same-minute random control in both, (4) be positive in up and
in down sessions (regime split), (5) keep ≥ 50% of the parent's trades, (6) day-clustered all-data t of the delta ≥ the
lineage bar. Lineage N = 1,311 (gate lineage after bdi1023) + 12 = 1,323 → bar sqrt(2 ln N) = 3.79. A row that meets
(2)-(4) but not (1) or (6) is reported as a near-miss only. Also reported: kept share, avg R without the best day and
the best day's share of total R (owner 2026-10-25).

## Addendum (written after the 12 burst-skip rows were scored, before the fade was run)

**New setup idea, BDI1026 "Coil Burst Fade" (short):** live 10-26 the opposite side of coil-k4 was +32.4R (52 trades)
and the burst trades never worked. Hypothesis: when Coil Under the High (4 bars) fires on many symbols in the same bar,
the breakout is the index pausing at its high; fade it. Signal = the coil-k4 kernel unchanged (09:50-11:30, ADV
≥ $95M, first signal per symbol-day), entered **short** next bar, R = 0.25 × daily ATR, no scale-out, 15:55 flatten,
costs in, same-minute random-short control. **8 configs:** geometry t1s1 (1R stop / 1R target) and t05s1 (0.5R target /
1R stop) × burst filter n_bar ≥ 1 (all) / 5 / 10 / 15. Same gates as above; lineage N 1,323 + 8 = 1,331 → bar 3.79.
Note: the burst-skip rows' delta per parent trade is positive for any skip of a losing setup; the gate that matters
there is gate 1 (kept trades positive after costs) and kept exp vs parent exp, reported in NOTES.
