Educational only — not financial advice

# ticksel_1125: should setups be more selective about which stocks/tickers they trade? (research only)

Owner 11-25: be more selective with setups by ticker without cutting trade counts. Pre-registered (PREREG.md, ≤ 13 configs); E1-style 2-year backtest with bench10 rules (FIT 2024-10 + 2025-03..09; CHECK 2025-10..2026-11-04; T2 2023-01..2024-09; locked block never read); live 10-06..11-24 as a direction check only (CLAUDE.md STOP2 / RESEARCH_RULES 26). Setups: L3-fromopen, L3-lowdist, L3-rsi5hi, RW3, RW5, RW7, RW6, GEN-261029-06 (NM-ETF had too few tickers). Every rule had to hold on the research cost basis and on an adjusted basis that adds back half the modelled cost on sub-$20 names.

## Verdict: no exclusions, no ticker lists, no size tilts
- Individual tickers: a ticker's past results for a setup do not predict its future. Top- vs bottom-decile tickers (ranked on FIT) differ on CHECK with t < 2 for all 8 setups; FIT-vs-CHECK rank correlation −0.05..+0.13; live has ~1.1–2.0 trades per name per setup. B1 (drop bottom-decile tickers) and B2 (1.5× size on top-decile) both FAIL; B1's total-R "gains" are mechanical (dropping trades from a losing book). An apparent live edge for top tickers (+0.33R, t 3.3) came from the ranking window overlapping the live window; with ranks cut off at 10-05 it is +0.11R, t 1.25.
- Ticker traits: no trait bucket met the FIT bar (0 exclusion and 0 tilt configs qualified). Across all 297 FIT trait cells, a cell kept its sign on CHECK 53% of the time and on live 45% — a coin flip. The best tilt (L3 price) failed on the adjusted cost basis: the sub-$20 cost artifact.
- Rules: sizing tilts are on the "Stop doing" list (consultant_p3: −33 to −47R); live per-setup filters from short samples failed 0/31 (W4-NOFILTER).

## One lead (post-hoc, not a pass)
L3 family in high-ATR% names (ATR14 ≥ 8.8% of price): live +0.329R on 337 trades (w/o best day +0.289R, best day 30%) vs +0.009R on 407 other trades — nearly all of L3's live R. Lab support is partial (CHECK +0.11R vs the rest, t 2.7; FIT +0.05R, t 0.8; 2023-24 +0.02R, t 0.2) and part of it is the stock rather than the setup. Acting on it would cut ~55% of L3's trades or need a size tilt (both against owner rules). Option: a journal-only tag (no orders) scored after 20 fresh sessions — needs the owner's yes.

Rule-change context: see the live-window list in research/repsrot_1125 (10-14..11-24). Biases: lab universe 1,226 names vs ~4,200 live; static ETB/spread/ETF flags; no earnings or market-cap data. Scripts/data: scratchpad ticksel/ (not committed).
