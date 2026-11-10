# COMPCAL — a calibrated close-side line vs the sparse cell table (Builder, frozen 2026-11-10 ~14:30 ET, before any score)

*Educational only — not financial advice.* Owner COMPASS task (owner-20261110-1405-1, part 2: continuous conditional
stats to fall back on); builds on main-session research/compass_5m (claude/charming-mccarthy-i3rhhr) and Observer's
benchmark (observer-20261110-1342-1/2). Display research only; no trading change.

Target: at mark T (every 10 min, 10:00..15:50; SPY state from 1-min bars that START before T), y = 1 if SPY closes on the
same side of its open as it is at T (marks with SPY exactly at its open dropped). Prior-close side = SPY at T above /
below yesterday's close.
Models (all fitted / looked up on TRAIN only, or on data strictly before the day):
- **M0 cell table** (the card's current fall-back): time (10-min) x SPY-from-open bin (<-0.4, -0.4..-0.2, -0.2..0, 0..0.2,
  0.2..0.4, >0.4 %) x prior-close side; P = TRAIN hit rate of the cell (cells n < 15 fall back to time x bin; Laplace +1/+2).
- **M1 remaining-move benchmark** (Observer): P = share of the prior 60 sessions whose SPY move from the same T to the
  close, m, satisfies sign(fo) x (fo + m) > 0 (fo = today's SPY % from open at T). No fitting.
- **M2 = M1 + prior-close side:** logit(P) = a + b logit(M1) + c x [same side as yesterday's close], a/b/c fit on TRAIN.
Periods: TRAIN <= 2025-09-30; VALID 2025-10-01..2026-10-07; FWD 2026-10-08..2026-11-09. Locked block absent.
Scores: Brier score and log loss per period; day-clustered t of the per-day Brier difference (M1 - M0, M2 - M0, M2 - M1);
calibration table (10 bins) per model. 3 comparisons; reporting at t >= 2 (descriptive tool comparison, not a trading
bar). Recommendation rule (fixed): the card should use the model with the lowest Brier in BOTH VALID and FWD, unless the
difference vs M0 has |t| < 1 in VALID, in which case the simpler M1 line is preferred for being continuous.
