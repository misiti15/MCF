# BDI stack study 2026-10-09: basic indicator stacks for live-probation candidates

*Educational only - not financial advice. Lab results on the 2-year history only; nothing here is a live result.*

Owner's order (2026-10-09): "BDI needs to work until at least 5 new setup options are available for live testing.
Keep things basic. Indicator on top of indicator on top of indicator."

**Section 1 (pre-declaration) was written on 2026-10-09 ~12:05 UTC, before any configuration of this study was scored.**
Results go in section 2 and may not change section 1.

## 1. Pre-declaration

### 1.1 Data and population
- Two-year frames `research/history2y/data/frames` via `research/history2y/lib.py` (open months only; the rule-19 locked
  block 2024-11-01..2025-02-28 is never loaded, `MCF_HIST_ALLOW_LOCKED` is never set). 426 open sessions, regimes from
  `lib.regimes()` (up / flat / down terciles of the universe median open-to-close).
- Population: point-in-time `adv20 >= 95,000,000` (the min_adv of every live lab setup), bars 09:50-15:00 (bar close).
- Entry: first qualifying 5-min bar per symbol-day inside the window, at that bar's close; R = 0.25 x daily ATR;
  exit at target / stop / 15:55; production costs (`gates.prod_r`). Same convention as `RESCORE.md`.
