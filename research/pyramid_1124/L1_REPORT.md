Educational only — not financial advice

# Project Pyramid — Team L1: catch the movers we miss (longs) (2026-11-24)

Research only. Pre-registered and hashed (scratchpad/pyramid/L1/PLAN.md, 23:28 UTC; selection frozen 23:43 UTC before check). 12 configs (3 candidates × 2 rule values × 2 exits). bench10 pipeline, LR8, testing book, 1-min exits. FIT 170 / CHECK 276 / 2023-24 427 sessions. Locked block never read. Result: 0 of 3 pass; all FAIL.

| Candidate | Rule (selected config) | Fit | Check (t) | 2023-24 | Corr with book proxy | R on book's 10 worst check days |
|---|---|---|---|---|---|---|
| C1 RS-RED | 10:00–11:30, QQQ ≤ −0.3% from open, stock green & above VWAP, outperforms QQQ by ≥ 1%; 2R/1R | −0.059 | −0.104 (−3.05) | −0.132 | −0.21 | +155.8R |
| C2 SECTOR-LEAD-PB | 10:05–13:00, stock's sector ETF strongest of 11 and ≥ 0.3% over SPY, VWAP-test hold; 2R/1R | −0.078 | −0.108 (−3.28) | −0.067 | −0.32 | +355.8R (but −2,329R overall on check) |
| C3 OR20-RECLAIM | 10:00–12:00, close above the 09:30–09:50 high, volume ratio ≥ 2.5, above VWAP; 2R/1R | +0.020 (best day 281%) | −0.055 (−1.72) | +0.024 | −0.13 | +39.8R |

Plateau check: all 12 configs negative on check (−0.055 to −0.121).

## Why they fail
- They are bets on the tape turning up: +0.13 to +0.43R per trade on SPY-up days, −0.19 to −0.59R on SPY-down days. The hedge value is real but far too costly.
- Confirmation entries come too late: by the time "above VWAP / high retaken" fires, the move is mostly done. The 11-24 long movers were bid at 09:35–09:40, before the 09:50 entry floor.
- Rotation days 11-10/11-11/11-24 could not be scored (bar data ends 11-04). Biases (survivorship, close fills, later sector map) all favour the candidates, so true results are worse.

## Next (backlog, untested)
- (a) A "tape turned up" gate (SPY reclaims its morning VWAP) on C3 only, 1 config.
- (b) Catching the 09:35–09:40 rotation bid needs entries before 09:50 (owner decision) or a pre-open sector-flow predictor.
- (c) Not recommended: using C1/C2 as a book hedge.
