# 2-year live-code replay — notes

*Educational only — not financial advice. Research only: no trading, setup, exit or config change was made. Plan:
[PLAN.md](PLAN.md) (committed before results; addenda A and B written before any 2-year result was scored). Results:
[RESULTS.md](RESULTS.md); per setup: [per_setup.csv](per_setup.csv).*

## What was run

- Engine: `mcf.replay` (the real `PaperRunner` loop) + `mcf/replay/livecal.py` with [params_2y.json](params_2y.json)
  (= research/replay_cal/params_v2.json with poll logs and recorded quotes off, because the 2-year sessions have
  neither). Code and config replayed: commit 8a9a0cb6c (today's account files; every enabled setup, 206 setup slots in
  10 accounts; account caps / lots / latches / twin rules as today). Fills `costs`, fast path on.
- Universe per session = the pack's point-in-time universe (~4,200 names, delisted names included). Priors = the live
  prep from the session's 1day pack + 24 calendar days of 1-minute packs before it.
- R per entry lot after the **LR8** live cost model on the replay's own fills (research/replay_cal/score.py `lots`),
  the same for live trades in every comparison.
- Driver: scratchpad worker pool (one job = one account × one session, `mcf.replay.__main__._one`), then
  [analyze.py](analyze.py). Per-session outputs stayed in the scratchpad (not committed; regenerable).

## Deviations from the plan (all forced by compute or data, none chosen after seeing results)

1. **Sample, not the full store.** One account-session takes 400-1,400 s on one core (the per-symbol feature frames of
   the full universe dominate; accounts share little). The full replayable store × 10 accounts is ~30+ core-days.
   Run here: 2024-10-11, 2024-10-23, 2025-04-30, 2025-05-21, 2025-06-02 (tier-1 accounts only), 2025-07-15, 2025-09-16
   — the first sessions of the fixed, day-major job order (addendum A/B list) that finished before the stop. The rest of
   the list was not run (RESULTS.md gives exact coverage per account).
2. **Container restart** at ~23:30 UTC killed the workers mid-session; finished sessions were on disk and kept,
   interrupted ones were re-run from the start.
3. **2025-03-03..2025-04-29 cannot be replayed** although stored: the priors look-back (60 calendar days) reaches into
   the locked block and `store.check_dates` refuses them. `MCF_HIST_ALLOW_LOCKED` was never set. The locked block
   2024-11-01..2025-02-28 was never read.
4. Overlap check ran on 2026-11-12, 11-13, 11-17 (11-16 not run: compute).

## Findings about the engine / live code (not setup results)

- **Live-code robustness bug (replay crash):** Testing 1, 2025-05-21: the whole session died with
  `ValueError: zero-size array to reduction operation fmax` in `CWT09-gapdn-bounce-g10-lowerhalf-short.py`
  `stop_price` → `L.a7_stop(f, i)` (an empty look-back slice). If the live runner does not catch per-setup exceptions
  there, the same input would stop a live session. Worth a guard in the lab lib (backlog / owner; not fixed here,
  market hours and research-only).
- **Explore 1 as-live replay crash** on 2026-11-12 and 11-17 (`ValueError: non-broadcastable output operand with shape
  (1,) doesn't match the broadcast shape (2,)`), with that day's frozen setups; today's Explore 1 config replays fine
  on every 2-year session. Explore 1 overlap therefore has 1 session (7 live trades) only.
- **Primary overlap is the weakest (54.5% match):** L3-gap-slope-fromopen-FD matched 15% of 59 live trades (replay_cal
  held-out: 44%). Without poll logs the replay mis-times this open-window setup most.

## Caveats

- **SRCV1** (research/src_value) found that no non-live source has predicted later live results so far. This replay is
  screening only (weight 0) and must earn trust through the overlap check (it does not pass it — RESULTS.md) and a
  later SRC-VALUE re-score on fresh live sessions.
- The sample is small per setup (≤ 7 sessions); most setup records are a handful of trade-days and many carry the
  `1 day` tag. Treat them as a first look, not a verdict.
- Today's config applied to 2024-2025: setups are replayed as they are now, with today's caps; shortable / ETB flags
  are today's, no earnings blackout, revised SIP bars, default poll cadence, modelled spreads.
- Rule-change context (owner 2026-11-02): the replay uses one fixed config, so no rule change falls inside its window.
  The **live** records it is compared with span 10-06..11-17 and include the ledger changes of that period, notably
  LR8 costs from 11-12 (neutralised here: LR8 applied to every live trade), the Primary −2R latch counted in cost R
  from 11-12 (LR3), Testing A full universe from 11-12, Testing D/E/F and Explore 1 / Live Lab accounts starting
  11-12 / 11-05, and the setup moves logged in research/ledger.jsonl and docs/live/assignments.json.

Configurations tried: 1 (one engine, one params file). Every setup is reported in per_setup.csv.
