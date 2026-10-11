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

### 1.9 Amendments (dated; none changes a counted configuration or a gate)
- **A0 (2026-10-11, before scoring, clarification):** trading thresholds (1.4) use the prior sessions' seconds inside
  the entry window 09:50-15:30; the case study (1.5) uses all regular-session seconds as declared.
- **A1 (2026-10-11, after the first lift table):** the swing-start lift also reports the OPPOSITE-direction rate for
  the same flag (`dir_excess`, `t_dir` in `lift_summary.csv`), because a flag can raise both directions (volatility
  rather than direction). Diagnostic only, not a try; the scan was re-run to store the extra counts (deterministic,
  results otherwise identical).
- **A2 (2026-10-11, after scoring):** `gross.py` - the gross mid move after the strongest flow readings (p99 / p1,
  follow direction, 2 s latency) vs the quoted spread. Diagnostic only, not a try.

## 2. Results (written after scoring; section 1 unchanged except the dated amendments)

### 2.0 Failures and caveats first
- **No flow line makes money after costs. 0 of 240 trade lines is positive on any cost basis** (primary
  quote-crossing, SPY-hedged, or the mid-to-mid production-cost check). Best primary line: `flow|dlt300|fade|p999|E4`
  -4.24 bps/trade, t -1.91, n 494; best secondary (mid + production cost): -2.31 bps, t -1.06. Nothing comes near
  the t bar of 3.61 (N = 676) in the positive direction, so every gate fails at the first step (exp <= 0).
- **The reason is size, not sign:** after the strongest 1 % of flow readings the mid moves on average **+0.03 to
  +0.65 bps in the flow's direction** over the next 10 s - 15 min at 2 s latency (`gross.csv`), while the quoted spread
  at those very seconds is **3.5 - 4.7 bps**. The 0.5 % target is 50 bps. The information in the tape is real but
  tiny and almost all of it is priced within the first 1-2 seconds.
- **Predictive power exists only at seconds horizons.** Rank IC with the next 10 s mid return: qimb10 0.033
  (t 34), ofi10 0.036 (t 25.5), dlt10 0.030 (t 23.9). At 5 min it is 0.003-0.012, at 15 min flows are *negative*
  (mean reversion, the same sign as past price: dlt300 -0.034, r300 -0.054). The 10 s IC is measured from the decision
  second with no latency, so it overstates what is tradeable (see the gross numbers above).
- **Swing starts (>= 0.5 % before -0.25 %, 30 min): flow extremes flag volatility, not direction** - the same failure
  as the 57,612 bar lines (turns1009/scale). A p90 buy-flow reading raises the chance of a long swing start
  (lift 1.13-1.35) and raises the chance of a SHORT swing start just as much: directional excess t between -1.46 and
  +2.07 for all 36 feature-sides (bar 3.61). Quote imbalance, sweep and absorption flags even have lift < 1.
- **Flow as confirmation does not rescue C3b / C6.** Requiring flow within 60 s of the bar close improves the
  expectancy by +0.1 to +2.3 bps (30 of 40 confirmed lines beat their bare version: absorb60 +1.5 bps on average,
  dlt60/ofi60/qimb10/sweep30 +0.7-0.8) but every line stays negative: C3b -13.9 .. -16.6 bps (bare -15.9 .. -17.8),
  C6 -4.4 .. -7.2 bps (bare -5.7 .. -6.9). The improvement is far smaller than the cost.
- **Case study: flow would not have flagged the owner's turns in advance.** In the 30 minutes before each of the 5
  turns, essentially every flow feature (18 of 18) reached its p99 in the turn's direction at some point, and the same
  readings fire 1-13 times per session on ordinary days. Their precision for the 0.5 % swing on the 20 prior sessions
  is at base rate (e.g. AAPL long: base 5.7 %, flags 2.9-21 %; SPCX short: base 25 %, flags 15-32 %).
- Caveats: 40 hand-picked liquid names (survivorship / selection), 20 sessions (no walk-forward possible), sample
  overlaps the older holdout; Lee-Ready signing on SIP is noisy for off-exchange prints (~40-50 % of volume) and
  inside-spread prints; SIP NBBO sizes are only the best venue's top-of-book, not depth; the SIP timestamp is used for
  both trades and quotes. None of these is likely to flip a 4-bps-per-trade deficit.

### 2.1 Data volumes
| item | value |
|---|---|
| symbol-days | 840 (40 x 21) |
| raw SIP trades downloaded / kept after the condition filter | 265.4 M / 252.9 M |
| raw NBBO quote updates downloaded | 460.9 M |
| aggregates kept on disk (`data/`, git-ignored) | 797 MB (1-second records ~0.95 MB / symbol-day, zstd parquet) |
| download + aggregation time (one process, 10 I/O threads) | ~1.55 CPU-h of aggregation, ~3 h wall |
| live message rate, these 40 names | mean 1,478 msg/s; sum of per-symbol p99 8,275 msg/s; single-symbol bursts to 10,000 msg/s (NVDA, SPCX) |

