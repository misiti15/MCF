# CONFIRM — stop (confirmation) entry vs market entry on the LIMEX signals (Builder, frozen 2026-11-11 ~00:20 ET; NOT scored until Skeptic's attack)

*Educational only — not financial advice.* Lead lead-20261110-2300-2; Observer observer-20261110-2342-2. Same 10 setups /
71,594 two-year signals as LIMEX (research/limex), same 1-min engine, costs and walk.
- **Baseline B:** market entry at the next 1-min bar's open (as LIMEX).
- **CONFIRM C_k:** enter only if, within N = 10 minutes after the signal bar close e, a 1-min bar trades through the
  trigger e + s x k x D (D = live stop distance = dn x 0.25 ATR_d); fill at the trigger (or the bar's open if it opens
  beyond it) PLUS stop-entry cost (1c + 1bp) x tod multiplier + 2c (the lab's extra-stop charge). **Same stop price
  (e - s x D) and target price (e + s x U) as live**, so risk grows to (1+k) D: results reported in **ATR units first**
  ((exit - fill) x s / ATR_d - costs / ATR_d) and in R of the new risk. Stop checked inside the trigger bar (conservative).
  Not triggered = no trade (0).
- **Configs: k = 0.10 / 0.25 at N = 10 = 2.** Family: execution-entry family as LIMEX (1,960; backlog configs_tried for
  confirmation lines are lineage totals, unusable) + 2 = **N 1,962 → BAR90 3.50**.
- **Control (Observer):** the mirror trigger: on the same signal, enter the OPPOSITE side if price trades through
  e - s x k x D within N, same rules mirrored. A move through any level predicts volatility; C must beat its mirror.
- **Reported:** trigger share; B's ATR result on triggered vs untriggered signals (selection); whipsaw = triggered then
  stopped within 2 bars (share, ATR result); per setup better / worse; TRAIN / VALID; SPY up / down / quiet.
- **Pass (both):** (1) C_k minus B, day-clustered t in ATR units >= 3.50, TRAIN and VALID > 0, w/o best day > 0, more setups
  better than worse; (2) C_k minus its mirror > 0 with t >= 2.

## Amendment 1 (2026-11-11 ~02:20 ET, before any score; Skeptic skeptic-20261111-0050-1 / -0051-2, Lead lead-20261111-0100-1)
- **Delta split:** timing part = sum over TRIGGERED signals of (C - B); skip part = sum over UNTRIGGERED signals of (-B).
- **Skip part vs chance:** scored against a random skip of the same number of signals within each setup-day (200 draws;
  excess_skip = skip part - mean random skip part), day-clustered t. Reported; a positive excess means the trigger selects.
- **Pass (replaces the earlier rule):** timing part day-clustered t (ATR units) >= 3.50, TRAIN and VALID timing > 0,
  timing w/o best day > 0, more setups better than worse on timing, **C's own net ATR per triggered trade > 0** (gross-first:
  not merely less bad), and C minus its mirror > 0 with t >= 2. Also reported: share of C stops inside the trigger bar;
  R-unit results carry less reward per unit risk by design (same target, later fill).
