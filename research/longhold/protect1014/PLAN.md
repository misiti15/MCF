# S6 protection study (2026-10-14): pre-declared plan

*Educational only - not financial advice. Backtest research on daily bars. Nothing here changes the live book,
`config/`, `mcf/` or any workflow. This file was written **before any configuration below was scored**. It may change
only by dated amendments at the bottom.*

Owner (2026-10-14), about `S6_mom12_1rev_N20_W`: worried about large market drawdowns (Covid, Ukraine, 2008). Asks
whether stops, profit-locks or crash rules would help without exiting on small pullbacks, wants a fully automated
rule, and asks whether 20 names are diverse enough (30 / 40?).

Lineage: child of `lh-mom-revfilter` (MANAGEMENT.md 3). S6's single look at the locked block 2024-11..2025-02 is
used. **This study never reads returns inside that block.** Every return inside it is set to 0, as in `study.py`, and
its days are dropped from every statistic. No locked look is made here.

## 1. Data, splits, costs (same as `research/longhold/NOTES.md`)
- Daily bars `research/swarm1010/w3_daily/data/daily_2016.parquet` (2016-01-04..2026-10-09, 1,225 symbols, split- and
  dividend-adjusted), extra ETFs `research/longhold/data/etf_extra.parquet` (BIL = cash leg).
- Splits: warm-up 2016, train 2017-2020, valid 2021-01..2024-10, LOCKED 2024-11..2025-02 (zeroed), valid2
  2025-03..2026-10-09.
- S6 rule unchanged: weekly signal at the last close of the week. Eligible names: price >= $5, ADV20 >= $20M,
  at least 253 bars, not an ETF. Drop the top decile of the 21-day return, rank by 12-1 momentum, hold the top N at
  equal weight, and fill MOO at the next open.
- Costs: 1c/share + 1 bps per side on every traded dollar at the open, as in the study. Intraday stop fills also pay
  **+5 bps extra stop slippage** (rule 1). A stop gapped through fills at the open. Cash parked by a stop or an
  overlay earns BIL's daily return and pays 1 bps per side.
- Survivorship: the universe is today's list run backward (NOTES 2.0, EW universe beats RSP by 6.3 %/yr). **This
  biases the test against per-name stops.** Names that crashed and were delisted, where a stop would have saved
  money, are missing. Names that crashed and recovered, where a stop costs money, are over-represented. The per-name
  stop results below are therefore a pessimistic estimate of stop value. The book-level results are less affected.
- Parity first: the baseline in this study's own simulator must reproduce `S6_mom12_1rev_N20_W` from
  `research/longhold/data/daily_returns.parquet` to < 1e-9 per day before anything is scored.

## 2. Mechanics of the new rules
**Per-name stop state.** Stop levels use each name's return index, the cumulative product of daily close-to-close
returns with the locked block zeroed. Locked-block prices therefore never trigger or set a stop.
- Entry level = the fill open of the day the name enters the book. A name that stays in the top N across rebalances
  keeps its entry and its high. Trims and adds at a rebalance do not reset them.
- High = the highest close since entry.
- Rules, with the stop level at the close of day d:
  - `fixX`: entry x (1 - X).
  - `trailX`: high x (1 - X).
  - `lockP_trailX`: no stop until the high reaches entry x (1 + P), then high x (1 - X).
  - `lockP_be`: same activation, then the stop sits at entry (breakeven).
  - `lockP_p10`: same activation, then the stop sits at entry x 1.10 (+10 % locked).
- Trigger variants:
  - `C` (close): close <= level at day d, then sell MOO at the open of d+1 at the open price.
  - `L` (intraday low, harsher): a resting stop. If the low of day d+1 <= level, fill at min(open, level), plus 5 bps
    extra slippage. On a rebalance day this is checked after the open for names held after the rebalance.
- Re-entry variants:
  - `cash`: proceeds sit in BIL until the next weekly rebalance. That rebalance is the normal S6 rebalance, so a
    stopped name that is still in the top N is bought back.
  - `repl`: the same, but a stopped name is barred from the next rebalance. Its slot goes to the next-ranked eligible
    name. The bar lasts for one rebalance only.
  - Under `C`, if the exit open is itself the rebalance open: under `cash` the name simply follows the target (no
    exit if it stays in the top N). Under `repl` it is barred.
- **Premature-exit rate:** the share of stop exits where the name's close 20 sessions after the exit day is above the
  exit fill. Also reported: the median 20-session return after the exit and the stops fired per year.

