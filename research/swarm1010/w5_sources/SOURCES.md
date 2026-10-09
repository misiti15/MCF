# More trade data: source survey (swarm1010 W5, 2026-10-09)

*Educational only - not financial advice.*

Owner ask: "Can we pull more trade data from other sources?" Short answer: **yes - most of the value is already
paid for inside our Alpaca SIP plan and reachable from this container; the free public sources are all blocked by
this container's network policy but reachable from GitHub Actions**, where a staged workflow
(`actions/public-data.yml` + `actions/fetch_public.py`) can pull them to a `research-data` branch.

Every endpoint below was tested read-only (GET) on 2026-10-09; keys came from env and were never printed or written.
No setup was scored here (configurations tried: 0). Pulled data lives in `research/swarm1010/w5_sources/data/`
(parquet only, git-ignored by `research/**/*.parquet`; ~35 MB total).

## 1. Alpaca (our paid SIP plan) - what we use vs what we don't

| endpoint | status here | history | what it is | MCF use today | research it enables | effort |
|---|---|---|---|---|---|---|
| `/v2/stocks/bars` SIP | 200 | 2016+ (tested 2016-01-04 1-min) | OHLCV bars | **used** (all frames) | - | - |
| `/v2/stocks/quotes` SIP (NBBO) | 200 | 2016+ (tested) | every NBBO update: bid/ask, sizes, exchanges, conditions | **not used** | real spread/cost model by time of day and name (done: `spread_calibration.md`); spread/size features at entry; fill-quality audit of live fills | low (sampled pull, 1 multi-symbol request per sample time, ~1 s) |
| `/v2/stocks/trades` SIP (tape) | 200 | 2016+ | every print: price, size, exchange, conditions | **not used** | order-flow / signed volume (quote rule vs NBBO), block prints, odd-lot share, auction vs continuous volume | **high** for history: AAPL 2,200 prints/min at 10:00; HOOD 246k prints/day (25 pages, 23 s), SMTC 63k (7 s). ~1 s per 10k prints, so ~1 h/day for 130 names; 2-year history infeasible here. Feasible as a nightly per-minute aggregate for the traded/watch list going forward |
| `/v2/stocks/auctions` | 200 | 2016+ | opening/closing auction prices and sizes | not used | open-gap/auction-imbalance research for the open window | low |
| `/v2/stocks/snapshots` | 200 | live only | latest quote/trade/bars | used live | - | - |
| `/v1/corporate-actions` | 200 | ~2016+ (AAPL/NVDA/TSLA 2018-2026 returned splits, dividends, mergers; 2005-2015 empty) | splits, reverse splits, dividends, mergers, spin-offs, symbol changes | not used | clean adjustment audit for the 2-year frames; exclude split/merger days; dividend-ex-date gap fills | low |
| `/v1beta1/news` (Benzinga) | 200 | **2015+** (tested 2015-01-02) | headline, symbols, source, author, created/updated time (content optional) | used only as the earnings-blackout fallback | **DATA ONLY for now (owner: no news rules yet)**: news-day flags, historical earnings dates from headlines, catalyst tagging of live trades | done (see section 3) |
| `/v1beta1/screener/stocks/movers`, `most-actives` | 200 | **live only, no history** | top gainers/losers/most active | not used | a daily 16:05 snapshot would build its own history (in-play list research) | low (needs a scheduled job) |
| options: `/v2/options/contracts`, `/v1beta1/options/{bars,trades,snapshots}` feed=opra | 200 (opra and indicative) | **2024-01+** (2024 contract bars returned; 2023 empty) | contract list, OPRA bars/trades, snapshots (greeks not returned in our sample) | not used | put/call volume, unusual options volume per underlying, implied-move proxies; covers the 2-year history | medium (contract-level data; aggregate per underlying per day) |
| `/v2/calendar`, `/v2/assets` | 200 | full | sessions, early closes; shortable / easy_to_borrow / borrow_status | used | - | - |
| `/v2/account/activities/FILL`, `/v2/orders` | 200 | account life | our own fills/orders | used by EOD | fill-vs-NBBO audit (done, section 5 of spread_calibration.md) | low |
| crypto bars | 200 | - | - | n/a | n/a | - |
| `/v1beta1/logos` | **403** (plan does not include) | - | - | - | - | - |

