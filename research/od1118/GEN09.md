Educational only — not financial advice.

# W2-HK-GEN09 — GEN-261022-09 burst on 11-17 (owner housekeeping yes 2026-11-18; diagnostic only, no change)

Setup: `GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short` (Gen until 11-18; Graveyard from
11-19 under C3-EXIT100). Data: Gen live journal (run 1, mcf-data-gen as of the 11-18 close); R after costs = pnl_adj / risk.
Configurations tried: 0 (descriptive).

## What happened
- **144 short entries in three minutes (10:55 / 10:56 / 10:57 ET: 32 / 50 / 61, plus 1 at 11:01), 144 different symbols,
  one lot each.** 126 stopped out, 18 flattened: **−134.6R, −$349.4** after costs.
- Every entry came from the same 5-minute decision bucket: the setup's conditions (15-minute return ≤ −0.16 ATR, bar range
  ≥ 0.11 ATR, ADX(7) ≥ 64, AM window, below VWAP) are market-wide on a broad sell-off bar, so the setup fired on most of
  the universe at once. It was **one index bet split into 144 lots**, then the market turned up.
- The Gen per-setup cap was 150 positions, so nothing stopped the burst (144 < 150). Signals not taken: 12 size < 1 share
  after the liquidity cap, 5 not shortable/ETB, ~10 spread / spread-vs-stop, 1 crosscheck.
- **Stop slippage is real but secondary:** stop exits median −1.23R (mean −1.28R; 16 of 126 worse than −1.5R). Stops were
  tight (median 0.50% of price, median risk $2.37 per lot), so the LR8 stop cost plus entry cost alone is ~0.1R, and the
  fill beyond the stop added a median 0.07R (10th percentile 0.21R). No reconcile or cap bug found.
- Record: 211 trades on 3 sessions (11-05 57 trades −42.7R, 11-10 10 −4.5R, 11-17 144 −134.6R): every session negative.

## Where it stands
- Already handled by approved rules: C3-EXIT100 moved it to the Graveyard from 11-19, where the per-setup cap is 75
  positions and the per-setup −2R latch applies (the latch would have stopped new lots after the first ~2R of realized loss;
  the 11-17 burst entered before any stop filled).
- The general failure mode ("a lab setup firing on ≥ 20 symbols in one poll = one index bet") is already the backlog idea
  `nightly-1029-burst20-one-bet` (BL-1029). This case is added there as evidence; no new rule is proposed (Remedies rule:
  a burst cap must be tested across setups, not tailored to this one).