- Survivorship caveat as RESCORE.md (today's 1,226 names applied to the past).

### 1.2 Live parity (why only these building blocks)
The live LabStrategy frame (`heat_frame` + `setup_lab.extra_features`) carries close/high/low, rsi, rsi5, emaDiff,
macdPct, volumeRatio, vwapDistPct, buyPressure, fromOpen, gap, tod, atr_d, dist_pdh/pdl/hod/lod_atr, sma20/50 dist,
sma20 slope, flow3 - but **no volume, no open, only today's rows**. So:
- VWAP SD bands cannot be computed live (no volume) -> replaced by **VWAP stretch bands in daily ATR**:
  z = (close - VWAP) / atr_d, VWAP = close / (1 + vwapDistPct/100).
- EMA9/EMA21 position/slope individually, ADX/DI, CMF/OBV need warm-up history or volume -> replaced by emaDiff
  (EMA9 vs EMA21), sma20 slope (trend), buyPressure (19-bar signed volume share, the CMF/OBV proxy) and flow3.
- Prior-day VAH/VAL are not available live -> replaced by prior-day high/low (PDH/PDL).
- MACD histogram is not in the frame -> MACD line (macdPct) sign / zero cross.
- Opening range (09:30-10:00) high/low = the high/low of day at the 10:00 bar (close + dist_hod_atr x atr_d),
  carried forward within the symbol-day; OR triggers only from the 10:05 bar on.
- Crosses use the previous bar of the same symbol-day. The history frames start at the 09:50 bar, live has 09:35-09:45
  bars as well: a cross on the very first 09:50 bar can fire live but not in the scan (small, stated).

### 1.3 Triggers (12 families, each in both cross directions x both sides = 48 trigger-sides)
"up" event / "dn" event on this bar (prev bar on the other side):
1. vwap: z crosses 0.  2. ema: emaDiff crosses 0.  3. rsi14: up = rsi crosses above 30, dn = crosses below 70.
4. rsi5: up = crosses above 20, dn = below 80.  5. macd: macdPct crosses 0.  6. or: up = close crosses above OR high,
dn = crosses below OR low.  7. sma50: close crosses its 5-min SMA50.  8. sma20: crosses SMA20.
9. pdbrk: up = crosses above PDH, dn = crosses below PDL.  10. pdfail: up = crosses back above PDL (reclaim),
dn = crosses back below PDH (failed breakout).  11. band05 / 12. band10: up = z crosses back above -k
(touch-and-close-back-inside of the lower band), dn = z crosses back below +k; k = 0.5 / 1.0 ATR.
Each event is paired with side long and short (with = momentum, against = fade).

### 1.4 Filter menu (side-relative; s = +1 long / -1 short; ~30 variants)
vwap_with / vwap_against (s*z > 0 / < 0); ema_with / against (s*emaDiff); sma50_with / against; slope20_with /
against (s*sma20_slope_pct); macd_with / against; bp_with / against (s*buyPressure); flow3_with / against;
vol>=1.5 / vol>=2.0 (volumeRatio); fo_with_1 / fo_with_3 (s*fromOpen > 1 / 3); fo_against_1 / fo_against_3
(s*fromOpen < -1 / -3); gap_with / gap_against (s*gap > 1 / < -1); rsi_ext (fade extreme: short rsi >= 70, long
rsi <= 30); rsi5_ext (short rsi5 >= 80, long <= 20); rsi_with50 (s*(rsi-50) > 0); stretch_small (|z| < 0.5);
near_ext (long dist_hod_atr < 0.25 / short dist_lod_atr < 0.25); pd_out_with (long close > PDH / short < PDL);
pd_inside (PDL <= close <= PDH).
Threshold grids for the plateau check: volumeRatio {1.25, 1.5, 2, 2.5, 3}; fromOpen {0.5, 1, 2, 3, 4};
gap {0.5, 1, 2}; rsi_ext {60, 65, 70, 75, 80}; rsi5_ext {70, 75, 80, 85, 90}; stretch_small {0.25, 0.5, 0.75, 1.0};
near_ext {0.1, 0.25, 0.5}; triggers rsi14 30/70 -> {25, 30, 35}; rsi5 20/80 -> {15, 20, 25}; band k {0.25..1.25 step 0.25}.

### 1.5 Windows and exits
am 09:50-11:30, mid 11:35-13:30, pm 13:35-15:00 (bar close). Exits t1s1, t05s1, t1s05.

### 1.6 Search (stage-wise, greedy; every evaluated configuration is counted)
- Robust score = min(day-clustered t in up sessions, in down sessions); used only for ranking within the search.
- Stage 1: 48 trigger-sides x 3 windows x 3 exits = 432 configurations.
- Stage 2: the 20 best stage-1 (trigger-side, window) pairs by robust score (n >= 300) x every filter x 3 exits.
- Stage 3: the 30 best stage-2 stacks by robust score (n >= 200) x every third filter x 3 exits.
- Further rounds (new trigger families, YouTube-digest / MarcoFlow ideas as simple stacks) are added and counted the
  same way; their count is reported.
- Plateau neighbours evaluated for the finalists are counted too.
- N for t_required = total configurations of this study + the RW6 lineage is not mixed in (separate lineage).

### 1.7 Live-probation criterion (pre-declared; all must hold)
n >= 150 over the open 2 years; exp R > 0 after costs in up AND down sessions (flat reported, also > 0 if n_flat
>= 30); day-clustered t >= 2.0 overall; walk-forward positive-fold share >= 0.6 (`gates.walk_forward`, locked months
excluded); plateau: mean exp of the one-step neighbours of every threshold > 0 (and none of the neighbours worse than
-0.05R mean per threshold pair); ex-best-day exp > 0. Trades/day reported. t vs t_required(N) reported honestly - these
are LIVE-PROBATION candidates, not "keep".
Diversity: candidates are chosen best-first by overall t among those meeting the criterion, skipping one whose
trigger family + side + window equals a chosen one or whose symbol-day overlap with a chosen one exceeds 30%.
RW6 + G1k2 (trendguard, +0.264R n 424 t 2.39) is listed for comparison (not re-scored here; it needs volume).

### 1.8 Amendment A (2026-10-09 12:20 UTC, after the first scan pass of 7,062 configurations; those count)
The first pass was dominated by one session: the top stack (band10-dn short am, n 211, "t 8.4") had 156 of its 211
trades on 2025-04-07 (tariff crash day) - the day-clustered SE understates noise when one session carries most trades.
Changes, declared before the second pass was scored:
- Search ranking (not a gate) = min(day-level t in up sessions, in down sessions), where day-level t treats each
  session's mean R as one observation (equal weight per day); a stack whose busiest session holds > 10% of its trades
  gets rank -9.
- Beams keep at most 2 entries per trigger family + side in stage 1 (beam 24) and 3 in stages 2-3 (beam 30) (diversity).
- Criterion 1.7 gains one stricter gate: the busiest session holds <= 10% of the trades. Day-clustered t (gates.summary)
  stays the t gate; day-level t is reported too.
- N for t_required counts both passes plus every finalist re-score and plateau neighbour.

### 1.9 Amendment B (2026-10-09 12:25 UTC, after pass 2 of 7,338 configurations; those count)
Pass 2 left only 6 stacks meeting the cheap gates (n, up > 0, down > 0, t >= 2, busiest day <= 10%); stage-1 ranking
is negative everywhere, so a narrow greedy beam is too myopic. Pass 3 (same triggers, filters, windows, exits, gates):
- Stage 2 is exhaustive: every one of the 144 trigger-side x window combinations x every filter x 3 exits.
- Stages 3 and 4 keep beams of 100 (at most 8 per trigger family + side).
- All three passes are counted in N.

### 1.10 Amendment C (2026-10-09 12:32 UTC, after pass 3 of 29,016 configurations; those count)
Pass 3's survivors all carry a big move from the open (|fromOpen| > 3%), the same shape as the RW6 lead (big movers
are idiosyncratic, so less tied to the session regime). Pass 4 makes that the base layer: first filter forced to one
of fo_with 2 / fo_with 3 / fo_against 2 / fo_against 3, then every trigger-side x window x second filter x 3 exits
(exhaustive), then a beam of 100 (at most 8 per trigger family + side) x third filter x 3 exits. Same gates; counted.

