# LR6: the entry-execution sweet spot, per setup, per market condition and per ticker (2026-11-11)

Research only. This was written during market hours: no config, workflow or order was changed. The plan and its grid
were committed before scoring (`PLAN.md`, commit 1b122f205). Educational only — not financial advice.

## Plain English

**1. What entries cost today.** Market entries fill on average **4.4 bps (median 3.6) past the signal price, which is
about half the spread at the signal (4.6 bps)**. That is **0.040 R per trade**. The cost is set by the spread, not by
the setup or the market:
- by spread at the signal: < 5 bps costs 0.015 R; 5-10 bps 0.039 R; 10-20 bps 0.060 R; 20+ bps 0.078 R;
- ETFs cost 0.018 R and leveraged ETFs 0.014 R, against 0.048 R for single stocks;
- SPY-up moments cost 0.056 R and SPY-down moments 0.017 R (long-heavy books chase on up tape);
- the dearest families are NS5, NS1, NS3, MF1, NS2/RW4 and CWT12 (0.055-0.068 R); the cheapest are LIQ, RW6, CWT05 and
  ST2 (≤ 0.014 R);
- Primary pays 3.7 bps / 0.038 R. The signal-to-fill delay is 1.5 s (median) in every account.

**2. A marketable limit does not make the fills we get any cheaper.** The paper engine already fills at the ask about
1.5 s after the signal. A marketable limit that crosses fills at that same price. Every R a limit can gain comes from
two places only: (a) orders that **rest** and fill later at the limit, and (b) trades it **misses**.

**3. Most of the "net R per signal" a limit seems to add is a mirage.** All the books lose money on average
(−0.13 R per trade). So any rule that drops trades at random raises net R per signal. A pure limit at the signal price,
cancelled after 60 s, shows +0.059 R per signal, but it **drops 39% of trades (≈ 264 reps per session across the
accounts)**, and 0.052 R of that gain is just "fewer trades of a losing book". I split every change into three parts:
- price: a better price on resting fills;
- selection: are the missed trades better or worse than the average trade?
- book: what a random skip of the same share would give.

Only price + selection ("execution value") belongs to the execution rule. Scored that way, no single global policy
adds more than **+0.009 R per signal**, and the ones that come near it give up 10-55% of reps.

**4. Adverse selection is real, and it decides the cancel window.** The trades a limit misses are the ones where price
ran away from the signal, which are the runners. Had they filled at the signal price they would have averaged
**+0.01 to +0.38 R** (more the longer the window) (filled trades: −0.13 to −0.18 R). At the market price they are about average for short windows,
because the extra slip eats the run. With 5-minute windows the trades still missed are clear winners even at market
(+0.04 to +0.09 R). A limit that waits saves slip on the trades that come back, and loses the trades that go. The
two effects nearly cancel everywhere **except in wide-spread names**.

**5. The sweet spot depends on the ticker's spread, and on nothing else that held up.** Train picks by setup (with
shrinkage), entry style, momentum into the signal, price, SPY condition and one global rule all **failed on the
valid week** (execution value t between −0.3 and 1.5). The by-spread rule's wide leg held: for signals with a spread of
**≥ 10 bps** (≈ 35-40% of trades), a limit at the signal price ± 10 bps, cancelled after 300 s, gave execution value
**+0.022 R (train) and +0.013 R (valid, t 3.7, +0.010 without the best day, best-day share 42%)**. Fill rate is 91%.
In tight names (< 10 bps) every limit was flat or negative on valid. There the right order is LR6 as written (a
collar), which changes nothing in R and costs 0.1% of reps.

**6. LR6 as written is a free collar.** The order is ask (bid) ± min(0.25 × risk, 20 bps), with cancel after 60 s.
It fills **99.9%** of entries (0.5 reps lost per session across all accounts; Primary 0.2) and changes R by −0.0002
per signal. It is protection against halts, LULD and gap prints, not an R lever. It keeps that protection in every
regime.

