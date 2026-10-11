# IX index linkage (2026-10-11): how the major indexes drive our products, and market-aware setups

*Educational only - not financial advice. Lab backtests on the open two-year history (and ten years of daily bars);
nothing here is a live or paper result.*

Owner (2026-10-11): "Do we have a process that makes sure we follow the major markets when making setup decisions?
Research the relevance of major indexes and how they affect individual products. Use the findings for better setup
development and execution effective immediately - even small improvements to tried setups count." Plus the thought
experiment: "if the S&P 500 dipped within the first 20 minutes of the open (sometimes later), it could frequently be
bought with a day-ending gain. If the total market moves a certain direction, and a related ticker is bought/sold at a
particular or random time of day and held the whole day, what do end-of-day results look like?"

**Section 1 (pre-declaration) was written on 2026-10-11 before any data of this study was built or scored.** Seen
beforehand: published numbers of earlier studies only (RESCORE.md, regime1009 NOTES 2.x, W2 NOTES, turns1009/scale
NOTES, W3 NOTES, the base expectancy of the timeofday trade lists, which reproduces RESCORE). Section 1 may change only
by dated amendments in 1.9.

**Prior evidence that bounds expectations (must be read with the results):**
- regime1009 (1,052 configurations, 0 pass): SPY / QQQ / IWM from-open, breadth and SPY-vs-VWAP at 10:00 / 10:30 do
  not predict the rest-of-day direction (|rho| <= 0.09); gating setups by SPY's sign from the open (G3) or a 0.30%
  dead zone (G4) does not improve them. This study's SPY-from-open filter (F3) repeats G3 as a reference.
- W2 (530 configurations, 0 pass): hedging removes the up/down split and leaves a negative stock-specific residual.

## 1. Pre-declaration

### 1.1 Data (open history only)
- 1-minute SIP cache `data/cache_hist/1Min` (RTH). Rows in the rule-19 locked block 2024-11-01..2025-02-28 are dropped
  right after each symbol's load, before any computation; only the 426 open sessions of `lib.daily()` are kept.
  `MCF_HIST_ALLOW_LOCKED` is never set and the locked months are never loaded through `lib`.
- Built once by `build.py` (one process) into `data/` (git-ignored):
  - dense 5-minute arrays for all 1,226 lab symbols [symbol, session, bar], bar-close tod 09:35..15:55 (77 bars):
    close `C5` and volume `V5` (float32); first 1-minute open of the session `O0` (= the frames' day open) and the
    last 1-minute close `CL` (15:59 bar);
  - 1-minute arrays (O/H/L/C/V, 390 minutes) for the index / sector / macro ETFs only (SPY QQQ IWM DIA, the 26 W2
    sector ETFs, VXX UVXY TLT GLD USO, UUP if fetched);
  - during the same pass, per symbol, 1-minute lead-lag statistics against SPY and QQQ (1.3).
- UUP (dollar proxy) is not in the lab universe: fetched read-only from Alpaca (`feed=sip`, 5-minute and daily bars,
  open sessions only) if the keys work; else the dollar proxy is reported as missing.
- Ten-year daily bars: `research/swarm1010/w3_daily/data/daily_2016.parquet` (survivors only; see W3 NOTES). Sessions
  inside 2024-11-01..2025-02-28 are dropped here too.
- Integrity check (declared): `C5` and `O0` reproduce the lab frames' `close` and `fromOpen` at the same (symbol, date,
  tod) for >= 99.5% of sampled rows; SPY / QQQ `vwapDistPct` rebuilt from the 5-minute bars matches the frames'.
- Point-in-time betas: `beta_spy`, `corr_spy`, `beta_qqq` from the previous 60 open sessions' daily open-to-close
  returns (min 30), computed here the same way as W2 (`research/swarm1010/w2_neutral/betas.py`); the sector map
  (`sec`, 26 ETFs, fallback SPY when the best correlation < 0.30) is reused from W2's `betas.npz`.
- Regimes: `lib.regimes()`. Splits: train = sessions <= 2025-12-31, valid = 2026-01-02..2026-10-07. Walk-forward:
  `gates.walk_forward` (locked months excluded). Costs: `gates.prod_r` with time-of-day entry costs (lab lists);
  ETF / basket trades: 1c + 1 bps per side, the entry side times `gates.tod_cost_mult`.

