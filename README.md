# MCF borrow / short-volume record (PRE1, owner 2026-11-03)

Written each trading morning (~09:08 ET) by .github/workflows/borrow-record.yml (mcf/data/borrow_record.py).

* `borrow/<day>.csv.gz` - one file per trading day: Alpaca asset flags at ~09:08 ET (shortable, easy_to_borrow,
  borrow_status, marginable, short margin requirement, PTP) for every tradable common stock / ETF on a major
  exchange, the previous session's universe tier, and the FINRA Reg SHO daily short volume of the prior session
  (short-sale VOLUME, not short interest). Booleans are 1/0; empty = not available.
* `borrow/index.jsonl` - one line per day: counts, finra_status (ok / missing / error), universe built_at, run time.

Retention: keep every day (about 200 KB a day, ~55 MB a year). If the branch passes ~250 MB, fold whole years
into one zstd parquet on `research-data` and drop the daily files of those years from this branch (history may then
be squashed). Nothing in the live trading path reads this branch.

Educational only - not financial advice.
