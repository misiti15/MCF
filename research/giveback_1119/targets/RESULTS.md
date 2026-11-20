# Target / R-geometry exits per family: results

*Educational only — not financial advice.* 2026-11-20. Plan written before any variant was scored: `PLAN.md`.
Nothing was committed and no live setting, setup, exit or ledger line was touched. **Verdict: FAIL.** Closer
targets, partial exits and target caps all lose R. Removing the target is not a fix either.

## What was tested
- **Scoring sample:** the 2-year lab. 1,106,391 first signals per (setup, symbol, day) from bt_lab1104, 95 setups and
  36 family-sides, walked BEREPLAY-style on cache_hist 1-minute bars as in map/lab_paths.py. Parent R matches the
  map (check-half avg −0.0723, the same as time_in_trade). The locked block 2024-11-01..2025-02-28 was filtered at
  read and asserted absent in both the walk and the scoring.
- **Halves:** fit = 170 sessions to 2025-09-30 (370,276 trades). Check = 276 sessions after that (736,115 trades),
  scored once.
- **Costs:** bt_all costs. Every partial, cap or time exit also pays a market exit plus $0.01/share.
- **Six fixed variants**, with levels in stop units from the fill:
  - C1 PART06: 50% off at +0.6.
  - C2 PART08: 50% off at +0.8.
  - C3 CAP10: target = min(parent, +1.0).
  - C4 CAP15: target = min(parent, +1.5).
  - C5 NOTGT-EOD: no target; exit at the stop or the end-of-day flatten.
  - C6 NOTGT-120: no target; exit at the stop or at 120 minutes.
- **Paired scoring** (variant − parent on the same trade):
  - Per family-side, the fit-best config was adopted only if fit ΔR > 0, day-clustered t ≥ 2, ΔR without the best
    day > 0, and ≥ 100 trades were changed.
  - Each config was also scored book-wide as a secondary.
- **Target from the fill was not re-run.** Wave 2 Y3 got +0.026R/trade, t 1.58, and its later half was negative.
  The geometry check in PLAN.md (no outcomes used) found no new evidence for it:
  - In every family, the target measured from the fill is already closer than the signal ratio k, because slippage
    is mostly adverse.
  - Far targets (> 1.2R from the fill) come from the setups' own 2:1 and 2.5:1 geometry: CWT09, MF1, MF2, CWT12-k6,
    LIQ, NS4, ST4.
  - Anchoring to the fill would move most targets farther away, so this variant had 0 configs.
- **Configs:** this class has 6 × 36 per family + 6 book-wide = **222**. Lineage N = map 916 + time_in_trade 2,664 +
  day_lock 16 + 222 = **3,818**. Bar = max(1.5, √(2 ln N)) = **4.06**.

## Fit selection
**0 of 36 family-sides adopted a config.** No family-side had a config with fit t ≥ 2; the highest fit t of any
positive config is 1.26 (RW6 short, NOTGT-120). The largest fit gain, CWT14 long NOTGT-EOD at +8,374R, had t 0.68
and then lost 8,689R on check. Applying each family's fit-best config to the check half anyway (a diagnostic, not
part of the rule): 2 better (+219R), 17 worse, 17 unchanged.

## Check half: the adopted book
It equals the parent: −53,193R, avg −0.0723, avg without the best day −0.0736. ΔR = 0. No family-side or setup is
better or worse. Pass rule items 1, 4 and 5 are not met.

## Check half: each config book-wide (secondary)
| config | trades changed | ΔR | Δ avg/trade | paired t | family-sides better / worse (R) | setups better / worse |
|---|---|---|---|---|---|---|
| PART06 | 120,774 | −4,246.9 | −0.0058 | −8.79 | 0 / 27 (0 / −4,247) | 1 / 58 |
| PART08 | 99,834 | −3,526.5 | −0.0048 | −12.76 | 0 / 27 (0 / −3,527) | 0 / 59 |
| CAP10 | 10,395 | −1,623.4 | −0.0022 | −6.81 | 0 / 8 (0 / −1,623) | 0 / 10 |
| CAP15 | 8,058 | −1,136.1 | −0.0015 | −8.31 | 0 / 8 (0 / −1,136) | 0 / 10 |
| NOTGT-EOD | 404,867 | −13,863.6 | −0.0188 | −1.82 | 6 / 30 (+596 / −14,460) | 28 / 67 |
| NOTGT-120 | 493,861 | −16,007.4 | −0.0217 | −3.47 | 4 / 32 (+313 / −16,321) | 25 / 70 |

Every config is negative in both halves except NOTGT-EOD. Its fit half is +687R at t 0.06, and 15% of that comes
from one day. Full per-family table: `data/bookwide_check_family.csv`.

**The far-target pocket (lab t1s05, target 2R; 20,777 check trades)** is where the map located the giveback (28% of
+0.8R trades end at a stop). Shortening those targets loses R:

| config | ΔR | t |
|---|---|---|
| CAP10 | −1,623 | −7.0 |
| CAP15 | −1,136 | −8.5 |
| PART06 | −1,024 | −6.4 |
| PART08 | −956 | −7.0 |
| NOTGT-EOD | +4 | 0.0 |

The four named setups, check ΔR:

| setup | CAP10 | PART08 | NOTGT-EOD |
|---|---|---|---|
| CWT09-g5 | −187 | −118 | −115 |
| MF1-945 | −561 | −319 | −137 |
| MF2-open | −197 | −110 | +125 |
| CWT12-k6 | −178 | −106 | +16 |

The trades that do reach 2R pay for the round trips. Taking money off early gives up more than the stops after
+0.8R cost. The map's "stopped after +0.8" share was computed after the fact; it is not an exit signal.

## Live (descriptive only)
Run 1, all 10 accounts, 10-06..11-19, 28,118 trades (the map's de-duplicated set), with LR8 costs subtracted from
both arms. Replay calibration: 81% within 0.10R of the live R; mean replay − live = +0.014R.

| config | fit ΔR (t) | check ΔR (t) | check family-sides better / worse |
|---|---|---|---|
| PART06 | −145.7 (−4.19) | −169.3 (−3.56) | 14 / 39 |
| PART08 | −95.7 (−3.45) | −87.6 (−2.76) | 9 / 40 |
| CAP10 | −133.8 (−3.99) | −93.3 (−1.86) | 7 / 33 |
| CAP15 | −51.0 (−2.68) | −47.2 (−1.56) | 7 / 21 |
| NOTGT-EOD | +189.6 (0.59) | +295.2 (0.97) | 30 / 21 |
| NOTGT-120 | −326.9 (−1.61) | −306.6 (−1.26) | 14 / 38 |

- **GEN hold setups (no target), partials:** PART06 −3.9R fit / −77.4R check. PART08 +7.3R fit / −66.1R check.
- **Live targets > 1.2R from the fill (2,730 trades):** every config hurts.
  - CAP10 −164.6R (t −3.06), CAP15 −98.2R, PART06 −93.8R, PART08 −76.6R, NOTGT-120 −176.9R, NOTGT-EOD −78.4R.
- **Live NOTGT-EOD is +493R in total but is not evidence:**
  - Only 15 of 33 days are positive, and the best day (10-15, +206R) is 42% of the total. The worst day is 11-12
    (−172R).
  - Shorts provide +452R of it, in a mostly choppy-to-down tape.
  - The 2-year lab gives the same rule −13,864R on check, with 30 of 36 family-sides worse.
- **Rule changes inside the live window** (research/ledger.jsonl, as in the map):
  - Testing2 scale-out to breakeven (10-16/17).
  - Per-setup latch (10-23).
  - Primary sizing changed twice (10-28).
  - Primary −2R latch (10-29).
  - Testing cost filter (10-30).
  - LR1 flatten time, LR3/LR8 costs, Gen/Graveyard sizing (11-12).
  - TSZ1 sizing and the SPYEXIT copies (11-17).
  - C3 Epoch 1 (11-19).
  - Replayed parent brackets ignore the scale-outs, latches and SPY exits; this accounts for most of the 19%
    replay mismatch.

## Pass rule
| condition | result |
|---|---|
| total and avg R improve on check | no (adopted ΔR 0; every book-wide config is negative) |
| avg R without the best day not worse | not met (no change) |
| not carried by one day | n/a |
| more families / setups better than worse | no (0 / 0 adopted; book-wide 0-6 better vs 8-32 worse) |
| paired t ≥ 4.06 | no |

**FAIL.** Nothing goes to the backlog from this class. Bringing the target closer, banking half early or capping the
2R targets all lose R in both halves, in the lab and in the live replay. On the 11-19 type of day this would have
helped, but over 2 years the trades that run to the far target pay for more than the round trips. This agrees with
L16, the book-wide breakeven, W5, the Wave 2 trail, Wave 2 Y3 and time_in_trade. A trade's own path and geometry do
not say when to take money off. What is left from the map's list are the book-level levers: an exposure brake or
SPY/QQQ hedge when the book is one-sided, and a trail for GEN hold setups (a different class).

## Caveats
- The lab enters at the signal-bar close with no fill slippage, so it cannot test anchoring; that comes from the
  live geometry check only.
- The lab has no ETB, stacking, latch or GEN hold lists, and only the first signal per (setup, symbol, day).
- A level touched in the same minute as the stop is counted as a stop (conservative toward the variants).
- The partial and cap exit costs (market exit + $0.01) are conservative; a free limit fill would shrink the losses
  but was not scored (pre-registered costs only).

## Files
Code: `lab_walk.py`, `live_walk.py`, `score.py`. Data (`data/`, 44 KB):
- `fit_grid.csv`
- `fitbest_on_check.csv`
- `check_adopted_family.csv`, `check_adopted_setup.csv`
- `bookwide.csv`, `bookwide_check_family.csv`
- `live.csv`
- `summary.json`
