# pyramid_1124 — committed evidence (reproducibility note)

Educational only — not financial advice.

- Scripts, logs and outputs were copied from the session scratchpad (`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/`) on 2026-11-26 (commit b53782c717). Scripts and logs still name those
  absolute scratchpad paths, so they do not re-run from `research/pyramid_1124/` as committed; re-running needs the inputs below
  rebuilt and the paths edited.
- Inputs left out of git (size / regenerable): the bench trade tables (`trades_t1.parquet`, `trades_t2.parquet`), `spy_days.parquet`, `etb_rate.parquet`, `ctx.parquet`, `live_dedup.parquet`, `G/gate.parquet` and journal copies (`journal.db`).
- Sub-studies keep their pre-registration in `<X>/PREREG.md` or `<X>/PLAN.md` and the report in `<X>_REPORT.md`. Those pre-registrations entered git (b53782c717) after their reports; their own `PREREG.sha256` / `PLAN.sha256` files carry the pre-scoring hash (`L1/PLAN.sha256` named `../pyramid/L1/PLAN.md`; changed to `PLAN.md` on 2026-11-26, hash unchanged). Grandfathered in tests/test_prereg_order.py.
