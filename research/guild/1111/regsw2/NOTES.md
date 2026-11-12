# REGSW-2 — results (Builder, 2026-11-11 evening). Educational only — not financial advice.

Plan: PLAN.md (frozen 08:45 ET), Skeptic audit skeptic-20261111-0902-3 applied: GAP state copied from Phase 1's
score.py (th(gap, 0.0025); gap NaN after the locked block), shared-day permutation null for S1, live check in-sample.
Base (stage 1, committed 57911e03c before scoring): 11 setups with TRAIN gross > 0 AND live net > 0 (>= 20 trades);
48,450 lab trades after the earnings blackout (15.7% removed), 449 days. Configs: 4 (lineage N 103, BAR90 2.74).

**Result: 0 of 4 pass.**
- S1 GAP-U: beats the shared-day null's MEAN, but not its 95th percentile in any period
  (net delta TRAIN -141 vs null mean -105 / 95th +1,225; VALID +420 vs -154 / +607; FWD +13 vs +126 / +500).
  The per-setup better/worse check does not apply to S1: it switches whole setup-days off, so the within-setup-day
  control is zero.
- S2 CHK, S3 W60, S4 SPYFO: excess NEGATIVE in TRAIN, VALID and FWD, gross and net. Net t: ALL -3.33 / -2.80 / -2.37,
  VALID -2.31 / -2.78 / -3.42. Most setups get worse (S3: 11 of 11 in VALID). Mostly shorts.
- Not pre-registered, so an observation only: on this short-heavy winning base, entries taken AGAINST the market state
  do BETTER than the same setup-day's other entries. That matches 'fade the market' setups. |t| 3.42 is below the
  market-state family BAR90 3.57.
- Rule-change context: lab lists, no live rule changes involved; the base selection used live journals to 11-10
  (TEAM-6 move on 11-11 is after the window).
- PBO not computed: with every config's excess negative or below the null, selection among them is moot.
- Live check: in-sample by construction (Skeptic), and moot after 0 of 4.

## Follow-up (Skeptic 11-11 16:51): ex-market and full base (exmkt_out.txt; same 3 switches, reporting only)
- Full 75-setup lab base: the "against the state is better" contrast is LARGER (VALID gross t -5.9 / -5.9 / -6.3),
  so it is book-wide, not a product of how the 11 winners were chosen.
- Ex-market (gross - TRAIN-fitted beta x SPY % over the trade's own hold) removes ~70% of it. On the full base VALID
  ex-market t is -3.05 / -2.13 / -3.28; TRAIN -2.08 / -1.03 / -1.62; FWD mixed. It is mostly SPY mean-reverting after it
  leaves its open. The residual is below the market-state family BAR90 3.57: nothing to pre-register yet.
