# W2 market-neutral study (swarm 2026-10-10): hedged scoring of every setup + relative-value setups

*Educational only - not financial advice. Lab backtests on the open two-year history only; nothing here is a live or
paper result.*

Brief (lead, 2026-10-09): every setup tested so far is mostly market direction (longs win up sessions, shorts win down
sessions). Take the market out of the trade: (1) score every existing setup net of SPY / its sector ETF with a beta
from prior sessions only, costs on both legs; (2) basic pure relative-value intraday setups (stock vs SPY / sector,
pairs within a sector); (3) say what the live system needs for a hedged trade and a cheap first step.

**Section 1 (pre-declaration) was written before any hedged or relative-value trade was scored.** The only things seen
beforehand are earlier studies' published numbers (RESCORE.md, timeofday, regime1009, reddit NOTES). Section 1 may
change only by dated amendments.

## 1. Pre-declaration

### 1.1 Data (open history only)
- Lab frames and daily table via `research/history2y/lib.py`; `MCF_HIST_ALLOW_LOCKED` is never set (the rule-19 block
  2024-11-01..2025-02-28 is refused by the loader).
- 5-minute bars 09:35..15:55 (bar-close tod, as `mcf.research.heat`) rebuilt from `data/cache_hist/1Min` with
  `mcf.data.bars.resample` (the history2y pipeline). Locked-block rows are dropped right after each symbol's load,
  before any computation (as research/bdi/timeofday 0.6); only the 426 open sessions of `lib.daily()` are kept.
  Needed because the lab frames stop at 15:00 while the lab exits run to 15:55, and a hedge leg needs the ETF price at
  the stock's exit bar. Dense float32 arrays [symbol, session, bar] in `data/` (git-ignored).
- Integrity checks (declared): rebuilt close == frame close at the same (symbol, date, tod) for >= 99.9% of rows
  sampled; the re-simulated exit reproduces the frame's lab R (`r_{side}_{geom}`) for >= 99% of trades.
- Session regimes: `lib.regimes()` (universe median open-to-close terciles, open history).

### 1.2 Betas, sector map, pairs (prior sessions only)
- Returns: daily open-to-close (%) per symbol from `lib.daily()` (the intraday part of the day, which is what an
  intraday trade is exposed to).
- For session d, window = the previous 60 open sessions (min 30 with data); nothing from d or later. (The window can
  span the locked gap: 2025-03 sessions use 2024-10 sessions; no locked data is used.)
- **beta_SPY** = OLS slope of the stock's o2c on SPY's o2c in the window, clipped to [0, 3].
- **Sector ETF** = the candidate with the highest correlation of o2c in the window. Candidates (26, fixed now):
  XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE XLC SMH SOXX XBI IBB KRE KBE XRT XHB ITB GDX XOP OIH IGV XME JETS (self
  excluded). If the best correlation is < 0.30 the sector hedge falls back to SPY. **beta_SEC** = OLS slope on it,
  clipped to [0, 3].
- **Pair partner** = the non-ETF stock with the same sector ETF whose o2c correlation is highest, if >= 0.60;
  beta_PAIR = OLS slope on the partner, clipped to [0.2, 3].
- ETF list (never a primary leg of a new setup): the broad / sector / country / leveraged / commodity / crypto ETFs of
  the universe (`ETFS` in `common.py`).
- Trades whose beta is undefined (first ~30 open sessions: 2024-10 and early 2025-03) are dropped from BOTH the hedged
  and the unhedged line, so the two lines compare the same trades.

### 1.3 Hedged P/L (both legs' costs)
- Stock leg: unchanged lab trade (entry at the signal bar close, R = 0.25 x daily ATR, fixed geometry, timed exit by
  15:55), production R via `gates.prod_r` (1c + 1 bps per side, exit free on a target fill, +2c on stops).
