# pod1022 - podcast / YouTube / educator setup mining (2026-10-22)

*Educational only - not financial advice.*

**Result: 0 setups accepted. Nothing was added to the Setup Generator account** (`config/account_gen.yaml`),
`config/setup_names.yaml`, `docs/live/setup_names.json`, `docs/live/assignments.json` or
`docs/live/generator_lab.json`. No live behaviour changes. The ledger gets one research entry recording the batch and its
counts (no config patch).

**Update 2026-10-23 (owner decision ~08:00 ET): 3 of the 8 positive-in-both ideas were added to the Setup Generator
account as OBSERVATION setups** (they did not pass the merit bar; nothing above is changed). See the addendum below.

## Counts
- Module files written: **464** (`modules/pod-*.py`, plus shared helpers `_*.py`). Each is a LabStrategy-format module;
  long/short halves, pre-declared second configs, exit-geometry twins and controls are separate files.
- Scored on the full open history: **452**. Not scored (full run did not finish in time; smoke tests only, all
  weak or zero-trade): 12 - bbt bottom-reversal hammer, bbt falling-wedge div, bbt late-day squeeze, cwt2 berry staircase,
  cwt2 cortes elephant bar, cwt2 glick beaten-down base, cwt2 kalayjian 30m div, cwt2 tagr peers leader, smb first green
  day, smb gap give-and-go, smb rubberband, wt ascending triangle. They are untested, not rejected on evidence.
- Verdicts of the 452 scored: **319 fail** (negative after costs in train and/or valid), **121 too few trades to judge**
  (< 100 pooled, or 0 trades), **12 positive in both periods but failed the other gates** (see below). **0 accepted.**
- Trades simulated: about 3.58 million (pooled train + valid), costs from `config/default.yaml` always in.
- Tiers: tier-A 0, tier-B 0.
- Side: 382 of 452 scored modules are long (85%). About 97 module files target quiet / choppy / balance / range / midday
  tape by name; long or quiet/choppy together: 399 of 464. The owner asked for long and quiet-choppy ideas; they were
  the bulk of the batch, and none passed.

## Method
1. Source mining (web): Chat With Traders (beyond eps already mined as CWT01-49), Better System Trader, Bear Bull
   Traders, Warrior Trading, SMB Capital, Alpha Trends (Shannon), Raschke, Unger, TraderLion/Qullamaggie, Axia, Trader
   Dante, Dalton/market profile, Brooks, Velez, Camarilla, Fisher ACD, Zarattini/Aziz papers, Quantified Strategies,
   QuantRocket (Gao et al.), Edgeful, calendar effects (opex, TOM, pre-holiday, FOMC, NFP, CPI), Williams, Crabel,
   Connors, Elder, Grimes, O'Neil, Kell, Hougaard, Steenbarger, Thrasher, Augen, Carter, Mancini, Bespoke.
   **Web access was partial**: WebSearch worked, but WebFetch/curl were refused for nearly every host, so rules were
   built from search-result summaries plus long-published book material. Thresholds not quoted by a source are our
   pre-declared translations to 5-minute bars, set before scoring.
2. Duplicate screen before coding against `research/backlog.jsonl`, the CWT catalog, the video/Reddit/articles
   families, `setups_research.json`, `config/setup_names.yaml` and the GEN names. Copies dropped before coding:
   Raschke Holy Grail (plain), Turtle Soup / liquidity sweeps, 80-20, NR7-ORB, Crabel stretch (plain), noise band, gap
   fill, VWAP reclaim/fade, AVWAP pinch, Ross micro-pullback, volume top, gap-and-go, red-to-green, bull flag (plain),
   HOD break, classic 5/15/20/30-min ORB, VWAP false breakout short, EMA9/20 ride, first VWAP pullback, BBT bottom
   reversal, Zarattini-Aziz SPY noise band and VWAP-trend ETF, SMB VWAP flip / Offsides / HitchHiker / Opening Drive /
   Second-Day breakout / gap fill / RubberBand (R03), Breitstein capitulation (CWT05), Larry Williams Oops (CWT43 - later
   scored in ETF/red-day variants), Heston-Korajczyk-Sadka same half-hour, Bensdorp six-day surge, first-to-last
   half-hour momentum (live intraday_momentum), Part Time Larry ORB/TTM squeeze, Quantified Strategies RSI(2)/IBS.
   Every kept idea names its parent and the stated change in its docstring.
3. Scoring with `score_batch.py` (see `HARNESS.md`): open history 2024-10..2026-10 split train / valid, the rule-19
   locked block 2024-11-01..2025-02-28 never read, costs in, earnings blackout, same-minute random-entry control
   ("excess"), regime split (regime labels are hindsight and never used as filters), duplicate overlap vs the batch and
   (for later rounds) every `type: lab` config setup via `--ref-config`. At most one declared tweak per idea; every
   tweak is stated in the module docstring and in the table below.
4. Selection: an idea had to be positive after costs in train and valid, significant, with enough trades, not carried by
   one day, not a duplicate (overlap < 0.60). None qualified.

## Failures first: why nothing passed
- **Most ideas lose after costs in both periods** (319). Typical: -0.05 to -0.25R. Tight structural stops (trigger-bar,
  CE line, sweep low, 0.1 ATR ORB stop) make R small, so costs alone take 0.2-0.7R per trade (TD Sequential, Augen spike,
  VSA, Dante poor-low sweep, Cady balance break, Zarattini SIP ORB).
- **Market-direction proxies**: many "work" only on Bull days (longs) or Bear days (shorts) - a hindsight label. Examples:
  Nesnidal POI breakout, Raschke trend-day last hour, Fashionably Late, Edgeful green open, STC hook, Davey 3-down.
- **Rare-rule stacks**: many source rule sets almost never fire on liquid names in 5-minute frames (0-20 trades in 21
  months): Breitstein ETF capitulation, BBT extreme reversal X, parabolic capitulation long, Morad impulse flag, SMB LOD
  coil, single-print defense, Shannon WTD/MTD AVWAP, Redler 8/21 weak hour, HYG non-confirmation (HYG not in the data).
- **Positive but not credible (12 rows)**:
  - WT bull flag "breakout or bailout" and its pullback-count gates (a1/a2/a3): train +0.08..+0.11R, valid +0.11..+0.21R,
    t 3-5, but 555 of 796 trades are on 2025-04-09 (best-day share 0.73), valid is about 40 trades, and overlap 0.61
    with pod-smb-second-chance-hod-retest - dup flag set. Without 2025-04 the plain-exit version is 220 trades at +0.21R;
    worth a later look only as a backlog item with a cap on same-day clustering.
  - Thrasher breadth thrust on stocks (+0.10 / +0.29R, t 1.27, n 2114) and breadth thrust on index ETFs (+0.06 / +0.40R,
    t 0.95, n 168, one day = 37% of R; excess 0 by construction): not significant.
  - Raschke ADX gapper short (+0.06 / +0.00R, n 155, one day 77% of R), SMB 20-day-high time acceptance (best day 126%
    of R), Gogolak 1000-bar SMA dip (n 127, best day 59%), Aziz VWAP reversal (t 0.67, best day 45%), Aziz-Zarattini index
    first-candle ORB (n 167, t 0.52): too thin / concentrated.
  - Too few trades but eye-catching (not evidence): SMB 2-day AVWAP first touch quiet (14 trades, +1.08R pooled, best day
    90%), Dalton open-drive config D long (+0.41 / +0.40R, but tiny n under a 0.375 ATR stop cap), Hill IWM leads reversal
    on IWM (12 trades), OA narrow first-hour PM break (28 trades), Chop and Pop (23 trades), Colkitt LETF close +1.5% (29).
- **Harness additions** (pod-local, documented in HARNESS.md): GEOM `S+ts2` (bailout + break-even), `S+bar1`
  (one-bar trail), `S+x` (module-defined exit / time stop). Several sources' exits (EMA trails, 45-60 min time stops
  before these were added, 15:05-15:30 entries) could not be modelled; each such module says so.

## Context columns / live feasibility
Not applicable this round: nothing was added. Several ideas used data the live engine lacks (daily ADX/DI, SMA200 on
daily bars, prior-session 5m bars, 1-minute volume curves, VIX/VXX/UVXY, HYG, SPY VWAP as a context column, 30/60-minute
bars). Any future promotion of these would need those columns live first.

## Indicator notes (what these sources rate most useful)
- **VWAP and anchored VWAP** are the most-cited tools (Shannon, SMB, BBT, Aziz): session VWAP as the trend side and
  reversal target; AVWAPs from the day's high/low, gap, prior close, week/month/quarter/year start. Shannon: price above a
  rising AVWAP is "innocent until proven guilty". Tested here as reclaim, hand-off, 2-day and 5-day VWAP pullbacks,
  HOD/LOD AVWAP: none positive after costs.
- **EMA9/EMA20 on 1-5 min** (Ross Cameron, BBT, SMB, Brooks, Raschke): pullback location and trailing exits.
- **Prior-day high/low/close and day-type references** (Raschke, Dalton, Camarilla, Fisher ACD pivots, Trader Dante):
  first-hour range / initial balance, open type, value area, poor highs/lows.
- **Daily trend gates**: ADX(14) > 30 with DI (Raschke), 5-day SMA and its slope (Shannon), SMA20/50/200, stage analysis.
- **Short oscillators**: LBR 3/10 (16 signal), Stoch 7/10 hook (the Anti), RSI(3) of ROC (Momentum Pinball); RSI only as
  an extreme filter (Aziz RSI < 10 / > 90).
- **Relative volume / in-play**: RVOL vs same-time 14-20 day average, opening-range volume rank (Zarattini top 20),
  SMB IPR; climax volume >= 2x after 3 large bars (BBT parabolic); low-volume counter-moves (SMB, VSA).
- **Daily ATR** to normalise all distances, stops and targets (BBT ORB target 80-100% of ATR; Zarattini 10% ATR stop).
- **Market context**: breadth (stand-in for NYSE TICK), SPY/QQQ from-open, VIX level / change (Gao et al. last half-hour).
- **Time of day**: first 30 min = price discovery (Bellafiore); "best reversals in the morning, last hour tells the truth"
  (Raschke); Unger uses patterns as filters on a breakout core, not as entries.
- **Evidence quality warning**: BBT decks report low hit rates; an independent replication of the Zarattini-Aziz ORB
  found net-of-cost returns about zero; Warrior Trading settled with the FTC over misleading claims (2022). This batch is
  consistent with that: popular retail setups, mechanised and costed, do not beat the random-entry control.

## Full results (452 scored modules, worst pooled avgR first)
avgR is per trade after costs; excess = avgR minus the same-minute random-entry control. Scorer outputs were
`r*.jsonl` in the session scratchpad (not kept); per-module notes are in each module docstring.

