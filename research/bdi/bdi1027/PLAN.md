# bdi1027 PLAN (written before any history was scored)

*Educational only — not financial advice.*

**Data:** open two-year history (research/history2y frames, 5-min decision bars 09:50-15:00 plus the 15:05-15:55
tail rows for exits, SIP), train ≤ 2025-12-31, valid 2026-01-01..2026-10-07. The locked block 2024-11-01..2025-02-28
is never read (lib refuses it; asserts in the script; MCF_HIST_ALLOW_LOCKED never set). No holdout is scored tonight
(rule 2/19: only a finalist that passes train + valid gates is scored once, by the lead).

**Costs:** production + time-of-day entry costs and stop slippage, exactly `research/bdi/top5_1019/scan_1019.sim`
(1c + 1 bps per side, ×3.8/2.1/1.4 before 09:35/09:50/10:30, +2c on stops). R = 0.25 × daily ATR. Entry at the
signal bar's close (em = 0, as every parent in top5_1019/1021). 15:55 flatten.

**Control:** same-minute random long from the universe pool (ADV ≥ $95M, 5 draws, seed 20261027), same geometry —
for idea A it is the test that matters (does picking the leaders beat buying any stock at the same bounce minute?).

## Idea A (NEW long setup): "Leaders on the Index Reclaim" (BDI1027-LIR-long)
Live 10-27: QQQ dipped to −0.21% at 10:17, reclaimed its open and closed +0.86%; the longs that worked were the names
that had held up through the dip (Graveyard ORL longs +$209, Gen ORB-fail-up hold +$441), while shorts lost
everywhere. Hypothesis: once the index has dipped and reclaimed its open, the stocks that are already well ahead of
the index (held up through the dip) lead the recovery into the close.
- **Trigger (index, known at the bar close):** the first decision bar of the day in 10:00-13:00 at which QQQ's
  from-open (`qqq_fo`, lab context) is ≥ 0 and its running minimum since 09:50 is ≤ −d. One trigger per day.
- **Stock (at the trigger bar):** ADV20 ≥ $95M, above its session VWAP (`vwapDistPct` > 0), relative strength
  `fromOpen − qqq_fo` ≥ k. One trade per symbol-day.
- **Configs (12, pre-declared):** d ∈ {0.20, 0.40}% × k ∈ {0.5, 1.0} %-pt × exit ∈ {hold: 1R stop, no target, out
  15:55; t1s1; t2s1}.
- Lineage: new trigger, but stock selection is relative strength vs the index, a family that already failed
  (t4-rel-strength 30, rw-t4_long_nomf 579 incl. holdout look 1, bdi-rdt-r16-rel-strength 128). Counted
  conservatively as that lineage: N = 737 + 12 = 749 → bar sqrt(2 ln N) = 3.64.

## Idea B (rework, tonight's nightly idea): `nightly-1027-pdl-long-index-low-age`
Failed prior-day-low break longs (CWT14 kernel of top5_1019, live geometry t05s1, 09:50-15:00, ADV ≥ $95M, first
signal per symbol-day): skip the entry while QQQ's low of day (running min of the 5-min `qqq_fo` closes — an
approximation of the true 1-min low; stated limit) was set fewer than a bars ago.
- **Configs (4, pre-declared):** setups CWT14-failbrk-pdl-p10-long, CWT14-failbrk-pdl-p05-lowvol-long × a ∈ {3 bars
  (15 min), 6 bars (30 min)}. Parent rows are scored for reference (not counted as configs).
- Lineage: nightly-1012-cwt14-long-index-confirm (800) + 4 = 804 → bar 3.66.

## Gates (fixed now, same as bdi1026)
(1) positive after costs in train AND valid; (2) beats the same-minute random control in train AND valid; (3) positive
in up AND down sessions (regime split, lib.regimes()); (4) day-clustered all-data t ≥ the lineage bar. For B also
(5) improves the parent's avg R in train AND valid and keeps ≥ 50% of the parent's trades. A row that meets (2)-(3)
(and 5) but not (1) or (4) is a near-miss only. Reported for every row: n, sessions, avg R without the best day and
the best day's share of total R (owner 2026-10-25), walk-forward share of positive months.

## Addendum (written after the 16 rows above were scored — 0 pass — and before this rework was scored)
Idea A beat the same-minute random long in all 12 rows (+0.01..+0.05R) but lost in down sessions in every row (a
direction bet). **Rework A-R (4 configs, rule 18 "add one condition"):** the two best rows on valid (d 0.20 / 0.40, k 1.0,
t1s1) with one breadth condition at the trigger bar: `breadth_open` (share of the universe above its own open, lab
context) ≥ 0.5 / ≥ 0.6 — the reclaim must be broad, not QQQ alone. Post-filter of the same trades (no re-simulation).
Lineage N 749 + 4 = 753 → bar 3.64. Same gates.

## Addendum 2 (written before scoring): cluster cap for the CWT14 pdl longs (Testing 1 / Primary 10-27 clusters)
Live 10-27 the pdl longs came in clusters (Testing 1 CWT14-failbrk-pdl-p05-long 22 lots in one bar; Primary clusters
> 9 −0.34R vs singles +0.43R). Burst skips already failed on two years for shorts (nightly-1015) and the coil
(bdi1026); not yet for the pdl longs. **C (4 configs):** the two B parents, skip every entry of a (date, signal bar)
with ≥ 5 / ≥ 10 of the setup's entries. Post-filter of the B parent trades. Lineage 804 + 4 = 808 → bar 3.66. Gates as B.
