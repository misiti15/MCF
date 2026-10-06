# Owner decisions log

Dated record of what the owner decided and how MCF implements it. Newest first.

## 2026-10-06: fourth round (research swarm, heat score, daily improvement)

| Topic | Owner request | What was done |
|---|---|---|
| Heat score | Use a bot swarm to tune MarcoFlow's heat score into the best weighted version for viable longs and shorts. | Heat ported and recomputed on SIP data (1,000 names, 63 sessions). Five tuners tried ~19,200 configurations and an auditor checked them; the locked test was scored once. The original is negative everywhere. The surviving version is a *consistent* reversion score, gated by time of day: heat_fade_short (09:50–10:30) and heat_fade_long (11:05–13:30) are paper-only. See `research/heat/HEAT_STUDY.md`. |
| Setup research | Research as many sources as possible for the most common and best intraday setups, and build setups from them. | Four research families (~117 sources, via search summaries because page fetches were blocked), synthesised into 17 ranked specs. Eight setups were built and screened on 63 sessions of SIP 1-minute bars. Only orb20_a passed, and thinly. The previously enabled ORB-5 and noise-band setups lose after costs and are off. See `research/SETUP_SCREEN.md`. |
| Daily improvement | Every live day better than the last. | Not achievable for daily P/L: no documented setup does it, and chasing it overfits. Instead, each close produces a review (`reviews/` on the state branch) scoring execution, data, every rule's what-if cost or saving, and results against yesterday and the 5/20-day averages. Setups change only through the gates. |

## 2026-10-05: third round (go-live)

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Fill realism | Paper fills anything the price touches; results must be as close to real fills as possible. | Before every order: live SIP quote. Skip if the spread is > 30 bps or > 25% of the stop distance; cap size at 10% of the symbol's recent 1-minute volume. Every trade records entry slippage vs the signal price and an adjusted P/L that adds real-book stop slippage; target fills are flagged as touch fills. See `live:` in config. |
| Universe | More tickers only if they are good for the setups. | Two tiers, no fixed count (4,954 today). Extended-tier names ($1–5M ADV) trade only when in play (opening rvol ≥ 3×), at 3× the slippage assumption. |
| 9:30–9:50 | Soft rule: very volatile and hard to capture with any latency; there may be opportunities. | `live.no_entry_before: "09:50"`. Signals in the window are journaled as **shadow** and simulated after the close, so the window's real value is measured before the rule is revisited. Discovery also starts at 09:50. |
| New setups | A built-in way to add setups as they're noticed, e.g. layered rules (RSI14 > 65 + above the 20 SMA). | Weekly `discover` workflow mines 1–3-layer rules on ~1,500 liquid names, 60 sessions: found on the older 2/3, checked on the newest 1/3, first trigger per symbol-day, costs in R. Candidates appear in the dashboard's Setup lab. Promotion is a config entry (`type: rule`), never automatic. |
| Data | Subscribed to Alpaca Algo Trader Plus (SIP). | `data.feed: sip`; real-time SIP bars and quotes verified 2026-10-05. |
| Go-live | Trade and collect data automatically from the 2026-10-06 open; show it live on the dashboard as "MCF Update" against MarcoFlow. | GitHub Actions `trade` workflow (see `docs/OPERATIONS.md`); status every 2 minutes on the `mcf-data` branch; dashboard section "MCF Update" reads it. MCF closes only its own positions (`mcf-` order ids). |

## 2026-10-05: second round

| Topic | Owner decision | How MCF applies it |
|---|---|---|
| Success model | **Win % first, then tweak setups to hold winners longer.** | Two-stage scorecard. (1) **Success rate** = price reached +1R before −1R, measured to the end of the session whatever the exit did. It is symmetric, so a coin-flip setup scores 50% and target/stop geometry can't inflate it. Setups are selected on this first. (2) Exit tuning (scale-outs, trails, holding longer) then raises P/L on setups that already pass (1). |
| Threshold | **65%** | Gates: success rate ≥ 65% **and** realized win rate ≥ 65% **and** expectancy > 0, out of sample, after costs, ≥ 200 trades. |
| Universe | Scan about 3,500+ tickers often. A bigger pool means more chances; favour liquid names for easy entry and exit. | `mcf universe`: top 3,500 by **consolidated** 20-day $ volume (≥ $10M), price ≥ $5, shortable/ETB flags. `mcf.data.scanner`: snapshot scan of the whole universe every minute (35 requests per pass, within the free 200/min limit). |
| Shorting | Crucial. | Kept as a hard requirement for the execution venue (see `docs/DATA_AND_BROKER.md`). |

## 2026-10-05: first round of answers

| # | Topic | Owner decision | How MCF applies it |
|---|---|---|---|
| 1 | MarcoFlow rules | **No MarcoFlow hard rule carries over** unless it is tested and verified to add value for MCF. | Skipped entry hours, the knife guard, "never cap entries" and so on are all off. Each one can be added back as a toggle once a backtest shows it adds value. |
| 2 | Win rate | 90% isn't required, but **a win rate not well above 50% means the system is too close to failing.** | Every setup must clear **both** gates out of sample, after costs: win rate ≥ 55% **and** expectancy > 0. Scale-out exits (bank half at +1R, stop to breakeven) are on by default. The dashboard shows win % next to break-even win %. |
| 3 | Data / broker | Efficiency first. Use the Robinhood MCP if possible; otherwise pick the cheapest option with better data. Learn from MarcoFlow's data timing and execution. | See `docs/DATA_AND_BROKER.md`. Alpaca now (paper, free → $99 SIP). Robinhood Agentic is kept as a later long-only live option. |
| 4 | Sizing | **100 slots** to start; make full use of funds and don't miss opportunities. | `slots: 100`, capital per slot = equity × 2 ÷ 100. Risk-based cap of 0.25% equity per trade. Each setup can use up to 60 slots. |
| 5 | Shorting | Long **and** short, with as many trading options as possible. | `shorts.enabled: true`. Live shorts only on names the broker flags shortable and easy-to-borrow (no borrow fee intraday at Alpaca). |
| 6 | Automation | Fully automated paper trading from the start, then a move to live funds. | The paper runner places orders with no approval step. Live is the same code with `paper=False`, after the gates in #2 pass. |
| 7 | Reporting | A daily email to misiti15@gmail.com **and** a free hosted page. The owner values an overview of data and process. | `mcf brief --send` (Gmail SMTP app password). Hosted dashboard: https://claude.ai/artifact/LxSZBti7GjRxzKncf4Q1ow (private Claude artifact). |
| 8 | MarcoFlow | MCF runs **independently** of MarcoFlow. Use MarcoFlow's data to learn what to do right or differently, and explore anything worth building on. | MarcoFlow is read-only reference data (`docs/MARCOFLOW_ANALYSIS.md`, a reference source on the dashboard). There is no runtime dependency on it. |
