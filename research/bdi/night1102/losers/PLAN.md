Educational only — not financial advice

# night1102 / losers — plan (written before scoring)

1. Loser set: all 5 intraday journals (run_id 1, live paper), 2026-10-20..11-02. R = pnl_adj / (|entry-stop| x shares).
   Loser = R <= -1, plus each account-day's 10 worst trades. Primary reported first.
2. Per loser: setup, side, entry/signal time, symbol type (stock / 3x ETF / inverse ETF, from a hand list), entry vs the
   signal bar's range, MFE before exit, minutes to stop, SPY from open at entry; 1-minute bars (data/replay 1Min to
   10-26, read-only Alpaca GET for 10-27..11-02 into scratch for the loser symbols only).
3. What-ifs on the 1-minute path (costs in: 1c + 1 bps per side, +2c on stop fills; same $ risk):
   wait 1/3/5 bars; limit at VWAP / 0.25R pullback (fill only if touched within 30 min, else no trade); time stop
   30/60 min; break-even after +0.3R; partial 1/2 at +0.5R; wider stop 1.5x at same $ risk (fewer shares);
   opposite side in hindsight. Measured on ALL live trades (not only losers) to avoid selection bias — the loser-only
   view is reported but never used to pick.
4. Patterns: group losers (inverse-ETF shorts, leveraged ETFs, stacked same-theme lots, late-day, first-5-min, market
   against at entry...). One adjustment per pattern; test on all live trades (paired with/without) and on the 2-year
   lab trades (research/history2y/data/lab_trades.parquet + cache_hist 1-minute paths) outside the locked block.
5. Count every configuration scored. Report failures first.
