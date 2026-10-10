# Longhold (2026-10-10): slow, documented strategies on daily bars, weekly / monthly rebalancing

*Educational only - not financial advice. Lab backtests on daily bars; nothing here is a live or paper result.*

Owner decision (2026-10-10): "Move to longer holding periods. This system's purpose is to find edge [and] to be an
efficient autonomous system in the market." Intraday setups showed no stock-specific edge after costs (~1.3M configs).
This study tests well-documented slow strategies whose turnover is small relative to the edge they are supposed to
have, and `DESIGN.md` specs the autonomous runner that would trade one.

**Section 1 (the pre-declaration) was written before any configuration was scored.** Before writing it I only read
the earlier studies (`research/swarm1010/w3_daily/NOTES.md`, `w2_neutral/NOTES.md`) and checked which symbols and
dates the data holds. Section 1 may change only by dated amendments in 1.9. Results are in section 2.

## 0. Data
- Stocks and most ETFs: `research/swarm1010/w3_daily/data/daily_2016.parquet` (W3 pull: Alpaca SIP 1Day, split and
  dividend adjusted, 2016-01-04..2026-10-09, 1,225 symbols, read-only, not copied). ETF tags from
  `research/swarm1010/w3_daily/assets_meta.csv`.
- Extra ETFs pulled for this study by `download_extra.py` -> `data/etf_extra.parquet` (git-ignored): RSP, MTUM, USMV,
  SPLV, QUAL, BIL, SHY, IEF, AGG, VTI (all 2,708 sessions). BIL is the cash leg (T-bills). RSP (equal-weight S&P 500,
  point-in-time membership) is the survivorship yardstick (1.7). MTUM/USMV/SPLV/QUAL are reference lines only.
- **Survivorship:** the stock universe is today's liquid list applied back to 2016. No symbol ends before 2026-10 (W3).
  Long-only stock results are biased upward, most in train (2016-2020). See 1.7 for how it is quantified.

## 1. Pre-declaration

### 1.1 Splits
| split | dates | use |
|---|---|---|
| warm-up | 2016-01-04 .. 2016-12-30 | features only (12-month lookbacks); no return is scored |
| train | 2017-01-01 .. 2020-12-31 | in-sample |
| valid | 2021-01-01 .. 2024-10-31 | choose finalists |
| LOCKED | 2024-11-01 .. 2025-02-28 | **not used.** Every daily return inside it is set to 0 before simulation (positions do not drift, nothing is earned or lost), and its days are dropped before any statistic. The lead scores finalists on it once |
| valid2 | 2025-03-01 .. 2026-10-09 | second validation (gate, never a ranking input) |

Features (12-month momentum, 52-week high, 252-day vol / beta) in 2025-03..2026-02 use prices from the locked block.
These are inputs, not outcomes (same convention as W3).

### 1.2 Mechanics (all configurations)
- **Signal** at the close of the rebalance day t: monthly = last trading day of the month; weekly = last trading day of
  the week. **Execution at the next session's open** (MOO). The portfolio earns the old weights from close t to open
  t+1 and the new weights from open t+1 on. Between rebalances weights drift with prices (no daily re-weighting).
- **Costs** per side on every traded dollar: `0.01 / open_price + 0.0001` (1c/share + 1 bps). Every rebalance trades
  only the difference between drifted and target weights (no band in the backtest; the band is a live-runner choice).
- **Shorts** (long-short variants): borrow 3 %/yr on the short gross, charged per calendar day held. 100 % long /
  100 % short of equity (dollar neutral), short proceeds earn nothing.
- **Cash:** stock strategies are always fully invested in their N names. ETF strategies and the vol-target overlay put
  the unused weight in **BIL** (traded with the same costs).
- Missing price on a held name: return 0 that day. A target name with no open on the execution day is skipped (its
  weight stays in cash at 0 return until the next rebalance).
