# QP1 (Scout, 2026-11-09 07:58 ET): ex-ante quiet-day predictors at 10:00 that are NOT from SPY's own range

*Educational only — not financial advice. Descriptive predictor test, no trades, no costs needed at this stage.*

Pre-registered before any data was downloaded or scored. Builds on QD1 (8 configs) / QR1 (3 configs), which found
SPY's own opening range does not flag quiet days (+17.6 / +5.5 pts). Bar from QD1: a predictor must beat the base rate
of quiet closes by >= 15 points in TRAIN and VALID, flag >= 10% of days in each.

- **Data:** Alpaca SIP 5-minute RTH bars, 2024-10-01..2026-11-06, SPY, VXX, XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY
  (all in research/lab_symbols.txt). **Locked block 2024-11-01..2025-02-28 dropped at load, never scored**; rolling
  windows use prior open sessions only.
- **Quiet close:** |SPY open-to-close| <= 0.25% (QDAY definition, as QR1). Split TRAIN < 2025-09-01, VALID >= 2025-09-01.
- **Features at 10:00** (bars 09:30..09:55, i.e. closes known at 10:00):
  - `fo10`   SPY % from open at the 09:55 bar close
  - `disp`   cross-sectional stdev of the 11 sector ETFs' % from open at the 09:55 close; `disp_ratio` = disp / mean disp
             of the prior 20 sessions
  - `vxx10`  VXX % from open at the 09:55 close
  - `cross`  number of sign changes of (SPY close − SPY open) across the six 5-min closes 09:30..09:55
- **Configs (4, all counted):**
  - Q1 `disp_ratio` in TRAIN bottom tercile and |fo10| <= 0.25
  - Q2 `vxx10` in TRAIN bottom tercile (vol falling at the open) and |fo10| <= 0.25
  - Q3 `cross` >= 2 and |fo10| <= 0.25
  - Q4 Q1 and Q2
- **Pass:** P(quiet | flag) >= base + 15 pts in TRAIN and VALID, flag share >= 10% in each. A passing flag goes to the
  Builder as a gate for counter-index / range entries (stage 2); a failing one is reported and parked.
