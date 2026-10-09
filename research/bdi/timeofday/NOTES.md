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

### 0.5a Deviation (recorded 2026-10-09 after the first run, before the corrected test was run)
The declared within-session *row* shuffle is not a valid null here: by construction a symbol-day contributes at most one
trade per bucket, and a symbol's trades on the same day are positively correlated. The row shuffle can put those
correlated trades into the same bucket, which the real design never does, so the permuted F is inflated and the test is
conservative (heat_fade_long: observed F 26 vs a null median of 66, p = 1.0; NS5, RW8 likewise). The cluster Wald
(secondary) had already been seen at this point. Correction: the primary test becomes a **within-session block
relabelling** - each session's five bucket labels are permuted as whole blocks (one random permutation per session,
2,000 draws), which keeps the one-per-bucket structure and the within-day correlation. Both p-values are reported
(`rowperm_p` = as declared, `perm_p` = corrected); BH and the recommendation rule use the corrected one.

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

**Configurations scored in this study:** 30 setups x 7 trade sets (current, full day, 5 buckets) = 210 rule runs, plus
30 exploratory opening configurations (0.6). Nothing was fitted; the buckets and tests were fixed in 0.3-0.5 (with the
0.5a correction). Reproduction check: every current-window result equals research/history2y/rescore.csv exactly
(e.g. heat_fade_short n 14,433 / +0.0168R; RW6G1 n 424 / +0.2637R; ST1-ST8 equal the stack1009 table).
Open history: 426 sessions, H1 = 213 sessions to 2025-12-01, H2 = 213 sessions after.

### Failures and caveats first
- **The declared row-shuffle permutation test was wrong for this design** (0.5a). It is reported as `rowperm_p` but
  not used. With it, 7 setups were BH discoveries; with the corrected block relabelling, 1 is.
- **The windows' "advantage" is mostly selection.** Choosing each setup's best bucket on one half gives +0.105R over the
  full day in-sample but only **+0.015R +- 0.014 out of sample** (60 setup-half pairs; the chosen bucket beats the full
  day out of sample in 57% of pairs - near a coin flip). About 85% of the apparent time-window edge disappears.
- Every window was chosen in-sample (table below). For the heat, exhaustion, MF, NS and RW lineages the window was
  searched on 2026 data (inside H2), so H1 (mostly data no study had loaded before rule 19) is their only out-of-sample
  half. On H1 those 20 setups' windows beat the full day by +0.031R +- 0.018 (11 of 20); on H2 (in-sample) by
  +0.056R +- 0.009 (18 of 20). The ST1-ST8 windows were chosen on the whole open history, so no half is out of sample
  for them, and RW6G1's band guard was chosen on the whole history too.
- Most of these setups lose money at production cost in the window AND over the full day (rescore verdicts stand).
  "Widen" below never means the setup becomes tradeable - it means the time layer is not supported by evidence.
- Setups share lineages (NS2 -> RW6 -> RW6G1; NS3 -> RW4; MF2 -> RW1/RW7; MF3 -> RW3/RW5; exhaustion -> RW2; NS2 -> RW8), so the 30 tests are not
  independent; BH is valid under this positive dependence but the effective number of separate findings is smaller.
- Survivorship: today's 1,226 names applied to the past (as RESCORE.md).
- **Live/lab parity defect found in passing (housekeeping, not fixed here):** live and the backtester warm the 5-minute
  indicators with only the prior 40 bars (mcf/data/priors.py tail5, mcf/backtest/engine.py tail(40)), so the 5-min
  SMA50 is NaN until the 10:20 bar close and an SMA50 cross cannot fire before 10:25 live. The lab frames are
  continuous, so they do fire there. Share of current-window lab trades before 10:25 that live cannot take: NS3 40%
  (+0.099R), RW4 39% (+0.099R), NS2 23%, RW6 21%, NS5 12%, RW6G1 11% (+0.011R). Fix: carry >= 50 (e.g. 60) prior bars.
  This matters for any time-of-day statement about 09:50-10:20.

### Who chose each window
| Lineage | window search |
|---|---|
| heat_fade_short / long | heat study: 5-7 tod windows x gates (2026-06..10 data) |
| exhaustion_short, RW2 | setups2 swarm: 6 time windows (2026 data) |
| MF1-MF5 | MarcoFlow session windows ranked on 2026-08/09 data (MF5 already 09:50-15:00) |
| NS1-NS5 | owner1008 scan am / pm / all (2026 data) |
| RW1-RW8 | rework1008 grid: 5 windows (2026 data; RW8 already 09:50-15:00) |
| RW6G1 | RW6's window (2026 data); band guard chosen on the whole open 2-year history |
| ST1-ST8 | stack1009 am / mid / pm, chosen on the whole open 2-year history |

### 1. Is expectancy different across the day? (per setup)
Corrected primary test (block relabelling within sessions): raw p <= 0.05 for 5 of 30 setups (RW6G1 0.003, ST4 0.007,
NS1 0.029, ST1 0.034, ST6 0.043) - about what 30 x 5% = 1.5 false positives plus a little signal would give. After
Benjamini-Hochberg only **RW6G1 (q 0.090)** clears q <= 0.10; none clears q <= 0.05. The secondary session-clustered
Wald test is more liberal (BH q <= 0.05: RW6G1, ST2, ST1, ST4; q <= 0.10 adds NS1, ST8); its small-bucket behaviour is
less reliable (ST2: Wald p 0.0003, block p 0.42).

