# ticksel_1125 — committed evidence (reproducibility note)

Educational only — not financial advice.

- Scripts, logs and outputs were copied from the session scratchpad (`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel/`) on 2026-11-26 (commit b53782c717). Scripts and logs still name those
  absolute scratchpad paths, so they do not re-run from `research/ticksel_1125/` as committed; re-running needs the inputs below
  rebuilt and the paths edited.
- Inputs left out of git (size / regenerable): `trades_t1.parquet`, `trades_t2.parquet`, `bk_t1.parquet`, `static.parquet`, `etb_rate.parquet`, `tr_live.parquet`, `live_daily.parquet` and `pyramid/X/live_dedup.parquet`.
- `PREREG.sha256` originally recorded the absolute scratchpad path; the path was changed to `PREREG.md` on 2026-11-26 (hash unchanged) so `sha256sum -c PREREG.sha256` works from this folder.
