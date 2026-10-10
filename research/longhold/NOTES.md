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
- **2026-10-10, after the first full scoring (gates unchanged, grid unchanged, N stays 105).** Two bug fixes before
  any number was read: benchmark keys `EW`/`SPY` were renamed to the simulated series `BENCH_EW`/`BH_SPY` (the first
  run crashed on the lookup), and the rolling covariance got `pairwise=False` explicitly.
- **2026-10-10, tightening diagnostics added after seeing the gates (they can only remove a candidate, never add
  one; written before running them; `diag.py`, not counted in N, reported as `diag_*` rows):**
  1. *Large-cap universe:* the same stock configs on the top 300 eligible names by 20-day median dollar volume at t.
     Large caps rarely disappear except by takeover, so this universe carries much less survivorship bias.
  2. *Corporate-action artifact filter:* drop from ranking any name with a daily close-to-close move > +300 % or
     < -75 % in the last 252 sessions (the file has spin-off / ticker-reuse artifacts such as SN 2023-07-31 x117,
     NVS 2019-04-09 -82 %).
  3. *2x costs* and *one-day execution delay* (signal at t, fill at the open of t+2).
  A recommendation must keep active > 0 in train, valid and valid2 under each of 1-3.

## 2. Results (105 configurations; failures first)

*Educational only - not financial advice. Backtest only (daily bars, MOO fills, costs in). The locked block
2024-11..2025-02 is in no figure. Annualised; "active" = strategy minus its family benchmark (1.5), arithmetic.*

**Counts.** 105 pre-declared configurations scored (N for every bar). Not counted, reported only: 9 benchmarks,
54 `cohort2016` reruns (1.7) and 4 x 54 tightening diagnostics (1.9, `diag.csv`). Try-count bar t >= 3.05.
SR0 for the deflated Sharpe (annualised): 0.93 absolute, 1.47 active.

| family (N) | A_edge | B_risk | near | fail |
|---|---|---|---|---|
| S1 momentum 12-1 / 6-1 (12) | 0 | 0 | 12 | 0 |
| S2 residual momentum (12) | 0 | 0 | 12 | 0 |
| S3 52-week high (6) | 0 | 0 | 1 | 5 |
| S4 low volatility (12) | 0 | 0 | 0 | 12 |
| S5 low beta (6) | 0 | 0 | 0 | 6 |
| S6 momentum + reversal filter (6) | **1** | 0 | 5 | 0 |
| L1-L5 long-short (14) | 0 | 0 | 8 | 6 |
| E1 Faber trend (9) | 0 | 0 | 7 | 2 |
| E2 dual momentum GEM (4) | 0 | 0 | 1 | 3 |
| E3 ETF relative momentum (6) | 0 | 0 | 4 | 2 |
| E4 ETF time-series momentum (6) | 0 | 0 | 6 | 0 |
| E5 risk parity-lite (2) | 0 | 0 | 1 | 1 |
| V vol targeting (10) | 0 | 0 | 5 | 5 |
| **total (105)** | **1** | **0** | **62** | **42** |