Rate limits: no 429 seen at 4 concurrent requests; the paid plan's documented limit is far above what any of this needs.

## 2. Free / public sources

**Every one is blocked from this container**: the proxy answers `403` to CONNECT (policy denial), recorded
2026-10-09 for cdn.finra.org, api.finra.org, www.sec.gov, data.sec.gov, api.nasdaq.com, cdn.cboe.com, www.cboe.com,
fred.stlouisfed.org, api.stlouisfed.org, mba.tuck.dartmouth.edu, stooq.com, query1.finance.yahoo.com,
www.alphavantage.co, www.nasdaqtrader.com, ftp.nyse.com, api.gdeltproject.org, quiverquant, polygon, FMP, kaggle,
huggingface.co, s3.amazonaws.com. Reachable: data.alpaca.markets, paper-api.alpaca.markets, raw.githubusercontent.com,
api.github.com, pypi. The owner can allow hosts in the cloud environment's settings (Network access -> Allowed
domains), or - simpler and already the repo's pattern (`reddit-dumps.yml`) - fetch them on GitHub Actions, which has
open internet.

| source | what it is | history | how to get it | limits | MCF research it enables | effort |
|---|---|---|---|---|---|---|
| **CBOE VIX / VIX9D / VIX3M / VVIX** | daily index OHLC | VIX 1990+, VIX9D 2011+, VIX3M 2007+, VVIX 2006+ | `cdn.cboe.com/api/global/us_indices/daily_prices/<IX>_History.csv` (Actions); **VIX already pulled here** from the `datasets/finance-vix` GitHub mirror (1990-01-02..2026-09-22, ~2-week lag) | none | regime gate inputs (level, term slope VIX9D/VIX vs VIX3M); the regime1009 study used only universe-internal measures | **done** (VIX); low for the rest via Actions |
| **FINRA Reg SHO daily short volume** | per symbol per day: off-exchange (TRF) short volume, short-exempt, total volume. NOT short interest | ~2009+ daily files | `cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt`, pipe-delimited, ~1 file/day | none published; be polite | short-volume ratio as a crowding / squeeze feature for long setups and short-side filters | low via Actions (~510 files for 2 years, filtered to the universe -> ~30-50 MB parquet) |
| **FINRA short interest (bi-monthly)** | true short interest per symbol | 2018+ via API | `api.finra.org` (free key for some datasets) | API quota | days-to-cover feature | medium |
| **Nasdaq earnings calendar** | per day: symbol, time (pre/after), EPS forecast | years back (one request per date) | `api.nasdaq.com/api/calendar/earnings?date=` (already used live in `mcf/data/earnings.py`) | unofficial; throttle | **apply the live earnings blackout to the 2-year history** - the history scans do not apply it today, so live/history parity is off for every setup | low via Actions (~520 requests) |
| **SEC EDGAR** (submissions, Form 4, 8-K) | filings index; insider buys/sells (Form 4); quarterly insider data sets | 1994+ / 2003+ for Form 4 data sets | `data.sec.gov/submissions/CIK*.json`, `www.sec.gov/files/structureddata/data/insider-transactions-data-sets/*.zip` | 10 req/s, User-Agent with contact required | insider-buy days, 8-K event days as catalysts (data only) | medium |
| **FRED** | rates, credit spreads, dollar | decades | `fred.stlouisfed.org/graph/fredgraph.csv?id=...` (no key) | generous | macro regime context (2s10s, HY spread) - weak for intraday, cheap | low |
| **Fama-French factors / Ken French industry portfolios** | daily MKT, SMB, HML, RF, momentum; 12/48 industry returns | 1926+ | zipped CSVs from mba.tuck.dartmouth.edu | none | factor-neutral attribution of setup P/L (is a "setup" just momentum/industry beta?); industry regime | low |
| **Stooq / Yahoo daily** | daily OHLCV incl. indices (^VIX, ^SPX) | decades | CSV/JSON endpoints | unofficial, throttled | nothing Alpaca SIP daily bars don't already give, except index levels | not recommended |
| Nasdaq Trader symbol directory | listed symbols, ETF flag, test issues | current | `nasdaqtrader.com/dynamic/SymDir/*.txt` | none | universe hygiene (ETF/test-issue flags) | low, low value |

