# W4-conditions: per-setup conditions map and one bespoke rule each — plan (written before any scoring)

*Educational only — not financial advice.* Crunch workstream W4 (owner crunch request 2026-11-18 ~16:30 ET). Research
and proposals only: no config, setup, exit, latch or runtime change; nothing merged that affects trading; no final
decision without the owner.

## Data
- Live trades: run_id 1 of the ten `mcf-data*` journals (Primary, On Deck, Testing A-F, Gen, Graveyard) as of the
  11-18 close. Window **10-06..11-17** (11-18 has no bar pack yet; its trades are left out and said so).
  R = pnl_adj / (|entry - stop| x shares), i.e. after costs (LR8 from 11-12; pnl_adj before that).
- **De-duplication:** the same setup on the same symbol/day with signals within 5 minutes in two accounts (twin
  copies, moves) counts once (earliest fill kept). Raw and de-duplicated counts are both reported.
- Setups: the **top 30 by live trades** (raw count, all accounts), plus the Primary six not already in it
  (addendum, same method), so every Primary setup is covered.
- Bars: release packs `bars-2026-10/11` (1-minute RTH, full live universe; 1-day for priors). SPY from the same packs.
  The locked block 2024-11-01..2025-02-28 is never read (no 2-year data is used here at all).

## Conditions (point-in-time at the signal; the bar that closed before the signal time)
1. `tod` minutes since 09:30 · 2. `gap` % open vs prior close · 3. `spy10` SPY % from its open to min(signal, 10:00) ·
4. `atr_pct` ATR14 (prior days) / prior close · 5. `price` · 6. `adv` log10 20-day $ volume · 7. `etf` (name-based;
categorical) · 8. `withday` side x % move open→signal (> 0 = trade is with the stock's day so far) ·
9. `vwap` side x (price - VWAP) / ATR · 10. `open` side x (price - open) / ATR · 11. `pday` prior-day % return ·
12. `or30` first-30-min range (or range so far before 10:00) / ATR.

## Map (descriptive)
Per setup, per condition: R by setup-specific tercile (n, avg R, total R, days); time of day also in fixed buckets
(09:30-10:00, 10:00-10:30, 10:30-11:30, 11:30-13:30, 13:30-15:00, 15:00+). Reported for every setup.

## Bespoke rule candidate (one per setup, ≤ 1 changed part, within C3-WB's ≤ 2)
- **Split:** each setup's own active sessions, ordered by date; first half = **fit**, second half = **check**
  (unseen when the rule is chosen).
- **Candidate set (68 per setup):** for each continuous condition (11), drop the lower or the upper tail at the fit
  quantile q ∈ {0.10, 0.20, 0.30} (66), plus `etf`: skip ETFs / skip stocks (2). Thresholds are frozen as values from
  the fit half.
- **Failure-mode choice on fit:** eligible = keeps ≥ 70% of fit trades and ≥ 90% of fit top-decile winners (top 10%
  by R) and the removed trades have avg R < 0. Pick the one with the largest fit gain in total R (= the condition tail
  where the parent's fit-half losses concentrate). If none is eligible, the setup gets "no rule".
- **Verdict on check (scored once):** Δ total R, Δ avg R/trade, keep %, top-decile retention, day-clustered paired t
  of the daily Δ (check days of the setup), filtered R without best day and best-day share, plateau (the same
  condition/tail at the other two q also Δ > 0 on check).
- **Pass (pre-registered):** check Δ total R > 0, keep ≥ 70%, top-decile retention ≥ 90%, plateau holds, and t ≥
  max(1.5, sqrt(2 ln N)) with **N = 68 x 35 = 2,380 → bar 3.94**. A **lead** = all of the above except t, with
  t ≥ the per-setup bar sqrt(2 ln 68) = 2.90. Everything else is reported as fail/no-rule.
- **Guardrails:** `L3-gap-slope-fromopen-FD` is protected (scored for the record; no proposal). CWT12/CWT14 are closed
  to new variants (P3 "Stop doing") — scored for the record; a pass there would only be a note, not a proposal.
- Caveats fixed in advance: a filter on live trades ignores the slot it would free; live R mixes rule epochs
  (ledger changes listed in RESULTS); samples are 5-30 sessions per half.

## Also
A framework proposal for per-setup bespoke rules in Primary (FRAMEWORK.md) with the evidence bar, drawing on this
run and research/l3_bespoke_1117/BESPOKE_RULES.md.