The one consistent, large time pattern is inside the NS2 -> RW6 -> RW6G1 lineage: **13:05-14:00 is strongly negative**
(NS2 -0.224R t -4.1, RW6 -0.227R t -3.3, RW6G1 -0.208R t -2.9), negative in both halves and in up and down sessions
for RW6/RW6G1. That is evidence *against one hour*, not for the 09:50-11:30 window as such.

| Setup | side | window | current n (/day) | current exp (t) | full-day n (/day) | full-day exp (t) | B1 09:50-10:30 | B2 10:35-11:30 | B3 11:35-13:00 | B4 13:05-14:00 | B5 14:05-15:00 | block-perm p | BH q | Wald p | H1 cur / full | H2 cur / full | best bucket on H1 -> H2 exp (full H2) | best on H2 -> H1 exp (full H1) | Rule 0.7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| heat_fade_short | short | 950-1030 | 14433 (33.88) | +0.017 (0.68) | 75136 (176.38) | -0.032 (-2.22) | +0.017 (14433) | -0.031 (18449) | -0.038 (37267) | -0.042 (30809) | -0.011 (32833) | 0.3033 | 0.700 | 0.2740 | +0.001 / -0.054 | +0.028 / -0.016 | B1: +0.028 (-0.016) | B1: +0.001 (-0.054) | widen to full day |
| heat_fade_long | long | 1105-1330 | 14460 (33.94) | -0.046 (-1.16) | 23506 (55.18) | -0.031 (-1.22) | -0.051 (7394) | -0.037 (10025) | -0.042 (9416) | -0.003 (5613) | +0.032 (4522) | 0.7211 | 1.000 | 0.4671 | -0.068 / -0.039 | -0.029 / -0.025 | B5: +0.057 (-0.025) | B5: -0.004 (-0.039) | widen to full day |
| exhaustion_short | short | 1300-1500 | 5973 (14.02) | -0.010 (-0.32) | 28458 (66.8) | -0.059 (-3.59) | -0.081 (8461) | -0.071 (11558) | -0.055 (7104) | -0.013 (3236) | -0.010 (2942) | 0.5347 | 0.930 | 0.5858 | -0.056 / -0.106 | +0.027 / -0.026 | B5: +0.018 (-0.026) | B4: -0.097 (-0.106) | widen to full day |
| MF1-945-flowsell-vwapup | short | 950-1030 | 2389 (5.61) | -0.058 (-2.1) | 10540 (24.74) | -0.074 (-5.41) | -0.061 (2679) | -0.067 (5508) | -0.104 (1819) | -0.053 (987) | -0.132 (733) | 0.5387 | 0.930 | 0.1250 | -0.129 / -0.093 | +0.019 / -0.054 | B2: -0.074 (-0.054) | B1: -0.129 (-0.093) | widen to full day |
| MF2-open-rsimidhi-flowsell | short | 950-1100 | 610 (1.43) | -0.030 (-0.83) | 4517 (10.6) | -0.046 (-2.23) | -0.037 (185) | -0.012 (883) | -0.052 (1865) | -0.045 (1026) | -0.067 (804) | 0.9085 | 1.000 | 0.8525 | -0.060 / -0.029 | -0.015 / -0.058 | B4: -0.080 (-0.058) | B2: -0.056 (-0.029) | widen to full day |
| MF3-open-flowsell-rsi5hi | short | 950-1100 | 4136 (9.71) | -0.074 (-2.5) | 10564 (24.8) | -0.071 (-4.07) | -0.079 (2248) | -0.062 (3229) | -0.079 (2680) | -0.074 (1805) | -0.097 (1398) | 0.9650 | 1.000 | 0.9369 | -0.112 / -0.094 | -0.033 / -0.049 | B5: -0.118 (-0.049) | B1: -0.144 (-0.094) | widen to full day |
| MF4-h40-open-flowsell | short | 950-1100 | 3318 (7.79) | -0.089 (-3.02) | 7273 (17.07) | -0.079 (-4.51) | -0.069 (1503) | -0.090 (3238) | -0.061 (1823) | -0.109 (909) | -0.091 (724) | 0.9020 | 1.000 | 0.7923 | -0.145 / -0.116 | -0.041 / -0.048 | B5: -0.137 (-0.048) | B3: -0.096 (-0.116) | widen to full day |
| MF5-flowsell-vwapup-rsi5hi | short | 950-1500 | 6827 (16.03) | -0.052 (-2.39) | 6827 (16.03) | -0.052 (-2.39) | -0.042 (1920) | -0.061 (2954) | -0.077 (1257) | -0.024 (731) | -0.114 (535) | 0.8031 | 1.000 | 0.3463 | -0.093 / -0.093 | -0.006 / -0.006 | B2: -0.043 (-0.006) | B1: -0.133 (-0.093) | widen to full day |
| NS1-rsidip-rsi5pop-long | long | 950-1130 | 444 (1.04) | +0.034 (0.87) | 2438 (5.72) | -0.068 (-3.34) | -0.008 (134) | +0.050 (314) | -0.094 (856) | -0.122 (629) | -0.042 (565) | 0.0285 | 0.255 | 0.0174 | -0.022 / -0.066 | +0.065 / -0.068 | B2: +0.081 (-0.068) | B2: -0.028 (-0.066) | widen to full day |
| NS2-sma50break-overbought-short | short | 950-1130 | 3124 (7.33) | +0.006 (0.11) | 8151 (19.13) | -0.054 (-1.79) | +0.012 (853) | +0.010 (2351) | -0.046 (1981) | -0.224 (1226) | -0.059 (2667) | 0.1599 | 0.480 | 0.0770 | +0.042 / -0.037 | -0.023 / -0.066 | B2: -0.057 (-0.066) | B1: -0.050 (-0.037) | widen to full day |
| NS3-failed-vwap-reclaim-short | short | 950-1130 | 1510 (3.54) | +0.056 (1.26) | 10201 (23.95) | -0.028 (-1.37) | +0.104 (788) | +0.006 (1009) | +0.021 (1391) | -0.059 (4405) | -0.009 (6087) | 0.2924 | 0.700 | 0.0953 | +0.055 / -0.027 | +0.057 / -0.028 | B1: +0.042 (-0.028) | B2: -0.154 (-0.027) | widen to full day |
| NS4-pm-vwap-reclaim-oversold-short | short | 1130-1500 | 1469 (3.45) | -0.065 (-2.03) | 1692 (3.97) | -0.054 (-1.88) | +0.019 (175) | -0.005 (89) | -0.024 (473) | -0.073 (458) | -0.093 (565) | 0.7281 | 1.000 | 0.6527 | -0.117 / -0.095 | -0.030 / -0.027 | B1: -0.014 (-0.027) | B1: +0.064 (-0.095) | widen to full day |
| NS5-sma50-flush-oversold-long | long | 950-1130 | 1305 (3.06) | -0.038 (-0.47) | 3139 (7.37) | -0.043 (-0.81) | +0.026 (171) | -0.050 (1142) | -0.082 (817) | -0.065 (358) | -0.014 (754) | 0.9780 | 1.000 | 0.9234 | -0.166 / -0.076 | +0.086 / -0.015 | B4: -0.147 (-0.015) | B1: -0.209 (-0.076) | widen to full day |
| RW6G1-ns2-up3-vwap2sd-short | short | 950-1130 | 424 (1.0) | +0.264 (2.39) | 1969 (4.62) | -0.011 (-0.18) | +0.057 (65) | +0.301 (362) | +0.069 (330) | -0.208 (462) | -0.060 (941) | 0.0030 | 0.090 | 0.0000 | +0.328 / +0.034 | +0.076 / -0.046 | B2: +0.028 (-0.046) | B1: -0.157 (+0.034) | keep window |
| ST1-ordn-long-pm-t05s1 | long | 1335-1500 | 395 (0.93) | +0.091 (2.53) | 1621 (3.81) | -0.053 (-1.99) | -0.101 (584) | -0.124 (173) | -0.091 (387) | -0.002 (264) | +0.100 (309) | 0.0340 | 0.255 | 0.0026 | +0.093 / -0.021 | +0.089 / -0.074 | B5: +0.087 (-0.074) | B5: +0.117 (-0.021) | widen to full day |
| ST2-slope20up-long-am-t05s1 | long | 950-1130 | 164 (0.38) | +0.128 (2.43) | 10956 (25.72) | -0.015 (-0.82) | +0.330 (31) | +0.082 (137) | -0.041 (4871) | +0.015 (3763) | -0.035 (3747) | 0.4198 | 0.840 | 0.0003 | +0.055 / -0.043 | +0.163 / -0.001 | B2: +0.109 (-0.001) | B2: +0.028 (-0.043) | widen to full day |
| ST3-rsi5up-short-pm-t1s1 | short | 1335-1500 | 358 (0.84) | +0.106 (2.35) | 657 (1.54) | +0.017 (0.41) | -0.003 (67) | -0.196 (67) | -0.065 (215) | +0.037 (216) | +0.090 (278) | 0.1254 | 0.418 | 0.1379 | +0.118 / +0.007 | +0.101 / +0.021 | B5: +0.056 (+0.021) | B4: -0.071 (+0.007) | widen to full day |
| ST4-emadn-long-am-t1s05 | long | 950-1130 | 168 (0.39) | +0.157 (2.29) | 1300 (3.05) | +0.018 (0.6) | +0.332 (64) | +0.050 (104) | +0.049 (316) | +0.028 (369) | -0.073 (472) | 0.0070 | 0.105 | 0.0021 | +0.093 / -0.027 | +0.187 / +0.043 | B4: +0.062 (+0.043) | B1: +0.382 (-0.027) | widen to full day |
| ST5-pdbrkup-short-mid-t05s1 | short | 1135-1330 | 162 (0.38) | +0.107 (2.17) | 426 (1.0) | -0.035 (-0.82) | -0.081 (187) | -0.086 (212) | +0.095 (145) | +0.201 (50) | +0.028 (73) | 0.0835 | 0.358 | 0.0306 | -0.030 / -0.070 | +0.184 / -0.014 | B1: -0.130 (-0.014) | B3: -0.043 (-0.070) | widen to full day |
| ST6-volspikeup-short-mid-t1s1 | short | 1135-1330 | 222 (0.52) | +0.126 (2.15) | 607 (1.42) | +0.024 (0.68) | +0.035 (22) | -0.361 (24) | +0.163 (143) | +0.024 (194) | -0.011 (311) | 0.0430 | 0.258 | 0.0284 | +0.178 / -0.057 | +0.107 / +0.054 | B3: +0.140 (+0.054) | B3: +0.234 (-0.057) | widen to full day |
| ST7-rsi50dn-long-pm-t1s1 | long | 1335-1500 | 166 (0.39) | +0.162 (2.02) | 1035 (2.43) | +0.033 (0.71) | -0.037 (7) | +0.010 (675) | -0.033 (141) | +0.156 (100) | +0.137 (115) | 0.8051 | 1.000 | 0.4443 | +0.041 / -0.050 | +0.248 / +0.074 | B4: +0.118 (+0.074) | B5: -0.098 (-0.050) | widen to full day |
| ST8-volspikedn-long-pm-t1s1 | long | 1335-1500 | 408 (0.96) | +0.107 (2.01) | 528 (1.24) | +0.041 (0.83) | -0.412 (31) | +0.072 (12) | -0.047 (52) | -0.024 (97) | +0.105 (353) | 0.0790 | 0.358 | 0.0145 | +0.107 / +0.021 | +0.106 / +0.048 | B5: +0.102 (+0.048) | B5: +0.112 (+0.021) | widen to full day |
| RW1-gapdn-bounce-flowsell-short | short | 950-1100 | 2489 (5.84) | -0.007 (-0.22) | 7474 (17.54) | -0.046 (-2.2) | -0.051 (540) | -0.019 (2853) | -0.069 (2364) | -0.087 (1276) | -0.040 (995) | 0.6197 | 0.979 | 0.5814 | -0.097 / -0.072 | +0.066 / -0.026 | B5: -0.063 (-0.026) | B2: -0.090 (-0.072) | widen to full day |
| RW2-exhaustion-noon-adv150-short | short | 1200-1500 | 7797 (18.3) | -0.009 (-0.35) | 22187 (52.08) | -0.056 (-3.3) | -0.080 (6436) | -0.066 (9001) | -0.051 (5618) | -0.003 (2620) | +0.002 (2397) | 0.4188 | 0.840 | 0.5177 | -0.041 / -0.101 | +0.015 / -0.025 | B5: +0.025 (-0.025) | B4: -0.093 (-0.101) | widen to full day |
| RW3-gapdn-rsi5pop-flowsell-short | short | 950-1100 | 1816 (4.26) | -0.041 (-1.22) | 5995 (14.07) | -0.068 (-3.1) | -0.020 (566) | -0.079 (1838) | -0.084 (2049) | -0.043 (1142) | -0.085 (813) | 0.8401 | 1.000 | 0.6519 | -0.091 / -0.087 | +0.006 / -0.051 | B4: -0.060 (-0.051) | B1: -0.089 (-0.087) | widen to full day |
| RW4-ns3-adv150-short | short | 950-1130 | 1216 (2.85) | +0.054 (1.13) | 8069 (18.94) | -0.028 (-1.33) | +0.105 (630) | +0.004 (810) | +0.033 (1130) | -0.058 (3471) | -0.013 (4831) | 0.2849 | 0.700 | 0.1010 | +0.039 / -0.027 | +0.062 / -0.029 | B1: +0.039 (-0.029) | B2: -0.220 (-0.027) | widen to full day |
| RW5-heat30-flowsell-rsi5pop-gapdn-short | short | 950-1100 | 1294 (3.04) | -0.013 (-0.32) | 5598 (13.14) | -0.058 (-2.47) | -0.073 (281) | -0.034 (1472) | -0.073 (2001) | -0.059 (1267) | -0.070 (851) | 0.9520 | 1.000 | 0.9373 | +0.007 / -0.053 | -0.033 / -0.061 | B2: -0.047 (-0.061) | B4: -0.117 (-0.053) | widen to full day |
| RW6-ns2-up3-short | short | 950-1130 | 1461 (3.43) | +0.057 (0.77) | 3614 (8.48) | -0.021 (-0.51) | -0.076 (354) | +0.104 (1142) | +0.008 (783) | -0.227 (549) | -0.039 (1181) | 0.1204 | 0.418 | 0.1342 | +0.101 / +0.006 | +0.010 / -0.040 | B2: +0.025 (-0.040) | B2: +0.170 (+0.006) | widen to full day |
| RW7-gapdn-bounce-early-short | short | 950-1030 | 1590 (3.73) | -0.029 (-0.94) | 26164 (61.42) | -0.058 (-2.91) | -0.029 (1590) | -0.030 (7618) | -0.063 (10384) | -0.098 (5642) | -0.056 (4394) | 0.5582 | 0.930 | 0.5291 | -0.063 / -0.082 | +0.008 / -0.038 | B5: -0.052 (-0.038) | B1: -0.063 (-0.082) | widen to full day |
| RW8-sma50up-spikefade-short | short | 950-1500 | 459 (1.08) | -0.090 (-1.4) | 459 (1.08) | -0.090 (-1.4) | – (0) | -0.154 (9) | -0.068 (111) | -0.077 (131) | -0.104 (213) | 0.9995 | 1.000 | 0.9904 | -0.080 / -0.080 | -0.096 / -0.096 | B4: -0.221 (-0.096) | B5: -0.241 (-0.080) | widen to full day |

