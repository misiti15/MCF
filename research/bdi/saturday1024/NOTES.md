# BDI Saturday deep run 2026-10-24 (week 10-19..10-23)

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7). History numbers are
**backtests** on the open two-year history (train ≤ 2025-12-31, valid 2026-01-01..10-07), production + tier costs in.
The locked block 2024-11-01..2025-02-28 was never read (`MCF_HIST_ALLOW_LOCKED` never set; every loader asserts it;
the 1-min cache drops it on read). No holdout was scored. No config, setup, exit or assignment was changed.
`PLAN.md` was written before scoring; its addendum (L) was written after S / G1-G3 were scored and before L.*

**Configurations tried: 29** (S 8, G1 3, G2 6, G3 6, L 6). Lineage N 1,311 (gate lineage, bdi1023) + 29 = 1,340
→ bar max(1.5, sqrt(2 ln N)) = **3.79**. **0 pass the bar.** 3 Primary rows are "no-harm" (ST-P, below the bar).

## Failures first
1. **No give-back rule passes, and none of the trade-neutral ones helps.** Of the 29 rows only the Primary per-setup
   stop (S1.5 / S2 / S3) improves avg R in train and valid and in up and down sessions while keeping ≥ 85% of trades;
   even it is below the bar (t 3.01-3.32 vs 3.79). Everything else either costs avg R in one split or one regime, or
   cuts give-back only by cutting 15-75% of trades.
2. **The late profit lock is clearly harmful** (L1500 / L1430, all books, delta −0.004..−0.009R per trade, t −3.6..−8.0).
   Trades already +0.5R after 14:30 keep drifting into the close on two years; the 15:55 flatten give-back is cheaper
   than locking it. This is the opposite of what this week's live flatten give-back suggested.
3. **The open-risk bound (LL-OPEN, "SO") is far too restrictive:** it keeps 24-54% of trades in every book and loses in
   down sessions. LL-OPEN is closed.
4. **Coverage limits:** books = today's assignments ∩ the gates1021 signal cache: Primary 10 of 11 setups
   (CWT14-failbrk-pdl-p10-lowvol-long missing), Testing 1 19 of 33, Testing 2 24 of 47 (CWT04/09/12/13 and part of
   CWT14 missing), Graveyard and Gen 0. Slots, concurrent-position caps and sizing are not simulated (1R per trade;
   lot / twin / per-setup caps and the book daily stop are). Exit minutes were re-simulated on the 5-min frames for the
   cached signals that lacked them (`exits.py`: win/loss agreement with the cache 100% where a bracket was hit; 41% held
   to the close); the late lock walks the 1-min cache.
5. **Discrepancy:** the routine brief says Primary is "4 of 14 green"; the journal says **3 of 14** (10-12, 10-14, 10-22).

## 1. Discover workflow (weekly) — finished
- Run 40103968169 (schedule, 2026-10-24 14:46 UTC): **success in 26m36s**; every step green (Mine, research bar cache,
  refresh bars to the last session, backlog re-test, stage, publish). mcf-data commit 2f803d2f "discovery + backlog
  2026-10-24".
- **Bar cache refreshed to 2026-10-23** (lab-cache sample 2026-06-15..10-23). **Backlog re-tested: 66 lab entries**,
  results in `mcf-data/backlog/backlog_results.jsonl` (history now 132 rows; last week's run also published 66, so the
  10-10 "scored nothing" failure is fixed). 43 of 66 positive in-sample on the cache window, 21 positive on forward
  sessions. Top in-sample: NS1-rsidip-rsi5pop-long +0.230R (n 112, t 4.12; forward 10 trades +0.158R),
  bdi-rw-gapdn-rsi5pop-flowsell (RW3 base) +0.213R (354, t 3.96; forward 42, +0.194R). The cache window is one
  4-month regime; RW3-FD is −0.076R on two years (top5_1023). Not a pass on the two-year gates.
