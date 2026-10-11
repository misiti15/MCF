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

## 2. Results, part 2 (204 configurations; failures first)

*Educational only - not financial advice. Backtest only: daily bars (MOC/MOO fills) and a 1-minute after-hours
sample; costs in (1c + 1 bps per side, 3 %/yr borrow on shorts, AH: + half the quoted spread, floor 10 bps). The
locked block 2024-11..2025-02 is in no figure. Window 2019-01..2026-10-09. "net ex" = mean net excess per trade vs
the EW eligible universe over the same window; t = day-clustered (by entry date). Bar t >= 3.34 (N_lineage 264).*

**Counts.** 204 pre-declared configurations scored (B 24, U 48, P 72, G 36, A 24). Not counted: 24 all-event
controls, 15 diagnostic reruns. **0 candidates, 90 near, 114 fail. Nothing goes to the locked block (1.7).**

| family (N) | candidate | near | fail | best row (net ex / trade, t, n) | why it fails |
|---|---|---|---|---|---|
| B reaction only (24) | 0 | 11 | 13 | L th8 CLOSE H20: +0.81 %, t 1.67, n 2,332 | t; train -0.09 %; down months -0.21 % |
| U pre-report run-up (48) | 0 | 23 | 25 | L th4 RUN5down OPEN H20: +1.84 %, t 2.99, n 605 | t < 3.34; down months -0.38 %; **causal fixed window +0.33 %, t 0.24** |
| P previous 2-4 reactions (72) | 0 | 30 | 42 | L th4 SAME2 CLOSE H1: +0.18 %, t 2.17, n 1,291 | t; train -0.07 %; fixed window +0.01 % |
| G gap vs intraday (36) | 0 | 9 | 27 | S th4 GAPFADE CLOSE H1: +0.24 %, t 1.62, n 963 | t; WF 0.56 |
| A after hours (24) | 0 | 17 | 7 | S th4 AH H1: +0.68 %, t 2.77, n 890 | t < 3.34 only (all other gates pass) |

### 2.1 Failures
- **Controls first.** Buying every earnings event (no reaction filter) lags the same-window universe after costs:
  -0.06 / -0.10 / -0.26 % per trade at H1 / 5 / 20 (CLOSE entry), t -1.0..+0.2. Shorting every event also loses
  (-0.08..-0.11 %, t down to -2.6). There is no earnings-announcement premium to harvest here, net of costs.
- **Shorting after a negative reaction (B, U, P, G short rows) does not work.** All 12 B short rows are <= +0.00 %
  per trade; at H20 shorts lose -1.75..-1.90 % raw (the market drifted up) and only break even vs the universe.
  Short after a negative report when the stock was already falling (RUN5/RUN20 down) is the worst cell in the scan:
  -0.5..-1.5 % per trade (H5/H20), i.e. negative reactions on already-weak names *bounce*.
- **Long after a positive reaction (B long)** is flat at H1/H5 (-0.03..+0.16 %) and positive only at H20 for big
  reactions (th8: +0.81 / +0.89 % per trade, t 1.7 / 1.5), with train (2019-22) negative and SPY-down months
  negative (-0.2 / -0.6 %). That is the saturday1010 PEAD near-miss again; top-300 removes most of it (+0.61 %,
  t 0.24).
- **"Already rising before" (RUN up) adds nothing:** long after a positive reaction on a stock up >= 5 % in 5 days or
  >= 10 % in 20 days: -0.12..+1.42 % per trade, every H20 cell has a negative train split (RUN20up valid -1.6 %).
- **Previous reactions (P):** consistent reactors (previous 2/3/4 reactions with the same sign) are not better than
  all events at H5/H20 (long SAME3 H20 +0.28 %, t 0.84; SAME4 n 286 and train negative). Small positive H1 cells
  (SAME2 CLOSE H1 +0.18 %, t 2.17) vanish in the causal fixed window (+0.01 %). Big past reactors (BIG3) and past
  follow-through (FT3) are flat or negative. Short side: every P short row is negative except SAME2 H20 (+0.15 %)
  and OPP2 H20 (+0.29 / +0.30 %, t 1.8 / 1.7).
- **Gap vs intraday (G):** a positive reaction made *intraday* without a gap is followed by underperformance
  (INTRADAY long: -0.20 / -0.25 / -0.97 % at H1/5/20, t to -2.2). Gap-and-go long is flat at H1/H5 and +0.39..0.47 %
  at H20 (t 0.9). Gap-up-then-fade long is +0.30..0.38 % at H5 (t 0.9-1.2) and flat at H20 (+0.01 / -0.06 %).

### 2.2 After hours (family A, 1-minute sample)
- Sample: 3,648 events with an after-close report confirmed by 16:01-16:54 volume >= 10 % of the 20-day median
  (train 1,710, valid 892, valid2 1,046). Quotes existed for 98 % of the traded events; median half-spread at
  16:55-16:57 is **12-13 bps** (p90 39-48 bps).
- **Entering at ~16:55 beats waiting for the next open in all 12 matched pairs** (same events, same exit). The price
  keeps moving in the AH direction between 16:55 and the next open: +0.86 % (long, AH move >= 4 %), +1.10 % (>= 8 %),
  +0.66 % / +0.93 % for shorts (mean, before costs). At the next open that move is gone: OPEN entries are -0.31..
  +0.56 % per trade.
