# HKS950 — RESULT: CLOSED (both configs). One look, 2026-11-17 ~17:20 ET, run exactly as re-signed (69bd15445; no code change)
Educational only — not financial advice. Output: research/hks950/hks950_out.txt; per-day files hks950_L20_days.csv / hks950_L40_days.csv.
Data source: cached 30-min bars, 2-year history (512 names, 434/418 scored days after the warm-up, locked block absent, half days dropped).
Configs 2; family N 42 -> 44 after this look (cross-sectional return family).

## Failures first
- **L20 CLOSED**: VALID L-S gross +1.82 bps, t +2.18, below BAR90 2.46. TRAIN agrees (+0.58, t 0.77), 8/11 slots, above null95.
  Even if it had passed, net is -10.2 bps: break-even is 0.91 bps per leg round trip vs the 6 bps cost.
- **L40 CLOSED**: VALID -0.23 bps (t -0.28); TRAIN +1.29; 5/11 slots. The sign does not hold out of sample.
- Long leg alone (tilt reading): L20 VALID +1.09 bps (t 1.92); L40 -0.14. Neither carries a tilt case past its 6 bps cost.
- Nothing above ~2.6-2.8 bps per half-hour (VALID MDE at BAR90); smaller is unknown. That is far below any cost we pay.
- **Control caveat (method note for the guild):** the shuffle null's SD (0.22 bps) is ~4x smaller than the real portfolio's day
  SE (~0.83). The signal picks the same volatile names on both legs, so the real L-S is noisier than random deciles.
  'Above null95' is therefore a weak check here; the day-clustered t is the honest one. Keep both, but don't read null95 alone.

## What is real but not usable (reported, not a proposal)
- The 15:30 slot (ends at the 16:00 close, auction included) is strong in both configs: L20 VALID +11.8 bps (t 4.40), TRAIN
  +5.3; L40 VALID +9.1 (t 3.20). This matches the paper's end-of-day finding. Live is flat by 15:55, so it is not tradable under
  our rules, and it is still below a round trip on most names. This is not a pass and was not part of the main reading.
- Afternoon slots 13:00-15:00 are positive in both configs; that is post hoc, so no claim.

## Reading (pre-registered table): VALID t < 2.46 -> CLOSED. The backlog `wi-same-halfhour` can be parked with this MDE (Lead routes).
