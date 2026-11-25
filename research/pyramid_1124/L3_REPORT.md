Educational only — not financial advice

# Project Pyramid — Team L3: ride the trend / mine the live record (longs) (2026-11-24)

Research only. Pre-registered and hashed before scoring (scratchpad/pyramid/L3/PREREG.md, 23:30 UTC); 12 configs (A: 3 parents + 3 tightenings; B: 3 candidates × 2 exits); cumulative t bar 3.89. Splits: FIT 2024-10 + 2025-03..09 (170), CHECK 2025-10..2026-11-04 (276), T2 2023-01..2024-09 (427). Testing-arena book, LR8, 1-min exits. Locked block never read. Result: 0 TIER A; nothing to deploy.

## Live long record (10-06..11-24, deduped, LR8)
Longs overall: 17,441 trades, −0.195R each (shorts −0.079R). 77 long setups with ≥ 20 trades: 5 positive, only 2 positive without their best day.

| # | Setup | Trades | Sessions | Avg R | w/o best day | Best-day share |
|---|---|---|---|---|---|---|
| 1 | GEN-261027-01 (late MACD-hist pullback; pending ODP2) | 35 | 9 | +0.277 | +0.233 | 50% |
| 2 | GEN-261020-09 (midday QQQ-down z-dip) | 257 | 11 | +0.272 | −0.015 | 104% |
| 3 | GEN-261019-02 (PM band dip, QQQ down) | 26 | 9 | +0.081 | +0.023 | 75% |

## Part A — tighten the best live longs (≤ 2 changes each)
- A1 GEN-261027-01: check −0.026, 2023-24 −0.005 → FAIL in the backtest; its live edge does not reproduce (the engine is known to under-read live — L3-fromopen is the documented case). Keep as a live forward test only (ODP2).
- A1t (+ SPY 30-min return > 0, ADV ≥ $100M): check +0.006 but one session = 497% of check R, 2023-24 −0.016 → TIER B by the letter, not deployable.
- A2 GEN-261020-09: check −0.052 → FAIL; A2t worse.
- A3 GEN-261019-02: check +0.019 (w/o best day −0.003), 2023-24 −0.076, < 2 trades/session → TIER B, low-rep rotation only; A3t no lift.
- All six configs are negative on 2023-24 (the only clean out-of-sample half for GEN parents).

## Part B — momentum longs (new mechanism: UP1030 trend-day gate + new-high-of-day breakouts)
| Candidate | Check avg R | 2023-24 | Verdict |
|---|---|---|---|
| B1 NHOD-AM-TREND (10:30–11:30) | −0.067 | −0.230 (t −3.75) | FAIL |
| B2 PM-LEADER-NHOD (13:30–15:00) | −0.041 | −0.019 | FAIL (fit already −0.216) |
| B3 TREND-CLOSE-DRIFT (hold to 15:55) | −0.037 | −0.042 | FAIL; worst check day −72R (concentration) |
Breakout-chasing longs on up days do not hold up after costs. No meaningful hedge value (correlation with the Primary book ≈ 0). The same-day random-entry control is biased upward here; the Move Hunt baseline (~ −0.09 to −0.10R for random 45-min long bars) is the fair comparison.

## Next
Keep GEN-261027-01 on its live forward test (ODP2); drop new-high-of-day breakout longs; GEN-261019-02 only as a low-rep rotation setup.
