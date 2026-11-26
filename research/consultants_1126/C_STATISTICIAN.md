Educational only — not financial advice

# Consultant memo C (statistician): can "regime steering" of Primary be validated? (2026-11-26)

Independent review for the owner's brief of 11-26 ("diversify Primary, steer setups by Market Compass / regime, net positive daily").
Research only; nothing changed. **Live** = Primary via `footrace.live_trades` (LR8, 10-23..11-25, 24 sessions); **Shadow** = regime_switch
`shadow_scoreboard.csv` forward rows (11-11..11-25) and compass_gate `forward.csv` (from 11-20); **bench (E1/bench10)** = figures quoted from
primshorts_1126, squeeze_1125, breadth_1125, ultimate_1119/top10. Locked block not read. Configs tried here: **0** (re-analysis only); cumulative N ≈ 2,271.

## 0. Failures first: what the record already says
- REGSW (11-11): 0 of 74 switches passed; 62 of 74 "improve R" only because the lab lists lose money (TRAIN −19,920R). Only 13 beat
  the random-switch *mean* in VALID. REGX: a setup's best/worst state in TRAIN matches VALID 31% of the time vs 32% chance
  (rank corr −0.08). GATE1 0 of 112; BREADTH-1125 0 of 12 close-gates; day-type 0 of 67. Rule 26 lists day-type on/off switches as
  "ask the owner first"; the owner has asked, so this memo proceeds, but these priors set the bar.
- Primary is negative in every bench window (avg day CHECK −3.03R, T2 −1.75R) and live (**−5.89R/day, SD 17.7, red 16/24 = 67%,
  t −1.63, worst-5 −151.5R, w/o best day −7.88R**). Steering a negative-EV book shrinks losses; it cannot make it positive alone.

## 1. Power analysis (80% power; MDE = (t_bar + 0.84) · σ / √n)
σ: live Primary day SD 17.7R; live paired switch-difference SD 8.7R/day (GAP-U on Primary, 23% of lots switched); bench book day
SD ≈ 10R (from CHECK mean −3.03 and red 62.3%, normal approx; L3 alone 7.4R from its t −1.73 over 276 sessions); bench paired SD
≈ 5-5.6R (L3-out option: Δ +0.953R/session, t 2.83, n 276 ⇒ 5.6R).

| Sample | Quantity | MDE at t 1.96 | at t 3.03 (REGSW bar) | at t 3.93 = √(2 ln 2,270) |
|---|---|---|---|---|
| Live, 24 sessions | book avg R/day vs 0 | 10.1R | 14.0R | 17.3R |
| Live, 24 sessions | paired switch ΔR/day | **5.0R** | 6.9R | 8.5R |
| Bench, 860 sessions | book avg R/day | 0.95R | 1.3R | 1.6R |
| Bench, 860 sessions | paired switch ΔR/day | **0.48-0.53R** | 0.66-0.74R | 0.81-0.91R |
| Live, 24 / bench 860 | red-day % (paired, 23.5% discordant days as in squeeze_1125) | **28 pp** / 4.6 pp | — | 47 pp / 7.9 pp |