### 2.0 Benchmarks and survivorship (read first)
| series | CAGR train | valid | valid2 | 2017-2026 | note |
|---|---|---|---|---|---|
| SPY | 15.2 % | 13.1 % | 19.8 % | 15.1 % | Sharpe 0.83 / 0.83 / 1.13, maxDD -34 % |
| EW universe (today's list) | 17.8 % | 14.2 % | 26.5 % | 17.7 % | the stock benchmark |
| EW universe, 2016 cohort only | 16.7 % | 14.8 % | 23.0 % | 17.0 % | |
| RSP (EW S&P 500, point in time) | 11.6 % | 10.6 % | 13.0 % | 11.4 % | |
| MTUM / USMV / QUAL | | | | 16.4 / 10.1 / 14.6 % | reference |

- **Survivorship is large: the EW universe beats RSP by 6.3 %/yr** (17.7 vs 11.4 %), and by 13.5 %/yr in valid2. Part
  of that is universe choice (mid caps, growth names), but most of it is today's list applied backward. Every
  long-only stock number below is inflated by a comparable amount in absolute terms; the *active* numbers compare
  against the same biased universe, so they are less affected, but momentum is the style most exposed to this bias
  (it buys exactly the names that later became today's large, liquid stocks, and misses the ones that crashed out).
- The 2016-cohort rerun changes little (EW -0.7 %/yr; momentum active stays +10..+66 %/yr), so new listings are not
  what drives the results. The deaths that are missing cannot be tested with this file.

### 2.1 Failures
- **Low volatility (S4, 12) and low beta (S5, 6): all fail.** Active vs EW -3..-16 %/yr in train and valid and
  -12..-24 %/yr in valid2 (a strong-beta tape: low-vol names lagged). Sharpe below the EW universe in every split;
  drawdowns not smaller (-32..-41 %). USMV/SPLV show the same (valid2 +5.5 % / +0.1 %). Long-short versions (L4, L5)
  are disasters: -15..-81 %/yr, maxDD -86..-99 %.
- **52-week-high proximity (S3, 6): 5 fail, 1 near.** Active negative in train and valid in every version; weekly
  rebalancing churns 32-46x/yr (cost drag 1.8-2.6 %/yr). L3 long-short -0.5..-33 %/yr. Unlike W3's 20-day 52wh
  trades, nothing here beats the universe.
- **Dual momentum GEM (E2, 4): 3 fail, 1 near.** Active vs SPY -3..-12 %/yr in train and valid; switches late in
  2018/2020/2022.
- **Vol targeting (V, 10): 5 fail, 5 near.** On SPY and the EW universe it lowers return more than risk (Sharpe below
  base in train). On momentum it cuts max drawdown from -43 % to -15/-21 % and keeps Sharpe ~1.1, but gives up
  20-30 %/yr; B1 fails in train.
- **Faber trend (E1), ETF time-series momentum (E4), risk parity-lite (E5), ETF relative momentum (E3): no pass; the
  Tier-B misses are all on the deflated Sharpe.** Seven configs pass B1 (Sharpe > benchmark in all three splits), B2
  (shallower drawdown) and B4 (plateau) and fail only B3: E1_faber10_Erisk, E1_faber12_Erisk, E3_relmom3_top3_Erisk,
  E4_tsmom3_eq/iv, E4_tsmom6_iv, V_S4lv_vt10 (DSR 0.35-0.48 < 0.95). Example E1_faber10_Erisk: CAGR 8.1 / 4.9 / 13.3 %,
  maxDD -10 % (E_risk EW -26 %, SPY -34 %), Sharpe 1.16 / 0.67 / 1.31. They are risk reducers, not edge, and with
  105 trials their Sharpe is not distinguishable from luck. All are survivorship-free.
- **Residual momentum (S2, 12) and long-short momentum (L1/L2, 8): all near.** Positive active in every split
  (S2 +1..+12 %/yr in train/valid, up to +33 % in valid2; L1 +14..+50 %/yr) but t 0.7-2.2, below 3.05; deflated active Sharpe <= 0.01.
- **Plain momentum (S1, 12): all near.** Active vs EW +12..+39 %/yr in train and valid and +35..+88 %/yr in valid2,
  t 2.17-2.91 (just under the bar). Beta 1.3-2.2, vol 35-60 %, maxDD -41..-59 %.

### 2.2 The one Tier-A pass: `S6_mom12_1rev_N20_W`
Rule: weekly (last trading day of the week, signal at the close, fill at the next open), among eligible stocks
($5, $20M ADV, 253 bars, not ETF) drop the top decile of the 21-day return, then hold the 20 highest 12-1 month
returns at equal weight.

| split | CAGR | vol | Sharpe | maxDD | active vs EW | excess vs SPY | beta | turnover | cost drag | hit months / vs EW |
|---|---|---|---|---|---|---|---|---|---|---|
| train 2017-20 | 49.1 % | 33 % | 1.37 | -44 % | +26.8 % | +29.6 % | 1.30 | 15.8x | 1.3 % | 69 % / 69 % |
| valid 2021-24.10 | 39.5 % | 36 % | 1.10 | -27 % | +24.8 % | +26.1 % | 1.41 | 15.7x | 1.3 % | 59 % / 61 % |
| valid2 2025.03+ | 101.8 % | 56 % | 1.53 | -34 % | +60.9 % | +66.6 % | 2.15 | 16.1x | 1.2 % | 70 % / 65 % |

- Gates: A1 yes; A2 monthly active t 3.25 >= 3.05 (narrow); A3 neighbours' active +24 %/yr; A4 active in SPY-up
  months +32 %/yr and SPY-down months +29 %/yr (all open months). Calendar years vs EW: 9 of 10 positive (2021: +17 % vs +29 %);
  2018 +8.5 % (EW -4.9 %), 2022 +49 % (EW -13 %, energy names led the momentum list).
- Tightening diagnostics (1.9), active train / valid / valid2: top-300 large caps +17 / +10 / +58 %/yr (t 2.03);
  artifact filter +27 / +25 / +63 %; 2x costs +26 / +24 / +60 %; one-day delay +24 / +27 / +61 %. All positive.
- **Weak points:** deflated Sharpe of the active return is only 0.12 (N = 105); without the best 3 months the
  monthly active t is 2.3 / 1.0 / 0.4 (valid2 is carried by a few months, best 2026-04 +34 %); the top 10 names
  give 21 % of the summed contribution (CVNA, BE, ETSY, SHOP, SEDG, SE, QBTS ...), 485 names held over the sample.
  The monthly sibling `S6_mom12_1rev_N20_M` (t 2.98, turnover 6.8x) is "near"; the whole momentum cluster is
  consistent, so the result is not a single lucky cell, but its size is very likely overstated by survivorship.

## 3. Recommendation (rule fixed in 1.8)
1. **Paper forward test: `S6_mom12_1rev_N20_W`** (only Tier-A pass), after the lead scores it once on the locked
   block 2024-11..2025-02 (look 1: active vs EW universe > 0; the EW benchmark must be simulated on the same block).
   Expect 35-55 % vol and -30..-45 % drawdowns; treat the backtest CAGR as an upper bound (survivorship).
2. No Tier-B pass, so no second recommendation under the pre-declared rule. If the lead wants a survivorship-free
   **control line**, the closest Tier-B miss is `E1_faber10_Erisk` (or `E3_relmom3_top3_Erisk`); it must be
   labelled "near, failed B3 (deflated Sharpe)", not a pass.
3. Locked-block scoring needs the returns inside 2024-11..2025-02, which `study.py` zeroes unconditionally (line
   `R[locked] = 0.0`); the lead's scorer should rebuild `R_cc/R_co/R_oc` without that line, simulate the finalist and
   BENCH_EW from the 2024-10-31 targets, and report only 2024-11-01..2025-02-28.

## 4. Files
- `NOTES.md` (this), `DESIGN.md` (runner spec), `results.csv` (every config, benchmark and cohort rerun x
  train / valid / valid2 / trval / all / calendar year), `gates.csv` (one row per config, verdict and every gate),
  `diag.csv` (tightening diagnostics).
- `study.py` (grid, simulator, stats, gates), `diag.py` (diagnostics), `download_extra.py` (extra ETFs),
  `runner_core.py` + `tests/test_longhold_core.py` (pure core of the proposed runner).
- `data/` (git-ignored): `etf_extra.parquet`, `daily_returns.parquet`, `sim_cache.npz` (~13 MB in total).
