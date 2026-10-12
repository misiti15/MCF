# BDI 2026-10-12 - pre-declared plan (written before anything below was scored)

*Educational only - not financial advice. Backtest plan on the open two-year history; nothing here is a paper or live result.*

Source: nightly autopsy `research/bdi/nightly1012/NOTES.md` -> backlog `nightly-1012-cwt14-long-index-confirm` and
`nightly-1012-same-side-crowding-cap`. Seen before writing this plan: the published numbers of CWT package B
(`research/bdi/cwt/test_b/NOTES.md`, `results.csv`), indexlink (`research/bdi/indexlink/NOTES.md`: ix-gate 912
configurations, 0 pass, on the live/Testing-FD lists incl. NS1/NS5/heat_fade_long) and regime1009 (1,052, 0 pass).
Because the index filters were already scored on the primary / Testing-1 long lists (ix-gate F1-F3), this plan does
**not** re-score them there; the new ground is the CWT package-B long lists (Testing 2), which did not exist on 10-11.

## Data (open history only)
- Trade lists: `research/bdi/cwt/test_b/data/trades.npz` (package B, 426 open sessions 2024-10..2026-10-07, adv20 >=
  $95M, one trade per symbol-day, entry at the signal bar close, production costs + `gates.tod_cost_mult` entry side,
  x3 extended tier, R = 0.25 x daily ATR; columns day/sym/tod/xtod/r/rh/kind). Not re-simulated.
- Index state at the entry bar (bar-close tod = the trade's `tod`, known at entry): SPY and QQQ rows of the lab frames
  (`research/history2y/lib.load_month`, open months only; `MCF_HIST_ALLOW_LOCKED` never set): `fromOpen`,
  `vwapDistPct`, `dist_lod_atr`.
- Splits (indexlink convention): train = sessions <= 2025-12-31, valid = 2026-01-02..2026-10-07; open history = both.
  Regimes `lib.regimes()`, walk-forward `gates.walk_forward` (locked months excluded).

## Study A - index confirmation for long setups (lineage `bdi1012-ixconf`)
Base lists (160): every package-B long configuration of the families Testing 2 runs live
- B2 CWT13 VWAP stretch, side long, U = all: 2 z x 4 exits x 2 windows = 16
- B3 CWT14 failed breakdown, side long: 2 L x 2 p x 2 V x 3 exits x 2 windows = 48
- B4 CWT12 coil / flag: 32
- B5 CWT05 flush: 64

Filters (5), a trade is kept only when, at its entry bar:
| id | rule |
|---|---|
| X1 spy_fo | SPY fromOpen > 0 |
| X2 spy_vwap | SPY vwapDistPct > 0 |
| X3 qqq_fo | QQQ fromOpen > 0 |
| X4 qqq_vwap | QQQ vwapDistPct > 0 |
| X5 notlow | SPY and QQQ both dist_lod_atr >= 0.10 (index not at / near a new session low; the backlog's literal idea) |

**160 x 5 = 800 configurations.** Missing index row at the entry bar -> trade dropped (counted).

Per configuration, reported: n / exp / day-clustered t on train, valid and open history; up / down regime exp;
WF share; ex-best-day; busiest-session share; SPY-hedged exp (`rh`); base (unfiltered) exp; dropped-trade exp.
Plateau = mean open-history exp of the other 4 filters on the same base list.

## Study B - same-side crowding cap (lineage `bdi1012-crowd`)
Book = the 17 Testing-2 long sources found in package B (B2 2, B3 8, B4 3, B5 4; `config/account_testing2.yaml`
`testing2.source`). Merge their trades, order by entry tod (ties: config order), one open position per symbol (a
signal while the symbol is open is skipped, as live), position open from the entry tod to the exit tod (`xtod`).
Cap K concurrent open longs: **K in {10, 20, 40} = 3 configurations.** Reported vs the uncapped book: n, exp/trade,
t, total R, worst-5% session R, and a random-skip control (same number of trades removed per session at random,
mean of 20 draws, seed 1012).

## Counting and bars
N this round = 803. Lineage N per base family = test_b `N_lineage` + regime1009 1,052 + ix-gate 912 + 800
(B2 2,956 -> t >= 4.00; B3 123,363 -> 4.84; B4 2,924 -> 4.00; B5 30,970 -> 4.55). Crowding: N 3 + window-open-cluster
/ exhaustion-cluster unknown counts -> floor 1.5 used and stated.

## Gates (fixed now)
- **Primary candidate (to the lead for ONE locked-block score):** exp > 0 on train AND valid, n >= 150,
  `gates.verdict` == keep with the lineage N above (t >= bar, both regimes > 0, WF >= 0.6), plateau > 0,
  ex-best-day > 0, busiest session <= 10%, hedged exp > 0, and exp above the base list's exp.
- **Testing near-miss:** open-history exp > 0 AND train exp > 0 AND valid exp > 0, n >= 150, both regimes > 0,
  WF >= 0.6, t >= 2.0 (swarm1010 probation bar), hedged exp > 0. Lineage bar not required.
- **Backlog / rework:** improves the base in train and valid (exp higher) but fails the above.
- **Drop:** everything else.
- Crowding cap: "useful" only if exp/trade of the capped book > uncapped AND > the random-skip control, in train and
  valid. It cannot make a negative book positive; a positive book is required for Testing/primary routing.
