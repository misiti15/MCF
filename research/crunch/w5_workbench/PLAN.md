# W5-workbench — pre-registered plan (crunch 2026-11-18, written before any scoring)

*Educational only — not financial advice.* Research and proposals only: no config, setup, exit, latch or runtime
change; nothing merged that affects trading. Promotion hold on. L3-gap-slope-fromopen-FD is not tuned (protected).
Locked block 2024-11-01..2025-02-28 not read (no 2-year data used at all).

## Question
Today ~100+ Workbench tunes (U7 20 picks / 265 candidates, U8 10 / 1,100, L3 bespoke 21, P4 73, W4 2,176) passed or
looked good in-sample and failed on unseen sessions. Why, how much data a real +0.05R / +0.10R tune needs to show,
and what protocol could find real improvements.

## Part A — diagnosis (descriptive; re-uses earlier outputs, no new tune configurations)
- A1 U7 (research/usage/u7_workbench/u7_candidates.csv, 250 eligible candidates): Spearman and OLS slope of check gain
  on fit gain; fit vs check gain of the 17 chosen tunes (winner's curse); split by tune kind (exit / gate).
- A2 Pooling retro-test on the same U7 file: group candidates by tune class (14 one-gate classes x 16 setups, exit
  classes x 4). Compare (a) the class's summed fit gain vs summed check gain (Spearman across classes) with
  (b) per-setup selection. Also "class-level choice": pick the class with the best pooled fit gain, apply it to every
  setup, score check. No new configurations (U7 already counted them).
- A3 L3 bespoke (research/l3_bespoke_1117/C_workbench.csv, 21 variants): Spearman of Δ vs parent across replay /
  2-year TRAIN / VALID / FWD.
- A4 Noise model from the live journals (run 1, all ten accounts, 10-06..11-18, R after costs, identical signals in
  more than one account counted once): per-trade SD of R; day-level intra-class correlation within setup and the
  design effect 1 + (m-1)·ICC; trades per traded day; how much of a setup's daily R moves with the same-day mean of
  all other setups on the same side (common day factor = regime); fit→check level shift of the setups' avg R.
- A5 Multiple testing: expected max of K null t-statistics (K = 5, 15, 20, 265) vs the bars used.

## Part B — power (formula, with the A4 noise numbers and the Part D paired SDs)
Trades n (and sessions) needed for 80% power to detect δ = +0.05 and +0.10 R/trade at one-sided bars t = 1.645, 2.45,
3.34, for: (i) unpaired copy vs parent (two separate records), (ii) a paired gate (drop a share p of the parent's own
trades), (iii) a paired exit tune on the parent's own trades. Day clustering via the design effect.

## Part C — protocol proposal (WB2), written from A/B.

## Part D — one demonstration of WB2 on 5 setups (the only new configurations)
- Setups (fixed by rule, before scoring): one mechanism family = gap-down short fades with fixed targets, ≥ 150 live
  trades and ≥ 20 traded days, excluding the protected L3-fromopen and closed CWT12/14:
  RW7-gapdn-bounce-early-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, RW3-gapdn-rsi5pop-flowsell-short-FD,
  RW1-gapdn-bounce-flowsell-short-FD, L3-gap-slope-rsi5hi-FD.
- Tune classes (exit-only, allowed on proven parents under C3-WB; each a fixed parameter, no search):
  X1 target at 0.75 x the parent's target distance; X2 stop to break-even (entry) once MFE reaches +0.5R;
  X3 60-minute time stop if MFE so far < +0.25R.
- Configurations: 3 x 5 = **15**. Bar t ≥ max(1.5, sqrt(2 ln 15)) = **2.33**.
- Counterfactual: each live trade walked on 1-minute SIP bars (release packs bars-2026-10/11, streamed) from the entry
  minute up to the live exit; the variant can only exit earlier than live (otherwise it keeps the live R). Inside a
  bar: stop first (conservative), target needs a 3 bp touch-through (U7 rule), break-even and time-stop exits pay
  max($0.01, 1 bp)+$0.01 per share on top of the live trade's costs. Trades with no bars keep their live R.
- WB2 scoring per class: paired per-trade Δ = R_var − R_live; per setup a day-clustered mean Δ and SE (daily sums /
  trades); pooled class effect by random-effects (DerSimonian-Laird) over the 5 setups; empirical-Bayes shrunk
  per-setup Δ = μ + B(θ_i − μ), B = τ²/(τ²+SE_i²); sign-flip permutation test on pooled daily Δ (10,000 flips, seed
  20261118); leave-one-week-out sign stability; a normal-mixture sequential test (mSPRT) on the pooled daily Δ with
  the first session where the e-value reaches 20 (α = 0.05) in either direction.
- **WB2 pass rule for a class** (all): pooled t ≥ 2.33; permutation p < 0.01; ≥ 4 of 5 shrunk per-setup Δ > 0 and none
  < −0.02R; positive in ≥ 75% of leave-one-week-out folds; pooled variant avg R w/o best day ≥ parent's.
- Contrast (old protocol, same data): per setup pick the best of X1-X3 on the earlier half of its sessions, score on
  the later half; report agreement with WB2.
- Report per setup: n, days, parent avg R / w/o best day (share), variant the same, Δ, improve/worsen counts.
- A pass is a proposal only (paired shadow A/B of a WB copy, owner's yes needed); a fail is reported with its numbers.

## Rule changes to note
From research/ledger.jsonl for 10-06..11-18 (listed in RESULTS.md).