- Returns are simple daily returns from adjusted prices; Sharpe uses rf = 0 (stated, so cash-heavy strategies are not
  flattered; BIL's return is reported for reference).

### 1.3 Universes
- **Stocks (point in time at t):** not ETF-tagged; close >= $5; 20-day median dollar volume >= $20M; >= 253 bars of
  history (so every stock family ranks the same names); the feature is defined.
- **E_risk** (9): SPY, QQQ, IWM, EFA, EEM, VNQ, TLT, IEF, GLD.
- **E_sector** (11): XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE, XLC (XLC joins once it has the lookback).

### 1.4 Grid (pre-declared; every row counts)
Stock long-only, top-N equal weight, N in {10, 20, 50}, rebalance in {M (monthly), W (weekly)}:
- **S1 momentum:** rank by `C[t-21]/C[t-252]-1` (12-1) or `C[t-21]/C[t-126]-1` (6-1). 2 x 3 x 2 = **12**
- **S2 residual momentum vs SPY:** beta from 252 daily log returns vs SPY (at t); score = (sum of the stock's log
  returns over the formation window - beta x SPY's over the same window) / residual sd (sqrt(var_r - beta^2 var_m),
  252 days). Formation 12-1 or 6-1. 2 x 3 x 2 = **12**
- **S3 52-week-high proximity (George-Hwang):** rank by `C[t] / max(H over the last 252 sessions)`, highest first.
  3 x 2 = **6**
- **S4 low volatility:** lowest sd of daily returns over 63 or 252 sessions. 2 x 3 x 2 = **12**
- **S5 low beta:** lowest 252-day beta vs SPY. 3 x 2 = **6**
- **S6 momentum with a short-term-reversal filter:** S1 12-1, after removing names in the top decile of the 21-day
  return (`C[t]/C[t-21]-1`) among eligible stocks. 3 x 2 = **6**

Stock long-short (top N long, bottom N short, equal weight, monthly only), N in {20, 50}:
- **L1** momentum 12-1 / 6-1 (4), **L2** residual momentum 12-1 / 6-1 (4), **L3** 52-week high (2), **L4** low vol
  252 (long lowest vol, short highest) (2), **L5** low beta (2). = **14**

ETFs (monthly):
- **E1 trend (Faber):** hold each asset whose month-end close > its n-month SMA of month-end closes, else BIL;
  1/n slots. n in {6, 10, 12} x universe {SPY alone, E_risk, E_sector}. = **9**
- **E2 dual momentum (Antonacci GEM):** pick the risk asset with the highest k-month return; hold it if that return
  beats BIL's over the same k months, else hold AGG. k in {6, 12} x risk set {(SPY, EFA), (SPY, QQQ, IWM, EFA)}. = **4**
- **E3 relative momentum with an absolute filter:** top 3 by k-month return, each slot held only if its return beats
  BIL's, else BIL. k in {3, 6, 12} x universe {E_risk, E_sector}. = **6**
- **E4 time-series momentum on E_risk:** asset held if its k-month return beats BIL's, else that weight goes to BIL.
  k in {3, 6, 12} x weighting {equal 1/9, inverse 63-day vol normalised over all 9}. = **6**
- **E5 risk parity-lite:** inverse 63-day vol weights, always invested, over E_risk, or over {SPY, TLT, GLD}. = **2**

Portfolio-level volatility targeting (overlay):
- **V:** exposure s = min(1, target / realised vol of the base strategy's daily net returns over the last 63
  sessions), set at each weekly signal and applied from the next session; the rest in BIL. Overlay trading cost:
  |delta s| x 2 bps on each change of s (approximation: 1 bps + 1c at a ~$100 average price). The base keeps its own
  costs (scaled by s). Bases: SPY buy-and-hold, EW stock universe (benchmark below), S1 12-1 N20 M, S3 N20 M,
  S4 vol252 N50 M. Target in {10 %, 15 %}. = **10**

**Total N = 54 + 14 + 27 + 10 = 105.** Try-count bar `t_required(105) = sqrt(2 ln 105) = 3.05`.

Benchmarks (not counted as configurations; same mechanics and costs): SPY buy-and-hold; **EW universe** (every
eligible stock, equal weight, monthly rebalance); E_risk equal weight and E_sector equal weight (monthly); RSP, MTUM,
USMV, QUAL buy-and-hold for reference.

### 1.5 Benchmark per family (for "active" and "Sharpe vs benchmark")
- S1-S6 -> EW universe (it carries the same survivorship bias, so the comparison is fair). SPY is also reported.
- L1-L5 -> cash (0): the active return is the strategy's own return.
- E1 SPY-alone, E2 -> SPY. E1/E3/E4/E5 on E_risk -> E_risk EW. E1/E3 on E_sector -> E_sector EW.
- V -> its own base strategy.

### 1.6 Statistics (per split, and train+valid pooled)
CAGR (geometric, from daily net returns), annual vol, Sharpe (rf 0), max drawdown (equity restarted at the split
start), turnover (one-way, per year: sum |delta w| / 2), cost drag (% per year), hit rate (share of months > 0, and
share of months beating the benchmark), excess vs SPY and vs EW universe (difference of annualised arithmetic means),
beta to SPY, active t (monthly active returns vs the family benchmark: mean / sd x sqrt(months)), per calendar year
return / SPY / active (2024 = Jan-Oct, 2025 = Mar-Dec), active return in SPY-up vs SPY-down months.
**Deflated Sharpe ratio** (Bailey & Lopez de Prado 2014) on train+valid daily returns with N = 105 trials and the
cross-trial variance of the daily Sharpe, for both the absolute return and the active return.

### 1.7 Survivorship (quantified two ways, diagnostics, not counted)
1. **Universe vs a point-in-time index:** CAGR of the EW universe minus RSP's (an equal-weight S&P 500 that keeps its
   delisted members). The gap is an upper-bound-ish estimate of what survivorship plus universe choice adds per year.
