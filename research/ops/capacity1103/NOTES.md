Educational only — not financial advice

# capacity1103 — will more accounts overload GitHub or our system? (measured 2026-11-03 ~11:00 ET)

Owner 2026-11-03: "Make sure more accounts will not overload GitHub or our system — that is a priority over having an
additional account." This note gives measurements, not estimates, wherever the data exists. Every estimate is labelled
as one. Research / ops only: no config, setup, exit or live-path change is merged here. Three small load reducers sit
on a new, unmerged branch, `claude/capacity-1103` (see "Prepared on a branch").

**What was measured.**
- GitHub: every workflow run in misiti15/MCF created from 2026-10-27 to 2026-11-03 ~10:55 ET, and every job in those
  runs. That is 342 runs and 1,044 jobs, read through the repository-scoped Actions REST API (`gh api`). This is the
  same data the GitHub MCP `actions_list` tool returns; it was spot-checked against MCP on trade.yml.
- Jobs: the full logs of the 105 trade jobs that ran (10-27..11-02).
- Poll logs: `polls/<day>/` on all 5 data branches for 10-30, 11-02 and 11-03 (11-03 up to 10:54 ET), read with
  `mcf.execution.runner.read_poll_log`.
- Script: `measure.py` (re-run it after every rollout step). Output: `results.json`.

**Rule / config changes inside the window** (`research/ledger.jsonl`; they change setup counts per account, so they
matter for poll speed):
- 10-27: session guard live, GX1 5-minute lab clock (every account), GEN seeds.
- 10-28: Primary size ~$4k.
- 10-29: Primary -2R per-setup stop, generator paused, BAR90.
- 10-30: Testing cost filter CF.
- 11-02: R2A legs into Testing 2, NS3-FD and RW4-FD to the Graveyard.
- 11-03: MF3-FD and MF5-FD to the Graveyard, SO-1A, RW3S into Testing 2.
- 11-04 (pending): DM-N3.
- The ET clock moved from EDT to EST on 11-01, and every time below is ET.

## 1. GitHub Actions: concurrency, queueing, run time

**Plan / limit.** The API does not show the plan. `GET /user` returns `plan: null` to this session's token, and
user-level endpoints are blocked. The account was created 2026-10-05 and has 1 public repository, so it is very
likely **GitHub Free**. Free allows **20 concurrent jobs** across all of the account's repositories (Pro allows 40).
The repository is public, so standard-runner minutes are free. **Concurrency is the binding limit, not minutes.** The
plan is still unverified; the owner can see it under Settings → Billing and plans.

**Standby jobs hold no runner (measured).** A standby trade job that waits in its concurrency group shows
`started_at = created_at`, but it stays `pending` with no runner. 150 such jobs over the week had no runner name, and
none is counted below. When a newer standby arrives, GitHub cancels the older pending one. That accounts for
5 of the 8 trade runs on 11-02.

**Peak concurrently running jobs, 09:00-16:30 ET** (exact, second-resolution sweep over jobs that held a runner):

| day | exact peak | at (ET) | mix at the peak | per-minute median | minutes with ≥ 10 jobs |
|---|---|---|---|---|---|
| 10-27 | 10 | 09:48 | 5 trade + 5 watchdog | 5 | 20 |
| 10-28 | 10 | 09:54 | 5 trade + 5 watchdog | 5 | 20 |
| 10-29 | 10 | 09:56 | 5 trade + 5 watchdog | 5 | 21 |
| 10-30 | 11 | 11:36 | 5 trade + 5 watchdog + 1 session-guard | 5 | 21 |
| 11-02 | **15** | **14:34** | **5 trade + 5 watchdog + 5 eod** (the stand-by hand-over) | 5 | 21 |
| 11-03 (to 10:55) | 10 | 09:08 | 5 trade + 5 watchdog | 5 | 5 |

**Today's measured peak is 10.** The week's peak is 15, at the 14:34 hand-over on 11-02. It was **never above 15 of
20**. Steady state is exactly 1 runner per trading account. A burst is short: watchdog jobs run a median of 0.63 min
and EOD skip jobs 0.07 min.

