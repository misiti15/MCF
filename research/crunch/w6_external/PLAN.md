# W6-external — pre-registered plan (written 2026-11-18 ~17:00 ET, before any scoring)

Educational only — not financial advice.

Research only. No config, runtime, setup or exit change; nothing merged that affects trading. Proposals carry reply codes for the owner.

## Data and conventions (fixed now)

- Live run (run_id 1) trades from the ten `mcf-data*` journals (Primary, On Deck, Testing A-F, Gen, Graveyard), sessions 2026-10-06..2026-11-17 (11-18 left out, as in Part 3). R = pnl_adj / (|entry - stop| x shares), LR8 costs in.
- Fit half = 10-06..10-27 (16 sessions); check half = 10-28..11-17 (15 sessions). A rule "holds" only if its sign is right in both halves.
- Daily bars: release asset `bars-2026-11/1day-2026-11-17.parquet` (08-31..11-17, ~5,150 names). Only values known before the open of the trade's session are used (prior close, prior 20-session dollar volume, prior 5-session return, today's open for the gap).
- SPY 1-minute bars 10-06..11-17 from the Alpaca market-data GET endpoint (read-only).
- The locked block 2024-11-01..2025-02-28 is not read. No 2-year data is used.
- Bar for any filter result: day-clustered t >= max(1.5, sqrt(2 ln N)), N = configurations tried in this workstream (counted below), and sign right in both halves; per-setup improve/worsen counts and avg R w/o best day + share are reported.
- Guardrails: sizing tilts and daily caps are on the "Stop doing" list (P8). X6 is run only because it is a different mechanism (scale by market variance known before the open, Moreira-Muir), not by setup record or a cap; it is labelled as such and needs owner consent before any further spend.

## Tests (one config each unless stated)

| ID | Source idea | Hypothesis (direction fixed now) | Configs |
|---|---|---|---|
| X1 | PBO / CSCV (Bailey, Borwein, Lopez de Prado, Zhu) | Picking the setup with the best in-sample record does not reliably pick an above-median setup out of sample: PBO > 0.5 for "best total R" selection over setups with >= 20 trades. Matrix = session x setup daily R (setup pooled across accounts), S = 8 contiguous blocks, 70 splits. Two selection metrics: total R and avg R per trade. | 2 |
| X2 | Deflated Sharpe / Harvey-Liu haircut | Few live setups survive a try-count-scaled bar: day-clustered t of daily R >= sqrt(2 ln N), N = number of distinct live setups ever run. Reported as a list, no decision. | 1 |
| X3 | Overnight-intraday reversal is concentrated in small/illiquid names and high-uncertainty periods (Branch-Ma via CXO; Turku 2011-2024 thesis) | Trades that fade the open gap (side opposite the gap, abs gap >= 2%) earn more in the lowest prior-20-day dollar-volume tercile than the top tercile, and more on high-uncertainty days (SPY prior-10-session realized vol above the fit-half median) than low. Cells reported; filter F3 = "skip gap-fade trades in the top ADV tercile" scored per setup. | 6 cells + 1 filter = 7 |
| X4 | Short-squeeze / short-selling risk concentrated in small, hard-to-borrow names (Engelberg-Reed-Ringgenberg 2018; Schultz 2024) | Short tail losses (R <= -1.5) are concentrated in shorts with prior 5-session run-up >= +25% and/or price < $10. Filter F4 = "skip shorts whose prior 5-session return >= +25%" improves short R in both halves. Buckets: price 4, run-up 3, gap-up 3. | 10 cells + 1 filter = 11 |
| X5 | Market intraday momentum (Gao, Han, Li, Zhou 2018, JFE) | Trades entered at or after 15:00 ET that align with SPY's prior-close-to-10:00 return (long if > 0, short if < 0) have higher R than those against it. Filter F5 = "after 15:00 take only aligned trades". | 1 split + 1 filter = 2 |
| X6 | Volatility-managed exposure (Moreira-Muir 2017, JF) | Scaling each day's risk by 1/RV (RV = variance of SPY daily returns over the prior 10 sessions, weights normalised to mean 1 on the fit half, capped at 2x) raises the daily Sharpe of the pooled book and Primary's journal in both halves. Plateau check: lookbacks 5 and 20. | 3 |
| X7 | Breadth / fundamental law (Grinold-Kahn; Clarke-de Silva-Thorley implied breadth) | Descriptive: implied breadth of Primary's current six = N / (1 + (N - 1) rho_avg) from daily-R correlations; no decision. | 0 |

Total configurations pre-registered: **26** (N for the bar: sqrt(2 ln 26) = 2.55).

## Outputs

RESULTS.md (failures first), SOURCES.md (ten ideas, citations, mapping to MCF), code/ (scripts), no data files over 100 kB.