Read: 24 live sessions detect only a ~5R/day switch (nearly the whole −5.9R daily loss) and no plausible red-day change (28 pp).
The bench sees ~0.5-0.9R/day (15-50% of its book's daily loss): **select on the bench; live can only confirm a large effect or veto**,
and only if bench and live rank setup × state cells alike (REGX says not; §5 analysis 1).

Forward sessions needed (80% power, observed forward mean μ and SD σ per session; n = ((t+0.84)σ/μ)²):

| Shadow series (forward, 10 sessions) | μ / σ per session | n for t 1.5 | t 2.0 | t 3.03 |
|---|---|---|---|---|
| GAP-U ΔR, all accounts | +33.9 / 56.6 | 15 | 22 | 42 |
| GAP-U ΔR, all, without best day | +23.4 / 56.6 | 32 | 47 | 88 |
| GAP-U **excess over same-day random switch**, all | +12.1 / 44.8 | 75 | 111 | 206 |
| GAP-U ΔR, Primary only | +3.7 / 8.7 | 30 | 45 | 83 |
| GAP-U excess, Primary only | +0.45 / 2.2 | 134 | 198 | 368 |
| IDX3-P ΔR, all | +14.7 / 46.4 | 54 | 80 | 149 |
| IDX3-P ΔR, all, without best day | +1.5 / 46.4 | 5,530 | 8,146 | 15,127 |
| IDX3-P excess, all | +5.0 / 11.7 | 30 | 44 | 82 |
| IDX3-P ΔR, Primary only | +1.8 / 12.1 | 249 | 367 | 681 |

"Excess" = ΔR(OFF) minus the expected ΔR of switching the same share of that account-day's trades at random
(−share × base R). It is a proportional null computed from the scoreboard, cruder than REGSW's permutation, but it removes
"trading less of a losing list". The 20-session re-score due ~12-10 (pass rule: ΔR > 0 overall and on TEAM-6, selectivity ≥ 60%,
beats a permutation) has no t requirement; at 20 sessions the point estimates are noise for every Primary-level series.

## 2. Audit of the forward evidence (Shadow, 10 sessions 11-11..11-25; 11-13 is missing from the scoreboard — fix the gap)
| Config | Total ΔR | day t | best day (share) | avg w/o best | excess total (t) | sign-flip p (ΔR / excess) | Primary ΔR (best-day share) |
|---|---|---|---|---|---|---|---|
| GAP-U | +339.0 | 1.89 | 11-16 +128.3 (38%) | +23.4 (t 1.44) | +120.7 (0.85; best 65%) | 0.056 / 0.22 | +37.1 (75%, 11-11); excess +4.5 |
| IDX3-P | +147.1 | 1.00 | 11-25 +134.0 (**91%**, `1 day`) | +1.5 (t 0.21) | +50.2 (1.35) | 0.21 / 0.13 | +17.9 (177%); excess −0.9 |
| SPYO-P | +63.7 | 0.71 | 11-25 +83.9 (132%, `1 day`) | −2.2 | −46.7 (−1.80) | 0.37 / 0.95 | +0.9 |

- **GAP-U +339R is not one-day driven (38%), but it is not regime information either:** 78% of it (+264R) is the Graveyard, it
  switches 35% of all trades on days the base lost, and only +121R (t 0.85) survives the proportional null. On Primary it is +37R,
  75% from 11-11, and +4.5R of excess. Verdict: consistent with "trade less of a losing list"; no evidence of steering skill.
- **IDX3-P +147R is one day (11-25, the swing-midday-flip day): 91% share, +1.5R/day without it, t 0.21.** Primary-level excess is
  negative. Not meaningful. SPYO-P: negative excess, also carried by 11-25.
- Compass gate (frozen 11-19, 4 forward sessions 11-20..11-25): blocked 2,454 trades avg −0.275R, **session t −1.97** (trade t −17
  is not the honest one), best session 11-20 −400R = 59% of the saved 674R (fails check 3 today), families 20 better / 13 worse
  (lost 18R vs saved 692R). Primary: 22 blocked, −17R saved, session t −1.57; 11-25 (−42.3R live) had 0 Primary blocks. Its own
  backfill (11-06..11-18) had session t −0.34 and 164% best-day share, so 4 good sessions after a poor backfill are a lead, not a
  result. Scored once at ≥ 15 sessions and ≥ 40 blocked trades, as frozen. gate1-checkpoint-gate and comp15-w60-early tallies stop
  at 11-10 (3 sessions each): stale; re-run or retire explicitly.
- Rule changes in these windows (ledger): 10-28 sizing; 10-29 −2R latch; 11-11 TEAM-6; 11-12 LR8/LR3/restructure; 11-16 ROT1; 11-17 TSZ1;
  11-19 Epoch 1, NS5 out; 11-20 stop rounding; 11-23 burst brake, ST7 out. ΔR scales each trade's own R, but the trade set changed.

## 3. Pre-registrable validation protocol for regime steering (REGSTEER-1)
1. **Book and setups, fixed in the PREREG:** Primary's current 4 (L3-fromopen, RW3, RW5, NM-ETF) plus at most 4 named long
   candidates (e.g. NM-ETF+SPY≥open, GEN-261027-01). bench10 engine, Primary book rules, LIVE-L costs (primshorts_1126). No new engine.
2. **At most 2 state variables, both known at decision time and on the full 2023-26 bench:** S1 = SPY open gap tercile at 09:30
   (GAP-U's input); S2 = W60 compass confirmed side at entry (−1/0/+1, `compass_live.compute` on day packs; breadth for 2023-24 from
   breadth_1125). At most 9 cells per setup. No VIX, no sector, no per-setup fingerprints (REGX: they flip).
3. **Monotone, sign fixed a priori:** exposure = side × beta sign (compass_gate RULE §2 classes). Weight w ∈ {0, 0.5, 1} must be
   non-increasing as the state moves against the exposure (isotonic fit). The direction is never fitted.
4. **Hierarchical shrinkage:** trade R = μ_s + γ_{side,k} + b_{s,k} + u_day, with b_{s,k} ~ N(0, τ²) and a day random effect
   (day clustering), fitted by REML/empirical Bayes on the training fold only. A cell gets w = 0 only if the shrunk cell mean
   < −0.02R and P(< 0) ≥ 0.9; w = 0.5 if P ≥ 0.75; else 1. Pooling across setups is the default; a setup earns its own cell only
   through the data (τ² estimated, not chosen).
5. **Walk-forward:** expanding window, refit monthly, test the next month, 2023-01..2026-11 minus the locked block (≈ 40 OOS months,
   ≈ 860 sessions). The concatenated OOS daily book is the only scored series.
6. **Four nulls, each on the same OOS days:** (a) unsteered book; (b) a constant weight with the same average gross exposure;
   (c) random switches with the same per-day switched share (≥ 500 draws, 95th pct); (d) a side-only switch (no per-setup cells).
   Steering must beat (b) and (c), else it is a size cut, not regime skill.
7. **Grid and PBO:** ≤ 12 configs ({S1, S2, S1+S2} × {pooled γ only, hierarchical} × {OFF-only, OFF/HALF}). CSCV: 16 contiguous
   blocks, all C(16,8) = 12,870 splits, pick the IS-best by OOS-relevant metric (paired ΔR/day vs null c), PBO = P(OOS logit < 0).
   **PBO ≤ 0.20** (W6 found 0.74 for avg-R ranking). Hansen SPA / White RC over the 12 with a stationary bootstrap (mean block 5
   days): p ≤ 0.05.
8. **Prior tries:** report the deflated Sharpe at N = 2,271 (with the cross-trial Sharpe variance) for information, and require the
   walk-forward paired t vs null (c) ≥ √(2 ln N_lineage), N_lineage = every regime/gate/switch config ever tried (my count ≈ 400:
   REGSW 99, GATE1 112, COMP15 68, day-type 67, L3LEASH 12, BREADTH 14, regsw2 and Guild variants; the lead verifies) ⇒ **t ≥ 3.46**.
9. **Also required:** both halves positive (T2 2023-24 and 2025-26); ≥ 60% of OOS months positive; best-day share < 10%; per setup
   better/worse with R (no setup worse by > 2R/month; owner remedy rule); worst-5 improves ≥ 20%; locked block once, look 1
   bar t ≥ 1.0 (rule 19); then a journal-only live shadow of ≥ 40 sessions scored on excess vs null (c), power stated in advance.

## 4. An honest goal metric (replace "net positive daily")
With σ ≈ 18R/day, a book making +3R/day is still red Φ(−3/17.7) ≈ 43% of days; at σ 10R, 38%. Daily green is not a target.
| Metric (Primary, LIVE-L) | Now (24 sessions) | Stage 1 target (next 40 sessions) | Stage 2 |
|---|---|---|---|
| Red days per month (~21 sessions) | 14 (67%) | ≤ 11 (≤ 52%) | ≤ 9 (≤ 43%) |
| Worst-5-day sum, trailing 60 sessions | −151.5R (in 24) | ≥ −90R | ≥ −60R |
| 20-session rolling R floor | −80 to −143R | ≥ −40R | ≥ −20R, > 0 in ≥ 50% of windows |
| Avg R/day without best day, 40 sessions | −7.9R | ≥ −2R | > 0 |
Report all four weekly with n, SE, the one-big-day check and ledger rule-change dates.

## 5. The two analyses to run first, and what makes me say "build it"
1. **Bench-live concordance (cheap gate, 1 config):** for Primary's 4 setups, cell means on S1 × S2 from the bench (2025-26) vs live
   (all accounts, 10-14..11-25, LIVE-L), Spearman with a day-block bootstrap; plus the same for the sign of γ_{side,k}. If ρ ≤ 0.2
   or its 90% CI includes 0, bench-trained per-setup steering cannot be trusted live: stop at a side-level rule (S1/S2 × exposure).
2. **REGSTEER-1 walk-forward + CSCV (§3), ≤ 12 configs**, pre-registered with sha256 before any score.
**"Build it" (as a journal-only shadow, then a Friday epoch):** ρ ≥ 0.3 with CI > 0; OOS paired gain vs random-switch null
≥ +0.5R/day with t ≥ 3.46; PBO ≤ 0.20 and SPA p ≤ 0.05; beats the constant down-weight; both halves and ≥ 60% of months
positive; worst-5 ≥ 20% better; no Primary setup worse by > 2R/month. Anything less: label it insurance, not edge, or drop it.
