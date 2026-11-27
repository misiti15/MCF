Educational only — not financial advice.

# MOVEHUNT_1127: can we see the day's big movers coming at 09:50? (verdict: LEAD)

## Plain-language summary
- **Yes, we can find the big movers ahead of time, at about 4-5× the random rate.** A simple model frozen on FIT (K6, a
  logistic score on the 09:30-09:49 range, opening volume vs normal, the gap, the market-relative move, the prior-day
  range) puts **23% of the day's top-2% remaining movers into its top-50 list on CHECK** (random 4.7%, lift 4.9, day t
  22.8) and **40% on T2** (random 12.7% because T2 has ~400 names, lift 3.1, t 27.0). Top-20 / top-100: CHECK 13% / 33%,
  T2 27% / 54%. The single best feature is the 09:30-09:49 range in ATR units (K3), then opening relative volume (K1).
  "Just liquid" and "just volatile" names (controls) do no better than random.
- **No, we cannot tell which way they will go.** On the top-20 list, "keep going the way the first 20 minutes went" is
  right 49% of the time (CHECK 49.2%, T2 49.5%); gap direction 48-50%. So the ranker finds *size*, not *direction*.
- **None of the 3 setups (6 setup-sides) makes money after costs.** Continuation (S1), fade (S2) and 20-minute-range
  breakout (S3) on the top-20 list are all negative on CHECK and on T2 at LIVE-L and at LR8 (best: S1-short CHECK
  −0.042 R/trade, t −1.9; S1-long CHECK −0.071, T2 −0.039). 0 of 6 pass.
- **What can be salvaged:** the list does pick *better* trades than random names under the same rule. For S1 (both sides)
  and S3-short the top-20 list beats a size-matched random draw by **+0.05 to +0.09 R/trade** on CHECK and T2 (paired day
  t 2.2-2.7, above 96-100% of 50 random draws). The fade (S2) gets no lift from selection. That makes K6 a candidate
  **priority / universe filter for setups that already carry a direction signal** — a LEAD, not a setup.

## Data, splits, rules
1-min RTH bars: data/cache_hist (1,226 symbols; FIT 141 sessions, CHECK 276) and data/cache_fresh (468 symbols; T2 427).
The repo has ~1,200 minute-history names, not the full ~3,000 universe, and no premarket bars, so "gap" = 09:30 open vs
prior close. Locked block 2024-11-01..2025-02-28 never read (pyarrow filter + asserts in build.py and score.py). Eligible:
price ≥ $5, adv20 ≥ $20M, ATR14 known (~1,100 names/day CHECK, ~980 FIT, ~400 T2). Shorts need easy_to_borrow
(data/universe.csv snapshot — not point-in-time; disclosed). Target = |close − P50| / ATR14, P50 = the 09:49 bar close,
top 2% per day. Costs: LIVE-L (primshorts_1126 cells_live.json, scored) and LR8 research. Pre-registration:
PREREG.md (committed before scoring). No live trades of these rules exist, so no live window and no ledger overlap
to note.

## Configurations
14 this study (8 rankers + 6 setup-sides). Cumulative ≈ 8,952 → ≈ 8,966. Per-study setup bar t ≥ 3.0 CHECK / 2.0 T2.

## Rankers — capture of the top-2% remaining movers (day mean; base = N / eligible)
| Ranker | CHECK @20 / @50 / @100 (lift @50, t) | T2 @20 / @50 / @100 (lift @50, t) |
|---|---|---|
| K1 rvol | 0.111 / 0.194 / 0.283 (4.13, 20.4) | 0.235 / 0.370 / 0.501 (2.91, 25.2) |
| K2 gap | 0.099 / 0.154 / 0.215 (3.27, 13.6) | 0.193 / 0.287 / 0.394 (2.25, 16.7) |
| K3 20-min range | 0.122 / 0.210 / 0.298 (4.49, 21.7) | 0.250 / 0.371 / 0.514 (2.91, 24.7) |
| K4 prior-day range | 0.043 / 0.098 / 0.162 (2.09, 11.0) | 0.117 / 0.216 / 0.357 (1.69, 10.8) |
| K5 combo (rvol+gap+rng) | 0.124 / 0.204 / 0.294 (4.35, 20.3) | 0.236 / 0.361 / 0.510 (2.84, 24.4) |
| **K6 logit (FIT-frozen)** | **0.134 / 0.230 / 0.325 (4.90, 22.8)** | **0.265 / 0.397 / 0.538 (3.11, 27.0)** |
| K7 dollar volume (ctrl) | 0.013 / 0.029 / 0.063 (0.61, −7.0) | 0.037 / 0.097 / 0.216 (0.76, −5.0) |
| K8 ATR% (ctrl) | 0.010 / 0.034 / 0.076 (0.72, −3.9) | 0.069 / 0.144 / 0.275 (1.13, 2.4) |
Base rates: CHECK 0.019 / 0.047 / 0.094; T2 0.051 / 0.127 / 0.255. FIT agrees (K6 @50 0.298, lift 5.7).
K6 coefficients (FIT, standardised): range +0.44, rvol +0.26, idio +0.15, prior-day range +0.09, atr% +0.04, gap +0.03,
dollar volume −0.09, first-20-min net move −0.22 (a big range that closes back near the open is the best tell).
Top-mover rate by K6 decile, CHECK: 0.6% (bottom) … 2.7% (9th) → 6.7% (top); T2 0.7% … 7.1%. The signal is concentrated
in the top decile.
Secondary targets (K6 @50, not scored): open-to-close movers CHECK 36% (lift 7.7; flattered — the first 20 minutes are
inside both the feature and the target), max excursion after 09:50 CHECK 29% (lift 6.2), T2 47% (lift 3.7).
Direction on the K6 top-20 list (CHECK / T2): continuation hit 49.2% / 49.5% on all listed names; 55.6% / 54.9% on the
listed names that became top movers (only known after the fact); gap direction 49.8% / 48.4%.

