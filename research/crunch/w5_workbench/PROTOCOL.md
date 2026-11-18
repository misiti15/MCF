# WB2 — Workbench evaluation protocol (proposal; needs the owner's yes, code WB2-PROTOCOL)

*Educational only — not financial advice.* This is a research-process change. It changes no trade by itself. Evidence
is in [RESULTS.md](RESULTS.md) (Parts A-D). It amends C3-WB rules 3-4 where they differ (research/workbench/RULES.md)
and keeps C3-WB rules 1, 2, 5 and 6: tune type by parent record, ≤ 2 parts, no automatic -FD copies, closed CWT12/14.

## Why change
- One fit pick out of 4-15 candidates on 3-13 sessions selects noise. Fit gain vs check gain: Spearman −0.26 (U7, 250
  candidates). Gates come out at −0.37 because a setup's level mean-reverts between halves (−0.22 over 71 setups).
- An unpaired copy-vs-parent record needs ~1,000-3,000 sessions to show +0.05R. A paired exit tune needs ~30-150.
- The common day factor (median r 0.37) and day clustering (design effect ~3.7) are the main noise sources, and pairing
  on the same signals cancels both (paired Δ ICC 0.04).

## The protocol

**W1. Unit of evidence = tune class x mechanism family.**
- A family is ≥ 3 live setups that share a mechanism tag (C3-MECH), e.g. gap-down short fades.
- A class is one change with one fixed parameter, e.g. "target 0.75x parent", "refire off" or "no entries after 13:00".
  The parameter comes from the mechanism, an earlier study or a round default. It is never searched on the data being
  scored.
- At most 3 classes per family per run, pre-registered in a PLAN.md commit before scoring.
- N for the bar = classes x setups, summed over the lineage.

**W2. Paired scoring on the parent's own signals.**
- Exit, refire and gate classes: per-trade Δ = R_variant − R_live on each live trade.
  - Exits: walk the 1-minute bars (stop first, target through by 3 bp, extra exit cost on early exits, live costs kept).
  - Gates and refire: Δ = −R of the trades removed.
- Classes that need trades the parent never took (later or larger exits, new entries): calibrated replay (W7) or the
  live shadow overlay (W6). Never an unpaired copy record.

**W3. Pooled estimate over all sessions.**
- Per setup: day-clustered mean Δ and SE (daily sums / trades).
- Per class: DerSimonian-Laird random-effects μ, τ, SE_μ. Use the larger of SE_μ and the day-clustered SE over all of
  the family's trades, because setups in one family share symbol-days.
- Robustness:
  - sign-flip permutation on pooled daily Δ (10,000 flips, fixed seed);
  - leave-one-week-out folds;
  - the class's avg R w/o best day vs the parent's, with the best-day share (1-day tag at ≥ 50%).

**W4. Pass rule (all must hold).**
- t = μ / SE ≥ max(1.5, √(2 ln N)).
- Permutation p < 0.01.
- ≥ 75% of leave-one-week-out folds have the same sign as μ.
- Avg R w/o best day not worse than the parent's.
- Per-setup adoption: only setups whose empirical-Bayes Δ_i = μ + τ²/(τ²+SE_i²)·(θ_i − μ) is > 0. The class is
  rejected if any shrunk Δ_i < −0.02R.

**W5. Harm findings are kept.**
- A class with t ≤ −bar (or permutation p < 0.01 on the negative side) goes into research/backlog.jsonl as a "do not"
  note for that family, with its numbers.
- The guardrail list stays as it is; WB2 adds family-specific notes.

**W6. Live confirmation: shadow overlay + sequential test.**
- A passing class runs as a journal-only overlay on the parent's live signals (run 3, same polls, no orders, no slot).
- Read-out: a normal-mixture SPRT on daily paired Δ, with mixture scale = the effect of interest (0.05R).
  - Stop for harm when e ≥ 20 on the negative side.
  - Confirm when e ≥ 20 on the positive side, or at the power horizon with t ≥ 1.645.
  - Power horizon: exits ≥ 120 paired trades and ≥ 15 sessions; gates ≥ 400 paired trades.
- Only after confirmation does a class become a proposal to change the parent (owner's yes; after hours; ledger;
  assignments.json if a setup moves; adversarial review if it touches Primary).

**W7. 2-year replay.**
- Weight 0 while the rule-21 audit fails.
- Once green: rerun W3 on replay as an independent pooled estimate, combined as a prior with weight equal to its measured
  out-of-sample agreement (Spearman of class effects, replay vs live).
- "Meets parent" in replay is never a pass (guardrail).

**W8. Reporting (every run).**
- Configs tried and the bar.
- Per setup: n, sessions, parent / variant avg R and avg R w/o best day (share), Δ ± SE, shrunk Δ, improve / worsen
  counts with R.
- Rule changes inside the window (ledger).
- The old-protocol answer on the same data, for contrast, until WB2 has a track record.

## Sizes to expect (Part B)
| design | +0.10R at t 1.645 | +0.05R at t 1.645 |
|---|---|---|
| unpaired copy vs parent | 1,250-2,600 trades (260-420 sessions) | 5,000-10,400 trades (1,000-1,700 sessions) |
| paired gate (drop 1/3) | 210-430 trades | 830-1,730 trades |
| paired exit / overlay | 64-80 trades (9-22 sessions) | 255-320 trades (33-85 sessions) |
| WB2 pooled family of 5 (paired exit) | ~1-2 weeks | ~28 sessions resolve ±0.03R |

## What this does not do
It does not make the setups better on its own. It stops the Workbench from shipping noise, which cost U7 −45.6R on check
and the old protocol −31.0R in the Part D demo. It also turns each run into a usable answer for the whole family, harm
findings included.
