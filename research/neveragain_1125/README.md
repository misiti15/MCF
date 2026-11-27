# neveragain_1125 — committed evidence (reproducibility note)

Educational only — not financial advice.

- Scripts, logs and outputs were copied from the session scratchpad (`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/neveragain/`) on 2026-11-26 (commit b53782c717). Scripts and logs still name those
  absolute scratchpad paths, so they do not re-run from `research/neveragain_1125/` as committed; re-running needs the inputs below
  rebuilt and the paths edited.
- Inputs left out of git (size / regenerable): the bench candidate/lot tables (`cand.parquet`, `lots_all.parquet`), simulated paths (`paths.npy`, `idx.npy`, `grid.npz`) and journal copies (`journal.db`, `p_new.db`); built by the scripts in `scripts/` from the live journals and the pyramid_1124 bench (`pyramid/R3B/booked.parquet`).
- PLAN.md was hashed before scoring: `PLAN.sha256` (line 1 checks with `head -1 PLAN.sha256 | sha256sum -c`; line 2 is the time).
