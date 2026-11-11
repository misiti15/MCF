Educational only — not financial advice.

# obs-horizon — is there any horizon where the gross edge clears costs? (Observer, 2026-11-11 ~06:00 ET; descriptive, 0 configs)

Lead's request lead-20261111-0500-2. Sources read: research/longhold/NOTES.md + MANAGEMENT.md + locked.json, research/swarm1010/w3_daily
and w2_neutral NOTES, the guild's days 1-3 (research/obs-synthesis/DAY1-3.md), and the live S6 paper status (mcf-data-longhold
longhold/status.json, read 11-11 01:04 ET).

| horizon | evidence | configs | result |
|---|---|---|---|
| intraday, minutes to the close | swarm1010 (owner 10-10: "~1.3M configs, no stock-specific edge after costs") + guild days 1-3 | ~1.3M + 134 | no pass. Live: 87% of trades sit in setups that lose BEFORE costs; new sources give size, not direction |
| intraday, hedged / relative value | swarm1010 w2_neutral | 530 | 0 pass |
| overnight / daily bars (1-20 days) | swarm1010 w3_daily | 158 | 4 'candidates' (3 Connors mean-reversion, 1 momentum/52-week high); overnight family 0 of 30 |
| weekly / monthly | research/longhold | 105 | **1 Tier-A pass: S6_mom12_1rev_N20_W** (12-1 momentum, skip top-decile 21-day winners, 20 names, weekly) |

## Where gross clears costs, and how solidly
- **Only the slow momentum family clears costs by a wide margin in the lab:** S6 active vs the EW universe +27 / +25 / +61 %/yr
  (train / valid / valid2) against a 1.2-1.3 %/yr cost drag, plus a whole 'near' cluster (S1, S2, L1). The arithmetic is the point:
  at a monthly horizon the expected spread is many times the round trip; intraday it is a fraction of it.
- **Its weak points are large** (longhold 2.2): active t 3.25 against a bar of 3.05; deflated Sharpe of the active return 0.12; without the
  best 3 months t 2.3 / 1.0 / 0.4; beta 1.3-2.2, vol 35-56 %; survivorship inflates the universe by ~6 %/yr (EW universe 17.7 % vs RSP 11.4 %).
  Locked block (scored once): +7.9 % active over 80 days, weekly active t 0.58, i.e. positive but not significant.
- **Live paper since 2026-10-12 (22 sessions): -18.2 % vs SPY -3.6 % and EW universe +1.0 %; max drawdown -29.9 %.** Within the backtest's
  stated -30..-45 % drawdown range and only a month, so not evidence either way (rough 1-2 sigma on ~35 %/yr active vol).

## Outside-voice flag for the owner (decision is the owner's; nothing changed)
- MANAGEMENT.md: at -25 % drawdown 'no new orders (holdings kept; owner decides)'. The 11-06 weekly rebalance was halted (-26.8 %).
  So the live book is now a **frozen** momentum portfolio holding its losers (e.g. AAOI -52 %, AXTI -37 % vs entry). The backtest rebalanced
  weekly through every drawdown, including -44 % in train. A frozen book is a different strategy from the one that passed. Its tracking
  vs the backtest replay is not computed (status: backtest_replay 0.0, te null). Question: should the -25 % halt stop the weekly rotation,
  or only new money / leverage? Momentum drawdowns are where rotation does its work.
