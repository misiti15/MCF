Educational only — not financial advice

# night1102 / simple — are our setups too complex?

Pre-declared in `PLAN.md` (written before anything was scored). Scripts: `live_census.py` (step 1), `build_live_frames.py`
(live-period frames), `score.py` (step 2-3), `report.py` (tables). Outputs: `census.csv`, `census_out.txt`, `results.csv`,
`report_out.txt`, `parity.csv`. Locked block 2024-11-01..2025-02-28 never loaded (asserted). Costs always in
(production 1c + 1 bps per side, +2c on stops, time-of-day entry multiplier). A container restart killed the first run
at 2026-08; `score.py` was re-run from scratch with a per-month cache (same code otherwise).

**Configurations counted:** census = 5 correlations (3 pooled + 2 non-GEN); kernel study = **89 kernel x form configurations
scored (77 distinct trade sets** — shared cores across the three RW kernels and one CWT13 condition that never binds).
BAR90 at that N: t >= 2.70. **0 of 89 pass.** 0 "simpler twins" pass the pre-declared twin bar.

## Bottom line for the owner

1. **Simpler is not better — on either data set.** Across all 89 forms, avg R gets *worse* with every condition removed,
   on the 2-year frames AND on the live re-score (mean over forms):

   | conditions | trades/day (2y) | 2y avg R | 2y vs random | LIVE re-score avg R | LIVE vs random |
   |---|---|---|---|---|---|
   | 4 | 42 | -0.063 | +0.034 | -0.025 | +0.086 |
   | 3 | 76 | -0.068 | +0.027 | -0.053 | +0.054 |
   | 2 | 298 | -0.077 | +0.015 | -0.073 | +0.025 |
   | 1 | 719 | -0.085 | +0.002 | -0.085 | +0.005 |

   Single conditions are random entries (~0 vs random). Each condition buys back only ~+0.01..0.03R; the base rate for a
   random entry with these exits and costs is about -0.08..-0.10R. **Our problem is not too many conditions; it is that
   the conditions together add too little edge over a cost-heavy base, and the sign is set by the market's direction.**
2. **Live census agrees.** 203 enabled setups, 102 with >= 10 live paper trades 10-06..11-02: condition count vs live avg R
   rho +0.08 (p 0.42, no link); vs trades/session rho -0.23 (p 0.02, fewer conditions = more trades, as expected); vs
   live-minus-backtest gap rho +0.27 (p 0.10, n 38; if anything the simpler setups fall *further* below their backtest).
   The four 1-condition setups (heat_fade family) are the worst live group (mean setup avg R -0.28).
3. **No subset removes the market-direction bet.** Every short form, simple or not, loses on up days and wins on down days
   (2y up-day avg R about -0.30 for every RW/exhaustion form; longs mirror it). Dropping conditions never moved a form
   toward "works in both". That job belongs to a regime/direction layer (see the regime workstream), not to
   simplification.
4. **The one place simpler looked better live is the Primary gap-down flow-sell shorts with the RSI condition removed**
   (below) — but on the 2-year frames those forms are still negative and do not beat random. Forward observation only.

## Census (step 1)

`census.csv` / `census_out.txt`. Counted conditions = module LAYERS / TRIGGER+FILTERS / CONDS lines minus time windows,
ADV floors and exit notes; loop kernels and classic strategies counted by hand (table in `live_census.py`). Live avg R =
paper `pnl_adj / $ risk`, run_id 1 of each journal. By count (setups >= 10 trades):

| k | setups | trades | mean setup avg R | median trades/session | trade-weighted avg R |
|---|---|---|---|---|---|
| 1 | 4 | 1,177 | -0.280 | 12.2 | -0.227 |
| 2 | 8 | 2,851 | -0.135 | 24.8 | -0.115 |
| 3 | 53 | 6,046 | -0.140 | 4.8 | -0.147 |
| 4 | 35 | 1,828 | -0.135 | 5.7 | -0.098 |
| 5 | 2 | 89 | +0.001 | 3.3 | -0.079 |

## Kernel study (steps 2-3)

Kernels (busiest live, decomposable on the lab frames): CWT14-failbrk-pdl-p10-long (423 paper trades), RW7-gapdn-bounce-
early-short-FD (331), ST2-slope20up-long-am-t05s1-FD (166), CWT13-vwapstretch-z05-long (149), exhaustion_short-FD (139,
+ the RW2 ADV150 twin), plus the two busiest Primary setups RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (104) and
RW3-gapdn-rsi5pop-flowsell-short-FD (91). Not decomposable: heat_fade_short-FD (one composite threshold), CWT12-coil (loop),
GEN-ORBfailUp (hold exit).

**Parity.** My parent masks = the live modules bar for bar on 2026-09 (all 7 exact except CWT13 1,206/1,247 = 97%).
LIVE re-score = frames rebuilt from 1-minute SIP bars of the replay universe (1,096 names with warm-up; the live universe is
larger) for 2026-10-06..11-02, 20 sessions, first signal per symbol-day, no slots / caps / scale-outs / setup stops.
77-94% of each parent's paper symbol-days are found in the re-score; on matched days the paper R is close to the paper
total (RW5 +0.368 vs +0.329, RW3 +0.357 vs +0.367, CWT14 -0.034 vs -0.051). The re-score takes 3-5x more trades than the
paper (no slot cap) and its averages are lower than paper for RW5 (+0.117 vs +0.329) and RW3 (+0.093 vs +0.367): the
Primary paper record sits on the subset its slots happened to take. Replay caveats from replay_audit1029 apply.

**Per kernel** (full tables in `report_out.txt`; 2y = TRAIN 2024-10, 2025-03..12 / VALID 2026-01..03, 07-01..09-15):

