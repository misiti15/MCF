# SPY dip accumulation in leveraged S&P ETFs — RESULTS (2026-11-17)

*Educational only — not financial advice. Research only: no config, account, setup or live-code change. Every number
below is a **backtest** on real ETF daily / minute bars with costs in, except the "live" intraday book in the hedge
section, which is **live paper** (journals, cost-in P/L). Nothing here has run live.*

Plan written before scoring: `PLAN.md` (commit e6e6149b6). Method, data and caveats: `NOTES.md`.
Owner follow-up (hedge value, best automated rule, runner spec) was added mid-study; its grid is a separate,
counted step (section 4).

## 0. Failures first
- **Part B (intraday, out by 15:55): nothing passes.** 135 configs; best day-t 1.40 (bar 3.13; Testing bar 2.82).
  41% of rows have a positive mean R; 14 rows are positive in TRAIN and VALID, positive without the best day and
  beat both nulls, but all have t ≤ 1.40 and n 22-57.
- **Account level, a slice-buyer does not "stay ahead of the S&P".** With $500 slices on gap-down ≥ 1% days the
  account is 67% cash on average and compounds at 10.2% a year (SEG-A) vs SPY buy-and-hold 14.3%.
- **Final dollars: weekly-drawdown triggers lose to a plain schedule.** `wkclose` and `wkhigh` (buy when below last
  week's close / high) finish behind the same dollars spent on a fixed schedule in SEG-A (0% of schedule offsets
  beaten), although their per-dollar return (XIRR) beats it — they keep cash idle longer in a rising market.
- **The designed rule fails its validation against same-dollar benchmarks.** Chosen on TRAIN 2016-2021, in the
  2022-2024 VALID years it is behind the same dollars spent on random days (0 of 100 draws beaten) and on a schedule,
  and, inside a run that started in 2016, behind SPY (6.9% vs 7.9% a year) with a deeper drawdown (-32% vs -25%).
- **No hedge seen in live data.** 30 live sessions: the dip book's daily P/L correlates -0.16 with the intraday
  book's (a hint of offset), but +0.44 with the next day's and +0.39 by week; over 10-06..11-16 both lost.
- **History starts 2016.** Alpaca is the only reachable data host; 2008 (SPXL-style 3x ≈ -95%) is not in the sample.

## 1. Overlap verdict (what is new)
| prior work / live setup | what it does | overlap with this idea |
|---|---|---|
| Index Dip Bounce 1-5 (IDX1/2/3/5; research/bdi/idxdip1015) | intraday, SPY/QQQ down from **today's open** by 09:45/09:55, 20% recovery, SPXL/UPRO/TQQQ, stop + trail, out 15:55 | Part B instrument and side; trigger days barely overlap (Jaccard 0.02-0.18, `overlap_partB.csv`), since the owner measures from the **previous close** (gap included) |
| SPY Dip 0.2 ATR / 0.30% with Breadth Turn (LD6, LD8), other LD setups | intraday, dip from the open + breadth turn, SPXL or stocks | Part B; LD8's dip part shares 12-37 of each family's days; LD1-5/LD7 are stock setups |
| research/drop_rebound_1116 | first-hour drop + 0.5% rebound; trigger ≈ random entries on the same days | Part B repeats its finding: being long on a dip day ≈ random times that day |
| research/forward/dip_day | frozen forward log: are dip days good for IDX/LD/NM-ETF? | untouched; different question |
| arena-index-etf, Late-Day ETF Dip Buy (NM-ETF-late-dip, WB1/WB4) | 14:00-15:00 dips in many volatile ETFs, small targets | Part B `pm1430` (SPY down from prev close at 14:30, long SPXL/SSO to 15:55) is negative — not a duplicate, not an edge |
| long-hold S6 runner (config/longhold.yaml) | weekly stock momentum, own paper account, MOO/MOC orders | **Part A is new**: no multi-day index-ETF accumulation exists. Shares the runner mechanics, not the signal |

**Verdict:** Part A (accumulate SPXL on dips and hold) is new work. Part B is a near-duplicate of the IDX / drop-rebound
family on different days, and it adds no measurable edge.

## 2. Part A — accumulation, finalists vs benchmarks (SPXL, hold, x = 1.0%, fixed $500 per buy)
Finalist per family = the hold row with the best SEG-A XIRR over random days (pre-declared); the deepest threshold
(1.0%) won in every family, 0.5 → 0.75 → 1.0% is a monotone plateau. SEG-A 2016-01..2024-10 (8.8 y); SEG-B
2025-03..2026-11 (1.7 y), scored as is.

