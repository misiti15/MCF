# ER earnings: buying / shorting after an earnings reaction (owner question 2026-10-11)

*Educational only - not financial advice. Lab backtests on daily bars (and a 1-minute after-hours sample); nothing
here is a live or paper result.*

Owner (2026-10-11): what happens when a stock is bought / shorted after a positive (negative) earnings report? If it
was already rising before? After hours? Strictly on EPS? Revenue? What did it do on the previous 2-4 reports?

**Section 1 was written before any configuration was scored.** Before writing it I only (a) read schemas and date
ranges, (b) checked a causal timing rule on volume only (1.2), (c) wrote the data fetcher (section 4).

## 0. Data
- Daily bars `research/swarm1010/w3_daily/data/daily_2016.parquet` (1,225 symbols, 2016-01..2026-10-09), loaded as in
  `research/bdi/saturday1010/new/lib.py` (eligibility, 1c + 1 bps per side cost, locked block).
- Earnings dates: `earnings_cal.parquet` from branch `research-data` (Nasdaq calendar, 2019-01..2026-11). It has **no
  actual EPS, no surprise, no revenue**, and `time` is missing for 98.7 % of rows (201 known rows in our symbols).
- After-hours sample: Alpaca SIP 1-minute bars and quotes (data endpoints only), 15:59-17:05 ET on report day d.
- Surprise / revenue data: not available yet; `actions/fetch_earnings.py` + `.github/workflows/earnings-data.yml`
  collect it on GitHub Actions (section 4). Part 3 (EPS beat / revenue) is pre-declared when that data lands.
- Survivorship: today's symbol list applied backward (no delisted names). Biases long books up.

## 1. Pre-declaration (part 2: reaction-based, no surprise data)

### 1.1 Splits (by reaction day R)
| split | dates |
|---|---|
| train | 2019-01-01 .. 2022-12-31 |
| valid | 2023-01-01 .. 2024-10-31 |
| LOCKED | 2024-11-01 .. 2025-02-28: never used. An event is dropped if any bar from R-25 to R+21 lies in it |
| valid2 | 2025-03-01 .. 2026-10-09 |
Every rule is fixed (nothing is fitted), so gates pool the three open splits and also require each split positive.

### 1.2 Events and timing
- Event = earnings_cal row, symbol in the bars and not an ETF; d = first trading day on/after the calendar date;
  repeats of a symbol within 10 sessions keep the first.
- **Reaction day R**: R = d if V[d] >= V[d+1], else R = d+1. This stands in for a timing schedule known in advance
  (bmo -> d, amc -> d+1; saturday1010 measured 90 % / 89 % agreement on known rows). It peeks at V[d+1] for bmo
  events, so it is a proxy, not a live rule. Checked before writing this: a causal rule on V[d] alone (V[d]/median
  >= 2 -> bmo) is only 62 % / 70 % right, so it is not used. **Diagnostic for the best rows (1.7): the fully causal
  fixed window** (reaction = close d-1 -> close d+1, signal at the close of d+1, as saturday1010).
  Part 3 replaces the proxy by Yahoo's report hour.
