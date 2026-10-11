# OF-A: does order flow (tape, footprint, aggression, NBBO queues) read turns better than bars? (owner 2026-10-11, Step A)

*Educational only - not financial advice. Lab study on historical SIP trades and NBBO quotes. Nothing here is a
live or paper result.*

Owner question (2026-10-11): would order flow - the tape, volumetric/footprint bars, buy vs sell aggression, orders
resting at levels (DOM / Level 2) - give a better real-time read of where and how sharply price will move? Step A
only: test with data we already have (Alpaca SIP trades + NBBO quotes, no paid depth feed). Target moves >= 0.5%,
entries at/after 09:50 ET.

**Section 1 (pre-declaration) was written on 2026-10-11 before any feature, IC or trade of this study was computed.**
Seen beforehand: research/bdi/turns1009/CASES.md and scale/NOTES.md (published numbers only), and one test
aggregation of ROKU 2026-10-08 used to debug the downloader (descriptive columns only, no outcome computed).
Section 1 may change only by dated amendments in 1.9.

## 1. Pre-declaration

### 1.1 Data and sample
- Read-only Alpaca market data REST (`/v2/stocks/{sym}/trades`, `/quotes`, feed `sip`), regular session
  09:30:00-15:59:59 ET. `fetch_agg.py` downloads each symbol-day in 30-minute windows and aggregates on the fly;
  raw pages are never written. Kept: 1-second records (`data/sec/{sym}/{date}.parquet`), 1-minute footprint summaries
  (`data/min/...`), and the full per-price footprint for the case day only (`data/footprint/`). 5-second records are
  sums of the 1-second records. Daily and 1-minute SIP bars (Alpaca bars endpoint, 2026-08-01..10-09) for daily ATR
  and the bar-level signatures.
- **Symbols (pre-declared, 40):**
  ETFs SPY QQQ IWM XLF XLE SMH; mega caps AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO JPM LLY; large caps across sectors
  CAT UNH XOM COST BA WMT HD GS NFLX ORCL; mid caps DKNG AFRM ROKU CCL RBLX DAL; high beta SPCX AMD PLTR COIN MSTR
  SMCI HOOD MARA. All are in `research/lab_symbols.txt`. (Selected for liquidity/diversity from today's list:
  survivorship and selection caveat applies.)
- **Sessions:** 2026-09-11..2026-10-09 (21). 09-11 is warmup only (thresholds, prior-day p99 print size); the 20
  scored sessions are 09-14..10-09. Halves: **H1** = 09-14..09-25 (10 sessions, discovery), **H2** = 09-28..10-09
  (10 sessions, confirmation). Caveat: the window overlaps the older holdout Sep 16 - Oct 5 2026, which rule 19
  already marks as no longer clean; the 2-year locked block is not touched (no tick data is fetched for it). This is
  an exploration: a pass here can at most justify a Step-B data spend, never a live change.
- Case study: the owner's five moments M1-M5 (`research/bdi/turns1009/moments.csv`: AAPL 13:49 long, AAPL 15:14 short,
  SPCX 10:13 short, CAT 10:11 long, TSLA 10:51 short) and SPY, 2026-10-09, against each stock's 20 prior sessions.
- Trade filter, signing, large prints, sweeps, OFI: exactly as documented in the `fetch_agg.py` docstring
  (conditions excluded: 1 4 5 6 7 8 9 A B C D G H K L M N O P Q R S T U V W X Z; odd lots kept and flagged; Lee-Ready
  with the prevailing NBBO, no lag; tick rule at the mid; quote rule strict for "through-touch" volume; large =
  >= prior-session p99 size; sweep = same millisecond, >= 2 venues, all at/through one side of the NBBO; CKS OFI).

### 1.2 Features (all known at the end of second t; positive = bullish reading)
Quote state is forward-filled; mid_t = (bid + ask) / 2 at the end of second t. "V_k" = the symbol's mean volume per
k-second window over its prior sessions in the sample (expanding, warmup 09-11 included); "D" = the symbol's prior
sessions' mean NBBO depth (bid size + ask size) / 2; sigma_k = prior sessions' std of k-second mid log-returns.

