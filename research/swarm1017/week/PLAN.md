# swarm1017/week — live-week rework plan (written before any scoring)

*Educational only — not financial advice. Live paper results; diagnosis, not evidence (RESEARCH_RULES rule 7).*

Scope: every real trade (journal.db run_id=1) 2026-10-06..2026-10-16 on Primary (origin/mcf-data),
Testing 1 (origin/mcf-data-testing, from 10-09), Testing 2 (origin/mcf-data-testing2, from 10-12).
Broker equity per day = first (pre-open) / last (closed) status.json commit per session_date.

1. Week vs last week (10-12..16 vs 10-06..09) per account; trades, win%, avg R, P/L journal + broker,
   cost-adjusted P/L (pnl_adj, the journal's cost-in field), per setup, long/short, with SPY/QQQ/IWM open->close.
2. Last 3 sessions (10-14..16) vs prior 3 (10-09, 10-12, 10-13), same metrics.
3. Per setup (all accounts pooled + per account): n, win%, avg win R / avg loss R, avg R, break-even win%,
   backtest expected R (mcf.report.scorecard._expected), first-half vs second-half trend.
   Ranking for "most promising / worst": shrunk avg R = sum(R)/(n+10) (shrinks small n toward 0) — descriptive only.
4. Rework on SIP 1-min bars (Alpaca market data only, read-only): per trade, replay from entry fill with
   (a) as-traded check, (b) opposite side [HINDSIGHT], (c) tighter stop 0.5R / 0.75R, (d) time stops 30/60/120 min,
   (e) scale-out 1/2 at +0.5R then BE stop, (f) target off/hold to 15:55, (g) skip by day-class known at decision time
   (index return open->entry minute sign vs trade side). Costs: subtract the trade's own cost haircut
   (pnl - pnl_adj, in R) from each variant. Conservative intrabar: stop before target when both in a bar.
   Every variant is counted as a configuration (live data, not a backtest; not gated, no locked data touched).
No history frames, no locked block. No candidate modules from this folder (descriptive task).
