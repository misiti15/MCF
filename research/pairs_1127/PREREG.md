# PAIRS-1127 — stock vs sector-ETF intraday residual mean reversion (pre-registration)

Educational only — not financial advice. Research only: no change to config/, setups, exits, assignments.json,
decisions.json or the ledger. Written and committed before any scoring.

## Question
When a liquid stock's intraday move departs from its beta-adjusted sector-ETF move by more than k sigma, does trading the
stock against the ETF hedge back toward zero make money after costs on BOTH legs? It is market-neutral by construction (the
"negative market intercept" fix). RESID-MAP-1127 found pre-cost residual reversal smaller than one round trip (beta = 1 vs
SPY, decile books); here the hedge is the sector ETF with a prior-60-day beta and only large deviations trade.

## Data and splits
- SIP 1-minute bars: data/cache_fresh/1Min (469 names, 2022-10-03..2024-09-13) + data/cache_hist/1Min (1,226 names,
  2024-09-16..2026-11-04), aggregated to 5-minute bars (09:30-16:00). Half days (NYSE list) excluded.
- **Locked block 2024-11-01..2025-02-28 is never read**: row filter at read time plus an assert in the build and score code.
- FIT = 2024-10 + 2025-03..2025-09; CHECK = 2025-10..2026-11-04; T2 = 2023-01..2024-09. EARLY (pre-2023) is not available
  for single stocks (cache starts 2022-10-03, consumed by the 60-day lookback) -> reported as n/a.
- Survivorship: the universe is today's caches applied to the past (T2 = the 469-name fresh cache).

## Construction (fixed for all configs)
- Hedge ETFs: XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH. Each stock-day, its ETF = the one with the highest
  correlation of 5-min returns over the prior 60 available sessions (strictly before the day); beta = OLS slope (no
  intercept) on those bars, clipped to [0.2, 3.0]; residual sigma5 = std of 5-min residual returns over those bars. Require
  >= 50 valid lookback sessions and corr >= 0.30. Lookback windows skip the locked block (never read), so FIT 2025-03 betas
  use 2024 sessions (stale, FIT only).
- Universe per day: non-ETF names (name regex as RESID-MAP), prior close >= $5, ranked by prior-20-session avg dollar
  volume; top 500 (or top 200 where stated).
- Residual: X(j) = sum over 5-min bars 0..j of (r_stock - beta r_etf), bar 0 measured from the 09:30 open.
  OPEN baseline z = X(j) / (sigma5 sqrt(j+1)); R60 baseline z = (X(j) - X(j-12)) / (sigma5 sqrt 12) (j >= 12).
- Entry: first 5-min close with |z| > k, decisions from the 10:00 bar close to the 15:00 bar close; one trade per stock-day.
  Fill both legs at the open of the next minute (the next 5-min bar's first minute). Side: z > 0 -> short stock / long
  beta x ETF notional; z < 0 -> long stock / short ETF.
- Exit (checked at 5-min closes, filled at the next minute open, both legs): reversion s*z <= X_exit; pair stop s*z >= k+2;
  time stop H; forced at the 15:55 open.
- P/L in bp of stock notional: gross = 1e4 [side ln(S1/S0) - side beta ln(E1/E0)]. R width W = 2 sigma5 sqrt(n_ref) in bp
  (n_ref = j+1 for OPEN, 12 for R60), i.e. the pair-stop distance; R = net bp / W.

## Costs (always in, both legs)
- **LIVE-L (main)**: stock leg cost_bp = a + b x W with (a, b) from research/primshorts_1126/cells_live.json by price
  bucket and exit kind (stop kind for pair stops, market kind for reversion / time / 15:55 exits). ETF leg, beta x notional:
  per side one full tick ($0.01 / price) + 1 bp cushion. SEC fee on sell notional of both legs (from 2026-04-04).
- **LR8 (alongside)**: entry 1 bp; market exit max($0.01, 1 bp), stop exit max($0.02, 4 bp); SEC; same on the ETF leg.

## Configurations (28; all reported)
- Grid 24: baseline {OPEN, R60} x k {2.5, 3.0, 4.0} x exit X_exit {0 (full), 0.5k (half)} x hold H {60 min, EOD}; top 500.
- Extra 4: top 200, baseline {OPEN, R60} x k {3.0, 4.0}, X_exit = 0.5k, H = EOD.
Configs this study: **28** -> cumulative N ~ 9,176 + 28 = **9,204** (lineage bar sqrt(2 ln N) ~ 4.28).

## Selection and pass bars
- Primary finalist = the config with the highest FIT day-clustered t of LIVE-L net bp/trade (n >= 100 trades). Every config
  is reported on FIT / CHECK / T2.
- PASS (primary finalist) requires all of: LIVE-L net mean > 0 on CHECK and on T2 separately; LR8 > 0 on both; pooled
  CHECK+T2 day-clustered t >= 2.61 (= sqrt(2 ln 30), family multiplicity bar); best-day share < 50% and avg without best
  day > 0 on CHECK and T2; beats a size-matched random control (same days, same trade count per day, random eligible
  stock, random time in the window, random side, same hold length, same costs; 200 draws) at >= 95th pct on CHECK and T2;
  stress (+1 minute entry and exit fill, +2 bp per leg per side) pooled t >= 1.65 and mean > 0; daily book P/L |corr| with
  SPY open-to-close < 0.30 (market beta reported, bp per 1% SPY).
- LEAD: positive after LIVE-L costs on CHECK and T2 with t below the family bar or one non-core bar missed.
  FAIL otherwise. Promotion-grade evidence would need the lineage bar (t >= 4.28) — not claimable from this study alone.
- Also reported: gross (pre-cost) bp by k to answer "do costs kill it", cost breakdown per leg, per-ETF effect for the
  finalist, market beta, and the share of trades ending by reversion / stop / time.
- No live window is used, so no ledger rule change falls inside these figures (historical replay of fixed rules).
