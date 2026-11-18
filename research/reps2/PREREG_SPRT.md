# REPS2 item 4 — early decisions by a sequential test (PRE-REGISTRATION)

*Educational only — not financial advice. Written 2026-11-18 after the close, BEFORE the test is applied to any current
setup's record or simulated on the live records (only the pooled nuisance numbers σ² and ρ below were looked at). Not
edited after scoring: a later change is a dated addendum below the last line. Research only: no setup, exit, account or
config change.*

Owner (2026-11-17): "we have to be able to more quickly identify the 0 or low trade setups that could have high potential
that would otherwise take a month to test out through live." REPS2 item 4: a pre-registered sequential test (SPRT or
similar, costs in) that ends a setup's test early when the evidence is clear, with error rates.

## Data and unit (fixed)

- **Trades:** closed trades of the live run (journal run kind `paper`) on every mcf-data* state branch, pooled per setup
  name across accounts (as FASTDEC did). R after costs = `mcf.costs.cost_r` (pnl_adj / risk, LR8 live cost model). No
  clipping. Shadow, replay and 2-year numbers are never used (SRCV1: comparison only).
- **Unit = session:** for each setup and session s, `n_s` trades and `S_s` = sum of their R.
- **Model:** `S_s ~ Normal(n_s·μ, V_s)`, `V_s = n_s·σ²·(1 + (n_s − 1)·ρ)` (same-day trades move together).
  σ² (per-trade variance around the setup mean) and ρ (same-session correlation) are pooled moment estimates over all
  setups, recomputed each night from the sessions before the scored one (nuisance only; never tuned per setup).
  Value seen while writing this file (10-06..11-18): σ² = 0.728, ρ = 0.119.

## The test: two Wald SPRTs against break-even after costs

| test | H0 | H1 | α (false call at μ = 0) | β (miss at H1) | cross up (call) | cross down (no call) |
|---|---|---|---|---|---|---|
| FAILS | μ = 0 | μ = −0.20R | 0.05 | 0.20 | LLR ≥ ln(0.8/0.05) = **2.773** → **FAIL** | LLR ≤ ln(0.2/0.95) = −1.558 → "not a big loser" |
| WORKS | μ = 0 | μ = +0.20R | 0.05 | 0.20 | LLR ≥ 2.773 → **WORKS** (review flag) | LLR ≤ −1.558 → "not a big winner" |

Per session, `LLR += n_s·(μ1 − μ0)·(S_s − n_s·(μ0 + μ1)/2) / V_s`, summed over the setup's live sessions in date order.
The test stops at the first crossing (later sessions do not undo it).

**Guards (fixed):**
- WORKS also needs the owner's one-big-day check: avg R without the best session > 0 and best session < 50% of total R.
  Otherwise the verdict is `WORKS?-1day` and the test continues.
- **Truncation:** 60 active sessions or 600 trades without a crossing → `UNDECIDED (truncated)`, handed back to the
  standard rules (C3-ROT 15 days / 30 trades, C3-EXIT100, GY-LIFE).
- Verdicts are research flags only. A WORKS never promotes by itself (PROMO2 hold; Primary needs its full live record and
  the owner's yes). A FAIL in a testing account follows the standing moves (GY-LIFE / trimmed-setup rule), never a plain
  switch-off; before 15 active days / 30 trades it needs the owner's yes (C3-ROT), asked as a DECISION.

## Error rates — how they are checked (fixed)

1. **Wald bounds** (theory): P(FAIL or WORKS | μ = 0) ≤ α/(1−β) = 0.0625 each; power ≥ 0.80 at |μ| = 0.20.
2. **Parametric simulation** (20,000 paths per μ, seed 20261118): sessions with `n_s` drawn from the pooled empirical
   trades-per-session distribution, Gaussian sessions with the σ², ρ above; μ ∈ {−0.30, −0.20, −0.10, 0, +0.10,
   +0.20, +0.30}. Report P(FAIL), P(WORKS), P(truncated), average sessions and trades to a verdict (ASN).
3. **Block bootstrap on real records** (the check that matters: real fat tails and day effects): every setup with
   ≥ 15 live sessions; its sessions re-centred so its trade-weighted mean is exactly μ (same μ grid), then drawn with
   replacement in sequence until a verdict or truncation; 200 paths per setup per μ, seed 20261118. Report the same
   numbers pooled over setups. If the bootstrap false-call rate at μ = 0 exceeds 0.10 for either test, the test is
   reported as NOT fit for use and no decision is asked.
4. **Walk-forward on history:** each setup's record replayed session by session from 10-06; at the first crossing, the
   setup's later live avg R (sessions after the call, ≥ 10 later trades) is compared with the call's sign — precision with
   a Wilson 95% CI, against the base rate of later-negative setups.

## What is reported (fixed)

- The count of current setups (docs/live/assignments.json, any account) by verdict today, and per account; every FAIL /
  WORKS listed with trades, sessions, avg R, avg R without the best day, best-day share, LLR.
- Low-rep view: verdicts among setups with 0-10 live trades (expected: almost none; the test only calls big effects).
- **Configurations tried: 3** — primary δ = ±0.20R (the one used for decisions); sensitivity δ = ±0.15R and ±0.30R,
  reported only. α, β, truncation, guards and the data unit are not varied.
