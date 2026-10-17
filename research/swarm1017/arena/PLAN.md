# Arena (swarm 2026-10-17) - PLAN (written before any scoring)

*Educational only - not financial advice.*

Goal: a reusable "training arena" - every point-in-time indicator screened for an edge on TRAIN, plus a combiner
that later agents call to test AND-combinations of 2-3 conditions and to emit lab modules.

## Data and split (fixed now)
- Frames: research/history2y/data/frames (5-minute lab frames, bar closes 09:50-15:00 ET; the frames carry no
  1-minute bars and no raw volume - indicators are built from 5-minute closes/highs/lows and the existing columns).
- Locked block 2024-11-01..2025-02-28 is never loaded (lib.load_month refuses it; we never set MCF_HIST_ALLOW_LOCKED).
- TRAIN = 2024-10 and 2025-03..2025-12 (open months <= 2025-12-31). VALID = 2026-01-01 onward (to 2026-10-07).
  (Note: VALID contains the older, no-longer-clean holdout windows Apr-Jun 2026 and Sep 16-Oct 5 2026; per the
  swarm brief they are treated as valid here. The screen itself uses TRAIN only.)
- Universe: adv20 >= 95e6 (the live lab min_adv used by 67 config entries).

## Outcomes and costs (rule 1)
- Lab geometry columns r_/win_{long,short}_{t05s1,t1s1,t1s05}: entry at the decision bar close, R = 0.25 x daily ATR,
  first touch, stop-first, timed exit 15:55.
- Production R: mcf.research.gates.prod_r with time-of-day entry costs (tod=...), and x3 costs on the extended
  tier (|gap| >= 20% or price < $5), as research/bdi/opp1014.
- One trade per symbol-day: the first qualifying bar inside the window (gates.first_per_symbol_day convention).
- Random baseline: for each trade, the mean production R of ALL universe bars at the same date and minute, same
  side and geometry ("random same-minute entry"). Excess = r - control. Day-clustered t for r and for excess.

## Single-indicator screen (TRAIN only)
- ~80 indicators (mcf/research/arena/indicators.py). Windows 09:50-11:00, 11:00-14:00, 14:00-15:30 (bar close
  >= lo and < hi; frames end at 15:00 so the last window is 14:00-15:00 in practice).
- Bins per (indicator, window): train deciles d1..d10 (interval), tails <= q05, <= q20, >= q80, >= q95.
  Binary/categorical indicators: one bin per value.
- Each cell x side (long/short) x geometry (3). Every cell counts as one configuration.
- Sample: every other symbol-day (deterministic hash of symbol|date), documented, to fit time/RAM.
- Recorded per cell: n, days, exp_r, day-clustered t, excess vs random, t of excess, exp_r in up and down sessions
  (gates.session_regimes via research/history2y/lib.regimes), exp_r in the first and second half of train.
- Output: single_screen.parquet (all cells), top300.csv (ranked by excess t with n >= 200), NOTES.md.

## Combiner (for later agents)
- mcf/research/arena/combine.py: load_arena(...), evaluate_combo(...) - train/valid, regime split, random baseline,
  walk-forward (gates.walk_forward), try-count bar t_required(N); write_module(...) emits a lab module
  (SIDE, GEOM, LAYERS, mask(df)) that calls indicators.compute on the live LabStrategy frame.
- Context (cross-asset/breadth) indicators are research-only: the live LabStrategy mask sees one symbol's frame.

## Gates for any candidate (none expected from the screen itself)
exp > 0 after costs on train AND valid, regime gate, >= 200 trades, beats random same-minute, t >= max(1.5,
sqrt(2 ln N_lineage)), walk-forward share >= 0.6. The screen is a hypothesis generator; its cells are NOT candidates.