Per-bucket up / down session expectancy (R):

| Setup | B1 up/down | B2 up/down | B3 up/down | B4 up/down | B5 up/down |
|---|---|---|---|---|---|
| heat_fade_short | -0.199 / +0.154 | -0.264 / +0.228 | -0.243 / +0.123 | -0.198 / +0.090 | -0.128 / +0.126 |
| heat_fade_long | +0.160 / -0.160 | +0.156 / -0.170 | +0.064 / -0.124 | +0.105 / -0.140 | +0.090 / -0.070 |
| exhaustion_short | -0.226 / +0.129 | -0.183 / +0.093 | -0.139 / +0.093 | -0.065 / +0.037 | -0.083 / +0.147 |
| MF1-945-flowsell-vwapup | -0.219 / +0.065 | -0.210 / +0.125 | -0.271 / +0.023 | -0.150 / +0.056 | -0.185 / -0.014 |
| MF2-open-rsimidhi-flowsell | -0.162 / +0.014 | -0.072 / +0.067 | -0.104 / +0.038 | -0.200 / +0.067 | -0.160 / +0.038 |
| MF3-open-flowsell-rsi5hi | -0.297 / +0.141 | -0.308 / +0.198 | -0.323 / +0.046 | -0.232 / +0.070 | -0.188 / +0.038 |
| MF4-h40-open-flowsell | -0.247 / +0.068 | -0.240 / -0.022 | -0.158 / +0.002 | -0.281 / +0.009 | -0.142 / +0.015 |
| MF5-flowsell-vwapup-rsi5hi | -0.275 / +0.187 | -0.310 / +0.227 | -0.334 / +0.074 | -0.187 / +0.142 | -0.235 / +0.087 |
| NS1-rsidip-rsi5pop-long | +0.143 / -0.217 | +0.071 / +0.058 | +0.049 / -0.240 | -0.021 / -0.275 | +0.046 / -0.199 |
| NS2-sma50break-overbought-short | -0.068 / +0.174 | -0.048 / +0.154 | -0.162 / +0.126 | -0.435 / +0.014 | -0.155 / +0.041 |
| NS3-failed-vwap-reclaim-short | +0.003 / +0.222 | -0.214 / +0.276 | -0.130 / +0.145 | -0.219 / +0.005 | -0.130 / +0.120 |
| NS4-pm-vwap-reclaim-oversold-short | -0.066 / +0.089 | -0.012 / -0.059 | -0.135 / +0.117 | -0.213 / +0.207 | -0.172 / +0.097 |
| NS5-sma50-flush-oversold-long | +0.683 / -0.157 | +0.053 / -0.211 | -0.066 / -0.168 | -0.017 / -0.075 | +0.110 / -0.043 |
| RW6G1-ns2-up3-vwap2sd-short | +0.094 / -0.006 | +0.347 / +0.096 | +0.111 / -0.135 | -0.334 / -0.115 | -0.137 / +0.036 |
| ST1-ordn-long-pm-t05s1 | -0.043 / -0.083 | -0.000 / -0.263 | -0.004 / -0.146 | +0.053 / -0.048 | +0.194 / +0.127 |
| ST2-slope20up-long-am-t05s1 | -0.082 / +0.483 | +0.104 / -0.044 | -0.002 / -0.076 | +0.065 / -0.026 | +0.080 / -0.144 |
| ST3-rsi5up-short-pm-t1s1 | -0.023 / -0.080 | -0.368 / +0.019 | -0.200 / -0.048 | -0.113 / -0.002 | +0.024 / +0.081 |
| ST4-emadn-long-am-t1s05 | +0.310 / +0.209 | +0.444 / -0.028 | +0.048 / -0.025 | +0.091 / -0.023 | +0.119 / -0.114 |
| ST5-pdbrkup-short-mid-t05s1 | -0.051 / -0.077 | -0.199 / -0.004 | +0.163 / +0.141 | -0.002 / +0.146 | +0.168 / -0.057 |
| ST6-volspikeup-short-mid-t1s1 | +0.217 / +0.504 | -0.517 / -0.328 | -0.088 / +0.204 | -0.105 / +0.113 | -0.039 / +0.040 |
| ST7-rsi50dn-long-pm-t1s1 | -1.042 / +0.264 | +0.256 / -0.124 | +0.138 / -0.084 | +0.317 / -0.062 | +0.223 / +0.214 |
| ST8-volspikedn-long-pm-t1s1 | -0.022 / -0.593 | +0.972 / -0.191 | -0.149 / -0.013 | +0.010 / +0.007 | +0.103 / -0.011 |
| RW1-gapdn-bounce-flowsell-short | -0.222 / +0.124 | -0.279 / +0.239 | -0.297 / +0.106 | -0.281 / +0.062 | -0.160 / +0.045 |
| RW2-exhaustion-noon-adv150-short | -0.224 / +0.131 | -0.178 / +0.113 | -0.131 / +0.096 | -0.047 / +0.039 | -0.063 / +0.151 |
| RW3-gapdn-rsi5pop-flowsell-short | -0.236 / +0.265 | -0.312 / +0.104 | -0.272 / +0.046 | -0.235 / +0.129 | -0.129 / +0.007 |
| RW4-ns3-adv150-short | +0.018 / +0.231 | -0.262 / +0.277 | -0.122 / +0.150 | -0.217 / +0.012 | -0.119 / +0.112 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short | -0.337 / +0.197 | -0.306 / +0.240 | -0.349 / +0.109 | -0.246 / +0.120 | -0.185 / +0.078 |
| RW6-ns2-up3-short | -0.111 / +0.033 | +0.073 / +0.196 | -0.044 / +0.102 | -0.393 / -0.073 | -0.117 / +0.067 |
| RW7-gapdn-bounce-early-short | -0.252 / +0.230 | -0.278 / +0.207 | -0.313 / +0.115 | -0.267 / +0.065 | -0.185 / +0.047 |
| RW8-sma50up-spikefade-short | – / – | -0.567 / -0.365 | -0.233 / +0.092 | -0.130 / -0.225 | -0.265 / +0.092 |


