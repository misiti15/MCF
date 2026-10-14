# S6 crash protection, stops and breadth (2026-10-14)

*Educational only - not financial advice. These are backtests on daily bars (2017-2026, costs in, MOO fills).
Nothing here is a paper or live result. Nothing in `config/`, `mcf/` or the workflows was changed. The locked block
2024-11..2025-02 was **not** scored. Its returns are zeroed and its days are dropped from every number, as in the
study.*

Owner question (2026-10-14): would stops, profit-locks or a crash rule protect S6 against Covid, Ukraine or 2008-type
drawdowns without exiting on small pullbacks? And would 30 or 40 names be safer?
The pre-declared plan is `PLAN.md`, written before any scoring. Its two dated amendments are a parity tolerance and a
cost bug fixed and re-run.

## Short answer
- **0 of 121 configurations pass the pre-declared bar.** The bar: max drawdown cut by at least 5 points in both
  train and valid, CAGR within 3 points in both, Sharpe not lower in any split, better in 4 of 6 stress windows,
  plateau, and at least 60 % of years.
- **No rule earns an "improves Sharpe" claim.** The best block-bootstrap t is 1.82, against a bar of 3.32
  (lineage try count 251).
- **Recommendation: keep S6 as it is.** That means 20 names, equal weight, weekly, no stops, and the existing
  automated -25 % halt of new orders. Do not widen to 30 or 40 names.
- Every protection rule tested either costs more return than it saves in drawdown, or only helped in 2020.

## Counts and bars
- 121 configurations scored in this study:
  - A per-name stops: 96
  - B book-level overlays: 20
  - C breadth / sector cap: 5
- Lineage `lh-mom-revfilter`: 105 (study) + 7 (CWT S6 overlays) + 18 (sat1010 crash guards) + 121 = **251**.
  The bar is t >= sqrt(2 ln 251) = 3.32.
- Not repeated, because already tested and failed: SPY > SMA200 / SMA10 to cash, follow-through, two closes < SMA20,
  Kidd EMA, Keltner and the 20-week equity governor on S6 W (CWT), and 18 crash guards on the monthly sibling
  (sat1010). This study extends them with a BIL leg, a daily check with an overnight split, a 10-month Faber rule, a
  half-exposure rule, book drawdown stops with four re-entry rules, and vol targets of 20-40 % on 20-day vol.

| block | configs | G1 DD cut both | G2 CAGR kept | G3 Sharpe not lower | G4 stress 4/6 | G5 plateau | G6 years | pass |
|---|---|---|---|---|---|---|---|---|
| A per-name stops | 96 | 0 | 78 | 15 | 18 | 37 | 55 | **0** |
| B drawdown stop | 12 | 0 | 0 | 0 | 4 | 0 | 0 | **0** |
| B SPY trend | 4 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |
| B vol target | 4 | 1 | 0 | 0 | 0 | 0 | 0 | **0** |
| C breadth / cap | 5 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |

G3 passes in A all come from stops that almost never fire (profit-lock 50 %), so they are baseline copies.

## 1. Main table (failures and all; train 2017-20 / valid 2021-24.10 / valid2 2025.03+)
Columns:
- **DD**: max drawdown in %, equity restarted per split.
- **vol**: train+valid vol.
- **worst mo**: worst calendar month 2017-2026.
- **TO**: one-way turnover per year.
- **stops/yr**: stop exits per year across the 20-name book.
- **prem.**: premature-exit rate, the share of stop exits where the name's close 20 sessions later was above the
  exit fill.
- **t**: bootstrap t of the train+valid Sharpe difference vs baseline.
- **gates**: G1-G6, x = pass.