### 1.11 Amendment D (2026-10-09 12:42 UTC, after pass 4 of 54,858 configurations; those count)
Passes 1-4 give 4 diverse stacks meeting 1.7 (11 passers, 4 after the diversity rule). Pass 5 adds 6 new basic trigger
families (both cross directions x both sides), searched as pass 3 (stage 1 all, stage 2 exhaustive, stages 3-4 beam
100, at most 8 per family + side), same filters, windows, exits, gates; counted:
13. hodlod: up = close makes a new high of day (dist_hod_atr == 0, previous bar below its HOD); dn = new low of day.
14. rsi50: RSI(14) crosses 50.  15. volspike: volumeRatio crosses up through 2.0 (up = on a bar closing above VWAP,
dn = below VWAP).  16. fo3: fromOpen crosses +3% (up) / -3% (dn).  17. slope20: SMA20 slope crosses 0.
18. flow3: flow3 (3-bar signed volume share) crosses +0.5 (up) / -0.5 (dn).

## 2. Results (appended 2026-10-09 ~12:55 UTC; section 1 unchanged except the dated amendments A-D)

*Lab results on the open 2-year history only (backtest, not live, not paper). Educational only - not financial advice.*

### 2.1 Failures first

- **No stack clears the try-count bar.** Configurations evaluated: 120,375 (pass 1 7,062; pass 2 7,338; pass 3 29,016; pass 4 54,858; pass 5 21,951; finalist re-scores and plateau neighbours ~275). t_required = sqrt(2 ln N) = 4.837; the best day-clustered t found is 2.66. With ~120k tries, a best t of ~2.7 is what noise alone would be expected to produce, so these are **live-probation candidates whose edge is unproven**, not 'keep'.
- Pass 1 was dominated by one session (2025-04-07: 156 of 211 trades of the top stack, 't 8.4'); amendment A added the busiest-day <= 10% gate.
- Only 23 of 29 stacks that met the cheap gates (n >= 150, up > 0, down > 0, t >= 2, busiest day <= 10%) also met walk-forward >= 0.6, plateau and ex-best-day; all are listed in `finalists.csv` (failures included). 8 survive the diversity rule.
- Every candidate has a big move from the open (6 of 8: > 3%) as a layer: the regime-robust shape is idiosyncratic big decliners, as with the RW6 lead. The big-move layer alone is negative (baseline column), so the trigger/stack does the work in-sample - or the search found the lucky subsets.
- Trades/day are small (0.4-1.0); together ~4.8/day before overlap.
- ST1 module vs scan: 395 vs 403 trades (+0.091R t 2.53 vs +0.094 t 2.66): the scan stored the opening-range level in float32, so an exact-touch prior bar was misclassified; the module (float64, the live code) is the reference. ST2-ST8 reproduce exactly. Every module gives identical masks on a single symbol-day without symbol/date columns (live-frame shape), 840/840 checks.
- Not done: no locked-block scoring (the lead does it once); RW6+G1k2 not re-scored here (needs volume-weighted VWAP SD, not in the live frame).

### 2.2 Candidate table (module numbers; scan numbers where identical)

