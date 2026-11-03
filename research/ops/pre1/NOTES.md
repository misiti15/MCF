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