| config | CAGR % | Sharpe | DD % | vol | worst mo | TO | stops/yr | prem. | t | gates |
|---|---|---|---|---|---|---|---|---|---|---|
| **baseline S6 N20** | 49.1 / 39.5 / 101.8 | 1.37 / 1.10 / 1.53 | -44 / -27 / -34 | 35 | -22.4 | 15.7 | - | - | - | - |
| *A: fixed stop below entry, close-triggered, cash until rebalance* | | | | | | | | | | |
| `A_fix10_C_cash` | 53.3 / 38.6 / 77.4 | 1.59 / 1.14 / 1.41 | -33 / -29 / -35 | 32 | -31.2 | 19.3 | 106 | 58 % | 1.31 | .x.xxx |
| `A_fix10_C_repl` (best t) | 52.4 / 42.4 / 70.0 | 1.55 / 1.24 / 1.34 | -32 / -24 / -32 | 32 | -30.0 | 20.2 | 90 | 56 % | 1.82 | .x..xx |
| `A_fix15_C_cash` | 53.7 / 38.9 / 73.3 | 1.56 / 1.13 / 1.32 | -32 / -29 / -34 | 33 | -29.0 | 17.6 | 58 | 58 % | 1.30 | .x..x. |
| `A_fix20_C_cash` | 54.1 / 36.7 / 84.7 | 1.55 / 1.06 / 1.43 | -32 / -32 / -32 | 33 | -26.6 | 16.9 | 36 | 59 % | 0.92 | .x.xxx |
| `A_fix25_C_cash` | 52.6 / 38.6 / 90.7 | 1.50 / 1.10 / 1.47 | -36 / -27 / -33 | 33 | -23.7 | 16.4 | 22 | 60 % | 1.31 | .x.xxx |
| `A_fix30_C_cash` | 50.2 / 38.9 / 88.3 | 1.43 / 1.10 / 1.43 | -40 / -29 / -34 | 34 | -25.9 | 16.1 | 13 | 67 % | 1.15 | .x.xx. |
| *A: trailing stop from the position's high, close-triggered* | | | | | | | | | | |
| `A_trail10_C_cash` | 54.8 / 35.9 / 55.7 | 1.67 / 1.11 / 1.18 | -30 / -30 / -33 | 31 | -30.8 | 21.9 | 185 | 56 % | 1.35 | ...xx. |
| `A_trail15_C_cash` | 52.7 / 35.7 / 52.9 | 1.57 / 1.07 / 1.12 | -32 / -27 / -31 | 32 | -28.3 | 19.0 | 97 | 59 % | 0.92 | ....x. |
| `A_trail20_C_cash` | 56.3 / 37.7 / 82.0 | 1.61 / 1.09 / 1.43 | -32 / -30 / -29 | 33 | -26.8 | 17.5 | 53 | 56 % | 1.39 | .x.xxx |
| `A_trail25_C_cash` | 54.1 / 38.5 / 83.5 | 1.55 / 1.10 / 1.42 | -32 / -31 / -32 | 33 | -27.6 | 16.7 | 34 | 58 % | 1.20 | .x.xx. |
| *A: intraday-low trigger (resting stop, harsher)* | | | | | | | | | | |
| `A_fix20_L_cash` | 50.0 / 33.7 / 73.8 | 1.48 / 1.00 / 1.32 | -36 / -29 / -36 | 33 | -32.1 | 17.3 | 50 | 61 % | -0.02 | ....x. |
| `A_trail20_L_cash` | 50.0 / 32.1 / 71.1 | 1.50 / 0.98 / 1.31 | -36 / -29 / -33 | 32 | -32.0 | 18.3 | 80 | 60 % | -0.05 | ....x. |
| `A_trail10_L_cash` | 40.9 / 24.1 / 32.7 | 1.41 / 0.86 / 0.89 | -32 / -34 / -26 | 29 | -20.7 | 25.0 | 290 | 57 % | -0.81 | ...... |
| *A: profit-lock (stop only after the position is up P %)* | | | | | | | | | | |
| `A_lock20_trail10_C_cash` | 48.4 / 39.6 / 101.8 | 1.36 / 1.10 / 1.54 | -44 / -27 / -33 | 35 | -21.9 | 15.9 | 8 | 51 % | -0.20 | .x..xx |
| `A_lock30_be_C_cash` | 49.2 / 39.5 / 103.5 | 1.37 / 1.10 / 1.54 | -44 / -27 / -34 | 35 | -22.4 | 15.8 | 1 | 50 % | 0.81 | .xx.xx |
| `A_lock50_trail10_C_cash` | 49.1 / 39.5 / 101.8 | 1.37 / 1.10 / 1.53 | -44 / -27 / -34 | 35 | -22.4 | 15.7 | 0.3 | - | -0.63 | .x.... |
| *B: book drawdown stop -> BIL, re-entry rule* | | | | | | | | | | |
| `B_dd10_8w` | 27.0 / 3.9 / 35.9 | 1.21 / 0.28 / 1.20 | -24 / -36 / -18 | 24 | -18.0 | 12.5 | - | - | -1.65 | ...x.. |
| `B_dd15_8w` | 40.7 / 14.1 / 23.3 | 1.43 / 0.60 / 0.73 | -27 / -25 / -33 | 28 | -22.2 | 14.1 | - | - | -1.08 | ...x.. |
| `B_dd20_s50` | 42.6 / 37.5 / 53.8 | 1.48 / 1.07 / 1.13 | -22 / -26 / -39 | 31 | -33.6 | 15.7 | - | - | 0.05 | ...x.. |
| `B_dd20_s200` | 39.9 / 28.3 / 58.7 | 1.36 / 0.90 / 1.19 | -37 / -29 / -39 | 31 | -33.6 | 14.8 | - | - | -0.77 | ...... |
| *B: SPY trend filter -> BIL* | | | | | | | | | | |
| `B_trend_d200` (daily) | 32.6 / 20.0 / 52.8 | 1.26 / 0.74 / 1.12 | -31 / -32 / -34 | 28 | -27.7 | 15.4 | - | - | -1.20 | ...... |
| `B_trend_w200` (weekly) | 34.4 / 18.7 / 75.9 | 1.31 / 0.70 / 1.39 | -28 / -32 / -34 | 28 | -22.6 | 14.0 | - | - | -1.13 | ...... |
| `B_trend_m10` (Faber 10-month) | 33.4 / 18.7 / 43.9 | 1.26 / 0.70 / 0.96 | -31 / -30 / -34 | 29 | -22.6 | 13.6 | - | - | -1.28 | ...... |
| `B_trend_w200_half` (50 % below) | 42.2 / 29.8 / 91.5 | 1.43 / 0.97 / 1.52 | -29 / -28 / -34 | 30 | -22.6 | 14.9 | - | - | -0.50 | ...... |
| *B: volatility target, 20-day realised vol of S6, rest in BIL* | | | | | | | | | | |
| `B_vt20_20d` | 28.7 / 19.6 / 39.0 | 1.27 / 0.93 / 1.55 | -26 / -17 / -13 | 22 | -14.2 | 12.7 | - | - | -1.21 | x..... |
| `B_vt30_20d` | 35.5 / 30.6 / 60.1 | 1.25 / 1.03 / 1.59 | -36 / -24 / -17 | 29 | -21.4 | 15.0 | - | - | -1.10 | ...... |
| `B_vt40_20d` | 38.2 / 37.6 / 78.8 | 1.22 / 1.10 / 1.61 | -42 / -27 / -20 | 32 | -26.7 | 15.7 | - | - | -1.16 | ...... |
| `B_vt30_20d_daily` | 37.5 / 30.4 / 59.9 | 1.34 / 1.04 / 1.60 | -29 / -23 / -16 | 28 | -14.7 | 15.6 | - | - | -0.53 | ...... |