- Hedge leg: opposite side, notional = beta x stock notional, entered at the ETF's 5-min close of the entry bar,
  exited at the ETF's close of the stock leg's exit bar (the stock exits intrabar at its target/stop; the hedge is
  priced at that bar's close - up to 5 minutes of mismatch, a known approximation). Hedge P/L in stock-R units:
  -side x beta x stock_px x (H_exit / H_entry - 1) / R. Hedge costs: market orders both sides,
  beta x stock_px x (0.01 / H_entry + 1e-4) per side, no target freebie, no stop extra.
- hedged R = stock production R + hedge P/L - hedge costs.

### 1.4 Task 1 - trade lists scored (no new fitting)
- 33 full-day lists: the 32 `research/bdi/fullday/*-FD.py` modules (30 from `research/bdi/timeofday/data/trades.parquet`
  set `full`; the 3 L3-*-FD regenerated with their FD modules, min_adv 0 as specs.json, first bar per symbol-day,
  09:50-15:00) + RW8 (its window already is 09:50-15:00; timeofday `full`).
- 30 current-window lists (timeofday set `current`) - secondary.
- 40 Reddit base rules (`research/bdi/reddit/strategies.py`: 20 strategies x long/short, no filter, t1s1, full day),
  regenerated with the Reddit engine exactly as `research/bdi/regime1009/gen_reddit.py` (run in row chunks to keep
  memory low; checked against the published n / exp of regime1009).
- 103 lists x 2 hedges (SPY, SEC) = **206 hedged configurations**; the unhedged line on the same trades is a reference.
- Per list and hedge: n, exp R, day-clustered t, ex-best-day, busiest session share, exp/n/t in up / flat / down
  sessions, walk-forward share (`gates.walk_forward`, locked months excluded), verdict vs the live-probation bar.
- t bar per list = max(2.0, sqrt(2 ln(N_lineage + 206))), N_lineage from the source studies: heat 19,200;
  exhaustion 855,600; MF 8,012; NS 7,374; RW1/3/5/7 82,068; RW4/6/6G1/8 81,430; RW2 934,522; ST 120,500;
  L3 11,178 (layering stage only - a lower bound); Reddit 2,551.

### 1.5 Task 2 - relative-value setups (lineage `sw-w2-rv`, new)
- Population: non-ETF symbols, adv20 >= 95M point in time, atr_d > 0, beta / map / partner defined for the session.
- Hedge instrument H by family: **F1 SPY**, **F2 SEC** (sector map 1.2), **F3 PAIR** (partner 1.2).
- Spread at bar close t: S_N(t) = ln(C_t / C_{t-N}) - beta x ln(H_t / H_{t-N}), both from the same session's 5-min
  closes (no signal if t-N is before the 09:35 bar).
- Scale: sigma_bar = mean over the previous 20 open sessions (min 10) of each session's std of 5-min residual
  returns e_b = ln(C_b/C_{b-1}) - beta_d ln(H_b/H_{b-1}) (bars 09:40..15:55, beta_d of that session). z = S_N /
  (sigma_bar x sqrt(N)).
- Rules: **fade** - long when z <= -k (laggard), short when z >= +k (leader); **momentum** - long when z >= +k, short
  when z <= -k. First qualifying bar per symbol-day per side, bar close 09:50..15:00.
- Grid: family {F1, F2, F3} x N {3, 6, 12} x k {1.5, 2.0, 2.5} x {fade, momentum} = 54 rules x 2 sides = 108
  side-configs. Exit: t1s1 on the stock leg, timed exit by 15:55, hedge leg closed at the same bar (1.3).
- Each side-config is scored hedged (the primary score) and single-leg (stock only, what a lab module could trade);
  each rule is also scored as a long+short book (both legs). **N = 108 x 2 + 54 x 2 = 324** -> t bar
  max(2.0, sqrt(2 ln 324)) = **3.40**.
- Plateau neighbours of a config: same family / direction / side / leg-variant with k +- 0.5 and N one step (in the grid).

### 1.6 Bar (RULES.md live-probation bar)
n >= 150; exp > 0 in up AND down sessions (n >= 30 each); day-clustered t >= the bar above; walk-forward positive share
>= 0.6; plateau neighbours' mean exp > 0 (task 2 only; task-1 setups are fixed rules); ex-best-day > 0; busiest session
<= 10% of trades. A single-leg config passing everything -> lab module + staged Testing YAML. A config passing only
hedged -> spec for two-leg execution, no module. Failures reported first.

## 2. Results (written after scoring; section 1 unchanged)

**Configurations: 530 scored in total.** Task 1 used 206 hedged configs (103 lists x {SPY, sector}); the unhedged line on
the same trades is a reference and is not counted. Task 2 (lineage `sw-w2-rv`) used 324. **0 of 530 pass the bar.**
No setup or exit was fitted. The locked block was never loaded and `MCF_HIST_ALLOW_LOCKED` was never set.

### 2.0 Failures and caveats first
- **No candidates.** No hedged list and no relative-value config passes. Every full-day list (0/33) and every Reddit
  rule (0/40) has negative hedged expectancy, and all 324 RV configs are negative. So no lab module and no Testing YAML
  is staged; section 3 gives the two-leg spec and a cheap report-only first step.
- **Hedging does what was asked, and that shows the edge was the market.** The mean |up - down| expectancy gap across
  lists falls as follows:

  | Lists | Unhedged | SPY hedge | Sector hedge |
  |---|---|---|---|
  | Full-day | 0.243R | 0.043R | 0.024R |
  | Current-window | 0.247R | 0.089R | 0.062R |
  | Reddit | 0.387R | 0.072R | 0.031R |

  What remains is each setup's stock-specific part, and it is negative.
- **Decomposition with the SPY hedge** (mean over trades with a beta):

  | Lists | Stock leg (prod R) | SPY move x beta | Hedge cost | Residual before hedge cost |
  |---|---|---|---|---|
  | Full-day | -0.043 | -0.001 | 0.028 | -0.044 |
  | Current-window | -0.015 | +0.001 | 0.029 | -0.015 |
  | Reddit | -0.083 | -0.004 | 0.029 | -0.086 |

  Across all trades the market term averages about 0. It only adds or subtracts within a regime. The hedge leg costs
  about 0.03R per trade with SPY and about 0.05R with the sector ETF (cheaper ETFs make 1c per share a larger cost, and
  sector betas are near 1). The median R is 0.76% of price.
- **The only positive hedged lines are windowed ST setups:**

  | Setup (window) | n | SPY-hedged exp | t | Up | Down |
  |---|---|---|---|---|---|
  | ST5-pdbrkup-short-mid-cur | 152 | +0.174 | 2.96 | +0.169 | +0.273 |
  | ST6-volspikeup-short-mid-cur | 215 | +0.110 | 1.87 | +0.153 | +0.030 |
  | ST7-rsi50dn-long-pm-cur | 159 | +0.080 | 1.41 | +0.088 | +0.081 |
  | ST3-rsi5up-short-pm-cur | 343 | +0.070 | 1.55 | +0.108 | +0.011 |
  | ST1-ordn-long-pm-cur | 365 | +0.036 | 1.13 | +0.086 | +0.046 |

  Each is below its t bar of 4.84 (stack1009 lineage, 120,500 configs). Their windows and layers were searched on
  this same history (timeofday NOTES), so they are in-sample. Their full-day versions are all negative hedged
  (-0.008 to -0.079R). This is not evidence of an edge. It is worth one note: when ST5 is hedged its down-session
  edge survives (+0.27R).
- **Approximations:**
  - The hedge exits at the 5-minute close of the stock's exit bar, while the stock exits intrabar. The mismatch is
    up to 5 minutes.
  - Betas use daily open-to-close returns. Intraday 5-minute betas could differ.
  - The first ~30 open sessions (2024-10 and early 2025-03) have no beta. They are dropped from both lines.
  - Pair partners can be less liquid than the primary leg, and the cost model does not charge for that.
  - Survivorship: as RESCORE.md (today's 1,226 names applied to the past).
- **Checks:**
  - Rebuilt 5-minute closes equal the frame closes on 600k sampled rows (100%).
  - The re-simulated exits reproduce the listed production R for 99.998% of 5,467,378 trades (`data/parity.json`).
  - The 40 Reddit lists equal regime1009's n and expectancy exactly.
- **Process:** a container restart killed the first scoring run after the per-trade file was written. Scoring was
  re-run from that file (`score_existing_results.py`), and nothing was re-generated or re-chosen. The task-1 build
  peaked at about 3.4 GB RSS while the trade table was assembled, which is above the 2.5 GB guideline. Every later
  step stayed under 1.7 GB.

### 2.1 Task 1 - hedged scoring (206 configurations; 0 pass)
- **Coverage:**
  - Sector map: a sector ETF for 93% of symbol-days, the SPY fallback (best correlation < 0.30) for 4.5%, undefined
    for 2%. The median best correlation is 0.63.
  - Most frequent sector ETFs: IGV 8.8%, XLI 8.3%, XLF / XLK 6.3%, SOXX 5.9%.
  - Median beta to SPY is 0.94. The mean beta of the trades is about 1.4 for the lab setups (high-beta names) and
    about 1.06 for the Reddit lists.
  - A pair partner (corr >= 0.6) exists on 65% of symbol-days.
- **Counts:**
  - Positive hedged expectancy: 11/103 lists with the SPY hedge and 6/103 with the sector hedge. All of them are
    current-window lists.
  - Positive in both up and down sessions: 6 lists (SPY) and 3 lists (sector). Every one of them fails the t bar.
- Per-list tables follow, sorted by sector-hedged expectancy, worst first. Exp is R after costs (both legs for hedged
  lines). t is day-clustered. `results.csv` (part = existing) has the full columns: flat sessions, walk-forward share,
  ex-best-day, busiest-session share, fails.

#### Full-day lists (33)

| list | n | unhedged exp (up / down) | SPY-hedged exp (up / down) | t | sector-hedged exp (up / down) | t |
|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup-FD | 10037 | -0.072 (-0.210 / +0.075) | -0.120 (-0.154 / -0.105) | -11.55 | -0.157 (-0.172 / -0.152) | -19.18 |
| MF5-flowsell-vwapup-rsi5hi-FD | 6495 | -0.049 (-0.276 / +0.177) | -0.090 (-0.144 / -0.070) | -5.32 | -0.145 (-0.173 / -0.139) | -12.31 |
| MF3-open-flowsell-rsi5hi-FD | 10027 | -0.070 (-0.276 / +0.104) | -0.103 (-0.140 / -0.088) | -7.95 | -0.135 (-0.159 / -0.124) | -14.19 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 5612 | -0.067 (-0.249 / +0.090) | -0.088 (-0.120 / -0.058) | -5.83 | -0.127 (-0.129 / -0.117) | -10.81 |
| NS1-rsidip-rsi5pop-long-FD | 2340 | -0.064 (+0.040 / -0.187) | -0.103 (-0.075 / -0.107) | -5.49 | -0.122 (-0.110 / -0.097) | -6.76 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 5243 | -0.053 (-0.278 / +0.139) | -0.091 (-0.160 / -0.053) | -5.76 | -0.119 (-0.148 / -0.121) | -9.45 |
| MF4-h40-open-flowsell-FD | 6877 | -0.078 (-0.223 / +0.021) | -0.094 (-0.105 / -0.084) | -7.50 | -0.110 (-0.127 / -0.099) | -11.15 |
| RW7-gapdn-bounce-early-short-FD | 24459 | -0.054 (-0.269 / +0.131) | -0.084 (-0.122 / -0.051) | -8.69 | -0.105 (-0.116 / -0.092) | -15.36 |
| exhaustion_short-FD | 26938 | -0.056 (-0.170 / +0.132) | -0.083 (-0.090 / -0.052) | -6.69 | -0.102 (-0.100 / -0.085) | -10.06 |
| L3-gap-slope-rsi5hi-FD | 5365 | -0.021 (-0.077 / +0.085) | -0.095 (-0.106 / -0.091) | -4.11 | -0.101 (-0.113 / -0.103) | -4.87 |
| RW1-gapdn-bounce-flowsell-short-FD | 6976 | -0.042 (-0.252 / +0.133) | -0.071 (-0.098 / -0.058) | -5.45 | -0.096 (-0.098 / -0.106) | -9.31 |
| RW2-exhaustion-noon-adv150-short-FD | 21049 | -0.054 (-0.163 / +0.136) | -0.078 (-0.079 / -0.048) | -6.11 | -0.095 (-0.092 / -0.074) | -8.88 |
| L3-gap-slope-lowdist-FD | 3926 | -0.097 (-0.246 / +0.186) | -0.106 (-0.071 / -0.166) | -3.19 | -0.094 (-0.077 / -0.131) | -4.26 |
| MF2-open-rsimidhi-flowsell-FD | 4295 | -0.052 (-0.122 / +0.045) | -0.091 (-0.073 / -0.069) | -6.89 | -0.093 (-0.063 / -0.084) | -8.76 |
| NS4-pm-vwap-reclaim-oversold-short-FD | 1632 | -0.056 (-0.162 / +0.108) | -0.062 (-0.080 / -0.031) | -3.18 | -0.089 (-0.094 / -0.080) | -5.40 |
| L3-gap-slope-fromopen-FD | 4579 | -0.029 (-0.107 / +0.170) | -0.079 (-0.094 / -0.022) | -3.47 | -0.086 (-0.089 / -0.066) | -3.63 |
| NS2-sma50break-overbought-short-FD | 7793 | -0.050 (-0.154 / +0.123) | -0.090 (-0.096 / -0.062) | -4.62 | -0.082 (-0.069 / -0.081) | -4.96 |
| RW6G1-ns2-up3-vwap2sd-short-FD | 1867 | -0.001 (-0.007 / +0.010) | -0.083 (-0.064 / -0.122) | -2.92 | -0.081 (-0.064 / -0.093) | -3.35 |
| ST5-pdbrkup-short-mid-t05s1-FD | 407 | -0.050 (-0.066 / -0.005) | -0.018 (-0.002 / +0.021) | -0.37 | -0.079 (-0.090 / -0.083) | -2.29 |
| NS5-sma50-flush-oversold-long-FD | 3027 | -0.043 (+0.051 / -0.146) | -0.050 (-0.087 / -0.043) | -2.43 | -0.077 (-0.108 / -0.081) | -4.69 |
| ST2-slope20up-long-am-t05s1-FD | 10438 | -0.014 (+0.026 / -0.066) | -0.050 (-0.071 / -0.043) | -4.87 | -0.074 (-0.087 / -0.070) | -9.84 |
| RW8-sma50up-spikefade-short-FD | 439 | -0.102 (-0.243 / -0.032) | -0.057 (-0.089 / -0.134) | -1.32 | -0.074 (-0.094 / -0.169) | -2.00 |
| RW6-ns2-up3-short-FD | 3452 | -0.014 (-0.076 / +0.107) | -0.079 (-0.077 / -0.062) | -3.63 | -0.069 (-0.056 / -0.066) | -3.89 |
| heat_fade_short-FD | 71374 | -0.033 (-0.226 / +0.132) | -0.053 (-0.078 / -0.038) | -7.36 | -0.069 (-0.073 / -0.071) | -15.86 |
| ST1-ordn-long-pm-t05s1-FD | 1504 | -0.045 (+0.020 / -0.063) | -0.069 (-0.067 / -0.054) | -3.30 | -0.067 (-0.086 / -0.058) | -3.80 |
| NS3-failed-vwap-reclaim-short-FD | 9659 | -0.023 (-0.149 / +0.089) | -0.068 (-0.075 / -0.048) | -3.93 | -0.064 (-0.070 / -0.064) | -6.45 |
| RW4-ns3-adv150-short-FD | 7647 | -0.023 (-0.142 / +0.090) | -0.069 (-0.067 / -0.050) | -3.70 | -0.060 (-0.060 / -0.067) | -5.69 |
| heat_fade_long-FD | 22565 | -0.028 (+0.110 / -0.131) | -0.044 (-0.046 / -0.043) | -4.07 | -0.057 (-0.077 / -0.051) | -7.75 |
| ST4-emadn-long-am-t1s05-FD | 1243 | +0.032 (+0.146 / -0.024) | -0.010 (+0.019 / -0.026) | -0.45 | -0.052 (-0.018 / -0.067) | -2.90 |
| ST8-volspikedn-long-pm-t1s1-FD | 504 | +0.050 (+0.058 / -0.038) | -0.005 (+0.003 / -0.062) | -0.11 | -0.048 (-0.077 / -0.069) | -1.62 |
| ST3-rsi5up-short-pm-t1s1-FD | 628 | +0.002 (-0.092 / +0.004) | -0.016 (-0.031 / -0.070) | -0.39 | -0.037 (-0.020 / -0.095) | -1.05 |
| ST7-rsi50dn-long-pm-t1s1-FD | 998 | +0.041 (+0.224 / -0.045) | -0.032 (+0.022 / -0.045) | -0.94 | -0.034 (-0.001 / -0.022) | -1.19 |
| ST6-volspikeup-short-mid-t1s1-FD | 589 | +0.013 (-0.074 / +0.070) | -0.008 (-0.029 / +0.025) | -0.22 | -0.028 (-0.056 / -0.008) | -0.89 |

#### Current-window lists (30)

| list | n | unhedged exp (up / down) | SPY-hedged exp (up / down) | t | sector-hedged exp (up / down) | t |
|---|---|---|---|---|---|---|
| MF3-open-flowsell-rsi5hi-cur | 3960 | -0.072 (-0.293 / +0.157) | -0.095 (-0.136 / -0.080) | -4.03 | -0.155 (-0.168 / -0.154) | -9.16 |
| MF5-flowsell-vwapup-rsi5hi-cur | 6495 | -0.049 (-0.276 / +0.177) | -0.090 (-0.144 / -0.070) | -5.32 | -0.145 (-0.173 / -0.139) | -12.31 |
| MF1-945-flowsell-vwapup-cur | 2272 | -0.057 (-0.236 / +0.072) | -0.118 (-0.164 / -0.120) | -4.59 | -0.145 (-0.152 / -0.153) | -6.17 |
| RW3-gapdn-rsi5pop-flowsell-short-cur | 1708 | -0.047 (-0.303 / +0.198) | -0.058 (-0.164 / +0.015) | -1.94 | -0.142 (-0.188 / -0.120) | -5.55 |
| RW7-gapdn-bounce-early-short-cur | 1474 | -0.034 (-0.267 / +0.227) | -0.062 (-0.138 / +0.000) | -2.20 | -0.134 (-0.142 / -0.124) | -6.01 |
| NS1-rsidip-rsi5pop-long-cur | 427 | +0.045 (+0.105 / +0.007) | -0.071 (-0.178 / +0.049) | -1.08 | -0.122 (-0.260 / -0.002) | -1.78 |
| MF4-h40-open-flowsell-cur | 3147 | -0.090 (-0.251 / +0.036) | -0.083 (-0.082 / -0.086) | -3.71 | -0.117 (-0.122 / -0.115) | -6.75 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-cur | 1227 | -0.011 (-0.269 / +0.276) | -0.046 (-0.160 / +0.074) | -1.29 | -0.116 (-0.154 / -0.155) | -3.90 |
| NS4-pm-vwap-reclaim-oversold-short-cur | 1416 | -0.068 (-0.175 / +0.121) | -0.069 (-0.091 / -0.015) | -3.22 | -0.095 (-0.104 / -0.062) | -5.33 |
| RW1-gapdn-bounce-flowsell-short-cur | 2328 | -0.006 (-0.259 / +0.255) | -0.022 (-0.086 / +0.028) | -0.98 | -0.080 (-0.099 / -0.071) | -4.02 |
| MF2-open-rsimidhi-flowsell-cur | 576 | -0.037 (-0.091 / -0.031) | -0.067 (-0.030 / -0.127) | -2.01 | -0.075 (-0.025 / -0.131) | -2.62 |
| RW8-sma50up-spikefade-short-cur | 439 | -0.102 (-0.243 / -0.032) | -0.057 (-0.089 / -0.134) | -1.32 | -0.074 (-0.094 / -0.169) | -2.00 |
| RW2-exhaustion-noon-adv150-short-cur | 7231 | +0.007 (-0.065 / +0.145) | -0.055 (-0.060 / -0.037) | -3.82 | -0.069 (-0.071 / -0.053) | -5.84 |
| exhaustion_short-cur | 5393 | +0.014 (-0.056 / +0.180) | -0.054 (-0.070 / -0.016) | -3.22 | -0.065 (-0.085 / -0.032) | -5.09 |
| NS2-sma50break-overbought-short-cur | 3006 | +0.004 (-0.056 / +0.161) | -0.076 (-0.072 / -0.067) | -2.66 | -0.061 (-0.038 / -0.085) | -2.79 |
| heat_fade_long-cur | 13838 | -0.043 (+0.066 / -0.139) | -0.032 (-0.084 / -0.026) | -2.39 | -0.058 (-0.104 / -0.052) | -5.96 |
| RW6-ns2-up3-short-cur | 1405 | +0.056 (+0.032 / +0.173) | -0.055 (-0.039 / -0.041) | -1.61 | -0.045 (-0.021 / -0.046) | -1.59 |
| ST7-rsi50dn-long-pm-t1s1-cur | 159 | +0.179 (+0.194 / +0.229) | +0.080 (+0.088 / +0.081) | 1.41 | -0.040 (-0.021 / -0.016) | -0.79 |
| heat_fade_short-cur | 13853 | +0.009 (-0.202 / +0.145) | +0.001 (-0.024 / +0.003) | 0.07 | -0.036 (-0.034 / -0.057) | -4.11 |
| NS5-sma50-flush-oversold-long-cur | 1258 | -0.040 (+0.091 / -0.212) | +0.013 (-0.063 / +0.014) | 0.39 | -0.028 (-0.101 / -0.041) | -0.95 |
| RW4-ns3-adv150-short-cur | 1168 | +0.047 (-0.110 / +0.231) | -0.022 (-0.008 / +0.052) | -0.52 | -0.027 (-0.001 / -0.027) | -0.95 |
| ST8-volspikedn-long-pm-t1s1-cur | 390 | +0.110 (+0.109 / +0.008) | +0.048 (+0.071 / -0.015) | 1.05 | -0.026 (-0.010 / -0.067) | -0.86 |
| ST2-slope20up-long-am-t05s1-cur | 156 | +0.131 (+0.070 / +0.106) | +0.062 (-0.058 / +0.122) | 1.09 | -0.024 (-0.059 / -0.015) | -0.52 |
| NS3-failed-vwap-reclaim-short-cur | 1453 | +0.049 (-0.093 / +0.237) | -0.012 (+0.011 / +0.061) | -0.30 | -0.023 (+0.020 / -0.024) | -0.82 |
| RW6G1-ns2-up3-vwap2sd-short-cur | 406 | +0.267 (+0.317 / +0.136) | +0.014 (+0.034 / -0.025) | 0.31 | +0.007 (+0.017 / +0.025) | 0.18 |
| ST1-ordn-long-pm-t05s1-cur | 365 | +0.102 (+0.187 / +0.113) | +0.036 (+0.086 / +0.046) | 1.13 | +0.008 (+0.078 / +0.001) | 0.32 |
| ST4-emadn-long-am-t1s05-cur | 158 | +0.172 (+0.405 / +0.098) | +0.075 (+0.292 / -0.034) | 0.96 | +0.030 (+0.245 / -0.100) | 0.47 |
| ST3-rsi5up-short-pm-t1s1-cur | 343 | +0.099 (+0.069 / +0.074) | +0.070 (+0.108 / +0.011) | 1.55 | +0.033 (+0.095 / -0.046) | 0.86 |
| ST5-pdbrkup-short-mid-t05s1-cur | 152 | +0.118 (+0.114 / +0.182) | +0.174 (+0.169 / +0.273) | 2.96 | +0.053 (+0.129 / +0.059) | 1.36 |
| ST6-volspikeup-short-mid-t1s1-cur | 215 | +0.108 (+0.033 / +0.096) | +0.110 (+0.153 / +0.030) | 1.87 | +0.079 (+0.111 / -0.002) | 1.39 |

#### Reddit base rules (40)

| list | n | unhedged exp (up / down) | SPY-hedged exp (up / down) | t | sector-hedged exp (up / down) | t |
|---|---|---|---|---|---|---|
| RDT-R03-vwap-fade-short | 2477 | -0.194 (-0.270 / -0.000) | -0.291 (-0.374 / -0.111) | -2.04 | -0.327 (-0.409 / -0.142) | -2.25 |
| RDT-R03-vwap-fade-long | 2273 | -0.098 (+0.000 / -0.178) | -0.139 (-0.072 / -0.200) | -4.99 | -0.163 (-0.145 / -0.214) | -6.36 |
| RDT-R15-sweep-long | 58903 | -0.105 (+0.115 / -0.260) | -0.129 (-0.085 / -0.155) | -15.75 | -0.161 (-0.147 / -0.180) | -28.28 |
| RDT-R07-hod-break-long | 105036 | -0.089 (+0.081 / -0.335) | -0.138 (-0.110 / -0.171) | -17.12 | -0.160 (-0.151 / -0.174) | -27.00 |
| RDT-R16-rel-strength-long | 38605 | -0.114 (+0.074 / -0.215) | -0.127 (-0.087 / -0.155) | -7.36 | -0.160 (-0.162 / -0.164) | -15.91 |
| RDT-R12-rsi-div-long | 227562 | -0.097 (+0.100 / -0.271) | -0.125 (-0.083 / -0.162) | -21.34 | -0.159 (-0.153 / -0.173) | -46.60 |
| RDT-R20-sma-macd-long | 217068 | -0.090 (+0.084 / -0.297) | -0.131 (-0.097 / -0.166) | -21.65 | -0.157 (-0.148 / -0.166) | -47.70 |
| RDT-R08-bull-flag-short | 33412 | -0.091 (-0.288 / +0.014) | -0.128 (-0.142 / -0.125) | -12.42 | -0.155 (-0.162 / -0.161) | -21.14 |
| RDT-R08-bull-flag-long | 34532 | -0.081 (+0.086 / -0.353) | -0.120 (-0.069 / -0.203) | -8.01 | -0.155 (-0.123 / -0.199) | -11.94 |
| RDT-R17-pd-retest-long | 117876 | -0.084 (+0.108 / -0.290) | -0.124 (-0.091 / -0.150) | -15.84 | -0.153 (-0.144 / -0.156) | -35.46 |
| RDT-R01-orb30-long | 185950 | -0.075 (+0.130 / -0.320) | -0.130 (-0.094 / -0.164) | -16.11 | -0.152 (-0.138 / -0.164) | -33.65 |
| RDT-R09-ema20-pullback-long | 277869 | -0.087 (+0.111 / -0.295) | -0.126 (-0.089 / -0.161) | -22.03 | -0.152 (-0.144 / -0.163) | -43.39 |
| RDT-R11-rsi-os-long | 114684 | -0.086 (+0.082 / -0.273) | -0.121 (-0.094 / -0.147) | -15.65 | -0.152 (-0.148 / -0.160) | -33.82 |
| RDT-R02-vwap-reclaim-long | 209835 | -0.077 (+0.138 / -0.283) | -0.114 (-0.081 / -0.142) | -17.34 | -0.151 (-0.143 / -0.162) | -40.46 |
| RDT-R10-ema-cross-long | 278669 | -0.085 (+0.116 / -0.285) | -0.113 (-0.071 / -0.146) | -18.88 | -0.148 (-0.135 / -0.158) | -42.31 |
| RDT-R13-macd-zero-long | 235925 | -0.083 (+0.115 / -0.288) | -0.111 (-0.068 / -0.146) | -17.88 | -0.148 (-0.136 / -0.157) | -40.55 |
| RDT-R07-hod-break-short | 100442 | -0.088 (-0.297 / +0.065) | -0.120 (-0.141 / -0.098) | -16.87 | -0.147 (-0.148 / -0.137) | -31.60 |
| RDT-R15-sweep-short | 52100 | -0.114 (-0.283 / +0.095) | -0.111 (-0.136 / -0.082) | -7.96 | -0.146 (-0.139 / -0.160) | -13.21 |
| RDT-R16-rel-strength-short | 34325 | -0.089 (-0.142 / +0.014) | -0.109 (-0.109 / -0.136) | -9.70 | -0.145 (-0.126 / -0.207) | -18.48 |
| RDT-R19-orb-fib-long | 94379 | -0.079 (+0.152 / -0.319) | -0.116 (-0.071 / -0.161) | -13.97 | -0.144 (-0.123 / -0.166) | -24.76 |
| RDT-R12-rsi-div-short | 238157 | -0.088 (-0.274 / +0.115) | -0.108 (-0.143 / -0.075) | -18.08 | -0.143 (-0.155 / -0.130) | -40.63 |
| RDT-R01-orb30-short | 179614 | -0.082 (-0.325 / +0.104) | -0.115 (-0.149 / -0.083) | -15.20 | -0.142 (-0.143 / -0.128) | -32.94 |
| RDT-R14-ict-fvg-long | 94789 | -0.059 (+0.123 / -0.251) | -0.113 (-0.072 / -0.155) | -13.66 | -0.142 (-0.129 / -0.156) | -27.75 |
| RDT-R18-orb-fvg-short | 57470 | -0.081 (-0.295 / +0.095) | -0.122 (-0.160 / -0.078) | -14.15 | -0.142 (-0.148 / -0.115) | -26.56 |
| RDT-R02-vwap-reclaim-short | 213406 | -0.077 (-0.303 / +0.142) | -0.107 (-0.151 / -0.068) | -16.66 | -0.139 (-0.153 / -0.126) | -39.80 |
| RDT-R20-sma-macd-short | 209982 | -0.082 (-0.299 / +0.106) | -0.113 (-0.153 / -0.079) | -18.98 | -0.139 (-0.149 / -0.125) | -38.30 |
| RDT-R11-rsi-os-short | 111159 | -0.088 (-0.300 / +0.115) | -0.112 (-0.150 / -0.071) | -14.64 | -0.137 (-0.152 / -0.124) | -30.11 |
| RDT-R14-ict-fvg-short | 95696 | -0.068 (-0.244 / +0.103) | -0.112 (-0.142 / -0.072) | -14.98 | -0.137 (-0.139 / -0.117) | -31.39 |
| RDT-R09-ema20-pullback-short | 271568 | -0.085 (-0.291 / +0.108) | -0.111 (-0.148 / -0.075) | -19.63 | -0.136 (-0.145 / -0.123) | -42.50 |
| RDT-R19-orb-fib-short | 94102 | -0.097 (-0.330 / +0.119) | -0.116 (-0.150 / -0.089) | -14.69 | -0.135 (-0.141 / -0.119) | -26.68 |
| RDT-R05-gap-fill-long | 11185 | -0.018 (+0.253 / -0.306) | -0.112 (-0.075 / -0.136) | -4.81 | -0.135 (-0.120 / -0.142) | -8.35 |
| RDT-R06-red-green-long | 33692 | -0.068 (+0.106 / -0.326) | -0.105 (-0.077 / -0.144) | -7.44 | -0.135 (-0.127 / -0.140) | -10.49 |
| RDT-R13-macd-zero-short | 236629 | -0.077 (-0.274 / +0.119) | -0.105 (-0.138 / -0.071) | -17.02 | -0.134 (-0.137 / -0.123) | -39.61 |
| RDT-R18-orb-fvg-long | 55786 | -0.060 (+0.120 / -0.277) | -0.107 (-0.056 / -0.155) | -10.69 | -0.133 (-0.107 / -0.155) | -20.38 |
| RDT-R10-ema-cross-short | 279551 | -0.075 (-0.270 / +0.122) | -0.104 (-0.135 / -0.070) | -17.35 | -0.133 (-0.136 / -0.124) | -42.15 |
| RDT-R17-pd-retest-short | 111083 | -0.082 (-0.322 / +0.117) | -0.102 (-0.153 / -0.059) | -13.45 | -0.133 (-0.146 / -0.118) | -28.43 |
| RDT-R06-red-green-short | 35980 | -0.073 (-0.265 / +0.054) | -0.113 (-0.124 / -0.111) | -11.58 | -0.132 (-0.124 / -0.144) | -22.07 |
| RDT-R04-gap-go-long | 12151 | -0.081 (+0.054 / -0.286) | -0.120 (-0.133 / -0.141) | -6.65 | -0.110 (-0.110 / -0.138) | -7.82 |
| RDT-R04-gap-go-short | 11248 | -0.026 (-0.316 / +0.179) | -0.091 (-0.145 / -0.067) | -3.99 | -0.092 (-0.083 / -0.089) | -6.59 |
| RDT-R05-gap-fill-short | 12114 | -0.010 (-0.247 / +0.195) | -0.050 (-0.057 / -0.029) | -3.10 | -0.088 (-0.096 / -0.072) | -8.73 |

### 2.2 Task 2 - relative-value setups (lineage `sw-w2-rv`, N = 324, t bar 3.40; 0 pass)
Mean and best expectancy (R after costs) over the 27 side-configs or 9 books of each cell:

| Family | Direction | Hedged (two legs) mean / best | Single leg mean / best | Hedged books mean / best |
|---|---|---|---|---|
| SPY | fade | -0.101 / -0.088 | -0.075 / -0.068 | -0.101 / -0.097 |
| SPY | momentum | -0.116 / -0.099 | -0.085 / -0.073 | -0.116 / -0.112 |
| Sector ETF | fade | -0.127 / -0.117 | -0.072 / -0.064 | -0.127 / -0.122 |
| Sector ETF | momentum | -0.151 / -0.141 | -0.089 / -0.081 | -0.152 / -0.148 |
| Pair | fade | -0.104 / -0.091 | -0.063 / -0.054 | -0.104 / -0.094 |
| Pair | momentum | -0.172 / -0.159 | -0.092 / -0.080 | -0.172 / -0.164 |

- **Fade beats momentum everywhere,** so there is some residual mean reversion. It stays well below the costs of one
  leg, let alone two.
- **The hedged RV trades are regime-neutral, as designed** (mean |up - down| 0.036R). The single-leg versions are
  market direction again (0.27R). For example, PAIR N12 k2 fade short single-leg makes +0.158R in down sessions and
  -0.250R in up sessions.
- The best hedged config (SPY N3 k2.5 fade short) is -0.088R with t -9.1. The best single-leg config (PAIR N3 k2.5
  fade long) is -0.055R.
- **Trade counts are high:** 25k to 275k per side-config, about 60 to 650 per session. A relative-value trigger fires
  on most liquid names every day, and per-trade costs dominate.
- Per-config rows are in `results.csv` (part = rv). They include plateau, walk-forward and fails.

## 3. What the live system would need for a hedged trade (spec; nothing built)

No hedged configuration meets the bar, so this is a specification for later, not a proposal.

### 3.1 Two-leg execution
1. **Signal carries the hedge.** At signal time (bar close), attach `hedge_symbol` (SPY, or the sector ETF from the
   prior-60-session correlation map) and `beta` (prior-session OLS on daily open-to-close, clipped to [0, 3]). Both
   come from a nightly job that writes `data/hedge_map.parquet` (symbol -> etf, beta, corr). The job runs before the
   open and is never recomputed intraday.
2. **Sizing.**
   - Stock leg: as today (`RiskManager.size`, risk per trade / (0.25 ATR)).
   - Hedge quantity: q_h = round(beta x q_stock x P_stock / P_etf), opposite side.
   - The risk budget must include the hedge. The hedged position's risk is the residual volatility, but the stop is
     still on the stock.
   - `slot_notional` / buying-power checks must count both legs (about 2x gross notional at beta 1).
3. **Orders.**
   - Stock: the existing bracket (`submit_bracket`).
   - Hedge: a plain market order (or a marketable limit) sent right after the stock entry fills. It must not be
     triggered by the signal alone, so that the hedge never sits unpaired.
   - Close the hedge when the stock leg's target or stop fills (fill-event listener / `reconcile.py`), and at the
     15:55 flatten.
   - Client order ids share a prefix with the parent so `orders_today_with_prefix` / `cancel_orders_with_prefix` pick
     them up.
4. **Netting (cheaper, recommended over per-trade orders).** The account holds ONE net position per hedge ETF, equal
   to -sum(beta_i x notional_i x side_i). It is re-balanced only when the drift exceeds a band (for example $5k or
   10%), and at most once per bar. Long and short trades offset each other, which cuts hedge turnover and cost. The
   journal attributes the hedge P/L to each trade by beta x the ETF return over that trade's holding time.
   - Note: the `RiskManager.check` rule "already in symbol" and the per-strategy position caps must exempt the hedge
     ETF.
5. **Costs to model and track:** both legs at 1c + 1 bps per side. The hedge pays both sides with no target freebie.
   ETF borrow for short hedges is easy-to-borrow (`shortable` check). At the scales tested, the hedge costs about
   0.03R per trade with SPY and about 0.05R with a sector ETF. A netted hedge should cost much less, and this is the
   number to measure first.
6. **Guards:**
   - Do not hedge if the ETF quote is stale or the spread is above 2 bps.
   - If the hedge order is rejected, either flatten the stock leg or mark the trade "unhedged" in the journal.
   - Daily check that the net hedge exposure is about zero after 15:55.

### 3.2 Cheap first step (report-only; no orders): a "market-adjusted" line in the EOD report
- For each closed trade: `mkt_r = -side x beta x P_entry x (SPY_exit / SPY_entry - 1) / R`.
  - beta comes from the prior 60 sessions' open-to-close returns. It can be computed in the EOD job from the daily
    bars already cached.
  - SPY_entry and SPY_exit are SPY 1-minute closes at the trade's entry and exit times (SPY bars are already loaded
    for the EOD chart).
- `hedge_cost_r = 2 x beta x P_entry x (0.01 / SPY_entry + 1e-4) / R`.
- `adj_r = r_multiple + mkt_r - hedge_cost_r`.
- Add an "Adj R (net of SPY)" column to the "By setup" table in `mcf/report/eod.py`, and one sentence: "of today's
  P/L, X R came from SPY's direction". Also add a running per-setup tally of adj_r over the last 20 sessions.
- This is housekeeping-sized (report-only) and tells the owner daily how much of each setup's result was the market.
  It is filed as backlog `sw-w2-eod-hedged-line` (idea) so the lead can decide to ship it as report housekeeping.

## 4. Files
- `common.py`, `build_bars.py` (dense 5-minute bars from the 1-minute cache, locked rows dropped at load), `betas.py`
  (prior-session betas, sector map, pairs).
- `gen_reddit.py` (Reddit base rules in row chunks; identical to regime1009), `hedge.py` (exit re-simulation, hedge
  leg, gates).
- `score_existing.py` + `score_existing_results.py` (task 1), `rv.py` (task 2), `merge_results.py`.
- `results.csv`: all 633 rows. part = existing has 103 lists x {none, SPY, SEC}; part = rv has 324 configs.
- `data/` is git-ignored. After the run only small files are kept (betas, parity, logs, RV sample trades). The 5-minute
  bar arrays (480 MB) and per-trade files (350 MB) were deleted; they rebuild in about 10 + 30 minutes.
- Backlog: `sw-w2-hedged-existing` (failed), `sw-w2-rv-stock-etf` (failed), `sw-w2-rv-pairs` (failed),
  `sw-w2-eod-hedged-line` (idea).