Per-symbol rates and median quoted spread: `feasibility.csv` (median spread 0.2 bps SPY .. 9.7 bps MARA).

### 2.2 Case study (owner's 5 moments, 2026-10-09; `case_summary.csv`, `case_minutes.csv`, `case_alarms.csv`, `case_footprint.md`)
Percentiles are vs the same stock's 20 prior sessions; "turn direction" = bullish for a long turn, bearish for a short.

| moment | flow at T (+-1-2 min) in the turn's direction | 30 min before | alarms of the same p99 readings |
|---|---|---|---|
| M1 AAPL 13:49 long | dlt10 99.8, qimb10 99.7, imb60 99.8, big60 99.3 - but r10 (price) 99.0 too: the bounce off the low shows in price and flow at the same second. A 33k-share buy at 334.92 in the 13:48 footprint. | every feature hit p99 at some point (both directions) | dlt10 14 onsets on 10-09 (8.1/prior session), 0 hit; qimb10 13 (12/session) |
| M2 AAPL 15:14 short | qimb10 99.7, absorb60 99.8, dlt10 98.8; dlt300 / big60 / fp_stack against the turn | buy flow p99+ into the top (dlt10 99.6) | caught T+-5 min only by absorb60 (11 onsets that day, 1 hit) |
| M3 SPCX 10:13 short | dlt10 99.1, qimb10 99.4, r10 99.3; sell flow already p100 in the 30 min before (a sell-off since the premarket) | sell flow extreme the whole half hour | 11 of 18 features caught T+-5, but each fired 2-12 times that day; precision 15-32 % vs a 25 % base |
| M4 CAT 10:11 long | nothing above p96.9 (dlt10) except r10 99.9 / r60 99.8 (price) | | caught by fp_low_d only (4 onsets, 0 hits) |
| M5 TSLA 10:51 short | absorb60 100, burst10 99.1, qimb10 99.1, r10 97.1 | | absorb60, burst10, ofi, sweep caught T+-5; 5-9 onsets that day each |

SPY at the same minutes: no consistent reading (dlt10 91-95, qimb10 86-99).

### 2.3 Predictive tests (a) - 196 counted tests (`ic_summary.csv`, `lift_summary.csv`)
Rank IC (mean over 20 sessions of the cross-symbol mean; day-clustered t), raw:

| feature | 10 s | 60 s | 5 min | 15 min |
|---|---|---|---|---|
| qimb10 | 0.033 (34.0) | 0.016 (13.8) | 0.008 (5.6) | 0.007 (3.0) |
| ofi10 | 0.036 (25.5) | 0.013 (6.3) | 0.001 (0.4) | -0.007 (-3.3) |
| dlt10 | 0.030 (23.9) | 0.015 (13.1) | 0.003 (2.2) | -0.003 (-2.3) |
| dlt60 | 0.011 (9.5) | 0.006 (2.7) | -0.008 (-2.5) | -0.016 (-6.5) |
| dlt300 | 0.001 (0.6) | -0.008 (-2.8) | -0.023 (-4.9) | -0.034 (-6.5) |
| sweep30 | 0.008 (9.4) | 0.004 (2.3) | -0.002 (-1.0) | -0.006 (-3.1) |
| cvd_div300 | 0.007 (4.0) | 0.009 (2.5) | 0.012 (1.8) | 0.017 (3.1) |
| absorb60 | -0.011 (-19.5) | -0.007 (-6.2) | 0.001 (0.6) | 0.003 (1.9) |
| price r10 / r60 / r300 | 0.012 / -0.003 / -0.006 | ... | -0.004 / -0.015 / -0.036 | -0.010 / -0.025 / -0.054 |

Incremental IC beyond r10/r60/r300 (partial rank correlation): ofi10 0.047 / 0.021 / 0.009 / 0.005 (t 58 / 21 / 6.7 /
2.6); dlt10 0.028 / 0.017 / 0.007 / 0.004; qimb10 0.033 / 0.016 / 0.008 / 0.007. So flow does carry information that
recent price does not - at 10-60 s, with an IC of 0.01-0.05 and a gross move far below the spread (2.0).
absorb60 has the opposite sign to its "sellers absorbed" reading at 10-60 s (absorbed aggression keeps winning
briefly).