All 121 rows are in `gates.csv` / `results.csv`, and all 96 stop rows are in `stops.csv`. The rows not shown follow
the same pattern:
- `repl` (stopped name barred at the next rebalance) is about the same as `cash`.
- Every `L` (intraday) row is worse than its `C` (close) twin.
- `lock20/30/50` rows barely differ from the baseline.

### What the stop results mean
- **Close-based stops at 10-25 % look good in train, but almost all of that is 2020.** Train max DD falls from -44 %
  to about -32 % and train Sharpe rises from 1.37 to 1.5-1.67. That comes from the Covid crash: the crash leg was
  -22..-30 % vs -36 %, and the stopped names were replaced by new leaders for the rebound. Excluding 2020, the
  train+valid Sharpe is 1.16-1.26 vs the baseline's 1.16 (CAGR 35-39 % vs 38 %).
- In valid, the drawdown is **not** cut (-24..-32 % vs -27 %).
- In valid2 every stop **lowers** the Sharpe (1.12-1.47 vs 1.53) and CAGR (53-91 % vs 102 %). 2026 is 45-105 % vs
  110 %.
- **Premature exits are the norm.** Across every fixed and trailing stop, 56-67 % of stopped positions were higher
  20 sessions later. The median 20-session move after the exit is +2..+10 %. A 10 % trailing stop fires about 185
  times a year on a 20-name book (9 per name per year).
