# SPY dip accumulation — NOTES (method, data, caveats)

*Educational only — not financial advice. Research only: no config, account, setup or live-code change; no PR merged.*

Owner idea 2026-11-17 (buy a 0.25-0.5% slice of a leveraged S&P ETF on S&P dips, hold; also an intraday version),
plus the owner's follow-up the same morning (the long hold as a hedge for the intraday book; design an automated rule
that maximises dip purchases; a runner spec). Tables and verdicts: `RESULTS.md`. Plan before scoring: `PLAN.md`.

## Failures and limits first
- Part B (intraday) has no candidate: best t 1.40 vs bar 3.13 (N 135).
- At account level a slice-buyer lags SPY buy-and-hold (cash drag); the rule only gets ahead of SPY with a large
  SPXL sleeve (~40% of the book), i.e. mostly through leverage.
- The designed rule loses to same-dollar random / schedule buying in its 2022-2024 validation years.
- Live hedge sample is 30 sessions; nothing can be concluded, and what there is points the wrong way.
- **No pre-2016 data**: Alpaca (SIP daily from 2016-01-04) is the only market-data host this session can reach; Stooq,
  Yahoo and others are refused by the proxy. 2008 is not tested. The leveraged ETFs all existed for the whole window,
  so **every Part A number is real ETF data; nothing is simulated**. The 3x / 2x daily-rebalanced simulation is only a
  tracking check (it overstates SPXL by ~2.3 pts/yr).
- Survivorship is not an issue (three index ETFs), but the sample is one long bull market with three sharp, fast
  recoveries (2018 Q4, 2020, 2022-23) plus April 2025 — the regime where buying dips works best.
- XIRR on short tranches (exit variants) is annualised and not comparable with hold rows; compare within an exit.

## Data
- Daily: `scripts/download_daily.py` (Alpaca SIP 1Day, adjustment=all = split and dividend adjusted, keys from the
  environment, read-only). SPY, SPXL, UPRO, SSO, BIL, 2016-01-04..2026-11-16 (11-17 partial, dropped). Rows in the
  locked block are dropped before saving. Data file not committed (kept in the session scratchpad; rerun the script).
- Minute: `data/cache_hist/1Min/{SPY,SPXL,UPRO,SSO}.parquet` (SIP 1-minute RTH, 2024-09-16..2026-11-04).
  Locked rows dropped at load (`scripts/common.py`). Minute fills are converted to the adjusted daily scale with that
  day's (adjusted close / raw 15:59 close) factor.
- **Locked block 2024-11-01..2025-02-28 is never read.** Nothing straddles it: SEG-A 2016-01-04..2024-10-31,
  SEG-B 2025-03-03..2026-11-16 run separately from $100k; the first SEG-B session and first week have no previous
  close / week and cannot trigger. Part B uses 2024-09-16..10-31 + 2025-03-03..2026-11-04 (ATR only from sessions on
  the same side of the block).
- Live book: `scripts/live_book.py` reads the ten intraday journals read-only (git show origin/mcf-data*:journal.db,
  temp copy deleted), run_id 1, sessions 2026-10-06 onward; P/L = pnl_adj (cost-in) where booked, else pnl.

## Costs
- Part A and the rule design: $0.01/share + 1 bp of notional per side (the long-hold book's model); ETF expense
  ratios and financing are inside the ETF prices; idle cash earns BIL.
- Part B: LR8 live model (config/default.yaml): entry 1 bp, market exit max($0.01, 1 bp), stop exit +max($0.02, 4 bp),
  SEC $20.60/$1M of sells from 2026-04-04, TAF $0.000166 (2025) / $0.000195 (2026) per share, CAT $0.00005/share/side.

## Method
- Part A (`scripts/partA.py`): per trigger day a fixed-$ slice; per-date outcome (exit date, multiple after costs)
  precomputed; XIRR vectorised (bisection). Benchmarks: random days (1,000 draws, same n, same fill clock), every
  schedule offset (one buy every k = sessions / n), SPY on the same dates, SPY buy-and-hold $100k, each ETF bought and
  held. Account view with a $100k cash pool, skipped buys counted. Local edge: each dip slice vs the slices of the ±10
  surrounding sessions (same time to the end). `partA_checks.py`: window removals (2020, 2022, 2018 Q4, Mar-May 2025),
  per-year local edge, equity_segA.png. `partA_terminal.py`: final dollars vs all schedule offsets and 200 random draws.
- Part B (`scripts/partB.py`): one trade per session per config, entry at the trigger bar's close, nulls = 20 random
  entry bars 09:50-14:30 on the same days and the same minute on every session; IDX-style day sets from SPY minute bars
  (IDX2/3/5 dip-from-open part, LD8 dip part; the recovery / breadth parts are not modelled, so these are supersets).
- Rule design (`scripts/design.py`): account simulation with compounding % sizes, cap and trim; pick on TRAIN
  2016-2021 by a rule fixed before the grid ran (best CAGR with max DD ≥ 1.2 x SPY's); VALID 2022-2024/10 fresh and as
  part of a continuous 2016 run; SEG-B fresh. Note: SEG-A and SEG-B had already been looked at in Parts A/B before this
  step, so VALID and SEG-B are not virgin for the design step (the same lineage), which makes the VALID shortfall more,
  not less, informative.
- Hedge (`scripts/hedge.py`): the chosen rule's SEG-B book ($100k from 2025-03-03) daily P/L vs live daily P/L and R.

## Configurations
Part A 720, Part B 135, rule design 96 — **951 total**. Lineage for the intraday family (with idxdip1015 1,134 and
drop_rebound_1116 36): 1,305, bar sqrt(2 ln 1305) = 3.79.

## Reproduce
    python -I research/spy_dip_accum_1117/scripts/download_daily.py OUT/daily.parquet
    MCF_ROOT=/home/user/MCF python research/spy_dip_accum_1117/scripts/partA.py OUT/daily.parquet OUT
    python .../partA_checks.py OUT/daily.parquet OUT; python .../partA_terminal.py OUT/daily.parquet OUT
    python .../partB.py OUT
    python .../live_book.py OUT/live_book_daily.csv     # needs git fetch of the mcf-data* branches
    python .../design.py OUT/daily.parquet OUT; python .../hedge.py OUT/daily.parquet OUT
Outputs here: results_partA.csv (all 1,080 Part A rows incl. SEG-B re-scores, decay and sim checks), partA_checks.csv,
partA_terminal.csv, partA_years.csv, results_partB.csv, trades_partB.csv.gz, overlap_partB.csv, design_grid.csv,
design_benchmarks.csv, rule_segB_daily.csv, live_book_daily.csv, hedge_*.csv, equity_segA.png, design_equity.png,
hedge_1006_1116.png.
