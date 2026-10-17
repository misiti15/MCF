# swarm1017/week — live-week rework, 2026-10-06..10-16 (Primary, Testing 1, Testing 2)

*Educational only — not financial advice. Live paper results (rule 7): a diagnosis, not evidence. No history frames,
no locked data, no backtest. Configurations scored on live trades: 11 exit variants + 3 day-class thresholds + 1 hour
split = 15 (descriptive; nothing here is gated or proposed for promotion without a lab backtest).*

Inputs: journal.db (run_id=1) and status.json git history from origin/mcf-data, -testing, -testing2 (fetched 10-16 ~20:00 UTC);
SIP 1-min bars (Alpaca market data, read-only) for every traded symbol-day + SPY/QQQ/IWM. Scripts: `fetch.py`, `load.py`,
`summ.py` (summ_out.txt), `setups.py` (setups_out.txt, results.csv = setups_live.csv), `rework.py` (rework_trades.csv),
`rework_summ.py` (rework_out.txt), `daycheck.py` (daycheck_out.txt). Note: Testing 1's first session is 10-09 in the journal
(not 10-07/08). Rework replay fidelity: corr(actual R, replayed R) 0.95, same sign 97%.

Key numbers: see summ_out.txt / setups_out.txt / rework_out.txt / daycheck_out.txt. Summary is the report returned to the lead.
Candidate modules: none (descriptive task). Backlog suggestions are in the lead report.
