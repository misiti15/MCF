Educational only — not financial advice.

# obs-verdicts — faster sound verdicts? (Observer, 2026-11-11 ~12:30 ET; owner live-reps priority, item 3)

Lead lead-20261111-1100-4. Builds on the main session's research/fastdec (branch claude/charming-mccarthy-i3rhhr). `verdicts.py` ->
`verdicts_out.txt`. Live paper trades, 7 journals, run_id 1, 10-06..11-10 (26 sessions, 18,878 trades, 194 setups). 6 rule x measure
cells, counted as looks. Rule-change context: the window holds the changes fastdec lists (stacking 10-13, re-entry 10-14, twin cap
10-20/21, CF cost filter 10-30, UNI1 11-04, Primary sizing 10-28 and -2R latch 10-29, ROLL1 11-05). One record mixes them.

Measure x = each trade's R minus the leave-one-out mean of the OTHER setups' trades on the same date and side (Skeptic: removes the
common day x side factor). Rules: (a) RAW running session-clustered avg (|t| >= 1.28), (b) EB shrinkage toward the leave-one-out family x
side mean (DL tau^2), (c) XA-EPROC alarms (cap 1R, K >= 20). Walk-forward as fastdec: 16 checkpoints, first call per setup, next-5 sessions.

## Failures first
- **No demote rule beats the base rate on either measure.** On raw R: RAW 64% vs base 69% (42 calls), EB 66% vs 69% (35), the same as fastdec.
  On the setup's own component x it is WORSE than base: RAW 40% vs 53% (20 calls), EB 38% vs 49% (8). Setups demoted on their excess
  went on to beat their day-side pool (+0.16R per trade forward). Excess records mean-revert over 5 sessions.
- **XA-EPROC raised no alarm in 26 sessions, edge or harm**, as its power analysis predicts (20 sessions confirm almost nothing).
- Promote: on x, at base (RAW 52% vs 47%; EB 38% vs 42%). The only cell above base, EB promote on raw R (6 of 7, base 28%), is 7 calls on
  raw R: a side/regime call (shorts in a short window), not the setup.
- Split-half persistence across 71 setups with >= 8 sessions: raw R r -0.07; excess x r +0.16 (z 1.35). The setup's own component
  persists a little more than raw, but not significantly.

## The outside-voice number for the owner's priority: information comes from SESSIONS, not trades
Trades of one setup on one day are correlated: ICC ~0.185 within setup-session. At today's size-weighted 31 trades per setup-session,
the design effect is 6.6, so a session is worth ~4.8 independent trades. **Doubling same-day reps gives 5.1, quadrupling 5.2**
(ceiling 1/ICC ~5.4). So 'unlock reps' levers that add trades on days a setup already trades barely speed verdicts. What speeds them:
(1) more DAYS per setup (setups that skip days: benched, rotated, capped out early, low-rep homes), (2) more independent setups per
family rather than more variants on the same symbol-days, (3) calibrated replays (rule 21) that add sessions, not trades.