### 1.2 Task 1 - linkage map (descriptive; no trading configurations except 1.3)
Per product (all 1,226 symbols: stocks AND ETFs), over the open history:
- daily open-to-close beta and correlation to SPY, QQQ, IWM, DIA; to the best-fit sector ETF (highest 5-minute-return
  correlation among the 26, self excluded; fallback SPY if < 0.30); correlation to VXX, TLT, UUP (if fetched), GLD.
- intraday 5-minute return beta and correlation to SPY and QQQ (bars 09:40..15:55; the overnight / first bar excluded).
- stability: the 5-minute beta to SPY per calendar quarter -> mean, std across quarters, and first-half vs second-half
  correlation; the share of sessions where the point-in-time best sector equals the full-history one.
- lead-lag (1.3).
- relative-strength persistence: residual e = product move - beta_spy x SPY move. Correlation (pooled over sessions)
  between the residual open->10:30 and the residual 10:30->15:55, overall and on SPY dip (SPY from open at 10:30 <=
  -0.4%) and rally (>= +0.4%) sessions; the share of sessions where the two residual signs agree.
Output: `linkage.csv` (one row per symbol, committed) for the live system.

### 1.3 Lead-lag and its tradability (lineage `ix-leadlag`)
- Descriptive: per symbol, correlation of its 1-minute return at t with SPY's (and QQQ's) 1-minute return at t-L, L =
  0..15 minutes, within sessions; 5-minute lag 1..3 too.
- Tradable test (pooled over non-ETF symbols with point-in-time adv20 >= 95M, signals 09:50..15:00): index I in {SPY,
  QQQ}; lookback k in {1, 5} minutes with move threshold |I move| >= 0.10% (k=1) / 0.25% (k=5); hold h in {1, 5, 15}
  minutes; trade the product in the index's direction at the close of the signal minute, exit at the close h minutes
  later. **12 configurations.** Reported: mean gross and net bps per trade (round trip 1c + 1 bps per side, the entry
  side times the tod multiplier), the index's own continuation over the same h (to separate lead-lag from index
  momentum), day-clustered t. Per-symbol rows are descriptive only (not candidates).

