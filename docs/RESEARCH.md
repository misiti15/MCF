# Setup research summary (2026-10-05)

Sources: academic papers (SSRN, JFE), independent GitHub replications, and practitioner
statistics. Some paper figures came from abstracts and summaries because the PDFs were
unreachable from the build environment, so check the originals before hard-coding parameters.
Figures marked [unverified] could not be traced to a primary source.

## 1. Setups ranked by strength of evidence

| # | Setup | Evidence | Published stats | Caveats |
|---|---|---|---|---|
| 1 | **5-min ORB on stocks in play** (top-20 by first-5-min relative volume, ≥1; price >$5, ATR >$0.50; direction from the first candle; stop-entry at the range high/low; stop at 0.10×ATR; exit at end of day) | Zarattini, Barbon & Aziz 2024, SSRN 4729284 | 2016–23: Sharpe 2.81, about 41% IRR, net of commission only | **The relative-volume filter is the edge.** Without it ORB is weak. Needs SIP volume. Stop slippage is large relative to the tight R. |
| 2 | **ORB on QQQ only** | Zarattini & Aziz 2023, SSRN 4416622 | +1,484% gross | Independent replication: Sharpe 1.06 gross → **0.23 with 2¢ entry / 4¢ stop slippage**. Break-even is about 2.2¢/share. About 75% of trades stop out. |
| 3 | **Noise-band momentum, SPY** (band = 14-day average move from the open at each minute; checks on the half hour; trailing stop at band/VWAP; flat at the close) | Zarattini, Aziz & Barbon 2024, SSRN 4824172 | 2007–24: Sharpe 1.33, win rate 37–39%, payoff about 2:1 | One replication reports **Sharpe ≈ 0 since 2025**, so the edge may be decaying. |
| 4 | **Last-half-hour momentum** (previous close → 10:00 return sets the 15:30–16:00 position) | Gao et al., JFE 2018; Baltussen et al., JFE 2021 | Sharpe about 1.08; effect stronger on volatile and macro-news days | Only a few bps per trade. Depends on the dealer-gamma regime. |
| 5 | **VWAP trend on QQQ** (side of VWAP; flip on each cross) | Zarattini & Aziz 2023, SSRN 4631351 | Sharpe 2.1, **17% win rate** | Very high turnover, so costs dominate. IEX-only VWAP ≠ consolidated VWAP. |
| 6 | **Overnight→intraday reversal** (cross-sectional: long the worst overnight gaps, short the best, market-neutral, exit at the close) | Lou, Polk & Skouras, JFE 2019 | Intraday out-of-sample Sharpe 2–5× that of close-to-close reversal | Exclude earnings and news gaps. |
| 7 | Gap-and-go | vendor statistics only | about 52% win rate [unverified] | 65% of small-cap gap-ups close below the open. This is ORB-on-stocks-in-play in disguise. |
| 8 | VWAP-band fade / reclaim | blog statistics only | 57–63% win rate [unverified, likely invented] | Negative skew: trend days wipe out the gains. |
| 9 | Small SPY gap fill (0.1–0.5%) | practitioner statistics | 60–80% same-day fill rate | A high fill rate does not mean positive expectancy. |
| 10 | RSI(2), low-float shorts, bull flags, red-to-green | daily-bar or anecdotal evidence | — | Not intraday-proven. Low-float shorts can't be modelled on Alpaca paper (no borrow costs). |

## 2. Infrastructure realities
- **Data:** Alpaca's free real-time feed is IEX, about 4% of US volume. Relative volume, VWAP,
  and highs/lows from IEX are wrong for setups 1, 3 and 5. **Live scanning of 3,000+ symbols
  needs SIP (Algo Trader Plus, about $99/month).** For backtests, the free 15-minute-delayed SIP
  history is fine.
- **Paper fills are optimistic.** Alpaca paper fills at the NBBO with no market impact, no queue
  position and no borrow fees. Treat paper P/L as an upper bound.
- **The PDT rule was retired** on 4 June 2026 (FINRA Rule 4210 amendments). Alpaca now uses
  intraday margin with a $2k minimum.
- **Base rates:** in Taiwan, fewer than 1% of day traders are reliably profitable after fees
  (Barber et al.). In Brazil, 97% of persistent day traders lost money (Chague et al.).

## 3. About the 90% win-rate goal
- Every robust published intraday edge above wins **17–55%** of the time and makes its money on
  payoff ratio.
- With a stop S and a target T on a driftless price, P(win) ≈ S/(S+T). A 90% win rate therefore
  needs a stop about 9× the target. That gives roughly zero gross expectancy and negative
  expectancy after costs, unless real predictive skill is present.
- High win rates do appear in the data. They come from **negative skew**: tiny targets with wide
  or no stops, and occasional large losses.

**Proposal: track win rate, but gate decisions on these metrics:**
- expectancy ≥ +0.10R per trade **net of costs**, out of sample
- profit factor ≥ 1.3, and daily Sharpe ≥ 1.0
- green-day rate. This is where a high percentage (70%+) is achievable with a diversified book
  of uncorrelated setups, and it may be the better home for the "90%" ambition.
- win rate shown next to its **break-even win rate** (the dashboard does this)

A high-win-rate sleeve, such as small gap fills or VWAP reversion with a hard stop, can be
researched explicitly. It is judged by tail risk (worst day, worst trade in R), not by win rate.

## 4. Build priority
1. Noise-band SPY/QQQ momentum and last-half-hour momentum: liquid, cheap to trade, easy to verify.
2. ORB on stocks in play: highest published Sharpe. Needs SIP and the full-universe scanner.
3. Overnight→intraday cross-sectional reversal: market-neutral.
4. Experimental setups only after 1–3 are measured.

## 5. MarcoFlow setup families (added 2026-10-05)
MarcoFlow had no fixed setups. Its daily review mined the "best rule stack" from recent signals.
In 83 reviews it named **63 different best rules**, each backed by a **median of 29 trades**, so the
rules were mostly fitting noise. The recurring themes are still worth testing as explicit,
fixed-parameter MCF setups, judged by the same gates as everything else:

| Family | MarcoFlow evidence (signal level, not paper) | MCF version to test |
|---|---|---|
| Follow-the-drop short | 56.1% (n=8,857), avg return −0.04% | Short continuation after a large down move on rvol, ETB names only |
| Oversold open bounce (long) | recurring best rule; RSI < 25 in 9:30–11 ET, n≈30 each | Long reclaim of the opening low after a washout, stocks in play |
| VWAP loss / reclaim | recurring best rule 11–12 ET | Existing `vwap_reclaim`, plus a short-side VWAP loss mirror |
| Heat-strength ETF longs | best rule 6 times, n≈200 | Covered by noise-band and last-half-hour momentum on index ETFs |
| Signed-volume pressure | several midday rules, n≈20–30 | Feature for the setups above, not a standalone setup |

No setup is ruled out up front. Every candidate must pass the gates out of sample; nothing is
promoted on in-sample or signal-level results.

## Key sources
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284 (ORB, stocks in play)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622 (ORB, QQQ); replication https://github.com/giovannibrusco/zarattini-2023-orb-qqq
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172 (noise-band momentum, SPY)
- https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 (Gao et al. 2018)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365 (Baltussen et al. 2021)
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4631351 (VWAP trend)
- http://www.econ.yale.edu/~shiller/behfin/2015-04-11/lou_polk_skouras.pdf (overnight/intraday reversal)
- https://docs.alpaca.markets/us/docs/about-market-data-api (IEX vs SIP)
- https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/
- https://tradingstats.net/win-rate-profit-factor-expectancy/ (win-rate geometry)
