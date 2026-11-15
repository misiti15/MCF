# Scout's closed studies with their minimum detectable effects (guild standard, Lead lead-20261115-0100-1)
Educational only — not financial advice. SE = estimate / t from each study's own output (day-clustered or permutation SE as
scored). MDE80 = 2.8 x SE (80% power at |t| 2); 'at bar' = (bar + 0.84) x SE. Read every 'closed' as 'nothing above MDE; smaller unknown'.
| Study (output) | Quantity | Estimate (t) | SE | MDE80 | MDE at its bar |
|---|---|---|---|---|---|
| LEAD20 (lead20_out.txt) | SPY 10:30->close, broad vs other up mornings | +6.1bps (0.37) | 16.5bps | 46bps | 73bps (3.57) |
| ETFTIER (etftier_out.txt) | SPXL tiered - plain, per trade | -0.021R (-0.67) | 0.031R | 0.088R | 0.14R (3.57) |
| ETFTIER | SPXL tiered net per trade | -0.052R (-0.99) | 0.053R | 0.15R | 0.23R |
| SHORTUP (shortup_out.txt) | pick - same-minute strong movers, 10:30->11:30 | +0.0067 ATR (0.30) | 0.022 ATR | 0.062 ATR | 0.098 ATR |
| NEWSMID (newsmid_out.txt) | analyst-action excess to 15:55, ex-SPY | -0.024 ATR (-1.83) | 0.013 ATR | 0.037 ATR | 0.048 ATR (2.84) |
| DISP1 (disp1_out.txt) | flat-sector split, ex-sector to 15:55 | -0.028 ATR (-0.70) | 0.040 ATR | 0.11 ATR | 0.14 ATR (2.71) |
| COILGAP (coilgap_out.txt) | ex-mkt kept-book total vs shared-day random | -1.4R (z -0.01) | ~140R total (~0.03R per removed trade) | ~0.083R per removed trade | ~0.13R (3.57) |
| SIZETREND (sizetrend_out.txt) | path efficiency Q5 - Q1 after 10:00 | -0.0006 (-0.20) | 0.003 | 0.0084 (vs level 0.45) | - |
| ANCHOR950 (Skeptic's power check) | SPY 09:50->close, dip-then-turn days | +6.0bps (1.00) | ~6bps | ~17bps | - |
Reading: the index-level studies (LEAD20, ANCHOR950) can only exclude large effects (tens of bps). The trade-level ones (NEWSMID,
SHORTUP, ETFTIER) exclude effects down to ~0.04-0.09 ATR / R per trade. That is about the size of our round-trip cost (~0.03-0.07),
so 'smaller unknown' there mostly means 'smaller than costs'.