- Eligible at R-1: close >= $5, 20-day median dollar volume >= $20M, >= 253 bars. Shorts also need `shortable`
  in assets_meta.csv (today's flag; caveat).

### 1.3 Features (all market-adjusted: stock minus SPY over the same window)
- REACT = C[R]/C[R-1] - 1. GAP = O[R]/C[R-1] - 1. INTRA = C[R]/O[R] - 1.
- RUN5 = C[R-1]/C[R-6] - 1, RUN20 = C[R-1]/C[R-21] - 1 (pre-report run-up).
- PREV_k = REACT of the symbol's previous k events (previous events within 400 sessions; else missing).
- FT_prev = sign(REACT_p) x (excess 20-day return after R_p vs the EW universe) for a previous event p, only if
  R_p + 20 < R - 1 (fully known).
- Positive report proxy: REACT >= +theta; negative: REACT <= -theta.

### 1.4 Trades
- Long after positive, short after negative.
- Entry {CLOSE: MOC at C[R]; OPEN: MOO at O[R+1]}. Exit MOC at C[R+H], H in {1, 5, 20} (OPEN + H1 = O[R+1] -> C[R+1]).
- Cost per side 0.01/price + 0.0001 (production); shorts also pay 3 %/yr borrow (no hard-to-borrow fees: caveat).
- **Metric = net excess per trade** = side x (r - r_EW) - costs, r_EW = mean return of all eligible non-ETF names over
  the same entry -> exit window (rule 6: same side, same window, random name). Net raw (side x r - costs) reported.

### 1.5 Grid (counted)
- **B base** (24): side {L, S} x theta {4 %, 8 %} x entry {CLOSE, OPEN} x H {1, 5, 20}.
- **U run-up** (48): theta 4 %; condition {RUN5 >= +5 %, RUN5 <= -5 %, RUN20 >= +10 %, RUN20 <= -10 %} x side x
  entry x H. ("already rising" = RUN up.)
- **P previous reactions** (72): theta 4 %; condition {SAME2, SAME3, SAME4: the previous 2/3/4 REACT all have the
  current sign; OPP2: previous 2 both opposite sign; BIG3: mean |PREV_3| >= 6 %; FT3: mean FT_prev over the previous 3
  events > 0} x side x entry x H.
- **G gap vs intraday** (36): theta 4 %; condition (for shorts mirrored) {GAPGO: GAP >= 2 % and INTRA >= 0; GAPFADE:
  GAP >= 2 % and INTRA < 0; INTRADAY: |GAP| < 2 %} x side x entry x H.
- **A after hours** (24, the 1-minute sample, 1.6): theta {4 %, 8 %} on AHMOVE x side x entry {AH, OPEN} x H.
- **Total part 2: N = 204.** The lineage also includes saturday1010's 60 PEAD configurations: **N_lineage = 264,
  try-count bar t >= sqrt(2 ln 264) = 3.34** for every row.

Not counted (controls): ALL events (same side, no reaction filter) x entry x H; for U/P/G the matching B theta-4 row
is the "no condition" reference.

### 1.6 After-hours sample (family A)
- Universe: every event in the open splits (any timing proxy), 1-minute SIP bars 15:59-17:05 ET on d, and quotes
  16:55-16:57 ET, raw (unadjusted) prices.
- **After-close report confirmed at decision time**: volume 16:00-16:55 >= 10 % of the 20-day median daily volume
  (ending d-1). Only confirmed events trade (R = d+1 for them, whatever the volume proxy said).
- AHMOVE = close of the 16:54 bar / close of the 15:59 bar - 1, minus SPY's same move.
- AH entry: close of the 16:55 bar + **half the median quoted spread 16:55-16:57 (floor 10 bps; 50 bps if no quote)
  + 1c + 1 bps**. Mapped to the daily frame by the ratio to the 15:59 close. OPEN entry: O[d+1] as in B. Exit MOC
  C[d+H] (d+1 = R).
- Diagnostic (best rows, not counted): AH cost x2.

### 1.7 Statistics and gates (fixed now)
Day-clustered by entry date (mean per day, t over days). Per row: n, net excess mean / median / hit, day-clustered t,
net raw mean, splits, calendar years, ex-best-day mean, busiest-day share, SPY-up / SPY-down months (entry month).
**Candidate** (all of): n >= 150; net excess > 0 in train, valid and valid2; pooled day-clustered t >= 3.34; mean > 0
in SPY-up and SPY-down months; walk-forward share >= 0.6 (months with >= 10 trades from the 4th on, share with mean
> 0); plateau: mean of neighbours (H one step, CLOSE<->OPEN, B: theta 4<->8, U: RUN5<->RUN20 same direction, P:
SAME2<->SAME3<->SAME4, A: theta 4<->8) > 0; ex-best-day mean > 0; busiest entry day <= 10 % of trades.
**near**: pooled mean > 0 and >= 2 of 3 splits > 0. **fail**: the rest.
Diagnostics for candidates and the best near-miss per family (not counted, can only remove): 2x costs; causal fixed
window (1.2); top-300 by ADV; A: AH cost x2.
At most 2 finalists go to the lead for the locked block (Tier = candidate only). Nothing else.

### 1.8 Amendments (dated)
- 2026-10-11, before any scoring (seen while checking one fetched AH file; no returns looked at): the 16:00 minute
  bar carries the closing-auction print (e.g. BSX 1.6M shares on 2019-02-06), so the confirmation volume is summed
  over the **16:01-16:54** bars. If there is no 16:55 bar, the AH entry uses the last bar close from 16:50-16:55;
  with none, the event has no AH entry and is dropped from family A (for both entries, so AH and OPEN trade the same
  events). The signal price is the last bar close at or before 16:54 (from 16:30 on); none -> dropped.
