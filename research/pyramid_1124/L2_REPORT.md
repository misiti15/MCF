Educational only — not financial advice

# Project Pyramid — Team L2: buy the flush (longs) (2026-11-24)

Research only. Pre-registered and hashed (scratchpad/pyramid/L2/PREREG.md, 23:27Z; selection frozen 23:54Z). 12 configs + 2 live diagnostics. bench10 pipeline unchanged (parity check passed), LR8, testing book. FIT 170 / CHECK 276 / 2023-24 427 sessions. Locked block never read. One pre-registered regime gate G: SPY at or above its open at the decision bar. Result: 0 TIER A, 1 TIER B, nothing to deploy.

| Candidate | Fit | Check (w/o best day) | 2023-24 | Live | Verdict |
|---|---|---|---|---|---|
| C1a seed NM-AR-AM-gapdown-capitulation-long (as live) | +0.340 (2025-04-04 = 64%) | +0.102 (+0.062) | −0.097 | 111 tr, −0.117R (w/o best day −0.255); 11-24's +10.76R only clawed back earlier losses; −8.64R on live Primary's 10 worst days | FAIL — both clean windows negative; fit/check not clean (designed on them) |
| C2a gap-down OR-high reclaim long | +0.067 (89% one day) | −0.023 (−0.045) | −0.097 | — | FAIL; best hedge piece (corr −0.32, +179.6R on the book's 10 worst days) but negative carry |
| C3a gap-down flush-spring | +0.109 (72% one day) | −0.009 | −0.110 | — | FAIL |
| C4a NM-ETF-late-dip-di-long + gate G | +0.243, t 3.77 | +0.140 (+0.116), t 2.75 | −0.015 | gate passes 13 tr at +0.229; blocked 40 tr at −0.140 | TIER B — fails A only on volume (0.33 trades/session vs 1.0) |

Ungated NM-ETF for comparison: fit +0.260, check +0.049, 2023-24 −0.039, live −0.050 on 53 trades. Plateau: no config positive in both check and 2023-24. Every capitulation long is ≤ −0.097 in 2023-24 (losses on SPY-down days).

## Next (backlog, not deployed)
1. NM-ETF + G: forward shadow logging the "SPY at or above its open" split nightly, judged at ≥ 15 sessions (filter change to a Primary setup → backlog + shadow first, Friday epoch, owner yes). Cost: ~60% of its trades.
2. C2 as a hedge would need an at-entry "short thesis failing" trigger to cut its negative carry — new work.

Rule-change context: backtests use one fixed rule set; lab frames end 11-04 (rotation days 11-10/11-11/11-24 not testable). Seed live window 10-21..11-24 spans the 10-30 testing cost filter, 11-12 LR8, 11-17 TSZ1, 11-23 burst brake.
