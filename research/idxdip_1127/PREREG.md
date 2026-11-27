# IDXDIP-1127 — index open-dip FAMILY, pre-registration (written and committed before any scoring)

*Educational only — not financial advice.* Research only: no change to config/, setups, exits, assignments.json,
decisions.json or the ledger.

## Question
Wave 3 (research/qqqopen_1127) found IDX3 (SPY down >= 0.75% by 09:55, buy SPXL on a 20% bounce, trail) at +0.42R over
57 trades in 10 years, but fragile (+1 min entry -> t 1.44; weak neighbours) and a lead IDX6 (QQQ >= 1.5%, TQQQ, trail; 16
trades +1.15R). Is there a **robust region** of the index open-dip family (neighbouring configs all positive), not one
lucky point, that survives +1 minute latency and +2 bp slippage? How many trades/year would it add, and how does it
correlate with Primary's daily R?

## Data (engine label: E4, one-off simulator `qo_sim.py` of QQQOPEN-1127, reused unchanged; check time is a parameter)
SIP 1-minute RTH bars, raw prices. Signals SPY / QQQ / IWM / DIA; traded 3x bull ETF SPXL / TQQQ / TNA / UDOW (shorts
sell the same 3x bull ETF). 2016-01-04..2022-09-30 GET-only Alpaca (scratch), 2022-10..2024-09 `data/cache_fresh/1Min`,
2024-09-16..2026-11-04 `data/cache_hist/1Min`. **Locked block 2024-11-01..2025-02-28 dropped at load and asserted
absent** on every frame and the trade table.

## Splits
EARLY 2016-01..2022-12 (extra out-of-sample) · T2 2023-01..2024-09 · FIT 2024-10 + 2025-03..09 · CHECK 2025-10-01..2026-11-04.

## Rule (same as live IDX / qo_sim FADE-LONG, generalised to check time T)
Index running low since 09:30 <= open x (1 - X%) on a bar closed by T; trigger = first index bar closing in [T-5, T+10]
with close >= run_low + B x (open - run_low). Trade the 3x ETF at the next bar's open (bar after the ETF bar at/before
the trigger minute); stop = ETF running low - 0.10 x (ETF open - ETF low); stop-first, gap-through fills at the open.
Exits: TRAIL (1R trail once MFE >= 1R, engine semantics), HOLD (flat 15:55; half days last bar - 4 min), TGT2 (limit
target at +2R, else HOLD). SHORT = the symmetric open-pop fade (running high >= +X%, pull back B of the rise, short the
3x bull ETF, stop above the ETF high).

## Configurations (counted: 40)
* **G1 core lattice (27):** index {SPY, QQQ, IWM} x X {0.75, 1.0, 1.5}% x T {09:45, 09:55, 10:15}; long, B 0.20, TRAIL.
* **G2 DIA (3):** X {0.75, 1.0, 1.5} at 09:55, long, B 0.20, TRAIL.
* **G3 anchor variants (6)** at IDX3 (SPY 0.75 09:55) and IDX6 (QQQ 1.5 09:55): B 0.35 TRAIL; B 0.20 HOLD; B 0.20 TGT2.
* **G4 shorts (4):** open-pop short, B 0.20 TRAIL, 09:55: SPY 0.75, SPY 1.0, QQQ 1.0, QQQ 1.5.
Cumulative program N ~9,176 + 40 = ~9,216 (lineage-claim bar stays t >= ~4.3; nothing here can claim that).

## Costs (always in)
LIVE-L main (research/primshorts_1126/cells_live.json, cost_R = a / stop_bps + b by price bucket x exit kind), LR8
alongside (same code as qo_score.costs). **Stress:** S1 = +1 minute entry (fill at the open one bar later; stop kept);
S2 = +2 bp adverse slippage per side (entry and exit) on top of LIVE-L; S12 = both.

## Statistics and bars (multiplicity-aware)
Day-clustered t (sum per day). Per-config bar for any config-level claim: t_ALL >= sqrt(2 ln 40) = **2.72** over all
non-locked history (EARLY+T2+FIT+CHECK) under LIVE-L.

**H-FAM (pre-specified, one test, no selection): the G1 lattice as a family.** Family daily R = the mean, over the 27
configs, of each config's day R (0 on its no-trade days), on days where at least one config trades. Passes if: LIVE-L
family mean > 0 on EARLY, T2 and CHECK separately; family day t over all history >= 2.0; under S12 family mean > 0 on
all history with t >= 1.65; best-day share < 50% and mean w/o best day > 0.

**H-REGION (robust region):** lattice neighbours = same index, adjacent X or adjacent T (4-neighbourhood). A config
is a **robust point** if ALL hold: (1) LIVE-L mean > 0 on EARLY, T2, CHECK; (2) t_ALL >= 2.72; (3) best-day share < 50%,
w/o-best > 0; (4) mean above the 95th pct of a size-matched random-day control (500 draws: same split, other days, same
clock minute, same stop % and exit, cost = the trade's LIVE-L cost); (5) S12 mean > 0 and S12 t >= 1.65; (6) every
lattice neighbour has LIVE-L ALL mean > 0 and S12 ALL mean > 0. A **robust region** = >= 3 configs connected in the
lattice, each with (1), (5) and t_ALL >= 2.0, containing at least one robust point.
G2/G3/G4 configs are judged on (1)-(5) only (no lattice), and reported.

## Verdict rule
PASS = H-FAM passes AND a robust region exists. LEAD = H-FAM positive on EARLY/T2/CHECK (or a robust point exists) but
a bar missed. FAIL = H-FAM negative on T2 or CHECK, or no config positive on EARLY/T2/CHECK with S12 > 0.
INCONCLUSIVE = < 30 trades family-wide.

## Also reported (no pass/fail)
Every config's split means (LIVE-L and LR8), t, best-day share, w/o-best, S1/S2/S12; regime (SPY above/below 50-day SMA).
**Book impact:** trades/year and distinct trade days/year of (a) the best robust region (union, one trade per index per
day), (b) the whole G1 lattice union; **correlation with Primary daily R**: Primary 4 base book daily R (bench,
regsteer_1126 base.parquet: Primary rules, costs in; 2023-01..2026-11-04, locked block absent) vs the family / region
daily R on the same days (Pearson on all Primary days with 0 for no-IDX days, and Primary's mean R on IDX days vs other
days), plus the combined daily Sharpe. Live window note: rule changes from research/ledger.jsonl if live trades are cited.
