# Data, broker and infrastructure choice (2026-10-05)

*Prices and features come from vendor pages as summarised by search results on 2026-10-05.
Re-check them before paying. Educational only — not financial advice.*

## What MarcoFlow's history says about data and timing
From `docs/MARCOFLOW_ANALYSIS.md`:
- **Data:** 5-minute bars from Yahoo, about 15 minutes delayed, scanned every 5 minutes.
- **Timing:** entries came a median 6 minutes after the signal was recorded, so the real lag from price move to fill was 20+ minutes.
- **Entry cost:** fills averaged **+0.16% worse** than the signal price. That is most of the −0.28% per-trade paper loss.
- **Persistence test:** 15 minutes of waiting cost about 14 win-rate points.
- **Short holds:** 470 trades held ≤ 5 minutes won only 14.9%. The fixed 1.25% stop and the 0.3% trail sat inside normal noise.
- **Volume data:** `volumeRatio` is 0 on most rows and IEX volume is about 2–3% of the tape. The volume features MarcoFlow relied on were mostly missing.

**MCF rules that follow:**
1. Real-time **consolidated (SIP)** 1-minute bars, streamed, not polled.
2. Decide on bar close.
3. Entry and stop orders **rest at the broker** at the trigger price, so latency can't move the fill.
4. Stops and trails are sized in **ATR/R**, never fixed percentages.

## Robinhood (the owner's account): verdict for now
Robinhood Agentic Trading (MCP at `agent.robinhood.com/mcp/trading`, soft launch 2026-05-27) is rolling out more widely after HOOD Summit (9/29–30). It is free, and a headless Python process can call it through the MCP SDK with OAuth.

**Not usable as MCF's primary venue today:**
- **No paper trading.** Agent orders are real orders.
- **No short selling** in the Agentic account (long equities, options and crypto only; no margin borrowing).
- **No documented bracket or OCO orders**, so stops can't rest at the broker together with targets.
- **No streaming or bulk bar data.** Data comes one tool call at a time, which can't scan 3,500 symbols every minute.
- **Rate limits and token lifetime aren't published.** "Trade approvals" is on by default and must be switched off for automation.
- Unofficial Robinhood stock APIs break the terms of service. Never use them.

**Plan:** keep a broker interface so Robinhood can be added later as a **long-only live venue** once MCF's paper results pass the gates. Revisit if Robinhood adds shorts or a sandbox.

## Recommended stack
| Need | Choice | Cost |
|---|---|---|
| Paper trading + execution (long & short) | **Alpaca** (paper now, live later; same code) | $0. Easy-to-borrow shorts have no borrow fee. Hard-to-borrow locates are live-only. PDT rule retired 6/4/2026. |
| Backtest history (1-minute, multi-year) | Alpaca SIP history (free once data is more than 15 minutes old) | $0 |
| Real-time data, 3,500 symbols | **Alpaca Algo Trader Plus**: full SIP; `bars` websocket with `*` wildcard = 1-minute bars for every symbol | **$99/mo**. Free IEX is fine for building and testing the plumbing, but paper results on IEX data won't be trusted (MarcoFlow lesson). |
| Alternative data | Massive (formerly Polygon) Advanced: `AM.*` all-symbol minute stream, 20 years of history | $199/mo |
| Process host (always on in market hours) | Oracle Cloud Always Free (if capacity is available) or a Hetzner VPS | $0 or about €6/mo |
| Daily email | Gmail SMTP with an app password | $0 |
| Hosted dashboard | Private Claude artifact now; Cloudflare Pages + Cloudflare Access (free) for an automatically updated private site | $0 |

Ruled out at this scale:
- Schwab: 500 symbols per stream, 7-day re-login, no paper account.
- IBKR: 100 market-data lines.
- Tiingo and Alpaca Basic for live decisions: IEX only.
- Databento: price unclear and possibly $4k/mo.
- GitHub Actions for the trading loop: 6-hour job cap, and 2,000 minutes/month on private repos. It is fine for the brief and the dashboard build.