- Discovery scan: 2,292 rule/direction combinations, 32 "replicated". The strongest family ("RSI14 < 35 + new high of
  day", short) is an odd combination (a new high of day with RSI14 under 35) and looks like a feature artefact; not
  added. Every other replicated row is ≤ +0.03R test expectancy.

## 2. Rule-18 rework round + give-back tests (`book_sim.py`, `book_sim.csv`, `book_sim_out.txt`)
Book simulator on the cached signals: by entry minute then symbol; live checks replayed: max 3 lots per symbol, no lot
against an opposite-side lot, twin block (setup vs its -FD / twin_group), per-setup open cap (P 100, T1 150, T2 50), book
daily stop (P −20R, T1/T2 −120R). Give-back = per day, peak (≥ 0) minus close of the realized-R curve by exit time.

| book | cfg | kept % tr / va | avg R tr / va | Δ R tr / va | t (all) | Δ up / down | give-back mean tr / va (R) | swing days va (of peak days) | worst day va | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | B0 | 100 / 100 | −0.098 / −0.035 | — | — | — | 12.7 / 11.9 | 41 / 118 | −71 | baseline |
| Primary | S1.5 | 88 / 88 | −0.096 / −0.027 | +0.013 / +0.012 | 3.01 | +0.023 / +0.007 | 11.3 / 10.4 | 40 / 118 | −46 | no-harm |
| Primary | **S2** | 90 / 90 | −0.093 / **−0.025** | +0.013 / +0.013 | **3.32** | +0.020 / +0.011 | 11.4 / 10.5 | 41 / 120 | −46 | no-harm |
| Primary | S3 | 95 / 95 | −0.090 / −0.028 | +0.012 / +0.008 | 3.10 | +0.011 / +0.013 | 11.9 / 11.1 | 40 / 118 | −52 | no-harm |
| Primary | SO | 54 / 54 | −0.093 / −0.026 | +0.047 / +0.021 | 3.46 | +0.113 / −0.022 | 6.6 / 6.1 | 24 / 98 | −22 | fail |
| Primary | G1 | 82 / 83 | −0.103 / −0.036 | +0.013 / +0.006 | 2.29 | +0.038 / −0.013 | 10.3 / 9.4 | 36 / 113 | −47 | fail |
| Primary | G2k3 | 92 / 94 | −0.088 / −0.039 | +0.017 / −0.001 | 1.55 | +0.024 / +0.004 | 10.8 / 11.1 | 40 / 113 | −58 | fail |
| Primary | G2k5 | 96 / 98 | −0.087 / −0.036 | +0.014 / −0.000 | 1.88 | +0.018 / +0.004 | 11.4 / 11.5 | 41 / 118 | −62 | fail |
| Primary | G3f50 | 88 / 86 | −0.095 / −0.036 | +0.014 / +0.004 | 1.84 | +0.020 / −0.006 | 11.2 / 10.6 | 39 / 118 | −47 | fail |
| Primary | G3f33 | 84 / 81 | −0.082 / −0.031 | +0.029 / +0.010 | 3.20 | +0.039 / −0.003 | 10.3 / 9.9 | 32 / 118 | −47 | fail |
| Primary | L1500 | 100 / 100 | −0.102 / −0.042 | −0.004 / −0.006 | −4.41 | −0.001 / −0.009 | 12.8 / 12.0 | 40 / 118 | −70 | fail |
| Primary | L1430 | 100 / 100 | −0.102 / −0.042 | −0.005 / −0.006 | −3.61 | +0.000 / −0.011 | 12.7 / 11.9 | 40 / 118 | −70 | fail |
| Testing 1 | B0 | 100 / 100 | −0.094 / −0.039 | — | — | — | 44.3 / 42.7 | 40 / 125 | −294 | baseline |
| Testing 1 | S2 | 66 / 63 | −0.091 / −0.030 | +0.034 / +0.020 | 3.75 | +0.096 / −0.032 | 29.4 / 26.7 | 32 / 104 | −137 | fail |
| Testing 1 | SO | 28 / 24 | −0.085 / −0.025 | +0.070 / +0.033 | 4.49 | +0.182 / −0.074 | 11.8 / 9.8 | 16 / 61 | −30 | fail |
| Testing 1 | G1 | 78 / 77 | −0.094 / −0.037 | +0.020 / +0.011 | 3.41 | +0.059 / −0.020 | 33.9 / 31.8 | 31 / 108 | −212 | fail |
| Testing 1 | G2k3 | 83 / 80 | −0.090 / −0.037 | +0.019 / +0.009 | 2.74 | +0.052 / −0.024 | 34.7 / 31.0 | 34 / 115 | −220 | fail |
| Testing 1 | G2k5 | 91 / 89 | −0.092 / −0.038 | +0.010 / +0.005 | 2.07 | +0.028 / −0.013 | 39.3 / 35.8 | 36 / 115 | −242 | fail |
| Testing 1 | G3f50 | 86 / 83 | −0.082 / −0.045 | +0.023 / +0.001 | 2.20 | +0.035 / −0.013 | 37.1 / 38.4 | 46 / 125 | −294 | fail |
| Testing 1 | G3f33 | 83 / 80 | −0.082 / −0.040 | +0.025 / +0.007 | 2.64 | +0.041 / −0.016 | 36.0 / 35.8 | 41 / 125 | −294 | fail |
| Testing 1 | L1500 | 100 / 100 | −0.101 / −0.046 | −0.007 / −0.007 | −7.83 | −0.004 / −0.011 | 45.2 / 43.8 | 40 / 123 | −296 | fail |
| Testing 1 | L1430 | 100 / 100 | −0.101 / −0.045 | −0.007 / −0.006 | −4.22 | −0.003 / −0.010 | 44.8 / 42.8 | 38 / 121 | −301 | fail |
| Testing 2 | B0 | 100 / 100 | −0.085 / −0.016 | — | — | — | 28.0 / 25.4 | 32 / 124 | −199 | baseline |
| Testing 2 | S2 | 70 / 66 | −0.066 / −0.018 | +0.039 / +0.004 | 3.33 | +0.070 / −0.023 | 19.3 / 19.2 | 29 / 103 | −145 | fail |
| Testing 2 | SO | 33 / 27 | −0.080 / −0.021 | +0.059 / +0.010 | 3.38 | +0.124 / −0.057 | 10.0 / 8.6 | 7 / 46 | −31 | fail |
| Testing 2 | G1 | 82 / 79 | −0.087 / −0.021 | +0.013 / −0.001 | 1.66 | +0.026 / −0.014 | 23.0 / 20.7 | 25 / 107 | −137 | fail |
| Testing 2 | G2k3 | 84 / 83 | −0.076 / −0.018 | +0.021 / +0.001 | 2.25 | +0.033 / −0.014 | 21.9 / 20.7 | 22 / 113 | −151 | fail |
| Testing 2 | G2k5 | 92 / 92 | −0.080 / −0.019 | +0.012 / −0.002 | 1.22 | +0.017 / −0.009 | 24.3 / 23.4 | 24 / 118 | −179 | fail |
| Testing 2 | G3f50 | 91 / 86 | −0.086 / −0.017 | +0.007 / +0.001 | 0.99 | +0.011 / −0.006 | 26.5 / 24.0 | 34 / 124 | −199 | fail |
| Testing 2 | G3f33 | 88 / 82 | −0.084 / −0.015 | +0.011 / +0.004 | 1.75 | +0.018 / −0.009 | 25.4 / 22.7 | 30 / 124 | −199 | fail |
| Testing 2 | L1500 | 100 / 100 | −0.092 / −0.024 | −0.007 / −0.008 | −7.98 | −0.005 / −0.010 | 28.7 / 26.5 | 32 / 124 | −190 | fail |
| Testing 2 | L1430 | 100 / 100 | −0.093 / −0.024 | −0.008 / −0.009 | −6.46 | −0.005 / −0.012 | 28.5 / 26.1 | 33 / 123 | −184 | fail |

Reading:
- **Rework verdicts (rule 18):** cluster cap G2 (rework of failed `loop-1008-exhaustion-cluster-t1`) and post-peak
  side brake G3 (rework of failed `gb-1019-post-peak-index-guard`) fail again: the gains are up-session thinning
  (Δ up > 0 and Δ down < 0 in 10 of 12 rows; the 2 exceptions, Primary G2, lose in valid instead), the classic pattern of every book-level gate in MCF. G1 (one lot per symbol,
  the untested `gb-1019-twin-setup-exposure` / `nightly-1016-primary-one-lot-per-symbol`) the same.
- **Testing 1 / 2: the per-setup −2R stop keeps only 63-70% of trades** and loses in down sessions on two years —
  consistent with the owner's ST-A (stop off in the testing accounts). Do not restore it.
- **Give-back is structural:** Primary's book on history peaks at ≥ +3R on 118 valid days and closes ≤ 0 on 41 of them
  (35%); no rule here changes that share except by trading less.

### ST-P: Primary per-setup stop on two years (`stp2y.py`, `stp2y_out.txt`)
| | S1.5 | **S2** | S3 |
|---|---|---|---|
| trades blocked | 3,886 (13.7%) | 3,299 (11.6%) | 1,782 (6.3%) |
| blocked trades avg R (train / valid) | −0.109 / −0.101 | −0.137 / −0.130 | −0.221 / −0.156 |
| total Δ over 2 years | +347R | **+374R** | +292R |
| without the best day | +287R | +309R | +230R |
| months better | 16 of 21 | 17 of 21 | 17 of 21 |
| the book's 20 best days (B0 +753R): give-up | −49.4R (7 days cut) | −26.5R (5) | **−2.4R (2)** |
| all 170 green days give-up / red days gain | −242 / +589R | −174 / +548R | −74 / +366R |

By setup (S2): MF2-FD +115R, MF4 +95R, NS5 +77R (−46R → +31R), RW3-FD +76R, RW5-FD +71R; MF4-h40-FD −68R (its losing
days recover). It is a plateau (all three thresholds positive in both splits and regimes). Live (nightly1023 `stp.py`,
14 sessions): latch 2R +19.4R, 1.5R +17.9R, 3R +10.0R vs none, best day 10-22 not hurt, t ≤ 0.82. The Primary book is
still negative after costs with the stop (valid −0.025R/trade): the stop trims losing setup-days, it does not create an
edge. **→ DECISION ST-P (owner).**

## 3. Weekly give-back review (live paper, 10-19..10-23; `nightly1019..1023/daily_peak.csv`, `giveback_out.txt`)
Marked intraday peak → close ($, costs in):

| account | 10-19 | 10-20 | 10-21 | 10-22 | 10-23 | week close |
|---|---|---|---|---|---|---|
| Primary | +64 (10:05) → −64 | +58 (14:45) → −46 | +90 (12:28) → **−627** | **+1,553** (15:47) → +1,369 | 0 → −92 | **+$540** |
| Testing 1 | **+671** (10:05) → **−404** | **+912** (14:45) → +692 | +50 (10:06) → −548 | +22 → −73 | +190 (14:41) → +180 | −$152 |
| Testing 2 | +60 (10:19) → −79 | +297 (14:45) → +281 | +91 (15:11) → −15 | +105 (13:28) → +1 | +230 (14:51) → +157 | +$345 |
| Graveyard | — | — | +199 (10:41) → −747 | +12 → −1,338 | 0 → −651 | −$2,737 (3 days) |
| Gen | +42 → +21 | **+321** (10:58) → −75 | +489 (15:11) → +420 | 0 → −568 | **+933** (15:37) → +890 | +$688 |

What gave it back (peak-minute attribution):
- **"Up a lot, then a loss" happened once:** Testing 1 10-19, +$671 at 10:05 → −$404. New entries after the peak −$780
  (343 trades) and open winners stopped −$438 (39); heat_fade_long and its twin heat_fade_long-FD lost
  −$620 together. The twin-exposure cap went live the next day (10-20).
- **Primary 10-21, +$90 → −$627:** one setup's stacked lots — NS3-failed-vwap-reclaim-short-FD −$524 (28 lots open at the
  peak, stopped as SPY rose); not new entries (−$56). NS3-FD was demoted the next morning (N5). A per-setup stop would
  not have stopped lots already open; this is the open-lot cluster problem (G2 / SO: both fail on history).
