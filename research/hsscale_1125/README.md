# hsscale_1125 — committed evidence (reproducibility note)

Educational only — not financial advice.

- Scripts, logs and outputs were copied from the session scratchpad (`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hsscale/`) on 2026-11-26 (commit b53782c717). Scripts and logs still name those
  absolute scratchpad paths, so they do not re-run from `research/hsscale_1125/` as committed; re-running needs the inputs below
  rebuilt and the paths edited.
- Inputs left out of git (size / regenerable): `paths.npy`, `cand.parquet`, the live poll extract (`polls.parquet`, built by `scripts/polls_extract.py` from the live poll logs), `OUT.parquet`, and the capfit_1125 / pyramid_1124 tables (`capfit/all_trades.parquet`, `pyramid/S/etb_rate.parquet`).
- PLAN.md was hashed before scoring: `PLAN.sha256` (line 1 checks with `head -1 PLAN.sha256 | sha256sum -c`; line 2 is the time). PLAN.md and REPORT.md entered git in the same commit (grandfathered in tests/test_prereg_order.py).
