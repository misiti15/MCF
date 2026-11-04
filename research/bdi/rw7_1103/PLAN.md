# rw7_1103 — RW7-gapdn-bounce-early-short-FD: live record, drivers, small variant grid (PRE-REGISTERED)

*Educational only — not financial advice.* Written 2026-11-03 ~20:00 ET before any variant below was scored.
Research only: nothing in config/ or the trading path changes.

## Parent (P0) — as live in Testing 1
short; MarcoFlow heat <= -20, buyPressure < -0.15, 55 <= RSI(14) <= 65, gap < 0; decision bar close 09:50-15:00;
adv20 >= $95M; first signal per symbol-day (no refire); t1s1 (R = 0.25 x daily ATR), out 15:55.

## Data, costs, splits
- Two-year lab frames (research/history2y/lib; locked block 2024-11-01..2025-02-28 never loaded, MCF_HIST_ALLOW_LOCKED unset).
- Exits simulated on SIP 1-min bars (data/cache_hist/1Min) from the minute after the decision bar close, entry at the
  decision-bar close, stop first inside a bar, out at the 15:55 close. Sanity: simulated t1s1 must match the lab's
  r_short_t1s1 on the parent (report agreement).
- Cost per trade = max(0.10R, production model): (1c + 1 bps) x time-of-day entry multiplier, + (1c + 1 bps) on non-limit
  exits, + 2c on stops; x3 on extended-tier names (|gap| >= 20% or price < $5). Production-only cost reported too.
- Train = open months <= 2025-12-31; valid = 2026-01..2026-10-16. Choose on valid only after train is positive.
- Random baseline: short entries at the same date and bar close on adv20 >= $95M names (random 3% sample of all such bars,
  same exits and costs), matched to each config's (date, tod) distribution.

## Grid (24 configs; every one reported)
| id | change vs P0 |
|---|---|
| P0 | parent |
| W1 | entry bar close 10:30-15:00 |
| W2 | 10:30-13:00 |
| W3 | 09:50-14:00 |
| R1 | RSI 50-60 |
| R2 | RSI 60-70 |
| H1 | heat <= -24, bp < -0.18 (20% tighter) |
| H2 | heat <= -16, bp < -0.12 (20% looser) |
| E1 | t1.5s1 |
| E2 | t0.5s1 |
| E3 | half off at +0.5R, rest stop to entry, target +1R |
| E4 | t1s1 + 60-minute time stop |
| E5 | t1s1, stop to entry once +0.5R is reached |
| M1 | SPY below its open at the decision bar (spy_fo < 0) |
| M2 | SPY <= -0.25% from open |
| U1 | top-500 pool (adv20 >= $95M ranked by adv20 x ATR%, per date; UNI1 definition) |
| U2 | adv20 >= $300M |
| C1 | refire, cooldown 12 bars (60 min) per symbol |
| C2 | refire, cooldown 6 bars (30 min) |
| G1 | gap <= -1.0% |
| K1 | M1 + E2 |
| K2 | M1 + W1 |
| K3 | ETFs (incl. leveraged) only |
| K4 | stocks only |
M1/M2/K3/K4/W2 are informed by tonight's live drill-down (17 sessions) — labelled live-informed.

## Gates (fixed now)
- N = 24 in this study -> full bar t >= max(1.5, sqrt(2 ln 24)) = 2.52; Testing bar (BAR90) = 0.9 x 2.52 = 2.27 (min 1.35).
  The RW7 lineage (rework1008 swarm, fullday) already tried many more configs, so this bar is a floor, not generous.
- Testing bar also needs: day-clustered t on all open data >= 2.27, train and valid each > 0, exp > 0 in up AND down
  regime sessions (gates.session_regimes), walk-forward positive months >= 54%, beats the random baseline,
  avg R w/o best day > 0 (flag best-day share >= 50%), BETA1 ex-market avg R reported, ~1+ trade/session.
- Filters must keep >= 80% of P0 trades and >= 90% of its top-decile winners (charter, filter creep) or be labelled so.
- Near-miss = valid > 0, t >= 1.35, regime pass, beats random -> backlog + forward-shadow hypothesis, not a decision.
- Locked block: not scored tonight (a finalist would be scored once later by the lead).