- **The wider the stop, the less it protects.** A 30 % fixed stop leaves the train drawdown at -40 %.
- So there is no stop percentage that "doesn't exit prematurely" and still protects: the tight ones churn, and the
  wide ones fire too late to matter.
- **Intraday-low (resting) stops are worse than close-based stops in every pair.** Gaps and intraday wicks sell at
  the low. The t ranges from -0.8 to 0.5.
- **Profit-locks do almost nothing.** Once a name is up 30-50 %, S6's own reversal filter (it drops the top decile
  of 1-month winners) and the weekly re-rank usually sell it before a lock would trigger. lock50 fires at most about
  once a year.
- Worst month gets **worse** with stops (-24..-31 % vs -22 %). After a stop, the replacements bought at the next
  rebalance can fall too.
- **Survivorship caveat (works against stops):** the universe is today's list run backward. Names that crashed and
  were delisted, where a stop would have saved money, are missing. Names that crashed and recovered are
  over-represented. Real stop value is somewhat better than shown, but there is no data here to say by how much.

### What the book-level overlays mean
- **Book drawdown stops are the worst idea tested.** Selling after a -10/-15/-20 % book drawdown sells near the low
  of momentum's frequent sharp dips. The rebound is then missed: valid CAGR is 4-38 % vs 39 %, and every valid Sharpe
  is lower.
- **SPY trend filters** (200-day, daily or weekly, Faber 10-month) protect best in real crashes. The Covid crash leg
  is -7 % vs -36 % and the 2008 proxy is -3..-6 % vs -56 % (section 3). But they cost 15-20 CAGR points in both
  train and valid, because S6 makes much of its money in choppy or bearish tapes. 2022: S6 +49 %, trend-filtered
  -8..-10 %; 2019 +74 % vs +18..27 %. This confirms CWT C8.
  - The half-exposure version costs 7 / 10 points.
- **Vol targeting** cuts drawdowns most evenly: vt20 gives -26 / -17 / -13 %, the only G1 pass. It also raises the
  valid2 Sharpe. But it gives up 10-60 CAGR points, and its Sharpe is lower in train and valid. It cuts leverage
  rather than adding protection.

## 2. Breadth (C): more names do not reduce S6's drawdowns, they reduce its returns

| config | weight / name | CAGR % (tr / v / v2) | Sharpe | max DD % | vol | TO | active vs EW-universe tr / v / v2 |
|---|---|---|---|---|---|---|---|
| **N20 (S6)** | 5.0 % | 49.1 / 39.5 / 101.8 | 1.37 / 1.10 / 1.53 | -44 / -27 / -34 | 35 | 15.7 | see study: +27 / +25 / +61 |
| N30 | 3.3 % | 44.6 / 34.3 / 90.9 | 1.34 / 1.05 / 1.50 | -42 / -26 / -34 | 32 | 14.6 | lower |
| N40 | 2.5 % | 39.8 / 28.4 / 92.8 | 1.28 / 0.96 / 1.58 | -41 / -24 / -34 | 30 | 13.8 | lower |
| N50 (study, ref) | 2.0 % | 39.2 / 25.3 / 73.5 | 1.31 / 0.91 / 1.41 | -41 / -23 / -34 | 29 | 13.4 | +16 / +12 / +34 |
| N20, max 3 / sector | 5.0 % | 24.8 / 32.4 / 74.0 | 0.90 / 1.07 / 1.54 | -47 / -27 / -28 | 30 | 17.8 | |
| N20, max 4 / sector | 5.0 % | 31.9 / 31.6 / 78.6 | 1.07 / 1.01 / 1.51 | -46 / -29 / -27 | 31 | 16.7 | |
| N20, max 5 / sector | 5.0 % | 38.5 / 26.9 / 88.4 | 1.21 / 0.88 / 1.56 | -44 / -30 / -28 | 32 | 16.5 | |

- Going from 20 to 40 names costs about 9-11 CAGR points in train and valid, and Sharpe falls in both. The maximum
  drawdown improves by only 3 points.
- The diversification is illusory in a crash. The extra names are the next-best momentum stocks, so they fall
  together: Covid crash N20 -36 %, N40 -36 %.
