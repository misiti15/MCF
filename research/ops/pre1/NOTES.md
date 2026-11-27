Educational only — not financial advice

# PRE1 — morning borrow / short-volume recorder (owner approved 2026-11-03)

Owner 2026-11-03: "yes, if the system, memory and load allow it, start recording borrow and short-volume data each
morning so we can learn from it later." Proposal: research/bdi/eu1103/preopen/NOTES.md (PRE1-record).
Research data only. No setup, exit, sizing or live-path change; trade.yml is untouched. No ledger entry needed.

**What.** `mcf/data/borrow_record.py`, run by `.github/workflows/borrow-record.yml` at ~09:08 ET on market days:
- Alpaca asset flags (one read-only GET /v2/assets, primary keys): shortable, easy_to_borrow, borrow_status,
  marginable, margin_requirement_short, maintenance_margin_requirement, PTP. Kept for every tradable common stock / ETF
  on a major exchange (the universe builder's candidate filter, 11,968 rows on 11-03), so it is a superset of the
  live universe (4,811 symbols on 11-02).
- `in_universe` / `tier` / `adv_rank` from the newest `universe.csv` on `mcf-data`. That file is committed at the end of
  each session, so at 09:08 it is the **previous** session's universe (its `built_at` is in index.jsonl). For the
  exact same-day universe, join with the universe.csv mcf-data commits later that day.
- FINRA Reg SHO consolidated daily short volume (CNMSshvol<prior session>.txt, free CDN). Short **volume**, not short
  interest. Holiday / late / blocked file → empty columns, `finra_status` = missing / error, the run still succeeds.

**Where.** Branch `mcf-data-borrow` (created on first run): `borrow/<day>.csv.gz` (one per trading day) +
`borrow/index.jsonl` (one summary line per day) + README with the retention rule.

**Size / runtime / load (measured 2026-11-03, live /v2/assets, from the Claude container).**
- Flags only: 40 KB gzipped per day. With FINRA columns: ≤ 215 KB (measured with random volumes, a worst case for
  compression; real volumes compress better). About 10-55 MB a year.
- Fetch time 5.9 s (the /v2/assets response is 6.5 MB, 14,395 assets); recorder CPU 0.3 s, memory < 100 MB.
- Job: no pip install (stdlib only), sparse checkout of `mcf/`, depth-1 clone of the data branch. Estimated
  ~0.3-0.5 runner-minutes a day, ~10 min a month (public repo: free). One job, one runner, 5-minute timeout, own
  concurrency group. 09:08 ET is clear of the 09:30-09:50 and 14:30-14:40 peaks (research/ops/capacity1103); the
  off-season cron line (08:08 ET in EST / 10:08 ET in EDT) stops at the first step in a few seconds.
- FINRA's CDN is blocked from the Claude container (proxy 403), so the FINRA part was tested offline only; GitHub
  Actions reaches it (public-data.yml already fetches the same files there). Check `finra_status` after the first run.

**Note.** The live universe.csv already carries shortable / easy_to_borrow, so past values for the universe can also be
read from the git history of `mcf-data` (depth-limited clones; one version per day, built ~08:4x ET).

## OPS-PRE1 fix (2026-11-26 night, inspector 11-27): recorder dead since 11-05

**What happened.** The `mcf-data-borrow` branch holds only 2026-11-04 and 2026-11-05. From 11-06 GitHub delivered the
09:08 ET cron 6-9 hours late (run start times, ET: 11-06 14:56, 11-09 17:57, 11-10 15:25, 11-11 15:09, 11-12 15:46,
11-13 15:26, 11-16 17:51, 11-17 16:43, 11-18 16:21, 11-19 16:25, 11-20 16:01, 11-23 19:45, 11-24 17:59, 11-25 17:27),
and only one of the two cron lines fired per day. The workflow's window check (08:45-10:00 ET) skipped every one of
those runs and the job still showed **success**, so nobody saw it.

**Lost sessions (14):** 2026-11-06, 11-09, 11-10, 11-11, 11-12, 11-13, 11-16, 11-17, 11-18, 11-19, 11-20, 11-23,
11-24, 11-25 (11-26 market holiday). The Alpaca borrow flags of those days cannot be recovered from Alpaca (current
state only). Partial recovery: the live `universe.csv` on `mcf-data` carries shortable / easy_to_borrow for the
universe names (~4.8k), one version per day in its git history (built ~08:4x ET). FINRA daily short volume for those
days is still on the CDN and can be fetched later for a study. Do NOT backfill with `workflow_dispatch` day=<past> +
force: that would file TODAY's flags under a past date (such a run is tagged timing="backfill" in index.jsonl).

**Fix (housekeeping, research data only; no trading path reads this branch).**
- A run anywhere from 08:45 ET to midnight ET on a weekday records that ET day (holidays still skip via the calendar).
  index.jsonl gains `timing` (on_time / late / backfill), `late_min` (minutes after 10:00 ET) and `prior_recorded`
  (false = the prior session's file is missing). A late run and a missing prior session each print a GitHub
  `::warning::`, so a delayed or lost day is visible on the run page instead of a silent green tick.
- Retry cron lines at :18 past the hour, 15-21 UTC (10:18-16:18 ET in EST, 11:18-17:18 ET in EDT), clear of the
  09:30-09:50 and 14:30-14:40 load peaks. An "Already recorded?" step (one GitHub contents GET) stops every later run of
  the day before checkout, so the extra lines cost a few seconds each.
- Research caveat: a late record's flags are as of `fetched_at_et`, not ~09:08. A study of the ETB/shortable flip
  (BORROW-FLIP, ideas.json) should use `timing` to separate morning and late snapshots.
  `timing` values: on_time (08:45-10:00 ET), late (+ late_min past 10:00), early (a manual run before 08:45 ET or on a
  weekend, late_min 0), backfill (another day).
- Tests: tests/test_borrow_record.py (late same-day run records + warns; evening run is still the same ET day; after
  midnight ET skips; missing prior session flagged; workflow no longer drops late runs and skips cheaply once done).

Educational only - not financial advice.
