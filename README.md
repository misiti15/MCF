# MCF — Intraday Trading System

Research → backtest → paper trade → (eventually) live, for intraday setups across a 3,000–4,000
symbol US equity/ETF universe. Crypto and options guidance come later (see `docs/ROADMAP.md`).

**Start here:** `MARCOFLOW_CONTEXT.md` (lessons from the predecessor), `docs/DECISIONS.md` (owner decisions),
`docs/DATA_AND_BROKER.md` (stack), `docs/MARCOFLOW_ANALYSIS.md` (data deep-dive). Hosted dashboard:
https://misiti15.github.io/MCF/live/ (EOD reports: https://misiti15.github.io/MCF/live/report.html)

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

## Accounts (paper, owner 2026-11-11 names)

Display names only; the internal keys, state branches, `MCF_ACCOUNT` values and order prefixes are unchanged.

| Key (`MCF_ACCOUNT`) | Name | Role |
|---|---|---|
| `primary` | Primary | promoted setups |
| `testing` | On Deck | promotion candidates (2-3x Primary's size, eventually ~15-30 setups); formerly "Testing 1" |
| `testing2` | Testing A | testing area; formerly "Testing 2" |
| `explore1` | Testing B | testing area; formerly "Explore 1" |
| `livelab` | Testing C | testing area; formerly "Live Lab" |
| `gen` | Setup Generator | machine-generated setups |
| `graveyard` | Graveyard | lowest performers |

Setups advance testing area → On Deck → Primary. On/off switch experiments are field-tested only in the testing areas.

## Kill switch (LR4, owner 2026-11-11)

Stops trading on one account or all of them within about a minute, without cancelling any GitHub run.

1. Open the repository on github.com and click **Actions**.
2. In the left list click **kill** (the workflow `.github/workflows/kill.yml`).
3. Click **Run workflow** (top right of the run list).
4. **Use workflow from**: leave the default branch.
5. **Account**: `primary` (or another account, or `all`).
6. **Mode**:
   - `no-new-entries`: no new entries for the rest of the session; open trades keep their stops and targets, and the
     normal flatten (15:55, or 5 min before an early close) still runs.
   - `flatten`: no new entries, and every MCF order on the account is cancelled and every MCF position closed now
     (the kill run does it itself and the trading run does it too).
   - `resume`: clears the flag (with `all`: clears every account's flag); new entries resume on the next poll.
7. Leave **dry_run** unticked (ticked = only log what would happen) and click the green **Run workflow**.

The flag stays set, also for the next sessions, until you run `resume`. It is the file `HALT.json` on the branch
`mcf-control`; each trading run checks it every poll and shows it in its status (`health.kill`). Only MCF's own orders
(order prefix per account) are touched, never anything else on an account. Educational only — not financial advice.

## Setups (Phase 0)
| name | basis | default |
|---|---|---|
| `orb` | 5-min opening-range breakout on the top-20 stocks in play by relative volume (Zarattini, Barbon & Aziz 2024) | on |
| `noise_band_momentum` | SPY/QQQ noise-area momentum (Zarattini, Aziz & Barbon 2024) | on |
| `intraday_momentum` | first half-hour return predicts the last half hour (Gao, Han, Li & Zhou 2018) | on |
| `vwap_reclaim`, `gap_and_go`, `gap_fade`, `vwap_reversion` | practitioner setups with weak or vendor-only evidence | off (experimental) |
