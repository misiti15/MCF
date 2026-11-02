# saturday1031 PLAN (pre-declared 2026-10-31 ~15:05 UTC, before any row below was scored)

*Educational only — not financial advice.* Weekend run: no config, setup, exit or assignment change. Anything that
passes becomes an owner DECISION.

## Data rules (all studies)
- Open two-year history only. The locked block 2024-11-01..2025-02-28 is never read (`MCF_HIST_ALLOW_LOCKED` unset;
  every loader asserts it; lab files do not contain it; 1-min reads drop it).
- The old holdouts are kept out of the sweeps: 2026-04-01..2026-06-30 and 2026-09-16 onward are dropped before scoring.
- Split: TRAIN 2024-10-01..2025-08-31 (minus the locked block), VALID 2025-09-01..2026-09-15 (minus Apr-Jun 2026).
- Production costs in (gates.prod_r / 1c + 1 bps per side, ToD entry multiplier, +2c on stops, 3x extended tier where
  the harness has it). Day-clustered t. Regimes = gates.session_regimes (universe median open-to-close terciles).
- Every row is reported, failures included; avg R without the best day and its share are reported.

## A. Exit rework: earlier day-trade flatten (backlog `nightly-1027-flatten-1545`, lineage looks: live replays only)
Data: `research/history2y/data/lab_trades.parquet` (21 live / probation lab setups, base windows). Entry price = the
5-min frame close at the entry bar; R = 0.25 x ATR_d; geometry per setup inferred from the r distribution
(target / stop multiples in {0.5, 1}). Each trade is walked on the 1-min cache from the entry bar end: if no stop /
target touch before the flatten minute F, the trade is closed at the 1-min close ending at F (exit cost 1c + 1 bps),
otherwise unchanged.
Configs (5): F = 15:40, 15:45, 15:50 (all trades); F = 15:45 longs only; F = 15:45 shorts only.
Pass (exit change for every account incl. Primary -> full bar): Δ per trade > 0 in TRAIN and VALID, Δ > 0 in up and
down sessions, day-clustered t of the per-day Δ >= max(1.5, sqrt(2 ln 5)) = 1.79, plateau (neighbouring F also > 0),
top-decile winners keep >= 90% of their R.
Sanity first: share of trades the 1-min walk classes as "open at 15:55" vs the lab r being a flatten value.

## B. Give-back proposal: burst risk sharing (backlog `nightly-1029-burst20-one-bet`, 0 configs so far)
A burst = one setup entering >= K symbols on the same 5-min bar. Rule: every lot of a burst is sized so the burst
risks C R in total (each lot C / n of normal risk); no trade is removed, exits unchanged.
Configs (6): K in {10, 20} x C in {3, 5, 10}.
Two-year (lab_trades): per-lot avg R of burst lots vs the rest (day-clustered t of the difference); the weighted book
(R per unit of risk deployed), daily-P/L std, worst 5 days, share of the top-decile winners' R kept (in $ terms).
Live (journals 10-06..10-30, all 5 accounts, costs in): the same sizing replayed on the realized-R curve by exit time:
per day peak -> close give-back, close, and the best days given up.
Pass: burst lots lose vs the rest in TRAIN and VALID and in up and down sessions; the weighted book's R per unit risk
improves in both splits; t of the burst-minus-rest difference >= max(1.5, sqrt(2 ln 6)) = 1.89 (full bar: it would
apply to Primary too). Trades kept = 100% by construction; top-decile winners' $ kept is reported (the 80/90 rule is
for filters; risk sharing keeps every trade).

## C. Rule-18 rework of F4-RW4-L (rdt1030: OR-low sweep + 15-min FVG, QQQ >= +0.20% from open, long)
Harness: an unchanged copy of `research/bdi/rdt1030/F4/build.py` / `score.py` (scratch path moved), new rework rows
only. Lineage N = 2,137 (rdt1030 as scored) + 8 = 2,145 -> BAR90 t >= 0.9 x sqrt(2 ln 2145) = 3.52, WF >= 54%,
> 0 in TRAIN and VALID, up- and down-day R > 0, >= 3 trades/session, above the random control.
Configs (8, long only): neighbourhood of the QQQ gate 0.10 / 0.30; pairs with RW4's gate at 0.20: break-even at
+1R; fixed 2R target; retrace entry at the FVG edge; tight stop at the FVG's first candle; stronger displacement
(0.30 ATR); bigger gap (0.10 ATR).
F2-RW3-L is not reworked: its +0.039R is 89% one day (2025-04-07; w/o best day +0.005R), so under the one-big-day rule
it is not a near-miss; reported as such.

## D. New ideas for the 09:35-09:50 window (LONG), Move Hunt lineage (mh-1030 N 12 + 8 = 20 -> full bar 2.45,
BAR90 2.20)
Data: `research/bdi/timeofday/data/open` (09:35..10:30 5-min rows) + daily table, adv20 >= $95M, earnings blackout
(+-4 trading days) removed, first qualifying bar per symbol-day among 09:40 / 09:45 / 09:50 bar closes.
Move library prior (10-29 + 10-30, 69 early long movers): median gap -1.7%, RSI5 16, below VWAP, at / below the PDL,
volumeRatio 2.2, ATR 3.9% of price.
- D1 Opening capitulation reversal, volume-confirmed (long): gap <= -1%, the prior 5-min row RSI5 <= 20, this bar
  closes above the prior bar's close with buyPressure > 0, volumeRatio >= V, close <= PDL + 0.25 ATR. V in {1.5, 3}.
- D2 Gap-and-go opening drive (long): gap >= +1%, fromOpen >= +0.25 ATR_d (as %), close above VWAP, volumeRatio >= V,
  SPY fromOpen > 0 at the same bar. V in {1.5, 3}.
Exits (2 each): t1s1 (frame outcome, 0.25 ATR stop / target, to 15:55) and h1030-wide (stop 0.5 ATR_d checked on each
later row, else exit at the 10:30 close; R = 0.5 ATR_d).
8 configs. Random baseline: the first eligible 09:40 row of every symbol-day, same exit. Pass = BAR90 (t >= 2.20,
WF >= 54%, > 0 in TRAIN / VALID and up / down sessions, above the baseline).

Total configurations declared: A 5 + B 6 + C 8 + D 8 = **27**.
