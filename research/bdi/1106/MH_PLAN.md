# MH1106-P1 — "defensive rotation long" precursor, pre-registered 2026-11-06 ~23:20 ET, before any two-year number

*Educational only — not financial advice. Research only; nothing in config/ or the trading path changes.*

**From the Move Hunt 11-06** (moves_1106_out.txt): on an up open that rolled over in tech (SPY +0.74% / QQQ +0.68% at
10:00, QQQ −0.21% by 10:30, SPY closed flat = QDAY *quiet* day), 13 of the 25 biggest tradable long moves were
low-beta defensives that had not joined the open rally (TSN, HSY, KO, SBUX, MDLZ, HDV, WMT, PM, XLP, DRI, QSR, VONV,
PVAL), decision 09:35–09:40, extremes 10:24–11:09, 1.0–1.6 daily ATR. The only live setup on them was Gen
`GEN-261021-02` (09:50, 85 trades +35.9R), which skipped 6 of them on "max positions for this setup".

**Rule (one configuration).** At the 09:50 lab bar (first live-eligible bar, entry at its close):
- SPY from its open (lab context `spy_fo`, tod 950) **≥ +0.40 %**;
- the stock's **60-session daily beta to SPY ≤ 0.50** (daily close-to-close returns, sessions before the day,
  ≥ 40 valid; `research/history2y/data/daily.parquet`);
- the stock's **fromOpen ≤ +0.10 %** (it has not joined the rally);
- adv20 ≥ $95M, close ≥ $5.
- **Long, t1s1** (target and stop 0.25 × daily ATR, 15:55 flatten) = the frame outcome `r_long_t1s1`, re-costed to
  production costs (entry + exit $0.01 + 1 bp each side × the time-of-day multiplier, + $0.02 stop slippage on
  losers; tier 3 below $5 not needed).

**Base rate:** every other liquid name (adv20 ≥ $95M, close ≥ $5) at the same 09:50 bar on the same qualifying days, same
geometry and costs. Precision = win share; excess = class avg R − base avg R on the same day.

**Data:** lab frames + context, open months only (locked block 2024-11-01..2025-02-28 never read, asserted).
TRAIN ≤ 2026-02-28, VALID 2026-03-01..2026-11-04.

**Pass (Testing / Live Lab candidate, BAR90):** configs tonight N = 2 (SQZ1 + this) → full bar 1.50, BAR90 1.35.
avg R after costs > 0 in TRAIN and VALID; excess day-clustered t ≥ 1.35 on all days; positive avg R on up AND down
(SPY open-to-close ±0.25 %) sessions; walk-forward positive months ≥ 54 %; avg R without the best day > 0 (best day's
share reported, flagged ≥ 50 %); n ≥ 300 on ≥ 30 days. **Reported regardless:** QDAY split by day type (up / down /
quiet) and by SPY vs its open at 10:00 (here always above by construction), per-month table.
