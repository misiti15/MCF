Educational only — not financial advice

# Round 5 — hunt freeze (FRESH_PLAN sec. 4.7 / 7.2)

Written 2026-11-19 ~10:29Z by the harness stage, from `hunt_volume/FREEZE_VOLUME.json` (frozen 10:12:15Z). Machine-readable
copy: `FREEZE_HUNT.json` (frozen_utc 2026-11-19T10:28:39Z, sha256 57652b84771a3560…). When it was written,
`/home/user/MCF/data/cache_fresh` did not exist (asserted), so no fresh bar, frame or signal existed.

Before writing, every hash was re-checked: FREEZE_CORE 31 / 31 files match, and FREEZE_VOLUME 14 / 14 match (8 files + 6 deps).

## Slots
| Slot | Rule | Track |
|---|---|---|
| H1 | H-V1 (leg X, WB4 mirror, short) | volume (H5V) |
| H2 | H-V2 (leg K, one-bar shock snap, long) | volume (H5V) |
| H3-H6 | **empty** | no other track delivered a freeze before this file. These slots stay empty for round 5; we never force weak setups |

## Frozen hunt rules (module `hunt_volume/H5V.py`, sha256 1aba95f091c37af6…, frozen P)
| Id | Rule | Side / exit | Check /session | Check avg R | w/o best day | best-day share | t | Fit avg R (w/o best) |
|---|---|---|---|---|---|---|---|---|
| H-V1 | X-r0.75-t05s1: W list (100), adv20 >= $95M, 14:00-15:00, ret3 >= +0.75%, di_diff7 <= +5, ret12 <= +1.0%, atr_d_pct >= 3.5968, cost_r <= 0.10; easy-to-borrow only; borrow 1.2 bp (3 bp < $20) | short / t05s1 | 0.58 | +0.105 | +0.078 | 32% | 1.77 | +0.095 (+0.048; 55% **1 day**) |
| H-V2 | K-EQB-k0.2-t1s1: EQB ETFs (143), adv20 >= $300M, 10:15-15:00, ret1 <= -0.2 x atr_d%, vol_climax >= 2, cost_r <= 0.10; SPY long filter | long / t1s1 | 1.00 | +0.187 | +0.095 | **54% (1 day)** | 1.46 | +0.116 (-0.008; 106% **1 day**) |

Both run on the round-4 chassis: ULT-28 walk + LR8 cost_R, R per u = 0.25 x atr_d, 45-min time exit, flat by 15:50.
Selection is `hunt.py select()`, which is ULT-32 `chain()`: one lot per symbol, max 2 per symbol-session, refire
>= 30 min after the exit, day cap 30.

**Warnings (carried forward)**
- H-V2's top two check days carry 90% of its check R. Without them its avg R is +0.022.
- H-V1 is concentrated: SOXL, NUGT and TECL make up 66% of its trades.
- H-V1 and H-V2 move together: their daily R correlation is 0.43.

## M and the FRESH t bar
- Rules scored once on FRESH: R1 BOOK-EM (32e), R2 leg E, R3 leg M, R4 ST7-FD, R5 NM-ETF-late-dip, R6 ST7-base, H-V1 and H-V2.
- **M = 8**, so the **t bar is max(1.5, sqrt(2 ln 8)) = 2.039**.
- The full pass bar (sec. 5): avg R > +0.0836; w/o best day > +0.0734; R/session > 0; day-clustered t >= 2.039;
  positive on the check half.

## Configurations
This file tries no configuration. Cumulative N is 1,036 (up to 1,052), which includes the H5V hunt's 40. The M = 8
fresh scorings are reported next to it.

Rule-change context: no live-account window is quoted, so no `research/ledger.jsonl` change applies.

Educational only — not financial advice.