- **Gen 10-20, +$321 → −$75:** GEN-261020-07 hold-long open winners flattened / stopped −$395 (hold exit; backlog
  `nightly-1020-gen-hold-mfe-giveback`).
- **Late flatten of open winners** (small, recurring): T1 10-20 −$221 (78 lots), P 10-22 −$135, T2 10-21 −$84,
  T2 10-23 −$63, Gen 10-21 −$121. The late lock (L) shows this is cheaper to bear than to fix.
- **Graveyard:** post-peak entries every day (−$670 / −$1,274 / −$651), CWT14 ORL long clusters and RW2-FD; the latched
  −2R stop tripped with 13-22 lots already open (in-poll overshoot).
- **Timing:** 10:00-11:59 entries carry the losses again in every account (as in giveback1019).

Did the live caps help (blocked signals priced in the what-if run, `nightly1020..1023/caps_out.txt`; slot effects ignored):
- **Twin-exposure cap: yes.** Blocked twin signals would have made −27.9R net: Testing 1 −14.8R (helped), Graveyard
  −15.3R (helped), Primary +0.7R and Testing 2 +1.6R (cost a little).
- **Per-setup −2R stop (10-20..10-22 in T1/T2, 10-21..10-23 Graveyard): mixed.** Testing 1's blocked signals would have
  made **+65.9R** (the stop cost money: RW7-FD alone +45.9R on 10-22), Testing 2 −26.3R and Graveyard −28.9R (helped).
  After ST-A (10-23) the two testing setups that would have tripped made +8.4R afterwards. Two-year history agrees for
  the testing books (S2 keeps 63-70% and loses in down sessions) and disagrees for Primary (S2 helps in every cell).