### 2.4 Tradeable tests (b) - 480 counted lines (`results_lines.csv`)
| family | lines (x raw/hedged) | exp/trade, bps (primary) | best | positive lines |
|---|---|---|---|---|
| flow follow p99 / p999 | 40 / 40 | median -6.9 / -7.5 | -4.83 | 0 |
| flow fade p99 / p999 | 40 / 40 | median -6.9 / -6.4 | -4.02 | 0 |
| price-only (r60/r300) same rules | 32 | median -7.5 .. -9.2 | -5.60 | 0 |
| random entries (same window) | 4 exits (not tries) | -6.1 .. -7.6 | | 0 |
| C3b bare / + flow confirmation | 4 / 20 | -15.9..-17.8 / -13.9..-16.6 | -13.92 | 0 |
| C6 bare / + flow confirmation | 4 / 20 | -5.7..-6.9 / -4.4..-7.2 | -4.41 | 0 |
| SPY-hedged versions of all of the above | 240 | 2-3.5 bps worse (hedge cost, no beta drift to remove at 5-30 min) | -6.87 | 0 |

Flow beats the matched price-only rule in 129 of 160 flow lines (by ~1-2 bps), i.e. flow selection is a little less
bad than price selection, never good. Up vs down sessions: no line is positive in either regime overall except a
handful of single-regime cells at 0 to +0.3 bps (e.g. dlt60 fade p999 E4 secondary +0.26 in up sessions).

### 2.5 Does flow add real after-cost edge?  **No (Step A).**
At the horizons that matter for >= 0.5 % moves (minutes), SIP trade + NBBO flow adds an IC of ~0.005-0.01 beyond
price, worth a fraction of a basis point, while a round trip costs ~4-8 bps on these names. Flow is a good
*description* of what is happening right now (e.g. the 33k-share buyer at M1), but by the time a 1-second system
can act on it, the price has already adjusted. It does not separate a turn from a look-alike any better than bars.

### 2.6 Live feasibility (what Step B would need)
- **Data:** Alpaca's SIP websocket (`trades` + `quotes` channels) carries everything used here; for these 40 names
  ~1,500 msg/s average, ~8,000 msg/s at busy seconds, bursts of 10,000 msg/s on one name. The full lab universe
  (1,226 names) would be well above that - quote updates dominate. The plan already used for SIP REST includes the
  SIP websocket (verify the subscription tier; free/IEX feeds are not SIP and would not match these numbers).
- **Compute:** a single Python process with msgpack parsing and per-second numpy aggregation handles a few thousand
  msg/s; 40 names is feasible, hundreds of names needs a compiled parser or a sharded consumer.
- **Hosting:** the trade job runs on GitHub Actions polling 1-minute bars. A tape reader needs a persistent
  connection for 6.5 h; Actions jobs stop at 6 h and (on a private repo) would use ~8,000 runner-minutes a month.
  Realistically a small always-on VM ($5-20/month) plus reconnect / gap-recovery logic.
- **Level 2 / depth:** Alpaca does not sell equity depth. Depth (Nasdaq TotalView, NYSE OpenBook, Cboe) comes from a
  broker terminal/API or a data vendor, typically tens of dollars per exchange per month for non-professional
  display data and more for vendor API feeds (verify current prices). Honest expectation: depth beyond the NBBO
  mostly helps on the same seconds horizon where our top-of-book OFI / queue imbalance already showed the strongest
  IC (0.03-0.05) - and that horizon is the one the spread eats. Lit depth also misses the ~40-50 % of volume that
  prints off-exchange, and resting orders are cancelled within milliseconds. I see no plausible path from paid depth
  to a 0.5 % move edge for a minute-scale system.

### 2.7 Recommendation
- **Step B (live websocket flow capture / paper signal): not recommended** on this evidence - there is no
  after-cost candidate to carry forward, and the cost (persistent host, websocket, engineering) is real.
- **Step C (paid Level-2): not recommended.** The top-of-book flow that is free already shows the "depth is
  short-lived" pattern; paying for more of it targets the wrong horizon for our 0.5 % / minutes trading.
- Cheap, useful by-product: per-second spread and flow at entry is a good *cost* diagnostic. The measured spreads at
  flow extremes (3.5-4.7 bps) are about twice the typical median, i.e. our entries tend to happen when spreads are
  widest; the time-of-day cost multipliers (`gates.TOD_COST`) could be re-checked with these 1-second data.
- If the owner still wants to look: the only flow quantity with a positive IC that survives past one minute and
  beyond price is quote/queue imbalance (qimb10, ofi10: IC ~0.008 at 5 min). It would at most be a tie-breaker for
  limit-order placement (join the bid vs cross), a housekeeping/execution question, not a setup.

### 2.8 Files
`fetch_agg.py` (download + aggregation), `fetch_bars.py`, `of_lib.py` (features, signatures, regimes), `case.py`,
`scan.py`, `report.py`, `gross.py`, `feasibility.py`; outputs `case_*.csv`, `case_footprint.md`, `ic_summary.csv`,
`lift_summary.csv`, `results_lines.csv`, `gross.csv`, `feasibility.csv`. Data in `data/` (git-ignored, 797 MB):
delete with `rm -rf research/bdi/orderflow/data` when no longer needed.
