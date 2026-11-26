Educational only — not financial advice

# Crypto foundations: how the top coins work, crypto price action, and the first hand-built setups (2026-11-26)

Owner request 2026-11-26: a full research project, like the one behind the first equity setups, ending in setups to test.
This file is the **knowledge base**. It builds on `research/crypto_r1/MARKET_RESEARCH.md` (Alpaca fees, effects, failsafes), which it does not repeat.
It also builds on rounds 1-3 (`research/crypto_r{1,2,3}/REPORT.md`): **1,477 configs, 0 survivors after costs**.
- The only intraday lead is continuation after top-1% hours: +0.10R gross against a 0.13R cost.
- Every idea below is a **hypothesis**. It must be pre-registered and scored with costs in under docs/RESEARCH_RULES.md.

**Method and limits.**
- Sources are WebSearch extracts. WebFetch could not reach coinmarketcap.com or coincodex.com (not on the network allow-list), so figures come from search snippets.
- Market caps differ by ±10% between sources. **[verify]** marks a figure to check before code depends on it.
- Alpaca spreads are our own 2026 medians (`research/crypto_r1/spreads.json`), not the venue's quoted spreads.

## 0. Regime right now (it matters for a long-only book)
- **Price.** BTC made its all-time high of about $126.2k on 2025-10-06. It is about 50% below that now: roughly $62-65k in mid-November 2026, with November down as much as 23% and six red weeks in a row ([CryptoBriefing](https://cryptobriefing.com/bitcoin-falls-23-november-2026-bear-market/)).
- **ETF flows.** Spot BTC ETFs saw about $1.9B of outflows over Nov 5-13 ([Investing](https://ng.investing.com/analysis/bitcoin-drawdown-signals-a-liquidity-reset-as-etf-outflows-pressure-the-market-212264)). Total crypto market cap is about $2.6T, against $4.27T at the peak ([solcard](https://www.solcard.cc/blog/total-crypto-market-cap)).
- **Volatility.** BTC implied vol (Deribit DVOL) is 37-41, about **2.0-2.2% a day**. Realized 30-day vol in late Oct to early Nov was only 21-29% a year, about **1.1-1.5% a day**: low against 2021-25 ([CryptoBriefing DVOL](https://cryptobriefing.com/bitcoin-options-calmest-year-deribit-dvol/), [CryptoQuant](https://cryptoquant.com/insights/quicktake/6adfc8ff836e5235297410f4-Bitcoins-30-Day-Realized-Volatility-Is-Lower-Than-on-97-of-Days-Since-2021)).
- **Dominance.** BTC dominance is about 60% and the Altcoin Season Index was 39 in September 2026 (75 = alt season). Altcoins have lagged BTC for a 4th straight year ([BeInCrypto](https://beincrypto.com/altcoin-season-analysis-bitcoin-dominance/), [KuCoin](https://www.kucoin.com/news/flash/altcoins-underperform-bitcoin-for-fourth-consecutive-year)).
- **Implication.** A long-only book in a bear market with low realized vol is the worst case for continuation longs. The first setups should be (a) **reversal-from-flush** longs, which work in both regimes, and (b) continuation longs **gated by a daily uptrend**, which lie dormant now and switch on by rule.

## 1. The top 10 crypto currencies tradeable on Alpaca (USD pairs, stablecoins excluded)
**How the list was built.** It is market-cap order for Nov 20-26, 2026 ([cv.cm](https://cv.cm/en/rankings/crypto-market-cap/), [therighttrader](https://therighttrader.com/crypto/largest-cryptocurrencies-by-market-cap), [slickcharts](https://www.slickcharts.com/currency)), filtered to pairs with a live Alpaca print (`data/crypto/1Min/`, 30 USD pairs).
- **Left out because Alpaca does not list them:** BNB, TRX, ZEC, XMR, XLM, SUI. Stablecoins are left out by design.
- **The ten:** **BTC, ETH, XRP, SOL, HYPE, DOGE, LINK, ADA, BCH, LTC.**
- **Next five:** AVAX (#11, close to LTC), then DOT, UNI and AAVE. They are worth keeping because their Alpaca spreads are tight.
- **Short history:** HYPE and ADA listed on Alpaca in 2025-26, so they have little history (CHECK/LOCKED only).

**How to read the table.**
- "Vol x BTC" is a planning estimate of daily-range multiples against BTC (r1 vol levels; Kaiko puts DOGE at about 2.07x). The harness must measure it per pair.
- Correlations are the latest published figures: ETH 0.88 and SOL 0.83 on 90 days in Oct 2026 ([KuCoin](https://www.kucoin.com/news/flash/bitcoin-altcoin-correlation-hits-10-month-low-as-capital-rotates)). The rest are estimates.
- Correlation is unstable: the 14-day average alt-BTC correlation fell to 0.26 in May 2026. Correlations jump towards 1 in sell-offs.

| # | Coin (mcap ~Nov 2026) | What it is / how supply works | What moves it; recurring events | Vol x BTC | Corr BTC | Alpaca spread 2026 |
|---|---|---|---|---|---|---|
| 1 | **BTC** (~$1.25-1.39T) | **What:** proof-of-work, 21M cap. **Supply:** 3.125 BTC/block since the Apr-2024 halving, about 0.8%/yr; next halving about spring 2028 | **Drivers:** macro and liquidity, spot-ETF flows (IBIT etc.), corporate treasuries. **Events:** CPI and FOMC; Deribit expiry Fridays 08:00 UTC; ETF flows published after the US close | 1.0 | — | **12 bps** (venue: 0.1-1 bps) |
| 2 | **ETH** (~$207-214B, ~$1.7k) | **What:** proof-of-stake. **Supply:** issuance minus fee burn; net about +0.6-0.8%/yr in 2026, because burns cover about 2% of issuance after Fusaka (Dec 2025) cut fees ~90%. **Staking:** 34% staked, yield ~3%. EIP-8361 proposes tapered issuance ([CryptoSlate](https://cryptoslate.com/eth-fee-burns-cover-just-2-of-new-coins-printed-in-2026/), [The Block](https://theblock.co/news/ecosystems/2026-08-12-ethereum-staking-climbs-34-proposal-targets-validator-rewards-eth-treasury-firm-yields-411312)) | **Drivers:** BTC beta, ETH ETF flows, the ETH/BTC trend, upgrade dates. Glamsterdam was reported postponed (Nov 2026) **[verify]** | 1.3-1.5 | 0.88 | **13 bps** |
| 3 | **XRP** (~$60-65B) | **What:** XRP Ledger, federated consensus, no mining or staking. **Supply:** 100B pre-minted; Ripple escrow unlocks **1B on the 1st of each month** and re-locks 60-80% of it ([crypto.news](https://crypto.news/how-ripples-xrp-escrow-works-monthly-unlock-explained/)) | **Drivers:** regulation and Ripple news, US spot ETFs (since Nov 2025; $1.45B cumulative by July 2026, [CryptoSlate](https://cryptoslate.com/wall-street-just-poured-nearly-90-million-into-altcoins-as-xrp-sol-and-hype-rip-higher/)), CME XRP futures. **Events:** 1st-of-month unlock (headline risk only) | 1.5-1.8 | ~0.75 est | 51 bps |
| 4 | **SOL** (~$42-48B) | **What:** proof-of-stake plus proof-of-history. **Supply:** inflation 3.86%/yr (Aug 2026), falling 15%/yr; SIMD-0550 (vote Aug 2026) doubles the disinflation rate towards a 1.5% floor around 2029 ([The Block](https://theblock.co/news/ecosystems/2026-08-31-solana-fees-hit-record-as-validators-double-pace-of-inflation-cuts-413135)). **Staking:** yield about 5.4-5.8%. Alpenglow (150 ms finality) status unconfirmed | **Drivers:** on-chain activity (memecoins, DEX), spot ETFs ($1.14B inflows by July 2026), outage history | 1.6-1.9 | 0.83 | 52 bps |
| 5 | **HYPE** (~$15-18B) | **What:** the Hyperliquid L1, whose perps DEX is its own chain. **Buybacks:** the Assistance Fund buys back HYPE with about 97-99% of fees: $1.16-1.36B cumulative, slowing to about $190M/quarter in Q1-26. **Unlocks:** team vesting pays out **on the 6th of each month** (~9.9M HYPE), with unstaking 7 days before ([The Block](https://www.theblock.co/post/383880/hype-tokens-unstaked-for-hyperliquid-labs-first-allocation), [KuCoin](https://www.kucoin.com/news/articles/hyperliquid-hype-token-unlock-305-million-market-impact-analysis)) | **Drivers:** Hyperliquid perp volume (crypto leverage appetite), buyback pace, the 6th-of-month unlock, HYPE ETFs ($350M by July 2026) | 2.0-2.5 | ~0.7 est | 53 bps |
| 6 | **DOGE** (~$9B) | **What:** proof-of-work (Scrypt, merge-mined with LTC). **Supply:** **5B DOGE/yr fixed**, about 3.2-3.5% and falling; no unlocks ([KuCoin](https://www.kucoin.com/news/flash/dogecoin-s-3-49-annual-inflation-is-intentional-analysts-say)) | **Drivers:** retail risk appetite, social and Musk headlines; the highest beta to BTC rallies. ETFs are small | ~2.0 | ~0.75 est | 44 bps |
| 7 | **LINK** (~$6.6-7B) | **What:** the Chainlink oracle network token, 1B cap. **Unlocks:** about 7%/yr released from non-circulating wallets **roughly quarterly**, often sent to Binance (Apr 2026: ~19M) ([chain.link](https://chain.link/circulating-supply), [BeInCrypto](https://beincrypto.com/chainlink-token-unlock-binance-price-dip/)). **Staking:** v0.2 | **Drivers:** BTC/ETH beta, tokenisation and bank-partnership news, ETF flows ($13M/wk peaks). **Events:** unlock days (headline risk) | 1.7-2.0 | ~0.8 est | **25 bps** |
| 8 | **ADA** (~$5.5B) | **What:** Ouroboros proof-of-stake, 45B cap. **Supply:** each 5-day epoch releases about 0.3% of the remaining reserve (80% to stakers, 20% to the on-chain treasury) ([dev.to](https://dev.to/mrnasdog/ada-inflation-analysis-june-2026-a-capped-coin-that-still-drips-supply-1043)) | **Drivers:** BTC beta, governance and treasury votes, few hard catalysts. **History:** Alpaca since 2025-26 only | 1.7-2.0 | ~0.75 est | 45 bps |
| 9 | **BCH** (~$4-8B **[verify]**) | **What:** a proof-of-work SHA-256 fork of BTC with minority hashrate, 21M cap. **Supply:** next halving about Apr 2028 | **Drivers:** BTC beta and not much else; low news flow. Wide Alpaca spread | 1.4-1.7 | ~0.75 est | 90 bps |
| 10 | **LTC** (~$3.5-6B **[verify]**) | **What:** proof-of-work (Scrypt), 84M cap. **Supply:** next halving **about July 2027** (6.25→3.125, [Blockworks](https://blockworks.com/news/bitcoin-litecoin-halvings)) | **Drivers:** BTC beta, a halving narrative into 2027. Its ETF saw zero flows | 1.4-1.6 | ~0.8 est | 89 bps |
| + | AVAX | Proof-of-stake, 720M cap; about 1.67M Foundation unlocks per quarter in 2026 ([MEXC](https://www.mexc.com/price/AVAX/tokenomics)) | BTC beta; subnet news | 1.8-2.1 | ~0.75 | 90 bps |
| + | DOT / UNI / AAVE | DOT: nominated proof-of-stake. UNI and AAVE: DeFi governance tokens; AAVE runs buybacks | DeFi activity, fee-switch and governance votes | 1.7-2.0 | ~0.75 | **23 / 23 / 25 bps** |

**What the table says for MCF.**
- **Cheapest on Alpaca:** BTC and ETH (12-13 bps), then LINK, DOT, UNI, AAVE, CRV and SKY (23-25 bps).
- **Twice that:** SOL, XRP, HYPE, DOGE and ADA (44-53 bps).
- **Four times that:** BCH, LTC and AVAX (about 90 bps). Their spread alone almost doubles the round trip.
- **Data quality:** only 16-35% of 2026 minutes carry a real trade, even on BTC/ETH/SOL (r3). Signals must use traded-minute bars plus an external reference price.

## 2. Price action specific to crypto

### Sessions and liquidity
- **US hours dominate.** The 13:00-22:00 UTC window carries about **50% of BTC variance in 2022-25** (38% in 2016-18) and about **47% of spot volume**.
- **The US market is the cause.** On weekday US holidays, the US-hours share of variance drops 13.9 pp, which ties it to US market activity. The change-point is Nov 2021, before the ETFs ([CryptoSlate/Kraken study](https://cryptoslate.com/crypto-never-closes-but-bitcoin-ethereum-xrp-and-solana-now-move-on-wall-street-time/), [DailyCoin/Kaiko](https://dailycoin.com/bitcoin-us-etfs-shift-global-trading/)).
- **Anchor to ET, not UTC.** The US window moves with US daylight saving time.
- **Asia still has the biggest weeks.** Asia hours own 51 of the 85 weeks with a ≥10% move since 2021, though the US share of those weeks' variance rose from 24% to 33% after the ETFs ([ParaFi](https://parafi.com/signals/bitcoin-biggest-moves-market-hours)).
- **The sign of session returns flips between studies** (2019-21 "US up, Asia down" vs Velo "Asia best"), so use sessions as filters, not as signals.
- **Weekends are thin.** Weekday volume is about **2x weekend volume**, and the gap widened in 2025-26. Weekend spreads widen most on US venues (Coinbase). Depth within 1% of mid is about $30M on Binance and $16-20M on Coinbase ([CryptoSlate/Kaiko](https://cryptoslate.com/how-institutions-made-bitcoin-a-weekday-market-so-retail-takes-on-all-the-weekend-risk/)).
- **Weekend moves are wick-prone and often partly reversed when weekday liquidity returns.** There is no clean Monday-return study after 2021.

### The CME gap
- **It is mostly obsolete.** CME crypto futures and options have traded **24/7 since 2026-05-29** ([CME](https://www.cmegroup.com/media-room/press-releases/2026/6/01/cme_group_announceslaunchof247cryptocurrencyfuturesandoptionstra.html), [The Block](https://www.theblock.co/post/403304/cme-groups-crypto-derivatives-50-million)).
- **What is left:** a weekly maintenance halt around Sat 02:00-03:45 CT, and weekend CME volume is tiny (about $50M on the first weekend).
- **Old stats are pre-2026 folklore:** "95% fill", and a median time to fill of 36 h in 2024 and 19 h in 2025 ([NewsBTC](https://www.newsbtc.com/news/bitcoin-cme-futures-gaps-are-filled-with-95-certainty-but-trading-them-is-risky/), [CryptoSlate](https://cryptoslate.com/?p=476499)).
- **What replaces it:** the Friday US-close level (16:00 ET) as a weekend magnet.

### Leverage effects (none visible in Alpaca data)
- **Wick hunts and liquidation cascades.** Perp leverage turns drops into forced selling.
  - 10-10-2025: $19B liquidated, BTC −14%, alts printed near zero, USDe at $0.65 on Binance.
  - Prices rebounded strongly within 48 h, and liquidity came back the same day (r1 sources, [Notebookcheck](https://www.notebookcheck.net/Crypto-bounces-after-19-billion-wipe-Data-shows-a-faster-recovery-than-ever.1137690.0.html)).
- **No metric warns of every cascade** (7-event Binance study, [CryptoSlate](https://cryptoslate.com/new-bitcoin-study-shows-the-strongest-recurring-liquidation-warning-signs-cannot-warn-of-an-individual-crash/)).
- **The slow horizon is bearish.** After the top-5% liquidation days, BTC's 30-day return averages 0.78% against a typical 5.9% (K33 via [The Block](https://www.theblock.co/post/372115/whats-next-after-cryptos-fourth-largest-long-liquidation-event-of-2025)). So a flush bounce is a **hours trade, not a swing**.
- **Funding resets** happen every 8 h at 00/08/16 UTC on most venues.
  - The academic footprint is a vol and volume periodicity around settlement ([arXiv 2109.12142](https://arxiv.org/abs/2109.12142)). **No study found a tradeable price pattern at the reset itself.**
  - Deeply negative funding coincided with local lows in Aug 2024 and Apr 2025 ([Glassnode via CMC](https://coinmarketcap.com/academy/article/bitcoin-funding-rates-hit-lowest-since-2023-as-price-climbs-glassnode-reports)). That is an extreme-value filter, not a clock trade.

### Levels and options
- **Round numbers.** Prices cluster at round numbers (more than 10% of BTC prices end in 00), but **there is no return pattern after touching them** (Urquhart 2017). Use them for stop and target placement and as sweep levels only.
- **Options expiry.** Deribit settles at **08:00 UTC on Fridays**; monthly and quarterly expiries fall on the last Friday.
  - *Finance Research Letters*, 1,059 expiries 2021-23: BTC tends to **fall in the hour before expiry and reverse over the next 2 h**, but only when at-the-money open interest is in the top decile. An independent check of the 08:00 UTC window did not confirm the rebound ([CryptoSlate](https://cryptoslate.com/?p=561776)).
  - "Max pain": settlement was within 2% of max pain on 34 of 46 expiries, but the last 4 missed by 6-9% ([CryptoQuant](https://cryptoquant.com/insights/quicktake/6afbb1c6cd57dd300eaac44e-Max-Pain-Held-on-34-of-46-Bitcoin-Expiries-the-Last-Four-Missed-by-6-to-9)). Large expiries are usually a "nothing burger".

### Stablecoins, dominance and macro
- **Stablecoin depegs.** USDC and USDT held. USDe hit $0.65 on Binance (Oct 2025) and $0.92 (Sep 2026), and Resolv's USR collapsed (Mar 2026). A synthetic-dollar unwind is a transmission channel into crypto prices ([NY Fed](https://libertystreeteconomics.newyorkfed.org/2026/06/synthetic-stablecoins-and-financial-stability/)). MCF trades USD pairs, so the guard in r1 §4.6 is enough.
- **BTC dominance and alt season.** Alts outperform only when dominance falls and ETH/BTC rises. In 2026 there have only been short rotations (ETH/BTC peaked near 0.033 in Aug-Sep 2026; dominance is back above 60%). Rotation is a **slow daily filter** (choose ETH/alts vs BTC), not an intraday trigger.
- **The US stock market and macro.**
  - BTC's 30-day correlation with the Nasdaq-100 swung from 0.96 (Apr 2026) to about 0 (Jun 2026). It reasserts itself in risk-off moves ([Crypto.com](https://crypto.com/us/market-updates/bitcoin-and-nasdaq-100-break-correlation-what-happens-next)).
  - **CPI is the one release that matters** (NY Fed SR 1052; NFP sensitivity has faded). In 2026 the CPI surprise explains ~80% of the 1-hour BTC move after the release (R²), though the move per unit of surprise is smaller ([Blockscholes](https://www.blockscholes.com/institutional-research/is-bitcoin-showing-greater-sensitivity-to-us-cpi-releases-again)).
  - FOMC (14:00 ET) brings volatility, but its direction is anecdotal.
  - Spot ETF flows are published after the US close and react to prices as much as they lead them. There is no rigorous intraday causal study; Volmex (2024) links IBIT flows to intraday volume.

## 3. Metrics traders use: what Alpaca spot bars can and cannot give us
| Metric | What it tells you | From Alpaca spot bars? |
|---|---|---|
| Realized vol (close-to-close or Parkinson, 1h/1d) | regime, sizing, stop width | **Yes**, on traded-minute bars only. Bad prints inflate it, so use a trailing filter |
| ATR% (1h, 4h, 1d) | stop distance; is a move big against costs? | **Yes** (same caveat) |
| VWAP / anchored VWAP, volume profile | fair price of the session; reclaim levels | **Partly.** Alpaca volume is a tiny, noisy slice of the market. Use it for levels, not for volume z-scores. A Coinbase public-candle volume feed would be better |
| Volume z-score (volz) | climax and flush detection | **Weak.** 65-85% of minutes have no print. Use external venue volume if possible |
| Open interest, funding, liquidations, basis | leverage and crowding | **No.** Needs Binance/Bybit/OKX public REST or Coinglass, logged as an optional `ext` feature |
| BTC dominance | rotation regime | **Approximation only:** BTC vs equal-weight alt basket returns. True dominance needs total market cap (CoinGecko) |
| ETH/BTC ratio | alt-risk appetite | **Yes** (ETH/USD ÷ BTC/USD; Alpaca also lists ETH/BTC) |
| Exchange flows (on-chain in/out) | supply hitting venues | **No.** Needs on-chain data (CryptoQuant/Glassnode). Daily speed, no intraday evidence |
| Implied vol (DVOL), options open interest, max pain | expected range, expiry pinning | **No.** Deribit public API |
| ETF flows | institutional demand | **No.** Farside/SoSoValue, daily after the close |
| Spread and depth | cost per trade | **Yes.** `latest/orderbooks`; log it per hour of the week |

## 4. Online leads: practitioner playbooks and academic evidence (last 2 years preferred)
| Playbook | Typical rule | Evidence | Status for MCF |
|---|---|---|---|
| Intraday time-series momentum | first-session return predicts the last session | Shen/Urquhart/Wang 2022 (in and out of sample, stronger on high-volume days); no cost-aware replication found | r2 TSMOM seed −0.30R. **Faded at Alpaca cost** |
| 12h session reversal | after a big 12h move, fade it in the next 12h (BTC); ETH: overnight drift plus daytime reversal | [JRFM 2025](https://www.mdpi.com/1911-8074/19/9/692), Kraken 2016-25, many-rule search | **Untested at MCF.** Few trades, cost-friendly |
| Asia-range breakout (London/US) | break of the 00-07 UTC range | London breaks the Asia range on 48-52% of days and continues on ~54% ([MQL5, 2018-26](https://www.mql5.com/en/blogs/post/778873)). That is about a coin flip | r2 seed −0.24R. **Faded** |
| US-open drive / ORB | 09:30-10:00 ET range break | US-hours variance share is up (above); no net-of-cost study | r2 ORB seed −0.21R. **Faded** |
| CME-gap fill | trade toward the Friday CME close | folklore (95% unsourced); CME runs 24/7 since 2026-05-29 | **Dead.** Replace with a Friday-close magnet |
| Weekend fade / Monday reclaim | fade thin weekend moves | liquidity collapse is documented; return effect not shown since 2021 | untested; plausible only as reclaim-from-a-wick |
| Post-liquidation reclaim | buy the wick after a cascade | mechanism documented, fast liquidity recovery; no hourly study; 30-day horizon weak | r2 flush −0.17R on 41-106 trades (thresholds too small, dirty bars) → **re-test with clean bars and bigger flushes** |
| Funding-reset reversal | fade crowded side after the 00/08/16 reset | none rigorous; negative-funding extremes near lows are anecdotal | needs `ext` funding feed |
| ETF-hours momentum | buy strength while ETFs trade | volume shift is real; no flow-to-price intraday causality | low priority |
| Expiry pin/reversal | dip into 08:00 UTC Friday expiry, buy the reversal | FRL 2021-23 (conditional on high ATM OI); not confirmed after | small moves (<1%) → **cost-dead** unless filtered |
| Big-hour continuation | top-1% hour, ride 24 h | **MCF r3:** +0.10R gross, beats 96-100% of random hours; net −0.03R | **best MCF lead.** Needs a maker exit and a trend gate |
| Round-number sweep | sweep below 00-level, reclaim | Urquhart 2017: clustering, but no return effect | r1 "above round" near-misses all lost |
| CPI reaction | trade the 1h post-CPI direction | Blockscholes 2026: 1h R² ~80% on the surprise | 12 events/yr; ok as an event setup |

**Signal sellers, courses and screenshot "backtests" were skipped.** No public net-of-fee intraday crypto playbook with out-of-sample results turned up. The consistent message from practitioners and academics is the one MCF's own rounds found: **intraday crypto edges are small against retail fees**. What survives is (a) volatility-timing and (b) rare, large dislocations.

## 5. Implications for MCF: candidate first setups

### Design rules from costs (r1 §3 and r2/r3)
- **Cost per round trip** is 0.30-0.40% for BTC/ETH (maker in, taker out) and 0.45-0.55% for LINK/DOT/UNI/AAVE.
- **Keep cost ≤ 0.15R** → stop ≥ **2.5-3% BTC/ETH, ≥ 3.5% cheap alts**. Gross targets ≥ 4-6%, so holds run **4-24 h**.
- **Maker entries by default.** Use a **resting maker target** where a target exists (it saves 10 bps against a taker exit). Exits on stop are taker, with a collar.
- **Pairs:** BTC, ETH, LINK, AAVE, UNI and DOT by default. SOL, XRP, DOGE and HYPE only in flush setups where the move is ≥ 2x the cost.
- **Never trade** BCH, LTC or AVAX until their spreads come in.
- **Size:** weekends at half size. No new entries 5 min before to 15 min after CPI/FOMC except in event setups.
- **Data:** signals come from clean traded bars, ideally Coinbase public candles, with fills on Alpaca (r2/r3).

### Notation
- ATR1h = ATR(14) of 1h bars.
- σ_h(n) = standard deviation of n-hour returns over the trailing 90 days.
- "Trend gate" = BTC daily close > SMA50 (r3 rules 980/983).
- "Friday close" = BTC price at Fri 16:00 ET (21:00 UTC in winter, 20:00 UTC in summer).

### What would change the ranking
- Owner scope on swing holds over 24 h.
- A tier-2/3 fee level.
- Adding the Coinbase/Binance public data feeds (they unlock rows 10-11).
- The parallel agent's measurement of our own data.

### Ranked candidate setups
All are long only. **ext** = needs non-Alpaca public data.

| Rank | Setup | Mechanism (why it should exist) | Entry trigger (exact) | Window (UTC) | Stop / target | Hold | Coins | What kills it |
|---|---|---|---|---|---|---|---|---|
| 1 | **Flush-reclaim v2** | Liquidation cascades overshoot. Liquidity returns within hours, so price mean-reverts part of the forced move | Drop over ≤ 4 h of ≥ 5% BTC/ETH (≥ 8% alts) **and** ≥ 3σ_h(4). Then a 15-min close back above flush low + 35% of the drop range. Maker bid at that level −0.1%, live 60 min | 24/7; weekend ½ size | stop: flush low −0.5 ATR1h (≥ 2.5%); T1 50% retrace (maker, ½ size); trail rest at 2 ATR1h | 4-12 h, tstop 12 h | BTC ETH SOL LINK AAVE (DOGE/HYPE at ½) | cascade continues in a bear grind; bad prints fake the wick (needs a clean reference); a depeg |
| 2 | **Big-hour continuation + trend gate** | Volatility clusters. Information shocks continue for hours (r3 +0.10R gross); a daily uptrend raises the odds | A 1h up move ≥ 99th percentile of trailing-30-day \|1h ret\| **and** the trend gate passes. Maker bid at close −0.25 ATR1h, live 60 min | 24/7 (US hours preferred) | stop max(3 ATR1h, 3%); resting maker target +2R | ≤ 24 h | BTC ETH SOL LINK | bear regime (gate off now); maker misses the runaway hours (r3: 34-68% fills) |
| 3 | **12h session reversal (BTC)** | Overreaction across the Asia/EU and US 12h blocks (JRFM 2025). Only 2 decisions a day, so cheap | At 08:00 and 20:00 UTC: prior-12h return ≤ −2σ_h(12) → maker bid at mid −0.05%, live 30 min | 08:00 / 20:00 UTC | disaster stop max(3 ATR4h, 4%); exit at the next session boundary | 12 h | BTC (ETH: overnight leg 20→08 only if trend gate) | data-snooped original; regime breaks; a fall-through on news days |
| 4 | **US-open drive (TSMOM v2)** | US cash open = ETF and institutional flow. A strong Asia/EU session plus a firm open tends to continue (Shen 2022) | 00:00 UTC→09:30 ET return ≥ +1.5σ_h(session) **and** the 09:30-10:00 ET bar closes in the top 30% of its range and above 00:00-UTC VWAP. Maker bid at the 09:30-10:00 VWAP | entries 10:00-11:00 ET | stop max(09:30-10:00 low, 2.5%); maker target +2R | to 16:00 ET (≤ 6 h) | BTC ETH | US holidays (variance share −14 pp; skip them); FOMC days; small trigger moves |
| 5 | **Weekend-wick Monday reclaim** | Thin weekend books overshoot. When weekday institutional liquidity returns (2x volume), price re-prices to the Friday consensus | Sat-Sun low ≤ Friday close −4% (BTC) / −6% (alts); then a 1h close above the Friday close between Sun 22:00 and Mon 15:00 UTC. Maker bid at the Friday close | Sun 22:00-Mon 15:00 | stop weekend low −0.3% (≥ 3%); target the weekend high or Fri high (maker) | ≤ 24 h | BTC ETH LINK | real weekend news (tariffs, hacks); only about 10-20 events/yr |
| 6 | **CPI up-drift** | CPI is the only macro print that moves BTC; the 1h reaction tracks the surprise (R² ~80%) | CPI day, 08:45 ET: BTC ≥ +1.2% vs 08:29 **and** above the 08:30-08:45 VWAP. Maker bid at that VWAP, live 30 min | CPI days 08:45-10:00 ET | stop at the 08:29 price (≥ 2%); target +2R maker | to 16:00 ET | BTC ETH | 12 events/yr (low n); reversal at the 09:30 ET equity open |
| 7 | **Day-2 capitulation bounce** | After a ≥ 8% UTC-day drop, forced sellers are gone and the next Asia session finds a base | Day D UTC return ≤ −8% (BTC) / −12% (alts). On D+1, the price trades below D's low and then a 1h close above D's low. Maker bid at D's low | D+1 00:00-16:00 | stop D+1 low −0.5 ATR1h (≥ 3%); target 50% of D's range | ≤ 24 h | BTC ETH SOL | the 30-day forward return after big liquidation days is weak (K33). Must exit same day; few events |
| 8 | **Funding-extreme reclaim (ext)** | Crowded shorts (very negative funding) plus a spot reclaim = squeeze fuel | Binance BTC/ETH perp funding ≤ −0.01%/8h (≤ 5th percentile, 180 days); after the next 00/08/16 UTC settlement, a 1h close above 24h VWAP | after settlements | stop max(2.5 ATR1h, 3%); trail 2 ATR1h | ≤ 24 h | BTC ETH SOL | needs a reliable ext feed; funding venue regime changes |
| 9 | **Asia-compression breakout v2** | Low-range Asia sessions store volatility; EU/US release it (vol clusters by session) | 00:00-07:00 UTC range < 0.5x its 20-day median **and** the trend gate; after 07:00, a 1h close above the Asia high. Maker bid at the Asia high on retest | 07:00-17:00 | stop max(Asia low, 3%); target 3x Asia range | ≤ 12 h | BTC ETH | breakout odds ≈ 54% (coin flip); a tight stop makes cost too large |
| 10 | **Liquidation-print long (ext)** | True version of #1: real forced-sell volume, not a proxy | Binance/Bybit long liquidations in 15 min ≥ 99th percentile (90 days), then the #1 reclaim rule | 24/7 | as #1 | as #1 | BTC ETH SOL | ext feed latency; rare events |
| 11 | **Alt catch-up, slow (ext optional)** | Alts follow BTC impulses with a lag that is long only for small caps; the cheap-spread DeFi alts lag the most | BTC +3% in 2 h **and** the trend gate; buy the alt in {LINK, AAVE, UNI, DOT} whose β-adjusted 2h return lags BTC by ≥ 2%. Maker bid | US hours | stop max(1.5 ATR1h, 3.5%); exit when the gap closes or at 8 h | ≤ 8 h | LINK AAVE UNI DOT | the lag is seconds to minutes (dead); r1 #228 lost |
| 12 | **Expiry-hour dip buy** | Dealer hedging unwinds into expiry; a post-expiry rebound (FRL 2021-23) | Monthly/quarterly last Friday: BTC 07:00→07:55 UTC ≤ −1.5%. Maker bid at 08:00 | Fri 07:55-08:05 | stop 2.5%; target the 07:00 price | ≤ 4 h | BTC ETH | not confirmed after 2023; only 12 events/yr; a move under 2x cost |
| 13 | **Friday-close magnet (CME-gap heir)** | Price returns to the last liquid consensus level | Mon 00:00-14:00 UTC: price ≥ 3% below the Friday close with the trend gate; 1h close back above Mon 00:00 open. Maker bid | Mon | stop ≥ 3%; target the Friday close | ≤ 24 h | BTC | CME 24/7 removed the gap mechanism; overlaps #5 |
| 14 | **Round-level sweep reclaim** | Stops cluster below round levels; a sweep then reclaim marks exhaustion | BTC trades ≥ 0.6% below a $5,000 multiple (ETH: $100), then a 15-min close back above it, with the trend gate. Maker bid at the level | 24/7 | stop sweep low −0.3% (≥ 2.5%); target 2R | ≤ 12 h | BTC ETH | no return effect in the literature (Urquhart); r1 round-number rules lost |
| 15 | **Regime gates (filters on all setups)** | Avoid dead and chaotic regimes | 1d realized vol percentile 30-90 (1-year); BTC trend gate for continuation setups; weekend ½ size; skip HYPE 5th-7th and XRP the 1st; skip US holidays for #4 | — | — | — | all | over-filtering starves trades (owner: playing time) |

**Common to every setup:** one open trade per pair, the r1 §4 failsafes, the one-big-day check, and N counted from 1,477.

**Expected frequency at these thresholds** (rough):
- #1 about 1-3 per month per pair in normal vol;
- #2 about 4-7 per month per pair when the gate is on;
- #3 about 3-6 per month;
- #4 about 2-4 per month;
- #5-7 about 1-2 per month each.

**The honest outlook:** the five ideas behind #1, #4 and #9 already lost in r2 at smaller thresholds on dirty bars.
- What is new here: bigger triggers, wider stops, maker targets, clean bars and the cheap-spread pair set.
- **#1-#3 have the strongest mechanism-plus-evidence case** and should be pre-registered first. #2 is the only one with a measured gross edge on MCF data.
- Report every config tried and score FIT → CHECK once → LOCKED once (rising bar).

Educational only — not financial advice