| # | module | side | n train / valid | avgR train | avgR valid | t pooled | excess valid | verdict | file |
|---|---|---|---|---|---|---|---|---|---|
| 1 | pod-cwt-breitstein-etf-capitulation-rightV | long | 0 / 0 |  |  |  |  | too few | r0_1.jsonl |
| 2 | pod-cwt-breitstein-etf-capitulation-rightV-3x | long | 0 / 0 |  |  |  |  | too few | r0_1.jsonl |
| 3 | pod-cwt-breitstein-etf-capitulation-rightV-holdtr | long | 0 / 0 |  |  |  |  | too few | r0_1.jsonl |
| 4 | pod-cwt-breitstein-stock-multiday-flush-B | long | 0 / 0 |  |  |  |  | too few | r0_1.jsonl |
| 5 | pod-bbt-extreme-rev-mtf-long | long | 0 / 0 |  |  |  |  | too few | r0_2.jsonl |
| 6 | pod-cwt3-morad-impulse-flag-retest-long | long | 0 / 0 |  |  |  |  | too few | r2_0.jsonl |
| 7 | pod-of3-single-print-zone-pm-defense-long | long | 0 / 0 |  |  |  |  | too few | r2_11.jsonl |
| 8 | pod-bbt-parabolic-ema9-capitulation-daily-level-long | long | 0 / 0 |  |  |  |  | too few | r2_2.jsonl |
| 9 | pod-smb-lod-coil-after-down-drive-reversal-long | long | 0 / 0 |  |  |  |  | too few | r2_4.jsonl |
| 10 | pod-williams-smash-day-pdh-long-hidden | long | 0 / 0 |  |  |  |  | too few | r2_5.jsonl |
| 11 | pod-shannon-wtd-avwap-reclaim-mtd-hold-etf-long | long | 0 / 0 |  |  |  |  | too few | r2_6.jsonl |
| 12 | pod-hyg-nonconfirm-spy-newlow-long | long | 0 / 0 |  |  |  |  | too few | r3_11.jsonl |
| 13 | pod-redler-821-trend-weak-hour-dip-long | long | 0 / 0 |  |  |  |  | too few | r3_12.jsonl |
| 14 | pod-cwt2-levy-index-confluence-level-long | long | 2 / 1 | -1.064 | -1.117 | -65.392 | -1.348 | too few | r1_0.jsonl |
| 15 | pod-nfp-weak-open-recovery-long | long | 0 / 3 |  | -1.080 |  | +0.010 | too few | r3_12.jsonl |
| 16 | pod-bst018-andrews-etf-follow-beyond-long | long | 17 / 12 | -0.866 | -1.372 | -2.127 | -0.589 | too few | r0_0.jsonl |
| 17 | pod-smb-quiet-tape-level-fade-short | short | 3 / 5 | -1.690 | -0.631 | -2.347 | -0.676 | too few | r0_3_qt.jsonl |
| 18 | pod-bst018-andrews-etf-follow-beyond-short | short | 21 / 19 | -0.977 | -0.894 | -3.820 | -0.416 | too few | r0_0.jsonl |
| 19 | pod-bbt-extreme-rev-daily-level-engulf-short | short | 29 / 6 | -0.820 | -1.216 | -8.559 | -1.037 | too few | r0_3.jsonl |
| 20 | pod-cal-monthend-rebalance-contra-index-long | long | 0 / 4 |  | -0.855 |  | +0.000 | too few | r1_5.jsonl |
| 21 | pod-cwt3-cady-balance-ma-converge-break-long | long | 1633 / 1147 | -0.785 | -0.870 | -7.914 | -0.768 | fail | r2_0.jsonl |
| 22 | pod-bst018-andrews-etf-follow-beyond-sectors-short | short | 54 / 54 | -0.822 | -0.741 | -4.252 | -0.203 | fail | r0_0.jsonl |
| 23 | pod-bst018-andrews-etf-follow-beyond-sectors-long | long | 32 / 39 | -0.467 | -0.989 | -1.776 | -0.592 | too few | r0_0.jsonl |
| 24 | pod-dante-poor-low-double-touch-sweep-quiet-long | long | 474 / 419 | -0.672 | -0.730 | -12.613 | -0.612 | fail | r1_10.jsonl |
| 25 | pod-of3-dalton-neutral-day-center-revert | long | 0 / 2 |  | -0.695 | -2.778 | -0.462 | too few | r2_10.jsonl |
| 26 | pod-cal-monthend-rebalance-contra-index-short | short | 0 / 8 |  | -0.660 | -2.133 | -0.019 | too few | r1_5.jsonl |
| 27 | pod-r3-td-seq-buy9-perfected-pflip-long | long | 26254 / 27513 | -0.663 | -0.637 | -8.769 | -0.521 | fail | r2_8.jsonl |
| 28 | pod-smb-lt-support-first-test-hold-long | long | 7 / 6 | -1.082 | +0.022 | -2.194 | -0.059 | too few | r2_4.jsonl |
| 29 | pod-iwm-spy-spread-z-choppy-revert-long | long | 43 / 38 | -0.646 | -0.453 | -3.807 | -0.260 | too few | r3_12.jsonl |
| 30 | pod-gao-newsday-first30-hold-long | long | 9 / 1 | -0.466 | -1.109 | -2.008 | +0.032 | too few | r2_12.jsonl |
| 31 | pod-bbt-lightning-bolt-vwap-cross-continuation-long | long | 375 / 96 | -0.620 | -0.147 | -3.492 | -0.070 | fail | r2_1.jsonl |
| 32 | pod-of3-dalton-rf-balance-lowerhalf-long | long | 4 / 0 | -0.515 |  | -0.985 |  | too few | r2_9.jsonl |
| 33 | pod-augen-spike-downshock-upday-long | long | 2800 / 2739 | -0.534 | -0.487 | -14.211 | -0.312 | fail | r3_11.jsonl |
| 34 | pod-dante-poor-high-magnet-trend-long | long | 3764 / 3134 | -0.593 | -0.410 | -6.699 | -0.304 | fail | r1_10.jsonl |
| 35 | pod-trush-chandelier-zlsma-flip-long | long | 42991 / 33414 | -0.396 | -0.657 | -5.620 | -0.530 | fail | r3_8.jsonl |
| 36 | pod-vsa-stopping-volume-no-supply-test-long | long | 543 / 489 | -0.561 | -0.452 | -10.782 | -0.328 | fail | r1_9.jsonl |
| 37 | pod-qs-turnaround-tuesday-intraday-long-hold | long | 14 / 2 | -0.531 | -0.356 | -2.066 | +0.374 | too few | r1_8.jsonl |
| 38 | pod-charm-preopex-week-pm-vwap-hold-index-long | long | 4 / 6 | -0.508 | -0.502 | -1.512 | -0.183 | too few | r3_11.jsonl |
| 39 | pod-trush-chandelier-zlsma-flip-long-flip | long | 42991 / 33414 | -0.393 | -0.640 | -5.686 | -0.513 | fail | r3_8.jsonl |
| 40 | pod-trush-chandelier-zlsma-flip-long-bar1 | long | 42991 / 33414 | -0.431 | -0.582 | -7.600 | -0.455 | fail | r3_8.jsonl |
| 41 | pod-bbt-parabolic-ema9-snapback-short | short | 6 / 2 | -0.239 | -1.177 | -1.025 | -0.906 | too few | r0_2.jsonl |
| 42 | pod-smb-day3-extended-belowvwap-coil-break-short | short | 6 / 6 | -0.849 | -0.079 | -1.415 | +0.137 | too few | r2_3.jsonl |
| 43 | pod-of4-iceberg-floor-hivol-touches-long | long | 423 / 202 | -0.413 | -0.430 | -8.922 | -0.309 | fail | r3_10.jsonl |
| 44 | pod-smb-not-in-play-quiet-vwap-snap-long | long | 1284 / 1356 | -0.469 | -0.362 | -6.612 | -0.214 | fail | r0_4.jsonl |
| 45 | pod-of-second-test-hod-break | long | 3650 / 2343 | -0.472 | -0.320 | -17.127 | -0.233 | fail | r0_12.jsonl |
| 46 | pod-bbt-inverse-hs-below-vwap-long | long | 8 / 3 | -0.365 | -0.515 | -1.435 | -0.439 | too few | r1_2.jsonl |
| 47 | pod-of4-valentini-imbalance-lvn-pullback-long | long | 6059 / 4723 | -0.423 | -0.363 | -19.182 | -0.211 | fail | r3_10.jsonl |
| 48 | pod-gao-newsday-first30-hold-long-ctrl-nonrelease | long | 19 / 14 | -0.462 | -0.304 | -2.594 | +0.064 | too few | r2_12.jsonl |
| 49 | pod-smh-leads-qqq-nonconfirm-long-ctrl | long | 243 / 220 | -0.774 | +0.060 | -1.214 | +0.063 | fail | r3_8.jsonl |
| 50 | pod-charm-preopex-week-pm-vwap-hold-index-long-ctrl-nonopex | long | 41 / 17 | -0.522 | -0.026 | -2.706 | +0.031 | too few | r3_11.jsonl |
| 51 | pod-bbt-lightning-bolt-vwap-cross-continuation-long-allday | long | 618 / 218 | -0.452 | -0.163 | -2.647 | -0.032 | fail | r2_1.jsonl |
| 52 | pod-r3-connorsrsi-5m-trendday-dip-long | long | 13614 / 9334 | -0.381 | -0.363 | -12.901 | -0.258 | fail | r2_8.jsonl |
| 53 | pod-bbt-mountain-pass-failed-2nd-low-sma50-long | long | 8 / 4 | -0.584 | +0.067 | -1.226 | +0.353 | too few | r2_1.jsonl |
| 54 | pod-r3-ou-halflife-zscore-quiet-long | long | 15833 / 16665 | -0.339 | -0.379 | -14.114 | -0.216 | fail | r2_8.jsonl |
| 55 | pod-of-dante-insideday-fail-pm-short | short | 553 / 297 | -0.496 | -0.096 | -4.694 | +0.001 | fail | r0_10.jsonl |
| 56 | pod-cwt-raschke-whiplash-intraday-D2 | long | 41 / 48 | -0.559 | -0.173 | -1.816 | +0.009 | too few | r0_1.jsonl |
| 57 | pod-raschke-first-pullback-after-20d-high-long | long | 25 / 24 | -0.474 | -0.182 | -1.948 | -0.128 | too few | r2_7.jsonl |
| 58 | pod-oa-wide-first-hour-continuation-short | short | 31 / 53 | -0.221 | -0.391 | -2.011 | +0.115 | too few | r0_12.jsonl |
| 59 | pod-cwt3-breitstein-oversold-largecap-open-print-long | long | 8 / 25 | -0.236 | -0.354 | -1.940 | -0.238 | too few | r2_1.jsonl |
| 60 | pod-quantpy-variance-ratio-chop-fade-long | long | 1460 / 2621 | -0.372 | -0.296 | -7.594 | -0.163 | fail | r1_9.jsonl |
| 61 | pod-of-quiet-midday-range-fail-L-long | long | 3826 / 3242 | -0.329 | -0.306 | -7.878 | -0.240 | fail | r0_11.jsonl |
| 62 | pod-of-quiet-midday-range-fail-L-short | short | 3195 / 2917 | -0.397 | -0.214 | -8.924 | -0.186 | fail | r0_11.jsonl |
| 63 | pod-smb-day3-extended-belowvwap-coil-pm-reclaim-long | long | 4 / 4 | -0.025 | -0.591 | -1.592 | -0.346 | too few | r2_3.jsonl |
| 64 | pod-velez-narrow-state-break-long | long | 7430 / 4293 | -0.296 | -0.324 | -9.274 | -0.205 | fail | r0_9.jsonl |
| 65 | pod-qs-turnaround-tuesday-intraday-long | long | 14 / 2 | -0.278 | -0.462 | -1.261 | +0.267 | too few | r1_8.jsonl |
| 66 | pod-quantpy-variance-ratio-chop-fade-vr050-long | long | 830 / 1508 | -0.296 | -0.300 | -6.131 | -0.166 | fail | r1_9.jsonl |
| 67 | pod-baltussen-tlt-flight-to-quality-close-long-t025 | long | 8 / 6 | -0.206 | -0.416 | -1.444 | -0.270 | too few | r3_8.jsonl |
| 68 | pod-baltussen-tlt-flight-to-quality-close-long | long | 8 / 6 | -0.206 | -0.416 | -1.444 | -0.270 | too few | r3_8.jsonl |
| 69 | pod-zarattini-aziz-sip-top20-rvol-30m-orb-atrstop-eod-long | long | 735 / 669 | -0.243 | -0.351 | -2.892 | -0.189 | fail | r3_1.jsonl |
| 70 | pod-qs-tlt-monthend-intraday-long-ctrl-mid | long | 48 / 53 | -0.180 | -0.397 | -2.317 | +0.125 | fail | r3_8.jsonl |
| 71 | pod-smb-bouncy-ball-support-break | short | 129 / 68 | -0.342 | -0.183 | -2.167 | -0.063 | fail | r0_4.jsonl |
| 72 | pod-tosind-lunch-compression-index-break-long | long | 20 / 20 | -0.463 | -0.102 | -1.649 | -0.235 | too few | r0_13.jsonl |
| 73 | pod-cwt4-raschke-failed-inside-bar-breakdown-long | long | 4787 / 4095 | -0.272 | -0.279 | -19.768 | -0.148 | fail | r3_0.jsonl |
| 74 | pod-zarattini-noise-lower-fail-quiet-long-ctrl-nonquiet | long | 30 / 58 | -0.071 | -0.370 | -2.305 | -0.005 | too few | r3_9.jsonl |
| 75 | pod-velez-narrow-state-break-short | short | 7240 / 4194 | -0.324 | -0.164 | -7.169 | -0.122 | fail | r0_9.jsonl |
| 76 | pod-cal-turnaround-tuesday-index-reclaim-long | long | 35 / 16 | -0.392 | +0.020 | -0.793 | -0.043 | too few | r1_6.jsonl |
| 77 | pod-williams-willspread-spy-tlt-cross-long-ctrl-spyonly | long | 135 / 100 | -0.349 | -0.144 | -2.597 | +0.101 | fail | r3_11.jsonl |
| 78 | pod-tl-rvol-at-time-flat-stock-quiet-tape-ignition-long | long | 666 / 340 | -0.330 | -0.118 | -4.032 | +0.008 | fail | r2_7.jsonl |
| 79 | pod-of4-trapped-hivol-breakdown-barhigh-reclaim-long | long | 13601 / 12127 | -0.288 | -0.225 | -11.278 | -0.113 | fail | r3_10.jsonl |
| 80 | pod-of-defended-origin-retest-g025-long | long | 17 / 20 | -0.432 | -0.104 | -1.146 | -0.032 | too few | r0_11.jsonl |
| 81 | pod-of-quiet-midday-range-fail-M-long | long | 1660 / 1431 | -0.255 | -0.252 | -7.253 | -0.101 | fail | r0_11.jsonl |
| 82 | pod-of3-dalton-rf-divergence-newlow-pm-long | long | 611 / 519 | -0.234 | -0.273 | -4.730 | -0.132 | fail | r2_9.jsonl |
| 83 | pod-wt-gap-full-fill-pdc-hold-long | long | 50 / 82 | -0.287 | -0.230 | -1.731 | -0.159 | fail | r1_2.jsonl |
| 84 | pod-unger-first-hour-2nd-hour-break-B-long | long | 1824 / 1232 | -0.248 | -0.254 | -6.109 | -0.090 | fail | r0_0.jsonl |
| 85 | pod-qs-30m-lower-lows-etf-long-holdtr | long | 149 / 182 | -0.347 | -0.164 | -3.054 | +0.032 | fail | r0_10.jsonl |
| 86 | pod-of4-vsa-absorb-then-ease-long | long | 421 / 301 | -0.224 | -0.276 | -5.743 | -0.189 | fail | r3_9.jsonl |
| 87 | pod-qs-tlt-monthend-intraday-long | long | 31 / 23 | -0.045 | -0.513 | -1.369 | -0.078 | too few | r3_8.jsonl |
| 88 | pod-shannon-pc-loss-retest-short | short | 6676 / 6619 | -0.263 | -0.222 | -13.441 | -0.106 | fail | r1_8.jsonl |
| 89 | pod-bbt-booty-reversal-pm-15m-consolidation-long | long | 2634 / 2846 | -0.253 | -0.230 | -7.778 | -0.093 | fail | r2_2.jsonl |
| 90 | pod-of4-wyckoff-spring-lowvol-test-long | long | 34747 / 32478 | -0.230 | -0.248 | -18.449 | -0.130 | fail | r3_9.jsonl |
| 91 | pod-axia-spy-newlow-divergence-long | long | 5996 / 2737 | -0.192 | -0.337 | -2.834 | -0.081 | fail | r1_10.jsonl |
| 92 | pod-brooks-h2-second-entry-long | long | 7898 / 7652 | -0.272 | -0.198 | -10.963 | -0.095 | fail | r0_9.jsonl |
| 93 | pod-cal-preholiday-index-vwap-long | long | 45 / 72 | -0.263 | -0.215 | -1.224 | -0.083 | fail | r1_5.jsonl |
| 94 | pod-bbt-ma-trend-vwap-held-ema20-pullback-trail-long | long | 1023 / 905 | -0.271 | -0.187 | -3.871 | -0.067 | fail | r3_1.jsonl |
| 95 | pod-brooks-range-day-edge-fade-RT-long | long | 3593 / 4142 | -0.216 | -0.241 | -7.476 | -0.087 | fail | r0_10.jsonl |
| 96 | pod-qs-30m-lower-lows-etf-long | long | 149 / 182 | -0.271 | -0.194 | -2.167 | +0.028 | fail | r0_10.jsonl |
| 97 | pod-raschke-310-first-cross-long | long | 39519 / 32963 | -0.233 | -0.221 | -16.994 | -0.096 | fail | r0_7.jsonl |
| 98 | pod-smb-changing-fundamentals-hold-short-holdtr | short | 1277 / 1094 | -0.149 | -0.320 | -2.337 | -0.160 | fail | r0_4.jsonl |
| 99 | pod-of4-valentini-2nd-failed-ib-probe-poc-long | long | 1376 / 1249 | -0.201 | -0.253 | -6.487 | -0.148 | fail | r3_9.jsonl |
| 100 | pod-unger-daydrop-vwap-reclaim-etf | long | 153 / 124 | -0.262 | -0.180 | -2.671 | +0.010 | fail | r0_7.jsonl |
| 101 | pod-of-dante-insideday-fail-pm-long | long | 447 / 327 | -0.218 | -0.233 | -3.686 | -0.144 | fail | r0_10.jsonl |
| 102 | pod-of-absorption-bar-level-long | long | 222 / 192 | -0.256 | -0.188 | -3.388 | -0.067 | fail | r0_11.jsonl |
| 103 | pod-r3-elder-ray-bearpower-hook-long | long | 60075 / 46988 | -0.235 | -0.206 | -6.468 | -0.102 | fail | r2_8.jsonl |
| 104 | pod-fisher-pivot-range-pullback-long | long | 1405 / 1421 | -0.198 | -0.240 | -5.409 | -0.099 | fail | r1_11.jsonl |
| 105 | pod-brooks-range-day-edge-fade-BR-short | short | 3964 / 2464 | -0.276 | -0.126 | -7.401 | -0.104 | fail | r0_10.jsonl |
| 106 | pod-hart-serafini-midday-range-edge-fade-short | short | 253 / 154 | -0.258 | -0.148 | -4.172 | -0.048 | fail | r0_6.jsonl |
| 107 | pod-brooks-range-day-edge-fade-BR-long | long | 3268 / 2658 | -0.203 | -0.227 | -7.172 | -0.103 | fail | r0_10.jsonl |
| 108 | pod-hart-serafini-midday-range-edge-fade-long | long | 234 / 170 | -0.314 | -0.076 | -3.101 | +0.017 | fail | r0_6.jsonl |
| 109 | pod-cwt3-chan-bb-volfloor-quiet-etf-long | long | 335 / 328 | -0.185 | -0.238 | -3.631 | +0.004 | fail | r2_0.jsonl |
| 110 | pod-raschke-310-first-cross-short | short | 39294 / 33972 | -0.236 | -0.176 | -13.430 | -0.111 | fail | r0_7.jsonl |
| 111 | pod-speck-quiet-day-closing-drift | long | 121 / 57 | -0.258 | -0.104 | -2.547 | -0.024 | fail | r0_6.jsonl |
| 112 | pod-chan-buy-on-gap-etf-idio | long | 1 / 1 | -1.039 | +0.627 | -0.350 | +1.447 | too few | r0_6.jsonl |
| 113 | pod-dalton-open-drive-pullback-D-short | short | 8 / 10 | +0.006 | -0.372 | -0.651 | -0.217 | too few | r0_9.jsonl |
| 114 | pod-of-lowerwick-cluster-quiet-lod-long | long | 188 / 285 | -0.206 | -0.203 | -4.084 | -0.006 | fail | r1_9.jsonl |
| 115 | pod-cwt3-chan-bb-volfloor-quiet-etf-long-nofloor | long | 557 / 511 | -0.147 | -0.264 | -4.724 | -0.017 | fail | r2_0.jsonl |
| 116 | pod-brooks-h2-second-entry-short | short | 7341 / 6773 | -0.201 | -0.203 | -6.638 | -0.106 | fail | r0_9.jsonl |
| 117 | pod-of4-intraday-ad-divergence-newlow-long | long | 8385 / 7776 | -0.163 | -0.244 | -9.376 | -0.087 | fail | r3_10.jsonl |
| 118 | pod-of4-absorption-box-lower-third-long | long | 73 / 126 | -0.130 | -0.240 | -3.062 | -0.096 | fail | r3_9.jsonl |
| 119 | pod-velez-bull180-at-support-short | short | 5297 / 4155 | -0.201 | -0.194 | -9.353 | -0.100 | fail | r0_10.jsonl |
| 120 | pod-chop-gate-vwapcross-inner-band-long | long | 626 / 433 | -0.141 | -0.278 | -3.802 | -0.181 | fail | r2_12.jsonl |
| 121 | pod-bbt-vwap-false-breakdown-long | long | 14864 / 11021 | -0.179 | -0.221 | -8.908 | -0.099 | fail | r0_3.jsonl |
| 122 | pod-williams-willspread-spy-tlt-cross-long | long | 119 / 83 | -0.183 | -0.213 | -1.810 | -0.124 | fail | r3_11.jsonl |
| 123 | pod-fisher-failed-adown-cup-long | long | 1622 / 1276 | -0.191 | -0.201 | -3.043 | -0.065 | fail | r1_11.jsonl |
| 124 | pod-raschke-anti-stoch-hook-long | long | 11063 / 9302 | -0.194 | -0.189 | -17.628 | -0.062 | fail | r0_6.jsonl |
| 125 | pod-of-quiet-midday-range-fail-M-short | short | 1444 / 1355 | -0.233 | -0.145 | -5.641 | -0.131 | fail | r0_11.jsonl |
| 126 | pod-three-push-deceleration-low-long | long | 396 / 397 | -0.172 | -0.209 | -3.195 | -0.097 | fail | r1_9.jsonl |
| 127 | pod-brooks-range-day-edge-fade-RT-short | short | 4191 / 3905 | -0.275 | -0.095 | -5.841 | -0.066 | fail | r0_10.jsonl |
| 128 | pod-shannon-hod-avwap-reclaim-long | long | 676 / 278 | -0.167 | -0.234 | -2.546 | -0.166 | fail | r0_1.jsonl |
| 129 | pod-cpr-wide-range-day-pivot-fade-short | short | 4530 / 4082 | -0.231 | -0.134 | -7.867 | -0.049 | fail | r0_13.jsonl |
| 130 | pod-raschke-5sma-7bar-downrun-quiet-snap-long | long | 1709 / 1781 | -0.223 | -0.147 | -5.540 | -0.046 | fail | r3_6.jsonl |
| 131 | pod-cwt3-colkitt-letf-rebalance-close-long-short | short | 36 / 28 | -0.306 | -0.027 | -0.896 | -0.121 | too few | r2_0.jsonl |
| 132 | pod-cwt-morad-day5-pdl-zone-long | long | 2294 / 2237 | -0.188 | -0.178 | -4.030 | -0.067 | fail | r1_5.jsonl |
| 133 | pod-smb-daily-uptrend-sma20-intraday-touch-long | long | 3607 / 3330 | -0.199 | -0.166 | -6.762 | -0.046 | fail | r1_4.jsonl |
| 134 | pod-raschke-trendday-d2-prior-close-hold-long | long | 1229 / 986 | -0.230 | -0.121 | -4.297 | -0.002 | fail | r1_6.jsonl |
| 135 | pod-qs-lowvol-day-gapup-etf-open-hold-long-g075 | long | 10 / 7 | -0.393 | +0.122 | -0.639 | -0.316 | too few | r3_7.jsonl |
| 136 | pod-wt-abcd-buy-at-c-dtarget-long | long | 123 / 160 | -0.417 | +0.002 | -1.198 | +0.047 | fail | r0_2.jsonl |
| 137 | pod-smb-gapdown-opening-print-reclaim-B-long | long | 76 / 56 | -0.310 | -0.004 | -1.572 | +0.057 | fail | r1_4.jsonl |
| 138 | pod-tosind-lunch-compression-index-break-short | short | 18 / 17 | -0.161 | -0.199 | -0.833 | -0.331 | too few | r0_13.jsonl |
| 139 | pod-raschke-anti-stoch-hook-short | short | 11244 / 9365 | -0.188 | -0.168 | -15.318 | -0.091 | fail | r0_6.jsonl |
| 140 | pod-wt-cup-handle-midday-long | long | 247 / 174 | -0.281 | -0.032 | -2.422 | +0.082 | fail | r1_2.jsonl |
| 141 | pod-velez-bull180-at-support-long | long | 6107 / 3996 | -0.162 | -0.197 | -8.905 | -0.055 | fail | r0_10.jsonl |
| 142 | pod-wt-abcd-sell-at-c-short | short | 189 / 191 | -0.214 | -0.138 | -2.111 | -0.068 | fail | r0_2.jsonl |
| 143 | pod-inside-open-pdh-magnet-IO-etf-long | long | 328 / 224 | -0.159 | -0.200 | -2.484 | +0.022 | fail | r0_10.jsonl |
| 144 | pod-raschke-scalpbox-macd-zero-ema20-pullback-long | long | 123865 / 104642 | -0.159 | -0.195 | -10.440 | -0.072 | fail | r3_6.jsonl |
| 145 | pod-brooks-wedge-bottom-long | long | 3779 / 4020 | -0.176 | -0.173 | -5.924 | -0.062 | fail | r1_11.jsonl |
| 146 | pod-cwt3-raschke-day3-after-two-hilo-days-long | long | 1037 / 1444 | -0.152 | -0.191 | -4.402 | -0.044 | fail | r2_0.jsonl |
| 147 | pod-of-absorption-bar-level-short | short | 295 / 262 | -0.122 | -0.234 | -3.184 | -0.175 | fail | r0_11.jsonl |
| 148 | pod-smb-fashionably-late-short | short | 6125 / 7485 | -0.221 | -0.133 | -3.462 | -0.042 | fail | r0_3.jsonl |
| 149 | pod-elder-triple-screen-fi2-dip-long | long | 34627 / 30397 | -0.194 | -0.147 | -11.788 | -0.048 | fail | r3_11.jsonl |
| 150 | pod-cwt3-fabrio-commodity-etf-underreact-gap-long | long | 13 / 13 | +0.200 | -0.537 | -0.813 | -0.470 | too few | r2_1.jsonl |
| 151 | pod-cwt-mcdermitt-rs-hold-at-index-newlow-long-holdtr | long | 14005 / 16513 | -0.227 | -0.118 | -5.062 | -0.041 | fail | r1_5.jsonl |
| 152 | pod-bbt-orb-vwap-pullback-atr-room-long | long | 3401 / 3963 | -0.206 | -0.130 | -2.951 | -0.061 | fail | r0_2.jsonl |
| 153 | pod-raschke-scalpbox-macd-zero-ema20-pullback-short | short | 117746 / 103373 | -0.180 | -0.144 | -8.350 | -0.072 | fail | r3_6.jsonl |
| 154 | pod-baltussen-tlt-flight-to-quality-close-long-short | short | 6 / 0 | -0.162 |  | -0.551 |  | too few | r3_8.jsonl |
| 155 | pod-cwt4-raschke-sma5-7bar-streak-first-cross-long | long | 1492 / 1426 | -0.183 | -0.139 | -5.378 | -0.004 | fail | r3_1.jsonl |
| 156 | pod-raschke-holygrail-adx-ema20-long | long | 14471 / 10824 | -0.164 | -0.155 | -9.010 | -0.028 | fail | r0_6.jsonl |
| 157 | pod-unger-daydrop-orb-long | long | 1874 / 1765 | -0.177 | -0.141 | -4.211 | +0.006 | fail | r0_5.jsonl |
| 158 | pod-chop-etf-oversold-vwap-magnet-long | long | 249 / 360 | -0.206 | -0.128 | -3.484 | +0.073 | fail | r1_6.jsonl |
| 159 | pod-wt-gapup-open-shakeout-orh-reclaim-long | long | 86 / 79 | -0.066 | -0.258 | -1.786 | -0.233 | fail | r3_2.jsonl |
| 160 | pod-r3-taylor-buy-day-pdl-test-long | long | 3581 / 2966 | -0.136 | -0.181 | -6.817 | -0.019 | fail | r2_7.jsonl |
| 161 | pod-dalton-open-drive-pullback-OF-short | short | 161 / 147 | -0.211 | -0.096 | -2.358 | +0.134 | fail | r0_9.jsonl |
| 162 | pod-cwt2-mcdermitt-5m-flip-hourly-hl-long | long | 35294 / 30121 | -0.153 | -0.157 | -10.115 | -0.037 | fail | r1_0.jsonl |
| 163 | pod-smb-changing-fundamentals-hold-short | short | 1277 / 1094 | -0.092 | -0.225 | -1.261 | -0.075 | fail | r0_4.jsonl |
| 164 | pod-smb-strong-today-rank-quiet-pm-long | long | 18 / 12 | -0.194 | -0.091 | -1.530 | +0.058 | too few | r2_4.jsonl |
| 165 | pod-smb-trend-trend-pm-consolidation-hold-holdtr | long | 5010 / 4641 | -0.203 | -0.097 | -6.501 | +0.027 | fail | r0_5.jsonl |
| 166 | pod-baltussen-tlt-flight-to-quality-close-long-t060 | long | 7 / 3 | -0.328 | +0.258 | -0.694 | +0.334 | too few | r3_8.jsonl |
| 167 | pod-smb-trend-trend-pm-consolidation-hold | long | 5010 / 4641 | -0.198 | -0.102 | -5.541 | +0.024 | fail | r0_5.jsonl |
| 168 | pod-mancini-fomc-fake-breakdown-long | long | 4 / 4 | +0.142 | -0.444 | -0.484 | -0.016 | too few | r2_11.jsonl |
| 169 | pod-of4-open-drive-dryup-pullback-long | long | 1536 / 1952 | -0.122 | -0.174 | -2.749 | -0.033 | fail | r3_10.jsonl |
| 170 | pod-dalton-quiet-poc-revert-long | long | 4176 / 3871 | -0.136 | -0.166 | -4.423 | -0.035 | fail | r1_11.jsonl |
| 171 | pod-wt-abcd-buy-at-c-long | long | 123 / 160 | -0.300 | -0.035 | -1.210 | +0.010 | fail | r0_2.jsonl |
| 172 | pod-cwt4-cortes-trapzone-low-edge-hold-long | long | 508 / 264 | -0.172 | -0.108 | -2.367 | -0.016 | fail | r3_0.jsonl |
| 173 | pod-cpr-wide-range-day-pivot-fade-long | long | 3964 / 3693 | -0.116 | -0.185 | -6.631 | -0.072 | fail | r0_13.jsonl |
| 174 | pod-inside-open-pdh-magnet-IO-long | long | 17314 / 11563 | -0.142 | -0.155 | -5.418 | -0.018 | fail | r0_10.jsonl |
| 175 | pod-raschke-blindfold-breadth-div | long | 2968 / 3274 | -0.128 | -0.163 | -6.303 | -0.052 | fail | r0_7.jsonl |
| 176 | pod-of3-axia-absorption-initiation-hod-break-long | long | 212 / 113 | -0.165 | -0.105 | -1.908 | +0.018 | fail | r2_10.jsonl |
| 177 | pod-dalton-open-above-value-vah-test-long | long | 125 / 107 | -0.168 | -0.116 | -1.605 | -0.050 | fail | r1_10.jsonl |
| 178 | pod-axia-spy-newlow-divergence-long-holdtr | long | 5996 / 2737 | -0.073 | -0.297 | -1.409 | -0.009 | fail | r1_10.jsonl |
| 179 | pod-shannon-gapdown-dual-vwap-reclaim-pullback-am-long | long | 4984 / 5861 | -0.208 | -0.088 | -3.042 | -0.059 | fail | r3_6.jsonl |
| 180 | pod-smb-backside-long-into-vwap | long | 112 / 89 | -0.156 | -0.126 | -0.992 | -0.120 | fail | r0_5.jsonl |
| 181 | pod-shannon-midday-vwap-base-quiet-long | long | 2750 / 2183 | -0.151 | -0.128 | -4.663 | +0.012 | fail | r0_8.jsonl |
| 182 | pod-traderlion-open-low-pm-continuation-long | long | 552 / 747 | -0.105 | -0.167 | -2.559 | -0.030 | fail | r1_7.jsonl |
| 183 | pod-traderlion-broad-rally-laggard-vwap-catchup-long | long | 100 / 62 | -0.122 | -0.169 | -1.028 | -0.131 | fail | r1_7.jsonl |
| 184 | pod-wt-late-r2g-pdc-coil-break-long | long | 265 / 488 | -0.165 | -0.126 | -2.572 | +0.012 | fail | r3_2.jsonl |
| 185 | pod-unger-first-hour-2nd-hour-break-U-long | long | 8113 / 6823 | -0.136 | -0.142 | -5.415 | +0.005 | fail | r0_0.jsonl |
| 186 | pod-r3-hidden-bull-div-upday-long | long | 28488 / 23733 | -0.137 | -0.138 | -8.251 | -0.042 | fail | r2_8.jsonl |
| 187 | pod-of-liquidity-vacuum-fill-vr08-short | short | 2522 / 1932 | -0.158 | -0.110 | -9.669 | -0.072 | fail | r0_11.jsonl |
| 188 | pod-dalton-half-gap-hold-long-holdtr | long | 365 / 430 | -0.085 | -0.181 | -1.715 | -0.048 | fail | r1_10.jsonl |
| 189 | pod-cwt2-barrett-pdh-break-otf-confirm-long | long | 1271 / 1081 | -0.058 | -0.230 | -2.047 | -0.093 | fail | r1_0.jsonl |
| 190 | pod-raschke-breadth-thrust-vwap-reclaim-long-B | long | 5361 / 2821 | -0.071 | -0.256 | -1.744 | -0.121 | fail | r1_6.jsonl |
| 191 | pod-bbt-fallen-angel | long | 14 / 25 | +0.182 | -0.313 | -0.721 | -0.183 | too few | r0_2.jsonl |
| 192 | pod-of-liquidity-vacuum-fill-vr08-long | long | 2972 / 2165 | -0.149 | -0.114 | -12.889 | -0.004 | fail | r0_11.jsonl |
| 193 | pod-cwt-breitstein-stock-multiday-flush | long | 718 / 1185 | -0.183 | -0.102 | -2.726 | +0.065 | fail | r0_1.jsonl |
| 194 | pod-zarattini-aziz-sip-top20-rvol-30m-orb-atrstop-eod-long-spyquiet | long | 309 / 240 | -0.135 | -0.129 | -0.732 | +0.049 | fail | r3_1.jsonl |
| 195 | pod-of-defended-origin-retest-long | long | 1 / 1 | -1.095 | +0.831 | -0.194 | +0.636 | too few | r0_11.jsonl |
| 196 | pod-trush-stc-25-hook-ema200-long-15m | long | 25211 / 19549 | -0.138 | -0.122 | -5.282 | +0.000 | fail | r3_8.jsonl |
| 197 | pod-of3-dalton-rf-trend-bracket-low-pullback-long | long | 36724 / 24863 | -0.112 | -0.157 | -4.388 | -0.048 | fail | r2_10.jsonl |
| 198 | pod-traderlion-insideday-pdh-long | long | 258 / 186 | -0.139 | -0.117 | -2.066 | +0.022 | fail | r0_8.jsonl |
| 199 | pod-raschke-5sma-7bar-run-first-dip-long-t15r | long | 8362 / 7169 | -0.138 | -0.120 | -5.114 | -0.006 | fail | r3_6.jsonl |
| 200 | pod-of-liquidity-vacuum-fill-short | short | 4379 / 3421 | -0.154 | -0.099 | -11.305 | -0.060 | fail | r0_11.jsonl |
| 201 | pod-bespoke-friday-gapdown-index-orh-long-ctrl-monthu | long | 23 / 14 | -0.047 | -0.265 | -0.694 | -0.169 | too few | r2_4.jsonl |
| 202 | pod-raschke-5sma-7bar-downrun-first-rally-short | short | 6011 / 4413 | -0.135 | -0.122 | -7.221 | +0.020 | fail | r3_7.jsonl |
| 203 | pod-kell-daily-ema-crossback-first-touch-long | long | 153 / 162 | -0.155 | -0.104 | -1.841 | +0.034 | fail | r2_7.jsonl |
| 204 | pod-bbt-fallen-angel-base-long | long | 8 / 4 | +0.053 | -0.487 | -0.460 | -0.244 | too few | r0_2.jsonl |
| 205 | pod-trush-stc-25-hook-ema200-long | long | 70565 / 55501 | -0.121 | -0.135 | -6.004 | -0.018 | fail | r3_8.jsonl |
| 206 | pod-of-liquidity-vacuum-fill-long | long | 5137 / 3929 | -0.136 | -0.114 | -14.026 | -0.003 | fail | r0_11.jsonl |
| 207 | pod-of-dante-insideday-fail-short | short | 3305 / 2516 | -0.172 | -0.066 | -3.945 | +0.018 | fail | r0_10.jsonl |
| 208 | pod-trush-stc-25-hook-ema200-long-t10 | long | 65485 / 51722 | -0.121 | -0.132 | -5.860 | -0.015 | fail | r3_8.jsonl |
| 209 | pod-cwt-raschke-whiplash-intraday | long | 3646 / 3658 | -0.210 | -0.040 | -1.834 | +0.020 | fail | r0_1.jsonl |
| 210 | pod-crabel-stretch-nr4-dip-long | long | 5910 / 4203 | -0.128 | -0.118 | -6.868 | +0.019 | fail | r1_12.jsonl |
| 211 | pod-traderlion-dryup-ema21-pullback-long | long | 386 / 476 | -0.189 | -0.070 | -2.182 | +0.021 | fail | r1_7.jsonl |
| 212 | pod-smb-low-ipr-not-in-play-or-low-test-long | long | 1223 / 557 | -0.085 | -0.198 | -3.389 | -0.013 | fail | r3_4.jsonl |
| 213 | pod-edgeful-powerhour-containment-fade-long | long | 6666 / 5950 | -0.107 | -0.133 | -6.462 | -0.012 | fail | r0_12.jsonl |
| 214 | pod-raschke-5sma-7bar-run-first-dip-long-t1r | long | 8362 / 7169 | -0.123 | -0.114 | -5.556 | -0.000 | fail | r3_6.jsonl |
| 215 | pod-of-dante-insideday-fail-long | long | 3520 / 2658 | -0.098 | -0.146 | -2.852 | +0.007 | fail | r0_10.jsonl |
| 216 | pod-raschke-pinball-firsthour-short | short | 6606 / 4273 | -0.105 | -0.139 | -2.326 | -0.046 | fail | r0_0.jsonl |
| 217 | pod-smb-summit-capitulation-bb-3leg-up-volclimax-short | short | 251 / 206 | -0.126 | -0.108 | -3.191 | -0.055 | fail | r3_4.jsonl |
| 218 | pod-r3-davey-trend-aligned-3down-pullback-holdtr-long | long | 13055 / 11463 | -0.115 | -0.120 | -4.089 | -0.008 | fail | r2_9.jsonl |
| 219 | pod-shannon-gapdown-stage1-first-vwap-cross-pm-long | long | 56 / 113 | -0.236 | -0.057 | -1.167 | +0.113 | fail | r1_7.jsonl |
| 220 | pod-cwt2-katz-roundnum-first-test-pm-long | long | 31 / 53 | -0.124 | -0.111 | -0.939 | -0.039 | too few | r1_0.jsonl |
| 221 | pod-wt-stale-base-breakout-fail-short | short | 107 / 79 | -0.109 | -0.123 | -1.230 | -0.007 | fail | r0_3.jsonl |
| 222 | pod-raschke-daily-7close-below-5sma-intraday-reclaim-long-holdtr | long | 754 / 1169 | -0.051 | -0.155 | -1.887 | +0.047 | fail | r3_7.jsonl |
| 223 | pod-dalton-half-gap-hold-long | long | 365 / 430 | -0.124 | -0.103 | -1.631 | +0.038 | fail | r1_10.jsonl |
| 224 | pod-raschke-5sma-7bar-run-first-dip-long | long | 4998 / 4520 | -0.108 | -0.118 | -9.498 | +0.009 | fail | r3_6.jsonl |
| 225 | pod-shannon-maxvol-bar-avwap-first-touch-long | long | 238 / 235 | -0.163 | -0.062 | -2.008 | +0.015 | fail | r3_7.jsonl |
| 226 | pod-wt-micro-pullback-midday-reload-quiet-long | long | 397 / 434 | -0.064 | -0.156 | -1.246 | -0.044 | fail | r2_3.jsonl |
| 227 | pod-hyg-nonconfirm-spy-newlow-long-ctrl-nohyg | long | 5 / 3 | -0.317 | +0.230 | -0.537 | -2.853 | too few | r3_11.jsonl |
| 228 | pod-lps-intraday-leg-persistence-quiet-long | long | 2432 / 1681 | -0.122 | -0.098 | -3.726 | +0.041 | fail | r3_5.jsonl |
| 229 | pod-smb-second-chance-hod-retest | long | 23448 / 17934 | -0.112 | -0.111 | -6.838 | +0.017 | fail | r0_3.jsonl |
| 230 | pod-cwt3-peterto-inplay-open-trend-vwap-trail-long | long | 285 / 379 | -0.147 | -0.083 | -1.179 | +0.051 | fail | r2_1.jsonl |
| 231 | pod-bbt-quiet-day-powerhour-hod-long-short | short | 403 / 454 | -0.176 | -0.052 | -1.493 | -0.000 | fail | r0_0.jsonl |
| 232 | pod-vixy-nonconfirm-index-newlow-long | long | 23 / 22 | -0.032 | -0.190 | -0.410 | -0.379 | too few | r2_11.jsonl |
| 233 | pod-raschke-holygrail-adx-ema20-short | short | 12766 / 10396 | -0.077 | -0.147 | -3.939 | -0.062 | fail | r0_6.jsonl |
| 234 | pod-edgeful-powerhour-containment-fade-short | short | 7770 / 6088 | -0.141 | -0.066 | -5.614 | -0.024 | fail | r0_12.jsonl |
| 235 | pod-r3-slowday-stoch-range-low-small-target-long | long | 7582 / 9010 | -0.100 | -0.112 | -6.903 | -0.007 | fail | r2_9.jsonl |
| 236 | pod-cwt2-levy-index-confluence-level-ctrl-long | long | 27 / 24 | -0.149 | -0.058 | -0.568 | -0.028 | too few | r1_0.jsonl |
| 237 | pod-qr-gao-first-and-penult-volgate-close-long-ctrl-novol | long | 100 / 69 | -0.102 | -0.110 | -1.257 | -0.035 | fail | r3_9.jsonl |
| 238 | pod-lps-60d-loser-intraday-drift-long-holdtr | long | 2575 / 3744 | -0.066 | -0.131 | -2.668 | +0.009 | fail | r3_6.jsonl |
| 239 | pod-shannon-pdh-vwap-confluence-retest-long | long | 18448 / 13924 | -0.095 | -0.116 | -7.928 | +0.038 | fail | r1_7.jsonl |
| 240 | pod-carter-pm-midrange-squeeze-long | long | 557 / 480 | -0.112 | -0.092 | -2.093 | -0.043 | fail | r1_12.jsonl |
| 241 | pod-raschke-daily-7close-below-5sma-intraday-reclaim-long-t15r | long | 754 / 1169 | -0.031 | -0.148 | -1.898 | +0.082 | fail | r3_7.jsonl |
| 242 | pod-qr-gao-first-and-penult-volgate-close-long-ctrl-short | short | 9 / 38 | -0.042 | -0.116 | -0.581 | -0.109 | too few | r3_9.jsonl |
| 243 | pod-smb-stuffed-triple-top-neckline | short | 16003 / 13312 | -0.137 | -0.058 | -8.992 | -0.005 | fail | r0_5.jsonl |
| 244 | pod-smb-midday-shock-flush-into-daily-support-long | long | 192 / 170 | -0.120 | -0.078 | -3.198 | +0.031 | fail | r3_4.jsonl |
| 245 | pod-cwt-breitstein-same-price-ev-gate-holdtr | long | 2149 / 2103 | -0.045 | -0.156 | -1.545 | -0.045 | fail | r0_1.jsonl |
| 246 | pod-moglen-pd-lasthour-undercut-open-reclaim-long | long | 2623 / 2201 | -0.141 | -0.051 | -3.959 | +0.062 | fail | r3_6.jsonl |
| 247 | pod-of-trapped-breakout-stall-short | short | 5456 / 5122 | -0.109 | -0.089 | -6.536 | -0.042 | fail | r0_11.jsonl |
| 248 | pod-raschke-trend-day-last-hour-long-R | long | 5422 / 3865 | -0.125 | -0.064 | -2.392 | -0.017 | fail | r0_8.jsonl |
| 249 | pod-of-ib-mid-rotation-long | long | 11492 / 12296 | -0.102 | -0.096 | -6.113 | +0.036 | fail | r0_10.jsonl |
| 250 | pod-shannon-30m-higher-high-flat5dma-long | long | 13631 / 11280 | -0.114 | -0.082 | -5.735 | +0.044 | fail | r2_6.jsonl |
| 251 | pod-raschke-trend-day-last-hour-long-G | long | 6718 / 5246 | -0.105 | -0.089 | -2.934 | -0.017 | fail | r0_8.jsonl |
| 252 | pod-moglen-pd-lasthour-undercut-open-reclaim-long-tB | long | 2486 / 2070 | -0.130 | -0.059 | -4.482 | +0.051 | fail | r3_6.jsonl |
| 253 | pod-shannon-vwap-2d-pinch-lunch-break-long | long | 2541 / 1722 | -0.109 | -0.081 | -4.735 | +0.033 | fail | r2_7.jsonl |
| 254 | pod-wt-abcd-c-above-vwap-measured-move-quiet-long | long | 118 / 85 | -0.069 | -0.134 | -1.186 | +0.031 | fail | r3_2.jsonl |
| 255 | pod-lps-60d-loser-intraday-drift-long | long | 2575 / 3744 | -0.064 | -0.116 | -2.927 | +0.032 | fail | r3_6.jsonl |
| 256 | pod-cwt3-colkitt-letf-rebalance-close-long-t075 | long | 43 / 40 | -0.136 | -0.050 | -0.738 | -0.003 | too few | r2_0.jsonl |
| 257 | pod-camarilla-h4-trendday-break-short | short | 2715 / 1806 | -0.103 | -0.081 | -1.685 | +0.044 | fail | r0_9.jsonl |
| 258 | pod-wt-flat-top-poor-high-long | long | 3801 / 2487 | -0.103 | -0.078 | -5.945 | +0.017 | fail | r0_2.jsonl |
| 259 | pod-bst130-alvarez-regime-classified-etf-dip-long | long | 59 / 81 | -0.237 | +0.013 | -0.502 | +0.233 | fail | r3_5.jsonl |
| 260 | pod-qr-gao-first-and-penult-volgate-close-long | long | 25 / 34 | -0.413 | +0.143 | -0.640 | +0.065 | too few | r3_9.jsonl |
| 261 | pod-unger-first-hour-2nd-hour-break-U-short | short | 8542 / 6852 | -0.062 | -0.128 | -1.292 | -0.042 | fail | r0_0.jsonl |
| 262 | pod-dalton-open-rejection-reverse-M-short | short | 6865 / 6298 | -0.117 | -0.064 | -4.808 | +0.041 | fail | r0_9.jsonl |
| 263 | pod-bbt-hod-break-rising-volume-1bar-trail-long-ctrl2r | long | 1099 / 1086 | -0.081 | -0.102 | -2.160 | +0.019 | fail | r2_2.jsonl |
| 264 | pod-smb-summit-capitulation-bb-3leg-volclimax-long | long | 443 / 428 | -0.030 | -0.154 | -2.426 | +0.018 | fail | r3_3.jsonl |
| 265 | pod-connors-hourly-rsi2-uptrend-index-long | long | 73 / 111 | -0.202 | -0.018 | -1.407 | +0.157 | fail | r2_12.jsonl |
| 266 | pod-wt-first-new-high-after-base-pullback-macd-gate-long | long | 1 / 1 | +1.135 | -1.317 | -0.105 | -1.955 | too few | r3_2.jsonl |
| 267 | pod-raschke-trend-day-last-hour-short-R | short | 5102 / 3206 | -0.024 | -0.197 | -1.527 | -0.078 | fail | r0_8.jsonl |
| 268 | pod-grimes-keltner-thrust-first-ema20-pullback-long | long | 1623 / 2188 | -0.074 | -0.103 | -4.164 | -0.009 | fail | r3_11.jsonl |
| 269 | pod-raschke-pinball-firsthour-long | long | 7047 / 5278 | -0.053 | -0.137 | -2.032 | +0.012 | fail | r0_0.jsonl |
| 270 | pod-dalton-open-rejection-reverse-M-long | long | 7379 / 6577 | -0.115 | -0.059 | -4.867 | +0.048 | fail | r0_9.jsonl |
| 271 | pod-hougaard-school-run-2nd15-break-short | short | 1843 / 2330 | -0.080 | -0.095 | -0.888 | +0.046 | fail | r1_8.jsonl |
| 272 | pod-camarilla-l3-quiet-fade-long | long | 2784 / 2047 | -0.097 | -0.076 | -5.404 | +0.054 | fail | r0_9.jsonl |
| 273 | pod-unger-first-hour-2nd-hour-break-B-short | short | 1763 / 1128 | -0.094 | -0.077 | -1.463 | -0.024 | fail | r0_0.jsonl |
| 274 | pod-shannon-lod-avwap-loss-short | short | 1313 / 642 | -0.111 | -0.037 | -0.613 | +0.133 | fail | r0_7.jsonl |
| 275 | pod-smb-fashionably-late-long | long | 8749 / 9334 | -0.041 | -0.128 | -1.523 | -0.026 | fail | r0_3.jsonl |
| 276 | pod-smb-big-dog-consolidation-above-vwap-break-long | long | 158 / 152 | -0.070 | -0.102 | -1.441 | +0.033 | fail | r2_3.jsonl |
| 277 | pod-of3-multiday-balance-break-acceptance-long | long | 315 / 207 | -0.045 | -0.144 | -1.972 | +0.041 | fail | r2_10.jsonl |
| 278 | pod-bbt-hod-break-rising-volume-1bar-trail-long | long | 1099 / 1086 | -0.086 | -0.080 | -3.902 | +0.041 | fail | r2_2.jsonl |
| 279 | pod-traderlion-open-low-pm-continuation-long-holdtr | long | 552 / 747 | -0.063 | -0.098 | -1.963 | +0.046 | fail | r1_7.jsonl |
| 280 | pod-raschke-daily-7close-below-5sma-intraday-reclaim-long | long | 754 / 1169 | +0.005 | -0.139 | -1.180 | +0.091 | fail | r3_7.jsonl |
| 281 | pod-cwt-unger-maxhigh-afternoon-short | short | 11795 / 10609 | -0.085 | -0.080 | -4.063 | +0.026 | fail | r0_1.jsonl |
| 282 | pod-raschke-breadth-thrust-vwap-reclaim-long-A | long | 5361 / 2821 | -0.045 | -0.153 | -1.767 | -0.087 | fail | r1_6.jsonl |
| 283 | pod-cwt4-alintoff-pressure-point-30m-stoch-div-break-long-ctrl-nodiv | long | 4748 / 4460 | -0.089 | -0.073 | -4.087 | +0.076 | fail | r3_1.jsonl |
| 284 | pod-shannon-rolling-2d-vwap-quiet-pullback-long | long | 4583 / 1997 | -0.080 | -0.084 | -4.220 | +0.046 | fail | r2_6.jsonl |
| 285 | pod-bbt-920-trade-near-52wh-first-ema21-touch-long | long | 279 / 281 | -0.179 | +0.017 | -0.925 | +0.105 | fail | r2_2.jsonl |
| 286 | pod-vwap-1sd-band-ride-pullback-long | long | 195 / 172 | -0.033 | -0.132 | -1.136 | -0.120 | fail | r2_12.jsonl |
| 287 | pod-bst018-andrews-gapzone-fade-H-short | short | 754 / 833 | -0.121 | -0.040 | -3.825 | -0.054 | fail | r0_5.jsonl |
| 288 | pod-shannon-5dma-mtf-pullback-long | long | 5091 / 4180 | -0.095 | -0.056 | -4.591 | +0.085 | fail | r0_7.jsonl |
| 289 | pod-smb-day2-pdc-support-hold-long | long | 41 / 28 | -0.068 | -0.091 | -0.746 | +0.044 | too few | r1_4.jsonl |
| 290 | pod-smb-bull-flag-no-overhead-supply-long | long | 120 / 171 | -0.157 | -0.021 | -1.009 | +0.058 | fail | r3_4.jsonl |
| 291 | pod-cwt4-jelinek-multiday-unfilled-gap-magnet-long-ctrl-nogap | long | 30106 / 25961 | -0.078 | -0.075 | -2.639 | +0.005 | fail | r3_1.jsonl |
| 292 | pod-smb-held-floor-triple-bottom-long | long | 3229 / 3449 | -0.111 | -0.043 | -3.099 | +0.038 | fail | r1_4.jsonl |
| 293 | pod-camarilla-l3-quiet-fade-short | short | 2980 / 2124 | -0.085 | -0.060 | -4.322 | +0.007 | fail | r0_9.jsonl |
| 294 | pod-smb-k-opening-drive-vwap-consolidation-reasons2sell-long | long | 4115 / 4705 | -0.061 | -0.084 | -3.611 | +0.051 | fail | r3_3.jsonl |
| 295 | pod-hill-iwm-leads-reversal-long | long | 6 / 6 | -0.033 | -0.111 | -0.291 | -0.274 | too few | r2_11.jsonl |
| 296 | pod-raschke-adx-gapper-long | long | 85 / 62 | -0.002 | -0.168 | -1.076 | +0.005 | fail | r0_0.jsonl |
| 297 | pod-of3-barros-ib-failed-lookbelow-opposite-extension-long | long | 328 / 280 | -0.126 | -0.005 | -1.115 | +0.065 | fail | r2_9.jsonl |
| 298 | pod-cwt3-harris-kama-atr-band-to-band-long | long | 684 / 694 | +0.003 | -0.141 | -1.379 | -0.043 | fail | r2_0.jsonl |
| 299 | pod-cwt4-alintoff-pressure-point-30m-stoch-div-break-long | long | 1117 / 1008 | -0.093 | -0.043 | -2.249 | +0.108 | fail | r3_1.jsonl |
| 300 | pod-of3-barros-failed-auction-high-revisit-long | long | 5452 / 5161 | -0.051 | -0.087 | -2.429 | +0.050 | fail | r2_10.jsonl |
| 301 | pod-r3-williams-smash-day-pdh-reversal-long-t1s1 | long | 2031 / 1648 | -0.040 | -0.104 | -1.844 | +0.008 | fail | r2_9.jsonl |
| 302 | pod-lps-overnight-loser-intraday-rebound-etf-long | long | 6496 / 7399 | -0.021 | -0.110 | -2.538 | +0.005 | fail | r3_5.jsonl |
| 303 | pod-cwt-breitstein-same-price-ev-gate | long | 2149 / 2103 | -0.049 | -0.088 | -1.083 | +0.017 | fail | r0_1.jsonl |
| 304 | pod-nesnidal-poi-breakout-short | short | 33203 / 25853 | -0.036 | -0.109 | -1.457 | -0.021 | fail | r0_6.jsonl |
| 305 | pod-fisher-acd-aup-pivot-long | long | 5142 / 4152 | -0.049 | -0.090 | -1.855 | +0.051 | fail | r1_11.jsonl |
| 306 | pod-traderlion-kell-wedge-pop-long | long | 809 / 806 | -0.085 | -0.048 | -1.165 | +0.048 | fail | r1_8.jsonl |
| 307 | pod-wt-first-two-pullbacks-only-gate-long--coil-a2 | long | 6556 / 7036 | -0.064 | -0.069 | -4.311 | +0.007 | fail | r3_3.jsonl |
| 308 | pod-cwt-mcdermitt-rs-hold-at-index-newlow-long | long | 14005 / 16513 | -0.093 | -0.043 | -3.015 | +0.043 | fail | r1_5.jsonl |
| 309 | pod-wt-first-two-pullbacks-only-gate-long--coil-ungated | long | 6879 / 7373 | -0.063 | -0.069 | -4.308 | +0.008 | fail | r3_3.jsonl |
| 310 | pod-cwt-unger-maxhigh-afternoon-long | long | 14001 / 10633 | -0.066 | -0.065 | -2.243 | +0.058 | fail | r0_1.jsonl |
| 311 | pod-smb-gap-above-lt-level-rebid-long | long | 8 / 8 | -0.207 | +0.076 | -0.200 | +0.046 | too few | r2_3.jsonl |
| 312 | pod-wt-first-two-pullbacks-only-gate-long--coil-a3 | long | 6789 / 7271 | -0.063 | -0.068 | -4.276 | +0.009 | fail | r3_3.jsonl |
| 313 | pod-wt-first-two-pullbacks-only-gate-long | long | 6789 / 7271 | -0.063 | -0.068 | -4.276 | +0.009 | fail | r3_3.jsonl |
| 314 | pod-of3-responsive-val-reclaim-inside-value-open-long | long | 1189 / 1119 | -0.029 | -0.104 | -2.174 | +0.038 | fail | r2_10.jsonl |
| 315 | pod-raschke-trend-day-last-hour-short-G | short | 5882 / 4758 | -0.005 | -0.139 | -1.189 | -0.061 | fail | r0_8.jsonl |
| 316 | pod-bst018-andrews-gapzone-fade-F-short | short | 2098 / 2104 | -0.083 | -0.047 | -2.891 | -0.041 | fail | r0_5.jsonl |
| 317 | pod-bst018-andrews-gapzone-fade-F-long | long | 2329 / 1757 | -0.081 | -0.043 | -3.431 | +0.058 | fail | r0_5.jsonl |
| 318 | pod-nesnidal-poi-breakout-long | long | 31819 / 25037 | -0.015 | -0.126 | -1.822 | +0.023 | fail | r0_6.jsonl |
| 319 | pod-options-strike-pin-magnet-long | long | 704 / 1099 | -0.074 | -0.057 | -1.885 | +0.090 | fail | r1_12.jsonl |
| 320 | pod-crabel-stretch-open-reclaim-long | long | 4843 / 4071 | -0.071 | -0.054 | -4.449 | +0.070 | fail | r1_6.jsonl |
| 321 | pod-inside-open-pdh-magnet-PH-long | long | 684 / 655 | -0.104 | -0.021 | -1.195 | +0.040 | fail | r0_10.jsonl |
| 322 | pod-raschke-taylor-buyday-low-first-long | long | 7841 / 8310 | -0.082 | -0.046 | -2.764 | +0.073 | fail | r2_7.jsonl |
| 323 | pod-wt-flat-top-roundnum-long | long | 2165 / 2352 | -0.064 | -0.059 | -3.544 | +0.034 | fail | r0_2.jsonl |
| 324 | pod-zarattini-noise-lower-fail-quiet-long | long | 20 / 18 | -0.047 | -0.077 | -0.353 | -0.131 | too few | r3_9.jsonl |
| 325 | pod-cwt4-jelinek-multiday-unfilled-gap-magnet-long | long | 1294 / 1323 | -0.007 | -0.114 | -1.035 | -0.042 | fail | r3_1.jsonl |
| 326 | pod-of-pdh-time-acceptance-short | short | 7180 / 6652 | -0.052 | -0.071 | -2.765 | +0.016 | fail | r0_11.jsonl |
| 327 | pod-smb-market-flush-holder-long-t1s1 | long | 913 / 485 | -0.067 | -0.049 | -1.856 | -0.012 | fail | r0_5.jsonl |
| 328 | pod-vxx-volcrush-vwap-pullback-long | long | 134 / 111 | -0.067 | -0.051 | -0.739 | +0.055 | fail | r2_5.jsonl |
| 329 | pod-hougaard-school-run-2nd15-break-long | long | 10712 / 10388 | -0.064 | -0.055 | -1.989 | +0.024 | fail | r1_8.jsonl |
| 330 | pod-r3-eod-loser-reversal-spy-newhod-long-t05s1 | long | 487 / 661 | -0.082 | -0.041 | -2.366 | +0.011 | fail | r2_8.jsonl |
| 331 | pod-oneil-pocket-pivot-volume-pace-pm-long | long | 4285 / 3647 | -0.048 | -0.065 | -1.994 | +0.046 | fail | r2_6.jsonl |
| 332 | pod-cwt2-shapiro-ps60-hourly-pivot-long | long | 30375 / 21618 | -0.041 | -0.076 | -3.327 | +0.052 | fail | r1_0.jsonl |
| 333 | pod-bbt-dileo-vwap-bounce-break-level-bottom-long | long | 69 / 67 | +0.034 | -0.146 | -0.396 | -0.108 | fail | r2_2.jsonl |
| 334 | pod-qs-spy-prior-lasthour-low-morning-long-x1130 | long | 40 / 33 | +0.128 | -0.275 | -0.409 | +0.363 | too few | r3_8.jsonl |
| 335 | pod-r3-eod-loser-reversal-spy-newhod-long | long | 487 / 661 | -0.088 | -0.029 | -1.909 | +0.030 | fail | r2_8.jsonl |
| 336 | pod-of-pdh-time-acceptance-long | long | 9114 / 6266 | -0.028 | -0.091 | -2.567 | +0.030 | fail | r0_11.jsonl |
| 337 | pod-smb-k-opening-drive-vwap-consolidation-reasons2sell-long--fixed-target | long | 4114 / 4704 | -0.015 | -0.085 | -1.292 | +0.050 | fail | r3_3.jsonl |
| 338 | pod-shannon-ytd-avwap-first-touch-long | long | 78 / 247 | -0.128 | -0.027 | -0.597 | +0.017 | fail | r2_6.jsonl |
| 339 | pod-of-open-test-drive-long | long | 1004 / 766 | -0.002 | -0.113 | -1.280 | +0.044 | fail | r0_12.jsonl |
| 340 | pod-qs-lowvol-day-gapup-etf-open-hold-long-ctrl-normvol | long | 59 / 76 | +0.024 | -0.107 | -0.375 | +0.117 | fail | r3_7.jsonl |
| 341 | pod-bbt-quiet-day-powerhour-hod-long-long | long | 535 / 355 | -0.060 | -0.034 | -0.610 | +0.096 | fail | r0_0.jsonl |
| 342 | pod-smb-changing-fundamentals-hold-long-holdtr | long | 803 / 1362 | -0.146 | +0.008 | -0.670 | +0.049 | fail | r0_4.jsonl |
| 343 | pod-of-ib-mid-rotation-short | short | 11494 / 11718 | -0.083 | -0.015 | -2.854 | +0.015 | fail | r0_10.jsonl |
| 344 | pod-cal-opex-friday-strike-pin-fade-short | short | 1729 / 1654 | -0.101 | +0.009 | -0.988 | -0.003 | fail | r1_5.jsonl |
| 345 | pod-cwt4-singh-sma50-undercut-remount-long | long | 698 / 1461 | +0.028 | -0.084 | -1.876 | +0.037 | fail | r3_0.jsonl |
| 346 | pod-traderlion-undercut-rally-long | long | 584 / 747 | -0.060 | -0.037 | -1.491 | +0.022 | fail | r0_8.jsonl |
| 347 | pod-smb-market-flush-holder-long | long | 913 / 485 | -0.044 | -0.049 | -2.316 | -0.006 | fail | r0_5.jsonl |
| 348 | pod-bst018-andrews-gapzone-fade-H-long | long | 826 / 627 | -0.039 | -0.050 | -2.863 | +0.044 | fail | r0_5.jsonl |
| 349 | pod-traderlion-orh60-leader-long | long | 86 / 53 | -0.046 | -0.036 | -0.731 | -0.023 | fail | r0_8.jsonl |
| 350 | pod-moglen-daily-ema21-pullback-pdh-break-long | long | 326 / 334 | -0.100 | +0.016 | -1.521 | +0.104 | fail | r3_7.jsonl |
| 351 | pod-smb-day2-drive-pullback-long | long | 53 / 86 | -0.202 | +0.058 | -0.325 | +0.042 | fail | r0_4.jsonl |
| 352 | pod-dalton-open-rejection-reverse-H-short | short | 6865 / 6298 | -0.056 | -0.021 | -3.131 | +0.084 | fail | r0_9.jsonl |
| 353 | pod-cwt4-raschke-post-expansion-range-low-test-long | long | 391 / 1419 | -0.040 | -0.037 | -1.707 | +0.115 | fail | r3_0.jsonl |
| 354 | pod-dalton-open-rejection-reverse-H-long | long | 7379 / 6577 | -0.044 | -0.028 | -3.191 | +0.079 | fail | r0_9.jsonl |
| 355 | pod-cal-tom-vwap-pullback-stock-long | long | 15500 / 14939 | -0.076 | +0.005 | -1.112 | +0.004 | fail | r1_5.jsonl |
| 356 | pod-cwt4-adrian-gapdown-mae-limit-fill-long | long | 7 / 15 | +0.127 | -0.112 | -0.107 | +0.210 | too few | r3_0.jsonl |
| 357 | pod-steenbarger-powerhour-breadth-thrust-long | long | 267 / 308 | -0.072 | -0.003 | -0.292 | +0.031 | fail | r1_12.jsonl |
| 358 | pod-shannon-mtf-5dma-rejection-short | short | 1599 / 2687 | -0.099 | +0.003 | -1.676 | +0.021 | fail | r0_8.jsonl |
| 359 | pod-smb-spencer-index-fixed-drop-off-morning-high-long | long | 44 / 45 | -0.092 | +0.021 | -0.308 | +0.075 | too few | r3_3.jsonl |
| 360 | pod-smb-ipr-inplay-or-ratio-first-pullback-long | long | 105 / 93 | -0.102 | +0.043 | -0.432 | +0.142 | fail | r3_3.jsonl |
| 361 | pod-axia-inventory-correction-gapdown-etf-long | long | 56 / 37 | -0.165 | +0.167 | -0.172 | +0.183 | too few | r1_10.jsonl |
| 362 | pod-cwt064-radge-atr-limit-dip-close-exit-long | long | 1922 / 3277 | -0.030 | -0.031 | -2.001 | +0.116 | fail | r3_5.jsonl |
| 363 | pod-smb-gapdown-opening-print-reclaim-A-long | long | 401 / 331 | -0.004 | -0.064 | -0.302 | +0.053 | fail | r1_4.jsonl |
| 364 | pod-smb-quiet-tape-level-fade-long | long | 7 / 4 | +0.028 | -0.133 | -0.097 | -0.154 | too few | r0_3_qt.jsonl |
| 365 | pod-alvarez-nostop-etf-oversold-time-exit-long | long | 249 / 360 | -0.029 | -0.032 | -1.650 | +0.169 | fail | r2_5.jsonl |
| 366 | pod-qs-3down-days-orh-break-long-ctrl-no3down | long | 170 / 274 | -0.010 | -0.042 | -0.533 | +0.041 | fail | r2_12.jsonl |
| 367 | pod-qs-spy-prior-lasthour-low-morning-long-high-short | short | 122 / 73 | -0.046 | +0.003 | -0.250 | +0.190 | fail | r3_8.jsonl |
| 368 | pod-cwt3-dhadwar-3day-value-below-reclaim-long | long | 913 / 943 | -0.006 | -0.045 | -0.560 | +0.004 | fail | r2_1.jsonl |
| 369 | pod-of3-barros-ib-failed-lookbelow-opposite-extension-long-hold1 | long | 226 / 183 | -0.058 | +0.017 | -0.456 | +0.053 | fail | r2_9.jsonl |
| 370 | pod-shannon-avwap-handoff-long | long | 3596 / 2732 | -0.042 | +0.000 | -1.012 | +0.094 | fail | r0_7.jsonl |
| 371 | pod-bst-alvarez-pd-lowibs-etf-vwap-hold-long | long | 95 / 90 | +0.106 | -0.159 | -0.302 | +0.139 | fail | r3_5.jsonl |
| 372 | pod-smb-light-counter-move-long | long | 743 / 517 | -0.060 | +0.035 | -0.230 | +0.085 | fail | r0_4.jsonl |
| 373 | pod-rule201-ssr-intraday-trigger-reclaim-long | long | 64 / 123 | +0.041 | -0.052 | -0.327 | +0.112 | fail | r3_4.jsonl |
| 374 | pod-traderlion-qqq-vwap-reclaim-rs-leader-long-S | long | 3020 / 3791 | +0.092 | -0.105 | -0.337 | +0.009 | fail | r1_7.jsonl |
| 375 | pod-brooks-final-bear-flag-fail-long | long | 232 / 253 | +0.038 | -0.068 | -0.385 | +0.027 | fail | r1_9.jsonl |
| 376 | pod-dalton-open-drive-pullback-OF-long | long | 182 / 125 | +0.085 | -0.162 | -0.315 | +0.019 | fail | r0_9.jsonl |
| 377 | pod-edgeful-green-first15-open-hold-long | long | 1746 / 1791 | +0.023 | -0.053 | -0.304 | +0.026 | fail | r0_13.jsonl |
| 378 | pod-smb-changing-fundamentals-hold-long | long | 803 / 1362 | -0.087 | +0.030 | -0.193 | +0.057 | fail | r0_4.jsonl |
| 379 | pod-opex-friday-round-strike-pin-fade-long | long | 2 / 4 | -0.263 | +0.112 | -0.063 | +0.064 | too few | r1_9.jsonl |
| 380 | pod-williams-oops-pdl-reclaim-long | long | 834 / 763 | -0.009 | -0.016 | -0.409 | +0.041 | fail | r2_11.jsonl |
| 381 | pod-cwt-unger-quietib-fade-short | short | 1966 / 1305 | -0.048 | +0.044 | -0.451 | +0.039 | fail | r0_0.jsonl |
| 382 | pod-qs-spy-prior-lasthour-low-morning-long | long | 40 / 33 | +0.212 | -0.282 | -0.079 | +0.357 | too few | r3_8.jsonl |
| 383 | pod-smb-pdl-bounce-momentum-confirm | long | 5 / 12 | -0.381 | +0.145 | -0.081 | +0.240 | too few | r0_4.jsonl |
| 384 | pod-traderlion-qqq-vwap-reclaim-rs-leader-long | long | 3020 / 3791 | +0.124 | -0.115 | -0.136 | -0.049 | fail | r1_7.jsonl |
| 385 | pod-fomc-2pm-flush-reversal-long | long | 5 / 4 | +0.209 | -0.278 | -0.037 | +0.309 | too few | r2_5.jsonl |
| 386 | pod-camarilla-h4-trendday-break-long | long | 3102 / 1803 | +0.057 | -0.116 | -0.076 | +0.001 | fail | r0_9.jsonl |
| 387 | pod-lunch-effect-index-long | long | 252 / 195 | -0.010 | -0.000 | -0.069 | -0.002 | fail | r0_12.jsonl |
| 388 | pod-cal-opex-friday-strike-pin-fade-long | long | 1651 / 1839 | +0.091 | -0.085 | -0.031 | +0.047 | fail | r1_5.jsonl |
| 389 | pod-cwt-unger-quietib-fade-long | long | 1845 / 1246 | -0.016 | +0.022 | -0.021 | +0.110 | fail | r0_0.jsonl |
| 390 | pod-bbt-market-vwap-test-rs-hold-long-S | long | 248 / 234 | +0.033 | -0.036 | -0.019 | -0.019 | fail | r1_2.jsonl |
| 391 | pod-bbt-market-vwap-test-rs-hold-long | long | 271 / 242 | +0.036 | -0.040 | -0.005 | +0.010 | fail | r1_2.jsonl |
| 392 | pod-bst018-andrews-gapzone-fade-etf-long | long | 7 / 6 | +0.078 | -0.082 | +0.069 | -0.113 | too few | r0_5.jsonl |
| 393 | pod-traderlion-qqq-vwap-reclaim-rs-leader-long-holdtr | long | 3020 / 3791 | +0.163 | -0.121 | +0.056 | -0.043 | fail | r1_7.jsonl |
| 394 | pod-r3-williams-smash-day-pdh-reversal-long | long | 2031 / 1648 | +0.025 | -0.020 | +0.153 | +0.098 | fail | r2_9.jsonl |
| 395 | pod-bbt-vwap-reversal-no-new-5m-low-to-vwap-long-chopspy | long | 122 / 132 | -0.057 | +0.066 | +0.099 | +0.178 | fail | r3_1.jsonl |
| 396 | pod-rule201-ssr-day2-or-break-long | long | 54 / 124 | +0.088 | -0.023 | +0.180 | +0.035 | fail | r3_4.jsonl |
| 397 | pod-smb-day2-compression-afternoon-break-long | long | 12 / 11 | -0.332 | +0.390 | +0.062 | +0.555 | too few | r2_4.jsonl |
| 398 | pod-harris-monday-morning-weakness-open-reclaim-index-long | long | 32 / 22 | -0.060 | +0.156 | +0.225 | +0.185 | too few | r3_5.jsonl |
| 399 | pod-bbt-extreme-rev-mtf-920-long | long | 0 / 2 |  | +0.029 | +0.438 | +0.222 | too few | r0_2.jsonl |
| 400 | pod-of4-spy-pdl-stoprun-reclaim-rs-stock-long | long | 145 / 145 | +0.067 | -0.007 | +0.910 | +0.090 | fail | r3_10.jsonl |
| 401 | pod-raschke-adx-gapper-short | short | 70 / 85 | +0.061 | +0.004 | +0.593 | +0.368 | positive, failed gates | r0_0.jsonl |
| 402 | pod-smb-20d-high-time-acceptance-long | long | 299 / 179 | +0.009 | +0.069 | +0.491 | +0.185 | positive, failed gates | r1_4.jsonl |
| 403 | pod-qtr-end-window-dressing-winner-pm-long | long | 211 / 296 | +0.083 | -0.005 | +0.661 | +0.034 | fail | r2_6.jsonl |
| 404 | pod-williams-smash-day-pdh-long | long | 156 / 197 | -0.033 | +0.084 | +0.651 | +0.111 | fail | r2_5.jsonl |
| 405 | pod-breadth-trendday-index-pullback-long | long | 34 / 13 | +0.002 | +0.122 | +0.234 | +0.095 | too few | r0_13.jsonl |
| 406 | pod-em-vix-implied-lower-band-reclaim-long | long | 9 / 17 | +0.254 | -0.075 | +0.226 | +0.163 | too few | r2_11.jsonl |
| 407 | pod-cwt3-colkitt-letf-rebalance-close-long | long | 23 / 28 | +0.013 | +0.073 | +0.259 | +0.075 | too few | r2_0.jsonl |
| 408 | pod-bbt-vwap-reversal-no-new-5m-low-to-vwap-long | long | 148 / 182 | +0.020 | +0.068 | +0.665 | +0.127 | positive, failed gates | r3_1.jsonl |
| 409 | pod-aziz-zarattini-index-first-candle-direction-orb-10r-long | long | 84 / 83 | +0.044 | +0.051 | +0.520 | +0.090 | positive, failed gates | r3_2.jsonl |
| 410 | pod-cwt4-gogolak-1000bar-sma-dip-vixrise-etf-long | long | 65 / 62 | +0.004 | +0.102 | +0.680 | -0.286 | positive, failed gates | r3_0.jsonl |
| 411 | pod-raschke-compression-20d-channel-pm-break-long | long | 40 / 7 | +0.106 | -0.245 | +0.462 | -0.072 | too few | r3_7.jsonl |
| 412 | pod-qs-3down-days-orh-break-long | long | 12 / 22 | -0.132 | +0.156 | +0.332 | -0.171 | too few | r2_12.jsonl |
| 413 | pod-wt-first-two-pullbacks-only-gate-long--wtflag-a2 | long | 617 / 35 | +0.077 | +0.120 | +2.996 | +0.298 | positive, failed gates | r3_3.jsonl |
| 414 | pod-smb-inplay-quiet-spy-afternoon-vwap-snap-long | long | 10 / 3 | -0.452 | +1.870 | +0.211 | +1.613 | too few | r1_4.jsonl |
| 415 | pod-williams-oops-etf-red-day-long | long | 69 / 80 | +0.203 | -0.007 | +0.985 | +0.221 | fail | r2_5.jsonl |
| 416 | pod-oa-wide-first-hour-continuation-long | long | 31 / 32 | -0.101 | +0.282 | +0.419 | +0.156 | too few | r0_12.jsonl |
| 417 | pod-wt-first-two-pullbacks-only-gate-long--wtflag-a1 | long | 687 / 36 | +0.091 | +0.166 | +3.844 | +0.349 | positive, failed gates | r3_3.jsonl |
| 418 | pod-wt-first-two-pullbacks-only-gate-long--wtflag-a3 | long | 618 / 31 | +0.102 | +0.205 | +4.252 | +0.365 | positive, failed gates | r3_3.jsonl |
| 419 | pod-wt-bull-flag-breakout-or-bailout-long | long | 756 / 40 | +0.108 | +0.113 | +4.932 | +0.301 | positive, failed gates | r1_2.jsonl |
| 420 | pod-wt-first-two-pullbacks-only-gate-long--wtflag-ungated | long | 756 / 40 | +0.108 | +0.113 | +4.932 | +0.301 | positive, failed gates | r3_3.jsonl |
| 421 | pod-qs-lowvol-day-gapup-etf-open-hold-long-g030 | long | 17 / 21 | +0.320 | -0.061 | +0.312 | -0.031 | too few | r3_7.jsonl |
| 422 | pod-qs-lowvol-day-gapup-etf-open-hold-long | long | 14 / 17 | +0.169 | +0.077 | +0.319 | -0.069 | too few | r3_7.jsonl |
| 423 | pod-thrasher-intraday-breadth-thrust-long | long | 47 / 21 | +0.168 | +0.063 | +0.679 | -0.000 | too few | r1_8.jsonl |
| 424 | pod-vxx-lower-high-spy-newlow-div-long | long | 30 / 3 | +0.107 | +0.491 | +0.640 | +0.351 | too few | r2_5.jsonl |
| 425 | pod-smh-leads-qqq-nonconfirm-long | long | 8 / 10 | +0.274 | +0.037 | +0.685 | -0.218 | too few | r3_8.jsonl |
| 426 | pod-cwt2-johansson-index-divergence-holder-long | long | 18 / 10 | +0.012 | +0.395 | +0.989 | +0.264 | too few | r1_0.jsonl |
| 427 | pod-breadth-thrust-midday-index-long | long | 120 / 48 | +0.059 | +0.398 | +0.952 | +0.000 | positive, failed gates | r1_6.jsonl |
| 428 | pod-bespoke-hotcpi-gapdown-first-hour-bounce-long | long | 1 / 3 | +0.222 | +0.146 | +1.390 | +1.048 | too few | r2_4.jsonl |
| 429 | pod-thrasher-intraday-breadth-thrust-stocks-long | long | 1273 / 841 | +0.102 | +0.287 | +1.269 | +0.065 | positive, failed gates | r1_8.jsonl |
| 430 | pod-chop-pop-volume-breakout-long | long | 14 / 9 | +0.223 | +0.114 | +0.844 | +0.172 | too few | r0_12.jsonl |
| 431 | pod-wt-first-red-after-3-greens-ema9-touch-long | long | 1 / 1 | -1.597 | +1.980 | +0.151 | +0.470 | too few | r3_2.jsonl |
| 432 | pod-cwt3-colkitt-letf-rebalance-close-long-t150 | long | 12 / 17 | +0.285 | +0.180 | +1.082 | +0.149 | too few | r2_0.jsonl |
| 433 | pod-bbt-10am-reversal-spy-turn-long | long | 1 / 2 | -1.050 | +0.863 | +0.430 | +0.474 | too few | r1_2.jsonl |
| 434 | pod-turnaround-tuesday-open-reclaim-index-long | long | 3 / 7 | -0.260 | +0.472 | +1.036 | +0.209 | too few | r1_12.jsonl |
| 435 | pod-oa-narrow-first-hour-pm-break-long | long | 21 / 7 | +0.375 | -0.095 | +1.818 | +0.223 | too few | r3_12.jsonl |
| 436 | pod-baltussen-tlt-flight-to-quality-close-long-gld | long | 10 / 4 | +0.584 | -0.398 | +1.082 | -0.315 | too few | r3_8.jsonl |
| 437 | pod-wt-first-two-pullbacks-only-gate-long--redditflag-a1 | long | 687 / 36 | +0.333 | -0.013 | +4.503 | +0.170 | fail | r3_3.jsonl |
| 438 | pod-wt-bull-flag-breakout-or-bailout-long-S | long | 756 / 40 | +0.349 | -0.028 | +4.913 | +0.160 | fail | r1_2.jsonl |
| 439 | pod-wt-first-two-pullbacks-only-gate-long--redditflag-ungated | long | 756 / 40 | +0.349 | -0.028 | +4.913 | +0.160 | fail | r3_3.jsonl |
| 440 | pod-thrasher-intraday-breadth-thrust-pb-long | long | 32 / 15 | +0.268 | +0.548 | +1.509 | -0.036 | too few | r1_8.jsonl |
| 441 | pod-hill-iwm-leads-reversal-iwm-long | long | 6 / 6 | +0.325 | +0.461 | +3.039 | +0.211 | too few | r2_11.jsonl |
| 442 | pod-dalton-open-drive-pullback-D-long | long | 12 / 10 | +0.407 | +0.398 | +0.736 | +0.564 | too few | r0_9.jsonl |
| 443 | pod-qs-tlt-monthend-intraday-long-gld | long | 25 / 14 | +0.411 | +0.523 | +2.128 | -0.060 | too few | r3_8.jsonl |
| 444 | pod-axia-or-buying-tail-late-break-long | long | 2 / 3 | +0.662 | +0.316 | +1.054 | +0.403 | too few | r1_11.jsonl |
| 445 | pod-opex-friday-round-strike-pin-fade-short | short | 2 / 4 | -0.184 | +0.793 | +1.954 | +0.341 | too few | r1_9.jsonl |
| 446 | pod-steenbarger-breadth-shock-uptrend-index-long | long | 11 / 0 | +0.494 |  | +1.016 |  | too few | r1_8.jsonl |
| 447 | pod-bespoke-friday-gapdown-index-orh-long | long | 6 / 13 | +0.303 | +0.594 | +1.361 | -0.076 | too few | r2_4.jsonl |
| 448 | pod-mancini-fomc-fake-breakdown-short | short | 5 / 1 | +0.548 | +0.831 | +9.907 | -2.493 | too few | r2_11.jsonl |
| 449 | pod-smb-spencer-monday-lower-low-pullback-index-long | long | 2 / 0 | +0.734 |  |  |  | too few | r3_3.jsonl |
| 450 | pod-smb-2day-avwap-first-touch-quiet-long | long | 8 / 6 | +1.381 | +0.667 | +1.022 | +0.706 | too few | r2_3.jsonl |
| 451 | pod-bbt-1to10-index-megacap-close-reversal-long | long | 2 / 0 | +1.095 |  | +1.086 |  | too few | r2_2.jsonl |
| 452 | pod-of3-dalton-neutral-day-center-revert-short | short | 1 / 2 | +2.857 | +0.395 | +1.242 | +0.649 | too few | r2_10.jsonl |


