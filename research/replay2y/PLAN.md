# 2-year live-code replay — plan (written 2026-11-18, before any replay result was read)

*Educational only — not financial advice. Research only: no trading, setup, exit or config change. USAGE PLAN item 3,
owner-approved 2026-11-18. Terms as in docs/GLOSSARY.md ("2-year replay (planned)", "2-year history", "Session replay").*

## Question

Run the LIVE runner's decision path (mcf/replay/harness.py + the calibrated replay mcf/replay/livecal.py with
research/replay_cal/params_v2.json) over the full-universe 2-year history stored so far, for every enabled setup in
every account, and ask (a) does the engine reproduce live where it overlaps live, and (b) what does each setup's
replay record look like over the history.

## Engine (fixed now)

- `python -m mcf.replay run --account A --universe live --live-cal research/replay_cal/params_v2.json --fills costs`
  (fast path on, as every replay so far). Config = **today's** account files (`config/default.yaml` +
  `config/account_<A>.yaml` as committed on origin/claude/charming-mccarthy-i3rhhr at the worktree's base commit):
  every enabled setup, account caps / lots / latches / twin rules as they are today.
- Accounts: primary, testing, testing2, gen, graveyard, livelab, explore1, testingd, testinge, testingf (206 enabled
  setup slots).
- Universe = the session pack's point-in-time universe (meta `universe`); priors = the live prep (`build_priors`) from
  the session's 1day pack + the 24 calendar days of 1-minute packs before it (downloaded first, so the 5-minute
  profiles are built from real prior bars — the replay_cal "full priors" fix).
- What the 2-year sessions lack vs live (stated, not fixed): no poll log (default cadence), no recorded quotes (spread
  model from TRAIN live quotes), shortable / ETB = today's flags, no earnings blackout on record, bars are the
  revised SIP bars.
- Costs: R per entry lot = (pnl − LR8 live cost model on the replay's own fills) / risk, every day
  (`research/replay_cal/score.py::lots`, the same function the calibration scorecard used).

## Sessions

- Stored 2-year months (docs/live/storage.json): 2024-09, 2024-10, 2025-03..2025-06.
- **Locked block 2024-11-01..2025-02-28 never read.** `store.check_dates` also refuses every session whose priors
  look-back (50 + 10 calendar days) reaches into it, i.e. 2025-03-03..2025-04-29: those packs are stored but cannot be
  replayed with full priors. They are skipped, not degraded; `MCF_HIST_ALLOW_LOCKED` is never set.
- Replayable: 2024-09-16..2024-10-31 and 2025-04-30..2025-06-30. Sessions in the first 24 calendar days after
  2024-09-16 have partial 5-minute profiles (no earlier pack); they are run and flagged, and every per-setup number is
  also given without them (sensitivity).
- Streaming: per month, pull that month's packs + the 24 days before, replay all accounts, delete packs no longer
  needed. Work dir: the session scratchpad `rep2y/`.

## Overlap check (engine trust, run on live sessions)

- Same engine and settings as above, but each session's setups **as they traded** (`--as-live`, frozen setups on the
  data branch + config committed before the open), poll logs and recorded quotes **off** (the 2-year sessions have
  neither), on live sessions 2026-10-06 onward (packs bars-2026-10/11) for every account with a journal.
- Scored with research/replay_cal/score.py's `lots` / `match`: match % (same setup + symbol + side + decision bar),
  extra %, matched-pair R bias (replay − live, LR8 both sides), total-R gap, per account and per setup.
- Reference bar (TARGETS.md, research/replay_cal): ≥ 98% match, ≤ 2% extra, |bias| ≤ 0.01R. Replay_cal held-out with
  poll logs and quotes was 87.1% / 26.2% / +0.005R. Nothing is tuned on the overlap result.

## Outputs

1. Per setup (account-tagged): trades, sessions with a trade, sessions run, avg R after LR8, total R, win %,
   avg R w/o best day + best day's share of total R (`1 day` tag at ≥ 50%), green-day %, per-period split
   (2024-09/10 vs 2025-05/06).
2. Overlap check as above.
3. Comparison with the old 2-year screen (`docs/live/sim_inputs.json`) and 2-year backtest
   (`research/history2y/rescore.csv`): sign agreement and the largest disagreements.
4. Replay vs live record per setup; low-rep setups (< 20 live trades) with strong replay records flagged for the
   REPS2 fast lane (flag only: no move).
5. Remaining storage ETA + nightly job plan.

Configurations tried: 1 (one frozen engine, one params file); the overlap run is a check, not a variant. No setup is
changed, so no locked holdout is scored. Every setup is reported, good or bad.

## Caveat

SRCV1 (research/src_value) found that no non-live source predicted later live results so far. This replay is screening
only (weight 0) until it earns trust via the overlap check and a later SRC-VALUE re-score.