## Setups on the K6 top-20 list (LIVE-L avg R/trade | LR8; day-clustered t; control = size-matched random draw)
| Setup-side | FIT | CHECK (n, LIVE-L, LR8, t) | T2 (n, LIVE-L, LR8, t) | vs random CHECK / T2 (diff, paired t) | Pass |
|---|---|---|---|---|---|
| S1 CONT long | +0.022 | 2,896, −0.071, −0.036, −3.0 | 4,442, −0.039, −0.008, −1.7 | +0.062 (2.5) / +0.055 (2.2) | no |
| S1 CONT short | −0.100 | 2,541, −0.042, −0.010, −1.9 | 4,024, −0.088, −0.066, −3.6 | +0.077 (2.7) / +0.063 (2.2) | no |
| S2 FADE long | −0.098 | 2,612, −0.166, −0.151, −3.7 | 4,077, −0.091, −0.093, −2.1 | −0.006 (−0.1) / +0.032 (0.9) | no |
| S2 FADE short | −0.164 | 2,828, −0.123, −0.121, −2.6 | 4,411, −0.151, −0.175, −3.8 | −0.010 (−0.2) / +0.039 (1.0) | no |
| S3 ORB long | +0.008 | 1,595, −0.099, −0.062, −3.1 | 2,611, −0.049, −0.019, −1.6 | +0.056 (1.7) / +0.086 (2.7) | no |
| S3 ORB short | +0.015 | 1,350, −0.057, −0.024, −1.9 | 2,268, −0.145, −0.123, −5.0 | +0.088 (2.4) / +0.047 (1.4) | no |
One-big-day check: every CHECK/T2 total is negative, so best-day share is undefined; avg R without the best day is
lower still (e.g. S1-short CHECK −0.049, S1-long CHECK −0.077). FIT S1-long (+0.022) is 52% one day (`1 day`), S3-long
134% (`1 day`). Gross R before costs is ≈ 0 (S1-short CHECK +0.027, T2 −0.003): costs (~0.04-0.07 R/trade LIVE-L) turn a
coin flip into a loss, as the direction result predicts.
Family split (CHECK+T2 pooled, LIVE-L): of 6 setup-sides × 5 cells (gap ≥ 1 ATR-pct / < 1, price < $20 / 20-100 / 100+)
= 30 cells, 2 are positive (S1-long px<$20 +0.022, S3-long px<$20 +0.033, both small) and 28 negative (−0.03 to −0.23).
Gap ≥ 1 ATR (the earnings-like proxy) is no better than no gap except for S1-short (−0.027 vs −0.091).

## Finalists (all reported)
K6 ranker (strong: lift ≥ 2 and t ≥ 3 on CHECK and T2 — passes the descriptive bar); S1-long, S1-short, S2-long,
S2-short, S3-long, S3-short — all FAIL (gate 1 costs, gate 2 t, gate 3 one-big-day; gate 4 control passes for S1 both
sides and S3-short only).

## Verdict: LEAD
A strong, stable mover ranker (4-5× random on CHECK, 3× on T2, controls null) with no tradeable edge on its own because
it has no direction skill. The next step — and the reason for optimism — is that its selection lift (+0.05-0.09 R/trade
vs random under the same rule, both periods) is the size of the gap between the book's current small losses and a
small win: pair it with something that knows direction.

## Backlog proposal (for the synthesis step; not written to research/backlog.jsonl here)
`{"id": "MH-K6-PRIO", "title": "Move Hunt K6 09:50 mover score as a priority/universe filter for directional setups",
"idea": "Score every name at 09:50 with the frozen K6 logit (research/movehunt_1127/score.py: 20-min range/ATR, rvol vs
20-day same-window median, |r20 - SPY r20|/atr%, prior-day range/ATR, gap/atr%, log adv20, net 20-min move/ATR). Test (a)
restricting each existing directional setup's signals to K6 top-decile names and (b) using K6 rank to order entries when
slots are capped. Score per setup (how many improve / worsen and by how much), LIVE-L, vs a size-matched random filter.",
"evidence": "research/movehunt_1127/REPORT.md: capture@50 lift 4.9 CHECK / 3.1 T2; selection +0.06-0.09 R/trade vs random
under the same rule (paired t 2.2-2.7); direction 49%", "kind": "filter", "status": "proposed"}`
Second, smaller: a direction study restricted to K6 top-decile names (which of the existing direction signals — Market
Compass side, VWAP side at 09:50, sector/ETF lead — call the side of names already known to be about to move big).

## Files
build.py (per symbol-day features, target, S1-S3 candidate trades; work files in scratch, deleted), score.py,
results.json, score_out.txt, PREREG.md (+ sha256).