## Addendum 2026-10-23: observation setups added to the Setup Generator (owner)

The owner asked for the ideas that were positive after costs in BOTH train and valid, one version per idea, as
observation setups in `config/account_gen.yaml`, effective Monday 2026-10-26. **None passed the merit bar**: best-day
share is high on all of them and none is significant on valid; configurations tried in the batch: **452**. Costs in, the
locked block 2024-11-01..2025-02-28 never read.

### Added (3)
| id | live module | side / geom | train n, avgR, t | valid n, avgR, t | per session | excess vs random tr / va | best day (share of R) |
|---|---|---|---|---|---|---|---|
| GEN-POD1022-01-thrasher-breadth-thrust-stocks-holdtr-long | live/pod-thrasher-intraday-breadth-thrust-stocks-long-live.py | long / holdtr | 1273, +0.102, 0.64 | 841, +0.287, 1.19 | 4.96 | +0.030 / +0.065 | 2026-06-11 (33%); only 23 active days |
| GEN-POD1022-02-breadth-thrust-index-etf-holdtr-long | live/pod-breadth-thrust-midday-index-long-live.py | long / holdtr (SPY QQQ IWM DIA) | 120, +0.059, 0.29 | 48, +0.398, 1.53 | 0.39 | 0 / 0 (by construction) | 2025-04-30 (37%) |
| GEN-POD1022-03-wt-bull-flag-bailout-S-long | live/pod-wt-bull-flag-breakout-or-bailout-long-live.py | long / S + BE 0.5R + 10-min time stop | 756, +0.141, 5.88 | 40, +0.076, 0.40 | 1.87 (0.21 in valid) | +0.095 / +0.264 | 2025-04-09 (81%) |

