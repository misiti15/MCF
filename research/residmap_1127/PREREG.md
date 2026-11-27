Educational only — not financial advice

# RESID-MAP-1127 — pre-registration (inspector 1127 idea #5; research only, nothing changed)

Written 2026-11-26 ~21:50 ET, committed before any score. Question: is there STOCK-SPECIFIC (market-adjusted) intraday
edge in the cross-section of the lab universe, measured as a decile long-short spread held to the close, net of costs?

## Data
- 1-min RTH bars: data/cache_fresh/1Min (469 symbols, 2022-10..2024-09-13) + data/cache_hist/1Min (1,226 symbols,
  2024-09-16..2026-11-04); a symbol's two files are concatenated, duplicate minutes dropped (cache_hist wins).
- Universe: those symbols minus ETFs/ETNs/funds (name regex on data/universe.csv, in rm_build.py) and minus SPY (the
  market leg). Survivorship: the list is as of 2026-10 (disclosed; a long-short decile spread is less exposed than a
  long-only book, not immune). T2 has ~469 symbols, FIT/CHECK ~1,226.
- Locked block 2024-11-01..2025-02-28: never read. Every parquet read filters it out at read time and the builder
  asserts no row in it survives; a session whose previous session is in the block (2025-03-03, 03-04 for F5) has
  NaN prior-day features and drops out of the cells that need them.
- Splits (by session date): FIT 2024-10-01..2024-10-31 + 2025-03-01..2025-09-30; CHECK 2025-10-01..2026-11-04;
  T2 2023-01-01..2024-09-30.

## Cells: 4 checkpoints x 5 features = 20 configurations (no others scored)
Checkpoints c = 09:45, 10:30, 12:00, 14:00 ET. Information set = bars with timestamp < c (price_c = close of the c-1
bar). Entry = open of the first bar in [c, c+4 min]; exit = close of the last bar at or before close-5 min (15:55;
12:55 on half days, detected from SPY's last bar < 15:00). 14:00 is skipped on half days. Market adjustment
(beta = 1, no history needed so nothing touches the locked block): x_resid = x_stock - x_SPY over the same interval.
- F1 RGAP: ln(open_d / close_{d-1}) residual (overnight gap vs SPY).
- F2 RINTRA: ln(price_c / open_d) residual (move since the open).
- F3 RLAST5: ln(price_c / close of bar c-6) residual (last 5 minutes).
- F4 RZ: F2 / (sd of the stock's residual 1-min log returns since the open x sqrt(n minutes)) (idiosyncratic z).
- F5 RPREV: ln(close_{d-1} / close_{d-2}) residual (prior-day residual return).
Eligibility per (session, c): close_{d-1} >= $5; prior-session dollar volume >= $5M; >= 80% of the minutes from 09:30
to c present (>= 10 for 09:45); entry and exit bars present; finite feature. A cell-session needs >= 100 eligible names.

## Spread and costs
Per (session, c, feature): sort eligible names into deciles of the feature. Leg return = simple return entry->exit.
Gross spread = mean(top decile) - mean(bottom decile). Orientation: the sign of each cell's FIT mean gross spread fixes
which decile is long (s = +1 long top / -1 long bottom); CHECK and T2 use that sign unchanged.
Net spread (bps) = s*gross - (mean cost of the long leg + mean cost of the short leg), each leg costed per name as a
round trip under LR8 (mcf/costs.py lot_costs, config/default.yaml live_model, market entry + market exit, $10,000 notional
per name, dated fees). Stress (reported, not the bar): LIVE-L "market" a-term by price bucket
(research/primshorts_1126/cells_live.json, bps of price per round trip) instead of LR8 — LR8 sits on paper fills, so a
bar-price study needs the spread part LIVE-L carries.

## Pass bar (ideas.json, all required, LR8 net)
1. Mean net spread > 0 on FIT, CHECK and T2 each.
2. Daily t (mean / sd x sqrt(days)) >= 2.45 on pooled CHECK+T2 days.
3. Avg net per session without the best session > 0, and the best session's share of total net < 50% (CHECK and T2 each).
4. Same sign (> 0) on SPY-up and SPY-down days (SPY return over the same entry->exit window), CHECK and T2 each.
Lineage: N ≈ 8,891 (regsteer_1126) + this week's later studies (≈ 8,915 at stopx/cfprimary, + taileff) + 20 here ≈ 8,945;
the lineage-corrected bar (t ≈ 4.3) is shown beside every t; the pass bar is the ideas.json 2.45.

## Reported for every cell
Mean net/gross bps per split, daily t per split and pooled, avg w/o best day + best-day share, SPY-up/down means,
decile monotonicity (Spearman of decile mean vs decile rank, CHECK), LIVE-L stress, mean names per decile.
Goal metrics for any passing cell (or the best cell if none): red days per 21, worst-5 sessions, 20-session floor (bps).
DECISION draft only if a cell passes; it would go to research/backlog.jsonl as a setup idea, never straight to config.
