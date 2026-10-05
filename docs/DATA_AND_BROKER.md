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

## Robinhood (the owner's account): re-verified 2026-10-05

The owner's normal Robinhood **margin** account can short (rolled out late 2025). The **Agentic (MCP) account cannot**:
- **Long only (official):** "You can currently use a built-in or external agent to place **long** equities, options, and crypto orders."
  Order types: market (shares or dollars), limit, stop-limit, stop-market.
  https://robinhood.com/us/en/support/articles/trading-with-your-agent/
- **Separate account only (official):** the agent "can view information from your other Robinhood accounts" but "can **only place
  trades in its dedicated Agentic account**". That account is cash or "limited margin", and "margin borrowing isn't currently
  available in Agentic accounts". Robinhood only allows shorts in a margin account with borrowing.
  https://robinhood.com/us/en/support/articles/setting-up-an-agent/
- **HOOD Summit (Sept 29–30, 2026)** announced built-in agents, Agent Apps, "Loops", weekend equities and perps.
  **Nothing on agent short selling**, and no published roadmap item for it.
- **Data:** 5-minute bars at the finest (no 1-minute). Quotes take 20 symbols per call and come from Nasdaq Basic, not SIP.
  No streaming. Rate limit unpublished (one community measurement: about 240 calls/min).
  The **scanner** (`run_scan`, Legend's 60+ filters including relative volume) returns server-side ranked candidates,
  but its result size and refresh rate are unverified.
- **No paper trading.** Exchange data terms likely restrict using Robinhood's Nasdaq Basic data to drive trades elsewhere.

**Verdict:** the Robinhood MCP can't be MCF's primary venue while it is long-only, has no paper account, and has no 1-minute
or bulk data. Keep it as (a) an optional **long-only live mirror** later, and (b) a possible **second-opinion scanner**
(`run_scan`) once the owner's agentic account is set up. Re-check each quarter: if Robinhood adds agent shorting,
it becomes a real execution candidate.

## Free or cheaper real-time data: every option weighed
| Source | Cost | Whole market (3,500)? | Verdict |
|---|---|---|---|
| **Alpaca free: snapshots (IEX)** | $0 | **Yes, by polling**: 100 symbols/request → 35 requests per full pass; 200 requests/min allows one pass a minute | **Start here.** IEX prices track the tape. Volume is about 2–3% of the tape, so MCF uses *relative* volume within IEX. `scripts/validate_iex_proxy.py` checks it against SIP on history before we rely on it. |
| Alpaca Algo Trader Plus (SIP) | $99/mo | Yes, streamed (`*` wildcard) | Upgrade if the IEX check fails, or before live funds. |
| Robinhood MCP | $0 | Scanner only; quotes 20/call; 5-min bars | Helper, not primary (see above) |
| Schwab Trader API | $0 (account) | 500-symbol stream, one connection; REST 120/min | Needs a Schwab account; 7-day re-login. Backup option. |
| Moomoo/Futu OpenAPI | $0 (account) | 100–300 subscriptions | Too small |
| Tradier | $0 (funded account) | "several hundred" symbols | Too small |
| Tastytrade, TradeStation, Webull | $0 (funded) | Limits unpublished or small | Not designed for whole-market scanning |
| Massive (Polygon) Advanced | $199/mo | Yes (`AM.*`) | Only if Alpaca SIP falls short |

No free source streams real-time consolidated data for every symbol. The free design that comes closest:
**Alpaca IEX snapshots for the whole universe every minute → rank → act on the short list.**
Its blind spot is IEX volume, which the validation script measures.

## Recommended stack
| Need | Choice | Cost |
|---|---|---|
| Paper trading + execution (long & short) | **Alpaca** (paper now, live later; same code) | $0. Easy-to-borrow shorts have no borrow fee. Hard-to-borrow locates are live-only. PDT rule retired 6/4/2026. |
| Backtest history (1-minute, multi-year) | Alpaca SIP history (free once data is more than 15 minutes old) | $0 |
| Real-time data, 3,500 symbols | **Phase 1: Alpaca free IEX snapshots** (whole universe each minute). **Upgrade to Algo Trader Plus (SIP, $99)** if `validate_iex_proxy.py` shows IEX picks different stocks in play, or before live funds. | $0, then $99/mo |
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
