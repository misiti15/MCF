# Time-of-day evidence study (BDI, 2026-10-09)

*Educational only - not financial advice. Lab results on history only; nothing here is a live or paper result.*

Owner question (2026-10-09): "Is there really significant evidence that certain setups work better in certain
timeframes throughout the day? I do not want to limit our system for a setup that we only test or think would work in
a particular time frame and not others." Also: what would it take to trade 09:30-09:50 with confidence.

## 0. Pre-declaration (written before any trade was scored)

### 0.1 Data
- Open two-year history only: research/history2y lab frames, 2024-10-01 .. 2026-10-07 minus the rule-19 locked block
  (2024-11-01 .. 2025-02-28). `MCF_HIST_ALLOW_LOCKED` is never set; loaders refuse the locked months.
- Production costs (mcf/research/gates.prod_r): 1c + 1 bps per side, exit side free on target fills, +2c on stops.
- Sessions classed up / flat / down by mcf/research/gates.session_regimes (history2y/lib.regimes).
- Halves for the out-of-sample time test: H1 = open sessions up to and including the median open session date,
  H2 = the rest (equal session counts; H1 is roughly 2024-10 + 2025-03..2025-11, H2 2025-11..2026-10).

### 0.2 Setups (30)
Live config lab setups (exhaustion_short, MF1-MF5, NS1-NS5, RW6G1), heat_fade_short, heat_fade_long, ST1-ST8
(stack1009 modules), RW1-RW8 (rework1008 modules). Each keeps its min_adv (point-in-time adv20), side, exit geometry
and every non-time condition. The modules are NOT edited: the study loads a copy of each module's logic with only the
time-of-day clause removed (`tod_free.py`; ST modules: WINDOW overridden to (950, 1500); RW/NS/MF/exhaustion: the
literal `(tod >= a) & (tod <= b)` clause stripped from the source text; heat: `regime_score` re-called with
950..1500, same weights / gate / cost term / threshold; RW6G1: same module with its tod clause stripped, the VWAP
+2 SD band guard computed from 5-minute bars resampled from data/cache_hist/1Min). The ST opening-range trigger
(`tod > 1000`, OR = 09:30-10:00) is structural, not a window, and is kept.
orb20_a and intraday_momentum are time-defined by construction (an opening-range break; a 10:00 signal held from
15:30) - they have no "time layer" to remove and are not part of the bucket test.

### 0.3 Buckets (entry = bar close ET)
B1 09:50-10:30 (tod 950..1030), B2 10:35-11:30, B3 11:35-13:00, B4 13:05-14:00, B5 14:05-15:00.

### 0.4 Trade definitions
- **Current window**: the setup as configured (module window intersected with the YAML window), first qualifying bar
  per symbol-day (as research/history2y/rescore.py).
- **Full day**: tod clause removed, 09:50-15:00, first qualifying bar per symbol-day (what live would do if the window
  were widened).
- **Per-bucket**: tod clause removed, first qualifying bar per symbol-day *inside each bucket* (= the rule run with
  that bucket as its window). A symbol-day can trade in several buckets; all inference is clustered by session.

### 0.5 Tests (per setup), declared before scoring
- Per bucket: n, exp R after costs, day-clustered t (gates.summary), exp in up / down sessions.
- **Primary test of "expectancy differs across buckets":** within-session permutation test. Statistic
  F = sum_b n_b (mean_b - mean)^2 over the 5 buckets. Bucket labels are shuffled among the trades of the same session
  (2,000 permutations, seed 20261009), so day effects (regime) are held fixed and only within-day timing is tested.
  p = (1 + #{F_perm >= F_obs}) / 2001.
- **Secondary:** OLS of r on bucket dummies with session-clustered (CR1) covariance; Wald chi2 (4 df) for equal means.
- Benjamini-Hochberg across the 30 setups on the primary p, q = 0.10 declared as the discovery threshold (q = 0.05
  also reported).
- **Window selection check:** best bucket (highest exp with n >= 30) chosen on H1, scored on H2, and vice versa;
  compared with the full day on the same half. Pre-declared summary: the share of (setup, direction) pairs where the
  in-sample best bucket beats the full day out of sample, and the mean OOS difference (R). Also: the current window
  vs full day on H1 and H2 separately.
- **Pooled view:** for each setup, bucket exp minus that setup's full-day exp (relative time effect), averaged with
  equal weight per setup, split by side (long / short), by half (H1 / H2) and by regime (up / down). A pattern counts
  as robust only if it has the same sign in both halves and both regimes for that side. Reference: the random-bar
  baseline per bucket and side (every bar of every name with adv20 >= 95M, t1s1).

### 0.6 Opening window extension (EXPLORATORY)
- Frames built from data/cache_hist/1Min with the same pipeline (heat_frame + extra_features + lab outcomes, R =
  0.25 x daily ATR, exit by 15:55), but keeping the 09:35 / 09:40 / 09:45 bar closes. Locked-block rows dropped at
  load, before any computation; the first 10 open sessions after the block (2025-03) are dropped (warm-up across the gap).
- Population: adv20 >= 95M (point in time). Exit t1s1.
- Rules (10, both directions where meaningful), each scored at each decision bar 09:35, 09:40, 09:45 separately and
  for reference in B1 (09:50-10:30, first per symbol-day) on the same frames:
  O1 gap-go long: gap > +1% and fromOpen > 0;  O2 gap-go short: gap < -1% and fromOpen < 0;
  O3 gap-fail short: gap > +1% and fromOpen < 0;  O4 gap-fail long: gap < -1% and fromOpen > 0;
  O5 VWAP-with long: vwapDistPct > 0 and fromOpen > 0;  O6 VWAP-with short: vwapDistPct < 0 and fromOpen < 0;
  O7 RSI5 fade short: rsi5 >= 90;  O8 RSI5 fade long: rsi5 <= 10;
  O9 RSI5 momentum long: rsi5 >= 90;  O10 RSI5 momentum short: rsi5 <= 10;
  plus the random-bar baselines (long, short). 10 rules x 3 bars = 30 configurations, cost multiplier 1x / 2x / 3x on
  every per-side cost (1c + 1 bps, +2c stop extra) as a spread-width sensitivity - not extra configurations.
- Nothing from 0.6 can be proposed for live from this study (exploratory, train-and-report only).

### 0.7 Recommendation rule per setup (declared before scoring)
- **keep window**: the time test is a BH discovery (q <= 0.10) AND the current window's exp beats the full day's exp
  in BOTH halves (H1 and H2).
- **widen to full day**: q > 0.10 - no detectable within-session time effect, so the window is not supported by
  evidence. (Whether the setup is worth trading at all is a separate question - rescore verdicts stand.)
- **unclear**: q <= 0.10 but the window's advantage over the full day does not hold in both halves (time matters,
  but not in the way the current window encodes; a re-window is a new lineage step on train/valid, not adopted here).
- Any window change is a setup change: it goes to the backlog (rule 16), never straight to live.
- Setups whose current window already is 09:50-15:00 (MF5, RW8) can only be "keep (full day)" or "unclear".

## Results
(appended below after scoring)