**Live adaptations** (new files in `live/`; the research modules are unchanged):
- All three: the live LabStrategy frame is one symbol-day without `symbol` / `date` columns and starts at 09:35; the
  research modules raise KeyError there. The live copies add those columns and ignore bars before 09:50 (as the
  history frames do). The breadth modules also return early when breadth never reached both <= 0.30 and the fire
  threshold (same output, ~5x faster). On the history frames these changes are no-ops: re-scored with
  `score_batch.py`, the live copies give **identical** results to the research modules (same trades, same R).
- WT bull flag exit: the live engine has no `S+ts2` geometry. The entry runs as `geom: S` with the runner's existing
  management `be_at_r: 0.5`, `time_stop_min: 10`, `time_stop_min_r: 0.01`. The runner measures the bailout from the
  entry price, not from the entry bar's high, so the live module sets `BAILOUT_REF_R = 0.01` (new scorer option) and
  was re-scored that way: **train +0.141R / valid +0.076R** (research exit: +0.108R / +0.113R) on the same 796 entries;
  best-day share 0.81 (was 0.73). This is a stated exit difference, not the identical setup.
- Universe: the scores use the lab universe (adv20 floor, no ATR% filter); live, the account universe also drops names
  with daily ATR < 1% of price. Breadth live is over the polled universe, in the history over the lab universe.

