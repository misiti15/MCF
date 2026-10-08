# BDI - owner video digest: price-structure setups (2026-10-08)

*Educational only - not financial advice. Backtest (lab) results only; nothing here was tested live.*

## 0. Pre-declared grid (written 2026-10-08 14:59 UTC, BEFORE any feature was computed or any configuration scored)

### Data and split
- Setup-lab frame `research/setups2/data/{train,valid}.parquet`: train 2026-06-30..08-25 (40 sessions), valid 2026-08-26..09-15 (14 sessions).
- New columns are built from `data/cache/1Min`, read with the parquet filter `timestamp < 2026-09-16`. No later row is loaded. `data/cache_q2` is not touched and no `MCF_*_ALLOW_*` variable is set.
- Rows are joined to the lab frame on (symbol, date, tod); tod is the 5-minute bar close and runs 09:50-15:00.
- **Live parity.** Every feature for bar i of day D uses only the following:
  - D's 1-minute bars up to the close of bar i
  - the prior 40 five-minute bars, as `ctx.prior5`
  - the prior session's 1-minute bars, used for the prior-day volume profile and the prior-day anchors
  - the prior 14 sessions' cumulative volume by minute, as `ctx.avg_cum_volume` (min 5 sessions)
  - prior daily closes
- A truncation test checks this: features computed on a truncated day must equal the full-day features at every bar before the cut.

### Scoring
- First qualifying bar per symbol-day.
- **Lab geometries** t1s1, t05s1 and t1s05:
  - Entry at the signal bar's 5-minute close. R = 0.25 x daily ATR (the frame's `atr_d`). Exits by 15:55.
  - Production haircut subtracted: (2 x 1 bps x price + 0.02) / R, on top of the lab's 1c per side.
- **Structural exits**, simulated on 1-minute bars:
  - Market entry at the open of the next 1-minute bar after the signal bar closes. The block limit entry is the one exception.
  - Costs: 1c + 1 bps against us on each side, plus an extra 2c on stop fills.
  - Stops are checked first inside a bar. A gap through a stop fills at the bar's open.
  - Every trade is flat by 15:55 at the 15:55 bar's open. P/L is reported in the same R.
- Day-clustered t, halves of train by calendar, ex-best-day expectancy, valid green-day share.
- Windows (bar close): am 09:50-11:30, pm 11:30-15:00, all 09:50-15:00.
- Configurations with train n < 60 are counted as tried but not scored.

