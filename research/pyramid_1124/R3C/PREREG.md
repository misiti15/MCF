# PYRAMID R3 team C "fair costs" - pre-registration (written 2026-11-25 before any candidate is scored with either model)
Educational only - not financial advice. Research only; no config/setup/ledger change. Locked block 2024-11-01..2025-02-28 never read.
Disclosure: one unfiltered pyarrow read of data/cache_hist/1Min/SPY.parquet was made to print its min/max date (coverage check);
no locked-block value was printed, kept or scored.

## 1. Live-calibrated cost model (counts as 1 config)
Data: all closed run-1 live trades 10-06..11-24, 10 journals (git show, read-only), deduped; joined to their submitted signal
(ref_price = decision-bar close, verified median ref-vs-bar-close 0 by Team G; bar_time; spread_bps).
Per trade, in $/share (side-signed so + = cost):
  entry = side*(fill - ref_price) + LR8 entry 1 bp
  exit  = stop:   side*(engine_fill - fill) + LR8 stop cost, engine_fill = stop, or the exit-minute 1-min SIP open if it
                  already gapped through the stop (bench10 rule)
          market (flatten/timestop/spy_exit): side*(exit-minute 1-min open - fill) + LR8 market cost
          target: LR8 (limit; price improvement given back) = 0 slippage
  + LR8 regulatory fees (SEC/TAF/CAT) in the exit part.  Borrow: research 1.2 bp (shorts) kept unchanged (not observed live).
Exclusions: multi-part exits (scaled+*), |fill-ref|/ref > 2% (bad ref), missing exit-minute bar, price < $5.
Model: cell means in bps of price.  ENTRY cell = price bucket {5-10,10-20,20-50,50-100,100+} x entry time band
{<10:30, 10:30-12:00, 12:00-14:00, >=14:00}; EXIT cell = price bucket x exit kind {stop, market, target}. Cells with
< 50 fit trades fall back to the price-bucket mean. Trades winsorised at the 1st/99th pct of per-component bps before
averaging. No x3 extended tier (live cells already contain whatever such names traded); lab books drop entry < $5 anyway.
Fit/validate: the 36 live dates sorted; even positions = FIT days, odd = VALIDATION days. Validation report: mean
predicted minus realised cost in R (per unit of |ref - stop|) overall and by price bucket, stop width (risk in bps of
price: <50, 50-100, 100-200, 200+), time band, side, exit kind, for BOTH the research model (bench10 add_r) and the
calibrated model. The calibrated model is accepted if its overall |mean error| <= 0.01R and it beats the research model
in most buckets. The final model is then refit on all 36 days and frozen (cells.json) before any lab re-score.

## 2. Re-score (2-year lab: FIT 2024-10 + 2025-03..09 (170), CHECK 2025-10-01..2026-11-04 (276), T2 2023-01-03..2024-09-13 (427))
Same signal/exit files, same books as each source (bench10 book; ETB as source), r_gross unchanged; only the cost term
switches. Both models reported side by side. No rule re-tuning; no re-selection (each candidate's frozen pick is reused).
(a) top-10 benchmark (bench10 home books): L3-fromopen, RW3-FD, L3-lowdist, RW5-FD, L3-rsi5hi, RW6-FD, NM-RWN4, CWT14-orl-WB5,
    NM-ETF-late-dip, CWT09-g10 (the 3 last-generated with a reduced copy of bench10.py, SETUPS cut to those 3).
(b) gap-down short family: L3-fromopen/lowdist/rsi5hi, RW3, RW5, RW6 (as in (a)) + RW7-gapdn-bounce-early-short-FD (testing rules).
(c) Pyramid R1/R2 finalists and TIER B: S: GEN-261029-06, GEN-261023-06, ST5; L1: C1_D1_G2, C2_S03_G2, C3_V25_G2; L2: C1a, C2a,
    C3a, C4a; L3: A1, A1t, A2, A2t, A3, A3t, B1a, B2b, B3a; E: E1_X3_G2, E2_G10_G2, E3_S03_G2; G: B3a+TT1, NM-ETF+TT1, A1+TT1,
    C3+TT1, A3+TT1. ultimate_1119 candidates: re-costed only where the kept trade files carry price, risk and exit kind;
    otherwise bounded (the calibrated change cannot exceed the research cost itself) and stated as such.
Parity: each candidate's research-model numbers must reproduce its source report (+-0.005R) before the calibrated column is read.

## 3. Verdict rules (uniform, applied identically under both cost models)
TIER A: fit > 0, check > 0, check w/o best day > 0, 2023-24 (T2) > -0.02, check day-clustered t >= 1.5, check >= 1.0 trades/session.
TIER B: fit > 0 and check > -0.02 (or A short only on volume / t / T2).  FAIL otherwise.
BEATS TOP-10 (clear-cut): TIER A and, under the SAME cost model, check avg R and check avg R w/o best day above the best
of the top 10, and T2 avg R and T2 avg R w/o best day above the best of the top 10, and total R/session > 0 in both.
"Meets standard" (secondary): above the top-10 median on check and on T2 (same cost model).
Verdict changes are reported research -> calibrated for every candidate. Failures first.
Configs: 1 (cost model). Cumulative job N ~1,918.

## ADDENDUM 1 (2026-11-25 15:02 UTC; written after the calibration validation and a partial lab read of model 1, before
## any lab score of model 2). Disclosed deviations and one extra config.
- Data cleaning added after first look at validation (not in the original text): drop trades whose exit-minute bar is
  > 10% from the fill (split-adjusted SIP bars: 82 trades) and stop exits filled > 0.25R better than the journal stop
  (stop had been moved: 274 trades). Validation then: research model under-predicts realised live cost by 0.042R/trade
  overall; model 1 error +0.000R; model 1 beats research in 4/5 price, 3/4 stop-width, 4/4 time buckets -> ACCEPTED.
- Model 1 is mis-specified on stop width (validation: over-predicts 0.098R for stops < 50 bp, under-predicts 0.02-0.03R for
  100 bp+), and an in-sample per-setup check shows it over-charges RW3/RW5/RW7 (~+0.03..+0.06R) and under-charges some
  GEN/NM-RWN4. The task brief names stop width as a calibration axis, so a MODEL 2 is added (config #2):
  ENTRY cell = price bucket x stop-width bucket {<50, 50-100, 100-200, 200+ bp of price}; EXIT cell = exit kind x
  price bucket x stop-width bucket; fallback (< 50 fit trades) to exit kind x stop-width, then to model-1 cells.
  Same winsorisation, same even/odd day validation; accepted under the same rule. Both models are reported; the verdict
  table uses BOTH and a candidate counts as "flipped" only if the flip holds under both models (no cherry-pick).
Configs now 2. Cumulative job N ~1,919.
