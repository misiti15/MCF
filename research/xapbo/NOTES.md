# XA-PBO — probability of backtest overfitting (CSCV), guild tool (Builder, 2026-11-10)

*Educational only — not financial advice.* `pbo.py` (own implementation of Bailey et al. 2014 CSCV). Tests: `pbo_tests.csv`.

## How to use
`python pbo.py <trades file> <config col> <date col> <value col> [S=16] [metric=sharpe|mean]`, or `pbo.pbo(M)` on a
days x configs P&L matrix. Report PBO **next to** BAR90, avg R, the controls and `p_oos_loss` — never instead of them.

## Calibration (selftest)
Pure noise: mean PBO 0.47-0.51 over 20-30 draws, **but sd ~0.22-0.24 per draw** (0.08..0.86) — one study's PBO is noisy;
treat 0.3-0.7 as "selection uninformative". One planted real edge (+0.35 sd/day): PBO 0.00.

## Known-answer tests
| study | N | PBO (sharpe / mean) | p_oos_loss | reading |
|---|---|---|---|---|
| GATE2, 8 setup configs | 8 | 0.64 / 0.36 | 0.94 / 0.87 | choosing the best config is no better than random, and it loses OOS ~90% of splits — matches 0 of 8 |
| GATE2 I-HB 4 | 4 | 0.33 / 0.09 | 0.86 / 0.78 | stable ranking (X0.50 = fewer trades = smaller losses), still a loser |
| GATE2 I-ETF 4 | 4 | 0.87 / 0.49 | 0.90 / 0.84 | overfit selection |
| STOPW 4 variants (± BASE) | 4-5 | 0.00 / 0.00 | 1.00 | perfectly stable ranking (W100 best every split) — because a bigger size cut always loses less on a losing book; the chosen variant loses OOS in 100% of splits |

**Lesson:** low PBO = the ranking is stable, NOT that the winner makes money or is an edge. STOPW shows a systematic
artefact (size cut) gets PBO 0. Read PBO with profitability, `p_oos_loss`, and the study's controls.
