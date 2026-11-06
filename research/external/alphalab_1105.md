# Alphalab (github.com/cve-zh00/alphalab) — ideas extracted 2026-11-05

Read-only review of the public README / repo layout (commit of 2026-11-03). License: **Alphalab Non-Commercial
License (NC-1.0)**, so **no code is copied into MCF**. Only the published, citable methods below are taken as
ideas, and each one gets our own implementation and our own tests under RESEARCH_RULES (costs in, locked block
unread, configs counted). Alphalab publishes no live or backtest results, so none of its claims are used as evidence.

What it is: a long-only S&P 500 value + AI-debate system (SEC XBRL valuation, momentum and sentiment filters,
~21-day holds, residual-vol sizing, Alpaca paper). Very different from MCF's intraday book.

## Already in MCF (no action)
- Deflated Sharpe ratio (`mcf/research/gates.py::deflated_sharpe`), configs counted, locked holdouts.
- Deterministic client order ids, kill switch / halts, sell-before-buy and 12-1 momentum (long-hold book `mcf/longhold`).

## Use now (intraday) — research queue
| ID | Idea | Source method |
|---|---|---|
| XA-PBO | Probability of backtest overfitting (CSCV) on every multi-config study, reported next to BAR90 | Bailey et al. 2016 |
| XA-EPROC | Anytime-valid forward monitor (betting-martingale e-process) for forward shadows / Testing setups: can be checked every session with no peeking penalty; informs, never auto-promotes | Waudby-Smith & Ramdas 2024 |
| XA-BRIER | Brier score + reliability / resolution split for Hunch and the market compass (is a stated 60% right 60% of the time?) | Brier decomposition |

## Backlog (setup / risk / swing) — status idea, gates in mcf/research/backlog.py
- `xa-1105-turbulence-sensor` (risk): Mahalanobis turbulence of sector-ETF returns as a market-condition sensor (REGX follow-up).
- `xa-1105-resid-vol-sizing` (risk): size by inverse 60-day residual (vs SPY) volatility, compared with RISK1 equal-$-risk.
- `xa-1105-hwm-giveback-exit` (exit): intraday high-water-mark trail — arm at +k R, exit after giving back 30% of the peak.
- `xa-1105-swing-value-momentum` (strategy, swing): PIT fundamental value (shrunk margin of safety, sector z-score) + 12-1 momentum falling-knife filter, multi-week holds.
- `xa-1105-swing-garch-stop-cooldown` (exit, swing): GARCH(1,1) volatility-scaled stop anchored to the first lot (never lowered by adds), HWM giveback trail, 5-day re-entry cooldown.
- `xa-1105-swing-sentiment-overlay` (strategy, swing): headline-sentiment penalty (FinBERT-type) on swing candidates — needs a news feed we don't have yet.

Educational only — not financial advice.
