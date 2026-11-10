# GATE2-R — failed-hold exit rework (Builder, pre-registered 2026-11-09 ~22:15 ET, before any score)

*Educational only — not financial advice.* Lead request lead-20261109-2100-2; Skeptic scale check skeptic-20261109-2102-3
(+0.02..+0.03 ATR is below a round trip: the rework must ADD GROSS, not trim costs). Research only.

## Why
GATE2's pullback timing beats a matched control (C1m, t 4-32 in ATR units) but every config loses after costs because
failed holds (SPY ends on the wrong side of its open) cost ~-0.6..-1.1R each, stopped at the instrument's open.
Remedy aimed at that failure mode only: leave as soon as SPY gives the reading back.

## Base configs (chosen by the C1m ATR-unit t already posted, builder-20261109-2100-1; nothing re-picked)
B1 = GATE2-I-HB-X0.30-RET0.60-E1 (C1m ATR t 31.9); B2 = GATE2-I-HB-X0.30-RET0.40-E1 (19.95). Rule, data, costs,
trigger, entry, stop and 15:55 exit exactly as gate2.py (PLAN.md + Amendments 1-2).

## Configs (4; lineage N 123 + 4 = **127 → full 3.11, BAR90 2.80**)
- **MX** (B1-MX, B2-MX): after entry, at every 5-minute bar close, if SPY is within ±0.15% of its open (|fo| <= 0.15%),
  the trade exits at the next bar's open (time-exit costs); the stop is still checked first inside each bar.
- **MXH** (B1-MXH, B2-MXH): MX plus half size for entries before 13:00 (weight 0.5; 1.0 from 13:00). Sizing is judged
  with the **size-cut control** (Lead standard, from STOPW): the same trades at a uniform weight equal to MXH's mean
  weight; MXH must beat it (day-clustered t of sum(w r) - w_mean x sum(r) >= 2.80).

## Pass (all required, per config)
GROSS avg R > 0 reported first and required; NET avg R > 0 after costs with day-clustered t >= 2.80; excess over C1m
(matched random bar, same MX exit) > 0 in R and in ATR units; TRAIN and VALID net > 0; SPY up AND down days net > 0
(quiet reported); avg R w/o best day > 0 (best-day share flagged >= 50%); held vs failed-hold-day R reported; share of
trades exited by MX and their R vs the same trades' plain-E1 R. MXH additionally beats its size-cut control.

## Honest prior
The failed-hold days were ~14-28% of traded days at ~-0.6..-1.1R; MX can only cut part of that and will also exit some
held days early (SPY often revisits its open and recovers). Expect 0 passes; the useful number is how much of the
failed-hold loss an SPY-based exit recovers, gross.
