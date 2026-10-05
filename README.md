# MCF — Intraday Trading System

Research → backtest → paper trade → (eventually) live, for intraday setups across a 3,000–4,000
symbol US equity/ETF universe. Crypto and options guidance come later (see `docs/ROADMAP.md`).

**Start here:** `MARCOFLOW_CONTEXT.md` (lessons from the predecessor), `docs/DECISIONS.md` (owner decisions),
`docs/DATA_AND_BROKER.md` (stack), `docs/MARCOFLOW_ANALYSIS.md` (data deep-dive). Hosted dashboard:
https://claude.ai/artifact/LxSZBti7GjRxzKncf4Q1ow

**Status: Phase 0.5.** The engine, setup library, Alpaca paper-trading loop and
dashboard are built and tested on synthetic data. No strategy has been validated on real data yet.

## Design principles
1. **One code path for backtest and live.** A strategy is a pure function over a single
   symbol-day of bars up to "now". The backtester and the paper runner call the same code.
2. **Pessimistic fills.** Next-bar entries. Stop-before-target when both are inside one bar.
   Gaps through the stop fill at the open. Per-share and bps slippage on both sides.
   Published intraday edges are only a few cents per share, so a commission-only backtest is a
   gross backtest.
3. **No lookahead.** All prior-day statistics are shifted by one day. A test checks that
   truncating future data never changes past trades.
4. **Everything goes in the journal.** Every backtest run and every paper trade lands in SQLite
   (`data/journal.db`). The dashboard is built only from the journal.
5. **Expectancy over win rate.** See `docs/RESEARCH.md` §3 for why we track R-expectancy,
   profit factor and break-even win rate next to win %.

## Layout
```
config/default.yaml      all parameters (risk, costs, universe, per-setup params)
mcf/data/                bar schema, parquet cache, Alpaca downloader, synthetic data
mcf/features.py          VWAP, VWAP bands, RSI, ATR, relative volume, opening range (all causal)
mcf/strategies/          Strategy/Signal/DayContext interface + setup library
mcf/backtest/engine.py   bar-by-bar simulator + portfolio/risk allocator
mcf/analytics/metrics.py win rate, expectancy, PF, drawdown, breakdowns by setup/time/weekday/month
mcf/execution/           risk manager, Alpaca bracket-order broker, paper runner, fill reconciliation
mcf/journal.py           SQLite journal (runs, trades, orders)
mcf/dashboard/           static HTML dashboard generator
tests/                   engine and dashboard tests
```

## Quick start
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,alpaca]"
pytest -q
mcf demo                              # synthetic smoke run -> reports/dashboard.html
cp .env.example .env                  # add Alpaca PAPER keys
mcf download --symbols SPY,QQQ,AAPL --start 2024-01-01 --end 2025-01-01 --feed sip
mcf backtest --start 2024-01-01 --label "baseline"
mcf dashboard
mcf paper --watchlist SPY,QQQ,AAPL,NVDA,TSLA   # runs one session, then reconciles and rebuilds the dashboard
mcf brief --send                      # daily brief email (needs MCF_SMTP_* in .env)
python scripts/import_marcoflow.py    # rebuild data/marcoflow.sqlite from the committed export
python scripts/analyze_marcoflow.py   # regenerate docs/MARCOFLOW_ANALYSIS.md
python scripts/marcoflow_to_journal.py  # MarcoFlow trades as a dashboard reference source
```
Data you already have, such as a MarcoFlow export, can be imported from CSV with
`BarStore.from_csv_dir(csv_dir, "data/cache")`. Each CSV holds one symbol, with a timestamp column
first and then open/high/low/close/volume.

## Setups (Phase 0)
| name | basis | default |
|---|---|---|
| `orb` | 5-min opening-range breakout on the top-20 stocks in play by relative volume (Zarattini, Barbon & Aziz 2024) | on |
| `noise_band_momentum` | SPY/QQQ noise-area momentum (Zarattini, Aziz & Barbon 2024) | on |
| `intraday_momentum` | first half-hour return predicts the last half hour (Gao, Han, Li & Zhou 2018) | on |
| `vwap_reclaim`, `gap_and_go`, `gap_fade`, `vwap_reversion` | practitioner setups with weak or vendor-only evidence | off (experimental) |
