# FWDREP — forward-replay rep ledger (2026-11-11) — INTERIM (13:15 ET; the replays are still running)

*Educational only — not financial advice. Research only: no config, setup, assignment, ledger or account change. Every
forward-replay ("FWD") number below is a SIMULATED trade from the as-live engine. FWD reps are always labelled and are
never mixed into a live record. R is after costs everywhere. Paper results (live = Alpaca paper journals).*

## The short version (plain English)

- **What a forward rep is:** we replay a setup on a real session that came *after* its rule was frozen (Gen: the id date;
  others: the first session of the setup's current `strategies:` block on any data branch, unchanged since). Nothing was
  tuned on those sessions, so they are out-of-sample, not backtests. The engine is the real live runner loop
  (`mcf.report.team` → `mcf.replay.harness.run_session`, PR #174 fixes): point-in-time Primary universe, live earnings
  blackout, live spread pool, the setup's own account rules.
- **Calibration against live (where the setup also traded live, same sessions): the replay reproduces about 76% of live
  trades** (same setup, symbol, side, entry within 5 min; 77% within 10 min). **On the matched trades replay and live
  agree** (R diff +0.010 ± 0.31 per trade). **But the replay's whole record is rosier than live by about +0.08 R per trade**
  (replay −0.151 vs live −0.230 avg R over 4,539 vs 3,095 trades). That gap is the **haircut**: it comes from composition,
  not fills — replay-only trades (48% of replay trades) average about −0.09 R, while live-only trades (24% of live
  trades) average about −0.25 R.
- **This replay FAILS the rule-21 audit** (≥ 95% of live trades matched, avg R within ±0.03, never optimistic). Under
  RESEARCH_RULES 21, replays are a filter only and may not count toward a record. The owner's 11-11 ask ("forward-replay
  reps next to live, labelled separately") is what this ledger answers; the conflict with rule 21 is the owner's call. To
  respect both, the ledger never edits a live record: FWD reps get a haircut (+0.08 R/trade off) and a weight (0.76 of a
  live rep at most), and are shown in their own columns.
- **The Gen bottleneck is not exposure, it is how rarely the setups fire.** Gen setups already run live in the Gen
  account every session since creation, so the forward replay mostly re-finds the same sessions. It adds trades
  (replay-only: signals the Gen account lost to its own limits — halt, buying power, per-setup cap), but few new *traded
  sessions*. REPS-MIN needs 8 traded sessions; the best Gen records have 5-7.
- **Gen fast-track (interim, 13 of 17 forward sessions replayed): 0 Gen setups clear REPS-MIN 8/30 + OD-IN yet; 6 are
  "NEAR"** (they clear OD-IN on the combined record and miss only the 8-session minimum). Four of them sit in the Gen
  account, where account limits blocked many of their live signals (e.g. GEN-261019-04: 71 submitted, 63 lost to
  limits; GEN-261027-01: 14 submitted, 40 lost) — moving them to a testing area would give them real live exposure.
  **Every NEAR record is a `1 day` record** (best session ≥ 50% of total R).

Files: `gen_fasttrack.csv` (for the after-close apply step), `gen_ranked.csv` (all 93 Gen with the failing gate),
`calibration.csv`, `ledger.csv` (every setup: live | FWD | combined), `ondeck_combined.csv`, `trades/<date>.csv`.
The rest of this file (all accounts, the 10-19..10-22 and 11-11 sessions, the final list) is filled tonight.
