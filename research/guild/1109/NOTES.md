# Research Guild — session 2026-11-09 (research files from branch `mcf-guild`)

*Educational only — not financial advice.* Backtests on the 2-year lab history (SIP 1-min, 2024-09-16..2026-11-09), production
costs, next-bar entries, stop-first; **locked block 2024-11-01..2025-02-28 never read**. Live figures are paper. Research only:
nothing in config/ or the trading path changed. Full discussion: `board.jsonl` and `summary/2026-11-09.md` on `mcf-guild`.
Large trade lists (> 200 kB) stay on `mcf-guild` only.

## Failures first — 9 studies, 56 configs scored + 4 QP1 = 60 configs, 0 pass the Testing bar
| Study | Configs | Bar (N) | Result |
|---|---|---|---|
| QP1 quiet-day label at 10:00 | 4 | +15-pt lift | 0 pass; lineage (QD1+QR1+QP1) 15 → closed. Low sector dispersion = smaller day (size-dial idea) |
| OD0950 09:50 opening-drive join | 2 (control) | descriptive | net −0.10R every decile, gross −0.005..+0.025 → closed |
| GATE2 trade with the held side | 11 | BAR90 2.79 (N 123) | 0 pass; avg −0.05..−0.15R; failed holds −0.6..−1.1R; pullback beats C1 (t 7-12) but Skeptic: C1 likely an anti-signal + R-leverage → C1m check pending |
| SC2 cross-asset laggard | 12 | 2.71 (family N 92) | 0 pass; driver momentum, not catch-up |
| C3FR COMBO1-C3 at wider R | 6 | 2.22 (N 21) | 0 pass; friction 0.18 → 0.04R but gross shrinks; laggard family 0 / 92 → parked |
| SC1 event-day gap-and-hold | 8 + 4 rework | 1.84 / 2.01 (N 12) | 0 pass; plan run +0.355R on n 18 was small-sample; rework n 141-446 ≈ 0 |
| NH1 quiet-top continuation long | 8 | 3.47 (family N 1,671) | 0 pass; −0.06..−0.11R, it is market direction |
| BEREPLAY break-even exits | 3 | 2.35 (N 30) | 0 pass; BE50 worse on 27 of 27 family-sides; mfe-based giveback overstates an exit fix ~10× |
| CWT14SKIP skip CWT14 failed-break longs ≥ X ATR below open | 2 (+4 Skeptic plateau looks) | 2.10 (N 14) | X 1.5 t 2.13, plateau positive, keeps 99.6% — but down-day excess −56R (fails the regime gate), VALID t 0.96, +0.00026R/trade → lead only; earnings-overlap check pending |

## What was learned
- **Costs:** lab model charges 0.218R/trade vs ~0.06R in live paper (16,615 trades, every account, all 24 days) → lab bars are conservative. Tight stops drive cost (44bp quartile 0.42R vs 222bp 0.09R) → STOPW (minimum stop width, same $ risk) frozen, runs next.
- **Long side:** caught long movers are dip reversals; missed movers sit near HOD (descriptive, 6 sessions) — but "compressed near the top" (NH1) does not pick them out.
- **Setup Generator:** 2-year screen vs live avg R rank corr −0.04 (train) / −0.21 (valid); no gen.spec condition is positive w/o best day; tight brackets worst (t1s05 −0.91R). Rules are recoverable (93 modules) for replay.
- **Wrong-way trades on movers** are diffuse (top setup 13%; Graveyard + Gen 76%) → no veto.

Rule-change context for live windows 10-06..11-09: Graveyard moves 11-02 / 11-03, SO-1A 11-03, ROLL1 11-05; Gen per-setup −2R stop off 10-22, slots 80 → 200 10-26 (research/ledger.jsonl).
No DECISION. Next: STOPW, GATE2 C1m check → combined rework (GATE2 + min stop width + mid-day exit) if it survives.