### Give-back proposals (at most 2; tested)
1. **ST-P — a latched per-setup −2R daily stop in Primary** (the only tested rule that cuts give-back without touching
   exits or winners and without costing avg R in any split or regime). Valid give-back mean −12% (11.9 → 10.5R), p90
   27.1 → 23.6R, worst day −71 → −46R, avg R −0.035 → −0.025, 90% of trades kept; t 3.32 < 3.79. The −3R version keeps
   95% and gives up only 2.4R of the 20 best days. Owner decision, see the inbox.
2. **None.** The second candidate set (one lot per symbol, cluster cap, post-peak side brake, late lock, open-risk bound:
   23 configurations) all fail: they either cost avg R in down sessions or cut 15-75% of trades. No second proposal
   rather than an over-correction.

## 4. Week scorecard 10-19..10-23 (paper, costs in; journal `pnl_adj`, avg R = pnl_adj / $ risk)
| account | trades | win % | avg R | P/L | green days | last week (10-12..10-16) |
|---|---|---|---|---|---|---|
| Primary | 311 | 59 | +0.125 | **+$540** | 1 of 5 (10-22 +$1,369) | −$866 |
| Testing 1 | 1,034 (+132 est. 10-19) | 53 | −0.069 | −$152 | 2 of 5 | −$2,504 |
| Testing 2 | 828 | 65 | −0.000 | +$345 | 3 of 5 | −$4,134 |
| Graveyard (from 10-21) | 902 | 54 | −0.148 | −$2,737 | 0 of 3 | — |
| Gen | 80 | 49 | +0.071 | +$688 | 3 of 5 | — |
| **total** | | | | **−$1,316** | | |