### 1.4 Task 2 - market-aware conditions on the live setups (lineage `ix-gate`)
Lists (48, the setups live today): the 14 primary lab setups in their live windows (timeofday `current` trade lists:
heat_fade_short/long, exhaustion_short, MF1-5, NS1-5, RW6G1); the 29 Testing -FD lists from timeofday `full`
(MF1-5, NS1-5, RW1-7, RW6G1, ST1-8, exhaustion, heat x2) and the 3 L3-*-FD lists regenerated from their modules on the
frames (min_adv 0, prefilter gap as in YAML, first bar per symbol-day 09:50-15:00); orb20_a and intraday_momentum
(production-backtester trades `research/history2y/data/bt_trades.parquet`, context from the dense arrays at the entry
minute). Lab-list R is re-costed with the time-of-day entry cost (`gates.prod_r(tod=...)`, base numbers reported).
Context at the trade's entry bar (frame values for SPY / QQQ / sector ETF rows at the same date and tod - what a live
frame holds; beta and sector point in time). "Agrees" = long and x > 0, or short and x < 0.
| id | condition kept |
|---|---|
| F1 spy_vwap | SPY vwapDistPct agrees with the side |
| F2 qqq_vwap | QQQ vwapDistPct agrees |
| F3 spy_fo | SPY fromOpen agrees (= regime1009 G3, reference) |
| F4 sec_fo | the product's sector ETF fromOpen agrees (SPY if the map falls back) |
| F5 sec_vwap | sector ETF vwapDistPct agrees |
| F6 rs_with | relative strength RS = fromOpen - beta_spy x SPY fromOpen agrees (long a leader, short a laggard) |
| F7 rs_against | RS disagrees (long a laggard, short a leader) |
| F8 beta_leg | beta_spy x SPY fromOpen agrees and its size >= 0.20% |
| F9 spy_vwap_against | SPY vwapDistPct disagrees (contrarian control) |
| F10 sec_fo_against | sector ETF fromOpen disagrees (contrarian control) |
| F11 low_beta | beta_spy <= 1.0 |
| F12 high_beta | beta_spy > 1.0 |
| N1-N5 neighbours | F1, F2, F4 with a 0.10% dead zone; F3 with 0.15%; F6 with |RS| >= 0.25% |
| Z1 beta_size | weight clip(1 / beta_spy, 0.5, 2) (beta-scaled sizing; weighted exp = sum(w r) / sum(w)) |
| Z2 half_against | weight 1 when F1 agrees, 0.5 otherwise |
**19 conditions x 48 lists = 912 configurations.** The sibling lineage regime1009 tried 1,052 market-gate
configurations on the same setups, so the t bar is computed on N = 912 + 1,052 = 1,964: t >= sqrt(2 ln 1964) = **3.89**
(the setups' own lineages would raise it further; reported).
Per list x condition: n kept, exp before / after, day-clustered t, up / flat / down exp, walk-forward share, train /
valid exp, ex-best-day, busiest session, the blocked trades' exp and the day-clustered t of kept-minus-blocked.
Trades without a beta / sector (first ~30 open sessions) are dropped from base and conditioned lines alike for F4-F8,
F10-F12, N3, N5, Z1 (the base on the same trades is reported).
**Proposal rule (fixed now):** a list x condition becomes a proposed change only if it passes the live-probation bar
(RULES.md: n >= 150, up AND down exp > 0 with n >= 30, t >= 3.89, walk-forward share >= 0.6, ex-best-day > 0,
busiest session <= 10%, plateau = its neighbour's exp > 0 where one is defined) and improves on the base list in train
AND valid. **Portfolio-wide rule (fixed now):** a condition improves "consistently" if it raises exp in >= 75% of the
48 lists in train AND in valid (sign test) and its pooled kept-minus-blocked t >= 3.89; such a condition is proposed
as a shared filter even if no single list passes. Anything weaker is reported as an observation and goes to the
backlog, not to live.

### 1.5 Task 3 - the owner's thought experiment (lineage `ix-oe`)
Signal: SPY move from its open (O0, the 09:30 print) at decision time T, measured at the close of the 1-minute bar
ending at T. Entry: the instrument's close of the next minute (T+1, one minute of delay; 5-minute baskets enter at the
5-minute close at T, the lab convention, and the delay effect is measured on SPY). Exits: the close of the bar ending
15:55 ("hold to close"), and T+30 / T+60 minutes. Costs as 1.1 (entry side x tod multiplier: 2.1 at 09:45, 1.4 from
09:50 to 10:25).
- **A. Fixed time** T in {09:45 (DIAGNOSTIC, before the owner's 09:50 rule), 09:50 (= "the first 20 minutes"),
  10:00, 10:15, 10:30, 11:00, 12:00, 13:00, 14:00} (9); conditions: SPY from open <= -0.2 / -0.4 / -0.6% (dip) or
  >= +0.2 / +0.4 / +0.6% (rally) (6); actions: after a dip buy (buy-the-dip) or sell (follow); after a rally buy
  (follow) or sell (fade) (2); instruments: SPY, QQQ, IWM, DIA, SECT (equal-weight XLK XLF XLE XLV XLY XLP XLI XLB XLU
  XLRE XLC), HIBETA (the 30 non-ETF names with the highest point-in-time beta_spy, adv20 >= 95M), LINKED (the 30
  non-ETF names with the highest point-in-time corr_spy, adv20 >= 95M) (7); holds: close, 30, 60 min (3).
  9 x 6 x 2 x 7 x 3 = **2,268**, plus the unconditional controls (every session, long and short) 9 x 2 x 7 x 3 =
  **378**.
- **B. "Dipped at some point"** (owner: "dipped within the first 20 minutes, sometimes later"): SPY's lowest 1-minute
  low from 09:30 to T was <= -0.2 / -0.4 / -0.6% below the open, buy at T in {09:50, 10:00, 10:30}, 7 instruments, 3
  holds: 3 x 3 x 7 x 3 = **189**.
- **C. Random entry time**: every 5-minute bar close 09:50..15:00 is an equally likely entry time (the expectation of a
  random time; one equal-weight average per session, so each session counts once). Conditions at that time: SPY from
  open <= -0.2 / -0.4% or >= +0.2 / +0.4% with the 2 actions, plus unconditional long / short = 10; 7 instruments;
  hold to 15:55: **70**.
- **D. Ten-year daily** (open-to-close, MOO / MOC at 1c + 1 bps per side): SPY gap (open vs prior close) <= -0.2 /
  -0.4 / -0.6 / -1.0% or >= +0.2 / +0.4 / +0.6 / +1.0%, actions buy / sell, instruments SPY, QQQ, IWM, DIA, SECT:
  8 x 2 x 5 = 80, plus unconditional long / short x 5 = 10: **90**. By year 2016..2026.
**N = 2,268 + 378 + 189 + 70 + 90 = 2,995**; t bar sqrt(2 ln 2995) = **4.00** (and >= 2.0).
Measured per configuration (one observation per session): sessions, share of sessions with a gain, mean / median net
return (%), day t, up / flat / down regime exp, by year, walk-forward share, ex-best-day, and the difference to the
unconditional control with the same T, instrument, side and hold (Welch t). "Intraday mean reversion" is tested
directly: buy-the-dip at T vs the unconditional long at T, and SPY's rest-of-day return regressed on its move to T.
**Candidate rule (fixed now):** sessions >= 100, exp > 0 in up AND down regimes, t >= 4.00, beats the control with
difference t >= 2.0, walk-forward share >= 0.6, ex-best-day > 0, plateau (the neighbouring threshold AND the
neighbouring T both exp > 0), T >= 09:50 (09:45 rows are diagnostic, never candidates).

### 1.6 Counting
Lineages and N: `ix-leadlag` 12; `ix-gate` 912 (bar on 1,964 with regime1009); `ix-oe` 2,995. Total scored here:
**3,919**. The linkage map (1.2) is descriptive and not counted.

### 1.7 Live parity
A candidate must be expressible with live data at decision time: frame columns of SPY / QQQ / the sector ETF row at the
same bar (they are lab symbols), point-in-time beta / sector from a nightly table (the `linkage.csv` format). A lab
module would need a cross-symbol context column the LabStrategy frame does not have today; that is stated, not built,
unless something passes.

### 1.8 Backlog
One `ix-` entry per lineage (failures included) with configs_tried; atomic single-line appends after re-reading the file.

### 1.9 Amendments
- 2026-10-11 (before any scoring; data build only): the dense 5-minute arrays hold 78 bars (bar-close 09:35..16:00,
  390 minutes / 5); the 16:00 bar is not used as an exit (exits are the 15:55 bar). Integrity check result
  (`parity.json`): close and fromOpen match the frames on 600,000 sampled rows (share 1.0). The vwapDistPct of SPY /
  QQQ / sector ETFs for the 46 lab lists is read from the frames directly, so the rebuilt VWAP is used only for the
  orb20_a / intraday_momentum context (entry minutes outside the frames' 09:50-15:00).
- 2026-10-11 (AFTER scoring part C; a design flaw, found when part C disagreed with every fixed-T row): part C as
  declared averages each session over its qualifying bars, i.e. weights every bar by 1 / (number of qualifying bars
  that session), a number known only at the close. Sessions where SPY dips briefly and recovers get full weight from
  few bars; sessions that stay down are diluted (correlation of the per-session bar count with the session's mean
  -0.46 for SPY dip 0.2%). That is look-ahead. The declared C rows are kept, flagged `diag` / `lookahead_weight`, and
  never candidates. Added causal versions of the same 70 configurations: **Cpool** (every qualifying bar a trade of
  fixed size, day-clustered t), **Cfirst** (first qualifying bar per session), **Crand** (one random bar per session,
  seed 20261011, the same draw for every configuration) = **210** more; ix-oe N = 3,205, t bar 4.02.
- 2026-10-11 (AFTER the first part A-D run; implementation bug vs the declaration): "non-ETF names" for HIBETA /
  LINKED was implemented with W2's 84-name ETF list only, which misses leveraged / other ETFs (LINKED was 98% ETFs such
  as SSO / QLD / VT, HIBETA 25% leveraged ETFs such as TECL / MSTX). Fixed to exclude the W3 `assets_meta.csv` ETF tag
  as well (203 names) and re-run; the declared definition and the counts are unchanged. The linkage table's `is_etf`
  uses the same union. The ix-leadlag pooled test kept W2's list; its stocks-only means (W3 tag) are reported too.
- 2026-10-11 (before scoring the L3 lists): the L3 masks also read `dist_lod_atr`, added to the loaded columns.

## 2. Results (written after scoring; section 1 changed only by the dated amendments in 1.9)

*Lab backtests on the open two-year history (426 sessions, 2024-10 and 2025-03..2026-10-07) and on ten years of
daily bars. Nothing here is a live or paper result. Production costs throughout. Educational only - not financial
advice.* The locked block was never loaded and `MCF_HIST_ALLOW_LOCKED` was never set.

**Configurations scored: 4,129** = ix-leadlag 12 + ix-gate 912 + ix-oe 3,205 (2,995 declared + 210 causal part-C
variants, amendment 1.9). **0 pass** any declared bar. No proposed setup change, no lab module, no Testing YAML.

### 2.0 Failures and caveats first
- **ix-gate (912, bar t >= 3.89 incl. regime1009's 1,052): 0 pass.** No market-aware condition (SPY / QQQ vs VWAP,
  SPY / sector from the open, sector agreement, relative strength, beta-leg direction, low / high beta, beta-scaled
  or half-size-against-the-market sizing) turns any of the 48 live lists into a passer. **No condition meets the
  portfolio-wide rule** (>= 75% of lists improved in train AND valid, pooled t >= 3.89): the best is N5 (relative
  strength with a 0.25% dead zone) improving 22 of 48 lists in both halves, pooled kept-minus-blocked +0.017R, t 1.04.
- The "market agrees with the trade" filters are, pooled over all 48 lists, **zero or negative**: SPY vs VWAP agrees
  -0.007R (t -0.42) vs the blocked trades, QQQ vs VWAP -0.023R (t -1.25), sector from open -0.001R, sector vs VWAP
  -0.010R, beta-leg -0.002R. The contrarian controls (F9, F10) are slightly positive. This repeats regime1009: the
  market's direction so far does not tell which trades will win.
- Beta-scaled sizing (Z1, weight 1/beta) lowers expectancy on **every** list (48 of 48, mean -0.002R): higher-beta
  trades did slightly better (F12 high-beta only: +0.021R vs low-beta, t 1.42, 36/48 lists better in train, 25/48 in
  valid). Half size against SPY's VWAP (Z2): mean -0.003R.
- Relative-strength filters (F6 / N5) show a few large per-list numbers (NS2-cur +0.63R, t 6.8; ST1-FD, RW6G1-cur), but
  every one is a small subset concentrated on one or two sessions (busiest session 46-95% of trades, no down-session
  trades); none survives the bar. Pooled: shorts in laggards +0.024R vs leaders (t 1.35), longs in leaders -0.016R.
- **ix-oe (3,205, bar t >= 4.02): 0 candidates.** The owner's buy-the-dip idea does not hold on SPY, QQQ, DIA or the
  sector basket at any decision time 09:50-14:00: SPY down >= 0.2% from the open at 09:50 (the "first 20 minutes"
  dip, 68 of 426 sessions) then held to 15:55 ends up **-0.004%** on average after costs, green on 46% of sessions;
  the unconditional SPY long from 09:50 is +0.003%, green 52%. 2,453 non-control configurations: 5 reach t >= 2 (about
  60 would by chance at one-sided 2.5%), none reaches 4.02, none passes the regime split with a plateau.
- **Part C as declared had look-ahead** (amendment 1.9): averaging each session over its qualifying bars weights by a
  number known only at the close. It produced t 3-4.6 for "buy the dip at a random time" in every instrument; the
  causal versions (every qualifying bar, first qualifying bar, one random bar per session) are all ~0 or negative
  (SPY dip 0.2%: -0.059% pooled t -1.62, first bar -0.051%, random bar -0.027%). The declared C rows stay in
  `oe_results.csv`, flagged `diag` / `lookahead_weight`.
- **Basket bug fixed before the final run** (amendment 1.9): LINKED / HIBETA were first built with W2's ETF list
  only and were mostly ETFs (SSO, QLD, VT; TECL, MSTX). Re-run with the W3 ETF tag; only the corrected numbers are
  reported.
- **ix-leadlag (12): 0 pass, all negative after costs.** SPY / QQQ do lead single stocks by about one minute (median
  lag-1 correlation 0.035, positive in train and valid for 85% of liquid stocks), but the follow-through is 0.5-1.6 bps
  gross against ~6.2 bps of round-trip cost: net -4.7 to -7.6 bps per trade (t -6 to -45). Stocks only (W3 ETF tag
  excluded) the same. The index itself mean-reverts slightly after its own 1-minute jumps (-0.2 to -2.7 bps).
- Survivorship (today's universe applied back), two years only (426 sessions; 16-70 dip sessions per threshold at a
  fixed time), and the ten-year daily file is survivors only.

### 2.1 Linkage map (task 1; `linkage.csv`, `linkage_summary.json`; 1,225 products: 1,022 stocks, 203 ETFs)
Medians over the 773 stocks with median adv20 >= 95M (p10 / p90 in brackets):
| measure | median (p10 / p90) |
|---|---|
| 5-min return corr to SPY / QQQ / IWM / DIA | 0.40 (0.21 / 0.56) / 0.35 (0.11 / 0.54) / 0.41 (0.21 / 0.56) / 0.39 (0.26 / 0.55) |
| daily open-to-close corr to SPY | 0.42 (0.20 / 0.62) |
| 5-min beta to SPY | 0.94 (0.37 / 2.02) |
| best-fit sector ETF corr (5-min) | 0.56 (0.40 / 0.75); beats SPY's corr by +0.14 (0.03 / 0.42) |
| index with the highest 5-min corr | DIA 381, IWM 209, QQQ 109, SPY 74 names |
| sector ETFs used | XLI 95, IGV 85, XLF 75, XLK 62, SOXX 60, XLV 56, XRT 53, XLP 48 ... (fallback SPY 22) |
| daily corr to VXX / TLT / GLD / UUP | -0.36 / +0.10 / +0.10 / -0.02 (dollar proxy: no link) |
| beta stability: std of quarterly 5-min beta | 0.24 (0.15 / 0.53); train vs valid beta corr across names 0.88 |
| point-in-time sector (60-day daily) = full-history sector | 58% of sessions (15% / 100%) |
| 1-min lead-lag corr, SPY at t-1 -> stock at t | 0.035 (0.010 / 0.080); lag 0 = 0.31; lags 2-15 ~0 |
| 5-min lag-1 corr | 0.018 |
| relative-strength persistence: corr(residual open->10:30, residual 10:30->15:55) | -0.015 (-0.10 / +0.08); same sign 49.2% |
| same on SPY dip / rally sessions (|SPY| >= 0.4% at 10:30) | -0.02 / -0.01 |
Read: the sector ETF explains a stock's intraday moves better than any broad index (corr 0.56 vs 0.40), DIA and IWM
fit more names than SPY, betas are stable enough to use (train/valid 0.88), the market leads by about a minute but
not by enough to trade, and a stock that is stronger or weaker than its index in the morning is **not** more likely to
stay so in the afternoon (no relative-strength persistence, also on dip or rally days).

### 2.2 Task 2 per setup (`gate_results.csv`, `gate_pooled.csv`, `data/tables.md`)
Base = the live list re-costed with the time-of-day entry cost. "Best" = the condition with the highest exp among
those keeping n >= 150 (descriptive; choosing it is itself a search). None passes the bar; nearest misses below.
| list | base n | base exp (t) | best condition | n kept | exp after (t) | up / down after | WF | train / valid change |
|---|---|---|---|---|---|---|---|---|
| heat_fade_short-cur | 14,433 | +0.010 (0.41) | F9 spy_vwap_against | 9,077 | +0.033 (1.02) | -0.174 / +0.234 | 0.71 | +0.014 / +0.029 |
| heat_fade_long-cur | 14,460 | -0.046 (-1.16) | F8 beta_leg | 2,206 | +0.013 (0.38) | +0.081 / -0.086 | 0.53 | +0.111 / +0.021 |
| exhaustion_short-cur | 5,973 | -0.010 (-0.32) | F6 rs_with | 1,467 | +0.026 (0.49) | -0.034 / +0.222 | 0.47 | +0.021 / +0.007 |
| MF1-cur | 2,389 | -0.078 (-2.84) | F8 beta_leg | 186 | +0.032 (0.28) | -0.358 / +0.070 | 0.50 | +0.190 / +0.010 |
| MF2-cur | 610 | -0.032 (-0.88) | F10 sec_fo_against | 281 | +0.004 (0.07) | -0.162 / +0.036 | 0.73 | +0.071 / +0.027 |
| MF3-cur | 4,136 | -0.085 (-2.88) | N1 spy_vwap_dz10 | 527 | -0.011 (-0.18) | -0.211 / +0.002 | 0.44 | +0.187 / -0.041 |
| MF4-cur | 3,318 | -0.097 (-3.30) | F8 beta_leg | 720 | -0.051 (-1.35) | -0.212 / -0.019 | 0.47 | +0.113 / -0.008 |
| MF5-cur (= -FD) | 6,827 | -0.057 (-2.64) | N1 spy_vwap_dz10 | 861 | +0.002 (0.04) | -0.221 / +0.004 | 0.44 | +0.088 / +0.017 |
| NS1-cur | 444 | +0.032 (0.80) | N3 sec_fo_dz10 | 295 | +0.070 (1.46) | +0.133 / +0.014 | 0.46 | +0.027 / +0.028 |
| NS2-cur | 3,124 | +0.004 (0.07) | F6 rs_with | 157 | +0.625 (6.83) | +0.626 / - | - | concentrated: busiest session 67% |
| NS3-cur | 1,510 | +0.052 (1.17) | N4 spy_fo_dz15 | 493 | +0.093 (1.12) | -0.239 / +0.341 | 0.43 | +0.105 / -0.001 |
| NS4-cur | 1,469 | -0.065 (-2.03) | F11 low_beta | 469 | -0.041 (-0.91) | -0.173 / +0.116 | 0.36 | +0.003 / +0.030 |
| NS5-cur | 1,305 | -0.040 (-0.49) | F3 spy_fo | 389 | -0.004 (-0.07) | +0.018 / -0.117 | 0.47 | +0.134 / -0.082 |
| RW6G1-cur | 424 | +0.263 (2.36) | F9 spy_vwap_against | 353 | +0.306 (2.95) | +0.330 / +0.004 | 0.67 | +0.046 / -0.050 |
| orb20_a | 2,827 | -0.008 (-0.41) | F8 beta_leg | 653 | +0.023 (0.51) | +0.039 / +0.119 | 0.69 | +0.049 / +0.013 |
| intraday_momentum | 1,151 | -0.067 (-2.70) | F9 spy_vwap_against | 506 | -0.035 (-0.81) | -0.083 / -0.097 | 0.29 | +0.054 / +0.007 |
The 32 Testing -FD lists are in `data/tables.md` / `gate_results.csv`; 0 pass. Nearest misses on the Testing side
(both regimes > 0, WF >= 0.6, but t far below 3.89 and n < 300): ST4-FD + F11 low_beta (n 281, +0.076R, t 1.69,
up +0.095 / down +0.087, WF 0.67); ST6-FD + F5 sec_vwap (n 231, +0.104R, t 1.82, +0.145 / +0.066, WF 0.71).

### 2.3 Task 3 - the thought experiment (`oe_results.csv`, `oe_diag.json`)
SPY / QQQ / IWM / HIBETA long, hold to 15:55, mean net % per session (share of sessions green, sessions):
| T | SPY all | SPY dip >= 0.2% | SPY dip >= 0.4% | SPY rally >= 0.2% (follow) | IWM dip 0.4% | HIBETA dip 0.2% |
|---|---|---|---|---|---|---|
| 09:45 (diag) | +0.001 (52%, 426) | -0.033 (45%, 64) | +0.029 (52%, 21) | +0.127 (62%, 60) | +0.104 (21) | +0.231 (57) |
| 09:50 | +0.003 (52%) | -0.004 (46%, 68) | -0.092 (44%, 16) | +0.221 (63%, 70) | +0.328 (16) | +0.230 (62) |
| 10:00 | -0.006 (53%) | -0.008 (54%, 89) | -0.048 (54%, 28) | +0.141 (57%, 95) | -0.011 (28) | +0.254 (83) |
| 10:15 | -0.015 (50%) | -0.053 (43%, 95) | +0.009 (47%, 47) | +0.044 (55%, 109) | +0.184 (47) | +0.405 (87) |
| 10:30 | -0.004 (52%) | -0.013 (47%, 106) | +0.034 (50%, 46) | +0.049 (60%, 120) | +0.225 (46) | +0.577 (97), t 2.49 |
| 11:00 | -0.005 (51%) | -0.135 (43%, 114) | -0.140 (48%, 67) | -0.010 (54%, 133) | -0.003 (67) | +0.092 (103) |
| 12:00 | -0.000 (50%) | -0.063 (47%, 129) | -0.074 (47%, 70) | +0.054 (52%, 154) | +0.009 (70) | +0.083 (115) |
| 13:00 | -0.004 (49%) | -0.042 (45%, 127) | -0.034 (45%, 83) | +0.064 (55%, 157) | +0.048 (83) | +0.115 (115) |
| 14:00 | -0.032 (47%) | -0.068 (44%, 133) | -0.084 (44%, 81) | +0.007 (49%, 164) | -0.027 (81) | -0.059 (121) |
- **Mean reversion tested directly** (`oe_diag.json`): SPY's rest-of-day return regressed on its move to T has a
  **positive** slope at every T (09:50 +0.54, t 3.2; 10:00 +0.43, t 3.4; 13:00 +0.14, t 3.2; 14:00 +0.09, t 4.2):
  intraday the index slightly *continues*, it does not revert. A morning dip followed by a rebound is just one of the
  outcomes; on average dips are followed by a flat-to-lower afternoon, rallies by a flat-to-higher one. The follow
  side is not tradable either (rally-follow at 09:50 +0.22%, t 1.44; fade -0.28%).
- "Dipped at some point by T" (part B): SPY bought at 09:50 after its low reached -0.2% / -0.4%: -0.019% (145
  sessions) / +0.044% (36); at 10:30: -0.057% / -0.011%. Nothing beats the unconditional long (best diff t 1.85, LINKED 60-min; 1.43 for SPY / QQQ / DIA / sector).
- Random entry time (causal versions): every variant within noise; SPY / QQQ / DIA / sector buy-the-dip negative.
- Ten-year daily (part D, 2,628 sessions 2016-2026, survivors): SPY gap down >= 0.4% then open-to-close long
  +0.015% (52% green, 430 sessions, t 0.27); gap down >= 1.0% +0.117% (123, t 0.94). Gap-up follow (>= 0.6%) +0.100%
  (t 1.56). By year the sign flips (e.g. gap-down-0.4 buy: 2024 -0.25%, 2025 +0.23%). No gap rule reaches t 2.
- Nearest miss: HIBETA (the 30 highest-beta liquid stocks) bought at 10:30 after SPY is down >= 0.2%: +0.58% per
  session, green 61%, 97 sessions, t 2.49 (bar 4.02), beats its control (diff t 2.08), WF 0.89, but -0.52% in down
  sessions (+2.80% in up sessions): a leveraged bet on the afternoon direction, not an edge. Backlog only.

### 2.4 What the live system should use now
- **No setup or exit change is proposed** (rule 9/10: nothing passed). Do not add SPY / QQQ / sector "market agrees"
  filters to the live setups: on the 48 live lists they do not help (pooled -0.02 to +0.01R) and regime1009 found the
  same with 1,052 configurations.
- **Use the linkage table for context and risk, not for entries** (housekeeping-level, no trade changes): show each
  open position's sector ETF and beta (from `linkage.csv`, refresh nightly with point-in-time 60-day betas) in the
  dashboard / EOD report, and report the book's net beta-weighted exposure (sum side x beta x notional) so the owner
  can see when the paper book is one big market bet. That is the "process that follows the major markets".
- Market-aware *sizing* by beta made results worse; do not adopt.
- The thought experiment's answer: buying SPY / QQQ / DIA / sector ETFs after a morning dip and holding to the close
  has no edge after costs on two years of 1-minute data or ten years of daily data; IWM and high-beta stocks look
  better only because they amplify whatever the afternoon does.

### 2.5 Files and reproduction
`fetch_uup.py` (Alpaca market data, read-only) -> `build.py` (one pass over the 1-minute cache, ~3 min) -> `parity.py`,
`linkage.py`, `ix_gate.py`, `gate_pooled.py`, `ix_oe.py`, `report.py`. Committed outputs: `linkage.csv` (per-product
table for the live system), `linkage_summary.json`, `leadlag_results.csv`, `gate_results.csv`, `gate_pooled.csv`,
`oe_results.csv`, `oe_diag.json`, `parity.json`. The dense 5-minute arrays (`data/C5.f32`, `V5.f32`, 320 MB) were
deleted after the run (shared-disk rule); `build.py` rebuilds them.
