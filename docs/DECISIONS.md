# Owner decisions log

Dated record of what the owner decided and how MCF implements it. Newest first.

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
