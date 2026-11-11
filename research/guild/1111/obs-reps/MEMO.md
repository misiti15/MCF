Educational only — not financial advice.

# Faster, sound verdicts on live setups: what the guild found (owner memo, 2026-11-11, Observer for the Research Guild)

All figures are live **paper** results (after paper costs), window 10-06..11-10 (26 sessions) unless stated. Rule changes inside it
(stacking 10-13, re-entry 10-14, twin cap 10-20/21, CF cost filter 10-30, Testing A top-500 11-04, Primary ~$4k lots 10-28 and -2R latch
10-29, new homes 11-05, TEAM-6 and account renames 11-11) mix into every record. Sources are the guild branch `mcf-guild`.

## 1. The unit of evidence is the setup-DAY, not the trade
- Trades of one setup on one day move together: within-day correlation ~0.19. At today's ~31 trades per setup-session, one session
  is worth **~4.8 independent trades**. Doubling same-day trades gives 5.1, quadrupling 5.2; the ceiling is ~5.4 (research/obs-verdicts).
- So more trades on days a setup already trades (more buying power, higher per-setup caps) barely speeds a verdict. **New days per
  setup, and more setups trading each day,** are what speed it.

## 2. Levers ranked by new setup-days per week (Scout, research/reps1 + reps2; today ~482 setup-days/week across 165 live slots)
| lever | new setup-days / week | quality of the added reps | status |
|---|---|---|---|
| **More setups live** (new homes; rotate idle setups in) | ~1 per added setup; 20 frequent setups ~45-55 (+10%), 20 low-rep 6-18 | unknown until traded | the only lever that scales |
| Gen account -R halt later / off | +7.5 | +0.23R vs submitted, but 2 days, best day 83% | unproven |
| Gen buying power | +4.7 | +0.13R, t 1.7, 5 days | small, unproven |
| Spread / twin / short-gate / cost filters | (would add reps) | skipped signals are worse (e.g. spread-skips -0.52R Gen) | **keep the filters** |
| Hard-to-borrow shorts | virtual only (Alpaca cannot short them) | least representative (squeeze-prone) | keep out of verdicts |
- A live slot gives a median **2.7 setup-days/week** (Graveyard 5.0, Primary 4.4, On Deck 3.9, Testing A 2.8, Gen 2.0, Testing C 1.7, Testing B 1.3).
- Housekeeping: MF4-h40-open-flowsell signalled on 14 of 16 days but submitted 0 (twin block); MF3-open-flowsell-rsi5hi 2 of 15. These are near-dead slots.
- Consistent with the playing-time rule: starvation is fixed by more slots and session rotation, never by in-session throttling in Primary/Testing.

## 3. Cleverer statistics do not buy speed yet
- On 26 sessions **no demote rule beat the base rate** ('negative next 5 sessions' is 69%): running average 64%, shrinkage toward the
  family 66% (research/obs-verdicts; the main session's fastdec found the same).
- On the setup's own component (day x side mean removed) they do *worse* than base (38-40% vs 49-53%): excess records mean-revert.
- The e-process monitor (XA-EPROC) raised no alarm in 26 sessions, as its power analysis predicts (20 sessions confirm almost nothing).

## 4. The catch in 'more setups': more lucky flags (Skeptic, research/skeptic-20261111/promo_luck)
- At live noise (sd 0.87R, ICC 0.19, 10 trades/session, 20 sessions), today's promote flag passes **~11% of ZERO-edge setups** and only
  **~40% of real +0.10R setups**. With 100 mostly-null setups that means ~10 lucky flags against a few real ones: precision ~30%,
  close to the 4 of 10 past promotions that stayed positive.
- **Proposal (owner DECISION, via Lead): two-stage promotion.** On Deck is scored only on sessions AFTER the move (a fresh sample),
  and the flag must pass again before Primary. Independent stages cut zero-edge passes from ~11% to ~1% (0.11 x 0.11).
  The cost: a real +0.10R setup passes both 20-session stages ~16% of the time (0.4 x 0.4), and needs ~40 sessions instead of 20;
  longer On Deck windows raise that. Also show **K, the number of setups evaluated,** on every promotion suggestion.

## 5. Replays (FWDCAL)
Builder's mirror-live replay runs tonight. The delay is chosen on 11-04..11-06 and rule 21 (>= 95% of live trades matched, avg R within
+-0.03, never optimistic) is scored once on 11-10..11-11. Until it passes, replays stay a filter, never a record. The old replay was
+0.08R optimistic; Scout's crude exit model shows a similar gap (+0.071R), so the exit model may be the main cause.

## Questions for the owner
1. Add setups/homes for setup-days (Gen spread over more accounts, more low-rep slots), accepting more lucky candidates?
2. Adopt two-stage promotion (fresh On Deck sample) with K shown on every promotion suggestion?