XIRR = money-weighted return on the dollars actually deployed.
| family | seg | buys | XIRR dip SPXL | random days (1,000) | schedule (all offsets) | SPY, same dates | beats random / schedule |
|---|---|---|---|---|---|---|---|
| gap ≥ 1% at the open | A | 101 | **32.1%** | 26.6% | 26.6% | 16.4% | 100% / 100% |
| | B | 23 | **47.0%** | 25.8% | 26.7% | 19.7% | 100% / 100% |
| close ≥ 1% below prev close | A | 241 | 30.4% | 26.6% | 26.6% | 15.9% | 100% / 100% |
| | B | 47 | 40.8% | 25.9% | 26.3% | 17.8% | 100% / 100% |
| close ≥ 1% below last week's close | A | 379 | 29.3% | 26.6% | 26.3% | 15.7% | 100% / 100% |
| close ≥ 1% below last week's high | A | 832 | 28.5% | 26.6% | 25.8% | 15.3% | 100% / 100% |
| minute: SPY ≥ 1% below prev close at 10:15 | B | 20 | 47.9% | 26.2% | 26.4% | 20.1% | 100% / 100% |
| minute: same at 10:30 | B | 27 | 48.0% | 26.0% | 27.0% | 20.1% | 100% / 100% |
| minute: same at 15:30 (afternoon) | B | 42 | 42.1% | 26.4% | 26.7% | 18.1% | 100% / 100% |
| minute: gap at 09:30 | B | 24 | 46.6% | 25.9% | 26.9% | 19.6% | 100% / 100% |

All 72 SEG-A hold rows and all 144 SEG-B rows beat the random-day mean and SPY-same-dates; 100% / 96% beat the
schedule mean. The minute twins match the daily ones (15:30 decision 42.1% vs close proxy 40.8%), so the close-fill
proxy is not flattering.

**Final dollars** (same buys, $100k account, idle cash in T-bills, `partA_terminal.csv`):
| family (SEG-A) | deployed | dip SPXL | schedule mean (offsets beaten) | random mean (draws beaten) | SPY B&H $100k |
|---|---|---|---|---|---|
| gap ≥ 1% | $50.5k | $235.9k | $230.3k (100%) | $229.7k (76%) | $325.6k |
| close ≥ 1% | $120.5k | $395.0k | $394.5k (78%) | $388.0k (68%) | $325.6k |
| wkclose ≥ 1% | $189.5k | $528.5k | $604.6k (0%) | $544.4k (16%) | $325.6k |
| wkhigh ≥ 1% | $416.0k | $1,042k | $1,269k (0%) | $1,052k (31%) | $325.6k |
In SEG-B every daily and minute finalist beats schedule and random on final dollars (wkhigh: random only).
(close/wk rules deploy more than $100k: the excess is borrowed at the T-bill rate in this view — optimistic.)

**Drawdowns and cash drag** (gap ≥ 1%, $500, hold): account max DD -40.8% (SEG-A, 2020), longest underwater 535
sessions, 67% cash on average, CAGR 10.2% vs SPY B&H 14.3% (max DD -33.8%, 488 sessions). The open SPXL position fell
to -39.6% vs its cost basis at worst. SPXL itself: -76.9% max DD (2020), CAGR 27.7%; SSO -59.2%, 22.5%. SEG-B: account
-3.1% DD (small deployment), SPXL -40.5% (April 2025).

**Exits** (sell a tranche at +15/+30% or after 60/250 sessions): every exit row beats its random null (864/864), but
proceeds sit in T-bills — account CAGR 2-7% vs 10.2% for hold (gap, SEG-A). Hold wins for wealth.

**One-big-period check** (`partA_checks.csv`, `partA_years.csv`):
| finalist | all | without 2020 | without 2022 | without 2018 Q4 | SEG-B without Mar-May 2025 |
|---|---|---|---|---|---|
| gap ≥ 1% XIRR vs random | 32.1 vs 26.6 | 30.3 vs 25.9 (100%) | 31.7 vs 26.4 (100%) | 32.5 vs 26.6 | 21.0 vs 14.9 (86%) |
| close ≥ 1% | 30.4 vs 26.5 | 28.8 vs 25.9 | 30.2 vs 26.4 | 30.7 vs 26.6 | 22.3 vs 15.4 (99%) |
| 10:15 minute ≥ 1% | — | — | — | — | 28.2 vs 14.9 (99%) |
Per buy, the dip-day SPXL slice beats the slices of the ±10 surrounding sessions by +3.4% (gap) / +3.9% (close),
hit rate 66-76%, positive in **every** SEG-A year; no year carries more than 35% (gap: 2016; close: 2020 30%). In SEG-B,
2025 (April crash) carries 65-77% but 2026 is positive too. Not a one-crash result in SEG-A; SEG-B leans on April 2025.

