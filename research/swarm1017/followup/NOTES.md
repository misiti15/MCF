# swarm1017 follow-up: Q9 locked look 1, Q10 index filter, Q11 exits (2026-10-17)

*Educational only — not financial advice. History backtests only (rule 7). Nothing here is paper or live.
Costs are always in. PLAN.md was written before anything was scored.*

## Failures first
- **Q9: all 3 near-misses FAIL locked look 1.** Each was scored once, as frozen.
- **Q10: 0 of 133 family configurations pass.** 12 "help" by the pre-declared definition, but every filtered family is still negative.
- **Q11: 0 of 117 exit configurations pass.** Breakeven, trailing and the regime-dependent 0.5R stop all make things worse or change nothing.

## Q9: locked block 2024-11-01..2025-02-28, look 1 (`locked_score.py`, `locked_look1.json`, `locked_trades_*.csv`)
**LOOK 1 OF THE RULE-19 LOCKED BLOCK IS NOW USED for these three lineages:**
- the L3/ST rework lineage (RST1);
- arena-index-etf (AR-ETF-late-dip-adx-long);
- arena-am-long (AR-AM-gapdown-capitulation).

Any later version from these lineages faces look 2, with day-clustered t ≥ 1.5. `MCF_HIST_ALLOW_LOCKED=1` was set only in this one process, which ran once.

| version | n (days) | exp R | day-t | excess vs random | up / flat / down exp (n) | verdict |
|---|---|---|---|---|---|---|
| RST1 (frozen prod_r cost) | 125 (14) | −0.170 | −2.63 | −0.168 | −0.196 (119) / +0.341 (6) / – (0) | **FAIL** |
| RST1 (x3 extended tier) | 125 (14) | −0.283 | −3.79 | −0.272 | −0.303 / +0.114 / – | **FAIL** |
| AR-ETF-late-dip-adx-long | 89 (29) | −0.285 | −1.77 | +0.038 (vs ETF-only random −0.026) | −0.028 (16) / +0.143 (9) / −0.410 (64) | **FAIL** |
| AR-AM-gapdown-capitulation | 88 (40) | −0.254 | −1.74 | −0.133 | +0.061 (28) / −0.568 (19) / −0.325 (41) | **FAIL** |

- RST1: 125 of its trades fall in Feb 2025, mostly on up sessions. It lost on the kind of day it was built for.
- ETF-ADX: it beat the random ETF control, but lost heavily in down sessions (−0.41R).
- AM-GAPDN: it lost in down and flat sessions.

## Q10: skip trades against the index (`extract.py`, `q10_index_filter.py`, `q10_family.csv`, `q10_results.csv`, `q10_summary.json`)
- **Data:** 70 setups, 988,664 trades (rework-parent families, as configured), open history only.
- **Configurations:** 133 family-level + 1,330 setup-level diagnostics + 1,964 in the sibling lineages (ix-gate 912 + regime1009 1,052). N = 3,370, bar t ≥ 4.03.
- **Pass: 0.** Every kept family list is still negative after the filter.
- **"Helps"** (better in train and valid, and above the 95th percentile of random skips), 12 configurations:

| family | best filter | base → kept exp R |
|---|---|---|
| MF | ANY 0.25 | −0.072 → −0.063 |
| RW | ANY 0.25 | −0.050 → −0.037 |
| ST | BRD 0.35 | −0.014 → −0.005 |
| CWT | QQQ 0.25 | −0.091 → −0.086 |

  - MF also helps under SPY 0.50, SPY 0.75, QQQ 0.25, QQQ 1.00, ANY 1.00 and BRD 0.25, with gains of +0.002 to +0.009R.
  - Walk-forward share stays at 0.06–0.29.
- **Where it hurts:** L3, NS and MISC get worse under every threshold. For L3 the blocked trades are positive: L3 shorts taken while SPY is up are its better trades, which is RST1's idea.
- **Comparison with the live week:** the swarm's live-week claim that against-index trades lose −0.24..−0.63R does not generalise over two years.

## Q11: exits on 1-minute paths (`q11_sim.py`, `q11_analyze.py`, `q11_results.csv`, `q11_parity.csv`, `q11_summary.json`)
- **Parity:** 1-minute baseline vs the 5-minute frames, correlation 0.95–1.00 per setup, mean within 0.005R (ST5: 0.03R).
- **Configurations:** N = 117, bar t ≥ 3.06. **Pass: 0.**
- **(a) Breakeven at +0.5R, MF:**
  - pooled Δ −0.008R (t −2.08), negative in train and valid;
  - 0.25R is worse (Δ −0.026, t −3.29); 0.75R gives Δ −0.005;
  - for MF4 (t05s1) it does nothing, because the target is hit first.
- **(b) CWT12/14 longs:**
  - 1R trail with the target kept does nothing, because the target is ≤ 1R;
  - with no target, every trail is worse (pooled Δ −0.025 to −0.042R);
  - it helps in up sessions (+0.17) and costs more in down sessions (−0.18).
- **(c) 0.5R stop by decision-time class:** every family Δ is ≤ +0.002R, and none has t > 0.5.
- **Live runner support:**
  - `be_at_r`, `trail_r` and `trail_after_r` are already per-setup config keys (runner.manage, engine.simulate);
  - "no target" needs a code change, because LabStrategy always sets the target (a GEOM like `t∞s1`, or a `target_r: null` param);
  - a regime-dependent stop needs code: a context-aware stop in LabStrategy._signal plus SPY fromOpen in the live lab frame.

## Amendments and caveats
- Not scored: 5 structural-exit (GEOM S) setups, namely CWT09 x3 and LIQ x2.
- The `new_high_100m` prefilter is ignored, because the mask's own bear_div covers it.
- MF5 and MF5-FD have the same window (950-1500), so the MF pool counts those trades twice.
- The random baseline is Bernoulli skips at the same rate, not an exact count.
- The sector map comes from linkage.csv, which was estimated on the open history. That is mild look-ahead.
- Survivorship: today's universe is applied to the past.

Scratch (trades and sim parquet) was deleted after use. To rebuild: `extract.py` takes about 40 min, `q11_sim.py` about 7 min.
