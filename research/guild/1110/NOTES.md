# Research Guild — session 2026-11-10 (research files from branch `mcf-guild`)

*Educational only — not financial advice.* 2-year lab history (SIP 1-min, 2024-09-16..2026-11-09), production costs, next-bar
entries, stop-first; **locked block 2024-11-01..2025-02-28 never read**. Live figures are paper. Research only: nothing in config/,
mcf/, docs/live or the trading path changed. Board + running summary: `board.jsonl`, `summary/2026-11-10.md` on `mcf-guild`.
Files > 200 kB (tagged trade lists, compass backfill rows) stay on `mcf-guild`.

## Failures first — guild total since 11-09: 124 configs / looks scored, 0 setups pass
| Study | Looks | Bar (N) | Result |
|---|---|---|---|
| GATE2 C1m + GATE2-R rework | 4 + reporting | 2.80 (N 127) | timing beats a matched control in ATR (t 4-32) but ~0.02-0.03 ATR; rework gross −0.007..−0.021R → **GATE2 closed, 0 / 15** |
| STOPW minimum stop width | 4 | 2.65 (N 77) | 85% of the gain = size cut (post-hoc size control); stop effect negative on down days → closed |
| CWT14SKIP earnings check | — | 2.10 | 51.5% of skips in earnings blackout; blackout-free t 1.05 → closed |
| HODSEP v1 / v2 (descriptive) | 0 | — | v1 void (negative-index look-ahead, 66% of candidates); v2 ≈ 0 → closed |
| RCOMPASS midday-flip standby | 3 | 3.57 (N 2,605) | 357,664 afternoon trades: post-flip worse in 27-30 of ~65 family-sides; standby beats random ~half → closed |
| COILAM coil morning on/off | 1 | 3.57 | ex-market t 1.05, gross excess −0.029, up days −0.26R → fails |
| Morning-reading map (all families) | 2 | — | same sign TRAIN/VALID 19 / 37 (chance) |
| MFFRESHLOW | 2 | 1.50 (N 4) | t 0.89 / −0.36, retention < 90% → closed |
| SIZEBKT (descriptive) | 0 | — | direction-free brackets lose more where size is predicted → closed |
| FLOW1-2Y (owner queue) | 32 | 3.57 | TRAIN pick VALID t −0.26; restates SPY → **FLOW1 closed both halves** |
| EVD1 earnings reaction session | 4 | 3.31 (N 858) | mixed (11:30 TRAIN +0.078 / VALID −0.134 ATR) → closed by pre-registered rule; AMC-fade cell → forward-only FAMC |
| D2PM premarket direction | 3 | 2.97 (N 229) | neither L2 nor L3 beats the gap baseline → closed (kill line) |
| SZBAND / COMPCAL vol-scaled M1 | 1 + 1 | fixed rules | size band drifts with vol; vol-scaled M1 worse on FWD (t +2.14) → keep M1 |

## What passed (display, not a setup)
- **COMPCAL** (owner COMPASS task): the continuous line M1 — share of the prior 60 sessions whose move from time T to the close would not cross today's distance from the open — beats the card's cell table out of sample: Brier VALID 0.1241 vs 0.1299 (day-t −2.21), FWD 0.1106 vs 0.1191 (t −0.93); calibrated; prior-close side adds nothing. "Staying" is mostly arithmetic (Observer: +0.4 pt over the remaining-move benchmark). Next-interval direction stays 48-53%.
- **D3GEN**: a worst-quarter screen ranks live Generator setups (rho +0.24, perm p 0.037; bootstrap 90% CI +0.035..+0.437; leave-one-run-out +0.18..+0.31) where today's screen does not (+0.02); it ranks, it doesn't rescue (top third still −0.098R live). Pre-registered as a forward test.
- Tools: XA-PBO (CSCV; read with p_oos_loss), XA-EPROC (anytime-valid monitor; 20 sessions ≈ 0-19% power, 40-60 realistic).

Rule-change context for live windows: EXPO1109 temporary GEN moves 11-09/11-10 (reverted, effective 11-11); Graveyard moves 11-02 / 11-03; SO-1A 11-03; ROLL1 11-05; Owner CF cost filter Testing 1/2 from 10-30 (research/ledger.jsonl).
