# SRC-VALUE — how well each non-live source predicted LATER live results

*Educational only — not financial advice. Research only: no trading or config change was made here. Source names as in docs/GLOSSARY.md.*

Owner approval: 2026-11-16 ("src value, yes"). Run 2026-11-17 after the close. Script: `research/src_value/score.py`
(results: `src_value.csv` all rows incl. families, `per_setup.csv` per setup, `summary.json`).

## Method (fixed before looking at results)
- **Live**: closed trades of the live run (journal run kind `paper`) on every mcf-data* state branch (Primary, Testing 1/2,
  Gen, Graveyard, Live Lab, Explore 1, Testing D/E/F), pooled per setup. R after costs = pnl_adj / risk (`mcf.costs.cost_r`).
- **Later only**: for each source, only live trades dated *after* the source's data window count.
  | Source | Per-setup number | Data window ends | Later live from |
  |---|---|---|---|
  | 2-year screen | `docs/live/sim_inputs.json` backtest avg R (variant: valid-period R) — Generator runs 10-19..10-29 | 2026-10-07 | 10-08 |
  | 2-year backtest | `research/history2y/rescore.csv` exp R (variant: "unseen" pre-2026-03-10 exp R); exact name match, RW codes → the base live setup only (no -FD / -WB) | 2026-10-07 | 10-08 |
  | Session replay | `docs/live/replay.json` snapshot (09-01..10-21) avg R | 2026-10-21 | 10-22 |
  | Shadow | journal run kind `shadow` | first day 2026-11-17 | none yet |
- **Metrics** (per source, over setups with ≥ 10 later live trades; sensitivity ≥ 20):
  sign hit rate (source avg R sign = later live avg R sign), with the naive bar = share of setups on the majority live sign;
  optimism bias = mean over setups of (source − live) × n/(n+20) (shrunk toward 0 by live n); ratio = trade-weighted live avg R / trade-weighted source avg R;
  Spearman rank correlation; bootstrap 95% CIs (2,000 resamples of setups, seed 20261117).
- **Families**: name prefix (`shadow_calib.family_of`) with ≥ 3 setups, plus letter groups (MF*, NS*, RW*, ST*, CWT*).
- **Weight rule**: 0 unless Spearman CI low > 0 AND hit-rate CI low > naive bar (≥ 8 setups); then ρ_low × clip(ratio_low, 0, 1), capped at 0.35.
- **Configurations tried: 12** (6 source variants × 2 live-n thresholds); family rows are breakdowns, not extra configurations. Every one is reported below.
- No bars were read; the locked block 2024-11-01..2025-02-28 was never touched (the rescore file already excludes it).

## Results (all 12 configurations)

| Source (variant) | min live n | setups | later live trades | src avg R | live avg R | sign hit [95% CI] | naive bar | bias, shrunk [CI] | ratio [CI] | Spearman [CI] | weight |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2-year screen (avg R) | 10 | 68 | 4,483 | +0.055 | −0.189 | 34% [24, 46] | 69% | **+0.157** [0.11, 0.21] | −2.8 [−5.6, −1.2] | −0.02 [−0.25, 0.22] | 0 |
| 2-year screen (avg R) | 20 | 51 | 4,242 | +0.052 | −0.176 | 33% [20, 47] | 71% | +0.171 [0.11, 0.23] | −2.8 | +0.04 [−0.23, 0.32] | 0 |
| 2-year screen (valid R) | 10 | 68 | 4,483 | +0.035 | −0.189 | 29% [19, 40] | 69% | +0.143 [0.10, 0.20] | −4.1 | −0.03 [−0.28, 0.24] | 0 |
| 2-year screen (valid R) | 20 | 51 | 4,242 | +0.028 | −0.176 | 28% [16, 39] | 71% | +0.153 [0.10, 0.21] | −4.2 | −0.08 [−0.34, 0.21] | 0 |
| 2-year backtest (exp R) | 10 | 15 | 1,407 | −0.028 | −0.150 | 73% [53, 93] | 87% | +0.090 [0.04, 0.14] | 8.3 (unstable) | +0.04 [−0.47, 0.60] | 0 |
| 2-year backtest (exp R) | 20 | 14 | 1,389 | −0.027 | −0.131 | 71% [50, 93] | 86% | +0.083 [0.04, 0.13] | 8.2 (unstable) | +0.08 [−0.49, 0.67] | 0 |
| 2-year backtest (unseen exp R) | 10 | 15 | 1,407 | −0.064 | −0.150 | 87% [67, 100] | 87% | +0.064 [0.01, 0.12] | 3.3 [1.3, 10] | 0.00 [−0.54, 0.50] | 0 |
| 2-year backtest (unseen exp R) | 20 | 14 | 1,389 | −0.061 | −0.131 | 86% [64, 100] | 86% | +0.058 [0.00, 0.12] | 3.3 [1.2, 10] | −0.05 [−0.61, 0.51] | 0 |
| Session replay (snapshot) | 10 | 74 | 14,061 | −0.124 | −0.083 | 62% [51, 73] | 73% | −0.031 [−0.09, 0.03] | 0.90 [0.55, 1.42] | −0.03 [−0.29, 0.25] | 0 |
| Session replay (snapshot) | 20 | 64 | 13,899 | −0.110 | −0.083 | 69% [56, 80] | 75% | −0.025 [−0.08, 0.03] | 0.92 [0.56, 1.45] | +0.11 [−0.16, 0.38] | 0 |
| Shadow | 10 / 20 | 0 | – | – | – | – | – | – | – | – | 0 (no later live yet) |