Re-score rows: `live/rescore.jsonl` (originals, live copies, and `pod-wt-flag-live-refentry` = the final WT live module;
the `...-long-live` WT row there predates `BAILOUT_REF_R`, i.e. it is the research exit on the live entry code).
The index module's live symbol fallback was added after that re-score; it only acts on the live placeholder symbol.

**Live-path parity** (`live/parity_live.py` -> `live/parity.json`; real 1-minute bars through
`LabStrategy.generate` with the YAML params, history context for the date; seed 20261023): thrasher 40/40 scored
signals on the same bar and 34/34 non-signal symbol-days silent; index ETFs 40/40 and 40/40; WT flag 39/39 and 37/37
(**100%** each). The first run found two harness / module issues, both fixed before this result: the index module's
symbol allow-list saw the live placeholder symbol (0/40), and LabStrategy.eligible's 390-bar gate rejected cache days
with missing minutes (the check now applies only its universe part).

**Gen poll time** (`research/ops/pollspeed1022_profile.py 2026-10-16 gen new 10:00,11:00`, replay lab universe ~1,060
contexts, same machine, before / after the three entries): 10:00 poll 127.2 s -> 134.8 s (+7.6 s), 11:00 poll
119.7 s -> 133.6 s (+13.9 s); setup masks +8.7 s / +8.8 s. Per call on a cached frame ~3-4 ms per symbol (WT ~3.6 ms on
the adv >= $20M names, thrasher ~2.9 ms on adv >= $500M names, index ETFs 4 symbols); the adv >= $20M frames are already
built every decision bar by existing GEN setups. Live polls ~3x more symbols, so expect roughly +20-40 s on a
5-minute-bar poll: still well under 5 minutes, but worth checking on the first session's poll log.

### Not added (5) and why
- **pod-aziz-zarattini-index-first-candle-direction-orb-10r-long**: needs the 20-session median opening-range width
  (`orw_med20`) from prior sessions' 09:30-10:00 bars; the live frame / priors do not carry it (new live data plumbing).
- **pod-bbt-vwap-reversal-no-new-5m-low-to-vwap-long**: needs day relative volume (cumulative volume vs its 20-session
  same-time mean); the live mask cannot see `DayContext.avg_cum_volume` (and that is a 14-session baseline) - plumbing.
- **pod-smb-20d-high-time-acceptance-long**: needs the 20-day daily high (research daily table; live priors keep only
  D-1) and SPY's VWAP distance from other symbols' rows (no `spy_vwap` context column exists).
- **pod-raschke-adx-gapper-short**: daily ADX(14) / DI from the research daily table; not available live.
- **pod-cwt4-gogolak-1000bar-sma-dip-vixrise-etf-long**: VIX daily closes, a 1000-bar (about 13-session) 5-minute SMA
  and SPY's daily SMA200; none available live.
The WT variants a1/a2/a3/ungated are the same idea (one version per idea: the plain breakout-or-bailout was taken).
Educational only - not financial advice.
