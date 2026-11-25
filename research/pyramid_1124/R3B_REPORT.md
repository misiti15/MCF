Educational only — not financial advice

# Project Pyramid round 3 — Team B: judging 5-setup books against the top 10 (2026-11-25)

Research only. Pre-registered (R3B/PREREG.md, sha256 2c1d1020…0292, 14:50 UTC); books frozen on FIT (frozen.json, 15:09 UTC) before CHECK/2023-24. 10 configs (9 lab selection rules + 1 live walk-forward); cumulative N ≈ 1,927 (t bar ≈ 3.9). Pool: 10 shorts and 5 gated longs (TT1 or SPY ≥ open) from the TIER B list and live front-runners; 5 setups, 2–3 gated longs, ≤ 2 per family (gap-down group = one family); equal-risk weights (1R/trade reported too); research LR8 and a sub-$20-corrected cost basis. Locked block never read.

## Verdict: no 5-setup book clearly beats the top 10 out of sample — no Testing book proposed
B1 (FIT pick: NM-ETF+SPY≥open, B3 TREND-CLOSE-DRIFT, GEN-261027-01+TT1 long; NM-RWN4, GEN-261023-06 short):
| Window | B1 avg daily R | Top-10 | Worst-5 B1 / top-10 | Paired t vs top-10 |
|---|---|---|---|---|
| CHECK | +0.116 (2026-06-09 = 77% of R; w/o it +7.5R / 276 sessions) | −0.158 | −9.38 / −8.33 | 1.33 |
| 2023-24 | −0.069 | −0.142 | −6.74 / −3.46 | 1.18 |
Fails: worse worst-5 days in both windows; not significant; one-day carried. Every book incl. top-10 and Primary is negative on 2023-24. B6 meets the lab letter (paired t 2.59 on 2023-24) but is 1 of 9 configs, still negative on 2023-24 — chance-level. Cost basis shifts levels, no verdict.
- The long/short hedge did not appear once the gap-down shorts were excluded (sleeve correlation +0.30 / +0.12 / −0.05).
- Live walk-forward (weekly re-pick, 10-19..11-24): 5-book −9.4R vs top-10 −24.6R (same budget), t 1.11 — both lose.
- GEN-261023-06 is the swing factor in every book (CHECK +21.6R, 2023-24 −0.40R/trade).

## Next (backlog)
1. A per-setup daily risk cap to tame concentration (rare setups at full 1R swing the book).
2. Test "Primary shorts + 2 gated longs" (L3-fromopen, RW3 + NM-ETF+SPY≥open, GEN-261027-01+TT1) — the only place the anti-correlation hedge exists.
3. Keep journal-only forward tags for NM-ETF + gate and GEN-261023-06 to ≥ 20 sessions.
Scripts/data: scratchpad pyramid/R3B/.
