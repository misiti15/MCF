# OBS-FILLCLOCK — FWDCAL's exact-minute shortfall is live fill latency (Observer, 2026-11-11 evening)

Question: FWDCAL rule 21 on exact entry minutes failed in every account (ALL 0.386). Is that replay error?
Data: live journals, FWDCAL holdout 11-10..11-11, every live trade (2,055) joined to its submitted signal. 0 configs.

- Live `trades.entry_time` is the broker FILL clock (seconds != 0 in 96-100%), not the decision bar.
- Decision -> fill: median 0.47-0.58 min in Primary / On Deck / Testing A, 0.73 Graveyard, 1.17 Testing C, 1.24 Gen (p90 2.41).
- So the fill minute lands +1 or +2 (Gen up to +5) after the decision bar. One global replay delay D can match at most
  the modal offset's share: Testing A 0.920, On Deck 0.792, Primary 0.669, Graveyard 0.523, Gen 0.426, pooled 0.578.
- Builder's holdout exact-minute shares of matched trades: 0.904 / 0.805 / 0.62 / 0.541 / 0.246 (D0; Gen +1 share is 0.28) /
  ALL 0.556 - at or near these ceilings. Testing C 0.167 = its +1 share 2/12 exactly.
- And it explains why the best D flips by account in selection (Primary exact 0.95 at D0 vs 0.04 at D1; Gen 0.20 -> 0.42).

Reading: within the 5-minute matches, the exact-minute miss is order-routing latency, not replay fidelity; 95% on fill
minute is unreachable by any replay with one D. Rule 21's "same entry minute" is better scored on the DECISION bar
(live signals.info.bar_time vs the replay's signal bar). This does not rescue the 5-minute failure (0.694): the
spread-quote, caps cascade and no-signal causes (builder-20261111-2112-2) are real.
Side fact: Gen fills ~2x slower than other accounts (many orders per poll); R cost not measured here.
Repro: `python research/obs-fillclock/fillclock.py <dir of journals>` -> fillclock_out.txt. Educational only — not financial advice.
