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
- 2026-10-11 (before scoring the L3 lists): the L3 masks also read `dist_lod_atr`, added to the loaded columns.