2. **Late-listing exclusion:** every stock long-only config rerun on the 2016 cohort only (names with a bar on
   2016-01-04, i.e. drop every name that listed later). Reported as a row variant `cohort2016`; if a result depends on
   names that IPO'd during the sample (all of which survived to today), it shows here.

### 1.8 Gates (pre-declared; verdicts)
**Tier A "edge candidate"** (all):
- A1 active return > 0 in train, valid and valid2.
- A2 monthly active t on train+valid >= 3.05 (t_required(105)).
- A3 plateau: mean active return (train+valid) of the grid neighbours (one parameter one step: N 10-20-50, M<->W,
  12-1<->6-1, vol window 63<->252, MA 6-10-12, k 3-6-12 / 6-12, target 10<->15, weighting, universe kept) > 0.
- A4 active > 0 in SPY-up months and in SPY-down months (train+valid+valid2 pooled).

**Tier B "risk improver"** (all; relevant for trend, low vol and vol targeting, which promise lower risk rather than
more return):
- B1 Sharpe > benchmark Sharpe in train, valid and valid2.
- B2 max drawdown over train+valid shallower than the benchmark's.
- B3 deflated Sharpe (absolute, N = 105) >= 0.95.
- B4 plateau: neighbours' mean (Sharpe - benchmark Sharpe) on train+valid > 0.

**near:** Sharpe > 0 in all three splits, and (active > 0 or Sharpe > benchmark Sharpe) in at least 2 of the 3.
**fail:** everything else.

Recommendation rule (fixed now): at most 3 configurations for a paper forward test, Tier A first, then Tier B,
ranked by train+valid only; no two from the same family/lineage unless no other qualifies. The lead scores each
once on the locked block 2024-11..2025-02 (look 1: active > 0 for Tier A; Sharpe > benchmark for Tier B).

### 1.9 Amendments (dated)
(none yet)
