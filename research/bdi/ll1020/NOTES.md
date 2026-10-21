# Per-setup daily loss limit: 7-session replay (2026-10-12..10-20)

## Pre-declared before scoring (written before replay.py was run)

Question (owner): is `account.max_setup_daily_loss_r: 2.0` the right rule, or would 2.25R / another derivation keep
late-day recoveries (T1 MF1-FD on 10-20) while still stopping most bad setup-days?

Rules replayed (16 configurations; every one is reported):

| # | id | rule (a setup opens no new trade at time t when ...) |
|---|---|---|
| 1 | none | never blocked |
| 2-7 | fixed1.5 / 2 / 2.25 / 2.5 / 3 / 4 | realized R(t) <= -X |
| 8-9 | openrisk2 / openrisk3 | realized R(t) - (lots open at t, each counted at -1R) <= -X |
| 10 | pause60 | realized first reaches -2R at t0: no entries in [t0, t0+60 min); after that blocked only while realized <= -3R |
| 11 | pause30 | same with a 30-min pause |
| 12 | freq_sqrt | realized <= -X, X = max(2, 0.5*sqrt(avg trades/day over the setup's prior traded sessions)) |
| 13 | freq_step | realized <= -3 if the setup averaged >= 20 trades/day over prior sessions, else <= -2 |
| 14 | giveback3 | realized <= max(0, intraday realized high-water mark) - 3 |
| 15 | giveback3_floor2 | stop level = max(HWM - 3, -2), i.e. giveback3 but never looser than -2R (the "floor -2R" read as a cap on how deep it can go) |
| 16 | tod11 | realized <= -2, but only for entries at/after 11:00 ET (morning entries never blocked; morning losses still count after 11:00) |

Mechanics (fixed in advance):
- Unit = setup-day (account, session, strategy). Realized R(t) = sum of journal `r_multiple` of the setup's *taken* trades
  that exited before t, as production does (runner.py ~200 uses `r_multiple`). Rules are evaluated at each entry,
  not latched, exactly like `RiskManager.check` (realized can climb back above the line when open lots close green).
- "Prior sessions" for the frequency rules = the setup's run-1 history in the same account's journal before that day
  (all sessions it traded, last 10).
- Scoring uses **net R after costs**: live trades `pnl_adj / (|entry-stop| * shares)`; 10-20 blocked signals = journal
  what-if run 2 (`why=setup daily loss limit`) less the production cost model (as `nightly1020/caps.py`).
- Candidate trades per day = journal run-1 trades (+ on 10-20 the priced blocked signals). Before 10-20 no limit was
  live, so every candidate was really traded. The journal is used rather than `reports/<date>.csv` because it is a
  superset (late flatten / overnight records the EOD CSV missed: T1 10-12 +20, 10-14 +9, 10-19 +132; T2 10-12 +45).
- Ignored (second-order): slots / lot caps / buying power freed by blocked trades, signals that a blocked lot would
  have unblocked (twin / lot cap), and what-if fills vs live fills on 10-20.
- Accounts: Testing 1 (t1), Testing 2 (t2), Setup Generator (gen, from 10-19) carry the limit and form the total.
  Primary (p) has no per-setup limit; shown separately for information only.
- Outputs per rule: total and per-account net R, delta vs none split into saved (setup-days improved) and forgone
  (setup-days made worse), per-day totals, setup-days stopped, worst setup-day, T1 MF1-FD on 10-20,
  leave-one-day-out best rule, day-clustered mean/SE of the daily delta vs fixed2 (current) and vs none.

## Results (after scoring; full tables in `replay_out.md`)

Live **paper** trades, 7 sessions (10-12..10-20), 5,004 candidate entries in T1+T2+GEN (87 of them the 10-20 blocked
signals, what-if priced), 417 setup-days. Net R after costs. 16 configurations tried, all shown. Sanity: the fixed2
replay of 10-20 reproduces the live day (0 of 87 blocked signals taken, 2 of the 10-20 live entries would have been blocked).

**Failures first.**
- No realized-R rule (any fixed level, pause, frequency-scaled, give-back) keeps T1 MF1-FD's 10-20 recovery: it was
  already at -2.99R realized at 10:40, so 2.25/2.5 block it exactly like 2.0 (-6.63R vs +7.85R with no limit). Only
  `tod11` (+3.97R) and `pause30` (-2.98R) keep part of it, and both cost more elsewhere.
- **2.25R is not better than 2.0R:** -15.0R over 7 days (-2.2R/day, SE 3.6, t -0.6; better on 3 days, worse on 4).
  Every looser level loses more: 2.5 -18.7R, 3 -44.6R, 4 -89.8R, no limit -245.4R vs 2.0.
- 10-20 is the only one of 7 days where *no limit* beat 2.0 (+16.0R); on the other six the limit saved +12.9..+120.1R.
- The realized-only rule does not bound a setup-day: worst setup-day is -32.8R under every realized rule
  (T2 CWT14-pdl-p05-long 10-14: 31 lots opened before its first exit).
- Concentration: 10-15 carries ~half of every rule's saving (fixed2: +120R of +245R).

| rule | total | T1 | T2 | GEN | vs none | saved / forgone | vs random drop (ctrlA) | setup-days stopped | entries blocked | worst setup-day | MF1-FD 10-20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | -642.1 | -210.4 | -431.0 | -0.7 | 0 | 0 / 0 | 0 | 0 | 0 | -44.0 | +7.85 |
| fixed1.5 | -356.1 | -76.7 | -278.6 | -0.7 | +286.0 | +359.9 / -73.9 | +147.9 | 108 | 1173 | -32.8 | -4.26 |
| **fixed2 (live)** | **-396.6** | -81.3 | -314.7 | -0.7 | +245.4 | +312.7 / -67.3 | +123.4 | 93 | 1003 | -32.8 | -6.63 |
| fixed2.25 | -411.7 | -87.3 | -323.7 | -0.7 | +230.4 | +285.3 / -54.9 | +107.1 | 81 | 860 | -32.8 | -6.63 |
| fixed2.5 | -415.4 | -89.4 | -325.3 | -0.7 | +226.7 | +278.8 / -52.1 | +96.2 | 76 | 776 | -32.8 | -6.63 |
| fixed3 | -441.2 | -100.0 | -340.6 | -0.7 | +200.8 | +251.3 / -50.5 | +83.8 | 66 | 687 | -32.8 | -8.35 |
| fixed4 | -486.5 | -116.3 | -369.5 | -0.7 | +155.6 | +194.6 / -39.0 | +60.8 | 52 | 513 | -32.8 | -8.35 |
| openrisk2 | -113.1 | -33.9 | -77.7 | -1.4 | +529.0 | +843.1 / -314.1 | +474.7 | 231 | 3679 | -4.3 | -4.32 |
| openrisk3 | -177.5 | -60.2 | -116.3 | -1.0 | +464.5 | +757.3 / -292.7 | +422.7 | 203 | 3282 | -6.2 | -5.49 |
| pause60 | -399.0 | -86.2 | -312.1 | -0.7 | +243.1 | +319.7 / -76.6 | +132.2 | 96 | 1041 | -32.8 | -6.63 |
| pause30 | -401.7 | -81.3 | -319.7 | -0.7 | +240.3 | +307.6 / -67.3 | +123.2 | 94 | 971 | -32.8 | -2.98 |
| freq_sqrt | -416.9 | -90.6 | -325.7 | -0.7 | +225.1 | +288.1 / -63.0 | +97.5 | 84 | 823 | -32.8 | -6.63 |
| freq_step | -415.9 | -84.7 | -330.5 | -0.7 | +226.1 | +291.3 / -65.2 | +102.0 | 85 | 858 | -32.8 | -6.63 |
| giveback3 | -437.2 | -96.6 | -339.8 | -0.7 | +204.9 | +271.8 / -67.0 | +120.7 | 87 | 950 | -32.8 | -6.63 |
| giveback3_floor2 | -397.1 | -80.6 | -315.7 | -0.7 | +245.0 | +322.9 / -77.9 | +142.8 | 102 | 1136 | -32.8 | -6.63 |
| tod11 | -527.3 | -134.8 | -391.8 | -0.7 | +114.8 | +169.0 / -54.2 | +73.0 | 81 | 624 | -44.0 | +3.97 |

ctrlA = what dropping the same number of entries at random would give at the account's 7-day average net R per trade
(the accounts lose -0.09R (T1) / -0.16R (T2) per trade, so *any* rule that trades less looks good). A rule's real
selectivity is vs-none minus ctrlA: fixed1.5 +138, fixed2 +122, 2.25 +123, 2.5 +130, 3 +117, 4 +95, pause60 +111,
pause30 +117, freq_sqrt +128, freq_step +124, giveback3 +84, giveback3_floor2 +102, tod11 +42, **openrisk2 +54,
openrisk3 +42**. Primary (no limit configured) is in `replay_out.md`, info only.

**Variability.** Day-clustered delta vs fixed2 (n = 7 days): openrisk2 +40.5R/day (SE 18.7, t 2.2, 6/7 days better),
openrisk3 +31.3 (t 1.9), fixed1.5 +5.8 (SE 2.7, t 2.2, 6/7), every other rule <= 0 (2.25: -2.2, t -0.6). With 16
configurations the try-count bar is sqrt(2 ln 16) = 2.35: **nothing clears it**. Leave-one-day-out: openrisk2 is best
whichever day is dropped (openrisk3 second, every time); without the two open-risk rules fixed1.5 is best in all 7,
fixed2 ranks 2-6 and fixed2.25 ranks 3-8. The pick is made on the same 7 days it is measured on.

**Why not open-risk, despite the totals.** It blocks 3,679 of 5,004 entries (74%) and cuts 81 of 153 setup-days that
ended positive (-286R on them); per blocked entry it is barely better than random dropping (+54R over ctrlA vs +122R
for fixed2). Its gain is mostly "trade much less in accounts that lose per trade", which would also gut the Testing
accounts' purpose (collecting live data per setup), and the freed slots (ignored here) would be refilled by other
losing setups. It does fix a real defect - the worst setup-day falls from -32.8R to -4.3R - so it belongs in the backlog.

## Recommendation (firm)

**Keep `account.max_setup_daily_loss_r: 2.0` as it is in Testing 1, Testing 2, Graveyard and Setup Generator. Do not
move to 2.25R or to any of the other derivations.** Config change needed: none.

- 2.25R does not keep MF1-FD's 10-20 gain (it was -2.99R at the trip), and over 7 sessions it is 15R worse than 2.0R.
  Every looser or delayed variant is worse still; 10-20 was the one day of seven where the limit cost money.
- 2.0R saves ~2x what random trade-dropping would (+245R vs +123R), on 71 of the 91 bad setup-days (<= -3R), at a cost
  of 12 of 153 good setup-days (-48R).
- The data lean the other way (fixed1.5 +41R vs 2.0, t 2.2) but not past the 2.35 bar on 7 days; recheck after 10
  more sessions with `python replay.py <scratch>` (add the days to `DAYS`).
- Backlog (not live, rule 16): a separate open-risk bound on top of the -2R realized stop, e.g. a new key
  `account.max_setup_daily_risk_r: 3.0` = block when realized R + (open lots of the setup at -1R each) <= -3, checked in
  `RiskManager.check` next to the existing limit. It addresses the -32.8R overshoot; it needs a backlog replay with slot
  effects before any proposal. This exact combination was not among the 16 tested.

Limits: 7 sessions, paper fills; second-order slot / lot-cap effects ignored; 10-20 blocked signals priced by the
runner's what-if (next-bar entry) with the production cost model, live trades by journal `pnl_adj`.

## Files
- `replay.py` - the replay (`python replay.py <scratch>`, journals from `origin/mcf-data*` at `<scratch>/<acct>/journal.db`)
- `replay_out.md` - all tables (per rule, per day, deltas, day-clustered stats, leave-one-day-out, Primary, largest setup-day effects)
- `candidates.csv` - every candidate entry with net R and source (live / whatif)
- `setup_days.csv` - per rule x setup-day: candidates, taken, blocked, net R

Educational only - not financial advice.
