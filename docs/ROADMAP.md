# Roadmap

## Phase 0: Foundation ✅ (this commit)
- Strategy/Signal interface shared by the backtester and the paper runner
- Conservative bar-by-bar simulator, per-setup position sleeves, daily loss stop
- Setup library: ORB on stocks in play, noise-band momentum, last-half-hour momentum, plus experimental setups
- SQLite journal; static dashboard (P/L, win rate vs break-even, expectancy, setup / time-of-day / weekday / month breakdowns)
- Alpaca paper runner with broker-side bracket stops; end-of-day fill reconciliation

## Phase 0.5: MarcoFlow lessons and owner decisions ✅ (2026-10-05)
- [x] MarcoFlow history in SQLite, deep-dive analysis (`docs/MARCOFLOW_ANALYSIS.md`), and a reference source on the dashboard
- [x] Decisions log (`docs/DECISIONS.md`), data/broker choice (`docs/DATA_AND_BROKER.md`)
- [x] Scale-out exits, 100-slot sizing, long/short with an easy-to-borrow check, promotion gates (now success ≥65%, win ≥65%, expectancy >0, PF ≥1.2)
- [x] Daily Brief email (`mcf brief --send`); hosted dashboard (private Claude artifact)

## Phase 1: Real data and validation (next)
- [x] Alpaca paper keys verified (2026-10-05). They are MarcoFlow's account; its 126 leftover positions were closed (`reports/marcoflow_closeout/`). A separate MCF paper account is still recommended.
- [ ] SIP plan ($99, Algo Trader Plus): owner approved 2026-10-05. After subscribing, set `data.feed: sip` and `ALPACA_DATA_FEED=sip`.
- [x] Universe without a fixed cap: 4,947 symbols (3,755 core ≥ $5M ADV, 1,192 extended $1–5M traded only when in play), ATR ≥ 1% of price
- [x] Sustainability gate: ≥ 6 months out of sample and net-positive R in ≥ 2/3 of months, on top of the win-rate / expectancy / profit-factor gates
- [ ] Download 2–5 years of 1-minute bars for the liquid universe. Storage is roughly 1–2 GB of parquet per year for about 3,000 names.
- [ ] Import MarcoFlow trade history and data; compare its setups and results to ours
- [ ] Walk-forward validation: parameters fit on rolling in-sample windows, reported only out of sample
- [ ] Cost sensitivity sweep (0–4¢/share) for each setup: report the break-even slippage
- [ ] Parallel backtest by date (multiprocessing) for the full universe
- [ ] Full noise-band implementation: trailing stop and re-entries
- [ ] Overnight→intraday cross-sectional reversal setup
- [ ] MarcoFlow-family setups rebuilt as explicit rules and run through the same gates (see `docs/RESEARCH.md` §5)

## Phase 2: Paper trading at scale
- [ ] Websocket streaming bars (SIP `bars` wildcard `*`) instead of polling, for 3,000+ symbols
- [ ] Always-on host (Oracle Always Free or a ~€6 VPS) with data-count health checks per ET day (MarcoFlow lesson)
- [ ] Stop-entry orders resting at the broker (no latency between trigger and fill)
- [ ] Pre-market scanner (gap, pre-market relative volume, news/earnings flags)
- [ ] Scheduled daily jobs: pre-market scan → session → reconcile → dashboard publish
- [ ] Backtest-vs-paper drift report: same days, same signals, slippage comparison
- [ ] Automatic setup kill-switch when rolling expectancy falls below a threshold

## Phase 3: Improvement loop
- [ ] Daily attribution: which filters (relative volume, gap, time, regime) separate winners from losers
- [ ] Regime features (VIX, trend/chop, macro calendar) used as setup on/off gates
- [ ] Portfolio risk: correlation and sector caps; volatility-targeted sizing

## Phase 4: Expansion
- [ ] Crypto (Alpaca crypto API, 24/7 sessions: the session model must become configurable)
- [ ] Options guidance: 0DTE/weekly overlays on top of equity signals (Alpaca options API)
- [ ] Live execution: Alpaca live (same code, `paper=False`). Optional long-only mirror on the
      Robinhood Agentic MCP (official; no shorts, no paper, no brackets as of 2026-10). Never use unofficial wrappers.