**7. The 15 s quote-age cut is not worth its reps.** It drops 1.8% of trades (≈ 15 per session across accounts;
70-80% of them wide-spread names). Those trades average −0.18 R against −0.12 R kept, so +0.003 R per signal, almost
all book effect. On Primary the 15 dropped trades averaged **+0.29 R** (n 15, so noise, but the wrong sign). With a
limit order in place a stale quote cannot buy a bad fill, so **60 s** is enough: it drops 0.04% of trades.

**8. Recommended rule set (per account, Primary flagged):**

| Signal | Order | Cancel | Expected Δ net R / signal | Fill | Reps lost |
|---|---|---|---|---|---|
| Spread at signal < 10 bps | Marketable limit: ask (bid) ± min(0.25 × risk, 20 bps) (LR6 collar) | 60 s | ≈ 0 (−0.0005 valid) | 99.8-99.9% | ~0 |
| Spread at signal ≥ 10 bps | Limit at signal price ± 10 bps | 300 s | **+0.027 valid / +0.038 train** (execution part +0.013 / +0.022) | 91% | ~9% of wide signals |
| Quote age | Skip if > 60 s (not 15 s) | — | ≈ 0 | 99.96% | ~0 |
| Spread > 30 bps / > 25% of stop | Unchanged (already skipped today) | | | | |

On all signals together (valid): **+0.011 R per signal (t 5.9), execution part +0.006 R (t 3.6), fill 96.3%**. 20
families improve and 13 get worse (worst −0.065 R).

**Primary:** fill 98.5%, **0.6 reps lost per session** (of ~39-47), +0.016 R per signal over all dates (+0.013 valid),
execution part +0.014 (+0.010 valid). That is about **+0.5 to +0.7 R per session**. Team-6 on Primary: RW3 +0.003,
RW5 +0.008, L3-fromopen +0.044, NS5 +0.058, ST7 −0.011 (n 20). Primary is the account where this matters most for
live money. Run it on Primary with the 5-session fill-rate check that LR6 already asked for.

**9. What a 1-minute bar test cannot settle.** Cancel windows of 15 and 30 s, and the first minute of every window, are
sub-minute: the bars cannot say whether the through-trade came before or after the signal second. Those cells carry
wide bounds, for example a pure limit at the signal with 15 s cancel: fill 38-69% (point 45%). The recommended
300 s window is the best resolved (fill bounds 88-94% on wide names, point 91%). The resting fills need a 1-tick
trade-through, which is a live queue proxy. Alpaca paper fills a resting limit on a touch, so **paper will show a
higher fill rate than live**. Only 0.1% of resting fills needed a bracket re-simulation. Tick data (SIP quotes and
trades around each signal) would add:
- the true NBBO at the signal and at the fill (is the paper fill really the ask?);
- the exact second the limit price traded, to settle 15/30/60 s;
- size at the limit and trade-through volume, for the queue position;
- whether the 1.5 s latency itself costs slip.

Requested as LR6-D (after 16:00, rate-limited).

## Data and method

- 19,148 closed live paper entries (all 7 accounts with trades, 2026-10-06..11-11) for the cost tables. Policy scoring
  uses 17,687 of the 18,878 entries up to 11-10 with 1-minute bars (93.7% coverage). Train: 10-06..10-30 (10,666
  signals). Valid: 11-02..11-10 (7,021 signals). No locked holdout exists for live fills, so the next sessions are the
  forward test.
- Signal price = `orders.entry_ref`. Stop and target are absolute (set at the signal). R per signal uses the planned
  risk |ref − stop| for every policy, and a missed entry is 0 R. Costs are in on every fill: today's $0.02 stop
  allowance plus SEC/TAF/CAT fees (LR8 rates).
- Bars: `data/cache_hist/1Min`, read with a ≥ 2026-10-01 filter (the locked block 2024-11..2025-02 is never
  examined), plus the Move Hunt day files for 11-05/06/09/10. No API call was made (market hours).
