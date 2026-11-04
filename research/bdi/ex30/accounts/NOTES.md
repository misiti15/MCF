Educational only — not financial advice

# ex30 / accounts — three new paper accounts wired (2026-11-03)

**Trimmed to 2 accounts (owner 2026-11-03 evening):** Explore 2 (`mx2-`, `mcf-data-explore2`) is dropped; only Live Lab
(`mll-`) and Explore 1 (`mx1-`) are wired. **Explore 1 is the home for setups trimmed for low activity (INACT2):** a
setup trimmed for low activity moves there for more exposure, never just switched off; the 7 INACT2 setups (IDX1 trail,
IDX1 hold, IDX2, IDX3, IDX5, LD4, LD5) move to Explore 1 when it opens. This branch is NOT merged until the owner adds
the Alpaca keys (ALPACA_LIVELAB_* / ALPACA_EXPLORE1_*); ROLL1 (roll-out order) is deferred until then. Rows below that
mention Explore 2 describe the original 3-account draft.

Branch `claude/accounts-3new` (from `claude/charming-mccarthy-i3rhhr`), pushed, **no PR opened, not merged**. It touches
`config/` (new overlays only) and live paths (`.github/workflows/*`, `mcf/execution/*`), so it merges outside
09:30-16:00 ET after the owner's review. No existing account's setups, exits or risk rules change. No bar history was
read (the locked block is not touched). Number of configurations tried: 0 (wiring, not research).

## What is wired

| key | label | orders | state branch | concurrency group | secrets the owner adds |
|---|---|---|---|---|---|
| livelab | Live Lab | `mll-` | `mcf-data-livelab` | `mcf-trade-livelab` | `ALPACA_LIVELAB_API_KEY`, `ALPACA_LIVELAB_SECRET_KEY` |
| explore1 | Explore 1 | `mx1-` | `mcf-data-explore1` | `mcf-trade-explore1` | `ALPACA_EXPLORE1_API_KEY`, `ALPACA_EXPLORE1_SECRET_KEY` |
| explore2 | Explore 2 | `mx2-` | `mcf-data-explore2` | `mcf-trade-explore2` | `ALPACA_EXPLORE2_API_KEY`, `ALPACA_EXPLORE2_SECRET_KEY` |

Market data stays on the primary SIP keys (`ALPACA_API_KEY` / `ALPACA_SECRET_KEY`) for every job.

Overlays `config/account_{livelab,explore1,explore2}.yaml` (identical sizing, from the livelab NOTES "Exact pieces needed"):
`strategies_exclusive: true`, `strategies: {}` (no setup enabled), 200 slots, `buying_power_multiple 2.0` →
$100k x 2 / 200 = **$1,000 per lot** (asserted in the test), `max_positions_per_strategy 10`,
`max_setup_daily_loss_r: null` (per-setup stop off), `max_daily_loss_r 120` (the Testing account backstop; the livelab
NOTES draft said 60, the task said "as in Testing"), `max_trades_per_day 1500`, `max_stop_cost_r 0.15` (the Testing
cost filter CF 2026-10-29 — owner may want it off for the exploratory accounts; one line each),
`block_twin_same_symbol false`, `scale_out_max_per_day 0`, `retry_after_release` / `longs_first_on_ties` as Testing.
Not built (separate runner changes listed in the livelab NOTES items 3-7): the cross-setup symbol lock switch, the
shadow_class tag, `mcf/report/livelab.py`, `mcf/research/lane.py`, fail-fast automation.

Where the accounts were added (every `graveyard` enumeration):
- `.github/workflows/trade.yml`: matrix rows, concurrency group / COID prefix / state branch / both secrets; the skip
  check requires both secrets; **new "Setup check" step**: any account with no enabled setup skips prep and trading
  (~1 min job instead of a 6.5 h idle session). A config error fails the job (bash -e + pipefail), never a silent skip.
- `watchdog.yml`: matrix + env; **new skip** when the account's state branch does not exist yet (never traded → no MCF
  position can exist), so empty accounts do not install Python every 10 minutes.
- `eod.yml`: matrix + state branch (EOD already skips accounts with no state branch; no email for non-Primary).
- `session-guard.yml` + `mcf/execution/session_guard.py`: HAS_* flags; `has_setups()` drops an exclusive overlay with no
  enabled setup, so the guard does not re-dispatch trade.yml 6 times a day for an account that skips on purpose.