- Testing 1 10-19 P/L includes 132 trades estimated from the journal gap (nightly1019 t1_missing); trade stats use the
  1,034 journal trades.
- **Primary's week is one day:** without 10-22 it is −$829. Positive-day streak **0**; **3 of 14** sessions green since
  10-06; since start −$1,113 (−20.6R). The live-funds hold stays (3 green in a row needed).
- Primary leaders (live since start, nightly1023): RW3-FD 78 trades +0.443R, RW5-FD 85 +0.398R, MF2-FD 51 +0.743R,
  MF4-h40-FD 56 +0.157R — each with a negative two-year backtest (−0.06..−0.08R for RW3/RW5). Laggard: MF1 25 trades
  −0.19R (MF1-D open). CWT14-failbrk-pdl-p10-lowvol-long 38 trades +0.034R / −$101 (review 10-27).
- Testing 2 best: CWT12-coil-k4-long, CWT14-failbrk-pdl-p10-long; worst CWT09-gapdn-vwaploss-g5-short (D2 open).
- Gen: GEN-261020-07 (RSI-slope AM hold-long) carries the week (+$612 on 10-23); GEN-261022-01 −$568 on 10-22.
- Week vs last week: every account better (Primary +$1,406, T1 +$2,352, T2 +$4,479), mostly because the weakest setups
  went to the Graveyard (its −$2,737 is where they now trade) and because of 10-22.