**Book-level overlays.** These apply to the baseline S6 daily return series, with exposure s in [0, 1] and the rest
in BIL. Decisions are made at a close and applied from the next open: the overnight part of the next day's S6 return
is earned at the old s and the open-to-close part at the new s. Switching cost per unit |delta s| = S6's realised
average cost per traded dollar (from the simulator) + 1 bps BIL.
- `ddX_reR`: book drawdown stop. Measured on the overlaid book's own equity from its high-water mark. At
  DD <= -X % at a close, go to BIL. Re-entry, always at a weekly rebalance open:
  - `4w` / `8w`: at the first rebalance at least 20 / 40 sessions after the exit.
  - `s50` / `s200`: at the first rebalance whose signal close has SPY > its 50 / 200-day SMA.
  - At re-entry the high-water mark resets to the current equity.
- `trend_d200`: SPY close > SMA200, checked every close; below it, BIL. (This extends CWT C8, which went to 0-return
  cash.)
- `trend_w200`: the same, checked only at the weekly signal close.
- `trend_m10`: SPY month-end close > its 10-month SMA of month-end closes (Faber), checked at month end.
- `trend_w200_half`: weekly SPY < SMA200 -> s = 0.5 instead of 0.
- `vtT_20d`: s = min(1, T / annualised 20-day realised vol of S6's daily net returns), updated at each weekly signal.
- `vt30_20d_daily`: the same with T = 30 %, updated every close.

**Breadth and sector cap.** These change the S6 target, which is re-simulated with full costs.
- `N30`, `N40`: top 30 / 40 at equal weight. N20 and N50 W are already scored in the study and shown as references,
  not counted.
- `N20_capK`: walk down the ranking and skip a name whose sector already has K names, K in {3, 4, 5}. There is no
  point-in-time GICS file in the repo; the only map, `research/rework/web_families/sector_map.json`, covers 299
  names from one month of 2026. So the sector is **statistical and point in time**. At each signal close t, each
  candidate is assigned to the SPDR sector ETF (XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE, XLC; only ETFs
  with >= 200 bars) whose SPY-residual daily returns over the last 252 sessions correlate most with the name's
  SPY-residual returns. This is a caveat: it is not GICS.

## 3. Grid (pre-declared; every row counts)
| block | configs | count |
|---|---|---|
| A per-name stops | rules {fix10, fix15, fix20, fix25, fix30, trail10, trail15, trail20, trail25, lock{20,30,50} x {trail10, trail15, trail20, be, p10}} = 24 rules x trigger {C, L} x re-entry {cash, repl} | **96** |
| B book drawdown stop | X {10, 15, 20} x re-entry {4w, 8w, s50, s200} | **12** |
| B trend filter | d200, w200, m10, w200_half | **4** |
| B vol scaling | vt20_20d, vt30_20d, vt40_20d, vt30_20d_daily | **4** |
| C breadth | N30, N40, N20_cap3, N20_cap4, N20_cap5 | **5** |
| **total** | | **121** |

Try-count bars: this study, N = 121, sqrt(2 ln 121) = **3.10**. Lineage `lh-mom-revfilter`, cumulative: study 105 +
CWT S6 overlays 7 + sat1010 crash guards 18 + this 121 = 251, sqrt(2 ln 251) = **3.32**. The higher bar, 3.32, is
used for any "improves Sharpe" or "improves return" claim.

Already tested and not repeated: SPY > SMA200 / SMA10 to 0-return cash, follow-through, two closes < SMA20, Kidd EMA,
Keltner, and the 20-week equity governor on S6 W (CWT). On the monthly sibling and S1W (sat1010): SPY200 -> EW / BIL,
TR, VIX percentile, momentum-vol percentile, bear state, and vol scaling to EW. `trend_d200` overlaps C8. The
differences are the BIL leg and the daily check with an overnight split; it is counted anyway.

## 4. Statistics
These are computed per split (train, valid, valid2), for train+valid pooled, and for all open days:
- CAGR, annual vol, Sharpe (rf 0, as in the study), max drawdown (equity restarted at the split start), and the
  worst calendar month.
- Turnover (one-way per year) and cost drag.
- Active vs the EW universe.
- Per-name weight (breadth block).
- Stops: stops per year, premature-exit rate, and median 20-session return after the exit.

**Stress windows** (D; returns compounded over the window; all are open days):
- Q4 2018: 2018-10-01..2018-12-24
- Covid crash: 2020-02-19..2020-03-23
- Covid crash + rebound: 2020-02-19..2020-06-30. This shows what a rule gives up by being out for the rebound.
- Nov 2020 momentum reversal: 2020-11-01..2020-11-30
- 2022 H1 (rates / Ukraine): 2022-01-03..2022-06-16
- 2022 full year
- 2025 tariff selloff: 2025-03-01..2025-04-08 (valid2)
- Aug 2015 / early 2016: **not covered** (the data starts 2016-01-04 and 2016 is the warm-up year).

**2008 proxy (diagnostic, not counted, not a gate).** There is no stock or ETF price data before 2016 in the repo.
The only long history is Ken French daily factors (`research/bdi/saturday1010/rework/data/ff_factors3_daily.parquet`,
`ff_mom_daily.parquet`, 1926..2026-08).
- Proxy: S6_proxy = RF + a + b_m x (Mkt-RF) + b_u x Mom, with a, b_m, b_u fitted by OLS of S6's daily returns on
  train+valid. The intercept is dropped in the stress replay (conservative).
- Run the book-level overlays (B) on the proxy for 2007-06..2010-12. This covers the 2008 crash and the March-May 2009
  momentum crash. Also run 2000-2003 (dot-com).
- The SPY trend rules use a market index rebuilt from Mkt-RF + RF.
- Per-name stops and breadth cannot be proxied with factor data, and this is stated.

## 5. Gates for "recommendable protection rule" (owner bar + MANAGEMENT 3b)
A candidate (from A or B) must pass **all** of the following:
1. **G1 drawdown cut:** max drawdown at least 5 points shallower than baseline S6 in train **and** in valid,
   separately.
2. **G2 return kept:** CAGR at least baseline - 3.0 points in train **and** in valid.
3. **G3 Sharpe not lower:** Sharpe >= baseline Sharpe in train, valid and valid2.
4. **G4 stress:** a smaller loss than baseline in at least 4 of the 6 stress windows inside train+valid+valid2,
   counting Covid crash, Q4 2018, Nov 2020, 2022 H1, 2022 full and the 2025 tariff selloff.
5. **G5 plateau:** the mean over the parameter neighbours (one step of X, P, T or re-entry, same block) of the
   train+valid Sharpe change is >= 0 and the mean of the maxDD change is > 0 (shallower).
6. **G6 consistency:** in at least 60 % of calendar years 2017-2026 (locked days excluded), the yearly Sharpe is >=
   baseline.

Any claim that a rule **raises** Sharpe also needs the block-bootstrap t of the train+valid Sharpe difference (daily
returns, 20-day blocks, 1,000 draws, fixed seed) to be >= 3.32.

Breadth block (C): reported against the same bars (G1-G3, G5 with N20-N30-N40-N50 as neighbours), plus active vs EW
in every split. A breadth change passes "without risking gains" only if it passes G2 and G3. A lower drawdown is a
bonus, not required.

If nothing passes, the recommendation is to keep S6 as it is and to keep the existing automated -25 % book-drawdown
halt of new orders (DESIGN 5). That halt is not tested here as a sell rule, because it does not sell.

## 6. Outputs
`protect.py` (simulator, grid, stats), `proxy2008.py` (FF proxy), `results.csv` (config x period), `gates.csv`,
`stress.csv`, `stops.csv`, `proxy.csv`, `NOTES.md` (tables and a plain-English recommendation). Scratch is under
the session scratchpad `s6p/` and is deleted at the end.

## Amendments (dated)
- **2026-10-14, after the first run (grid, gates and windows unchanged; N stays 121).**
  1. *Parity tolerance:* `daily_returns.parquet` stores float32, so 1e-9 is not attainable. Measured max abs
     difference vs the study's S6 N20 W = 5.7e-9/day (N50 W 6.7e-9). Accepted as parity.
  2. *Bug fix:* the B overlays' switching cost per unit of exposure was computed from dollar trades instead of
     equity-fraction trades (0.4 bps instead of 4.1 bps). The first run's gate counts were seen (0 passes) before
     the fix. Fixed and everything was re-run. Only B costs changed; the verdicts did not.
  3. *Proxy usage:* `proxy2008.py` takes S6's measured cost per traded dollar + 1 bps (5.05 bps) as its switching
     cost. Each proxy window is simulated from 2 years before its start, so trend and vol state is warm.