| ID | layers | side/exit | window | n | /day | win | exp R | t | t req | up exp (n) | flat exp (n) | down exp (n) | WF + share | plateau mean (min) | ex-best-day | overlap live | max overlap other cands | random-bar baseline | big-move layer alone |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ST1-ordn-long-pm-t05s1 | close crosses below the 09:30-10:00 opening-range low; stock down > 3.0% from the open; volume ratio >= 1.5; close inside the prior-day range | long/t05s1 | 1335-1500 | 395 | 0.93 | 0.6987 | +0.091 | 2.53 | 4.837 | +0.169 (70) | +0.017 (126) | +0.109 (207) | 0.8 | +0.069 (+0.037) | +0.081 | 0.432 | 0.025 | -0.072 | -0.009 (n 31918) |
| ST2-slope20up-long-am-t05s1 | 5-min SMA20 slope turns positive; stock down > 3.0% from the open; 19-bar buy pressure > 0; close within 0.5 daily ATR of VWAP | long/t05s1 | 950-1130 | 164 | 0.38 | 0.7683 | +0.128 | 2.43 | 4.837 | +0.086 (52) | +0.208 (62) | +0.072 (50) | 0.6 | +0.090 (+0.003) | +0.110 | 0.665 | 0.146 | -0.075 | -0.074 (n 29574) |
| ST3-rsi5up-short-pm-t1s1 | RSI(5) crosses back above 20; stock down > 3.0% from the open; close above VWAP; gap up > 1.0% | short/t1s1 | 1335-1500 | 358 | 0.84 | 0.5866 | +0.106 | 2.35 | 4.837 | +0.056 (93) | +0.152 (148) | +0.087 (117) | 0.769 | +0.094 (+0.031) | +0.086 | 0.539 | 0.168 | -0.074 | -0.119 (n 31918) |
| ST4-emadn-long-am-t1s05 | EMA9 crosses below EMA21; stock down > 3.0% from the open; RSI(14) > 50; RSI(5) <= 20 | long/t1s05 | 950-1130 | 168 | 0.39 | 0.4881 | +0.157 | 2.29 | 4.837 | +0.386 (37) | +0.130 (58) | +0.063 (73) | 1.0 | +0.126 (+0.008) | +0.129 | 0.708 | 0.048 | -0.091 | -0.074 (n 29574) |
| ST5-pdbrkup-short-mid-t05s1 | close crosses above the prior-day high; stock down > 3.0% from the open; close above the 5-min SMA50 | short/t05s1 | 1135-1330 | 162 | 0.38 | 0.7099 | +0.107 | 2.17 | 4.837 | +0.125 (34) | +0.052 (64) | +0.153 (64) | 0.833 | +0.091 (+0.033) | +0.087 | 0.753 | 0.123 | -0.065 | -0.037 (n 32044) |
| ST6-volspikeup-short-mid-t1s1 | volume ratio crosses above 2.0 on a bar closing above VWAP; stock down > 3.0% from the open; gap up > 1.0% | short/t1s1 | 1135-1330 | 222 | 0.52 | 0.5856 | +0.126 | 2.15 | 4.837 | +0.015 (60) | +0.180 (86) | +0.154 (76) | 0.857 | +0.139 (+0.068) | +0.102 | 0.473 | 0.27 | -0.075 | -0.034 (n 32044) |
| ST7-rsi50dn-long-pm-t1s1 | RSI(14) crosses below 50; RSI(14) <= 30; stock down > 1.0% from the open; 19-bar buy pressure > 0 | long/t1s1 | 1335-1500 | 166 | 0.39 | 0.5904 | +0.162 | 2.02 | 4.837 | +0.192 (34) | +0.095 (51) | +0.192 (81) | 0.714 | +0.097 (-0.003) | +0.104 | 0.205 | 0.012 | -0.084 | -0.037 (n 117162) |
| ST8-volspikedn-long-pm-t1s1 | volume ratio crosses above 2.0 on a bar closing below VWAP; stock down > 3.0% from the open; MACD line above 0; 3-bar signed-volume share > 0 | long/t1s1 | 1335-1500 | 408 | 0.96 | 0.5515 | +0.107 | 2.01 | 4.837 | +0.126 (74) | +0.198 (162) | +0.012 (172) | 0.786 | +0.050 (+0.024) | +0.080 | 0.515 | 0.025 | -0.084 | +0.007 (n 31918) |
| RW6+G1k2 (trendguard, comparison) | NS2 SMA50 break up while RSI >= 60, up > 3% from open; no short while a +2 SD VWAP excursion is unresolved | short/t1s1 | 950-1130 | 424 | 3.97* | - | +0.264 | 2.39 | 4.757 | +0.318 | - | +0.082 | 0.625 | G1k1 -0.02 (no plateau) | - | high (NS2 lineage) | - | - | - |

*RW6+G1k2 numbers from trendguard NOTES (trades/day there is per active session); not computable on the live frame (no volume).

Up/flat counts are scan counts; ST1 regime counts differ by a few trades from the module. Window = bar close ET. All modules: min_adv 95,000,000.

### 2.3 Modules
`research/bdi/stack1009/modules/ST1..ST8-*.py` (SIDE, GEOM, LAYERS, mask(df); live-frame columns only; VWAP from vwapDistPct, VWAP stretch / OR / PDH / PDL from the *_atr distance columns, prev-bar respects symbol-day boundaries). Backlog: `bdi-st-st1..st8-*` (status testing, lab_module set).


## Locked block (rule 19), scored ONCE by the lead 2026-10-09 ~09:00 ET (`score_locked.py`, `locked.json`)
Bar (look 1): exp > 0 and t >= 1.0 after costs. Passes: **ST3** (+0.257R, t 1.72, n 57, ex-best-day +0.187, up +0.17 /
down +0.56) and **ST5** (+0.156R, t 1.10, n 21 - small, down sessions -0.23). Fails: ST1 -0.045, ST2 -0.033, ST4 -0.166,
ST6 +0.113 (t 0.55), ST7 -0.115, ST8 -0.088. RW6G1 (live since 2026-10-09): -0.209R, t -1.11, n 27 (up -0.43 / down +0.60).
Educational only - not financial advice.