| id | feature | definition |
|---|---|---|
| F1-F4 | dlt10, dlt30, dlt60, dlt300 | signed (Lee-Ready) volume over the last k s / V_k (CVD change over k) |
| F5 | imb60 | (buy - sell) / (buy + sell) over 60 s |
| F6 | cvd_div300 | dlt300 / sd(dlt300) - ret300 / sigma_300 (flow more bullish than price = bullish divergence) |
| F7, F8 | ofi10, ofi60 | sum of CKS OFI over k s / D |
| F9 | qimb10 | time-weighted queue imbalance (bid size - ask size) / (bid size + ask size), mean of last 10 s |
| F10 | big60 | (large buy - large sell) volume over 60 s / V_60 |
| F11 | sweep30 | (buy sweeps - sell sweeps) volume over 30 s / V_30 |
| F12 | iso30 | (ISO-flagged buy - sell) volume over 30 s / V_30 |
| F13 | burst10 | trade count over 10 s / prior mean count per 10 s, times sign(ret10) (intensity burst in the move's direction) |
| F14 | absorb60 | -sign(dlt60) x vol60 / V_60 when abs(ret60) < 0.5 sigma_60 and abs(imb60) >= 0.2, else 0 (aggression that did not move price; positive = sellers absorbed) |
| F15 | lit60 | lit-exchange-only signed volume over 60 s / V_60 |
| F16 | fp_stack | stacked diagonal buy imbalances - stacked sell imbalances in the last completed 1-minute footprint bar |
| F17 | fp_low_d | footprint delta at the lowest two traded levels of the last completed minute / its volume |
| F18 | fp_high_d | same at the two highest levels |
| F19 | spread_z | time-weighted spread / prior-session median spread (unsigned; used for |IC| and as a cost diagnostic) |
| F20 | flicker10 | quote updates over 10 s / prior mean (unsigned) |
| P1-P3 | r10, r60, r300 | mid log-return over k s (price-only controls, "bar-only" information) |

### 1.3 Predictive tests (a)
- Sample every 5th second, 09:50:00..15:44:55, symbol-days with valid quotes. Forward mid log-returns at h = 10 s,
  60 s, 300 s, 900 s.
- **IC:** Spearman correlation within each symbol-day; averaged over symbols per session; t across the 20 sessions
  (day-clustered). Reported for F1-F20 and P1-P3.
- **Incremental IC:** the same after residualizing both the feature and the forward return on (r10, r60, r300) within
  each symbol-day (does flow add anything beyond recent price?).
- **Swing-start lift:** L_t = mid reaches +0.5% before -0.25% within 30 min (S_t the mirror). For each signed
  feature, P(L | feature >= its prior-session p90) / P(L) and P(S | feature <= p10) / P(S); session-clustered t of the
  difference in hit rates.
- Count: (20 + 20) features x 4 horizons (raw + incremental IC) = 160, + 18 signed features x 2 sides lift = 36 ->
  **196** (P1-P3 are controls, reported, not counted as tries).

### 1.4 Tradeable tests (b)
- **Clock:** decision at the end of each second t, entries 09:50:00..15:30:00 ET; one open position per symbol; after
  an exit, a 60 s cooldown. Thresholds are percentiles of the feature over the symbol's prior sessions (expanding,
  09-11 warmup gives the first day's reference).
- **Execution (primary):** entry 2 s after the decision at the quote then prevailing, crossing the spread (buy at the
  ask, sell short at the bid) + 1 bps. Target: a resting limit at entry x (1 +- 0.5%), filled when the far-side quote
  trades through it (bid >= target for a long), filled at the target, no cost. Stop: when the near-side quote reaches
  the stop at a second's end, exit 1 s later at that side of the quote + 1 bps + 2c. Time exit: 1 s later crossing the
  spread + 1 bps. Positions still open at 15:59:30 exit there. P/L in bps of the entry price.
- **Secondary cost check:** mid-to-mid fills with the production model (1c + 1 bps per side, x `gates.tod_cost_mult`
  on entry, exit free on target, +2c on stops).
- **Signals (10):** dlt60, dlt300, ofi60, qimb10, big60, sweep30, burst10, absorb60, cvd_div300, fp_stack.
  Modes: follow (long when the feature >= q, short when <= 1 - q) and fade (the reverse). q in {p99, p99.9}.
- **Exits (4):** E1 +0.5% / -0.25% / 30 min max; E2 +0.5% / -0.5% / 30 min; E3 time 5 min; E4 time 15 min.
- **Lines:** each signal x mode x q x exit, raw and SPY-hedged (hedged = minus beta x SPY mid return over the holding
  period, beta = prior sessions' 1-minute beta, minus SPY spread/2 + 1 bps per side x beta) = 10 x 2 x 2 x 4 x 2 = 320.
- **Bar-only / price baseline (same entries without flow):** the same rules on r60 and r300 instead of the flow
  feature = 2 x 2 x 2 x 4 x 2 = 64. **Random baseline:** random seconds, same side mix, same window, same count per
  symbol-day as the line it is compared with (reported, 8 lines: 2 sides x 4 exits, not tries).
- **Confirmation on bar setups:** C3b (5-min VWAP-z and RSI14 both at the stock's prior-20-session p10/p90 plus a
  1-minute trigger) and C6 (1-minute roc10/ATR at p10/p90 plus trigger), exactly as `turns1009/signatures.py`
  (MACD-hist cross within 3 bars, engulfing, hammer/star), 1-minute SIP bars, thresholds on the stock's 20 prior
  sessions. Entry decision at the 1-minute bar close. Bare (2 setups x 4 exits) and with flow confirmation required
  within 60 s of the bar close (entry at the first confirming second): dlt60 >= p80 in the trade's direction, ofi60
  >= p80, sweep30 >= p90, absorb60 >= p90 (sellers absorbed for a long), qimb10 >= p80 -> 2 x (1 + 5) x 4 x 2 (hedged)
  = 96.
- **N (trade lines) = 320 + 64 + 96 = 480**; with the 196 predictive tests the lineage count is **N = 676 -> t bar =
  max(1.5, sqrt(2 ln 676)) = 3.61.**
- **Gates (pre-declared; a "flow edge" claim needs all):** exp > 0 after primary costs; day-clustered t >= 3.61;
  n >= 150; exp > 0 in up AND down sessions (sessions classed by the 40 names' median open-to-close, terciles over the
  20 scored sessions); ex-best-day > 0; busiest session <= 10% of trades; positive in H1 and H2; and better than the
  price-only rule with the same mode/q/exit (difference > 0). Walk-forward is not possible on 20 sessions (stated).

### 1.5 Case study
For M1-M5 (and SPY): every feature's percentile vs the stock's 20 prior sessions (all seconds 09:30-16:00), per
minute from T-30 to T+10 (T = the turn bar in moments.csv); the strongest reading in the 30 minutes before T in the
turn's direction; and false alarms: onsets (15-minute refractory, 09:50-15:30) of the same reading (>= p99 in the
turn's direction) on 10-09 and per prior session, with the share followed by a 0.5% move in that direction before
0.25% against within 30 min.

### 1.6 Machine limits
One process (a 10-thread I/O pool inside it for downloads), RAM < 2.5 GB, data/ < 1.5 GB, stop if free disk < 1.2 GB.

### 1.9 Amendments
(none yet)
