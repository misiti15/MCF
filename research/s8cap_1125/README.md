# s8cap_1125 — committed evidence (reproducibility note)

Educational only — not financial advice.

- Scripts, logs and outputs were copied from the session scratchpad (`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/s8cap/`) on 2026-11-26 (commit b53782c717). Scripts and logs still name those
  absolute scratchpad paths, so they do not re-run from `research/s8cap_1125/` as committed; re-running needs the inputs below
  rebuilt and the paths edited.
- Inputs left out of git (size / regenerable): `live_lots.parquet`, `live_grid.npy`, `paths.npy`, `cand.parquet`, and the capfit_1125 / pyramid_1124 tables they read (`capfit/all_trades.parquet`, `capfit/whatif.parquet`, `pyramid/G/live_bars.parquet`).
- PLAN.md was hashed before scoring: `PLAN.sha256` (line 1 checks with `head -1 PLAN.sha256 | sha256sum -c`; line 2 is the time).