- `longhold.yml` + `mcf/longhold/broker.py`: the new API key ids join the long-hold key-separation check.
- `mcf/execution/outage.py` (`MCF_PREFIXES` + `mll- mx1- mx2-`; watchdog refuses unknown prefixes), docstrings.
- `mcf/report/assignments.py` (ACCOUNTS; `docs/live/assignments.json` regenerated: 3 empty lists + labels, no setup
  moved, `last_change` unchanged), `daily_post.py` (accounts, leaderboard, colours; accounts with no status.json are left
  out of the post; "All 5" labels now count the accounts shown), `playing_time.py`, `mcf/replay/{export,harness,store}.py`,
  `mcf/research/generator/screen.py` (overlap check also covers the new accounts' setups).
- Dashboard `docs/live/index.html` (all A / ACC / BRANCH / LBL / ACCOUNTS lists, account switch, all-accounts cards,
  short codes LL / X1 / X2, move targets: a pass goes to Testing 1 / 2) and `docs/live/report.html`.
- Tests: `tests/test_new_accounts_1103.py` (8 tests: sizing and empty overlays, every workflow expression evaluated for
  all 8 accounts, guard / long-hold / prefixes, reports and dashboard, post skips unstarted accounts);
  `tests/test_graveyard_account.py` two string checks widened for the longer matrix.
- Full pytest: **472 passed** (464 + 8 new); one timing test (`test_poll_log::test_overhead_and_size_on_a_live_sized_universe`)
  failed once under machine load (load avg 7 from other agents) and passes on re-run.

## Capacity with 8 intraday accounts — what could break

1. **GitHub Actions concurrent jobs (the main risk).** The repo is public, so standard-runner minutes are free and
   unmetered; the limit is concurrency: **20 concurrent jobs on a Free account, 40 on Pro** (per account, all repos).
   During the session: 8 trade jobs running all day + watchdog bursts of up to 8 jobs (~1-2 min every 10 min) +
   session-guard 1 + long-hold snapshot 1 (+ pages / EOD around the close) = **~18-19 at the :05/:15/:35 marks**.
   That is at the Free limit. If it is hit, jobs queue: a watchdog check runs late, or — worse — a trade handover
   (each job hits the 355-minute limit around 14:30 and its queued standby must get a runner) waits for a free slot,
   losing polls in the last 90 minutes. Mitigations if it shows up: owner on GitHub Pro (40); watchdog every 15-20 min
   or one watchdog job looping over all accounts; stagger the pre-open cron. Hourly standby runs do not use a runner
   while pending in their concurrency group. Empty accounts cost ~1 runner minute per trigger (Setup check / branch
   skip), not a slot all day.
2. **Alpaca market data, one shared SIP key.** Each job polls the whole ~4,000-symbol watchlist every poll: ~10 bar
   requests (400 symbols each, 8 threads) + quote checks per entry. 8 jobs ≈ 100-150 requests/min steady; the Algo
   Trader Plus limit is 10,000/min (the plan is per key), so steady state is fine. Bursts to watch: the 08:35 pre-open
   prep (all 8 jobs miss the same-day priors cache at once and each runs prep), and a mid-day restart/handover that
   refetches the day from 09:30 (~150 paged requests per job). A 429 is caught per batch (one batch lost, the session
   continues), so the symptom is silent missed bars, not a crash. If the plan were ever the free 200/min tier, 8 jobs
   would exceed it.
3. **Alpaca trading API**: per account key (200/min each), so separate keys do not compete. Each new account must be
   its own paper account; the `mll- / mx1- / mx2-` prefixes keep the watchdog and outage flatten inside the account.
4. **Poll coverage.** Each job has its own runner (2 vCPU), so new accounts do not slow the existing ones' CPU.
   Testing 2 / Graveyard / Gen already run at 76-80% of the 384 1-minute polls (nightly1030) because poll time grows
   with the number of context setups. A Live Lab / Explore account with 20 context-heavy setups will be in the same
   range; exploratory setups that use many opt-in context columns will poll slowest. Check `polls` per account after
   the first session before filling 20 seats.
5. **Buying power**: $1,000 x 200 slots = $200k = equity x 2.0, inside paper buying power (4x intraday on $100k);
   slots bind before buying power. 10 lots per setup x 20 seats = 200 slots, so one setup cannot take the account.
6. Prep cache: the same-day priors cache key is shared; concurrent saves from 8 jobs produce "unable to reserve cache"
   warnings (already the case with 5), not failures.
7. Dashboard / post: every page fetch now asks 3 more raw.githubusercontent.com branches; missing branches return 404
   and are skipped until the accounts start.

## Owner actions

1. Create three Alpaca paper accounts (each its own account, not the long-hold profile).
2. Add six repository secrets: `ALPACA_LIVELAB_API_KEY`, `ALPACA_LIVELAB_SECRET_KEY`, `ALPACA_EXPLORE1_API_KEY`,
   `ALPACA_EXPLORE1_SECRET_KEY`, `ALPACA_EXPLORE2_API_KEY`, `ALPACA_EXPLORE2_SECRET_KEY`.
3. Merge this branch outside market hours; then add setups to an overlay (each one a setup move + assignments + ledger).
   Until both secrets and at least one setup exist, every job skips the account.
