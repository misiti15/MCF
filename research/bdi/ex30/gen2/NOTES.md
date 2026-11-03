Educational only — not financial advice

# ex30 / gen2 — grammar + beam-search generator, regime-maximin fitness (results, 2026-11-03)

Pre-declared in `PLAN.md` (commit 86778d529, before anything was scored). Script `gen.py` (generator + harness, pandas
primitives); modules in `modules/` (numpy `gen2_lib.py` + 5 generated modules). Outputs: `candidates.csv.gz` (every
rule evaluated, TRAIN only), `results.csv` (the 30 shortlisted, TRAIN + VALID, the 5 delivered flagged), `parity.csv`,
`picks.json`. **Configurations evaluated: 18,519** (stage A 9,099 + stage B 9,420; 6,235 met the frequency / day-type
minimums) + VALID scored on the 30 shortlisted (same rules, not new configs). A one-month smoke run (2025-06 / 2026-09)
was used to debug the code only; its outputs were deleted unread. Locked block 2024-11-01..2025-02-28 never loaded
(asserted). Costs in (gates.prod_r production 1c + 1 bps per side, +2c on stops, time-of-day entry multiplier).
Backtest only (two-year lab frames, light gate). Nothing here is a paper or live result.
Rule-change context: new setups scored on fixed historical frames; no ledger rule change (sizing, stops, filters,
timing, moves) applies to them.

## Method (how gen2 differs from the paused Setup Generator)

The old generator (`mcf/research/generator`) draws random indicator-threshold combinations and screens them on mean R.
gen2 is a **typed grammar**: every rule is exactly one TRIGGER (an event at this bar: VWAP cross, MACD zero-cross,
wick rejection, divergence, round-number touch, inside bar, volume dry-up, ...; 19) + up to two CONTEXTS (a state: move
from open in ATR, gap bucket, 20-bar SMA stretch / slope, prior-day range position, heat, buy pressure, daily
volatility, SPY from open, breadth, relative strength vs SPY; 35) x side x exit geometry (t1s1 / t05s1 / t1s05) x window
(10:00-11:30, 11:30-14:00, 10:00-15:00). Max 3 conditions.
- **Fitness = the WORST of the three SPY day types** (avg R on up, down and quiet days, TRAIN), minus 0.01 per
  condition, minus 0.02 when the (trigger, side) is a live GEN token. A rule only scores well if it earns on all three
  day types — aimed straight at the live book's quiet-day hole. >= 30 trades per day type, 1.5-25 trades/session.
- Near-duplicates of live setups and of this week's exhausted families are excluded before scoring (VWAP reclaim /
  failed reclaim, RSI5 pop, flow-sell shorts, HOD fade shorts, LOD longs, volume spikes, PDL/PDH sweep-reclaim,
  gap-down bounce shorts).
- Beam search: all 1-2-condition rules, then the 300 best (>= 1.5 trades/session) extended by one more context.
- Shortlist: best fitness first, a rule is kept only if its TRAIN trade set has Jaccard < 0.30 with every kept rule;
  30 kept. **Delivered = first 5 with distinct triggers, chosen on TRAIN only.** VALID was then scored as a check.

## Failures first: 0 of 5 delivered setups pass the light lane gate

TRAIN 234 sessions, VALID 114. Day type = SPY open-to-close, +-0.25%. t = day-clustered.

| setup | rule (plain words) | TRAIN avg R (t) | VALID avg R (t) | trades/session | vs random TRAIN / VALID | VALID up / down / quiet | gate |
|---|---|---|---|---|---|---|---|
| G2-1-macdup-vrlo-vwup-W1-t1s1-short | short 10:00-11:30: MACD % crosses above 0 on a low-volume bar (<= 0.6x) while >= 0.5 ATR above VWAP | +0.148 (0.8) | -0.024 (-0.3) | 1.67 | +0.325 / +0.099 | +0.013 / -0.046 / -0.032 | fail (VALID R by 0.004) |
| G2-2-lwick-brlo-heatlo-W2-t1s05-long | long 11:30-14:00: lower-wick rejection bar (>= 60%, >= 0.10 ATR) while breadth <= 30% and heat <= -25 | +0.183 (0.9) | -0.180 (-2.6) | 2.22 | +0.286 / -0.044 | +0.286 (n 7) / -0.248 / -0.079 | fail (VALID R) |
| G2-3-uwick-brhi-d20hi-W2-t1s1-long | long 11:30-14:00: upper-wick bar (>= 60%) while breadth >= 70% and >= 0.8% above the 20-bar SMA | +0.371 (1.8) | -0.046 (-0.5) | 7.68 | +0.049 / -0.175 | +0.139 / -0.924 / -0.362 | fail (VALID R) |
| G2-4-round-foup-slopedn-W2-t05s1-long | long 11:30-14:00: close within 0.02 ATR of a round number while >= 0.5 ATR up from the open and the 20-bar SMA is falling | +0.089 (1.7) | -0.023 (-0.6) | 2.76 | +0.177 / +0.038 | +0.097 / -0.162 / -0.015 | fail (VALID R by 0.003) |
| G2-5-bulldiv-vrlo-vwdn-W1-t1s1-long | long 10:00-11:30: bullish RSI divergence at a new 20-bar low on a low-volume bar, >= 0.5 ATR below VWAP | +0.063 (1.3) | -0.050 (-0.8) | 6.05 | +0.241 / +0.067 | +0.176 / -0.151 / -0.060 | fail (VALID R) |