- Fill model and grid as in `PLAN.md`: 45 configurations (1 market + 25 bps-offset × cancel + 15 spread-multiple ×
  cancel + 1 LR6-as-written + 4 quote-age, of which 3 are new) and 7 segmentations selected on train. The picks
  searched 41 policies over 20 segment cells (820 cells) plus ~190 setups (shrunk to family), and each objective was
  run twice. At p = 0.05 dozens of cells look good by chance, which is why only valid-week results are used for the
  recommendation.
- **Honesty note (deviation from the plan):** the plan's selection objective was Δ net R per signal. Under that
  objective, (c) momentum, (d) spread, (f) SPY condition and (g) per setup all "pass" on valid (Δ +0.010..+0.017,
  t 2.1-2.7, fill ≥ 90%), and (b) style misses the fill bar (89.7%). Files: `*_predeclared.csv`. After the first
  scoring I saw that this objective rewards dropping trades of a losing book. So I added the price / selection / book
  split and re-picked on execution value. Files without a suffix. Both are reported.
  The final rule **"(d-wide)" was formed after seeing the per-spread split**: its wide leg is exactly the train pick
  of the pre-declared (d) rule (O10_W300 for both 10-20 and 20+), and its tight leg is the do-nothing collar. Treat
  its valid score as semi-post-hoc. A second variant, +20 bps / 300 s on wide spreads, is labelled post-hoc and is
  weaker (valid execution value +0.0048, t 1.4).
- Entry style is set from data, not names: a setup whose median 3-minute move into the signal (side-signed) is > 0 is
  breakout/momentum; otherwise dip (long) or fade (short). Map: `setup_style.csv`.

**Rule-change context inside the window (`research/ledger.jsonl`):**
- 10-28: Primary size ~$4k ($ only).
- 10-29: Primary −2R per-setup latch.
- **10-30: Testing 1/2 cost filter CF** (`max_stop_cost_r 0.15`). It is the train/valid boundary, and after it Testing
  skips the most cost-heavy entries.
- 11-04: Testing 2 top-500 pool (UNI1: more liquid, tighter spreads).
- 11-05: ROLL1 homes.
- 11-11: Team-6 on Primary (not in the scored window).
- Many setup moves 10-22..11-11.

Spread mix changed across the boundary (wide share: train 33%, valid 42%), so per-signal results are given per spread
leg as well as in total.

## Tables

### Entry cost today (market orders; all 19,148 entries; `entry_cost_by_segment.csv`)

| Segment | n | slip bps mean | median | p90 | half-spread bps | slip R |
|---|---|---|---|---|---|---|
| All | 19,148 | 4.4 | 3.6 | 25.0 | 4.6 | 0.040 |
| Long / short | 10,769 / 8,379 | 4.2 / 4.7 | 3.2 / 3.9 | | 4.5 / 4.8 | 0.040 / 0.041 |
| Breakout-momentum / dip / fade | 9,829 / 3,353 / 5,966 | 4.2 / 5.1 / 4.5 | | | | 0.039 / 0.052 / 0.037 |
| 09:30-10:00 / 10-11 / 11-13 / 13-15 / 15+ | 1,813 / 8,633 / 5,619 / 2,869 / 214 | 3.6 / 4.9 / 4.1 / 4.5 / 2.6 | | 31.0 / 26.6 / 22.8 / 22.2 / 22.0 | | 0.028 / 0.046 / 0.038 / 0.038 / 0.025 |
| Price < 20 / 20-50 / 50-100 / 100-250 / 250+ | | 4.6 / 4.0 / 3.8 / 5.3 / 4.6 | | | | 0.030 / 0.034 / 0.042 / 0.050 / 0.043 |
| ADV Q1 (low) … Q4 | 4,753 each | 4.7 / 4.6 / 4.5 / 3.9 | | | | 0.042 / 0.048 / 0.043 / 0.028 |
| ATR% low / mid / high | 6,333 each | 2.2 / 4.7 / 6.4 | | 13.5 / 23.3 / 37.5 | | 0.037 / 0.048 / 0.036 |
| **Spread < 5 / 5-10 / 10-20 / 20+ bps** | 6,668 / 5,319 / 5,388 / 1,770 | **1.0 / 4.0 / 6.7 / 11.9** | | | 1.4 / 3.7 / 7.1 / 12.1 | **0.015 / 0.039 / 0.060 / 0.078** |
| Stock / ETF / leveraged ETF | 14,586 / 3,100 / 1,462 | 5.2 / 1.0 / 4.3 | | 25.6 / 12.5 / 42.2 | | 0.048 / 0.018 / 0.014 |
| SPY from open up / quiet / down | 5,868 / 9,989 / 3,021 | 6.1 / 4.1 / 2.3 | | | | 0.056 / 0.039 / 0.017 |
| Compass up / mixed / down / n.a. | | 4.7 / 4.5 / 3.7 / 5.0 | | | | 0.044 / 0.047 / 0.034 / 0.043 |
| Vol regime low / mid / high | | 4.1 / 4.5 / 4.7 | | | | 0.041 / 0.043 / 0.039 |
| Momentum into signal: against / flat / with | | 5.9 / 3.6 / 4.4 | | | | 0.046 / 0.040 / 0.035 |
| Primary / On Deck / Testing A / Gen / Graveyard | 1,109 / 3,872 / 5,032 / 2,827 / 6,187 | 3.7 / 4.5 / 4.4 / 4.6 / 4.5 | | | | 0.038 / 0.038 / 0.035 / 0.043 / 0.045 |

