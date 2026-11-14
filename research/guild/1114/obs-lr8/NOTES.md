# OBS-LR8 — what the LR8 cost basis does to live R (Observer, 2026-11-14 ~05:55 ET)

Skeptic's checklist 37 (LR8: live pnl_adj on the live cost model from 11-12; old trades not rewritten). Checked on
Primary, Testing A, Gen, Graveyard journals (18,241 trades, 10-06..11-13) with scripts/recompute_pnl_adj.py (read-only).
Repro: recompute_pnl_adj.py --journal ... --out X.csv ; python lr8check.py X.csv -> lr8check_out.txt. 0 configs.
1. Confirmed: on pre-11-12 trades LR8 costs 0.035-0.040R more than booked (Primary 0.040, Testing A 0.039, Graveyard
   0.037, Gen 0.035). Post-11-12 booked == LR8 on 100% of trades, so the script and live booking agree.
2. LR8's cost is EXIT-LINKED: stop exits ~0.09-0.10R (median 0.07), targets ~0.03, flattens ~0.03. Its per-trade mean
   moves with the stop share: pre 0.061R (38% stops) vs post 0.042R (23% stops); post at the pre exit mix 0.050R.
   So a flat '-0.04R' adjustment misstates setups by their stop rate: recompute per trade (the script), don't shift.
3. Raw R (pnl / risk = r_multiple) is the same basis on both sides of 11-12 (pnl/risk == r_multiple to 0.0000 in every
   account and period). Gross-first series need no LR8 fix. OBS-ETFLIVE used r_multiple: unaffected.
Use: for any series crossing 11-12, report raw R (gross) plus LR8-recomputed R for every trade. The exit mix also shifts with
the tape: post-11-12 had fewer stop-outs, so 'costs fell after 11-12' is mostly the exit mix, not the model.
Educational only — not financial advice.