**Why the hand-over is the peak.** Each trade job reaches its 355-minute limit about 347 minutes after the 08:4x start,
at about 14:31 ET. Its finished run then triggers eod.yml (`workflow_run`), which starts one runner per account just to
skip. If a watchdog fire lands in the same minute, the result is 3 × N jobs at once.

**Queue delay** (job created → started) and **minutes per job**, all jobs that held a runner, 10-27..11-03:

| workflow | jobs | queue median / p90 / max (s) | minutes median / p90 | total minutes |
|---|---|---|---|---|
| trade | 110 | 3 / 2,689* / 3,190* | 0.3 / 346 | 10,702 |
| watchdog | 275 | 2 / 3 / 377 | 0.63 / 1.0 | 178 |
| eod | 285 | 2 / 8 / 72** | 0.07 / 0.6 | 46 |
| longhold | 74 | 2 / 3 / 12 | 0.68 / 0.8 | 63 |
| session-guard | 54 | 2 / 3 / 8 | 0.35 / 0.5 | 20 |
| pages | 69 | 3 / 4 / 289 | 0.2 / 0.7 | 21 |
| setup-freeze (PR check) | 26 | 2 / 3 / 91 | 0.5 / 0.8 | 18 |

\* For trade, "queue" includes the intended wait in its own concurrency group. The real runner gap at the hand-over
(old job completed → standby started) was **2-9 s over all 25 hand-overs** (median 3 s).
\** EOD's 30-72 s waits happen at the close, behind the account's earlier EOD run in its own concurrency group. That
is not a runner shortage.

**One GitHub-side slowdown was seen, and it was not our limit.** On 10-27 between 13:07 and 13:37 ET, every workflow
waited 1.5-6 minutes for a runner (watchdog up to 377 s, pages 289 s). Only **5-6 jobs** were running at the time. That
points to GitHub's hosted-runner provisioning, not our concurrency. Adding accounts does not cause this kind of
incident, but a hand-over that falls inside one would lose polls.

**GitHub cron is throttled to about once an hour.** The watchdog cron says every 10 minutes, but it fired 9 times on
11-02 (09:10, 09:59, 10:55, ...), out of about 38 slots in its window. The session-guard cron behaved the same way.
Bursts are therefore about hourly, not every 10 minutes. This also means the outage watchdog checks about hourly. That
is a known limit of GitHub schedules, and it is separate from capacity.

**Projection for 6, 7 and 8 accounts.** These are computed from the measured parts and assume every account trades all
day. The parts per account are 1 trade job (all day), 1 watchdog job a fire and 1 EOD job a trade-run completion.
Fixed jobs are session-guard, long-hold, pages and a PR check, at about 4 when they coincide.

| accounts N | steady | typical hourly burst (trade + watchdog + guard) | worst coincidence today (3N + 4) | vs Free 20 |
|---|---|---|---|---|
| 5 (measured) | 5 | 10-11 | 19 (seen: 15) | OK |
| 6 | 6 | 13 | 22 | over at the worst minute |
| 7 | 7 | 15 | 25 | over at the worst minute |
| 8 | 8 | 17 | 28 | over at the worst minute |
| 8, with R1-R3 below | 8 | 10 | **N + 5 = 13** | OK (65%) |
| 8, with R1-R3 below, on Pro | 8 | 10 | 13 | 33% of 40 |

**What "over" means.** Nothing fails. Jobs above 20 wait for a slot. The extra jobs are watchdog and EOD jobs that run
under a minute, so a standby trade job caught in that minute would start about 1 minute late, and the hand-over would
lose 1 more poll.

**The real overload risk is a research matrix, not an account.** `cwt-transcripts.yml` has `max-parallel: 20` with
up to 355-minute jobs, and `reddit-archive.yml` has no cap. Either one, dispatched during a session, would take all 20
Free slots for hours. Every standby would then queue, and the 14:31 hand-over would wait hours. Neither ran this week
(last runs 10-09..10-12, all outside market hours). R4 below caps both at 4.

The 3 empty accounts on `claude/accounts-3new` (secrets set, no setup) also start a runner for each trade, watchdog
and EOD trigger, for a few seconds to about 1 minute each. They count in the burst minutes until R5 skips them at the
job level.