**Leverage decay** (SPXL return minus 3x SPY return, all start dates): -0.6% over 20 sessions, -1.9% over 60,
-7.5% over 250 (SEG-A; SEG-B -1.0 / -2.8 / -9.8%). SSO about half. A daily-rebalanced 3x SPY simulation (0.91%
expense + T-bill financing) runs 2.3 pts/yr above real SPXL in SEG-A (29.9% vs 27.7%): swap spreads and cash drag
the simple model misses. All headline numbers use the real ETFs.

## 3. Part B — intraday (verdict: duplicate family, no edge)
Best rows (all 135 in `results_partB.csv`; LR8 costs; TRAIN to 2025-12, VALID 2026):
| config | n | avg R | t | TRAIN / VALID | w/o best day | random times same days | same minute all days |
|---|---|---|---|---|---|---|---|
| SPY ≥ 1% below last week's close at 10:15, UPRO, hold to 15:55 | 38 | +0.150 | 1.40 | +0.165 / +0.139 | +0.090 | +0.044 | -0.012 |
| same, SPXL, ATR stop | 38 | +0.145 | 1.34 | +0.163 / +0.132 | +0.085 | +0.055 | -0.011 |
| gap ≥ 1%, enter 09:50, SPXL, to 15:55 | 22 | +0.107 | 0.73 | +0.171 / +0.014 | +0.051 | -0.024 | -0.001 |
| gap ≥ 0.75%, enter 09:50, UPRO, to 15:55 | 35 | +0.085 | 0.74 | +0.139 / +0.013 | +0.045 | -0.063 | 0.000 |
| SPY ≥ 1% below prev close at 10:15, SPXL, to 15:55 | 18 | -0.055 | -0.37 | | | | |
| SPY ≥ 1% below prev close at 14:30, SPXL, to 15:55 | 35 | -0.032 | -0.55 | | | | |
The low-stop exit (just under the ETF's morning low) gives tiny R units and wild R (one day carries > 100%). The
10:15 / 10:30 / 14:30 drops from the previous close are negative. Nearest thing to a lead: the weekly-drawdown day
(SPY ≥ 1% below last Friday's close at 10:15), positive in both halves, beats random times by +0.10R — t 1.4 on 38
days, far from any bar. Try count 135 (lineage with idxdip1015 + drop_rebound_1116: 1,305, bar 3.79).

## 4. Owner follow-up: the best automated rule (96 configs)
Grid: trigger {gap at the open, close vs prev close, either (top-up)} x ladder {flat 0.5% at -1%; L1 0.25/0.5/1% at
-0.5/-1/-2%; L2 0.5/1/2%; L3 1/2/4%} x cap on SPXL as % of book equity {25, 40, 60, 100%} x trim {none; sell back to
the cap when above 1.25 x cap}. Sizes are % of current book equity (compounding), costs in, idle cash in T-bills.
Pre-declared pick: best TRAIN (2016-2021) CAGR with TRAIN max DD no worse than 1.2 x SPY's (-40.6%).

**Chosen: close trigger, ladder L2, cap 40%, trim to cap.** Uncapped / 100% rows earn more (TRAIN up to 40% a year)
but with -77% drawdowns; the 40% cap is the most the drawdown limit allows.
| window | dip rule | same $ on a schedule | same $ random days | static 40% SPXL (monthly) | SPY B&H |
|---|---|---|---|---|---|
| TRAIN 2016-21, fresh | **20.8%**, DD -40.3% | 14.4%, -36.0% | final $224k vs $311k (100%) | 19.6%, -35.4% | 17.4%, -33.8% |
| VALID 2022-24/10, fresh | 13.0%, -23.0% | 15.3%, -13.2% | $148k vs $141k (0%) | 6.8%, -30.4% | 7.9%, -24.5% |
| VALID inside the 2016 run | 6.9%, -32.1% | 5.5%, -31.6% | | 6.8%, -30.4% | 7.9%, -24.5% |
| SEG-A 2016-24/10 continuous | **16.3%**, -40.3% | 11.6%, -35.9% | $262k vs $378k (100%) | 15.4%, -35.4% | 14.3%, -33.8% |
| SEG-B 2025-03..2026-11 | **19.1%**, -11.6% | 8.7%, -7.5% | $115k vs $135k (100%) | 15.5%, -16.9% | 16.2%, -14.7% |
Average SPXL weight ~37-43% (≈ 1.2x S&P exposure), 85 / 81 / 39 buy days. Plain reading: most of "ahead of the
S&P" is the ~1.2x leverage of a 40% SPXL sleeve; the dip timing adds about +0.9 pt/yr over a static 40% SPXL book in
SEG-A and +3.6 in SEG-B, and loses a little in 2022-24. The 2022 bear hurts any capped book: the cap fills early in
the decline, so the deepest dips are not bought.

## 5. Hedge value (live paper book vs the chosen dip book, 2026-10-06..11-16, 30 sessions)
| | all 10 accounts | Primary only |
|---|---|---|
| live intraday P/L (cost-in) | -$33,369 | -$504 |
| dip book on $100k (backtest), same days | -$9,127 | -$9,127 |
| SPY B&H $100k | -$4,384 | |
| daily corr, same day / next day / next 5 days | -0.16 / +0.44 / +0.35 | -0.20 / -0.03 / -0.07 |
| weekly corr, same week / next week (7 / 6 weeks) | +0.39 / -0.35 | +0.58 / -0.64 |
| dip book on live losing days: same day / next day | -$245 / -$509 (25 days) | -$200 / -$605 (21 days) |
The intraday book's P/L correlates -0.17 with SPY's daily move, so a long-S&P book offsets it a little on the same
day, but over these six weeks the S&P fell and both books lost: combined curve below both SPY and the intraday book
alone (`hedge_1006_1116.png`). 30 days is far too few to call it (|r| ≥ 0.36 needed at p = 0.05). Structurally the dip
book is a ~1.2x long-S&P beta sleeve: it "hedges" an intraday book only to the extent that book loses when the market
rises; it does not protect on down days, it buys them.
Rule-change context inside 10-06..11-16 (research/ledger.jsonl): IDX setups from 10-16, Setup Generator 10-19,
Graveyard and LD1-LD8 10-21, Primary size $5k → $4k 10-28, Primary per-setup daily stop 2R 10-29, Testing cost filter
10-30, low-rep rotation 11-05, LR1-LR8 (cost-in R, live cost model, kill switch) and account halt 300 11-12, Testing
D/E/F 11-12, plus many setup moves; the live P/L mixes all of these.

## 6. Plain-English spec for an automated runner (research only; nothing is built or enabled)
- **Where:** never in an intraday account — `flatten_mcf` closes the whole SPXL position and the IDX setups trade SPXL /
  UPRO intraday (longhold DESIGN §2). Use the long-hold runner's mechanics in its own paper account (a 4th paper
  account, or a separate sleeve of the long-hold account with its capital split from S6, which needs a code change).
- **Daily at 15:45 ET:** read SPY's last price vs yesterday's official close. Drop ≥ 0.5% → buy SPXL worth 0.5% of book
  equity; ≥ 1% → 1%; ≥ 2% → 2% (one buy a day, the deepest tier). Market-on-close order, whole shares, client id
  `mcl-dip-<date>-SPXL-b` (deterministic, rerun-safe), skip under $25; cash buffer as in config/longhold.yaml
  (`moc_cutoff_et 15:45`, MOC cutoff 15:50).
- **Cap:** no buy that lifts SPXL above 40% of book equity. **Trim:** if SPXL is above 50% after a rally, sell back to
  40% at the close (the only sell). Idle cash in T-bills (BIL) or the broker's cash yield.
- **Kill switch:** a HALT file and data-sanity skips as in the long-hold design; book drawdown beyond -50% (worse than
  any 2016-2026 case, -40%) → no new buys, alert the owner, holdings kept (the book exists to buy drawdowns, so a
  normal drawdown must not stop it). Weekly report: SPXL weight, book vs SPY B&H and vs static 40% SPXL.
- **Expect:** about 10-20 buy days a year; drawdowns of 40% in a 2020-style crash and worse in a 2008-style one;
  ~-7.5% a year of leverage decay vs 3x SPY.

## 7. Configurations tried
Part A 720 (daily 360 scored on SEG-A and re-scored on SEG-B; minute 360 on SEG-B) + Part B 135 + rule design 96 =
**951**. Robustness reruns, benchmarks, nulls and the hedge analysis are not configurations.

## 8. Recommendation
1. Do **not** add an intraday dip setup (Part B): it duplicates the IDX / drop-rebound family with no edge. The
   weekly-drawdown day (`wk1015`) could go to `research/backlog.jsonl` as a day-type note for the frozen dip-day log,
   not as a setup.
2. Part A is worth a **forward paper test as a dry-run shadow book** in the long-hold runner's framework (no orders
   first; `mcl-dip-` ids), $100k notional, rule as in section 6, scored against SPY B&H and static 40% SPXL weekly.
   Present it to the owner as "≈1.2x S&P with dip-timed entries", not as a hedge — the live data show no hedge yet.
3. Before any real-money use, get pre-2016 data (2008) from an allowed host to size the crash drawdown.
