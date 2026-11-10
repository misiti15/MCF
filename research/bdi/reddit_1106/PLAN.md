# reddit_1106 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), same harness as reddit_1105: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries; stop first when a
bar touches stop and target; gaps through a stop fill at the open; locked block 2024-11-01..2025-02-28 never read
(1-minute rows and daily rows dropped at load, before any computation); old holdouts 2026-04..06 and >= 2026-09-16
dropped; earnings blackout (`GD._blackout`) removed; point-in-time top 250 non-ETF names by prior-day adv20; one trade
per symbol-day per config; day-clustered t; regime gate `gates.session_regimes` (up and down both > 0); WF = share of
months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID after (both > 0); beats random entries (excess > 0); avg R without
the best day and the best-day share; R split by SPY day type (SPY open-to-close > +0.25% up, < -0.25% down, else
quiet). Data: the 2-year cache rebuilt 2026-11-04 (research/bdi/1104/DATA.md).
**N = 8 configurations tonight (A only). Full bar sqrt(2 ln 8) = 2.04; Testing bar (rule 22 BAR90) = 1.84.**
No post-hoc configs. The locked block is scored only if a config clears every open-history gate.

## A — low-volume pullback day, then a volume-confirmed 15-minute EMA20 bounce (LONG; r/Daytrading 1xpp3mz, 2026-11-06)
Poster (DAL long on a weak SPY day): daily up-day on high volume, next day a pullback on ~70% of that volume while
holding the daily EMA20; intraday, price pulls back to the rising 15-minute EMA20 and prints a bullish 15-minute
candle on ~2x the volume of the preceding bearish candle; structural stop under the support; target the top of the
prior red day.
- Daily context `ctx` (D = today): D-2 close > D-2 open and > D-3 close; D-1 close < D-1 open; volume(D-1) <=
  0.75 x volume(D-2); D-1 close > daily EMA20 of closes through D-1. `ctx=off` drops this whole block.
- 15-minute bars (09:30-anchored, regular session; EMA20 of 15-minute closes carried across sessions).
  Signal bar k (closes 10:00..14:30): low_k <= EMA_k + 0.05 x ATR14 (daily, prior days); close_k > EMA_k;
  close_k > open_k; bar k-1 bearish (close < open); volume_k >= v x volume_{k-1}; EMA_k > EMA_{k-4} (rising).
  First signal per symbol-day.
- Entry: open of the first 5-minute bar after bar k closes. Stop: low_k - 1c. Skip R < 0.10% of price or R > 1.0 ATR.
- Exit: target m x R, else out at the last bar's close (5-minute simulation).
- Grid: ctx {on, off} x v {1.5, 2.0} x m {1.5, 2.0} = **8 configs**.
- Random control: per trade, 3 random 5-minute entry bars (opens 10:05..14:45) on the same symbol-day, long, same $ R
  and m x R target.

## Not tested tonight
- reddit-1106-dataday-wait-or-settle (r/StockMarket 1xpl1wq + comment): needs an 8:30 macro-release calendar; ~15
  NFP days in the open history is too few for a day-clustered t. Backlog only.
