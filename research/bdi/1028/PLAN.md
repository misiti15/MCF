# BDI 1028 PLAN (written before any history was scored)

*Educational only — not financial advice.*

**Data / rules:** as bdi1027/PLAN.md — open two-year history (research/history2y frames), train ≤ 2025-12-31, valid
2026-01-01..2026-10-07; the locked block 2024-11-01..2025-02-28 is never read (lib refuses it, asserts in the scripts,
MCF_HIST_ALLOW_LOCKED never set); no holdout is scored. Costs: `top5_1019/scan_1019.sim` (1c + 1 bps per side ×
time-of-day multipliers, +2c on stops); R = 0.25 × daily ATR; entry at the signal bar's close; 15:55 flatten.

## Why (live, 10-27 and 10-28)
bdi1027's "Leaders on the Index Reclaim" beat the same-minute random long in all 16 rows (+0.01..+0.05R) but lost in
every down-session split: the stock pick had an edge, the index trigger was a direction bet. On 10-28 the books were
again one direction bet (shorts −$3.1k on a slow grind up, NS3 family 2 / 48). Hypothesis: keep the selection, drop the
direction — trade the leaders **and** the laggards at the same minute, equal R per leg, so the day's index move mostly
cancels.

## Idea (NEW strategy): "Leader / Laggard Spread" (BDI1028-LLS)
- At a fixed decision bar T (no index condition), universe = ADV20 ≥ $95M, ATR > 0.
- RS = stock from-open % − QQQ from-open % (lab context `qqq_fo`).
- **Long legs:** the N highest RS with the close above session VWAP. **Short legs:** the N lowest RS with the close below
  VWAP. One basket per day; R per leg = 0.25 ATR.
- **Configs (8, pre-declared):** T ∈ {10:30, 12:00} × N ∈ {5, 10} × exit ∈ {hold: 1R stop, no target, out 15:55; t1s1}.
- Basket R per day = mean of all its legs (a day only counts if both sides have ≥ N/2 legs).

## Gates (fixed now)
(1) basket avg R > 0 after costs in train AND valid; (2) long legs beat the same-minute random long AND short legs beat
the same-minute random short, in train AND valid (K = 5 draws, seed 20261028); (3) basket avg R > 0 in up AND down
sessions (lib.regimes()); (4) day-clustered t of the basket ≥ the lineage bar. Lineage = relative-strength family
(bdi1027 N 753) + 8 = **761 → bar 3.64**. Reported per row: n legs, sessions, avg R, avg R without the best day and its
share, walk-forward share of positive months. A row meeting (2)+(3) but not (1) or (4) is a near-miss only.
