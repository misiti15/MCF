# FILLCOST — what entry latency costs in R, per account (descriptive, 0 configs)
Educational only — not financial advice. Follows Observer's obs-fillclock side fact ("Gen fills ~2x slower; R cost not measured").
Source: 14,740 live paper trades 10-20..11-11 (7 journals); trades.meta carries bar_age_min (decision bar close -> order), spread_bps,
and slip_bps (fill vs reference). `fillcost.py` -> `fillcost_out.txt`.

**Bug caught before posting:** meta strings can carry a suffix after the JSON (e.g. `;touch_fill`), and those trades are outcome-linked
(+0.61R vs -0.62R). A naive JSON parse dropped 41% of trades and kept a loser-heavy subset. Fixed: parse the JSON prefix only.
Selection check now: all trades -0.124R, kept -0.120R (14,685 of 14,740).

| Account | n | Bar close -> order (median min) | Order -> fill (median s) | Spread (median bps) | Entry slip (bps / R) | Net avg R |
|---|---|---|---|---|---|---|
| Gen | 2,986 | 1.25 | 1.9 | 8.9 | 5.1 / +0.009 | -0.198 |
| Graveyard | 6,349 | 1.25 | 1.7 | 7.4 | 4.8 / +0.022 | -0.098 |
| On Deck | 1,934 | 1.28 | 1.4 | 7.1 | 5.4 / +0.024 | -0.108 |
| Primary | 799 | 1.26 | 1.7 | 6.8 | 3.6 / +0.011 | -0.077 |
| Testing A | 2,492 | 1.26 | 1.5 | 8.1 | 5.1 / +0.011 | -0.111 |

Reading: decision latency is the same in every account (~1.25 min, the bar-close-to-order cycle), and broker fills take ~2 seconds.
Entry slip is ~half the spread and costs +0.01 to +0.02R, in Gen at the low end. So Gen's weaker net R is not a fill problem.
Observer's longer Gen 'decision -> fill' (1.24 vs ~0.5 min) likely reflects how the decision bar is stamped in Gen's journal
(5-minute signal bars in some Gen rows), not a slower broker. Worth reconciling on the bar_time field, not acting on.
The regression slope of slip on bar age is negative (-0.11 R/min, t -13) after spread. That is a confounded association
(later orders tend to come in calmer tape), not a causal 'waiting helps'. Do not use it.
