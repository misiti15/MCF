# NH1 — quiet-top continuation long (Scout plan, FROZEN 2026-11-09 13:45 ET, before any score)

*Educational only — not financial advice. Pre-registration only; nothing scored. Script next (research/nh1/nh1.py).*

## Why (and why this shape, not another HOD break)
Observer (research/obs-longmovers, 6 sessions, descriptive): the long movers we MISS sit at the decision bar with fromOpen ~0,
RSI ~49 and within 0.23 ATR of the HOD; the ones we catch are dip reversals (fromOpen -1.7%, RSI 23). Our long book is a
dip-buying book. But a mover that is ~flat on the day AND near its high is a name whose **whole session so far is a narrow
range with price pinned at its top** — a quiet coil at the high, before the move, not a breakout already under way.
What the family already says (so we don't repeat it): plain HOD-break longs lose (bdi-rdt-r07: -0.099R, up +0.061 /
down -0.308); in-play continuation has ~0 excess over random (mh-1029); orb20_a + 225 guard sets reach +0.014R at best;
WT bull flag's +0.1..0.2R was 73% one day (2025-04-09). So NH1 (a) enters *before* any break, inside a compressed day,
(b) is judged on excess over same-minute random longs in the same fromOpen bucket, and (c) caps same-day clustering.

## Family try-count
Near-HOD / new-high / ORB / gap-and-go / opening-drive / flag-breakout continuation longs in backlog.jsonl + pod1022:
**N = 1,663** (t2-orb15 32, t3-rvol-cons 38, t5-inside-bar 24, orb20_a 1, bdi-tg-orb20-a 463, bdi-tod-open-0935 30,
rdt r01/r04/r07/r18/r19 640, cwt a3 72 / a4 32 / a8 80 / b4 32 / b6 32, mh-1029-inplay 8, 3barplay 8, reddit-1030 orbfvg
f1-f3,f5,f6 113, rs-spydip-orh 4, sat1031 gap-and-go 4, pod1022 long-continuation lines 50). GEN NewHOD: the live GEN
NewHOD setups are all SHORTS and the generator registry is hashed, so GEN tries can't be attributed (not counted, flagged).
Observer's 09:50 opening-drive measurement adds its count when it runs. + NH1's 8 = **1,671: full bar 3.85, BAR90 3.47**.
NH1's own bar (N 8): BAR90 1.84 -> a pass there is only a "lead worth pursuing".

## Data
2-year lab history as gate2: 1-min SIP cache -> 5-min RTH bars, `lib.daily()`; **locked block 2024-11-01..2025-02-28
filtered at read and asserted absent**; rolling windows restart after a > 5-day gap. Universe = gate2 I-HB base without the
beta filter: top-500 by adv20 x ATR% with adv20 >= $95M, earnings blackout out, index ETFs and ETPs (SC1 `ETP_RE`) out.

## Rule (bar closes 09:50..14:00; first signal per symbol-day)
- **Compressed day so far:** HOD - LOD (since 09:30) <= K x ATR_d.
- **At the top:** HOD - close <= 0.25 x ATR_d and close in the top 30% of the day's range.
- **Not a dip, not stretched:** 0 <= fromOpen <= 0.5 x ATR_d; RSI(14) of 5-min closes (prior session's bars seed it) in [45, 65].
- **Market context M:** M0 none | M1 SPY close >= its open at the signal bar.
- **Entry** next bar open. **Stop** = LOD so far - 0.05 ATR_d; skip if risk < 0.15 ATR_d or > 1.0 ATR_d.
- **Exit** E1 15:55 close | E2 breakeven at +1R, trail 1R from +2R (gate2 E2 logic). Stop-first, gaps fill at the open.
- Costs: production as gate2 `trade()` (tod multiplier, + 4.4bp spread on entry, 2c on stops).

## Grid (8 configs, all reported)
K {0.5, 0.8} x exit {E1, E2} x M {M0, M1}.

## Controls and reports (no extra configs)
- **C1 (pass control, Lead):** same-minute random long from the universe whose fromOpen at that bar is in the same bucket
  ([0, 0.25) or [0.25, 0.5] ATR_d) and that is NOT a signal; same stop rule (its own LOD - 0.05 ATR, same skip bounds; up to 5
  draws) and exit. Excess = r - r_C1, day-clustered t.
- **C2 (descriptive):** same name and bar, same stop, but the name is in the BOTTOM 30% of its compressed range (quiet but not
  at the top) — does "at the top" matter?
- Up / down / quiet day split (SPY o-c +-0.25%), TRAIN (<= 2025-09-30) / VALID / live (>= 2026-10-06), walk-forward share,
  avg R w/o best day, best-day share, **share of trades on the busiest day** (WT-flag lesson), trades per session, median cost/R.
- North-star check (descriptive, 6 days): of the Move Hunt long movers (research/bdi/moves/moves.csv, decision >= 09:50,
  non-blackout), how many fire NH1 at or before their decision bar.

## Pass (Testing, BAR90) — all required
C1-excess t >= 3.47 (family bar) and raw t >= 3.47; TRAIN > 0 and VALID > 0; up-day AND down-day avg R > 0; walk-forward
positive months >= 54%; avg R w/o best day > 0; best-day share < 50%. At NH1's own bar (1.84) a result is a lead only.