### Policy grid (all scored signals, 10-06..11-10; `policy_grid.csv`, train/valid split in the same file)

Fill is the point estimate with [lower, upper] bar bounds. "Missed R" is the market R of the trades not filled, and "@ref"
is the same trades priced at the signal (filled trades: −0.13 to −0.18).

| Policy | Fill [bounds] | Reps lost / session (all accts) | Δ net R / signal | price | selection | book | **exec value** (t) | missed R mkt / @ref |
|---|---|---|---|---|---|---|---|---|
| Market (today) | 100% | 0 | 0 | | | | 0 | |
| **LR6 as written** (touch + min(.25R, 20 bps), 60 s) | **99.9%** [99.8, 100] | **0.5** | −0.000 | 0.000 | −0.000 | 0.000 | −0.000 (−1.5) | +0.18 / +0.37 |
| Limit at signal, 15 s | 44.6% [38, 69] | 377 | +0.080 | 0.005 | 0.001 | 0.074 | 0.006 (1.1) | −0.13 / +0.01 |
| Limit at signal, 60 s | 61.2% [38, 74] | 264 | +0.059 | 0.019 | −0.012 | 0.052 | 0.007 (1.6) | −0.10 / +0.07 |
| Limit at signal, 300 s | 79.0% [76, 83] | 143 | +0.034 | 0.042 | −0.036 | 0.028 | 0.007 (2.0) | +0.04 / +0.24 |
| +5 bps, 30 s | 66.6% [55, 84] | 228 | +0.054 | 0.009 | 0.001 | 0.044 | 0.009 (1.7) | −0.13 / +0.05 |
| +10 bps, 60 s | 84.0% [70, 92] | 109 | +0.027 | 0.011 | −0.005 | 0.021 | 0.006 (1.3) | −0.10 / +0.14 |
| +10 bps, 300 s | 92.3% [90, 95] | 52 | +0.016 | 0.020 | −0.014 | 0.010 | 0.005 (2.3) | +0.05 / +0.33 |
| +20 bps, 30 s | 89.8% [85, 96] | 70 | +0.021 | 0.003 | 0.004 | 0.014 | 0.007 (2.0) | −0.17 / +0.10 |
| +20 bps, 300 s | 96.9% [96, 98] | 21 | +0.007 | 0.009 | −0.006 | 0.004 | 0.003 (2.1) | +0.06 / +0.38 |
| ref + 0.5 × spread (≈ touch), 60 s | 72.2% [53, 83] | 189 | +0.040 | 0.015 | −0.012 | 0.037 | 0.004 (0.7) | −0.09 / +0.11 |
| ref + 1 × spread, 120 s | 85.8% [81, 91] | 96 | +0.021 | 0.017 | −0.014 | 0.019 | 0.003 (1.0) | −0.03 / +0.21 |
| ref + 2 × spread, 300 s | 94.2% [93, 96] | 39 | +0.007 | 0.012 | −0.013 | 0.008 | −0.001 (0.3) | +0.09 / +0.37 |