| kernel | forms | keep on 2y (>= parent avg R with >= trades) | better LIVE re-score | any form > 0 on 2y | parent 2y TRAIN / VALID | parent LIVE |
|---|---|---|---|---|---|---|
| RW7 gap-down bounce short | 14 | 1 | 1 | 0 | -0.079 / -0.033 | +0.012 |
| RW5 heat30 flow-sell short | 14 | 0 | 1 | 0 | -0.052 / -0.077 | +0.117 |
| RW3 gap-down flow-sell short | 14 | 3 | 1 | 0 | -0.092 / -0.040 | +0.093 |
| exhaustion_short-FD | 6 | 0 | 6 (all still < 0) | 0 | -0.102 / -0.026 | -0.146 |
| ST2 slope-up long | 14 | 0 | 6 (all still < 0) | 0 | -0.051 / +0.014 | -0.092 |
| CWT13 VWAP stretch long | 14 | 6 | 3 (all still < 0) | 0 | -0.066 / -0.079 | -0.099 |
| CWT14 failed PDL break long | 5 | 3 | 2 (all still < 0) | 0 | -0.088 / -0.086 | -0.059 |

No form of any kernel is > 0 in TRAIN, VALID and LIVE together. The parents themselves are negative on the 2-year frames
with costs (this matches the low-confidence-in-backtest view; it also means "keeps the parent's avg R" is a low bar).

## Ranked "simpler twins" for forward observation (none passes the pre-declared bar)

Ranked by LIVE re-score avg R (owner: live first). All three are one family (gap-down stock, heavy sell flow, short) —
**put at most one in Testing**, and read it as a down-tape bet: its live up-day avg R is negative.

| # | form (conditions) | LIVE re-score n / avg R / t | w/o best day; best-day share | 10-29, 10-30, 11-02 avg R | 2y TRAIN / VALID; vs random | live up / down days |
|---|---|---|---|---|---|---|
| 1 | **RW3 without rsi5>80**: heat <= -20, buyPressure < -0.35, gap < 0, short t1s1, 09:50-15:00, ADV >= 95M | 1,727 / **+0.110** / 1.56 (parent 309 / +0.093) | +0.072; 42% | -0.16, +0.23, +0.25 (parent -0.40, -0.88, -0.15) | -0.071 / -0.026 (parent -0.092 / -0.040, **keeps**); 0.000 | -0.125 / +0.327 |
| 2 | RW5 without rsi5>80: heat <= -30, buyPressure < -0.15, gap < 0 | 1,308 / **+0.170** / 2.06 (parent 287 / +0.117) | +0.134; 33% | -0.28, +0.44, +0.09 (parent -0.63, -0.92, -0.68) | -0.089 / -0.054 (worse than parent); -0.008 | -0.104 / +0.484 |
| 3 | RW7 without rsi55-65: heat <= -20, buyPressure < -0.15, gap < 0 | 3,740 / +0.072 / 0.98 (parent 1,365 / +0.012) | +0.038; 52% (**1 day**) | -0.15, +0.51, +0.29 | -0.072 / -0.034 (keeps); +0.012 | -0.176 / +0.374 |

Recommendation: **#1 only** (RW3-simple) — the one form that both keeps on the 2-year frames and beats its parent live,
with 5x the trades and a record not carried by one day. #2 has the best live number but is worse than its parent on 2y
and does not beat random there. Concrete test: add `RW3S-gapdn-flowsell-short-FD` = RW3-FD's module with the rsi5 > 80
line removed, to Testing 1 or 2 (equal weight), observation only, frozen rules; judge after >= 20 sessions / >= 60
trades on avg R, avg R w/o best day, and up-day vs down-day split. Logged as backlog `simple1102-rw3-no-rsi5`
(status failed on the 2y finalist gate; owner-exception forward candidate). Not a config change; owner decides.

Free housekeeping-level finding (no trade changes): CWT13's "previous bar range >= 0.4 ATR" never binds (implied by
"previous close >= 0.5 ATR below VWAP"; identical trades on all 2y and live data) — it can be deleted from the module's
LAYERS without changing a single trade.

## Rule / config changes in effect inside the live window 10-06..11-02 (research/ledger.jsonl)

The paper records above mix setup behaviour with these changes; the LIVE re-score ignores slots, caps and exits-in-account
and is not affected by them. 10-06 exhaustion_short on; 10-07 all live setups on probation; 10-09 Testing gets ST1-8 /
RW1-7; 10-12 research scoring adds time-of-day entry costs; 10-12 narrowest-setup-first priority; 10-14 refire option B;
10-16 live scale-out + Testing 2 CWT14 scale-out; 10-20 scale-out fix (bank + breakeven OCO), twin cap, per-setup -2R
daily loss limit; 10-21 promotion = move (RW5-FD, RW3-FD, MF2-FD, MF4-FD, NS3-FD, MF3-FD Primary only), Graveyard account
opened; 10-23 per-setup stop latched, then off in Testing 1/2/Gen; 10-26 CWT13-z05-long promoted, 10-27 demoted; 10-27
lab clock gate GX1 (5-minute clock); 10-28 Primary position size $5k then $4k (slots 61 -> 77); 10-29 Primary per-setup
-2R latched daily stop; 10-30 Testing 1/2 cost filter (skip entries with stop round-trip cost > 0.15R); 10-30 L3-rsi5hi-FD
promoted; 11-02 PDL-1a R2A legs into Testing 2. The bad Primary stretch (10-29, 10-30, 11-02) falls entirely after the
10-28 sizing change and the 10-29 per-setup stop.