## 2. Our system: market data, poll coverage, hand-overs

**Rate limits: no 429 in the week (measured).** The 105 trade job logs (10-27..11-02) contain **0 HTTP 429 / "too
many requests" / rate-limit lines**. They contain **4 `fetch error batch` lines in total**, all `Connection aborted /
RemoteDisconnected`. Each one lost 1 of 8 batches (400 symbols) for one poll. Fetch time per poll (`ms` in the poll
log) has a median of 4.5-8.1 s and a p90 of 6.5-10.5 s, with no trend across the day.

**Request rate (from code, an estimate: requests are not counted on the wire).**
- Each poll fetches the watchlist (about 2,955 symbols today) in batches of 400, which is 8 requests. Each request
  asks for the last 3 minutes, a single page. That gives about 8 bar requests a minute per account: **about 40/min for
  5 accounts and about 64/min for 8**.
- A hand-over restart refetches from 09:30 (about 0.9 M bars), which is **about 90 paged requests per account in about
  a minute**.
- Pre-open prep (5-minute profiles for about 4,800 symbols, batch 100, about 24 days) comes to **about 600 requests
  per account over about 2.5 min**.
- The SIP feed returns real-time bars, which suggests the Algo Trader Plus plan at 10,000 requests/min per key. That
  is inferred, not verified. Under it, 8 accounts at the worst burst (8 preps at once, about 2,000/min) stay at about
  20%. On the free 200/min tier, even today's 5 preps would fail. They do not, which supports the inference.

**Duplicated prep (measured).** Every morning all 5 accounts miss the same-day priors cache together. Each runs its own
prep (universe plus priors, 2-3 min). 4 of the 5 then fail to save the cache ("Unable to reserve cache"). On 10-30
this gave **different universes across accounts (4,676 vs 4,678 symbols)**. With 8 accounts the work repeats 8 times.
R6 below runs prep once.

**Poll coverage (measured: distinct poll minutes / expected 1-minute polls).**

| account (setups today) | 10-30 | 11-02 | 11-03 to 10:54 |
|---|---|---|---|
| Primary (10) | 97% | 100% | 100% |
| Testing 1 (25) | 97% | 100% | 100% |
| Testing 2 (45) | 79% | 77% | 94% |
| Graveyard (33) | 80% | 91% | 82% |
| Gen (93) | 76% | 66% | 85% |

The losses come from the 5-minute decision polls. These take 90-215 s on Testing 2, the Graveyard and Gen (lab setups
are evaluated on the completed 5-minute bucket), so the next 1-3 one-minute polls are skipped. Coverage tracks how many
setups an account has (and how much context they use). It does not track the number of accounts: every job has its own
2-vCPU runner, and fetch times did not rise. **A new account costs no other account any coverage. Its own coverage
depends on its seat count.** Up to 25 plain setups stay at 97-100%.

**Hand-overs (measured).**
- In all 25 hand-overs (5 accounts × 5 days), the runner switched in 2-9 s.
- The poll pause was measured from the poll logs on 11-02: 132-150 s on Primary, Testing 1 and the Graveyard, and
  229-281 s on Testing 2 and Gen (where it adds to a 5-minute decision poll). The pause is setup plus the refetch from
  09:30.
- **On 10-30 all 5 accounts lost 11-14 minutes (14:36-14:49 ET).** In each new job, `actions/setup-python`'s
  pip-cache download hung for exactly 600 s, the default 10-minute cache segment timeout of GitHub's cache service.
- This is the largest measured system loss of the week. It hits every account at once, so more accounts mean more
  setups lose those minutes. R7 below cuts it to at most 1 min.

## 3. Load reducers (effect in jobs at the worst minute, N accounts)

| # | change | effect | status |
|---|---|---|---|
| R1 | eod.yml job-level `if`: skip `workflow_run` triggers from **cancelled** trade runs (replaced standbys) | 5 of 8 EOD fires a day start no runner (11-02: 25 of 40 EOD jobs) | **prepared** on `claude/capacity-1103` |
| R2 | one watchdog job that loops over the accounts (one checkout and install, then N quick checks) instead of an N-row matrix | watchdog burst N → 1 (8 accounts: -7 jobs) | design only (live path; needs its own tests) |
| R3 | eod.yml: one small `when` job (time window or dispatch), then the matrix `needs: when` and `if: needs.when.outputs.run == 'true'` | the 14:31 hand-over EOD burst N → 1; the real close still runs N (trade jobs are finished by then) | design only |
| R4 | research matrices capped: `cwt-transcripts` `max-parallel` 20 → 4, `reddit-archive` → 4 (plus a test that any non-account matrix is ≤ 4) | worst research burst 20 → 4 | **prepared** |
| R5 | a `plan` job computes the active accounts (both secrets set and ≥ 1 enabled setup); the trade, watchdog and EOD matrices use `fromJSON(needs.plan.outputs.accounts)`, falling back to the full list if `plan` fails | empty accounts cost 0 runners (today's branch: 3 jobs per trigger) | design only (put it on `claude/accounts-3new` before merging) |
| R6 | one `prep` job before the matrix saves the priors cache, and the trade jobs only restore it | 8 preps → 1 (about 600 data requests and 2-3 runner-min per account a morning), and one universe for all accounts | design only |
| R7 | `SEGMENT_DOWNLOAD_TIMEOUT_MINS: "1"` on the trade job | a hung cache download costs at most 1 min (then a plain pip install of about 20 s) instead of 10 | **prepared** |
| — | stagger crons | little effect: GitHub fires them about hourly anyway | not needed |
| — | merge Graveyard + Gen into one job | **not recommended**: both are CPU-bound already (Gen 66-85% coverage), and two broker accounts in one process add risk | — |

With R1-R3 the worst minute is N + 5 (8 accounts: 13 of 20). With R4 added, a research dispatch adds at most 4 more
(17 of 20).

## 4. Recommended rollout (safe order)

0. **Before any new account** (after the close, owner OK, setup-freeze outside 09:30-16:00):
   - merge `claude/capacity-1103` (R1, R4, R7);
   - add R5 to `claude/accounts-3new`, so empty accounts start no jobs;
   - do not dispatch research workflows during a session.
1. **Live Lab only.** Merge `claude/accounts-3new`. The owner adds only the two Live Lab secrets; Explore 1 and 2 stay
   without secrets, so they skip. Run 2 sessions, then run `measure.py`.
2. **Go / no-go gates for the next account** (all of them, on both sessions):
   - exact peak ≤ 14 (70% of 20);
   - no non-trade job queued > 60 s while fewer than 15 jobs ran (more than that is GitHub-side; note it and re-run);
   - every hand-over runner gap ≤ 10 s and poll pause ≤ 3 min;
   - each existing account's poll coverage within 3 points of its last-5-session level;
   - 0 HTTP 429 in the trade logs, and fetch-ms median not up by more than 25%.
3. **Explore 1**, 2 sessions, same gates. Build R2 + R3 during this step.
4. **Explore 2**, 2 sessions, same gates (8 accounts; projected worst minute 13 with R1-R3).
5. **Optional, owner's call:** GitHub Pro (40 concurrent jobs) doubles the headroom. The current plan could not be
   read and needs confirming.

Sizing of the new accounts' seats matters more than the account count. The Live Lab cap of 20 seats (see
`research/bdi/livelab_pipeline/PLAN.md`) keeps that account in the 97-100% coverage band that Testing 1 shows with 25
setups.

## Prepared on a branch (not merged)

Branch `claude/capacity-1103` (from `claude/charming-mccarthy-i3rhhr`). It touches live-path workflows, so it merges
only outside 09:30-16:00 ET and after the owner's review.
- `.github/workflows/eod.yml`: R1 job-level `if`.
- `.github/workflows/cwt-transcripts.yml`, `reddit-archive.yml`: R4 `max-parallel: 4`.
- `.github/workflows/trade.yml`: R7 `SEGMENT_DOWNLOAD_TIMEOUT_MINS: "1"`.
- `tests/test_capacity_1103.py`: 3 tests.

Full pytest on the branch: **468 passed**.

Number of configurations tried: 0 (measurement and ops design, no setup scored).

Educational only — not financial advice.