### Source mapping -> triggers (long described; every short is the exact mirror)
| fam | source | trigger (bar i, 5-minute) | declared variants |
|---|---|---|---|
| MP | Ross Cameron micro-pullback | trend: close > VWAP, close > EMA9, EMA9 > VWAP; a pullback run of 1..kmax consecutive bars before i, each with high <= the previous bar's high, every pullback close >= VWAP; a pullback low touched the level (low - level <= 0.02 ATR); trigger: high_i > high_{i-1} (first candle making a new high) | touch {e9, vw, any} x kmax {1,2,3} x vol {any, light: mean pullback-bar volume < 1.0 x mean volume of the 3 bars before the run} = 18 |
| VT | Ross Cameron "volume top", used as an entry (short at a top, long at a bottom) | short: high_i >= today's high before bar i, upper wick >= 0.5 x range, and volume_i either >= the largest earlier 5-minute volume today (peak) or volumeRatio >= 2 (vr2) | {peak, vr2} = 2 |
| JD | Jdub 9 EMA + VWAP trend ride | close > VWAP, EMA9 > VWAP, low_i <= EMA9 + 0.02 ATR and close_i >= EMA9 (touch, no close below) | trend {any, strong: >= 80% of today's 5-minute closes so far above VWAP} = 2 |
| VA | Fractal Flow value-area re-entry (80%-rule style) | opened below the prior-day VAL (70% value area, contiguous expansion from the POC, 1-minute profile); close_i between VAL and POC | {cross1: close_{i-1} <= VAL; cross2: closes i and i-1 inside, close_{i-2} <= VAL; inside: no cross needed} = 3 |
| BLK | Trader Dale accumulation-block POC retest | the latest block = L consecutive 5-minute bars whose range <= c x ATR (today only); a breakout close above the block high; price then extends >= 0.25 ATR beyond the block high; first retest bar with low_i <= block POC and close_i >= block POC | L {6,12} x c {0.3,0.5} = 4 |
| LVN | Fractal Flow LVN air pocket | close_i > the highest high of the prior 6 bars, and the air ahead (mean composite-profile volume per bin over (close, close + 0.5 ATR]), divided by the POC-bin volume, is < a. The composite profile is the prior day plus today so far, from 1-minute bars | a {0.15, 0.30} = 2 |
| AVR | Jumpstart anchored-VWAP first retest | anchor {open (= gap bar), pdhv (prior day's highest-volume 1-minute bar), pdh (prior-day high bar), pdl (prior-day low bar), tdhv (today's highest-volume 1-minute bar after 09:35, so far)}. Price has already been >= 0.3 ATR above that AVWAP today; the first bar after that with low_i <= AVWAP + 0.02 ATR and close_i > AVWAP | anchor x delta {any, green: close_i > open_i} = 10 |
| AVF | Jumpstart AVWAP +2 SD fade | short when high_i >= AVWAP + k x sigma (volume-weighted SD since the anchor) and volume_i < volume_{i-1} (fading volume); long mirror at -k sigma | anchor (5) x k {2.0, 2.5} = 10 |

Per side: 18 + 2 + 2 + 3 + 4 + 2 + 10 + 10 = **51 triggers**. Both sides: **102**.

### Exits assigned per family
- **lab3** = t1s1, t05s1, t1s05.
- **jd** (Jdub stop):
  - Exit after a 5-minute close below the closer of EMA9 and VWAP, i.e. below max(EMA9, VWAP) for a long.
  - The exit fills at the next 1-minute open.
  - Hard stop at 2R.
- **e9c1:** Exit after a 1-minute close below the 1-minute EMA9 (seeded at 09:30). Hard stop at 2R.
- **vt** (Ross):
  - Stop 1c beyond the extreme of bars i-2..i (the pullback low).
  - Exit after the next volume-top 5-minute bar: new HOD, upper wick >= 0.5, volume = today's peak.
- **vt9:** vt plus an exit on a 5-minute close below EMA9.
- **tx:** Hold to 15:55, with a hard stop at 2R.
- **poc / poc2:**
  - Target the prior-day POC (poc) or the opposite VA edge (poc2).
  - Stop 1c beyond the session extreme so far.
  - NaN when the target is not ahead of the entry.
- **avw:**
  - Target is a touch of that anchor's AVWAP line; the stop is 1R.
  - NaN when the AVWAP is not ahead of the entry.
- **blk:**
  - A limit order at the block POC is placed at the close of the bar where the extension completes.
  - It fills on the first later 1-minute bar with low <= POC, at min(open, POC).
  - Stop 1c beyond the block VAL (the HVN edge). Target the post-breakout extreme.
  - The order is cancelled on a 5-minute close below the VAL, or at 15:00.

| fam | exits | per-side trigger x exit |
|---|---|---|
| MP | lab3, jd, e9c1, vt, vt9, tx (8) | 18 x 8 = 144 |
| VT | lab3, jd, e9c1, tx (6) | 2 x 6 = 12 |
| JD | lab3, jd, e9c1, vt9, tx (7) | 2 x 7 = 14 |
| VA | lab3, poc, poc2, jd, tx (7) | 3 x 7 = 21 |
| BLK | lab3 (entry at the retest close), blk (4) | 4 x 4 = 16 |
| LVN | lab3, jd, e9c1, tx (6) | 2 x 6 = 12 |
| AVR | lab3, jd, e9c1, tx (6) | 10 x 6 = 60 |
| AVF | lab3, avw, e9c1 (5) | 10 x 5 = 50 |

Per side: 329 trigger-exit pairs. Both sides: **658**.

### Layers (16; side-aligned unless marked)
| layer | rule |
|---|---|
| rvol15 / rvol2 | cumulative RVOL >= 1.5 / >= 2.0 (today's cumulative volume to the bar close vs the prior-14-session average at that minute) |
| vwap_with / vwap_against | close on / against the trade side of the session VWAP |
| e9_with | close beyond the 5-minute EMA9 on the trade side |
| m15_with | last completed 15-minute close beyond its 15-minute EMA9 AND beyond VWAP on the trade side (Jdub multi-timeframe) |
| rsi5_hi / rsi5_lo | RSI(5) >= 70 / <= 30 (not side-aligned) |
| flowsell / flowbuy | buyPressure < -0.25 / > 0.25 (not side-aligned; MarcoFlow opening flow) |
| gap_with / gap_against | gap >= 1% in / against the trade direction |
| gapper | abs(gap) >= 2% (Ross gappers) |
| orb_with | close beyond the 15-minute opening range (09:30-09:45) on the trade side |
| dsma20_with | close beyond the daily SMA20 of prior closes on the trade side. This is the proxy for Ross's daily 200 EMA, which is untestable: the cache starts 2026-06-15, so there are at most about 65 daily bars |
| pdroom | long: close > PDH or PDH - close >= 0.5 ATR (no overhead prior-day resistance within 0.5 ATR); short mirror at PDL |

Combos: none (L0) 1, single layers (L1) 16, and pairs (L2) C(16,2) = 120 minus 5 dropped pairs = 115. The dropped pairs are vwap_with+vwap_against, rsi5_hi+rsi5_lo, flowsell+flowbuy, gap_with+gap_against and rvol15+rvol2. That gives **132 layer sets**.

### Total declared
658 trigger-exit pairs x 132 layer sets x 3 windows = **260,568 configurations**, plus the plateau neighbours (counted).
At p = 0.05, roughly 13,000 configurations would look positive on valid by chance alone.

### Gates (fixed in advance)
1. train exp > 0 and valid exp > 0, after costs
2. valid n >= 30
3. valid day-clustered t >= 1.5
4. both train halves > 0
5. edge over the same-side, same-window random baseline > 0 on train and valid. The baseline is every bar in the window under the same exit:
   - lab3, jd, e9c1, vt, vt9, tx: the identical exit applied to every bar
   - poc, poc2, avw: every bar where the target is ahead
   - blk: the lab t1s05 baseline (the closest geometry; a stated approximation)
6. plateau positive: the mean train AND mean valid expectancy of the neighbours > 0, and >= 2/3 of the neighbours positive on valid
7. valid ex-best-day expectancy reported (not a gate)

### Plateau neighbours (pre-declared)
- **Trigger parameters:**
  - MP: kmax +-1, touch tolerance 0.0 / 0.05 ATR, light-volume ratio 0.75 / 1.25.
  - VT: wick 0.4 / 0.6; vr2 -> 1.5 / 2.5.
  - JD: touch tolerance 0.0 / 0.05; strong 70% / 90%.
  - VA: value area 60% / 80%.
  - BLK: the other L, the other c, and extension 0.15 / 0.40 ATR.
  - LVN: a one step (0.10 / 0.20 / 0.40 around the base), lookahead 0.25 / 0.75 ATR.
  - AVR: departure 0.2 / 0.5 ATR.
  - AVF: k 1.5 / 3.0 (and 2.0 <-> 2.5).
- **Layer thresholds:**
  - rvol 1.25 / 1.5 / 2.0 / 2.5
  - RSI5 65 / 75 (35 / 25)
  - flow -0.15 / -0.35 (+0.15 / +0.35)
  - gap 0.5 / 1.5 (gapper 1.5 / 3)
  - pdroom 0.25 / 0.75
- **Window:** am <-> all, pm <-> all.

### Finalists
- At most 8, chosen by min(train t, valid t) among the configurations that pass every gate.
- Duplicate masks (the same trades) are collapsed.
- Each finalist gets a `type: lab` module (SIDE, GEOM, LAYERS, REQUIRES, mask(df)).
- Finalists with structural exits are flagged: LabStrategy cannot run those exits today.

## 0b. Volume II amendment (declared 2026-10-08 ~15:25 UTC, still BEFORE any configuration was scored)

The owner added `SOURCE_owner_pdf_vol2.txt` (videos 6-15). Its "Volume II Technical Synthesis Matrix" gets extra weight: each matrix row becomes a named family, tested faithfully (no layers) and layered.
- The features come from a second pass, `build2.py` / `features2.py`. That pass is causal; the truncation test passed.
- Section 0 is amended below. Everything not mentioned stays as declared: data, costs, gates and windows.

**Anchors available before 2026-09-16 (no look-ahead):**
- **pwh / pwl:** the highest-high / lowest-low 1-minute bar of the previous calendar week.
- **gap:** the open bar of the latest prior session with abs(gap) >= 2%.
- **qop:** the first session of the day's calendar quarter (2026-07-01).
  - If the day is itself that session, or the quarter began before the cache, the anchor is the cache start (2026-06-15). This affects only 06-30 and 07-01.
  - A **year-open** anchor is impossible because the cache starts 2026-06-15; the quarter open stands in for it.
- **Earnings anchor:** not derivable. There is no earnings calendar in the data, so it was not tested.

**Delta proxy (no footprint data):**
- dlt = sum over the bar's 1-minute bars of sign(close - previous 1-minute close) x volume, divided by the bar's volume (tick rule, range -1..1).
- The first minute of the session is compared with the prior session's last close.
- This is a crude stand-in for bid/ask footprint delta.

**Flat-VWAP filter:**
- vsl = abs(VWAP_i - VWAP_{i-6}) / ATR, i.e. the VWAP move over the last 30 minutes in daily-ATR units.
- The "> 30 degrees" rule depends on chart scale and has no unit-free meaning.
- Threshold 0.03 (neighbours 0.015 / 0.06). This was set from the feature's distribution alone, before any outcome was looked at: about the 70th percentile, median 0.014.

### Matrix families (long described, short = mirror)
| fam | matrix row / video | trigger | variants |
|---|---|---|---|
| IC | Institutional Confluence (SMB #6) | session VWAP within tol% of a multi-day AVWAP (anchor pwh/pwl/gap/qop). Level = the far side of the two lines: max(VWAP, AVWAP) for a long. **bounce:** previous close above the level, low_i <= level, close_i > level. **break:** previous close <= level, close_i > level | anchor 4 x tol {0.1, 0.2, 0.3}% x {bounce, break} = 24 |
| ENVF | Mean Reversion Envelopes (Wysetrade #7) | short: high_i >= VWAP + 2 SD (session VWAP / volume-weighted SD from 1-minute bars) on dropping volume | drop {1bar: v_i < v_{i-1}; vr: volumeRatio < 1} = 2 |
| ENVC | Wysetrade continuation | strong trend (>= 80% of closes above VWAP); low_i <= level + 0.02 ATR and close_i > level, level in {+1 SD, VWAP}; surging RVOL {cum: rvol >= 1.5; bar: volumeRatio >= 1.5} | 4 |
| SWP | Microstructure Sweeps (Conti #8) | the previous close was above VWAP; a bar within the last m bars (incl. i) pierced VWAP by >= x ATR; closes stayed outside until bar i, which closes back above VWAP with dlt > 0 | x {0.05, 0.10, 0.20} x m {1, 2, 3} = 9 |
| OFP | Order Flow Precision (PAVT #10) | WHERE: **hvnedge** = low in an HVN (density >= 0.5 x POC) with an LVN below (mean density over the next 0.25 ATR < 0.3); **lvnedge** = low probed an LVN (density < 0.3) and the close is in the upper half of the bar. WHEN: **aggr** dlt >= 0.3; **absorb** dlt <= 0 with close >= open | 2 x 2 = 4 |
| DCN | Dual Confluence Nodes (Mind Math Money #9) | a new LAYER on every family: abs(session VWAP - today's session-profile POC) / VWAP <= 0.2% | (layer) |

### Other Volume II rules
| fam | source | trigger | variants |
|---|---|---|---|
| BK | BKTraders 9-EMA ride (#11) | EMA9 > EMA20; low_i <= EMA9 + 0.02 ATR; close_i >= EMA9 | {trend; trend + close beyond VWAP} = 2 |
| VA30 | Data Trader 80% rule (#14), as stated | opened outside the prior-day 70% VA; the last two completed 30-minute bars (from 09:30) are inside | {close: both closes inside; full: both ranges inside} = 2 |
| PINCH | TheOneLanceB anchor pinch (#13) | abs(AVWAP_qop - AVWAP_gap) / close <= p%; close breaks above both (previous close <= the higher one) with dlt > 0 (order-flow direction) | p {0.25, 0.5} = 2 |
| PWR | Trader Dale prior-week AVWAP (#12) | first retest of the pwh / pwl AVWAP (same rule as AVR: 0.3 ATR departure, first touch holds). The source uses a limit order; here the entry is at the touch bar's close | anchor 2 x delta {any, green} = 4 |

### New exits
- **c9:** exit at the next open after a 5-minute close beyond EMA9. Hard stop at 2R.
- **trail9** (BKTraders):
  - The stop starts 1c beyond the signal candle's extreme.
  - It trails candle by candle to each later completed 5-minute bar's low (long) or high (short).
  - Also exits on a 5-minute close beyond EMA9.

| fam | exits | per-side pairs |
|---|---|---|
| MP | Vol I exits + c9, trail9 (10) | 180 |
| JD | Vol I exits + c9, trail9 (9) | 18 |
| VT, VA, BLK, LVN, AVR, AVF | unchanged | 12 + 21 + 16 + 12 + 60 + 50 = 171 |
| IC | lab3, jd, e9c1, tx (6) | 144 |
| ENVF | lab3, avw (target the session VWAP), e9c1 (5) | 10 |
| ENVC | lab3, jd, c9, trail9, tx (7) | 28 |
| SWP | lab3, jd, e9c1, tx (6) | 54 |
| OFP | lab3, jd, e9c1, tx (6) | 24 |
| BK | lab3, trail9, c9, tx (6) | 12 |
| VA30 | lab3, poc2 (opposite edge = the rule's target), poc, tx (6) | 12 |
| PINCH | lab3, jd, e9c1, tx (6) | 12 |
| PWR | lab3, jd, e9c1, tx (6) | 24 |

Per side: 369 (Vol I families) + 320 (Vol II) = 689. Both sides: **1,378 trigger-exit pairs**.

### Layers (now 18)
- The 16 layers of section 0, plus:
  - **dcn:** VWAP-POC within 0.2% (neighbours 0.1 / 0.3)
  - **vslope:** vsl >= 0.03 (neighbours 0.015 / 0.06)
- Layer sets: none 1 + single 18 + pairs C(18,2) = 153 minus the 5 dropped pairs = 148, so **167 layer sets**.

### Total declared (supersedes section 0's total)
1,378 x 167 x 3 = **690,378 configurations**, plus the plateau neighbours. At p = 0.05, roughly 35,000 configurations would come out positive by chance alone.

### Plateau neighbours for the new families
| family | neighbours |
|---|---|
| IC | the adjacent tolerance |
| ENVF / ENVC | k 1.5 / 2.5 (ENVF); strong 70% / 90%; surge threshold 1.25 / 2.0 |
| SWP | adjacent x; adjacent m; dlt threshold 0.1 |
| OFP | density 0.4 / 0.6; LVN 0.2 / 0.4; dlt 0.2 / 0.4 |
| BK | tolerance 0.0 / 0.05 |
| VA30 | VA 60 / 80 |
| PINCH | adjacent p (0.1 / 0.25 / 0.5 / 1.0) |
| PWR | departure 0.2 / 0.5 |
| dcn / vslope | as listed above |

---

## 1. Sources mapped, and what could not be tested
- **Volume I:**
  - Ross Cameron: micro-pullback (MP) and volume top (VT, also used as an exit).
  - Trader Dale: accumulation-block POC retest (BLK).
  - Fractal Flow: value-area re-entry (VA) and LVN air pocket (LVN).
  - Jumpstart: AVWAP first retest (AVR) and +2 SD fade (AVF).
  - Jdub: EMA9 + VWAP ride (JD).
  - RVOL appears as a layer everywhere.
- **Volume II matrix:**
  - Institutional Confluence (IC)
  - Mean Reversion Envelopes (ENVF fade, ENVC continuation)
  - Microstructure Sweeps (SWP)
  - Dual Confluence Nodes (the dcn layer)
  - Order Flow Precision (OFP)
- **Other Volume II rules:**
  - BKTraders 9-EMA ride (BK) with the trail9 exit
  - the 80% rule as stated (VA30)
  - Flat-VWAP filter (the vslope layer)
  - anchor pinch (PINCH)
  - prior-week AVWAP first retest (PWR)
- **Not testable, so logged as backlog ideas:**
  - Daily 200 EMA. The cache starts 2026-06-15, so there are fewer than 70 daily bars; the daily SMA20 was used as a proxy.
  - Earnings and catalyst anchors: there is no earnings calendar.
  - Year-open anchor: the quarter open was used instead.
  - Footprint delta: a tick-rule proxy from 1-minute bars was used instead.
  - Low-float gappers: there is no float data. The universe is the cache's 1,226 names, mostly liquid.
  - 1-minute entries: LabStrategy evaluates 5-minute bars, so only 5-minute triggers were scored. Exits were simulated on 1-minute bars.

## 2. What was built
- **`features.py` / `features2.py`:**
  - Causal per-day feature functions.
  - About 190 columns plus 61, covering EMAs, pullback runs, volume tops, 15-minute alignment, cumulative RVOL, the prior-day and composite 1-minute volume profiles, 9 AVWAP anchors with SD, block state machines, sweeps, the delta proxy, the session POC, VWAP slope, and 30-minute value-area bars.
  - A truncation test (`build.py --test-causal`, `build2.py --test-causal`) recomputes every column on days cut at 4 points and requires equality with the full-day values. It passed.
- **`build.py` / `build2.py`:**
  - Features plus structural outcomes for 1,226 symbols x 54 sessions.
  - Exits are simulated with numba on 1-minute bars.
  - Read filter: `timestamp < 2026-09-16`.
  - The rows match the lab frame exactly: close, the VWAP distance (max diff 1e-5 %), atr_d and the upper wick are identical.
  - 248 lab rows were dropped: 11 symbol-days (BWET 08-05 and 10 VEEA days) have fewer than 60 one-minute bars.
- **`vid_rules.py`:** every trigger and layer, in numpy only. The scanner and the lab modules call the same code.
- **`scan.py` / `report.py` / `gen_modules.py` / `finalist_check.py`:** scoring, tables, modules and the extra finalist checks.

## 3. Counts
| item | count |
|---|---|
| Declared (section 0 + 0b) | **690,378** |
| Scored (train n >= 60) | 520,014 |
| Counted but unscored (train n < 60) | 170,364 |
| Plateau neighbours scored | 2,106 |
| **Total tried** | **692,484** |
| Lineage context: earlier BDI article grid today | 23,868 |

Gate funnel (cumulative, over scored configurations):

| gate | passing |
|---|---|
| train > 0 | 17,719 |
| + valid > 0 | 5,780 |
| + valid n >= 30 | 4,664 |
| + valid t >= 1.5 | 926 |
| + train half 1 > 0 | 789 |
| + train half 2 > 0 | 326 |
| + edge over baseline on train and valid | 326 |
| + plateau | **312** |

If every configuration had zero true mean, these gates would let through roughly 1-2% by chance, i.e. thousands. Only 0.06% passed, because almost the whole population is negative after costs: the baselines are -0.06 to -0.21R.

## 4. Results - failures first

**No faithful rule passes.** With no layers, none of the 17 families passes the gates on either side, under any exit. Long side mean expectancy per family is -0.11 to -0.18R on train and -0.12 to -0.27R on valid.

### Faithful (no layers, 09:50-15:00), all variants x exits per family
| fam | side | configs | mean train | mean valid | best train | best valid | train>0 | valid>0 |
|---|---|---|---|---|---|---|---|---|
| MP (Ross micro-pullback) | long | 180 | -0.106 | -0.158 | -0.071 | -0.079 | 0 | 0 |
| MP | short | 180 | -0.079 | -0.091 | -0.034 | -0.001 | 0 | 0 |
| VT (volume top/bottom entry) | long / short | 12 / 12 | -0.114 / -0.125 | -0.148 / -0.051 | -0.057 / -0.056 | -0.090 / 0.171 | 0 / 0 | 0 / 2 |
| JD (Jdub) | long / short | 18 / 18 | -0.111 / -0.076 | -0.159 / -0.096 | -0.072 / -0.041 | -0.093 / -0.007 | 0 / 0 | 0 / 0 |
| BK (9-EMA ride) | long / short | 12 / 12 | -0.139 / -0.089 | -0.190 / -0.114 | -0.082 / -0.054 | -0.121 / 0.003 | 0 / 0 | 0 / 1 |
| VA (VA re-entry) | long / short | 21 / 21 | -0.129 / -0.076 | -0.227 / -0.113 | -0.052 / -0.049 | -0.119 / -0.060 | 0 / 0 | 0 / 0 |
| VA30 (80% rule as stated) | long / short | 12 / 12 | -0.133 / -0.119 | -0.227 / -0.149 | -0.093 / -0.077 | -0.179 / -0.102 | 0 / 0 | 0 / 0 |
| BLK (Dale block) | long / short | 16 / 16 | -0.176 / -0.162 | -0.227 / -0.080 | -0.104 / -0.123 | -0.156 / 0.024 | 0 / 0 | 0 / 2 |
| LVN | long / short | 12 / 12 | -0.106 / -0.068 | -0.162 / -0.095 | -0.072 / -0.042 | -0.096 / -0.004 | 0 / 0 | 0 / 0 |
| AVR (AVWAP retest) | long / short | 60 / 60 | -0.141 / -0.113 | -0.171 / -0.090 | -0.056 / 0.012 | -0.076 / 0.297 | 0 / 2 | 0 / 7 |
| AVF (AVWAP 2SD fade) | long / short | 50 / 50 | -0.141 / -0.095 | -0.137 / -0.062 | -0.075 / -0.049 | -0.089 / 0.012 | 0 / 0 | 0 / 3 |
| IC (institutional confluence) | long / short | 144 / 144 | -0.153 / -0.077 | -0.220 / -0.112 | -0.057 / 0.035 | -0.079 / 0.131 | 0 / 5 | 0 / 13 |
| ENVF (2SD envelope fade) | long / short | 10 / 10 | -0.141 / -0.104 | -0.131 / -0.070 | -0.078 / -0.081 | -0.090 / -0.041 | 0 / 0 | 0 / 0 |
| ENVC (envelope continuation) | long / short | 28 / 28 | -0.132 / -0.091 | -0.165 / -0.144 | -0.076 / 0.019 | -0.105 / -0.076 | 0 / 2 | 0 / 0 |
| SWP (VWAP sweep + delta) | long / short | 54 / 54 | -0.165 / -0.088 | -0.162 / -0.163 | 0.038 / 0.131 | 0.491 / 0.093 | 1 / 3 | 2 / 2 |
| OFP (profile + delta) | long / short | 24 / 24 | -0.122 / -0.084 | -0.165 / -0.094 | -0.071 / -0.022 | -0.092 / 0.012 | 0 / 0 | 0 / 2 |
| PINCH | long / short | 12 / 12 | -0.171 / -0.026 | -0.251 / -0.246 | -0.065 / 0.152 | -0.143 / -0.142 | 0 / 3 | 0 / 0 |
| PWR (prior-week AVWAP retest) | long / short | 24 / 24 | -0.121 / -0.092 | -0.118 / -0.025 | -0.070 / -0.019 | -0.052 / 0.283 | 0 / 0 | 0 / 5 |

The best faithful configuration positive on both splits is IC pwh break short, tx, AM:
- Train: n 2,005, +0.068R, t 0.99.
- Valid: n 704, +0.136R, t 0.91.
- It fails the t gate.

### Exits: the structural exits are only slightly better than lab geometries, and still negative
Faithful means over all triggers (09:50-15:00):

| exit | long train | long valid | short train | short valid |
|---|---|---|---|---|
| jd | -0.087 | -0.115 | -0.064 | -0.109 |
| e9c1 | -0.085 | -0.099 | -0.079 | -0.091 |
| c9 | -0.079 | -0.110 | -0.053 | -0.086 |
| vt | -0.113 | -0.201 | -0.096 | -0.106 |
| trail9 | -0.112 | -0.130 | -0.105 | -0.126 |
| t1s1 | -0.173 | -0.218 | -0.101 | -0.123 |

- The structural exits cut the loss mostly by holding winners shorter and losing less per stop. None turns a family positive.
- The candle-by-candle trail (trail9, BKTraders) is among the worst exits on almost every family: 5-minute noise stops it out.
- Ross's volume-top exit (vt) is no better than the plain EMA9 exits.

### Per family: configurations passing the gates (scored; pre-plateau / plateau)
| family | passing |
|---|---|
| AVR | 114 / 110 |
| IC | 74 / 70 |
| PWR | 62 / 62 |
| MP | 43 / 41 |
| AVF | 16 / 12 |
| VT | 11 / 11 |
| OFP | 4 / 4 |
| SWP | 2 / 2 |
| JD, BK, BLK, LVN, VA, VA30, ENVC, ENVF, PINCH | 0 |

- **Of the 326 passers, 317 are SHORT and 297 use the tx exit** (hold to 15:55, 2R hard stop).
- The long side has 9 passers, all with weak train t.
- dcn (VWAP-POC confluence) appears in 43 passers and vslope in 23. Neither filter rescues any family.

## 5. Finalists (8, chosen by min(train t, valid t); identical trade sets collapsed)
**All 8 are shorts that need the structural tx exit.** LabStrategy cannot run that exit today (section 7).

All numbers are after costs. "Halves" are the two calendar halves of train.

| # | module | rule | train n / exp / t (halves) | valid n / exp / t | valid ex-best-day | valid ex-top-3-days |
|---|---|---|---|---|---|---|
| 1 | VID1-mp-2-vw-any-rsi5_hi-short-am-tx | Ross micro-pullback SHORT: a 1-2 bar higher-low bounce touching VWAP, then the first new-low bar, with RSI(5) >= 70 (09:50-11:30) | 206 / +0.191 / 2.35 (+0.30/+0.11) | 68 / +0.301 / 2.09 | +0.224 | +0.104 |
| 2 | VID2-ic-pwh-break-01-e9_with-gap_with-short-pm-tx | SMB confluence: session VWAP within 0.1% of the prior-week-high AVWAP, close breaks below the node, below EMA9, gap down >= 1% (11:30-15:00) | 133 / +0.162 / 2.03 (+0.33/+0.02) | 34 / +0.451 / 3.25 | +0.391 | +0.236 |
| 3 | VID3-mp-1-vw-any-rsi5_hi-short-am-tx | as #1 with a 1-bar pullback (a subset of #1's symbol-days) | 135 / +0.300 / 2.55 (+0.28/+0.32) | 47 / +0.277 / 1.93 | +0.179 | +0.061 |
| 4 | VID4-mp-1-vw-any-rsi5_lo-gap_with-short-pm-tx | micro-pullback short, RSI(5) <= 30, gap down >= 1% (pm) | 805 / +0.098 / 1.88 (+0.17/+0.01) | 303 / +0.132 / 1.83 | +0.073 | **-0.003** |
| 5 | VID5-ic-pwh-break-02-rvol15-e9_with-short-am-tx | IC prior-week-high AVWAP node (0.2%) break short, RVOL >= 1.5, below EMA9 (am) | 271 / +0.265 / 1.82 (+0.48/+0.02) | 123 / +0.235 / 2.04 | +0.168 | +0.073 |
| 6 | VID6-vt-vr2-gap_with-dsma20_with-short-pm-tx | Ross volume top (new HOD, upper wick >= 0.5, volumeRatio >= 2) short on gap-down days below the daily SMA20 (pm) | 137 / +0.188 / 2.01 (+0.17/+0.21) | 82 / +0.317 / 1.78 | +0.255 | **-0.062** |
| 7 | VID7-mp-1-vw-any-rsi5_hi-pdroom-short-am-tx | #3 plus no prior-day low within 0.5 ATR (a subset of #3) | 75 / +0.268 / 2.07 (+0.21/+0.32) | 30 / +0.358 / 1.78 | +0.257 | +0.066 |
| 8 | VID8-avr-pdh-any-gap_with-dsma20_with-short-pm-tx | Jumpstart AVWAP (prior-day-high anchor) first retest short, gap down >= 1%, below the daily SMA20 (pm) | 491 / +0.199 / 1.78 (+0.12/+0.30) | 166 / +0.435 / 5.83 | +0.387 | +0.312 |

**Warnings that come with these finalists. Read these before acting on them.**
1. **The edge lives entirely in the exit.** The same masks with every other exit are flat or negative (`finalist_exits.csv`).
   - For example, #1 with t1s1 is +0.109 train / +0.076 valid, and with jd it is -0.018 / -0.123.
   - So these are "short and hold to the close" bets on weak days. The trigger mostly picks the day and the name.
2. **Regime.** The tx-short random baseline is -0.061R on train but **+0.011R on valid**: the valid window drifted down intraday.
   - The edge over that baseline is still +0.24 to +0.44R on valid. But a tilt in market direction can carry these results.
   - The locked holdouts (Sep 16 - Oct 5; Apr-Jun) are the real test.
3. **Concentration.**
   - #4 and #6 go negative on valid without their 3 best days.
   - #2, #5 and #8 lean on train half 1: their half-2 means are +0.02, +0.02 and +0.30 respectively (#8 is fine).
4. **Overlap.** #1, #3 and #7 are one idea: #7's symbol-days sit inside #3's, and #3's inside #1's. The other pairs overlap 0-17%. So there are **6 distinct ideas**:
   - the micro-pullback short with RSI5 extreme
   - the micro-pullback short on gap-down days
   - the IC prior-week-high node break (2 variants)
   - the volume top on gap-down days
   - the AVWAP pdh retest on gap-down days
5. **Multiple testing.** 692,484 configurations were tried. Each finalist's train t is 1.78 to 2.55, which by itself would not survive a correction across this many tries. The holdouts decide.

### Other passers worth knowing (all gates met, outside the top-8 cut)
These were not written as modules; `gen_modules.py` can write them.
- **LabStrategy-runnable (lab geometry)**, PWR prior-week-low AVWAP retest short, gap down >= 1% + below the daily SMA20, pm, t1s1:
  - Train: n 200, +0.132R, t 1.36.
  - Valid: n 98, +0.188R, t 2.10, ex-best-day +0.154.
  - Siblings with rsi5_hi or vwap_against also pass (valid t 2.2-2.9).
  - 16 lab-geometry configurations passed in total (`passers.csv`).
- **AVR pdh short, gapper + below the daily SMA20, pm, t1s1:**
  - Train: n 275, +0.062R, t 1.13.
  - Valid: n 74, +0.158R, t 1.81.
- **AVF prior-day-high-volume-bar AVWAP +2SD fade short, RVOL >= 1.5 + gap down, avw exit:**
  - Train: n 225, +0.127R, t 1.60.
  - Valid: n 69, +0.369R, t 2.92.
- **Common thread:** every robust passer is a SHORT on a gap-down / below-SMA20 / extended-RSI5 day. This matches the earlier BDI and MarcoFlow findings (flow-sell into strength, short side less bad).

All 8 modules reproduce the scan exactly (n and expectancy) when run on the lab frame (`finalists_verify.json`).

## 6. Near misses (exactly one gate failed, valid n >= 30)
1,520 configurations. Failed gate:

| failed gate | configurations |
|---|---|
| valid t | 920 |
| train half 2 | 463 |
| train half 1 | 137 |

The most useful ones:
- **ENVF / AVF-open 2SD fade SHORT, gap-down + gapper, pm, t1s1 (lab geometry):**
  - Train: n 854, +0.085R, t 1.83.
  - Valid: n 325, +0.153R, t 1.88.
  - Fails train half 2 (-0.040).
  - The same mask with the avw exit gives train +0.116R (t 2.64), valid +0.134R (t 1.74), half 2 -0.002.
  - This is the best LabStrategy-native near miss and a Testing-account candidate.
- **IC prior-week-high break short, RSI5 <= 30, all day, tx:**
  - Train: n 1,605, +0.077R, t 1.39.
  - Valid: n 569, +0.134R, t 1.43.
  - It is big and simple, and fails valid t only.
- **IC gap-day AVWAP break short, below EMA9 + gap down, pm, tx:**
  - Train: n 129, +0.159R.
  - Valid: n 55, +0.255R, t 2.66.
  - Fails train half 2 (-0.052).
- **LVN air-pocket short, below VWAP + gapper, pm, tx:**
  - Train: n 1,355, +0.079R.
  - Valid: n 388, +0.188R, t 1.66.
  - Fails half 2 (-0.107).
- **VA cross2 short (RVOL >= 1.5 + flow-buy, am), poc exit:** train +0.218R (n 64), valid +0.121R t 1.06. Too small.

The full tables are in `data/report.md` (git-ignored) and `results.csv`. results.csv holds every no-layer configuration plus every configuration positive on both splits with valid n >= 30: 8,727 rows, 1.6 MB.

## 7. What live deployment would need (precisely)
1. **Exit.**
   - LabStrategy.GEOMS only has t1s1 / t05s1 / t1s05.
   - The finalists need "tx": stop at entry + 2R (short), no target, flat at 15:55. That could be a GEOMS entry with a far target (e.g. (100.0, 2.0)).
   - The research filled entries at the next 1-minute open after the signal bar.
   - The `jd`, `c9`, `trail9`, `vt`, `poc` and `avw` exits would need real exit-management code. None of them is needed by a finalist.
2. **Features.** LabStrategy.generate must join:
   - `features.day_features(ctx.bars, prior_session_1min, ctx.prior5, ctx.avg_cum_volume, ctx.atr)`
   - `features2.day_features2(ctx.bars, history_1min_since_anchors, prior_session_1min, ctx.atr, anchors, ctx.prev_close)`
   - and set `d_sma20 = ctx.sma20`, `atr_b = ctx.atr`
3. **DayContext data.**
   - DayContext has no prior-session 1-minute bars (needed for the prior-day profile and the pdh/pdl/pdhv anchors).
   - It has no multi-day 1-minute history (the pwh/pwl/gap/qop AVWAPs). Live could keep running AVWAP sums per anchor instead.
   - Which finalists depend on these anchors:

     | finalist | anchor data needed |
     |---|---|
     | #1, #3, #4, #6, #7 | none |
     | #2, #5 | the prior week's 1-minute bars |
     | #8 | prior-session 1-minute bars |

4. **ATR.** Research R uses the lab's atr_d (5-minute-derived daily TR, rolling 14, min 10). LabStrategy passes ctx.atr from the engine. The two can differ slightly.
5. **Dependencies.** numba is used only by the research build. The masks are numpy-only (`vid_rules.py`).

## 8. Recommendation
- **Primary account: nothing.**
  - No finalist has been scored on the locked holdouts yet, and all 8 need an exit LabStrategy does not have.
  - The result is a short-side, regime-sensitive, hold-to-close effect, found among 692k tries.
- **Lead: score the holdouts once, in this order:**
  - **#8** (AVR pdh short): the largest sample, and positive in both train halves.
  - **#1** (as the representative of #1/#3/#7).
  - **#5, #2** (IC prior-week-high node).
  - **#6, #4** (concentrated on valid; lowest priority).
  - #3 and #7 only if #1 passes; they share its lineage.
  - Use the look-1 bar (t >= 1.0) on both holdouts.
- **Testing account** (experimental, tagged, 3-session scorecard), once the tx geometry exists:
  - the PWR prior-week-low gap-down short (lab t1s1, already runnable)
  - the ENVF 2SD gap-down fade (lab t1s1 near miss)
  - VID8
  - These share the "gap-down afternoon short" theme. Run them as one cluster with a combined risk cap, because they will fire on the same days.
- **Drop for now (failed, logged in the backlog):**
  - long micro-pullbacks, Jdub, the BKTraders trail
  - the volume-profile rules (the 80% rule in both forms, the Dale block, LVN)
  - the Wysetrade continuation, the anchor pinch
  - the DCN / flat-VWAP filters as general improvers

## 9. Files and reproduce
```
python research/bdi/videos/build.py && python research/bdi/videos/build2.py     # ~90 min on 4 cores, data/ git-ignored
python research/bdi/videos/scan.py                                               # ~35 min; data/all_results.parquet, counts.json, passers.csv, plateau.csv
python research/bdi/videos/report.py > research/bdi/videos/data/report.md         # tables + finalists.json + results.csv
python research/bdi/videos/gen_modules.py && python research/bdi/videos/finalist_check.py
```
- Backlog entries `bdi-vid-*` (25):
  - 8 finalists
  - 2 extra passer groups
  - 10 failures, including the grid summary
  - 5 untestable ideas
- Educational only - not financial advice.

---

## 10. Locked holdouts (scored ONCE, 2026-10-08, lead-authorized; look 1, bar: t >= 1.0, exp > 0 and ex-best-day > 0 on BOTH)
`score_holdouts.py` -> `holdouts.json`.

**What was scored:**
- 10 rules: VID1-VID8 exactly as committed, plus the 2 extra passers.
  - X1 = PWR prior-week-low AVWAP retest short, gap_with + dsma20_with, pm, t1s1.
  - X2 = AVF pdhv +2SD fade short, rvol15 + gap_with, all day, avw.
- No module, rule or exit was changed after seeing the numbers.

**How:**
- **Features** were built with the research code (build.one / build2.one) for:
  - test 2026-09-16..10-05, from data/cache/1Min with timestamps < 2026-10-06 (14 sessions)
  - q2 2026-04-01..06-30, from data/cache_q2/1Min, which starts 2026-03-10 (62 sessions)
- **History rules** were the same as in research: 40 prior 5-min bars, plus prior-session and prior-week 1-min bars.
  - The prior-week anchor existed on every symbol-day; 0 days were excluded.
  - 554 q2 lab rows had no features (symbol-days with < 60 one-minute bars) and were dropped. Test lost 0 rows.
- **Costs:**
  - Lab t1s1 uses the `prod` function from research/owner1008/score_holdouts.py.
  - tx / avw use the 1-minute simulator: 1c + 1 bps per side, +2c on stops; tx exits at the 15:55 open and pays exit costs.

### Verdict: 0 of 10 pass. Every rule fails at least one holdout.
| rule | test n / days | test exp / t / ex-best / green | q2 n / days | q2 exp / t / ex-best / green | look-1 |
|---|---|---|---|---|---|
| VID1 mp-2 rsi5_hi short am tx | 89 / 14 | -0.025 / -0.12 / -0.146 / 0.43 | 277 / 61 | +0.064 / 0.52 / +0.001 / 0.36 | FAIL |
| VID2 ic-pwh-break 0.1 gap pm tx | 34 / 11 | -0.207 / -2.60 / -0.258 / 0.27 | 148 / 43 | -0.184 / -1.46 / -0.239 / 0.47 | FAIL |
| VID3 mp-1 rsi5_hi short am tx | 61 / 14 | +0.063 / 0.24 / -0.075 / 0.50 | 180 / 56 | +0.101 / 0.70 / +0.026 / 0.39 | FAIL |
| VID4 mp-1 rsi5_lo gap pm tx | 173 / 14 | +0.061 / 0.52 / -0.012 / 0.64 | 1,032 / 62 | -0.090 / -1.32 / -0.111 / 0.44 | FAIL |
| VID5 ic-pwh-break 0.2 rvol am tx | 118 / 14 | +0.046 / 0.25 / -0.052 / 0.57 | 437 / 62 | -0.145 / -1.43 / -0.186 / 0.44 | FAIL |
| VID6 vt-vr2 gap sma20 pm tx | 65 / 14 | -0.117 / -1.27 / -0.171 / 0.21 | 274 / 50 | -0.027 / -0.33 / -0.064 / 0.50 | FAIL |
| VID7 mp-1 rsi5_hi pdroom am tx | 40 / 13 | +0.087 / 0.25 / -0.076 / 0.46 | 97 / 45 | **+0.271 / 1.59 / +0.171 / 0.53** | FAIL (test) |
| VID8 avr-pdh gap sma20 pm tx | 175 / 13 | -0.051 / -0.49 / -0.127 / 0.38 | 615 / 60 | -0.005 / -0.05 / -0.055 / 0.53 | FAIL |
| X1 pwr-pwl gap sma20 pm t1s1 | 72 / 12 | **+0.112 / 1.26 / +0.049 / 0.58** | 279 / 48 | -0.015 / -0.18 / -0.052 / 0.50 | FAIL (q2) |
| X2 avf-pdhv 2SD rvol gap avw | 68 / 13 | +0.144 / 0.79 / +0.008 / 0.62 | 305 / 56 | -0.050 / -0.63 / -0.081 / 0.45 | FAIL |

Win rates are in holdouts.json.

### Market context (why the q2 number is the real check)
| | test (Sep 16 - Oct 5) | q2 (Apr - Jun) |
|---|---|---|
| median open-to-close, all symbol-days | -0.22% | +0.025% |
| sessions with a negative median | 79% | 48% |
| random short, tx exit, 09:50-15:00 / pm | -0.040 / -0.008 R | -0.047 / -0.046 R |
| random short, t1s1 (prod), 09:50-15:00 / pm | -0.086 / -0.075 R | -0.048 / -0.042 R |

**Reading:**
- The research-window edge was a down-drift effect.
- Even on test, another down-drift window, the hold-to-close shorts did not repeat: 6 of 8 have negative ex-best-day.
- On q2, a flat market, the gap-down and IC shorts are clearly negative: VID2, VID4 and VID5 have t from -1.3 to -1.5.
- VID7, the narrowest version of the micro-pullback short (RSI5 >= 70, AM, prior-day-low room), is the only rule positive on q2 at t >= 1.0. It is noise-level on test (n 40, t 0.25, ex-best-day negative).
- Its parent VID1, with 3x the trades, is flat on both holdouts. So the VID7 q2 result is most likely selection luck inside a dead family.

**Status:**
- All 10 are `holdout_failed` (look 1 burned for the bdi-vid lineages).
- Under rule 18, a rework could take look 2 (t >= 1.5). Of the lineages, only the micro-pullback short with an RSI5 extreme (VID1/3/7) has any holdout support, and it is weak.
- Nothing goes to the primary account.
- The Testing account option is a probation-style forward test of VID7 only, labelled as a holdout failure. That is the owner's call. Recommendation: do not deploy.