### 2. Pooled view (equal weight per setup; bucket exp minus that setup's full-day exp, R)
| side | slice | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|---|
| long (8 setups) | H1 | -0.055 | -0.014 | -0.058 | +0.064 | +0.032 |
| long | H2 | +0.070 | +0.037 | -0.033 | -0.014 | +0.048 |
| long | up sessions | +0.177 | +0.064 | -0.078 | -0.013 | +0.033 |
| long | down sessions | +0.027 | -0.007 | -0.012 | +0.017 | +0.067 |
| short (22 setups) | H1 | +0.007 | +0.017 | +0.022 | -0.039 | +0.003 |
| short | H2 | +0.038 | +0.007 | +0.010 | -0.003 | -0.009 |
| short | up sessions | +0.028 | -0.019 | +0.009 | -0.030 | +0.054 |
| short | down sessions | +0.027 | +0.052 | -0.003 | -0.039 | -0.020 |

Standard errors across setups are 0.01-0.05R (long B1: 0.10-0.13; only 7 long setups trade B1). Four cells keep their
sign in both halves and both regimes: long 11:35-13:00 (-), long 14:05-15:00 (+), short 09:50-10:30 (+), short
13:05-14:00 (-). Each is 0.01-0.05R, about one standard error, and the setups overlap - **no robust, tradeable
time-of-day pattern** in the pooled view.

