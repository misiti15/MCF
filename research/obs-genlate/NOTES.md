Educational only — not financial advice.

# obs-genlate — is late-buying a GEN trait? (Observer, 2026-11-09 ~13:45 ET, journals only)

Lead's request lead-20261109-1258-4. Descriptive, **0 configs**. `genlate.py` -> `genlate_out.txt`.
All LONG paper trades, all 7 accounts, 2026-10-06..11-06 (9,393 trades; GEN 1,439 on 15 days).

## Failures / caveats first
- **No bars here, so "late" is proxied**: never-worked share (mfe_r < 0.15) and giveback (mfe_r >= 0.5 then closed <= 0).
  mfe_r cannot say whether the stop came before or after the peak.
- GEN 'chase' vs 'dip' is parsed from setup names (crude regex), 12 and 11 days; one regime-heavy month.

## Answer: mostly NO — GEN's long problem is giveback (exits), not late entries
| | non-GEN longs | GEN longs |
|---|---|---|
| trades / total R / avg | 7,954 / -1,165R / -0.147 | 1,439 / -345R / **-0.240** |
| never-worked share | 20.8% | 20.8% (same) |
| reached +0.5R | 29.8% | **44.8%** |
| of those, closed <= 0 | 18.3% | **31.0%** |
| R lost on those giveback trades | -452R | **-168R (49% of GEN's long loss)** |

- GEN longs get going MORE often than other longs, then give it back. By exit tag: `hold` (no trail, 485 trades) -0.32 avg;
  `holdtr` (trail, 287) -0.16; `t1s1` (439) -0.13; `t05s05` (88) -0.61.
- Late-buying after a mover's top (-20.9R, run 3) is a slice owned by a few chase-conditioned GEN setups (e.g. GEN-261021-05,
  ORHdist >= 0.42 in the LAM window). Name-parsed 'chase' GEN longs avg -0.30 (379) vs 'dip' -0.11 (383).
- GEN window: LATE +0.17 (75 trades), PM -0.08; AM -0.34, LAM -0.47 worst.
- Side fact: CWT14 longs are 5,148 trades / -708R across accounts — the long book's biggest drain by volume; Primary's
  205 longs are -0.035 avg (never-worked 12.7%).

## Suggested next (remedy order per charter: sizing / execution / exits before filters)
GEN-family exit remedy: break-even after +0.5R (or switch `hold` to `holdtr`) on GEN long setups, replayed on 1-min bars
(stop-first, costs in), per-setup better/worse counts. Needs the bar path, so Builder's cache.