## 3. Pulled into git-ignored storage (this run)

| file (under `research/swarm1010/w5_sources/data/`) | rows | source | notes |
|---|---|---|---|
| `nbbo_sample.parquet` | 67,144 | Alpaca SIP quotes | 133 traded symbols x 5 sessions 2026-10-05..09, 126 sample times/session |
| `fill_quotes.parquet`, `orders.parquet` | 306 / 501 | Alpaca paper orders + SIP NBBO at submit and at fill | fill-quality audit |
| `vix_daily.parquet` | 9,194 | CBOE VIX via GitHub mirror | 1990-01-02..2026-09-22, **rule-19 locked block removed** |
| `vix_daily_lockedblock.parquet` | 84 | same | 2024-11-01..2025-02-28, for the lead's once-only holdout scoring |
| `news/news_YYYY-MM.parquet` | ~20-25k / month | Alpaca news | 2024-10 and 2025-03..2026-10 (locked block skipped), id, times, headline, symbols, source, author; zstd, ~1.5 MB/month. DATA ONLY |
| FINRA short volume | - | **not pulled: blocked here** | staged in `actions/fetch_public.py` (`--only finra`) |

## 4. Recommendations, ranked by value / effort

1. **Time-of-day cost model from NBBO** (value high, effort low). Open-window quoted spread is 2-4x the model in R;
   full-day is fine. Re-measure on 20+ sessions and the lab universe, then put a ToD multiplier in `prod_r` via the
   ledger. Backlog `sw-w5-cost-tod-multiplier`.
2. **Historical earnings calendar -> blackout parity on the 2-year history** (high, low). Run `public-data.yml`
   with `--only earn`; a fallback is the Alpaca news history pulled here (headline regex as in
   `mcf/data/earnings.py`, past side only). Backlog `sw-w5-earnings-history`.
3. **CBOE vol indices (VIX done; VIX9D/VIX3M/VVIX via Actions)** as pre-declared regime-gate inputs (medium-high,
   low). Backlog `sw-w5-vix-regime`.
4. **Fill-quality audit as a daily EOD report** (medium-high, low): NBBO at submit vs fill for every live fill, by
   order type and minute; catches the stop-fill tail (mean $0.12/sh past the stop vs $0.05 modelled). Housekeeping
   (reporting), but it informs costs. Backlog `sw-w5-fill-audit`.
5. **FINRA daily short volume** (medium, low via Actions). Backlog `sw-w5-finra-shvol`.
6. **Corporate actions** for a frame-adjustment audit and event-day exclusion (medium, low). Backlog `sw-w5-corp-actions`.
7. **Alpaca news history** - pulled, data only (medium later, done). Backlog `sw-w5-news-history`.
8. **Daily movers/most-actives snapshot** to build an in-play history (medium, low but needs a scheduled job and time
   to accumulate). Backlog `sw-w5-movers-snapshot`.
9. **OPRA options aggregates per underlying** (medium, medium; history only from 2024-01). Backlog `sw-w5-options-flow`.
10. **Tape-based order flow** (unknown, high): per-minute signed volume, nightly for the watch list only. Backlog
    `sw-w5-tape-orderflow`.
11. Fama-French / FRED / EDGAR Form 4 (low-medium, low-medium) - attribution and context, one entry
    `sw-w5-factor-macro-edgar`. Stooq/Yahoo: not recommended (duplicates Alpaca).

## What the live system would need

Nothing for the data pulled here (research-only). Recommendation 1 changes research cost accounting only (a
`prod_r` change through the ledger); recommendation 4 is an EOD report. Installing `public-data.yml` means copying it
from `actions/` into `.github/workflows/` (lead), then a manual `workflow_dispatch`; `fetch_public.py` is untested
end-to-end because its hosts are blocked here (parsers follow the published file formats; first run should be
checked).
