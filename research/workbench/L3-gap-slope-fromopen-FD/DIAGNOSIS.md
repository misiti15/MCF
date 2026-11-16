# Diagnosis — Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Primary, TEAM-6)
Educational only — not financial advice. Mechanic, 2026-11-16 (built during market hours: research only).

Engine: `L3-gap-slope-fromopen-FD_engine.png` (P1..P24, blueprint `L3-gap-slope-fromopen-FD.md`). Live evidence = all 340
live trades (Primary 118, Testing 1 222; 10-13..11-12; 11-13 had 0 trades) and 4,963 live signals. Live R mixes the old
cost allowance (to 11-11) with LR8 (from 11-12) — see the rule-change list in the blueprint. Live numbers are used here to
DIAGNOSE only; the pass decision uses the identical backtests (RESULTS.md), never the live record (owner 2026-11-16).
Catalogue column = the part of research/workbench/PARTS_CATALOGUE.md the symptom points to.

## The three trades
| Trade | What happened | Part that caused it | Catalogue part | What a small tweak would have done to THIS trade |
|---|---|---|---|---|
| RRGB 10-15 −1.71R (`_trade1_RRGB_2026-10-15.png`) | P8 refire lot shorted 10:32:33 @ 8.75 on a stock gapped only −2.71%; 1R = $0.09; never better than −0.11R; P21 stop 10:38:00 @ 8.89. The fixed $0.02 stop cost is 0.22R of a $0.09 R → −1.71R | P4/P10 gap barely past −2.66%; P18 tiny 1R | Intake (gap); Entry/sizing (1R) | gap ≤ −3.2% (WB2/WB3): not taken (+1.71R). Window 13:00 (WB1): still taken |
| UGP 10-26 −1.42R (`_trade2_UGP_2026-10-26.png`) | Short 12:35:53 @ 6.47 (gap −19.4%), 1R = $0.05; MFE +1.42R at 12:47 = exactly the target, which did not fill on a touch; reversed, P21 stop 13:07:33 @ 6.52 | P22 target (limit not filled on a touch) + tiny 1R | Target | target 0.8R (V04) would have filled ~12:4x (+0.8R) — but V04 failed both tests overall. Window 13:00: still taken (12:35). Gap −3.2: still taken |
| SNAP 10-22 +2.24R best (`_best1_SNAP_2026-10-22.png`) | Refire lot 11:40:54 @ 6.55 (slip −53.7 bps), MAE −0.73R 11:52, P22 target 12:51:17 @ 6.43 | works as designed | — | gap ≤ −3.2 would have MISSED it (gap −2.68%): the deeper-gap tweak costs some winners too. Window 13:00 keeps it |

## Across all 340 live trades (which part is most often behind the losses)
- **Timer / window (P6) — the clearest pattern.** Entries 09:50-12:59: 304 trades, +89.7R (avg +0.30R). Entries 13:00-15:00:
  36 trades, −13.9R (avg −0.39R; 13:00-13:59 8 trades −6.8R, 14:00-15:00 28 trades −7.0R). The afternoon rally on a gap-down
  name is more often a real recovery than an exhaustion pop. → V01/V02 (end 13:00 / 14:00). Catalogue: "losers cluster at one time of day".
- **Stop (P21):** 77 stops (23%), avg −1.13R. Only 10 of 77 had MFE ≥ 0.8R and 18 ≥ 0.5R first, so the stop is mostly not
  cutting trades that would have worked; targets' MAE median −0.23R (worst −0.97R). → V05 (1.25R) tested anyway.
- **Target (P22):** 150 targets (44%) at +0.97R. 10 stopped trades touched 0.8R first (UGP-type). → V04 (0.8R).
- **Time exit (P24):** 113 flattens (33%), avg +0.15R, avg MFE +0.55R — some give-back late. → V06 (flat 15:00).
- **Refire / lots per symbol (P8/P13):** 1st lot on a symbol-day avg +0.24R, 2nd +0.21R, 3rd +0.12R; 57% of trades are
  stacked lots. → V10 (cooldown 3 bars), V11 (≤ 2 lots per symbol).
- **Open-lot cap (P12):** blocked 648 signals (13%), mostly 10-20 / 11-12, the best days. → V12 (40) — the L3 cap what-if
  already covered this; re-scored here only for completeness.
- **Intake (P4) / borrow (P5):** 61% of signals were not shortable/ETB (inverse/leveraged ETFs etc.) — not a tunable part.
  Thin 1R (RRGB $0.09, UGP $0.05) makes the fixed stop cost large, but across live trades R size shows no clean pattern
  (1R/price 1.0-1.5%: 51 trades −0.32R; < 1%: +0.22R; 1.5-2%: +0.21R), so no 1R floor was tried.
- **Sensors (P9/P11):** no single-trade evidence; V07 (fromOpen > 4.0) and V08 (slope > 0.45) tested as threshold nudges.
- **Day type:** 11-13 had 0 trades (gap-downs did not recover) — that is the setup's nature, not a failure. Up-market days
  are the losing day type (2-year: up −0.16R, flat −0.01R, down +0.08R) — leashes for that were tested in L3LEASH/-2 (0 of 12 passed); not redone.

## Candidates chosen (each ONE part, small) and why
1. **WB1 — P6 window end 15:00 → 13:00** (strongest live pattern).
2. **WB2 — P4+P10 gap ≤ −2.66% → ≤ −3.2%** (fewer marginal gap-downs like RRGB; prefilter and module kept consistent).
3. **WB3 — WB1 + WB2 combined** (each passed alone).
Also passed but not shortlisted: V06 flat 15:00, V08 slope 0.45, V10 cooldown 3 (smaller or one-test-only gains) and V11
≤ 2 lots per symbol (good in both tests, but the lot cap is an ACCOUNT setting, `live.max_lots_per_symbol`, shared by all
setups; a per-setup lot cap needs a small runner hook first — backlog idea, not a config copy).