The full 41-policy grid is in the CSV. Read across a row: the longer the window, the more the price gain is eaten by
missing the runners (selection turns negative). The shorter the window, the more reps are lost.

### Rule sets picked on train, scored once on valid (`rulesets_scored.csv`; pre-declared objective: `rulesets_scored_predeclared.csv`)

| Rule set (train pick, execution objective) | Valid fill | Reps lost / session | Valid Δ R / signal (t) | **Valid exec value (t)** | w/o best day | Families + / − |
|---|---|---|---|---|---|---|
| LR6 as written | 99.8% | 1.8 | −0.000 (−0.6) | −0.000 (−1.5) | −0.000 | 3 / 3 |
| (a) one global (+20 bps / 30 s) | 88.7% | 113 | +0.020 (2.0) | +0.005 (0.6) | −0.003 | 15 / 18 |
| (b) by entry style | 91.6% | 84 | +0.019 (2.9) | +0.008 (1.5) | +0.003 | 22 / 13 |
| (c) by momentum into signal | 92.2% | 79 | +0.015 (2.7) | +0.004 (0.9) | +0.000 | 15 / 18 |
| (d) by spread | 91.3% | 87 | +0.017 (2.1) | +0.005 (0.8) | −0.001 | 18 / 16 |
| — (d) wide leg (≥ 10 bps): +10 bps / 300 s | 91.2% | 37 | +0.027 (6.9) | **+0.013 (3.7)** | +0.010 | 13 / 7 |
| — (d) tight leg (< 10 bps): +20 bps / 15-30 s | 91.3% | 51 | +0.010 (0.8) | −0.001 (0.0) | +0.003 | 14 / 12 |
| (e) by price | 90.3% | 98 | +0.017 (1.6) | +0.004 (0.5) | −0.005 | 13 / 20 |
| (f) by SPY condition | 91.3% | 88 | +0.016 (2.3) | +0.004 (0.6) | −0.001 | 17 / 16 |
| (g) per setup, shrunk to family | 94.2% | 59 | +0.008 (2.4) | −0.000 (−0.3) | +0.002 | 17 / 13 |
| **(d-wide): wide leg as (d), tight = LR6 collar** | **96.3%** | **37** | **+0.011 (5.9)** | **+0.006 (3.6)** | +0.004 | 20 / 13 |

Train for (d-wide): fill 96.8%, Δ +0.013 (t 5.8), execution value +0.008 (t 3.9). On valid the tight leg alone is
−0.0007 R (t −2.8): the collar misses a handful of fast runners. This is tiny, but it is consistently negative. The
cost of the protection.

### (d-wide) by account (`ruleset_spread_split.csv`)

| Account | Trades / session now | Fill (valid) | Reps lost / session (valid) | Δ R / signal valid / all | Exec value valid / all |
|---|---|---|---|---|---|
| **Primary** | 47 | **98.8%** | **0.6** | **+0.013 / +0.016** | +0.010 / +0.014 |
| On Deck (Testing 1) | 67 | 97.4% | 1.7 | −0.004 / +0.011 | −0.007 / +0.007 |
| Testing A (Testing 2) | 140 | 96.3% | 5.2 | +0.018 / +0.013 | +0.011 / +0.008 |
| Setup Generator | 256 | 94.9% | 13.1 | +0.021 / +0.022 | +0.009 / +0.010 |
| Graveyard | 476 | 96.6% | 16.2 | +0.006 / +0.007 | +0.003 / +0.004 |
| Testing B / C | 18 / 12 | 98.7% / 91.2% | 0.2 / 1.0 | +0.011 / −0.002 | +0.009 / +0.001 |

### Wide leg by market condition and ticker (`wide_leg_robustness.csv`, execution value train / valid)

