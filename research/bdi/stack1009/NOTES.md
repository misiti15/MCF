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