Families (min live n 10; full rows in `src_value.csv`): no family has a Spearman CI above 0. 2-year screen = one family (GEN, 68 setups, same as ALL).
2-year backtest: MF* bias +0.071 [0.02, 0.14] (5 setups), NS* +0.091 [−0.01, 0.20] (5). Session replay: CWT14 (11 setups) +0.049 [0.01, 0.09] optimistic,
CWT* (25) −0.073 [−0.17, 0.01] pessimistic, MF* +0.094, NS* +0.055, RW* −0.076, ST* −0.029 (all CIs span 0); single small families swing both ways (CWT09 −0.50, L3 −0.24, CWT05 +0.14).

## Reading
- **None of the sources ranks setups**: every Spearman is ~0 with CIs spanning 0 (12/12 configurations). Knowing which setup scored best off-live told us nothing about which did best live afterwards.
- **2-year screen is clearly optimistic**: +0.16R per trade (shrunk), and its sign is right on only 34% of setups — worse than always guessing "negative" (69%). The valid-period number is no better. This fits the GEN graduation experience: positive screens, negative live.
- **2-year backtest**: optimistic by +0.06..+0.09R; its sign hit equals the naive bar only because nearly everything is negative both ways. The "unseen" pre-2026-03 number is the less optimistic variant. Only 15 setups — small.
- **Session replay snapshot**: level is about right (ratio 0.9, bias −0.03R, CI spans 0), so it is a fair *level* check for the book, but it has no per-setup rank skill. Consistent with the 87.1% held-out match → weight 0.
- **Shadow**: first day 11-17, nothing later to score. First measurable read once ~10 sessions of shadow + later live exist (≈ early December).
- What can be salvaged: replay's unbiased *level* and the screen's known, stable optimism (+0.15R) are usable as fixed haircuts in comparison columns; neither earns ranking weight yet.

## Proposal
**Keep every non-live source separate, comparison only — measured weight 0 for all four.** Already true for Session replay (0) and the 2-year screen/backtest in the blend (`history_in_blend: false`).
The one change: `config/effective_sessions.json` `history_weight` 0.175 (2-year history, screening / experience only) has no measured support → **0** (decision SRCV1, owner inbox 2026-11-17).
Method re-measured monthly (first Monday of the month, after the close): `python research/src_value/score.py`; a source earns weight only by the rule above.

## Rule changes inside the live windows (research/ledger.jsonl) — live results span these
10-12 SMA50 warm-up parity; 10-20 twin cap + per-setup −2R daily loss (Primary); 10-23 loss-stop latch, off in Testing 1/2 & Gen; 10-28 Primary position size ~$5k → ~$4k;
10-30 Testing 1/2 cost filter (skip stop round-trip > 0.15R); 11-12 LR8 live cost model in pnl_adj (earlier trades flat $0.02 stop allowance) and GEN-GRAD to Testing D/E/F;
11-17 SPYEXIT engine (WB4 variants), TSZ1 testing half-size lots (R comparable, $ not), KILL-FLAT Graveyard/Gen. Live R is pooled across accounts incl. Graveyard.

Educational only — not financial advice.
