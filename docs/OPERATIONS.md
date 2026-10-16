# Operations: the live paper session

*Educational only — not financial advice.*

## How it runs
- **Where:** GitHub Actions (`.github/workflows/trade.yml`). The repo is public, so hosted runner minutes are free.
- **When:** weekdays. Runs fire at about 08:35 and 08:55 ET, then hourly as standbys. Every run checks the ET clock and exits at once outside 08:00–15:50 ET, on weekends and on market holidays.
- **One session = several jobs.** A job can run at most 6 hours, so each job trades until the close or for about 5h40m, whichever comes first. The next queued job then takes over. All jobs share one concurrency group, so two never run at once. A crashed or skipped job costs at most an hour, and broker-side stops protect open positions in the meantime.
- **Pre-market prep (about 8 minutes):** today's universe (`mcf universe` rules) and per-symbol priors: prior close, ATR, ADV and the volume profile used for relative volume. The result is cached for the day's later jobs.
- **Each minute:** fetch only the new SIP 1-minute bars for the universe (about 13 s for ~5,000 symbols). Then run the enabled setups, run the fill-realism checks and risk checks, and place the order. Every signal is journaled.
- **15:55 ET:** close MCF's own positions. MCF never touches other positions on the account. Then pair the fills into trades, simulate every signal that was not taken (the what-if run), and publish.

## Where the data lives
The **`mcf-data` branch** holds the system's state; the workflow creates the branch on its first run.

| File | What it holds | When it's written |
|---|---|---|
| `status.json` | the live snapshot that the dashboard reads | every 2 minutes |
| `journal.db` | SQLite: signals, orders, trades, what-if trades | every 30 minutes and at the end of each job |
| `universe.csv` | today's universe | daily |
| `discovery/` | the weekly setup scans | weekly |

Dashboard: https://misiti15.github.io/MCF/live/ (GitHub Pages; reads status.json from the mcf-data branch, no connector). EOD reports: https://misiti15.github.io/MCF/live/report.html

## One-time setup (owner)
1. Add the repository secrets **ALPACA_API_KEY** and **ALPACA_SECRET_KEY** (paper keys): GitHub → misiti15/MCF → Settings → Secrets and variables → Actions → New repository secret.
2. Merge this work into `main`. Scheduled workflows only run from the default branch.
3. Optional: Actions → trade → Run workflow (dry run) to watch one job end to end.

## Checks (MarcoFlow lesson: count data, don't trust "process alive")
- The dashboard pill shows "no update for N min" if `status.json` is more than 10 minutes old during trading.
- The data health tile shows how many symbols printed a bar in the last minute. A quiet afternoon is normally about 3,000–3,400 of ~4,950; thin names don't trade every minute.
- The Actions tab lists every job with its full log.

## Outage plan (owner 2026-10-16)
No emails or alerts at any step; everything is logged in `status.json` (`health.data_stale`, `health.data_outages`,
`health.outage_actions`) and the job logs. Settings: `live.outage`, `live.quote_crosscheck_*` in `config/default.yaml`.

1. **Detect** (since 2026-10-15): fewer than 5% of the symbols with a bar in the last 5 minutes = `health.data_stale`.
2. **Backup data feed:** deferred until real funds (docs/DECISIONS.md).
3. **Cross-check before every entry:** the signal's reference price must be within 2.0% of the live SIP quote mid, the
   quote at most 300 s old and the decision bar at most 10 min old; otherwise the signal is journaled `skipped` with a
   `crosscheck: ...` reason. On 2026-10-06..10-16 journals this would have rejected 0 of 3,380 submitted entries (max
   deviation 1.73%, decision bar at most 3.6 min old).
4. **Escalation by outage length** (minutes of continuous stale data, once per outage):
   - 5 (`enter_pause_min`): no new entries; open lots keep their broker-side brackets.
   - 15 (`protect_min`): the stop of every open lot that is in profit by the broker's last price moves to breakeven
     (that lot's own stop leg only; losing lots are left alone).
   - 30 (`flatten_min`): every MCF position is flattened through the normal 15:55 flatten path.
   - The broker API unreachable (clock call failing) for 30 minutes also flattens; if the broker is fully down the
     flatten is retried every poll and done as soon as it answers.
5. **Independent watchdog** (`.github/workflows/watchdog.yml`, every 10 min 09:35-15:55 ET, per account): if
   `status.json` is more than 15 min old while MCF positions/orders are open (trading run dead), or `data_stale` has
   lasted more than 30 min, it cancels the account's open MCF orders and flattens its MCF positions (prefix
   `mcf-`/`mct-`/`mt2-` only; never `mcl-` or anything else). **Default mode `dry`**: it only writes what it would do to
   the job summary. To arm it set the repository variable `MCF_WATCHDOG_MODE=act` (or run it manually with mode `act`).
   It has its own concurrency group and never writes to the state branches.
6. **Fire drills:** `python -m mcf.execution.drill --scenario stale_data|broker_down|run_dead|all` runs each scenario
   against a fake broker and a synthetic clock and checks the order pause -> protect -> flatten and the watchdog
   decisions. The drills also run in `pytest` (`tests/test_outage.py`).

Caveats: a market-wide trading halt also stops bars, so after 30 minutes MCF would flatten into the reopening; the
watchdog sees a dead run only through `status.json`, so a run that is alive but not pushing status (git push failing)
looks dead to it.

## Known limits
- The loop polls once a minute, so entries land about 15–60 s after the signal bar closes. Slippage against the signal is measured on every trade (`slip_bps`). Streaming bars and resting stop-entry orders are the next step if slippage is large.
- `max_daily_loss_r` counts only trades closed so far.
- Paper P/L is still optimistic on limit (target) exits. Those trades are flagged `touch_fill`.
- The account is the same Alpaca paper account MarcoFlow used. MCF orders carry the `mcf-` prefix and MCF closes only its own positions. A separate paper account is still cleaner.