Random-bar baseline (every bar, adv20 >= 95M, t1s1, production cost): -0.07 to -0.09R in every bucket for both sides.
By regime the gap is enormous and fades through the day (long: up sessions +0.146 at B1 -> +0.017 at B5; down
-0.303 -> -0.204). **The session regime moves expectancy by ~0.45R; time of day by ~0.02R.** Time windows mostly act
as a crude regime proxy (an early-morning short on a down day has more of the day's move left).

### 3. 09:30-09:50 (EXPLORATORY - not evidence for live)
What is available at 09:35-09:45 live: RSI(14), RSI(5), EMA9/21, MACD, buy pressure, volume ratio, momentum - all
computed over the prior 40 bars + today's, so warm. Gap, fromOpen, prior-day levels: yes. VWAP is 1-3 bars old (noisy).
SMA50 is NOT available live before 10:20 (see parity defect), SMA20 slope and 20-bar levels span yesterday's close.
No opening range exists yet. Lab frames were rebuilt from the 1-minute cache with the same pipeline (exact parity with
the history2y frames on overlapping bars; locked block dropped before computing; 416 sessions after the 10-session
warm-up drop).

Result: **all 30 opening configurations lose after costs at 1x** (best: O8 RSI5 <= 10 long at 09:45, -0.015R, t -0.5;
O4 gap-down-reclaim long at 09:45, -0.049R). At 2x / 3x cost (a fairer assumption for opening spreads) every one is
-0.09R to -0.33R. The random bar itself is -0.065 to -0.099R at 09:35-09:45, the same as at 09:50-10:30: the open is
not worse for a random entry at 1x cost, but nothing simple beats the random bar by more than +0.05R, and the regime
split dominates (gap-go long: +0.134 up / -0.254 down). To trade the open with confidence one would need (a) real
quote data for 09:30-09:50 spreads (the live journal's "shadow" signals are the place to measure it), (b) the 40-bar
warm-up fix, (c) a pre-declared rule set scored on train/valid of the history with the open bars kept (data/open
here), and (d) an entry/exit simulation on 1-minute bars, since 5-minute outcomes at the open hide the first-minute
spread and the stop-first ambiguity.

| Rule | bar | n (/day) | exp 1x (t) | exp 2x | exp 3x | vs random (1x) | up / down (1x) | H1 / H2 (1x) |
|---|---|---|---|---|---|---|---|---|
| O1 gap-go long | 09:35 | 28762 (69.14) | -0.061 (-2.52) | -0.129 | -0.197 | +0.017 | +0.134 / -0.254 | -0.055 / -0.064 |
| O1 gap-go long | 09:40 | 29293 (70.42) | -0.067 (-2.38) | -0.135 | -0.204 | +0.013 | +0.135 / -0.270 | -0.063 / -0.069 |
| O1 gap-go long | 09:45 | 29550 (71.03) | -0.077 (-2.32) | -0.145 | -0.212 | -0.012 | +0.140 / -0.289 | -0.101 / -0.063 |
| O1 gap-go long | B1 09:50-10:30 | 39800 (95.67) | -0.065 (-2.22) | -0.134 | -0.202 | +0.005 | +0.147 / -0.254 | -0.063 / -0.066 |
| O2 gap-go short | 09:35 | 26907 (64.68) | -0.066 (-1.8) | -0.133 | -0.201 | +0.025 | -0.210 / +0.125 | -0.038 / -0.082 |
| O2 gap-go short | 09:40 | 27065 (65.06) | -0.089 (-2.13) | -0.157 | -0.226 | -0.004 | -0.277 / +0.200 | -0.087 / -0.090 |
| O2 gap-go short | 09:45 | 27464 (66.02) | -0.141 (-3.26) | -0.210 | -0.279 | -0.041 | -0.375 / +0.142 | -0.218 / -0.091 |
| O2 gap-go short | B1 09:50-10:30 | 35972 (86.47) | -0.089 (-2.43) | -0.157 | -0.225 | +0.004 | -0.361 / +0.211 | -0.129 / -0.065 |
| O3 gap-fail short | 09:35 | 32139 (77.26) | -0.080 (-3.05) | -0.148 | -0.216 | +0.011 | -0.294 / +0.091 | -0.124 / -0.053 |
| O3 gap-fail short | 09:40 | 31704 (76.21) | -0.070 (-2.64) | -0.138 | -0.207 | +0.015 | -0.269 / +0.065 | -0.137 / -0.027 |
| O3 gap-fail short | 09:45 | 31522 (75.77) | -0.070 (-2.71) | -0.140 | -0.209 | +0.029 | -0.267 / +0.069 | -0.112 / -0.045 |
| O3 gap-fail short | B1 09:50-10:30 | 41198 (99.03) | -0.066 (-2.59) | -0.135 | -0.204 | +0.027 | -0.270 / +0.057 | -0.138 / -0.022 |
| O4 gap-fail long | 09:35 | 28965 (69.63) | -0.073 (-2.16) | -0.141 | -0.209 | +0.004 | +0.070 / -0.258 | -0.060 / -0.082 |
| O4 gap-fail long | 09:40 | 28894 (69.46) | -0.070 (-1.84) | -0.138 | -0.206 | +0.011 | +0.138 / -0.311 | -0.041 / -0.088 |
| O4 gap-fail long | 09:45 | 28545 (68.62) | -0.049 (-1.25) | -0.116 | -0.184 | +0.016 | +0.236 / -0.362 | +0.067 / -0.123 |
| O4 gap-fail long | B1 09:50-10:30 | 38877 (93.45) | -0.026 (-0.71) | -0.092 | -0.159 | +0.044 | +0.255 / -0.358 | +0.059 / -0.084 |
| O5 vwap-with long | 09:35 | 156457 (376.1) | -0.091 (-5.96) | -0.172 | -0.253 | -0.014 | +0.088 / -0.292 | -0.083 / -0.098 |
| O5 vwap-with long | 09:40 | 151958 (365.28) | -0.081 (-4.64) | -0.161 | -0.242 | -0.000 | +0.125 / -0.310 | -0.067 / -0.092 |
| O5 vwap-with long | 09:45 | 148975 (358.11) | -0.077 (-4.35) | -0.158 | -0.238 | -0.013 | +0.134 / -0.311 | -0.049 / -0.101 |
| O5 vwap-with long | B1 09:50-10:30 | 243339 (584.95) | -0.076 (-4.89) | -0.157 | -0.238 | -0.006 | +0.157 / -0.313 | -0.055 / -0.094 |
| O6 vwap-with short | 09:35 | 155382 (373.51) | -0.105 (-6.6) | -0.185 | -0.266 | -0.013 | -0.294 / +0.065 | -0.138 / -0.079 |
| O6 vwap-with short | 09:40 | 146216 (351.48) | -0.086 (-5.23) | -0.168 | -0.249 | -0.002 | -0.291 / +0.117 | -0.116 / -0.064 |
| O6 vwap-with short | 09:45 | 149177 (358.6) | -0.114 (-6.09) | -0.196 | -0.278 | -0.014 | -0.342 / +0.103 | -0.145 / -0.089 |
| O6 vwap-with short | B1 09:50-10:30 | 236633 (568.83) | -0.091 (-5.81) | -0.172 | -0.254 | +0.002 | -0.329 / +0.117 | -0.116 / -0.070 |
| O7 rsi5 fade short | 09:35 | 62404 (150.01) | -0.126 (-6.2) | -0.212 | -0.299 | -0.035 | -0.341 / +0.062 | -0.176 / -0.089 |
| O7 rsi5 fade short | 09:40 | 55645 (133.76) | -0.105 (-4.58) | -0.192 | -0.278 | -0.021 | -0.298 / +0.090 | -0.163 / -0.061 |
| O7 rsi5 fade short | 09:45 | 48174 (115.8) | -0.083 (-3.33) | -0.169 | -0.256 | +0.017 | -0.272 / +0.107 | -0.111 / -0.061 |
| O7 rsi5 fade short | B1 09:50-10:30 | 141805 (340.88) | -0.085 (-5.21) | -0.169 | -0.253 | +0.008 | -0.296 / +0.138 | -0.122 / -0.054 |
| O8 rsi5 fade long | 09:35 | 59457 (142.93) | -0.106 (-4.33) | -0.192 | -0.277 | -0.029 | +0.044 / -0.282 | -0.124 / -0.094 |
| O8 rsi5 fade long | 09:40 | 52151 (125.36) | -0.075 (-2.72) | -0.159 | -0.243 | +0.006 | +0.132 / -0.323 | -0.079 / -0.071 |
| O8 rsi5 fade long | 09:45 | 46919 (112.79) | -0.015 (-0.48) | -0.097 | -0.179 | +0.050 | +0.235 / -0.273 | +0.024 / -0.045 |
| O8 rsi5 fade long | B1 09:50-10:30 | 131070 (315.07) | -0.077 (-4.41) | -0.159 | -0.242 | -0.006 | +0.164 / -0.289 | -0.070 / -0.082 |
| O9 rsi5 mom long | 09:35 | 62404 (150.01) | -0.057 (-2.75) | -0.139 | -0.222 | +0.021 | +0.163 / -0.252 | -0.027 / -0.079 |
| O9 rsi5 mom long | 09:40 | 55645 (133.76) | -0.070 (-3.07) | -0.153 | -0.237 | +0.010 | +0.126 / -0.269 | -0.029 / -0.101 |
| O9 rsi5 mom long | 09:45 | 48174 (115.8) | -0.093 (-3.76) | -0.179 | -0.265 | -0.028 | +0.097 / -0.283 | -0.083 / -0.101 |
| O9 rsi5 mom long | B1 09:50-10:30 | 141805 (340.88) | -0.083 (-5.1) | -0.167 | -0.250 | -0.013 | +0.131 / -0.308 | -0.061 / -0.102 |
| O10 rsi5 mom short | 09:35 | 59457 (142.93) | -0.073 (-2.94) | -0.156 | -0.239 | +0.018 | -0.217 / +0.103 | -0.074 / -0.071 |
| O10 rsi5 mom short | 09:40 | 52151 (125.36) | -0.099 (-3.63) | -0.183 | -0.268 | -0.014 | -0.299 / +0.149 | -0.111 / -0.090 |
| O10 rsi5 mom short | 09:45 | 46919 (112.79) | -0.156 (-5.18) | -0.243 | -0.329 | -0.057 | -0.398 / +0.102 | -0.210 / -0.115 |
| O10 rsi5 mom short | B1 09:50-10:30 | 131070 (315.07) | -0.090 (-5.14) | -0.173 | -0.255 | +0.003 | -0.329 / +0.124 | -0.111 / -0.073 |
| random long | 09:35 | 377177 (906.68) | -0.077 (-5.92) | -0.159 | -0.240 | +0.000 | +0.112 / -0.265 | -0.064 / -0.088 |
| random long | 09:40 | 376104 (904.1) | -0.080 (-5.59) | -0.162 | -0.243 | +0.000 | +0.128 / -0.296 | -0.068 / -0.090 |
| random long | 09:45 | 376305 (904.58) | -0.065 (-4.26) | -0.145 | -0.226 | +0.000 | +0.157 / -0.288 | -0.042 / -0.082 |
| random long | B1 09:50-10:30 | 377279 (906.92) | -0.070 (-4.52) | -0.151 | -0.231 | +0.000 | +0.164 / -0.289 | -0.049 / -0.088 |
| random short | 09:35 | 377177 (906.68) | -0.091 (-7.0) | -0.172 | -0.254 | +0.000 | -0.278 / +0.095 | -0.119 / -0.069 |
| random short | 09:40 | 376104 (904.1) | -0.085 (-5.89) | -0.166 | -0.247 | +0.000 | -0.290 / +0.131 | -0.111 / -0.063 |
| random short | 09:45 | 376305 (904.58) | -0.099 (-6.58) | -0.181 | -0.263 | +0.000 | -0.319 / +0.124 | -0.136 / -0.070 |
| random short | B1 09:50-10:30 | 377279 (906.92) | -0.093 (-5.98) | -0.174 | -0.256 | +0.000 | -0.324 / +0.126 | -0.128 / -0.064 |


### 4. Recommendation
Per setup (rule 0.7, corrected primary test): **keep window: RW6G1-ns2-up3-vwap2sd-short** (q 0.090; window beats the
full day in H1 +0.328 vs +0.034 and H2 +0.076 vs -0.046; H1 is out of sample for the window but not for the guard).
**Widen / window not supported: the other 29.** Read with these qualifiers:
- ST1, ST4 (and NS1): the secondary Wald test flags a time effect and the window wins in both halves, but both halves
  are in-sample for ST windows -> treat as **unclear**, decide on forward data.
- NS2 / RW6 lineage: the robust finding is "13:05-14:00 is bad", not "only 09:50-11:30" -> **unclear**; a re-window
  (e.g. 09:50-13:00 + 14:05-15:00) is a new lineage step for the backlog.
- heat_fade_short: the window is the only non-negative bucket, but the corrected test is not significant (p 0.30) and
  the window itself is +0.017R, t 0.7 -> widening does not help; the setup's problem is not the window.
- Losing setups (MF1-MF5, NS4, NS5, RW1-RW3, RW5, RW7, RW8, exhaustion, RW2, heat_fade_long): widening changes nothing
  material; full-day expectancy is also negative. Their rescore verdicts decide.

General policy proposal (backlog bdi-tod-policy-fullday-default): **a new setup is scored over the full 09:50-15:00 day
by default; a time window is allowed only when (1) the block-relabelling time test is a BH discovery across the
setups scored together, (2) the window chosen on one half beats the full day on the other half, and (3) the window
is counted as a search dimension in the lineage's configuration count.** Time cuts that exclude a specific bad
hour (supported in both halves and both regimes) are preferred over narrow "good" windows. 09:30-09:50 stays closed
until the open study in section 3 is repeated with quote-based costs and the warm-up fix; nothing simple is
tradeable there after costs today.

Files: tod_free.py (time layer removed in memory, modules untouched), build_open.py (opening frames + RW6G1 band
guard from the 1-minute cache), scan.py, analyze.py, open_study.py; results.csv (setup x trade set), tests.csv (per
setup tests), pooled.csv, baseline.csv, open_results.csv; large files in data/ (git-ignored parquet).