## 5. New setup ideas
- **`sat1024-pm-drift-continuation` (idea, 0 configs):** the late-lock test says trades +0.5R after 14:30 keep drifting
  into the close; a dedicated 14:30-15:00 continuation entry (day move ≥ X ATR, right side of VWAP, hold to 15:55) may
  capture it. Needs the frames + the 1-min cache after 15:00.
- Discovery scan: nothing new worth adding (above). The C7 ETF down-streak near-miss (sat1017) still waits for a
  sector-neutral pre-declaration.

## 6. Plan for next week (10-26..10-30)
- **Owner decisions open:** ST-P (new), MF1-D, D2 (from 10-23), N3, SO-CAP.
- **Mon 10-26:** first session of the 10 new GEN setups; OPS-POLL last check (close if T2/Gen ≥ 85% of Primary's polls);
  OBS-1023 (ST7Q, NS3V1 first signals; NS3-T2 twin group). **Tue 10-27:** PROMO-PDL first review.
- **If ST-P yes:** config change after the close only, ledger entry, `ledger check`, and the nightly ST-P monitor
  switches to live-vs-replay.
- **BDI weekdays:** (1) add the CWT04/09/12/13/14 family to the history signal cache (risk rules then cover Testing 2's
  busiest setups and Primary's missing CWT14-pdl-p10-lowvol); (2) `gb-1019-noise-floor-stop` widen-to-floor at the same
  $ risk (pre-declare 3 floors × 3 books); (3) `sat1024-pm-drift-continuation`; (4) C7 ETF sector-neutral version.
- **Message-board proposals (owner has not decided; proposals only, nothing built):**
  - *Borrow-fee modelling for shorts:* add a per-day borrow cost (ETB tier vs HTB) to backtest costs; HK-2 already shows
    many "not shortable" skips, so HTB names are partly excluded live but not in backtests.
  - *SSR flag on every short in backtests:* mark shorts on names ≥ −10% from the prior close (uptick rule, that day and
    the next) and report pop-fade vs breakdown shorts separately; breakdown shorts under SSR cannot short on the bid.
  - *Trade-through-only fills for limit targets:* paper fills targets on touch; score targets as filled only when price
    trades through by ≥ 1 tick (the replay engine already does this; extend to the lab and to the live P/L adjustment).
  - *Local slippage stress test:* re-score every live setup with slippage ×1 / ×1.5 / ×2 / ×3 and per-share +$0.01..0.03
    and report where each setup's expectancy crosses zero.
  - *NBBO at signal vs fill:* the journal `meta` already logs bid / ask / spread / quote age at submit; add the NBBO at the
    signal minute and a nightly table of signal-NBBO vs fill (bps and R) per setup.

## Backlog (`backlog_updates.py`, BACKLOG.md re-rendered)
New: `sat1024-rw-cluster-cap` (failed, 6), `sat1024-rw-post-peak-side-brake` (failed, 6), `sat1024-one-lot-per-symbol-2y`
(failed, 3), `sat1024-late-profit-lock` (failed, 6), `sat1024-pm-drift-continuation` (idea). Updated:
`st-a-1022-primary-setup-stop` → rework (+9, numbers above; decision ST-P), `nightly-1020-setup-loss-limit-open-risk`
→ failed (+3), `gb-1019-twin-setup-exposure` → failed, `nightly-1016-primary-one-lot-per-symbol` → failed.

## Files
`PLAN.md`, `exits.py` → `exits_out.txt`, `late_lock.py` → `late_lock_out.txt`, `book_sim.py` → `book_sim.csv`,
`book_sim_out.txt`, `stp2y.py` → `stp2y_out.txt`, `backlog_updates.py`. Scratch (`exits.parquet`, `lock.parquet`, ~10 MB)
deleted.

Educational only — not financial advice.