- In 2022 the extra names diluted the energy winners: N20 +49 %, N40 0 %.
- N40 has the best valid2 Sharpe (1.58), the only split where it wins.
- **Sector caps hurt.** Train CAGR drops 11-24 points, because they block the concentrated leadership (2017-19 metals
  and energy, 2020 tech) that S6 earns its return from.
  - Sector here is **statistical, not GICS**: the closest SPDR sector ETF by residual correlation, point in time. No
    GICS history is in the repo. It is reliable for energy, metals and semis and noisy for biotech and idiosyncratic
    names.
- Answer to "are we diverse enough?": 20 names at 5 % each is concentrated, by design. Concentration is where the
  return comes from. Crash risk in S6 comes from the momentum factor and the market, not from single names, and
  adding names does not remove it.

## 3. Stress windows (D)
Window return in %. All rows are backtest; the locked block is excluded.

| window | S6 | EW univ. | SPY | N40 | fix20 C | trail20 C | trail10 C | dd20 s50 | trend w200 | trend m10 | w200 half | vt20 | vt30 daily |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q4 2018 (10/01-12/24) | -31.0 | -19.7 | -18.9 | -29.2 | -30.9 | -29.6 | -30.0 | -20.5 | -26.7 | -30.2 | -28.6 | -18.8 | -26.7 |
| Covid crash (02/19-03/23/2020) | -35.8 | -39.3 | -33.5 | -35.9 | -26.1 | -25.2 | -22.0 | -16.4 | -7.2 | -7.2 | -22.2 | -22.2 | -25.1 |
| Covid crash + rebound (to 06/30) | +8.2 | -9.7 | -7.3 | +8.7 | +23.2 | +23.8 | +24.4 | -1.7 | +1.2 | +1.2 | +5.8 | -9.6 | -5.2 |
| Nov 2020 momentum reversal | +36.6 | +16.2 | +10.9 | +27.7 | +36.5 | +36.8 | +34.8 | +36.2 | +36.2 | +36.2 | +36.2 | +15.8 | +23.7 |
| 2022 H1 (rates / Ukraine, to 06/16) | +22.7 | -22.1 | -22.6 | -0.3 | +28.4 | +25.9 | +30.0 | +23.0 | -3.3 | -2.1 | +9.8 | +10.0 | +11.6 |
| 2022 full year | +49.4 | -13.2 | -18.2 | +18.9 | +55.1 | +51.8 | +52.4 | +36.8 | -10.1 | -7.5 | +18.1 | +18.8 | +26.7 |
| 2025 tariff (03/01-04/08) | -24.2 | -16.8 | -16.2 | -22.0 | -21.9 | -19.9 | -15.8 | -21.7 | -4.2 | -13.7 | -14.0 | -12.0 | -14.5 |
| Aug 2015 / early 2016 | not covered: the data starts 2016-01-04 and 2016 is the feature warm-up year | | | | | | | | | | | | |

- In this sample, S6's real danger windows were **Q4 2018, the Covid crash and the 2025 tariff selloff**. The
  Ukraine/rates year 2022 was S6's second-best relative year, because momentum rotated into energy. "Ukraine" was not
  a drawdown for S6.
- A momentum-reversal month like Nov 2020 did not hurt S6's weekly book. Its reversal filter and weekly re-rank
  rotated it.
- Q4 2018 is the window nothing fixed except vol targeting and the drawdown stop. It was a slide, not a crash, so
  stops fire late.

### 2008: not in the data; factor proxy (diagnostic only, not a gate)
The repo has no stock or ETF bars before 2016. The only long history is Ken French daily factors (1926..2026-08).
- Proxy: S6 ~ RF + 1.40 x (Mkt-RF) + 0.65 x Mom. This was fitted on train+valid (R^2 0.64; the fitted alpha of
  +20 %/yr is **left out**).
- Book overlays were replayed on it with the same code (`proxy2008.py`).
- It cannot test per-name stops or breadth.
- It is linear, so it likely **understates** how badly a real top-20 momentum book would have done in H2 2008, when
  commodity and energy leaders collapsed.