- Best: **short at ~16:55 after an AH drop >= 4 %, cover at the next day's close (A_S_th4_AH_H1)**: +0.68 % net
  excess per trade, t 2.77, n 890, train / valid / valid2 +0.50 / +0.94 / +0.66 %, SPY-up / down months +0.61 /
  +0.85 %, WF 0.78, ex-best-day +0.63 %, busiest day 1.3 %. **Fails only the try-count bar (2.77 < 3.34).** 2x all
  costs: +0.39 % (t 1.77); 2x AH spread: +0.42 % (t 1.88); top-300: +0.74 % (t 2.12). Same at th8: +1.00 %, t 2.51,
  n 447.
- Long side: AH jump >= 8 %, H1/H5: +0.71 / +1.12 % (t 1.7 / 2.1), WF 0.8-0.9, but SPY-down months -0.17 % (H1).
- All AH-confirmed events (control): long at 16:55 -0.49 % (t -3.3), short -0.16 % per trade: the edge is in the
  direction of the AH move, not in trading AH as such.
- Caveats: the 16:55 fill is the last trade of a thin market plus half the quoted spread; size beyond a few hundred
  shares would move the price. Shorting AH needs locate/borrow before 16:55 and an extended-hours LIMIT order (no
  market orders after hours). The confirmation rule (volume) only finds ~15 % of events; Yahoo's report hour (part 3)
  would find the rest.

### 2.3 Diagnostics (diag.csv) and honest caveats
- The best U row (RUN5down, long, +1.84 %, t 2.99) and the best P row **depend on the timing proxy** (1.2), which
  peeks at V[d+1] for bmo events: in the fully causal fixed window they drop to +0.33 % (t 0.24) and +0.01 %. They
  are not evidence until re-run with the true report hour (part 3, family TR, pre-declared).
- B th8 H20: survives 2x costs (+0.74 %, t 1.49) and the fixed window (+0.58 %, t 1.36), not top-300 (t 0.24).
- Survivorship (today's list), 2019-2026 only (one bear year), H20 trades overlap (day-clustering on entry date only
  understates the dependence for H20; the t values for H20 are, if anything, optimistic).

### 2.4 Answers to the owner (part 2)
- Buy after a positive report: next day flat; after a big (>= 8 %) reaction +0.8 % vs the market over 20 days, not
  significant after 264 tries, and only in small names.
- Already rising before: no help (worse in train). Falling before + positive report: the best daily row, but it
  collapses under causal timing.
- Short after a negative report: loses money in every daily variant; worst when the stock was already falling.
- Previous 2-4 reactions: no usable pattern.
- After hours: the clearest effect in the study. The AH move continues to the next open by ~0.7-1.1 %, so acting at
  ~16:55 instead of the next open turns a flat trade into +0.3..+1.1 % per trade. Not yet significant at the bar.
- EPS / revenue: not answerable yet (no data); fetcher and pre-declared grid (section 3) are ready.

## 3. Pre-declaration, part 3 (EPS surprise / revenue; written 2026-10-11 before that data exists)
Scored once `earnings_yf.parquet` and `sec_revenue_q.parquet` land on `research-data` (never their
`*_lockedblock` files). Same splits, costs, metric, statistics and gates as 1.4-1.7.
- **Timing**: Yahoo report hour -> bmo (hour < 9:30: R = d), amc (>= 16:00: R = d+1), unknown/12 AM/intraday ->
  the 1.2 volume proxy. Event match: Yahoo date within +-3 calendar days of the calendar date; else the Yahoo row
  is its own event. Surprise_pct is clipped to +-200 %.
- **E, strictly on EPS** (54): side {L after beat, S after miss} x X {0, 5, 10 %} (beat: surprise >= X; X = 0 means
  > 0) x entry {OPEN_R = O[R], the first regular open after the release, before the reaction day is seen; CLOSE_R;
  OPEN_R1 = O[R+1]} x H {1, 5, 20} (exit C[R+H-1] for OPEN_R so H1 is the reaction day itself; else C[R+H]).
- **EB, EPS and price agree or disagree** (24): {AGREE: beat >= 5 % and REACT >= +4 % (L) / miss <= -5 % and
  REACT <= -4 % (S); DISAGREE: beat >= 5 % but REACT <= -4 % (L, reversal bet) / miss <= -5 % but REACT >= +4 %
  (S)} x entry {CLOSE, OPEN} x H.
- **RV, revenue** (36): revenue matched to the event by fiscal period end within 0-100 days before d.
  {EPS beat (>= 0) and rev_beat_proxy > 0 (growth accelerated); EPS beat and rev_beat_proxy <= 0; rev_beat_proxy > 0
  alone} (S mirrored: miss / deceleration) x entry {OPEN_R, CLOSE_R} x H. No consensus revenue exists in free data:
  the proxy is growth acceleration, not a revenue surprise.
- **SH, surprise history** (12): previous 3 surprises with the current sign x side x entry {OPEN_R, CLOSE_R} x H.
- **TR, part-2 rework with true timing** (12): U RUN5down / RUN20down, long, theta 4 %, entry {CLOSE, OPEN} x H.
- Part 3 N = 138; lineage N = 264 + 138 = **402 -> bar t >= sqrt(2 ln 402) = 3.46**.

## 4. Files
`NOTES.md` (this), `elib.py` (events + features), `study.py` (grid, gates, diagnostics), `ah_fetch.py` (Alpaca 1-min
AH bars + quotes, data only), `actions/fetch_earnings.py` + `.github/workflows/earnings-data.yml` (Yahoo EPS surprise +
SEC revenue -> research-data branch), `results.csv` (every config + controls), `gates.csv`, `diag.csv`.
`data/` (git-ignored, 28 MB): earnings_cal copy, AH sample, trades.parquet.
Reproduce: `python research/bdi/earnings/ah_fetch.py` (~2 h, resumable) then `python research/bdi/earnings/study.py`
(~10 min, one process, < 1 GB).
