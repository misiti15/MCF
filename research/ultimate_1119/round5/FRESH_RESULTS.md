Educational only — not financial advice

# Round 5 — FRESH results: NOT SCORED (blocked by the plan's own guards)

Status written 2026-11-19 ~10:15Z by the scorer stage. **No fresh-window bar, frame, signal or trade was downloaded or
read.** `/home/user/MCF/data/cache_fresh/` does not exist. `fresh_once.json` was not written, so the single score of every
rule is still unused. A later scorer replaces this file with the real results.

## What was checked (read-only, no fresh data)
| Guard (FRESH_PLAN) | State | Pass? |
|---|---|---|
| FREEZE_CORE.json hashes (R1-R6 code + refs, frozen 09:57:28Z) | 31 / 31 files match | yes |
| hunt_volume/FREEZE_VOLUME.json hashes (H-V1, H-V2, frozen 10:12:15Z) | 8 / 8 files match (corrected from "14 / 14" by the skeptic re-hash; the manifest lists 8 files plus 6 deps) | yes |
| `fresh_data_exists_at_freeze` in both freezes | false | yes |
| sec. 4.7 / 7.2 `FREEZE_HUNT.json` + `HUNT_FREEZE.md` (fixes M and the t bar) | missing | **no** |
| sec. 2.5 `FRESH_PLAN.md` sha256 matches `FRESH_PLAN.sha256` | e52de481… vs b54e69c5… (the 4-V edit, not re-hashed) | **no** |
| sec. 2.5 / 7.3 harness `fresh_bt.py` | missing | **no** |
| sec. 2.6 parity check on 2025-10 (ULT-32 32e, ST7-FD, NM-ETF trades) | not run (no harness) | **no** |
| sec. 7.4 download + stream into cache_fresh | not done (download_fresh.py correctly refuses) | **no** |

Scoring now would break the pre-registered order of work. The FREEZE_HUNT timestamp must come before the first fresh
file's mtime, and the parity check must pass before the first fresh byte. So nothing was scored, and no partial result exists.

## Rules waiting for their single score (all frozen, code hashes verified)
R1 BOOK-EM (ULT-32 32e), R2 leg E, R3 leg M, R4 ST7-FD (bench), R5 NM-ETF-late-dip (bench), R6 ST7-base (chassis),
H-V1 (leg X, short), H-V2 (leg K, long). If no other track adds rules, M = 8 and the t bar is 2.039.

Pass bar (sec. 5): avg R > +0.0836; w/o best day > +0.0734; R/session > 0; day-clustered t >= the M bar; positive on the
check half.

## To unblock (lead, in this order)
1. Close the hunt and write `FREEZE_HUNT.json` + `HUNT_FREEZE.md` (H-V1, H-V2 from FREEZE_VOLUME.json, plus any other
   track's entries). This fixes M.
2. Re-hash `FRESH_PLAN.md` into `FRESH_PLAN.sha256`, and record the reason (the 4-V append).
3. Build `fresh_bt.py` (overrides only as in sec. 2.5). Pass the 2025-10 parity check, and assert that no fresh file exists.
4. Run `download_fresh.py` (484 retained names on disk, the other 717 streamed), then `verify_fresh.py`.
5. Score once → `fresh_once.json` and this file.

Configs: no configuration was tried at this stage. Cumulative N stays 1,036 (up to 1,052) and M is not yet fixed.
Rule-change context: no live window is quoted, so no ledger entry applies.

Educational only — not financial advice.
