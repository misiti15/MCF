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