| window (proxy) | S6 proxy | dd15 8w | dd20 s200 | trend d200 | trend w200 | trend m10 | w200 half | vt20 | vt30 daily |
|---|---|---|---|---|---|---|---|---|---|
| GFC 2007-10-09..2009-03-09 | **-56.3** | -40.2 | -35.6 | -6.0 | -3.1 | +2.8 | -32.9 | -37.3 | -46.6 |
| 2009 momentum crash (03/09-05/29) | +1.7 | -0.7 | 0.0 | 0.0 | 0.0 | 0.0 | +1.1 | +0.1 | +0.6 |
| GFC full 2007-06..2010-12 | -22.3 | -13.2 | -1.4 | +12.6 | +26.5 | +38.5 | +2.9 | -2.2 | -5.6 |
| dot-com 2000-03..2003-03 | -41.9 | -37.1 | -29.7 | -35.3 | -29.2 | -29.6 | -34.2 | -33.4 | -39.4 |
| Aug 2015..Feb 2016 | -12.9 | -24.6 | -12.9 | -9.2 | -12.5 | -9.5 | -12.3 | -10.3 | -13.2 |
| 1990-2015: CAGR / Sharpe / max DD | 16.9 % / 0.75 / -58 % | 15.4 / 0.82 / -51 | 16.6 / 0.85 / -39 | 14.4 / 0.83 / -44 | 15.1 / 0.86 / -39 | 16.3 / 0.87 / -45 | 16.4 / 0.85 / -43 | 16.1 / 0.88 / -42 | 17.3 / 0.84 / -49 |

- On a zero-alpha proxy, a 2008-type bear market is where a SPY trend filter earns its keep: -56 % becomes about
  -5 %. Over 1990-2015 the trend rules and vt20 cut the proxy's max DD from -58 % to about -39..-45 % for about 1-2.5
  CAGR points.
- The real S6 is different. Its edge is earned largely while SPY is weak or choppy (2022, 2018-19), so in the actual
  2017-2026 data the same rules cost 15-20 points a year.
- **Both statements are true, and the trade-off is the owner's call.** Under the pre-declared bar, the trend filter
  fails.

## 4. Recommendation (fully automated rule set)
1. **Keep S6 unchanged:** 20 names, 5 % each, weekly MOO rebalance, no per-name stops, no profit-locks.
   - No stop level clears the bar. Stops fire on pullbacks that recover 56-67 % of the time, the intraday versions
     are worse, and the only big benefit was in one year (2020).
   - The weekly re-rank already acts as a slow stop: a name that falls out of the top 20 is sold within a week.
2. **Do not widen to 30-40 names and do not add a sector cap.** Both cost 4-24 CAGR points with no meaningful
   drawdown reduction.
3. **Keep the existing automated guard rails** (DESIGN 5, MANAGEMENT 2): -15 % warn and -25 % halt of new orders.
   These are not sell rules. Size S6 for a **-45 % peak-to-trough** (backtest train) and a possible -55..-60 % in a
   2008-type bear (proxy).
   - The automated "protection" that survives the test is **position size**: hold less of the account in S6 rather
     than adding a timing rule.
   - Vol targeting at 20-30 % is in effect an automated way to do that, but in this data it lowers the Sharpe in
     train and valid.
4. If the owner nevertheless wants a hard crash rule for a 2008 scenario, accepting about 7-10 CAGR points a year,
   the least damaging rule tested is `B_trend_w200_half`: 50 % S6 / 50 % BIL whenever SPY's weekly close is below
   its 200-day average.
   - It fails the bar (valid Sharpe 0.97 vs 1.10).
   - It needs its own backlog entry, its own locked look and a replay line before any live use (MANAGEMENT 3; rules
     9-11, 16).
5. Backlog suggestion for the lead (not written here): `lh-s6-stops-fail` and `lh-s6-bookguard-fail`, with these
   numbers. `A_fix10_C_repl` / `A_trail20_C_cash` could be tracked as a forward **replay line** only (t 1.8 / 1.4,
   far below 3.32).

## 5. Files
- `PLAN.md`: the pre-declaration, with dated amendments.
- `protect.py`: data block copied from `study.py`, a simulator with per-name stops (parity with the study's S6 N20 W
  to 5.7e-9/day, float32 reference), overlays, stats and gates.
- `proxy2008.py`: the FF factor proxy. It reuses `protect.overlay` via AST, not a copy.
- `results.csv`: config x period, including stress windows and calendar years.
- `gates.csv`: per config, G1-G6, the bootstrap t and neighbours.
- `stops.csv`: stops per year, premature rate and the return after the exit.
- `stress.csv`
- `proxy.csv`
- Run: `python research/longhold/protect1014/protect.py <scratch dir>` (about 45 s), then
  `python research/longhold/protect1014/proxy2008.py 0.000505`.
