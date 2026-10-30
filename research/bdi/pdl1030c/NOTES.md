# pdl1030c: one extra indicator on the two demoted pdl longs (owner 2026-10-30)

Educational only — not financial advice.

Setups: CWT14-failbrk-pdl-p05-long, CWT14-failbrk-pdl-p05-lowvol-long (moved to the Graveyard 10-30).
Top 10 indicators our live setups use (pick agent): move from open (35 setups), VWAP position/cross (34), RSI(14) (21),
order-flow lead buyPressure/flow3 (21), RSI(5) (20), index context (18), gap (16), 5-min SMA50 (16), MarcoFlow heat (15),
relative volume (10). Each added alone, on the parent exits and on the S3 (3x stop, same $) + cost<=5% base.
**69 configs, 0 pass** (BAR90 t >= 4.355, N 121,705). No row positive on both TRAIN and VALID; best t 0.0. Parity exact.
Best rows: p05 S3+cost5 + buyPressure > 0: +0.005 / -0.005 at 22/session; p05 S3+cost5 + close below SMA50: -0.003 / -0.008 at
49/session; heat > -20: -0.003 / -0.007 at 48/session. Indicators either cut volume 70-95% or move avg R by < 0.01R. Every row
still makes a little on SPY up days and loses on down days. Per-agent folders: ind1..ind5 (PLAN, NOTES, results, scripts).
Lineage total now 245 configs across pdl1030 / 1030b / 1030c.
