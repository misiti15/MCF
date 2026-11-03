Educational only — not financial advice

# night1102 / livelab — plan (written before any number was computed, 2026-11-03 ~02:00 UTC)

Research only. No config / setup / exit change, nothing merged. Locked block 2024-11-01..2025-02-28 never loaded
(nothing here reads bar history at all; only live journals, configs and the backlog).

Inputs: `journal.db` of the 5 state branches (run_id 1 live paper, run_id 2 what-if), `config/account_*.yaml`,
`research/backlog.jsonl`, `research/ops/blocked_audit.md`. Live R = pnl_adj / (|entry-stop| x shares) (costs and
fill-realism in, as night1102/regime and simple).

Pre-declared analyses (script `livelab.py`):
A. Capacity per account/session: trades, peak concurrent lots, enabled setups, buying-power rejects, place-in-line.
B. How fast does live data give a verdict? For every setup x account with >= 8 live sessions and >= 40 trades:
   early record (first 5 sessions, first 10 sessions, first 30 trades) vs the rest (later trades only).
   Spearman rank correlation early vs later; sign agreement. Kill rules (grid, each counted as a configuration):
   kill after K trades if avg R <= x, K in {15, 30, 45}, x in {-0.40, -0.30, -0.20, -0.10, 0.00}: share of killed
   setups whose later record was > 0 (false kill) and R saved on the later trades.
C. Does a backtest gate predict live? Gen setups: screen train/valid exp vs live avg R (Spearman).
D. Day-clustered noise: per-setup daily R variance -> sessions needed for t = 1.5 at a true +0.10R / +0.20R.
E. Shadow coverage: share of skipped / rejected live signals that already get a what-if trade (run_id 2).
F. Backlog: count idea / rework (+ near-miss tagged) entries that a minimal gate would admit, by bucket.
Caveat known up front: the live window is 20 sessions with 5 up / 5 down / 10 quiet days, so "early vs later"
compares different market days; a low correlation can be regime, not noise.
