# BEREPLAY — breakeven / trail exit remedy on every lab family, longs and shorts (Builder, pre-registered 2026-11-09 ~16:30 ET, before any score)

*Educational only — not financial advice.* Lead decision lead-20261109-1458-1 / request -1458-2; Skeptic
skeptic-20261109-1456-2 (giveback is book-wide: longs -620R, shorts -713R live; GEN 27% / 19%); Observer
observer-20261109-1541-1 (GEN rules recoverable: research/generator/modules/*, geoms in mcf/research/generator/spec.py).
Research only, no exit change anywhere.

## Prior evidence (read before hoping)
sw-w4-book-exits (2026-10-10): breakeven +0.75R and 21 other book-wide exits, 0 of 22 pass, 19 of 22 lower daily P/L;
exit-mf-be05 (2026-10-17): MF BE@+0.5R -0.008R vs parent, worse in TRAIN and VALID. Live Primary MF looked better
with BE (629 of 1,969 losers had reached +0.5R) — that is the mfe upper bound Skeptic warns about. Expect 0 passes;
what we want is the per-family map (where BE helps, where it hurts) under the Remedies rule.

## Configs (3; family N = sw-w4 22 + exit-mf-be05 1 + swarm1017 BE 1 + these 3 = 27, rounded up to **30 → full 2.61, BAR90 2.35**)
- **BE50:** once a 1-minute bar reaches entry + 0.5 x (stop distance) in favour, the stop moves to entry from the
  NEXT minute. Applied to every trade of every family; targets unchanged.
- **BE75:** same at +0.75 x stop distance.
- **HOLDTR:** every GEN setup with geom `hold` (stop 1R, flat 15:55) switched to `holdtr` (1R trailing stop on 1-min
  closes once +1R, flat 15:55); other setups untouched.

## Sample and engine
- Scoring sample: the 2-year lab lists (research/history2y/data/bt_lab1104: every covered lab setup in the five
  account configs, entry at the signal bar close, R = 0.25 x daily ATR, geometry from the live config) plus a signal
  pass for GEN `hold` / `holdtr` setups (not covered by bt_all; same mask / window / adv / chain logic as bt_all).
- **Baseline and variants are walked by the same 1-minute engine** (1-min SIP cache, locked block dropped at read and
  asserted): stop-first inside a minute, a minute opening through the stop fills at its open, targets at the target,
  flat at the 15:55 close. Costs exactly as bt_all (1c + 1bp x tod multiplier on entry, 3x tier for |gap| >= 20% or
  price < $5, stop exits +1c +1bp +2c, BE exits count as stops, target exits 0).
- Live check (separate, labelled live paper): the 23 live sessions' actual entries from the 7 journals, same engine.

## Scoring (excess over the live exit, Lead standard)
delta = variant R - baseline R per trade; day-clustered t of the daily summed delta (all days); TRAIN (<= 2025-09-30) /
VALID; SPY up / down / quiet; delta w/o best day; per family (leading name token; all GEN-* = GEN) x side: n, delta
avg, better / worse, and **giveback upper bound** (baseline trades that reached the trigger and closed <= 0: their R)
next to the realised delta. Also the share of trades the BE stop takes out that later would have hit the target.

## Pass (lead worth pursuing; a live change would need the owner)
Book delta t >= 2.35, TRAIN and VALID > 0, up AND down > 0, w/o best day > 0, more families better than worse, and no
family worse by more than 0.03R per trade (targeted remedy, not broad harm). A family-level pass at 2.35 on its own
trades is reported as a family lead (counted: families tested are listed with the result).
