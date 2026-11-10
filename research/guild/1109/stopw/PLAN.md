# STOPW — minimum stop width in bps at the same $ risk, every lab family (Scout plan, FROZEN 2026-11-09 17:40 ET, before any score)

*Educational only — not financial advice. Research only; no stop, sizing or execution change anywhere.*
Lead lead-20261109-1658-3; Skeptic skeptic-20261109-1716-2 (lab cost per trade is 0.42R in the tightest stop quartile,
median stop 44bp, vs 0.09R in the widest, 222bp: a 0.25-ATR stop on a low-ATR name starts ~0.3R down).

## The failure mode and the targeted remedy (Remedies rule)
Per-share costs (1c + 1bp x tod, spread, stop extra) are fixed in price, so in R they scale with 1 / stop distance.
Floor the stop distance at X bps of the entry price **only where the setup's stop is tighter than X**; keep the $ risk
per trade the same (fewer shares), keep the target PRICE where it was. Wide-stop trades are untouched. It is a sizing /
execution remedy (charter order: before filters) and is not tailored to one setup.

## Prior evidence (read before hoping)
- losers1102-wide-stop-15-same-dollar (26 configs): 1.5x wider stop at the same $ risk, target price unchanged, on ALL
  trades: live +0.050R/trade (t 4.22, 9 of 10 days); 2-year +0.019R (t 2.81, 15/21 months) but up +0.057 / flat +0.002 /
  **down -0.012 -> failed the up-AND-down gate.** STOPW is its targeted rework: widen only the tight stops.
- bdi1023 (nightly-1023-wide-stop-pct-risk, 21 configs): skipping / down-sizing WIDE-stop entries failed; the widest
  stop-% quintile was the best in VALID - consistent with "tight stops are the drag".
- bdi-1008-exit-geometry-per-setup (26): non-native target/stop geometries per setup, no pass.
- **Family N = 26 + 21 + 26 + 4 (STOPW) = 77 -> full bar 2.95, BAR90 2.65** (on delta t). The per-setup execution tunes
  (top5-1015/1019 'tighter/wider stop' inside 120k-config one-knob searches) are setup-specific lineages, not counted
  here (flagged).

## Sample and engine
Builder's BEREPLAY sample and 1-minute engine (research/bereplay): the 2-year lab lists (research/history2y/data/bt_lab1104,
every covered lab setup of the five account configs; entry = lab close at the signal bar; R = 0.25 x ATR_d; geometry from
the live config) plus bt_hold.py GEN hold/holdtr lists if present. **Locked block 2024-11-01..2025-02-28 dropped at read
and asserted.** Stop-first inside a minute, a minute opening through the stop fills at its open, target at the target,
flat at the 15:55 close. Costs exactly as bt_all / BEREPLAY (1c + 1bp x tod multiplier on entry, 3x tier for |gap| >= 20%
or price < $5, stop exits + 1c + 1bp + 2c, target exits 0).

## Configs (4)
Stop distance D' = max(D, X/10^4 x entry), where D = the setup's stop distance; same $ risk, so every result is in units
of the trade's own risk (R' = P/L / D'), and costs in R shrink by D / D'.
- **W60, W80, W100:** X = 60 / 80 / 100 bp; target price unchanged (U as in the live geometry). holdtr trails use D'.
- **W80S:** X = 80 bp with the target scaled in proportion (U' = U x D'/D), i.e. the same R:R as the setup.

## Scoring (excess over the current stop, Lead standard)
delta = variant R' - BASE R per trade (BASE = the current stop, same engine), day-clustered t of the daily summed delta;
TRAIN (<= 2025-09-30) / VALID; SPY up / down / quiet sums; delta w/o best day; per family (leading name token; all GEN-* =
GEN) x side: n, share of trades changed (D < X), delta avg, better / worse. **Retention:** every trade is kept (no skips),
so retention = top-decile winners (by BASE R within each family) still closing > 0 under the variant, and their summed
R' vs BASE R. Cost/R before and after (median) per family.

## Pass (lead worth pursuing; any live change is the owner's call)
Book delta t >= 2.65 (family bar); TRAIN and VALID > 0; up-day AND down-day summed delta > 0; delta w/o best day > 0;
more families better than worse; no family worse by more than 0.03R per trade; >= 90% of top-decile winners still > 0.