Parity (module vs harness, bar by bar, 2026-09-01..15, window + ADV): exact for all 5 (15 / 3 / 20 / 48 / 112 bars).

One-big-day check: G2-1 and G2-2 TRAIN totals are carried by one session (best-day share 1.37 / 1.38; without it
-0.079 / -0.099R), so their TRAIN numbers are not records. G2-3 share 0.87 (w/o best +0.076), G2-4 0.64 (+0.039),
G2-5 0.49 (+0.037). All VALID totals are negative (no carry).

## What the generator says

1. **The regime-maximin fitness did not transfer.** On TRAIN all five were positive on up, down AND quiet days. On
   VALID none is positive on quiet days and only G2-1/G2-4 come close (-0.03 / -0.02). The maximin over ~18.5k
   rules picked rules whose TRAIN quiet-day edge was noise; with ~18.5k tries the best TRAIN rule is expected near
   4.5 standard errors by luck, and the TRAIN t of the picks (0.8-1.8) is far below that bar.
2. **Two picks are still tape bets.** G2-3 (breadth >= 70%) and G2-2 (breadth <= 30%) are, in effect, "the tape keeps
   going": G2-3 -0.92R on VALID down days, G2-2 -0.25R. Same failure as ex30/xsec and ex30/levels.
3. **Three picks beat the day-matched random entry on VALID** (G2-1 +0.099 t 1.3, G2-4 +0.038 t 1.1, G2-5 +0.067
   t 1.3), i.e. the selection is above random but not above the ~0.1R cost hole. G2-1 and G2-4 miss the -0.02 gate by
   0.004 and 0.003 R — reported as fails, not rounded.
4. **Shortlist transfer (information only, the 30 shortlisted):** 10 of 30 have VALID avg R >= -0.02, mean VALID
   -0.044R; 21 of 30 beat random on VALID. The distinct-trigger rule that chose the 5 skipped three other MACD-cross
   shorts that held better on VALID: rank 2 `macdup + slope_dn + vr_lo` short t1s1 10:00-15:00 (VALID +0.033, 2.2/session,
   down +0.196 / quiet +0.144 / up -0.233) and rank 5 `macdup + br_hi + vw_up` short W1 (VALID +0.122, but 0.7 VALID
   trades/session, quiet -0.250). Swapping them in would be a choice made on VALID, so they are NOT delivered; if the owner
   wants them they are labelled "VALID-selected" and need forward sessions only.
5. **Most usable family the generator found: "MACD % crosses up while stretched / on low volume = fade short".** 6 of
   the 30 shortlisted rules are macdup shorts (ranks 1, 2, 5, 20, 23, 25); 5 of 6 beat random on VALID and 4 of 6 have
   VALID avg R >= -0.02 (-0.024, +0.033, +0.122, -0.107, +0.005, +0.065). Not a live family (GEN MACDh rules are
   histogram levels). Picked by the generator from 18.5k tries, so it is a lead for live exposure, not an edge.

## Recommendation for the exploratory accounts (owner decides allocation)

None pass the light gate. If exploratory exposure is wanted anyway, the least bad are G2-1 (MACD cross fade short,
beats random both splits) and G2-4 (round number in an up-from-open name with falling short SMA, beats random both
splits, -0.015 quiet on VALID); G2-2 and G2-3 should not get seats (direction bets with large VALID day-type losses).
Live verdict by the Live Lab rules: fail fast at 5+ sessions and 45+ trades with avg R <= -0.30 or <= -15R, verdict at
20 sessions, split by SPY up / down / quiet day.
