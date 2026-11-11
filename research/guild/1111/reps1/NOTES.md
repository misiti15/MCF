# REPS1 — where live reps are lost: lever table (owner P1 item 1; Lead lead-20261111-1100-2). Descriptive, 0 configs.
Educational only — not financial advice. Research only; no config change. Any lever change is the owner's call.

Source: `signals` + `trades` of the 7 account journals (live paper runs), sessions 10-20..11-10 (16), pulled 11-11 11:15 ET.
`load.py` -> `fetch.py` (Alpaca 5-min SIP bars, all 2,236 signal symbols) -> `reps1.py` -> `reps1_out.txt`.
repv (main session) is not on any branch I can read, so this does not build on it. Overlap should be checked once it is pushed.

## Method
Every signal is labelled with its lever (the skip reason, mapped). Reps/session = skipped signals / 16 sessions, i.e. what fully
releasing that lever would add. Quality = a what-if GROSS R with a SIMPLIFIED exit (entry at the signal's ref price, 5-min bars
starting after the signal bar, stop first, target if set, else the 15:50-bar close). Calibrated on the 13,694 submitted signals that
have a live trade: simplified gross -0.029R vs live gross -0.100R, i.e. **+0.071R optimistic** (corr 0.92; Gen +0.08, others +0.07).
So compare a lever's what-if with the SUBMITTED row of the same group, never as an absolute R. No costs are in the what-if; for
wide-spread signals the true cost is far above the usual. Rule 21: this is a filter-level estimate, never a record.
Groups: Gen = Gen account (89 setups); low-rep = < 20 submitted live signals in the window or homed in Explore 1 / Live Lab (41).
Only 439 of 23,223 skipped signals were traded in another account the same day, so skipped signals are new information.

## Lever table (reps/session if released; what-if minus SUBMITTED in the same group)
| Group | Lever | Reps/session | Setups | Longs | What-if vs submitted |
|---|---|---|---|---|---|
| Gen | account halt (-R halt) | 66.3 | 40 | 69% | +0.204R (+0.092 vs -0.112) |
| Gen | buying power | 60.4 | 53 | 92% | +0.102R |
| Gen | spread filters | 83.1 | 79 | 68% | +0.075R gross, but no spread cost in it |
| Gen | per-setup max positions | 30.4 | 7 | 39% | -0.018R |
| Gen | not shortable / ETB | 26.8 | 28 | 0% | -0.016R |
| Low-rep | not shortable / ETB | 30.6 | 22 | 0% | -0.003R (submitted itself is only 19.9/session) |
| Low-rep | spread filters | 12.6 | 30 | 28% | +0.240R gross; spread cost not in it |
| Low-rep | twin / opposite side held | 11.2 | 10 | 2% | -0.273R |
| Low-rep | split-tape short gate | 6.3 | 5 | 0% | -0.402R |
| All | setup daily loss cap | 321.8 | 41 | 60% | -0.010R; almost none are Gen or low-rep setups |

## Reading (optimistic, honest)
1. **Gen is starved by account-level limits, not by its setups.** The -R account halt and buying power together skip ~127 Gen
   signals a session across 40-53 setups, about 0.7x what Gen submits (176). Their what-if is no worse than what was traded
   (better, if anything). Releasing them is an account question: spread Gen setups over the new Testing D/E/F accounts, or smaller
   size per Gen trade (reps matter, not P/L). The halt is a risk control, so this is the owner's call.
2. **Low-rep setups are starved by borrow.** Their single biggest loss is not shortable / ETB: 30.6 signals a session, more
   than they submit (19.9). Alpaca cannot short hard-to-borrow names, so this is not unlockable by config. It could be recorded as
   labelled 'virtual' reps (filter only, never a record), with no borrow fee in that number.
3. Spread filters skip many signals with good-looking gross what-ifs. The cost those names would really pay is not in the
   what-if, so do not release them without a cost-in estimate from the logged spread (next step).
4. The setup daily loss cap is the biggest lever by count (322 a session), but it sits on 41 busy setups that already have reps.
   Releasing it does not help the setups the owner wants judged.
5. Twin / opposite-side and the split-tape short gate block low-rep shorts whose what-if is clearly worse. Keep them.

Rule-change context in the window: Explore 1 / Live Lab trade from 11-05; Testing A top-500 pool from 11-04; Gen/Testing size and
halt settings per the ledger in 10-20..11-10. Counts mix those regimes; per-day counts are in `reps1_signals_sim.csv.gz` (scratch).

## REPS1b — levers in SETUP-DAYS (Lead lead-20261111-1300-2; Skeptic's fixes) — `reps1b.py` -> `reps1b_out.txt`, `spreadcost_out.txt`
The unit is the setup-day (Observer: same-day ICC ~0.19, a session ~ 4.8 independent trades). A skipped signal counts as a NEW
setup-day only if that setup submitted nothing that day in any account. What-ifs now subtract the exit-model gap by entry
hour (sim minus live gross on submitted trades: 9h +0.077, 10h +0.080, 11h +0.059, 12h +0.088, 13h +0.060, 14h +0.042, 15h +0.008).
Each lever is compared per day with the same group's submitted live gross (day-clustered t, n days, best-day share).
Current submitted setup-days per week: Gen 90.9, low-rep 43.8, other 260.3.

| Rank | Lever | New setup-days / week | Quality (hour-adjusted, vs traded) | Read |
|---|---|---|---|---|
| 1 | More setups live (new homes: Testing D/E/F, rotation of idle setups) | ~1 per added setup (Gen 1.07; low-rep median 3 submitted days of 16) | each setup's own | the only lever that scales; low-rep setups fire on a median 6 of 16 days, so their limit is how often they signal, not blocks |
| 2 | Gen account halt (spread Gen over more accounts) | 7.5 (40 setups) | +0.23R, but only 2 halt days, best day 83% | real days, unproven quality; one or two rebound afternoons |
| 3 | Gen buying power (same remedy) | 4.7 (53 setups) | +0.13R, day-t 1.71, 5 days | modest, plausible |
| - | Borrow (not shortable / ETB) | low-rep 21.3, other 11.6, Gen 6.6 | low-rep -0.02 (day-t -2.4); other +0.19 (t 2.8) | not unlockable at Alpaca. 'Virtual' only, labelled, never in a verdict (squeeze-prone, no borrow fee) |
| - | Spread filters | low-rep 16.9, Gen 8.4 | after the logged full spread (median 0.33R): Gen -0.52R, low-rep -0.16R vs live net -0.22 / -0.09 | KEEP the filters |
| - | Twin / opposite side; split-tape short gate; cost filter | low-rep 10.6 / 4.1 / 4.7 | -0.29 / -0.42 / -0.21R | KEEP |
| - | Setup daily loss cap; per-setup max positions | 0 new days | ~0 | only extra same-day entries on busy setups |

Honest bottom line: releasing blocks adds at most ~12 good-quality Gen setup-days a week (halt + buying power, about +13%), and
the halt's quality rests on 2 days. Every other block is either protective (spread, twin, short gate, cost) or not unlockable
(borrow). The scalable source of setup-days is more setups live at once: more homes and accounts, and rotating idle setups in.
That fits the playing-time rule (session rotation, no in-session throttling). Benched sessions produce no signals, so this
journal table cannot measure rotation itself. That needs the bench log.
