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

---

## Addendum A (2026-11-18 18:30 UTC, after a timing test, before any 2-year result was scored)

- **Compute:** one account-session takes ~500-800 s on one core (testing2 2025-06-02: 799 s; primary 494 s, testing
  608 s; the per-symbol feature frames of the full ~4,200-name universe dominate, so running accounts together saves
  little). All 76 replayable sessions × 10 accounts ≈ 34 h on this 4-core box — not possible in one sitting.
- **Sample (fixed now, before results):** 13 sessions spread evenly over both stored periods —
  2024-10-11, 10-17, 10-23, 10-29 and 2025-04-30, 05-07, 05-14, 05-21, 05-28, 06-02, 06-10, 06-18, 06-26 (2024-09
  sessions skipped: < 24 days of prior packs). Jobs run in account tiers: (1) primary, testing, testing2, explore1,
  livelab; (2) testingd, testinge, testingf; (3) gen; (4) graveyard. Whatever is not finished is reported as not run;
  the nightly job (RESULTS.md) extends the sample to every replayable session.
- **Overlap sample:** live sessions 2026-11-12, 11-13, 11-17 (+ 11-16 if time), all 10 accounts, `--as-live`,
  params_2y.json (= params_v2 with poll logs and recorded quotes off).
- **Fast-lane flag (REPS2), fixed now:** live trades < 20 (pooled over accounts, sessions to 2026-11-17) AND replay
  trades ≥ 30 AND replay avg R after LR8 > +0.027R (the replay_cal haircut) AND avg R w/o best day > 0 AND best-day
  share < 50% AND green-day % ≥ 50% AND avg R > 0 in both periods (2024-10 and 2025). Flag only, no move.
- **Supports / contradicts:** setups with ≥ 30 replay trades and ≥ 20 live trades; supports = same sign, contradicts =
  opposite sign; ranked by |replay avg R − live avg R| (contradicts) and by min(|replay|, |live|) (supports).

## Addendum B (2026-11-18 18:40 UTC, before any 2-year result was scored)

storage.json (generated 2026-11-18 09:19 ET, merged in after addendum A) now shows the 2-year history stored through
2026-01 (265 of 435 sessions). To cover the second half of 2025 as well, a **batch 2** of one session per month is
added after batch 1 (tier-1 accounts first, same engine): 2025-07-15, 2025-08-14, 2025-09-16, 2025-10-15,
2025-11-13, 2025-12-11, 2026-01-14. Periods for the both-periods test become: 2024-10, 2025 H1 (04-30..06-26),
2025 H2 + 2026-01; the fast-lane rule then requires avg R > 0 in at least 2 of the 3 periods with trades (and none
below −0.10R). Base commit of the config and code replayed: 8a9a0cb6c (the merge brought only research files and
storage.json; no config or code changed).