The leg was positive on both halves in almost every cut, so no condition-specific variant is needed:
- SPY down +0.029 / +0.021; up +0.015 / +0.017; quiet +0.022 / −0.002;
- compass up +0.017 / +0.018, down +0.031 / +0.010;
- breakout +0.015 / +0.017, dip +0.020 / +0.005, fade +0.031 / +0.015;
- every ADV quartile positive on both halves;
- price < $20: −0.000 / +0.024, fill only 81-84%; $50-100: +0.025 / −0.005;
- **09:30-10:00: +0.008 / −0.015** (the opening half hour is the one weak cell: a watch item, not a rule).

### Per family (owner remedy rule; all dates; `dwide_by_family.csv`, setups: `dwide_by_setup_account.csv`)

On Δ R per signal, 31 families improve and 5 get worse. On execution value, 28 improve and 8 get worse.

| | Families |
|---|---|
| Worse (Δ R / signal) | NS4 −0.058 (n 69), ST7 −0.016 (35), ST4 −0.014 (36), MF1 −0.014 (129), NS1 −0.003 |
| Flat | RW3 −0.000, NM −0.001, intraday_momentum 0 |
| Best | ST8 +0.098, NS3V1 +0.077, NS5 +0.052, RW4 +0.047, orb20_a +0.038, RW6G1 +0.036, NS3 +0.033 |

### Quote age (market entries with a logged quote age; `quote_age.csv`, `quote_age15_by_account.csv`)

| Max age | Dropped | Reps lost / session | R dropped vs kept | slip bps dropped vs kept | Δ R / signal |
|---|---|---|---|---|---|
| 5 s | 9.3% | 81 | −0.162 vs −0.115 | 7.3 vs 4.4 | +0.015 (mostly book) |
| 15 s (LR6 proposal) | 1.8% | 15.5 | −0.184 vs −0.119 | 8.6 vs 4.6 | +0.003 |
| 60 s | 0.04% | 0.4 | −0.264 vs −0.120 | | +0.000 |
| 300 s (today) | 0 | 0 | | | 0 |

Primary at 15 s: 15 trades dropped (0.9 per session), +0.294 R dropped vs −0.067 R kept → −0.006 R per signal.

## Reply codes

- **LR6-A yes**: LR6 collar for every entry with spread < 10 bps: marketable limit at ask (bid) ± min(0.25 × risk,
  20 bps), cancel unfilled after 60 s. Primary first, all accounts after 5 sessions. ~0 R, ~0 reps, protects against
  halts, LULD and gap prints.
- **LR6-B yes**: for spread at signal ≥ 10 bps, limit at signal price ± 10 bps, cancel after 300 s. Expected +0.027 R
  per wide signal (+0.011 per signal overall), Primary ~+0.5-0.7 R per session, ~0.6 reps lost per session on
  Primary. It changes which trades are taken, so it goes through the backlog and ledger and the setup-freeze timing.
  Measure the live fill rate for 5 sessions (paper fills on a touch, so it will run above the 91% modelled). Variant
  "LR6-B testing": Testing 1/2 first, then Primary.
- **LR6-C yes**: max quote age 60 s, not 15 s, once the limit/collar is in (15 s costs ~2% of reps for no clear R; on
  Primary it dropped winners).
- **LR6-D yes**: after 16:00, fetch SIP quotes and trades (rate-limited) around ~600 recent wide-spread and Primary
  signals (11-05..11-11), to settle the sub-minute fills, queue position and paper-at-ask (merges with LR15).
- LR6-E (no action needed): no per-setup, per-style or per-market-condition entry rule. None held on the valid week.

## Files

- `PLAN.md`: pre-declared plan (committed before scoring).
- `build.py`: trades, features, bars.
- `sim.py`: the 41 entry policies.
- `analyze.py`: cost tables, grid, rule sets; `LR6_OBJ=delta` reproduces the pre-declared objective.
- `wide.py`, `family.py`, `robust.py`: (d-wide) split, by family, robustness.
- CSVs as named above.
- `policy_by_segment.csv`: every policy × segment (all dates).

Educational only — not financial advice.
